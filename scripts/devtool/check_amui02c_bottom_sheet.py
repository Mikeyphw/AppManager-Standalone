#!/usr/bin/env python3
"""AMUI02C: theme-context-driven bar contrast, no global night-mode shortcuts."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
APP='app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/AppearanceUtils.java'
CAP='libcore/ui/src/main/java/io/github/muntashirakon/dialog/CapsuleBottomSheetDialogFragment.java'
TEST='app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui02ThemeInstrumentedTest.java'
WF='.github/workflows/amui-targeted-ci.yml'
FILES=(APP,CAP,TEST,WF)

def validate(src:dict[str,str])->bool:
    def require(condition,reason):
        if not condition:raise AssertionError('AMUI02C_REFUSED: '+reason)
    app=src[APP];cap=src[CAP];dev=src[TEST];wf=src[WF]
    body=app.split('private static boolean isDarkAppearance(',1)
    require(len(body)==2,'isDarkAppearance missing')
    body=body[1].split('private static void applySystemBarIconContrast(',1)[0]
    require('mapNightModeOnce(context, Prefs.Appearance.getNightMode())' in body,
            'effective night-mode selection lost')
    require('(context.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)' in body,
            'follow-system appearance must use supplied context configuration')
    require('Resources.getSystem().getConfiguration()' not in body,
            'global resources cannot determine a themed wrapper night mode')
    require(app.count('applyPureBlackBackground(themedContext, transparent);')==2,
            'pure-black root-only appearance lost')
    section=cap.split('private static class BottomSheetDialogInternal extends BottomSheetDialog',1)
    require(len(section)==2,'capsule bottom-sheet internal dialog missing')
    section=section[1].split('Objects.requireNonNull((View) findViewById(R.id.container))',1)[0]
    require('WindowCompat.setDecorFitsSystemWindows(window, false);' in section,
            'edge-to-edge bottom-sheet window behavior lost')
    require('window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);' in section,
            'transparent system bars must be owned by dialog window')
    require('window.setStatusBarColor(Color.TRANSPARENT);' in section and
            'window.setNavigationBarColor(Color.TRANSPARENT);' in section,
            'both system bars must remain transparent')
    require('boolean lightBars = !UiUtils.isDarkMode(getContext());' in section,
            'bar icon contrast must come from dialog themed context')
    require('controller.setAppearanceLightStatusBars(lightBars);' in section and
            'controller.setAppearanceLightNavigationBars(lightBars);' in section,
            'status and navigation icons must agree with current theme')
    require('UiUtils.setSystemBarStyle(window, true)' not in section and
            'UiUtils.isDarkMode()' not in section,
            'legacy global-mode system bar styling must not override context theme')
    require('window.addFlags(WindowManager.LayoutParams.FLAG_BLUR_BEHIND);' in section,
            'existing optional dialog blur behavior missing')
    require('mBehavior.setSkipCollapsed(true);' in cap and
            'mBehavior.setSkipHalfExpanded(true);' in cap,
            'original bottom-sheet interaction contract must be retained')
    for marker in ('darkBottomSheetUsesDialogContextForBarContrast',
                   'lightBottomSheetUsesDialogContextForBarContrast',
                   'UiUtils.isDarkMode(context)',
                   'Prefs.Appearance.setPureBlackTheme(originalPureBlack);',
                   'Prefs.Appearance.setNightMode(originalMode);'):
        require(marker in dev,'device regression or preference restore lost: '+marker)
    require(dev.count('@Test')>=10,'Android appearance tests unexpectedly reduced')
    require('python3 -B scripts/devtool/check_amui02c_bottom_sheet.py --check' in wf and
            'python3 -B scripts/devtool/test_amui02c_bottom_sheet.py' in wf,
            'targeted source validation unregistered')
    require('Scoped Android resource and Java compile (no emulator)' in wf,
            'hosted targeted compiler gate removed')
    return True

def check(root:Path=ROOT):
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})
if __name__=='__main__':
    import argparse
    x=argparse.ArgumentParser();x.add_argument('--check',action='store_true');x.parse_args()
    check();print('AMUI02C_BOTTOM_SHEET_SOURCE_PASS')
