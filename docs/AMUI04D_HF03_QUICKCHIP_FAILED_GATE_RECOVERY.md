# AMUI-04D HF03 — API 35/36 quick-filter regression and failed final-gate recovery

Parent: `ae14dd90b9e7cefe0033f904bfa226ccfebc4f7c` (AMUI04D 5/5, **unqualified**).

Failed manual workflow: [42838584935](https://github.com/Mikeyphw/AppManager-Standalone/actions/runs/42838584935), attempt 1. Both Android 15 and 16 emulator jobs returned `2 passed, 1 failed` in `Amui03CQuickFiltersInstrumentedTest`: the specific failing ID is `quickChipSelectionCanToggleWithoutChangingPackages`. The API 36 real disposable APK install/replacement/uninstall passed; API 35 Tasker instrumentation and earlier theme tests passed. This was a real shared device-test failure, not a GitHub annotations 504.

## Repair

The AMUI03C toggle test inflated and mutated an unattached Material `Chip` outside the Android UI thread. A real ChipGroup's internal checked-state listener is a UI control; the old test could misrepresent production interaction. HF03 moves inflation, group introspection, checking and unchecking into `Instrumentation.runOnMainSync`, tests the actual checked and unchecked states and idles the instrumentation thread after the changes. It also explicitly sets `app:selectionRequired="false"` on the real ChipGroup so "none/all" deselection remains supported, not merely asserted by the test. The original API35/36 three-test floor and other quick-filter tests are preserved. Both source checker and negative mutation suite now require the main-thread behavior, `selectionRequired=false` and the two state assertions.

Because the archived failed receipts include only the failing test name, not the JUnit exception and stack trace, this is a grounded correction for the off-main-thread test setup and potential theme-derived selection policy, **not a claim that the exact assertion line is known**. The next real hosted full gate is authoritative.

## Gate state and protections

The outer ZIP is an embedded Python/Rich launcher; run `python3 /storage/emulated/0/Download/AMUI04D_HF03_QUICKCHIP_AND_FAILED_5_OF_5_RECOVERY.overlay.zip` in Termux. It is a new source-pinned Devtool-native overlay, not a reapply of AMUI04D HF02.

After the new commit passes both targeted CI jobs, the launcher checks that the local milestone 5 entry still holds the **old failed** SHA and the sole pending run is **42838584935**. It verifies that exact run failed, including both specific emulator jobs, then **replaces** the fifth milestone with the new commit. It never appends a sixth overlay, changes the previously qualified four SHA entries, acknowledges the failed run or resets the counter. The failed run is retained in an explicit `recovery_history` entry.

The new fifth-milestone run is strictly manual `workflow_dispatch` in full mode, exact SHA, and is dispatched once. The launcher polls the GitHub run and job APIs directly, not `gh run watch` and its annotations call. It verifies all five hosted jobs, downloads both API 35/36 artifact bundles, executes the existing stringent `scripts/devtool/amui04d_receipt_audit.py` (including AMUI01 lifecycle, AMUI02..04D, screenshot hashes), and **only then** invokes canonical `amui_ci_gate.py --ack-run`.

If any source test, Java compile, Android test, full workflow, artifact or input validation fails, qualification is refused and state remains pending. No forced push, local Termux Gradle, automatic merge, package modification or unauthorized user profile creation.

## Qualification boundary

This repairs a failed emulator test and recovery of the existing 5/5 gate. A future green result is not proof of every original full roadmap item: real wallpaper changes, complete screen-by-screen Material You parity, older API runtime fallback, real work profile creation and physical ARM64 acceptance remain separately scoped and must not be called completed.
