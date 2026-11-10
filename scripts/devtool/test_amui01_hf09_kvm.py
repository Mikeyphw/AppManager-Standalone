#!/usr/bin/env python3
"""Mutation tests around hosted KVM access and receipt integrity."""
import unittest
from check_amui01_hf09_kvm import validate, WORKFLOW, WATCHER, JOB_MARKER, split_api36_job
class KvmHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf=WORKFLOW.read_text(encoding='utf-8')
        cls.watcher=WATCHER.read_text(encoding='utf-8')

    def reject(self, wf=None, watcher=None):
        with self.assertRaises(AssertionError):
            validate(self.wf if wf is None else wf, self.watcher if watcher is None else watcher)

    def test_source_passes(self): self.assertTrue(validate(self.wf,self.watcher))
    def mutate_api36(self, old, new):
        # API35 intentionally has some identical KVM conditions. Mutating
        # the *first* global occurrence makes a negative test falsely fail.
        before, api36, subsequent = split_api36_job(self.wf)
        self.assertEqual(api36.count(old), 1, 'API36 mutation anchor ambiguous')
        return before + JOB_MARKER + api36.replace(old, new, 1) + subsequent

    def test_refuse_chmod_removed(self):
        self.reject(wf=self.mutate_api36('sudo chmod 0666 /dev/kvm', 'true'))

    def test_refuse_chmod_0600(self):
        self.reject(wf=self.mutate_api36('sudo chmod 0666 /dev/kvm',
                                         'sudo chmod 0600 /dev/kvm'))

    def test_refuse_chmod_after_access_gate(self):
        before, api36, subsequent = split_api36_job(self.wf)
        grant='          sudo chmod 0666 /dev/kvm\n'
        closure=("            echo '::error::KVM inaccessible for API36 emulator' "
                 '>&2; exit 1;\n          }\n')
        self.assertEqual(api36.count(grant),1)
        self.assertEqual(api36.count(closure),1)
        altered=api36.replace(grant,'',1).replace(closure,closure+grant,1)
        self.reject(wf=before+JOB_MARKER+altered+subsequent)

    def test_refuse_missing_access_test(self):
        self.reject(wf=self.mutate_api36('test -r /dev/kvm && test -w /dev/kvm', 'true'))

    def test_refuse_device_gate_removed(self):
        # Regression for the real HF09 local failure: both API35 and API36
        # contain this exact guard; only changing the API36 guard is relevant.
        self.assertGreaterEqual(self.wf.count('if [[ ! -c /dev/kvm ]]'), 2)
        self.reject(wf=self.mutate_api36('if [[ ! -c /dev/kvm ]]', 'if [[ false ]]'))

    def test_refuse_no_api36(self):
        self.reject(wf=self.mutate_api36('api-level: 36', 'api-level: 35'))

    def test_refuse_no_receipt_enforcement(self):
        self.reject(wf=self.mutate_api36('if-no-files-found: error',
                                         'if-no-files-found: warn'))

    def test_api35_and_api36_guard_are_distinct(self):
        before, api36, _ = split_api36_job(self.wf)
        self.assertIn('if [[ ! -c /dev/kvm ]]',before)
        self.assertIn('if [[ ! -c /dev/kvm ]]',api36)
        self.assertTrue(validate(self.wf,self.watcher))

    def test_additional_acceptance_job_does_not_duplicate_api36_guard(self):
        before, api36, subsequent = split_api36_job(self.wf)
        self.assertIn('amui05-acceptance:', subsequent,
                      'reproduce AMUI05 exact subsequent-job collision')
        self.assertEqual(api36.count('if-no-files-found: error'), 1)
        self.assertGreaterEqual(subsequent.count('if-no-files-found: error'), 1)
        self.assertTrue(validate(self.wf,self.watcher))

    def test_later_strict_upload_cannot_mask_api36_weakened_upload(self):
        self.assertIn('amui05-acceptance:', self.wf)
        mutated=self.mutate_api36('if-no-files-found: error',
                                  'if-no-files-found: warn')
        self.assertIn('if-no-files-found: error',
                      split_api36_job(mutated)[2],
                      'later strict upload must remain intact')
        self.reject(wf=mutated)

    def test_api36_duplicate_upload_guard_is_refused(self):
        before, api36, subsequent=split_api36_job(self.wf)
        self.reject(wf=before+JOB_MARKER+api36.replace(
            '          if-no-files-found: error\n',
            '          if-no-files-found: error\n          if-no-files-found: error\n',1)+subsequent)

    def test_refuse_no_registration(self): self.reject(wf=self.wf.replace('python3 scripts/devtool/check_amui01_hf09_kvm.py --check','echo skipped',1))
    def test_refuse_watcher_old_source(self): self.reject(watcher=self.watcher.replace('cf8dd9522991fcdf5c0027e58e4eee205985fc09','64337fe557a1c91293d432a89d4d52a158488c99',1))
    def test_refuse_no_pr_checks(self): self.reject(watcher=self.watcher.replace('gh pr checks','gh pr view',1))
    def test_refuse_no_tmpdir(self): self.reject(watcher=self.watcher.replace('TMPDIR','OTHER_TMP'))

if __name__ == '__main__': unittest.main()
