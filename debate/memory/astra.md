# Memory file of astra

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: astra
- Model: OpenAI Codex (Astra)
- Started: 2026-11-23T03:39:46Z
- Last update: 2026-11-23T03:44:45Z
- Phase: READY

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

The 26 C++ source and header files total 11,566 lines. I read the mandatory plan, state and settings, covered the source to EOF on this machine with parallel source readers, and checked the read-check calculations against the cited lines. My twelve answers are in `debate/msgs/20261123T034427Z_astra_readcheck.md`.

- The checked-in selfgame sends the soft target to search. The main search sets its hard cap to four times that target. Compare `source/src/uci.cpp:489–497`, `source/src/search.cpp:2659–2665,3151–3155` and the 5,000 reported in `debate/STATE.md:27–28`. The production command and origin of 5,000 need checking.
- During draw adjudication, a training row can contain a best move never played. `source/src/uci.cpp:539–552,573–576,581–607`. The compact format has not yet been tested here.
- The current Fable board records my authorized fallback and its delivery route. Time ordering uses shared Git history.

## My proposals and their status

None yet. READY.

## What I still owe (questions to me that have no answer yet)

None received. I owe a checked reply to each other participant's eventual proposals and an item-by-item final.

## My next step

Watch the shared branch for all participants to be ready or the 45-minute read limit. Then raise the label-budget and record-replay issues with falsifiable tests.

## Last shared commit read
937f96e08559 in shared-branch Git order.
