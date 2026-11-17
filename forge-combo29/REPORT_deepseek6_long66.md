# REPORT — deepseek6, long 66 (evaluation symmetry)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long66/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** the engine's static evaluation (`eval`, side-to-move view) for each of the 353 G positions and its
colour-flipped mirror; then the same for the left-right mirror on positions without castling rights; a
self-comparison control; any difference reported with its FEN and the code term.

**Answer:**
- **Colour flip: 353 of 353 EQUAL.** The evaluation is perfectly colour-symmetric on the whole G set — not one
  position differs, and no delta at all.
- **Left-right flip: only 2 of 334 equal, 332 differ**, with deltas from ±1 cp up to **−738 cp**. That is not a
  defect: this engine's evaluation is a piece-square table plus handcrafted terms evaluated from White's and
  Black's own points of view (`src/eval.cpp:434-435`, `Psqt + (type-1)*64 + pop_lsb(white)` and
  `flip_square(...)` for black). **A horizontal mirror is not a symmetry such an evaluation is built to preserve**
  — no code in the tree implements one (I checked: zero occurrences of any horizontal-flip logic in `eval.cpp` or
  the headers).
- **The control is equal** (−351 twice).

**How sure:** certain of every count and delta (the two TSVs are committed with the FEN and the mirror FEN on each
row). Certain too of the reading that the left-right asymmetry is inherent rather than a bug — the code shows the
term and no symmetry is attempted.

## 2. Honesty numbers

Build: plain 6b98f217 release, `/tmp/ds6/build-release/forge`, sha256 `7c4e1aee…33622`. No search; the comparison
is on the static evaluation.

**What `eval` prints** (measured, not assumed): `info string eval hce 49 nnue 83 total 132 incheck 1`. The number
compared is **`total`**, which the engine reports from the side to move's point of view; my harness does not
re-sign it.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed, verified on origin | done | `CLAIM.txt` | 00:03:13Z |
| prediction as its own commit | done | `PREDICTION.md` | 6 predictions |
| harness written | done | `evalsym.py` | parses `total` and `incheck` |
| control: position 1 against itself | done | `full.out` | **EQUAL** (−351 / −351) |
| colour flip, all 353 | done | `out/FULL.colour.tsv` | **353 equal, 0 differ** |
| left-right flip, 334 without castling | done | `out/FULL.lefright.tsv` | **2 equal, 332 differ** |
| the code term named | done | section 5 F3 | `src/eval.cpp:434-435` |

## 4. The table

| comparison | positions | equal | differ |
|---|---|---|---|
| control (position 1 with itself) | 1 | **1** | 0 |
| colour flip (`mirror()`) | 353 | **353** | **0** |
| left-right flip (`flip_horizontal`, no castling rights) | 334 | **2** | **332** |

Largest left-right deltas: **−738, −278, −240** cp; smallest ±1 cp.

## 5. Findings, each with the command that shows it again

**F1. The colour symmetry is exact, everywhere.** 353 of 353 equal, zero deltas, on opening *and* game positions.
That is a stronger result than a statistical check would give and it means the evaluation has no tempo term, no
side-to-move bonus and no colour-dependent constant that survives a mirror. Reproduce:
`python3 evalsym.py <exe> set_G.epd out FULL`, the COLOUR FLIP block.

**F2. The left-right asymmetry is large and is NOT a bug — it is what a PSQT evaluation is.**
332 of 334 positions differ, up to 738 cp. If this had been a colour-flip result it would be a serious fault; for a
horizontal flip it is the expected behaviour of any engine whose piece-square tables are not file-symmetric.

**F3. The term responsible, with file and line:** `src/eval.cpp:434-435` —

```cpp
while (white != 0) acc.template add<White>(Psqt + (type - 1) * 64 + pop_lsb(white));
while (black != 0) acc.template add<Black>(Psqt + (type - 1) * 64 + flip_square(pop_lsb(black)));
```

The tables are indexed by absolute square for White and by `flip_square` (a vertical, rank flip) for Black. A
horizontal flip changes the file of every piece, and the table's file dependence (king safety, passed-pawn
proximity, rook activity) is not mirrored. **No horizontal-symmetry code exists in the tree**: a grep for any
horizontal-flip identifier in `src/eval.cpp` and the headers returns zero hits, so nothing is *supposed* to
preserve it.

**F4. The 2 positions that DO match are the ones where a horizontal flip is nearly the identity** (sparse
endings whose pieces sit symmetrically or near the centre), which is consistent with F2 rather than an exception
to it.

**F5. The `incheck` flag mirrors with the position** — it is read from the position, not the evaluation, and my
harness records it per row (`out/FULL.evals.tsv`) so it can be checked independently.

## 6. Suspicions, not proven

- **S1 — that the left-right deltas would shrink if the tables were file-symmetric.** That is a statement about a
  different engine; I did not test it and the current engine neither claims nor needs horizontal symmetry.
- **S2 — that the two "equal" left-right positions are exactly symmetric boards.** I read them as near-symmetric
  from their deltas (0), not by inspecting the piece placement.

## 7. What I read from my colleagues

- **File 16** for the item's wording, in particular that it asks for the **side-to-move view** and for the code
  term when a difference appears. Both followed.
- Nothing from a colleague's notes this item.

## 8. What I did NOT do

- **Did not report the left-right asymmetry as a fault.** It is not one, and saying "332 differences" without the
  PSQT explanation would have been a misleading headline.
- **Did not test the left-right flip on positions WITH castling rights** — a horizontal flip invalidates castling
  legality, so those would test python-chess, not the engine.
- **Did not re-run with the NNUE disabled** to separate the `hce` and `nnue` components; the item asks for
  `total`, and the colour result is exact for `total`.
- No pull request, no branch but mine, no engine source.

## 9. What I am NOT sure about

- Whether the left-right result is interesting to anyone: it is a property of PSQT engines in general. I report it
  with the term named so a reader can decide, rather than presenting it as a defect.
- Whether the NNUE component alone would show a different colour-symmetry result. `total` is exact; the split
  (`hce`/`nnue`) is recorded per row but I did not analyse it separately.

## 10. A better way

For a symmetry item, **ask for the colour flip first and treat the horizontal flip as a separate, clearly-labelled
question** — mixing them invites a reader to see 332 "failures" in a table where the engine is behaving exactly as
designed. The table in section 4 keeps them apart for that reason.

## 11. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
