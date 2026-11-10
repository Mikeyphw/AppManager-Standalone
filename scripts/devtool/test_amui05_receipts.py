#!/usr/bin/env python3
"""Hostile API receipt and human-approval evidence replay. No device or network."""
from __future__ import annotations
import copy,hashlib,json,sys,tempfile,unittest,zlib,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from amui05_receipt_audit import audit
from amui05_manual_matrix import template,verify
SHA='a'*40

def mk(api,kind,floor):
    return dict(amui05_exact_sha=SHA,amui05_api=api,amui05_class=kind,
      status='passed',returncode=0,cleanup_status='passed',device_serial='emulator-5554',
      target_package='io.github.muntashirakon.AppManager.debug',executed=floor,
      passed=floor,failed=0,skipped=0)
class DeviceEvidenceMutations(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.dirs={api:self.root/str(api) for api in (30,35,36)}
        for api,d in self.dirs.items():
            d.mkdir()
            r=dict(api=api,sha=SHA,hardware='disposable-emulator-only',
                   physical_arm64='NOT_CLAIMED',real_work_profile='NOT_CLAIMED',
                   compatibility_tests=7,wallpaper_tests=2 if api>=35 else 0,whole_app_visual_parity='NOT_CLAIMED')
            (d/f'amui05-scope-api{api}.json').write_text(json.dumps(r))
            for kind,floor in [('compatibility',7)]+([('wallpaper',2)] if api>=35 else []):
                (d/f'amui05-{kind}-api{api}.json').write_text(json.dumps(mk(api,kind,floor)))
    def rewrite(self,api,kind,field,value):
        p=self.dirs[api]/f'amui05-{kind}-api{api}.json';r=json.loads(p.read_text());r[field]=value;p.write_text(json.dumps(r))
    def check(self):return audit(self.dirs,SHA)
    def test_clean(self):self.assertTrue(self.check())
    def test_missing_android_11(self):
        (self.dirs[30]/'amui05-compatibility-api30.json').unlink()
        with self.assertRaises(ValueError):self.check()
    def test_wrong_commit(self):
        self.rewrite(35,'wallpaper','amui05_exact_sha','b'*40)
        with self.assertRaises(ValueError):self.check()
    def test_false_completion(self):
        self.rewrite(35,'wallpaper','status','failed')
        with self.assertRaises(ValueError):self.check()
    def test_skipped_not_pass(self):
        self.rewrite(36,'compatibility','skipped',1)
        with self.assertRaises(ValueError):self.check()
    def test_missing_test(self):
        self.rewrite(36,'wallpaper','executed',1)
        with self.assertRaises(ValueError):self.check()
    def test_false_zero_test(self):
        self.rewrite(30,'compatibility','passed',0)
        with self.assertRaises(ValueError):self.check()
    def test_wrong_target_package(self):
        self.rewrite(35,'compatibility','target_package','another.app')
        with self.assertRaises(ValueError):self.check()
    def test_wrong_emulator_identity(self):
        self.rewrite(35,'wallpaper','device_serial','phone')
        with self.assertRaises(ValueError):self.check()
    def test_scope_false_device_claim(self):
        p=self.dirs[36]/'amui05-scope-api36.json';r=json.loads(p.read_text());r['physical_arm64']='PASSED';p.write_text(json.dumps(r))
        with self.assertRaises(ValueError):self.check()
    def test_wrong_scope_test_floor(self):
        p=self.dirs[36]/'amui05-scope-api36.json';r=json.loads(p.read_text());r['wallpaper_tests']=0;p.write_text(json.dumps(r))
        with self.assertRaises(ValueError):self.check()
    def test_fake_all_screen_parity(self):
        p=self.dirs[35]/'amui05-scope-api35.json';r=json.loads(p.read_text());r['whole_app_visual_parity']='PASS';p.write_text(json.dumps(r))
        with self.assertRaises(ValueError):self.check()
    def test_missing_scope(self):
        (self.dirs[35]/'amui05-scope-api35.json').unlink()
        with self.assertRaises(ValueError):self.check()
    def test_bool_pass_count(self):
        self.rewrite(30,'compatibility','passed',True)
        with self.assertRaises(ValueError):self.check()
class ManualLedgerMutations(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.original=template(SHA)
    def test_initial_82_pending(self):
        self.assertEqual(len(self.original['entries']),82)
        with self.assertRaisesRegex(ValueError,'PENDING'):verify(self.original,self.root,SHA)
    @staticmethod
    def png_for_case(index):
        w=h=100
        red=(index*73)%256;green=(index*31)%256;blue=(index*11)%256
        row=b'\x00'+bytes((red,green,blue))*w
        def chunk(tag,data):
            return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
        ihdr=struct.pack('>IIBBBBB',w,h,8,2,0,0,0)
        return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',ihdr)+chunk(b'tEXt',b'description\x00'+b'proof-fixture'*115)+chunk(b'IDAT',zlib.compress(row*h))+chunk(b'IEND',b'')
    def test_all_82_genuine_unique_png_receipts_can_pass(self):
        b=copy.deepcopy(self.original)
        for i,item in enumerate(b['entries']):
            img=self.png_for_case(i);name=f'shot{i}.png';(self.root/name).write_bytes(img)
            item.update(status='PASS',approved_by='manual reviewer',screenshot_path=name,
                        screenshot_sha256=hashlib.sha256(img).hexdigest())
        self.assertTrue(verify(b,self.root,SHA))
        b['entries'][1]['screenshot_path']=b['entries'][0]['screenshot_path']
        b['entries'][1]['screenshot_sha256']=b['entries'][0]['screenshot_sha256']
        with self.assertRaisesRegex(ValueError,'REUSED_SCREENSHOT'):
            verify(b,self.root,SHA)
    def test_no_approved_without_image(self):
        b=copy.deepcopy(self.original)
        for item in b['entries']:
            item.update(status='PASS',approved_by='human',screenshot_path='missing.png',screenshot_sha256='0'*64)
        with self.assertRaises(ValueError):verify(b,self.root,SHA)
    def test_no_wrong_sha(self):
        with self.assertRaisesRegex(ValueError,'SHA'):verify(self.original,self.root,'b'*40)
    def test_no_duplicate(self):
        b=copy.deepcopy(self.original);b['entries'].append(b['entries'][0])
        with self.assertRaises(ValueError):verify(b,self.root,SHA)
    def test_no_traversal(self):
        p=self.root/'visual.png';p.write_bytes(b'\x89PNG\r\n\x1a\n'+b'a'*1100)
        b=copy.deepcopy(self.original);b['entries'][0].update(status='PASS',approved_by='human',screenshot_path='../out.png',screenshot_sha256='a'*64)
        with self.assertRaises(ValueError):verify(b,self.root,SHA)
    def test_no_approval_without_person(self):
        p=self.root/'visual.png';p.write_bytes(b'\x89PNG\r\n\x1a\n'+b'a'*1100)
        b=copy.deepcopy(self.original);b['entries'][0].update(status='PASS',approved_by='',screenshot_path='visual.png',screenshot_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        with self.assertRaises(ValueError):verify(b,self.root,SHA)
if __name__=='__main__':unittest.main(verbosity=2)
