#!/usr/bin/env zsh
# Shared safe post-push qualification hook. Call after a successful exact-SHA
# targeted run. GitHub-only full matrix dispatches at the configured gate.
emulate -L zsh
setopt errexit nounset pipefail extendedglob
[[ $# -eq 1 && "$1" == [0-9a-f]## ]] || { print -ru2 -- 'AMUI_CI_POST_PUSH_REFUSED: expected exact commit SHA'; exit 1; }
readonly sha="$1"
[[ ${#sha} -eq 40 ]] || { print -ru2 -- 'AMUI_CI_POST_PUSH_REFUSED: SHA length'; exit 1; }
[[ -n "${TMPDIR:-}" && -d "$TMPDIR" && -w "$TMPDIR" ]] || { print -ru2 -- 'AMUI_CI_POST_PUSH_REFUSED: TMPDIR unavailable'; exit 1; }
[[ -f scripts/devtool/amui_ci_gate.py ]] || { print -ru2 -- 'AMUI_CI_POST_PUSH_REFUSED: not in AppManager root'; exit 1; }
[[ "$(git rev-parse HEAD)" == "$sha" ]] || { print -ru2 -- 'AMUI_CI_POST_PUSH_REFUSED: HEAD changed'; exit 1; }
readonly every="${AMUI_GATE_EVERY:-5}"
[[ "$every" =~ ^[0-9]+$ && "$every" -ge 1 && "$every" -le 30 ]] || { print -ru2 -- 'AMUI_CI_POST_PUSH_REFUSED: gate cadence must be 1..30'; exit 1; }
python3 -B scripts/devtool/amui_ci_gate.py --record "$sha" --gate-every "$every" --repo "$PWD"
