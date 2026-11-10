#!/usr/bin/env python3
"""AMUI-03C isolated negative mutations, including stale-anchor refusal."""
from __future__ import annotations
import sys, unittest, xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui03c_consolidated import ROOT,FILES,ACT,VM,ADAP,QUICK,LAYOUT,DEVICE,SCRIPT,TARGET,FULL,NS,APP,validate

class ConsolidatedListContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}

    def reject(self,path,old,new):
        self.assertNotEqual(old,new,'identical mutation is a no-op')
        self.assertEqual(self.src[path].count(old),1,'stale or ambiguous anchor: '+path)
        changed=dict(self.src);changed[path]=changed[path].replace(old,new,1)
        self.assertNotEqual(changed[path],self.src[path],'mutation was a no-op')
        with self.assertRaisesRegex(AssertionError,'AMUI03C_REFUSED'):
            validate(changed)

    def test_positive(self):self.assertTrue(validate(self.src))
    def test_stale_anchor_fails_closed(self):
        with self.assertRaisesRegex(AssertionError,'stale or ambiguous anchor'):
            self.reject(FULL,"      - 'app/src/main/java/obsolete/path/**'",'')
    def test_no_extra_mutation(self):
        with self.assertRaisesRegex(AssertionError,'identical mutation'):
            self.reject(ACT,'bindQuickFilters();','bindQuickFilters();')
    def test_no_include(self):self.reject(LAYOUT,'<include layout="@layout/amui03c_quick_filters" />','')
    def test_no_quick_user(self):self.reject(QUICK,'android:id="@+id/amui03c_user"','android:id="@+id/obsolete_user"')
    def test_no_clear_button(self):self.reject(ACT,'viewModel.clearListFilters();','// silently ignored')
    def test_no_safe_toggle(self):self.reject(ACT,'viewModel.setQuickFilterFlag(flag, chip.isChecked());','// silently ignored')
    def test_no_exclusive_user(self):self.reject(VM,'next &= ~MainListOptions.FILTER_SYSTEM_APPS;','')
    def test_no_exclusive_system(self):self.reject(VM,'next &= ~MainListOptions.FILTER_USER_APPS;','')
    def test_no_profile_clear(self):self.reject(VM,'Prefs.MainPage.setFilteredProfileName(null);','')
    def test_no_advanced_indicator(self):self.reject(ACT,'viewModel.hasAdvancedListFilters()','false')
    def test_no_mode_persistence(self):self.reject(ACT,'getPreferences(Context.MODE_PRIVATE).edit().putBoolean("amui03c_detailed", detailed).apply();','')
    def test_no_restore_mode(self):self.reject(ACT,'getPreferences(Context.MODE_PRIVATE).getBoolean("amui03c_detailed", false)','false')
    def test_no_rebind(self):self.reject(ADAP,'notifyDataSetChanged();','')
    def test_missing_ui_thread_method_annotation(self):
        self.reject(ADAP, '    @UiThread\n    void setDefaultList(List<ApplicationItem> list) {',
                    '    void setDefaultList(List<ApplicationItem> list) {')

    def test_illegal_ui_thread_field_annotation(self):
        self.reject(ADAP, '    private boolean mDetailedMode;',
                    '    @UiThread\n    private boolean mDetailedMode;')

    def test_no_hide_date(self):self.reject(ADAP,'holder.date.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);','')
    def test_no_hide_uid(self):self.reject(ADAP,'holder.userId.setVisibility(mDetailedMode ? View.VISIBLE : View.GONE);','')
    def test_no_current_item_routing(self):self.reject(ADAP,'handleClick(getItem(currentPos));','handleClick(item);')
    def test_no_targeted_checker(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amui03c_consolidated.py --check','echo skip')
    def test_no_full_checker(self):self.reject(FULL,'python3 scripts/devtool/check_amui03c_consolidated.py --check','echo skip')
    def test_full_manual_to_push(self):self.reject(FULL,'  workflow_dispatch:', '  push:')
    def test_no_android_report(self):self.reject(SCRIPT,'AMUI03C_HOSTED_UI_PASS','AMUI03C_NOT_TESTED')
    def test_no_android_tests(self):self.reject(DEVICE,'public void allQuickFiltersInflateAndAreCheckable()', 'public void allQuickFiltersRemoved()')

    def mutate_xml_chip(self, chip_name, update):
        source=dict(self.src)
        root=ET.fromstring(source[QUICK])
        selected=[x for x in root.iter() if x.get(NS+'id')=='@+id/amui03c_'+chip_name]
        self.assertEqual(len(selected),1,'required chip missing')
        update(selected[0])
        source[QUICK]=ET.tostring(root, encoding='unicode')
        with self.assertRaisesRegex(AssertionError,'AMUI03C_REFUSED'):
            validate(source)

    def test_rejects_user_chip_not_checkable(self):
        self.mutate_xml_chip('user',lambda el:el.set(NS+'checkable','false'))

    def test_rejects_advanced_chip_checkable(self):
        self.mutate_xml_chip('advanced',lambda el:el.set(NS+'checkable','true'))

    def test_rejects_app_namespace_chip_checkable(self):
        def wrong_namespace(el):
            del el.attrib[NS+'checkable']
            el.set(APP+'checkable','true')
        self.mutate_xml_chip('frozen',wrong_namespace)

    def test_rejects_missing_horizontal_scroll(self):
        source=dict(self.src)
        root=ET.fromstring(source[QUICK])
        scroll=root.find('HorizontalScrollView')
        self.assertIsNotNone(scroll)
        scroll.tag='FrameLayout'
        source[QUICK]=ET.tostring(root,encoding='unicode')
        with self.assertRaisesRegex(AssertionError,'AMUI03C_REFUSED'):
            validate(source)

if __name__=='__main__':unittest.main()
