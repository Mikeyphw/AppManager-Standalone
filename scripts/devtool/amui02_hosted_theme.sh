#!/usr/bin/env bash
# Hosted Android 15/16 real resource/theme acceptance; no valuable application data is restored.
set -Eeuo pipefail
: "${RUNNER_TEMP:?RUNNER_TEMP must exist on GitHub Actions}"
: "${JAVA_HOME:?JAVA_HOME must be provisioned by hosted workflow}"
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd -- "$repo"
api="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
[[ "$api" == '35' || "$api" == '36' ]] || { echo "AMUI02_WRONG_API=$api" >&2; exit 1; }
if [[ -n "${AMUI02_EXPECT_API:-}" && "$api" != "$AMUI02_EXPECT_API" ]]; then
  echo "AMUI02_API_MISMATCH wanted=$AMUI02_EXPECT_API found=$api" >&2; exit 1
fi
original="$(mktemp "$RUNNER_TEMP/amui02-devtool.XXXXXXXX.toml")"
cp -- .devtool.toml "$original"
trap 'cp -- "$original" .devtool.toml; rm -f -- "$original"' EXIT
python3 -B scripts/devtool/amt03_hosted_config.py .devtool.toml --java-home "$JAVA_HOME"
report="$RUNNER_TEMP/amui02-appearance-api${api}.json"
log="$RUNNER_TEMP/amui02-appearance-api${api}.log"
set +e
python3 -B -m devtool.android_instrumentation "$PWD" --target app \
  --class io.github.muntashirakon.AppManager.utils.appearance.Amui02ThemeInstrumentedTest \
  --report "$report" 2>&1 | tee "$log"
rc="${PIPESTATUS[0]}"
set -e
python3 -B - "$report" "$rc" "$api" <<'PY'
import json,sys,os
from pathlib import Path
p=Path(sys.argv[1]); rc=int(sys.argv[2]); api=int(sys.argv[3])
assert p.is_file(), 'AMUI02_MISSING_HOSTED_RECEIPT'
receipt=json.loads(p.read_text())
assert rc==0 and receipt.get('returncode')==0, receipt
assert receipt.get('status') in ('success','passed'), receipt
assert int(receipt.get('executed',0)) >= 4, receipt
assert int(receipt.get('passed',0)) >= 4 and int(receipt.get('failed',1))==0, receipt
receipt['amui02_commit']=os.environ.get('GITHUB_SHA','')
receipt['amui02_api']=api
receipt['amui02_scope']='real dynamic theme resources; settings restored after tests'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('AMUI02_HOSTED_THEME_PASS',api,receipt['amui02_commit'])
PY
# AMUI-03C: read-only quick filter/density instrumentation on both API 35 and 36.
quick_report="$RUNNER_TEMP/amui03c-ui-api${api}.json"
quick_log="$RUNNER_TEMP/amui03c-ui-api${api}.log"
set +e
python3 -B -m devtool.android_instrumentation "$PWD" --target app \
  --class io.github.muntashirakon.AppManager.main.Amui03CQuickFiltersInstrumentedTest \
  --report "$quick_report" 2>&1 | tee "$quick_log"
quick_rc="${PIPESTATUS[0]}"
set -e
python3 -B - "$quick_report" "$quick_rc" "$api" <<'PY'
import json,sys,os
from pathlib import Path
p=Path(sys.argv[1]); rc=int(sys.argv[2]); api=int(sys.argv[3])
assert p.is_file(), 'AMUI03C_MISSING_HOSTED_DEVICE_RECEIPT'
receipt=json.loads(p.read_text())
assert rc==0 and receipt.get('returncode')==0, receipt
assert receipt.get('status') in ('success','passed'), receipt
assert int(receipt.get('executed',0)) >= 3, receipt
assert int(receipt.get('passed',0)) >= 3 and int(receipt.get('failed',1))==0, receipt
receipt['amui03c_commit']=os.environ.get('GITHUB_SHA','')
receipt['amui03c_api']=api
receipt['amui03c_scope']='read-only quick filter and compact-list UI inflation'
p.write_text(json.dumps(receipt,indent=2)+'\n')
print('AMUI03C_HOSTED_UI_PASS',api,receipt['amui03c_commit'])
PY
# AMUI-04A: five real Android UI/palette tests and three rendered screenshots.
# Required on both API 35 and API 36; no new Gradle invocation on Termux.
visual_report="$RUNNER_TEMP/amui04a-api${api}.json"
visual_log="$RUNNER_TEMP/amui04a-api${api}.log"
set +e
python3 -B -m devtool.android_instrumentation "$PWD" --target app \
  --class io.github.muntashirakon.AppManager.utils.appearance.Amui04AVisualInstrumentedTest \
  --report "$visual_report" 2>&1 | tee "$visual_log"
