# AppManager-Standalone signed Android APKs

All **distributed** debug/release APK artifacts must be signed, verified with
`apksigner`, bound to the source commit and validated against the certificate
loaded from a protected GitHub Actions environment. Never publish an unsigned
release, an APK signed with the old repository debug identity, or an unverified
fixture as an app release.

## GitHub Secrets and environments

Set four separate names in each of the protected `debug-signing` and
`release-signing` environments (not the repository-level secret namespace):

- Debug: `AM_DEBUG_KEYSTORE_B64`, `AM_DEBUG_KEY_ALIAS`,
  `AM_DEBUG_STORE_PASSWORD`, `AM_DEBUG_KEY_PASSWORD`.
- Release: `AM_RELEASE_KEYSTORE_B64`, `AM_RELEASE_KEY_ALIAS`,
  `AM_RELEASE_STORE_PASSWORD`, `AM_RELEASE_KEY_PASSWORD`.

Environments must be restricted to trusted branches. Protect `release-signing`
with required reviewers and a narrow deployment-branch rule. These settings
cannot be established or independently proven by a source checkout: an owner
must confirm them in GitHub Settings before trusting the release workflow.
GitHub-hosted jobs use a private `RUNNER_TEMP` keystore and do not commit or
upload it. Failed/missing secrets or wrong certificate identities fail closed.

## Workflows

- `.github/workflows/devtool-tasker-ci.yml`: full Android acceptance by
  explicit `workflow_dispatch` (`mode=full`) at the exact PR commit; the hosted build signs app
  debug APKs with `debug-signing` and verifies every APK before artifact upload.
  Android 15/16 instrumentation remains separate device evidence.
- `.github/workflows/amui-targeted-ci.yml`: required CI runs the entire
  `scripts/devtool/test_*.py` regression suite, not just selected source checks.
  PR compilation eligibility compares the PR base to its actual head so a
  source-only follow-up does not conceal prior Java/resource/test changes.
  Push-only checks may remain incremental for efficiency.
- `.devtool.toml` `ci-full` dispatches the `feature/tasker-automation` **base**.
  It is not a PR-head acceptance shortcut. Qualify the current PR with explicit
  `gh workflow run devtool-tasker-ci.yml -R Mikeyphw/AppManager-Standalone
  --ref feature/amui-installer-original-apk-port-20261118 -f mode=full`, after
  checking that GitHub reports the expected exact head SHA. The runtime's
  source-bound Devtool session is the authority for required-CI qualification.

- `config/delivery-required-ci.json`: native Devtool required PR checks on
  `feature/tasker-automation`, with exact verified GitHub IDs for Targeted CI,
  Tests, Lint, and CodeQL. The targeted source gate is now executed for
  same-repository pull requests; no skipped PR job is accepted as a pass.
  All four checkout the actual PR head, not GitHub's synthetic merge commit.
  Native CI observation remains separate from the manually dispatched full
  Android 15/16 device acceptance and release-signing approval.
- `.github/workflows/appmanager-signed-apks.yml`: explicitly dispatched signed
  debug/release APKs. Release dispatch needs `release-signing` approval. A new
  workflow must be present on the GitHub default branch before ordinary manual
  workflow_dispatch is reliably available; do not treat an absent dispatch UI
  as a pass.
- Tests/lint/CodeQL are separate source/compile gates; they do not publish
  unsigned APKs. CodeQL compiles debug Java rather than requesting all variants.
- `amt06c-fixture` builds a disposable Android-debug-signed test fixture; it is
  not a distributed application APK or the protected app signing identity.

**Local debug builds** use Android's normal auto-signed debug keystore when
`AM_SIGNING_VARIANT` is unset; Gradle's `app/dev_keystore.jks` and its public
password are no longer used. That old tracked file should be retired through a
separate authorized native deletion once deletion support is reviewed. Never
rely on it as a private identity. **Local release packaging without the
protected release identity is rejected** by Gradle. The release artifact
signature gate matches only distributable `assemble/package/bundle` release
APK/AAB tasks (including product flavors and universal APKs). It does **not**
reject Android Gradle Plugin intermediate tasks such as `packageReleaseResources`,
`packageReleaseAssets`, `bundleReleaseClassesToRuntimeJar`, or
`packageReleaseUnitTestForUnitTest`, which are dependencies of unit tests or
lint and never publish an unsigned release artifact. `./gradlew test` must execute debug and release unit tests without
creating or publishing a distributable unsigned release APK.

## Acceptance

Verify GitHub Actions job/environment approval, SHA, `apksigner verify`,
certificate SHA-256 fingerprint, SHA-256 checksum manifest and artifact
contents for all produced ABI/universal outputs. The GitHub Actions workflow
is not itself proof that production signing was approved. Preserve the release
keystore offline; losing it may prevent application updates.
