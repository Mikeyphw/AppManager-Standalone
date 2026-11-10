#!/usr/bin/env python3
"""AMUI04D targeted negative mutations, including upstream/Tasker legacy protection."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui04d_final_gate import ROOT,FILES,JAVA,RUNNER,TARGET,FULL,AUDIT,VM,ACT,RECEIVER,validate

class FinalGateContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,p,old,new):
        self.assertNotEqual(old,new)
        self.assertEqual(self.src[p].count(old),1,'stale or ambiguous anchor: '+p)
        src=dict(self.src);src[p]=src[p].replace(old,new,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):validate(src)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_device_class(self):self.reject(JAVA,'class Amui04DFinalAcceptanceInstrumentedTest','class MissingClass')
    def test_installed_package(self):self.reject(JAVA,'getPackageInfo(context.getPackageName(), 0)','getPackageInfo("unknown", 0)')
    def test_uid_identity(self):self.reject(JAVA,'assertEquals(Process.myUid(), info.applicationInfo.uid)','assertEquals(0, info.applicationInfo.uid)')
    def test_package_parser(self):
        old='PackageChangeReceiver.packagesFromPackageIntent(intent)'
        self.assertGreater(self.src[JAVA].count(old),1)
        src=dict(self.src);src[JAVA]=src[JAVA].replace(old,'Collections.emptyList().toArray(new String[0])')
        # All tests using parser must have real parser in source, not a fake.
        src[JAVA]=src[JAVA].replace(old,'Collections.emptyList().toArray(new String[0])')
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):validate(src)
    def test_replacing(self):self.reject(JAVA,'Intent.EXTRA_REPLACING','Intent.EXTRA_DELETED')
    def test_partial(self):self.reject(JAVA,'AppListSyncStatus.success("resume", 60, 2, 1, 9)','AppListSyncStatus.success("resume", 60, 2, 0, 9)')
    def test_failure(self):self.reject(JAVA,'AppListSyncStatus.failure("package-event-failure", "SecurityException")','AppListSyncStatus.success("failure", 0, 0, 0, 0)')
    def test_unmodifiable(self):self.reject(JAVA,'catch (UnsupportedOperationException expected)','catch (Exception expected)')
    def test_cleanup(self):self.reject(JAVA,'model.onCleared();','// no cleanup')
    def test_palette(self):self.reject(JAVA,'AppearanceUtils.getThemedContext(target(), false)','target()')
    def test_no_mutation(self):
        src=dict(self.src);src[JAVA]+='\n// Runtime.getRuntime().exec("pm uninstall...")\n'
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):validate(src)
    def test_runtime_class(self):self.reject(RUNNER,'--class io.github.muntashirakon.AppManager.main.Amui04DFinalAcceptanceInstrumentedTest','--class missing.Test')
    def test_runtime_receipt(self):self.reject(RUNNER,'AMUI04D_HOSTED_FINAL_PASS','AMUI04D_SKIPPED')
    def test_runtime_fail_count(self):
        # Previous phases legitimately contain the same failed==0 expression.
        marker='# AMUI-04D: final read-only identity, package-event, list and semantic-theme acceptance.'
        runner=self.src[RUNNER]
        self.assertEqual(runner.count(marker),1,'AMUI04D phase marker stale/ambiguous')
        earlier,final=runner.split(marker,1)
        old="assert int(receipt.get('failed',1))==0,receipt"
        self.assertEqual(final.count(old),1,'AMUI04D final receipt guard stale/ambiguous')
        src=dict(self.src)
        src[RUNNER]=earlier+marker+final.replace(old,"assert int(receipt.get('failed',1))>=0,receipt",1)
        # Earlier phases still contain valid guards, so only the final-phase
        # source checker can detect this mutation.
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):
            validate(src)
    def test_final_fail_guard_cannot_be_satisfied_by_legacy_phases(self):
        marker='# AMUI-04D: final read-only identity, package-event, list and semantic-theme acceptance.'
        runner=self.src[RUNNER]
        self.assertEqual(runner.count(marker),1)
        earlier,final=runner.split(marker,1)
        old="assert int(receipt.get('failed',1))==0,receipt"
        self.assertEqual(final.count(old),1)
        # Extra identical assertions before the final phase replicate the
        # already-observed AMUI04A/B/C collision on real hosted sources.
        earlier += "\n# synthetic prior-phase receipt\n" + (old+"\n")*3
        src=dict(self.src)
        src[RUNNER]=earlier+marker+final.replace(old,"assert int(receipt.get('failed',1))>=0,receipt",1)
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):
            validate(src)
    def test_runtime_final_receipt_duplicate_refused(self):
        marker='# AMUI-04D: final read-only identity, package-event, list and semantic-theme acceptance.'
        runner=self.src[RUNNER]
        self.assertEqual(runner.count(marker),1)
        old="assert int(receipt.get('failed',1))==0,receipt"
        a,final=runner.split(marker,1)
        self.assertEqual(final.count(old),1)
        src=dict(self.src)
        src[RUNNER]=a+marker+final.replace(old,old+"\n"+old,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):
            validate(src)
    def test_runtime_pass_floor(self):self.reject(RUNNER,"int(receipt.get('passed',0))>=10","int(receipt.get('passed',0))>=0")
    def test_exact_sha(self):self.reject(RUNNER,"receipt['amui04d_commit']=sha","receipt['amui04d_commit']='fake'")
    def test_target(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amui04d_final_gate.py --check','echo skip')
    def test_full(self):self.reject(FULL,'python3 scripts/devtool/check_amui04d_final_gate.py --check','echo skip')
    def test_full_manual(self):self.reject(FULL,'  workflow_dispatch:', '  push:')
    def test_legacy_tasker(self):self.reject(FULL,'  amt06c-fixture:', '  removed-fixture:')
    def test_legacy_35(self):self.reject(FULL,'  device-instrumentation:', '  removed-instrumentation:')
    def test_legacy_36(self):self.reject(FULL,'  amui01-android16:', '  removed-api36:')
    def test_epoch(self):self.reject(VM,'final long filterEpoch = mListEpoch.get();','final long filterEpoch = 0;')
    def test_immutable_epoch(self):self.reject(VM,'if (epoch != mListEpoch.get())','if (false)')
    def test_package_lifecycle_source(self):self.reject(RECEIVER,'if (intent.getBooleanExtra(Intent.EXTRA_REPLACING, false))','if (false)')
    def test_main_refresh(self):self.reject(ACT,'viewModel.refreshApplications("pull")','// skipped pull')
    def test_auditor_api35(self):self.reject(AUDIT,'verify_api(args.api35,35,args.sha)','verify_api(args.api35,36,args.sha)')
    def test_auditor_api36(self):self.reject(AUDIT,'verify_api(args.api36,36,args.sha)','verify_api(args.api36,35,args.sha)')
    def test_auditor_sha(self):self.reject(AUDIT,"require(rows[filename]==h,'PNG SHA-256 mismatch '+folder_name+'/'+filename)","require(True,'PNG SHA-256 mismatch '+folder_name+'/'+filename)")
    def test_auditor_identical_images(self):self.reject(AUDIT,"require(len(digests)==len(cases),'duplicate rendered captures '+folder_name)","require(len(digests)>=1,'duplicate rendered captures '+folder_name)")
    def test_duplicate_runtime_receipt_rejected(self):
        src=dict(self.src);src[RUNNER]+='\n# AMUI04D_HOSTED_FINAL_PASS duplicate\n'
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):validate(src)
    def test_missing_api35_receipt(self):
        old='${{ runner.temp }}/amui04d-api*.json';self.assertEqual(self.src[FULL].count(old),2)
        src=dict(self.src);src[FULL]=src[FULL].replace(old,'removed/path',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):validate(src)
    def test_missing_api36_log(self):
        old='${{ runner.temp }}/amui04d-api*.log';self.assertEqual(self.src[FULL].count(old),2)
        src=dict(self.src);src[FULL]=src[FULL].replace(old,'removed/path',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):validate(src)
    def test_deny_png_crc_bypass(self):
        self.reject(AUDIT,'zlib.crc32(kind+payload)','0')
    def test_deny_png_decode_bypass(self):
        self.reject(AUDIT,'actual=png_geometry(path)','actual=(0,0)')
    def test_deny_lifecycle_removal(self):
        self.reject(AUDIT,"LIFECYCLE=(('amui01-installed.json',5),('amui01-removed.json',1))",'LIFECYCLE=()')
    def test_deny_lifecycle_fixture_identity(self):
        self.reject(AUDIT,"meta.get('disposable_fixture')==FIXTURE", "meta.get('disposable_fixture')!='real private app'")
    def test_deny_apk_digest(self):
        self.reject(AUDIT,"require(sha_rows[0].split('  ',1)[0]==digest,", "require(True,")
    def test_deny_api35_fixture_hash_upload_missing(self):
        old='${{ runner.temp }}/amui01-fixture.sha256'
        self.assertEqual(self.src[FULL].count(old),2)
        src=dict(self.src);src[FULL]=src[FULL].replace(old,'missing-fixture-evidence',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04D_REFUSED'):validate(src)
    def test_deny_boolean_test_count_success(self):
        self.reject(AUDIT,"require(type(x.get(key)) is int,'missing/non-integer '+key+' '+path.name)",
                    "require(True,'missing/non-integer '+key+' '+path.name)")
    def test_no_op_anchor_fails(self):
        with self.assertRaisesRegex(AssertionError,'stale or ambiguous anchor'):
            self.reject(JAVA,'AMUI04D_ABSENT_TEST','')

if __name__=='__main__':unittest.main()
