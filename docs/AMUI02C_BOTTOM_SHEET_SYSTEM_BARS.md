# AMUI-02C — Bottom-sheet system bars follow the actual themed context

Exact base: `5f2fed234ffd860d44da4e001e81a2aff5cccafa` · branch `feature/amui02-global-material-you-20261109` · PR #2.

## Implemented
- Capsule bottom-sheet dialogs no longer rely on the global static `UiUtils.isDarkMode()` to paint window chrome. They read night mode from `getContext()` and apply matching status/navigation icon contrast.
- Dialog edge-to-edge and transparent status/navigation bars remain enabled. Existing drag/skip-collapsed behavior and optional blur remain unchanged.
- Pure Black's follow-system fallback uses the **supplied themed Context** configuration instead of global system resources. Material surface roles are not overwritten.
- Two Android 15/16 instrumentation tests assert light/dark context resolution. They will execute only at the next full-gate milestone.
- Targeted CI runs source mutation checks and GitHub-hosted Java/instrumentation compilation only, without starting an emulator.

## Scope / limitations
This is source and behavior integration, **not** a real-device visual signoff. Screenshot/interactive bottom-sheet acceptance still belongs to the next full gate or later AMUI-04 UX acceptance. No app-list layout, Tasker functionality, font size, permissions, or releases were modified.

Gate count expected after exact-SHA push and successful targeted run: **3/5**. Actual local count must be read from the installed counter.
