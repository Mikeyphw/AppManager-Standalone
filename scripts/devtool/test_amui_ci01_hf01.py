#!/usr/bin/env python3
"""Source-only mutation tests for AMUI CI01 HF01, no Android/Gradle/network."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from check_amui_ci01_hf01 import FILES,ROOT,validate
class Ci01Hf01Mutations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s={k:(ROOT/p).read_text(encoding='utf-8') for k,p in FILES.items()}
    def reject(self,key,old,new):
        self.assertIn(old,self.s[key]);bad=dict(self.s);bad[key]=bad[key].replace(old,new,1)
        with self.assertRaises(AssertionError):validate(bad)
    def test_positive(self):self.assertTrue(validate(self.s))
    def test_no_auto_heavy_push(self):self.reject('full','permissions:', '  push:\n    branches: [feature/tasker-automation]\npermissions:')
    def test_no_auto_heavy_pr(self):self.reject('full','permissions:', '  pull_request:\n    branches: [master]\npermissions:')
    def test_targeted_not_removed(self):self.reject('targeted','  push:', '  dispatch_removed:')
    def test_amt00_targeted_guard(self):self.reject('amt00','manual-only heavy CI','automatic heavy CI')
    def test_amt04_androidtest_guard(self):self.reject('amt04','instrumentation-only pushes','eventless instrumentation')
    def test_amt04b2_guard(self):self.reject('amt04b2','amui-targeted-ci.yml','missing-targeted.yml')
    def test_amt04b2b_guard(self):self.reject('amt04b2b','amui-targeted-ci.yml','missing-targeted.yml')
    def test_javac_nontransitive(self):self.reject('android_test','androidx.appcompat.R.attr.colorPrimary','com.google.android.material.R.attr.colorPrimary')
    def test_scoped_compile_not_removed(self):self.reject('targeted',':app:compileDebugAndroidTestJavaWithJavac',':app:compileDebugJavaWithJavac')
    def test_gate_hook_cadence(self):self.reject('hook','AMUI_GATE_EVERY:-5','AMUI_GATE_EVERY:-999')
    def test_post_push_records_once(self):self.reject('hook','scripts/devtool/amui_ci_gate.py --record "$sha"','scripts/devtool/amui_ci_gate.py --status')
if __name__=='__main__':unittest.main()
