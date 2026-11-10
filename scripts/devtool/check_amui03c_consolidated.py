#!/usr/bin/env python3
"""AMUI-03C static safety and UI source contracts (no Gradle or device)."""
from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
ACT='app/src/main/java/io/github/muntashirakon/AppManager/main/MainActivity.java'
VM='app/src/main/java/io/github/muntashirakon/AppManager/main/MainViewModel.java'
ADAP='app/src/main/java/io/github/muntashirakon/AppManager/main/MainRecyclerAdapter.java'
LAYOUT='app/src/main/res/layout/activity_main.xml'
QUICK='app/src/main/res/layout/amui03c_quick_filters.xml'
STR='app/src/main/res/values/strings_amui03c.xml'
DEVICE='app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui03CQuickFiltersInstrumentedTest.java'
SCRIPT='scripts/devtool/amui02_hosted_theme.sh'
TARGET='.github/workflows/amui-targeted-ci.yml'
FULL='.github/workflows/devtool-tasker-ci.yml'
FILES=(ACT,VM,ADAP,LAYOUT,QUICK,STR,DEVICE,SCRIPT,TARGET,FULL)
NS='{http://schemas.android.com/apk/res/android}'
APP='{http://schemas.android.com/apk/res-auto}'
IDS=('all','user','system','frozen','backed_up','advanced','display_mode')