visual_rc="${PIPESTATUS[0]}"
set -e
python3 -B - "$visual_report" "$visual_rc" "$api" <<'PYVISUAL'
import json,os,sys
from pathlib import Path
p=Path(sys.argv[1]); rc=int(sys.argv[2]); api=int(sys.argv[3])
assert p.is_file(), 'AMUI04A_MISSING_HOSTED_DEVICE_RECEIPT'
receipt=json.loads(p.read_text())
assert rc == 0 and receipt.get('returncode') == 0, receipt
assert receipt.get('status') in ('success', 'passed'), receipt
assert int(receipt.get('executed', 0)) >= 5, receipt
assert int(receipt.get('passed', 0)) >= 5, receipt
assert int(receipt.get('failed', 1)) == 0, receipt
assert os.environ.get('GITHUB_SHA', '').strip(), 'AMUI04A_MISSING_EXACT_COMMIT'
receipt['amui04a_commit']=os.environ['GITHUB_SHA']
receipt['amui04a_api']=api
receipt['amui04a_scope']='device-rendered synthetic list + chips; light/dark/black palette'
p.write_text(json.dumps(receipt,indent=2)+'\n')
PYVISUAL
# Package is a debug variant; pictures use app-scoped storage, not other apps' data.
app_id="io.github.muntashirakon.AppManager.debug"
device_dir="/sdcard/Android/data/${app_id}/files/Pictures/amui04a"
shot_dir="$RUNNER_TEMP/amui04a-screenshots-api${api}"
mkdir -p "$shot_dir"
AMUI04A_EXPECT_SCREENSHOT_COUNT=3
for name in light dark pure-black; do
  adb pull "$device_dir/${name}.png" "$shot_dir/${name}.png"
  test -s "$shot_dir/${name}.png"
done
actual_count="$(find "$shot_dir" -maxdepth 1 -type f -name '*.png' | wc -l | tr -d ' ')"
[[ "$actual_count" == "$AMUI04A_EXPECT_SCREENSHOT_COUNT" ]] || {
  echo AMUI04A_SCREENSHOT_COUNT_REFUSED >&2; exit 1;
}
sha256sum "$shot_dir/light.png" "$shot_dir/dark.png" "$shot_dir/pure-black.png" \
  > "$RUNNER_TEMP/amui04a-screenshots-api${api}.sha256"
python3 -B - "$shot_dir" "$RUNNER_TEMP/amui04a-screenshots-api${api}.sha256" <<'PYIMAGE'
import hashlib,struct,sys
from pathlib import Path
folder,manifest=Path(sys.argv[1]),Path(sys.argv[2])
assert manifest.is_file(), 'AMUI04A_MISSING_SHA_MANIFEST'
hashes=set()
for name in ('light','dark','pure-black'):
    blob=(folder/(name+'.png')).read_bytes()
    assert len(blob)>1024 and blob[:8]==b'\x89PNG\r\n\x1a\n', 'AMUI04A_INVALID_PNG_'+name
    width,height=struct.unpack('>II',blob[16:24])
    assert width==1080 and 100<=height<=3200, 'AMUI04A_WRONG_SCREENSHOT_GEOMETRY_'+name
    digest=hashlib.sha256(blob).hexdigest()
    assert digest in manifest.read_text(), 'AMUI04A_SHA_MISMATCH_'+name
    hashes.add(digest)
