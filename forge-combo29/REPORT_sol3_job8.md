# sol3 — Job 8 fused v3 refresh checks

**Step 0 passed.** The assigned Carbon2 patch at `8a70ec514de022e6873c55b8ae29529f2c5f763e` matched SHA-256 `7989b1954ec7a101473c7da05ef9e0f3506a29866e21783a8de31044a367e65f`. It applied to the k11 scratch tree with `patch -p1 -F0` and no offset, fuzz or reject. k11, k11f and net768 matched their assigned hashes. k11v built to `a9d4eef3de37cf74611c59a2f35b64f205cf95b7463e65554271e64d1ce01c80`. The PC20 benches ran with active net768 checksum `30ab43b4ba5db5f3`. [Input check](sol3/job8/stage0/input_hashes.txt) · [Patch receipt](sol3/job8/stage0/patch_apply.txt) · [Build](sol3/job8/stage0/build_v.txt) · [Bench readback](sol3/job8/stage0/verified/pins.txt)

| Build | Default bench 11 | Default bench 13 | Default perft 5 | PC20 net768 bench 11 | PC20 net768 bench 13 |
| --- | ---: | ---: | ---: | ---: | ---: |
| k11 | 312866 | 862329 | 4865609 | 882074 | 4275906 |
| k11v | 312866 | 862329 | 4865609 | 882074 | 4275906 |

**Prediction grade.** All seven warm-workload numbers matched for both k11v builds. The unplanted verifier exited 0 with zero mismatches, and C1, C2 and C3 stopped where predicted in the workload, at game 0, game ply 8. The forecast for internal evaluation ply held for C1 and C3. C2 failed at internal ply 1, two plies earlier than forecast. Both 50000-node cells matched all 389 rows, as forecast. The separately pushed prediction is `c1c319961256080110a3052370546291b186ef69`. [Prediction](sol3/job8/prediction.txt) · [Stamps](sol3/job8/stamps.txt)

### Step 1 warm workload on k11v

I used the Job 6 driver unchanged for 60 games with PC20, one thread, Hash 16 MiB, default MultiPV 1, net768, seed 20261117, eight opening plies, a 300-ply maximum and `go softnodes 2000` with hard cap 8000. k11v matched the k11 pins and every saved k11 search row in the game, ply, position, bestmove, last-iteration nodes and score, final nodes, and terminal status fields. The observer used in Step 2 also preserved all of those fields. [Exact command and hashes](sol3/job8/step1/run.meta) · [Baseline comparison](sol3/job8/step1/first_difference.json) · [Driver and independent readback](sol3/job8/step1/gate.txt)

| Build | Searches | Last-iteration nodes | Legacy trace | Terminal fallbacks | Final sum | At 8000 | Final trace |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| k11, Job 6 baseline | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |
| k11v | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |
| k11v with verify flag | 8612 | 29333343 | `5c705841c3ea17b4` | 42 | 35918624 | 971 | `5356dbb3a5f1bee3` |

### Step 2 v3 verification and planted controls

With `-DFORGE_NNUE_V3_VERIFY=1`, `Worker::static_evaluate_v3` compares its result with the fresh scalar reference in `src/search.cpp:3806`. All four arms used the same warm workload and active AVX-512 net768 as Step 1. The unplanted verifier returned **engine exit 0** and **zero** `V3 VERIFY FAILED` lines. Its seven pins and all timed search rows matched Step 1. Its executable SHA-256 was `83610e28d0573517f6c9e8a8adb113826baad722d9d20577488807e6d63d3707`. [Compiler invocation](sol3/job8/step2/verify/verify_compile.txt) · [Build](sol3/job8/step2/verify/build.txt) · [Independent readback](sol3/job8/step2/verify/gate.txt) · [Row comparison](sol3/job8/step2/verify/first_difference.json)

| Arm | Changed exactly one line in | Engine exit | Failure lines | First game | Game ply | Evaluation ply | Search path / reference |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| [C1](sol3/job8/step2/C1/gate.txt) | [Fused refreshed-side tail](sol3/job8/step2/C1.patch.txt) | 3 | 1 | 0 | 8 | 3 | 845 / 946 |
| [C2](sol3/job8/step2/C2/gate.txt) | [Fused updated-side first column](sol3/job8/step2/C2.patch.txt) | 3 | 1 | 0 | 8 | 1 | 576 / 927 |
| [C3](sol3/job8/step2/C3/gate.txt) | [Full refresh four-at-a-time additions](sol3/job8/step2/C3.patch.txt) | 3 | 1 | 0 | 8 | 0 | -176 / 339 |

