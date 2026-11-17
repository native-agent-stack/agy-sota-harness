"""Executable Quantitative, Dimensional, Pre-Wall & Schema Invariants (`L6` / `L8` / `T1` / `T4` / `T5`).

Grounded in:
- `trailofbits/skills` (`dimensional-analysis`, `fp-check`, `property-based-testing`)
- `ADR-0022` (`max_stop_pct <= 2.00%` across long & short; NMS tick-grid quantization)
- Harvey, Liu & Zhu (2016) dynamic multiple-testing t-statistic hurdle `t*(N)`
- `unionai-oss/pandera` + `pola-rs/polars` zero-copy OHLCV schema validation
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from statistics import NormalDist
from typing import Literal

import pandera.polars as pa
import polars as pl

STUDY_WALL_DATE = date(2026, 10, 15)
ADR0022_MAX_STOP_PCT = 2.0
HLZ_BASE_ONE_SIDED_P = 0.00135
_STD_NORM = NormalDist(0.0, 1.0)


@dataclass(frozen=True, slots=True)
class StopPreset:
    side: Literal["long", "short"]
    entry_px: Decimal
    stop_px: Decimal
    stop_distance_pct: float
    stop_distance_bps: float


def _require_finite(val: float, name: str) -> float:
    fval = float(val)
    if not math.isfinite(fval):
        raise ValueError(f"{name} must be finite (got {val!r})")
    return fval


def bps_to_ratio(value_bps: float) -> float:
    """Convert basis points (`100 bps == 1% == 0.01`) to multiplicative ratio."""
    return _require_finite(value_bps, "value_bps") / 10_000.0


def pct_to_ratio(value_pct: float) -> float:
    """Convert percentage points (`2.0 pct == 2% == 0.02`) to multiplicative ratio."""
    return _require_finite(value_pct, "value_pct") / 100.0


def ratio_to_bps(value_ratio: float) -> float:
    """Convert multiplicative ratio (`0.01 == 100 bps`) to basis points."""
    return _require_finite(value_ratio, "value_ratio") * 10_000.0


def quantize_nms_price(raw_px: float, *, side: Literal["long", "short"], is_stop: bool = True) -> Decimal:
    """Quantize price to legal US NMS Reg NMS Rule 612 tick grid ($0.01 >= $1.00, $0.0001 < $1.00).

    For protective stops, rounds conservatively inward so quantized distance never exceeds ADR-0022 cap.
    """
    fpx = _require_finite(raw_px, "raw_px")
    if fpx <= 0.0:
        raise ValueError(f"Price must be strictly positive (got {raw_px!r})")
    dpx = Decimal(str(fpx))
    tick = Decimal("0.01") if dpx >= Decimal("1.00") else Decimal("0.0001")
    if is_stop:
        rounding = ROUND_CEILING if side == "long" else ROUND_FLOOR
    else:
        rounding = ROUND_FLOOR if side == "long" else ROUND_CEILING
    q = (dpx / tick).to_integral_value(rounding=rounding) * tick
    if q <= Decimal("0"):
        raise ValueError(f"Quantized price collapsed to <= 0 for {raw_px!r}")
    return q


def validate_adr0022_stop(
    entry_px: float,
    requested_stop_pct: float,
    *,
    side: Literal["long", "short"] = "long",
) -> StopPreset:
    """Compute and validate an atomic ADR-0022 protective stop (`0 < stop_pct <= 2.00%`)."""
    e_val = _require_finite(entry_px, "entry_px")
    s_pct = _require_finite(requested_stop_pct, "requested_stop_pct")
    if e_val < 0.05:
        raise ValueError(f"entry_px must be >= $0.05 (got {entry_px!r})")
    if s_pct <= 0.0 or s_pct > ADR0022_MAX_STOP_PCT:
        raise ValueError(
            f"ADR-0022 violation: requested_stop_pct={s_pct} outside (0.0, {ADR0022_MAX_STOP_PCT}]%"
        )
    if side not in ("long", "short"):
        raise ValueError(f"Unsupported side: {side!r}")

    q_entry = quantize_nms_price(e_val, side=side, is_stop=False)
    ratio = Decimal(str(s_pct)) / Decimal("100")
    raw_stop = q_entry * (Decimal("1") - ratio) if side == "long" else q_entry * (Decimal("1") + ratio)
    q_stop = quantize_nms_price(float(raw_stop), side=side, is_stop=True)

    if side == "long" and q_stop >= q_entry:
        tick = Decimal("0.01") if q_entry > Decimal("1.00") else Decimal("0.0001")
        q_stop = q_entry - tick
    elif side == "short" and q_stop <= q_entry:
        tick = Decimal("0.01") if q_entry >= Decimal("1.00") else Decimal("0.0001")
        q_stop = q_entry + tick

    realized_ratio = float(abs(q_entry - q_stop) / q_entry)
    realized_pct = realized_ratio * 100.0
    if realized_pct <= 0.0 or realized_pct > ADR0022_MAX_STOP_PCT + 1e-9:
        raise ValueError(
            f"Quantized tick grid cannot satisfy ADR-0022 <=2.00% at entry_px={q_entry} (realized={realized_pct:.4f}%)"
        )

    return StopPreset(
        side=side,
        entry_px=q_entry,
        stop_px=q_stop,
        stop_distance_pct=round(realized_pct, 6),
        stop_distance_bps=round(realized_ratio * 10_000.0, 4),
    )


def enforce_prewall_cutoff(sample_max_date: date | str, *, allow_frozen_oos: bool = False) -> date:
    """Enforce the machine-wide `<= 2026-10-15` factor discovery & CPCV wall."""
    parsed = date.fromisoformat(sample_max_date) if isinstance(sample_max_date, str) else sample_max_date
    if not allow_frozen_oos and parsed > STUDY_WALL_DATE:
        raise ValueError(
            f"Study-Wall Violation: {parsed.isoformat()} > {STUDY_WALL_DATE.isoformat()} (post-wall data reserved for frozen OOS only)"
        )
    return parsed


def hlz_dynamic_t_hurdle(cumulative_trials_n: int) -> float:
    """Return Harvey-Liu-Zhu multiple-testing t-hurdle `t*(N)` (`3.000` at `N=1`, monotonically increasing)."""
    if cumulative_trials_n < 1:
        raise ValueError(f"cumulative_trials_n must be >= 1 (got {cumulative_trials_n})")
    p_target = HLZ_BASE_ONE_SIDED_P / float(cumulative_trials_n)
    return round(float(_STD_NORM.inv_cdf(1.0 - p_target)), 4)


class OhlcvBarSchema(pa.DataFrameModel):
    symbol: str = pa.Field(str_length={"min_value": 1, "max_value": 16})
    open_px: float = pa.Field(gt=0.0)
    high_px: float = pa.Field(gt=0.0)
    low_px: float = pa.Field(gt=0.0)
    close_px: float = pa.Field(gt=0.0)
    volume_shares: float = pa.Field(ge=0.0)


def validate_ohlcv_polars_frame(df: pl.DataFrame) -> pl.DataFrame:
    """Validate zero-copy Polars OHLCV frame via Pandera + intrabar envelope checks."""
    validated = OhlcvBarSchema.validate(df)
    bad = validated.filter(
        (~pl.col("open_px").is_finite())
        | (~pl.col("high_px").is_finite())
        | (~pl.col("low_px").is_finite())
        | (~pl.col("close_px").is_finite())
        | (~pl.col("volume_shares").is_finite())
        | (pl.col("high_px") < pl.max_horizontal("open_px", "close_px", "low_px"))
        | (pl.col("low_px") > pl.min_horizontal("open_px", "close_px", "high_px"))
    )
    if bad.height > 0:
        raise ValueError(f"OHLCV envelope or NaN/Inf violation in {bad.height} row(s)")
    return validated
