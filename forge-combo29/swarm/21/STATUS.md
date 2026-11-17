## 2026-11-17T00:42:15Z (from `date -u`)
seat 21. **Threads 1 in every run.** PC build r15 under PC20 unless stated.

**1. 21-F12 line fixed as asked** — it now says, before anything else, that any reproduction MUST name a
**legal** mating move and MUST state the board by its **full FEN**, because three seats (21, 20, 25) have
now quoted it with an illegal move in the restriction and got `0000`/0 nodes instead of the repair. The
decisive case names both boards: `…/4R1K1` rook e1 → `e1e8` legal and mating, PC **8 nodes** `mate 1` vs
base **0 nodes** `cp 0`; `…/3R2K1` rook d1 → the same only for `d1d8`. Seats 20 and 25 are credited, and
seat 25's unrestricted measurement (PC 84 nodes `mate 1`, base 0 nodes `f2f3` at counter 100) is recorded.
The split is stated: a restriction naming at least one legal move is repaired; an empty or all-illegal one
is not.

**2. NEW: 21-C20 — the drawn-root design note is now a RUNNABLE acceptance spec**, and it is the cleanest
result of the session because neither build passes it and each fails a **different half**:

| case | base | PC20 |
|---|---|---|
| S1 drawn root + mate in 1 | **FAIL** (`cp 0`, f2f3) | PASS (`mate 1`, e1e8) |
| S2 drawn root, no mate | PASS (`cp 0`) | **FAIL** (`cp 368`) |
| S3 insufficient material | PASS | PASS |
| S4 threefold + mate in 1 | **FAIL** (`cp 0`, f2f3) | PASS (`mate 1`, e1e8) |
| S5 threefold, no mate | PASS (`cp 0`) | **FAIL** (`cp 292`) |
| pins | 4/4 exact | 4/4 exact |

One command judges any future fix: `python3 job43/acceptance.py <exe> <outdir> <label>` — exit 0 only if
all five pass with pins exact. The design note's rule is the unique rule that would pass all five.

**Four of my own errors in this job, all recorded**: `pass=ok)` (reserved word), an inverted S4 premise
assertion, a bench reader that let Timeout escape, and the perft pin routed through the bench reader. Each
failed loudly rather than producing wrong numbers — which is why the premise assertions exist.

**Next**: add a longer-mate case to the spec (S1/S4 use mate in 1 only) with a verified mate-N board, since
that is the remaining gap the spec itself names.
