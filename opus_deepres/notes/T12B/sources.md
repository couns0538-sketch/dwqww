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
- E1 | official-stockfish/Stockfish commit titles since 2016-01-01 (tools/mine_commits.py --grep 'overflow|sanitiz|out of
  bound|MAX_MOVES|MAX_PLY|buffer|asan|ubsan|undefined behav' --top 25; 3,000 commits cached, page cap 30) | GPL-3.0,
  commit titles only | bug-class list: ee515ad root PV longer than MAX_PLY (already T04 row 9), 1548538 "Fix deep
  recursion", c56bd10 "Fix undefined behavior in stalemate trap detection", df01cb7 branchless ValueList::push_back,
  893a08a "Allow for higher depths", e407a4f / 2c36d1e arithmetic overflows (no buffer) | T12B-02
- E2 | https://github.com/official-stockfish/Stockfish/commit/1548538ede , /commit/c56bd10cb5 , /commit/df01cb7ed3 (full
  messages via mine_commits --show) | GPL-3.0, commit messages only, no diff | 1548538 (issue 7156, PR 7170): LMR
  negative reductions chained up to MAX_PLY; fix stops such extensions deep in the tree; non-regression <-1.75,0.25>
  STC 154,752 games LLR 2.94, LTC 55,782 games LLR 2.94. c56bd10 (PR 6235): a helper read the end of a move list
  before the quiet generation stage (undefined contents), "really rarely triggered", found via a wrong bench in a test;
  non-regression STC 203,008 games (default book) and 31,616 games (stalemates book). df01cb7 (PR 6703): always write
  into the buffer, grow the size only for valid entries; "No functional change", local +0.67 % +- 0.19 | T12B-02
- E3 | official-stockfish/Stockfish commit titles (tools/mine_commits.py --grep 'sanitiz|valgrind|asan|ubsan|tsan', 17
  of 3,000 cached) | GPL-3.0, titles only | sanitizer CI history: 7ede1ed "Allow for address sanitizer" (2019, #2119),
  3802cdf "Makefile: Extend sanitize support" + 98cbaa6 "Enhance CI to error on leaks" (2021), 4be94f4 "Update
  sanitizer CI to ubuntu 22.04" (2023), fb07281 TSan false positives (2024), b7f1734 "Fix Sanitizer Tests" (2024),
  5380403 valgrind harness for expected-failure tests (2026), 7316ef4 oversized Syzygy symbol tables (2026), 23df829
  negative time values (2026) | T12B-02
- E4 | https://github.com/official-stockfish/Stockfish/commit/23df82905b , /commit/7316ef4e86 , /commit/5380403393 ,
  /commit/b7f17346e5 (messages via mine_commits --show) | GPL-3.0, commit messages only | 7316ef4 (PR 7237): a table's
  symbol count is read as 16 bits but three buffers hold 4096 entries; counts above the size now take the existing
  corrupt-table path; "All 75 upstream instrumented tests passed on a debug build with AddressSanitizer and
  UndefinedBehaviorSanitizer"; bench unchanged (1,559,611 nodes); no runtime reproducer was run. 5380403 (PR 7081):
  failure-path tests hid leak reports because the error exit code was taken as the expected one; an expect_failure flag
  keeps the memory-error check on. 23df829 (PR 7257): some GUIs send negative remaining time; clamp it; "No
  functional change". b7f1734: title only (PR 5692) | T12B-02; 23df829 = evidence for notes/T07/UCI_EDGE_CASES.md
  case 28 (Forge already clamps negative clocks to 0 at src/uci.cpp:99-102)
- E5 (forum 1 of 5) | https://talkchess.com/viewtopic.php?p=801104 ("is there a worst position than this one", 2019-06-09,
  first page, 10 posts) | forum text (no licence stated), ideas/facts only | FEN 3Q4/1Q4Q1/4Q3/2Q4R/Q4Q2/3Q4/1Q4Rp/1K1BBNNk
  w - - 0 1 = 218 moves ("Reachable or not this is 218 moves"); a proof game to move 83 is posted (not replayed); one
  engine sized its list to 128 from a testing maximum of 100; "so 256 is needed"; no pseudo-legal maximum and no
  capture maximum stated | T12B-02, T12B-04
- (search, no source) WebSearch "chess position maximum 218 legal moves FEN ... pseudo-legal moves maximum" -> E5; no
  page states a maximum number of pseudo-legal moves or of captures
