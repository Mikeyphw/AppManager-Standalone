#!/usr/bin/env python3
"""AMUI05 HF03 NDK/CMake hosted-failure recovery: source-pinned Devtool ZIP + hosted evidence.

No local Gradle. No forced merge, no destructive physical-device work, no reset
of previously qualified 5/5 CI state. Recover from GitHub API errors by rerun.
"""
from __future__ import annotations
import argparse,ast,hashlib,io,json,os,re,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
try:
    from rich.console import Console
except ImportError:
    class Console:
        def print(self,*x,**k):print(*x)
C=Console()
REPO='Mikeyphw/AppManager-Standalone'
BRANCH='feature/amui03b-responsive-list-20261109'
PIN='a8f2b2842e03d740d1c2fb3bf6d1a5688234eccb'
QUALIFIED_SHA='46e34adcc490c1ddcf1a2cbcaab96df7440798f8'
FAILED_RUN=42865440211
QUALIFIED_RUN=42850475422
PR=4
SUBJECT='fix(amui05): provision native SDK and repair scoped acceptance mutation gates'
NATIVE='AMUI05_HF03_PINNED_NATIVE_DEVTOOL.overlay.zip'
MODIFIED={'.github/workflows/devtool-tasker-ci.yml',
 'scripts/devtool/check_amui05_acceptance.py',
 'scripts/devtool/test_amui05_acceptance.py',
 'scripts/devtool/amui05_hosted_acceptance.sh',
 'docs/AMUI05_REMAINING_ACCEPTANCE_MATRIX.md'}
ADDED={'scripts/devtool/amui05_hf03_launcher.py',
 'scripts/devtool/test_amui05_hf03_recovery.py'}
FILES=MODIFIED|ADDED
class Refused(RuntimeError):pass

def must(test,reason):
    if not test:raise Refused('AMUI05_REFUSED: '+reason)
def stage(what):C.print('AMUI05_HF03_STAGE '+what)
def run(args,repo=None,show=False,retries=1):
    for attempt in range(retries):
        p=subprocess.run(args,cwd=repo,text=True,stdout=None if show else subprocess.PIPE,
                         stderr=None if show else subprocess.PIPE,check=False)
        if p.returncode==0:return p.stdout or ''
        if attempt+1<retries:time.sleep(3*(attempt+1))
    raise Refused('command failed: '+repr(args)+' '+(p.stderr or p.stdout or '')[-900:])
