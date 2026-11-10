# AMUI-05 — consolidated outstanding roadmap acceptance (not a release claim)

**NOT_FULL_ROADMAP_ACCEPTANCE.** This patch leaves the successfully qualified AMUI-04D full 5/5 gate untouched: exact SHA `46e34adcc490c1ddcf1a2cbcaab96df7440798f8`, run 42850475422. It adds a **separate manual-dispatch-only** acceptance workflow and privacy-preserving physical acceptance tooling. A new source-check or emulator success does NOT certify every feature or justify a PR merge.

## Where the original roadmap stands

- AMUI-00: baseline, security and Tasker non-regression guarded by existing CI.
- AMUI-01: serialized authoritative refresh, immutable snapshots, event URI handling and actual disposable APK install/replacement/uninstall proven on API35 and 36. Background Activity resume/restart and real work-profile denial remain separate checks.
- AMUI-02: Material3 infrastructure and 24 activity XML roots verified. This is **not** proof of all 24 activity screens, every dialog/sheet, bars and notification surface in three modes. The new hosted API30 run verifies older-Android resource compatibility. The Android35/36 wallpaper class actually calls WallpaperManager.setBitmap on an isolated disposable emulator and checks that the system wallpaper-color source changes; it never modifies a user's phone. A passing test alone does not guarantee that every open Activity dynamically recolors without recreation.
- AMUI-03: compact/detail mode, responsive list and quick filters implemented and device tests passed; all legacy batch operations and keyboard/scroll UX need real screen inspection.
- AMUI-04: source, Gradle, lint, API35/36, disposable APK, Tasker and independent receipt proof already qualified by run 42850475422 on the exact SHA above.

## Consolidated acceptance: what the new overlay adds

1. Source-indexed 24 activity root audit (same Material background contract as existing theme check), with mutation tests and *no replacement* of old source/security contracts.
2. Manual-only the **existing** `.github/workflows/devtool-tasker-ci.yml` in `mode=instrumentation`: exact commit, pinned Devtool source, real seven-test compatible Material theme class on Android 11/API30, Android15/API35 and Android16/API36, plus two real wallpaper-service tests on disposable API35 and API36 emulators. Java/Gradle runs only on GitHub Actions.
3. Independent `amui05_receipt_audit.py` checks all three API bundles, exact SHA, test counts, zero skipped/failed, emulator identity and absence of unsupported physical/profile claims. All required device jobs must succeed before any AMUI05-hosted receipt is called green.
4. Optional physical ARM64 Android16 **read-only** inventory script: requires an exact consent token and ADB serial. Captures only SDK/ABI, generic hardware check, debug app install boolean and aggregate user/profile counts. Does not save serial, package lists, usernames, screenshot or UID. It will print **INSPECTION_ONLY**, not physical qualification.
5. `amui05_manual_matrix.py`: an unapproved, exact-commit matrix for **24 activity screens × light/dark/dark+pure-black** and ten additional lifecycle, palette, dialog, edge-to-edge, work-profile, scroll/selection and physical criteria. A case is accepted only after a human records approval and a matching local screenshot PNG SHA-256. It refuses incomplete, corrupted or mixed-commit records.

## How to finish the remaining tests without inventing evidence

- Apply consolidated Python executable Devtool zipapp from Termux; require clean branch and source-pinned parent; run all regression contracts and targeted hosted Java compilation before any separate AMUI05 workflow dispatch.
- For fresh API30/35/36 emulator acceptance, manually dispatch `devtool-tasker-ci.yml` with `mode=instrumentation` or use launcher continuation. Its API 35/36 wallpaper writes are confined to CI-disposable emulators; it does not change user wallpaper.
- Physical diagnostics on the user's Android 16 arm64 device, **only with explicit read-only consent**:
  `python3 -B scripts/devtool/amui05_physical_acceptance.py --serial YOUR_ADB_SERIAL --sha EXACT_COMMIT --ack I_AUTHORIZE_READ_ONLY_DEVICE_PROBE --output "$TMPDIR/amui05-physical.json"`.
  Does not prove real profile lifecycle, UI correctness, process death or live wallpaper changes. Those still need consented manual functional tests; never auto-install, create users, reboot, kill processes, change wallpaper or perform backups on personal data.
- Create manual evidence matrix:
  `python3 -B scripts/devtool/amui05_manual_matrix.py --init --file "$TMPDIR/amui05-manual.json" --sha EXACT_COMMIT`
  Navigate the app through each tested real Activity and mode, capture any screenshots *yourself*, review them, enter approved_by + screenshot_path + screenshot_sha256 and set status PASS. These screenshots can expose private app metadata, so keep them local and do not upload by default. Verify with `--verify` instead of `--init`; it will refuse every missing case.
- Negative results or unsupported real work-profile cases remain **PENDING/UNVERIFIED** and prevent entire-roadmap acceptance. The previous five-job hosted gate remains qualified historically.

## Release boundary

A green AMUI05 hosted matrix means *older API fallback and disposable-emulator wallpaper sources are tested*, not full app screen visual parity or physical ARM64 acceptance. Do not merge PR #4, claim production release readiness, or unpause Tasker work because of synthetic screenshots, a static XML audit or an inspected-only physical handset. Screen-by-screen and actual usage must be reviewed. The ledger intentionally begins PENDING for all 82 cases.

## HF03: recover hosted native toolchain and scoped test anchors (2026-11-10)

Manual instrumentation run **42865440211** failed on Android 11 (API30), 15 (API35)
 and 16 (API36) before **any Android test ran**. All three device receipts
 reported `device-readiness`: exact NDK 27.0.12077973 and CMake 3.22.1/Ninja
 were not installed in the new AMUI05 matrix job. The earlier AMUI04D
 qualified 5/5 run 42850475422 remains unchanged and is not evidence for
 acceptance of the subsequent AMUI05 commit.

HF03 adds `android-actions/setup-android@v4`, installs the exact platform,
 build-tools, NDK and CMake packages already required by the established
 Android15/16 jobs, verifies the native compiler, `ndk-build`, `cmake`,
 `ninja`, and `aapt` *before* launching the emulator. The hosted wrapper also
 checks these native binaries fail-closed before calling instrumentation.
 The new Python launcher verifies exact failed-run identity, retains
 its SHA/run ID as historical evidence, and creates no duplicate dispatch.
 GitHub-hosted results and manual/physical acceptance remain pending until
 real checks pass; never call SDK readiness an app UI acceptance pass.

## HF01: API36 legacy mutation contract and new-job isolation

The full 707-test Devtool validation originally refused before commit because
`test_amui01_hf09_kvm.py` counted `if-no-files-found: error` across *both* the
existing `amui01-android16` job and the appended AMUI05 matrix. The legacy
checker and its mutation tests now isolate the original API36 job by its next
top-level YAML job boundary. The API36 receipt policy must still contain exactly
one strict `if-no-files-found: error` and no `warn`; the independently strict
AMUI05 upload continues to be checked by AMUI05 source contracts. New negative
tests reproduce the two guards, reject weakening API36 even while AMUI05 remains
strict, and reject duplicate strict API36 upload policies. This is a complete
replacement source-pinned overlay against the same qualified parent. Hosted
acceptance remains pending until real GitHub runs succeed.
