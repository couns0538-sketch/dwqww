# REPORT_job2 — seat 11, area 1: extreme numbers in the FEN fields

## 1. What was asked
Extreme values in FEN fields: halfmove clock 0 / 99 / 100 / 150 / 9999 / -1; fullmove 0 / 1 /
10^9; ep square on a wrong rank; two kings of one colour; pawns on rank 1 or 8. Record the
answer lines, `go depth 4`, sanitizer lines, and perft 2 against python-chess where
python-chess accepts the FEN.

## 2. The answer
30 cases, **0 crashes, 0 sanitizer lines, 0 illegal bestmoves**. The engine refuses every
structurally impossible field and accepts every extreme-but-valid number. No defect found in
this area: the numeric parsing is bounded by `halfmove < 0` and `fullmove < 1` (board.cpp:266)
and the en-passant square is checked twice, for shape (file a–h, rank 3/6) at board.cpp:319
and for consistency (square empty, origin empty, pawn present) at board.cpp:325–333.
Two things worth knowing, neither a fault: a leading `+` is accepted in the numeric fields
(python-chess does the same), and fullmove up to 2^31 is accepted without overflow.

## 3. How sure
High. Every case is a single hand-written FEN, the raw output is committed, and each
"accepted" row was cross-checked with python-chess (legal bestmove verified).

## Honesty numbers
Unchanged from `HONESTY.txt`: 312866 / 862329 / 3024920 / 4865609, all four match.
Sanitizer proofs from job 1 (35 __asan_ / 15 __ubsan_ symbols; planted fault counted).

## 4. Table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| halfmove 0/99/100/150/9999 | done | `job2/run/results.jsonl` j2-01..05 | 5/5 ACCEPTED (as predicted) |
| halfmove -1 | done | j2-06 | REFUSED `invalid FEN fields` (as predicted) |
| fullmove 0 / 1 / 10^9 | done | j2-07..09 | refused / accepted / accepted (refusal count 1, as predicted) |
| fullmove 2^31 | done | j2-29 | ACCEPTED, no overflow |
| fullmove 21 digits | done | j2-10 | REFUSED `FEN must contain six fields` (my case was malformed: 21 digits) |
| ep on wrong rank e4/e5/e1/e8 | done | j2-11..14 | all REFUSED `invalid en-passant square` |
| ep file i | done | j2-15 | REFUSED `invalid en-passant square` |
| ep on a valid rank but no pawn | done | j2-16 | REFUSED `inconsistent en-passant square` |
| ep reachable (black pawn on e5) | done | j2-17 | ACCEPTED, bestmove c2c4 |
| two/three kings one colour | done | j2-18, j2-19, j2-21 | all REFUSED `invalid FEN fields` |
| pawns on rank 1 / rank 8 | done | j2-22..27 | all 6 REFUSED `pawn on promotion rank` |
| leading `+` in a number | done | j2-30 | ACCEPTED (python-chess accepts too) |
| perft 2 vs python-chess | done | `job2/perft2_compare.txt` | 10 comparable cases, **0 differences** |
| sanitizer lines | done | `job2/run/` | 0 (proofs as job 1) |

Perft 2 comparison (`job2/perft2_compare.txt`): every case both engines accept gives the same
node count — j2-01..05 = 25, j2-17 = 600, j2-20/28/29/30 = 25. **0 differing cases.**
Where python-chess accepts and the engine refuses, the engine is the STRICTER one (fullmove 0,
two kings of one colour, pawns on rank 1/8, wrong-rank ep squares). That direction is safe:
the engine never builds a board python-chess would call impossible by *accepting* it.

## 5. Findings
No new engine defect. The observations below confirm existing knowledge or are notes.

- Numeric bounds are correct. Evidence `job2/run/results.jsonl`, cases j2-06 (`halfmove -1`
  → `invalid FEN fields`) and j2-07 (`fullmove 0` → same). Shows it again:
  `printf 'uci\nposition fen 4k3/8/8/8/8/8/8/4K3 w - - -1 1\nisready\nquit\n' | /home/ubuntu/builds/rel/forge`
- The en-passant square has TWO independent checks and both fire. j2-16 (`... e3 ...`, a
  legal-rank square with no pawn beside it) gives `inconsistent en-passant square` — this
  matches seat 06's S-F2 and seat 12's S-C1 of seat 06, independently.
- Pawn on the promotion rank is caught in the placement loop (board.cpp:253) before any
  legality question, for both colours and both ranks — 6/6 refused.

## 6. Suspicions, not proven
- python-chess ACCEPTS two kings of one colour, adjacent kings, and pawns on rank 1/8 (it
  reports them as status flags rather than refusing to build the board). The engine refuses
  them. So "python-chess accepts" is not the same as "legal"; I read the engine's refusal as
  correct and python-chess's accept as lenient, but I did not read python-chess's source.
- `std::istringstream >> long long` on a 19-digit field (the largest that fits) was not
  tested; j2-10 had 21 digits and failed at the token level, not the number level.
- A leading `+` is accepted by both engines, so I treat it as harmless; the FEN grammar has
  no sign, so a strict third-party tool may disagree.

## 7. What I did NOT do
- Did not re-run the perft-2 comparison for every accepted FEN (only the legal-bestmove check,
  which is what the brief's job 2 asks for).
- Did not test halfmove values between 150 and 9999 exhaustively (the bound is monotonic).
- Did not test extreme values *combined* with other malformations.

## 8. What I am NOT sure about
- Whether the 50-move rule at halfmove 9999 should have produced a draw score at the root.
  job 2 does not ask for scores, and my prediction's point 9 was about a crash, which did not
  happen. Draw scoring is area 5's subject.

## 9. Times
See `job2/stamps.txt`.

## 10. Last command's output
```
$ ls job2/
PREDICTION.md  cases.tsv  run/  stamps.txt
$ git status --short   (clean after commit)
```
