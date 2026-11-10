#!/usr/bin/env python3
"""AMUI04D final Android/Tasker full-gate invariant; phase-specific and fail-closed."""
from __future__ import annotations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
JAVA='app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui04DFinalAcceptanceInstrumentedTest.java'
RUNNER='scripts/devtool/amui02_hosted_theme.sh'
TARGET='.github/workflows/amui-targeted-ci.yml'
FULL='.github/workflows/devtool-tasker-ci.yml'
AUDIT='scripts/devtool/amui04d_receipt_audit.py'
VM='app/src/main/java/io/github/muntashirakon/AppManager/main/MainViewModel.java'
ACT='app/src/main/java/io/github/muntashirakon/AppManager/main/MainActivity.java'
RECEIVER='app/src/main/java/io/github/muntashirakon/AppManager/types/PackageChangeReceiver.java'
FILES=(JAVA,RUNNER,TARGET,FULL,AUDIT,VM,ACT,RECEIVER)

def validate(src):
    def must(ok,why):
        if not ok:raise AssertionError('AMUI04D_REFUSED: '+why)
    java,runner,target,full,audit,vm,act,receiver=(src[p] for p in FILES)
    must('class Amui04DFinalAcceptanceInstrumentedTest' in java and java.count('@Test')==10,
         'ten device tests required')
    for marker in ('PackageChangeReceiver.packagesFromPackageIntent(intent)',
        'getPackageInfo(context.getPackageName(), 0)',
        'assertEquals(Process.myUid(), info.applicationInfo.uid)',
        'Intent.EXTRA_CHANGED_PACKAGE_LIST', 'Intent.EXTRA_REPLACING',
        'AppListSyncStatus.success("resume", 60, 2, 1, 9)',
        'AppListSyncStatus.failure("package-event-failure", "SecurityException")',
        'Collections.<ApplicationItem>emptyList()',
        'MainViewModel.class.getDeclaredMethod("publishVisibleItems", List.class, long.class)',
        'catch (UnsupportedOperationException expected)',
        'model.onCleared();', 'vm.onResume();',
        'AppearanceUtils.getThemedContext(target(), false)',
        'R.layout.amui03c_quick_filters'):
        must(marker in java,'device check missing '+marker)
    for forbidden in ('Runtime.getRuntime().exec', 'Intent.ACTION_PACKAGE_DELETE',
                      'deletePackage(', 'deleteApplication(', 'pm uninstall', 'setWallpaper('):
        must(forbidden not in java,'unsafe Android test mutation '+forbidden)
    must(runner.count('Amui04DFinalAcceptanceInstrumentedTest')==1 and
         runner.count('AMUI04D_HOSTED_FINAL_PASS')==1 and
         runner.count('amui04d-api${api}.json')==1,
         'final device class/receipt missing or duplicated')
    # AMUI04A/B/C also check failed==0. Verify the AMUI04D PYFINAL block,
    # not the combined runner, or an earlier phase could mask a regression.
    phase_marker='# AMUI-04D: final read-only identity, package-event, list and semantic-theme acceptance.'
    must(runner.count(phase_marker)==1,'AMUI04D runtime phase missing or duplicated')
    final_phase=runner.split(phase_marker,1)[1]
    must(final_phase.count("<<'PYFINAL'")==1
         and final_phase.count("\nPYFINAL\n")==1,
         'AMUI04D strict receipt parser absent or duplicated')
    final_receipt=final_phase.split("<<'PYFINAL'",1)[1].split('\nPYFINAL\n',1)[0]
    for marker in ("assert int(receipt.get('executed',0))>=10,receipt",
                   "assert int(receipt.get('passed',0))>=10,receipt",
                   "assert int(receipt.get('failed',1))==0,receipt",
                   "receipt['amui04d_commit']=sha", "receipt['amui04d_api']=api"):
        must(final_receipt.count(marker)==1,
             'AMUI04D phase receipt guard missing, duplicated or weakened '+marker)
    for prior in ('AMUI02_HOSTED_THEME_PASS','AMUI03C_HOSTED_UI_PASS',
                  'AMUI04A_HOSTED_VISUAL_PASS','AMUI04B_HOSTED_VIEWPORT_PASS',
                  'AMUI04C_HOSTED_RACE_PASS'):
        must(prior in runner,'previous emulator gate lost '+prior)
    for musts in ('python3 -B scripts/devtool/check_amui04d_final_gate.py --check',
                  "python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v",
                  'Scoped Android resource and Java compile (no emulator)'):
        must(musts in target,'targeted source/compile gate missing '+musts)
    must('python3 scripts/devtool/check_amui04d_final_gate.py --check' in full,
         'full gate lost final source check')
    event=full.split('"on":',1)[1].split('permissions:',1)[0]
    must('  workflow_dispatch:' in event and '  push:' not in event and '  pull_request:' not in event,
         'heavy full Android gate must remain manual-dispatch-only')
    for mandatory in ('  device-instrumentation:', '  amui01-android16:',
        '  hosted-android:', '  amt06c-fixture:',
        'AMT-03 Android instrumentation via Devtool emulator',
        'AMUI-01 real package lifecycle on Android 16',
        'AMT-06C disposable debug fixture (hosted only)',
        'bash scripts/devtool/amt03_hosted_instrumentation.sh',
        'AMUI01_EXPECT_API=36 bash scripts/devtool/amui01_hosted_instrumentation.sh',
        'scripts/devtool/check_amui04a_visual_gate.py --check',
        'scripts/devtool/check_amui04b_viewport_stress.py --check',
        'scripts/devtool/check_amui04c_refresh_races.py --check'):
        must(mandatory in full,'legacy full gate weakened '+mandatory)
    for item in ('${{ runner.temp }}/amui04d-api*.json',
                 '${{ runner.temp }}/amui04d-api*.log',
                 '${{ runner.temp }}/amui04c-api*.json',
                 '${{ runner.temp }}/amui04b-screenshots-api*/**',
                 '${{ runner.temp }}/amui04a-screenshots-api*/**'):
        must(full.count(item)==2,'both API35/API36 must upload '+item)
    must('mListExecutor = Executors.newSingleThreadExecutor()' in vm and
         'final long filterEpoch = mListEpoch.get();' in vm and
         'if (epoch != mListEpoch.get())' in vm and
         'completeRequestId == mRefreshRequestId.get()' in vm,
         'authoritative synchronized list pipeline lost')
    for marker in ('viewModel.onResume();','viewModel.refreshApplications("menu")',
                   'viewModel.refreshApplications("pull")', 'viewModel.getRefreshState().observe('):
        must(marker in act,'main Activity refresh/lifecycle bridge missing '+marker)
    must('packagesFromPackageIntent(@NonNull Intent intent)' in receiver and
         'if (uri != null && "package".equals(uri.getScheme()))' in receiver and
         'if (intent.getBooleanExtra(Intent.EXTRA_REPLACING, false))' in receiver,
         'package lifecycle receiver guards missing')
    for marker in ('verify_api(args.api35,35,args.sha)',
                   'verify_api(args.api36,36,args.sha)',
                   "LIFECYCLE=(('amui01-installed.json',5),('amui01-removed.json',1))",
                   'actual=png_geometry(path)', 'zlib.crc32(kind+payload)',
                   "require(type(x.get(key)) is int,'missing/non-integer '+key+' '+path.name)",
                   "require(len(digests)==len(cases),'duplicate rendered captures '+folder_name)",
                   "require(rows[filename]==h,'PNG SHA-256 mismatch '+folder_name+'/'+filename)",
                   "require(x.get(sha_key)==sha and type(x.get(api_key)) is int and x[api_key]==api,",
                   "require(x['executed']>=floor and x['passed']>=floor and x['failed']==0 and",
                   "require(sha_rows[0].split('  ',1)[0]==digest,",
                   "require(meta.get('disposable_fixture')==FIXTURE"  # handled separately
                   ):
        if marker.startswith('require(meta.get('):
            # Actual checker uses a compound expression, not a fake isolated predicate.
            must("meta.get('disposable_fixture')==FIXTURE" in audit,
                 'disposable fixture identity audit missing')
        else:
            must(marker in audit,'independent evidence check missing '+marker)
    must(full.count('${{ runner.temp }}/amui01-fixture.sha256')==2,
         'both API35/API36 must archive disposable APK SHA256')
    return True

def check(root=ROOT):
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.parse_args()
    check();print('AMUI04D_FINAL_FULL_GATE_SOURCE_PASS')
