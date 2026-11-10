# AMUI-04A — device-rendered palette and screenshot acceptance foundation

- Parent: `03fc6b256898b17e82872c8c2a8a529ba430c293` (`feature/amui03b-responsive-list-20261109`) in `Mikeyphw/AppManager-Standalone`; **milestone 2/5, not full release qualification**.
- New Java instrumented test has 5 read-only cases: light, dark, dark+pure-black,
  quick filters and row inflation, and three synthetic rendered UI PNG screenshots.
- Screenshot PNGs are rendered by Android View.draw(Canvas), in the UI thread,
  on the actual API 35/36 emulator, with only synthetic app names.
- The screenshots are **fixtures, not full-screen screenshots** or a claim to
  cover every Material screen. They do not prove wallpaper change, older API fallback,
  live app lifecycle, process recreation, multiuser profiles or device performance.
- The hosted visual runner preserves existing AMUI-02 theme and AMUI-03C checks;
  an exact-commit JSON receipt, three nonempty PNGs and their SHA-256 manifest
  are required on both API 35 and 36. No historical lint debt changes.
- Source checks and mutation tests on targeted push; Gradle only on GitHub Actions.
- Full Android job remains **manual** until fifth cadence milestone. The instrumentation
  is wired now for next manual gate, but it is **not** automatically run at 2/5.
- Tasker security/restore unchanged and paused until full AMUI-04 qualification.
- PR #4 stays open; no auto merge or forced push; no background watchers.
