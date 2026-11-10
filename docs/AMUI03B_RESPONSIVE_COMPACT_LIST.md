# AMUI-03B — Responsive compact list and exact-position app actions

Source commit: `a7366a34c74bc7c52b6db5729a9d8ef7162b9893` (merged PR #3, branch `feature/tasker-automation`).
Target branch: `feature/amui03b-responsive-list-20261109`.

## User-facing behavior
- Maintain AMUI-03A's original 14 visible/optional metadata view IDs, compact icon (40dp), normal-size Material 3 typography and stable selection/highlight controls. No font enlargement or new accessibility UI.
- App list uses `AutoFitGridLayoutManager` with **480dp minimum column width**, retaining one-column cards on phones and sensible columns for larger/foldable windows.
- `AutoFitGridLayoutManager` recalculates spans when the actual layout width changes, not only at first layout; padding is subtracted from total available width. Zero-width and invalid column widths resolve safely to one column.
- Tapping an app opens the **item at the live adapter position**, not an outdated item captured during a previous bind. Icon tap and long press continue selection, and uninstall/disabled/stopped/status stroke precedence remains intact.

## Guardrails and acceptance
- Minimal source change: grid manager, MainActivity grid attachment, adapter click, existing AMUI03A checker + its negative test, Android instrumentation smoke test, and targeted workflow registration. `MainViewModel`, package reconciliation, sorting, batch actions and Tasker are unchanged.
- Targeted CI runs source regression checks plus hosted Java and AndroidTest compilation (no emulator per overlay).
- Once local overlay registration reaches **5/5**, the shared post-push gate hook dispatches full `mode=full` (lint, tests, hosted Android 15 and 16). The installer will watch the exact SHA gate and acknowledge qualification only if every required job succeeds. No automatic merge/release.
- Full acceptance is mandatory at the fifth overlay and whenever user requests release. A targeted pass alone is not runtime qualification.
- Preflight rejects wrong branch, stale merge SHA, unrelated dirty files, source blob changes and unexpected origin. Uses `$TMPDIR` for staging, and neither force pushes nor modifies unrelated work.

## Gate state
`python3 -B scripts/devtool/amui_ci_gate.py --status` (Termux, `~/Code/AppManager`).
Only the user-side Termux state knows the actual overlay count; the expected count immediately before this overlay is **4/5**. If the count differs, the local counter is authoritative.