def git(repo,*args):return run(['git',*args],repo).strip()
def gh(repo,*args):return json.loads(run(['gh',*args],repo,retries=3))
def verify(package):
    with zipfile.ZipFile(package) as z:
        must(z.testzip() is None,'outer ZIP CRC failed')
        outer={n:z.read(n) for n in z.namelist()}
    must(set(outer)=={'__main__.py',NATIVE,'README.txt','SHA256SUMS.txt'},'outer ZIP files drifted')
    rows=outer['SHA256SUMS.txt'].decode().splitlines()
    must(len(rows)==3,'outer SHA table incomplete')
    for row in rows:
        checksum,path=row.split('  ',1)
        must(path in outer and hashlib.sha256(outer[path]).hexdigest()==checksum,'outer checksum '+path)
    with zipfile.ZipFile(io.BytesIO(outer[NATIVE])) as z:
        must(z.testzip() is None,'native ZIP CRC failed')
        inner={n:z.read(n) for n in z.namelist()}
    m=json.loads(inner['.devtool-artifact.json'])
    must(m['schema_version']==2 and m['type']=='overlay' and m['target']=='app','invalid Devtool schema')
    must(m['repository']['branch']==BRANCH and m['apply']['atomic'] is True,'branch/atomic drift')
    must(m['apply']['commit']['message']==SUBJECT,'commit metadata drift')
    must(set(m['preflight']['write_paths'])==MODIFIED,'modified file set mismatch')
    must({e['path'] for e in m['inventory']['entries']}==ADDED,'new file set mismatch')
    for e in m['inventory']['entries']:
        must(e['action']=='add' and e['size']==len(inner[e['path']]) and
             e['sha256']==hashlib.sha256(inner[e['path']]).hexdigest(),
             'new-file digest mismatch '+e['path'])
    for section in ('preflight','validation'):
        entry=m[section]['script'];must(hashlib.sha256(inner[entry['path']]).hexdigest()==entry['sha256'],
                                       'Devtool script digest '+section)
    must(inner['scripts/devtool/amui05_hf03_launcher.py']==outer['__main__.py'],
         'tested in-repo launcher and embedded launcher differ')
    source=inner['.devtool-artifact/preflight.py'].decode()
    ast.parse(source)
    must('PIN='+repr(PIN) in source,'exact parent pin removed')
    base=ast.literal_eval(source.split('BASE=',1)[1].split('\nADDED=',1)[0])
    patches=ast.literal_eval(source.split('PATCHES=',1)[1].split('\ndef must(',1)[0])
    must(set(base)==MODIFIED and len(patches)==6 and
         {b['path'] for b in patches}==MODIFIED,
         'HF01 source-pinned checker/test and workflow patches missing')
    for block in patches:
        must((block['blob'],block['sha256'])==tuple(base[block['path']]) and
             block['count']==1 and block['old']!=block['new'],
             'HF01 pinned source patch drift')
    must(any('sdkmanager --install' in b['new'] and 'ndk;27.0.12077973' in b['new']
             and 'cmake;3.22.1' in b['new'] for b in patches),
         'exact hosted NDK/CMake setup lost')
    must(any('AMUI05_HOSTED_PINNED_NATIVE_TOOLCHAIN_NOT_READY' in b['new']
             for b in patches),'hosted fail-closed native toolchain guard omitted')
    must('scripts/devtool/amui05_hf03_launcher.py' in inner and
         'scripts/devtool/test_amui05_hf03_recovery.py' in inner,
         'failed-run recovery source/test missing from artifact')
    must('github.com/Mikeyphw/AppManager-Standalone' in outer['README.txt'].decode(),
         'provenance absent')
    stage('ZIP_AND_NATIVE_SEALS_PASS')
    return outer[NATIVE],source

def origin_ok(repo):
    x=git(repo,'remote','get-url','origin').removesuffix('.git')
    return x in (f'https://github.com/{REPO}',f'git@github.com:{REPO}',f'ssh://git@github.com/{REPO}')
def ensure_repo(repo):
    must(repo.is_dir() and Path(git(repo,'rev-parse','--show-toplevel')).resolve()==repo,'wrong git worktree')
    must(origin_ok(repo),'origin changed')
    must(not git(repo,'status','--porcelain','--untracked-files=all'),'uncommitted changes; no reset')
    run(['git','fetch','--no-tags','origin','refs/heads/'+BRANCH],repo,show=True)
    run(['git','switch',BRANCH],repo,show=True)
    run(['git','merge','--ff-only','FETCH_HEAD'],repo,show=True)
    head=git(repo,'rev-parse','HEAD')
    must(git(repo,'ls-remote','origin','refs/heads/'+BRANCH).split()[0]==head,'local/remote mismatch')
    return head

def pr_head(repo):
    x=gh(repo,'pr','view',str(PR),'-R',REPO,'--json','state,headRefOid,headRefName,baseRefName')
    must(x['state']=='OPEN' and x['headRefName']==BRANCH and
         x['baseRefName']=='feature/tasker-automation','PR #4 changed/merged')
    return x['headRefOid']
def wait_pr(repo,head):
    for i in range(25):
        if pr_head(repo)==head:return
        if i<24:time.sleep(3)
    raise Refused('PR head not synchronized; rerun to resume')

def validate_historical_qualification():
    path=Path.home()/'.local/state/appmanager-ci/overlay-gates.json'
    must(path.is_file() and not path.is_symlink(),'existing qualified 5/5 state missing')
    before=path.read_bytes()
    state=json.loads(before)
    gate=state.get('qualified_gate') or {}
    must(gate.get('sha')==QUALIFIED_SHA and gate.get('run_id')==QUALIFIED_RUN,
         'existing AMUI04D qualified 5/5 was modified; refusing')
    return path,hashlib.sha256(before).hexdigest()

