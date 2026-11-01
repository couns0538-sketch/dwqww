# Astra R9 results

Started 2026-11-01 13:57 America/Los_Angeles. Six-hour deadline: 19:57.
Status: baseline preflight; no optimization implemented or accepted. Elo: UNPROVEN.

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
