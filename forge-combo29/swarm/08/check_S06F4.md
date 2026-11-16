# CHECK of seat 06's finding S-F4 — seat 08 (area 8)

Their finding, as written on branch for-fable-and-opus/swarm-06, FINDINGS.md:

> S-F4 | 6 | left-right flip changes the static score of 98-99% of real positions, median 20 cp on hce and
> 60 cp on total, max 838 cp

## Verdict: CONFIRMS (with two numbers of theirs that I could not reproduce)

My harness is my own, written from their sentence alone: `forge-combo29/swarm/08/check_s06f4.py`, using
python-chess `board.transform(chess.flip_horizontal)` (files a<->h, NO colour swap) and one fresh engine
process per `eval` so no line can be attributed to the wrong position.

## Controls (both passed, see check_S06F4_raw.txt)
- a position against itself: hce 52/52, nnue 22/22, total 74/74, identical — the reader is stable;
- a position with the g2 pawn moved to f2: total 74 -> -58, differ — the reader can see a change.

## Results — 453 positions (all 353 of G + the first 100 of my R_seed801), on
`/home/ubuntu/builds/release/forge` sha256 e06310eca3...

| quantity | seat 06 said | I measured | agree? |
|---|---|---|---|
| hce differs | 98-99 % | 444 / 453 = 98.0 % | yes |
| nnue differs | (not given) | 444 / 453 = 98.0 % | — |
| total differs | 98-99 % | 450 / 453 = 99.3 % | yes |
| median abs delta hce | 20 cp | **20 cp** | yes, exact |
| median abs delta total | 60 cp | **38 cp** | NO |
| max abs delta total | 838 cp | **738 cp** | NO (different position set, so not a contradiction) |

The 3 positions whose total does NOT differ (99.3 % not 100 %) are the case their S-F5 describes: the two
components move and cancel. So F4 and F5 are consistent.

## Beyond their finding
The largest single left-right delta I measured is not a near-mate score: `5Q2/2k5/8/4KB2/7P/4R3/8/8 w - - 0 1`
evaluates 2705 and its mirror 1967 — a **738 cp** difference on a position with equal material, purely from
which side of the board the pieces stand on. That is 7.4 pawns of static evaluation from a horizontal mirror.
Any tuning that assumes the hand-written terms are left-right symmetric inherits this.

## Show it again

    cd forge-combo29/swarm/08 && python3 check_s06f4.py ~/builds/release/forge /tmp/GR453.fens /tmp/out.txt

where /tmp/GR453.fens is `cut -d' ' -f1-6 job1/set_G.epd` followed by `head -100 job1/R_seed801.fens`.
Raw output committed as check_S06F4_GR453.txt (453 positions) and check_S06F4_raw.txt (60 positions).
