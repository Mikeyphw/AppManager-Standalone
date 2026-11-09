# AMUI CI01 HF01 — targeted workflow recovery

Baseline exact SHA: `463ff79d952d1e6fb0fdafdea54f3be1c66bbdb3`. PR #2 remains open against `feature/tasker-automation`.

## Fixed
- AMT00 consumer CI contract now checks that **targeted** PR/push checks exist and **full** CI is manual-only, while retaining all pinned Devtool/Gradle/lint safeguards.
- AMT04 source contract now watches AndroidTest changes via targeted workflow; its real Tasker backend/manifest checks are unchanged.
- AMT04B2 and AMT04B2B assert the targeted source checks and still require manual full qualification.
- `Amui02ThemeInstrumentedTest.java` resolves `colorPrimary` from `androidx.appcompat.R.attr` (the nontransitive owner). `colorSurface` remains Material.
- Targeted source job runs the repaired contracts, with source-only mutation tests and no device startup.
- `scripts/devtool/amui_ci_post_push.zsh` is the shared **post-targeted-success** hook for future overlay installers. After independently checking the remote SHA, the existing counter records the exact commit once and dispatches `mode=full` only at overlay 5/10/15... or an explicitly requested high-risk gate.

## Do not conflate checks
- Passing targeted source/compile checks is NOT Android 15/16 device qualification.
- Existing full mode stays manual and still retains lint baseline reports and real emulator/KVM/device gates.
- An outstanding Android 15/16 full run failure does not become a success by using targeted checks.

## Follow-up after hosted targeted success
`python3 -B scripts/devtool/amui_ci_gate.py --status`

If the five-overlay gate is due, the post-push hook dispatches `mode=full` using GitHub CLI; inspect the resulting hosted run. Do not merge or release until every required gate is green. Future overlay installers should call `zsh scripts/devtool/amui_ci_post_push.zsh "$newsha"` after their SHA-verified push and successful targeted CI.
