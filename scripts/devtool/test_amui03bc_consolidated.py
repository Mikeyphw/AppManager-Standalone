#!/usr/bin/env python3
"""AMUI-03B/03C positive and negative source regression tests."""
import unittest
from check_amui03bc_consolidated import ROOT,FILES,validate,ACT,AD,VM,QUICK,MAIN,ROW,GRID,TARGETED,FULL
class ConsolidatedUXTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def test_positive(self):
        self.assertTrue(validate(self.src))
    def reject(self,path,old,new):
        self.assertIn(old,self.src[path]);source=dict(self.src)
        source[path]=source[path].replace(old,new,1)
        with self.assertRaises(AssertionError):validate(source)
    def test_missing_chip(self):self.reject(QUICK,'@+id/amui03c_frozen','@+id/broken')
    def test_chip_unbound(self):self.reject(ACT,'R.id.amui03c_backed_up','R.id.broken')
    def test_no_clear_filter(self):self.reject(ACT,'viewModel.clearListFilters();','// removed')
    def test_no_detail_toggle(self):self.reject(ACT,'mAdapter.setDetailedMode(detailed);','// removed')
    def test_no_display_mode_listener(self):self.reject(ACT,'mDisplayMode.setOnClickListener(v -> {','mDisplayMode.setOnClickListener(null) /* removed */; //')
    def test_no_display_mode_inversion(self):self.reject(ACT,'boolean detailed = !mAdapter.isDetailedMode();','boolean detailed = mAdapter.isDetailedMode();')
    def test_no_display_mode_refresh(self):
        # The toggle must update its selected state, not merely the adapter.
        self.reject(ACT,
                    'getPreferences(Context.MODE_PRIVATE).edit().putBoolean("amui03c_detailed", detailed).apply();\n            updateQuickFilters();',
                    'getPreferences(Context.MODE_PRIVATE).edit().putBoolean("amui03c_detailed", detailed).apply();\n            // no refresh')
    def test_no_startup_restore(self):self.reject(ACT,'mAdapter.setDetailedMode(getPreferences(Context.MODE_PRIVATE).getBoolean("amui03c_detailed", false));','// lost startup display preference')
    def test_no_persistence(self):self.reject(ACT,'putBoolean("amui03c_detailed", detailed)','putBoolean("different", detailed)')
    def test_no_date_collapse(self):self.reject(AD,'holder.date.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);','// removed')
    def test_no_sdk_collapse(self):self.reject(AD,'holder.size.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);','// removed')
    def test_no_live_click(self):self.reject(AD,'handleClick(getItem(currentPos));','handleClick(item);')
    def test_no_selection(self):self.reject(AD,'toggleSelection(currentPos);','// removed')
    def test_no_filter_preservation(self):self.reject(VM,'next &= ~MainListOptions.FILTER_SYSTEM_APPS;','// removed')
    def test_no_resize(self):self.reject(GRID,'availableSpace != mLastAvailableSpace','false')
    def test_no_quick_view(self):self.reject(MAIN,'@layout/amui03c_quick_filters','@layout/missing')
    def test_unsafe_ellipsize(self):self.reject(ROW,'android:singleLine="true"','android:maxLines="1"')
    def test_no_targeted_gate(self):self.reject(TARGETED,'python3 -B scripts/devtool/check_amui03bc_consolidated.py --check','echo ignored')
    def test_no_full_gate(self):self.reject(FULL,'python3 scripts/devtool/check_amui03bc_consolidated.py --check','echo ignored')
if __name__=='__main__':unittest.main()
