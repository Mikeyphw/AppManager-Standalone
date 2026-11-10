#!/usr/bin/env python3
"""AMUI-04D HF03: exact-SHA source-pinned quick-chip repair and failed fifth-gate replacement."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
try:
    from rich.console import Console
except ImportError:
    class Console:
        def print(self, *args, **kwargs): print(*args)

C = Console()
REPO = 'Mikeyphw/AppManager-Standalone'
BRANCH = 'feature/amui03b-responsive-list-20261109'
PIN = 'ae14dd90b9e7cefe0033f904bfa226ccfebc4f7c'
OLD_FULL_RUN = 42838584935
OLD_GATE = 'c2a27476c637f702263614707d3b25108781480d'
PRIOR = ('03fc6b256898b17e82872c8c2a8a529ba430c293',
         '0d89ebe7bc432769694d906133054e1c6470fbbb',
         '369fe24d9b374b84f3f5bab40e7c0cdbc6e0c7a5',
         'c407e2091dea029d1bdb7eb68458e35bc45d79fa')
SUBJECT = 'fix(amui04d): repair API35/36 quick-chip main-thread deselection and failed-gate recovery'
NATIVE = 'AMUI04D_HF03_PINNED_DEVTOOL.overlay.zip'
MODIFIED = {
    'app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui03CQuickFiltersInstrumentedTest.java',
    'app/src/main/res/layout/amui03c_quick_filters.xml',
    'scripts/devtool/check_amui03c_consolidated.py',
    'scripts/devtool/test_amui03c_consolidated.py',
}
ADDED = {
    'scripts/devtool/amui04d_hf03_recovery.py',
    'scripts/devtool/test_amui04d_hf03_recovery.py',
    'docs/AMUI04D_HF03_QUICKCHIP_FAILED_GATE_RECOVERY.md',
}
FILES = MODIFIED | ADDED
REQUIRED_JOBS = {
    'Devtool source contract and upstream merge safety',
    'Android Gradle through Devtool (GitHub-hosted only)',
    'AMT-03 Android instrumentation via Devtool emulator',
    'AMUI-01 real package lifecycle on Android 16',
    'AMT-06C disposable debug fixture (hosted only)',
}

class Refused(RuntimeError): pass

def must(condition, reason):
    if not condition: raise Refused(reason)

def stage(name): C.print('AMUI04D_HF03_STAGE ' + name)

def execute(argv, repo=None, show=False, attempts=1):
    for i in range(attempts):
        p = subprocess.run(argv, cwd=repo, text=True,
                           stdout=None if show else subprocess.PIPE,
                           stderr=None if show else subprocess.PIPE, check=False)
        if p.returncode == 0: return p.stdout or ''
        message = (p.stderr or p.stdout or '')[-1200:]
        transient = any(t in message.lower() for t in (
            '502', '503', '504', 'gateway timeout', 'connection abort', 'connection reset',
            'tls handshake timeout', 'connection timed out', 'temporary failure', 'eof'))
        if i + 1 < attempts and transient: time.sleep(min(3 * (i + 1), 15))
        else: raise Refused('command rc='+str(p.returncode)+' '+repr(argv)+' '+message)
    raise Refused('unreachable command retry state')

def git(repo, *args): return execute(['git', *args], repo).strip()
def gh_json(repo, *args): return json.loads(execute(['gh', *args], repo, attempts=5))

def verify_zip(path: Path):
    with zipfile.ZipFile(path) as z:
        must(z.testzip() is None, 'outer ZIP CRC invalid')
        outer = {n:z.read(n) for n in z.namelist()}
    must(set(outer)=={'__main__.py',NATIVE,'README.txt','SHA256SUMS.txt'},'outer payload inventory drift')
    lines=outer['SHA256SUMS.txt'].decode().splitlines()
    must(len(lines)==3,'outer SHA manifest incomplete')
    for row in lines:
        digest,name=row.split('  ',1)
        must(name in outer and hashlib.sha256(outer[name]).hexdigest()==digest,'outer SHA mismatch '+name)
    with zipfile.ZipFile(io.BytesIO(outer[NATIVE])) as z:
        must(z.testzip() is None, 'inner ZIP CRC invalid')
        inner = {n:z.read(n) for n in z.namelist()}
    manifest=json.loads(inner['.devtool-artifact.json'])
    must(manifest['schema_version']==2 and manifest['type']=='overlay' and
         manifest['target']=='app' and manifest['apply']['atomic'] is True,'native Devtool contract changed')
    must(manifest['repository']['branch']==BRANCH and manifest['repository']['remote']==f'https://github.com/{REPO}.git',
         'native target drift')
    must(manifest['apply']['commit']['message']==SUBJECT,'native commit drift')
    must(set(manifest['preflight']['write_paths'])==MODIFIED,'modified-file manifest drift')
    entries=manifest['inventory']['entries']
    must({e['path'] for e in entries}==ADDED,'new-file manifest drift')
    for e in entries:
        must(e['action']=='add' and e['path'] in inner and e['size']==len(inner[e['path']]) and
             e['sha256']==hashlib.sha256(inner[e['path']]).hexdigest(),'native inventory mismatch '+e['path'])
    for key in ('preflight','validation'):
        info=manifest[key]['script']
        must(hashlib.sha256(inner[info['path']]).hexdigest()==info['sha256'],'native script seal drift')
    must(inner['scripts/devtool/amui04d_hf03_recovery.py']==outer['__main__.py'],
         'repository recovery source differs from embedded launcher')
    for marker in ('AMUI04D_HF03_PINNED_PATCH_PASS',"'--dry-run'",'git(\'hash-object\''):
        must(marker in inner['.devtool-artifact/preflight.py'].decode(),'native source preflight missing '+marker)
    for marker in ('check_amui03c_consolidated.py',"unittest discover -s scripts/devtool"):
        must(marker in inner['.devtool-artifact/validate.sh'].decode(),'native full regression gate missing')
    stage('ZIP_NATIVE_SHA_PINS_PASS')
    return outer[NATIVE],inner['.devtool-artifact/preflight.py']

def remote_pr_head(repo):
    result=gh_json(repo,'pr','view','4','-R',REPO,'--json',
                   'state,headRefName,baseRefName,headRefOid')
    must(result['state']=='OPEN' and result['headRefName']==BRANCH and
         result['baseRefName']=='feature/tasker-automation','PR #4 changed/merged')
    return result['headRefOid']

def pr_sync(repo,head):
    for i in range(35):
        if remote_pr_head(repo)==head:return
        if i<34:time.sleep(3)
    raise Refused('PR metadata head stale; rerun this ZIP, no reapply')

def local_repo(repo):
    must(repo.is_dir() and Path(git(repo,'rev-parse','--show-toplevel')).resolve()==repo,'wrong checkout')
    must(not git(repo,'status','--porcelain','--untracked-files=all'),'dirty checkout; never reset')
    origin=git(repo,'remote','get-url','origin').removesuffix('.git')
    must(origin in (f'https://github.com/{REPO}',f'git@github.com:{REPO}',f'ssh://git@github.com/{REPO}'),
         'unexpected git origin')
    execute(['git','fetch','--no-tags','origin','refs/heads/'+BRANCH],repo,show=True)
    execute(['git','switch',BRANCH],repo,show=True)
    execute(['git','merge','--ff-only','FETCH_HEAD'],repo,show=True)
    head=git(repo,'rev-parse','HEAD')
    must(git(repo,'ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head,
         'remote branch drift')
    return head

def state_path(): return Path.home()/'.local/state/appmanager-ci/overlay-gates.json'

def read_state():
    p=state_path()
    must(p.is_file() and not p.is_symlink(),'gate state missing or symlink')
    s=json.loads(p.read_text())
    must(s.get('schema')==1 and s.get('gate_every')==5 and
         isinstance(s.get('overlays'),list) and isinstance(s.get('pending_gates'),list),
         'gate cadence/schema malformed')
    return s

def write_state(state):
    p=state_path()
    must(p.is_file() and not p.is_symlink(),'state changed while saving')
    fd,name=tempfile.mkstemp(dir=p.parent,prefix='.overlay-gates-hf03-')
    try:
        with os.fdopen(fd,'w') as f:
            f.write(json.dumps(state,sort_keys=True,indent=2)+'\n')
            f.flush();os.fsync(f.fileno())
        os.chmod(name,p.stat().st_mode & 0o777)
        os.replace(name,p)
    finally:
        if os.path.exists(name):os.unlink(name)

def gate_phase(state,head):
    if (state.get('qualified_gate') or {}).get('sha')==head:
        must(not state['overlays'] and not state['pending_gates'],'qualified state contains pending work')
        return 'qualified'
    must((state.get('qualified_gate') or {}).get('sha')==OLD_GATE,'old 5/5 qualified seal drift')
    overlays=state['overlays'];pending=state['pending_gates']
    must(len(overlays)==5 and [x.get('sha') for x in overlays[:4]]==list(PRIOR),
         'prior 4/5 milestone lineage drift; refuse counter reset')
    must(all(x.get('branch')==BRANCH for x in overlays),'recorded branch mismatch')
    last=overlays[4].get('sha')
    if last==PIN:
        must(len(pending)==1 and pending[0].get('sha')==PIN and
             pending[0].get('run_id')==OLD_FULL_RUN and pending[0].get('count')==5,
             'failed gate must still be pending at known SHA/run')
        return 'failed-old'
    must(last==head,'fifth entry belongs to unrelated SHA')
    if not pending:return 'staged'
    must(len(pending)==1 and pending[0].get('sha')==head and
         pending[0].get('branch')==BRANCH and pending[0].get('count')==5 and
         isinstance(pending[0].get('run_id'),int),
         'replacement pending record inconsistent')
    return 'pending'

def recover_failed_gate_data(state,new_sha,old_run):
    """Pure, fail-closed failed fifth-milestone substitution, never sixth append."""
    must(len(new_sha)==40 and new_sha!=PIN and all(x in '0123456789abcdef' for x in new_sha),
         'invalid new fifth SHA')
    must(gate_phase(state,new_sha)=='failed-old','not the exact failed fifth milestone')
    must(old_run.get('id')==OLD_FULL_RUN and old_run.get('head_sha')==PIN and
         old_run.get('event')=='workflow_dispatch' and old_run.get('status')=='completed' and
         old_run.get('conclusion')=='failure' and
         str(old_run.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml',
         'old full run not verified failed exact-SHA')
    out=json.loads(json.dumps(state))
    out.setdefault('recovery_history',[]).append({
        'failed_sha':PIN,'failed_run_id':OLD_FULL_RUN,'replaced_by':new_sha,
        'cause':'same AMUI03C quick chip toggle failed on both Android API35 and API36',
    })
    out['overlays'][4]={'sha':new_sha,'branch':BRANCH}
    out['pending_gates']=[]
    must(len(out['overlays'])==5 and gate_phase(out,new_sha)=='staged',
         'replacement incorrectly changed gate cardinality')
    return out

def committed(repo,head):
    must(head!=PIN and git(repo,'rev-parse','HEAD^')==PIN,
         'hotfix commit must directly descend from failed fifth SHA')
    must(git(repo,'log','-1','--format=%s')==SUBJECT,'unexpected hotfix commit')
    paths=set(git(repo,'diff','--name-only',PIN,head).splitlines())
    must(paths==FILES,'commit contains unexpected or missing files: '+str(paths^FILES))
    must(not git(repo,'status','--porcelain','--untracked-files=all'),'dirty commit')
    for a in ('scripts/devtool/check_amui03c_consolidated.py --check',
              'scripts/devtool/test_amui03c_consolidated.py',
              'scripts/devtool/test_amui04d_hf03_recovery.py'):
        execute([sys.executable,'-B',*a.split(' ')],repo,show=True)

def api_run(repo,run_id):
    return gh_json(repo,'api',f'repos/{REPO}/actions/runs/{run_id}')

def targeted(repo,head):
    stage('TARGETED_2_OF_2_EXACT_COMMIT')
    run_id=None
    for i in range(100):
        d=gh_json(repo,'api',f'repos/{REPO}/actions/runs?per_page=100')
        matches=[r for r in d.get('workflow_runs',[])
                 if r.get('head_sha')==head and r.get('event')=='push' and
                 str(r.get('path','')).split('@')[0]=='.github/workflows/amui-targeted-ci.yml']
        if matches:
            run_id=matches[0]['id']
            if matches[0].get('status')=='completed':break
        if i<99:time.sleep(5)
    must(run_id is not None,'targeted run not found for exact hotfix SHA')
    r=api_run(repo,run_id)
    must(r.get('head_sha')==head and r.get('event')=='push' and
         r.get('status')=='completed' and r.get('conclusion')=='success',
         'targeted incomplete/failed; no full dispatch: '+str(run_id))
    jobs=gh_json(repo,'api',f'repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100')['jobs']
    passed={j['name'] for j in jobs if j.get('conclusion')=='success'}
    must({'Targeted source and regression contracts',
          'Scoped Android resource and Java compile (no emulator)'}.issubset(passed),
         'missing targeted tests/Android compiler')
    C.print('AMUI04D_HF03_TARGETED_2_OF_2_PASS',run_id,head)

def exact_full_runs(repo,head):
    data=gh_json(repo,'api',f'repos/{REPO}/actions/workflows/devtool-tasker-ci.yml/runs?event=workflow_dispatch&branch={BRANCH}&per_page=100')
    return [r for r in data.get('workflow_runs',[])
            if r.get('head_sha')==head and r.get('event')=='workflow_dispatch' and
            r.get('head_branch') in (None,BRANCH) and
            str(r.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml' and
            (not isinstance(r.get('inputs'),dict) or r['inputs'].get('mode') in (None,'full'))]

def ensure_fifth_pending(repo,head):
    current=read_state();phase=gate_phase(current,head)
    if phase=='qualified':return None
    if phase=='failed-old':
        run=api_run(repo,OLD_FULL_RUN)
        updated=recover_failed_gate_data(current,head,run)
        # Also prove the two failing jobs before replacing the exact failed SHA.
        jobs=gh_json(repo,'api',f'repos/{REPO}/actions/runs/{OLD_FULL_RUN}/jobs?per_page=100')['jobs']
        failed={j['name'] for j in jobs if j.get('conclusion')=='failure'}
        must(failed=={'AMT-03 Android instrumentation via Devtool emulator',
                      'AMUI-01 real package lifecycle on Android 16'},
             'prior full run failure job fingerprint changed')
        write_state(updated)
        stage('FAILED_FIFTH_SHA_SUPERSEDED_NO_SIXTH_OVERLAY')
        current=read_state();phase=gate_phase(current,head)
    if phase=='pending':return current['pending_gates'][0]['run_id']
    must(phase=='staged','unexpected phase while dispatching')
    candidates=exact_full_runs(repo,head)
    must(len(candidates)<=1,'multiple new exact-SHA full runs; manual reconciliation')
    if not candidates:
        # Persist dispatch intent before the remote side effect. If it disappears
        # mid-flight, retry cannot silently dispatch another identical workflow.
        intent=current.get('hf03_dispatch_intent')
        must(intent is None,'prior dispatch intent exists without visible run; inspect GitHub before retry')
        current['hf03_dispatch_intent']={'sha':head,'branch':BRANCH,'state':'remote_dispatch_may_have_started'}
        write_state(current)
        execute(['gh','workflow','run','devtool-tasker-ci.yml','-R',REPO,'--ref',BRANCH,
                 '-f','mode=full'],repo,show=True,attempts=1)
        for i in range(70):
            candidates=exact_full_runs(repo,head)
            must(len(candidates)<=1,'duplicate fifth-gate dispatch detected')
            if candidates:break
            if i<69:time.sleep(4)
    must(len(candidates)==1,'new full run not visible; pending intent retained, do not redispatch')
    run_id=int(candidates[0]['id'])
    current=read_state()
    must(gate_phase(current,head)=='staged','gate state changed during dispatch')
    current['pending_gates']=[{'sha':head,'branch':BRANCH,'count':5,'run_id':run_id}]
    current.pop('hf03_dispatch_intent',None)
    write_state(current)
    C.print('AMUI04D_HF03_5_OF_5_PENDING_RUN',run_id,head)
    return run_id

def validate_full_run(repo,head,run_id):
    stage('FULL_FIVE_HOSTED_JOBS_POLL_DIRECT_NO_ANNOTATIONS')
    r=None
    for i in range(200):
        r=api_run(repo,run_id)
        must(r.get('head_sha')==head and r.get('event')=='workflow_dispatch' and
             str(r.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml',
             'full workflow wrong SHA/identity')
        if r.get('status')=='completed':break
        if i<199:time.sleep(5)
    must(r.get('status')=='completed' and r.get('conclusion')=='success',
         'full Android gate failed/incomplete: run '+str(run_id)+' conclusion '+str(r.get('conclusion')))
    jobs=gh_json(repo,'api',f'repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100')['jobs']
    passed={j['name'] for j in jobs if j.get('conclusion')=='success'}
    must(REQUIRED_JOBS.issubset(passed),'full gate did not pass all five mandatory jobs')
    return int(r.get('run_attempt',1))

def attest(repo,head,run_id,attempt,tmp):
    stage('STRICT_API35_36_RECEIPT_PNG_AND_LIFECYCLE_AUDIT')
    for api,name in ((35,'appmanager-amt03-instrumentation'),(36,'appmanager-amui01-api36')):
        target=tmp/f'api{api}'
        target.mkdir()
        execute(['gh','run','download',str(run_id),'-R',REPO,
                 '--name',f'{name}-{run_id}-{attempt}','--dir',str(target)],repo,show=True,attempts=3)
    execute([sys.executable,'-B','scripts/devtool/amui04d_receipt_audit.py',
             '--api35',str(tmp/'api35'),'--api36',str(tmp/'api36'),
             '--sha',head,'--run-id',str(run_id)],repo,show=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--repo',type=Path,default=Path.home()/'Code/AppManager')
    args=parser.parse_args()
    package=Path(sys.argv[0]).resolve()
    native,preflight=verify_zip(package)
    if args.verify_only:
        C.print('AMUI04D_HF03_ZIP_INTEGRITY_PASS')
        return
    tmp=Path(os.environ.get('TMPDIR',''))
    must(tmp.is_dir() and os.access(tmp,os.W_OK),'writable $TMPDIR required')
    repo=args.repo.expanduser().resolve()
    head=local_repo(repo)
    if head==PIN:
        must(gate_phase(read_state(),PIN)=='failed-old','prior full gate not known failed/pending')
        with tempfile.TemporaryDirectory(prefix='amui04d-hf03-',dir=tmp) as d:
            overlay=Path(d)/NATIVE;overlay.write_bytes(native)
            script=Path(d)/'preflight.py';script.write_bytes(preflight)
            stage('SOURCE_PINNED_PRELIGHT_DRY_RUN')
            execute([sys.executable,'-B',str(script),'--dry-run'],repo,show=True)
            stage('ATOMIC_DEVTOOL_APPLY')
            execute(['devtool','--repo',str(repo),'--target','app','--yes','apply-overlay',str(overlay)],repo,show=True)
        head=git(repo,'rev-parse','HEAD')
    else:
        stage('RESUME_NEW_HOTFIX_COMMIT_NO_REAPPLY')
    committed(repo,head)
    stage('PUSH_NON_FORCE')
    execute(['git','push','origin',BRANCH],repo,show=True)
    pr_sync(repo,head)
    targeted(repo,head)
    run_id=ensure_fifth_pending(repo,head)
    if run_id is None:
        C.print('AMUI04D_HF03_ALREADY_QUALIFIED',head)
        return
    attempt=validate_full_run(repo,head,run_id)
    with tempfile.TemporaryDirectory(prefix='amui04d-hf03-evidence-',dir=tmp) as d:
        attest(repo,head,run_id,attempt,Path(d))
    stage('ACKNOWLEDGE_NEW_SUCCESSFUL_EXACT_SHA_ONLY')
    execute([sys.executable,'-B','scripts/devtool/amui_ci_gate.py','--ack-run',str(run_id),
             '--repo',str(repo)],repo,show=True)
    must(gate_phase(read_state(),head)=='qualified','fifth gate not sealed after audit')
    pr_sync(repo,head)
    C.print('AMUI04D_HF03_FINAL_5_OF_5_QUALIFIED',run_id,head)
    C.print('AMUI04D_PR_4_OPEN_UNMERGED_NO_FORCE_PUSH')

if __name__=='__main__':
    try:main()
    except (Refused,ValueError,TypeError,KeyError,OSError,zipfile.BadZipFile,
            json.JSONDecodeError) as e:
        C.print('AMUI04D_HF03_REFUSED '+str(e))
        raise SystemExit(1)
