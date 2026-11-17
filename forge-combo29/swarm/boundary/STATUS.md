# STATUS — swarm/boundary

**State: PUSHED, six measured rows, five clean, no engine defect found in this area.**

## Done and evidenced

| item | where | result |
|---|---|---|
| Build + four honesty pins | FINDINGS.md header | all four matched |
| Self-test: checkers fire on planted faults | `scripts/selftest.py`, `evidence/selftest.txt` | 15/15 PASS |
| Row 1 — one ply from stalemate | `evidence/matrix_rows.json` | 3/3 `cp 0`, control `cp 1208` |
| Row 2 — one ply from insufficient material | same | 5/5 drawn → 0.00; won control non-zero |
| Row 3 — forced clock-resetting capture | same | clock handled correctly, `−486` vs `−471` |
| Row 4 — all-pawn-moves at halfmove 99 | same | never 0.00; scores win at d1 and d12 alike |
| Row 5 — `0000` at every mate root | same | 6/6 `0000`, 0 moves, no inconsistency |
| Row 6 — the three `0000` shapes | `evidence/family6_0000.json` | all reproduced; `info string` only on restriction |
| Fifty-move band `H > 100 − p` | `evidence/family4_fifty.json` | p=2 and p=4 both reproduce exactly |
| Repetition roots | `evidence/family3_repetition.json` | threefold/fourfold bail; twofold control searches |
| Mate in 1 played / avoided | `evidence/family1_mate.json` | 50/50 and 50/50 at two budgets |

## Not done — stated plainly

- **Loser-stalemate preference** (a losing side that can *choose* stalemate):
  **not measured.** Two exhaustive constructions found zero fixtures; the third
  was still scanning at the cutoff. Row 1 covers unavoidable stalemate only.
- **Static-vs-search disagreement at insufficient material** (`eval` says −138 /
  −155 / +107 where search says `cp 0`): recorded as a **lead**, not a finding.
  Every instance is a drawn root, so the bail hides the static number from a
  client. Whether it reaches a non-drawn searched node is untested.
- **Band beyond `p = 4`** (p = 6, wider clocks): not swept.
- **PC build**: all rows are on the base build only. §1b reports every GUI
  hazard present on both; I did not re-verify these six rows on PC.

## Files

- `FINDINGS.md` — result first, then evidence, then withdrawals, then gaps.
- `scripts/forge_drv.py` — UCI driver; raises `RefusedFen`; `pv_shape()`
  distinguishes present-and-empty from absent.
- `scripts/selftest.py` — planted-fault proofs (15 checks).
- `scripts/stalemate.py`, `scripts/construct.py`, `scripts/fixtures.py` —
  fixture construction. `fixtures.py` is superseded by `construct.py` +
  `stalemate.py` but kept because its random generator's *failure* to reach
  "every move stalemates" in 2,000,000 tries is part of the record.
- `scripts/family1_mate.py`, `family3_repetition.py`, `family4_fifty.py`,
  `family5_material.py`, `family6_0000.py`, `matrix_rows.py`.
- `evidence/*.json` — per-row raw records including full `info` lines.

## Known fixture hazards, recorded so they are not repeated

1. The engine **truncates** a move list at the first illegal token and searches
   the prefix (or the root, if the first token is bad). `family3_repetition.py`
   now builds every list through a python-chess replay and asserts legality.
2. `is_valid()` is not enough — three fixtures passed it and were still not
   what the row asserted (`BAD_CASTLING_RIGHTS`; side-to-move in check;
   checkmate where the loop expected a choice). Every row asserts its
   structural claim separately.
3. A tuple-in-a-comprehension predicate is always truthy. It reported 26/26
   stalemating where the truth was 4/26.
