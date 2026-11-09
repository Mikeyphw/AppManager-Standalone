#!/usr/bin/env python3
"""AMUI02C: negative contract mutations. Never launches Gradle or emulators."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui02c_bottom_sheet import APP,CAP,TEST,WF,ROOT,FILES,validate

class BottomSheetContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,path,old,new):
        self.assertIn(old,self.src[path])
        bad=dict(self.src);bad[path]=bad[path].replace(old,new,1)
        with self.assertRaises(AssertionError):validate(bad)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_reject_global_system_mode(self):self.reject(APP,'context.getResources().getConfiguration().uiMode','Resources.getSystem().getConfiguration().uiMode')
    def test_reject_dark_mode_selection_lost(self):self.reject(APP,'mapNightModeOnce(context, Prefs.Appearance.getNightMode())','AppCompatDelegate.MODE_NIGHT_NO')
    def test_reject_black_theme_lost(self):self.reject(APP,'applyPureBlackBackground(themedContext, transparent);','// removed')
    def test_reject_global_dialog_mode(self):self.reject(CAP,'UiUtils.isDarkMode(getContext())','UiUtils.isDarkMode()')
    def test_reject_legacy_systembar_style(self):self.reject(CAP,'boolean lightBars = !UiUtils.isDarkMode(getContext());','UiUtils.setSystemBarStyle(window, true);\n                boolean lightBars = false;')
    def test_reject_status_bar_transparency(self):self.reject(CAP,'window.setStatusBarColor(Color.TRANSPARENT);','window.setStatusBarColor(Color.BLACK);')
    def test_reject_navigation_bar_transparency(self):self.reject(CAP,'window.setNavigationBarColor(Color.TRANSPARENT);','window.setNavigationBarColor(Color.BLACK);')
    def test_reject_icon_contrast_status(self):self.reject(CAP,'controller.setAppearanceLightStatusBars(lightBars);','// removed')
    def test_reject_icon_contrast_navigation(self):self.reject(CAP,'controller.setAppearanceLightNavigationBars(lightBars);','// removed')
    def test_reject_existing_blur_removed(self):self.reject(CAP,'window.addFlags(WindowManager.LayoutParams.FLAG_BLUR_BEHIND);','// no blur')
    def test_reject_collapsed_behavior_change(self):self.reject(CAP,'mBehavior.setSkipCollapsed(true);','mBehavior.setSkipCollapsed(false);')
    def test_reject_dark_device_test(self):self.reject(TEST,'darkBottomSheetUsesDialogContextForBarContrast','missingTest')
    def test_reject_light_device_test(self):self.reject(TEST,'lightBottomSheetUsesDialogContextForBarContrast','missingTest')
    def test_reject_preferences_restore(self):self.reject(TEST,'Prefs.Appearance.setNightMode(originalMode);','// lost')
    def test_reject_source_gate_removed(self):self.reject(WF,'python3 -B scripts/devtool/check_amui02c_bottom_sheet.py --check','echo skipped')
    def test_reject_compile_gate_removed(self):self.reject(WF,'Scoped Android resource and Java compile (no emulator)','Scoped Android source only')

if __name__=='__main__':unittest.main()
