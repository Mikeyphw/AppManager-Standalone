#!/usr/bin/env python3
"""AMUI-04D final 5/5 source-pinned Devtool, CI and independent device artifact qualification."""
from __future__ import annotations
import argparse,ast,hashlib,io,json,os,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
try:
    from rich.console import Console
except ImportError:
    class Console:
        def print(self,*args,**kwargs):print(*args)
C=Console()
REPO='Mikeyphw/AppManager-Standalone'
BRANCH='feature/amui03b-responsive-list-20261109'
PIN='c407e2091dea029d1bdb7eb68458e35bc45d79fa'
OLD_GATE='c2a27476c637f702263614707d3b25108781480d'
MILESTONES=(
    '03fc6b256898b17e82872c8c2a8a529ba430c293',
    '0d89ebe7bc432769694d906133054e1c6470fbbb',
    '369fe24d9b374b84f3f5bab40e7c0cdbc6e0c7a5',
    PIN,
)
SUBJECT='test(amui04d): full 5-of-5 Android acceptance with independently verified device receipts'
NATIVE='AMUI04D_SOURCE_PINNED_NATIVE_DEVTOOL.overlay.zip'
MODIFIED={'.github/workflows/amui-targeted-ci.yml','.github/workflows/devtool-tasker-ci.yml','scripts/devtool/amui02_hosted_theme.sh'}
ADDED={'app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui04DFinalAcceptanceInstrumentedTest.java',
       'scripts/devtool/check_amui04d_final_gate.py',
       'scripts/devtool/test_amui04d_final_gate.py',
       'scripts/devtool/amui04d_receipt_audit.py',
       'scripts/devtool/test_amui04d_receipt_audit.py',
       'docs/AMUI04D_FULL_ANDROID_5_OF_5_RELEASE_GATE.md',
       'docs/AMUI_FULL_ROADMAP_FULFILLMENT_AUDIT_20261110.md',
       'scripts/devtool/test_amui04d_dispatch_recovery.py',
       'scripts/devtool/amui04d_launcher.py'}
FILES=MODIFIED|ADDED
class Refused(RuntimeError):pass

def must(ok,why):
    if not ok:raise Refused(why)
def stage(what):C.print('[cyan]AMUI04D_STAGE[/cyan] '+what)
def cmd(args,repo=None,show=False):
    p=subprocess.run(args,cwd=repo,text=True,stdout=None if show else subprocess.PIPE,
                     stderr=None if show else subprocess.PIPE,check=False)
    if p.returncode:
        raise Refused('command rc='+str(p.returncode)+' '+repr(args)+' '+(p.stderr or p.stdout or '')[-1300:])
    return p.stdout or ''
