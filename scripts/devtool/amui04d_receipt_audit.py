#!/usr/bin/env python3
"""AMUI-04D HF01: fail-closed exact-SHA Android 35/36 *real* artifact acceptance.

This confirms hosted evidence, not proof of whole-application UX parity, wallpaper
mutation, real work profiles, or physical devices. No network/adb inside auditor.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct,sys,zlib
from pathlib import Path

class AuditError(RuntimeError): pass

RECEIPTS=(
    ('amui02-appearance-api{api}.json','amui02_commit','amui02_api',4),
    ('amui03c-ui-api{api}.json','amui03c_commit','amui03c_api',3),
    ('amui04a-api{api}.json','amui04a_commit','amui04a_api',5),
    ('amui04b-api{api}.json','amui04b_commit','amui04b_api',6),
    ('amui04c-api{api}.json','amui04c_commit','amui04c_api',7),
    ('amui04d-api{api}.json','amui04d_commit','amui04d_api',10),
)
LIFECYCLE=(('amui01-installed.json',5),('amui01-removed.json',1))
PNG_CASES={
    'amui04a':{'light':(1080,None),'dark':(1080,None),'pure-black':(1080,None)},
    'amui04b':{'narrow':(720,1280),'wide':(1920,1200),'rtl':(720,1280)},
}
FIXTURE='dev.mikeyphw.amt06c.fixture'
STAGES=['real_install','signed_replacement','authoritative_reconcile',
        'real_uninstall','reconcile_removed']

def require(value,why):
    if not value:raise AuditError('AMUI04D_EVIDENCE_REFUSED: '+why)

def single(root,filename):
    results=list(root.rglob(filename))
    require(len(results)==1,'missing/duplicated '+filename+' count='+str(len(results)))
    p=results[0]
    require(p.is_file() and not p.is_symlink(),'unsafe file '+filename)
    require(p.stat().st_size<=25*1024*1024,'oversized file '+filename)
    return p

def receipt_ok(path,floor):
    x=json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(x,dict),'malformed receipt '+path.name)
    require(x.get('status') in ('success','passed') and x.get('returncode')==0,
            'failed device execution '+path.name)
    # Avoid coercing floats, booleans, strings, or negative numbers into success.
    for key in ('executed','passed','failed'):
        require(type(x.get(key)) is int,'missing/non-integer '+key+' '+path.name)
    require(x['executed']>=floor and x['passed']>=floor and x['failed']==0 and
            x['passed']<=x['executed'], 'insufficient test totals '+path.name)
    return x

def png_geometry(path):
    data=path.read_bytes()
    require(1024<len(data)<=25*1024*1024,'empty/oversized PNG '+path.name)
    require(data.startswith(b'\x89PNG\r\n\x1a\n'),'PNG signature '+path.name)
    pos=8;ihdr=None;idat=[];ended=False
    while pos<len(data):
        require(pos+12<=len(data),'truncated chunk '+path.name)
        length=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8]
        pos+=8
        require(length<=25*1024*1024 and pos+length+4<=len(data),
                'invalid chunk bounds '+path.name)
        payload=data[pos:pos+length]
        checksum=struct.unpack('>I',data[pos+length:pos+length+4])[0]
        require((zlib.crc32(kind+payload)&0xffffffff)==checksum,
                'PNG CRC mismatch '+path.name)
        pos+=length+4
        if ihdr is None:
            require(kind==b'IHDR' and length==13,'missing first IHDR '+path.name)
            ihdr=struct.unpack('>IIBBBBB',payload)
        elif kind==b'IDAT':idat.append(payload)
        elif kind==b'IEND':
            require(length==0 and pos==len(data),'invalid IEND/trailing bytes '+path.name)
            ended=True;break
    require(ended and idat,'PNG IDAT/IEND absent '+path.name)
    width,height,depth,color,compression,filtering,interlace=ihdr
    require(0<width<=4096 and 0<height<=4096 and depth==8 and
            color in (0,2,4,6) and compression==0 and filtering==0 and interlace==0,
            'unsupported PNG geometry/format '+path.name)
    components={0:1,2:3,4:2,6:4}[color]
    rowlen=1+width*components
    require(height*rowlen<=80*1024*1024,'decoded size limit '+path.name)
    try:
        inflater=zlib.decompressobj()
        max_size=height*rowlen
        uncompressed=inflater.decompress(b''.join(idat),max_size+1)
        require(inflater.eof and not inflater.unconsumed_tail and not inflater.unused_data,
                'truncated/extra PNG compressed bytes '+path.name)
    except zlib.error as e:raise AuditError('AMUI04D_EVIDENCE_REFUSED: bad PNG compressed stream '+path.name) from e
    require(len(uncompressed)==height*rowlen,'decoded row count '+path.name)
    require(all(uncompressed[i*rowlen]<=4 for i in range(height)),
            'invalid PNG scanline filter '+path.name)
    return width,height

def verify_api(root,api,sha):
    source=Path(root)
    require(not source.is_symlink(),'evidence root symlink refused')
    root=source.resolve()
    require(api in (35,36),'unsupported API')
    require(re.fullmatch(r'[0-9a-f]{40}',sha) is not None,'invalid commit SHA')
    require(root.is_dir() and not root.is_symlink(),'missing evidence directory')
    checked=[]
    for template,sha_key,api_key,floor in RECEIPTS:
        filename=template.format(api=api)
        x=receipt_ok(single(root,filename),floor)
        require(x.get(sha_key)==sha and type(x.get(api_key)) is int and x[api_key]==api,
                'wrong exact SHA/API '+filename)
        checked.append(filename)
    # Real disposable install, replacement, authoritative refresh and uninstall
    # were run in AMUI-01; do not infer them from success of other UI classes.
    for filename,floor in LIFECYCLE:
        receipt_ok(single(root,filename),floor)
        checked.append(filename)
    meta=json.loads(single(root,'amui01-meta.json').read_text(encoding='utf-8'))
    require(isinstance(meta,dict) and meta.get('commit')==sha and
            type(meta.get('api')) is int and meta.get('api')==api and
            meta.get('disposable_fixture')==FIXTURE and meta.get('stages')==STAGES,
            'disposable APK lifecycle identity/stages/API/SHA mismatch')
    digest=meta.get('fixture_sha256')
    require(isinstance(digest,str) and re.fullmatch(r'[0-9a-f]{64}',digest),
            'invalid disposable APK SHA256')
    sha_rows=single(root,'amui01-fixture.sha256').read_text(encoding='utf-8').splitlines()
    require(len(sha_rows)==1 and re.fullmatch(r'[0-9a-f]{64}  [^\r\n]+\.apk',sha_rows[0]) is not None,
            'invalid APK digest manifest')
    require(sha_rows[0].split('  ',1)[0]==digest,
            'disposable APK digest mismatch')
    checked.extend(('amui01-meta.json','amui01-fixture.sha256'))

    images=[]
    for phase,cases in PNG_CASES.items():
        folder_name=f'{phase}-screenshots-api{api}'
        lines=single(root,f'{folder_name}.sha256').read_text(encoding='utf-8').splitlines()
        rows={}
        for entry in lines:
            pieces=entry.split('  ',1)
            require(len(pieces)==2 and re.fullmatch(r'[0-9a-f]{64}',pieces[0]),
                    'malformed PNG digest manifest '+folder_name)
            rel=Path(pieces[1]);require(rel.parent.name==folder_name and '..' not in rel.parts,
                    'wrong manifest directory '+folder_name)
            require(rel.name not in rows,'duplicate screenshot manifest row '+rel.name)
            rows[rel.name]=pieces[0]
        require(set(rows)=={k+'.png' for k in cases},'PNG manifest inventory '+folder_name)
        digests=set()
        for name,dimensions in cases.items():
            filename=name+'.png'
            candidates=[p for p in root.rglob(filename) if p.parent.name==folder_name]
            require(len(candidates)==1,'missing/duplicated PNG '+folder_name+'/'+filename)
            path=candidates[0]
            require(path.is_file() and not path.is_symlink(),'unsafe PNG '+folder_name+'/'+filename)
            actual=png_geometry(path)
            expected_width,expected_height=dimensions
            require(actual[0]==expected_width and
                    (100<=actual[1]<=3200 if expected_height is None else actual[1]==expected_height),
                    'PNG viewport dimensions wrong '+folder_name+'/'+filename)
            h=hashlib.sha256(path.read_bytes()).hexdigest()
            require(rows[filename]==h,'PNG SHA-256 mismatch '+folder_name+'/'+filename)
            images.append(folder_name+'/'+filename);digests.add(h)
        require(len(digests)==len(cases),'duplicate rendered captures '+folder_name)
    return {'api':api,'commit':sha,'receipts':checked,'pngs':images}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--api35',required=True,type=Path)
    ap.add_argument('--api36',required=True,type=Path)
    ap.add_argument('--sha',required=True)
    ap.add_argument('--run-id',required=True,type=int)
    args=ap.parse_args()
    require(args.run_id>0,'invalid run ID')
    results=[verify_api(args.api35,35,args.sha),verify_api(args.api36,36,args.sha)]
    print('AMUI04D_API35_API36_LIFECYCLE_AND_PNG_EVIDENCE_PASS',args.run_id,args.sha,
          'receipts=18 manifests=6 pngs=12')
    return {'schema':2,'run_id':args.run_id,'commit':args.sha,'results':results}

if __name__=='__main__':
    try:main()
    except (AuditError,OSError,ValueError,KeyError,TypeError,zlib.error,json.JSONDecodeError) as e:
        print('AMUI04D_EVIDENCE_REFUSED',e,file=sys.stderr)
        raise SystemExit(1)
