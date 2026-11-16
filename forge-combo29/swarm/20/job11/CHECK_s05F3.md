# seat 20 — check of seat 05's S-F3 (the fifty-move draw reaches the root score ~9 plies early)

Verdict: **CONFIRMS seat 05's S-F3** — and it is a *different mechanism* from my own S-C1, which is the point
worth recording.

Raw: `out_check.txt` (pasted), `check_s05f3.json` (every sweep point as data). Script: `check_s05f3.py`.
Build: `/agent/repos/build-base/forge` sha256 `e06310ec…` (4/4 pins).

## The result — `go depth 10`, halfmove counter swept

| board | first `cp 0` at halfmove | nodes there | pv length |
|---|---|---|---|
| `1K6/8/8/3R4/8/8/8/k7 w` (KR v K, seat 05's board) | **91** | 16,370,887 | 9 |
| `3k4/8/8/R7/8/8/8/7K w` (KR v K, mine) | **90** | 10,972,398 | 9 |
| `4R3/k7/8/8/8/4K3/8/8 w` (KR v K, mine) | **90** | 13,462,537 | 10 |
| `8/5K2/7Q/4k3/8/8/8/8 w` (KQ v K, mine) | **91** | 130,251,981 | 8 |
| `6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w` (mate in 1, mine) | **100** | **0** | **0** |

Below the onset the score is a real advantage (`cp 271`–`cp 381` at halfmove 90 on my boards); at and above it the
score is exactly `cp 0` while **the engine is still searching** — 16 M nodes, a 9-move pv. Only at halfmove 100 does
the node count fall to 0 with an empty pv.

## The two mechanisms, separated by the node count

| | root shortcut (my S-C1 / seat 01's S-F5) | fifty-move horizon seen in the tree (this finding) |
|---|---|---|
| when | halfmove >= 100 exactly | from halfmove ~90, board-dependent |
| nodes | **0** | millions |
| pv | **empty** | 8–10 moves |
| bestmove | first legal move | a searched move |

That is why both findings are true and neither refutes the other: the counter threshold at the ROOT is exactly
100, but the SEARCH reaches the fifty-move horizon inside the tree about 10 plies before the counter gets there.

## Agreement with seat 05
Their number: `cp 0` from H=91 on `1K6/8/8/3R4/8/8/8/k7 w`. Mine on their own board: **first zero at 91**, exactly.
On my other boards the onset is 90, which is why their "about 9 plies early" is the right way to say it: the shift
depends on the position, not on a constant.

## What the engine is doing (source read, not guessed)
`src/search.cpp:1300-1310`, `Worker::is_draw`:
```
if (board.halfmove_clock() >= 100) {
    // Checkmate on the hundredth half-move still wins; everything else is a draw.
    return !board.in_check() || board.has_legal_move();
}
```
so any leaf whose counter has reached 100 is a draw; a depth-10 search from counter 90 can therefore reach it. The
`root_drawn` shortcut at 2251 is the separate, root-only path.

## A correction to my own work, kept on record
My first sweep included `8/8/8/8/8/8/K7/R6k w - - 0 1`, which is **not a legal position** (the kings are
adjacent) — the engine refused it with `invalid FEN: side that moved left its king in check` and I was silently
measuring the PREVIOUS position. I added an `assert python-chess is_valid` guard to the script, which then caught a
second bad board of mine (`1K6` with `R6k` — also adjacent kings). Both are gone; the table above is from boards
python-chess validates. The intermediate run's rows for those boards are not used anywhere.

## Where my predictions went
All five held. Prediction 3 (at least two distinct onset values) held with 90 and 91. Prediction 2 (nodes > 0 at the
first zero) held on all four non-mating boards.

## Commands that show it again
```
python3 check_s05f3.py /agent/repos/build-base/forge /tmp/o
printf 'uci\nsetoption name OwnBook value false\nisready\nposition fen 1K6/8/8/3R4/8/8/8/k7 w - - 91 1\nisready\ngo depth 10\nquit\n' | ./forge | tail -2
printf 'uci\nsetoption name OwnBook value false\nisready\nposition fen 1K6/8/8/3R4/8/8/8/k7 w - - 90 1\nisready\ngo depth 10\nquit\n' | ./forge | tail -2
```
