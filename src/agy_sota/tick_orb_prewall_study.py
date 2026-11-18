"""Pre-Wall (`<= 2026-10-15`) Nanosecond `published-orb` Tape Microstructure Study (`T1`/`T2`/`T3`/`T4`/`L8`).

Implements pre-registered `H06_PREWALL_PUBLISHED_ORB_NANOSECOND_TAPE_SHIELD` (`Trial N = 80`, `t*(80) = 4.1466`):
1. Strict pre-wall truncation (`enforce_prewall_cutoff` <= `2026-10-15`) across all `14,750` `published-orb/{trades,quotes}`
   nanosecond Parquet pairs, `daily_raw`, `daily_split`, `sec_filings`, and `short_volume`.
2. Verified CTA/UTP condition-code semantics (`alpaca-sip/raw/meta/codes.json:88-90`):
   - `"F"` = Inter-market Sweep Order (`ISO`) — institutional lit sweep
   - `"I"` = Odd Lot Trade (never conflated with `"F"`)
   - `u is null` = non-canceled, uncorrected trade print
3. Causal Minute-`m` (`[m_start_ns, ns_entry)`) nanosecond Lee-Ready quote-matched Order-Flow Imbalance (`OFI`),
   `"F"` ISO buyer share, Boehmer-Jones-Zhang-Zhang (2021) non-retail `x == "D"` dark-pool share, prior-day FINRA
   `RegSHO` short-volume ratio (`day < trade_date`), and Point-in-Time SEC Dilution Shield (`filed_date <= trade_date - 1d`).
4. Realistic nanosecond execution at `ns_entry = m_start_ns + 60s` (start of minute `m+1`) buying at live firm NBBO ask
   `ap_entry` (`spread <= 35 bps`, directly paying entry half-spread!) and exiting at RTH `raw_close[t]` (`16:00 ET`),
   plus `1x` (`5 bps` + Almgren-Chriss sqrt impact) and `2x` (`10 bps` + `2x` impact) exit/impact stress.
"""

from __future__ import annotations

import argparse
import json
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from datetime import time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio_from_statistics
from skfolio.model_selection import CombinatorialPurgedCV

from agy_sota.invariants import (
    STUDY_WALL_DATE,
    bps_to_ratio,
    enforce_prewall_cutoff,
    hlz_dynamic_t_hurdle,
    ratio_to_bps,
)
from agy_sota.prewall_study import (
    DILUTION_FORMS,
    TICKET_NOTIONAL_USD,
    SubperiodMetric,
    _date_clustered_mean_tstat,
    _sample_moments,
)

NY_TZ = ZoneInfo("America/New_York")
EXIT_HALF_SPREAD_1X_BPS: float = 5.0


@dataclass(frozen=True, slots=True)
class TickOrbStudyResult:
    hypothesis_id: str
    evaluated_at_utc: str
    sample_min_date: str
    sample_max_date: str
    cumulative_trials_n: int
    required_hlz_t_hurdle: float
    orb_liquid_events_total: int
    events_count: int
    distinct_dates: int
    exposed_events_count: int
    mean_entry_spread_bps: float
    gross_ask_to_close_excess_bps: float
    mean_exit_and_impact_1x_bps: float
    net_return_1x_bps: float
    net_return_2x_bps: float
    net_1x_without_best_day_bps: float
    shield_vs_exposed_spread_1x_bps: float
    t_stat_clustered_1x: float
    t_stat_clustered_2x: float
    se_clustered_1x_bps: float
    daily_sharpe_native: float
    annualized_sharpe_1x: float
    dsr_probability: float
    deflated_sharpe_native: float
    cpcv_n_paths: int
    cpcv_median_oos_sharpe_annualized: float
    cpcv_positive_path_fraction: float
    subperiods: list[SubperiodMetric]
    passes_all_gates: bool


