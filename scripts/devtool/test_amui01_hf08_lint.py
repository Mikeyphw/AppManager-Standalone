#!/usr/bin/env python3
"""Mutation tests ensure strict lint and unattended PR contract cannot be weakened."""
import unittest
from check_amui01_hf08_lint import check, MAIN, WORKFLOW, WATCHER

class HF08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = MAIN.read_text()
        cls.workflow = WORKFLOW.read_text()
        cls.watcher = WATCHER.read_text()

    def test_source(self):
        self.assertTrue(check(self.main,self.workflow,self.watcher))

    def test_reject_restricted_api(self):
        altered=self.main.replace('focusedView != null && mSearchView != null && mSearchView.hasFocus()', 'focusedView instanceof SearchView.SearchAutoComplete',1)
        with self.assertRaises(AssertionError): check(altered,self.workflow,self.watcher)

    def test_reject_missing_focus_guard(self):
        altered=self.main.replace('mSearchView.hasFocus()', 'true', 1)
        with self.assertRaises(AssertionError): check(altered,self.workflow,self.watcher)

    def test_reject_removing_ime_state(self):
        altered=self.main.replace('mImsVisibleBeforeLeave = insets != null', '/* removed */',1)
        with self.assertRaises(AssertionError): check(altered,self.workflow,self.watcher)

    def test_reject_removing_lint_baseline(self):
        altered=self.workflow.replace('python3 scripts/devtool/check_upstream_lint_baseline.py --report "$xml"','echo lint-circumvented',1)
        with self.assertRaises(AssertionError): check(self.main,altered,self.watcher)

    def test_reject_missing_ci_checker_registration(self):
        altered=self.workflow.replace('python3 scripts/devtool/check_amui01_hf08_lint.py --check','true',1)
        with self.assertRaises(AssertionError): check(self.main,altered,self.watcher)

    def test_reject_no_push(self):
        altered=self.watcher.replace('git push origin "$BRANCH"','print skipped',1)
        with self.assertRaises(AssertionError): check(self.main,self.workflow,altered)

    def test_reject_no_pr_watch(self):
        altered=self.watcher.replace('gh pr checks','gh pr view',1)
        with self.assertRaises(AssertionError): check(self.main,self.workflow,altered)

    def test_reject_unsafe_force_push(self):
        with self.assertRaises(AssertionError): check(self.main,self.workflow,self.watcher+'\n git push --force\n')

    def test_reject_missing_tmpdir(self):
        altered=self.watcher.replace('TMPDIR','SCRATCH')
        with self.assertRaises(AssertionError): check(self.main,self.workflow,altered)

if __name__=='__main__': unittest.main()
