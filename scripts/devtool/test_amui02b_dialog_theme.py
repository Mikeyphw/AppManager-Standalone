#!/usr/bin/env python3
"""Fail-closed source mutation tests for dialog theme context and widget parity."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui02b_dialog_theme import FILES,ROOT,APP,TEST,BASE,DIALOGS,validate
class DialogParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,path,old,new):
        self.assertIn(old,self.src[path]);bad=dict(self.src);bad[path]=bad[path].replace(old,new,1)
        with self.assertRaises(AssertionError):validate(bad)
    def test_source_positive(self):self.assertTrue(validate(self.src))
    def widget_reject(self,old,new):
        source=self.src[APP];left,right=source.split('public static Context getThemedWidgetContext(',1)
        self.assertIn(old,right)
        bad=dict(self.src)
        bad[APP]=left+'public static Context getThemedWidgetContext('+right.replace(old,new,1)
        with self.assertRaises(AssertionError):validate(bad)
    def test_widget_override_not_missing(self):self.widget_reject('newCtx.applyOverrideConfiguration(createOverrideConfiguration(context, options));','// skip widget config')
    def test_widget_night_pref_not_lost(self):self.widget_reject('options.nightMode = Prefs.Appearance.getNightMode();','options.nightMode = null;')
    def test_widget_dynamic_palette_not_lost(self):
        # Widget path contains a second DynamicColors occurrence; target the block.
        before=self.src[APP]; bad=dict(self.src)
        left,right=before.split('public static Context getThemedWidgetContext(',1)
        bad[APP]=left+'public static Context getThemedWidgetContext('+right.replace('DynamicColors.wrapContextIfAvailable(newCtx);','newCtx;',1)
        with self.assertRaises(AssertionError):validate(bad)
    def test_widget_black_preference_not_lost(self):
        before=self.src[APP];bad=dict(self.src)
        left,right=before.split('public static Context getThemedWidgetContext(',1)
        bad[APP]=left+'public static Context getThemedWidgetContext('+right.replace('applyPureBlackBackground(themedContext, transparent);','// no black',1)
        with self.assertRaises(AssertionError):validate(bad)
    def test_single_choice_no_raw_inflation(self):self.reject(BASE+DIALOGS[0],'context = mBuilder.getContext();','// raw activity context')
    def test_multi_choice_no_raw_inflation(self):self.reject(BASE+DIALOGS[1],'context = mBuilder.getContext();','// raw activity context')
    def test_items_no_raw_inflation(self):self.reject(BASE+DIALOGS[2],'context = mBuilder.getContext();','// raw activity context')
    def test_text_input_no_raw_inflation(self):self.reject(BASE+DIALOGS[3],'mContext = mBuilder.getContext();','mContext = context;')
    def test_dropdown_no_raw_inflation(self):self.reject(BASE+DIALOGS[4],'View view = View.inflate(mBuilder.getContext(),','View view = View.inflate(activity,')
    def test_dropdown_adapters_not_raw(self):self.reject(BASE+DIALOGS[4],'new AnyFilterArrayAdapter<>(mBuilder.getContext(),','new AnyFilterArrayAdapter<>(mActivity,')
    def test_targeted_source_gate_not_removed(self):self.reject('.github/workflows/amui-targeted-ci.yml','python3 -B scripts/devtool/check_amui02b_dialog_theme.py --check','echo skip')
    def test_device_dark_widget_test_retained(self):self.reject(TEST,'widgetContextDarkPureBlackLeavesRaisedSurfaceTonal','widget_dark_deleted')
    def test_device_light_widget_test_retained(self):self.reject(TEST,'widgetContextLightIsNotBlackWhenPreferenceRemainsEnabled','widget_light_deleted')
    def test_restore_night_pref(self):self.reject(TEST,'Prefs.Appearance.setNightMode(originalMode);','// loss of restore')
if __name__=='__main__':unittest.main()
