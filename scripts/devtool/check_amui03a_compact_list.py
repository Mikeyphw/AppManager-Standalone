#!/usr/bin/env python3
"""AMUI03A: compact M3 list row, no adapter or AMUI-01 reconciliation changes."""
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
ROW='app/src/main/res/layout/item_main.xml'
WF='.github/workflows/amui-targeted-ci.yml'
ADAPTER='app/src/main/java/io/github/muntashirakon/AppManager/main/MainRecyclerAdapter.java'
FILES=(ROW,WF,ADAPTER)
ANDROID='{http://schemas.android.com/apk/res/android}'
APP='{http://schemas.android.com/apk/res-auto}'
REQUIRED=('icon','backup_indicator','favorite_icon','label','packageName','version',
          'isSystem','size','date','shareid','issuer','sha','backup_info','backup_info_ext')
TEXTS=set(REQUIRED)-{'icon','favorite_icon'}

def validate(sources:dict[str,str])->bool:
    def must(ok,message):
        if not ok:raise AssertionError('AMUI03A_REFUSED: '+message)
    row=ET.fromstring(sources[ROW])
    must(row.tag=='com.google.android.material.card.MaterialCardView','MaterialCardView root required')
    must(row.get('style')=='@style/Widget.AppTheme.CardView.ListItem.Outlined','outlined M3 selection style removed')
    must(row.get(APP+'cardBackgroundColor')=='?attr/colorSurfaceContainerLow','dynamic Material container palette lost')
    for flag in ('clickable','focusable','checkable'):
        must(row.get(ANDROID+flag)=='true','row interaction disabled: '+flag)
    must(row.get(ANDROID+'minHeight')=='64dp','minimum card hit target drifted')
    nodes={}
    for node in row.iter():
        ident=node.get(ANDROID+'id','')
        if ident.startswith('@+id/'):
            name=ident[5:]
            must(name not in nodes,'duplicate id '+name)
            nodes[name]=node
        must(node.get(ANDROID+'textSize') is None,'hardcoded font override found')
    must(set(nodes)==set(REQUIRED),f'adapter field mismatch: missing {set(REQUIRED)-set(nodes)} extra {set(nodes)-set(REQUIRED)}')
    must(nodes['icon'].get(ANDROID+'layout_width')=='40dp' and nodes['icon'].get(ANDROID+'layout_height')=='40dp',
         'compact icon sizing drifted')
    must(nodes['label'].get(ANDROID+'textAppearance')=='?attr/textAppearanceTitleMedium','primary label typography drift')
    for name in TEXTS:
        n=nodes[name]
        must(n.tag.endswith('TextView'),'bound field no longer a TextView: '+name)
        must(n.get(ANDROID+'maxLines')=='1' and n.get(ANDROID+'ellipsize') in ('end','middle'),
             'long text cannot truncate safely: '+name)
        must(n.get(ANDROID+'textAppearance','').startswith('?attr/textAppearance'),
             'text palette role missing: '+name)
    must(nodes['packageName'].get(ANDROID+'ellipsize')=='middle','long package IDs must retain recognizable suffix')
    for name in ('issuer','sha','backup_info','backup_info_ext','backup_indicator'):
        must(nodes[name].get(ANDROID+'visibility')=='gone','optional metadata must not reserve height: '+name)
    for name in ('version','isSystem','size','date','shareid'):
        must(nodes[name].get(ANDROID+'layout_width')=='0dp' and float(nodes[name].get(ANDROID+'layout_weight','0'))>0,
             'side-by-side metadata must share available width: '+name)
    a=sources[ADAPTER]
    for marker in ('LayoutInflater.from(parent.getContext()).inflate(R.layout.item_main, parent, false)',
                   'cardView.setOnClickListener(', 'cardView.setOnLongClickListener(',
                   'holder.icon.setOnClickListener(', 'toggleSelection(currentPos);',
                   'handleClick(getItem(currentPos));', 'cardView.setStrokeColor(',
                   'getItem(position).hashCode()', 'notifySelectionChange();',
                   'mActivity.viewModel.select(', 'mActivity.viewModel.deselect('):
        must(marker in a,'AMUI-01 interaction/binding anchor lost: '+marker)
    # AMUI03A_HF01: real adapter has three independent toggle paths
    # (row selection-mode, long press, icon) and four status stroke branches.
    # Checking mere membership masked a missing call in the real adapter.
    must(a.count('toggleSelection(currentPos);')==3,
         'selection path count drift: row, long-press or icon selection missing')
    must(a.count('cardView.setStrokeColor(')==4,
         'status stroke priority drift: uninstall, disabled, stopped or default missing')
    for guard in ('if (!item.isInstalled)', 'else if (item.isDisabled)', 'else if (item.isStopped)'):
        must(guard in a,'status stroke priority guard missing: '+guard)
    for name in REQUIRED:
        must('R.id.'+name in a,'adapter no longer binds '+name)
    wf=sources[WF]
    must('python3 -B scripts/devtool/check_amui03a_compact_list.py --check' in wf and
         'python3 -B scripts/devtool/test_amui03a_compact_list.py' in wf,
         'targeted regression jobs not registered')
    must('Scoped Android resource and Java compile (no emulator)' in wf,'lightweight Java/resource compile lost')
    return True

def check(root:Path=ROOT)->bool:
    return validate({p:(root/p).read_text(encoding='utf-8') for p in FILES})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.parse_args()
    check();print('AMUI03A_COMPACT_M3_LIST_SOURCE_PASS')
