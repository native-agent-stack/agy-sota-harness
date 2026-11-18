"""Pre-Wall (`<= 2026-10-15`) Two-Stage Hybrid Entry × 50/50 Asymmetric Runner Convexity Study (`H089`).

Implements pre-registered Trial #89 (`H089_TWO_STAGE_HYBRID_ENTRY_X_ASYMMETRIC_RUNNER_CONVEXITY`,
`spec_sha256 = 0dffdb5d97cd5ef8d8964887d3b7f93f32fc6052540d36b081db79b2f5f09447`, `t*(89) = 4.1709`):
1. Resolves H088 Bottleneck #1 (`-46.37 bps` passive runaway exclusion):
   - Tranche P (`50%`, `USD 12,500`): `hftbacktest::RiskAdverseQueueModel` (`bs * 100.0` shares) passive
     `bp_entry` limit in `[ns_entry, ns_entry + 120s)`.
   - Tranche J (`50%`, `USD 12,500`): fills passively at `bp_entry` if full `USD 25,000` queue depletes in
     `[ns_entry, ns_entry + 180s)`, OR joins firm NBBO `ap_120s` (`spread <= 35 bps`) when the passive bid
     went unfilled and price broke higher (`ap_120s > ap_entry`).
2. Resolves H088 Bottleneck #2 (`97.8%` single-tranche `+60 bps` Gain-Lock right-tail censoring):
   - Downside Cap (`100%` of filled shares): `180 bps` (`<= ADR-0022 200 bps`) `ADVERSE_STOP_FIRST` stop.
   - Core Tranche (`50%`): arms Gain-Lock at `+150 bps` (`65%` MFE retention), banking mid-day impulse profit.
   - Runner Tranche (`50%`): holds uncapped to `15:55` ET RTH close (`raw_close[t]`), ratcheting its stop
     from `-180 bps` to `+10 bps` breakeven once MFE reaches `+180 bps`, preserving positive right-tail skewness.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
from ml4t.diagnostic.evaluation.stats import deflated_sharpe_ratio_from_statistics
from skfolio.model_selection import CombinatorialPurgedCV

from agy_sota.invariants import (
    STUDY_WALL_DATE,
    enforce_prewall_cutoff,
    hlz_dynamic_t_hurdle,
)
from agy_sota.prewall_study import (
    DILUTION_FORMS,
    TICKET_NOTIONAL_USD,
    SubperiodMetric,
    _date_clustered_mean_tstat,
    _sample_moments,
)

NY_TZ = ZoneInfo("America/New_York")

H089_HYPOTHESIS_ID = "H089_TWO_STAGE_HYBRID_ENTRY_X_ASYMMETRIC_RUNNER_CONVEXITY"
H089_TRIAL_N = 89
H089_SPEC_SHA256 = "0dffdb5d97cd5ef8d8964887d3b7f93f32fc6052540d36b081db79b2f5f09447"

CTA_UTP_LOT_SHARES = 100.0
HARD_INITIAL_STOP_BPS = 180.0
HARD_INITIAL_STOP_RATIO = 0.0180
CORE_GAIN_LOCK_ARM_BPS = 150.0
CORE_MFE_RETENTION = 0.65
RUNNER_BE_ARM_BPS = 180.0
RUNNER_BE_FLOOR_BPS = 10.0
EXIT_HALF_SPREAD_1X_BPS = 5.0


@dataclass(frozen=True, slots=True)
class QuoteNs:
    ts_ns: int
    bid_px: float
    bid_lots: float
    ask_px: float


@dataclass(frozen=True, slots=True)
class TradeNs:
    ts_ns: int
    price_px: float
    size_shares: float


@dataclass(frozen=True, slots=True)
class Bar1m:
    ts_ns: int
    open_px: float
    high_px: float
    low_px: float
    close_px: float


@dataclass(frozen=True, slots=True)
class HybridEntryResult:
    participated: bool
    mode: str  # "passive_100pct" | "passive_50pct" | "runaway_join_50pct" | "no_fill"
    weight_fraction: float
    avg_fill_px: float
    fill_ts_ns: int


@dataclass(frozen=True, slots=True)
class DualTrancheExitResult:
    core_exit_reason: str
    runner_exit_reason: str
    core_gross_bps: float
    runner_gross_bps: float
    combined_gross_bps: float
    combined_net_1x_bps: float
    combined_net_2x_bps: float


@dataclass(frozen=True, slots=True)
class H089StudyResult:
    hypothesis_id: str
    spec_sha256: str
    evaluated_at_utc: str
    sample_min_date: str
    sample_max_date: str
    cumulative_trials_n: int
    required_hlz_t_hurdle: float
    liquid_orb_events_total: int
    shielded_ignition_signals: int
    participated_events_count: int
    participation_rate_pct: float
    entry_mode_counts: dict[str, int]
    runner_reached_close_count: int
    runner_reached_close_pct: float
    distinct_dates: int
    mean_entry_spread_bps: float
    gross_excess_bps: float
    mean_exit_cost_1x_bps: float
    net_return_1x_bps: float
    net_return_2x_bps: float
    net_1x_without_best_day_bps: float
    h088_single_tranche_net_1x_bps: float
    convexity_lift_vs_h088_bps: float
    cvar95_bps: float
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


def simulate_two_stage_hybrid_entry(
    *,
    ns_entry: int,
    bp_entry: float,
    bs_entry: float,
    ap_entry: float,
    quotes: Sequence[QuoteNs],
    trades: Sequence[TradeNs],
    tick_eps: float = 1e-6,
) -> HybridEntryResult:
    """Simulate 50% passive `RiskAdverseQueueModel` (`120s`) + 50% full queue (`180s`) or `120s` runaway ask join."""
    if not (math.isfinite(bp_entry) and math.isfinite(bs_entry) and math.isfinite(ap_entry)) or bp_entry <= 0.0:
        raise ValueError("Invalid hybrid entry quote inputs")

    half_qty = max(1.0, float(round((0.5 * TICKET_NOTIONAL_USD) / bp_entry)))
    full_qty = 2.0 * half_qty
    front_q = bs_entry * CTA_UTP_LOT_SHARES
    ns_120 = ns_entry + 120_000_000_000
    ns_180 = ns_entry + 180_000_000_000

    events: list[tuple[int, int, float, float]] = []
    for qt in quotes:
        if qt.ts_ns <= ns_180:
            events.append((qt.ts_ns, 0, qt.bid_px, qt.bid_lots * CTA_UTP_LOT_SHARES))
            events.append((qt.ts_ns, 1, qt.ask_px, -1.0))
    for tr in trades:
        if tr.ts_ns <= ns_180:
            events.append((tr.ts_ns, 2, tr.price_px, tr.size_shares))
    events.sort(key=lambda x: (x[0], x[1]))

    half_filled_ts: int | None = None
    full_filled_ts: int | None = None

    for ts_ns, kind, px, sz_sh in events:
        if kind == 1:
            if 0.0 < px < bp_entry - tick_eps:
                if half_filled_ts is None and ts_ns <= ns_120:
                    half_filled_ts = ts_ns
                if half_filled_ts is not None:
                    full_filled_ts = ts_ns
                    break
        elif kind == 0:
            if abs(px - bp_entry) <= tick_eps:
                front_q = min(front_q, max(0.0, sz_sh))
        else:
            if px < bp_entry - tick_eps:
                if half_filled_ts is None and ts_ns <= ns_120:
                    half_filled_ts = ts_ns
                if half_filled_ts is not None:
                    full_filled_ts = ts_ns
                    break
            elif abs(px - bp_entry) <= tick_eps:
                front_q -= sz_sh
                if half_filled_ts is None and ts_ns <= ns_120 and front_q + tick_eps <= -half_qty:
                    half_filled_ts = ts_ns
                if half_filled_ts is not None and front_q + tick_eps <= -full_qty:
                    full_filled_ts = ts_ns
                    break

    if full_filled_ts is not None:
        return HybridEntryResult(
            participated=True,
            mode="passive_100pct",
            weight_fraction=1.0,
            avg_fill_px=bp_entry,
            fill_ts_ns=full_filled_ts,
        )
    if half_filled_ts is not None:
        return HybridEntryResult(
            participated=True,
            mode="passive_50pct",
            weight_fraction=0.5,
            avg_fill_px=bp_entry,
            fill_ts_ns=half_filled_ts,
        )

    # Unfilled passive bid after 120s: check firm NBBO quote at ns_120 for runaway breakout join
    q_120 = [qt for qt in quotes if qt.ts_ns <= ns_120 and qt.bid_px > 0.0 and qt.ask_px >= qt.bid_px]
    if q_120:
        last_q = q_120[-1]
        mid_120 = 0.5 * (last_q.bid_px + last_q.ask_px)
        spr_120_bps = ((last_q.ask_px - last_q.bid_px) / mid_120) * 10_000.0 if mid_120 > 0.0 else 999.0
        if last_q.ask_px > ap_entry + tick_eps and spr_120_bps <= 35.0:
            return HybridEntryResult(
                participated=True,
                mode="runaway_join_50pct",
                weight_fraction=0.5,
                avg_fill_px=last_q.ask_px,
                fill_ts_ns=last_q.ts_ns,
            )

    return HybridEntryResult(
        participated=False,
        mode="no_fill",
        weight_fraction=0.0,
        avg_fill_px=0.0,
        fill_ts_ns=0,
    )


def replay_dual_tranche_runner_convexity(
    *,
    entry_px: float,
    fill_ts_ns: int,
    post_fill_quotes: Sequence[QuoteNs],
    intraday_bars: Sequence[Bar1m],
    close_px: float,
    exit_cost_1x_bps: float,
) -> DualTrancheExitResult:
    """Replay 50% Core (+150bps 65% MFE Gain-Lock) + 50% Uncapped 15:55 Runner (+10bps BE @ +180bps) under 180bps stop."""
    if (
        not (math.isfinite(entry_px) and math.isfinite(close_px) and math.isfinite(exit_cost_1x_bps))
        or entry_px <= 0.0
        or close_px <= 0.0
        or exit_cost_1x_bps < 0.0
    ):
        raise ValueError("Invalid replay_dual_tranche_runner_convexity inputs")

    hard_stop_px = entry_px * (1.0 - HARD_INITIAL_STOP_RATIO)
    core_stop_px = hard_stop_px
    runner_stop_px = hard_stop_px
    peak_px = entry_px

    core_open = True
    runner_open = True
    core_exit_px = close_px
    runner_exit_px = close_px
    core_reason = "core_close_1555"
    runner_reason = "runner_close_1555"
    last_ns = fill_ts_ns

    def _update_ratchets(cand_high_px: float) -> None:
        nonlocal peak_px, core_stop_px, runner_stop_px
        if cand_high_px <= peak_px:
            return
        peak_px = cand_high_px
        mfe_bps = ((peak_px - entry_px) / entry_px) * 10_000.0
        if core_open and mfe_bps >= CORE_GAIN_LOCK_ARM_BPS:
            locked_bps = mfe_bps * CORE_MFE_RETENTION
            core_stop_px = max(core_stop_px, entry_px * (1.0 + locked_bps / 10_000.0))
        if runner_open and mfe_bps >= RUNNER_BE_ARM_BPS:
            runner_stop_px = max(runner_stop_px, entry_px * (1.0 + RUNNER_BE_FLOOR_BPS / 10_000.0))

    # Phase A: Exact nanosecond firm NBBO bid quote sweep
    for qt in post_fill_quotes:
        if qt.ts_ns <= fill_ts_ns or qt.bid_px <= 0.0:
            continue
        last_ns = max(last_ns, qt.ts_ns)
        if core_open and qt.bid_px <= core_stop_px + 1e-9:
            core_exit_px = min(qt.bid_px, core_stop_px)
            core_reason = "core_gain_lock" if core_stop_px > hard_stop_px + 1e-9 else "hard_adverse_stop_180bps"
            core_open = False
        if runner_open and qt.bid_px <= runner_stop_px + 1e-9:
            runner_exit_px = min(qt.bid_px, runner_stop_px)
            runner_reason = "runner_breakeven_stop" if runner_stop_px > hard_stop_px + 1e-9 else "hard_adverse_stop_180bps"
            runner_open = False
        if not core_open and not runner_open:
            break
        _update_ratchets(qt.bid_px)

    # Phase B: Strictly pessimistic ADVERSE_STOP_FIRST 1m bar replay (check bar.low <= stop BEFORE bar.high ratchet)
    half_spr = EXIT_HALF_SPREAD_1X_BPS / 10_000.0
    final_close = close_px
    if core_open or runner_open:
        for bar in intraday_bars:
            if bar.ts_ns <= last_ns:
                continue
            final_close = bar.close_px
            if core_open and bar.low_px <= core_stop_px + 1e-9:
                core_exit_px = min(bar.open_px, core_stop_px)
                core_reason = "core_gain_lock" if core_stop_px > hard_stop_px + 1e-9 else "hard_adverse_stop_180bps"
                core_open = False
            if runner_open and bar.low_px <= runner_stop_px + 1e-9:
                runner_exit_px = min(bar.open_px, runner_stop_px)
                runner_reason = (
                    "runner_breakeven_stop" if runner_stop_px > hard_stop_px + 1e-9 else "hard_adverse_stop_180bps"
                )
                runner_open = False
            if not core_open and not runner_open:
                break
            _update_ratchets(bar.high_px * (1.0 - half_spr))

    if core_open:
        core_exit_px = final_close
    if runner_open:
        runner_exit_px = final_close

    core_gross_bps = ((core_exit_px / entry_px) - 1.0) * 10_000.0
    runner_gross_bps = ((runner_exit_px / entry_px) - 1.0) * 10_000.0
    comb_gross_bps = 0.5 * core_gross_bps + 0.5 * runner_gross_bps
    return DualTrancheExitResult(
        core_exit_reason=core_reason,
        runner_exit_reason=runner_reason,
        core_gross_bps=core_gross_bps,
        runner_gross_bps=runner_gross_bps,
        combined_gross_bps=comb_gross_bps,
        combined_net_1x_bps=comb_gross_bps - exit_cost_1x_bps,
        combined_net_2x_bps=comb_gross_bps - 2.0 * exit_cost_1x_bps,
    )


def _extract_single_h089_candidate(
    item: tuple[str, dt.date, str, Path, Path],
) -> dict[str, object] | None:
    sym, d_obj, hhmm, t_path, q_path = item
    try:
        hh, mm = int(hhmm[:2]), int(hhmm[2:])
        m_start_ns = int(dt.datetime.combine(d_obj, dt.time(hh, mm, 0), tzinfo=NY_TZ).timestamp() * 1_000_000_000)
        ns_entry = m_start_ns + 60_000_000_000
        ns_end = ns_entry + 180_000_000_000

        q_raw = pl.read_parquet(q_path, columns=["t_ns", "bp", "bs", "ap"])
        q_clean = (
            q_raw.filter((pl.col("bp") > 0.0) & (pl.col("ap") >= pl.col("bp")))
            .select(["t_ns", "bp", "bs", "ap"])
            .sort("t_ns")
        )
        if q_clean.is_empty():
            return None

        q_before = q_clean.filter(pl.col("t_ns") <= ns_entry).tail(1)
        if q_before.height == 0:
            q_before = q_clean.filter(
                (pl.col("t_ns") > ns_entry) & (pl.col("t_ns") <= ns_entry + 5_000_000_000)
            ).head(1)
        if q_before.height == 0:
            return None

        bp_entry = float(q_before["bp"][0])
        bs_entry = float(q_before["bs"][0])
        ap_entry = float(q_before["ap"][0])
        mid_entry = 0.5 * (bp_entry + ap_entry)
        if mid_entry <= 0.0:
            return None
        entry_spread_bps = ((ap_entry - bp_entry) / mid_entry) * 10_000.0

        t_raw = pl.read_parquet(t_path, columns=["t_ns", "x", "p", "s", "c", "u"])
        t_m = t_raw.filter(
            (pl.col("t_ns") >= m_start_ns)
            & (pl.col("t_ns") < ns_entry)
            & pl.col("u").is_null()
            & (pl.col("p") > 0.0)
            & (pl.col("s") > 0)
        ).sort("t_ns")
        if t_m.height < 5:
            return None

        q_m = q_clean.filter(pl.col("t_ns") < ns_entry).select(["t_ns", "bp", "ap"])
        if q_m.height == 0:
            return None

        matched = t_m.join_asof(q_m, on="t_ns", strategy="backward", check_sortedness=False).with_columns(
            (0.5 * (pl.col("bp") + pl.col("ap"))).alias("mid_q")
        )
        total_sh = float(matched["s"].sum())
        if total_sh <= 0.0:
            return None

        signed = matched.with_columns(
            pl.when(pl.col("p") > pl.col("mid_q") + 1e-6)
            .then(pl.lit(1.0))
            .when(pl.col("p") < pl.col("mid_q") - 1e-6)
            .then(pl.lit(-1.0))
            .otherwise(
                pl.when(pl.col("p").diff().fill_null(0.0) > 0.0)
                .then(pl.lit(1.0))
                .when(pl.col("p").diff().fill_null(0.0) < 0.0)
                .then(pl.lit(-1.0))
                .otherwise(pl.lit(0.0))
            )
            .alias("lr_sign")
        )
        ofi = float((signed["s"] * signed["lr_sign"]).sum()) / total_sh
        iso_buy_sh = float(signed.filter(pl.col("c").list.contains("F") & (pl.col("lr_sign") > 0.0))["s"].sum())
        iso_f_buy_share = iso_buy_sh / total_sh

        dark_d = signed.filter(pl.col("x") == "D")
        inst_dark_sh = 0.0
        for px_v, sz_v in zip(dark_d["p"].to_list(), dark_d["s"].to_list(), strict=False):
            cents_mod = (Decimal(str(px_v)) * Decimal("100")) % Decimal("1")
            if cents_mod == Decimal("0") or (Decimal("0.40") <= cents_mod <= Decimal("0.60")):
                inst_dark_sh += float(sz_v)
        bjzz_inst_dark_share = inst_dark_sh / total_sh

        t_post_df = t_raw.filter(
            (pl.col("t_ns") > ns_entry)
            & (pl.col("t_ns") <= ns_end)
            & pl.col("u").is_null()
            & (pl.col("p") > 0.0)
            & (pl.col("s") > 0)
        ).sort("t_ns")
        q_post_df = q_clean.filter((pl.col("t_ns") > ns_entry) & (pl.col("t_ns") <= ns_end)).sort("t_ns")

        post_trades = [
            TradeNs(ts_ns=int(t), price_px=float(p), size_shares=float(s))
            for t, p, s in zip(t_post_df["t_ns"].to_list(), t_post_df["p"].to_list(), t_post_df["s"].to_list(), strict=False)
        ]
        post_quotes = [
            QuoteNs(ts_ns=int(t), bid_px=float(bp), bid_lots=float(bs), ask_px=float(ap))
            for t, bp, bs, ap in zip(
                q_post_df["t_ns"].to_list(),
                q_post_df["bp"].to_list(),
                q_post_df["bs"].to_list(),
                q_post_df["ap"].to_list(),
                strict=False,
            )
        ]

        entry_res = simulate_two_stage_hybrid_entry(
            ns_entry=ns_entry,
            bp_entry=bp_entry,
            bs_entry=bs_entry,
            ap_entry=ap_entry,
            quotes=post_quotes,
            trades=post_trades,
        )
        rem_quotes = [qt for qt in post_quotes if qt.ts_ns > entry_res.fill_ts_ns] if entry_res.participated else []

        return {
            "symbol": sym,
            "trade_date": d_obj,
            "entry_hhmm": hhmm,
            "ns_entry": ns_entry,
            "mid_entry": mid_entry,
            "entry_spread_bps": entry_spread_bps,
            "ofi": ofi,
            "iso_f_buy_share": iso_f_buy_share,
            "bjzz_inst_dark_share": bjzz_inst_dark_share,
            "participated": entry_res.participated,
            "entry_mode": entry_res.mode,
            "weight_fraction": entry_res.weight_fraction,
            "avg_fill_px": entry_res.avg_fill_px,
            "fill_ts_ns": entry_res.fill_ts_ns,
            "post_fill_quotes": rem_quotes,
        }
    except Exception:
        return None


def run_local_h089_prewall_study(
    *,
    years: tuple[int, ...] = (2024, 2025, 2026),
    docs_root: Path | None = None,
) -> H089StudyResult:
    """Execute full pre-wall (`<= 2026-10-15`) H089 evaluation across 14,750 SIP pairs + bars-1min."""
    base_docs = docs_root or (Path.home() / "Documents")
    u_root = base_docs / "trading-sota" / "data" / "private" / "universe"
    sip_raw = base_docs / "market-data" / "alpaca-sip" / "raw"
    o_root = sip_raw / "published-orb"
    bars_root = sip_raw / "bars-1min"
    p_root = base_docs / "market-data" / "public" / "tables"

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
            pl.read_csv(u_root / str(yr) / "daily_split.csv.gz", columns=["symbol", "ts_utc", "close"])
            .with_columns(pl.col("ts_utc").str.slice(0, 10).alias("day_str"))
            .filter((pl.col("day_str") <= wall_iso) & pl.col("symbol").is_in(op_set))
            .select(
                [
                    pl.col("symbol"),
                    pl.col("day_str").str.to_date().alias("trade_date"),
                    pl.col("close").cast(pl.Float64).alias("split_close"),
                ]
            )
        )
        daily_frames.append(spl_df.join(raw_df, on=["symbol", "trade_date"], how="inner"))

    daily_df = (
        pl.concat(daily_frames, how="vertical")
        .unique(subset=["symbol", "trade_date"], keep="last")
        .sort(["symbol", "trade_date"])
        .with_columns(
            [
                (pl.col("raw_close") * pl.col("raw_volume")).alias("raw_dv"),
                (pl.col("split_close") / pl.col("split_close").shift(1).over("symbol") - 1.0).alias("ret_1d"),
                pl.col("raw_close").shift(1).over("symbol").alias("prev_raw_close"),
                pl.col("split_close").shift(1).over("symbol").alias("prev_split_close"),
                (pl.col("split_close") / pl.col("raw_close")).alias("adj_factor"),
            ]
        )
        .with_columns(
            [
                pl.col("raw_dv").shift(1).rolling_median(window_size=20, min_samples=20).over("symbol").alias("adv_20d_usd"),
                pl.col("ret_1d").shift(1).rolling_std(window_size=20, min_samples=20).over("symbol").alias("sigma_20d"),
                (((pl.col("prev_split_close") / pl.col("prev_raw_close")) / pl.col("adj_factor") - 1.0).abs()).alias(
                    "split_drift"
                ),
            ]
        )
    )

    work_items: list[tuple[str, dt.date, str, Path, Path]] = []
    trades_base = o_root / "trades"
    quotes_base = o_root / "quotes"
    for sym_dir in sorted(trades_base.iterdir()):
        if not sym_dir.is_dir() or sym_dir.name not in op_set:
            continue
        q_sym_dir = quotes_base / sym_dir.name
        if not q_sym_dir.is_dir():
            continue
        for tf in sorted(sym_dir.glob("*.parquet")):
            stem = tf.stem
            if len(stem) < 15 or stem[:10] > wall_iso:
                continue
            qf = q_sym_dir / tf.name
            if not qf.is_file():
                continue
            d_obj = dt.date.fromisoformat(stem[:10])
            enforce_prewall_cutoff(d_obj)
            work_items.append((sym_dir.name, d_obj, stem[11:15], tf, qf))

    with ThreadPoolExecutor(max_workers=10) as pool:
        raw_cands = [r for r in pool.map(_extract_single_h089_candidate, work_items) if r is not None]

    quotes_by_key: dict[tuple[str, dt.date, str], list[QuoteNs]] = {}
    clean_rows: list[dict[str, object]] = []
    for item_dict in raw_cands:
        key = (
            str(item_dict["symbol"]),
            cast(dt.date, item_dict["trade_date"]),
            str(item_dict["entry_hhmm"]),
        )
        quotes_by_key[key] = cast(list[QuoteNs], item_dict.pop("post_fill_quotes"))
        clean_rows.append(item_dict)

    orb_df = pl.DataFrame(clean_rows)

    dilution_pit = (
        sec_filings.filter(pl.col("form").is_in(DILUTION_FORMS))
        .join(sec_symbols.select(["cik", "symbol"]), on="cik", how="inner")
        .with_columns(pl.col("filed").str.slice(0, 10).str.to_date().alias("filed_date"))
        .select(["symbol", "filed_date"])
        .unique()
        .sort(["symbol", "filed_date"])
    )
    short_pit = (
        short_vol.with_columns(
            [
                pl.col("day").str.slice(0, 10).str.to_date().alias("sv_date"),
                (pl.col("short_volume").cast(pl.Float64) / pl.col("total_volume").cast(pl.Float64)).alias(
                    "regsho_short_ratio"
                ),
            ]
        )
        .filter(pl.col("total_volume") > 0)
        .select(["symbol", "sv_date", "regsho_short_ratio"])
        .unique(subset=["symbol", "sv_date"], keep="last")
        .sort(["symbol", "sv_date"])
    )

    panel = (
        orb_df.join(
            daily_df.select(
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
            & (pl.col("entry_spread_bps") > 0.0)
            & (pl.col("entry_spread_bps") <= 35.0)
        )
        .with_columns(pl.col("trade_date").dt.offset_by("-1d").alias("prior_cal_date"))
        .sort(["symbol", "prior_cal_date"])
    )

    panel = panel.join_asof(
        dilution_pit,
        left_on="prior_cal_date",
        right_on="filed_date",
        by="symbol",
        strategy="backward",
        check_sortedness=False,
    ).with_columns(
        (pl.col("filed_date").is_not_null() & ((pl.col("trade_date") - pl.col("filed_date")).dt.total_days() <= 90)).alias(
            "recent_dilution_90d"
        )
    )
    panel = panel.join_asof(
        short_pit,
        left_on="prior_cal_date",
        right_on="sv_date",
        by="symbol",
        strategy="backward",
        check_sortedness=False,
    ).with_columns(
        [
            pl.col("regsho_short_ratio").fill_null(0.0),
            (pl.col("raw_close") / pl.col("mid_entry") - 1.0).alias("mid_to_close_ret"),
        ]
    )
    panel = panel.with_columns(pl.col("mid_to_close_ret").mean().over("trade_date").alias("univ_orb_ret"))

    shielded = panel.filter(
        (pl.col("ofi") >= 0.10)
        & ((pl.col("iso_f_buy_share") >= 0.15) | (pl.col("bjzz_inst_dark_share") >= 0.12))
        & (pl.col("regsho_short_ratio") >= 0.45)
        & (~pl.col("recent_dilution_90d"))
    )
    part_df = shielded.filter(pl.col("participated")).sort(["trade_date", "symbol"])

    syms_by_date: dict[dt.date, set[str]] = {}
    for sym_v, dt_v in zip(part_df["symbol"].to_list(), part_df["trade_date"].to_list(), strict=False):
        syms_by_date.setdefault(dt_v, set()).add(str(sym_v))

    def _load_day_bars(
        item: tuple[dt.date, set[str]],
    ) -> tuple[dt.date, dict[str, list[tuple[int, float, float, float, float]]]]:
        d_val, sym_set = item
        day_dir = bars_root / d_val.isoformat()
        if not day_dir.is_dir():
            return d_val, {}
        rth_open_ns = int(dt.datetime.combine(d_val, dt.time(9, 30, 0), tzinfo=NY_TZ).timestamp() * 1_000_000_000)
        flatten_ns = int(dt.datetime.combine(d_val, dt.time(15, 54, 0), tzinfo=NY_TZ).timestamp() * 1_000_000_000)
        df_b = (
            pl.scan_parquet(str(day_dir / "*.parquet"))
            .filter(
                pl.col("symbol").is_in(list(sym_set))
                & (pl.col("t_ns") >= rth_open_ns)
                & (pl.col("t_ns") <= flatten_ns)
                & (pl.col("l") > 0.0)
            )
            .select(["symbol", "t_ns", "o", "h", "l", "c"])
            .collect()
            .sort(["symbol", "t_ns"])
        )
        grouped: dict[str, list[tuple[int, float, float, float, float]]] = {}
        for s_n, t_n, o_p, h_p, l_p, c_p in zip(
            df_b["symbol"].to_list(),
            df_b["t_ns"].to_list(),
            df_b["o"].to_list(),
            df_b["h"].to_list(),
            df_b["l"].to_list(),
            df_b["c"].to_list(),
            strict=False,
        ):
            grouped.setdefault(str(s_n), []).append((int(t_n), float(o_p), float(h_p), float(l_p), float(c_p)))
        return d_val, grouped

    bars_lookup: dict[tuple[str, dt.date], list[tuple[int, float, float, float, float]]] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        for d_val, sym_map in pool.map(_load_day_bars, list(syms_by_date.items())):
            for sym_k, bar_list in sym_map.items():
                bars_lookup[(sym_k, d_val)] = bar_list

    gross_ret_col: list[float] = []
    cost_1x_col: list[float] = []
    runner_close_flags: list[bool] = []

    for row in part_df.iter_rows(named=True):
        key_q = (str(row["symbol"]), row["trade_date"], str(row["entry_hhmm"]))
        key_b = (str(row["symbol"]), row["trade_date"])
        fill_ts_v = int(row["fill_ts_ns"])
        rem_q = quotes_by_key.get(key_q, [])
        handoff_ns = max((qt.ts_ns for qt in rem_q), default=fill_ts_v)
        post_bars = [
            Bar1m(ts_ns=t_n + 60_000_000_000, open_px=o_p, high_px=h_p, low_px=l_p, close_px=c_p)
            for (t_n, o_p, h_p, l_p, c_p) in bars_lookup.get(key_b, [])
            if t_n >= handoff_ns
        ]
        wf = float(row["weight_fraction"])
        cost_1x_bps = (
            EXIT_HALF_SPREAD_1X_BPS
            + 0.10
            * float(row["sigma_20d"])
            * math.sqrt((wf * TICKET_NOTIONAL_USD) / float(row["adv_20d_usd"]))
            * 10_000.0
        )
        ex = replay_dual_tranche_runner_convexity(
            entry_px=float(row["avg_fill_px"]),
            fill_ts_ns=fill_ts_v,
            post_fill_quotes=rem_q,
            intraday_bars=post_bars,
            close_px=float(row["raw_close"]),
            exit_cost_1x_bps=cost_1x_bps,
        )
        gross_ret_col.append(ex.combined_gross_bps / 10_000.0)
        cost_1x_col.append(cost_1x_bps / 10_000.0)
        runner_close_flags.append(ex.runner_exit_reason == "runner_close_1555")

    part_df = part_df.with_columns(
        [
            pl.Series("dual_gross_ret", gross_ret_col, dtype=pl.Float64),
            pl.Series("exit_cost_1x_ratio", cost_1x_col, dtype=pl.Float64),
            pl.Series("runner_reached_close", runner_close_flags, dtype=pl.Boolean),
        ]
    ).with_columns(
        [
            # Size-weighted excess return (50% legs scale exposure & variance proportionally)
            (pl.col("weight_fraction") * (pl.col("dual_gross_ret") - pl.col("univ_orb_ret"))).alias("gross_excess_ret"),
            (
                pl.col("weight_fraction")
                * (pl.col("dual_gross_ret") - pl.col("univ_orb_ret") - pl.col("exit_cost_1x_ratio"))
            ).alias("net_1x_ret"),
            (
                pl.col("weight_fraction")
                * (pl.col("dual_gross_ret") - pl.col("univ_orb_ret") - 2.0 * pl.col("exit_cost_1x_ratio"))
            ).alias("net_2x_ret"),
        ]
    )

    net_1x_bps_arr = np.asarray(part_df["net_1x_ret"].to_numpy(), dtype=np.float64) * 10_000.0
    net_2x_bps_arr = np.asarray(part_df["net_2x_ret"].to_numpy(), dtype=np.float64) * 10_000.0
    gross_bps_arr = np.asarray(part_df["gross_excess_ret"].to_numpy(), dtype=np.float64) * 10_000.0
    cost_bps_arr = np.asarray(part_df["exit_cost_1x_ratio"].to_numpy(), dtype=np.float64) * 10_000.0
    spr_arr = np.asarray(part_df["entry_spread_bps"].to_numpy(), dtype=np.float64)
    date_groups = np.asarray(part_df["trade_date"].cast(pl.String).to_numpy())

    mean_1x_bps, se_1x_bps, t_1x = _date_clustered_mean_tstat(net_1x_bps_arr, date_groups)
    mean_2x_bps, _, t_2x = _date_clustered_mean_tstat(net_2x_bps_arr, date_groups)

    q05 = float(np.quantile(net_1x_bps_arr, 0.05))
    cvar95 = float(np.mean(net_1x_bps_arr[net_1x_bps_arr <= q05]))

    by_day = part_df.group_by("trade_date").agg(pl.col("net_1x_ret").mean().alias("cohort_net_1x")).sort("trade_date")
    best_day = by_day.sort("cohort_net_1x", descending=True).select("trade_date").head(1).item()
    without_best = part_df.filter(pl.col("trade_date") != pl.lit(best_day))
    no_best_bps = (
        float(np.mean(np.asarray(without_best["net_1x_ret"].to_numpy(), dtype=np.float64))) * 10_000.0
        if without_best.height > 0
        else 0.0
    )

    all_sessions = daily_df.select("trade_date").unique().sort("trade_date")
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

    skew, ex_kurt, ac1 = _sample_moments(daily_rets)
    dsr_res = deflated_sharpe_ratio_from_statistics(
        observed_sharpe=sr_native,
        n_samples=max(n_days, 10),
        n_trials=H089_TRIAL_N,
        variance_trials=max(1.0 / max(float(n_days), 1.0), 0.002),
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

    mode_counts: dict[str, int] = {}
    for row_m in part_df.group_by("entry_mode").len().iter_rows(named=True):
        mode_counts[str(row_m["entry_mode"])] = int(row_m["len"])

    runner_cnt = int(sum(runner_close_flags))
    runner_pct = (100.0 * runner_cnt / part_df.height) if part_df.height > 0 else 0.0

    subperiods: list[SubperiodMetric] = []
    yr_df = (
        part_df.with_columns(pl.col("trade_date").dt.year().alias("year"))
        .group_by("year")
        .agg(
            [
                pl.len().alias("events"),
                pl.col("trade_date").n_unique().alias("distinct_dates"),
                (pl.col("net_1x_ret").mean() * 10_000.0).alias("mean_net_1x_bps"),
                (pl.col("net_2x_ret").mean() * 10_000.0).alias("mean_net_2x_bps"),
            ]
        )
        .sort("year")
    )
    for row_y in yr_df.iter_rows(named=True):
        subperiods.append(
            SubperiodMetric(
                year=int(row_y["year"]),
                events=int(row_y["events"]),
                distinct_dates=int(row_y["distinct_dates"]),
                mean_net_1x_bps=round(float(row_y["mean_net_1x_bps"]), 3),
                mean_net_2x_bps=round(float(row_y["mean_net_2x_bps"]), 3),
            )
        )

    t_hurdle = hlz_dynamic_t_hurdle(H089_TRIAL_N)
    distinct_dt_count = int(part_df["trade_date"].n_unique())
    passes = (
        part_df.height >= 200
        and distinct_dt_count >= 60
        and t_1x >= t_hurdle
        and float(dsr_res.probability) >= 0.95
        and cpcv_pos_frac >= 0.80
        and mean_1x_bps > 0.0
        and mean_2x_bps > 0.0
        and no_best_bps > 0.0
    )

    h088_ref_bps = -15.160
    min_d_str = str(panel.select(pl.col("trade_date").min()).item())
    max_d_str = str(panel.select(pl.col("trade_date").max()).item())

    return H089StudyResult(
        hypothesis_id=H089_HYPOTHESIS_ID,
        spec_sha256=H089_SPEC_SHA256,
        evaluated_at_utc=dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        sample_min_date=min_d_str,
        sample_max_date=max_d_str,
        cumulative_trials_n=H089_TRIAL_N,
        required_hlz_t_hurdle=t_hurdle,
        liquid_orb_events_total=panel.height,
        shielded_ignition_signals=shielded.height,
        participated_events_count=part_df.height,
        participation_rate_pct=round(100.0 * part_df.height / max(shielded.height, 1), 2),
        entry_mode_counts=mode_counts,
        runner_reached_close_count=runner_cnt,
        runner_reached_close_pct=round(runner_pct, 2),
        distinct_dates=distinct_dt_count,
        mean_entry_spread_bps=round(float(np.mean(spr_arr)), 3),
        gross_excess_bps=round(float(np.mean(gross_bps_arr)), 3),
        mean_exit_cost_1x_bps=round(float(np.mean(cost_bps_arr)), 3),
        net_return_1x_bps=round(mean_1x_bps, 3),
        net_return_2x_bps=round(mean_2x_bps, 3),
        net_1x_without_best_day_bps=round(no_best_bps, 3),
        h088_single_tranche_net_1x_bps=h088_ref_bps,
        convexity_lift_vs_h088_bps=round(mean_1x_bps - h088_ref_bps, 3),
        cvar95_bps=round(cvar95, 3),
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pre-registered H089 pre-wall study (<=2026-10-15)")
    parser.add_argument("--out-json", type=str, default="")
    args = parser.parse_args()

    res = run_local_h089_prewall_study()
    payload = json.dumps(asdict(res), indent=2)
    if args.out_json:
        out_p = Path(args.out_json).expanduser().resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
