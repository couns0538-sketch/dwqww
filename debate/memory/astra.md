# Memory file of astra

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: astra
- Model: OpenAI Codex (Astra)
- Started: 2026-11-23T03:39:46Z
- Last update: 2026-11-23T04:19:31Z
- Phase: 2 debate

## What I have read to the end (tick a file only when you reached its last line; 26 source files, 11,566 lines)
- [x] debate/README.md
- [x] debate/PLAN.md
- [x] debate/STATE.md
- [x] debate/READ_CHECK.md (answered in my read-check message)
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

Readiness and source ledger are complete. Fable checked Astra's read-check message against the key and entered 12/12 on the board. Fable traced the former 5,000-node value to an unused legacy setting and corrected STATE to 2,000 soft, 8,000 hard (`source/src/uci.cpp:489–497`, `source/src/search.cpp:2659–2665`). Astra's Linux build produced 5,506 nodes on one search at opening line 4. Default bench 11/13, perft 5, and active-net bench 11/13 matched the five reference totals. The Linux diagnostic used unmodified source, GCC 14.2.0 and AVX-512. No PC strength match was run here.

The active Hash option changes the live searcher while bench constructs its own 16 MB searcher (source/src/uci.cpp:1105–1110,1245–1255). Two independent Linux builds reproduced 616966 bench nodes at both Hash 16 and 32, while live depth-18 startpos counts were 375880 and 375868. N2 now incorporates that negative control. The 600+ score outcome table samples after the existing outcome filter; see my N4 follow-up.

## My proposals and their status

- A1 ACCEPTED. The PC compared 16,005,930 ordered rows, every move/ply/result/FEN, 15,255,460 observable scores. Negative control found the planted move at row 167. Unmasked score oracle, per-ending counts, Linux converter, transport and retry remain rehearsal checks.
- A2 TO MEASURE AFTER THE DEBATE. Existing trainer parses text once; current secondary disk can fit the 88 GB decoded store. Measure the cold end-to-end path against 4.445 million presentations/s and verify row coverage and cross-round mixing.
- A3 ACCEPTED. Count each delivered logical piece once. Use the reference round partition for the existing duplicate filter regardless of transport chunk boundaries, and report cross-piece repeat estimates separately. This answers Fable's open question.
- A4 ACCEPTED. Fable compared the earlier rule to the existing LmrDeeperShallower arm. Astra then independently reproduced the declared 595569 bench-13 nodes with the switch on. Switch off was 616966. This supports equivalence checks, with the strength test still due post-P1.
- A5 ACCEPTED. Apply win/loss/inconclusive to the specific breadth mixture. A stride-only follow-up would keep the same rounds and per-round quotas.

## What I still owe (questions to me that have no answer yet)

I replied to N1–N9. Neon accepted the corrected three-way/overlap treatment for N5, plus a fresh confirmation of the selected candidate. N8 addresses persistent work IDs and independent trainer/export parity; N9 records the current teacher before any matched ablation. N1–N4 refinements were acknowledged by Neon. On N5 I dissent from declaring a ceiling when a single candidate's interval crosses zero and its point estimate is ≤+3. An upper confidence bound below a predeclared practical margin supports only a candidate-specific flat verdict. I support N6's targeted tests and N7 as a conditional, predeclared search experiment. I also clarified that the engine's format checksum and the net file SHA-256 identify different things. All three are READY. F1 has received Astra's reply: use the paired [−3,0] noninferiority SPRT, require calibrated handling at its cap or call that inconclusive, use runner controls as smoke tests, and measure time. I corrected the unpaired diffusion midpoint estimate to about 76,800 uncapped games under the stated assumptions. The new hypothetical cut-at-1000 arm of N4 must drop the crossing row and suffix, relabel the prefix and re-filter. No open direct question known. The item-by-item final remains due.

## My next step

Continue watching Fable and Neon on the shared branch, review each new proposal immediately, check measured results, and audit the eventual ordered final plan against the agreed tests. Astra publishes only on its authorized fallback branch.

## Last shared commit read
bb858e893ad9 in shared-branch Git order.
