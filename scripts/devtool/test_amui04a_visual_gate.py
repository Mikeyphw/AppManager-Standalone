#!/usr/bin/env python3
"""AMUI-04A isolated negative source mutations; stale-anchor tests fail closed."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui04a_visual_gate import ROOT,FILES,JAVA,RUNNER,TARGET,FULL,validate

class AMUI04AVisualGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,path,old,new):
        self.assertNotEqual(old,new,'no-op mutation')
        self.assertEqual(self.src[path].count(old),1,'stale or ambiguous anchor '+path)
        changed=dict(self.src);changed[path]=changed[path].replace(old,new,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04A_REFUSED'):
            validate(changed)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_stale_test_anchor_refused(self):
        with self.assertRaisesRegex(AssertionError,'stale or ambiguous anchor'):
            self.reject(RUNNER,'AMUI04A_OBSOLETE_LINE','')
    def test_restore_preferences(self):self.reject(JAVA,'Prefs.Appearance.setPureBlackTheme(originalBlack);','')
    def test_no_background_forced_black(self):self.reject(JAVA,'assertEquals(Color.BLACK, color(context, android.R.attr.colorBackground));','assertEquals(Color.WHITE, color(context, android.R.attr.colorBackground));')
    def test_material_accent_guard(self):self.reject(JAVA,'Color.BLACK, color(context, androidx.appcompat.R.attr.colorPrimary)','Color.WHITE, color(context, androidx.appcompat.R.attr.colorPrimary)')
    def test_source_is_ui_thread_render(self):self.reject(JAVA,'runOnMainSync(', 'unrelatedThread(')
    def test_real_png_generation(self):self.reject(JAVA,'bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)','')
    def test_quick_filter_fixture(self):self.reject(JAVA,'View chips = LayoutInflater.from(context).inflate(R.layout.amui03c_quick_filters','View chips = LayoutInflater.from(context).inflate(R.layout.obsolete_quick_filters')
    def test_no_dark_fixture(self):self.reject(JAVA,'snapshot("dark", true, false)','snapshot("dark", true, true)')
    def test_no_pure_black_fixture(self):self.reject(JAVA,'snapshot("pure-black", true, true)','snapshot("pure-black", false, true)')
    def test_no_device_class(self):self.reject(RUNNER,'--class io.github.muntashirakon.AppManager.utils.appearance.Amui04AVisualInstrumentedTest','--class wrong.package.Test')
    def test_no_receipt_guard(self):self.reject(RUNNER,'AMUI04A_HOSTED_VISUAL_PASS','AMUI04A_BYPASSED')
    def test_no_screen_capture(self):self.reject(RUNNER,'AMUI04A_EXPECT_SCREENSHOT_COUNT=3','AMUI04A_EXPECT_SCREENSHOT_COUNT=0')
    def test_no_adb_pull(self):self.reject(RUNNER,'adb pull "$device_dir/${name}.png" "$shot_dir/${name}.png"', 'echo skip-amui04a-pull')
    def test_duplicate_palette_images_rejected(self):self.reject(RUNNER,"assert len(hashes)==3, 'AMUI04A_DUPLICATE_PALETTE_SCREENSHOTS'","assert len(hashes)>=1, 'AMUI04A_DUPLICATE_PALETTE_SCREENSHOTS'")
    def test_duplicate_amui04a_hash_guard_is_refused(self):
        marker="assert len(hashes)==3, 'AMUI04A_DUPLICATE_PALETTE_SCREENSHOTS'"
        self.assertEqual(self.src[RUNNER].count(marker),1,'AMUI04A hash guard no longer unique')
        changed=dict(self.src);changed[RUNNER]=changed[RUNNER].replace(marker,marker+'\n'+marker,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04A_REFUSED'):validate(changed)
    def test_duplicate_amui04a_pull_is_refused(self):
        marker='adb pull "$device_dir/${name}.png" "$shot_dir/${name}.png"'
        self.assertEqual(self.src[RUNNER].count(marker),1,'AMUI04A pull no longer unique')
        changed=dict(self.src);changed[RUNNER]=changed[RUNNER].replace(marker,marker+'\n'+marker,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04A_REFUSED'):validate(changed)
    def test_amui04b_guard_cannot_replace_amui04a_guard(self):
        self.reject(RUNNER,"assert len(hashes)==3, 'AMUI04A_DUPLICATE_PALETTE_SCREENSHOTS'","assert len(hashes)==3,'AMUI04B_DUPLICATE_VIEWPORT_IMAGES'")
    def test_no_targeted_source_gate(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amui04a_visual_gate.py --check','echo bypass')
    def test_no_full_source_gate(self):self.reject(FULL,'python3 scripts/devtool/check_amui04a_visual_gate.py --check','echo bypass')
    def test_full_changed_to_push(self):self.reject(FULL,'  workflow_dispatch:', '  push:')
    def test_missing_api35_receipt(self):
        # Duplicated identical paths: removing one must be rejected.
        self.assertEqual(self.src[FULL].count('${{ runner.temp }}/amui04a-api*.json'),2)
        changed=dict(self.src);changed[FULL]=changed[FULL].replace('${{ runner.temp }}/amui04a-api*.json','removed/receipt',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04A_REFUSED'):validate(changed)
    def test_missing_api36_png(self):
        self.assertEqual(self.src[FULL].count('${{ runner.temp }}/amui04a-screenshots-api*/**'),2)
        changed=dict(self.src);changed[FULL]=changed[FULL].replace('${{ runner.temp }}/amui04a-screenshots-api*/**','removed/screenshots',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04A_REFUSED'):validate(changed)
if __name__=='__main__':unittest.main()
