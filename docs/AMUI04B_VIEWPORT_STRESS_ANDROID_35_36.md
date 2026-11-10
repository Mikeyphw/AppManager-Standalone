# AMUI-04B — bounded viewport stress, recycling and read-only evidence

- Exact parent: `0d89ebe7bc432769694d906133054e1c6470fbbb` in `Mikeyphw/AppManager-Standalone` on `feature/amui03b-responsive-list-20261109`.
- Milestone **3/5** after AMUI04A 2/5 (`0d89ebe7bc432769694d906133054e1c6470fbbb`), and the previously qualified
  Android 5/5 gate `c2a27476c637f702263614707d3b25108781480d` is not reset.
- Six real Android instrumented test cases (not just static source tests):
  600 synthetic rows; bounded RecyclerView virtualization; narrow/wide/narrow
  dynamic grid spans; multiple scroll/recycle passes with deterministic stable IDs
  and checked-state reset; horizontal quick filter interactions; RTL and narrow
  layout; 20 repeated view inflations that retain all 14 bound row IDs.
- Three on-device rendered viewport fixture screenshots: 720x1280 narrow,
  1920x1200 wide and 720x1280 RTL. They use synthetic row data in RecyclerView
  and a real quick-filter view. These are **not** full MainActivity screenshots.
- Both hosted API 35 and API 36 must produce the exact-commit JSON receipt,
  three validated PNGs, a hash manifest, distinct PNG hashes, and emulator logs.
- Existing AMUI-02, AMUI-03C and AMUI-04A instrumentation preserved unweakened.
- The source checker also audits production MainViewModel's single-thread executor,
  generation/epoch ordering and immutable list emission. The synthetic tests
  **do not prove** live DB races, process death, work-profile behavior, or package
  install/uninstall. Those are separate pending acceptance milestones.
- This overlay does not invoke Gradle locally or auto-dispatch full Android 5/5;
  the new API 35/36 instrumentation will run during the next manual full gate.
- PR #4 stays open, no merging or force-pushing; Tasker restore unchanged.