def extract_orb_minute_microstructure(
    trades_df: pl.DataFrame,
    quotes_df: pl.DataFrame,
    *,
    m_start_ns: int,
) -> dict[str, float] | None:
    """Compute causal Minute-`m` (`[m_start_ns, m_start_ns + 60s)`) tape features + `ns_entry` firm NBBO ask."""
    ns_entry = m_start_ns + 60_000_000_000

    q_clean = (
        quotes_df.filter((pl.col("bp") > 0.0) & (pl.col("ap") >= pl.col("bp")))
        .select(["t_ns", "bp", "ap"])
        .sort("t_ns")
    )
    if q_clean.is_empty():
        return None

    # Entry NBBO quote at ns_entry (last active firm quote <= ns_entry, or first within +5s if pre-entry quote absent)
    q_before = q_clean.filter(pl.col("t_ns") <= ns_entry).tail(1)
    if q_before.height == 0:
        q_before = q_clean.filter((pl.col("t_ns") > ns_entry) & (pl.col("t_ns") <= ns_entry + 5_000_000_000)).head(1)
    if q_before.height == 0:
        return None

    bp_entry = float(q_before["bp"][0])
    ap_entry = float(q_before["ap"][0])
    mid_entry = 0.5 * (bp_entry + ap_entry)
    if mid_entry <= 0.0:
        return None
    entry_spread_bps = ((ap_entry - bp_entry) / mid_entry) * 10_000.0

    # Strictly causal Minute-m trades: [m_start_ns, ns_entry), non-canceled (u is null), positive size & price
    t_m = trades_df.filter(
        (pl.col("t_ns") >= m_start_ns)
        & (pl.col("t_ns") < ns_entry)
        & pl.col("u").is_null()
        & (pl.col("p") > 0.0)
        & (pl.col("s") > 0.0)
    ).sort("t_ns")
    if t_m.is_empty():
        return None

    q_m = q_clean.filter(pl.col("t_ns") < ns_entry)
    if q_m.is_empty():
        q_m = q_before

    matched = t_m.join_asof(q_m, on="t_ns", strategy="backward").with_columns(
        [
            (0.5 * (pl.col("ap").fill_null(ap_entry) + pl.col("bp").fill_null(bp_entry))).alias("mid"),
            pl.col("p").shift(1).fill_null(pl.col("p")).alias("prev_p"),
            # CTA/UTP code "F" = Inter-market Sweep Order (ISO); "I" = Odd Lot (never conflated!)
            pl.col("c").list.contains("F").fill_null(False).alias("is_iso_f"),
            ((pl.col("p") * 100.0) % 1.0).alias("frac_cent"),
        ]
    )

    matched = matched.with_columns(
        [
            ((pl.col("p") > pl.col("mid")) | ((pl.col("p") == pl.col("mid")) & (pl.col("p") > pl.col("prev_p")))).alias(
                "is_buy"
            ),
            ((pl.col("p") < pl.col("mid")) | ((pl.col("p") == pl.col("mid")) & (pl.col("p") < pl.col("prev_p")))).alias(
                "is_sell"
            ),
            # BJZZ (2021) institutional / midpoint FINRA ADF/TRF dark-pool print: x=='D' excluding retail [0.01..0.39] & [0.61..0.99]
            (
                (pl.col("x") == "D")
                & (
                    (pl.col("frac_cent") < 0.01)
                    | (pl.col("frac_cent") > 0.99)
                    | ((pl.col("frac_cent") >= 0.40) & (pl.col("frac_cent") <= 0.60))
                )
            ).alias("is_bjzz_inst_dark"),
        ]
    )

    agg = matched.select(
        [
            pl.col("s").sum().alias("tot_vol"),
            pl.when(pl.col("is_buy")).then(pl.col("s")).otherwise(0.0).sum().alias("buy_vol"),
            pl.when(pl.col("is_sell")).then(pl.col("s")).otherwise(0.0).sum().alias("sell_vol"),
            pl.when(pl.col("is_buy") & pl.col("is_iso_f"))
            .then(pl.col("s"))
            .otherwise(0.0)
            .sum()
            .alias("iso_f_buy_vol"),
            pl.when(pl.col("is_bjzz_inst_dark")).then(pl.col("s")).otherwise(0.0).sum().alias("inst_dark_vol"),
        ]
    )
    tot_vol = float(agg["tot_vol"][0] or 0.0)
    if tot_vol <= 0.0:
        return None
    buy_vol = float(agg["buy_vol"][0] or 0.0)
    sell_vol = float(agg["sell_vol"][0] or 0.0)
    iso_f_buy_vol = float(agg["iso_f_buy_vol"][0] or 0.0)
    inst_dark_vol = float(agg["inst_dark_vol"][0] or 0.0)

    return {
        "ofi": (buy_vol - sell_vol) / tot_vol,
        "iso_f_buy_share": iso_f_buy_vol / max(buy_vol, 1.0),
        "bjzz_inst_dark_share": inst_dark_vol / tot_vol,
        "bp_entry": bp_entry,
        "ap_entry": ap_entry,
        "entry_spread_bps": entry_spread_bps,
        "minute_vol": tot_vol,
    }


