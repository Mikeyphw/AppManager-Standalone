#!/usr/bin/env python3
"""Current signing and hosted source-contract regression, no Gradle or credentials."""
from pathlib import Path
import json
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    'app/build.gradle', '.github/workflows/devtool-tasker-ci.yml',
    '.github/workflows/appmanager-signed-apks.yml',
    '.github/workflows/codeql.yml', 'scripts/devtool/ci_signing.sh',
    '.github/workflows/amui-targeted-ci.yml',
    '.github/workflows/tests.yml', '.github/workflows/lint.yml',
    'config/delivery-required-ci.json',
)

def inspect(root=ROOT):
    errors=[]
    try:
        gradle, ci, signed, codeql, script, targeted, tests, lint, policy_text = [(root/p).read_text() for p in SOURCES]
    except OSError as e:
        return ['missing source: '+str(e)]
    guards = {
      'app/build.gradle': (gradle, ['AM_SIGNING_VARIANT','AM_SIGNING_KEYSTORE',
          'ciSigningVariant == \'release\'', 'ciSigningVariant == \'debug\'',
          'Unsigned release packaging refused', 'signingConfigs.ciRelease', 'signingConfigs.ciDebug']),
      'devtool-tasker-ci.yml': (ci, ['workflow_dispatch:', 'environment: debug-signing',
          'bash scripts/devtool/ci_signing.sh prepare',
          'bash scripts/devtool/ci_signing.sh verify app/build/outputs/apk/debug',
          'Upload verified signed debug APKs', 'if: success()']),
      'appmanager-signed-apks.yml': (signed, ['workflow_dispatch:',
          "github.event_name == 'workflow_dispatch'", 'environment: ${{ inputs.variant',
          "release-signing", "debug-signing", "bash scripts/devtool/ci_signing.sh prepare",
          'bash scripts/devtool/ci_signing.sh verify', 'if: success()',
          'AM_RELEASE_KEYSTORE_B64: ${{ secrets.AM_RELEASE_KEYSTORE_B64 }}']),
      'codeql.yml': (codeql, [':app:compileDebugJavaWithJavac']),
      'ci_signing.sh': (script, ['set -Eeuo pipefail','base64 --decode',
          'keytool -list -v', 'apksigner', '--print-certs',
          'SIGNING_REFUSED', 'AM_SIGNING_CERT_SHA256', 'SIGNING_ACCEPTED'])
    }
    expected_head = "${{ github.event.pull_request.head.sha || github.sha }}"
    for name, body in (
        ('amui-targeted-ci.yml', targeted),
        ('tests.yml', tests), ('lint.yml', lint), ('codeql.yml', codeql),
    ):
        if 'ref: ' + expected_head not in body or 'pull_request:' not in body:
            errors.append(name + ': missing PR-triggered exact HEAD checkout')
        if 'run: test \"$(git rev-parse HEAD)\" = \"' + expected_head + '\"' not in body:
            errors.append(name + ': missing exact HEAD verification')
    if '    if: github.event_name != \'pull_request\'' in targeted:
        errors.append('targeted same-repository PR checks must not be skipped')
    for name, body in (('tests.yml', tests), ('lint.yml', lint), ('codeql.yml', codeql)):
        pr_spec = body.split('  pull_request:',1)[-1].split('\njobs:',1)[0]
        if 'feature/tasker-automation' not in pr_spec:
            errors.append(name+': PR base feature/tasker-automation missing')
    try:
        policy=json.loads(policy_text)
    except ValueError as e:
        errors.append('required-CI policy invalid JSON: '+str(e));policy={}
    if policy != {
        'schema_version': 1,
        'repository': 'Mikeyphw/AppManager-Standalone',
        'base_branch': 'feature/tasker-automation',
        'event': 'pull_request',
        'release_qualification': 'separate',
        'required_workflows': [
            {'name':'AppManager Targeted CI (development)', 'workflow_id':412582857},
            {'name':'Tests', 'workflow_id':412143726},
            {'name':'Lint', 'workflow_id':412143719},
            {'name':'CodeQL', 'workflow_id':412143715},
        ],
    }:
        errors.append('required-CI policy names, GitHub workflow IDs, base or qualification drifted')
    if '  pull_request:' in ci.split('"on":',1)[-1].split('\npermissions:',1)[0]:
        errors.append('manual heavy Android CI must remain separate from PR-required checks')
    for name,(body,needles) in guards.items():
        for needle in needles:
            if needle not in body: errors.append(name+': missing '+needle)
    for forbidden in ['dev_keystore.jks','kJCp!Bda']:
        if forbidden in gradle: errors.append('deprecated public signing credential still referenced')
    # Validate the *actual* Gradle task name patterns, rather than an
    # unrelated test-side approximation. Release tests cannot be mistaken for
    # distributable APKs, and release output tasks must remain fail-closed.
    release_patterns = re.findall(r'task\.name\s*==~\s*/([^/\n]+)/', gradle)
    expected_patterns = [
        '(?i)(assemble|package|bundle).*release.*',
        '(?i).*(unittest|androidtest).*',
    ]
    if release_patterns != expected_patterns:
        errors.append('release task graph must distinguish signed artifacts from unit-test packaging')
    if "if (releasePackage && System.getenv('AM_SIGNING_VARIANT') != 'release')" not in gradle:
        errors.append('release output gate no longer rejects missing protected signing identity')
    if 'uses: github/codeql-action/autobuild@v3' in codeql:
        errors.append('CodeQL must not request an unsigned release build')
    return errors