assert len(hashes)==3, 'AMUI04A_DUPLICATE_PALETTE_SCREENSHOTS'
print('AMUI04A_SCREENSHOT_PNG_SHA256_PASS',3)
PYIMAGE
printf 'AMUI04A_HOSTED_VISUAL_PASS api=%s sha=%s\n' "$api" "$GITHUB_SHA"
# AMUI-04B: read-only 600-row stress, resizing, RTL and three viewport captures.
# The original AMUI-02/03C/04A gates above remain mandatory on API 35 and 36.
stress_report="$RUNNER_TEMP/amui04b-api${api}.json"
stress_log="$RUNNER_TEMP/amui04b-api${api}.log"
set +e
python3 -B -m devtool.android_instrumentation "$PWD" --target app \
  --class io.github.muntashirakon.AppManager.main.Amui04BViewportStressInstrumentedTest \
  --report "$stress_report" 2>&1 | tee "$stress_log"
stress_rc="${PIPESTATUS[0]}"
set -e
python3 -B - "$stress_report" "$stress_rc" "$api" <<'PYSTRESS'
import json,os,sys
from pathlib import Path
p=Path(sys.argv[1]);rc=int(sys.argv[2]);api=int(sys.argv[3])
assert p.is_file(),'AMUI04B_MISSING_HOSTED_RECEIPT'
receipt=json.loads(p.read_text())
assert rc==0 and receipt.get('returncode')==0,receipt
assert receipt.get('status') in ('success', 'passed'),receipt
assert int(receipt.get('executed', 0)) >= 6,receipt
assert int(receipt.get('passed', 0)) >= 6,receipt
assert int(receipt.get('failed', 1)) == 0,receipt
assert os.environ.get('GITHUB_SHA', '').strip(),'AMUI04B_NO_EXACT_SHA'
receipt['amui04b_commit']=os.environ['GITHUB_SHA']
receipt['amui04b_api']=api
receipt['amui04b_scope']='synthetic 600-row RecyclerView stress, narrow/wide/RTL evidence'
p.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
PYSTRESS
# Read only app-scoped screenshots; no package enumeration or external app access.
app_id="io.github.muntashirakon.AppManager.debug"
stress_device_dir="/sdcard/Android/data/${app_id}/files/Pictures/amui04b"
stress_shot_dir="$RUNNER_TEMP/amui04b-screenshots-api${api}"
mkdir -p "$stress_shot_dir"
AMUI04B_EXPECT_SCREENSHOTS=3
for scene in narrow wide rtl; do
  adb pull "$stress_device_dir/${scene}.png" "$stress_shot_dir/${scene}.png"
  test -s "$stress_shot_dir/${scene}.png"
done
shot_count="$(find "$stress_shot_dir" -maxdepth 1 -type f -name '*.png' | wc -l | tr -d ' ')"
[[ "$shot_count" == "$AMUI04B_EXPECT_SCREENSHOTS" ]] || {
  echo 'AMUI04B_BAD_SCREENSHOT_COUNT' >&2;exit 1;
}
sha256sum "$stress_shot_dir/narrow.png" "$stress_shot_dir/wide.png" "$stress_shot_dir/rtl.png" \
  > "$RUNNER_TEMP/amui04b-screenshots-api${api}.sha256"
python3 -B - "$stress_shot_dir" "$RUNNER_TEMP/amui04b-screenshots-api${api}.sha256" <<'PYPIXELS'
import hashlib,struct,sys
from pathlib import Path
folder,manifest=Path(sys.argv[1]),Path(sys.argv[2])
assert manifest.is_file(),'AMUI04B_SHA_MANIFEST_MISSING'
recorded={}
for row in manifest.read_text().splitlines():
    bits=row.split('  ',1)
    assert len(bits)==2,'AMUI04B_MALFORMED_MANIFEST'
    assert bits[1] not in recorded,'AMUI04B_DUPLICATE_HASH_ROW'
    recorded[bits[1]]=bits[0]
assert len(recorded)==3,'AMUI04B_HASH_COUNT_INCORRECT'
expected={'narrow':(720,1280),'wide':(1920,1200),'rtl':(720,1280)}
hashes=set()
for name,dimensions in expected.items():
    path=folder/(name+'.png')
    blob=path.read_bytes()
    assert len(blob)>2048 and blob[:8]==b'\x89PNG\r\n\x1a\n','AMUI04B_INVALID_PNG_'+name
    assert struct.unpack('>II',blob[16:24])==dimensions,'AMUI04B_GEOMETRY_DRIFT_'+name
    digest=hashlib.sha256(blob).hexdigest()
    assert recorded.get(str(path))==digest,'AMUI04B_SHA256_DRIFT_'+name
    hashes.add(digest)
