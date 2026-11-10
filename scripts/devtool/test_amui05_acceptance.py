#!/usr/bin/env python3
"""Negative mutations for AMUI05. No Gradle, emulator or network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui05_acceptance import ROOT,FILES,TARGET,FULL,ACCEPT,RUNNER,COMPAT,WALL,PHYSICAL,LEDGER,AUDIT,DOC,LAYOUTS,validate

class AcceptanceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text() for p in FILES}
    def reject(self,path,old,new):
        self.assertNotEqual(old,new)
        self.assertEqual(self.src[path].count(old),1,'stale or ambiguous mutation anchor '+path)
        candidate=dict(self.src);candidate[path]=candidate[path].replace(old,new,1)
        with self.assertRaisesRegex(AssertionError,'AMUI05_REFUSED'):validate(candidate)
    def reject_acceptance(self,old,new):
        original=self.src[ACCEPT]
        needle='\n  amui05-acceptance:\n'
        self.assertEqual(original.count(needle),1)
        prefix,part=original.split(needle,1)
        self.assertEqual(part.count(old),1,'stale scoped acceptance mutation')
        updated=dict(self.src);updated[ACCEPT]=prefix+needle+part.replace(old,new,1)
        with self.assertRaisesRegex(AssertionError,'AMUI05_REFUSED'):validate(updated)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_old_api_removed(self):self.reject_acceptance('api: [30, 35, 36]','api: [35, 36]')
    def test_android_16_removed(self):self.reject_acceptance('api: [30, 35, 36]','api: [30, 35]')
    def test_auto_trigger_refused(self):self.reject(ACCEPT,'permissions:','  push:\npermissions:')
    def test_legacy_full_auto_trigger_refused(self):self.reject(FULL,'  workflow_dispatch:','  push:')
    def test_no_targeted_source_contract(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amui05_acceptance.py --check','echo skip')
    def test_no_full_source_contract(self):self.reject(FULL,'python3 scripts/devtool/check_amui05_acceptance.py --check','echo skip')
    def test_no_matrix(self):self.reject_acceptance('fail-fast: false','fail-fast: true')
    def test_missing_artifact_refused(self):self.reject_acceptance('if-no-files-found: error','if-no-files-found: ignore')
    def test_no_pinned_devtool(self):self.reject_acceptance('checkout --detach bee6e0b7e49aaaa0c56f755fd5be434a27c52b6c','checkout --detach main')
    def test_no_kvm_gate(self):self.reject_acceptance('[[ -r /dev/kvm && -w /dev/kvm ]]','true')
    def test_weaken_device_fail_count(self):self.reject(RUNNER,"int(r.get('failed',1))==0","int(r.get('failed',1))>=0")
    def test_weaken_device_skip_count(self):self.reject(RUNNER,"int(r.get('skipped',1))==0","int(r.get('skipped',1))>=0")
    def test_no_wallpaper_real_change(self):self.reject(WALL,'manager.setBitmap(bitmap, null, true, WallpaperManager.FLAG_SYSTEM);','// skip mutation')
    def test_fake_wallpaper_change(self):self.reject(WALL,'assertNotEquals("AMUI05_WALLPAPER_PALETTE_DID_NOT_CHANGE"','assertEquals("AMUI05_WALLPAPER_PALETTE_DID_NOT_CHANGE"')
    def test_dynamic_accent_change_still_required(self):self.reject(WALL,'assertNotEquals("AMUI05_DYNAMIC_ACCENT_DID_NOT_CHANGE"','assertEquals("AMUI05_DYNAMIC_ACCENT_DID_NOT_CHANGE"')
    def test_no_physical_guard(self):self.reject(WALL,'AMUI05_HARD_REFUSAL_PHYSICAL_WALLPAPER_MUTATION','AMUI05_ALLOW_PHYSICAL')
    def test_no_real_device_gate(self):self.reject(PHYSICAL,'I_AUTHORIZE_READ_ONLY_DEVICE_PROBE','UNAUTHORISED')
    def test_no_real_compatibility(self):self.reject(COMPAT,'assertFalse(user.isChecked());','assertTrue(user.isChecked());')
    def test_no_wide_screen_layout(self):
        import xml.etree.ElementTree as ET
        from check_amui05_acceptance import NS
        p=LAYOUTS[0];candidate=dict(self.src)
        root=ET.fromstring(candidate[p]);root.set(NS+'background','@android:color/black')
        candidate[p]=ET.tostring(root,encoding='unicode')
        with self.assertRaisesRegex(AssertionError,'AMUI05_REFUSED'):validate(candidate)
    def test_no_ledger_pending(self):self.reject(LEDGER,"return {'schema':1,'exact_sha':sha,'status':'PENDING',","return {'schema':1,'exact_sha':sha,'status':'PASSED',")
    def test_false_acceptance_claim(self):self.reject(DOC,'NOT_FULL_ROADMAP_ACCEPTANCE','ALL_DONE')
    def test_missing_audit(self):self.reject(AUDIT,'amui05_exact_sha','not_checked')

if __name__=='__main__':unittest.main(verbosity=2)
