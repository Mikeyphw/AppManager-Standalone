# AMUI-02 HF02 — Hosted AAPT2 style-parent hotfix

2026-11-09. Repository: `Mikeyphw/AppManager-Standalone`.
Branch: `feature/amui02-global-material-you-20261109`.
Failing **exact** SHA: `651e7f568018a2c45a1e7a9bd4089ccba7f98abf`.

## Reproduced hosted failure

- `42675787205` (workflow_dispatch/full): source contracts PASS, AMT-06C fixture PASS; hosted Gradle, Android 15 instrumentation and Android 16 installation tests FAIL.
- `42675784491` (pull_request): source contracts PASS, Gradle FAIL; three non-PR jobs were skipped.
- Both Gradle jobs fail in `:app:processDebugResources` with AAPT2 `resource style/ThemeOverlay.AppTheme not found`.
- Android 15/16 instrumentation builds fail on the same missing resource. Lint report upload fails because the build did not reach lint (not an independent lint regression).

## Root cause

Android's dotted style names inherit their prefix as implicit parents when `parent` is absent. `ThemeOverlay.AppTheme.PureBlackRoot` had an empty/no-parent role but did **not** explicitly declare `parent=""`. AAPT2 therefore tried to resolve a nonexistent style named `ThemeOverlay.AppTheme`.

## Patch

1. The day and night declarations of `ThemeOverlay.AppTheme.PureBlackRoot` now have **explicit `parent=""`**; no material color-role or activity-background changes.
2. `check_amui02_theme.py` parses the actual XML style element, requires exactly one overlay per day/night resource and rejects missing/nonempty parent attributes.
3. `test_amui02_theme.py` adds four negative regressions: omitted day parent, omitted night parent, accidental nonempty parent, duplicated overlay. All seven earlier source tests retained.
4. No changes to workflow predicates, KVM guards, emulator thresholds, lint report gates, Devtool configuration, existing Tasker contracts, HMAC/backup/restore code, or user app data.

## Qualification limitations

Offline source-contract and mutation tests are not GitHub-hosted Gradle/device evidence. Run workflow `devtool-tasker-ci.yml` with `mode=full` on the new feature SHA and check all five jobs, lint report and both emulator receipts. Do not merge until hosted qualification passes; later full-screen wallpaper and visual acceptance is still needed for AMUI-02.

## Safety

Overlay is exact failing commit Git-blob pinned. It requires a clean worktree, checks origin/branch/HEAD and uses Devtool's atomic transaction/rollback. Installer commits, pushes, reuses PR #2, dispatches full GitHub CI and watches checks without force reset, auto-merge, local Gradle or release publishing.
