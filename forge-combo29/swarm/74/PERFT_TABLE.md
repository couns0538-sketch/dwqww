# PERFT_TABLE

Engine: `forge-combo29` at commit `6b98f217`, built with g++ 13 (`-O3 -march=x86-64-v4`),
`Threads 1`, `go perft N` driven synchronously over UCI.

Reference for every cell: the Chess Programming Wiki perft-results page
(https://www.chessprogramming.org/Perft_Results). The `python-chess` column is an
**independent re-derivation** of the published number, run only where it is cheap
(depth ≤ 4 and ≤ 5,000,000 nodes); see the note at the foot for why depth 5–6 is
not re-derived in Python.

All 42 cells were reached through the gates in `uci_perft.py`: python-chess FEN
validation, a scan of the `position` reply *and* the `go perft` output for
`info string invalid FEN`, and a perft-1 + perft-2 board-identity check against
python-chess before the deep count.

## Standard suite — 7 positions, 42 cells

| position | depth | published | measured | python-chess | verdict |
|---|---:|---:|---:|---:|---|
| startpos | 1 | 20 | 20 | 20 | ok |
| startpos | 2 | 400 | 400 | 400 | ok |
| startpos | 3 | 8,902 | 8,902 | 8,902 | ok |
| startpos | 4 | 197,281 | 197,281 | 197,281 | ok |
| startpos | 5 | 4,865,609 | 4,865,609 | not re-derived | ok |
| startpos | 6 | 119,060,324 | 119,060,324 | not re-derived | ok |
| kiwipete | 1 | 48 | 48 | 48 | ok |
| kiwipete | 2 | 2,039 | 2,039 | 2,039 | ok |
| kiwipete | 3 | 97,862 | 97,862 | 97,862 | ok |
| kiwipete | 4 | 4,085,603 | 4,085,603 | 4,085,603 | ok |
| kiwipete | 5 | 193,690,690 | 193,690,690 | not re-derived | ok |
| kiwipete | 6 | 8,031,647,685 | 8,031,647,685 | not re-derived | ok |
| position3 | 1 | 14 | 14 | 14 | ok |
| position3 | 2 | 191 | 191 | 191 | ok |
| position3 | 3 | 2,812 | 2,812 | 2,812 | ok |
| position3 | 4 | 43,238 | 43,238 | 43,238 | ok |
| position3 | 5 | 674,624 | 674,624 | not re-derived | ok |
| position3 | 6 | 11,030,083 | 11,030,083 | not re-derived | ok |
| position3 | 7 | 178,633,661 | 178,633,661 | not re-derived | ok |
| position4 | 1 | 6 | 6 | 6 | ok |
| position4 | 2 | 264 | 264 | 264 | ok |
| position4 | 3 | 9,467 | 9,467 | 9,467 | ok |
| position4 | 4 | 422,333 | 422,333 | 422,333 | ok |
| position4 | 5 | 15,833,292 | 15,833,292 | not re-derived | ok |
| position4 | 6 | 706,045,033 | 706,045,033 | not re-derived | ok |
| position4-mirror | 1 | 6 | 6 | 6 | ok |
| position4-mirror | 2 | 264 | 264 | 264 | ok |
| position4-mirror | 3 | 9,467 | 9,467 | 9,467 | ok |
| position4-mirror | 4 | 422,333 | 422,333 | 422,333 | ok |
| position4-mirror | 5 | 15,833,292 | 15,833,292 | not re-derived | ok |
| position4-mirror | 6 | 706,045,033 | 706,045,033 | not re-derived | ok |
| position5 | 1 | 44 | 44 | 44 | ok |
| position5 | 2 | 1,486 | 1,486 | 1,486 | ok |
| position5 | 3 | 62,379 | 62,379 | 62,379 | ok |
| position5 | 4 | 2,103,487 | 2,103,487 | 2,103,487 | ok |
| position5 | 5 | 89,941,194 | 89,941,194 | not re-derived | ok |
| position6 | 1 | 46 | 46 | 46 | ok |
| position6 | 2 | 2,079 | 2,079 | 2,079 | ok |
| position6 | 3 | 89,890 | 89,890 | 89,890 | ok |
| position6 | 4 | 3,894,594 | 3,894,594 | 3,894,594 | ok |
| position6 | 5 | 164,075,551 | 164,075,551 | not re-derived | ok |
| position6 | 6 | 6,923,051,137 | 6,923,051,137 | not re-derived | ok |

**42 cells compared, 42 agree, 0 mismatches, 0 harness refusals.**
**28 of the 42 published counts were independently re-derived with python-chess
and all 28 agreed with the published value**, so the published table itself was
not taken on faith for those cells.

## Depth actually reached vs. the brief's "depth 5–6"

Every position reached the depth the brief asked for, and two reached further:

| position | deepest depth run |
|---|---:|
| startpos | 6 |
| kiwipete | 6 |
| position3 | 7 (CPW publishes d7) |
| position4 | 6 |
| position4-mirror | 6 |
| position5 | 5 (CPW publishes only to d5 for this position) |
| position6 | 6 |

position5 stops at 5 because that is where the CPW table stops, not because of a
budget. Position 4 is included twice — the published position and its mirror —
because the CPW page lists them as two identical rows and a mirror disagreement
is a real bug class for castling-rights handling.

## Why depth 5–6 is not re-derived in python-chess

python-chess has no built-in perft, so the reference here is a plain recursive
perft over `board.legal_moves` (see `py_perft` in `uci_perft.py`). That is a
genuinely independent move generator, which is what makes it worth something, but
it is pure Python at roughly 10⁴ nodes/sec: kiwipete at depth 6 is 8.03 billion
nodes, which is not a run, it is a week. The deep cells are therefore scored
against the published count, and python-chess's independent agreement is
established at the shallow depths (28 cells) plus at depth 3 across the fuzz set
(3,000 further positions).

## Divide accuracy

`go perft N` prints a per-root-move divide. Verified child-by-child against
python-chess on three mixed positions, matching every key and every count:

| position | root moves (eng/py) | differing children | total |
|---|---:|---:|---:|
| kiwipete | 48 / 48 | 0 | 97,862 |
| ep-live | 5 / 5 | 0 | 623 |
| promotion | 7 / 7 | 0 | 411 |
