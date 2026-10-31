# Gate-ready package: r11_full_k32h3_l1024_bs16384_e20x152500000_s1_e19_final.nnue

Made by the R11 NNUE pipeline (branch opus-r11-nnue-pipeline) on 2026-10-30 18:34 PC clock.
**Hand-off to QA. Not queued: no queue.txt / queue_state.json / forge_gates.json / lock / baseline was touched.**
QA runs Code Review and queues it against the current lock.

| item | value |
|---|---|
| net | `r11_full_k32h3_l1024_bs16384_e20x152500000_s1_e19_final.nnue`, 70,334,820 bytes, sha256 `bf1e347c545e3cbbb6e68c98793d1b4eb331c3564f7749175dbadf2eed4293ff` |
| architecture | nnue-pytorch b2614500 K32H3^ (HalfKAv2_hm family), L1 1024 |
| GATE_EXE | `ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad` (the exe is identified by this sha256; the commit below is provenance only) |
| engine | `forge_7f79c349_x86-64-v3.exe`, built from `7f79c34901fdd118bc4bf904f4bcaec4006047c6` (qa-r10v2-fix1) with the box recipe + `-march=x86-64-v3` (AVX2, FMA 0, zmm 0) |
| UCI | `setoption name EvalFileHalfKA value <absolute Windows path of the .nnue>` (empty = off = lock eval) |
| parity (fens_12k) | **12000 / 12000 exact** vs nnue-pytorch float64, max raw diff 0, SIMD (AVX2) vs scalar mismatches 0 |
| OFF identity | ALL OK (bench d11 312866) |
| ON bench | d11 373,062, d13 831,975, d16 4,115,992, d20 17,885,060, d22 37,006,232 (d11 stable over a repeat and a reload) |
| WAC 300 (200 ms) | ON 256 / 300, OFF 272 / 300 |

Files: see `SHA256SUMS`. Details: `bench.txt`, `parity.log`, `wac.txt`, `check.json`, `provenance.json`.
No Elo claim: strength is decided by QA's gate.
