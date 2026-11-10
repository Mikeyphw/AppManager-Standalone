#!/usr/bin/env python3
"""AMUI05 remaining-roadmap acceptance: source prerequisites, not device qualification."""
from __future__ import annotations
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
TARGET='.github/workflows/amui-targeted-ci.yml'
FULL='.github/workflows/devtool-tasker-ci.yml'
ACCEPT=FULL  # existing dispatchable default-branch workflow; no new dispatch-only file
RUNNER='scripts/devtool/amui05_hosted_acceptance.sh'
COMPAT='app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui05CompatibilityInstrumentedTest.java'
WALL='app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui05WallpaperInstrumentedTest.java'
PHYSICAL='scripts/devtool/amui05_physical_acceptance.py'
LEDGER='scripts/devtool/amui05_manual_matrix.py'
AUDIT='scripts/devtool/amui05_receipt_audit.py'
ORIGINAL='scripts/devtool/check_amui02_theme.py'
DOC='docs/AMUI05_REMAINING_ACCEPTANCE_MATRIX.md'
SCREENS = ('app_details','app_usage','apps_profile','auth_management','batch_ops_results',
           'code_editor','debloater','finder','fm','help','interceptor','labs','logcat',
           'main','one_click_ops','op_history','profiles','running_apps','settings',
           'settings_dual_pane','shared_prefs','sys_config','term','virus_total')
LAYOUTS=tuple('app/src/main/res/layout/activity_'+name+'.xml' for name in SCREENS)
FILES=(TARGET,FULL,ACCEPT,RUNNER,COMPAT,WALL,PHYSICAL,LEDGER,AUDIT,ORIGINAL,DOC,*LAYOUTS)
NS='{http://schemas.android.com/apk/res/android}'