def ensure_committed(repo,head):
    must(git(repo,'rev-parse','HEAD^')==PIN,'not a direct descendant of qualified parent')
    must(git(repo,'log','-1','--format=%s')==SUBJECT,'commit subject does not match overlay')
    changes=set(git(repo,'diff','--name-only',PIN,head).splitlines())
    must(changes==FILES,'file inventory drift: '+repr(changes^FILES))
    must(not git(repo,'status','--porcelain','--untracked-files=all'),'worktree dirty post-Devtool')
    run([sys.executable,'-B','scripts/devtool/check_amui05_acceptance.py','--check'],repo,show=True)
    run([sys.executable,'-B','scripts/devtool/test_amui05_acceptance.py'],repo,show=True)
    run([sys.executable,'-B','scripts/devtool/test_amui05_receipts.py'],repo,show=True)
    run([sys.executable,'-B','scripts/devtool/test_amui05_hf03_recovery.py'],repo,show=True)

def targeted(repo,head):
    stage('TWO_HOSTED_TARGETED_JOBS_EXACT_SHA')
    rid=None
    for i in range(50):
        runs=gh(repo,'run','list','-R',REPO,'--workflow','amui-targeted-ci.yml',
                '--commit',head,'--event','push','--limit','30','--json','databaseId,headSha')
        hits=[r for r in runs if r.get('headSha')==head]
        if hits:rid=int(hits[0]['databaseId']);break
        if i<49:time.sleep(4)
    must(rid is not None,'targeted run missing')
    for i in range(240):
        r=gh(repo,'api',f'repos/{REPO}/actions/runs/{rid}')
        must(r.get('head_sha')==head and r.get('event')=='push','wrong targeted workflow identity')
        if r.get('status')=='completed':break
        if i<239:time.sleep(5)
    must(r.get('status')=='completed' and r.get('conclusion')=='success','targeted CI did not pass '+str(rid))
    jobs=gh(repo,'api',f'repos/{REPO}/actions/runs/{rid}/jobs?per_page=100')['jobs']
    passed={j['name'] for j in jobs if j.get('conclusion')=='success'}
    must({'Targeted source and regression contracts',
          'Scoped Android resource and Java compile (no emulator)'}.issubset(passed),
         'both targeted jobs not passed')
    C.print('AMUI05_TARGETED_2_OF_2_PASS',rid,head)

