"""Pre-Wall (`<= 2026-10-15`) Whole-Market Microstructure & Point-in-Time SEC Dilution Study (`T2`/`T4`/`L8`).

Implements the pre-registered `H02_PREWALL_PRETRAVEL_VOLSHOCK_SEC_SHIELD` pipeline (hardened per `sota-falsifier` audit):
1. Strict pre-wall truncation (`enforce_prewall_cutoff` <= `2026-10-15`) BEFORE any forward-return shift so neither
   features nor `t+3` labels can touch frozen post-wall (`>= 2026-10-16`) market data.
2. Zero forward-outcome censoring: never truncates realized crash/rally tails (`FLYE` `-92%` retained); excludes only
   split-ex-date straddlers (`adj_factor[t+3] != adj_factor[t]`).
3. Point-in-time backward `join_asof` against `sec_filings.parquet` (`424B5`, `424B3`, `S-3`, `S-3/A`, `S-1`, `S-1/A`)
   plus explicit overnight gap (`close[t] -> open[t+1]`) vs. 3-day RTH (`open[t+1] -> close[t+3]`) excess decomposition.
4. True 1/3-tranche daily mark-to-market (`leg1` on `t+1`, `leg2` on `t+2`, `leg3` on `t+3`) avoiding `MA(4)` overlapping-sum
   Sharpe inflation, `skfolio` 5-path recombined `CombinatorialPurgedCV` (`get_path_ids()`), `statsmodels` date-clustered SE,
   and native-frequency `ml4t-diagnostic` Deflated Sharpe Ratio (`DSR`).
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm
from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio_from_statistics
from skfolio.model_selection import CombinatorialPurgedCV

from agy_sota.invariants import (
    STUDY_WALL_DATE,
    bps_to_ratio,
    enforce_prewall_cutoff,
    hlz_dynamic_t_hurdle,
    ratio_to_bps,
)

DILUTION_FORMS: tuple[str, ...] = ("424B5", "424B3", "S-3", "S-3/A", "S-1", "S-1/A")
TICKET_NOTIONAL_USD: float = 25_000.0
BASE_COST_1X_BPS: float = 10.0


@dataclass(frozen=True, slots=True)
class SubperiodMetric:
    year: int
    events: int
    distinct_dates: int
    mean_net_1x_bps: float
    mean_net_2x_bps: float


@dataclass(frozen=True, slots=True)
class PrewallStudyResult:
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
    overnight_gap_excess_bps: float
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


def _date_clustered_mean_tstat(values_bps: np.ndarray, cluster_dates: np.ndarray) -> tuple[float, float, float]:
    """Compute sample mean, date-clustered standard error, and t-statistic via `statsmodels`."""
    if values_bps.size < 4 or np.unique(cluster_dates).size < 2:
        return (float(np.mean(values_bps)) if values_bps.size else 0.0, float("nan"), 0.0)
    exog = np.ones((values_bps.size, 1), dtype=np.float64)
    fit = sm.OLS(values_bps.astype(np.float64), exog).fit(
        cov_type="cluster",
        cov_kwds={"groups": cluster_dates},
    )
    mean_bps = float(fit.params[0])
    se_bps = float(fit.bse[0])
    t_stat = float(fit.tvalues[0]) if math.isfinite(float(fit.tvalues[0])) else 0.0
    return mean_bps, se_bps, t_stat


def _sample_moments(arr: np.ndarray) -> tuple[float, float, float]:
    """Return `(skewness, fisher_excess_kurtosis, lag1_autocorr)` on finite 1D returns."""
    n = arr.size
    if n < 8:
        return 0.0, 0.0, 0.0
    centered = arr - float(np.mean(arr))
    std = float(np.std(arr, ddof=1))
    if std <= 1e-12:
        return 0.0, 0.0, 0.0
    z = centered / std
    skew = float(np.mean(z**3))
    ex_kurt = float(np.mean(z**4) - 3.0)
    ac1 = float(np.corrcoef(arr[:-1], arr[1:])[0, 1]) if n >= 3 else 0.0
    if not math.isfinite(ac1):
        ac1 = 0.0
    return skew, ex_kurt, ac1


def _build_true_daily_mtm_series(cohort_df: pl.DataFrame, all_sessions: pl.DataFrame) -> np.ndarray:
    """Construct un-smoothed 1/3-tranche daily MTM return series (`leg1` on `d-1`, `leg2` on `d-2`, `leg3` on `d-3`)."""
    if cohort_df.is_empty():
        return np.zeros(all_sessions.height, dtype=np.float64)
    by_day = (
        cohort_df.group_by("trade_date")
        .agg(
            [
                pl.col("leg1_net_1x").mean().alias("m_leg1"),
                pl.col("leg2_excess").mean().alias("m_leg2"),
                pl.col("leg3_excess").mean().alias("m_leg3"),
            ]
        )
        .sort("trade_date")
    )
    joined = all_sessions.join(by_day, on="trade_date", how="left").with_columns(
        [
            pl.col("m_leg1").fill_null(0.0),
            pl.col("m_leg2").fill_null(0.0),
            pl.col("m_leg3").fill_null(0.0),
        ]
    )
    mtm = joined.select(
        (
            (
                pl.col("m_leg1").shift(1).fill_null(0.0)
                + pl.col("m_leg2").shift(2).fill_null(0.0)
                + pl.col("m_leg3").shift(3).fill_null(0.0)
            )
            / 3.0
        ).alias("daily_mtm_1x")
    )
    return np.asarray(mtm["daily_mtm_1x"].to_numpy(), dtype=np.float64)


def evaluate_prewall_volshock_sec_shield(
    daily_df: pl.DataFrame,
    sec_symbols_df: pl.DataFrame,
    sec_filings_df: pl.DataFrame,
    *,
    hypothesis_id: str = "H02_PREWALL_PRETRAVEL_VOLSHOCK_SEC_SHIELD",
    cumulative_trials_n: int = 3,
    dilution_lookback_days: int = 90,
) -> PrewallStudyResult:
    """Evaluate pre-registered Pre-Travel Volume-Shock + Point-in-Time SEC Dilution Shield (`<= 2026-10-15`)."""
    if daily_df.is_empty():
        raise ValueError("daily_df cannot be empty")

    # 1. Hard Pre-Wall Gate BEFORE any rolling or forward-shift computation.
    max_input_date = daily_df.select(pl.col("trade_date").max()).item()
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
        daily_df.filter(
            (pl.col("trade_date") <= pl.lit(STUDY_WALL_DATE))
            & (pl.col("open") > 0.0)
            & (pl.col("high") > 0.0)
            & (pl.col("low") > 0.0)
            & (pl.col("close") > 0.0)
            & (pl.col("raw_close") > 0.0)
            & (pl.col("volume") > 0.0)
        )
        .join(operating.select("symbol"), on="symbol", how="inner")
        .sort(["symbol", "trade_date"])
    )

    # 2. Causal trailing features on [..t] + 1-day MTM legs across [t+1..t+3] + split-factor straddle check.
    panel = panel.with_columns(
        [
            (pl.col("close") / pl.col("raw_close")).alias("adj_factor"),
            (pl.col("raw_close") * pl.col("raw_volume")).alias("raw_dollar_vol"),
            (pl.col("close") / pl.col("close").shift(1).over("symbol") - 1.0).alias("ret_1d"),
            pl.col("volume").shift(1).rolling_mean(window_size=20, min_samples=20).over("symbol").alias("vol_ma20"),
            pl.col("close").rolling_mean(window_size=50, min_samples=50).over("symbol").alias("sma_50"),
            pl.col("open").shift(-1).over("symbol").alias("open_t1"),
            pl.col("close").shift(-1).over("symbol").alias("close_t1"),
            pl.col("close").shift(-2).over("symbol").alias("close_t2"),
            pl.col("close").shift(-3).over("symbol").alias("close_t3"),
            pl.col("raw_close").shift(-3).over("symbol").alias("raw_close_t3"),
        ]
    ).with_columns(
        [
            pl.col("raw_dollar_vol")
            .shift(1)
            .rolling_median(window_size=20, min_samples=20)
            .over("symbol")
            .alias("adv_20d_usd"),
            pl.col("ret_1d").rolling_std(window_size=20, min_samples=20).over("symbol").alias("sigma_20d"),
            (pl.col("volume") / pl.col("vol_ma20")).alias("rvol_20d"),
            ((pl.col("close") - pl.col("low")) / pl.max_horizontal(pl.col("high") - pl.col("low"), pl.lit(1e-9))).alias(
                "close_pos"
            ),
            (pl.col("open_t1") / pl.col("close") - 1.0).alias("overnight_gap_ret"),
            (pl.col("close_t1") / pl.col("open_t1") - 1.0).alias("leg1_ret"),
            (pl.col("close_t2") / pl.col("close_t1") - 1.0).alias("leg2_ret"),
            (pl.col("close_t3") / pl.col("close_t2") - 1.0).alias("leg3_ret"),
            (pl.col("close_t3") / pl.col("open_t1") - 1.0).alias("fwd_ret_3d"),
            ((pl.col("close_t3") / pl.col("raw_close_t3")) / pl.col("adj_factor") - 1.0).abs().alias("split_drift"),
        ]
    )

    # Zero forward-outcome censoring: filter strictly on ex-ante liquidity + split-factor invariance across [t..t+3].
    liquid = panel.filter(
        (pl.col("raw_close") >= 5.0)
        & (pl.col("adv_20d_usd") >= 5_000_000.0)
        & pl.col("rvol_20d").is_finite()
        & pl.col("sma_50").is_finite()
        & pl.col("sigma_20d").is_finite()
        & pl.col("fwd_ret_3d").is_finite()
        & (pl.col("split_drift") < 1e-4)
    ).sort(["symbol", "trade_date"])

    if liquid.is_empty():
        raise ValueError("Liquid pre-wall operating panel is empty after filters")

    # 3. Point-in-Time SEC Dilution Shield via backward asof join (filed_date <= trade_date).
    if dilution_pit.height > 0:
        liquid = liquid.join_asof(
            dilution_pit,
            left_on="trade_date",
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

    # 4. Date-demeaned excess returns (overnight + daily legs + 3d total) & 1x/2x Almgren-Chriss impact cost.
    base_1x_ratio = bps_to_ratio(BASE_COST_1X_BPS)
    liquid = (
        liquid.with_columns(
            [
                pl.col("overnight_gap_ret").mean().over("trade_date").alias("univ_overnight_ret"),
                pl.col("leg1_ret").mean().over("trade_date").alias("univ_leg1_ret"),
                pl.col("leg2_ret").mean().over("trade_date").alias("univ_leg2_ret"),
                pl.col("leg3_ret").mean().over("trade_date").alias("univ_leg3_ret"),
                pl.col("fwd_ret_3d").mean().over("trade_date").alias("univ_fwd_ret_3d"),
                (
                    pl.lit(base_1x_ratio)
                    + 0.10 * pl.col("sigma_20d") * (pl.lit(TICKET_NOTIONAL_USD) / pl.col("adv_20d_usd")).sqrt()
                ).alias("cost_1x_ratio"),
            ]
        )
        .with_columns(
            [
                (pl.col("overnight_gap_ret") - pl.col("univ_overnight_ret")).alias("overnight_excess_ret"),
                (pl.col("leg1_ret") - pl.col("univ_leg1_ret") - pl.col("cost_1x_ratio")).alias("leg1_net_1x"),
                (pl.col("leg2_ret") - pl.col("univ_leg2_ret")).alias("leg2_excess"),
                (pl.col("leg3_ret") - pl.col("univ_leg3_ret")).alias("leg3_excess"),
                (pl.col("fwd_ret_3d") - pl.col("univ_fwd_ret_3d")).alias("gross_excess_ret"),
            ]
        )
        .with_columns(
            [
                (pl.col("gross_excess_ret") - pl.col("cost_1x_ratio")).alias("net_excess_1x"),
                (pl.col("gross_excess_ret") - 2.0 * pl.col("cost_1x_ratio")).alias("net_excess_2x"),
                (
                    (pl.col("rvol_20d") >= 2.5)
                    & (pl.col("close_pos") >= 0.75)
                    & (pl.col("ret_1d") >= 0.005)
                    & (pl.col("ret_1d") <= 0.080)
                    & (pl.col("close") > pl.col("sma_50"))
                ).alias("volshock_ignition"),
            ]
        )
    )

    all_ignitions = liquid.filter(pl.col("volshock_ignition")).sort(["trade_date", "symbol"])
    shielded = all_ignitions.filter(~pl.col("recent_dilution_90d"))
    exposed = all_ignitions.filter(pl.col("recent_dilution_90d"))

    t_hurdle = hlz_dynamic_t_hurdle(cumulative_trials_n)
    min_dt = str(liquid.select(pl.col("trade_date").min()).item())
    max_dt = str(liquid.select(pl.col("trade_date").max()).item())

    if shielded.height == 0:
        return PrewallStudyResult(
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
            overnight_gap_excess_bps=0.0,
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

    overnight_bps_arr = np.asarray(shielded["overnight_excess_ret"].to_numpy(), dtype=np.float64) * 10_000.0
    gross_bps_arr = np.asarray(shielded["gross_excess_ret"].to_numpy(), dtype=np.float64) * 10_000.0
    cost_1x_bps_arr = np.asarray(shielded["cost_1x_ratio"].to_numpy(), dtype=np.float64) * 10_000.0
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

    # 5. True 1/3-tranche daily MTM return series + empirical cross-arm trial variance.
    all_sessions = liquid.select("trade_date").unique().sort("trade_date")
    daily_rets = _build_true_daily_mtm_series(shielded, all_sessions)
    exposed_daily = _build_true_daily_mtm_series(exposed, all_sessions)
    unshielded_daily = _build_true_daily_mtm_series(all_ignitions, all_sessions)

    def _native_sr(arr: np.ndarray) -> float:
        sd = float(np.std(arr, ddof=1)) if arr.size > 2 else 0.0
        return float(np.mean(arr) / sd) if sd > 1e-12 else 0.0

    n_days = int(daily_rets.size)
    sr_native = _native_sr(daily_rets)
    sr_ann = sr_native * math.sqrt(252.0)

    arm_srs = [sr_native, _native_sr(exposed_daily), _native_sr(unshielded_daily)]
    emp_var = float(np.var(arm_srs, ddof=1)) if len(arm_srs) >= 2 else 0.0
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

    # 6. skfolio 5-path recombined CombinatorialPurgedCV (purged_size=3, embargo_size=3).
    cpcv_sharpes: list[float] = []
    if n_days >= 60:
        cv = CombinatorialPurgedCV(n_folds=6, n_test_folds=2, purged_size=3, embargo_size=3)
        dummy_x = daily_rets.reshape(-1, 1)
        splits = list(cv.split(dummy_x))
        path_ids = cv.get_path_ids()
        n_paths = int(path_ids.max()) + 1
        for pid in range(n_paths):
            path_segments: list[np.ndarray] = []
            for s_idx, (train_idx, test_folds) in enumerate(splits):
                # Enforce purged/embargoed train-split check (verifies non-empty purged training set)
                if train_idx.size == 0:
                    continue
                for fold_pos, fold_indices in enumerate(test_folds):
                    if int(path_ids[s_idx, fold_pos]) == pid:
                        path_segments.append(np.asarray(fold_indices, dtype=int))
            if path_segments:
                full_oos_idx = np.sort(np.concatenate(path_segments))
                path_r = daily_rets[full_oos_idx]
                cpcv_sharpes.append(_native_sr(path_r) * math.sqrt(252.0))

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

    return PrewallStudyResult(
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
        overnight_gap_excess_bps=round(float(np.mean(overnight_bps_arr)), 3),
        gross_excess_bps=round(float(np.mean(gross_bps_arr)), 3),
        mean_cost_1x_bps=round(float(np.mean(cost_1x_bps_arr)), 3),
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


def load_local_prewall_panel(
    *,
    years: tuple[int, ...] = (2024, 2025, 2026),
    universe_root: Path | None = None,
    public_tables_root: Path | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Load survivorship-free whole-market `daily_raw` + `daily_split` (`<= 2026-10-15`) and SEC public tables."""
    u_root = universe_root or (Path.home() / "Documents" / "trading-sota" / "data" / "private" / "universe")
    p_root = public_tables_root or (Path.home() / "Documents" / "market-data" / "public" / "tables")

    frames: list[pl.DataFrame] = []
    wall_iso = STUDY_WALL_DATE.isoformat()
    for yr in years:
        raw_p = u_root / str(yr) / "daily_raw.csv.gz"
        spl_p = u_root / str(yr) / "daily_split.csv.gz"
        if not raw_p.is_file() or not spl_p.is_file():
            raise FileNotFoundError(f"Missing universe year {yr} files under {u_root}")

        raw_df = (
            pl.read_csv(raw_p, columns=["symbol", "ts_utc", "close", "volume"])
            .with_columns(pl.col("ts_utc").str.slice(0, 10).alias("day_str"))
            .filter(pl.col("day_str") <= wall_iso)
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
            pl.read_csv(spl_p, columns=["symbol", "ts_utc", "open", "high", "low", "close", "volume"])
            .with_columns(pl.col("ts_utc").str.slice(0, 10).alias("day_str"))
            .filter(pl.col("day_str") <= wall_iso)
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
        frames.append(spl_df.join(raw_df, on=["symbol", "trade_date"], how="inner"))

    combined = pl.concat(frames, how="vertical").unique(subset=["symbol", "trade_date"], keep="last")
    sec_symbols = pl.read_parquet(p_root / "sec_symbols.parquet")
    sec_filings = pl.read_parquet(p_root / "sec_filings.parquet").filter(pl.col("filed").str.slice(0, 10) <= wall_iso)
    return combined, sec_symbols, sec_filings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pre-registered pre-wall (<=2026-10-15) SEC-shielded study")
    parser.add_argument("--trials-n", type=int, default=3, help="Cumulative trial multiplicity N on peer bus")
    parser.add_argument("--hypothesis-id", type=str, default="H02_PREWALL_PRETRAVEL_VOLSHOCK_SEC_SHIELD")
    parser.add_argument("--out-json", type=str, default="", help="Optional output JSON path")
    args = parser.parse_args()

    daily_df, sec_symbols_df, sec_filings_df = load_local_prewall_panel()
    res = evaluate_prewall_volshock_sec_shield(
        daily_df,
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
