#!/usr/bin/env python3
"""Fail-closed regression checks for AMUI-02 source invariants (no local Gradle)."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_amui02_theme import ACTIVITIES, check

class ThemeSourceContracts(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix='amui02-tests-')
        self.root = Path(self._temp.name)
        def put(p, text):
            f=self.root/p; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(text)
        self.put=put
        self.put('libcore/ui/src/main/res/values/styles.xml','<resources><style name="ThemeOverlay.AppTheme.PureBlackRoot" parent="" /></resources>')
        self.put('libcore/ui/src/main/res/values-night/styles.xml','<resources><style name="ThemeOverlay.AppTheme.PureBlackRoot" parent=""><item name="android:colorBackground">@android:color/black</item></style><style name="AppTheme.Black"><item name="android:colorBackground">@android:color/black</item><item name="android:windowBackground">@android:color/black</item></style></resources>')
        self.put('app/src/main/res/values-night/styles.xml','<resources><style name="AppTheme.Splash.Black"><item name="windowSplashScreenBackground">@android:color/black</item></style></resources>')
        appearance=('DynamicColors.wrapContextIfAvailable(newCtx) applyPureBlackBackground(themedContext, transparent)\n')*2
        appearance += ('DynamicColors.applyToActivityIfAvailable(activity);\n boolean transparent = false;\napplyPureBlackBackground(activity, transparent);\n'
                       'if (!transparent && Prefs.Appearance.isPureBlackTheme() && isDarkAppearance(context))\n'
                       'ThemeOverlay_AppTheme_PureBlackRoot, true\n'
                       'controller.setAppearanceLightStatusBars(lightBackground);\n'
                       'controller.setAppearanceLightNavigationBars(lightBackground);\n')
        self.put('app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/AppearanceUtils.java',appearance)
        self.put('app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/ColorCodes.java','return MaterialColors.getColor(context, androidx.appcompat.R.attr.colorError, ColorCodes.class.getCanonicalName());')
        self.put('.github/workflows/devtool-tasker-ci.yml',
            "(github.event_name == 'push' && startsWith(github.ref, 'refs/heads/feature/amui01'))\n"*6
            + '"on":\n'
            + "  workflow_dispatch:\noptions: [source, build, test, lint, instrumentation, full]\n"
            + "permissions:\n"
            + 'python3 scripts/devtool/check_amui01_hf09_kvm.py --check\npython3 scripts/devtool/check_amui02_theme.py --check\n'
            +'scripts/devtool/amui02_hosted_theme.sh\n'*2+'AMUI02_EXPECT_API=36\n'+'${{ runner.temp }}/amui02-*.json\n'*2)
        self.put('app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui02ThemeInstrumentedTest.java','@Test\n'*6+'Prefs.Appearance.setPureBlackTheme(originalPureBlack);\nPrefs.Appearance.setNightMode(originalMode);\n'+'themeErrorColorUsesAppCompatAttributeInLightMode\n'+'themeErrorColorUsesAppCompatAttributeInDarkMode\n')
        for n in ACTIVITIES:
            self.put(f'app/src/main/res/layout/activity_{n}.xml', '<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android" android:background="?android:attr/colorBackground"/>')
    def tearDown(self): self._temp.cleanup()
    def test_positive(self): check(self.root)
    def test_hf02_reject_day_implicit_style_parent(self):
        p=self.root/'libcore/ui/src/main/res/values/styles.xml'
        p.write_text(p.read_text().replace('parent=""', '', 1))
        with self.assertRaisesRegex(AssertionError, 'parent='):
            check(self.root)

    def test_hf02_reject_night_implicit_style_parent(self):
        p=self.root/'libcore/ui/src/main/res/values-night/styles.xml'
        p.write_text(p.read_text().replace('parent=""', '', 1))
        with self.assertRaisesRegex(AssertionError, 'parent='):
            check(self.root)

    def test_hf02_reject_accidental_inherited_material_palette(self):
        p=self.root/'libcore/ui/src/main/res/values-night/styles.xml'
        p.write_text(p.read_text().replace('parent=""', 'parent="ThemeOverlay.AppTheme"', 1))
        with self.assertRaisesRegex(AssertionError, 'parent='):
            check(self.root)

    def test_hf02_reject_duplicate_overlay(self):
        p=self.root/'libcore/ui/src/main/res/values/styles.xml'
        p.write_text(p.read_text().replace('</resources>',
            '<style name="ThemeOverlay.AppTheme.PureBlackRoot" parent="" /></resources>'))
        with self.assertRaisesRegex(AssertionError, 'missing/duplicated'):
            check(self.root)

    def test_hf05_reject_wrong_material_r_namespace(self):
        p=self.root/'app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/ColorCodes.java'
        p.write_text(p.read_text().replace('androidx.appcompat.R.attr.colorError',
            'com.google.android.material.R.attr.colorError'))
        with self.assertRaisesRegex(AssertionError, 'Material R class'):
            check(self.root)

    def test_hf05_reject_hardcoded_error_indicator(self):
        p=self.root/'app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/ColorCodes.java'
        p.write_text('return 0xff000000;')
        with self.assertRaisesRegex(AssertionError, 'AppCompat colorError'):
            check(self.root)

    def test_hf05_reject_framework_only_error_attr(self):
        p=self.root/'app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/ColorCodes.java'
        p.write_text(p.read_text().replace('androidx.appcompat.R.attr.colorError',
            'android.R.attr.colorError'))
        with self.assertRaisesRegex(AssertionError, 'AppCompat colorError'):
            check(self.root)

    def test_reject_surface_black(self):
        p=self.root/'libcore/ui/src/main/res/values-night/styles.xml'
        p.write_text(p.read_text().replace('</resources>','<item name="colorSurface">@android:color/black</item></resources>'))
        with self.assertRaises(AssertionError): check(self.root)
    def test_reject_missing_root(self):
        p=self.root/'app/src/main/res/layout/activity_settings.xml'
        p.write_text('<FrameLayout/>')
        with self.assertRaises(AssertionError): check(self.root)
    def test_reject_missing_android16_gate(self):
        p=self.root/'.github/workflows/devtool-tasker-ci.yml'
        p.write_text(p.read_text().replace('AMUI02_EXPECT_API=36',''))
        with self.assertRaises(AssertionError): check(self.root)
    def test_reject_automatic_heavy_pr_trigger(self):
        p=self.root/'.github/workflows/devtool-tasker-ci.yml'
        p.write_text(p.read_text().replace('permissions:',
            '  pull_request:\n    branches: [feature/tasker-automation]\n\npermissions:',1))
        with self.assertRaises(AssertionError): check(self.root)

    def test_reject_automatic_heavy_push_trigger(self):
        p=self.root/'.github/workflows/devtool-tasker-ci.yml'
        p.write_text(p.read_text().replace('permissions:',
            '  push:\n    branches: [feature/tasker-automation]\n\npermissions:',1))
        with self.assertRaises(AssertionError): check(self.root)

    def test_reject_loss_of_legacy_amui01_push_gate(self):
        p=self.root/'.github/workflows/devtool-tasker-ci.yml'
        p.write_text(p.read_text().replace("(github.event_name == 'push' && startsWith(github.ref, 'refs/heads/feature/amui01'))",'false',1))
        with self.assertRaises(AssertionError): check(self.root)
    def test_reject_overwritten_dynamic_order(self):
        p=self.root/'app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/AppearanceUtils.java'
        p.write_text(p.read_text().replace('DynamicColors.applyToActivityIfAvailable(activity);','DynamicColors.missing(activity);'))
        with self.assertRaises(AssertionError): check(self.root)
    def test_reject_missing_preferences_restore(self):
        p=self.root/'app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui02ThemeInstrumentedTest.java'
        p.write_text(p.read_text().replace('Prefs.Appearance.setPureBlackTheme(originalPureBlack);',''))
        with self.assertRaises(AssertionError): check(self.root)

if __name__ == '__main__': unittest.main()
