# S-C1 — seat 12's check of seat 06's finding S-F2

Finding checked: **S-F2 (seat 06)** — "a FEN whose ep square is unreachable is REFUSED with
`info string invalid FEN: inconsistent en-passant square` (board.cpp:325-333)".

Verdict: **CONFIRMS**, with one addition the finding does not say.

## What I did (my own harness, not the finder's script)

`check.py` — fresh process per FEN, sends `position fen <FEN>`, `isready` (reads every line up to
`readyok`), `go depth 2`, waits for `bestmove`; compares each FEN against python-chess 1.11.2 and
asks whether the engine's bestmove is legal there. `cases.txt` is my own list; `out_release.txt`
and `out_asan.txt` are the raw records (two lines per case: the record, then the answer lines).
Rerun: `python3 forge-combo29/swarm/12/check1/check.py ~/build/release/forge forge-combo29/swarm/12/check1/cases.txt /tmp/o.txt`

## Result (pasted from out_release.txt)

| case | refused | python-chess accepts | bestmove legal |
|---|---|---|---|
| ep_unreachable_startpos_e6 | **True** | True | True |
| ep_unreachable_no_pawn_on_5th | **True** | True | True |
| ep_unreachable_black_side_e3 | **True** | True | True |
| ep_square_with_no_enemy_pawn | **True** | True | True |
| ep_square_wrong_rank_rank3_white | **True** | True | True |
| ep_square_on_rank_1 | **True** | True | True |
| ep_square_on_rank_8 | **True** | True | True |
| ep_nonempty_square_a6 | **True** | True | True |
| ep_reachable_after_double_push | False | True | True |
| ep_reachable_white_to_move_g6 | False | True | True |
| **ep_legal_after_e4_black_to_move** | **False** | True | True |
| **ep_legal_after_d4_black_to_move** | **False** | True | True |
| **ep_legal_after_e5_white_to_move** | **False** | True | True |
| ep_legal_capture_possible | False | True | True |

After a refusal the engine keeps the previous position and answers with a legal bestmove, so a
refusal is not itself a search fault. Same table under ASan+UBSan, 0 sanitizer lines.

## Beyond the finding (this is the part that is NEW)

Seat 06's sentence says "a FEN whose ep square is *unreachable*". Measured here, the test the
engine actually applies is narrower than reachability: a legitimate FEN that records the ep square
after a double push **with no enemy pawn able to capture** is ACCEPTED (the last three rows). So the
refusal is not "unreachable" but "no pawn of the side to move stands on the 5th rank next to the
square" (plus the structural checks: empty square, empty origin square, right rank for the side to
move). Consequence for a reader of S-F2: FEN producers that always write the ep square after a
double push are not refused, which is the compatible half of the rule.

## How sure

High on the 14 cases; the two exe are the honesty-checked release build
(sha256 e06310ec…, `id name Chess Engine Forge 6.4.24 candidate`) and the ASan+UBSan build of the
same commit. Not checked: what `board.cpp` says line by line — that part of S-F2 I did not read.
