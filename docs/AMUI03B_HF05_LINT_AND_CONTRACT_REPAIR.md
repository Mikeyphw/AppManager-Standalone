# AMUI-03B HF05 — Android lint plus stale compact-list contract

Live full CI at [02675955](https://github.com/Mikeyphw/AppManager-Standalone/actions/runs/42746094551) failed 4/5: only the hosted Gradle job failed, at Android Lint `EllipsizeMaxLines` in `item_main.xml:88:17`.

Android Lint: `ellipsize=middle` with `maxLines=1` can crash; use `singleLine=true`. Preserve the central truncation and adapter-bound `packageName` ID. No production Java, Tasker privilege, manifest or history changes.

Fixes the stale AMUI-03A source contract, which previously required maxLines=1 on every field. It now rejects the dangerous middle/maxLines pairing and permits the correct Android attribute. All preexisting status/selection checks and legacy source tests remain. Adds explicit negative tests and no-op mutation refusal.

The historical lint XML baseline is unchanged: never suppress new errors, replace baseline, or waive real Gradle failures. Existing targeted CI executes these checkers and unittest discovery; the manual full CI does the same.

The source is pinned to commit `0267595523e32470bb91b9a42bf79717d0b8a64e`, exactly 3 source files with Git blobs and SHA-256 verified in preflight; Devtool owns one transaction, rollback, and commit. No local Gradle; GitHub hosts compile/test/lint and both emulators.

The original fifth-overlay gate is still due; the failed full run `42746094551` at `0267595523e32470bb91b9a42bf79717d0b8a64e` cannot be acknowledged. After new targeted source **and hosted compile** are green, recover only the existing fifth gate to the corrected descendant SHA. Never count a sixth overlay, merge PR #4, force push, or run Gradle locally.
