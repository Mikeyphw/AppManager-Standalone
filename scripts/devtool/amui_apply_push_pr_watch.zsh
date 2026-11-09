#!/usr/bin/env zsh
# AMUI-01: source-pinned Devtool apply -> safe push -> open/reuse PR -> hosted CI/PR watch.
# Reusable on future hotfixes: supply the new overlay path as argument 1 and
# update EXPECTED_SHA to the new, independently audited source commit.
emulate -L zsh
setopt errexit nounset pipefail

readonly REPO="Mikeyphw/AppManager-Standalone"
readonly LOCAL_NAME="AppManager"
readonly BRANCH="feature/amui01-hf01-reissued-20261109"
readonly PR_BASE="feature/tasker-automation"
readonly EXPECTED_SHA="64337fe557a1c91293d432a89d4d52a158488c99"
readonly ARCHIVE="${1:-/storage/emulated/0/Download/AMUI01_HF08_RESTRICTED_API_AND_PR_WATCH_CONSOLIDATED_20261109.overlay.zip}"
readonly TITLE="AMUI-01: installed-app list reliability and hosted Android acceptance"

function refuse() {
  print -ru2 -- "AMUI01_HF08_REFUSED: $*"
  exit 1
}

[[ -n "${TMPDIR:-}" && -d "$TMPDIR" && -w "$TMPDIR" ]] || refuse 'TMPDIR unavailable'
export TMPDIR
[[ -f "$ARCHIVE" ]] || refuse "overlay missing: $ARCHIVE"
for tool in git devtool gh unzip python3 sha256sum mktemp; do
  command -v "$tool" >/dev/null 2>&1 || refuse "missing command: $tool"
done

cd "$HOME/Code/$LOCAL_NAME" || refuse 'repository not found'
[[ "$(git rev-parse --show-toplevel)" == "$PWD" ]] || refuse 'not at Git repository root'
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || refuse 'dirty worktree; preserving unrelated files'
case "$(git remote get-url origin)" in
  "https://github.com/$REPO"|"https://github.com/$REPO.git"|"git@github.com:$REPO"|"git@github.com:$REPO.git"|"ssh://git@github.com/$REPO.git") ;;
  *) refuse 'origin does not target independent AppManager-Standalone repository' ;;
esac

git fetch origin "$BRANCH" "$PR_BASE"
remote_before="$(git rev-parse "refs/remotes/origin/$BRANCH")"
git switch "$BRANCH"
git merge --ff-only "origin/$BRANCH"
local_sha="$(git rev-parse HEAD)"

# Verify canonical manifest on every invocation, including resumed pushes.
unzip -p "$ARCHIVE" .devtool-artifact.json | python3 -c '
import json, sys
x=json.load(sys.stdin)
r=x.get("repository",{})
assert x.get("schema_version")==2 and x.get("type")=="overlay"
assert r.get("name")=="AppManager" and r.get("branch")=="feature/amui01-hf01-reissued-20261109"
assert r.get("remote")=="https://github.com/Mikeyphw/AppManager-Standalone.git"
assert x.get("target")=="app"
print("AMUI01_HF08_MANIFEST_REPO_PASS")
' || refuse 'incorrect overlay repository metadata'
print -- "Archive SHA-256: $(sha256sum "$ARCHIVE")"

if [[ "$local_sha" == "$EXPECTED_SHA" && "$remote_before" == "$EXPECTED_SHA" ]]; then
  print -- '=== Source-pinned dry run (no write) ==='
  unzip -p "$ARCHIVE" .devtool-artifact/preflight.py | python3 - --dry-run || refuse 'overlay preflight failed'
  print -- '=== Devtool apply and complete source validation ==='
  devtool --repo "$PWD" --target app --yes apply-overlay "$ARCHIVE" || refuse 'Devtool failed: no push or PR created'
  local_sha="$(git rev-parse HEAD)"
  [[ "$local_sha" != "$EXPECTED_SHA" ]] || refuse 'Devtool produced no commit'
else
  # A failed network push or PR operation must not require reapplying the patch.
  # Only the exact single-child HF08 commit is eligible for recovery.
  [[ "$local_sha" != "$EXPECTED_SHA" ]] || refuse 'unexpected remote feature head'
  [[ "$(git rev-parse HEAD^)" == "$EXPECTED_SHA" ]] || refuse 'cannot resume: HEAD is not a direct child of source pin'
  [[ "$(git log -1 --format=%s)" == 'fix(app-list): remove restricted AppCompat search type and automate PR qualification' ]] || refuse 'cannot resume: unexpected commit identity'
  [[ "$remote_before" == "$EXPECTED_SHA" || "$remote_before" == "$local_sha" ]] || refuse 'cannot resume: remote branch has diverged'
  python3 -B scripts/devtool/check_amui01_hf08_lint.py --check || refuse 'cannot resume: HF08 source contract failed'
  print -- "AMUI01_HF08_RESUME_VERIFIED $local_sha"
