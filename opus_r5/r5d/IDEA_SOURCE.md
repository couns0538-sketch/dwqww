# R5D idea sources

Every implementation here is my own code; sources are where the ideas come from.

| idea | source |
|---|---|
| the bug, its known rates (1/40 on base b7c1772, 13/6000 KRK with SmpV2) and the suspect list | job spec R5D (Engine QA for Couns, 2026-10-29); R5B `opus_r5/r5b/tools/flake_tt_mate.sh` (branch opus-r5b-speed); Code Review note on SmpV2 helpers at depth+1 |
| reproduction harness (fresh Searcher per run, fixed depth, mate/no-mate verdict) and the warm-TT variant (`--prefill-fen`) | own code; the mate condition is the one of `tests/tt_mate_tb_tests.cpp` (R3-5) |
| diagnosis by logging every worker's TT stores at the nodes of the mating tree | own instrumentation (`diag/instrument*.py`, scratch copies only) |
| one-change experiments (dupfix, F2/F3/F6/F7, C2/C6, W2/W3, threefold-only) | own; each isolates one suspect of the job's list (TT write policy, store races, repetition, helper writes) |
| the cause: the only mating quiet move (zugzwang Re7) is dropped by move-count / history / SEE pruning or reduced by LMR, and the pruning-dependent bound reaches the root through the TT | own analysis of the `diag5` trace; the general fact that forward pruning can miss quiet zugzwang wins is standard chess-programming knowledge (it is why engines guard null-move pruning in pawnless or zugzwang-prone positions) |
| the fix: no quiet-move pruning and no LMR at nodes facing a bare king (mating mode), only in multi-worker searches | own design; the multi-worker gate exists only to keep the one-thread tree (bench pins) identical, as the job requires |
| CI regression test with a planted-bug control (the base tree must fail it) | Forge job practice (`forge-engine-verify` skill, section 4) |
| Threads 2 smoke runner | own R5C runner (`opus_r5/r5c/smoke_n3.py`, branch opus-r5c-netv4) with a `--threads` option and the FEN-legality fix of its stop stress |
