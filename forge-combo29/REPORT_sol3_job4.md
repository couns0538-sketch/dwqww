# sol3 — Job 4 independent stop-path check

**Step 0 passed.** All 14 patches applied with zero fuzz, offsets or rejects in scratch. The reconstructed r15d and k10 binaries matched their known SHA-256 values. The k11 PC20 built-in bench pins matched at **278024** and **587276** nodes for depths 11 and 13. [Step 11 patch output](sol3/job4/patch_11_stop_hot.patch.txt) · [Raw k11 benches](sol3/job4/bench_11.txt)

```text
bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6  /workspace/work/sol3-job4/build_0/forge
55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae  /workspace/work/sol3-job4/build_10/forge
a7a34a148b40c14e5ea960dd2d3182fceef7023a38d12db47c2521a430fc1ea5  /workspace/work/sol3-job4/build_11/forge
```

**Step 1 passed.** Synthetic net768 SHA-256 was `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. Both k10 and k11 emitted `NNUE v3 active` with `hidden 768`, `standalone`, `checksum 30ab43b4ba5db5f3` and `kernel avx512`, then `readyok`. The first readiness check incorrectly required the checksum at end of line. Its raw output contained the matching checksum and trailing weights metadata. The corrected field check passed on both builds, with the first attempt preserved. [Generator raw output](sol3/job4/generator.raw.txt) · [First parser failure](sol3/job4/net_known_answer.stderr.txt) · [Verified readiness](sol3/job4/net_readiness_verified.txt)

**Step 2 prediction matched.** With one worker, a depth-only search uses no node cap and leaves the fast branch disabled. `go nodes 20000` enables it with a cap of 20000. `go softnodes 2000` enables it with a finished-iteration target of 2000 and a hard cap of 8000. No live reader consumes the published `nodes_` in this Threads 1, MultiPV 1 configuration. The worker’s own `local_nodes_` supplies both the iteration rows and final node total. The source reading and prediction were pushed at `11a73949fd155503ac5c2ad770889627463e1e78` before any matrix search. Prediction grade was **5/5 cells** for k11 identity. The additional prediction of zero planted hard-node row differences, unchanged ND, and a detectable overrun in final soft-node totals also matched. [Source reading, line references and prediction](sol3/job4/READING_prediction.md)

### Step 3 identity table

B2 uses embedded AL1 s198 and `go nodes 20000`. B3 uses the same evaluator and `go softnodes 2000`. N2 and N3 use the same limits with the synthetic standalone net768. ND uses net768 at `go depth 8`. All use PC20, Threads 1, Hash 16 MiB and MultiPV 1. Each row compares final depth, last `info depth` node count, its first PV move and bestmove. [Raw rows, commands and engine output](sol3/job4)

| Tree | Cell | Rows equal to k10 | First difference (k10 → tree) |
| --- | --- | ---: | --- |
| 10 | B2 | 389/389 | — |
| 10 | B3 | 389/389 | — |
| 10 | N2 | 389/389 | — |
| 10 | N3 | 389/389 | — |
| 10 | ND | 389/389 | — |
| 11 | B2 | 389/389 | — |
| 11 | B3 | 389/389 | — |
| 11 | N2 | 389/389 | — |
| 11 | N3 | 389/389 | — |
| 11 | ND | 389/389 | — |
| P | B2 | 389/389 | — |
| P | B3 | 389/389 | — |
| P | N2 | 389/389 | — |
| P | N3 | 389/389 | — |
| P | ND | 389/389 | — |

**Planted-control gate: STOP.** Changing `<` to `<=` in the k11 fast stop check left all 389 rows equal in B2 and N2. It also left all 389 ND rows equal, as required. The hard-node rows missed this planted overrun. The already captured final `info string softnodes nodes ...` lines showed 8000 → 8001 on **two B3 positions** and **three N3 positions**, with identical last-iteration rows in each case. First soft total changes were at B3 row 202 and N3 row 20. k10 and k11 had identical soft-node totals in both cells. [Control diff](sol3/job4/plant.diff) · [Control readback](sol3/job4/control_gate.txt) · [P/B3 raw output](sol3/job4/identity_P_B3.stdout.txt) · [P/N3 raw output](sol3/job4/identity_P_N3.stdout.txt)

## Facts

- I rebuilt the source from `6b98f2170a3210e71beed04bbd2553972c253ed7` using the exact Job 3 r15d and stack input hashes. The step 11 patch came from Carbon2 commit `d15357a6c3a507db81404b44bdb51b3ee05382dc` and matched SHA-256 `c00d8d79e70d70afcee6dd45459eb833db7d39c991bd23cb508db65f65c31b9e`. All 29 r15d source hashes matched again. [Source refs](sol3/job4/source_refs.txt) · [r15d hashes](sol3/job4/r15d.sha256check.txt) · [Build logs](sol3/job4)
- All builds used CMake 4.2.3, GCC 14.2.0, libstdc++ 6.0.33, glibc 2.41 and the Job 3 Release x86-64-v4 recipe, which defines `FORGE_NNUE_V3=1`. The embedded weights source SHA-256 was `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. The P executable SHA-256 was `daf597b252104ba83277132426a8a83c6cd9308789e8abe5f53635861d3ad3fb`. [Exact build flags and compile line](sol3/job4/build_11.txt) · [Control build](sol3/job4/build_P.txt)
- Each cell used the 389 Job 3 FENs in order. The fixture SHA-256 was `d0630396e9e937318bf83e542d2f168c6216831e0dd83283875172d6ff72a2b2`. The runner used a fresh process per cell, sent the full PC20 setup, checked net readiness when applicable, and ran `ucinewgame`, `isready`, `position fen` and the declared `go` command before each position. A separate raw parser reconstructed all 5835 rows from stdout and confirmed the commands for every position. [Fixture](sol3/job3/positions.txt) · [Runner](sol3/job4/identity.py) · [Raw readback](sol3/job4/readback.py)

## Suspicions

The planted branch permits one extra counted node at equality when the cap is a nonmultiple of 1024. At the next checked entry above the cap, the fast guard fails and the full stop check runs. A node stop discards the unfinished iteration, so its extra work can leave the reported depth, nodes, PV head and bestmove untouched. The separate soft-node final total confirmed this mechanism in the five observed cases. A hard-node test that reads final `SearchInfo.nodes` could check cap enforcement directly. [Preregistered source analysis](sol3/job4/READING_prediction.md)

## What I did not do

I stopped searches after the declared planted-control gate failed. I made no repository engine source change. The control build and regenerated weights stayed in scratch, and the branch contains text evidence and the one-line control diff. I did not run a timing test, training, a match or a test on the owner’s PC.

## What I am not sure about

More than one thread (the piece switches itself off there), a clock (it switches itself off there too), MultiPV, the asserts (a Release build compiles them out), speed (no timing in this job).

The five cells establish identity of the measured last-iteration rows under these options. Hard-node final consumed counts were outside those rows. The declared control therefore did not validate direct hard-cap enforcement. [Clock and checkpoints](sol3/job4/stamps.txt)
