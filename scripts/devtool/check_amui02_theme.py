#!/usr/bin/env python3
"""AMUI02 source acceptance. Hosted instrumentation confirms device behavior separately."""
import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ACTIVITIES = (
    'app_details', 'app_usage', 'apps_profile', 'auth_management', 'batch_ops_results',
    'code_editor', 'debloater', 'finder', 'fm', 'help', 'interceptor', 'labs', 'logcat',
    'main', 'one_click_ops', 'op_history', 'profiles', 'running_apps', 'settings',
    'settings_dual_pane', 'shared_prefs', 'sys_config', 'term', 'virus_total',
)
APPEARANCE = 'app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/AppearanceUtils.java'
COLORS = 'app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/ColorCodes.java'
DAY = 'libcore/ui/src/main/res/values/styles.xml'
NIGHT = 'libcore/ui/src/main/res/values-night/styles.xml'
SPLASH = 'app/src/main/res/values-night/styles.xml'
WF = '.github/workflows/devtool-tasker-ci.yml'
TEST = 'app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui02ThemeInstrumentedTest.java'


def check(root: Path):
    def read(p):
        return (root/p).read_text(encoding='utf-8')
    day, night, appearance, wf = [read(x) for x in (DAY,NIGHT,APPEARANCE,WF)]
    for text in (day, night, read(SPLASH)):
        ET.fromstring(text)
    # HF02: Dotted Android style names implicitly inherit their prefix unless
    # parent is explicit. The old declarations made AAPT look for nonexistent
    # style/ThemeOverlay.AppTheme, breaking all Gradle and emulator jobs.
    for label, xml_text in (('day', day), ('night', night)):
        overlays = [node for node in ET.fromstring(xml_text).findall('style')
                    if node.get('name') == 'ThemeOverlay.AppTheme.PureBlackRoot']
        assert len(overlays) == 1, f'AMUI02_HF02: {label} pure-black overlay missing/duplicated'
        assert overlays[0].get('parent') == '', (
            f'AMUI02_HF02: {label} overlay must specify parent="" to prevent '
            'implicit ThemeOverlay.AppTheme inheritance and AAPT linking failure')
    assert '<item name="colorSurface">@android:color/black</item>' not in night, 'black must never replace M3 surface roles'
    assert night.count('<item name="android:colorBackground">@android:color/black</item>') >= 2
    assert '<item name="android:windowBackground">@android:color/black</item>' in night
    assert '<item name="windowSplashScreenBackground">@android:color/black</item>' in read(SPLASH)
    assert appearance.count('DynamicColors.wrapContextIfAvailable(newCtx)') == 2
    assert appearance.count('applyPureBlackBackground(themedContext, transparent)') == 2
    assert re.search(r'DynamicColors\.applyToActivityIfAvailable\(activity\);\s*boolean transparent.*?applyPureBlackBackground\(activity, transparent\);',appearance,re.S)
    assert 'if (!transparent && Prefs.Appearance.isPureBlackTheme() && isDarkAppearance(context))' in appearance
    assert 'ThemeOverlay_AppTheme_PureBlackRoot, true' in appearance
    assert 'controller.setAppearanceLightStatusBars(lightBackground);' in appearance
    assert 'controller.setAppearanceLightNavigationBars(lightBackground);' in appearance
    assert 'R.attr.colorError' in read(COLORS), 'M3 error color must be used'
    ns = '{http://schemas.android.com/apk/res/android}'
    for name in ACTIVITIES:
        p = f'app/src/main/res/layout/activity_{name}.xml'
        xml = ET.fromstring(read(p))
        assert xml.attrib.get(ns+'background') == '?android:attr/colorBackground', f'pure-black root missing: {p}'
    # Never rewrite AMUI-01's six source-contract-pinned predicates.
    old_push = "(github.event_name == 'push' && startsWith(github.ref, 'refs/heads/feature/amui01'))"
    assert wf.count(old_push) == 6
    assert "branches: [feature/tasker-automation, 'feature/amui01*']" in wf
    assert "branches: [master, feature/tasker-automation]" in wf
    assert "workflow_dispatch:" in wf and "options: [source, build, test, lint, instrumentation, full]" in wf
    assert 'python3 scripts/devtool/check_amui01_hf09_kvm.py --check' in wf
    assert 'python3 scripts/devtool/check_amui02_theme.py --check' in wf
    assert wf.count('scripts/devtool/amui02_hosted_theme.sh') == 2
    assert 'AMUI02_EXPECT_API=36' in wf
    assert wf.count('${{ runner.temp }}/amui02-*.json') == 2
    assert read(TEST).count('@Test') >= 4
    assert 'Prefs.Appearance.setPureBlackTheme(originalPureBlack);' in read(TEST)
    assert 'Prefs.Appearance.setNightMode(originalMode);' in read(TEST)
    assert 'AMT-06C' not in read(TEST), 'not allowed to perform Tasker fixture operations in UI tests'
    print(f'AMUI02_SOURCE_PASS roots={len(ACTIVITIES)} api35_api36=yes material3=yes tasker_preserved=yes')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', required=True)
    parser.add_argument('--root', default='.')
    args=parser.parse_args()
    check(Path(args.root))