def get(args,repo=None):return cmd(args,repo).strip()
def gh(args,repo):return json.loads(get(['gh',*args],repo))
def verify_zip():
    with zipfile.ZipFile(Path(sys.argv[0]).resolve()) as z:
        must(z.testzip() is None,'outer CRC corrupted')
        outer={p:z.read(p) for p in z.namelist()}
    must(set(outer)=={'__main__.py',NATIVE,'README.txt','SHA256SUMS.txt'},'outer inventory drift')
    lines=outer['SHA256SUMS.txt'].decode('utf-8').splitlines()
    must(len(lines)==3,'SHA table incomplete')
    for row in lines:
        digest,path=row.split('  ',1)
        must(path in outer and hashlib.sha256(outer[path]).hexdigest()==digest,'outer SHA mismatch '+path)
    with zipfile.ZipFile(io.BytesIO(outer[NATIVE])) as z:
        must(z.testzip() is None,'native CRC corrupted')
        inner={p:z.read(p) for p in z.namelist()}
    man=json.loads(inner['.devtool-artifact.json'])
    must(man['schema_version']==2 and man['type']=='overlay','wrong native Devtool schema')
    must(man['target']=='app' and man['apply']['atomic'] is True,'non-atomic target')
    must(man['repository']['branch']==BRANCH and man['repository']['remote']==f'https://github.com/{REPO}.git','repository drift')
    must(man['apply']['commit']['message']==SUBJECT,'commit message drift')
    must(set(man['preflight']['write_paths'])==MODIFIED,'modified file inventory drift')
    must({e['path'] for e in man['inventory']['entries']}==ADDED,'new file inventory drift')
    for e in man['inventory']['entries']:
        p=e['path']
        must(e['action']=='add' and p in inner and len(inner[p])==e['size'] and
             hashlib.sha256(inner[p]).hexdigest()==e['sha256'],'new file hash drift '+p)
    for field in ('preflight','validation'):
        script=man[field]['script'];p=script['path']
        must(hashlib.sha256(inner[p]).hexdigest()==script['sha256'],'script SHA mismatch '+p)
    pre=inner['.devtool-artifact/preflight.py'].decode()
    ast.parse(pre)
    must('PIN='+repr(PIN) in pre,'source commit pin absent')
    original=ast.literal_eval(pre.split('BASE=',1)[1].split('\nADDED=',1)[0])
    patches=ast.literal_eval(pre.split('PATCHES=',1)[1].split('\ndef refuse(',1)[0])
    must(set(original)==MODIFIED and len(patches)==5 and {b['path'] for b in patches}==MODIFIED,
         'patch inventory mismatch')
    for b in patches:
        must(tuple(original[b['path']])==(b['blob'],b['sha256']),'patch with mixed source SHA')
    for p in ('scripts/devtool/check_amui04d_final_gate.py',
              'scripts/devtool/test_amui04d_final_gate.py',
              'scripts/devtool/amui04d_receipt_audit.py',
              'scripts/devtool/test_amui04d_receipt_audit.py',
              'scripts/devtool/test_amui04d_dispatch_recovery.py'):
        ast.parse(inner[p],filename=p)
    java=inner['app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui04DFinalAcceptanceInstrumentedTest.java'].decode()
    must(java.count('@Test')==10 and 'PackageChangeReceiver.packagesFromPackageIntent(intent)' in java,
         'real package-intent tests lost')
    must(inner['scripts/devtool/amui04d_launcher.py']==outer['__main__.py'],
         'embedded launch logic differs from repo-tested launcher source')
    must('AMUI04D_HOSTED_FINAL_PASS' in patches[0]['new'],'device runner not wired')
    must(any('amui01-fixture.sha256' in p['new'] for p in patches),
         'real disposable APK digest evidence not archived')
    validate=inner['.devtool-artifact/validate.sh'].decode()
    must("python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v" in validate,
         'Devtool missing full regression suite')
    stage('SELF_CHECK_ARCHIVE_AND_NATIVE_PINS_PASS')
    return outer[NATIVE],pre

def state_read():
    p=Path.home()/'.local/state/appmanager-ci/overlay-gates.json'
    must(p.is_file() and not p.is_symlink(),'cadence state missing/symlink')
    data=json.loads(p.read_text())
    must(data.get('schema')==1 and data.get('gate_every')==5,'gate schema/cadence drift')
    must(isinstance(data.get('overlays'),list) and isinstance(data.get('pending_gates'),list),
         'gate state corrupted')
    return data

def state_path():
    return Path.home()/'.local/state/appmanager-ci/overlay-gates.json'

