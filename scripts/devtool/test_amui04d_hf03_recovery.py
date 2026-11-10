#!/usr/bin/env python3
"""HF03 strict failed fifth-gate recovery and exact-commit proof (offline)."""
from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import amui04d_hf03_recovery as h

NEW='0123456789abcdef0123456789abcdef01234567'

def state():
    return {'schema':1,'gate_every':5,
            'qualified_gate':{'sha':h.OLD_GATE,'run_id':42751712942},
            'overlays':[{'sha':sha,'branch':h.BRANCH} for sha in (*h.PRIOR,h.PIN)],
            'pending_gates':[{'sha':h.PIN,'branch':h.BRANCH,
                              'count':5,'run_id':h.OLD_FULL_RUN}]}

def old_run():
    return {'id':h.OLD_FULL_RUN,'head_sha':h.PIN,'status':'completed',
            'conclusion':'failure','event':'workflow_dispatch',
            'path':'.github/workflows/devtool-tasker-ci.yml@'+h.PIN}

class GateRecovery(unittest.TestCase):
    def test_exact_old_gate_recognized(self):self.assertEqual('failed-old',h.gate_phase(state(),h.PIN))
    def test_fifth_replacement_is_not_sixth(self):
        o=h.recover_failed_gate_data(state(),NEW,old_run())
        self.assertEqual(5,len(o['overlays']))
        self.assertEqual(list(h.PRIOR),[a['sha'] for a in o['overlays'][:4]])
        self.assertEqual(NEW,o['overlays'][4]['sha'])
        self.assertEqual('staged',h.gate_phase(o,NEW))
        self.assertEqual([],o['pending_gates'])
    def test_original_state_never_mutated(self):
        s=state();h.recover_failed_gate_data(s,NEW,old_run())
        self.assertEqual(h.PIN,s['overlays'][-1]['sha'])
    def test_failed_run_remains_in_history(self):
        o=h.recover_failed_gate_data(state(),NEW,old_run())
        self.assertEqual(h.OLD_FULL_RUN,o['recovery_history'][0]['failed_run_id'])
    def test_old_failed_gate_never_acknowledged(self):
        o=h.recover_failed_gate_data(state(),NEW,old_run())
        self.assertEqual(h.OLD_GATE,o['qualified_gate']['sha'])
    def test_wrong_run_id_rejected(self):
        r=old_run();r['id']=1
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),NEW,r)
    def test_run_succeeded_not_superseded(self):
        r=old_run();r['conclusion']='success'
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),NEW,r)
    def test_incomplete_run_not_superseded(self):
        r=old_run();r['status']='in_progress'
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),NEW,r)
    def test_wrong_event_rejected(self):
        r=old_run();r['event']='push'
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),NEW,r)
    def test_wrong_workflow_rejected(self):
        r=old_run();r['path']='.github/workflows/amui-targeted-ci.yml'
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),NEW,r)
    def test_unrelated_full_sha_rejected(self):
        r=old_run();r['head_sha']=NEW
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),NEW,r)
    def test_sixth_overlay_rejected(self):
        s=state();s['overlays'].append({'sha':NEW,'branch':h.BRANCH})
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(s,NEW,old_run())
    def test_wrong_fourth_sha_rejected(self):
        s=state();s['overlays'][3]['sha']=NEW
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(s,NEW,old_run())
    def test_unrelated_pending_run_rejected(self):
        s=state();s['pending_gates'][0]['run_id']=99
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(s,NEW,old_run())
    def test_counter_refuses_prior_gate_drifts(self):
        s=state();s['qualified_gate']={'sha':h.PIN,'run_id':h.OLD_FULL_RUN}
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(s,NEW,old_run())
    def test_counter_refuses_empty_pending(self):
        s=state();s['pending_gates']=[]
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(s,NEW,old_run())
    def test_refuses_nonhex_new_sha(self):
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),'x'*40,old_run())
    def test_refuses_original_sha_as_new(self):
        with self.assertRaises(h.Refused):h.recover_failed_gate_data(state(),h.PIN,old_run())
    def test_no_premature_qualified_pending(self):
        s=h.recover_failed_gate_data(state(),NEW,old_run())
        s['pending_gates']=[{'sha':NEW,'branch':h.BRANCH,'count':5,'run_id':123}]
        self.assertEqual('pending',h.gate_phase(s,NEW))
        self.assertEqual(h.OLD_GATE,s['qualified_gate']['sha'])
    def test_unrelated_pending_branch_rejected(self):
        s=h.recover_failed_gate_data(state(),NEW,old_run())
        s['pending_gates']=[{'sha':NEW,'branch':'master','count':5,'run_id':123}]
        with self.assertRaises(h.Refused):h.gate_phase(s,NEW)
    def test_no_force_or_local_gradle_in_launcher(self):
        source=Path(h.__file__).read_text()
        self.assertNotIn('git push --force',source)
        self.assertNotIn("'./gradlew'",source)
        self.assertNotIn("'gh','run','watch'",source)
    def test_full_gate_has_five_jobs(self):self.assertEqual(5,len(h.REQUIRED_JOBS))

if __name__=='__main__':unittest.main()
