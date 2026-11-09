# AMUI-03A HF01 — Compact Material 3 application list

Source: `f41f7fdc93458a7b37fc04223ed8343cb12407a9` on `feature/tasker-automation` (verified merged AMUI-02C base). New development branch: `feature/amui03-compact-app-list-20261109`. Open a new PR against `feature/tasker-automation`.

## Delivered
- Replace the old broad two-column internals in `item_main.xml` with one compact vertical information stack and a 40dp icon.
- Use the current wallpaper-dynamic `colorSurfaceContainerLow`, M3 title/label/body roles and clipping for narrow card widths.
- Keep all 14 IDs bound by `MainRecyclerAdapter`: app icon, debug marker, label, package, version, system/user, SDK, date, UID, signing/issuer and backup metadata. Optional lines start `gone` and are displayed only by existing adapter logic.
- Preserve card click, long-click/range multi-select, icon-selection toggle, visual indicator stroke priority, item stable IDs, selection, search highlights, backup details and all AMUI-01 reconciliation. No changes to `MainRecyclerAdapter`, `MainViewModel`, `MainActivity`, sorting, filters or Tasker.
- Register source+23 regression tests in targeted GitHub Actions and one Android read-only inflation smoke test to run at the next full gate. Hosted compilation remains scoped and emulator-free for this overlay.

## Qualification limitations
Static and isolated Devtool worktree simulations are not a substitute for hosted compilation or real visual testing. Retained 450dp grid layout means final visual layout on narrow two-column displays is unverified and belongs in AMUI-03B/AMUI-04. No user font scale adjustments, release or merge.

Gate expectation: starting from 3/5 previously reported, the next successful overlay is 4/5. Actual Termux counter remains authoritative.