assert len(hashes)==3,'AMUI04B_DUPLICATE_VIEWPORT_IMAGES'
print('AMUI04B_PNG_GEOMETRY_SHA256_PASS',3)
PYPIXELS
printf 'AMUI04B_HOSTED_VIEWPORT_PASS api=%s sha=%s\n' "$api" "$GITHUB_SHA"
# AMUI-04C: actual MainViewModel epoch/lifecycle races (no app package mutation).
# This executes only on the existing hosted API35/API36 full-device gate.
race_report="$RUNNER_TEMP/amui04c-api${api}.json"
race_log="$RUNNER_TEMP/amui04c-api${api}.log"
set +e
python3 -B -m devtool.android_instrumentation "$PWD" --target app \
  --class io.github.muntashirakon.AppManager.main.Amui04CLifecycleRaceInstrumentedTest \
  --report "$race_report" 2>&1 | tee "$race_log"
race_rc="${PIPESTATUS[0]}"
set -e
python3 -B - "$race_report" "$race_rc" "$api" <<'PYRACE'
import json,os,sys
from pathlib import Path
p=Path(sys.argv[1]); rc=int(sys.argv[2]); api=int(sys.argv[3])
assert p.is_file(), 'AMUI04C_MISSING_HOSTED_RECEIPT'
receipt=json.loads(p.read_text(encoding='utf-8'))
assert rc==0 and receipt.get('returncode')==0, receipt
assert receipt.get('status') in ('success','passed'), receipt
assert int(receipt.get('executed',0)) >= 7, receipt
assert int(receipt.get('passed',0)) >= 7, receipt
assert int(receipt.get('failed',1)) == 0, receipt
sha=os.environ.get('GITHUB_SHA','').strip()
assert len(sha)==40 and all(c in '0123456789abcdef' for c in sha), 'AMUI04C_NO_EXACT_SHA'
receipt['amui04c_commit']=sha
receipt['amui04c_api']=api
receipt['amui04c_scope']='real ViewModel publication epochs, rapid invalidation and immutable status; no package mutation'
p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('AMUI04C_HOSTED_RACE_PASS',api,sha)
PYRACE
# AMUI-04D: final read-only identity, package-event, list and semantic-theme acceptance.
# Existing AMUI-01 real disposable package lifecycle, AMT and AMUI04A/B/C gates precede it.
final_report="$RUNNER_TEMP/amui04d-api${api}.json"
final_log="$RUNNER_TEMP/amui04d-api${api}.log"
set +e
python3 -B -m devtool.android_instrumentation "$PWD" --target app \
  --class io.github.muntashirakon.AppManager.main.Amui04DFinalAcceptanceInstrumentedTest \
  --report "$final_report" 2>&1 | tee "$final_log"
final_rc="${PIPESTATUS[0]}"
set -e
python3 -B - "$final_report" "$final_rc" "$api" <<'PYFINAL'
import json,os,sys
from pathlib import Path
p=Path(sys.argv[1]);rc=int(sys.argv[2]);api=int(sys.argv[3])
assert p.is_file(),'AMUI04D_NO_DEVICE_RECEIPT'
receipt=json.loads(p.read_text(encoding='utf-8'))
assert rc==0 and receipt.get('returncode')==0,receipt
assert receipt.get('status') in ('success','passed'),receipt
assert int(receipt.get('executed',0))>=10,receipt
assert int(receipt.get('passed',0))>=10,receipt
assert int(receipt.get('failed',1))==0,receipt
sha=os.environ.get('GITHUB_SHA','').strip()
assert len(sha)==40 and all(c in '0123456789abcdef' for c in sha),'AMUI04D_NO_EXACT_SHA'
receipt['amui04d_commit']=sha
receipt['amui04d_api']=api
receipt['amui04d_scope']='read-only real installed debug app identity, exact package event parsing, immutable list, first resume, semantic palette'
p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('AMUI04D_HOSTED_FINAL_PASS',api,sha)
PYFINAL
