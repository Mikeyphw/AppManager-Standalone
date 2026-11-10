# AMUI-03B HF03 — Manual gate contract migration (AMT-05C and AMT-06B)

## Verified failure
Run `42737286042` (targeted CI), commit `2692bc996b9d1f95c25e68ff4d34dff6c7c70901`, fails `AMT05C_DURABLE_BACKUP_RECEIPT_FAIL`. The source contract incorrectly requires a no-longer-present `BatchOpsService.java` workflow path-filter token, an obsolete legacy auto-trigger requirement. AMT-06B has the same stale literal and would fail next.

## Fix
- Preserve all Tasker receipt, native service, exact restore snapshot and permission/privilege guards. No app Java or Android manifest changes.
- Replace obsolete workflow path-filter checks with checks on **real** manually dispatched Android 15/16 instrumentation and the targeted source and full-source checks.
- Add one new source parity checker and 17 isolated mutation regressions, run in both full and targeted source workflows.
- Preserve full gate manually dispatched only. Do **not** silently append a sixth overlay.
- Reuse `scripts/devtool/amui_gate_retry.py` from HF02 after targeted passes: it verifies original failed run `42735142696` and local 5/5 receipt, retargets existing pending gate from original SHA `b426ea724ec6bbef3951957ea310a52d77e252dd` to this corrected descendant and dispatches a new full run exactly once.

Exact source pin: `2692bc996b9d1f95c25e68ff4d34dff6c7c70901` branch `feature/amui03b-responsive-list-20261109`. PR #4 stays open until full Android qualification succeeds.

Source-only checks are **not** Android acceptance. Full workflow must pass all 5 required jobs before `amui_ci_gate.py --ack-run RUN_ID` resets local gate. No local Gradle, no auto-merge.
