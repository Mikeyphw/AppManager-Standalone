#!/usr/bin/env python3
"""CI01 HF01: explicit targeted development vs full qualification separation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILES={
  'full':'.github/workflows/devtool-tasker-ci.yml',
  'targeted':'.github/workflows/amui-targeted-ci.yml',
  'amt00':'scripts/devtool/check_contract.py',
  'amt04':'scripts/devtool/check_amt04_contract.py',
  'amt04b2':'scripts/devtool/check_amt04b2_contract.py',
  'amt04b2b':'scripts/devtool/check_amt04b2b_contract.py',
  'android_test':'app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui02ThemeInstrumentedTest.java',
  'hook':'scripts/devtool/amui_ci_post_push.zsh',
  'gate':'scripts/devtool/amui_ci_gate.py',
}
def validate(data:dict[str,str])->bool:
    def require(ok, label):
        if not ok: raise AssertionError('AMUI_CI01_HF01_REFUSED: '+label)
    full=data['full'];targeted=data['targeted']
    event_section=full.split('"on":\n',1)
    require(len(event_section)==2,'full workflow event section missing')
    full_event=event_section[1].split('\npermissions:',1)[0]
    require('  workflow_dispatch:' in full_event,'full manual dispatch lost')
    require('\n  push:' not in full_event and '\n  pull_request:' not in full_event,
            'full workflow automatically triggers')
    require('  pull_request:' in targeted and '  push:' in targeted and
            "branches: ['feature/amui*', feature/tasker-automation]" in targeted,
            'targeted PR/branch triggers missing')
    require('python3 -B scripts/devtool/check_contract.py --check' in targeted,
            'AMT00 targeted check missing')
    for name in ('check_amt04_contract','check_amt04b2_contract','check_amt04b2b_contract',
                 'check_amui_ci01_hf01'):
        require(f'python3 -B scripts/devtool/{name}.py' in targeted,
                f'targeted source validation missing: {name}')
    require('  android-compile:' in targeted and ':app:compileDebugAndroidTestJavaWithJavac' in targeted,
            'hosted AndroidTest compilation gate missing')
    require('app/src/(main|androidTest)/' in targeted,
            'AndroidTest change must trigger scoped compilation')
    require('amui-targeted-ci.yml' in data['amt00'] and
            'manual-only heavy CI' in data['amt00'],
            'AMT00 still requires automatic heavy CI')
    require('amui-targeted-ci.yml' in data['amt04'] and
            'instrumentation-only pushes' in data['amt04'],
            'AMT04 no longer checks AndroidTest source trigger')
    for key in ('amt04b2','amt04b2b'):
        require('amui-targeted-ci.yml' in data[key] and 'workflow_dispatch:' in data[key],
                key+' does not distinguish targeted vs full')
    java=data['android_test']
    require('androidx.appcompat.R.attr.colorPrimary' in java,
            'Android instrumentation colorPrimary namespace incorrect')
    require('com.google.android.material.R.attr.colorPrimary' not in java,
            'unowned Material colorPrimary attr still referenced')
    require('com.google.android.material.R.attr.colorSurface' in java,
            'working Material colorSurface role unintentionally removed')
    hook=data['hook']
    require('python3 -B scripts/devtool/amui_ci_gate.py --record "$sha"' in hook,
            'overlay counter not invoked after push')
    require('git rev-parse HEAD' in hook and 'AMUI_GATE_EVERY:-5' in hook,
            'hook missing exact HEAD or five-overlay cadence')
    require("['git','ls-remote'" in data['gate'] and 'CI_GATE_FULL_DISPATCHED:' in data['gate'],
            'counter must recheck pushed SHA and dispatch full due gate')
    return True

def check(root:Path=ROOT)->bool:
    return validate({key:(root/path).read_text(encoding='utf-8') for key,path in FILES.items()})
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.parse_args()
    check();print('AMUI_CI01_HF01_TARGETED_CONTRACT_PASS')
