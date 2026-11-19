# Installer: optional original APK cleanup (ported)

This feature was ported **without rewriting its 16 reviewed application/test
files** from `Mikeyphw/AppManager` branch `feature/appmanager-delete-original-apk-20261117-audited` at
`c11a4a709dd3115ae45ecf6c66d9f36b2150ee71` (Git tree `f23b1732e7f700ae3fad06f7e0b0f5a644149771`), into
`Mikeyphw/AppManager-Standalone` based on `feature/tasker-automation` at
`a7366a34c74bc7c52b6db5729a9d8ef7162b9893` (Git tree `171a10f339e9bdc83341f7c904993950a92f81f8`).

The original installer feature enables an opt-in setting and an install-dialog
switch to delete a user-selected original `.apk`, `.apkm`, `.apks` or `.xapk`
only **after a successful installation**. Failure, non-user-selected and
install-existing flows must never delete source. URI propagation, queue
alias/deferred deletion, external-storage safety and provider deletion checks
are covered by the imported Robolectric tests. Null/missing MIME type JSON
is handled by the previously hosted-qualified fix.

No UI/Tasker/AMUI03B files outside the 16 exact installer changes are replaced.
The three inherited Tests/Lint/CodeQL workflows gain dispatch, exact
feature-branch push eligibility and checkout commit-attestation; **scheduled
CodeQL analysis is retained**. The separate Standalone targeted CI already
matches `feature/amui*` so it runs source contracts and hosted Android compile
on this port branch without changing its scheduling or skipping source tests.
The Devtool Tasker Android CI deliberately remains dispatch-only because its
existing safety contracts prohibit automatic device jobs on arbitrary pushes.

## Acceptance

Use the native Devtool durable session receipt to check the exact committed
PR HEAD. Hosted targeted compilation, JVM Tests, Lint and CodeQL automatically
run on a push to the exact port branch. The separate full Android/Tasker
emulator workflow is not silently skipped: after PR creation, dispatch it on
the exact port HEAD with:

```zsh
gh workflow run devtool-tasker-ci.yml -R Mikeyphw/AppManager-Standalone --ref feature/amui-installer-original-apk-port-20261118 -f mode=full
```

Verify all exact-SHA job and artifact receipts. Test the installer using only
disposable APK files, including install success, failure, shared source,
provider-denied and opt-out paths before release. No local Termux Gradle,
privileged deletion of valuable files, automatic merge or release qualification
is implied.