class SigningSourceContract(unittest.TestCase):
    def test_current_signing_contract(self):
        self.assertEqual([], inspect(ROOT))
    def fixture(self, changed_path, from_text, to_text):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in SOURCES:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes((ROOT/name).read_bytes())
            p=root/changed_path
            s=p.read_text();self.assertIn(from_text,s)
            p.write_text(s.replace(from_text,to_text,1))
            self.assertNotEqual([], inspect(root))
    def test_cannot_restore_public_debug_key(self):
        self.fixture('app/build.gradle','signingConfigs.ciDebug','signingConfigs.debug')
    def test_cannot_skip_release_guard(self):
        self.fixture('app/build.gradle','Unsigned release packaging refused','unsigned allowed')
    def test_cannot_upload_without_signature_verification(self):
        self.fixture('.github/workflows/devtool-tasker-ci.yml',
                     'bash scripts/devtool/ci_signing.sh verify app/build/outputs/apk/debug',
                     'echo skipped')
    def test_cannot_remove_protected_release_environment(self):
        self.fixture('.github/workflows/appmanager-signed-apks.yml',
                     'release-signing', 'unprotected')
    def test_cannot_skip_certificate_verification(self):
        self.fixture('scripts/devtool/ci_signing.sh',
                     '--print-certs', '--no-cert-info')
    def test_cannot_skip_same_repository_pr_contract(self):
        self.fixture('.github/workflows/amui-targeted-ci.yml',
                     '    name: Targeted source and regression contracts',
                     "    if: github.event_name != 'pull_request'\n    name: Targeted source and regression contracts")
    def test_cannot_remove_required_ci_workflow(self):
        self.fixture('config/delivery-required-ci.json',
                     '412582857', '111111111')
    def test_cannot_weaken_policy_event(self):
        self.fixture('config/delivery-required-ci.json',
                     '"pull_request"', '"workflow_dispatch"')
    def test_cannot_miss_tests_pr_base(self):
        self.fixture('.github/workflows/tests.yml',
                     "      - 'feature/tasker-automation'", "      - 'unrelated-base'")
    def test_cannot_miss_head_pin(self):
        self.fixture('.github/workflows/codeql.yml',
                     'ref: ${{ github.event.pull_request.head.sha || github.sha }}',
                     'ref: main')
    def test_release_guard_task_classification(self):
        gradle = (ROOT/'app/build.gradle').read_text()
        patterns = re.findall(r'task\.name\s*==~\s*/([^/\n]+)/', gradle)
        self.assertEqual(['(?i)(assemble|package|bundle).*release.*',
                          '(?i).*(unittest|androidtest).*'], patterns)
        for task, should_gate in (
            ('assembleRelease', True),
            ('packageRelease', True),
            ('packageReleaseUniversalApk', True),
            ('bundleRelease', True),
            ('packageReleaseBundle', True),
            ('assembleDebug', False),
            ('packageDebug', False),
            ('testDebugUnitTest', False),
            ('testReleaseUnitTest', False),
            ('packageReleaseUnitTestForUnitTest', False),
            ('packageReleaseAndroidTest', False),
        ):
            actual = bool(re.fullmatch(patterns[0], task)) and not bool(re.fullmatch(patterns[1], task))
            self.assertEqual(should_gate, actual, task)

    def test_cannot_block_release_unit_test_packaging(self):
        self.fixture('app/build.gradle',
                     '!(task.name ==~ /(?i).*(unittest|androidtest).*/)',
                     'true')

    def test_cannot_allow_unsigned_release_assemble(self):
        self.fixture('app/build.gradle',
                     '(task.name ==~ /(?i)(assemble|package|bundle).*release.*/)',
                     '(task.name ==~ /(?i)(assemble|package|bundle).*debug.*/)')

    def test_cannot_remove_required_release_identity_check(self):
        self.fixture('app/build.gradle',
                     "if (releasePackage && System.getenv('AM_SIGNING_VARIANT') != 'release')",
                     'if (false)')

    def test_shell_syntax(self):
        proc=subprocess.run(['bash','-n',str(ROOT/'scripts/devtool/ci_signing.sh')],check=False)
        self.assertEqual(0,proc.returncode)

if __name__=='__main__': unittest.main()
