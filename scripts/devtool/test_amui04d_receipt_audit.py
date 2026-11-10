#!/usr/bin/env python3
"""Negative evidence tests: real PNG CRC/IDAT, exact hosted 35/36 lifecycle receipts."""
import hashlib,json,struct,sys,tempfile,unittest,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from amui04d_receipt_audit import RECEIPTS,LIFECYCLE,PNG_CASES,STAGES,FIXTURE,verify_api,png_geometry,AuditError
SHA='a'*40

def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)

def png(width,height,color):
    ihdr=struct.pack('>IIBBBBB',width,height,8,6,0,0,0)
    row=b'\x00'+bytes([color])*width*4
    compressed=zlib.compress(row*height,9)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',ihdr)+chunk(b'IDAT',compressed)+chunk(b'IEND',b'')

def make_fixture(root,api,sha=SHA):
    root.mkdir(parents=True,exist_ok=True)
    for template,sha_key,api_key,minimum in RECEIPTS:
        name=template.format(api=api)
        (root/name).write_text(json.dumps({'status':'success','returncode':0,'executed':minimum,
            'passed':minimum,'failed':0,sha_key:sha,api_key:api}))
    for name,minimum in LIFECYCLE:
        (root/name).write_text(json.dumps({'status':'passed','returncode':0,
            'executed':minimum,'passed':minimum,'failed':0}))
    apk_digest=hashlib.sha256(b'disposable-fixture-apk').hexdigest()
    (root/'amui01-meta.json').write_text(json.dumps({'commit':sha,'api':api,
        'disposable_fixture':FIXTURE,'stages':STAGES,'fixture_sha256':apk_digest}))
    (root/'amui01-fixture.sha256').write_text(apk_digest+'  scripts/devtool/amt06c_fixture/build/outputs/apk/debug/fixture-debug.apk\n')
    for phase,scenes in PNG_CASES.items():
        folder=root/f'{phase}-screenshots-api{api}';folder.mkdir()
        entries=[]
        for n,(width,height) in scenes.items():
            h=height if height is not None else 400
            data=png(width,h,((sum(map(ord,n+phase))+api)%240)+5)
            path=folder/(n+'.png');path.write_bytes(data)
            entries.append(hashlib.sha256(data).hexdigest()+'  /runner/'+folder.name+'/'+path.name)
        (root/(folder.name+'.sha256')).write_text('\n'.join(entries)+'\n')

class EvidenceContracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='amui04d-evidence-')
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        make_fixture(self.root,35)
    def mutate_json(self,file,field,value):
        p=self.root/file;x=json.loads(p.read_text());x[field]=value;p.write_text(json.dumps(x))
    def reject(self):
        with self.assertRaises((AuditError,ValueError)):verify_api(self.root,35,SHA)
    def test_valid_35(self):
        r=verify_api(self.root,35,SHA)
        self.assertEqual(len(r['receipts']),10)
        self.assertEqual(len(r['pngs']),6)
    def test_valid_36(self):
        x=self.root/'api36';make_fixture(x,36)
        self.assertEqual(verify_api(x,36,SHA)['api'],36)
    def test_wrong_sha(self):
        with self.assertRaises(AuditError):verify_api(self.root,35,'b'*40)
    def test_wrong_api(self):
        with self.assertRaises(AuditError):verify_api(self.root,36,SHA)
    def test_malformed_sha(self):
        with self.assertRaises(AuditError):verify_api(self.root,35,'INVALID')
    def test_missing_final_receipt(self):
        (self.root/'amui04d-api35.json').unlink();self.reject()
    def test_missing_preceding_receipt(self):
        (self.root/'amui04c-api35.json').unlink();self.reject()
    def test_wrong_app_lifecycle_commit(self):
        self.mutate_json('amui01-meta.json','commit','b'*40);self.reject()
    def test_lifecycle_wrong_api(self):
        self.mutate_json('amui01-meta.json','api',36);self.reject()
    def test_lifecycle_wrong_fixture(self):
        self.mutate_json('amui01-meta.json','disposable_fixture','real.private.app');self.reject()
    def test_lifecycle_missing_uninstall(self):
        (self.root/'amui01-removed.json').unlink();self.reject()
    def test_lifecycle_false_uninstall_success(self):
        self.mutate_json('amui01-removed.json','passed',0);self.reject()
    def test_lifecycle_missing_install(self):
        (self.root/'amui01-installed.json').unlink();self.reject()
    def test_lifecycle_sha_mismatch(self):
        (self.root/'amui01-fixture.sha256').write_text('0'*64+'  file.apk\n');self.reject()
    def test_lifecycle_no_replacement(self):
        self.mutate_json('amui01-meta.json','stages',['real_install','real_uninstall']);self.reject()
    def test_boolean_test_count(self):
        self.mutate_json('amui04d-api35.json','passed',True);self.reject()
    def test_test_count_more_than_executed(self):
        self.mutate_json('amui04d-api35.json','passed',100);self.reject()
    def test_missing_png(self):
        (self.root/'amui04b-screenshots-api35'/'rtl.png').unlink();self.reject()
    def test_bad_geometry(self):
        p=self.root/'amui04b-screenshots-api35'/'wide.png';d=bytearray(p.read_bytes());d[16:20]=struct.pack('>I',721);p.write_bytes(d);self.reject()
    def test_png_crc_tamper_even_if_manifest_updated(self):
        p=self.root/'amui04a-screenshots-api35'/'light.png';d=bytearray(p.read_bytes());d[30]^=1;p.write_bytes(d)
        m=self.root/'amui04a-screenshots-api35.sha256';lines=m.read_text().splitlines()
        for i,x in enumerate(lines):
            if x.endswith('light.png'):lines[i]=hashlib.sha256(d).hexdigest()+'  '+x.split('  ',1)[1]
        m.write_text('\n'.join(lines)+'\n');self.reject()
    def test_png_missing_iend_even_if_manifest_updated(self):
        p=self.root/'amui04a-screenshots-api35'/'dark.png';d=p.read_bytes()[:-12];p.write_bytes(d)
        m=self.root/'amui04a-screenshots-api35.sha256';m.write_text(m.read_text().replace(
            next(x.split('  ')[0] for x in m.read_text().splitlines() if x.endswith('dark.png')),
            hashlib.sha256(d).hexdigest()))
        self.reject()
    def test_png_fake_24_byte_header(self):
        p=self.root/'amui04a-screenshots-api35'/'light.png';p.write_bytes(b'\x89PNG\r\n\x1a\n'+b'\x00\x00\x00\rIHDR'+struct.pack('>II',1080,400)+b'X'*2000);self.reject()
    def test_png_invalid_stream_even_if_manifest_updated(self):
        p=self.root/'amui04b-screenshots-api35'/'rtl.png';d=png(720,1280,7)
        self.assertTrue(png_geometry(p))
        # Replace actual compressed data with invalid zlib stream, but recompute the chunk CRC.
        bad=bytearray(d)
        start=8+25+8;bad[start:start+2]=b'xx'
        length=struct.unpack('>I',bad[33:37])[0]
        crcstart=33+8+length
        bad[crcstart:crcstart+4]=struct.pack('>I',zlib.crc32(b'IDAT'+bad[start:start+length])&0xffffffff)
        p.write_bytes(bad)
        m=self.root/'amui04b-screenshots-api35.sha256';lines=m.read_text().splitlines()
        for i,x in enumerate(lines):
            if x.endswith('rtl.png'):lines[i]=hashlib.sha256(bad).hexdigest()+'  '+x.split('  ',1)[1]
        m.write_text('\n'.join(lines)+'\n');self.reject()
    def test_duplicate_png(self):
        f=self.root/'copy'/'amui04a-screenshots-api35';f.mkdir(parents=True)
        (f/'light.png').write_bytes((self.root/'amui04a-screenshots-api35'/'light.png').read_bytes())
        self.reject()
    def test_png_manifest_missing(self):
        (self.root/'amui04b-screenshots-api35.sha256').unlink();self.reject()
    def test_png_manifest_extra(self):
        p=self.root/'amui04b-screenshots-api35.sha256';p.write_text(p.read_text()+'0'*64+'  unknown.png\n');self.reject()
    def test_trailing_png_data(self):
        p=self.root/'amui04b-screenshots-api35'/'rtl.png';p.write_bytes(p.read_bytes()+b'unknown');self.reject()
    def test_missing_test_status(self):
        self.mutate_json('amui04d-api35.json','status','pending');self.reject()
    def test_missing_legacy_receipt(self):
        (self.root/'amui02-appearance-api35.json').unlink();self.reject()
    def test_nonzero_return(self):
        self.mutate_json('amui04d-api35.json','returncode',1);self.reject()
    def test_duplicate_lifecycle_meta(self):
        d=self.root/'duplicate';d.mkdir()
        (d/'amui01-meta.json').write_bytes((self.root/'amui01-meta.json').read_bytes());self.reject()
    def test_bad_json(self):
        (self.root/'amui04d-api35.json').write_text('{')
        with self.assertRaises(ValueError):verify_api(self.root,35,SHA)

if __name__=='__main__':unittest.main()
