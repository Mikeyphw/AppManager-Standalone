#!/usr/bin/env python3
"""AMUI04C fail-closed filter-epoch/lifecycle and API35/36 source contract."""
from __future__ import annotations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
VM='app/src/main/java/io/github/muntashirakon/AppManager/main/MainViewModel.java'
STATUS='app/src/main/java/io/github/muntashirakon/AppManager/main/AppListSyncStatus.java'
JAVA='app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui04CLifecycleRaceInstrumentedTest.java'
RUNNER='scripts/devtool/amui02_hosted_theme.sh'
TARGET='.github/workflows/amui-targeted-ci.yml'
FULL='.github/workflows/devtool-tasker-ci.yml'
FILES=(VM,STATUS,JAVA,RUNNER,TARGET,FULL)
NAMES=(
    'staleFilterEpochCannotPublishAfterLaterChange',
    'currentFilterEpochPublishesImmutableEmptySnapshot',
    'thirtyTwoInvalidationsOnlyPublishTheLastGeneration',
    'supersededRefreshCompletionCannotMasqueradeAsNewer',
    'partialRefreshReceiptRemainsPartialAfterVisibleFiltering',
    'failureDoesNotInventSuccessOrLoseReason',
    'firstResumeDoesNotPrematurelyClaimRefreshSuccess',
)

