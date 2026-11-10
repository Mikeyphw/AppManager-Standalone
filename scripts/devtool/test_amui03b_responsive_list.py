#!/usr/bin/env python3
"""AMUI03B static negative source regressions, portable and no Android/Gradle."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui03b_responsive_list import ROOT,FILES,AUTO,ACT,ADAP,INST,LEGACY,LEGACY_TEST,WF,validate

class ResponsiveListContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,path,old,new):
        self.assertIn(old,self.src[path],f'bad regression fixture anchor {path}')
        changed=dict(self.src)
        changed[path]=changed[path].replace(old,new,1)
        with self.assertRaisesRegex(AssertionError,'AMUI03B_REFUSED'):
            validate(changed)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_resize_condition(self):self.reject(AUTO,'availableSpace != mLastAvailableSpace','false')
    def test_unbounded_spans(self):self.reject(AUTO,'Math.max(1, Math.max(0, availableSpace) / columnWidth)', 'availableSpace / columnWidth')
    def test_zero_column_width(self):self.reject(AUTO,'if (columnWidth <= 0) return 1;','')
    def test_width_cache(self):self.reject(AUTO,'mLastAvailableSpace = availableSpace;','')
    def test_resize_calculator_usage(self):self.reject(AUTO,'calculateSpanCount(availableSpace, mColumnWidth)','1')
    def test_no_padding_calculation(self):self.reject(AUTO,'getWidth() - getPaddingRight() - getPaddingLeft()','getWidth()')
    def test_no_sizing_axis(self):self.reject(AUTO,'getHeight() - getPaddingTop() - getPaddingBottom()','getWidth()')
    def test_no_span_change_guard(self):self.reject(AUTO,'if (getSpanCount() != spanCount)','if (true)')
    def test_old_450_grid(self):self.reject(ACT,'new AutoFitGridLayoutManager(this, UiUtils.dpToPx(this, 480))','UIUtils.getGridLayoutAt450Dp(this)')
    def test_no_grid_import(self):self.reject(ACT,'import io.github.muntashirakon.view.AutoFitGridLayoutManager;','')
    def test_no_stable_ids(self):self.reject(ACT,'mAdapter.setHasStableIds(true);','')
    def test_stale_click(self):self.reject(ADAP,'handleClick(getItem(currentPos));','handleClick(item);')
    def test_row_position_guard(self):self.reject(ADAP,'if (currentPos == RecyclerView.NO_POSITION) return;','if (false) return;')
    def test_row_selection(self):self.reject(ADAP,'toggleSelection(currentPos);','// row selection lost')
    def test_long_selection(self):self.reject(ADAP,'cardView.setOnLongClickListener(', '// long press lost')
    def test_icon_selection(self):self.reject(ADAP,'holder.icon.setOnClickListener(', '// icon selection lost')
    def test_status_stroke(self):self.reject(ADAP,'cardView.setStrokeColor(', '// status stroke lost')
    def test_legacy_checker_migration(self):self.reject(LEGACY,"'handleClick(getItem(currentPos));'","'handleClick(item);'")
    def test_legacy_test_migration(self):self.reject(LEGACY_TEST,"'handleClick(getItem(currentPos));'","'handleClick(item);'")
    def test_missing_device_span(self):self.reject(INST,'spanCountTracksCompactWidthBoundaries','removedSpanTest')
    def test_missing_device_card(self):self.reject(INST,'cardCheckableStateStillRespondsToSelection','removedCardTest')
    def test_missing_hosted_checker(self):self.reject(WF,'python3 -B scripts/devtool/check_amui03b_responsive_list.py --check','echo skipped')
    def test_missing_hosted_tests(self):self.reject(WF,'python3 -B scripts/devtool/test_amui03b_responsive_list.py','echo skipped')
    def test_missing_compile(self):self.reject(WF,'Scoped Android resource and Java compile (no emulator)','compile disabled')

if __name__=='__main__':unittest.main()
