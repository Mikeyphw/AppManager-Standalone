# AMUI-03B/03C — Consolidated responsive list and quick filters

Source: the approved functional UI slices from unmerged PR #4, pinned to commit
`0136817deaccbd3db03870df873b8f49ed8e8934`. Target: clean named branch
`feature/amui03bc-consolidated-20261120` at exact `feature/tasker-automation`
commit `0e5137f5325e35f1d1ca9e47180012ea8ecc6258`.

## Implementation

- Keep the existing Material3 card and fourteen adapter-bound view IDs.
- Default compact card shows label, middle-truncated package ID, version and user/system;
  hides SDK, date, UID, signing and backup detail rows on every recycled bind.
- Detailed mode restores per-item SDK, date, UID, signer and backup details;
  setting persists independently of the quick-filter selection and search query.
- Horizontal Material3 chips: All (clear filters), User, System, Frozen,
  Backed up, More filters and Compact/Detailed. Summary reports visible/total apps.
- Filtering preserves existing advanced filters and search. User/System are exclusive.
- Grid responds to window width changes. Item clicks resolve live adapter position.
- Existing long press, icon selection, multi-selection and status stroke branches
  remain intact, with negative source tests to prevent regression.

## Scope / gates

The obsolete PR #4 HFxx/AMUI04/05 scaffold and conflicting workflow expansions are
NOT imported. Current targeted and full source gates remain; one current AMUI03BC
check plus mutation tests is added, and AMUI03A click contract is modernized to
match the safe live-position binding. Lint rules and baselines are unchanged.

Qualification required: native Devtool preflight, complete source regression,
GitHub-hosted Java/resources compile, lint, Android 15/16 instrumentation,
physical viewport screenshot verification at normal and increased font scale.
No signed release claims and no automatic merge.
