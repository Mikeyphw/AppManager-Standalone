#!/usr/bin/env python3
"""AMUI-04A fail-closed source checks: real API35/36 UI images and palette receipts."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
JAVA='app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui04AVisualInstrumentedTest.java'
RUNNER='scripts/devtool/amui02_hosted_theme.sh'
TARGET='.github/workflows/amui-targeted-ci.yml'
FULL='.github/workflows/devtool-tasker-ci.yml'
FILES=(JAVA,RUNNER,TARGET,FULL)

def validate(src):
    def must(ok,why):
        if not ok:raise AssertionError('AMUI04A_REFUSED: '+why)
    java,runner,target,full=(src[p] for p in FILES)
    must('class Amui04AVisualInstrumentedTest' in java and java.count('@Test')>=5,
         'device tests missing or reduced')
    for marker in ('@Before', '@After', 'restoreSettings()',
                   'Prefs.Appearance.setNightMode(originalNightMode);',
                   'Prefs.Appearance.setPureBlackTheme(originalBlack);',
                   'runOnMainSync(', 'View row = LayoutInflater.from(context).inflate(R.layout.item_main',
                   'View chips = LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters',
                   'View filters = LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters',
                   'assertEquals(Color.BLACK, color(context, android.R.attr.colorBackground))',
                   'Color.BLACK, color(context, androidx.appcompat.R.attr.colorPrimary)',
                   'Color.BLACK, color(context, com.google.android.material.R.attr.colorSurface)',
                   'getExternalFilesDir(Environment.DIRECTORY_PICTURES)',
                   'bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)',
                   'snapshot("light", false, false)', 'snapshot("dark", true, false)',
                   'snapshot("pure-black", true, true)'):
        must(marker in java,'device invariant absent: '+marker)
    must('FileOutputStream' in java and 'Bitmap.createBitmap(' in java,
         'PNG must be generated from rendered Android views')
    must('Intent.ACTION_PACKAGE_DELETE' not in java and 'deletePackage' not in java and
         'Runtime.getRuntime().exec' not in java,
         'AMUI04A visual tests must not modify real packages')
    for marker in ('Amui04AVisualInstrumentedTest', 'AMUI04A_HOSTED_VISUAL_PASS',
                   "int(receipt.get('passed', 0)) >= 5", "int(receipt.get('failed', 1)) == 0",
                   "assert p.is_file()", 'amui04a-api${api}.json',
                   'amui04a-screenshots-api${api}', 'adb pull',
                   'sha256sum', 'test -s', 'AMUI04A_EXPECT_SCREENSHOT_COUNT=3',
                   'assert len(hashes)==3'):
        must(marker in runner,'hosted receipt/screenshot guard absent '+marker)
    must('AMUI02_HOSTED_THEME_PASS' in runner and 'AMUI03C_HOSTED_UI_PASS' in runner,
         'older hosted instrumentations removed')
    must('python3 -B scripts/devtool/check_amui04a_visual_gate.py --check' in target,
         'targeted contract missing')
    must('python3 -B -m unittest discover -s scripts/devtool' in target and
         'Scoped Android resource and Java compile (no emulator)' in target,
         'targeted tests or compile weakened')
    must('python3 scripts/devtool/check_amui04a_visual_gate.py --check' in full,
         'full source check missing')
    events=full.split('"on":',1)[1].split('permissions:',1)[0]
    must('  workflow_dispatch:' in events and '  push:' not in events and '  pull_request:' not in events,
         'full Android gate is no longer manual-only')
    for token in ('  device-instrumentation:', '  amui01-android16:', '  amt06c-fixture:',
                  'script: bash scripts/devtool/amt03_hosted_instrumentation.sh',
                  'AMUI01_EXPECT_API=36 bash scripts/devtool/amui01_hosted_instrumentation.sh'):
        must(token in full,'old full Android gates weakened: '+token)
    must(full.count('${{ runner.temp }}/amui04a-api*.json')==2,
         'missing both API35/36 visual receipt artifact patterns')
    must(full.count('${{ runner.temp }}/amui04a-screenshots-api*/**')==2,
         'missing both API35/36 actual PNG artifact patterns')
    return True

def check(root=ROOT):
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})
if __name__=='__main__':
    import argparse
    argparse.ArgumentParser().add_argument('--check', action='store_true')
    check();print('AMUI04A_SOURCE_CONTRACT_PASS')
