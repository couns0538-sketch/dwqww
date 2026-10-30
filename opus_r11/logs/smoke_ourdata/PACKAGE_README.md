# SMOKE package (pipeline test, NOT a gate candidate): r11_smoke_k32h3_l256_bs4096_e4x2000000_s1_e3_best.nnue

Made by the R11 NNUE pipeline (branch opus-r11-nnue-pipeline) on 2026-10-30 14:23 PC clock.
**Hand-off to QA. Not queued: no queue.txt / queue_state.json / forge_gates.json / lock / baseline was touched.**
QA runs Code Review and queues it against the current lock.

| item | value |
|---|---|
| net | `r11_smoke_k32h3_l256_bs4096_e4x2000000_s1_e3_best.nnue`, 17,642,340 bytes, sha256 `e0462a878baff5aa5bb3fab5685f58d73e892e62a07c94a735e426fb542f7494` |
| architecture | nnue-pytorch b2614500 K32H3^ (HalfKAv2_hm family), L1 256 |
| GATE_EXE | `ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad` (the exe is identified by this sha256; the commit below is provenance only) |
| engine | `forge_7f79c349_x86-64-v3.exe`, built from `7f79c34901fdd118bc4bf904f4bcaec4006047c6` (qa-r10v2-fix1) with the box recipe + `-march=x86-64-v3` (AVX2, FMA 0, zmm 0) |
| UCI | `setoption name EvalFileHalfKA value <absolute Windows path of the .nnue>` (empty = off = lock eval) |
| parity (fens_12k) | **12000 / 12000 exact** vs nnue-pytorch float64, max raw diff 0, SIMD (AVX2) vs scalar mismatches 0 |
| OFF identity | ALL OK (bench d11 312866) |
| ON bench | d11 341,450, d13 946,351 (d11 stable over a repeat and a reload) |
| WAC 300 (200 ms) | ON 249 / 300, OFF 272 / 300 |

Files: see `SHA256SUMS`. Details: `bench.txt`, `parity.log`, `wac.txt`, `check.json`, `provenance.json`.
No Elo claim: strength is decided by QA's gate.
