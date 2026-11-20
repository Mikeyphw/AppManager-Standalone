#!/usr/bin/env python3
"""AMUI-03B/03C: source-backed compact/detailed, quick filters, and selection invariants."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
ACT='app/src/main/java/io/github/muntashirakon/AppManager/main/MainActivity.java'
AD='app/src/main/java/io/github/muntashirakon/AppManager/main/MainRecyclerAdapter.java'
VM='app/src/main/java/io/github/muntashirakon/AppManager/main/MainViewModel.java'
ROW='app/src/main/res/layout/item_main.xml'
MAIN='app/src/main/res/layout/activity_main.xml'
QUICK='app/src/main/res/layout/amui03c_quick_filters.xml'
STRINGS='app/src/main/res/values/strings_amui03c.xml'
GRID='libcore/ui/src/main/java/io/github/muntashirakon/view/AutoFitGridLayoutManager.java'
TARGETED='.github/workflows/amui-targeted-ci.yml'
FULL='.github/workflows/devtool-tasker-ci.yml'
FILES=(ACT,AD,VM,ROW,MAIN,QUICK,STRINGS,GRID,TARGETED,FULL)
NS='{http://schemas.android.com/apk/res/android}'

def validate(src):
    def must(ok,msg):
        if not ok: raise AssertionError('AMUI03BC_REFUSED: '+msg)
    for p in FILES: must(isinstance(src.get(p),str) and bool(src[p]),'missing '+p)
    act,ad,vm,grid=src[ACT],src[AD],src[VM],src[GRID]
    row=ET.fromstring(src[ROW]); page=ET.fromstring(src[MAIN]); quick=ET.fromstring(src[QUICK]); strings=ET.fromstring(src[STRINGS])
    must(any(node.get('layout')=='@layout/amui03c_quick_filters' for node in page.iter()),'filter row missing from live activity')
    for n in ['amui03c_all','amui03c_user','amui03c_system','amui03c_frozen','amui03c_backed_up','amui03c_advanced','amui03c_display_mode','amui03c_summary']:
        must(any(node.get(NS+'id')=='@+id/'+n for node in quick.iter()),'missing quick control '+n)
        must('R.id.'+n in act,'quick filter not bound to activity '+n)
    ids={n.get('name') for n in strings.iter()}
    for n in ['amui03c_all','amui03c_compact','amui03c_detailed','amui03c_results_summary']:
        must(n in ids,'missing localized label '+n)
    for marker in ['bindQuickFilters();','viewModel.setQuickFilterFlag(', 'viewModel.clearListFilters();',
        'viewModel.hasAdvancedListFilters()', 'viewModel.hasActiveListFilters()',
        'new AutoFitGridLayoutManager(this, UiUtils.dpToPx(this, 480))', 'mListSummary.setText(']:
        must(marker in act,'missing live quick-filter/density wiring '+marker)
    # A separate startup setDetailedMode call must never mask removal of the
    # user-facing display-mode toggle. Require the complete action in its own
    # listener, including selection inversion, adapter update and persistence.
    must('mAdapter.setDetailedMode(getPreferences(Context.MODE_PRIVATE).getBoolean("amui03c_detailed", false));' in act,
         'saved detailed-mode preference no longer restored on startup')
    match=re.search(r'mDisplayMode\.setOnClickListener\(v\s*->\s*\{(?P<body>.*?)\n\s*\}\);',act,re.S)
    must(match is not None,'display-mode chip click listener missing')
    toggle=match.group('body')
    for marker in ['boolean detailed = !mAdapter.isDetailedMode();',
        'mAdapter.setDetailedMode(detailed);',
        'getPreferences(Context.MODE_PRIVATE).edit().putBoolean("amui03c_detailed", detailed).apply();',
        'updateQuickFilters();']:
        must(marker in toggle,'display-mode chip does not toggle, persist and refresh: '+marker)
    for marker in ['private boolean mDetailedMode;', 'notifyDataSetChanged();',
        'holder.date.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);',
        'holder.userId.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);',
        'holder.size.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);',
        'holder.issuer.setVisibility(View.GONE);', 'holder.sha.setVisibility(View.GONE);',
        'holder.backupInfo.setVisibility(View.GONE);','holder.backupInfoExt.setVisibility(View.GONE);',
        'handleClick(getItem(currentPos));']:
        must(marker in ad,'missing compact/detailed or safe live click '+marker)
    # Rebind restores valid hidden metadata for each item, rather than relying on a previous holder.
    must('if (item.sha != null)' in ad and 'holder.issuer.setVisibility(View.VISIBLE);' in ad,
         'valid detailed signing metadata cannot return after switching')
    must('if (item.backup != null)' in ad and 'holder.backupInfo.setVisibility(View.VISIBLE);' in ad,
         'valid detailed backup metadata cannot return after switching')
    must(ad.count('toggleSelection(currentPos);')==3 and ad.count('cardView.setStrokeColor(')==4,
         'selection or status priority changed')
    for marker in ['AMUI03C_QUICK_FLAGS','MainListOptions.FILTER_USER_APPS',
        'MainListOptions.FILTER_SYSTEM_APPS', 'MainListOptions.FILTER_FROZEN_APPS',
        'MainListOptions.FILTER_APPS_WITH_BACKUPS','Prefs.MainPage.setFilters(',
        'next &= ~MainListOptions.FILTER_USER_APPS;', 'next &= ~MainListOptions.FILTER_SYSTEM_APPS;',
        'cancelIfRunning();','mListExecutor.submit(this::filterItemsByFlags)',
        'mFilterProfileName = null;', 'mSelectedUsers = null;', 'mListEpoch.get();']:
        must(marker in vm,'missing preserved advanced-filter/concurrency behavior '+marker)
    must('getSpanCount() != spanCount' in grid and 'availableSpace != mLastAvailableSpace' in grid,
         'width changes no longer update column count')
    pkg=next((n for n in row.iter() if n.get(NS+'id')=='@+id/packageName'),None)
    must(pkg is not None and pkg.get(NS+'singleLine')=='true' and pkg.get(NS+'maxLines') is None
         and pkg.get(NS+'ellipsize')=='middle','unsafe package ID ellipsizing')
    must('python3 -B scripts/devtool/check_amui03bc_consolidated.py --check' in src[TARGETED],
         'required targeted CI source check missing')
    must('python3 scripts/devtool/check_amui03bc_consolidated.py --check' in src[FULL],
         'full hosted source check missing')
    must("python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v" in src[TARGETED],
         'full targeted regression removed')
    return True

def check(root=ROOT):
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.parse_args()
    check();print('AMUI03BC_CONSOLIDATED_SOURCE_PASS')
