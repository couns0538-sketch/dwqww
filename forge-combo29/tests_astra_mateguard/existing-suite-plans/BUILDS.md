# Existing suite: native build completion

Compiled sequentially in the cloud VM; one compiler at a time. No tests or equality searches were launched by this build task. No engine source, existing tests, CMake, refs or root state was changed.

| Mode | Compile/link commands passed | Executables | Helper objects |
|---|---:|---:|---:|
| enabled | 50/50 | 47 | 3 |
| asan | 50/50 | 47 | 3 |

Zero failed or incomplete builds; nothing remains to compile in these two plans. Compiler batch1 ran 2026-11-14T20:53:36.808Z to 2026-11-14T20:58:37.254Z; batch2 ran 2026-11-14T20:58:42.514Z to 2026-11-14T20:58:46.783Z. These times are execution records only. The task finished before its25minute bound and never reached the2GiB disk stop threshold. Final free space: 3899867136bytes.

Every command used `/workspace/work/r4-run/execute-suite-step.mjs MODE builds ID`; its concrete compiler argv, actual stdout/stderr, exit, signal and hashes are under `/workspace/work/r4-run/existing-suite-MODE/logs/`. The outer sequential controller imposed132second timeout plus2second kill allowance per executor command; compiler entries themselves use120second timeout plus2second kill allowance. The controller was split into two commands, each below8minutes.

`build-manifest.json.txt` identifies every artifact and log hash. `build-progress.json.txt` preserves the per-command invocation/result records and before-build fingerprint of 99 engine/test/CMake files; those fingerprints were verified unchanged after both batches and again for this final manifest. Binary and helper object files stay in VM scratch and must not be committed.

The prepared plans have59 runtime/check entries per mode. Successful compilation does not establish that those tests pass or that sanitizers are clean at runtime. Root owns execution and reporting of each unchanged test, including historical fixture failures.