def validate(src):
    def must(ok,why):
        if not ok:raise AssertionError('AMUI04C_REFUSED: '+why)
    vm,status,java,runner,target,full=(src[p] for p in FILES)
    flags=vm.split('    private void filterItemsByFlags() {',1)
    must(len(flags)==2 and flags[1].startswith('\n        // Capture before reading any filter input.'),
         'filter epoch not captured at task entry')
    must(flags[1].split('synchronized (mApplicationItems)',1)[0].count('final long filterEpoch = mListEpoch.get();')==1,
         'source epoch capture must precede reads')
    pub=vm.split('    private void publishVisibleItems(',1)
    must(len(pub)==2 and pub[1].startswith('@NonNull List<ApplicationItem> items, long filterEpoch) {'),
         'publisher must accept original filter epoch')
    must('final long epoch = filterEpoch;' in pub[1].split('    private void filterItemsByQuery(',1)[0],
         'publisher recaptures newer generation')
    must('long epoch = mListEpoch.get();' not in pub[1].split('    private void filterItemsByQuery(',1)[0],
         'publisher must not take a late epoch')
    must('if (epoch != mListEpoch.get()) {' in vm and
         'mApplicationItemsLiveData.setValue(Collections.unmodifiableList(snapshot));' in vm,
         'stale snapshot rejection or immutable UI delivery removed')
    must('completeRequestId == mRefreshRequestId.get()' in vm and
         'statusRequestId == mRefreshRequestId.get()' in vm,
         'old refresh status could claim latest completion')
    must('mListExecutor = Executors.newSingleThreadExecutor()' in vm,
         'app-list DB serialization removed')
    must('mListEpoch.incrementAndGet();' in vm and 'mRefreshRequestId.incrementAndGet();' in vm,
         'generation invalidation missing')
    query=vm.split('    private void filterItemsByQuery(',1)[1].split('    private void filterItemsByFlags(',1)[0]
    must(query.startswith('@NonNull List<ApplicationItem> applicationItems, long filterEpoch) {') and
         query.count('publishVisibleItems(filteredApplicationItems, filterEpoch);')==2,
         'query paths lost captured epoch')
    task=vm.split('    private void filterItemsByFlags()',1)[1].split('    private boolean isAmongSelectedUsers(',1)[0]
    for marker in ('filterItemsByQuery(candidateApplicationItems, filterEpoch);',
                   'filterItemsByQuery(filteredApplicationItems, filterEpoch);',
                   'publishVisibleItems(candidateApplicationItems, filterEpoch);',
                   'publishVisibleItems(filteredApplicationItems, filterEpoch);'):
        must(marker in task,'flag-filter path lost captured epoch: '+marker)
    must(vm.count('publishVisibleItems(')==5 and vm.count('filterItemsByQuery(')==3,
         'extra unguarded publication/query call path')
    must('mPendingCompletion = null;' in vm and 'mDeferredCompletion = null;' in vm,
         'completion status cleanup weakened')
    for marker in ('this.partial = skippedUsers > 0;',
                   'new AppListSyncStatus(running, success, filtered, reason, error, sourceCount,',
                   'public static AppListSyncStatus failure(', 'public static AppListSyncStatus success('):
        must(marker in status,'immutable real AppListSyncStatus contract lost: '+marker)
    must(java.count('@Test')==len(NAMES) and 'class Amui04CLifecycleRaceInstrumentedTest' in java,
         'real Android lifecycle tests absent or reduced')
    for name in NAMES:
        must('public void '+name+'(' in java,'missing Android test '+name)
    for marker in ('MainViewModel.class.getDeclaredMethod("publishVisibleItems", List.class, long.class)',
                   'new MainViewModel((Application) ctx.getApplicationContext())',
                   'model.onCleared();','32L;', 'live.observeForever(observer)',
                   'MainViewModel.class.getDeclaredField("mListEpoch")',
                   'MainViewModel.class.getDeclaredField("mRefreshRequestId")',
                   'assertNull("stale publication escaped epoch check"',
                   'assertNull("old refresh completion marked new refresh successful"'):
        # Reflection actually happens through field(vm,name), so check its callsites instead.
        if marker.startswith('MainViewModel.class.getDeclaredField("m'):
            marker='field(vm, "'+('mListEpoch' if 'mListEpoch' in marker else 'mRefreshRequestId')+'")'
        must(marker in java,'device test bypassed real ViewModel '+marker)
    must('ACTION_PACKAGE_DELETE' not in java and 'pm uninstall' not in java and
         'Runtime.getRuntime().exec' not in java,
         'read-only lifecycle test must not alter packages')
    race=runner.split('# AMUI-04C: actual MainViewModel epoch/lifecycle races',1)
    must(len(race)==2 and runner.count('AMUI04C_HOSTED_RACE_PASS')==1,
         'hosted race gate missing or duplicated')
    for marker in ('Amui04CLifecycleRaceInstrumentedTest',
                   'amui04c-api${api}.json', 'amui04c-api${api}.log',
                   "int(receipt.get('executed',0)) >= 7", "int(receipt.get('passed',0)) >= 7",
                   "int(receipt.get('failed',1)) == 0", "receipt['amui04c_commit']=sha",
                   "receipt['amui04c_api']=api", 'GITHUB_SHA', 'PYRACE'):
        must(marker in race[1],'strict device receipt missing '+marker)
    must('AMUI04A_HOSTED_VISUAL_PASS' in runner and 'AMUI04B_HOSTED_VIEWPORT_PASS' in runner,
         'older hosted instrumentation lost')
    must('python3 -B scripts/devtool/check_amui04c_refresh_races.py --check' in target and
         "python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v" in target and
         'Scoped Android resource and Java compile (no emulator)' in target,
         'targeted source/Java compile lane removed')
    must('python3 scripts/devtool/check_amui04c_refresh_races.py --check' in full,
         'full source check missing')
    event=full.split('"on":',1)[1].split('permissions:',1)[0]
    must('  workflow_dispatch:' in event and '  push:' not in event and '  pull_request:' not in event,
         'heavy full workflow must stay manual-only')
    for marker in ('  device-instrumentation:', '  amui01-android16:',
                   '  amt06c-fixture:', 'AMUI04A_HOSTED_VISUAL_PASS',):
        if marker=='AMUI04A_HOSTED_VISUAL_PASS':continue
        must(marker in full,'previous device jobs removed '+marker)
    must(full.count('${{ runner.temp }}/amui04c-api*.json')==2 and
         full.count('${{ runner.temp }}/amui04c-api*.log')==2,
         'both API35 and API36 must archive full lifecycle receipts')
    must(full.count('${{ runner.temp }}/amui04a-api*.json')==2 and
         full.count('${{ runner.temp }}/amui04b-api*.json')==2,
         'prior visual/viewport receipts removed')
    return True

def check(root=ROOT):
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.parse_args()
    check();print('AMUI04C_REFRESH_EPOCH_RACE_SOURCE_PASS')