def state_write(data):
    # Do not truncate the canonical state file. The directory and saved file
    # may be user-owned; preserve its existing mode, refuse symlink drift.
    p=state_path()
    must(p.is_file() and not p.is_symlink(),'gate state lost/unsafe during reconciliation')
    fd,name=tempfile.mkstemp(prefix='.overlay-gates-',dir=p.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            f.write(json.dumps(data,indent=2,sort_keys=True)+'\n')
            f.flush();os.fsync(f.fileno())
        os.chmod(name,p.stat().st_mode & 0o777)
        os.replace(name,p)
    finally:
        if os.path.exists(name):os.unlink(name)

def check_state(head):
    d=state_read()
    if (d.get('qualified_gate') or {}).get('sha')==head:
        must(d.get('overlays')==[] and d.get('pending_gates')==[],
             'qualified gate has unexpected pending work')
        return 'qualified'
    must((d.get('qualified_gate') or {}).get('sha')==OLD_GATE,'previous 5/5 seal drift')
    overlays=d['overlays']
    must(len(overlays) in (4,5),'expected qualified 4/5 or pending 5/5')
    must([x.get('sha') for x in overlays[:4]]==list(MILESTONES),
         'prior four successful milestones changed')
    if len(overlays)==5:
        must(overlays[4].get('sha')==head,'fifth milestone belongs to another SHA')
        if not d['pending_gates']:
            # Expected crash-safe intermediate state: --record --no-dispatch
            # succeeded, but GitHub workflow run is not yet registered.
            return 'recorded'
        must(len(d['pending_gates'])==1 and d['pending_gates'][0].get('sha')==head
             and d['pending_gates'][0].get('count')==5 and
             d['pending_gates'][0].get('branch')==BRANCH,
             '5/5 state pending gate mismatch')
        return 'pending' 
    must(not d['pending_gates'],'unexpected outstanding full Android gate')
    return 'four'

def pr(repo):
    x=gh(['pr','view','4','-R',REPO,'--json','state,headRefName,baseRefName,headRefOid'],repo)
    must(x['state']=='OPEN' and x['headRefName']==BRANCH and
         x['baseRefName']=='feature/tasker-automation','PR #4 closed/merged/moved')
    return x['headRefOid']

def pr_sync(repo,head):
    for idx in range(24):
        if pr(repo)==head:return
        if idx<23:time.sleep(3)
    raise Refused('PR head still stale after bounded synchronization; rerun ZIP to resume, do not reapply')

def local_repo(repo):
    must(repo.is_dir() and Path(get(['git','rev-parse','--show-toplevel'],repo)).resolve()==repo,'wrong repo')
    must(not get(['git','status','--porcelain','--untracked-files=all'],repo),'dirty repository; refusing reset')
    origin=get(['git','remote','get-url','origin'],repo).removesuffix('.git')
    must(origin in (f'https://github.com/{REPO}',f'git@github.com:{REPO}',
                    f'ssh://git@github.com/{REPO}'),'wrong origin')
    cmd(['git','fetch','--no-tags','origin','refs/heads/'+BRANCH],repo,True)
    cmd(['git','switch',BRANCH],repo,True)
    cmd(['git','merge','--ff-only','FETCH_HEAD'],repo,True)
    head=get(['git','rev-parse','HEAD'],repo)
    must(get(['git','ls-remote','origin','refs/heads/'+BRANCH],repo).split()[0]==head,
         'local/remote branch mismatch')
    return head

def committed(repo,head):
    must(get(['git','rev-parse','HEAD^'],repo)==PIN,'overlay not a direct child of pinned parent')
    must(get(['git','log','-1','--format=%s'],repo)==SUBJECT,'unexpected overlay commit subject')
    paths=set(get(['git','diff','--name-only',PIN,head],repo).splitlines())
    must(paths==FILES,'unexpected commit diff '+str(paths^FILES))
    must(not get(['git','status','--porcelain','--untracked-files=all'],repo),'dirty after Devtool')
    cmd([sys.executable,'-B','scripts/devtool/check_amui04d_final_gate.py','--check'],repo,True)
    cmd([sys.executable,'-B','scripts/devtool/test_amui04d_final_gate.py'],repo,True)
    cmd([sys.executable,'-B','scripts/devtool/test_amui04d_receipt_audit.py'],repo,True)
    cmd([sys.executable,'-B','scripts/devtool/test_amui04d_dispatch_recovery.py'],repo,True)

def targeted(repo,head):
    stage('TARGETED_SOURCE_AND_HOSTED_ANDROID_COMPILE')
    run_id=None
    for i in range(45):
        rows=gh(['run','list','-R',REPO,'--workflow','amui-targeted-ci.yml','--commit',head,
                 '--event','push','--limit','25','--json','databaseId,headSha'],repo)
        hits=[x for x in rows if x.get('headSha')==head]
        if hits:run_id=int(hits[0]['databaseId']);break
        if i<44:time.sleep(3)
    must(run_id is not None,'targeted run for exact SHA not discovered')
    r=gh(['api',f'repos/{REPO}/actions/runs/{run_id}'],repo)
    must(r.get('head_sha')==head and r.get('event')=='push' and
         str(r.get('path','')).split('@')[0]=='.github/workflows/amui-targeted-ci.yml',
         'wrong targeted workflow identity')
    if r.get('status')!='completed':
        cmd(['gh','run','watch',str(run_id),'-R',REPO,'--exit-status'],repo,True)
    r=gh(['api',f'repos/{REPO}/actions/runs/{run_id}'],repo)
    must(r.get('status')=='completed' and r.get('conclusion')=='success','targeted failed '+str(run_id))
    jobs=gh(['api',f'repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100'],repo)['jobs']
    good={j['name'] for j in jobs if j['conclusion']=='success'}
    must({'Targeted source and regression contracts','Scoped Android resource and Java compile (no emulator)'}.issubset(good),
         'both targeted jobs not successful')
    C.print('[green]AMUI04D_TARGETED_2_OF_2_PASS[/green] '+str(run_id)+' '+head)

def find_exact_full_runs(repo,head):
    x=gh(['api',f'repos/{REPO}/actions/workflows/devtool-tasker-ci.yml/runs?event=workflow_dispatch&branch={BRANCH}&per_page=100'],repo)
    candidates=[]
    for record in x.get('workflow_runs',[]):
        if record.get('head_sha')!=head or record.get('event')!='workflow_dispatch':
            continue
        if record.get('head_branch') not in (BRANCH,None):continue
        if str(record.get('path','')).split('@')[0]!='.github/workflows/devtool-tasker-ci.yml':
            continue
        inputs=record.get('inputs')
        if isinstance(inputs,dict) and inputs.get('mode') not in (None,'full'):
            continue
        candidates.append(record)
    return candidates

def ensure_full_pending(repo,head):
    """Crash-safe 5/5 recovery: discover exact-SHA dispatch BEFORE a new dispatch.

    Never rely on a successful gh command returning before run registration. A
    failure after remote dispatch leaves 'recorded'; retries discover the run
    instead of dispatching again. Do not overwrite a different pending gate.
    """
    status=check_state(head)
    if status=='pending':
        gate=state_read()['pending_gates'][0]
        return gate.get('run_id')
    must(status=='recorded','no 5/5 staging record')
    stage('RECOVER_OR_DISPATCH_SINGLE_FULL_RUN')
    existing=find_exact_full_runs(repo,head)
    must(len(existing)<=1,'multiple exact-SHA full runs: manual reconciliation required')
    if not existing:
        # Only this launcher dispatches the fifth full workflow. The generic
        # gate script recorded the milestone with --no-dispatch.
        cmd(['gh','workflow','run','devtool-tasker-ci.yml','-R',REPO,
             '--ref',BRANCH,'-f','mode=full'],repo,True)
        for i in range(50):
            existing=find_exact_full_runs(repo,head)
            must(len(existing)<=1,'duplicate exact-SHA dispatch detected')
            if existing:break
            if i<49:time.sleep(3)
    must(len(existing)==1,'exact-SHA full workflow not discoverable; rerun to recover')
    run_id=int(existing[0]['id'])
    # Recheck gate state immediately before a single atomic save; no resets.
    state=state_read()
    must(check_state(head)=='recorded' and len(state['overlays'])==5 and
         not state['pending_gates'],'local 5/5 state changed while dispatching')
    state['pending_gates'].append({'sha':head,'branch':BRANCH,'count':5,'run_id':run_id})
    state_write(state)
    must(check_state(head)=='pending','pending gate receipt could not be restored')
    C.print('[green]AMUI04D_5_OF_5_PENDING_RUN_RECORDED[/green] '+str(run_id)+' '+head)
    return run_id

def full_run(repo,head):
    stage('FIFTH_FULL_GATE_EXACT_SHA')
    must(check_state(head)=='pending','expected exactly one pending 5/5 workflow')
    gate=state_read()['pending_gates'][0]
    run_id=gate.get('run_id')
    if run_id is None:
        # Compatibility with an earlier gate record that stored no run id.
        matches=find_exact_full_runs(repo,head)
        must(len(matches)==1,'legacy pending gate requires one exact-SHA run')
        run_id=int(matches[0]['id'])
    r=gh(['api',f'repos/{REPO}/actions/runs/{run_id}'],repo)
    must(r.get('head_sha')==head and r.get('event')=='workflow_dispatch' and
         str(r.get('path','')).split('@')[0]=='.github/workflows/devtool-tasker-ci.yml' and
         r.get('head_branch') in (BRANCH,None),
         'wrong full-run workflow/branch/SHA identity')
    inputs=r.get('inputs')
    must(not isinstance(inputs,dict) or inputs.get('mode') in (None,'full'),
         'run is not full Android mode')
    if r.get('status')!='completed':
        cmd(['gh','run','watch',str(run_id),'-R',REPO,'--exit-status'],repo,True)
    r=gh(['api',f'repos/{REPO}/actions/runs/{run_id}'],repo)
    must(r.get('status')=='completed' and r.get('conclusion')=='success','full 5/5 gate failed '+str(run_id))
    jobs=gh(['api',f'repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100'],repo)['jobs']
    required={'Devtool source contract and upstream merge safety',
              'Android Gradle through Devtool (GitHub-hosted only)',
              'AMT-03 Android instrumentation via Devtool emulator',
              'AMUI-01 real package lifecycle on Android 16',
              'AMT-06C disposable debug fixture (hosted only)'}
    good={j['name'] for j in jobs if j.get('conclusion')=='success'}
    must(required.issubset(good),'full Android 15/16, Tasker or lint job missing')
    C.print('[green]AMUI04D_FULL_5_OF_5_JOBS_PASS[/green] '+str(run_id)+' '+head)
    return run_id,int(r.get('run_attempt',1))

def attest(repo,head,run_id,attempt,tmp):
    stage('INDEPENDENT_API35_API36_ARTIFACT_SHA_AUDIT')
    api35=Path(tmp)/'api35';api36=Path(tmp)/'api36'
    api35.mkdir();api36.mkdir()
    for api,directory,artifact in ((35,api35,f'appmanager-amt03-instrumentation-{run_id}-{attempt}'),
                                   (36,api36,f'appmanager-amui01-api36-{run_id}-{attempt}')):
        cmd(['gh','run','download',str(run_id),'-R',REPO,'--name',artifact,'--dir',str(directory)],repo,True)
    cmd([sys.executable,'-B','scripts/devtool/amui04d_receipt_audit.py',
         '--api35',str(api35),'--api36',str(api36),'--sha',head,'--run-id',str(run_id)],repo,True)

def complete(repo,head,tmp):
    status=check_state(head)
    if status=='qualified':
        C.print('[green]AMUI04D_ALREADY_QUALIFIED_5_OF_5[/green] '+head)
        return
    if status=='four':
        stage('RECORD_FIFTH_OVERLAY_WITHOUT_DISPATCH')
        cmd([sys.executable,'-B','scripts/devtool/amui_ci_gate.py','--record',head,
             '--no-dispatch','--repo',str(repo)],repo,True)
        must(check_state(head)=='recorded','5/5 milestone was not staged')
    if check_state(head)=='recorded':ensure_full_pending(repo,head)
    run_id,attempt=full_run(repo,head)
    attest(repo,head,run_id,attempt,tmp)
    stage('ACKNOWLEDGE_VERIFIED_5_OF_5')
    cmd([sys.executable,'-B','scripts/devtool/amui_ci_gate.py','--ack-run',str(run_id),'--repo',str(repo)],repo,True)
    must(check_state(head)=='qualified','successful evidence audit did not seal full gate')
    C.print('[green]AMUI04D_QUALIFIED_FINAL_5_OF_5_PASS[/green] '+str(run_id)+' '+head)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path.home()/'Code/AppManager')
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--skip-watch',action='store_true',help='push, but no CI/gate counter updates')
    options=parser.parse_args()
    payload,pre=verify_zip()
    if options.verify_only:
        C.print('[green]AMUI04D_ZIPAPP_INTEGRITY_PASS[/green]')
        return
    tmpdir=Path(os.environ.get('TMPDIR',''))
    must(tmpdir.is_dir() and os.access(tmpdir,os.W_OK),'$TMPDIR must exist and be writable')
    repo=options.repo.expanduser().resolve()
    head=local_repo(repo)
    if head==PIN:
        must(check_state(PIN)=='four','4/5 prerequisite not qualified')
        with tempfile.TemporaryDirectory(prefix='amui04d-',dir=tmpdir) as d:
            artifact=Path(d)/NATIVE;artifact.write_bytes(payload)
            local_pre=Path(d)/'preflight.py';local_pre.write_text(pre)
            stage('PINNED_SOURCE_DRY_RUN')
            cmd([sys.executable,'-B',str(local_pre),'--dry-run'],repo,True)
            stage('NATIVE_DEVTOOL_ATOMIC_APPLY')
            cmd(['devtool','--repo',str(repo),'--target','app','--yes','apply-overlay',str(artifact)],repo,True)
        head=get(['git','rev-parse','HEAD'],repo)
    else:stage('RESUME_EXISTING_FINAL_COMMIT_NO_REAPPLY')
    committed(repo,head)
    stage('PUSH_NON_FORCE')
    cmd(['git','push','origin',BRANCH],repo,True)
    pr_sync(repo,head) # bounded PR metadata delay recovery, not an instant stale refusal
    if options.skip_watch:
        C.print('[yellow]AMUI04D_PUSHED_UNQUALIFIED_NO_GATE_DISPATCH[/yellow] '+head)
        return
    targeted(repo,head)
    with tempfile.TemporaryDirectory(prefix='amui04d-evidence-',dir=tmpdir) as d:
        complete(repo,head,d)
    pr_sync(repo,head)
    C.print('AMUI04D_PR_4_OPEN_UNMERGED_NO_FORCE_PUSH')

if __name__=='__main__':
    try:main()
    except (Refused,OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,zipfile.BadZipFile) as error:
        C.print('[red]AMUI04D_REFUSED[/red] '+str(error),style='bold red')
        raise SystemExit(1)
