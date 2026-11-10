#!/usr/bin/env python3
"""Read-only physical ARM64 qualification inventory. No root, screenshot, package listing or mutations."""
from __future__ import annotations
import argparse,json,re,subprocess,hashlib,os
from pathlib import Path

ACK='I_AUTHORIZE_READ_ONLY_DEVICE_PROBE'
PACKAGE='io.github.muntashirakon.AppManager.debug'

def adb(serial,*argv):
    p=subprocess.run(['adb','-s',serial,*argv],capture_output=True,text=True,timeout=20)
    if p.returncode:raise RuntimeError('AMUI05_ADB_REFUSED: '+str(argv)+' rc='+str(p.returncode))
    return p.stdout.strip()

def inspect(serial,sha):
    devices=[ln.split() for ln in adb(serial,'get-state').splitlines() if ln.strip()]
    if devices!=[['device']]:raise RuntimeError('AMUI05_ADB_DEVICE_NOT_READY')
    api=adb(serial,'shell','getprop','ro.build.version.sdk')
    abi=adb(serial,'shell','getprop','ro.product.cpu.abi')
    hardware=adb(serial,'shell','getprop','ro.hardware')
    if api!='36' or abi not in ('arm64-v8a','armeabi-v7a'):
        raise RuntimeError('AMUI05_EXPECTED_PHYSICAL_API36_ARM_DEVICE')
    if hardware in ('ranchu','goldfish'):
        raise RuntimeError('AMUI05_EMULATOR_NOT_PHYSICAL')
    users=adb(serial,'shell','pm','list','users')
    # Store only anonymized integer counts, never usernames, apps, serials or user IDs.
    count=sum(1 for ln in users.splitlines() if re.search(r'UserInfo\{\d+:',ln))
    managed=sum(1 for ln in users.splitlines() if 'MANAGED' in ln.upper() or 'MANAGED_PROFILE' in ln.upper())
    path=adb(serial,'shell','pm','path',PACKAGE)
    installed=any(ln.startswith('package:') for ln in path.splitlines())
    return {'schema':1,'source_sha':sha,'api':int(api),'abi':abi,'hardware_checked':'physical-not-emulator',
            'app_debug_installed':installed,'android_user_count':count,'managed_profile_count':managed,
            'background_package_delivery':'UNVERIFIED','process_recreation':'UNVERIFIED',
            'all_24_activity_screen_parity':'UNVERIFIED','physical_device_qualified':False,
            'status':'INSPECTION_ONLY','privacy':'no serial, package list, screenshot, usernames or user IDs recorded'}

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--serial',required=True)
    a.add_argument('--sha',required=True)
    a.add_argument('--ack',required=True)
    a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    if args.ack!=ACK:raise RuntimeError('AMUI05_EXPLICIT_READ_ONLY_CONSENT_REQUIRED')
    if not re.fullmatch(r'[0-9a-f]{40}',args.sha):raise RuntimeError('AMUI05_SOURCE_SHA_INVALID')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}',args.serial):raise RuntimeError('AMUI05_SERIAL_INVALID')
    result=inspect(args.serial,args.sha)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.is_symlink():raise RuntimeError('AMUI05_REFUSE_SYMLINK_OUTPUT')
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('AMUI05_PHYSICAL_READ_ONLY_INSPECTION_COMPLETE_NOT_QUALIFIED',args.output)
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
        print('AMUI05_PHYSICAL_REFUSED',e)
        raise SystemExit(1)
