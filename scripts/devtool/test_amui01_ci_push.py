#!/usr/bin/env python3
"""Negative tests: development events must not launch the entire emulator matrix."""
from pathlib import Path
import unittest
from check_amui01_ci_push import validate_workflow
ROOT=Path(__file__).resolve().parents[2]
WF=(ROOT/'.github/workflows/devtool-tasker-ci.yml').read_text()

class ManualGateTests(unittest.TestCase):
    def test_full_manual_gate_keeps_all_mandatory_jobs(self):
        self.assertTrue(validate_workflow(WF))
    def test_reject_automatic_push_full(self):
        with self.assertRaises(AssertionError):
            validate_workflow(WF.replace('permissions:', '  push:\n    branches: [feature/tasker-automation]\n\npermissions:',1))
    def test_reject_automatic_pr_full(self):
        with self.assertRaises(AssertionError):
            validate_workflow(WF.replace('permissions:', '  pull_request:\n    branches: [feature/tasker-automation]\n\npermissions:',1))
    def test_reject_removed_manual_full_mode(self):
        with self.assertRaises(AssertionError):
            validate_workflow(WF.replace('options: [source, build, test, lint, instrumentation, full]',
                                         'options: [source, build, test, lint, instrumentation]',1))
    def test_reject_removed_api35_full(self):
        with self.assertRaises(AssertionError):
            validate_workflow(WF.replace("inputs.mode == 'full' || inputs.mode == 'instrumentation'", "inputs.mode == 'source'",1))
    def test_reject_removed_api36_full(self):
        with self.assertRaises(AssertionError):
            validate_workflow(WF.replace("inputs.mode == 'instrumentation' || inputs.mode == 'full'", "inputs.mode == 'source'",1))
    def test_reject_api36_kvm_disabled(self):
        with self.assertRaises(AssertionError):
            validate_workflow(WF.replace("disable-linux-hw-accel: 'false'", "disable-linux-hw-accel: 'true'",1))
    def test_reject_loss_of_strict_lint_report(self):
        with self.assertRaises(AssertionError):
            validate_workflow(WF.replace('Upload hosted Android lint report','Upload optional Android lint summary',1))

if __name__ == '__main__': unittest.main()
