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
