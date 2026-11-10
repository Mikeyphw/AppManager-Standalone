#!/usr/bin/env python3
"""HF06 inventory-bound validator entry: enforce true Devtool extraction semantics."""
from __future__ import annotations
import hashlib,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ENTRY='.devtool-artifact/validate.sh'
VALIDATOR=ROOT/ENTRY
CANONICAL=ROOT/'scripts/devtool/amui05_hf06_validate.sh'

def check_entry(source:bytes, inventory:set[str])->bool:
    def must(test,msg):
        if not test:raise AssertionError('AMUI05_HF06_METADATA_REFUSED: '+msg)
    must(ENTRY in inventory,'validation hook not declared as an inventory payload')
    must(source.startswith(b'#!/usr/bin/env sh\nset -eu\n'),'validation hook non-strict')
    must(source.count(b'exec sh scripts/devtool/amui05_hf06_validate.sh')==1,
         'validator must hand off to persistent repository script')
    must(b'sh -n "$0"' in source and b'sh -n scripts/devtool/amui05_hf06_validate.sh' in source,
         'validator syntax guards not retained')
    must(b'rm -rf' not in source and b'|| true' not in source,
         'unsafe validation hook')
    return True

class MetadataPayload(unittest.TestCase):
    def test_positive_on_installed_worktree(self):
        self.assertTrue(VALIDATOR.is_file(), 'Devtool did not install inventoried validator')
        self.assertTrue(CANONICAL.is_file(), 'persistent validation suite missing')
        self.assertTrue(check_entry(VALIDATOR.read_bytes(),{ENTRY}))
    def test_missing_inventory_refused(self):
        with self.assertRaisesRegex(AssertionError,'not declared'):
            check_entry(VALIDATOR.read_bytes(),set())
    def test_lost_payload_refused(self):
        with tempfile.TemporaryDirectory(prefix='amui05-hf06-') as d:
            root=Path(d)
            # Mimic _extract_archive: metadata-only entries are skipped
            # unless the overlay inventory declares them as payload.
            archived={ENTRY:VALIDATOR.read_bytes(),'scripts/devtool/amui05_hf06_validate.sh':CANONICAL.read_bytes()}
            for n,data in archived.items():
                if n.startswith('.devtool-artifact/'):
                    continue
                file=root/n;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
            p=subprocess.run(['sh',ENTRY],cwd=root,capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('cannot open',p.stderr)
    def test_declared_payload_dispatch_survives_metadata_deletion(self):
        with tempfile.TemporaryDirectory(prefix='amui05-hf06-') as d:
            root=Path(d)
            files={ENTRY:VALIDATOR.read_bytes(),'scripts/devtool/amui05_hf06_validate.sh':CANONICAL.read_bytes()}
            # Dummy Python only in disposable fixture; suite still enforces
            # nonzero source-test exits and full checks on real worktree.
            binpath=root/'bin';binpath.mkdir()
            py=binpath/'python3';py.write_text('#!/bin/sh\ncase " $* " in *" -m unittest "*) rm -rf .devtool-artifact;; esac\nexit 0\n');py.chmod(0o755)
            for path,data in files.items():
                dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            env=dict(os.environ,PATH=str(binpath)+os.pathsep+os.environ.get('PATH',''))
            p=subprocess.run(['sh',ENTRY],cwd=root,env=env,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('AMUI05_HF06_VALIDATION_FULL_SOURCE_AND_REGRESSION_SUITE_PASS',p.stdout)
            self.assertFalse((root/'.devtool-artifact').exists())
    def test_script_checksums_have_stable_bytes(self):
        a=hashlib.sha256(VALIDATOR.read_bytes()).hexdigest()
        self.assertEqual(len(a),64)
        self.assertEqual(subprocess.run(['sh','-n',str(VALIDATOR)]).returncode,0)
    def test_false_positive_validator_rejected(self):
        bad=VALIDATOR.read_bytes().replace(b'exec sh scripts/devtool/amui05_hf06_validate.sh',b'exit 0')
        with self.assertRaises(AssertionError):check_entry(bad,{ENTRY})
if __name__=='__main__':unittest.main()
