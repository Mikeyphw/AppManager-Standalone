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
