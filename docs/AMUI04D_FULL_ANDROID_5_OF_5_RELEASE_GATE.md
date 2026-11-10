# AMUI-04D — final milestone 5/5, exact-SHA hosted Android acceptance

Parent **c407e2091dea029d1bdb7eb68458e35bc45d79fa**, from qualified AMUI-04C 4/5.

This is a qualification overlay, not a new visual redesign: production source is unchanged.
The entire previous AMUI-01/02/03C/04A/04B/04C suite and Tasker/AMT tests remain mandatory.

## New hosted instrumentation (Android API 35 and 36)

Ten **read-only** device tests: real installed debug package UID/metadata;
package URI parsing and missing-package fallback; multi-package events; replacement
semantics (no deletion performed); partial work-profile scan reporting; truthful
failure receipt; immutable published list snapshot; first-resume behavior; and
Material semantic role/quick-chip inflation. The existing hosted AMUI-01 job
covers actual disposable installation/removal. Tests do not install packages,
change wallpaper, create work profiles, or touch personal data.

The full workflow remains `workflow_dispatch`-only. The fifth successful targeted
milestone runs `scripts/devtool/amui_ci_gate.py --record SHA` and triggers the
existing single exact-commit full Android workflow. The launcher accepts a run
only when **all five** required full-gate jobs succeed. It then downloads
**only** the API 35 and API 36 instrumentation artifact bundles, independently
verifies twelve exact-SHA/test-count UI receipts, four real installed/removed APK
lifecycle receipts, two lifecycle metadata/API identities, two APK SHA-256
manifests, and twelve decoded PNG CRC/IDAT/SHA/geometry
checks (AMUI-04A and AMUI-04B), and finally calls `--ack-run` on that same
completed successful workflow dispatch run. On failure it leaves 5/5 pending;
it never invents a qualified state, resets the counter, or dispatches duplicates.

## What this does not qualify

No physical ARM64 Android 16 proof, live wallpaper replacement, factory-user
work-profile manipulation, forced process termination, or real privately installed
applications are claimed. Those require separate consented device diagnostics.
API 26+ fallback remains covered only by source/theme contracts, not by a hosted
older-API emulator in this 35/36 gate. Do not label an Android release qualified
until the full run and independent evidence verification pass.

## Apply / verify

`python3 /storage/emulated/0/Download/AMUI04D_CONSOLIDATED_FULL_ANDROID_FINAL_GATE_MILESTONE_5_OF_5.overlay.zip`

`python3 /storage/emulated/0/Download/AMUI04D_CONSOLIDATED_FULL_ANDROID_FINAL_GATE_MILESTONE_5_OF_5.overlay.zip --verify-only`

Source tests and local Devtool operations use Termux Python, zsh-safe commands,
`$TMPDIR`, no native Termux Gradle. GitHub-hosted Gradle and instrumented tests
remain authoritative. PR #4 stays open and unmerged.

## HF01 audited replacement (use this instead of original AMUI-04D)

The original package did not independently check AMUI-01's install/uninstall
receipts, and could become stuck after a crash between fifth-overlay counter
registration and full-workflow registration. The replacement archives and
audits genuine disposable APK evidence and uses an interruption-safe,
`--no-dispatch` fifth-milestone record followed by exact-SHA run discovery.

An additional canonical AMUI-00–04 fulfillment matrix is in
`docs/AMUI_FULL_ROADMAP_FULFILLMENT_AUDIT_20261110.md`. Full original
roadmap delivery is **not** asserted just because the hosted 5/5 gate passes.

## HF02 — phase-isolated negative mutation test (2026-11-10)

AMUI04D previously used a global test anchor for `failed==0`, although
AMUI04A/B/C use the same expression in the shared hosted script. HF02 scopes
negative mutations to AMUI04D's final `PYFINAL` parser, and its source checker
requires this exact phase's guard, independently of older phases. Two new
negative regression tests cover cross-phase collisions and duplicate guards.
The native Devtool overlay, all 35/36 evidence/lifecycle/Tasker and manual 5/5
requirements remain consolidated and unchanged in strength.
