#!/usr/bin/env python3
"""HF09 scoped KVM runner hardening contract; no local Gradle."""
import argparse
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WORKFLOW=ROOT / '.github/workflows/devtool-tasker-ci.yml'
WATCHER=ROOT / 'scripts/devtool/amui_apply_push_pr_watch.zsh'
JOB_MARKER='  amui01-android16:\n'

def split_api36_job(workflow):
    """Return only the original API36 job, excluding all subsequent jobs.

    Additional acceptance-matrix jobs must never satisfy or duplicate the
    API36 KVM and receipt guard. This also makes older negative tests target
    the right phase as the YAML grows.
    """
    assert workflow.count(JOB_MARKER)==1, 'HF09_REFUSED: API36 job missing/duplicated'
    before, tail = workflow.split(JOB_MARKER, 1)
    boundary = re.search(r'(?m)^  [A-Za-z][A-Za-z0-9_-]*:[ \t]*$', tail)
    if boundary:
        return before, tail[:boundary.start()], tail[boundary.start():]
    return before, tail, ''

def validate(workflow=None, watcher=None):
    workflow=WORKFLOW.read_text(encoding='utf-8') if workflow is None else workflow
    watcher=WATCHER.read_text(encoding='utf-8') if watcher is None else watcher
    _, api36, _ = split_api36_job(workflow)
    before = 'sudo udevadm trigger --name-match=kvm'
    grant = 'sudo chmod 0666 /dev/kvm'
    after = 'test -r /dev/kvm && test -w /dev/kvm'
    assert api36.count(before)==1, 'HF09_REFUSED: API36 device rule trigger absent'
    assert api36.count(grant)==1, 'HF09_REFUSED: API36 KVM chmod absent or duplicated'
    assert api36.count(after)==1, 'HF09_REFUSED: API36 KVM fail-closed check absent'
    assert api36.index(before)<api36.index(grant)<api36.index(after), 'HF09_REFUSED: KVM grant is not before fail-closed check'
    assert api36.count("stat -c '%a %U:%G %n' /dev/kvm")==2, 'HF09_REFUSED: missing before/after device permissions diagnostics'
    assert 'if [[ ! -c /dev/kvm ]]' in api36, 'HF09_REFUSED: KVM device absence gate missing'
    assert 'api-level: 36' in api36 and "disable-linux-hw-accel: 'false'" in api36, 'HF09_REFUSED: API36 x86_64 acceleration weakened'
    assert 'script: AMUI01_EXPECT_API=36 bash scripts/devtool/amui01_hosted_instrumentation.sh' in api36, 'HF09_REFUSED: API36 acceptance replaced'
    assert api36.count('if-no-files-found: error')==1 and 'if-no-files-found: warn' not in api36, 'HF09_REFUSED: API36 receipt gate weakened'
    assert "inputs.mode == 'full' || inputs.mode == 'instrumentation'" in workflow, 'HF09_REFUSED: API35 Tasker mode gate removed'
    assert 'disable-linux-hw-accel: false' in workflow, 'HF09_REFUSED: API35 acceleration removed'
    assert 'python3 scripts/devtool/check_amui01_hf09_kvm.py --check' in workflow, 'HF09_REFUSED: hosted source contract not registered'
    assert 'git push origin "$BRANCH"' in watcher and 'gh run watch' in watcher and 'gh pr checks' in watcher, 'HF09_REFUSED: unattended push/PR watch lost'
    assert 'readonly EXPECTED_SHA="cf8dd9522991fcdf5c0027e58e4eee205985fc09"' in watcher, 'HF09_REFUSED: watcher source pin mismatch'
    assert 'git push --force' not in watcher and 'gh pr merge' not in watcher, 'HF09_REFUSED: unsafe GitHub action'
    assert '[[ -n "${TMPDIR:-}"' in watcher and 'mktemp "$TMPDIR/' in watcher, 'HF09_REFUSED: TMPDIR-only temp policy lost'
    return True

if __name__ == '__main__':
    argparse.ArgumentParser().add_argument('--check', action='store_true')
    validate()
    print('AMUI01_HF09_KVM_SOURCE_PASS')
