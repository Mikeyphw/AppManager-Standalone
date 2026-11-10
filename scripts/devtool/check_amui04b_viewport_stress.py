#!/usr/bin/env python3
"""AMUI-04B: read-only API35/36 list viewport and virtualized large-list evidence contracts."""
from __future__ import annotations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
JAVA='app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui04BViewportStressInstrumentedTest.java'
RUNNER='scripts/devtool/amui02_hosted_theme.sh'
TARGET='.github/workflows/amui-targeted-ci.yml'
FULL='.github/workflows/devtool-tasker-ci.yml'
VIEWMODEL='app/src/main/java/io/github/muntashirakon/AppManager/main/MainViewModel.java'
FILES=(JAVA,RUNNER,TARGET,FULL,VIEWMODEL)

def validate(src):
    def must(ok,why):
        if not ok:raise AssertionError('AMUI04B_REFUSED '+why)
    java,runner,target,full,vm=(src[p] for p in FILES)
    must('class Amui04BViewportStressInstrumentedTest' in java and java.count('@Test')>=6,
         'six Android device cases absent')
    for marker in (
        'LARGE_LIST_SIZE = 600', 'setHasStableIds(true);',
        'onCreateViewHolder(', 'onBindViewHolder(',
        'getItemId(int position)', 'holder.card.setChecked((position % 2) == 0);',
        'runOnMainSync(', 'new AutoFitGridLayoutManager(context, columnPx)',
        'Math.max(1, width / 640)', 'list.getChildCount() < 100',
        'list.scrollToPosition(position);', 'getChildAdapterPosition(row)',
        'quickChipsRemainInteractiveAfterWidthAndRtlChanges',
        'repeatedViewRecreationPreservesAllAdapterBindingIds',
        'R.id.backup_info_ext', 'View.LAYOUT_DIRECTION_RTL',
        'R.layout.amui03c_quick_filters', 'R.layout.item_main',
        '"RTL viewport fixture"', '"Wide viewport fixture"',
        '"Narrow viewport fixture"',
        'Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)',
        'bitmap.compress(Bitmap.CompressFormat.PNG, 100, writer)',
        'getExternalFilesDir(Environment.DIRECTORY_PICTURES)',
        'snapshot("narrow", 720, 1280, false)',
        'snapshot("wide", 1920, 1200, false)',
        'snapshot("rtl", 720, 1280, true)',
    ):
        must(marker in java,'device fixture assertion missing: '+marker)
    must('Runtime.getRuntime().exec' not in java and 'deletePackage' not in java
         and 'ACTION_PACKAGE_DELETE' not in java and 'grantRuntimePermission' not in java,
         'device stress must not alter installed packages or permissions')
    for marker in (
        'Amui04BViewportStressInstrumentedTest',
        'AMUI04B_HOSTED_VIEWPORT_PASS',
        "int(receipt.get('executed', 0)) >= 6",
        "int(receipt.get('passed', 0)) >= 6",
        "int(receipt.get('failed', 1)) == 0",
        "assert receipt.get('status') in ('success', 'passed')",
        "assert os.environ.get('GITHUB_SHA', '').strip()",
        'amui04b-api${api}.json',
        'amui04b-screenshots-api${api}',
        'AMUI04B_EXPECT_SCREENSHOTS=3',
        'adb pull', 'sha256sum',
        "assert len(hashes)==3,'AMUI04B_DUPLICATE_VIEWPORT_IMAGES'",
        "'narrow':(720,1280)",
        "'wide':(1920,1200)",
        "'rtl':(720,1280)",
    ):
        must(marker in runner,'device receipt, geometry or hash verification removed: '+marker)
    must(runner.count("assert len(hashes)==3,'AMUI04B_DUPLICATE_VIEWPORT_IMAGES'")==1,
         'AMUI04B unique screenshot hash guard missing or duplicated')
    must('AMUI04A_HOSTED_VISUAL_PASS' in runner and 'AMUI03C_HOSTED_UI_PASS' in runner
         and 'AMUI02_HOSTED_THEME_PASS' in runner,
         'prior device visual/theme acceptance removed')
    must('python3 -B scripts/devtool/check_amui04b_viewport_stress.py --check' in target,
         'targeted AMUI04B source acceptance absent')
    must("python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v" in target and
         'Scoped Android resource and Java compile (no emulator)' in target,
         'targeted mutation or Java compilation guard removed')
    must('python3 scripts/devtool/check_amui04b_viewport_stress.py --check' in full,
         'full source acceptance absent')
    events=full.split('"on":',1)[1].split('permissions:',1)[0]
    must('  workflow_dispatch:' in events and '  push:' not in events and '  pull_request:' not in events,
         'full Android qualification cannot be automatic')
    for token in ('  device-instrumentation:', '  amui01-android16:', '  amt06c-fixture:',
                  'script: bash scripts/devtool/amt03_hosted_instrumentation.sh',
                  'AMUI01_EXPECT_API=36 bash scripts/devtool/amui01_hosted_instrumentation.sh'):
        must(token in full,'prior Android/Tasker gates weakened: '+token)
    for token in ('${{ runner.temp }}/amui04b-api*.json',
                  '${{ runner.temp }}/amui04b-api*.log',
                  '${{ runner.temp }}/amui04b-screenshots-api*/**',
                  '${{ runner.temp }}/amui04b-screenshots-api*.sha256'):
        must(full.count(token)==2,'both API35/API36 must archive evidence: '+token)
    for token in ('${{ runner.temp }}/amui04a-api*.json',
                  '${{ runner.temp }}/amui04a-screenshots-api*/**'):
        must(full.count(token)==2,'AMUI04A evidence removed: '+token)
    # These are audit anchors in the actual concurrent ViewModel, not a simulated model.
    for token in ('Executors.newSingleThreadExecutor()',
                  'private final AtomicLong mListEpoch = new AtomicLong();',
                  'private final AtomicLong mRefreshRequestId = new AtomicLong();',
                  'if (epoch != mListEpoch.get())',
                  'mApplicationItemsLiveData.setValue(Collections.unmodifiableList(snapshot));',
                  'public void refreshApplications(@NonNull String reason)',
                  'filterItemsByFlags();',
                  'mRefreshState.setValue(status.withVisibleCount(snapshot.size(), filtered));'):
        must(token in vm,'source refresh/race invariant lost: '+token)
    return True

def check(root=ROOT):
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})

if __name__=='__main__':
    import argparse
    argparse.ArgumentParser().add_argument('--check',action='store_true')
    check();print('AMUI04B_VIEWPORT_STRESS_SOURCE_PASS')
