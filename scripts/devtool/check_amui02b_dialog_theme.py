#!/usr/bin/env python3
"""AMUI02B source contracts: widget configuration and dialog-content palette parity."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
APP='app/src/main/java/io/github/muntashirakon/AppManager/utils/appearance/AppearanceUtils.java'
TEST='app/src/androidTest/java/io/github/muntashirakon/AppManager/utils/appearance/Amui02ThemeInstrumentedTest.java'
WF='.github/workflows/amui-targeted-ci.yml'
BASE='libcore/ui/src/main/java/io/github/muntashirakon/dialog/'
DIALOGS=('SearchableSingleChoiceDialogBuilder.java','SearchableMultiChoiceDialogBuilder.java',
         'SearchableItemsDialogBuilder.java','TextInputDialogBuilder.java','TextInputDropdownDialogBuilder.java')
FILES=(APP,TEST,WF)+tuple(BASE+n for n in DIALOGS)
def validate(src:dict[str,str])->bool:
    def require(ok, reason):
        if not ok:raise AssertionError('AMUI02B_REFUSED: '+reason)
    app=src[APP]
    a=app.split('public static Context getThemedWidgetContext(',1)
    require(len(a)==2,'widget context missing')
    widget=a[1].split('public static Context getSystemContext(',1)[0]
    for token in ('options.locale = LangUtils.getFromPreference(context);',
                  'options.layoutDirection = Prefs.Appearance.getLayoutDirection();',
                  'options.theme = transparent ? Prefs.Appearance.getTransparentAppTheme() : Prefs.Appearance.getAppTheme();',
                  'options.nightMode = Prefs.Appearance.getNightMode();',
                  'newCtx.applyOverrideConfiguration(createOverrideConfiguration(context, options));',
                  'DynamicColors.wrapContextIfAvailable(newCtx);',
                  'applyPureBlackBackground(themedContext, transparent);'):
        require(widget.count(token)==1,'widget configuration token absent or duplicated '+token)
    require(widget.index('newCtx.applyOverrideConfiguration(')<widget.index('DynamicColors.wrapContextIfAvailable(')<widget.index('applyPureBlackBackground('),
            'widget theme order must be override, dynamic palette, root black')
    for name in DIALOGS:
        body=src[BASE+name]
        init='mBuilder = new MaterialAlertDialogBuilder('
        require(body.count(init)==1,'dialog builder missing/duplicated '+name)
        begin=body.index(init)
        attach = 'mBuilder.setView(mView);' if name=='SearchableMultiChoiceDialogBuilder.java' else 'mBuilder.setView(view);'
        require(attach in body,'dialog custom view missing '+name)
        require(body.index(attach)>begin,'dialog view before builder '+name)
        if name=='SearchableMultiChoiceDialogBuilder.java':
            require('context = mBuilder.getContext();' in body,'searchable multi-choice not using themed context')
            require(begin<body.index('context = mBuilder.getContext();')<body.index('mView = View.inflate(context,'),
                    'searchable multi-choice inflated before theme')
        elif name=='TextInputDialogBuilder.java':
            require('mContext = mBuilder.getContext();' in body, 'text input theme context missing')
            require(begin<body.index('mContext = mBuilder.getContext();')<body.index('View view = View.inflate(mContext,'),
                    'input dialog content must use themed context')
        elif name=='TextInputDropdownDialogBuilder.java':
            require('View view = View.inflate(mBuilder.getContext(),' in body,'dropdown inflater lost dialog theme')
            require(begin<body.index('View view = View.inflate(mBuilder.getContext(),'),
                    'dropdown input must inflate with Material dialog context')
            require('new AnyFilterArrayAdapter<>(mActivity,' not in body and
                    'new NoFilterArrayAdapter<>(mActivity,' not in body,
                    'dropdown adapter still uses activity theme')
            require(body.count('new AnyFilterArrayAdapter<>(mBuilder.getContext(),')>=1 and
                    body.count('new NoFilterArrayAdapter<>(mBuilder.getContext(),')>=1,
                    'dropdown adapter not tied to dialog palette')
        else:
            require('context = mBuilder.getContext();' in body,'searchable dialog context overlay missing '+name)
            require(begin<body.index('context = mBuilder.getContext();')<body.index('View view = View.inflate(context,'),
                    'searchable dialog inflated before Material overlay: '+name)
            require('MaterialAttributes.resolveInteger(context,' in body,
                    'list row style must resolve in themed context '+name)
        require('new MaterialAlertDialogBuilder(context).setView(' not in body and
                'new MaterialAlertDialogBuilder(activity).setView(' not in body,
                'legacy dialog builder constructed after inflation '+name)
    wf=src[WF]
    require('python3 -B scripts/devtool/check_amui02b_dialog_theme.py --check' in wf and
            'python3 -B scripts/devtool/test_amui02b_dialog_theme.py' in wf,
            'new source regressions not registered in targeted CI')
    device=src[TEST]
    for marker in ('widgetContextDarkPureBlackLeavesRaisedSurfaceTonal',
                   'widgetContextLightIsNotBlackWhenPreferenceRemainsEnabled',
                   'Prefs.Appearance.setPureBlackTheme(originalPureBlack);',
                   'Prefs.Appearance.setNightMode(originalMode);'):
        require(marker in device,'instrumentation/restore coverage missing '+marker)
    require(device.count('@Test')>=8,'device appearance test count unexpectedly reduced')
    return True

def check(root:Path=ROOT)->bool:
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.parse_args()
    check();print('AMUI02B_DIALOG_WIDGET_SOURCE_PASS')
