#!/usr/bin/env python3
"""AMUI03B HF02: recover a failed 5/5 gate using the corrected, pushed descendant SHA.

Never silently resets the counter or converts a failed run into a success.
Dispatches only the original full workflow, at the already-due 5/5 threshold.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = 'Mikeyphw/AppManager-Standalone'
WORKFLOW = 'devtool-tasker-ci.yml'
FAMILY = 'feature/amui03b-responsive-list-20261109'
ORIGINAL = 'b426ea724ec6bbef3951957ea310a52d77e252dd'
FAILED_RUN = 42735142696

def cmd(*args, cwd=None):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if p.returncode:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: '+repr(args)+': '+p.stderr.strip())
    return p.stdout.strip()

def verify_run(record, sha, *, failed=False):
    path = str(record.get('path','')).split('@')[0]
    if (record.get('head_sha') != sha or record.get('event') != 'workflow_dispatch'
            or path != '.github/workflows/'+WORKFLOW):
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: wrong workflow/event/commit')
    if failed and (record.get('status') != 'completed' or record.get('conclusion') != 'failure'):
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: original run was not a failed gate')

def verify_source(root, head):
    if cmd('git','rev-parse','--show-toplevel',cwd=root) != str(root):
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: wrong checkout')
    if cmd('git','branch','--show-current',cwd=root) != FAMILY:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: wrong feature branch')
    if cmd('git','rev-parse','HEAD',cwd=root) != head:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: requested SHA differs from HEAD')
    if cmd('git','status','--porcelain','--untracked-files=all',cwd=root):
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: worktree dirty')
    remote = cmd('git','remote','get-url','origin',cwd=root).removesuffix('.git')
    if remote not in (f'https://github.com/{REPO}',f'git@github.com:{REPO}',f'ssh://git@github.com/{REPO}'):
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: origin mismatch')
    if cmd('git','ls-remote','origin','refs/heads/'+FAMILY,cwd=root).split()[0] != head:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: hotfix not pushed to exact SHA')
    # Must be a descendant of the original failed gate, not another unrelated overlay.
    cmd('git','merge-base','--is-ancestor',ORIGINAL,head,cwd=root)
    if head == ORIGINAL:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: old failed SHA cannot be retried as a fix')

def find_existing_run(sha):
    # Already-created exact-SHA workflow_dispatch runs are never dispatched a second time.
    data=json.loads(cmd('gh','api',f'repos/{REPO}/actions/workflows/{WORKFLOW}/runs?event=workflow_dispatch&branch={FAMILY}&per_page=100'))
    for row in data.get('workflow_runs',[]):
        if row.get('head_sha') == sha and row.get('event') == 'workflow_dispatch':
            verify_run(row,sha)
            return row['id']
    return None

def atomic_save(path, state):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp.'+str(os.getpid()))
    try:
        with temp.open('x',encoding='utf-8') as out:
            out.write(json.dumps(state,indent=2,sort_keys=True)+'\n')
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)

def recover(state, failed, head):
    if state.get('schema') != 1 or state.get('gate_every') != 5:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: unexpected gate schema/cadence')
    overlays=state.get('overlays')
    gates=state.get('pending_gates')
    if not isinstance(overlays,list) or len(overlays)!=5 or not isinstance(gates,list) or len(gates)!=1:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: expected exactly one pending 5/5 gate')
    gate=gates[0]
    if gate.get('count')!=5 or gate.get('branch')!=FAMILY or overlays[-1].get('branch')!=FAMILY:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: unrelated pending gate')
    if overlays[-1].get('sha')==head and gate.get('sha')==head and gate.get('recovered_from')==ORIGINAL:
        return False  # idempotent recovery, e.g. dispatch succeeded before network timeout
    if overlays[-1].get('sha')!=ORIGINAL or gate.get('sha')!=ORIGINAL:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: expected original failed SHA at fifth slot')
    if failed.get('head_sha') != ORIGINAL:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: failed run mismatch')
    overlays[-1]['sha']=head
    gate['sha']=head
    gate['recovered_from']=ORIGINAL
    gate['failed_run_id']=FAILED_RUN
    return True

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--head',required=True)
    p.add_argument('--failed-run',type=int,default=FAILED_RUN)
    p.add_argument('--repo',default='~/Code/AppManager')
    p.add_argument('--state-file',default='~/.local/state/appmanager-ci/overlay-gates.json')
    args=p.parse_args()
    if args.failed_run != FAILED_RUN:
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: unexpected failed gate id')
    root=Path(args.repo).expanduser().resolve()
    verify_source(root,args.head)
    failed=json.loads(cmd('gh','api',f'repos/{REPO}/actions/runs/{args.failed_run}'))
    verify_run(failed,ORIGINAL,failed=True)
    path=Path(args.state_file).expanduser()
    if not path.is_file():
        raise RuntimeError('AMUI03B_HF02_GATE_REFUSED: original local gate state missing')
    state=json.loads(path.read_text(encoding='utf-8'))
    changed=recover(state,failed,args.head)
    if changed:atomic_save(path,state)
    current=find_existing_run(args.head)
    if current is not None:
        print('AMUI03B_HF02_GATE_RUN_EXISTING',current,args.head)
    else:
        cmd('gh','workflow','run',WORKFLOW,'-R',REPO,'--ref',FAMILY,'-f','mode=full')
        print('AMUI03B_HF02_GATE_DISPATCHED',args.head)
    print('AMUI03B_HF02_GATE_COUNT_REMAINS_5_OF_5',args.head)

if __name__=='__main__':
    try:main()
    except (OSError,KeyError,ValueError,RuntimeError) as e:
        print('AMUI03B_HF02_GATE_ERROR:',e,file=sys.stderr)
        raise SystemExit(1)
