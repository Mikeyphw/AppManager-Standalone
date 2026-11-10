#!/usr/bin/env python3
"""AMUI03B: resize-safe compact app grid, fresh row dispatch, legacy guards retained."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
AUTO='libcore/ui/src/main/java/io/github/muntashirakon/view/AutoFitGridLayoutManager.java'
ACT='app/src/main/java/io/github/muntashirakon/AppManager/main/MainActivity.java'
ADAP='app/src/main/java/io/github/muntashirakon/AppManager/main/MainRecyclerAdapter.java'
INST='app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui03CompactRowInstrumentedTest.java'
LEGACY='scripts/devtool/check_amui03a_compact_list.py'
LEGACY_TEST='scripts/devtool/test_amui03a_compact_list.py'
WF='.github/workflows/amui-targeted-ci.yml'
FILES=(AUTO,ACT,ADAP,INST,LEGACY,LEGACY_TEST,WF)

def validate(src:dict[str,str])->bool:
    def must(ok,reason):
        if not ok:raise AssertionError('AMUI03B_REFUSED: '+reason)
    grid=src[AUTO];act=src[ACT];adapter=src[ADAP];inst=src[INST];old=src[LEGACY];tests=src[LEGACY_TEST];wf=src[WF]
    must('private int mLastAvailableSpace = -1;' in grid,'width cache absent')
    must('public static int calculateSpanCount(int availableSpace, int columnWidth)' in grid,'testable pure span sizing absent')
    must('if (columnWidth <= 0) return 1;' in grid,'zero-column-width guard removed')
    must('Math.max(1, Math.max(0, availableSpace) / columnWidth)' in grid,'span count no longer bounded to >= 1')
    must('int availableSpace = getOrientation() == VERTICAL' in grid and
         'getWidth() - getPaddingRight() - getPaddingLeft()' in grid and
         'getHeight() - getPaddingTop() - getPaddingBottom()' in grid,'padding/axis sizing lost')
    must('if ((mColumnWidthChanged || availableSpace != mLastAvailableSpace) && mColumnWidth > 0)' in grid,
         'window resize must recompute spans')
    must('int spanCount = calculateSpanCount(availableSpace, mColumnWidth);' in grid,'span sizing not using tested function')
    must('if (getSpanCount() != spanCount) setSpanCount(spanCount);' in grid,'repeated spans trigger unnecessary relayouts')
    must('mLastAvailableSpace = availableSpace;' in grid and
         'mColumnWidthChanged = false;' in grid,'resize cache never updated')
    must('new AutoFitGridLayoutManager(this, UiUtils.dpToPx(this, 480))' in act,
         'compact grid should reserve 480dp for full metadata')
    must('recyclerView.setAdapter(mAdapter);' in act and
         'mAdapter.setHasStableIds(true);' in act and 'mSwipeRefresh.setOnRefreshListener(this);' in act,
         'app list binding/refresh lifecycle changed')
    must('io.github.muntashirakon.view.AutoFitGridLayoutManager' in act,'grid import missing')
    must('UIUtils.getGridLayoutAt450Dp(this)' not in act,'old undersized card columns retained')
    must(adapter.count('handleClick(getItem(currentPos));')==1,'row click must use current bound position')
    must('handleClick(item);' not in adapter,'stale captured item may route wrong app')
    click=adapter.split('cardView.setOnClickListener(v -> {',1)
    must(len(click)==2,'main row click listener missing')
    click=click[1].split('cardView.setOnLongClickListener(',1)[0]
    for marker in ('getBindingAdapterPosition()', 'RecyclerView.NO_POSITION',
                   'if (isInSelectionMode())', 'toggleSelection(currentPos);',
                   'handleClick(getItem(currentPos));'):
        must(marker in click,'row click position/selection guard lost '+marker)
    must(adapter.count('toggleSelection(currentPos);')==3,
         'selection paths must remain row, long-press and icon')
    must(adapter.count('cardView.setStrokeColor(')==4,
         'stroke priority must preserve four branches')
    for marker in ('if (!item.isInstalled)', 'else if (item.isDisabled)', 'else if (item.isStopped)',
                   'holder.icon.setOnClickListener(', 'cardView.setOnLongClickListener(',
                   'notifySelectionChange();','getItem(position).hashCode()'):
        must(marker in adapter,'selection/status/stable IDs drifted '+marker)
    must("'handleClick(getItem(currentPos));'" in old,"AMUI03A legacy checker not migrated")
    must("'handleClick(getItem(currentPos));'" in tests,"AMUI03A negative regression test not migrated")
    must("'handleClick(item);'" not in old and "'handleClick(item);'" not in tests,
         'legacy source guard still pins stale click path')
    for marker in ('spanCountTracksCompactWidthBoundaries', 'cardCheckableStateStillRespondsToSelection',
                   'assertEquals(3, AutoFitGridLayoutManager.calculateSpanCount(1440, 480));',
                   'card.setChecked(true);','card.setChecked(false);'):
        must(marker in inst,'hosted smoke test missing '+marker)
    must(inst.count('@Test')>=3,'device smoke test coverage reduced')
    must('python3 -B scripts/devtool/check_amui03b_responsive_list.py --check' in wf and
         'python3 -B scripts/devtool/test_amui03b_responsive_list.py' in wf,
         'targeted CI missing new checks')
    must('Scoped Android resource and Java compile (no emulator)' in wf,
         'hosted compilation gate removed')
    return True

def check(root:Path=ROOT)->bool:
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.parse_args()
    check();print('AMUI03B_RESPONSIVE_SOURCE_PASS')
