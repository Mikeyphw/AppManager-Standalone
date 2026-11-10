#!/usr/bin/env python3
"""Regression tests of the *same exact embedded launcher* shipped in the ZIP."""
from __future__ import annotations
import copy,sys,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import amui04d_launcher as L
HEAD='f'*40

def new_state(n=4,pending=None,seal=None):
    overlays=[{'sha':x,'branch':L.BRANCH} for x in L.MILESTONES[:n]]
    if n==5:overlays.append({'sha':HEAD,'branch':L.BRANCH})
    return {'schema':1,'gate_every':5,'qualified_gate':{'sha':L.OLD_GATE,'run_id':42751712942} if seal is None else seal,
            'overlays':overlays,'pending_gates':pending or []}

def run_record(head=HEAD,mode='full',run_id=1234,path='.github/workflows/devtool-tasker-ci.yml'):
    return {'id':run_id,'head_sha':head,'head_branch':L.BRANCH,
            'event':'workflow_dispatch','path':path+'@refs/heads/'+L.BRANCH,'inputs':{'mode':mode}}

class GateRecovery(unittest.TestCase):
    def setUp(self):self.d=new_state(5)
    def install(self):
        def write(x):self.d=copy.deepcopy(x)
        return patch.multiple(L,state_read=lambda:self.d,state_write=write,
            stage=lambda x:None)
    def test_four_registered(self):
        self.d=new_state(4)
        with self.install():self.assertEqual(L.check_state(HEAD),'four')
    def test_recorded_awaiting_dispatch(self):
        with self.install():self.assertEqual(L.check_state(HEAD),'recorded')
    def test_pending(self):
        self.d=new_state(5,pending=[{'sha':HEAD,'branch':L.BRANCH,'count':5,'run_id':1234}])
        with self.install():self.assertEqual(L.check_state(HEAD),'pending')
    def test_fully_qualified(self):
        self.d=new_state(4,seal={'sha':HEAD,'run_id':1234});self.d['overlays']=[]
        with self.install():self.assertEqual(L.check_state(HEAD),'qualified')
    def test_wrong_prior_gate(self):
        self.d['qualified_gate']['sha']='b'*40
        with self.install(),self.assertRaises(L.Refused):L.check_state(HEAD)
    def test_wrong_milestone(self):
        self.d['overlays'][0]['sha']='b'*40
        with self.install(),self.assertRaises(L.Refused):L.check_state(HEAD)
    def test_wrong_fifth_sha(self):
        self.d['overlays'][4]['sha']='b'*40
        with self.install(),self.assertRaises(L.Refused):L.check_state(HEAD)
    def test_invalid_pending_other_branch(self):
        self.d['pending_gates']=[{'sha':HEAD,'branch':'wrong','count':5}]
        with self.install(),self.assertRaises(L.Refused):L.check_state(HEAD)
    def test_invalid_extra_pending(self):
        self.d['pending_gates']=[{'sha':HEAD,'branch':L.BRANCH,'count':5}]*2
        with self.install(),self.assertRaises(L.Refused):L.check_state(HEAD)
    def test_candidate_exact_sha(self):
        with patch.object(L,'gh',return_value={'workflow_runs':[run_record()]}):
            self.assertEqual(len(L.find_exact_full_runs(None,HEAD)),1)
    def test_candidate_wrong_sha_ignored(self):
        with patch.object(L,'gh',return_value={'workflow_runs':[run_record('b'*40)]}):
            self.assertEqual(L.find_exact_full_runs(None,HEAD),[])
    def test_candidate_wrong_workflow_ignored(self):
        with patch.object(L,'gh',return_value={'workflow_runs':[run_record(path='.github/workflows/wrong.yml')]}):
            self.assertEqual(L.find_exact_full_runs(None,HEAD),[])
    def test_candidate_wrong_mode_ignored(self):
        with patch.object(L,'gh',return_value={'workflow_runs':[run_record(mode='build')]}):
            self.assertEqual(L.find_exact_full_runs(None,HEAD),[])
    def test_candidate_wrong_branch_ignored(self):
        x=run_record();x['head_branch']='not-main'
        with patch.object(L,'gh',return_value={'workflow_runs':[x]}):
            self.assertEqual(L.find_exact_full_runs(None,HEAD),[])
    def test_reuse_existing_run_no_dispatch(self):
        called=[]
        with self.install(),patch.object(L,'gh',return_value={'workflow_runs':[run_record()]}),patch.object(L,'cmd',side_effect=lambda *a,**k:called.append(a)):
            self.assertEqual(L.ensure_full_pending(None,HEAD),1234)
            self.assertEqual(L.check_state(HEAD),'pending')
            self.assertEqual(self.d['pending_gates'][0]['run_id'],1234)
        self.assertEqual(called,[],'recovery must not dispatch existing workflow twice')
    def test_fresh_dispatch_once_then_save(self):
        called=[]; dispatched=[False]
        def remote(a,repo):
            return {'workflow_runs':[run_record()]} if dispatched[0] else {'workflow_runs':[]}
        def dispatch(*args,**kw):
            called.append(args)
            dispatched[0]=True
            return ''
        with self.install(),patch.object(L,'gh',side_effect=remote),patch.object(L,'cmd',side_effect=dispatch):
            self.assertEqual(L.ensure_full_pending(None,HEAD),1234)
            self.assertEqual(L.check_state(HEAD),'pending')
        self.assertEqual(len(called),1)
        self.assertIn('mode=full',called[0][0])
    def test_duplicate_exact_sha_refused(self):
        with self.install(),patch.object(L,'gh',return_value={'workflow_runs':[run_record(),run_record(run_id=333)]}),self.assertRaises(L.Refused):
            L.ensure_full_pending(None,HEAD)
    def test_existing_pending_no_dispatch(self):
        self.d=new_state(5,pending=[{'sha':HEAD,'branch':L.BRANCH,'count':5,'run_id':1234}])
        with self.install(),patch.object(L,'gh',side_effect=AssertionError('unexpected GitHub query')):
            self.assertEqual(L.ensure_full_pending(None,HEAD),1234)
    def test_qualified_not_dispatched(self):
        self.d=new_state(4,seal={'sha':HEAD,'run_id':1234});self.d['overlays']=[]
        with self.install(),self.assertRaises(L.Refused):L.ensure_full_pending(None,HEAD)
    def test_bad_workflow_run_cannot_qualify(self):
        self.d=new_state(5,pending=[{'sha':HEAD,'branch':L.BRANCH,'count':5,'run_id':1234}])
        bad=run_record('b'*40);bad.update({'head_sha':'b'*40,'status':'completed','conclusion':'success'})
        with self.install(),patch.object(L,'gh',return_value=bad),self.assertRaises(L.Refused):L.full_run(None,HEAD)
    def test_failed_full_run_cannot_qualify(self):
        self.d=new_state(5,pending=[{'sha':HEAD,'branch':L.BRANCH,'count':5,'run_id':1234}])
        bad=run_record();bad.update({'status':'completed','conclusion':'failure'})
        with self.install(),patch.object(L,'gh',return_value=bad),self.assertRaises(L.Refused):L.full_run(None,HEAD)
    def test_non_full_manual_run_refused(self):
        self.d=new_state(5,pending=[{'sha':HEAD,'branch':L.BRANCH,'count':5,'run_id':1234}])
        bad=run_record(mode='test');bad.update({'status':'completed','conclusion':'success'})
        with self.install(),patch.object(L,'gh',return_value=bad),self.assertRaises(L.Refused):L.full_run(None,HEAD)
    def test_missing_fifth_job_refused(self):
        self.d=new_state(5,pending=[{'sha':HEAD,'branch':L.BRANCH,'count':5,'run_id':1234}])
        record=run_record();record.update({'status':'completed','conclusion':'success','run_attempt':1})
        def remote(args,repo):
            if args[1].endswith('/jobs?per_page=100'):
                return {'jobs':[{'name':'Devtool source contract and upstream merge safety','conclusion':'success'}]}
            return record
        with self.install(),patch.object(L,'gh',side_effect=remote),self.assertRaises(L.Refused):L.full_run(None,HEAD)

if __name__=='__main__':unittest.main()
