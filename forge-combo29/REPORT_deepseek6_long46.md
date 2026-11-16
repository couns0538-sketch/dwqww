# REPORT — deepseek6, long 46 (UCI robustness under ASan + UBSan, the twelve cases)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long46/ · claimed with the stamps-first rule (the claim time is stamps.txt's first line); PREDICTION.md before the probing runs.

## 1. Three lines
**Asked:** the twelve UCI robustness cases (illegal move in a move list, Hash 0, go+stop, a valueless setoption, go depth 0, an unknown command, a 600-ply game, go infinite+stop, ponder+ponderhit, ucinewgame during a search, Hash changed between searches, a 2,000-char garbage FEN) each in a fresh process under ASan+UBSan, with the answer lines, bestmove legality, sanitizer lines and exit codes.
**Answer:** **zero sanitizer lines across all twelve cases; exit 0 everywhere; every bestmove that appeared is legal for its position (python-chess); the four known answer lines reproduced verbatim** ("illegal move e1e3"; "invalid value for option Hash"; "invalid value for option LmpBase"; the garbage FEN refused with "invalid FEN: FEN must contain six fields"). **The held-back number: after the refused illegal move the engine KEEPS THE LAST LEGAL POSITION — `go perft 1` then prints 29** (the replies to 1.e4 e5) — my prediction guessed 20 or 430 and is KILLED by the measurement; the mechanism (skip the illegal move, keep the legal prefix) is now measured. The unknown command is silently ignored (two readyoks around it ✓ the known). The release-build probe agrees on every case line except three timing-dependent bestmove VALUES (all legal).
**How sure:** certain of the twelve case records (each its own process, stdout+stderr captured, the sanitizer lines counted from stderr).

## 2. Honesty numbers
The sanitizer build /tmp/l46_san/build/forge (clean 6b98f217, RelWithDebInfo + ASan/UBSan); the plain build cross-probe in plain/.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (stamps first line) | done | stamps.txt | the claim time first |
| the twelve cases under the sanitizer build | done | c*.txt (12 files), probe_out.txt | 0 sanitizer lines; exit 0 x12 |
| the four known answer lines | done | the grep in stamps-adjacent output | all four verbatim |
| the held-back perft-1 number | done | c1_illegal_move.txt (nodes 29) | 29 — my guess killed |
| the release cross-probe | done | plain/c*.txt, probe_plain.txt | identical except 3 timing bestmoves |
| prediction own commit first | done | PREDICTION.md | 2-8 held; 1's guess killed |

## 4. Findings
1. **The engine's illegal-move handling keeps the legal prefix**: after "position startpos moves e2e4 e7e5 e1e3" the position is the one AFTER e2e4 e7e5 (perft 1 = 29) — the illegal move is skipped, not fatal, and not silently applied.
2. **The UCI layer is robust under the sanitizer across all twelve stresses** — including ucinewgame DURING a depth-30 search and a Hash change between searches without ucinewgame (no crash, no sanitizer line, legal bestmoves).
3. **The garbage FEN is refused with a field-count message** (six fields expected) — consistent with long 37's validator.
4. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 13 (the item, the known answers, and the stamps-order correction — applied here: the claim time is this folder's stamps.txt first line).

## 7. What I did NOT do
Case variants beyond the twelve (e.g. a ponderhit WITHOUT go ponder — untested, unasked).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
None.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long46/stamps.txt
?? forge-combo29/REPORT_deepseek6_long46.md
?? forge-combo29/tests_deepseek6_long46/c10_ucinewgame_during_search.txt
?? forge-combo29/tests_deepseek6_long46/c11_hash_between_searches.txt
?? forge-combo29/tests_deepseek6_long46/c12_garbage_fen.txt
?? forge-combo29/tests_deepseek6_long46/c1_illegal_move.txt
?? forge-combo29/tests_deepseek6_long46/c2_hash_zero.txt
?? forge-combo29/tests_deepseek6_long46/c3_go_stop.txt
?? forge-combo29/tests_deepseek6_long46/c4_setoption_no_value.txt
?? forge-combo29/tests_deepseek6_long46/c5_go_depth_0.txt
?? forge-combo29/tests_deepseek6_long46/c6_unknown_command.txt
?? forge-combo29/tests_deepseek6_long46/c7_600_ply_game.txt
?? forge-combo29/tests_deepseek6_long46/c8_go_infinite_stop.txt
?? forge-combo29/tests_deepseek6_long46/c9_go_ponder_ponderhit.txt
?? forge-combo29/tests_deepseek6_long46/plain/
?? forge-combo29/tests_deepseek6_long46/probe_out.txt
?? forge-combo29/tests_deepseek6_long46/probe_plain.txt
$ ls forge-combo29/tests_deepseek6_long46/
c10_ucinewgame_during_search.txt
c11_hash_between_searches.txt
c12_garbage_fen.txt
c1_illegal_move.txt
c2_hash_zero.txt
c3_go_stop.txt
c4_setoption_no_value.txt
c5_go_depth_0.txt
c6_unknown_command.txt
c7_600_ply_game.txt
c8_go_infinite_stop.txt
c9_go_ponder_ponderhit.txt
CLAIM.txt
plain
PREDICTION.md
probe_out.txt
probe_plain.txt
stamps.txt
uciprobe.py
```
