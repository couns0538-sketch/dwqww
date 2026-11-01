# Astra R9 results

Started 2026-11-01 13:57 America/Los_Angeles. Six-hour deadline: 19:57.
Status: c1 correctness proof PASS; advisory speed test next. No candidate accepted yet. Elo: UNPROVEN.

- Lock SHA256 PASS: FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072.
- Kit MD5 PASS: 729FE7275C3C01D22C751CB751D5C9D2.
- Fresh shallow independent clone and owned worktree; original checkout unchanged.
- Root AGENTS.md absent in supplied checkout; created here with requested policy verbatim.
- Source imported from read-only lock directory; baseline manifest pending.
- Disk preflight: C 154.82 GiB, D 77.77 GiB free. CPU 2/3 initially ~11% utilization.
- Approved exception: short T4 correctness smoke with affinity restricted to two logical CPUs.
- Ruling: shallow clone avoids copying 7.57 GiB history into a 10 GiB workspace budget.
- Ruling: task ledgers live in astra_r9 as requested, rather than skill-default paths.
- Next: native sampling profile of the unchanged lock, baseline pins, sanitizer toolchain feasibility.
- Proof pending: all bench/perft/eval/sanitizer/smoke/build-reproducibility/timing checks.

## Review milestones

Baseline profile complete before engine edits: 24,112 samples; output arithmetic
4.380%, quiet SIMD updates 2.999%, refresh 0 samples. d20 PASS on all 19 complete runs.
Crew corpus found: 12,000 unique legal FENs, SHA256
c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265.
Next candidate: default-off NNUEWideOutput, ordered AVX-512 float output only.
Refresh cache skipped by profile; integer/VNNI deferred for lack of exact proof.
Native llvm-mingw sanitizer toolchain downloaded under D:\a9, archive SHA256
FD5462B7F5D93B2FF981FCD3F9C7E427E47F3203C64EA91C27BCC444EEBD74CD;
positive controls pending. No optimized engine built yet.

M1 review and focused recheck PASS (not candidate acceptance). Reviewed nnue.cpp:
D11B4EED401A3F6C05EA7A5C8917E1E7F933A9E1BDF3E3992D44C62424F3F635.
Confirmed reviewer gaps fixed: float lane/output bit checks, combined residual/HCE
digest, long 128-ply incremental/unmake coverage. Separate unchanged-lock and
candidate harnesses PASS: 684200 evaluations, 324100 legal moves, 12000 nulls,
digest 3bd3b27ac5a60483. Diagnostic-only ON counter 684200.
Lock all five bench pins and both perft pins PASS. ASan/UBSan positive controls PASS.
Next: immutable c1 source snapshot, two v2.3 production builds and full remaining proof.

## M2 — reproducible production and correctness proof

Source implementation commit fb58080, frozen D:\a9\c1 (manifest c1-source.json).
Production b1 = b2 SHA256:
775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284.
Both unchanged v2.3 kit runs PASS: OFF/ON full pins and perft, plain-vs-LTO+PGO
identity, no missing-profile warnings, no FMA; longest gcda path 83 characters.
One benign serial-LTRANS warning; gcov-dump unavailable (kit permits record-only omission).
First attempt a1 failed before compilation because Windows PowerShell did not load
Get-FileHash. Retained FAILED/log; corrected host to installed pwsh 7.6.8 with new tags.

Production lock/OFF/ON depth-2 corpus comparison PASS: all 12000 score/node/bestmove
records identical, every bestmove legal. T1/T4 movetime smoke OFF/ON PASS (48 legal
bestmoves, each awaited before quit). ASan+UBSan c1 self-play OFF/ON PASS: 8 games /
592 legal plies each, zero reports; native sanitizer exe SHA256
A56762278935AF93344680BA147A9076F63B52504E2495A686D7FE5F28A4A2AA.

Harness review found absolute-timeout and setup-cleanup gaps plus missing during-run
timing telemetry. All fixed; three targeted regressions PASS; focused recheck PASS.
Timing now retains all rows and rejects experiments with any contaminated run.
Next: predeclared four A/A and ten ABBA blocks, no concurrent owned heavy work.
