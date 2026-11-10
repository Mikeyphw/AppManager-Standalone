#!/usr/bin/env python3
"""AMUI03A fail-closed layout and adapter-binding mutation tests; no Gradle."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_amui03a_compact_list import FILES,ROOT,ROW,WF,ADAPTER,validate

class CompactListContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src={p:(ROOT/p).read_text(encoding='utf-8') for p in FILES}
    def reject(self,path,old,new):
        self.assertIn(old,self.src[path]);s=dict(self.src);s[path]=s[path].replace(old,new,1)
        with self.assertRaises(AssertionError):validate(s)
    def test_positive(self):self.assertTrue(validate(self.src))
    def test_no_dynamic_surface(self):self.reject(ROW,'?attr/colorSurfaceContainerLow','@android:color/black')
    def test_no_normal_card_style(self):self.reject(ROW,'Widget.AppTheme.CardView.ListItem.Outlined','Widget.AppTheme.CardView')
    def test_no_click(self):self.reject(ROW,'android:clickable="true"','android:clickable="false"')
    def test_no_long_click(self):self.reject(ADAPTER,'cardView.setOnLongClickListener(','// deleted long click')
    def test_no_icon_selection(self):self.reject(ADAPTER,'holder.icon.setOnClickListener(','// icon selection lost')
    def test_no_selection_state(self):self.reject(ADAPTER,'toggleSelection(currentPos);','// lost one selection path')
    def test_no_app_details(self):self.reject(ADAPTER,'handleClick(getItem(currentPos));','// removed')
    def test_no_selection_stroke(self):self.reject(ADAPTER,'cardView.setStrokeColor(','// removed one stroke branch')
    def test_no_selection_guard(self):self.reject(ADAPTER,'if (!item.isInstalled)','if (false)')
    def test_no_disabled_guard(self):self.reject(ADAPTER,'else if (item.isDisabled)','else if (false)')
    def test_no_stopped_guard(self):self.reject(ADAPTER,'else if (item.isStopped)','else if (false)')
    def test_no_package_id(self):self.reject(ROW,'android:id="@+id/packageName"','android:id="@+id/packageNameDeleted"')
    def test_no_backup(self):self.reject(ROW,'android:id="@+id/backup_info_ext"','android:id="@+id/lost_backup"')
    def test_no_signature(self):self.reject(ROW,'android:id="@+id/sha"','android:id="@+id/lost_sha"')
    def test_no_primary_label(self):self.reject(ROW,'?attr/textAppearanceTitleMedium','?attr/textAppearanceBodySmall')
    def test_no_optional_view_height(self):self.reject(ROW,'android:id="@+id/issuer"\n','android:id="@+id/issuer"\n') if False else self.reject(ROW,'android:visibility="gone"','android:visibility="invisible"')
    def test_no_truncation(self):self.reject(ROW,'android:ellipsize="middle"','android:ellipsize="none"')
    def test_no_large_icon(self):self.reject(ROW,'android:layout_width="40dp"','android:layout_width="64dp"')
    def test_no_small_touch_target(self):self.reject(ROW,'android:minHeight="64dp"','android:minHeight="40dp"')
    def test_no_compile_gate(self):self.reject(WF,'Scoped Android resource and Java compile (no emulator)','compile skipped')
    def test_no_targeted_source_check(self):self.reject(WF,'python3 -B scripts/devtool/check_amui03a_compact_list.py --check','echo bypass')
    def test_no_reconciliation(self):self.reject(ADAPTER,'notifySelectionChange();','// no refresh')

if __name__=='__main__':unittest.main()
