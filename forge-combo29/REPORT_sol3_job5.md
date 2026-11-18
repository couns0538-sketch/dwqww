# sol3 — Job 5 whole-game and final hard-node checks

**Step 0 passed.** The retained r15d, k10, k11 and planted P executables matched all four assigned SHA-256 values. The synthetic net768 matched SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. All four engines printed active checksum `30ab43b4ba5db5f3` and `readyok`. [Hash checks](sol3/job5/known_sha256.txt) · [Raw activation lines](sol3/job5/readiness.summary.txt)

**Step 1 matched the known answer.** Carbon2’s unchanged driver, SHA-256 `c79b95bf45762fa9869d23140ed7f946cfaf0cb6bc4f74325a18d5f934bf1c45`, produced **8612 searches**, **29333343 last-iteration nodes**, and legacy trace **`5c705841c3ea17b4`** on r15d. The workload is PC20, Threads 1, Hash 16 MiB, MultiPV 1 by default, synthetic net768, `go softnodes 2000`, 60 games, seed 20261117, eight randomized opening plies, and 300 maximum plies. [Original command](sol3/job5/original_command.txt) · [Raw original JSON](sol3/job5/r15d_original.json)

**Step 2 stopped at a missing line.** The strict final-count driver exited 1 at zero-based game 0, ply 83. Forge returned `bestmove 0000` and its last iteration reported zero nodes. It emitted no final softnodes line. The driver requires this line for every search and produced no JSON. The r15d early-return path in `src/search.cpp:2793–2812` returns before the softnodes final output at `3241–3249`. [Exact driver diff](sol3/job5/driver_final.diff) · [Step 2 stderr](sol3/job5/r15d_driver_final.stderr.txt)

**Prediction grade.** The standalone prediction was committed as `178b5b7fe47402a42cc93fd7ce6faebebd00fb7c`. It correctly forecast the same strict r15d stop on the Step 3 rerun and all 389 B2 searches ending at 20000 with the unplanted probes. The conditional k10/k11 legacy identity, the forecast of 66 k11 cap hits, and the conditional P trace difference were ungraded because Step 3 produced no qualifying trace. [Prediction](sol3/job5/prediction.txt)

### Step 3 whole-game table

| Tree | Disposition | Searches | Last-iteration nodes | Legacy trace | Final sum | At cap | Final hash |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| r15d | STOP, strict driver exit 1 at game 0 ply 83 | — | — | — | — | — | — |
| k10 | r15d gate stopped this step | — | — | — | — | — | — |
| k11 | r15d gate stopped this step | — | — | — | — | — | — |
| P | r15d gate stopped this step | — | — | — | — | — | — |

The Step 3 baseline reproduced Step 2’s missing line after the prediction. This stops the warm final-count comparison. [Baseline run and identity](sol3/job5/r15d_final.meta) · [Step 3 stderr](sol3/job5/r15d_final.stderr.txt)

### Step 4 final hard-node counts

Each probe used Job 4’s unmodified driver and 389-position fixture. PC20, Threads 1, Hash 16 MiB, MultiPV 1, and `go nodes 20000` were fixed. B2 used embedded AL1 s198. N2 used synthetic net768. The probe emitted final `SearchInfo.nodes` before bestmove. Its source change was one conditional output statement. k10’s patch hunk header was moved three lines to match its source context, with the same inserted C++ and zero application offset. [Probe diff](sol3/job5/probe.diff) · [Independent raw readback](sol3/job5/probe_readback.txt)

| Probe | Cell | Job 4 rows byte-identical | Final counts at 20,000 | Final counts equal to k10f | First final count difference (k10f → probe) |
| --- | --- | --- | ---: | ---: | --- |
| k10f | B2 | yes | 389 | 389/389 | — |
| k10f | N2 | yes | 389 | 389/389 | — |
| k11f | B2 | yes | 389 | 389/389 | — |
| k11f | N2 | yes | 389 | 389/389 | — |
| Pf | B2 | yes | 0 | 0/389 | 1 (20000 → 20001) |
| Pf | N2 | yes | 0 | 0/389 | 1 (20000 → 20001) |

**Step 4 passed.** k10f and k11f both finished at exactly 20000 nodes in all 778 searches. Pf finished at 20001 in every corresponding search. All six last-iteration row files stayed byte-identical to their Job 4 counterparts. [Probe verification and row hashes](sol3/job5/probe_readback.txt)

### Step 5 assertion-enabled build

The scratch k11 Release build removed the target `NDEBUG` define and the Release flag’s separate `-DNDEBUG`. The resulting compile-line grep count was **0**, and all nine compile commands had no `NDEBUG` token. The unchanged Step 1 driver completed with the prescribed seed, net and limits and produced **8612 searches**, **29333343 last-iteration nodes**, and **`5c705841c3ea17b4`**, exactly matching the original r15d known workload in Step 1. The driver and traced engine threads exited 0, with no `Assertion` output. The stopped Step 3 produced no k11 legacy triple for its specified direct comparison. [Compile guard](sol3/job5/assertion_compile_guard.txt) · [Raw JSON](sol3/job5/assertion_original.json) · [Run identity](sol3/job5/assertion_run.meta) · [Driver and engine stderr trace](sol3/job5/assertion_stderr_syscalls.txt)

## Facts

- The Job 4 trees and builds were still available. I rechecked their executable hashes and activation metadata. Job 4’s compiler, flags and source manifests establish the identities. The probe and assertion builds kept the same GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41, CMake 4.2.3 and x86-64-v4 Release optimization. The probe changed only output. The asserting build removed both sources of `NDEBUG` in scratch. [Job 4 build and scope](REPORT_sol3_job4.md) · [Probe builds and logs](sol3/job5)
- The exact strict-driver diff keeps the existing opening sequence and legacy search hash. It requires one final soft-node value before every bestmove and, upon successful completion, would add `final_sum`, `at_cap` and the FNV-1a hash over ASCII `<game>,<ply>,<N>;` records. The untimed opening warm-up is validated and falls outside the aggregate indexed game searches. [Driver diff](sol3/job5/driver_final.diff) · [Mock tests](sol3/job5/mock-tests.txt)
- Step 4 independently parsed final `info string final nodes N` lines and reproduced the six rows files from their raw stdout. Both existing Job 4 SHA-256 values matched every corresponding row file. The positive control changed the final count by one while retaining exactly the same legacy rows. [Readback](sol3/job5/probe_readback.txt)

## Suspicions

The absent final line is an output-path gap for terminal roots. The original workload counts that zero-node search before stopping its game. A final-count contract that covers every returned `SearchInfo`, including early returns, would let the strict driver measure warm final totals without changing the workload or filling in missing counts.

## What I did not do

I stopped the Step 3 warm final-count matrix at its baseline gate and did not infer values for the missing cells. I made no engine-source change in the repository. The rebuilt probes, asserting build and weights stayed in scratch. Commits contain the text evidence and exact diffs.

## What I am not sure about

More than one thread, a clock, MultiPV (the piece switches itself off there), speed (no timing in this job), a fault that changes neither a final count, nor a search's last line, nor a later search of the same game.

The hard-node cap is verified in the declared cold B2 and N2 searches. The effect of the planted node on later warm searches remains unmeasured. [Clock stamps and checkpoints](sol3/job5/stamps.txt)
