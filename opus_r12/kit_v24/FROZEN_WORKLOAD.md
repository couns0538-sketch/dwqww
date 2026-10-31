# M8 frozen profiling workload (LTO+PGO), v1, 2026-10-30

This is the ONLY training run used for every LTO+PGO build (lock/opponent and every candidate, box and PC), so both sides of a gate are profiled the same way (CR condition D2). Do not edit these files: the scripts check their sha256 and refuse to run if they change. A new workload needs a new version name, a CR review, and a rebuild of BOTH gate sides.

## Files
| file | sha256 | content |
|---|---|---|
| workload/frozen_train_cmds.txt | 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30 | UCI input fed to the instrumented exe on stdin (LF line ends) |
| workload/bench_fens.txt | 16f158933265dc5dc05ffd00a181809d345b25d72d3de8e169804efed7b1a835 | the 8 `bench` positions, extracted by script from the lock's src/uci.cpp + include/forge/board.hpp (not retyped); used only by the per-position identity check, not by training |

frozen_train_cmds.txt, exactly:

    uci
    isready
    bench 11
    bench 13
    bench 16
    isready
    quit

## Rules
- **Every UCI option stays at its default / OFF.** The file has no `setoption` line, and both scripts refuse a workload that has one. Candidate options are therefore OFF during training, so a candidate's profile covers the same code paths as the lock's (candidate-independent).
- `bench` only: 8 fixed positions, fixed depths 11, 13 and 16, its own `Searcher(16)` (16 MB TT, independent of the Hash option), TT and histories cleared per position, single thread, no clock, no book. It is node-deterministic, so the profile counts are reproducible.
- Fixed depth list 11/13/16 (the same depths as the 8A4A00C9 training run). Threads = default 1, Hash = default (bench does not use it), OwnBook = default (bench does not use the book).
- Run: Linux `nice -n 19 taskset -c 5 timeout 3600 <instrumented exe> < workload/frozen_train_cmds.txt`; Windows `cmd /d /c "<instrumented exe> < frozen_train_cmds.txt > train_out.txt 2>&1"` (raw bytes; same as QA's 8A4A00C9 run). The output must have exactly 3 `bench depth` lines and one .gcda per object file.
- Archive: every build writes gcda_manifest.txt (sha256 + name of every .gcda, names sorted bytewise; the box replaces the mangled build path by `<BUILD>`) and a tar/zip of the profile dir. Record the manifest sha256 next to the exe sha256 in GATE_EXE.

## Difference from the 8A4A00C9 training run (for CR)
QA's train_cmds.txt for 8A4A00C9 also had `setoption name Threads value 1`, `Hash value 16`, `OwnBook value false`. Those values equal the defaults (Threads 1) or are not used by bench (Hash, OwnBook), so the searched nodes are the same, but the uci.cpp setoption code was counted, so the .gcda for uci.cpp and possibly the exe bytes differ. Per the "no setoption" rule, the AL1 opponent must be REBUILT with this frozen workload; 8A4A00C9 stays the pre-freeze build and should not be one side of a gate whose other side used this workload.

# Frozen workload v2 (net path + SMP), kit v2.4, Opus R12, 2026-10-30

v1 above stays frozen and stays the workload for **no-net builds**. v2 is for builds that are gated or timed **with a
HalfKA net loaded** (EvalFileHalfKA): with v1 the net code never runs during training, so -fprofile-use treats it as
never executed (QA R11 speed check: LTO+PGO HalfKA exe 9E5CB644 12.1-12.4% slower than the plain build with a net).
A v2 build and a v1 build are different build modes: never one side each of a gate or a speed comparison (LP vs LP of
the same workload only, as for v1).

| file | sha256 | content |
|---|---|---|
| workload/frozen_train_cmds_v2.txt | 52b8299ed4a2412c5295eca9438170aa9af17c844fe528374033050931f6d2ee | UCI lines, LF; `{NET:e19}` / `{NET:e9}` = net paths |
| workload/nets_v2.txt | 8448dae96755cb65f8880226b9fcc0b3ddf8904b9435021f747e0e9c4e2c74d3 | full sha256 of the two nets |
| tools/train_driver.py | (tool) | feeds v2 to the instrumented exe and waits for real output |

Content, in this order (three blocks; the only change from v1 is the mixed net / thread profile):
1. no net: `uci`, `isready`, `bench 11`, `bench 13`, `bench 16` (= v1), then `setoption name Threads value 2` and for each
   of the 8 bench FENs `position fen F` + `go nodes 200000`;
2. `setoption name Threads value 1`, `setoption name EvalFileHalfKA value {NET:e19}` (r11 e19_final, bf1e347c...),
   bench 11/13/16, then Threads 2 and the same 8 `go nodes 200000`;
3. the same with `{NET:e9}` (r11 e9_best, 5380f866...); `isready`, `quit`.

Rules:
- Only `Threads` and `EvalFileHalfKA` are set; every other option stays at its default (driver and script refuse other
  setoption lines). Bench ignores Threads (it has its own one-thread `Searcher(16)`), so the Threads=2 part uses `go`:
  with 2 workers the shared-TT path (`lock_stripe` locking, no exclusive lease), the helper thread and the node
  aggregation run; in v1 they never run.
- A `go` is stopped by the next UCI line, so v2 cannot be a plain stdin file: `tools/train_driver.py` sends one line at a
  time and waits for `uciok` / `readyok` / `bench depth N` / `bestmove`, checks each net's full sha256 against
  nets_v2.txt and that every EvalFileHalfKA setoption printed `info string EvalFileHalfKA loaded` (no ERROR), counts
  9 bench lines, 24 bestmoves and 2 loads, and needs engine exit code 0 (the .gcda files are written at exit). It writes
  the resolved input (LF) to `train_engine_out.txt.input.txt` and the engine output to `train_engine_out.txt`.
- The Threads=1 parts are node-deterministic (bench). The Threads=2 searches are NOT: two threads share the TT and the
  split of 200k nodes between them depends on timing, so the edge counters of those searches differ run to run (and
  `-fprofile-update=single` can drop racing increments; `-fprofile-correction` absorbs that). Whether the exe is still
  reproducible is exactly what the pc1 = pc2 exe sha256 check decides; see the R12 report for the measured result.
- Net paths are fixed per PC (`-NetE19` / `-NetE9`, defaults = the forge_push\bin copies QA times with); the path string
  is part of the training input, so pc1 and pc2 must use the same paths.

## Measured (R12, 2026-10-30): the Threads=2 part makes the exe non-reproducible -> workload v2t1
Two clean v2 builds of r10fix1 (tags r10fix1_w2_pc1 / _pc2, same PC, same pair 0x3, minutes apart) both passed every
identity check (OFF = lock pins, e19 and e9 = D8D90B68's counts at d11..d22) but gave different LTO+PGO exes:
8f162985... vs 18503c4d.... `opus_r12/tools/exe_func_diff.py`: 12 of 4686 functions differ and they are the hot ones
(Worker::search, qsearch, evaluate_position, static_evaluate, MovePicker::next, halfka::evaluate_raw,
generate_pseudo_legal, see_ge, the halfka layer kernel, should_stop, ...): the timing-dependent counts of the Threads=2
searches move PGO decisions in exactly the code that decides speed. The binding pc1 = pc2 rule cannot hold with a
Threads=2 `go` part, so:

| file | sha256 | content |
|---|---|---|
| workload/frozen_train_cmds_v2t1.txt | dca15f6620f8622ab0fbfec29cb1a405607d394aae831b0cc736b004a34767e2 | v2 without the Threads=2 searches |

v2t1, exactly (LF): `uci`, `isready`, `bench 11`, `bench 13`, `bench 16` (= v1), `setoption name EvalFileHalfKA value
{NET:e19}`, `isready`, bench 11/13/16, `setoption name EvalFileHalfKA value {NET:e9}`, `isready`, bench 11/13/16,
`isready`, `quit`. Node-deterministic (bench only; nets checked by sha256). It profiles the net path; the SMP code stays
unprofiled, as with v1. `-Workload v2t1` is the workload for gated net builds; `-Workload v2` stays in the kit as the
documented non-reproducible SMP experiment (do not gate its exes). Profiling SMP would need a different binding rule
(e.g. pc2 rebuilt from pc1's archived profile) - a CR decision, not taken here.
