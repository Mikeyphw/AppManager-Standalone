#!/usr/bin/env python3
"""HF03: Tasker 05C/06B safety contracts must validate actual manual and targeted CI.

No Android, privileged write, Gradle, network, or backup I/O.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
F05='scripts/devtool/check_amt05c_contract.py'
F06='scripts/devtool/check_amt06b_contract.py'
FULL='.github/workflows/devtool-tasker-ci.yml'
TARGET='.github/workflows/amui-targeted-ci.yml'
FILES=(F05,F06,FULL,TARGET)
PATH_TOKEN="app/src/main/java/io/github/muntashirakon/AppManager/batchops/BatchOpsService.java'"

def validate(source):
    def must(ok,why):
        if not ok:raise AssertionError('AMUI03B_HF03_REFUSED: '+why)
    full, target=source[FULL],source[TARGET]
    event=full.split('"on":',1)
    must(len(event)==2,'full event block absent')
    event=event[1].split('permissions:',1)[0]
    must('workflow_dispatch:' in event and '  push:' not in event and '  pull_request:' not in event,
         'full Android workflow must be manually dispatched')
    must('  device-instrumentation:' in full and '  amui01-android16:' in full and '  amt06c-fixture:' in full,
         'required full Android 15/16 and fixture gates absent')
    must('  push:' in target and '  pull_request:' in target,
         'targeted push and PR gates absent')
    for key in (F05,F06):
        src=source[key]
        must("'targeted': Path('.github/workflows/amui-targeted-ci.yml')" in src or
             "'targeted':Path('.github/workflows/amui-targeted-ci.yml')" in src,
             'missing targeted workflow file dependency: '+key)
        must("'workflow_dispatch:'" in src and "'  device-instrumentation:'" in src,
             'manual full qualification source assertions missing: '+key)
        must('inputs.mode == ' in src and 'instrumentation' in src,
             'lost manual Android instrumentation gate: '+key)
        must(PATH_TOKEN not in src.rsplit("'workflow':",1)[1].split("'targeted':",1)[0],
             'obsolete path-filter asserted as full workflow contract: '+key)
        must('BatchOpsService.java' in src and "'service':" in src,
             'real native backup/restore service safety checks removed: '+key)
        name=Path(key).name
        must('python3 scripts/devtool/'+name+' --check' in full,
             'full-source guard missing: '+key)
        must('python3 -B scripts/devtool/'+name+' --check' in target,
             'targeted source guard missing: '+key)
    for token in ('python3 -B scripts/devtool/check_amui03b_hf03_contracts.py --check',
                  'python3 -B scripts/devtool/test_amui03b_hf03_contracts.py',
                  "python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v"):
        must(token in target,'targeted regression missing: '+token)
    must('python3 scripts/devtool/check_amui03b_hf03_contracts.py --check' in full,
         'full-source parity guard missing')
    return True

def check(root=ROOT):return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.parse_args()
    check();print('AMUI03B_HF03_SOURCE_CONTRACTS_PASS')
