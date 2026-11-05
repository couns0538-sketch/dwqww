# T12B sources (robustness and fuzz suite: buffer bounds, crafted FENs, UCI edge cases, sanitizer CI)

Worker start 00:48 PC clock (PST -0800), research stop 01:38. One line per source: n | url or repo@sha | licence
tier | what it gave | card id or "no card".

## Own side (read-only, not counted in the 15-source cap)
- lock FD3A5190 source src_al1s198_clean, read in full for buffers: include/forge/search.hpp (408 lines),
  include/forge/board.hpp (205), src/search.cpp (1,531), src/board.cpp (1,058), src/uci.cpp (430),
  include/forge/nnue.hpp (65) + src/nnue.cpp (grep of every index), src/eval.cpp + include/forge/eval_params.hpp
  (grep of every table index) | own | fixed-buffer inventory in notes/T12B/TABLE.md | T12B-01, T12B-02
- notes/T04/BUG_CHECKLIST.md row 9 (bad_captures_ "likely unreachable") and rows 8, 12, 13, 17 | own | the brief's
  starting point | T12B-01, T12B-02
- notes/T07/UCI_EDGE_CASES.md (40 time-control cases) and cards/T12/T12-03 (bench + fuzz checklist) | own | overlap
  check: T07 = clock parsing only, T12-03 = node identity for speed changes | T12B-02
- project skill forge-candidate-checks/SKILL.md lines 33-37 | own | the existing sanitizer CI: opus-r13-san.yml, g++ 13
  -fsanitize=address,undefined -fno-sanitize-recover=all, selfplay_smoke.py (4 games x <= 160 plies, go nodes 20000,
  legality via go perft 1, stderr scan) | T12B-02
- project skill forge-engine-verify/SKILL.md lines 34-56 | own | all three CI build types define NDEBUG (asserts
  compiled out); -D_GLIBCXX_ASSERTIONS makes std::array::operator[] abort; the buffix census + annealer method |
  T12B-01, T12B-02
- memory note fable-review-opus-status.md lines 22-24, 41-52 + F:/opus_scratch/fable_review/buffix64/ (prove.log,
  final_mutant.log, final_fixed.log, search4_seed11/12.log) + branch fable-review-buffix 8632e8ab
  (tests/bad_capture_tests.cpp:141, git log) | own | the overflow is REAL: fixture "many-losing" noisy=69, see_losing=68,
  promotions=4, accepted by set_fen, not in check; 64-entry engine aborts under -D_GLIBCXX_ASSERTIONS (mutant exit 127),
  fixed engine 6/6 fixtures pass; fix a9cea71f sizes bad_captures_ to MoveList::Capacity (+ static_assert) | T12B-01

## External (cap 15)
