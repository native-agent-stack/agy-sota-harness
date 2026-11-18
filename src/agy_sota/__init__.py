"""AGY SOTA Harness Reference Invariants, Dimensional Guards & Workflow Library."""

from agy_sota.hybrid_runner_prewall_study import (
    H089_HYPOTHESIS_ID,
    H089_SPEC_SHA256,
    H089_TRIAL_N,
    H089StudyResult,
    replay_dual_tranche_runner_convexity,
    simulate_two_stage_hybrid_entry,
)
from agy_sota.invariants import (
    STUDY_WALL_DATE,
    StopPreset,
    bps_to_ratio,
    enforce_prewall_cutoff,
    hlz_dynamic_t_hurdle,
    pct_to_ratio,
    quantize_nms_price,
    ratio_to_bps,
    validate_adr0022_stop,
    validate_ohlcv_polars_frame,
)
from agy_sota.research_convergence import (
    STRATEGY_ARCHETYPES,
    build_seven_feed_research_manifest,
    load_pinned_shelf_shas,
    resolve_session_datafeed,
    scaffold_converged_strategy,
    validate_converged_strategy_manifest,
)

__all__ = [
    "H089StudyResult",
    "H089_HYPOTHESIS_ID",
    "H089_SPEC_SHA256",
    "H089_TRIAL_N",
    "STRATEGY_ARCHETYPES",
    "STUDY_WALL_DATE",
    "StopPreset",
    "bps_to_ratio",
    "build_seven_feed_research_manifest",
    "enforce_prewall_cutoff",
    "hlz_dynamic_t_hurdle",
    "load_pinned_shelf_shas",
    "pct_to_ratio",
    "quantize_nms_price",
    "ratio_to_bps",
    "replay_dual_tranche_runner_convexity",
    "resolve_session_datafeed",
    "scaffold_converged_strategy",
    "simulate_two_stage_hybrid_entry",
    "validate_adr0022_stop",
    "validate_converged_strategy_manifest",
    "validate_ohlcv_polars_frame",
]
