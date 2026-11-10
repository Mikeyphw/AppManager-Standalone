# AMUI-03C HF01 — targeted javac annotation correction

- Exact parent: `96952dbd2a5cfe51ea805f38b9a644b655db7229` on `feature/amui03b-responsive-list-20261109`; repository `Mikeyphw/AppManager-Standalone`.
- Evidence: targeted GitHub Actions run **42758285744**, compile step failed at
  `MainRecyclerAdapter.java:125`: `error: annotation interface not applicable to this kind of declaration`.
- Root cause: source transform retained `@UiThread` immediately before the newly inserted
  `mDetailedMode` field, removing it from the original `setDefaultList` method.
- Correction: remove `@UiThread` from the boolean field and restore it directly before
  `void setDefaultList(List<ApplicationItem> list)`.
- Staleness protection: update existing AMUI-03C source checker, add two negative mutation
  tests; Python unittest discovery automatically includes both, so no CI weakening.
- No changes to Quick Filters, settings, Tasker, selection, Android instrumentation, workflows,
  historical lint baseline, or full-gate cadence.
- Source-only test/Devtool apply on Termux; hosted Gradle via existing targeted Actions.
- One atomic overlay and one non-force push. PR #4 must remain open/unmerged.
- Previous 5/5 qualification at `c2a27476c637f702263614707d3b25108781480d`
  run `42751712942` is retained; successful AMUI-03C HF01 is the first new
  qualified milestone (1/5) because the parent AMUI-03C compile failed.