def evaluate_published_orb_tape_events(
    orb_events_df: pl.DataFrame,
    daily_df: pl.DataFrame,
    sec_symbols_df: pl.DataFrame,
    sec_filings_df: pl.DataFrame,
    short_vol_df: pl.DataFrame,
    *,
    hypothesis_id: str = "H06_PREWALL_PUBLISHED_ORB_NANOSECOND_TAPE_SHIELD",
    cumulative_trials_n: int = 80,
    dilution_lookback_days: int = 90,
) -> TickOrbStudyResult:
    """Evaluate pre-registered `published-orb` nanosecond tape ignition (`<= 2026-10-15`)."""
    if orb_events_df.is_empty() or daily_df.is_empty():
        raise ValueError("orb_events_df and daily_df cannot be empty")

    enforce_prewall_cutoff(orb_events_df.select(pl.col("trade_date").max()).item())
    enforce_prewall_cutoff(daily_df.select(pl.col("trade_date").max()).item())

    operating = (
        sec_symbols_df.filter((pl.col("entity_type") == "operating") & pl.col("symbol").str.contains(r"^[A-Z]{1,4}$"))
        .select(["cik", "symbol"])
        .unique(subset=["symbol"], keep="first")
    )

    dilution_pit = (
        sec_filings_df.with_columns(pl.col("filed").str.slice(0, 10).str.to_date().alias("filed_date"))
        .filter((pl.col("filed_date") <= pl.lit(STUDY_WALL_DATE)) & pl.col("form").is_in(DILUTION_FORMS))
        .join(operating, on="cik", how="inner")
        .select(["symbol", "filed_date"])
        .unique()
        .sort(["symbol", "filed_date"])
    )

    short_pit = (
        short_vol_df.with_columns(pl.col("day").str.slice(0, 10).str.to_date().alias("sv_date"))
        .filter((pl.col("sv_date") <= pl.lit(STUDY_WALL_DATE)) & (pl.col("total_volume") > 0.0))
        .group_by(["symbol", "sv_date"])
        .agg((pl.col("short_volume").sum() / pl.col("total_volume").sum()).alias("regsho_short_ratio"))
        .sort(["symbol", "sv_date"])
    )

    daily_ctx = (
        daily_df.filter((pl.col("trade_date") <= pl.lit(STUDY_WALL_DATE)) & (pl.col("raw_close") > 0.0))
        .join(operating.select("symbol"), on="symbol", how="inner")
        .sort(["symbol", "trade_date"])
        .with_columns(
            [
                (pl.col("close") / pl.col("raw_close")).alias("adj_factor"),
                (pl.col("raw_close") * pl.col("raw_volume")).alias("raw_dv"),
                (pl.col("close") / pl.col("close").shift(1).over("symbol") - 1.0).alias("ret_1d"),
                pl.col("raw_close").shift(1).over("symbol").alias("prev_raw_close"),
                pl.col("close").shift(1).over("symbol").alias("prev_split_close"),
            ]
        )
        .with_columns(
            [
                pl.col("raw_dv")
                .shift(1)
                .rolling_median(window_size=20, min_samples=20)
                .over("symbol")
                .alias("adv_20d_usd"),
                pl.col("ret_1d").shift(1).rolling_std(window_size=20, min_samples=20).over("symbol").alias("sigma_20d"),
                (((pl.col("prev_split_close") / pl.col("prev_raw_close")) / pl.col("adj_factor") - 1.0).abs()).alias(
                    "split_drift"
                ),
            ]
        )
    )

    panel = (
        orb_events_df.join(
            daily_ctx.select(
                ["symbol", "trade_date", "raw_close", "prev_raw_close", "adv_20d_usd", "sigma_20d", "split_drift"]
            ),
            on=["symbol", "trade_date"],
            how="inner",
        )
        .filter(
            (pl.col("prev_raw_close") >= 5.0)
            & (pl.col("adv_20d_usd") >= 5_000_000.0)
            & pl.col("sigma_20d").is_finite()
            & (pl.col("split_drift") < 1e-4)
            & (pl.col("ap_entry") > 0.0)
            & (pl.col("entry_spread_bps") <= 35.0)
        )
        .with_columns(pl.col("trade_date").dt.offset_by("-1d").alias("prior_cal_date"))
        .sort(["symbol", "prior_cal_date"])
    )

    if panel.is_empty():
        raise ValueError("Liquid pre-wall ORB panel is empty after ex-ante filters")

    if dilution_pit.height > 0:
        panel = panel.join_asof(
            dilution_pit,
            left_on="prior_cal_date",
            right_on="filed_date",
            by="symbol",
            strategy="backward",
            check_sortedness=False,
        ).with_columns(
            (
                pl.col("filed_date").is_not_null()
                & ((pl.col("trade_date") - pl.col("filed_date")).dt.total_days() <= dilution_lookback_days)
            ).alias("recent_dilution_90d")
        )
    else:
        panel = panel.with_columns(pl.lit(False).alias("recent_dilution_90d"))

    if short_pit.height > 0:
        panel = panel.join_asof(
            short_pit,
            left_on="prior_cal_date",
            right_on="sv_date",
            by="symbol",
            strategy="backward",
            check_sortedness=False,
        ).with_columns(pl.col("regsho_short_ratio").fill_null(0.0))
    else:
        panel = panel.with_columns(pl.lit(0.0).alias("regsho_short_ratio"))

    exit_1x_ratio = bps_to_ratio(EXIT_HALF_SPREAD_1X_BPS)
    panel = (
        panel.with_columns(
            [
                # Real ask-crossing entry ap_entry -> RTH raw_close[t] (entry half-spread already paid in ap_entry!)
                (pl.col("raw_close") / pl.col("ap_entry") - 1.0).alias("ask_to_close_ret"),
                (
                    pl.lit(exit_1x_ratio)
                    + 0.10 * pl.col("sigma_20d") * (pl.lit(TICKET_NOTIONAL_USD) / pl.col("adv_20d_usd")).sqrt()
                ).alias("exit_impact_1x"),
            ]
        )
        .with_columns(pl.col("ask_to_close_ret").mean().over("trade_date").alias("univ_orb_ret"))
        .with_columns((pl.col("ask_to_close_ret") - pl.col("univ_orb_ret")).alias("gross_excess_ret"))
        .with_columns(
            [
                (pl.col("gross_excess_ret") - pl.col("exit_impact_1x")).alias("net_excess_1x"),
                (pl.col("gross_excess_ret") - 2.0 * pl.col("exit_impact_1x")).alias("net_excess_2x"),
                (
                    (pl.col("ofi") >= 0.10)
                    & ((pl.col("iso_f_buy_share") >= 0.15) | (pl.col("bjzz_inst_dark_share") >= 0.12))
                    & (pl.col("regsho_short_ratio") >= 0.45)
                ).alias("tape_ignition"),
            ]
        )
    )

    all_ign = panel.filter(pl.col("tape_ignition")).sort(["trade_date", "symbol"])
    shielded = all_ign.filter(~pl.col("recent_dilution_90d"))
    exposed = all_ign.filter(pl.col("recent_dilution_90d"))

    t_hurdle = hlz_dynamic_t_hurdle(cumulative_trials_n)
    min_dt = str(panel.select(pl.col("trade_date").min()).item())
    max_dt = str(panel.select(pl.col("trade_date").max()).item())

    if shielded.height == 0:
        return TickOrbStudyResult(
            hypothesis_id=hypothesis_id,
            evaluated_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            sample_min_date=min_dt,
            sample_max_date=max_dt,
            cumulative_trials_n=cumulative_trials_n,
            required_hlz_t_hurdle=t_hurdle,
            orb_liquid_events_total=panel.height,
            events_count=0,
            distinct_dates=0,
            exposed_events_count=exposed.height,
            mean_entry_spread_bps=0.0,
            gross_ask_to_close_excess_bps=0.0,
            mean_exit_and_impact_1x_bps=0.0,
            net_return_1x_bps=0.0,
            net_return_2x_bps=0.0,
            net_1x_without_best_day_bps=0.0,
            shield_vs_exposed_spread_1x_bps=0.0,
            t_stat_clustered_1x=0.0,
            t_stat_clustered_2x=0.0,
            se_clustered_1x_bps=0.0,
            daily_sharpe_native=0.0,
            annualized_sharpe_1x=0.0,
            dsr_probability=0.0,
            deflated_sharpe_native=0.0,
            cpcv_n_paths=0,
            cpcv_median_oos_sharpe_annualized=0.0,
            cpcv_positive_path_fraction=0.0,
            subperiods=[],
            passes_all_gates=False,
        )

    spr_arr = np.asarray(shielded["entry_spread_bps"].to_numpy(), dtype=np.float64)
    gross_bps_arr = np.asarray(shielded["gross_excess_ret"].to_numpy(), dtype=np.float64) * 10_000.0
    cost_bps_arr = np.asarray(shielded["exit_impact_1x"].to_numpy(), dtype=np.float64) * 10_000.0
    net_1x_bps_arr = np.asarray(shielded["net_excess_1x"].to_numpy(), dtype=np.float64) * 10_000.0
    net_2x_bps_arr = np.asarray(shielded["net_excess_2x"].to_numpy(), dtype=np.float64) * 10_000.0
    date_str_arr = np.asarray(shielded["trade_date"].cast(pl.String).to_numpy())

    mean_1x_bps, se_1x_bps, t_1x = _date_clustered_mean_tstat(net_1x_bps_arr, date_str_arr)
    mean_2x_bps, _, t_2x = _date_clustered_mean_tstat(net_2x_bps_arr, date_str_arr)
    exposed_mean_1x_bps = (
        ratio_to_bps(float(np.mean(np.asarray(exposed["net_excess_1x"].to_numpy(), dtype=np.float64))))
        if exposed.height > 0
        else 0.0
    )

    by_day = (
        shielded.group_by("trade_date").agg(pl.col("net_excess_1x").mean().alias("cohort_net_1x")).sort("trade_date")
    )
    best_day = by_day.sort("cohort_net_1x", descending=True).select("trade_date").head(1).item()
    without_best = shielded.filter(pl.col("trade_date") != pl.lit(best_day))
    net_1x_no_best_bps = (
        ratio_to_bps(float(np.mean(np.asarray(without_best["net_excess_1x"].to_numpy(), dtype=np.float64))))
        if without_best.height > 0
        else 0.0
    )

    all_sessions = daily_ctx.select("trade_date").unique().sort("trade_date")
    daily_rets = np.asarray(
        all_sessions.join(by_day, on="trade_date", how="left")
        .with_columns(pl.col("cohort_net_1x").fill_null(0.0))["cohort_net_1x"]
        .to_numpy(),
        dtype=np.float64,
    )

    def _native_sr(arr: np.ndarray) -> float:
        sd = float(np.std(arr, ddof=1)) if arr.size > 2 else 0.0
        return float(np.mean(arr) / sd) if sd > 1e-12 else 0.0

    n_days = int(daily_rets.size)
    sr_native = _native_sr(daily_rets)
    sr_ann = sr_native * math.sqrt(252.0)

    exp_by_day = exposed.group_by("trade_date").agg(pl.col("net_excess_1x").mean().alias("r"))
    exp_rets = np.asarray(
        all_sessions.join(exp_by_day, on="trade_date", how="left")
        .with_columns(pl.col("r").fill_null(0.0))["r"]
        .to_numpy(),
        dtype=np.float64,
    )
    all_by_day = all_ign.group_by("trade_date").agg(pl.col("net_excess_1x").mean().alias("r"))
    all_rets = np.asarray(
        all_sessions.join(all_by_day, on="trade_date", how="left")
        .with_columns(pl.col("r").fill_null(0.0))["r"]
        .to_numpy(),
        dtype=np.float64,
    )
    emp_var = float(np.var([sr_native, _native_sr(exp_rets), _native_sr(all_rets)], ddof=1))
    var_trials = max(emp_var, 1.0 / max(float(n_days), 1.0))

    skew, ex_kurt, ac1 = _sample_moments(daily_rets)
    dsr_res = deflated_sharpe_ratio_from_statistics(
        observed_sharpe=sr_native,
        n_samples=max(n_days, 10),
        n_trials=max(cumulative_trials_n, 1),
        variance_trials=var_trials,
        benchmark_sharpe=0.0,
        skewness=skew,
        excess_kurtosis=ex_kurt,
        autocorrelation=ac1,
        frequency="daily",
    )

    cpcv_sharpes: list[float] = []
    if n_days >= 60:
        cv = CombinatorialPurgedCV(n_folds=6, n_test_folds=2, purged_size=1, embargo_size=1)
        dummy_x = daily_rets.reshape(-1, 1)
        splits = list(cv.split(dummy_x))
        path_ids = cv.get_path_ids()
        n_paths = int(path_ids.max()) + 1
        for pid in range(n_paths):
            segs: list[np.ndarray] = []
            for s_idx, (train_idx, test_folds) in enumerate(splits):
                if train_idx.size == 0:
                    continue
                for fold_pos, fold_indices in enumerate(test_folds):
                    if int(path_ids[s_idx, fold_pos]) == pid:
                        segs.append(np.asarray(fold_indices, dtype=int))
            if segs:
                full_oos_idx = np.sort(np.concatenate(segs))
                cpcv_sharpes.append(_native_sr(daily_rets[full_oos_idx]) * math.sqrt(252.0))

    cpcv_median = float(np.median(cpcv_sharpes)) if cpcv_sharpes else 0.0
    cpcv_pos_frac = float(np.mean([s > 0.0 for s in cpcv_sharpes])) if cpcv_sharpes else 0.0

    subperiods: list[SubperiodMetric] = []
    yr_df = (
        shielded.with_columns(pl.col("trade_date").dt.year().alias("year"))
        .group_by("year")
        .agg(
            [
                pl.len().alias("events"),
                pl.col("trade_date").n_unique().alias("distinct_dates"),
                (pl.col("net_excess_1x").mean() * 10_000.0).alias("mean_net_1x_bps"),
                (pl.col("net_excess_2x").mean() * 10_000.0).alias("mean_net_2x_bps"),
            ]
        )
        .sort("year")
    )
    for row in yr_df.iter_rows(named=True):
        subperiods.append(
            SubperiodMetric(
                year=int(row["year"]),
                events=int(row["events"]),
                distinct_dates=int(row["distinct_dates"]),
                mean_net_1x_bps=round(float(row["mean_net_1x_bps"]), 3),
                mean_net_2x_bps=round(float(row["mean_net_2x_bps"]), 3),
            )
        )

    distinct_dt_count = int(shielded["trade_date"].n_unique())
    passes = (
        shielded.height >= 200
        and distinct_dt_count >= 60
        and t_1x >= t_hurdle
        and float(dsr_res.probability) >= 0.95
        and mean_1x_bps > 0.0
        and mean_2x_bps > 0.0
        and net_1x_no_best_bps > 0.0
    )

    return TickOrbStudyResult(
        hypothesis_id=hypothesis_id,
        evaluated_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sample_min_date=min_dt,
        sample_max_date=max_dt,
        cumulative_trials_n=cumulative_trials_n,
        required_hlz_t_hurdle=t_hurdle,
        orb_liquid_events_total=panel.height,
        events_count=shielded.height,
        distinct_dates=distinct_dt_count,
        exposed_events_count=exposed.height,
        mean_entry_spread_bps=round(float(np.mean(spr_arr)), 3),
        gross_ask_to_close_excess_bps=round(float(np.mean(gross_bps_arr)), 3),
        mean_exit_and_impact_1x_bps=round(float(np.mean(cost_bps_arr)), 3),
        net_return_1x_bps=round(mean_1x_bps, 3),
        net_return_2x_bps=round(mean_2x_bps, 3),
        net_1x_without_best_day_bps=round(net_1x_no_best_bps, 3),
        shield_vs_exposed_spread_1x_bps=round(mean_1x_bps - exposed_mean_1x_bps, 3),
        t_stat_clustered_1x=round(t_1x, 4),
        t_stat_clustered_2x=round(t_2x, 4),
        se_clustered_1x_bps=round(se_1x_bps if math.isfinite(se_1x_bps) else 0.0, 3),
        daily_sharpe_native=round(sr_native, 5),
        annualized_sharpe_1x=round(sr_ann, 4),
        dsr_probability=round(float(dsr_res.probability), 5),
        deflated_sharpe_native=round(float(dsr_res.deflated_sharpe), 5),
        cpcv_n_paths=len(cpcv_sharpes),
        cpcv_median_oos_sharpe_annualized=round(cpcv_median, 4),
        cpcv_positive_path_fraction=round(cpcv_pos_frac, 4),
        subperiods=subperiods,
        passes_all_gates=passes,
    )


