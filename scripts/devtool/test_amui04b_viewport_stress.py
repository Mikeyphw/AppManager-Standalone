#!/usr/bin/env python3
"""AMUI-04B fail-closed mutation coverage; no Java/Gradle on Termux."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui04b_viewport_stress import ROOT,FILES,JAVA,RUNNER,TARGET,FULL,VIEWMODEL,validate

class AMUI04BStressContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,path,old,new):
        self.assertNotEqual(old,new,'no-op mutation')
        self.assertEqual(self.src[path].count(old),1,'stale or ambiguous source anchor '+path)
        changed=dict(self.src);changed[path]=changed[path].replace(old,new,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04B_REFUSED'):validate(changed)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_stale_anchor_refusal(self):
        with self.assertRaisesRegex(AssertionError,'stale or ambiguous'):
            self.reject(JAVA,'AMUI04B_OBSOLETE_TEST', '')
    def test_noop_anchor_refusal(self):
        with self.assertRaisesRegex(AssertionError,'no-op'):
            self.reject(JAVA,'LARGE_LIST_SIZE = 600','LARGE_LIST_SIZE = 600')
    def test_device_six_tests(self):self.reject(JAVA,'@Test\n    public void captureNarrowWideAndRtlViewportEvidence()', 'public void captureNarrowWideAndRtlViewportEvidence()')
    def test_virtualization_guard(self):self.reject(JAVA,'list.getChildCount() < 100','list.getChildCount() < LARGE_LIST_SIZE + 1')
    def test_stable_ids(self):self.reject(JAVA,'setHasStableIds(true);','setHasStableIds(false);')
    def test_no_large_list(self):self.reject(JAVA,'LARGE_LIST_SIZE = 600','LARGE_LIST_SIZE = 10')
    def test_no_visible_recycling(self):self.reject(JAVA,'getChildAdapterPosition(row)','getChildLayoutPosition(row)')
    def test_no_rebind_state_reset(self):self.reject(JAVA,'holder.card.setChecked((position % 2) == 0);','')
    def test_no_resize_span(self):self.reject(JAVA,'Math.max(1, width / 640)','1')
    def test_no_chips(self):self.reject(JAVA,'quickChipsRemainInteractiveAfterWidthAndRtlChanges','removedChipTest')
    def test_no_rtl(self):self.reject(JAVA,'snapshot("rtl", 720, 1280, true)','snapshot("rtl", 720, 1280, false)')
    def test_no_narrow_shot(self):self.reject(JAVA,'snapshot("narrow", 720, 1280, false)','snapshot("narrow", 240, 1280, false)')
    def test_no_wide_shot(self):self.reject(JAVA,'snapshot("wide", 1920, 1200, false)','')
    def test_no_ui_main_thread(self):
        changed=dict(self.src)
        changed[JAVA]=changed[JAVA].replace('runOnMainSync(', 'wrongThread(')
        self.assertNotEqual(changed[JAVA],self.src[JAVA])
        with self.assertRaisesRegex(AssertionError,'AMUI04B_REFUSED'):validate(changed)
    def test_no_rtl_scene_label(self):self.reject(JAVA,'"RTL viewport fixture"','"Narrow viewport fixture"')
    def test_no_png(self):self.reject(JAVA,'bitmap.compress(Bitmap.CompressFormat.PNG, 100, writer)','false')
    def test_no_receipt(self):self.reject(RUNNER,'AMUI04B_HOSTED_VIEWPORT_PASS','AMUI04B_BYPASSED')
    def test_no_android_class(self):self.reject(RUNNER,'--class io.github.muntashirakon.AppManager.main.Amui04BViewportStressInstrumentedTest','--class wrong.pkg.MockTest')
    def test_no_png_pull(self):self.reject(RUNNER,'AMUI04B_EXPECT_SCREENSHOTS=3','AMUI04B_EXPECT_SCREENSHOTS=0')
    def test_no_unique_hash(self):self.reject(RUNNER,"assert len(hashes)==3,'AMUI04B_DUPLICATE_VIEWPORT_IMAGES'","assert len(hashes)>=1,'AMUI04B_DUPLICATE_VIEWPORT_IMAGES'")
    def test_duplicate_amui04b_hash_guard_refused(self):
        marker="assert len(hashes)==3,'AMUI04B_DUPLICATE_VIEWPORT_IMAGES'"
        self.assertEqual(self.src[RUNNER].count(marker),1,'AMUI04B unique guard drifted')
        changed=dict(self.src)
        changed[RUNNER]=changed[RUNNER].replace(marker,marker+'\n'+marker,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04B_REFUSED'):
            validate(changed)
    def test_no_source_contract(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amui04b_viewport_stress.py --check','echo skipped')
    def test_no_full_source_contract(self):self.reject(FULL,'python3 scripts/devtool/check_amui04b_viewport_stress.py --check','echo skipped')
    def test_no_vm_epoch(self):self.reject(VIEWMODEL,'if (epoch != mListEpoch.get())','if (false)')
    def test_no_vm_serialization(self):self.reject(VIEWMODEL,'Executors.newSingleThreadExecutor()','Executors.newCachedThreadPool()')
    def test_no_full_manual_gate(self):self.reject(FULL,'  workflow_dispatch:', '  push:')
    def test_no_api35_receipt(self):
        token='${{ runner.temp }}/amui04b-api*.json'
        self.assertEqual(self.src[FULL].count(token),2)
        changed=dict(self.src);changed[FULL]=changed[FULL].replace(token,'removed/receipt',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04B_REFUSED'):validate(changed)
    def test_no_api36_png(self):
        token='${{ runner.temp }}/amui04b-screenshots-api*/**'
        self.assertEqual(self.src[FULL].count(token),2)
        changed=dict(self.src);changed[FULL]=changed[FULL].replace(token,'removed/screenshots',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04B_REFUSED'):validate(changed)
if __name__=='__main__':unittest.main()
