# T12B verify (adversarial), 2026-11-05 01:43-01:58 PC clock

No earlier VERIFY.md existed (no hand-back from the worker; everything on disk was checked). Scratch: F:/odr/work/T12B-verify/.
Format: card | claim | verdict | evidence.

## T12B-01 (full card)
- T12B-01 | lock search.cpp:361 unguarded write, :398 read-out, :453 `std::array<Move, 64> bad_captures_{}`, :454 counter right after it; :1051 is_legal; :894 / :781 ply guards; :1034-1035, :1186-1187 tried arrays | CONFIRMED | forge_has.sh + sed on src_al1s198_clean, all lines as cited.
- T12B-01 | branch fable-review-buffix 8632e8ab, fix a9cea71f (array sized MoveList::Capacity + static_assert, 5 lines in src/search.cpp), fixture commit ab2aa56b, tests/bad_capture_tests.cpp:141 holds the FEN 3r4/Pn1Q1p2/... w - - 0 1 | CONFIRMED | git log / git show in the main repo; line 141 is the FEN line.
- T12B-01 | r3-stack fix b0c3882b "both buffer variants" | CONFIRMED | commit title says "in both buffer variants + regression test".
- T12B-01 | census: noisy 69, SEE-losing 68, promotions 4, not in check, accepted | CONFIRMED | buffix64/prove.log lines 2 and 6.
- T12B-01 | mutant exit 127 under -D_GLIBCXX_ASSERTIONS; fixed engine 6/6; depth 3, 396 nodes, bestmove d3b1 | CONFIRMED | final_mutant.log:2 "mutant test exit 127"; final_fixed.log:13 "accepted=6 failures=0", :2 nodes=396 bestmove=d3b1.
- T12B-01 | bench pins d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354 | CONFIRMED | same string in the project skills (engine-verify / ltopgo).
- T12B-01 | O30 trees spsa_1 / v2port_1 / harness/h1 still 64 entries; R15 cands 0 hits | CONFIRMED | grep: spsa_1 search.cpp:497, v2port_1 :454, h1 :454 `std::array<Move, 64> bad_captures_{}`; D:/o15/cands 0 files.
- T12B-01 | Stockfish c56bd10cb5 = PR 6235, "really rarely triggered", found via a wrong bench; ee515ad = root PV longer than MAX_PLY; Caissa 136d3d0 overflown-move history | CONFIRMED | mine_commits --show (messages only); 136d3d0 title "Fix lack of history bonus for overflown best move".
- T12B-01 | "identity bench x5 / perft5 / kiwipete ALL OK" | CONFIRMED | git show a9cea71f:fable_review/logs/identity.log: bench d11-d22 = 312866/862329/3024920/12389307/34048354 OK, perft5 4865609 OK, kiwipete 193690690 OK, ALL OK.
- T12B-01 | no Elo claim, estimate 0 Elo UNPROVEN, nps effect UNPROVEN, crew 1-1.5 h | CONFIRMED | card text.
- T12B-01 | duplicate? | NOT A DUPLICATE | no card in cards/*/ (88 files) proposes the fix; T04 BUG_CHECKLIST row 9 is a checklist row ("likely unreachable") that this card corrects; T05C-02 is the zero-fill speed card and is cited as a pairing, not repeated. TRIED_GATES grep 'bad_capt|buffix|sanitiz|fuzz|assert|uci|fen' = 0 of 110.

## T12B-02 (full card)
- T12B-02 | Stockfish 7316ef4e86 = PR 7237, "All 75 upstream instrumented tests passed on a debug build with AddressSanitizer and UndefinedBehaviorSanitizer", bench 1,559,611 unchanged, no runtime reproducer | CONFIRMED | mine_commits --show. (The message also names a vendor tool; the card correctly does not copy it.)
- T12B-02 | 5380403393 = PR 7081 expect_failure flag keeps memory checks on | CONFIRMED | message.
- T12B-02 | 1548538ede = issue 7156 / PR 7170, non-regression STC 154,752 LLR 2.94 and LTC 55,782 LLR 2.94, bounds <-1.75,0.25> | CONFIRMED | message (W/L/D 39489/39403/75860 and 14432/14254/27096 = +0.2 and +1.1 Elo, non-regression as stated).
- T12B-02 | 3d92950859 = PR 5383, repro FEN 7K/P1p1p1p1/2P1P1Pk/6pP/3p2P1/1P6/3P4/8 w - - 0 1 + go nodes 1000000, STC 143,936 LLR 2.93 | CONFIRMED | message.
- T12B-02 | sanitizer CI since 2019: 7ede1ed (2019-04-27 "Allow for address sanitizer" #2119), 98cbaa6 (2021-06-03 "Enhance CI to error on leaks"), 4be94f4 (2023-08-13 "Update sanitizer CI to ubuntu 22.04") | CONFIRMED | gh api commits (titles only; outside the miner cache).
- T12B-02 | talkchess p=801104: FEN 3Q4/1Q4Q1/4Q3/2Q4R/Q4Q2/3Q4/1Q4Rp/1K1BBNNk w - - 0 1, "Reachable or not this is 218 moves", "so 256 is needed", one engine's list 128 from a testing maximum of 100, no pseudo-legal or capture maximum stated | CONFIRMED with a note | fetched first page (10 of 30 posts). Thread title is "max number of pseudo legal move" (2019-06-09), not the phrase quoted in sources.md E5; the OP calls 218 "pseudo legal moves". The card's "`go perft 1` should list 218 ... not run here" is honest; 218 stays an external count until the fixture is run.
- T12B-02 | existing CI: opus-r13-san.yml = self-play smoke (4 games x <= 160 plies, go nodes 20000, go perft 1 legality, stderr scan), g++ 13 ASan+UBSan | CONFIRMED | skill forge-candidate-checks lines 33-37.
- T12B-02 | "today's sanitizer row is built with NDEBUG: it cannot fire the MoveList assert" | CORRECTED | the NDEBUG statement in skill forge-engine-verify (lines 36-37) covers the three CMake CI build types only; opus-r13-san.yml at 3cfdb975 (main repo) compiles with a plain `g++ -std=c++20 -O1 -g -fsanitize=address,undefined ...` line, 0 hits for NDEBUG, so asserts are live in that row. The row still has no crafted positions, no -D_GLIBCXX_ASSERTIONS and never meets a 65-loser node, and the lock's bad_captures_ write has no assert at all, so the card's delta stands; the card sentence now carries the correction. notes/T12B/TABLE.md row A2 ("compiled out in every CI build") is wrong in the same way (not edited).
- T12B-02 | forge_has 'Capacity|assert\(' -> board.hpp:55, 57 only asserts; :51 Capacity 256, :71 array | CONFIRMED | grep.
- T12B-02 | buffix annealer imports python-chess (GPL) at fable_nnue_losing_search2.py:4 | CONFIRMED | line 4 `import ... chess`, line 5 `from chess import ...`.
- T12B-02 | no Elo claim; crew 4-6 h; UNPROVEN label | CONFIRMED | card text.
- T12B-02 | duplicate? | NOT A DUPLICATE, overlap declared | cards/T12/T12-03 level 8 is the existing ASan/UBSan self-play and level 6 the saturation set; T12B-02 states its delta (assert-enabled build, crafted limit fixtures, transcripts, mutant controls). No other card proposes crafted-FEN fixtures.

## T12B-03 (one-liner)
- T12B-03 | uci.cpp:30-33 reads up to six tokens greedily, :35-38 set_fen failure -> info string + return (previous position kept), :46 `if (token != "moves") return;`, :47-51 illegal token -> info string + return, :99-102 std::max(0, .) on wtime/btime/winc/binc; board.cpp:212 six fields required | CONFIRMED | sed on the lock source.
- T12B-03 | "a token other than moves after the FEN is ignored (uci.cpp:46)" | CORRECTED | at :46 the whole command is dropped silently (no info string in that case); card now says so ("corrected by verify").
- T12B-03 | Stockfish 23df82905b = PR 7257 "Sanitize negative time values", "No functional change" | CONFIRMED | message.
- T12B-03 | fastchess sends six-field FENs ("or every UHO gate would fail") | UNVERIFIABLE here | inference from the crew's gates running; no transcript opened.
- T12B-03 | crew h 1, UNPROVEN, no Elo claim | CONFIRMED.

## Rules
- Reading rule | CONFIRMED | all Stockfish items are commit messages via tools/mine_commits.py or gh api commit titles; no source file, diff or test file opened by the worker (sources.md) or by this verify. Caissa (MIT) title only.
- Tuned constants | CONFIRMED | none carried over; the only size proposed (MoveList::Capacity 256) is the lock's own constant.
- Licence rows | CONFIRMED | tools/licence_at.py --row re-run for c56bd10cb5, 7316ef4e86, 5380403393, 1548538ede, 3d92950859, 23df82905b: GPL-3.0 (Copying.txt), identical to notes/T12B/licences.md. df01cb7ed3 and b7f17346e5 rows not re-run (cited in notes only); the Caissa (MIT) row lives in notes/T04/licences.md and was not re-run either.
- Names | CONFIRMED | grep for vendor / model-company names in cards/T12B and notes/T12B: 0 hits; card_lint 0 findings.
- Caps | CONFIRMED | 3 cards (2 full + 1 one-liner) <= 4; 7 external sources; 0 engines deep-read; crew hours in every card.
- Lint | CLEAN | card_lint: 3 cards, 0 findings, 0 PENDING (re-run after the T12B-03 correction).

## Counts
checked 33 items (11 on T12B-01, 12 on T12B-02, 5 on T12B-03, 5 rule checks): CONFIRMED 30 (the two duplicate checks counted as confirmed not-duplicate), CORRECTED 2 (T12B-02 sanitizer-row NDEBUG claim; T12B-03 uci.cpp:46 wording), UNVERIFIABLE 1 (T12B-03 fastchess six-field FEN inferred), VIOLATION 0, DUPLICATE 0. Lint clean after both corrections.
