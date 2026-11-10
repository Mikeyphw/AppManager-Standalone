#!/usr/bin/env python3
"""AMUI05 HF03 failed-run provenance, crash-safe dispatch and false-pass refusal."""
from __future__ import annotations
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
FILE=Path(__file__).with_name('amui05_hf03_launcher.py')
spec=importlib.util.spec_from_file_location('amui05_hf03_launcher_tested',FILE)
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
SHA='f'*40
OLD={'schema':1,'sha':mod.PIN,'status':'pending','run_id':mod.FAILED_RUN,
     'exact_workflow':'devtool-tasker-ci.yml:instrumentation'}
HISTORY=[{'sha':mod.PIN,'run_id':mod.FAILED_RUN,'result':'failure'}]
PRIOR={'sha':mod.QUALIFIED_SHA,'run_id':mod.QUALIFIED_RUN}
class HF03Recovery(unittest.TestCase):
    def test_initial_failed_gate_reconciles(self):
        x=mod.reconcile(dict(OLD),SHA)
        self.assertEqual(x['status'],'dispatch_intent')
        self.assertEqual(x['sha'],SHA)
        self.assertEqual(x['failed_run_history'],HISTORY)
        self.assertEqual(x['previous_qualified_gate'],PRIOR)
    def test_failed_run_history_preserved_on_retry(self):
        x=mod.reconcile(dict(OLD),SHA)
        self.assertIs(mod.reconcile(x,SHA),x)
    def test_pending_run_resume_preserves_id(self):
        x=dict(mod.reconcile(dict(OLD),SHA),status='pending',run_id=1234)
        self.assertIs(mod.reconcile(x,SHA),x)
        self.assertEqual(x['run_id'],1234)
    def test_success_only_when_explicitly_marked(self):
        x=dict(mod.reconcile(dict(OLD),SHA),status='HOSTED_EMULATORS_ONLY_QUALIFIED',run_id=1234)
        self.assertIs(mod.reconcile(x,SHA),x)
    def test_wrong_original_sha_refused(self):
        with self.assertRaises(mod.Refused):mod.reconcile(dict(OLD,sha='1'*40),SHA)
    def test_fake_original_success_refused(self):
        with self.assertRaises(mod.Refused):mod.reconcile(dict(OLD,status='HOSTED_EMULATORS_ONLY_QUALIFIED'),SHA)
    def test_wrong_original_run_refused(self):
        with self.assertRaises(mod.Refused):mod.reconcile(dict(OLD,run_id=42850475422),SHA)
    def test_old_run_pending_must_not_be_marked_qualified(self):
        x=mod.reconcile(dict(OLD),SHA)
        self.assertEqual(x['status'],'dispatch_intent')
        self.assertNotIn('run_id',x)
    def test_malformed_schema_refused(self):
        with self.assertRaises(mod.Refused):mod.reconcile(dict(OLD,schema=3),SHA)
    def test_missing_failure_history_refused(self):
        x=mod.reconcile(dict(OLD),SHA);x.pop('failed_run_history')
        with self.assertRaises(mod.Refused):mod.reconcile(x,SHA)
    def test_changed_prior_qualified_gate_refused(self):
        x=mod.reconcile(dict(OLD),SHA);x['previous_qualified_gate']={'sha':mod.PIN,'run_id':55}
        with self.assertRaises(mod.Refused):mod.reconcile(x,SHA)
    def test_no_sixth_milestone_created(self):
        x=mod.reconcile(dict(OLD),SHA)
        self.assertNotIn('overlays',x)
        self.assertEqual(x['previous_qualified_gate'],PRIOR)
    def test_reject_failed_workflow_identity_change(self):
        r={'head_sha':mod.PIN,'status':'completed','conclusion':'failure',
           'event':'workflow_dispatch','path':'.github/workflows/devtool-tasker-ci.yml'}
        jobs={'jobs':[{'name':'Devtool source contract and upstream merge safety','conclusion':'success'}]+[
            {'name':f'AMUI05 Android API {n} acceptance','conclusion':'failure'} for n in (30,35,36)]}
        with patch.object(mod,'gh',side_effect=[r,jobs]): self.assertEqual(mod.verify_failed_run(None),r)
        with patch.object(mod,'gh',side_effect=[dict(r,head_sha='0'*40),jobs]):
            with self.assertRaises(mod.Refused):mod.verify_failed_run(None)
    def test_no_successfully_completed_old_run_can_be_superseded(self):
        r={'head_sha':mod.PIN,'status':'completed','conclusion':'success',
           'event':'workflow_dispatch','path':'.github/workflows/devtool-tasker-ci.yml'}
        with patch.object(mod,'gh',return_value=r):
            with self.assertRaises(mod.Refused):mod.verify_failed_run(None)
    def test_missing_failed_api_is_refused(self):
        r={'head_sha':mod.PIN,'status':'completed','conclusion':'failure',
           'event':'workflow_dispatch','path':'.github/workflows/devtool-tasker-ci.yml'}
        jobs={'jobs':[{'name':'Devtool source contract and upstream merge safety','conclusion':'success'},
                      {'name':'AMUI05 Android API 30 acceptance','conclusion':'failure'},
                      {'name':'AMUI05 Android API 35 acceptance','conclusion':'success'},
                      {'name':'AMUI05 Android API 36 acceptance','conclusion':'failure'}]}
        with patch.object(mod,'gh',side_effect=[r,jobs]):
            with self.assertRaises(mod.Refused):mod.verify_failed_run(None)
    def test_discovery_must_use_new_sha_and_workflow(self):
        valid={'id':3,'head_sha':SHA,'event':'workflow_dispatch','head_branch':mod.BRANCH,
               'path':'.github/workflows/devtool-tasker-ci.yml'}
        records=[valid,dict(valid,id=4,head_sha=mod.PIN),dict(valid,id=5,path='wrong.yml'),
                 dict(valid,id=6,event='push'),dict(valid,id=7,inputs={'mode':'full'})]
        with patch.object(mod,'gh',return_value={'workflow_runs':records}):
            self.assertEqual(mod.discover(None,SHA),[valid])
    def test_source_forbids_unsafe_automation(self):
        s=FILE.read_text()
        self.assertNotIn('git push --force',s)
        self.assertNotIn('gh pr merge',s)
        self.assertNotIn('git reset --hard',s)
        self.assertIn('OLD_FAILED_SHA_PRESERVED_IN_SUPERSESSION_HISTORY',s)
        self.assertIn('QUALIFIED_SHA',s)
        self.assertIn('amui05_receipt_audit.py',s)
        self.assertIn("'HOSTED_EMULATORS_ONLY_QUALIFIED'",s)
        self.assertIn('stage_write(dict(state,status=',s)
        self.assertNotIn('state_write(dict(state,status=',s)

    def test_verified_matrix_success_persists_qualified_state(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory(prefix='amui05-hf03-state-') as td:
            temp=Path(td)
            state_file=temp/'acceptance-state.json'
            current=dict(mod.reconcile(dict(OLD),SHA),status='pending',run_id=1234)
            state_file.write_text(json.dumps(current),encoding='utf-8')
            r={'id':1234,'head_sha':SHA,'event':'workflow_dispatch','head_branch':mod.BRANCH,
               'path':'.github/workflows/devtool-tasker-ci.yml','status':'completed',
               'conclusion':'success','run_attempt':1,'inputs':{'mode':'instrumentation'}}
            names={'Devtool source contract and upstream merge safety',
                   'AMT-03 Android instrumentation via Devtool emulator',
                   'AMUI-01 real package lifecycle on Android 16'} | {
                   f'AMUI05 Android API {api} acceptance' for api in (30,35,36)}
            jobs={'jobs':[{'name':n,'conclusion':'success'} for n in names]}
            with patch.object(mod,'state_file',return_value=state_file), \
                 patch.object(mod,'discover',return_value=[r]), \
                 patch.object(mod,'gh',side_effect=[r,jobs]), \
                 patch.object(mod,'run',return_value='') as executed:
                mod.acceptance(None,SHA,temp)
            after=json.loads(state_file.read_text(encoding='utf-8'))
            self.assertEqual(after['status'],'HOSTED_EMULATORS_ONLY_QUALIFIED')
            self.assertEqual(after['run_id'],1234)
            self.assertEqual(after['api_matrix'],[30,35,36])
            self.assertEqual(after['failed_run_history'],HISTORY)
            self.assertEqual(after['previous_qualified_gate'],PRIOR)
            self.assertEqual(after['physical'],'UNVERIFIED')
            self.assertEqual(after['all_24_screens'],'UNVERIFIED')
            self.assertEqual(executed.call_count,4,'three downloads and one receipt audit required')


if __name__=='__main__':unittest.main(verbosity=2)