def validate(src):
    def must(ok,reason):
        if not ok: raise AssertionError('AMUI03C_REFUSED: '+reason)
    a,vm,d=src[ACT],src[VM],src[ADAP]
    # HF01: UiThread is a method annotation, never a field annotation.
    # The previous overlay moved the original method annotation onto the new
    # mDetailedMode field, and Android javac correctly refused compilation.
    must('    @UiThread\n    void setDefaultList(List<ApplicationItem> list) {' in d,
         'UiThread must directly annotate the adapter list method')
    must('    @UiThread\n    private boolean mDetailedMode;' not in d,
         'UiThread illegally applied to mDetailedMode field')
    layout=ET.fromstring(src[LAYOUT]); quick=ET.fromstring(src[QUICK])
    ET.fromstring(src[STR])
    must(sum(1 for n in layout.iter() if n.get('layout')=='@layout/amui03c_quick_filters')==1,
         'quick filter strip missing or duplicated')
    nodes={n.get(NS+'id','').removeprefix('@+id/'):n for n in quick.iter() if n.get(NS+'id','').startswith('@+id/')}
    must(any(n.tag=='HorizontalScrollView' for n in quick.iter()),
         'horizontal quick-filter scrolling removed')
    must(not any(APP+'checkable' in n.attrib for n in quick.iter()),
         'invalid app:checkable namespace: Material Chip requires android:checkable')
    for item in IDS:
        ident='amui03c_'+item
        must(ident in nodes and nodes[ident].tag=='com.google.android.material.chip.Chip',
             'missing chip '+ident)
        if item!='advanced': must(nodes[ident].get(NS+'checkable')=='true','non-checkable quick chip '+item)
    must(nodes['amui03c_advanced'].get(NS+'checkable')=='false','advanced must be a button')
    must('amui03c_summary' in nodes and nodes['amui03c_summary'].tag.endswith('TextView'),
         'visible app result count missing')
    must('amui03c_chips' in nodes and nodes['amui03c_chips'].get(APP+'singleLine')=='true',
         'quick filters must scroll horizontally')
    must(nodes['amui03c_chips'].get(APP+'selectionRequired')=='false',
         'quick filters must permit deselection, including All/none state')
    for marker in ('bindQuickFilters();', 'mQuickAll.setOnClickListener(', 'viewModel.clearListFilters();',
                   'mQuickUser.setOnClickListener(', 'mQuickSystem.setOnClickListener(',
                   'mQuickFrozen.setOnClickListener(', 'mQuickBackedUp.setOnClickListener(',
                   'mQuickAdvanced.setOnClickListener(v -> showListOptions());',
                   'viewModel.setQuickFilterFlag(flag, chip.isChecked());',
                   'mDisplayMode.setOnClickListener(', 'mAdapter.setDetailedMode(detailed);',
                   'getPreferences(Context.MODE_PRIVATE).edit().putBoolean("amui03c_detailed", detailed).apply();',
                   'getPreferences(Context.MODE_PRIVATE).getBoolean("amui03c_detailed", false)',
                   'updateQuickFilters(applicationItems.size());',
                   'mQuickAll.setChecked(!viewModel.hasActiveListFilters());',
                   'viewModel.hasAdvancedListFilters()',
                   'mListSummary.setText(getString(R.string.amui03c_results_summary,'):
        must(marker in a,'missing UI wiring '+marker)
    for marker in ('AMUI03C_QUICK_FLAGS', 'public void setQuickFilterFlag(',
                   'public void clearListFilters()', 'public boolean hasActiveListFilters()',
                   'public boolean hasAdvancedListFilters()',
                   'next &= ~MainListOptions.FILTER_SYSTEM_APPS;',
                   'next &= ~MainListOptions.FILTER_USER_APPS;',
                   'Prefs.MainPage.setFilteredProfileName(null);',
                   'mFilterResult = mListExecutor.submit(this::filterItemsByFlags);'):
        must(marker in vm,'missing filter behavior '+marker)
    clear=vm.split('public void clearListFilters()',1)[1].split('public boolean hasActiveListFilters()',1)[0]
    must('mSearchQuery =' not in clear and 'mSortBy =' not in clear,
         'clear filters must preserve advanced search and current sorting')
    for marker in ('private boolean mDetailedMode;', 'boolean isDetailedMode()',
                   'void setDetailedMode(boolean detailed)', 'notifyDataSetChanged();',
                   'holder.date.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);',
                   'holder.userId.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);',
                   'holder.size.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);',
                   'holder.backupInfo.setVisibility(View.GONE);',
                   'holder.backupInfoExt.setVisibility(View.GONE);'):
        must(marker in d,'missing compact/detailed binding '+marker)
    must(d.count('toggleSelection(currentPos);')==3 and d.count('cardView.setStrokeColor(')==4,
         'multi-selection/status safety changed')
    must('handleClick(getItem(currentPos));' in d and 'handleClick(item);' not in d,
         'stale click routing')
    must('public void refreshApplications(@NonNull String reason)' in vm and
         'mListExecutor.submit(this::filterItemsByFlags)' in vm,
         'authoritative refresh/serialized filtering lost')
    t=src[TARGET];full=src[FULL];sh=src[SCRIPT];inst=src[DEVICE]
    must('python3 -B scripts/devtool/check_amui03c_consolidated.py --check' in t,
         'targeted source gate missing')
    must("python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v" in t,
         'targeted negative mutations not registered')
    must('Scoped Android resource and Java compile (no emulator)' in t,
         'hosted targeted compile removed')
    must('python3 scripts/devtool/check_amui03c_consolidated.py --check' in full,
         'full source gate missing')
    event=full.split('"on":',1)[1].split('permissions:',1)[0]
    must('  workflow_dispatch:' in event and '  push:' not in event and '  pull_request:' not in event,
         'full Android gate must stay manual-only')
    must('Amui03CQuickFiltersInstrumentedTest' in inst and inst.count('@Test')>=3 and
         'public void allQuickFiltersInflateAndAreCheckable()' in inst,
         'device test coverage reduced')
    # The previous test changed a detached Chip off the instrumentation UI thread.
    # Do not satisfy this guard with runOnMainSync in an unrelated test.
    toggle=inst.split('public void quickChipSelectionCanToggleWithoutChangingPackages()',1)
    must(len(toggle)==2,'quick-chip device test missing')
    body=toggle[1].split('\n    }\n',1)[0]
    for token in ('runOnMainSync(() -> {', 'group.isSelectionRequired()',
                  'user.isCheckable()', 'user.setChecked(true);',
                  'user.setChecked(false);', 'assertTrue("Main-thread check did not stick", user.isChecked());',
                  'assertFalse("Main-thread uncheck did not stick", user.isChecked());',
                  'waitForIdleSync();'):
        must(token in body,'real UI-thread chip toggle/unchecked assertion removed: '+token)
    must(body.index('runOnMainSync(() -> {') < body.index('user.setChecked(true);')
         < body.index('user.setChecked(false);') < body.index('waitForIdleSync();'),
         'quick-chip lifecycle order weakened')
    must('Amui03CQuickFiltersInstrumentedTest' in sh and
         "int(receipt.get('passed',0)) >= 3" in sh and 'AMUI03C_HOSTED_UI_PASS' in sh,
         'Android API35/36 device receipt gate missing')
    must('AMUI02_EXPECT_API' in sh and 'AMUI02_HOSTED_THEME_PASS' in sh,
         'theme acceptance weakened')
    must(full.count('${{ runner.temp }}/amui03c-ui-*.json')==2,
         'both API35 and API36 must publish device receipts')
    must('AMT-03 Android instrumentation via Devtool emulator' in full and
         'AMUI-01 real package lifecycle on Android 16' in full,
         'existing device gates lost')
    return True

def check(root=ROOT):
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.parse_args()
    check();print('AMUI03C_CONSOLIDATED_SOURCE_CONTRACT_PASS')
