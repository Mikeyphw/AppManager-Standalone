#!/usr/bin/env python3
"""Termux post-push overlay counter. Dispatch full CI only at the configured cadence.

Call with --record HEAD after a successful source-pinned Devtool commit and push.
This is local project state, not a security boundary or replacement for required PR checks.
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
DEFAULT_EVERY = 5


def run(argv: list[str], *, cwd: Path | None = None) -> str:
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        raise RuntimeError(f'CI_GATE_REFUSED: {argv[0]} {argv[1:]!r}: {p.stderr.strip()}')
    return p.stdout.strip()


def get_state(path: Path, every: int) -> dict:
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        if data.get('schema') != 1 or data.get('gate_every') != every:
            raise RuntimeError('CI_GATE_REFUSED: existing cadence differs; never silently reset counter')
        if not isinstance(data.get('overlays'), list) or not isinstance(data.get('pending_gates'), list):
            raise RuntimeError('CI_GATE_REFUSED: corrupt counter')
        return data
    return {'schema': 1, 'gate_every': every, 'overlays': [], 'pending_gates': [], 'qualified_gate': None}


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp.' + str(os.getpid()))
    try:
        temp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def record(args, state: dict) -> str:
    root = Path(args.repo).expanduser().resolve()
    if not (root / '.git').exists():
        # Linked git worktree .git is a file; Git itself decides validity.
        run(['git','rev-parse','--is-inside-work-tree'],cwd=root)
    branch = run(['git','branch','--show-current'],cwd=root)
    if not branch.startswith('feature/amui'):
        raise RuntimeError('CI_GATE_REFUSED: expected a named AMUI development branch')
    head = run(['git','rev-parse','HEAD'],cwd=root)
    if args.record != head:
        raise RuntimeError('CI_GATE_REFUSED: requested SHA must equal HEAD')
    if run(['git','status','--porcelain','--untracked-files=all'],cwd=root):
        raise RuntimeError('CI_GATE_REFUSED: dirty worktree')
    remote = run(['git','remote','get-url','origin'],cwd=root).removesuffix('.git')
    if remote not in (f'https://github.com/{REPO}',f'git@github.com:{REPO}',f'ssh://git@github.com/{REPO}'):
        raise RuntimeError('CI_GATE_REFUSED: unexpected origin')
    actual = run(['git','ls-remote','origin','refs/heads/'+branch],cwd=root).split()
    if not actual or actual[0] != head:
        raise RuntimeError('CI_GATE_REFUSED: exact SHA is not pushed to origin')
    existing = next((o for o in state['overlays'] if o['sha'] == head), None)
    if existing:
        print('CI_GATE_ALREADY_RECORDED',head)
        return head
    state['overlays'].append({'sha':head,'branch':branch})
    print(f"CI_GATE_OVERLAY_REGISTERED: {len(state['overlays'])}/{state['gate_every']} sha={head}")
    return head


def dispatch_if_due(args, state: dict, head: str) -> None:
    count = len(state['overlays'])
    if count == 0 or count % state['gate_every']:
        print(f"CI_GATE_NOT_DUE: count={count} every={state['gate_every']}")
        return
    overlay = state['overlays'][-1]
    if head != overlay['sha']:
        raise RuntimeError('CI_GATE_REFUSED: gate head mismatch')
    if any(g['sha'] == head for g in state['pending_gates']):
        print('CI_GATE_ALREADY_DISPATCHED',head)
        return
    if args.no_dispatch:
        print('CI_GATE_DUE_MANUAL:', 'gh workflow run', WORKFLOW, '-R', REPO, '--ref',overlay['branch'],'-f mode=full')
        return
    # No gh CLI token storage, no merge privileges: user's existing gh auth only.
    run(['gh','workflow','run',WORKFLOW,'-R',REPO,'--ref',overlay['branch'],'-f','mode=full'])
    state['pending_gates'].append({'sha':head,'branch':overlay['branch'],'count':count})
    print('CI_GATE_FULL_DISPATCHED:',head,'(qualification pending; full Android checks must succeed)')


def acknowledge(args, state: dict) -> None:
    x = json.loads(run(['gh','api',f'repos/{REPO}/actions/runs/{args.ack_run}']))
    head = x.get('head_sha')
    if x.get('status') != 'completed' or x.get('conclusion') != 'success' or x.get('event') != 'workflow_dispatch':
        raise RuntimeError('CI_GATE_REFUSED: run is not a successful manual workflow')
    if str(x.get('path','')).split('@')[0] != f'.github/workflows/{WORKFLOW}':
        raise RuntimeError('CI_GATE_REFUSED: wrong workflow')
    gate = next((g for g in state['pending_gates'] if g['sha'] == head),None)
    if gate is None:
        raise RuntimeError('CI_GATE_REFUSED: run SHA has no registered due gate')
    jobs = json.loads(run(['gh','api',f'repos/{REPO}/actions/runs/{args.ack_run}/jobs?per_page=100']))['jobs']
    names = {'Devtool source contract and upstream merge safety',
             'Android Gradle through Devtool (GitHub-hosted only)',
             'AMT-03 Android instrumentation via Devtool emulator',
             'AMUI-01 real package lifecycle on Android 16',
             'AMT-06C disposable debug fixture (hosted only)'}
    done = {j['name'] for j in jobs if j['conclusion']=='success'}
    if not names.issubset(done):
        raise RuntimeError('CI_GATE_REFUSED: full Android 15/16, lint, or regression job skipped/failed')
    state['qualified_gate']={'sha':head,'run_id':args.ack_run}
    state['overlays']=[o for o in state['overlays'] if o['sha'] != head and o not in state['overlays'][:gate['count']]]
    state['pending_gates']=[g for g in state['pending_gates'] if g['sha'] != head]
    print('CI_GATE_QUALIFIED:',head,args.ack_run)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--record',metavar='SHA')
    mode.add_argument('--ack-run',type=int)
    mode.add_argument('--status',action='store_true')
    p.add_argument('--gate-every',type=int,default=DEFAULT_EVERY)
    p.add_argument('--no-dispatch',action='store_true')
    p.add_argument('--repo',default='~/Code/AppManager')
    p.add_argument('--state-file',default='~/.local/state/appmanager-ci/overlay-gates.json')
    args=p.parse_args()
    if not 1 <= args.gate_every <= 30: p.error('gate-every must be 1..30')
    state_path=Path(args.state_file).expanduser()
    state=get_state(state_path,args.gate_every)
    if args.record:
        head=record(args,state)
        save(state_path,state)
        dispatch_if_due(args,state,head)
        save(state_path,state)
    elif args.ack_run is not None:
        acknowledge(args,state)
        save(state_path,state)
    else:
        print(json.dumps(state,indent=2))

if __name__=='__main__':
    try: main()
    except (OSError, ValueError, RuntimeError) as e:
        print('CI_GATE_ERROR:',e,file=sys.stderr)
        raise SystemExit(1)
