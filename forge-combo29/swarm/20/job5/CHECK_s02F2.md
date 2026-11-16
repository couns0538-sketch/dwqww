# seat 20 — check of seat 02's S-F2 (empty/unmatched `searchmoves` answers `bestmove 0000`)

Verdict: **CONFIRMS seat 02's S-F2**, on my own build, with my own harness and my own controls.

Raw: `out_check.txt` (pasted), `check_s02f2.txt` (every transcript, both builds), `check_s02f2.json`.
Script: `check_s02f2.py`.

## The result (startpos, 20 legal moves, `OwnBook false`)

| case | command | release bestmove | info string | depth lines | max nodes |
|---|---|---|---|---|---|
| a | `go searchmoves depth 2` | **0000** | "searchmoves restriction has no legal root moves" | 2 | 0 |
| b | `go searchmoves e7e5 depth 2` | **0000** | same line | 2 | 0 |
| c | `go searchmoves a2a3 b2b3 depth 4` | a2a3 | none | 4 | 56 |
| d | `go depth 2` | d2d4 | none | 2 | 54 |
| e | `go movetime 20` | d2d4 | none | 10 | 13102 |
| f | `go searchmoves a2a3 depth 4` | a2a3 | none | 4 | 49 |

The ASan+UBSan build gives the same answers on every case (only the `movetime 20` search length differs, as
expected from being ~9x slower): 0 sanitizer lines anywhere.

So: an empty restriction and a restriction naming an illegal move both produce `bestmove 0000` on a board with
20 legal moves, with 0 nodes searched; a restriction naming legal moves is respected exactly; unrestricted
searches are unaffected.

## Where in the source
`src/search.cpp:2204-2214` (6b98f217):
```
result.restricted_root_empty = root_restricted_ && !legal.empty() && root_candidates.empty();
if (result.restricted_root_empty && emit_info) { ... "info string searchmoves restriction has no legal root moves" ... }
```
then the terminal-root branch:
```
if (root_candidates.empty() || root_drawn) {
    ...
    if (!root_candidates.empty()) result.best_move = root_candidates.front();
    ...
    return result;                     // best_move stays Move::none() -> printed as 0000
}
```
Note the comment on the line above the terminal branch in the source says "Terminal or adjudicated roots:
report without searching" — an empty RESTRICTION is being handled as if it were a terminal position.

## Why it matters, and why it may not
UCI: `bestmove 0000` means "no move". A GUI that receives it in a live game has no legal move to play, so it
either forfeits or falls back to something of its own. Whether a GUI can produce the input is the open question:
a GUI that sends only legal moves cannot send case (b); case (a), a bare `searchmoves` keyword with nothing after
it, is a malformed command, so a well-behaved GUI will not send it either. **So the risk is real but a GUI must
misbehave first to reach it.**

Against the swarm's already-known list: Opus's file 1 records `bestmove 0000` only "on a position without legal
moves (checkmate, stalemate) ... is the engine's answer, not a fault". This is a board WITH 20 legal moves, so it
goes beyond that line — as seat 02 already said.

## Where my prediction was incomplete
Prediction 4 said 0000 would come with no `info depth` line carrying nodes > 0. It comes with TWO `info depth`
lines (depth 1 and 2) whose `nodes` field is **0** — same drawn-root reporting loop as the S-F5 shortcut. So
"no depth lines" is wrong; "nodes = 0" is the right test. (Same correction as S-F7 in `../FINDINGS.md`.)

## Commands that show it again
```
printf 'uci\nsetoption name OwnBook value false\nisready\nucinewgame\nisready\nposition startpos\ngo searchmoves depth 2\nquit\n' | ./forge | grep -E 'info string|bestmove'
  -> info string searchmoves restriction has no legal root moves
     bestmove 0000
printf 'uci\nsetoption name OwnBook value false\nisready\nucinewgame\nisready\nposition startpos\ngo depth 2\nquit\n' | ./forge | grep bestmove
  -> bestmove d2d4
python3 check_s02f2.py <release-exe> <asan-exe> .
```
