# Forge speed job - STATUS

Owner Couns. Job window 2026-11-05 08:38 -> 14:38 (PC clock = Vienna time); FINAL_REPORT due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Plan: `opus_speed/PLAN.md`. Scratch `F:\ospd\` (<= 8 GB).
Lock: exe FD3A5190 (`forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`), source = exact copy `F:\ospd\src\lock` (20 files).

| job | state | candidates | last update |
|---|---|---|---|
| A speed-only lock path (tools) | IN PROGRESS: tools written; kit self-test PASS (lp_v1 of the lock source = FD3A5190 byte for byte); test 2 PASS (mutant HistoryMax 16384->16000 FAILS at L1, no ABBA); A/A d16 + d20 wall sd 3.8 %/round -> CPU-time metric added; variant screen building (o3, lto, pgo, lp_z4 done; -fno-plt / -fno-semantic-interposition = identical exe); L4 sanitizer level reworked (MSVC ASan + g++ UBSan-trap) | - | 09:21 |
| B bit-exact hot-path changes | IN PROGRESS: worker b1tt (TT: S4 TT_NOTLS, TT align, prefetch early), worker b2mg (NNUE zmm output, S1 no-zero movelists, S3 matkey, pick_best, S2 PEXT) | - | 09:00 |
| C gate wall time | IN PROGRESS: worker jobc (replay, LLR projection, throughput, adjudication audit, book load, pre-gate screen, concurrency plan) | - | 09:00 |
| D net pipeline | NOT STARTED (only if A-C are done) | - | 09:00 |
