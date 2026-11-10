# AppManager AMUI-00–04 — audited fulfillment, 2026-11-10

Scope: canonical `AMUI_FULL_ORIGINAL_20261109.md` in `AppManager_AMUI03B_HF04_FULL_ROADMAP_HANDOFF_20261110.zip` (not an abbreviated milestone list). Audited public GitHub HEAD before this overlay: `c407e2091dea029d1bdb7eb68458e35bc45d79fa` on `Mikeyphw/AppManager-Standalone`, PR #4 open. The last completed targeted source + hosted compilation CI is `42819805783` on exactly that SHA. This overlay is source-pinned to that SHA and has **not** run its own hosted Android suite before application.

Statuses below mean:
- `implemented / source-checked`: code or source contract visibly present; not a device-level UX guarantee
- `hosted previously qualified`: a cited exact-SHA CI run actually succeeded
- `pending hosted` or `unverified`: needs evidence after this ZIP is applied
- `not delivered`: explicit roadmap acceptance coverage is absent, not euphemistically marked as complete

## AMUI-00 baseline and Tasker safeguards — implemented / qualified historically

- Root fork, exact branch, original source regressions, AMT test contracts and manual-only heavyweight CI are present.
- Source contracts, native Devtool workflow and upstream merge-tree safety are wired. Tasker HMAC scope, permission gates and disposable-data safeguards must remain unchanged.
- CI source/security contracts are included in both targeted `unittest discover` and full CI. **Current full Android acceptance at the new fifth commit is pending.**

## AMUI-01 refresh and package discovery — mostly implemented, acceptance incomplete

Present:
- cache-first startup followed by awaited authoritative AppDb reconciliation, serialized list executor, immutable publication snapshots, request IDs and filter epochs
- real disposable APK install/replacement/uninstall API 35/36 via `amui01_hosted_instrumentation.sh`, five installed tests, one removal test, and a scoped post-refresh receipt
- package URI/UID fallback, replacing semantics, explicit partial scan and failure status, search/filter preservation, new install reconciliation

Not proved or not fully delivered:
- **automatic background package-change reception as experienced by the visible Activity**; the hosted installer tests perform explicit reconciliations, not an end-to-end Activity foreground/background receiver transition
- bounded rescan policy: the current ViewModel queues an authoritative refresh at *each subsequent* `onResume()`, rather than coalescing rapid resumes; no performance receipt for repeated short resumes
- true concurrent install/change/uninstall under work-profile denial, real database fault injection, and independently verified selection after every lifecycle stage

This audit hotfix adds **independent full-gate validation of actual AMUI-01 installed and removed test receipts, exact-SHA API metadata, and the disposable fixture APK SHA-256**. It does not manufacture untested package events.

## AMUI-02 app-wide Material You + optional Pure Black — foundation implemented, complete UI parity NOT proved

Present:
- dynamic color wrapping in `AppearanceUtils`, black root overlay layered after wallpaper dynamic colors, dialog and bottom-sheet/system bar contracts, Pure Black preference restoration
- 24 named Activity root layouts are checked for theme-derived backgrounds, Material `colorError` is used where appropriate
- light/dark/black resource tests run against hosted Android 35/36 when the full workflow is dispatched

**Not delivered as evidence:** all major real screens (details, AppOps, permissions, backup, debloater, profiles, running apps, installer, file manager, code editor chrome, scanner, settings, notifications) captured and inspected in three themes; actual wallpaper-derived palette-switch proof; older API (e.g. 29/30) resource/semantic fallback emulator; real status/navigation insets/contrast across each activity and dialog/sheet; live no-restart settings transitions. Source-checking 24 XML roots is not equivalent to visually qualifying an entire app.

## AMUI-03 app-list UI modernization — key features implemented, broader parity incomplete

Present:
- compact/detailed mode preference, quick chips All/User/System/Frozen/Backed up, advanced filters and clear indication, result count and search, refreshed row styling with selection guards
- responsive grid/virtualization, scrolling, RTL, synthetic 600-row stress and three viewport PNG fixtures
- source contracts retain existing batch actions and safe click routing

Remaining evidence / optional work:
- no end-to-end user-visible keyboard/search/scroll-state persistence and new-app highlighting acceptance on a *real app list*; status badges/readability across all conditions not independently screenshot-approved; user/work-profile combinations and all legacy sort/batch actions not separately run as UI interactions
- the PNGs represent *rendered synthetic UI fixtures*, **not real full-screen screenshots**

## AMUI-04 release qualification — code wired; full gate pending

Present:
- scoped push-based source and hosted Java compile checks; explicit full Android 15/16 (API35/36) five-job workflow, no Termux Gradle
- real disposable APK install/remove/refresh tests, Tasker suite, AMUI-02 resource tests, AMUI-03/04A/B/C synthetic UI, viewport, palette and list-race tests, lint/regression gates
- final AMUI-04D read-only instrumentation tests (10) and strict, exact-commit evidence ZIP validation

Audited HF01 additions to original AMUI-04D:
- **real AMUI-01 lifecycle proof**: both installed/removed receipts per API, paired with `amui01-meta.json` source SHA/API/stages/fixture ID and `amui01-fixture.sha256`; both emulator artifact lists now include that SHA file
- **actual PNG decoding/integrity**: structurally valid PNG chunks, CRC-32, IDAT/zlib image data/scanline size, complete IEND, source geometry and independent SHA-256 checks; invalid header-only pseudo-images rejected
- **recoverable 5/5 dispatch**: stage fifth milestone with `--no-dispatch`, discover exact-run before any dispatch, never use a different SHA or unrelated workflow; register exact run ID before ACK, preserving PR #4 and no auto merge
- added negative tests for incomplete lifecycle evidence, fake PNGs and interrupted gate registration

Still NOT proved by hosted work even after a future green five-job run: physical ARM64 and forced process death, genuine wallpaper changes/re-composition, full activity screen-by-screen parity, real work-profile provisioning; original roadmap calls several of these out. Any statement of **full original roadmap delivered** would be inaccurate.

## Acceptance policy / next decisions

1. Run replacement consolidated 04D ZIP, not older 04D. Transaction must source-pass and targeted hosted compilation pass on a *new* exact descendant SHA.
2. Record 5/5 and dispatch the **existing manual-only** five-job full Android workflow once; both API35/API36 artifacts must independently validate including lifecycle + PNGs before ACK.
3. Do not merge PR #4, claim release readiness, or restart paused Tasker work on source-only success. Record exact full run and inspect output and screenshots; false success remains forbidden.
4. The remaining app-wide UX/physical/profile cases require separate implementation or manual acceptance. They cannot be made true by adding assertions to a source test.

## Provenance

- Canonical roadmap: `roadmaps/AMUI_FULL_ORIGINAL_20261109.md` (provided handoff ZIP)
- Repo: https://github.com/Mikeyphw/AppManager-Standalone
- PR #4: https://github.com/Mikeyphw/AppManager-Standalone/pull/4
- Most recent targeted green prior to 04D: https://github.com/Mikeyphw/AppManager-Standalone/actions/runs/42819805783 (SHA `c407e2091dea029d1bdb7eb68458e35bc45d79fa`)
- Current source checks: `scripts/devtool/check_amui01_contract.py`, `check_amui02_theme.py`, `check_amui03c_consolidated.py`, `check_amui04a_visual_gate.py`, `check_amui04b_viewport_stress.py`, `check_amui04c_refresh_races.py`
- Current hosted runners: `scripts/devtool/amui01_hosted_instrumentation.sh`, `amui02_hosted_theme.sh`; current full gate `.github/workflows/devtool-tasker-ci.yml`.
