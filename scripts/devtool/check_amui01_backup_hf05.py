#!/usr/bin/env python3
"""AMUI-01 HF05: production scan stays fail-closed; backup-only tests avoid fake PM.

Test focus: the Robolectric backup fixture must refresh exactly the backup
metadata it needs, not attempt an authoritative installed-app enumeration.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / 'app/src/test/java/io/github/muntashirakon/AppManager/backup/BackupManagerTest.java'
DB = ROOT / 'app/src/main/java/io/github/muntashirakon/AppManager/db/utils/AppDb.java'
WORKFLOW = ROOT / '.github/workflows/devtool-tasker-ci.yml'
OLD = 'new AppDb().loadInstalledOrBackedUpApplications(ContextUtils.getContext());'
NEW = 'new AppDb().getBackups(true);'

def check(test=None, db=None, workflow=None):
    test = TEST.read_text(encoding='utf-8') if test is None else test
    db = DB.read_text(encoding='utf-8') if db is None else db
    workflow = WORKFLOW.read_text(encoding='utf-8') if workflow is None else workflow
    assert test.count(OLD) == 0, 'HF05_REFUSED: backup-only tests still run installed-app scan'
    assert test.count(NEW) == 12, 'HF05_REFUSED: expected 12 explicit backup-metadata refresh sites'
    assert test.count('@Test') >= 24, 'HF05_REFUSED: backup test cases removed'
    assert 'getBackups(true);' in db and 'updateApplicationsChecked(context)' in db, 'HF05_REFUSED: production DB paths changed'
    assert 'if (packageInfoList == null || packageInfoList.isEmpty())' in db, 'HF05_REFUSED: empty authoritative scans are allowed'
    assert 'AppsDb.getInstance().runInTransaction' in db, 'HF05_REFUSED: transaction guard removed'
    assert 'getBackups(true);\n        updateApplications(context);' in db, 'HF05_REFUSED: production refresh contract changed'
    assert 'python3 scripts/devtool/check_amui01_backup_hf05.py --check' in workflow, 'HF05_REFUSED: source gate not registered'
    assert 'python3 -m unittest discover' in workflow, 'HF05_REFUSED: source mutation suite not registered'
    assert 'app/build/test-results/testDebugUnitTest/**/*.xml' in workflow, 'HF05_REFUSED: JUnit XML not uploaded'
    assert 'app/build/reports/tests/testDebugUnitTest/**' in workflow, 'HF05_REFUSED: detailed HTML report not uploaded'
    # The workflow also has required-error receipts in other jobs. A global
    # substring check can accidentally accept a weakened lint receipt gate.
    lint_heading = '      - name: Upload hosted Android lint report and baseline audit\n'
    lint_boundary = '  device-instrumentation:\n'
    assert workflow.count(lint_heading) == 1, 'HF07_REFUSED: lint upload step missing or duplicated'
    assert workflow.count(lint_boundary) == 1, 'HF07_REFUSED: device-job boundary changed'
    lint_step = workflow.split(lint_heading, 1)[1].split(lint_boundary, 1)[0]
    assert 'appmanager-lint-report-' in lint_step, 'HF07_REFUSED: lint report artifact removed'
    assert 'app/build/reports/lint-results-debug.xml' in lint_step, 'HF07_REFUSED: lint XML upload removed'
    assert 'app/build/reports/lint-results-debug.html' in lint_step, 'HF07_REFUSED: lint HTML upload removed'
    assert 'if-no-files-found: error' in lint_step, 'HF07_REFUSED: lint receipts must fail on missing files'
    assert 'if-no-files-found: warn' not in lint_step, 'HF07_REFUSED: lint receipt cannot use warn'
    assert 'python3 scripts/devtool/check_upstream_lint_baseline.py --report "$xml"' in workflow, 'HF05_REFUSED: lint baseline check removed'
    assert "inputs.mode == 'full' || inputs.mode == 'instrumentation'" in workflow, 'HF05_REFUSED: Tasker API35 gate weakened'
    assert 'amui01-android16:' in workflow, 'HF05_REFUSED: API36 test removed'
    return True

if __name__ == '__main__':
    import argparse
    argparse.ArgumentParser().add_argument('--check',action='store_true')
    check()
    print('AMUI01_HF05_BACKUP_FIX_SOURCE_CONTRACT_PASS')