def state_file():return Path.home()/'.local/state/appmanager-ci/amui05-acceptance.json'
def stage_write(state):
    p=state_file();p.parent.mkdir(parents=True,exist_ok=True)
    must(not p.is_symlink(),'acceptance state is a symlink')
    fd,name=tempfile.mkstemp(dir=p.parent,prefix='.amui05-hf03-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(state,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        if p.exists():os.chmod(name,p.stat().st_mode&0o777)
        os.replace(name,p)
    finally:
        if os.path.exists(name):os.unlink(name)

def verify_failed_run(repo):
    old=gh(repo,'api',f'repos/{REPO}/actions/runs/{FAILED_RUN}')
    must(old.get('head_sha')==PIN and old.get('status')=='completed' and
         old.get('conclusion')=='failure' and old.get('event')=='workflow_dispatch' and
         str(old.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml',
         'original failed acceptance run identity or status changed')
    jobs=gh(repo,'api',f'repos/{REPO}/actions/runs/{FAILED_RUN}/jobs?per_page=100')['jobs']
    actual={j.get('name'):j.get('conclusion') for j in jobs}
    must(all(actual.get(f'AMUI05 Android API {api} acceptance')=='failure' for api in (30,35,36)),
         'original 3-API failure evidence differs; refusing unsafe supersession')
    must(actual.get('Devtool source contract and upstream merge safety')=='success',
         'original source prerequisite not verified')
    return old

def reconcile(state,head):
    must(isinstance(state,dict) and state.get('schema')==1,
         'original AMUI05 state missing/invalid')
    if state.get('sha')==PIN:
        must(state.get('status')=='pending' and state.get('run_id')==FAILED_RUN and
             state.get('exact_workflow')=='devtool-tasker-ci.yml:instrumentation',
             'old AMUI05 run state not exactly failed pending receipt')
        return {'schema':1,'sha':head,'status':'dispatch_intent',
                'exact_workflow':'devtool-tasker-ci.yml:instrumentation',
                'failed_run_history':[{'sha':PIN,'run_id':FAILED_RUN,'result':'failure'}],
                'previous_qualified_gate':{'sha':QUALIFIED_SHA,'run_id':QUALIFIED_RUN}}
    must(state.get('sha')==head and
         state.get('exact_workflow')=='devtool-tasker-ci.yml:instrumentation' and
         state.get('status') in ('dispatch_intent','pending','HOSTED_EMULATORS_ONLY_QUALIFIED'),
         'unrelated acceptance state cannot be superseded')
    must(state.get('failed_run_history')==[{'sha':PIN,'run_id':FAILED_RUN,'result':'failure'}],
         'prior failure provenance was lost or replaced')
    must(state.get('previous_qualified_gate')=={'sha':QUALIFIED_SHA,'run_id':QUALIFIED_RUN},
         'old qualification provenance lost')
    return state

def discover(repo,head):
    r=gh(repo,'api',f'repos/{REPO}/actions/runs?event=workflow_dispatch&per_page=100')
    return [x for x in r.get('workflow_runs',[]) if x.get('head_sha')==head and
            str(x.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml' and
            x.get('event')=='workflow_dispatch' and x.get('head_branch') in (None,BRANCH) and
            (not isinstance(x.get('inputs'),dict) or x['inputs'].get('mode') in (None,'instrumentation'))]

def acceptance(repo,head,temp):
    stage('RECOVER_FAILED_RUN_AND_MANUAL_API30_35_36_DISPATCH')
    p=state_file()
    must(p.is_file() and not p.is_symlink(),'original pending AMUI05 state missing or unsafe')
    current=json.loads(p.read_text(encoding='utf-8'))
    next_state=reconcile(current,head)
    if next_state is not current:
        stage_write(next_state)
        stage('OLD_FAILED_SHA_PRESERVED_IN_SUPERSESSION_HISTORY')
    state=next_state
    if state['status']=='HOSTED_EMULATORS_ONLY_QUALIFIED':
        C.print('AMUI05_HF03_ALREADY_ACCEPTED',state['run_id'],head)
        return
    runs=discover(repo,head)
    must(len(runs)<=1,'duplicate new-SHA acceptance workflows require manual reconciliation')
    if state['status']=='pending':
        must(len(runs)==1 and int(runs[0]['id'])==state.get('run_id'),
             'pending run mismatch or no longer discoverable')
    elif not runs:
        # Durable intent exists before the network call; if the connection
        # drops after GitHub dispatched, a rerun discovers instead of duplicating.
        run(['gh','workflow','run','devtool-tasker-ci.yml','-R',REPO,'--ref',BRANCH,
             '-f','mode=instrumentation'],repo,show=True,retries=3)
        for i in range(60):
            runs=discover(repo,head)
            must(len(runs)<=1,'duplicate acceptance runs detected')
            if runs:break
            if i<59:time.sleep(4)
    must(len(runs)==1,'new exact-SHA run not discoverable; retain intent')
    rid=int(runs[0]['id'])
    if state['status']!='pending':
        state=dict(state,status='pending',run_id=rid)
        stage_write(state)
    for i in range(420):
        r=gh(repo,'api',f'repos/{REPO}/actions/runs/{rid}')
        must(r.get('head_sha')==head and r.get('event')=='workflow_dispatch' and
             str(r.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml' and
             r.get('head_branch') in (None,BRANCH) and
             (not isinstance(r.get('inputs'),dict) or r['inputs'].get('mode') in (None,'instrumentation')),
             'wrong manual acceptance run identity')
        if r.get('status')=='completed':break
        if i<419:time.sleep(5)
    must(r.get('status')=='completed' and r.get('conclusion')=='success',
         'new hosted acceptance failed or unfinished '+str(rid))
    jobs=gh(repo,'api',f'repos/{REPO}/actions/runs/{rid}/jobs?per_page=100')['jobs']
    required={'Devtool source contract and upstream merge safety',
              'AMT-03 Android instrumentation via Devtool emulator',
              'AMUI-01 real package lifecycle on Android 16'}|{
              f'AMUI05 Android API {n} acceptance' for n in (30,35,36)}
    good={j['name'] for j in jobs if j.get('conclusion')=='success'}
    must(required.issubset(good),'one of six mandatory acceptance jobs failed/skipped')
    attempt=int(r.get('run_attempt',1))
    for api in (30,35,36):
        d=temp/f'api{api}';d.mkdir()
        run(['gh','run','download',str(rid),'-R',REPO,'--name',
             f'amui05-api{api}-{rid}-{attempt}','--dir',str(d)],repo,show=True,retries=3)
    run([sys.executable,'-B','scripts/devtool/amui05_receipt_audit.py',
         '--api30',str(temp/'api30'),'--api35',str(temp/'api35'),
         '--api36',str(temp/'api36'),'--sha',head],repo,show=True)
    stage_write(dict(state,status='HOSTED_EMULATORS_ONLY_QUALIFIED',run_id=rid,
                     api_matrix=[30,35,36],physical='UNVERIFIED',
                     all_24_screens='UNVERIFIED'))
    C.print('AMUI05_HF03_HOSTED_MATRIX_3_OF_3_PASS',rid,head)
    C.print('AMUI05_FULL_ROADMAP_PENDING_PHYSICAL_AND_ALL_REAL_SCREENS')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path.home()/'Code/AppManager')
    p.add_argument('--verify-only',action='store_true')
    p.add_argument('--no-dispatch',action='store_true')
    a=p.parse_args()
    native,preflight=verify(Path(sys.argv[0]).resolve())
    if a.verify_only:print('AMUI05_HF03_ZIPAPP_INTEGRITY_PASS');return
    tmp=Path(os.environ.get('TMPDIR',''))
    must(tmp.is_dir() and os.access(tmp,os.W_OK),'writable $TMPDIR required')
    gate_file,gate_hash=validate_historical_qualification()
    repo=a.repo.expanduser().resolve();head=ensure_repo(repo)
    verify_failed_run(repo)
    must(state_file().is_file() and not state_file().is_symlink(),
         'existing failed AMUI05 receipt missing/unsafe')
    if head==PIN:
        with tempfile.TemporaryDirectory(prefix='amui05-',dir=tmp) as folder:
            directory=Path(folder);artifact=directory/NATIVE;artifact.write_bytes(native)
            script=directory/'preflight.py';script.write_text(preflight)
            stage('EXACT_SOURCE_DRY_RUN')
            run([sys.executable,'-B',str(script),'--dry-run'],repo,show=True)
            stage('ATOMIC_NATIVE_DEVTOOL_APPLY')
            run(['devtool','--repo',str(repo),'--target','app','--yes',
                 'apply-overlay',str(artifact)],repo,show=True)
        head=git(repo,'rev-parse','HEAD')
    else:stage('RESUME_COMMITTED_ACCEPTANCE_OVERLAY_NO_REAPPLY')
    ensure_committed(repo,head)
    stage('PUSH_NON_FORCE')
    run(['git','push','origin',BRANCH],repo,show=True)
    wait_pr(repo,head)
    targeted(repo,head)
    if not a.no_dispatch:
        with tempfile.TemporaryDirectory(prefix='amui05-evidence-',dir=tmp) as folder:
            acceptance(repo,head,Path(folder))
    must(gate_hash==hashlib.sha256(gate_file.read_bytes()).hexdigest(),
         'previous 5/5 qualification state unexpectedly modified')
    C.print('AMUI05_HF03_PR_4_OPEN_PRIOR_5_OF_5_PRESERVED')

if __name__=='__main__':
    try:main()
    except (Refused,OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,zipfile.BadZipFile) as e:
        C.print('AMUI05_HF03_REFUSED '+str(e));raise SystemExit(1)
