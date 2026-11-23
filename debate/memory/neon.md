# Memory file of neon

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: neon
- Model: Gemini 4 Neon
- Started: 2026-11-23T03:40:08Z
- Last update: 2026-11-23T04:04:27Z
- Phase: 2 debate

## What I have read to the end (tick a file only when you reached its last line; 26 source files, 11,566 lines)
- [x] debate/README.md
- [x] debate/PLAN.md
- [x] debate/STATE.md
- [x] debate/READ_CHECK.md (answered in `debate/msgs/20261123T034552Z_neon_readcheck.md`; Fable scored 12/12)
- [x] loop/LOOP_OPTIONS.txt
- [x] source/R65_NOTE.txt
- [x] source/src/search.cpp (3,426 lines)
- [x] source/src/board.cpp (1,811 lines)
- [x] source/src/uci.cpp (1,314 lines)
- [x] source/src/nnue_v3.cpp (993 lines)
- [x] source/src/eval.cpp (659 lines)
- [x] source/src/nnue.cpp (557 lines)
- [x] source/src/bitboard.cpp (207 lines)
- [x] source/src/book.cpp (193 lines)
- [x] source/src/eval_params.cpp (89 lines)
- [x] source/src/forge65.cpp (61 lines)
- [x] source/include/forge/search.hpp (667 lines)
- [x] source/include/forge/board.hpp (353 lines)
- [x] source/include/forge/nnue_v3.hpp (299 lines)
- [x] source/include/forge/bitboard.hpp (224 lines)
- [x] source/include/forge/b4.hpp (109 lines)
- [x] source/include/forge/nnue.hpp (105 lines)
- [x] source/include/forge/eval_params.hpp (103 lines)
- [x] source/include/forge/eval.hpp (90 lines)
- [x] source/include/forge/tm_node_share.hpp (69 lines)
- [x] source/include/forge/book.hpp (58 lines)
- [x] source/include/forge/clock_plan.hpp (52 lines)
- [x] source/include/forge/uci_clock.hpp (43 lines)
- [x] source/include/forge/tm_finish.hpp (39 lines)
- [x] source/include/forge/forge65.hpp (22 lines)
- [x] source/include/forge/uci_output.hpp (12 lines)
- [x] source/include/forge/uci.hpp (11 lines)

## What I found (each with file and line, or with the figures I recomputed)
- Local Linux builds (`g++ 13.3.0`) verified bit-exact pins (`312866/862329/4865609` defaults; `226187/616966` loop+r67) across AVX-512+PEXT (`260-268 ms`), AVX2+PEXT (`284-290 ms`), AVX2 no-PEXT (`363 ms`). Stock `CMakeLists.txt` lacks `FORGE_NNUE_V3=1` & `FORGE_MATE_ALPHA_GUARD=1` (gives `278016`).
- `loop/forge65_r0067.fnn3` identities verified: FNV-1a 64-bit format checksum `290bbb0b2e578ac` (`nnue_v3.cpp:536-541,628`), file SHA-256 `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`.
- Local Linux ASan+UBSan (`-fsanitize=address,undefined`) passed cleanly with 0 findings on `bench 11` (`226187`), `perft 4` (`197281`), and 30-ply `selfgame softnodes 2000` (`99365` nodes).
- `nnue_v3.cpp:125,134-151,156,197,678,780-783`: AVX2 `int32` output sum leaves 1.55% headroom at 1024 (`2,114,092,800` vs `INT32_MAX`), overflows at 1056.
- `STATE.md:19-21,55-58`: Plain 388M rounds 68-78 (`36,916g, -0.81`) and 129-136 (`29,968g, -0.07`) pool to `-0.48 [-2.12, +1.16]` across `66,884` games at 50k; r87 (`+2.35`) was a TD round (`STATE.md:55`), not plain.
- `source/src/uci.cpp:448-615` (`run_selfgame`): 100% deterministic (no RNG, no hash clear inside `run_selfgame`); `board.cpp:364-367` clears `key_history_` on `set_fen` so `uci.cpp:457` starts FEN-based games at `ply = 0`.
- `source/src/search.cpp:2432-2452` (`LmrDeeperShallower` mutates `new_depth` into PV re-search + skips null-window re-search at equal reduced depth), `2282/2304/2317-2328` (quiet checks SEE-pruned), `2184` (IIR at root), `2416` (`LmrHistoryDivisor` truncation), `1853-1857` (QS checking captures SEE-pruned), `2547-2588` (`CuckooRep` guards + dead duplicates), `1804,2000` (near-50 TT policy), `3412-3423` (`FORGE_NNUE_V3_VERIFY` checks engine-internal only, not trainer export), `uci.cpp:1124-1134` (`go perft` exit 2).

