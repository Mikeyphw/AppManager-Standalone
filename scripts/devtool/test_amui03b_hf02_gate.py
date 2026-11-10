#!/usr/bin/env python3
"""Pure source/metadata mutation tests. Never calls Gradle, GitHub, or Android."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui03b_hf02_gate import ROOT,FILES,FULL,TARGET,AMT,RETRY,validate
from amui_gate_retry import recover,ORIGINAL,FAILED_RUN,FAMILY

class GateParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def mutate(self,path,old,new):
        src=dict(self.src)
        self.assertIn(old,src[path]);src[path]=src[path].replace(old,new,1)
        with self.assertRaises(AssertionError):validate(src)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_targeted_source_contract(self):
        self.mutate(TARGET,'python3 -B scripts/devtool/check_amt04b_contract.py --check','echo bypass-AMT04B')
    def test_targeted_all_tests(self):
        self.mutate(TARGET,"python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v",'echo no-full-regression')
    def test_targeted_this_checker(self):
        self.mutate(TARGET,'python3 -B scripts/devtool/check_amui03b_hf02_gate.py --check','echo bypass')
    def test_targeted_contract_has_gate(self):
        self.mutate(AMT,"'  device-instrumentation:'", "'fake non-existent gate'")
    def test_full_must_stay_manual(self):
        self.mutate(FULL,'  workflow_dispatch:','  push:')
    def test_device_job_cannot_be_removed(self):
        self.mutate(FULL,'  device-instrumentation:','  deleted-device-job:')
    def test_dont_accept_any_failed_run(self):
        self.mutate(RETRY,'verify_run(failed,ORIGINAL,failed=True)','pass  # unsafe')
    def test_dont_skip_ancestor_validation(self):
        self.mutate(RETRY,"cmd('git','merge-base','--is-ancestor',ORIGINAL,head,cwd=root)",'pass # unsafe')

class RecoveryState(unittest.TestCase):
    def fixture(self):
        return {'schema':1,'gate_every':5,'qualified_gate':None,
                'overlays':[{'sha':f'{i:040x}','branch':FAMILY if i==5 else 'feature/amui02'} for i in range(1,5)] +
                           [{'sha':ORIGINAL,'branch':FAMILY}],
                'pending_gates':[{'sha':ORIGINAL,'branch':FAMILY,'count':5}]}
    def failed(self):return {'head_sha':ORIGINAL}
    def test_recovery_replaces_fifth_not_appends_sixth(self):
        state=self.fixture();sha='a'*40
        self.assertTrue(recover(state,self.failed(),sha))
        self.assertEqual(len(state['overlays']),5)
        self.assertEqual(state['overlays'][-1]['sha'],sha)
        self.assertEqual(state['pending_gates'][0]['sha'],sha)
        self.assertEqual(state['pending_gates'][0]['failed_run_id'],FAILED_RUN)
        self.assertFalse(recover(state,self.failed(),sha))
    def test_refuse_extra_overlays(self):
        s=self.fixture();s['overlays'].append({'sha':'2'*40,'branch':FAMILY})
        with self.assertRaises(RuntimeError):recover(s,self.failed(),'a'*40)
    def test_refuse_unrelated_pending_branch(self):
        s=self.fixture();s['pending_gates'][0]['branch']='feature/other'
        with self.assertRaises(RuntimeError):recover(s,self.failed(),'a'*40)
    def test_refuse_wrong_old_sha(self):
        s=self.fixture();s['pending_gates'][0]['sha']='0'*40
        with self.assertRaises(RuntimeError):recover(s,self.failed(),'a'*40)
    def test_refuse_wrong_cadence(self):
        s=self.fixture();s['gate_every']=4
        with self.assertRaises(RuntimeError):recover(s,self.failed(),'a'*40)
    def test_refuse_false_old_run_receipt(self):
        s=self.fixture()
        with self.assertRaises(RuntimeError):recover(s,{'head_sha':'0'*40},'a'*40)

if __name__=='__main__':unittest.main()
