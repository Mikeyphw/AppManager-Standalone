#!/usr/bin/env python3
"""AMUI03B HF02: manual full CI must retain all source contracts in targeted CI."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FULL='.github/workflows/devtool-tasker-ci.yml'
TARGET='.github/workflows/amui-targeted-ci.yml'
AMT='scripts/devtool/check_amt04b_contract.py'
RETRY='scripts/devtool/amui_gate_retry.py'
FILES=(FULL,TARGET,AMT,RETRY)

def source_commands(full):
    anchor='      - name: Source checks (no Gradle)\n        run: |\n'
    assert full.count(anchor)==1,'AMUI03B_HF02_REFUSED: missing single full source job'
    block=full.split(anchor,1)[1].split('      - name:',1)[0]
    commands=[line.strip() for line in block.splitlines() if line.strip().startswith(('python3 ','sh -n'))]
    assert len(commands)>=20,'AMUI03B_HF02_REFUSED: truncated full source gate'
    return commands

def validate(data):
    full=data[FULL]
    targeted=data[TARGET]
    amt=data[AMT]
    retry=data[RETRY]
    block=full.split('"on":',1)[1].split('\npermissions:',1)[0]
    assert 'workflow_dispatch:' in block and 'push:' not in block and 'pull_request:' not in block,\
        'AMUI03B_HF02_REFUSED: full CI auto-triggered'
    assert '  device-instrumentation:' in full and '  amui01-android16:' in full,\
        'AMUI03B_HF02_REFUSED: full emulator jobs removed'
    assert '  push:' in targeted and '  pull_request:' in targeted,\
        'AMUI03B_HF02_REFUSED: targeted triggers removed'
    for command in source_commands(full):
        if command.startswith('python3 scripts/'):
            check='python3 -B '+command.removeprefix('python3 ')
        elif command.startswith('python3 -m unittest'):
            check='python3 -B '+command.removeprefix('python3 ')
        else:check=command
        assert check in targeted, 'AMUI03B_HF02_REFUSED: full source check not targeted '+check
    assert 'amui-targeted-ci.yml' in amt and \
        "'workflow_dispatch:'" in amt and \
        "'  device-instrumentation:'" in amt and \
        'python3 -B scripts/devtool/check_amt04b_contract.py --check' in amt,\
        'AMUI03B_HF02_REFUSED: AMT04B1 still tied to automatic full trigger'
    assert 'python3 -B scripts/devtool/check_amui03b_hf02_gate.py --check' in targeted and \
        'python3 -B scripts/devtool/test_amui03b_hf02_gate.py' in targeted,\
        'AMUI03B_HF02_REFUSED: new source regression suite not targeted'
    for token in ('ORIGINAL =', 'FAILED_RUN = 42735142696','len(overlays)!=5',
                  "gate['recovered_from']=ORIGINAL",'find_existing_run(args.head)',
                  "verify_run(failed,ORIGINAL,failed=True)",
                  "cmd('git','merge-base','--is-ancestor',ORIGINAL,head,cwd=root)",
                  "cmd('git','ls-remote'"):
        assert token in retry,'AMUI03B_HF02_REFUSED: retry safety missing '+token
    return True

def run(root=ROOT):
    return validate({name:(root/name).read_text(encoding='utf-8') for name in FILES})
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--check',action='store_true');a.parse_args()
    run();print('AMUI03B_HF02_SOURCE_PARITY_PASS')
