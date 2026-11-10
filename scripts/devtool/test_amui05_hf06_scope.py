#!/usr/bin/env python3
"""HF06: guard targeted compile eligibility against real AMUI05 changed-files scopes.

Inspects the actual GitHub Actions grep expression; never substitutes a mocked
compile result for the workflow logic. No Android, Gradle or network needed.
"""
from __future__ import annotations
import re,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/'.github/workflows/amui-targeted-ci.yml'
OLD_HF03_CHANGED=(
 '.github/workflows/devtool-tasker-ci.yml',
 'docs/AMUI05_REMAINING_ACCEPTANCE_MATRIX.md',
 'scripts/devtool/amui05_hf03_launcher.py',
 'scripts/devtool/amui05_hosted_acceptance.sh',
 'scripts/devtool/check_amui05_acceptance.py',
 'scripts/devtool/test_amui05_acceptance.py',
 'scripts/devtool/test_amui05_hf03_recovery.py',
)
REQUIRED=(
 '.github/workflows/devtool-tasker-ci.yml',
 '.github/workflows/amui-targeted-ci.yml',
 'scripts/devtool/amui05_hosted_acceptance.sh',
 'scripts/devtool/amui05_receipt_audit.py',
 'scripts/devtool/amui05_hf03_launcher.py',
 'scripts/devtool/check_amui05_acceptance.py',
 'scripts/devtool/test_amui05_hf03_recovery.py',
 'scripts/devtool/amt03_hosted_instrumentation.sh',
 'scripts/devtool/check_amt03_contract.py',
 'app/src/androidTest/java/io/github/muntashirakon/AppManager/main/Amui04DFinalAcceptanceInstrumentedTest.java',
 'app/src/main/java/io/github/muntashirakon/AppManager/main/MainViewModel.java',
 'app/build.gradle',
 'build.gradle',
 'settings.gradle',
 'gradle/libs.versions.toml',
 'libcore/ui/src/main/res/layout/example.xml',
 'libcore/foo/src/main/java/Example.java',
)
NOT_COMPILE=(
 'README.md','docs/AMUI05_REMAINING_ACCEPTANCE_MATRIX.md',
 '.github/ISSUE_TEMPLATE/bug.yml', 'assets/theme-preview.png',
)
OLD_SCOPE=r'^(app/src/(main|androidTest)/|libcore/ui/src/main/|libcore/[^/]+/src/main/|build.gradle|settings.gradle|gradle/|gradle.properties)'


def extract_scope(source:str)->re.Pattern[str]:
    def require(ok:bool,msg:str):
        if not ok:raise AssertionError('AMUI05_HF06_SCOPE_REFUSED: '+msg)
    marker='      - name: Detect compile-relevant changes\n'
    require(source.count(marker)==1,'one exact compile detection step required')
    block=source.split(marker,1)[1].split('      - name:',1)[0]
    require('id: scope\n' in block,'scoped output ID missing')
    match=re.findall(r'''if grep -Eq '([^'\n]+)' "\$RUNNER_TEMP/amui-changed-files\.txt"; then''',block)
    require(len(match)==1,'one bounded grep classifier required')
    pattern=match[0]
    require(pattern.startswith('^(') and pattern.endswith(')'), 'path classifier must stay anchored')
    require('git diff --name-only "$from" "$to" > "$RUNNER_TEMP/amui-changed-files.txt"' in block,
            'classify the exact changed-file list, not branch names or guesses')
    require('elif [[ "$EVENT" == push ]]' in block and 'to="$CURRENT"' in block,
            'push must compare before/current commits')
    require("echo 'compile=true' >> \"$GITHUB_OUTPUT\"" in block and
            "echo 'compile=false' >> \"$GITHUB_OUTPUT\"" in block,
            'compile result must be published explicitly')
    require('  android-compile:\n' in source and
            "if: needs.source-contract.outputs.compile == 'true'" in source and
            'needs: [source-contract]' in source,
            'Android compile must depend on successful source gate and classified paths')
    require('python3 -B -m unittest discover -s scripts/devtool -p \'test_*.py\' -v' in source,
            'scope regression must be covered by full targeted source test discovery')
    rx=re.compile(pattern)
    for path in REQUIRED:
        require(bool(rx.search(path)),'compile omitted for '+path)
    for path in NOT_COMPILE:
        require(not rx.search(path),'unrelated path unexpectedly triggers hosted compile '+path)
    require(any(rx.search(path) for path in OLD_HF03_CHANGED),
            'regression: HF03 source-only job skipped all Android compilation')
    return rx

class HostedCompileScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=FILE.read_text(encoding='utf-8')
        cls.pattern=extract_scope(cls.source)

    def reject(self,changed:str)->None:
        with self.assertRaisesRegex(AssertionError,'AMUI05_HF06_SCOPE_REFUSED'):
            extract_scope(changed)

    def test_hf03_actual_changed_files_must_trigger_compile(self):
        self.assertTrue(any(self.pattern.search(p) for p in OLD_HF03_CHANGED))
        self.assertFalse(all(self.pattern.search(p) for p in OLD_HF03_CHANGED),
                         'docs-only changes should remain source-only')

    def test_hf03_previous_classifier_reproduces_skip(self):
        previous=re.compile(OLD_SCOPE)
        self.assertFalse(any(previous.search(p) for p in OLD_HF03_CHANGED))

    def test_workflow_and_script_paths_trigger(self):
        for path in REQUIRED:
            with self.subTest(path=path):self.assertRegex(path,self.pattern)

    def test_docs_not_forced_to_compile(self):
        for path in NOT_COMPILE:
            with self.subTest(path=path):self.assertNotRegex(path,self.pattern)

    def test_old_classifier_would_be_refused(self):
        line=re.search(r"if grep -Eq '([^'\n]+)'",self.source).group(1)
        self.reject(self.source.replace(line,OLD_SCOPE,1))

    def test_removed_workflow_scope_refused(self):
        self.reject(self.source.replace(r'\.github/workflows/',r'\.github/issues/',1))

    def test_removed_devtool_scope_refused(self):
        self.reject(self.source.replace('scripts/devtool/(amui|amt|check_amui|test_amui|check_amt|test_amt)',
                                        'scripts/devtool/(amui02|amt99)',1))

    def test_removed_app_test_scope_refused(self):
        self.reject(self.source.replace('app/src/(main|androidTest)/','app/src/main/',1))

    def test_compile_job_cannot_be_disabled(self):
        self.reject(self.source.replace("if: needs.source-contract.outputs.compile == 'true'",
                                        "if: false",1))

    def test_change_classifier_cannot_fake_true(self):
        self.reject(self.source.replace('if grep -Eq ', 'if true || grep -Eq ',1))

    def test_change_diff_must_be_exact(self):
        self.reject(self.source.replace('git diff --name-only "$from" "$to"',
                                        'git diff --name-only HEAD^ HEAD~0',1))

    def test_only_one_detector(self):
        needle='      - name: Detect compile-relevant changes\n'
        self.reject(self.source.replace(needle,needle+needle,1))

    def test_targeted_source_suite_cannot_be_disabled(self):
        self.reject(self.source.replace("python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v",'echo skipped',1))

    def test_real_posix_grep_matches(self):
        # Prove Python parsing agrees with GNU grep's -E behavior for these
        # supported regexp constructs, not merely a mocked classifier.
        try:
            import shutil
            if not shutil.which('grep'):self.skipTest('grep unavailable')
            pattern=self.pattern.pattern
            for path in REQUIRED+NOT_COMPILE:
                r=subprocess.run(['grep','-Eq',pattern],input=path+'\n',text=True,capture_output=True)
                self.assertIn(r.returncode,(0,1),r.stderr)
                self.assertEqual(r.returncode==0,bool(self.pattern.search(path)),path)
        except FileNotFoundError:self.skipTest('grep unavailable')

if __name__=='__main__':unittest.main()
