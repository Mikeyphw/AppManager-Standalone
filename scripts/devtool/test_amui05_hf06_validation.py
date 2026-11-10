#!/usr/bin/env python3
"""Devtool validation must survive ephemeral artifact cleanup, never skip tests.

Works on the hosted runner and Termux without Gradle, devices, or network.
"""
from __future__ import annotations
import os, shutil, subprocess, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
CANONICAL=HERE/'amui05_hf06_validate.sh'
VALIDATOR=HERE.parents[1]/'.devtool-artifact/validate.sh'
WRAPPER='''#!/usr/bin/env sh
set -eu
sh -n .devtool-artifact/validate.sh
sh -n scripts/devtool/amui05_hf06_validate.sh
exec sh scripts/devtool/amui05_hf06_validate.sh
'''
FINAL='AMUI05_HF06_VALIDATION_FULL_SOURCE_AND_REGRESSION_SUITE_PASS'
REQUIRED=(
 'python3 -B scripts/devtool/check_amui05_acceptance.py --check',
 'python3 -B scripts/devtool/test_amui05_hf06_scope.py',
 'python3 -B scripts/devtool/test_amui05_hf06_recovery.py',
 'python3 -B scripts/devtool/test_amui05_hf06_validation.py',
 'python3 -B scripts/devtool/test_amui05_hf06_metadata.py',
 'python3 -B scripts/devtool/test_amui05_hf03_recovery.py',
 'python3 -B scripts/devtool/check_amui04d_final_gate.py --check',
 'python3 -B scripts/devtool/check_amui02_theme.py --check',
 "python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v",
)

def audit_source(source: str) -> bool:
    def require(condition, reason):
        if not condition:raise AssertionError('AMUI05_HF06_VALIDATION_REFUSED: '+reason)
    require(source.startswith('#!/usr/bin/env sh\nset -eu\n'), 'no strict shell entry')
    require(source.count('sh -n "$0"')==1, 'self syntax must be checked once')
    require(source.index('sh -n "$0"') < source.index('python3 -B '),
            'syntax check must precede suite')
    require('.devtool-artifact/' not in '\n'.join(line for line in source.splitlines()
            if not line.strip().startswith('#')),
            'post-suite check cannot depend on transient metadata')
    require(source.count("-m unittest discover -s scripts/devtool -p 'test_*.py' -v")==1,
            'entire source and regression suite required')
    for line in REQUIRED:
        require(source.count(line)==1,'mandatory test step missing or repeated '+line)
    require(source.count("printf '"+FINAL+"\\n'")==1 and
            source.index("printf '"+FINAL+"\\n'")>source.index(REQUIRED[-1]),
            'final PASS must be after all tests')
    require(not any(x in source for x in ('|| true','set +e','; true','rm -rf', 'git reset --hard')),
            'validation must fail closed and not erase source')
    return True

class ValidationSurvival(unittest.TestCase):
    def test_positive(self):self.assertTrue(audit_source(CANONICAL.read_text()))
    def test_strict_syntax(self):
        p=subprocess.run(['sh','-n',str(CANONICAL)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
    def test_final_syntax_before_suite(self):
        s=CANONICAL.read_text()
        self.assertLess(s.index('sh -n "$0"'),s.index('python3 -B'))
    def test_post_suite_metadata_dependency_refused(self):
        s=CANONICAL.read_text().replace("printf '"+FINAL+"\\n'",
                "sh -n .devtool-artifact/validate.sh\nprintf '"+FINAL+"\\n'")
        with self.assertRaisesRegex(AssertionError,'transient metadata'):audit_source(s)
    def test_drop_full_suite_refused(self):
        s=CANONICAL.read_text().replace(REQUIRED[-1],'echo skip')
        with self.assertRaises(AssertionError):audit_source(s)
    def test_move_syntax_to_end_refused(self):
        s=CANONICAL.read_text().replace('sh -n "$0"\n','',1)
        s=s.replace("printf '"+FINAL+"\\n'",'sh -n "$0"\n'+"printf '"+FINAL+"\\n'")
        with self.assertRaises(AssertionError):audit_source(s)
    def test_bypass_failure_refused(self):
        s=CANONICAL.read_text().replace(REQUIRED[-1],REQUIRED[-1]+' || true')
        with self.assertRaises(AssertionError):audit_source(s)
    def run_fixture(self,remove_metadata:bool,fail_first:bool=False):
        # Simulate the exact failure mode without deleting any real repository
        # files. Python stub is used only in this disposable test fixture.
        scratch=os.environ.get('TMPDIR') or None
        with tempfile.TemporaryDirectory(prefix='amui05-hf06-',dir=scratch) as td:
            root=Path(td); (root/'.devtool-artifact').mkdir()
            scripts=root/'scripts/devtool'; scripts.mkdir(parents=True)
            (scripts/'amui05_hf06_validate.sh').write_bytes(CANONICAL.read_bytes())
            (root/'.devtool-artifact/validate.sh').write_bytes(VALIDATOR.read_bytes())
            bin_dir=root/'bin';bin_dir.mkdir()
            fail_stmt="exit 33" if fail_first else "exit 0"
            runner='''#!/usr/bin/env sh
set -eu
case " $* " in
  *" -m unittest "*)
    %s
    ;;
  *check_amui05_acceptance.py*)
    %s
    ;;
esac
exit 0
''' % ('rm -rf .devtool-artifact' if remove_metadata else ':',fail_stmt)
            exe=bin_dir/'python3';exe.write_text(runner);exe.chmod(0o755)
            env=dict(os.environ,PATH=str(bin_dir)+os.pathsep+os.environ.get('PATH',''))
            p=subprocess.run(['sh','.devtool-artifact/validate.sh'],cwd=root,
                             env=env,text=True,capture_output=True)
            return p,(root/'.devtool-artifact').exists()
    def test_ephemeral_artifact_removed_mid_suite_still_reports_valid_pass(self):
        p,exists=self.run_fixture(remove_metadata=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertFalse(exists)
        self.assertIn(FINAL,p.stdout)
    def test_real_check_failure_still_fails_closed(self):
        p,_=self.run_fixture(remove_metadata=True,fail_first=True)
        self.assertNotEqual(p.returncode,0)
        self.assertNotIn(FINAL,p.stdout)

if __name__=='__main__':unittest.main()
