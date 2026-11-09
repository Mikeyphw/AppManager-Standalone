#!/usr/bin/env python3
"""CI policy: full hosted acceptance only on explicit manual gates."""
from pathlib import Path

PUSH="(github.event_name == 'push' && startsWith(github.ref, 'refs/heads/feature/amui01'))"
ORIGINAL_AMT="inputs.mode == 'full' || inputs.mode == 'instrumentation'"
ORIGINAL_16="inputs.mode == 'instrumentation' || inputs.mode == 'full'"


def must(value, message):
    if not value: raise AssertionError('AMUI_CI_POLICY_REFUSED: '+message)


def validate_workflow(src):
    must(src.count('"on":\n') == 1, 'missing explicit Actions event trigger')
    trigger=src.split('"on":\n',1)[1].split('\npermissions:',1)[0]
    must('  workflow_dispatch:\n' in trigger and 'options: [source, build, test, lint, instrumentation, full]' in trigger,
         'manual full mode unavailable')
    must('\n  push:' not in trigger and '\n  pull_request:' not in trigger and '\n  workflow_run:' not in trigger,
         'automatic heavy Actions trigger detected')
    must(src.count(PUSH)==6, 'existing six protected legacy push expressions changed')
    must(src.count(ORIGINAL_AMT)==1 and src.count(ORIGINAL_16)==1,
         'manual API35/API36 full mode removed')
    must(src.count('disable-linux-hw-accel: false')==1, 'API35 KVM gate lost')
    must(src.count("disable-linux-hw-accel: 'false'")==1, 'API36 KVM gate lost')
    before_build,after_build=src.split('  hosted-android:\n',1)
    android,rest=after_build.split('  device-instrumentation:\n',1)
    legacy,rest=rest.split('  amt06c-fixture:\n',1)
    fixture,api36=rest.split('  amui01-android16:\n',1)
    must("github.event_name == 'workflow_dispatch'" in android.split('    runs-on:',1)[0] and "inputs.mode != 'source'" in android,
         'manual hosted Gradle/lint gate removed')
    must("github.event_name == 'workflow_dispatch'" in legacy.split('    runs-on:',1)[0] and ORIGINAL_AMT in legacy,
         'manual Android 15 device gate removed')
    must("github.event_name == 'workflow_dispatch'" in fixture.split('    runs-on:',1)[0] and "inputs.mode == 'full'" in fixture,
         'manual disposable Tasker fixture gate removed')
    must("github.event_name == 'workflow_dispatch'" in api36.split('    runs-on:',1)[0] and ORIGINAL_16 in api36,
         'manual Android 16 device gate removed')
    must('api-level: 35' in legacy and 'api-level: 36' in api36,
         'Android API acceptance mismatch')
    must('Upload hosted Android lint report' in android and 'if-no-files-found: error' in android,
         'strict hosted lint report gate removed')
    must('script: bash scripts/devtool/amt03_hosted_instrumentation.sh && bash scripts/devtool/amui01_hosted_instrumentation.sh' in legacy,
         'API35 Tasker and AMUI01 instrumentation not retained')
    must('script: AMUI01_EXPECT_API=36 bash scripts/devtool/amui01_hosted_instrumentation.sh' in api36,
         'API36 acceptance script missing')
    must('AMUI02_EXPECT_API=36' in api36 and 'scripts/devtool/amui02_hosted_theme.sh' in legacy,
         'AMUI02 dual-API device tests missing')
    return True

if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    validate_workflow((root/'.github/workflows/devtool-tasker-ci.yml').read_text())
    print('AMUI_CI_MANUAL_GATE_CONTRACT_PASS')
