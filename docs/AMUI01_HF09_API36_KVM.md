# AMUI-01 HF09 — API36 KVM node accessibility

## Observed hosted failure

GitHub Actions 42658012012, job 129301956412: all four other jobs pass. API36 setup emits `KVM inaccessible for API36 emulator` after installing the pinned Android SDK and Devtool; no lifecycle test runs and mandatory receipts are missing.

## Fix

Preserve the accelerated API36 emulator, strict `/dev/kvm` character-device existence check, and mandatory lifecycle receipts. On ephemeral hosted Linux runners, udev rules can take effect late or leave a preexisting `root:kvm 0660` node that the current job user cannot open. After `udevadm trigger`, explicitly `sudo chmod 0666 /dev/kvm`, print before/after mode and current identity, then require shell read/write. Do not fall back to slow unaccelerated emulation and do not relax acceptance/receipt checks. The earlier API35 instrumentation job is unchanged.

The existing source-pinned GitHub Actions push, commit and PR watcher is updated for this one patch. It reuses PR #1 to `feature/tasker-automation`, never force-pushes, never automatically merges, and stores temporary PR content in `$TMPDIR`.

## Status

Static contract and isolated mutation checks can pass offline. Real KVM qualification requires the next GitHub-hosted workflow; this change does not assert that KVM always exists on every GitHub runner.

## HF09 HF01 validation fix

Scope all KVM negative-test mutations to the API36 job. The API35 job also contains an identical device-character guard; changing the first global match leaves API36 unchanged and produces a false negative. The fixture and regression suite now explicitly require both guards. No production source, SDK, hardware acceleration, or receipt requirements were weakened.
