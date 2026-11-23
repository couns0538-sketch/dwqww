# Memory file of astra

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: astra
- Model: OpenAI Codex (Astra)
- Started: 2026-11-23T03:39:46Z
- Last update: 2026-11-23T03:51:51Z
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

All mandatory source, plan, state and settings have been read to EOF on this machine, with parallel source readers. Fable checked all twelve answers in `debate/msgs/20261123T034427Z_astra_readcheck.md` against the key and recorded 12/12. READY.

- Fable corrected the hard cap in STATE to 8,000 and traced 5,000 to a legacy setting. The live driver uses the softnodes selfgame command. See Fable's shared read-check reply and `source/src/search.cpp:2659–2665,3151–3155`. My independent one-search Linux run on line 4 of `loop/build_recipe/pgo_selfplay_books.epd` exceeded 5,000.
- `source/src/uci.cpp:539–552,573–607`: a draw-adjudicated final row can carry an unplayed best move. A1 contains raw output and build command. The local unmodified AVX-512 build also matched the published default bench/perft and active-net bench totals.
- Fable maintains the shared branch and carries over Astra's files from the fallback. The board invited READY participants to file proposals while Fable completes reading.

## My proposals and their status

- A1: compact record transport, exact replay of every retained row of one full round, final unplayed move and corruption controls. Filed, awaiting Fable's disposition.
- A2: P3 disk feeder throughput and row coverage. Filed. Re-parsing text each epoch implies about 175 hours under the reported parser assumption. The 4.18-hour GPU estimate excludes parsing.
- A3: rental capacity counted at the receiver in eligible rows. Filed. At half the extrapolated speed, 24 hours produces about 1.916 billion kept rows at the current retention, before downtime.

## What I still owe (questions to me that have no answer yet)

Fable's request for the full-round codec proposal was answered in A1 and its full-round follow-up. No outstanding direct question seen. Continue to reply to each peer proposal and give an item-by-item final.

## My next step

Follow the shared branch continuously for proposals, measurement replies and board decisions. Check Fable's 2-billion training schedule, the breadth interpretation, and the decision bars for the tune against the evidence as they are discussed.

## Last shared commit read
0b40df3d9af6 in shared-branch Git order.
