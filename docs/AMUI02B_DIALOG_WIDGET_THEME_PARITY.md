# AMUI-02B — Material-themed dialog content and widget context parity

Source-pinned baseline: `fa5c90e33e5b7039479c00fe8aa8930c15dd30e2` on `feature/amui02-global-material-you-20261109` in `Mikeyphw/AppManager-Standalone`.

## Changes
1. Widget contexts now honor the selected night mode, locale and layout direction before dynamic wallpaper colors and the optional root-black overlay. This uses the same configuration-resolution path as regular themed app contexts.
2. Searchable single/multi/items and standard text-input dialogs now **inflate content using the MaterialAlertDialogBuilder's themed context** rather than the pre-overlay activity context. This includes list item style resolution, avoiding mismatched controls when dialogs have a different Material overlay.
3. Dropdown dialogs use the themed builder's context for their view and adapters. The owning activity remains unchanged for FragmentActivity-specific actions.
4. Add two real hosted AMUI-02 theme tests for widget context (dark+black with preserved tonal surface, and light+black preference preserved but unapplied).
5. Source mutation tests fail if any dialog falls back to pre-themed view inflation or if widget night overrides are lost.

## Limits and qualification
- Existing settings, pure-black persistence, semantic colors, editor/file content, Tasker and KVM gates are unchanged. No font-size/accessibility overhaul.
- Source-only validation is not a replacement for GitHub-hosted Java/resource/AndroidTest compilation or Android 15/16 runtime/screenshot qualification.
- This overlay uses the current lightweight targeted workflow, including hosted compilation on relevant source changes, and records the successful pushed commit in the five-overlay counter.
- Do not dispatch full CI except when a gate is due, on a critical change, or for release/merge qualification.