def _process_single_orb_pair(item: tuple[str, date, str, Path, Path]) -> dict[str, object] | None:
    sym, d, hhmm, t_path, q_path = item
    try:
        hh = int(hhmm[:2])
        mm = int(hhmm[2:])
        m_start_ns = int(datetime.combine(d, dtime(hh, mm, 0), tzinfo=NY_TZ).timestamp() * 1_000_000_000)
        t_df = pl.read_parquet(t_path, columns=["t_ns", "x", "p", "s", "c", "u"])
        q_df = pl.read_parquet(q_path, columns=["t_ns", "bp", "ap"])
        feats = extract_orb_minute_microstructure(t_df, q_df, m_start_ns=m_start_ns)
        if feats is None:
            return None
        return {
            "symbol": sym,
            "trade_date": d,
            "entry_hhmm": hhmm,
            **feats,
        }
    except Exception:
        return None


def load_local_published_orb_prewall(
    *,
    years: tuple[int, ...] = (2024, 2025, 2026),
    universe_root: Path | None = None,
    orb_root: Path | None = None,
    public_tables_root: Path | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Load strictly pre-wall (`<= 2026-10-15`) `published-orb` nanosecond pairs + daily + SEC + RegSHO tables."""
    u_root = universe_root or (Path.home() / "Documents" / "trading-sota" / "data" / "private" / "universe")
    o_root = orb_root or (Path.home() / "Documents" / "market-data" / "alpaca-sip" / "raw" / "published-orb")
    p_root = public_tables_root or (Path.home() / "Documents" / "market-data" / "public" / "tables")

    wall_iso = STUDY_WALL_DATE.isoformat()
    sec_symbols = pl.read_parquet(p_root / "sec_symbols.parquet")
    sec_filings = pl.read_parquet(p_root / "sec_filings.parquet").filter(pl.col("filed").str.slice(0, 10) <= wall_iso)
    short_vol = pl.read_parquet(p_root / "short_volume.parquet").filter(pl.col("day").str.slice(0, 10) <= wall_iso)

    op_set = set(
        sec_symbols.filter((pl.col("entity_type") == "operating") & pl.col("symbol").str.contains(r"^[A-Z]{1,4}$"))[
            "symbol"
        ].to_list()
    )

    daily_frames: list[pl.DataFrame] = []
    for yr in years:
        raw_df = (
            pl.read_csv(u_root / str(yr) / "daily_raw.csv.gz", columns=["symbol", "ts_utc", "close", "volume"])
            .with_columns(pl.col("ts_utc").str.slice(0, 10).alias("day_str"))
            .filter((pl.col("day_str") <= wall_iso) & pl.col("symbol").is_in(op_set))
            .select(
                [
                    pl.col("symbol"),
                    pl.col("day_str").str.to_date().alias("trade_date"),
                    pl.col("close").cast(pl.Float64).alias("raw_close"),
                    pl.col("volume").cast(pl.Float64).alias("raw_volume"),
                ]
            )
        )
        spl_df = (
            pl.read_csv(
                u_root / str(yr) / "daily_split.csv.gz",
                columns=["symbol", "ts_utc", "open", "high", "low", "close", "volume"],
            )
            .with_columns(pl.col("ts_utc").str.slice(0, 10).alias("day_str"))
            .filter((pl.col("day_str") <= wall_iso) & pl.col("symbol").is_in(op_set))
            .select(
                [
                    pl.col("symbol"),
                    pl.col("day_str").str.to_date().alias("trade_date"),
                    pl.col("open").cast(pl.Float64),
                    pl.col("high").cast(pl.Float64),
                    pl.col("low").cast(pl.Float64),
                    pl.col("close").cast(pl.Float64),
                    pl.col("volume").cast(pl.Float64),
                ]
            )
        )
        daily_frames.append(spl_df.join(raw_df, on=["symbol", "trade_date"], how="inner"))

    daily_df = pl.concat(daily_frames, how="vertical").unique(subset=["symbol", "trade_date"], keep="last")

    # Enumerate only operating symbols & pre-wall dates <= 2026-10-15!
    work_items: list[tuple[str, date, str, Path, Path]] = []
    trades_base = o_root / "trades"
    quotes_base = o_root / "quotes"
    for sym_dir in sorted(trades_base.iterdir()):
        if not sym_dir.is_dir() or sym_dir.name not in op_set:
            continue
        sym = sym_dir.name
        q_sym_dir = quotes_base / sym
        if not q_sym_dir.is_dir():
            continue
        for tf in sorted(sym_dir.glob("*.parquet")):
            stem = tf.stem  # YYYY-MM-DD_HHMM
            if len(stem) < 15 or stem[:10] > wall_iso:
                continue
            qf = q_sym_dir / tf.name
            if not qf.is_file():
                continue
            d_obj = date.fromisoformat(stem[:10])
            enforce_prewall_cutoff(d_obj)
            work_items.append((sym, d_obj, stem[11:15], tf, qf))

    with ThreadPoolExecutor(max_workers=8) as pool:
        extracted = [r for r in pool.map(_process_single_orb_pair, work_items) if r is not None]

    orb_events_df = pl.DataFrame(extracted)
    return orb_events_df, daily_df, sec_symbols, sec_filings, short_vol


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run pre-registered published-orb nanosecond tape study (<=2026-10-15)"
    )
    parser.add_argument("--trials-n", type=int, default=80)
    parser.add_argument("--hypothesis-id", type=str, default="H06_PREWALL_PUBLISHED_ORB_NANOSECOND_TAPE_SHIELD")
    parser.add_argument("--out-json", type=str, default="")
    args = parser.parse_args()

    orb_df, daily_df, sec_symbols_df, sec_filings_df, short_vol_df = load_local_published_orb_prewall()
    res = evaluate_published_orb_tape_events(
        orb_df,
        daily_df,
        sec_symbols_df,
        sec_filings_df,
        short_vol_df,
        hypothesis_id=args.hypothesis_id,
        cumulative_trials_n=args.trials_n,
    )
    payload = json.dumps(asdict(res), indent=2)
    if args.out_json:
        out_p = Path(args.out_json).expanduser().resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