All three stopped in the untimed opening-0 warm-up, before any timed search row. The verifier's printed ply is the depth of the evaluated position relative to that root. The linked gate files contain the first failure line verbatim and the outstanding root command. The driver diff records every UCI output line and the actual child exit separately. [Observer diff](sol3/job8/step2/driver_verify.patch.txt) · [Independent raw-output checker](sol3/job8/step2/check_verify.py)

### Step 3 cold hard-node labels

k11vf used k11v plus the exact Job 5 final-node probe. The probe applied with no offset, fuzz or reject. k11vf SHA-256 was `caee26f53848c80917010be3774d131ab5059babbe8d57fc89e80d1e80bf0966`. For each net, the Job 7 harness restarted per cell and reset between the same 389 fixture FENs. PC20, Threads 1, Hash 16 MiB, MultiPV 1, and `go nodes 50000` were held fixed. Final count, bestmove and last-iteration score matched saved k11f on every row. [Probe build hash](sol3/job8/step3/build_vf.sha256.txt) · [Pairwise comparison](sol3/job8/step3/check_cold.py)

| Cell | Net | Equal final-count, move and score rows | k11f at 50000 | k11vf at 50000 |
| --- | --- | ---: | ---: | ---: |
| [B2](sol3/job8/step3/B2/gate.txt) | Embedded AL1 s198 | 389/389 | 389 | 389 |
| [N2](sol3/job8/step3/N2/gate.txt) | Standalone net768 | 389/389 | 389 | 389 |

## Facts

- I built with CMake 4.2.3 Release, GCC 14.2.0 and Debian libstdc++ from GCC 14.2.0-19, using the earlier k11 flags and `-march=x86-64-v4`. Each verifier arm added exactly `-DFORGE_NNUE_V3_VERIFY=1`. [Ordinary build](sol3/job8/stage0/build_v.txt) · [Verifier build](sol3/job8/step2/verify/build.txt) · [C1 build](sol3/job8/step2/C1/build.txt) · [C2 build](sol3/job8/step2/C2/build.txt) · [C3 build](sol3/job8/step2/C3/build.txt)
- The Step 0 runner initially opened the diagnostic stream in write-only mode. Its readback stopped before the PC20 numbers. The rerun enabled readback and preserved both attempts. A Git transport authentication failure required publishing the first checkpoint with the connector. The remote tree matched the local tree, and Git pushed the corrected check and prediction before Step 1. [Original diagnostic](sol3/job8/stage0/pins.stderr.txt) · [Corrected readback](sol3/job8/stage0/verified/pins.txt) · [Tree comparison](sol3/job8/step1/align_attempt1.txt)
- Step 3 initially stopped in file hashing before sending UCI commands. I restored the tracked fixture and Job 7 logs in the sparse checkout, then ran both cells. The comparison reconstructs rows from raw stdout and confirms the FEN order and node limit from the raw commands. [Preflight](sol3/job8/step3/B2_preflight/finding.txt) · [B2 command](sol3/job8/step3/B2/run.meta) · [N2 command](sol3/job8/step3/N2/run.meta)

## Suspicions

C2 fires sooner than C1 because reversing the first incremental column changes any nonempty fused update. C1 requires the refreshed side to have an addition left after the four-column loop and for that change to alter the final value. C3 fires on the root refresh. The controls establish detection of each planted evaluation error in this workload.

## What I did not do

I made scratch source copies for the build, verifier controls and hard-node probe. I ran no speed comparison, PC test or strength match. The branch holds text patches, logs, harnesses and reports.

## What I am not sure about

More than one thread, MultiPV, a game clock, speed (no timing in this job), the PC's own net and compiler.

The reference check compares evaluation outputs at the calls this workload made. I did not count all evaluation invocations or compare each internal accumulator element. [Raw verified stdout](sol3/job8/step2/verify/observed.engine.stdout.txt) · [Complete warm trace](sol3/job8/step2/verify/trace.jsonl)
