# REPORT — deepseek6, long 65 (PV legality on O and G at depth 12)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long65/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** every search of a rows run on O and G at depth 12 under S14: keep the last `info ... pv` line, replay
it with python-chess, check every ply legal, check mate scores against the PV length (2N-1 plies for `mate N` with
N>0, 2|N| for N<0), check that a PV ending in checkmate carries a mate score, and plant an illegal PV.

**Answer:** **553 of 553 PVs are fully legal** (200 O + 353 G), the plant is caught exactly, and **one real defect
surfaces**: position **193 of G** reports `score mate -12` at depth 12 but its PV is **18 plies** and does **not**
end in checkmate — a mate score whose PV contradicts it. Searching the same position deeper shows the depth-12
result was simply wrong: at depth 20 the engine gives `mate -4` with an 8-ply PV that **does** end in mate, and a
**different best move** (`c2b1`, not `c2c3`).

**How sure:** certain of the legality counts and of the mismatch (both PV rows are committed, the replay is one
command). Certain too that the depth-12 answer is wrong — the depth-20 PV checkmates.

## 2. Honesty numbers

Build: plain 6b98f217 release, `/tmp/ds6/build-release/forge`, sha256 `7c4e1aee…33622`. Its four pins were exact
at the start of this chat. S14, Threads 1, Hash 16, OwnBook false, depth 12, one fresh process per position.

**The plant** (`out/planted_example.pvrows`, `plant_result.txt`): one real PV's last move replaced by `a1h8` →
the checker reports `first illegal ply: [(1, 12, 'a1h8', 'illegal')]`. The plant runs through **`pvrows.py`'s own
`check()`**, not a separate script, so the committed code path is what catches it.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed, verified on origin | done | `CLAIM.txt` | 23:53:22Z |
| prediction as its own commit | done | `PREDICTION.md` | 6 predictions |
| collector + checker written | done | `pvrows.py` | records `pos/nodes/bestmove/score/pv` |
| plant | done | `out/planted_example.pvrows`, `plant_result.txt` | **caught at pos 1, ply 12** |
| O: 200 searches | done | `pv/O.pvrows` | 200/200 legal, 0 mate scores |
| G: 353 searches | done | `pv/G.pvrows` | 353/353 legal, 10 mate scores, **1 mismatch** |
| the mismatch investigated | done | `out/pos193_depth20.txt` | depth-20 answer is `mate -4`, 8 plies, mate |
| scorecard | done | `scorecard.txt` | 4 held, 2 killed |

## 4. The table

| set | searches | PVs fully legal | first illegal ply | mate scores | mate scores whose PV ends in mate at the stated length |
|---|---|---|---|---|---|
| O | 200 | **200** | none | **0** | — |
| G | 353 | **353** | none | **10** | **9** |

PV lengths: O min 9 / max 20; G min 3 / max 25; 3 PVs (0.8 %) under 4 plies; none over 64.

## 5. Findings, each with the command that shows it again

**F1. Every PV is legal on both sets — 553 of 553.** No illegal ply anywhere, at any length, on opening positions
or on game positions. Reproduce: `python3 pvrows.py <exe> O.fens pv O` and the same for `set_G.epd`.

**F2. One mate score contradicts its own PV, and the depth-12 result is genuinely wrong.**
Position 193 of G (`8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, a K+P ending) at depth 12:

```
score mate -12, bestmove c2c3, PV 18 plies: c2c3 d2d1q c3b2 e4e3 b2a2 d1c2 a2a1 c2c1 a1a2 c1c4 a2b2 c4d4 b2c1 d4a1 c1c2 a1d1 c2b2 e2d3
```

The PV is 18 plies but `mate -12` requires **24** (2×|−12|), and after the last move the position is **not**
checkmate (`in check: False`, 2 legal moves for the opponent). Same position at **depth 20**:

```
info depth 20 ... score mate -4 nodes 39083 pv c2b1 d2d1q b1b2 d1d2 b2a3 d2c2 a3b4 c2b3
bestmove c2b1
```

8 plies for `mate -4` — exactly 2×4 — and the PV **does** end in checkmate (`8/8/1p6/8/pK2p3/1q6/4k3/8 w - - 6 5`,
verified by replaying it in python-chess). So the depth-12 search reported a mate length that is not there and
**missed the winning line that its own deeper search finds**, changing its best move in the process. This is a
search-quality defect in a pawn ending, not a formatting artefact.

**F3. The remaining nine mate scores are internally consistent.** All nine have a PV ending in checkmate at exactly
the stated length, which is what makes F2 stand out rather than being one of a family.

**F4. No PV ends in checkmate with a plain centipawn score** (0 of 553), so the score reporting does not
under-report mates anywhere in this sample.

**F5. Three PVs are shorter than 4 plies (0.8 %)** — the shortest is 3 — all on G. At depth 12 a 3-ply PV is legal
and consistent, but it means the reported line is a stub; worth knowing for anyone reading PVs as analysis.

## 6. Suspicions, not proven

- **S1 — why position 193's depth-12 search is wrong.** The score `mate -12` with an 18-ply PV looks like a mate
  distance carried up from a reduced or null-move search without being re-verified at the full depth: the PV is
  truncated where the reduction stopped, and the score was never corrected. I have not instrumented the mate-score
  propagation, so that is a reading of the symptom.
- **S2 — whether F2 is isolated.** It is 1 of 10 mate scores and 1 of 553 searches. A dedicated sweep of K+P
  endings (the `set_G` sample has few) would say whether it is a class or a one-off.

## 7. What I read from my colleagues

- **File 16** for the item's exact rules, including the 2N−1 / 2|N| arithmetic, which I implemented literally
  rather than approximating.
- Nothing from a colleague's notes this item; the colleague read is on the four-hour clock.

## 8. What I did NOT do

- **Did not search G deeper across the board** — only position 193, to decide whether the score or the PV was
  wrong. A full depth-20 repeat is a different item.
- **Did not test MultiPV PVs** — MultiPV 1 only, as the item's rows-run condition implies.
- **Did not re-run O with a deeper search** — O produced 0 mate scores, so the mate clause had nothing to check
  there.
- No pull request, no branch but mine, no engine source.

## 9. What I am NOT sure about

- Whether F2's wrong mate score also affects the move the engine would play in a game at that node budget — at
  depth 12 it chose `c2c3`, at depth 20 `c2b1`. Both may be adequate, and one of them is demonstrably part of a
  forced mate; a match would be needed to say whether it matters in practice.
- Whether the 3-ply PVs (F5) indicate a truncation path or genuinely shallow lines.

## 10. A better way

For mate-score checking, **the PV length and the score must be checked together, always** — a mate score with a
PV of the wrong length is a contradiction that no "all PVs legal" test can see, and it is exactly the fault this
item was designed to hunt. My first instinct was to report "553 of 553 legal, 0 problems"; the mate-length clause
is what turned that into a finding.

## 11. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
