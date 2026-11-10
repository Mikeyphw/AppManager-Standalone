# AMUI-03B HF04 — source-pinned stale mutation regression repair

- Repo: `Mikeyphw/AppManager-Standalone`, PR #4, feature branch `feature/amui03b-responsive-list-20261109`.
- Parent SHA: `6f01348df9ce34f2c3bd2ad5a863c681f9593477`. Original `scripts/devtool/test_amt04_contract.py` Git blob: `2cf9a2591c459035b3a0c22a3bdf709f2ee16105`, SHA-256: `abff5f5a69e7bdfe9f73d1582bc2f264de63392c8f5206749786129cf4027d64`.
- New test SHA-256: `cbb7016db8022d6d5e7dbf0e38bb30b35e88930d75a93721289c1dde2d1c149d`.
- The former `test_hosted_instrumentation_push_scope` tried to remove an already-deleted full workflow path entry. The string replacement did nothing; the contract correctly passed, causing the unit test to fail.
- Replace it with a mutation of the real targeted workflow `app/src/(main|androidTest)/` regex, with assert-exactly-one anchor before replacement.
- All other AMT-04A mutation tests now use the same fail-closed mutation helper (no silent no-op); add targeted AMT-04 invocation removal, full source invocation removal, positive manual-full/feature-target checks, and a regression proving removed legacy anchors are rejected.
- Keep the production checker, Java sources, manifests, actual GitHub workflows and all other existing source/security contracts unchanged.
- The full 5/5 gate remains manual-only, unreconciled, pending the next exact SHA targeted source gate and downstream hosted Android 15/16 qualification. No sixth overlay, no auto merge.
- The launcher checks PR #4, source blobs and clean worktree, runs Devtool, pushes without force, verifies targeted CI, and uses the existing guarded `amui_gate_retry.py` to continue the failed fifth gate only after success.
- This delivery was authored from GitHub HEAD `6f01348df9ce34f2c3bd2ad5a863c681f9593477`; direct GitHub write access returned HTTP 403, so it has **not** been applied to the remote repository.
