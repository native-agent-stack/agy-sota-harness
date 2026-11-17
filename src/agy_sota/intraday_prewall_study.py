"""Pre-Wall (`<= 2026-10-15`) Whole-Market Intraday `1-Min` SIP Ignition & SEC Dilution Study (`T1`/`T2`/`T4`/`L8`).

Implements pre-registered `H04_PREWALL_INTRADAY_1030_IGNITION_TO_NEXTOPEN` (`Trial N = 78`, `t*(78) = 4.1408`):
1. Strict pre-wall truncation (`enforce_prewall_cutoff` <= `2026-10-15`) BEFORE computing `raw_open[t+1]`, ensuring neither
   intraday features (`09:30..10:29 ET`) nor next-morning exits (`open[t+1]`) read any post-wall (`>= 2026-10-16`) data.
2. Exact dimensional unit alignment (`NVDA` 10:1 verified): `bars-1min` holds raw prices & raw volumes, so trailing 20-day
   split-consistent volume `vol_ma20_split[t-1]` is mapped into day-`t` raw share units via `vol_ma20_split[t-1] * adj_factor[t]`,
   and returns `[open_1030[t] -> raw_close[t] -> raw_open[t+1]]` are evaluated on split-invariant windows (`split_drift < 1e-4`).
3. Causal `10:30:00 ET` signal (bars stamped `09:30:00..10:29:00 ET`, complete at `10:30:00 ET`) entering at the first
   tradable minute open in `[10:30:00..10:34:00 ET]` and exiting at `raw_open[t+1]`, decomposing remaining RTH drift
   (`10:30 -> 16:00`) vs. overnight drift (`16:00 -> open[t+1]`).
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from datetime import time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
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
    BASE_COST_1X_BPS,
    DILUTION_FORMS,
    TICKET_NOTIONAL_USD,
    SubperiodMetric,
    _date_clustered_mean_tstat,
    _sample_moments,
)

NY_TZ = ZoneInfo("America/New_York")


@dataclass(frozen=True, slots=True)
class IntradayPrewallResult:
    hypothesis_id: str
    evaluated_at_utc: str
    sample_min_date: str
    sample_max_date: str
    cumulative_trials_n: int
    required_hlz_t_hurdle: float
    universe_symbol_days: int
    events_count: int
    distinct_dates: int
    exposed_events_count: int
    rth_1030_to_close_excess_bps: float
    overnight_close_to_nextopen_excess_bps: float
    gross_excess_bps: float
    mean_cost_1x_bps: float
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


def evaluate_intraday_1030_ignition_panel(
    joined_df: pl.DataFrame,
    sec_symbols_df: pl.DataFrame,
    sec_filings_df: pl.DataFrame,
    *,
    hypothesis_id: str = "H04_PREWALL_INTRADAY_1030_IGNITION_TO_NEXTOPEN",
    cumulative_trials_n: int = 78,
    dilution_lookback_days: int = 90,
) -> IntradayPrewallResult:
    """Evaluate pre-registered `10:30 ET -> open[t+1]` Pre-Travel Volume-Shock + PIT SEC Dilution Shield (`<= 2026-10-15`).

    Expected `joined_df` columns:
      `symbol` (str), `trade_date` (Date),
      `raw_open` (f64), `raw_close` (f64), `raw_volume` (f64),
      `open` (f64, split-adj), `close` (f64, split-adj), `volume` (f64, split-adj),
      `open_0930` (f64, raw 1m), `high_0930_1029` (f64, raw 1m), `low_0930_1029` (f64, raw 1m),
      `close_1029` (f64, raw 1m), `vol_0930_1029` (f64, raw 1m), `open_1030` (f64, raw 1m).
    """
    if joined_df.is_empty():
        raise ValueError("joined_df cannot be empty")

    max_input_date = joined_df.select(pl.col("trade_date").max()).item()
    enforce_prewall_cutoff(max_input_date)

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

    panel = (
        joined_df.filter(
            (pl.col("trade_date") <= pl.lit(STUDY_WALL_DATE))
            & (pl.col("raw_close") > 0.0)
            & (pl.col("close") > 0.0)
            & (pl.col("volume") > 0.0)
        )
        .join(operating.select("symbol"), on="symbol", how="inner")
        .sort(["symbol", "trade_date"])
    )

    # Strictly causal prior-day [..t-1] universe state + pre-wall [open_1030[t] -> raw_open[t+1]] returns.
    panel = panel.with_columns(
        [
            (pl.col("close") / pl.col("raw_close")).alias("adj_factor"),
            (pl.col("raw_close") * pl.col("raw_volume")).alias("raw_dollar_vol"),
            (pl.col("close") / pl.col("close").shift(1).over("symbol") - 1.0).alias("ret_1d_split"),
            pl.col("raw_close").shift(1).over("symbol").alias("prev_raw_close"),
            pl.col("close").shift(1).over("symbol").alias("prev_split_close"),
            pl.col("close").shift(1).rolling_mean(window_size=50, min_samples=50).over("symbol").alias("prev_sma_50"),
            pl.col("volume")
            .shift(1)
            .rolling_mean(window_size=20, min_samples=20)
            .over("symbol")
            .alias("vol_ma20_split_prev"),
            pl.col("raw_open").shift(-1).over("symbol").alias("next_raw_open"),
            pl.col("close").shift(-1).over("symbol").alias("next_split_close"),
            pl.col("raw_close").shift(-1).over("symbol").alias("next_raw_close"),
        ]
    ).with_columns(
        [
            pl.col("raw_dollar_vol")
            .shift(1)
            .rolling_median(window_size=20, min_samples=20)
            .over("symbol")
            .alias("adv_20d_usd"),
            pl.col("ret_1d_split")
            .shift(1)
            .rolling_std(window_size=20, min_samples=20)
            .over("symbol")
            .alias("sigma_20d"),
            # Convert split-adjusted 20d mean volume into day-t raw share units (NVDA 10:1 verified: split_vol * adj_factor == raw_vol)
            (pl.col("vol_ma20_split_prev") * pl.col("adj_factor")).alias("vol_ma20_raw_equiv"),
            (
                ((pl.col("next_split_close") / pl.col("next_raw_close")) / pl.col("adj_factor") - 1.0).abs()
                + ((pl.col("prev_split_close") / pl.col("prev_raw_close")) / pl.col("adj_factor") - 1.0).abs()
            ).alias("split_drift"),
        ]
    )

    liquid = (
        panel.filter(
            (pl.col("prev_raw_close") >= 5.0)
            & (pl.col("adv_20d_usd") >= 5_000_000.0)
            & (pl.col("prev_split_close") > pl.col("prev_sma_50"))
            & pl.col("vol_ma20_raw_equiv").is_finite()
            & (pl.col("vol_ma20_raw_equiv") > 0.0)
            & pl.col("sigma_20d").is_finite()
            & pl.col("open_0930").is_finite()
            & (pl.col("open_0930") > 0.0)
            & pl.col("close_1029").is_finite()
            & (pl.col("close_1029") > 0.0)
            & pl.col("open_1030").is_finite()
            & (pl.col("open_1030") > 0.0)
            & pl.col("next_raw_open").is_finite()
            & (pl.col("next_raw_open") > 0.0)
            & (pl.col("split_drift") < 1e-4)
        )
        .with_columns(
            [
                # Strictly prior-day trade_date - 1d cutoff for SEC filings so zero same-day filing-timestamp ambiguity
                pl.col("trade_date").dt.offset_by("-1d").alias("prior_cal_date"),
                (pl.col("vol_0930_1029") / pl.col("vol_ma20_raw_equiv")).alias("fh_vol_frac"),
                (pl.col("close_1029") / pl.col("open_0930") - 1.0).alias("fh_o2c_ret"),
                (pl.col("open_0930") / pl.col("prev_raw_close") - 1.0).alias("open_gap_ret"),
                (
                    (pl.col("close_1029") - pl.col("low_0930_1029"))
                    / pl.max_horizontal(pl.col("high_0930_1029") - pl.col("low_0930_1029"), pl.lit(1e-9))
                ).alias("fh_close_pos"),
                (pl.col("raw_close") / pl.col("open_1030") - 1.0).alias("rth_rem_ret"),
                (pl.col("next_raw_open") / pl.col("raw_close") - 1.0).alias("overnight_ret"),
                (pl.col("next_raw_open") / pl.col("open_1030") - 1.0).alias("hold_1030_to_nextopen_ret"),
            ]
        )
        .sort(["symbol", "prior_cal_date"])
    )

    if liquid.is_empty():
        raise ValueError("Liquid intraday pre-wall panel is empty after ex-ante filters")

    if dilution_pit.height > 0:
        liquid = liquid.join_asof(
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
        liquid = liquid.with_columns(pl.lit(False).alias("recent_dilution_90d"))

    base_1x_ratio = bps_to_ratio(BASE_COST_1X_BPS)
    liquid = (
        liquid.with_columns(
            [
                pl.col("rth_rem_ret").mean().over("trade_date").alias("univ_rth_rem"),
                pl.col("overnight_ret").mean().over("trade_date").alias("univ_overnight"),
                pl.col("hold_1030_to_nextopen_ret").mean().over("trade_date").alias("univ_hold_ret"),
                (
                    pl.lit(base_1x_ratio)
                    + 0.10 * pl.col("sigma_20d") * (pl.lit(TICKET_NOTIONAL_USD) / pl.col("adv_20d_usd")).sqrt()
                ).alias("cost_1x_ratio"),
            ]
        )
        .with_columns(
            [
                (pl.col("rth_rem_ret") - pl.col("univ_rth_rem")).alias("rth_rem_excess"),
                (pl.col("overnight_ret") - pl.col("univ_overnight")).alias("overnight_excess"),
                (pl.col("hold_1030_to_nextopen_ret") - pl.col("univ_hold_ret")).alias("gross_excess_ret"),
            ]
        )
        .with_columns(
            [
                (pl.col("gross_excess_ret") - pl.col("cost_1x_ratio")).alias("net_excess_1x"),
                (pl.col("gross_excess_ret") - 2.0 * pl.col("cost_1x_ratio")).alias("net_excess_2x"),
                (
                    (pl.col("fh_vol_frac") >= 0.60)
                    & (pl.col("fh_o2c_ret") >= 0.010)
                    & (pl.col("fh_o2c_ret") <= 0.060)
                    & (pl.col("open_gap_ret").abs() <= 0.050)
                    & (pl.col("fh_close_pos") >= 0.75)
                ).alias("intraday_ignition"),
            ]
        )
    )

    all_ign = liquid.filter(pl.col("intraday_ignition")).sort(["trade_date", "symbol"])
    shielded = all_ign.filter(~pl.col("recent_dilution_90d"))
    exposed = all_ign.filter(pl.col("recent_dilution_90d"))

    t_hurdle = hlz_dynamic_t_hurdle(cumulative_trials_n)
    min_dt = str(liquid.select(pl.col("trade_date").min()).item())
    max_dt = str(liquid.select(pl.col("trade_date").max()).item())

    if shielded.height == 0:
        return IntradayPrewallResult(
            hypothesis_id=hypothesis_id,
            evaluated_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            sample_min_date=min_dt,
            sample_max_date=max_dt,
            cumulative_trials_n=cumulative_trials_n,
            required_hlz_t_hurdle=t_hurdle,
            universe_symbol_days=liquid.height,
            events_count=0,
            distinct_dates=0,
            exposed_events_count=exposed.height,
            rth_1030_to_close_excess_bps=0.0,
            overnight_close_to_nextopen_excess_bps=0.0,
            gross_excess_bps=0.0,
            mean_cost_1x_bps=0.0,
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

    rth_bps_arr = np.asarray(shielded["rth_rem_excess"].to_numpy(), dtype=np.float64) * 10_000.0
    on_bps_arr = np.asarray(shielded["overnight_excess"].to_numpy(), dtype=np.float64) * 10_000.0
    gross_bps_arr = np.asarray(shielded["gross_excess_ret"].to_numpy(), dtype=np.float64) * 10_000.0
    cost_bps_arr = np.asarray(shielded["cost_1x_ratio"].to_numpy(), dtype=np.float64) * 10_000.0
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

    # Non-overlapping 1-period daily strategy return series: [10:30[t] -> open[t+1]] has zero multi-day horizon overlap!
    all_sessions = liquid.select("trade_date").unique().sort("trade_date")
    daily_series_df = all_sessions.join(by_day, on="trade_date", how="left").with_columns(
        pl.col("cohort_net_1x").fill_null(0.0)
    )
    daily_rets = np.asarray(daily_series_df["cohort_net_1x"].to_numpy(), dtype=np.float64)

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

    return IntradayPrewallResult(
        hypothesis_id=hypothesis_id,
        evaluated_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sample_min_date=min_dt,
        sample_max_date=max_dt,
        cumulative_trials_n=cumulative_trials_n,
        required_hlz_t_hurdle=t_hurdle,
        universe_symbol_days=liquid.height,
        events_count=shielded.height,
        distinct_dates=distinct_dt_count,
        exposed_events_count=exposed.height,
        rth_1030_to_close_excess_bps=round(float(np.mean(rth_bps_arr)), 3),
        overnight_close_to_nextopen_excess_bps=round(float(np.mean(on_bps_arr)), 3),
        gross_excess_bps=round(float(np.mean(gross_bps_arr)), 3),
        mean_cost_1x_bps=round(float(np.mean(cost_bps_arr)), 3),
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


def _ny_minute_ns(d: date, hh: int, mm: int) -> int:
    dt = datetime.combine(d, dtime(hh, mm, 0), tzinfo=NY_TZ)
    return int(dt.timestamp() * 1_000_000_000)


def load_local_intraday_prewall_panel(
    *,
    years: tuple[int, ...] = (2024, 2025, 2026),
    universe_root: Path | None = None,
    bars_1min_root: Path | None = None,
    public_tables_root: Path | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Scan pre-wall `bars-1min/<day>` (`<= 2026-10-15` ONLY) via DuckDB and join to `daily_raw` + `daily_split`."""
    u_root = universe_root or (Path.home() / "Documents" / "trading-sota" / "data" / "private" / "universe")
    b_root = bars_1min_root or (Path.home() / "Documents" / "market-data" / "alpaca-sip" / "raw" / "bars-1min")
    p_root = public_tables_root or (Path.home() / "Documents" / "market-data" / "public" / "tables")

    wall_iso = STUDY_WALL_DATE.isoformat()
    sec_symbols = pl.read_parquet(p_root / "sec_symbols.parquet")
    sec_filings = pl.read_parquet(p_root / "sec_filings.parquet").filter(pl.col("filed").str.slice(0, 10) <= wall_iso)
    op_syms = (
        sec_symbols.filter((pl.col("entity_type") == "operating") & pl.col("symbol").str.contains(r"^[A-Z]{1,4}$"))
        .select("symbol")
        .unique()
    )

    daily_frames: list[pl.DataFrame] = []
    for yr in years:
        raw_df = (
            pl.read_csv(u_root / str(yr) / "daily_raw.csv.gz", columns=["symbol", "ts_utc", "open", "close", "volume"])
            .with_columns(pl.col("ts_utc").str.slice(0, 10).alias("day_str"))
            .filter(pl.col("day_str") <= wall_iso)
            .join(op_syms, on="symbol", how="inner")
            .select(
                [
                    pl.col("symbol"),
                    pl.col("day_str").str.to_date().alias("trade_date"),
                    pl.col("open").cast(pl.Float64).alias("raw_open"),
                    pl.col("close").cast(pl.Float64).alias("raw_close"),
                    pl.col("volume").cast(pl.Float64).alias("raw_volume"),
                ]
            )
        )
        spl_df = (
            pl.read_csv(
                u_root / str(yr) / "daily_split.csv.gz", columns=["symbol", "ts_utc", "open", "close", "volume"]
            )
            .with_columns(pl.col("ts_utc").str.slice(0, 10).alias("day_str"))
            .filter(pl.col("day_str") <= wall_iso)
            .join(op_syms, on="symbol", how="inner")
            .select(
                [
                    pl.col("symbol"),
                    pl.col("day_str").str.to_date().alias("trade_date"),
                    pl.col("open").cast(pl.Float64),
                    pl.col("close").cast(pl.Float64),
                    pl.col("volume").cast(pl.Float64),
                ]
            )
        )
        daily_frames.append(spl_df.join(raw_df, on=["symbol", "trade_date"], how="inner"))

    daily_all = pl.concat(daily_frames, how="vertical").unique(subset=["symbol", "trade_date"], keep="last")

    # Pre-identify which (trade_date, symbol) rows are liquid operating candidates so DuckDB filters early!
    cand_dates_df = (
        daily_all.sort(["symbol", "trade_date"])
        .with_columns(
            [
                (pl.col("raw_close") * pl.col("raw_volume")).alias("raw_dv"),
                pl.col("raw_close").shift(1).over("symbol").alias("prev_rc"),
                pl.col("close").shift(1).over("symbol").alias("prev_sc"),
                pl.col("close")
                .shift(1)
                .rolling_mean(window_size=50, min_samples=50)
                .over("symbol")
                .alias("prev_sma50"),
                pl.col("raw_open").shift(-1).over("symbol").alias("next_ro"),
            ]
        )
        .with_columns(
            pl.col("raw_dv").shift(1).rolling_median(window_size=20, min_samples=20).over("symbol").alias("adv20")
        )
        .filter(
            (pl.col("prev_rc") >= 5.0)
            & (pl.col("adv20") >= 5_000_000.0)
            & (pl.col("prev_sc") > pl.col("prev_sma50"))
            & pl.col("next_ro").is_finite()
        )
        .select(["trade_date", "symbol"])
    )
    active_days = sorted(cand_dates_df["trade_date"].unique().to_list())
    cand_syms = sorted(cand_dates_df["symbol"].unique().to_list())

    # Scan strictly pre-wall bars-1min/<day> directories via DuckDB (batched in 35-day chunks for low peak RSS).
    con = duckdb.connect(":memory:")
    con.execute("PRAGMA threads=8")
    con.register("op_syms_tbl", pl.DataFrame({"symbol": cand_syms}))

    intraday_chunks: list[pl.DataFrame] = []
    for d in active_days:
        d_iso = d.isoformat()
        enforce_prewall_cutoff(d)
        day_dir = b_root / d_iso
        if not day_dir.is_dir():
            continue
        pfiles = [str(p) for p in sorted(day_dir.glob("*.parquet"))]
        if not pfiles:
            continue
        ns_0930 = _ny_minute_ns(d, 9, 30)
        ns_1029 = _ny_minute_ns(d, 10, 29)
        ns_1030 = _ny_minute_ns(d, 10, 30)
        ns_1034 = _ny_minute_ns(d, 10, 34)

        rows = con.execute(
            """
            SELECT
                b.symbol,
                arg_min(b.o, b.t_ns) FILTER (WHERE b.t_ns BETWEEN ? AND ?) AS open_0930,
                max(b.h) FILTER (WHERE b.t_ns BETWEEN ? AND ?) AS high_0930_1029,
                min(b.l) FILTER (WHERE b.t_ns BETWEEN ? AND ?) AS low_0930_1029,
                arg_max(b.c, b.t_ns) FILTER (WHERE b.t_ns BETWEEN ? AND ?) AS close_1029,
                sum(b.v) FILTER (WHERE b.t_ns BETWEEN ? AND ?) AS vol_0930_1029,
                arg_min(b.o, b.t_ns) FILTER (WHERE b.t_ns BETWEEN ? AND ?) AS open_1030
            FROM read_parquet(?) b
            SEMI JOIN op_syms_tbl s ON b.symbol = s.symbol
            WHERE b.t_ns BETWEEN ? AND ?
            GROUP BY b.symbol
            """,
            [
                ns_0930,
                ns_1029,
                ns_0930,
                ns_1029,
                ns_0930,
                ns_1029,
                ns_0930,
                ns_1029,
                ns_0930,
                ns_1029,
                ns_1030,
                ns_1034,
                pfiles,
                ns_0930,
                ns_1034,
            ],
        ).fetchall()
        if rows:
            day_df = pl.DataFrame(
                rows,
                schema={
                    "symbol": pl.String,
                    "open_0930": pl.Float64,
                    "high_0930_1029": pl.Float64,
                    "low_0930_1029": pl.Float64,
                    "close_1029": pl.Float64,
                    "vol_0930_1029": pl.Float64,
                    "open_1030": pl.Float64,
                },
                orient="row",
            )
            intraday_chunks.append(day_df.with_columns(pl.lit(d).alias("trade_date")))

    con.close()
    if not intraday_chunks:
        raise ValueError("No pre-wall intraday bars found")
    intraday_all = pl.concat(intraday_chunks, how="vertical")
    joined = daily_all.join(intraday_all, on=["symbol", "trade_date"], how="left")
    return joined, sec_symbols, sec_filings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pre-registered intraday 10:30 ET pre-wall (<=2026-10-15) study")
    parser.add_argument("--trials-n", type=int, default=78)
    parser.add_argument("--hypothesis-id", type=str, default="H04_PREWALL_INTRADAY_1030_IGNITION_TO_NEXTOPEN")
    parser.add_argument("--out-json", type=str, default="")
    args = parser.parse_args()

    joined_df, sec_symbols_df, sec_filings_df = load_local_intraday_prewall_panel()
    res = evaluate_intraday_1030_ignition_panel(
        joined_df,
        sec_symbols_df,
        sec_filings_df,
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
