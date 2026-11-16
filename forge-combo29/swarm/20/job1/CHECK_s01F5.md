# seat 20 — check of seat 01's S-F5 (halfmove >= 100 misses a mate in one)

Verdict: **CONFIRMS seat 01's S-F5**, on my own build, with positions I built myself and a mate I proved
with python-chess before running the engine.

Raw output: `check_s01f5.txt` (pasted run), `check_s01f5.json` (every case as data).
Script: `check_s01f5.py` — written from seat 01's one-sentence claim, not from their `analyse_halfmove.py`
(I read their script only after mine worked, to compare position choices).

## The positions, and why the expectation is not seat 01's
`6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1` — I found it by asking python-chess for its own mate-in-1 moves:
`['d1d8']`. The same for `7k/6pp/8/8/8/8/6PP/5RK1 w - - 0 1` -> `['f1f8']`.
Both mates are proved by python-chess inside the script (`prove_mate()`), and recorded in the JSON under
`positions`.

## The result

| position | halfmove | bestmove | score | nodes | first legal move |
|---|---|---|---|---|---|
| Q-mate | 0, 97, 98, 99 | d1d8 | mate 1 | 168 | f2f3 |
| Q-mate | 100, 101, 102, 150 | f2f3 | cp 0 | 0 | f2f3 |
| R-mate | 0, 97, 98, 99 | f1f8 | mate 1 | 114 | g2g3 |
| R-mate | 100, 101, 102, 150 | g2g3 | cp 0 | 0 | g2g3 |
| checkmated | 0, 98, 99, 100, 101, 150 | 0000 | mate 0 | 0 | — |

- Threshold is exactly 100: 99 finds the mate, 100 does not, for both positions.
- At `halfmove >= 100` the engine plays the FIRST LEGAL MOVE of the position (`f2f3` / `g2g3`, both verified
  with the engine's own `go perft 1`, whose first line is exactly that move).
- Deeper or wider searches do not escape: `go depth 8`, `go depth 12`, `go nodes 100000`, `go movetime 200`
  at halfmove 100 all answer `f2f3`, `cp 0`, `nodes 0`.
- An already-checkmated board is NOT affected: `0000` / `mate 0` at every counter value, including 150.
- The ASan+UBSan build behaves identically (hm 99 mate 1 / hm 100 cp 0 nodes 0), 0 sanitizer lines.
- Control: on a normal position the same harness reports a searched move with 1683 nodes at halfmove 0 and
  the first legal move with 0 nodes at halfmove 100, so the harness can tell the two apart.

## Where my prediction was wrong, plainly
Prediction 2 said the fallback answer would carry no `info depth` line at all. It carries SIX — the
`root_drawn` branch loops `for depth = 1..max_depth` emitting `info depth <d> seldepth 1 score cp 0 nodes 0
nps 0 hashfull 0 time 0 pv` with an EMPTY pv, then returns the first legal move. So "unsearched" is right
about the nodes (0) and the pv (empty), but the line "no info depth line at all" is wrong. The substance of
S-F5 is unaffected; my phrasing was.

## The cause, read in the source
`src/search.cpp:~2253` (6b98f217):
```
const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100
                                           || board.is_insufficient_material());
if (root_candidates.empty() || root_drawn) { ... report without searching ... }
if (!root_candidates.empty()) result.best_move = root_candidates.front();
```
The `halfmove_clock() >= 100` term makes a position with a forced mate adjudicate as a draw AT THE ROOT.

## Why it matters in play
A game can reach halfmove 100 without either side claiming the draw (a claim is a choice; checkmate ends the
game at once and takes precedence). At that moment the engine stops searching and plays its first legal move,
so it can throw away a mate it had already found at halfmove 99.

## Commands that show it again
```
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 100 60\ngo depth 6\nquit\n' | ./forge | grep -E 'info depth|bestmove'
  -> info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
     bestmove f2f3
printf 'position fen 6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 99 60\ngo depth 6\nquit\n' | ./forge | grep -E 'info depth|bestmove'
  -> ... score mate 1 ... bestmove d1d8
python3 check_s01f5.py <release-exe> <asan-exe> .
```
