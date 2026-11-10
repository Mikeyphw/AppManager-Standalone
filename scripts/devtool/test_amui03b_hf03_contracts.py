#!/usr/bin/env python3
"""HF03 regression mutations, source-only; preserve native backup/restore security guards."""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui03b_hf03_contracts import ROOT,FILES,F05,F06,FULL,TARGET,validate
class ContractParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,key,old,new):
        self.assertIn(old,self.src[key]);s=dict(self.src);s[key]=s[key].replace(old,new,1)
        with self.assertRaises(AssertionError):validate(s)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_05c_manual(self):self.reject(F05,"'  device-instrumentation:'","'  removed-emulator:'")
    def test_06b_manual(self):self.reject(F06,"'  device-instrumentation:'","'  removed-emulator:'")
    def test_05c_targeted_dependency(self):self.reject(F05,"'targeted': Path('.github/workflows/amui-targeted-ci.yml')", "'fake': Path('no-workflow')")
    def test_06b_targeted_dependency(self):self.reject(F06,"'targeted':Path('.github/workflows/amui-targeted-ci.yml')", "'fake':Path('no-workflow')")
    def test_05c_native_service(self):self.reject(F05,"'service': Path('app/src/main/java/io/github/muntashirakon/AppManager/batchops/BatchOpsService.java')", "'service':Path('not-a-service')")
    def test_06b_native_service(self):self.reject(F06,"'service':Path('app/src/main/java/io/github/muntashirakon/AppManager/batchops/BatchOpsService.java')", "'service':Path('not-a-service')")
    def test_05c_source_gate(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amt05c_contract.py --check','echo bypass')
    def test_06b_source_gate(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amt06b_contract.py --check','echo bypass')
    def test_full_dispatch(self):self.reject(FULL,'  workflow_dispatch:', '  push:')
    def test_full_device(self):self.reject(FULL,'  device-instrumentation:','  removed-instrumentation:')
    def test_full_android16(self):self.reject(FULL,'  amui01-android16:','  removed-android16:')
    def test_full_fixture(self):self.reject(FULL,'  amt06c-fixture:','  removed-fixture:')
    def test_full_own_checker(self):self.reject(FULL,'python3 scripts/devtool/check_amui03b_hf03_contracts.py --check','echo bypass')
    def test_targeted_own_checker(self):self.reject(TARGET,'python3 -B scripts/devtool/check_amui03b_hf03_contracts.py --check','echo bypass')
    def test_targeted_test(self):self.reject(TARGET,'python3 -B scripts/devtool/test_amui03b_hf03_contracts.py','echo bypass')
    def test_all_source_mutations(self):self.reject(TARGET,"python3 -B -m unittest discover -s scripts/devtool -p 'test_*.py' -v",'echo bypass')
if __name__=='__main__':unittest.main()
