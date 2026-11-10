#!/usr/bin/env python3
"""Exact-SHA fail-closed hosted API30/35/36 receipt verification. Never certifies physical UX."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path

def audit(folders,sha):
    if not re.fullmatch(r'[a-f0-9]{40}',sha):raise ValueError('AMUI05_SHA_INVALID')
    for api,root in folders.items():
        expected={f'amui05-compatibility-api{api}.json':(7,'compatibility')}
        if api>=35:expected[f'amui05-wallpaper-api{api}.json']=(2,'wallpaper')
        for filename,(floor,kind) in expected.items():
            p=root/filename
            if not p.is_file() or p.is_symlink():raise ValueError('AMUI05_MISSING_RECEIPT '+filename)
            r=json.loads(p.read_text(encoding='utf-8'))
            if r.get('amui05_exact_sha')!=sha or r.get('amui05_api')!=api or r.get('amui05_class')!=kind:
                raise ValueError('AMUI05_WRONG_IDENTITY '+filename)
            if r.get('status') not in ('passed','success') or r.get('returncode')!=0 or r.get('cleanup_status')!='passed':
                raise ValueError('AMUI05_UNSUCCESSFUL_REAL_DEVICE '+filename)
            if r.get('device_serial')!='emulator-5554' or r.get('target_package')!='io.github.muntashirakon.AppManager.debug':
                raise ValueError('AMUI05_WRONG_APP_OR_EMULATOR '+filename)
            if not all(isinstance(r.get(k),int) and not isinstance(r.get(k),bool) for k in ('executed','passed','failed','skipped')):
                raise ValueError('AMUI05_INVALID_COUNTER_TYPES '+filename)
            if r['executed']<floor or r['passed']!=r['executed'] or r['failed']!=0 or r['skipped']!=0:
                raise ValueError('AMUI05_MISSING_PASS_OR_TESTS '+filename)
        scope=root/f'amui05-scope-api{api}.json'
        if not scope.is_file():raise ValueError('AMUI05_SCOPE_ABSENT '+str(api))
        s=json.loads(scope.read_text())
        if (s.get('api')!=api or s.get('sha')!=sha or s.get('hardware')!='disposable-emulator-only'
                or s.get('compatibility_tests')!=7 or s.get('wallpaper_tests')!=(2 if api>=35 else 0)
                or s.get('whole_app_visual_parity')!='NOT_CLAIMED'
                or s.get('physical_arm64')!='NOT_CLAIMED' or s.get('real_work_profile')!='NOT_CLAIMED'):
            raise ValueError('AMUI05_SCOPE_FORGED '+str(api))
    return True

def main():
    a=argparse.ArgumentParser();a.add_argument('--api30',required=True,type=Path)
    a.add_argument('--api35',required=True,type=Path);a.add_argument('--api36',required=True,type=Path)
    a.add_argument('--sha',required=True);args=a.parse_args()
    audit({30:args.api30,35:args.api35,36:args.api36},args.sha)
    print('AMUI05_HOSTED_30_35_36_EXACT_SHA_RECEIPTS_PASS',args.sha)
    print('AMUI05_NOT_FULL_ROADMAP_ACCEPTANCE_PHYSICAL_AND_24_SCREENS_PENDING')
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print('AMUI05_AUDIT_REFUSED',e,file=sys.stderr);raise SystemExit(1)