## My proposals and their status
- `N1` (`035243Z`, amended `035747Z`): Reconcile P1/P10 (2k soft-node bar + second net/seed + static guard audit). Astra: AGREE. Fable: pending reading.
- `N2` (`035243Z`, amended `035747Z`, `040027Z`): P3b Linux ThinLTO+PGO recipe, decoupled PEXT/ZMM, optional AVX2 fused kernel if unfused misses target, FNV-1a + SHA-256 pinned ref checks. Astra: AGREE. Fable: pending.
- `N3` (`035243Z`, amended `035747Z`): P4/P8 `int32` output-sum widening + load-time guard + both-sign raw-sum test before `hidden > 1024`. Astra: AGREE. Fable: pending.
- `N4` (`035243Z`, amended `035747Z`): P3c equal-N score-tail filter test (piece-count fixed) + `MEASURE` cross-tab request to Fable. Astra: AGREE. Fable: pending.
- `N5` (`035747Z`, amended `040027Z`, `040159Z`, `040257Z`): Q1 3-candidate pooled 250k test with exact 4-cell verdict (`LB > 0` / `UB < +5`), operational pause + measured thermal throughput, Q3 direct 250k SPRT shadowed over multiple candidates at `<= 1/day`. Astra: converged after wording/bound fixes. Fable: pending.
- `N6` (`035747Z`, amended `040027Z`): Q5/P8 source correctness items (`go perft`, `selfgame` ply convention, `CuckooRep` differential guard check + dead cleanup, near-50 TT doc). Astra: AGREE. Fable: pending.
- `N7` (`035747Z`, amended `040027Z`): Q4/P7 first post-P1 search bundle (`quiet && gives_check` SEE, root IIR, scaled fixed-point `LmrHistoryDivisor`, QS checking-capture SEE, paired with A4). Astra: AGREE. Fable: pending.
- `N8` (`040257Z`, amended `040427Z`): P3b persistent disjoint game-ID/seed restart gate + NVIDIA Triton smoke & quantized-trainer-vs-engine 1,000-FEN parity check. Astra: AGREE. Fable: pending.
- `N9` (`040257Z`, amended `040427Z`): P3/P4 fixed older teacher audit (`QUESTION` to Fable) + matched-scale ablation (`teacher_weight = 0`, no-change default on inconclusive). Astra: AGREE. Fable: pending.

## What I still owe (questions to me that have no answer yet)
- Replied to ALL Astra proposals (`RE A1`–`RE A5`) and ALL Astra critiques on `N1`–`N9` — zero unanswered items.
- Waiting on Fable to finish reading the remaining source files (latest ~`04:25Z`), post Fable's proposals (`F1+`), answer our `MEASURE` (`N4`) and `QUESTION` (`N9`), and record `BOARD.md` statuses.

## My next step
- Push `RE Astra on N8/N9` + memory update; poll both branches frequently so every message from Fable or Astra gets an immediate checked reply.

## Last shared commit read
11ed5c0582 (shared), 6f2ad21cf9 (Astra).
