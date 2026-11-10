#!/usr/bin/env python3
"""AMUI05 manual remaining-acceptance matrix: source-pinned Devtool ZIP + hosted evidence.

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
PIN='46e34adcc490c1ddcf1a2cbcaab96df7440798f8'
QUALIFIED_RUN=42850475422
PR=4
SUBJECT='test(amui05): consolidate fallback, wallpaper and manual UX acceptance with strict receipts'
NATIVE='AMUI05_ACCEPTANCE_PINNED_NATIVE_DEVTOOL.overlay.zip'
MODIFIED={'.github/workflows/amui-targeted-ci.yml','.github/workflows/devtool-tasker-ci.yml',
          'scripts/devtool/check_amui01_hf09_kvm.py','scripts/devtool/test_amui01_hf09_kvm.py'}
ADDED={
 'scripts/devtool/amui05_hosted_acceptance.sh',
 'scripts/devtool/amui05_physical_acceptance.py',
 'scripts/devtool/amui05_manual_matrix.py',
 'scripts/devtool/amui05_receipt_audit.py',
 'scripts/devtool/check_amui05_acceptance.py',
 'scripts/devtool/test_amui05_acceptance.py',
 'scripts/devtool/test_amui05_receipts.py',
 'scripts/devtool/amui05_launcher.py',
 'app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui05CompatibilityInstrumentedTest.java',
 'app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui05WallpaperInstrumentedTest.java',
 'docs/AMUI05_REMAINING_ACCEPTANCE_MATRIX.md',
}
FILES=MODIFIED|ADDED
class Refused(RuntimeError):pass

def must(test,reason):
    if not test:raise Refused('AMUI05_REFUSED: '+reason)
def stage(what):C.print('AMUI05_STAGE '+what)
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
    must(inner['scripts/devtool/amui05_launcher.py']==outer['__main__.py'],
         'tested in-repo launcher and embedded launcher differ')
    source=inner['.devtool-artifact/preflight.py'].decode()
    ast.parse(source)
    must('PIN='+repr(PIN) in source,'exact parent pin removed')
    base=ast.literal_eval(source.split('BASE=',1)[1].split('\nADDED=',1)[0])
    patches=ast.literal_eval(source.split('PATCHES=',1)[1].split('\ndef refuse(',1)[0])
    must(set(base)==MODIFIED and len(patches)==5 and
         {b['path'] for b in patches}==MODIFIED,
         'HF01 source-pinned checker/test and workflow patches missing')
    for block in patches:
        must((block['blob'],block['sha256'])==tuple(base[block['path']]) and
             block['count']==1 and block['old']!=block['new'],
             'HF01 pinned source patch drift')
    must(any('def split_api36_job(' in b['new'] for b in patches),
         'HF01 API36 job-only guard omitted')
    must(any('test_later_strict_upload_cannot_mask_api36_weakened_upload' in b['new'] for b in patches),
         'HF01 negative regression omitted')
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
    must(gate.get('sha')==PIN and gate.get('run_id')==QUALIFIED_RUN,
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
    if p.is_symlink():raise Refused('unsafe acceptance state symlink')
    fd,name=tempfile.mkstemp(dir=p.parent,prefix='.amui05-acceptance-')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(state,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(name,p)
    finally:
        if os.path.exists(name):os.unlink(name)

def discover(repo,head):
    r=gh(repo,'api',f'repos/{REPO}/actions/runs?event=workflow_dispatch&per_page=100')
    return [x for x in r['workflow_runs'] if x.get('head_sha')==head and
            str(x.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml' and
            x.get('event')=='workflow_dispatch' and x.get('head_branch') in (None,BRANCH)]

def acceptance(repo,head,temp):
    stage('SEPARATE_MANUAL_DISPATCH_ACCEPTANCE_30_35_36')
    runs=discover(repo,head)
    must(len(runs)<=1,'duplicate exact-sha AMUI05 runs: manual reconciliation required')
    intent=state_file()
    if intent.exists():
        x=json.loads(intent.read_text());must(x.get('sha')==head,'stale acceptance state; refuse overwrite')
    if not runs:
        must(not intent.exists(),'old dispatch intent with no visible run; manual reconciliation required')
        stage_write({'schema':1,'sha':head,'status':'dispatch_intent','exact_workflow':'devtool-tasker-ci.yml:instrumentation'})
        run(['gh','workflow','run','devtool-tasker-ci.yml','-R',REPO,'--ref',BRANCH,
             '-f','mode=instrumentation'],repo,show=True)
        for i in range(55):
            runs=discover(repo,head)
            must(len(runs)<=1,'more than one exact workflow dispatch')
            if runs:break
            if i<54:time.sleep(4)
    must(len(runs)==1,'run not discovered; retain intent and rerun without redispatch')
    rid=int(runs[0]['id'])
    stage_write({'schema':1,'sha':head,'status':'pending','run_id':rid,'exact_workflow':'devtool-tasker-ci.yml:instrumentation'})
    for i in range(420):
        r=gh(repo,'api',f'repos/{REPO}/actions/runs/{rid}')
        must(r.get('head_sha')==head and r.get('event')=='workflow_dispatch' and
             str(r.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml',
             'wrong hosted run identity')
        if r.get('status')=='completed':break
        if i<419:time.sleep(5)
    must(r.get('status')=='completed' and r.get('conclusion')=='success',
         'AMUI05 hosted acceptance failed or unfinished '+str(rid))
    jobs=gh(repo,'api',f'repos/{REPO}/actions/runs/{rid}/jobs?per_page=100')['jobs']
    needed={'Devtool source contract and upstream merge safety',
            'AMT-03 Android instrumentation via Devtool emulator',
            'AMUI-01 real package lifecycle on Android 16'}|{f'AMUI05 Android API {n} acceptance' for n in (30,35,36)}
    must(needed.issubset({j['name'] for j in jobs if j.get('conclusion')=='success'}),
         'missing exact successful 30/35/36 jobs')
    attempt=int(r.get('run_attempt',1))
    for api in (30,35,36):
        d=temp/f'api{api}';d.mkdir()
        run(['gh','run','download',str(rid),'-R',REPO,'--name',
             f'amui05-api{api}-{rid}-{attempt}','--dir',str(d)],repo,show=True,retries=3)
    run([sys.executable,'-B','scripts/devtool/amui05_receipt_audit.py',
         '--api30',str(temp/'api30'),'--api35',str(temp/'api35'),
         '--api36',str(temp/'api36'),'--sha',head],repo,show=True)
    stage_write({'schema':1,'sha':head,'status':'HOSTED_EMULATORS_ONLY_QUALIFIED',
                 'run_id':rid,'api_matrix':[30,35,36],
                 'physical':'UNVERIFIED','all_24_screens':'UNVERIFIED'})
    C.print('AMUI05_HOSTED_MATRIX_3_OF_3_PASS',rid,head)
    C.print('AMUI05_FULL_ROADMAP_PENDING_PHYSICAL_AND_ALL_REAL_SCREENS')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path.home()/'Code/AppManager')
    p.add_argument('--verify-only',action='store_true')
    p.add_argument('--no-dispatch',action='store_true')
    a=p.parse_args()
    native,preflight=verify(Path(sys.argv[0]).resolve())
    if a.verify_only:print('AMUI05_ZIPAPP_INTEGRITY_PASS');return
    tmp=Path(os.environ.get('TMPDIR',''))
    must(tmp.is_dir() and os.access(tmp,os.W_OK),'writable $TMPDIR required')
    gate_file,gate_hash=validate_historical_qualification()
    repo=a.repo.expanduser().resolve();head=ensure_repo(repo)
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
    C.print('AMUI05_PR_4_REMAINS_OPEN_UNMERGED_PRIOR_5_OF_5_PRESERVED')

if __name__=='__main__':
    try:main()
    except (Refused,OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,zipfile.BadZipFile) as e:
        C.print('AMUI05_REFUSED '+str(e));raise SystemExit(1)