fi
[[ -z "$(git status --porcelain --untracked-files=all)" ]] || refuse 'uncommitted changes remain; refusing push'

print -- '=== Push source commit to standalone origin ==='
git push origin "$BRANCH" || refuse 'push failed; no force-push attempted'
remote_sha="$(git ls-remote origin "refs/heads/$BRANCH" | cut -f1)"
[[ "$remote_sha" == "$local_sha" ]] || refuse 'pushed SHA could not be verified'
print -- "AMUI01_HF08_PUSH_PASS $local_sha"

print -- '=== Open or reuse PR against Tasker integration branch ==='
pr_num="$(gh pr list -R "$REPO" --state open --head "$BRANCH" --json number --jq '.[0].number // empty')" || refuse 'could not check existing PRs'
if [[ -n "$pr_num" ]]; then
  found_base="$(gh pr view "$pr_num" -R "$REPO" --json baseRefName --jq .baseRefName)" || refuse 'cannot inspect existing PR'
  [[ "$found_base" == "$PR_BASE" ]] || refuse "existing PR #$pr_num targets $found_base, not $PR_BASE"
else
  pr_body_file="$(mktemp "$TMPDIR/amui01-hf08-pr.XXXXXXXX.md")" || refuse 'cannot stage PR message'
  trap 'rm -f -- "$pr_body_file"' EXIT
  cat > "$pr_body_file" <<EOF
## AMUI-01 reliability and HF08 hosted lint fix

- Fix SearchView focus handling without referencing AppCompat's restricted SearchAutoComplete type.
- Preserve authoritative installed-package reconciliation and the HF05 backup-only Robolectric setup.
- Keep strict lint baseline, Android 15/16 instrumentation, and source contract tests.
- Record unattended Devtool apply / push / PR / hosted qualification workflow.

Source-pinned post-fix commit: $local_sha.
No local Gradle, no force-push, and no automatic merge.
EOF
  gh pr create -R "$REPO" --base "$PR_BASE" --head "$BRANCH" \
    --title "$TITLE" --body-file "$pr_body_file" || refuse 'PR creation failed after successful push'
  pr_num="$(gh pr list -R "$REPO" --state open --head "$BRANCH" --json number --jq '.[0].number // empty')"
  [[ -n "$pr_num" ]] || refuse 'PR creation response was not reflected in GitHub'
fi
print -- "AMUI01_HF08_PR_OPEN https://github.com/$REPO/pull/$pr_num"

print -- '=== Locate the exact-commit hosted workflow ==='
run_id=''
for (( attempt=1; attempt<=30; attempt++ )); do
  run_id="$(gh run list -R "$REPO" --commit "$local_sha" --event push       --workflow devtool-tasker-ci.yml --limit 20       --json databaseId --jq '.[0].databaseId // empty' || true)"
  [[ -n "$run_id" ]] && break
  sleep 5
done
[[ -n "$run_id" ]] || refuse 'GitHub did not register an exact-commit push run; inspect Actions manually'
observed_sha="$(gh api "repos/$REPO/actions/runs/$run_id" --jq .head_sha)" || refuse 'could not verify workflow SHA'
[[ "$observed_sha" == "$local_sha" ]] || refuse 'workflow SHA differs from pushed commit'
print -- "AMUI01_HF08_RUN https://github.com/$REPO/actions/runs/$run_id"

# Never auto-merge. Hosted Gradle runs on GitHub, never in Termux.
ci_rc=0
print -- '=== Watch hosted GitHub Actions ==='
gh run watch "$run_id" -R "$REPO" --exit-status || ci_rc=$?
pr_rc=0
print -- "=== Watch PR #$pr_num checks ==="
gh pr checks "$pr_num" -R "$REPO" --watch --fail-fast || pr_rc=$?
if (( ci_rc != 0 || pr_rc != 0 )); then
  print -ru2 -- "AMUI01_HF08_HOSTED_FAILURE: run_rc=$ci_rc pr_rc=$pr_rc"
  exit 1
fi
print -- "AMUI01_HF08_HOSTED_PASS: https://github.com/$REPO/pull/$pr_num"
