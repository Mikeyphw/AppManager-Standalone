#!/usr/bin/env python3
"""Mutation tests for backup-only Robolectric setup, not Android/Gradle tests."""
import unittest
from pathlib import Path
from check_amui01_backup_hf05 import check, TEST, DB, WORKFLOW, OLD, NEW

class AMUI01HF05BackupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.backup = TEST.read_text()
        cls.db = DB.read_text()
        cls.wf = WORKFLOW.read_text()

    def test_source_contract(self):
        self.assertTrue(check(self.backup,self.db,self.wf))

    def test_refuse_background_package_reconciliation_in_robolectric(self):
        with self.assertRaises(AssertionError):
            check(self.backup.replace(NEW,OLD,1),self.db,self.wf)

    def test_refuse_missing_backup_metadata_refresh(self):
        with self.assertRaises(AssertionError):
            check(self.backup.replace(NEW,'/* removed */',1),self.db,self.wf)

    def test_refuse_removed_authoritative_fail_closed_guard(self):
        with self.assertRaises(AssertionError):
            check(self.backup,self.db.replace('if (packageInfoList == null || packageInfoList.isEmpty())','if (false)',1),self.wf)

    def test_refuse_missing_unit_xml_diagnostic(self):
        with self.assertRaises(AssertionError):
            check(self.backup,self.db,self.wf.replace('app/build/test-results/testDebugUnitTest/**/*.xml','removed',1))

    def test_refuse_removing_legacy_lint_gate(self):
        # Mutate the lint artifact step itself, not an unrelated receipt.
        header = '      - name: Upload hosted Android lint report and baseline audit\n'
        prefix, lint_and_rest = self.wf.split(header, 1)
        lint_step, rest = lint_and_rest.split('  device-instrumentation:\n', 1)
        self.assertIn('if-no-files-found: error', lint_step)
        self.assertIn('if-no-files-found: error', rest)
        altered_lint = lint_step.replace('if-no-files-found: error',
                                         'if-no-files-found: warn', 1)
        with self.assertRaises(AssertionError):
            check(self.backup, self.db, prefix + header + altered_lint
                  + '  device-instrumentation:\n' + rest)

    def test_refuse_lint_receipt_deletion_even_when_other_error_receipts_exist(self):
        header = '      - name: Upload hosted Android lint report and baseline audit\n'
        prefix, lint_and_rest = self.wf.split(header, 1)
        lint_step, rest = lint_and_rest.split('  device-instrumentation:\n', 1)
        with self.assertRaises(AssertionError):
            check(self.backup, self.db, prefix + header
                  + lint_step.replace('          if-no-files-found: error\n', '', 1)
                  + '  device-instrumentation:\n' + rest)

    def test_refuse_lint_xml_path_loss(self):
        # The lint runner itself also mentions the XML path. Mutate the
        # artifact upload, leaving the runner unchanged.
        header = '      - name: Upload hosted Android lint report and baseline audit\n'
        prefix, lint_and_rest = self.wf.split(header, 1)
        lint_step, rest = lint_and_rest.split('  device-instrumentation:\n', 1)
        self.assertIn('app/build/reports/lint-results-debug.xml', lint_step)
        altered_lint = lint_step.replace('app/build/reports/lint-results-debug.xml',
                                         'app/build/reports/removed-lint.xml', 1)
        with self.assertRaises(AssertionError):
            check(self.backup, self.db, prefix + header + altered_lint
                  + '  device-instrumentation:\n' + rest)

    def test_refuse_missing_original_tasker_mode(self):
        with self.assertRaises(AssertionError):
            check(self.backup,self.db,self.wf.replace("inputs.mode == 'full' || inputs.mode == 'instrumentation'","inputs.mode == 'source'",1))

if __name__ == '__main__': unittest.main()