def validate(src):
    def must(condition,reason):
        if not condition:raise AssertionError('AMUI05_REFUSED: '+reason)
    must(len(SCREENS)==24 and len(set(SCREENS))==24,'screen catalog incomplete')
    for p in LAYOUTS:
        root=ET.fromstring(src[p]); bg=root.attrib.get(NS+'background')
        must(bg=='?android:attr/colorBackground','non-theme root '+p+'='+str(bg))
    must('ACTIVITIES = (' in src[ORIGINAL] and
         all("'"+s+"'" in src[ORIGINAL] for s in SCREENS), 'legacy root audit changed')
    t,f,a=src[TARGET],src[FULL],src[ACCEPT]
    must('python3 -B scripts/devtool/check_amui05_acceptance.py --check' in t,'targeted gate missing')
    must('python3 scripts/devtool/check_amui05_acceptance.py --check' in f,'full source guard missing')
    must("python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v" in t,
         'full mutation suite missing from targeted gate')
    must("python3 -m unittest discover -s scripts/devtool -p 'test_*.py' -v" in f,
         'full mutation suite missing from manual five-job gate')
    fe=f.split('"on":',1)[1].split('permissions:',1)[0]
    must('  workflow_dispatch:' in fe and '  push:' not in fe and '  pull_request:' not in fe,
         'existing 5/5 workflow must remain manual')
    must(a.count('  workflow_dispatch:')==1 and '  push:' not in a and '  pull_request:' not in a and
         '  schedule:' not in a,'AMUI05 acceptance must be explicit only')
    must('  amui05-acceptance:' in a, 'acceptance job absent')
    accept=a.split('\n  amui05-acceptance:\n',1)[1]
    must("if: github.event_name == 'workflow_dispatch' && inputs.mode == 'instrumentation'" in accept,
         'acceptance must require explicit existing instrumentation mode')
    must('matrix:' in accept and 'api: [30, 35, 36]' in accept,'missing Android11/15/16 matrix')
    must('strategy:' in accept and 'fail-fast: false' in accept,'matrix must not cancel untested devices')
    must('name: Devtool source contract and upstream merge safety' in a,'existing source acceptance job removed')
    must('name: AMUI05 Android API ${{ matrix.api }} acceptance' in accept,'matrix job missing')
    must('if-no-files-found: error' in accept,'missing-device receipt silently allowed')
    must('bash scripts/devtool/amui05_hosted_acceptance.sh' in accept,'hosted emulator runner absent')
    must(accept.count('bee6e0b7e49aaaa0c56f755fd5be434a27c52b6c')==2,'pinned devtool removed')
    must('python3 -m pip install "$RUNNER_TEMP/devtool-source"' in accept,'hosted devtool not installed')
    # HF02: source contract enforces exact Android native toolchain provisioning
    # before the pinned Devtool and before an emulator can issue any receipt.
    sdk_packages="sdkmanager --install 'platforms;android-36' 'build-tools;36.1.0' 'platform-tools' 'cmake;3.22.1' 'ndk;27.0.12077973'"
    must(accept.count('uses: android-actions/setup-android@v4')==1 and
         accept.count(sdk_packages)==1,'AMUI05 source matrix missing exact SDK/NDK/CMake provisioning')
    for executable in ('ndk/27.0.12077973/ndk-build',
                       'ndk/27.0.12077973/toolchains/llvm/prebuilt/linux-x86_64/bin/clang',
                       'cmake/3.22.1/bin/cmake', 'cmake/3.22.1/bin/ninja',
                       'build-tools/36.1.0/aapt'):
        must(accept.count('test -x "$sdk/'+executable+'"')==1,
             'AMUI05 missing pinned native executable check '+executable)
    must(accept.index('uses: android-actions/setup-android@v4') <
         accept.index(sdk_packages) < accept.index('Install pinned Devtool (hosted only)') <
         accept.index('Hosted exact-API Android instrumentation'),
         'AMUI05 native provisioning order unsafe')
    must('AMUI05_SDK_NDK_CMAKE_READY' in accept and '|| true' not in accept,
         'AMUI05 native toolchain provisioning must fail closed')
    must('[[ -r /dev/kvm && -w /dev/kvm ]]' in accept,'hardware acceleration guard removed')
    s=src[RUNNER]
    must('AMUI05_EXPECT_API' in s and '30 || "$api" == 35 || "$api" == 36' in s,
         'real emulator API guard missing')
    must("'cleanup_status')=='passed'" in s and "r.get('failed',1))==0" in s and
         "r.get('skipped',1))==0" in s,'device receipt fail-closed floor weakened')
    must('AMUI05_NOT_A_DISPOSABLE_EMULATOR' in s and 'ranchu' in s and 'goldfish' in s,
         'wallpaper must never touch a personal physical device')
    must('AMUI05_HOSTED_PINNED_NATIVE_TOOLCHAIN_NOT_READY' in s and
         'ndk/27.0.12077973/ndk-build' in s and 'cmake/3.22.1/bin/ninja' in s and
         'cmake/3.22.1/bin/cmake' in s and
         'toolchains/llvm/prebuilt/linux-x86_64/bin/clang' in s,
         'AMUI05 hosted runner missing strict native toolchain preflight')
    must('Amui05CompatibilityInstrumentedTest' in s and
         'Amui05WallpaperInstrumentedTest' in s,'both real test classes must run')
    must('accept io.github.muntashirakon.AppManager.utils.appearance.Amui05CompatibilityInstrumentedTest compatibility 7' in s,
         'seven baseline tests required on all APIs')
    must('accept io.github.muntashirakon.AppManager.utils.appearance.Amui05WallpaperInstrumentedTest wallpaper 2' in s,
         'two real wallpaper tests required on 35/36')
    c,w=src[COMPAT],src[WALL]
    must(c.count('@Test')==7 and 'DynamicColors.isDynamicColorAvailable()' in c,
         'seven real compatibility methods missing')
    must('runOnMainSync' in c and 'assertFalse(user.isChecked())' in c,
         'real on/off chip verification removed')
    must(w.count('@Test')==2 and 'manager.setBitmap(' in w and
         'getWallpaperColors(WallpaperManager.FLAG_SYSTEM)' in w and
         'assertNotEquals("AMUI05_WALLPAPER_PALETTE_DID_NOT_CHANGE"' in w and
         'assertNotEquals("AMUI05_DYNAMIC_ACCENT_DID_NOT_CHANGE"' in w,
         'actual wallpaper-change verification removed')
    must('AMUI05_HARD_REFUSAL_PHYSICAL_WALLPAPER_MUTATION' in w,
         'physical phone mutation guard absent')
    must('I_AUTHORIZE_READ_ONLY_DEVICE_PROBE' in src[PHYSICAL] and
         'screencap' not in src[PHYSICAL] and 'su -c' not in src[PHYSICAL],
         'physical acceptance must be explicitly authorized and privacy-preserving')
    must("return {'schema':1,'exact_sha':sha,'status':'PENDING'," in src[LEDGER] and 'screenshot_sha256' in src[LEDGER] and
         'PHYSICAL_ARM64' in src[LEDGER], 'manual screen/physical matrix must fail closed')
    must('amui05_exact_sha' in src[AUDIT] and 'failed' in src[AUDIT] and
         'api30' in src[AUDIT],'independent API receipt audit removed')
    must('NOT_FULL_ROADMAP_ACCEPTANCE' in src[DOC] and
         '24 activity' in src[DOC],'source-only success misrepresented as release')
    return True

def check(root=ROOT):
    src={p:(root/p).read_text(encoding='utf-8') for p in FILES}
    return validate(src)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true',required=True)
    ap.add_argument('--root',type=Path,default=ROOT);a=ap.parse_args()
    check(a.root);print('AMUI05_SOURCE_ACCEPTANCE_READY_3_APIS_24_SCREENS_PHYSICAL_PENDING')
