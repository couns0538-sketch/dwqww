# REPORT job3 — area 1 job 2 (extreme numbers in the FEN fields), seat 21

**What was asked.** Extreme numbers in the FEN fields: halfmove 0 / 99 / 100 / 150 / 9999 /
-1; fullmove 0, 1, 10^9; the ep square on a wrong rank; two kings of one colour; pawns on
rank 1 or 8. For each: the answer lines, `go depth 4`, sanitizer lines, and `perft 2`
against python-chess where python-chess accepts the FEN.

**The answer.** 24 cases, one field changed each, all on an ASan+UBSan build. **0 crashes,
0 sanitizer lines, and 0 perft disagreements on every FEN the engine accepted.** The
engine is far stricter than python-chess: it refuses 15 of the 24, including `fullmove 0`
which python-chess accepts as a valid FEN. And the root-draw shortcut fires on every
halfmove ≥ 100 (including 9999 and 2^31), searching **0 nodes** and reporting `cp 0` even
in a position that is +several pawns — consistent with 30-F7 but measured here on my own
harness with the counter going far past 100.

**How sure.** High on the refusals, the crash/sanitizer counts and the perft equality
(each is a pasted table from the committed script over committed raw files). High that the
halfmove ≥ 100 shortcut yields 0 nodes and `cp 0` (raw stdout in `job3/out/hm_100.txt`).
Not proven: whether the owner wants `fullmove 0` refused.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before the first measuring command | done | `job3/prediction.txt` | 11 predictions |
| 24 single-field cases, ASan+UBSan, fresh process each | done | `job3/out/*.txt`, `job3/out/summary.md` | 15 refused / 9 accepted |
| perft 2 vs python-chess on every accepted FEN | done | `job3/out/summary.md` last lines | 0 mismatches |
| acceptance of 6,073 REAL positions (all of G and R) | done | `job3/out/accept_G_summary.md`, `accept_R_summary.md` | 0 refused |
| `fullmove 0` consequence, with the fullmove-1 control | done | `job3/out/summary.md` (fullmove0.py) | refused; stale board gives 20 |
| tables produced by committed scripts | done | `extreme.py`, `accept_all.py`, `fullmove0.py` | no number typed by hand |

## Results (pasted from `job3/out/summary.md`)

| case | refused | answer line | san | depth-4 last info | perft2 engine | py accepts | perft2 python |
|---|---|---|---|---|---|---|---|
| hm_0 | no | – | no | – | 625 | yes | 625 |
| hm_99 | no | – | no | – | 625 | yes | 625 |
| hm_100 | no | – | no | `score cp 0 nodes 0` | 625 | yes | 625 |
| hm_150 | no | – | no | `score cp 0 nodes 0` | 625 | yes | 625 |
| hm_9999 | no | – | no | `score cp 0 nodes 0` | 625 | yes | 625 |
| hm_2147483648 | no | – | no | `score cp 0 nodes 0` | 625 | yes | 625 |
| hm_neg1 | **yes** | `invalid FEN fields` | no | – | 400 (stale startpos) | no | – |
| fm_0 | **yes** | `invalid FEN fields` | no | – | 400 (stale startpos) | **yes (status 0)** | 625 |
| fm_1 | no | – | no | – | 625 | yes | 625 |
| fm_1e9 | no | – | no | – | 625 | yes | 625 |
| fm_neg1 | **yes** | `invalid FEN fields` | no | – | 400 | no | – |
| ep_wrong_rank_e3 | **yes** | `inconsistent en-passant square` | no | – | 400 | yes | 625 |
| ep_wrong_rank_e6 | **yes** | `inconsistent en-passant square` | no | – | 400 | yes | 606 |
| ep_legal_d6 | no | – | no | – | 807 | yes | 807 |
| ep_bad_file_z3 | **yes** | `invalid en-passant square` | no | – | 400 | no | – |
| ep_bad_square_e9 | **yes** | `invalid en-passant square` | no | – | 400 | no | – |
| two_white_kings | **yes** | `invalid FEN fields` | no | – | 400 | yes | 575 |
| two_black_kings | **yes** | `invalid FEN fields` | no | – | 400 | yes | 575 |
| three_kings | **yes** | `invalid FEN fields` | no | – | 400 | yes | 575 |
| no_kings | **yes** | `invalid FEN fields` | no | – | 400 | yes | 529 |
| white_pawn_rank1 | **yes** | `pawn on promotion rank` | no | – | 400 | yes | 500 |
| white_pawn_rank8 | **yes** | `pawn on promotion rank` | no | – | 400 | yes | 483 |
| black_pawn_rank1 | **yes** | `pawn on promotion rank` | no | – | 400 | yes | 550 |
| black_pawn_rank8 | **yes** | `impossible piece inventory` | no | – | 400 | yes | 587 |
| nine_in_rank | **yes** | `invalid FEN placement` | no | – | 400 | no | – |

