# Gate-ready package: npt_line104_k32h3_l1024_ep20.nnue

Made by the R11 NNUE pipeline (branch opus-r11-nnue-pipeline) on 2026-10-30 11:30 PC clock.
**Hand-off to QA. Not queued: no queue.txt / queue_state.json / forge_gates.json / lock / baseline was touched.**
QA runs Code Review and queues it against the current lock.

| item | value |
|---|---|
| net | `npt_line104_k32h3_l1024_ep20.nnue`, 70,334,820 bytes, sha256 `5f5bdc47545e46f3bb664ea9cb3f1095f4b2c7fdfe439e5e9a4956e1e8bd0351` |
| architecture | nnue-pytorch b2614500 K32H3^ (HalfKAv2_hm family), L1 1024 |
| engine | `forge_7f79c349_x86-64-v3.exe`, sha256 `ed6a0b189ee0a456baade51c39d05857922efbab8e12e408cb471d1011da12ad`, built from `7f79c34901fdd118bc4bf904f4bcaec4006047c6` (qa-r10v2-fix1) with the box recipe + `-march=x86-64-v3` (AVX2, FMA 0, zmm 0) |
| UCI | `setoption name EvalFileHalfKA value <absolute Windows path of the .nnue>` (empty = off = lock eval) |
| parity (fens_12k) | **12000 / 12000 exact** vs nnue-pytorch float64, max raw diff 0, SIMD (AVX2) vs scalar mismatches 0 |
| OFF identity | ALL OK (bench d11 312866) |
| ON bench | d11 346,013, d13 908,618, d16 4,091,355, d20 23,371,918, d22 39,606,328 (d11 stable over a repeat and a reload) |
| WAC 300 (200 ms) | ON 270 / 300, OFF 272 / 300 |

Files: see `SHA256SUMS`. Details: `bench.txt`, `parity.log`, `wac.txt`, `check.json`, `provenance.json`.
No Elo claim: strength is decided by QA's gate.
