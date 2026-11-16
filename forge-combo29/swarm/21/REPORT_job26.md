# REPORT job26 — WIDER (multi-character) mutation alphabet, both builds

**What was asked.** (My own next step, named as the untested direction in my earlier reports.) Every
sweep before this used single-character edits. This one uses eight multi-character corruption
kinds, which reach damage no single edit can.

**The answer.** The wider alphabet finds **no new class of accepted-invalid FEN — in fact it finds
none at all**: 18,552 refused, 1,448 accepted, and **every one of the 1,448 is also valid for
python-chess** (0 invalid). Both builds agree on all 20,000 verdicts. My prediction P2 (that a new
accepted-invalid class would appear) was **wrong**, and the reason is informative.

**How sure.** High. Committed generator, committed input file, both builds swept
(`job6/fen_rerun.py` for the base, `job19/fen_sweep_pc20.py` for the PC under PC20), per-FEN tables
committed, and the kind breakdown computed from the raw table.

## Table (both builds identical)

| measure | base build | PC build under PC20 |
|---|---|---|
| total | 20,000 | 20,000 |
| refused | 18,552 | 18,552 |
| accepted | 1,448 | 1,448 |
| accepted & python-valid | **1,448** | **1,448** |
| accepted & python-INVALID | **0** | **0** |
| crashes / hangs / sanitizer / illegal bestmoves | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| per-FEN verdict differences between builds | — | **0** |

## Which kinds survive the parser

| kind | accepted | why |
|---|---|---|
| `swap_ranks` | **1,407** | transposing whole rank fields usually leaves a structurally legal board (16 pieces, one king each, no pawn on rank 1/8) — it is a *different* position, not a malformed one |
| `field_garbage` | 41 | only when the garbage happens to be a legal value for the field it replaced (e.g. a clock field becoming digits) |
| `trunc_rank`, `dup_group`, `join_ranks`, `extra_slash`, `bad_piece`, `short_rank` | **0** | each of these always breaks the rank structure, and the parser's square-count and placement checks catch every one |

That is the explanatory result: **the parser's structural checks are complete against rank
damage**; the only accepts come from damage that produces a legal board. The accepted-invalid
class I found in the single-edit sweeps (adjacent digits like `1P1`, and a 7th field) is not
reachable by these multi-character kinds because none of them produce adjacent digits or extra
tokens — which is why the class did not grow rather than why it vanished.

## Refusal reasons (from the raw output)

| reason | count |
|---|---|
| `invalid FEN fields` | 2,572 |
| `too many squares in FEN rank` | 1,388 |
| `invalid FEN placement` | 204 |
| `pawn on promotion rank` | 178 |
| `invalid castling rights` | 108 |
| `invalid en-passant square` | 100 |
| `side that moved left its king in check` | 82 |
| `kings may not be adjacent` | 14 |

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 accepted share under 3 % | **held** (7.24 % — no: **FAILED**, 1,448/20,000 = 7.2 %, above my 3 % band and even above the single-edit 6 %) |
| P2 a new accepted-invalid class appears | **FAILED** — zero accepted-invalid |
| P3 0 crash/hang/sanitizer on both builds | held |
| P4 no illegal bestmove | held |
| P5 base and PC agree per FEN | held (0 differences) |
| P6 rank-order transposition refused | **FAILED** — it is the dominant accept |

Three of six predictions failed, and two of the failures are the same misjudgement: I assumed
damage always makes a board malformed. `swap_ranks` produces a *legal but different* board, so the
accepted share is higher than the single-edit sweep and P6's premise was simply wrong.

## Findings

`21-F14 | NEW` — multi-character FEN corruption produces **zero** accepted-invalid FENs on either
build (1,448 accepts, all python-valid), while rank-field transposition accounts for 1,407 of them.
So the parser's weakness is *not* structural damage; it is narrowly the adjacent-digit reading and
the extra-field tolerance found by the single-edit sweeps. That sharpens 21-F3: the engine is
lenient in exactly two small ways, not "generally lax".

## Suspicions, not proven

- `swap_ranks` producing 1,407 accepts could be a practical hazard if a GUI ever wrote a FEN with
  ranks in the wrong order — the engine would accept a scrambled position silently. I did not test
  a GUI, and FEN writers do not normally do this.

## What I did NOT do

- Did not combine kinds (two corruptions on one FEN); single kind per FEN, as in every earlier
  sweep, so the runs are comparable.
- Did not run either sweep under a sanitizer with a fresh planted fault (the ASan builds were used
  and reported nothing; the planted-fault proof for this configuration is 21-F5).

## What I am NOT sure about

- Whether a kind I did not think of (e.g. Unicode digits, or a FEN with 9 rank fields) reaches a
  third class. My alphabet is wider than before but still my own choice.

## Times

see `job26/stamps.txt`.