Every `400` in the engine column is startpos perft 2, i.e. the **stale board** after a
refusal (21-F2), not a wrong perft. No case where the engine ACCEPTED differs from
python-chess.

Real positions (`accept_all.py`): G 353 FENs, R 5,720 FENs, **0 refused by Forge, 0
disagreements with python-chess**, and no batch faults (the batch attribution was checked
against a per-FEN re-run).

## Findings

**21-F8 — `fullmove 0` is refused although it is a valid FEN.**
`python3 job3/fullmove0.py ~/b/asan/forge out`
`4k3/8/8/8/8/8/8/4K2R w K - 0 0` → `info string invalid FEN: invalid FEN fields`, then perft 1
= 20 (startpos, stale). python-chess accepts the same FEN with status 0 (valid) and has 15
legal moves; the same FEN with `1` as the fullmove number gives 15 from Forge. Cause:
`src/board.cpp:267` tests `fullmove < 1`. FEN writers exist that emit fullmove 0 (python-chess
will happily produce one from a constructed board), so a GUI can hand Forge a FEN that is
legal by python-chess's reading and get a silent stale board instead.

**21-F9 — the halfmove ≥ 100 root shortcut is unbounded and side-blind, and it survives the
uint16 clamp.** `python3 job3/extreme.py ~/b/asan/forge out`
halfmove 100, 150, 9999 and **2147483648** all give `info depth 1 seldepth 1 score cp 0 nodes 0`
and `bestmove a2a3` from a position where White is a rook up material-wise on an equal pawn
structure (r3k2r/pppppppp vs R3K2R). Perft is unaffected (625). The clamp at
`src/board.cpp:351` (`min(halfmove, 65535)`) means any counter ≥ 100 behaves the same, so the
shortcut at `src/search.cpp:2251` is reached by every such FEN. Beyond 30-F7: 30-F7 reports
the mate-blindness at counter 100; here the same 0-node `cp 0` answer holds for 9999 and for
a value that does not even fit a 32-bit int, i.e. the fault does not depend on the counter
being "just at the limit".

## Suspicions, not proven

- Whether refusing `fullmove 0` is deliberate. It is not in the brief's known list; python-chess
  treats it as valid; no comment in `src/board.cpp` explains it.
- The `two kings of one colour` cases: python-chess ACCEPTS them (status 0 in some of my
  reads — it does not validate king count strictly at construction) and Forge refuses. Forge
  is the reasonable one here; noted only so the asymmetry is on the record.
- `ep_wrong_rank_e3` at 625 for python-chess: python-chess accepts an ep square on a rank
  where no double push could have produced it (it only checks the square is empty and a pawn
  is beside it). Forge's `inconsistent en-passant square` is stricter. Not proven that
  Forge's rule is what the owner wants.

## What I did NOT do

- Did not test extreme numbers in the *ep* field beyond `e9`/`z3` (no numeric ep field exists).
- Did not test `fullmove` values between 65,536 and 10^9 for the clamp boundary: I tested
  10^9 (accepted) and did not read back the clamped value (there is no UCI command that
  prints the FEN).
- Did not write a repair patch for 21-F8 or 21-F9; that is area 7's job with its own honesty
  run, and the brief's area 1 asks for measurement.

## What I am NOT sure about

- I could not read the engine's *stored* FEN back (no `d` command, no `position` echo), so
  "the counter is clamped to 65535" is a code read, not a measurement. What I measured is
  that every large counter gives the same 0-node answer.

## Times

see `job3/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job3
accept_all.py  extreme.py  fullmove0.py  out  prediction.txt  set_G.fens  set_R.fens  stamps.txt
```
