# AMUI-02 HF03 — Detached worktree branch guard, consolidating HF02 AAPT repair

Source: 651e7f568018a2c45a1e7a9bd4089ccba7f98abf on feature/amui02-global-material-you-20261109 (PR #2).

The original HF02 preflight used `git branch --show-current == BRANCH`. Devtool
can run its atomic overlay in a **detached linked worktree** where that returns
an empty string, even though the primary checkout has correctly switched to
the feature branch. Log c2f015c75270460695a8760a7ee817c5 stopped there;
Devtool verified its rollback, so HF02 was not successfully applied.

The corrected preflight accepts:
1. A direct checkout on the named feature branch, exact HEAD/source blob pin; OR
2. A detached secondary worktree registered with Git, with exact HEAD and
   feature ref both equal to the pinned commit, plus the primary checkout at
   `$HOME/Code/AppManager` itself checked out on that named feature branch at
   the same commit.

Any other named branch, stale/divergent feature ref, unrelated detached checkout,
wrong origin, dirty unexpected file, or mismatched source blob is refused.

HF03 remains a full replacement for the failed **HF02**; it includes both
`parent=""` style-linking fixes, checker/test mutations, and required Devtool
rollback, automatically committed as the same HF02 source-fix commit title.
Do not apply HF02 first. This change touches no Tasker code, regression
threshold, lint/report upload, KVM gate, release or restore safety.
No Android Gradle tasks are run outside GitHub Actions.
