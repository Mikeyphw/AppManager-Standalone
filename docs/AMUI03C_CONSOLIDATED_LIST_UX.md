# AMUI-03C — consolidated app-list UX and hosted UI acceptance

Exact preimage: `c2a27476c637f702263614707d3b25108781480d`. AppManager Standalone PR #4 remains **open and unmerged**.
Previous 5/5 full qualification: GitHub Actions `42751712942` at exact same SHA; the prior gate is qualified. This is **new overlay 1/5**, never retarget or acknowledge that historical gate.

## Integrated changes

- One scrollable Material 3 quick-filter bar (using `android:checkable`, not the invalid `app:checkable`): All filters, User, System, Frozen, Backed up, More filters, Compact/Detailed.
- Filters operate on the existing `MainViewModel` flags and the serialized filter executor. User and System are exclusive when selected from quick chips; other advanced bits persist. All filters clears flag/profile/user scope but **not search or sort**, which remain user-controlled. Profile/advanced activity is visible in the More filters label.
- Explicit `shown/total` indicator; responsive list stays on the current tested 480dp auto-span manager. Existing toolbar search, regex, refresh and selection controls stay intact.
- Compact default hides date, UID, SDK, signature and long backup text, retaining icon, label, package ID, version, user/system and backup indication. Detailed mode restores the existing metadata fields with **data-dependent visibility**, persistent through activity recreation via private activity preferences.
- Row click always fetches the current adapter position; long-press, icon selection, stable IDs, stroke colors, batch operations, Tasker and package lifecycle are untouched.
- Source contracts + 26 mutation/positive tests on targeted and full CI, fail-closed stale anchors; hosted UI smoke tests on **both API 35 and API 36** via the existing themed emulator runner and exact JSON receipts. Existing full workflow remains manual only.

## Verification classification

- Offline: pin/manifest/Python+XML syntax and mutation checks via source-only tests (no local Gradle).
- Hosted: targeted source and scoped resource/Java compile **required after push**. Exact API35/API36 UI receipts and the complete 5-job full gate need an explicit manual full run later; source tests alone are not Android acceptance.
- Never update the historical lint baseline or auto-merge PR #4. Pending task after this overlay: AMUI-04 wider screen-by-screen visual and interaction qualification, then resume Tasker AMT-06C2/06D.
