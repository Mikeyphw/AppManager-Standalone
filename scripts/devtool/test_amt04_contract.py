#!/usr/bin/env python3
"""Read-only Tasker query source and mutational contract tests (no local Gradle)."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from shutil import copy2
from check_amt04_contract import ROOT, REQUIRED, BASE, inspect


class AMT04AContractTests(unittest.TestCase):
    def fixture(self, root):
        for path in REQUIRED:
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            copy2(ROOT / path, root / path)

    def mutate(self, root, relative, anchor, replacement):
        """Refuse a stale test anchor instead of accepting a no-op mutation."""
        path = root / relative
        original = path.read_text(encoding='utf-8')
        self.assertEqual(1, original.count(anchor),
                         'stale or ambiguous mutation anchor in ' + str(relative))
        changed = original.replace(anchor, replacement, 1)
        self.assertNotEqual(original, changed, 'mutation did not change ' + str(relative))
        path.write_text(changed, encoding='utf-8')

    def test_source_contract(self):
        self.assertEqual('PASS', inspect(ROOT)['status'])

    def test_cannot_strip_profile_receiver_coexistence_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.mutate(root, BASE / 'TaskerActionReceiver.java',
                        'marker.containsKey(TaskerPackageQueryWire.KEY_VERSION)', 'false')
            self.assertEqual('FAIL', inspect(root)['status'])

    def test_missing_query_capability_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.mutate(root, BASE / 'TaskerPackageQueryAccess.java',
                        'MessageDigest.isEqual', 'unsafe_equals')
            self.assertEqual('FAIL', inspect(root)['status'])

    def test_privileged_receiver_call_is_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.mutate(root, BASE / 'TaskerPackageQueryReceiver.java',
                        'TaskerPackageQuery.query(context,',
                        'startForegroundService(TaskerPackageQuery.query(context,')
            self.assertEqual('FAIL', inspect(root)['status'])

    def test_manifest_query_editor_removal_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.mutate(root, Path('app/src/main/AndroidManifest.xml'),
                        'android:name=".automation.tasker.TaskerPackageQueryEditActivity"',
                        'android:name=".automation.tasker.NotQueryEditor"')
            self.assertEqual('FAIL', inspect(root)['status'])

    def test_targeted_ci_detects_androidtest_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.mutate(root, Path('.github/workflows/amui-targeted-ci.yml'),
                        'app/src/(main|androidTest)/', 'app/src/main/')
            self.assertEqual('FAIL', inspect(root)['status'])

    def test_targeted_ci_requires_amt04_source_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.mutate(root, Path('.github/workflows/amui-targeted-ci.yml'),
                        'python3 -B scripts/devtool/check_amt04_contract.py --check', '')
            self.assertEqual('FAIL', inspect(root)['status'])

    def test_full_ci_requires_amt04_source_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            self.mutate(root, Path('.github/workflows/devtool-tasker-ci.yml'),
                        'python3 scripts/devtool/check_amt04_contract.py --check', '')
            self.assertEqual('FAIL', inspect(root)['status'])

    def test_full_android_gate_remains_manual_only(self):
        workflow = (ROOT / '.github/workflows/devtool-tasker-ci.yml').read_text(encoding='utf-8')
        self.assertIn('"on":\n  workflow_dispatch:', workflow)
        self.assertNotRegex(workflow, r'(?m)^  (?:push|pull_request):')

    def test_targeted_source_gate_has_feature_push_scope(self):
        workflow = (ROOT / '.github/workflows/amui-targeted-ci.yml').read_text(encoding='utf-8')
        self.assertIn('  push:', workflow)
        self.assertIn("branches: ['feature/amui*', feature/tasker-automation]", workflow)
        self.assertIn('app/src/(main|androidTest)/', workflow)

    def test_stale_mutation_anchor_refuses_no_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            with self.assertRaisesRegex(AssertionError, 'stale or ambiguous mutation anchor'):
                self.mutate(root, Path('.github/workflows/devtool-tasker-ci.yml'),
                            "      - 'app/src/androidTest/java/io/github/muntashirakon/AppManager/automation/**'", '')


if __name__ == '__main__': unittest.main()
