# AMUI-01 HF08 — hosted lint correction and automatic PR watch

Source-pinned to `64337fe557a1c91293d432a89d4d52a158488c99` on `feature/amui01-hf01-reissued-20261109` in `Mikeyphw/AppManager-Standalone`. The local Devtool checkout remains `AppManager` (not AppManager-Standalone).

## Hosted run 42649094185

- Hosted Android build: passed.
- Hosted unit tests: passed (HF05 fixed 16 Robolectric backup failures).
- Android API35 Tasker instrumentation and API36 installed/uninstalled lifecycle: passed.
- Lint: exactly one new `RestrictedApi` error at `MainActivity.java:575`. This hotfix removes the reference to AppCompat's restricted nested class and uses public `View.hasFocus()` with the original current-focus check. No lint suppression, no baseline relaxation.

## One-step application

Download both the `.overlay.zip` and `APPLY_AMUI01_HF08_PUSH_PR_WATCH.zsh` into Android Downloads. From Termux:

```zsh
zsh -f /storage/emulated/0/Download/APPLY_AMUI01_HF08_PUSH_PR_WATCH.zsh
```

The helper checks origin, exact source SHA, clean worktree, manifest, and Devtool source pins, applies with Devtool (or resumes an exactly verified HF08 commit), verifies the new commit, pushes without force, opens/reuses a PR against `feature/tasker-automation`, then watches the same-commit Actions workflow and PR checks. No auto merge. No local Gradle. All temporary PR-body files and preflight patch staging use `$TMPDIR`.

For later overlays, use the reusable tracked helper: `zsh -f scripts/devtool/amui_apply_push_pr_watch.zsh /storage/emulated/0/Download/<new-overlay>.overlay.zip` after auditing/updating its expected SHA. Never reuse an old source pin against a newer base.

The workflow does not trigger an extra PR run for base `feature/tasker-automation`; the source branch `push` run qualifies all existing jobs. The helper watches that run explicitly and separately displays PR checks.
