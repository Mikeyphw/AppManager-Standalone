# AMUI-01 HF05 — Backup-only Robolectric harness and independent test diagnostics

Source: `Mikeyphw/AppManager-Standalone` `feature/amui01-hf01-reissued-20261109`
Pinned baseline: `e35ae07bf1a68d3f2463cc730a2a1f7e35c5e512`
Run: https://github.com/Mikeyphw/AppManager-Standalone/actions/runs/42630234609

The first same-commit hosted run has 4/5 passing jobs, including API35, API36, source and fixture.
Only the Gradle job failed. It built the app, then :app:testDebugUnitTest reported
574 tests, 16 errors, all in BackupManagerTest. The output only identifies
IllegalStateException at the test's AppDb.loadInstalledOrBackedUpApplications call.

HF05 **does not waive, skip, exclude or mark green any unit test**. It replaces
12 legacy setup calls that previously synchronized both backup metadata and
installed app inventory with `new AppDb().getBackups(true)`. The backup-only
Robolectric tests actually require the backup metadata refresh; the real
Android authoritative package manager scan remains strict and exercised by the
successful API35/API36 tests. The method is already part of AppDb and calls
BackupUtils.storeAllAndGetLatestBackupMetadata().

The original hosted Gradle, JUnit, lint baseline, API35, API36 and Tasker source
gates remain untouched. The workflow now uploads JUnit XML and HTML with
`if: always()` and `if-no-files-found: warn` on incomplete test stages so new
failures expose exact causes. The existing lint report retains `error` status.

This is a source-level hypothesis supported by failure call sites, not a claim
that 16 errors have passed: only the next hosted workflow can establish that.
The output of the 574 tests and lint remain mandatory same-commit gates.

The Devtool overlay is exact-source pinned, has a read-only dry-run, commits once,
and rolls back after validation failure. No local Gradle, no release, no changes
to app production or Tasker authorization/signing/restore code.

## Termux scratch directory

HF05 requires the `TMPDIR` environment variable for all preflight patch staging.
Temporary files use `tempfile.mkstemp(dir=$TMPDIR)` and are removed
when the operation finishes. For atomic replacement, `$TMPDIR` and the
Git checkout must be on the same filesystem; otherwise the overlay
refuses before writing. Devtool rollback **state** remains in its
persistent state directory and is not deleted or relocated.

## HF07 — lint report mutation guard

Retains the original required-error lint report artifact, scoped to the
`Upload hosted Android lint report and baseline audit` step. The previous
HF05 checker looked for a global `if-no-files-found: error`, which could be
satisfied by unrelated fixture/API36 artifact uploads after the lint step
was weakened. HF07 also adds negative tests targeting exactly that step.
No production code, Tasker security, or GitHub-hosted Gradle semantics change.
