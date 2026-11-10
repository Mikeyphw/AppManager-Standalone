# AMUI-04C — app-list lifecycle and publication-epoch race qualification

Parent source: `369fe24d9b374b84f3f5bab40e7c0cdbc6e0c7a5` (qualified milestone 3/5).

## Fixed production race

`MainViewModel` formerly read `mListEpoch` only inside `publishVisibleItems`, **after**
all filtering had finished. A UI change during an old filter could increment the epoch
before the old task captured it, making its stale snapshot look current. Every
filter task now captures `filterEpoch` on entry, passes the exact epoch through
query and flag filtering, and rejects superseded UI emissions on the main thread.
The existing single-threaded DB queue, refresh request-ID gate, deferred status,
immutable snapshots, selected packages and Tasker behavior remain unchanged.

## Android acceptance

`Amui04CLifecycleRaceInstrumentedTest` invokes the actual production
`MainViewModel.publishVisibleItems` method, checks stale vs latest publication,
32 superseded generations, stale refresh-status suppression, immutable partial
status, failure status and first-resume state. It creates only short-lived
ViewModels against hosted disposable Android 15/16 emulators. No packages,
profiles or backup data are written or removed by the test.

Seven instrumented tests on each Android version. Strict exact-commit JSON
receipts are collected as `amui04c-api35.json` and `amui04c-api36.json`, along
with emulator logs. No screenshot is claimed for this logic-focused phase.

## CI policy

This phase is milestone **4/5**. The push runs source regression and scoped
hosted Android Java/resource compilation. No full emulator workflow is
scheduled until the separate fifth milestone. No local Gradle or auto-merge.

Remaining: AMUI-04D full 5/5 acceptance (Android 15/16 device runs, real lifecycle
and app package fixture, visual evidence, wallpaper/theme changes, process death,
final Tasker non-regression) and any needed targeted remediation.
