# AMUI-02 — global Material 3 / Material You foundation (first consolidated tranche)

Source pin: `e329ca842ab9ca4d8567d433d1887803e2fe142c` (`Mikeyphw/AppManager-Standalone`, `feature/tasker-automation` after AMUI-01 PR #1).
Feature branch: `feature/amui02-global-material-you-20261109`. Tasker remains frozen.

## Implementation

- Retains existing `DynamicColors.applyToActivityIfAvailable` and `wrapContextIfAvailable`: no secondary palette generator or new preference, and older Android keeps built-in Material 3 fallback.
- Replaces the old dark `AppTheme.Black` override of `colorSurface` with a **root-only black** overlay applied *after* dynamic color injection in activity and non-activity theme contexts. No wallpaper-derived accent/container palette role is overwritten. Translucent activities/contexts are excluded.
- Separates root `android:colorBackground` from `colorSurface` in 24 Activity chrome layouts, including app list, app details, settings (single/two-pane), AppOps history, file manager, editor outer chrome, debloater, installed profiles, running apps, lab, shared prefs, scanner history, batch ops, terminal outer chrome and others. Media/PDF/image content canvases are deliberately not recolored.
- Gives dark+Pure Black splash an exact black background; switches status/navigation bar icon contrast for effective appearance mode.
- Material 3 `colorError` replaces one hardcoded generic failure color; semantic success/warning indicators remain separate and require visual examination before further changes.
- Adds 4 hosted instrumentation assertions in Android 15 and 16 jobs, retaining existing AMT and AMUI-01 gates. Installer explicitly dispatches hosted `mode=full` at the pushed AMUI-02 SHA, preserving the six existing AMUI-01 push predicates and source contracts; source tests run in the source-contract job.

## Verification limits / next tranche

This overlay is the **foundation**, not a claim that every individual legacy widget and nested screen has passed visual acceptance. After exact-commit hosted CI, audit nested app-details tabs, backup and installer sheets, tracker dialogs, bottom sheets and code-editor chrome under light/dark/pure-black, and test real wallpaper changes + screenshots on device before declaring AMUI-02 complete. No release update, automatic merge or destructive restore. Follow with AMUI-03 only after AMUI-02 acceptance.

## Apply / rollback

Overlay uses the native Devtool atomic transaction, source blob pins for every preflight-modified file, `write_paths` restrictions, and source-only validation. A clean checkout of the exact merged baseline is mandatory. It does not reset a dirty tree. Do not run Gradle on Termux. Push creates a PR to `feature/tasker-automation` and watches same-commit GitHub Actions. If any hosted test fails, leave PR unmerged and fix the actual failure. The image/color assertions are not substitutes for a visual review.
