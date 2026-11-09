#!/usr/bin/env python3
"""HF08 lint + unattended PR watcher source gate; no Android Gradle in Termux."""
from pathlib import Path
import argparse
ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / 'app/src/main/java/io/github/muntashirakon/AppManager/main/MainActivity.java'
WORKFLOW = ROOT / '.github/workflows/devtool-tasker-ci.yml'
WATCHER = ROOT / 'scripts/devtool/amui_apply_push_pr_watch.zsh'


def check(main=None, workflow=None, watcher=None):
    main = MAIN.read_text(encoding='utf-8') if main is None else main
    workflow = WORKFLOW.read_text(encoding='utf-8') if workflow is None else workflow
    watcher = WATCHER.read_text(encoding='utf-8') if watcher is None else watcher
    assert main.count('if (focusedView != null && mSearchView != null && mSearchView.hasFocus()) {') == 1, 'HF08_REFUSED: SearchView focus guard missing/duplicated'
    assert 'instanceof SearchView.SearchAutoComplete' not in main, 'HF08_REFUSED: RestrictedApi class reference remains'
    assert main.count('View focusedView = getCurrentFocus();') == 1, 'HF08_REFUSED: current focus tracking missing'
    assert 'focusedView.clearFocus();' in main, 'HF08_REFUSED: search focus not cleared'
    assert 'mImsVisibleBeforeLeave = insets != null' in main, 'HF08_REFUSED: IME persistence logic lost'
    assert 'python3 scripts/devtool/check_amui01_hf08_lint.py --check' in workflow, 'HF08_REFUSED: source gate not registered'
    assert 'python3 scripts/devtool/check_upstream_lint_baseline.py --report "$xml"' in workflow, 'HF08_REFUSED: strict lint baseline removed'
    assert 'if-no-files-found: error' in workflow.split('      - name: Upload hosted Android lint report and baseline audit',1)[1].split('  device-instrumentation:',1)[0], 'HF08_REFUSED: lint upload gate weakened'
    for token in ('git push origin "$BRANCH"', 'gh pr create', 'gh pr checks', 'gh run watch', 'feature/tasker-automation', 'AppManager-Standalone', '[[ -n "${TMPDIR:-}"', 'mktemp "$TMPDIR/', 'apply-overlay "$ARCHIVE"', 'gh run list', 'git status --porcelain', 'git rev-parse HEAD^'):
        assert token in watcher, 'HF08_REFUSED: apply/push/PR watcher contract lost: '+token
    for forbidden in ('git push --force', 'git reset --hard', 'gradlew', 'gradle build', 'gh pr merge', 'gh run cancel'):
        assert forbidden not in watcher, 'HF08_REFUSED: unsafe apply helper: '+forbidden
    return True

if __name__ == '__main__':
    argparse.ArgumentParser().add_argument('--check', action='store_true')
    check()
    print('AMUI01_HF08_LINT_AND_PR_WATCH_SOURCE_PASS')
