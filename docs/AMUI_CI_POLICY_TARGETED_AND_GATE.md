# AppManager AMUI CI — Targeted-by-default, full qualification every 5 overlays

## Exact migration
- Source GitHub SHA: `2351dfbded6a13d3995d1ffb82e26f6927d931e3` (`feature/amui02-global-material-you-20261109`).
- Existing heavy workflow `.github/workflows/devtool-tasker-ci.yml` is **manual dispatch only**. No push, PR, or merge event may start full Gradle/lint/Android 15/16 acceptance.
- New `.github/workflows/amui-targeted-ci.yml` runs once per AMUI feature-branch push at the **exact source SHA** and once on base-branch merges; same-repo PR events are skipped (fork PRs get real checks). It runs source checks. It runs GitHub-hosted Java/resource/AndroidTest **compilation** only when corresponding app/resources/build files change.
- For standalone feature branches without an open PR, manually dispatch targeted CI using `gh workflow run amui-targeted-ci.yml -R Mikeyphw/AppManager-Standalone --ref <branch> -f focus=auto` (manual auto scope only on PR/push; use `-f focus=compile` when you need compilation before opening PR).
- Gate default: **5 applied overlays**. Override to other X (1..30) with `--gate-every X` only on a fresh state or after manually migrating the counter.

## After each new overlay commit is pushed
```
python3 -B scripts/devtool/amui_ci_gate.py --record "$(git rev-parse HEAD)" --gate-every 5
```
This increments local `$HOME/.local/state/appmanager-ci/overlay-gates.json` **once per exact SHA** and dispatches `mode=full` only when the counter reaches 5. Integrate this one command into the **future** apply-push scripts, after verifying remote SHA. An old already-published apply kit will not be changed remotely by this overlay.

To inspect the counter: `python3 -B scripts/devtool/amui_ci_gate.py --status`.
After all five required full jobs have succeeded, record the run and reset the counter via `python3 -B scripts/devtool/amui_ci_gate.py --ack-run <run-id>`.

**Do not merge/release while a required full gate is failed, pending or skipped.** The counter is a local convenience; branch protection and human qualification remain authoritative. Prefer a full manual gate immediately for security-sensitive or high-risk changes and before release, regardless of overlay count.

## Existing regression protections retained
The source-contract job, Tasker disposable fixture, Android 15 KVM/runtime, Android 16 KVM/runtime, lint baseline/report enforcement, AMUI-01 app lifecycle and AMUI-02 theme tests are not reduced or deleted. The mandatory full suite still runs in its entirety when `mode=full` is explicitly dispatched:
```
gh workflow run devtool-tasker-ci.yml -R Mikeyphw/AppManager-Standalone --ref feature/amui02-global-material-you-20261109 -f mode=full
```

## Decommission
The targeted workflow and helper can be removed after UI development. If restoring automatic full CI in the future, update the changed CI contract checkers and their mutation tests at the same time. Do not silently re-enable heavy matrix triggers.

## Note about current qualification
At `2351dfbded6a13d3995d1ffb82e26f6927d931e3`, a hosted Gradle build passed but Android 15/16 instrumentation did **not** pass: the latest full run failed when compiling `Amui02ThemeInstrumentedTest.java` (line 76). This CI-policy overlay does not repair that test bug, and it **must not** be interpreted as AMUI-02 qualification.
