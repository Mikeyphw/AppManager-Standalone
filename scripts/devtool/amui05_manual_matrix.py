#!/usr/bin/env python3
"""Honest full-app/manual UX acceptance ledger; approvals require real screenshot evidence.

This tool NEVER invents device or screen pass receipts. The user records reviews.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,struct,zlib
from pathlib import Path

SCREENS=('app_details','app_usage','apps_profile','auth_management','batch_ops_results',
 'code_editor','debloater','finder','fm','help','interceptor','labs','logcat','main',
 'one_click_ops','op_history','profiles','running_apps','settings','settings_dual_pane',
 'shared_prefs','sys_config','term','virus_total')
THEMES=('light','dark','dark_pure_black')
SPECIAL=('WALLPAPER_LIVE_RECOLOR','PROCESS_RECREATION','BACKGROUND_INSTALL_RECEPTION',
 'WORK_PROFILE_DENIAL','WORK_PROFILE_PRESENT','PHYSICAL_ARM64','EDGE_TO_EDGE_STATUS_NAV',
 'DIALOG_BOTTOM_SHEET_PARITY','SEARCH_SORT_SCROLL_SELECTION','NONDESTRUCTIVE_TASKER_PARITY')

def template(sha):
    return {'schema':1,'exact_sha':sha,'status':'PENDING',
     'entries':[{'case':f'{s}/{t}','status':'PENDING','screenshot_path':None,
                 'screenshot_sha256':None,'approved_by':None,'notes':None}
                for s in SCREENS for t in THEMES]+[
       {'case':s,'status':'PENDING','screenshot_path':None,'screenshot_sha256':None,
        'approved_by':None,'notes':None} for s in SPECIAL]}

def validate_png(path):
    # Fail closed on forged PNG signature, CRC/truncation and compressed scanline data.
    raw=path.read_bytes()
    if not raw.startswith(b'\x89PNG\r\n\x1a\n') or not 1024<len(raw)<20*1024*1024:
        raise ValueError('AMUI05_INVALID_PNG_SIZE_OR_SIGNATURE')
    offset=8;ids=[];pixels=None;data=[];finished=False
    while offset<len(raw):
        if offset+12>len(raw):raise ValueError('AMUI05_TRUNCATED_PNG_CHUNK')
        length=struct.unpack('>I',raw[offset:offset+4])[0]
        kind=raw[offset+4:offset+8];end=offset+12+length
        if length>20*1024*1024 or end>len(raw):raise ValueError('AMUI05_PNG_OVERSIZED_CHUNK')
        payload=raw[offset+8:offset+8+length]
        crc=struct.unpack('>I',raw[offset+8+length:end])[0]
        if zlib.crc32(kind+payload)&0xffffffff!=crc:raise ValueError('AMUI05_PNG_CHUNK_CRC_MISMATCH')
        ids.append(kind)
        if kind==b'IHDR':
            if pixels is not None or length!=13:raise ValueError('AMUI05_PNG_BAD_IHDR')
            w,h,depth,kind_color,comp,fil,inter=struct.unpack('>IIBBBBB',payload)
            if not (100<=w<=4096 and 100<=h<=8192 and depth==8 and kind_color in (2,6)
                    and comp==fil==inter==0):raise ValueError('AMUI05_INVALID_SCREENSHOT_GEOMETRY')
            pixels=(w,h,3 if kind_color==2 else 4)
        if kind==b'IDAT':data.append(payload)
        if kind==b'IEND':
            if length!=0 or end!=len(raw):raise ValueError('AMUI05_TRAILING_OR_MALFORMED_PNG')
            finished=True;break
        offset=end
    if not (ids[0]==b'IHDR' and finished and data and pixels):raise ValueError('AMUI05_INCOMPLETE_PNG')
    w,h,ch=pixels;max_length=(w*ch+1)*h
    decompressor=zlib.decompressobj()
    unpacked=decompressor.decompress(b''.join(data),max_length+1)
    if len(unpacked)!=max_length or not decompressor.eof or decompressor.unconsumed_tail:
        raise ValueError('AMUI05_INVALID_PNG_IMAGE_DATA')
    for i in range(h):
        if unpacked[i*(w*ch+1)]>4:raise ValueError('AMUI05_INVALID_PNG_FILTER')
    return hashlib.sha256(raw).hexdigest()

def verify(blob,base,sha):
    if blob.get('schema')!=1 or blob.get('exact_sha')!=sha:raise ValueError('AMUI05_WRONG_SCHEMA_OR_EXACT_SHA')
    expected=template(sha)['entries'];real=blob.get('entries',[])
    if not isinstance(real,list) or [x.get('case') for x in real]!=[x['case'] for x in expected]:
        raise ValueError('AMUI05_MISSING_DUPLICATE_OR_REORDERED_CASE')
    pending=[];seen_digests=set()
    for e in real:
        if e.get('status')!='PASS':pending.append(e['case']);continue
        if not isinstance(e.get('approved_by'),str) or len(e['approved_by'].strip())<2:
            raise ValueError('AMUI05_ANONYMOUS_OR_FAKE_APPROVAL '+e['case'])
        rel=e.get('screenshot_path');digest=e.get('screenshot_sha256')
        if not rel or not re.fullmatch(r'[0-9a-f]{64}',str(digest)):
            raise ValueError('AMUI05_MISSING_SCREENSHOT_PROOF '+e['case'])
        p=(base/rel).resolve()
        if not p.is_relative_to(base.resolve()) or not p.is_file() or p.is_symlink():
            raise ValueError('AMUI05_UNSAFE_OR_MISSING_SCREENSHOT '+e['case'])
        computed=validate_png(p)
        if computed!=digest:raise ValueError('AMUI05_SCREENSHOT_TAMPERED '+e['case'])
        if computed in seen_digests:raise ValueError('AMUI05_REUSED_SCREENSHOT '+e['case'])
        seen_digests.add(computed)
    if pending:raise ValueError('AMUI05_MANUAL_ACCEPTANCE_PENDING '+str(len(pending))+' case(s) including '+', '.join(pending[:4]))
    return True

def main():
    a=argparse.ArgumentParser(description=__doc__)
    x=a.add_mutually_exclusive_group(required=True);x.add_argument('--init',action='store_true');x.add_argument('--verify',action='store_true')
    a.add_argument('--file',required=True,type=Path);a.add_argument('--sha',required=True)
    args=a.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}',args.sha):raise ValueError('AMUI05_BAD_SHA')
    if args.init:
        if args.file.exists():raise ValueError('AMUI05_REFUSE_OVERWRITE_MANUAL_RECEIPTS')
        args.file.parent.mkdir(parents=True,exist_ok=True)
        args.file.write_text(json.dumps(template(args.sha),indent=2)+'\n')
        print('AMUI05_MANUAL_MATRIX_CREATED_PENDING',len(template(args.sha)['entries']))
    else:
        verify(json.loads(args.file.read_text()),args.file.parent,args.sha)
        print('AMUI05_MANUAL_MATRIX_APPROVED_WITH_SCREENSHOT_EVIDENCE')

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError) as e:
        print('AMUI05_MANUAL_REFUSED',e,file=sys.stderr);raise SystemExit(1)
