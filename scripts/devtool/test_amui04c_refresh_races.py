#!/usr/bin/env python3
"""AMUI04C negative source mutations prove epoch propagation and lifecycle receipts."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui04c_refresh_races import ROOT,FILES,VM,STATUS,JAVA,RUNNER,TARGET,FULL,validate

class AMUI04CLifecycleContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,p,old,new):
        self.assertNotEqual(old,new,'no-op mutation')
        self.assertEqual(self.src[p].count(old),1,'stale/ambiguous AMUI04C mutation '+p)
        changed=dict(self.src);changed[p]=changed[p].replace(old,new,1)
        with self.assertRaisesRegex(AssertionError,'AMUI04C_REFUSED'):validate(changed)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_missing_capture(self):self.reject(VM,'final long filterEpoch = mListEpoch.get();','long filterEpoch = 0L;')
    def test_capture_at_publish_is_forbidden(self):self.reject(VM,'final long epoch = filterEpoch;','final long epoch = mListEpoch.get();')
    def test_capture_must_be_before_filter(self):self.reject(VM,'final long filterEpoch = mListEpoch.get();','final long filterEpoch = mListEpoch.get()+0;')
    def test_no_epoch_parameter(self):self.reject(VM,'private void publishVisibleItems(@NonNull List<ApplicationItem> items, long filterEpoch)','private void publishVisibleItems(@NonNull List<ApplicationItem> items)')
    def test_query_signature_retained(self):self.reject(VM,'private void filterItemsByQuery(@NonNull List<ApplicationItem> applicationItems, long filterEpoch)','private void filterItemsByQuery(@NonNull List<ApplicationItem> applicationItems)')
    def test_old_query_early_return(self):self.reject(VM,'            publishVisibleItems(filteredApplicationItems, filterEpoch);\n            return;','            publishVisibleItems(filteredApplicationItems, mListEpoch.get());\n            return;')
    def test_old_query_terminal(self):self.reject(VM,'        publishVisibleItems(filteredApplicationItems, filterEpoch);\n    }','        publishVisibleItems(filteredApplicationItems, mListEpoch.get());\n    }')
    def test_old_flags_unfiltered(self):self.reject(VM,'publishVisibleItems(candidateApplicationItems, filterEpoch);','publishVisibleItems(candidateApplicationItems, mListEpoch.get());')
    def test_old_flags_filtered(self):self.reject(VM,'                    publishVisibleItems(filteredApplicationItems, filterEpoch);\n                }','                    publishVisibleItems(filteredApplicationItems, mListEpoch.get());\n                }')
    def test_query_candidate_propagation(self):self.reject(VM,'filterItemsByQuery(candidateApplicationItems, filterEpoch);','filterItemsByQuery(candidateApplicationItems, mListEpoch.get());')
    def test_query_filtered_propagation(self):self.reject(VM,'filterItemsByQuery(filteredApplicationItems, filterEpoch);','filterItemsByQuery(filteredApplicationItems, mListEpoch.get());')
    def test_epoch_invalidation_retained(self):self.reject(VM,'mListEpoch.incrementAndGet();','// removed invalidation')
    def test_generation_rejection_retained(self):self.reject(VM,'if (epoch != mListEpoch.get()) {','if (false) {')
    def test_refresh_status_gate_retained(self):self.reject(VM,'statusRequestId == mRefreshRequestId.get()','true /* wrong status */')
    def test_single_executor_retained(self):self.reject(VM,'mListExecutor = Executors.newSingleThreadExecutor()','mListExecutor = Executors.newCachedThreadPool()')
    def test_partial_status_kept(self):self.reject(STATUS,'this.partial = skippedUsers > 0;','this.partial = false;')
    def test_android_real_method(self):self.reject(JAVA,'MainViewModel.class.getDeclaredMethod("publishVisibleItems", List.class, long.class)','MainViewModel.class.getDeclaredMethod("unknown", List.class, long.class)')
    def test_android_observer(self):self.reject(JAVA,'live.observeForever(observer)','// skip live observer')
    def test_android_must_not_fake_success(self):self.reject(JAVA,'assertNull("old refresh completion marked new refresh successful"','assertNotNull("old refresh completion marked new refresh successful"')
    def test_cleanup_model(self):self.reject(JAVA,'model.onCleared();','// leak receiver')
    def test_seven_android_tests(self):
        changed=dict(self.src);changed[JAVA]=changed[JAVA].replace('    @Test\n    public void failureDoesNotInventSuccessOrLoseReason()', '    public void failureDoesNotInventSuccessOrLoseReason()',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04C_REFUSED'):validate(changed)
    def test_no_device_race_class(self):self.reject(RUNNER,'--class io.github.muntashirakon.AppManager.main.Amui04CLifecycleRaceInstrumentedTest','--class wrong.package.Test')
    def test_no_strict_pass_count(self):self.reject(RUNNER,"int(receipt.get('passed',0)) >= 7","int(receipt.get('passed',0)) >= 0")
    def test_no_exact_sha(self):self.reject(RUNNER,"receipt['amui04c_commit']=sha", "receipt['amui04c_commit']='UNKNOWN'")
    def test_no_qualified_runner(self):self.reject(RUNNER,'AMUI04C_HOSTED_RACE_PASS','AMUI04C_SKIPPED')
    def test_no_targeted_checker(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amui04c_refresh_races.py --check','echo skip')
    def test_no_full_checker(self):self.reject(FULL,'python3 scripts/devtool/check_amui04c_refresh_races.py --check','echo skip')
    def test_manual_to_push_refused(self):self.reject(FULL,'  workflow_dispatch:', '  push:')
    def test_api35_receipt_missing(self):
        needle='${{ runner.temp }}/amui04c-api*.json';self.assertEqual(self.src[FULL].count(needle),2)
        changed=dict(self.src);changed[FULL]=changed[FULL].replace(needle,'removed/receipt',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04C_REFUSED'):validate(changed)
    def test_api36_log_missing(self):
        needle='${{ runner.temp }}/amui04c-api*.log';self.assertEqual(self.src[FULL].count(needle),2)
        changed=dict(self.src);changed[FULL]=changed[FULL].replace(needle,'removed/log',1)
        with self.assertRaisesRegex(AssertionError,'AMUI04C_REFUSED'):validate(changed)
    def test_stale_mutation_anchor_fails_closed(self):
        with self.assertRaisesRegex(AssertionError,'stale/ambiguous AMUI04C mutation'):
            self.reject(VM,'AMUI04C_OBSOLETE_NEVER_EXISTED','')
    def test_duplicate_runner_gate_fails_closed(self):
        changed=dict(self.src);changed[RUNNER]+= '\n# AMUI04C_HOSTED_RACE_PASS duplicate\n'
        with self.assertRaisesRegex(AssertionError,'AMUI04C_REFUSED'):validate(changed)

if __name__=='__main__':unittest.main()
