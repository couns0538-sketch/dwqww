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
