# AMUI-03B HF02 — fifth-overlay qualification retry

The full gate run `42735142696` at `b426ea724ec6bbef3951957ea310a52d77e252dd` stopped at the AMT04B1 source contract, before any Gradle or Android emulator jobs. The old contract looked for `app/src/androidTest/java/io/github/muntashirakon/AppManager/automation/**` in the manual-only full workflow. That path-trigger belongs to the new targeted workflow. The two workflow modes remain separate.

This hotfix:
- Preserves all AMT04B1 privileged-operation restrictions and its exported-component checks.
- Asserts that manually-dispatched full CI still contains the Android 15/16 jobs and the AMT04B1 source gate.
- Adds every full source-contract command plus the full Python mutation suite to targeted source CI, without launching local Gradle or emulators.
- Introduces `amui_gate_retry.py`, which checks the original failed workflow and the new clean, pushed descendant SHA. It retargets the existing *fifth* overlay and pending-gate record, without recording a sixth overlay. It reuses any existing exact-SHA dispatch.
- Retains mandatory full Android 15 and 16 qualifications before acknowledging/resetting the gate.

**Exact source base:** `b426ea724ec6bbef3951957ea310a52d77e252dd` on `feature/amui03b-responsive-list-20261109`. PR #4 remains open and must not merge until full qualification passes.

**Remediation flow:** apply the consolidated Devtool overlay; push the direct child commit; watch targeted source and hosted Android compile (if the workflow scopes compile); call `python3 -B scripts/devtool/amui_gate_retry.py --head "$HEAD" --failed-run 42735142696`; watch the newly-dispatched full workflow; acknowledge via `amui_ci_gate.py --ack-run RUN_ID` only if all required jobs passed. No retries automatically until a new source-pinned correction is ready.

**Warning:** The full Android gate may uncover additional issues beyond the initial AMT04B1 failure. This patch cannot claim full qualification before the new hosted jobs pass.
