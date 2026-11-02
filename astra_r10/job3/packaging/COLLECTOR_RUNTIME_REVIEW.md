# Runtime312 and regression collection — UNPROVEN

The prior reviewed collector is preserved unchanged as
`prepare_job3_pack.FE30-reviewed.py`, SHA256
`fe30f3e3f5a590ea966ce1b2f44066caecf8d1d5bc56cd1643993e771928f497`.

The extension pins the new isolated runtime manifest
`a8d8325cd5d6216477c26da3638fe976b7e784b5ead7277c67692e0211a9b461`,
wheel lock `ef9dcb6af1e3e64b9d2bbdbcf2eeac7480f9864a56b5bd96cad1741c50ac9a90`
and bootstrap receipt
`f9bba4329df2c6e99e1e65c6170b2683248ef86c1d1767901d71746fca2c4b3e`.
It adds original metadata/source URL receipts and installation logs; bulk
packages, wheels and the installed interpreter remain at their retained D paths.
The record distinguishes assembly from subsequent native qualification.

Each explicitly listed regression attempt contributes its original result or
failure, CPU_RUNTIME, source/runtime/toolchain bindings, command and runtime
JSON receipts when present. Native launcher logs and failed preflight receipts
already reside in the branch evidence tree and remain included. Execution
cache/temp/pycache/pytest-temp contents are hashed and inventoried after exit,
then rechecked before collection finishes. Generated code, DLLs and test data
remain outside the pack and Forge source. Unknown output names require review.

Independent reviewer `proof_contract` found one concrete association gap: a
primary suite report could have been paired with an unrelated successful
preflight receipt. The fix requires the primary report's exact listed attempt
launcher path and SHA256; PASS additionally requires that same launcher's native
exit0. PASS also requires at least73 collected/passing tests, zero failures or
skips, zero training loops/optimizer updates, and unchanged bound NPT, compiler
and isolated-runtime inputs. Failure records remain failures.

The focused static recheck closed at collector SHA256
`82955218e1f1961e5eed6c6596d3fa8d3165af79a9473ca52b15655dff8c6b7c`.
Eight focused synthetic fixtures are prepared in `test_collector_runtime.py`.
At this checkpoint they are NOT_RUN, because the native regression suite owns
both permitted cores. No collector or pack preparation has executed.

Next after the native worker releases CPU3: obtain a fresh inspected quiet pair,
then run `powershell -NoProfile -File
D:/a10/wt/astra_r10/job3/packaging/run-runtime-integration-fixtures.ps1 -RunId 01`.
Record the original launcher output and reviewer evidence closure before the
root publishes its final input receipt and runs the collector.

Completed fixture milestone: eight tests PASS, zero skips, at final collector
SHA256 `5a491d01ebf2ca1300dc35699fbcc9deb2d9e6ff67b75fcfb7dd121e154738da`.
The final small change explicitly permits the new D-only `pytest.log` artifact;
the failure-preservation fixture verifies that the log is shipped while generated
cache code is only inventoried. Original receipts are in
`runtime-integration-01-launch/`; native exit0 at2026-11-02T08:52:29.9181155Z,
Idle CPU3, one worker, no capture errors or disk-floor breach. The separately
inspected admission pair was CPU3 14.0 then15.6%, host79.8375 then81.08125%, in
`sealer-tests-collectorload01-launch/`. CPU3 was released before suite02.

The reviewer confirmed all eight original results, closed the log-artifact
addition and found no unresolved issue. Native collection still requires root's
final input/review receipt after the native suite exits. Include preflight01,
suite01 (infrastructure FAIL, zero tests) and each subsequent completed attempt;
bind the final suite report to its own launcher. No collector execution has
occurred as part of these fixtures.
