#!/usr/bin/env bash
# Hosted/disposable emulator only. No local Gradle, user apps, or real work profiles.
set -Eeuo pipefail
: "${RUNNER_TEMP:?GitHub-hosted runner required}"
: "${JAVA_HOME:?Host JDK21 required}"
: "${GITHUB_SHA:?Exact source SHA required}"
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd -- "$repo"
api="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
[[ "$api" == 30 || "$api" == 35 || "$api" == 36 ]] || { echo 'AMUI05_WRONG_API' >&2; exit 1; }
[[ "${AMUI05_EXPECT_API:?}" == "$api" ]] || { echo 'AMUI05_API_DRIFT' >&2; exit 1; }
# A single unused disposable emulator is the only authorized target for wallpaper writes.
hardware="$(adb shell getprop ro.hardware | tr -d '\r')"
[[ "$hardware" == ranchu || "$hardware" == goldfish ]] || { echo 'AMUI05_NOT_A_DISPOSABLE_EMULATOR' >&2; exit 1; }
original="$(mktemp "$RUNNER_TEMP/amui05-devtool.XXXXXXXX.toml")"
cp -- .devtool.toml "$original"
trap 'cp -- "$original" .devtool.toml; rm -f -- "$original"' EXIT
python3 -B scripts/devtool/amt03_hosted_config.py .devtool.toml --java-home "$JAVA_HOME"
accept() {
  local class="$1" key="$2" minimum="$3"
  local receipt="$RUNNER_TEMP/amui05-${key}-api${api}.json"
  local log="$RUNNER_TEMP/amui05-${key}-api${api}.log"
  rm -f -- "$receipt" "$log"
  set +e
  python3 -B -m devtool.android_instrumentation "$PWD" --target app \
    --class "$class" --report "$receipt" 2>&1 | tee "$log"
  local rc="${PIPESTATUS[0]}"
  set -e
  python3 -B - "$receipt" "$rc" "$api" "$GITHUB_SHA" "$minimum" "$key" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);rc=int(sys.argv[2]);api=int(sys.argv[3]);sha=sys.argv[4];minimum=int(sys.argv[5]);kind=sys.argv[6]
assert p.is_file(), 'AMUI05_MISSING_REAL_INSTRUMENTATION_RECEIPT'
r=json.loads(p.read_text())
assert rc==0 and r.get('returncode')==0, r
assert r.get('status') in ('passed','success') and r.get('cleanup_status')=='passed',r
assert int(r.get('executed',0))>=minimum and int(r.get('passed',0))>=minimum,r
assert int(r.get('failed',1))==0 and int(r.get('skipped',1))==0,r
assert r.get('device_serial')=='emulator-5554','AMUI05_WRONG_DEVICE'
assert len(sha)==40 and all(c in '0123456789abcdef' for c in sha),'AMUI05_SHA_MALFORMED'
r['amui05_exact_sha']=sha;r['amui05_api']=api;r['amui05_class']=kind
p.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print('AMUI05_RECEIPT_PASS',kind,api,sha)
PY
}
accept io.github.muntashirakon.AppManager.utils.appearance.Amui05CompatibilityInstrumentedTest compatibility 7
if [[ "$api" == 35 || "$api" == 36 ]]; then
  # Mutates wallpaper only on this throwaway CI emulator. Do not run on a phone.
  accept io.github.muntashirakon.AppManager.utils.appearance.Amui05WallpaperInstrumentedTest wallpaper 2
fi
python3 -B - "$RUNNER_TEMP/amui05-scope-api${api}.json" "$api" "$GITHUB_SHA" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'api':int(sys.argv[2]),'sha':sys.argv[3],
 'hardware':'disposable-emulator-only','compatibility_tests':7,
 'wallpaper_tests':2 if int(sys.argv[2])>=35 else 0,
 'whole_app_visual_parity':'NOT_CLAIMED',
 'physical_arm64':'NOT_CLAIMED','real_work_profile':'NOT_CLAIMED'},sort_keys=True,indent=2)+'\n')
PY
printf 'AMUI05_HOSTED_COMPATIBILITY_PASS api=%s sha=%s\n' "$api" "$GITHUB_SHA"
