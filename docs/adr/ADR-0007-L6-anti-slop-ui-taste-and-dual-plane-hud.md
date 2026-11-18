# ADR-0007: L6 Anti-Slop Institutional UI Taste, Chrome DevTools & Dual-Plane `24/5` HUD Architecture

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** `L6` UI Taste, DevTools & Real-Time `T8` Visualization
- **Evidence Grade:** E4 (`:8787` & `:8799` HTTP 200 Live HUDs + Apache-2.0 Attribution Verified)
- **GitHub Evidence:** https://github.com/tradingview/lightweight-charts (`c29c51e1e5bc61981da5832c97797cb8283d120f`), https://github.com/finos/perspective (`0264ec13cd28ef4a2a136c8ef021c3c112bc8990`), https://github.com/pbakaus/impeccable (`2026-SOTA`), https://github.com/Nutlope/hallmark (`2026-SOTA`)
- **Revisit Trigger:** 2027-01-01 or `lightweight-charts` / `perspective` major version bump

## Context and Problem Statement

Unattended `24/5` quantitative terminals (`sota-mover-ranker` on `:8787` and `sota-dynamic-trail-c` on `:8799`) require high-density, `tabular-nums` institutional blotters and candlestick charts without TradingView Advanced Charts UDF licensing restrictions, background GUI mouse-click loops, or generic AI-slop visual patterns.

## Decision Outcome

1. **Dual-Plane Visualization Split:**
   - **Unattended `24/5` Canonical HUDs (`127.0.0.1:8787` & `127.0.0.1:8799`):** Self-hosted Apache-2.0 `tradingview/lightweight-charts` (rendering visible attribution to `https://www.tradingview.com/` per Apache-2.0 NOTICE terms) paired with `finos/perspective` streaming blotters.
   - **Attended Human Charting (`TradingView.app`):** Native macOS desktop app (`US Real-Time Bundle` + `24h` session toggle) fed exclusively via cryptographic SHA-256 `pbcopy` staging, `<= 1–2/day` delta-gated Cloud MCP watchlist syncs, and on-demand `agent-desktop` Accessibility symbol focus (zero background GUI loops; zero Advanced Charts UDF localhost bridges).
2. **Anti-Slop Institutional Design & DevTools Verification:** Enforce `sota-taste-anti-slop` typography, alignment, and contrast rules alongside `chrome-devtools-plugin` DOM/console/LCP verification.

## Alternatives Considered

1. **Self-hosting TradingView Advanced Charts / Charting Library over a local UDF feed:** Rejected — proprietary redistribution/licensing constraints are unnecessary when Apache-2.0 `lightweight-charts` + `finos/perspective` cover unattended `24/5` visualization cleanly.
2. **Continuous `pyautogui` / GUI watchlist-clicking loops against `TradingView.app`:** Rejected — steals user focus and breaks deterministically on window resize (`G5_SUSTAINABLE_NO_GUI_LOOP`).

## Verification Witness

- `harness/run_probes.py` `L6` verifies `sota-taste-anti-slop` and `chrome-devtools-plugin` installation.
- `~/.agents/bin/sota-deadman-check` verifies `HTTP 200` liveness on both `http://127.0.0.1:8787/` and `http://127.0.0.1:8799/`.
