# S-C1 — CONFIRMS S01-F5 (seat 01's halfmove-100 root adjudication)

Checked by seat 28, area 8, on my own Release build (`~/build/base-release/forge`, sha256
`e06310ec…16a83`, bench 11/13/16 and perft 5 all matching — see `../HONESTY.txt`).

## The claim I tested
From seat 01's FINDINGS.md line alone: "With `halfmove >= 100` in the FEN the engine adjudicates the
root as a draw and searches 0 nodes, so a mate-in-one is MISSED (`bestmove f2f3`, `score cp 0`) while
the identical board at halfmove 99 gives `score mate 1` / `bestmove a1a8` / 126 nodes."

I did not read or copy seat 01's script. I wrote `check_s01f5.py` from that sentence, built my own
mate-in-one position with python-chess (`6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - {hm} 1`, mate by Ra8), and
judged the engine's answer independently with `python-chess` (`board.push(move).is_checkmate()`).

## Result — `check_s01f5.py`, pasted

```
== python-chess says of my own positions ==
MATE_ROOK_hm0: mate_in_one_exists=True
MATE_ROOK_hm99: mate_in_one_exists=True
MATE_ROOK_hm100: mate_in_one_exists=True
MATE_ROOK_hm101: mate_in_one_exists=True
MATE_ROOK_hm150: mate_in_one_exists=True
QUIET_hm99: mate_in_one_exists=False
QUIET_hm100: mate_in_one_exists=False

| case | halfmove | refused | engine nodes | score | bestmove | bestmove IS mate-in-one |
|---|---|---|---|---|---|---|
| MATE_ROOK_hm0 | 0 | False | 126 | mate 1 | a1a8 | True |
| MATE_ROOK_hm99 | 99 | False | 126 | mate 1 | a1a8 | True |
| MATE_ROOK_hm100 | 100 | False | 0 | cp 0 | f2f3 | False |
| MATE_ROOK_hm101 | 101 | False | 0 | cp 0 | f2f3 | False |
| MATE_ROOK_hm150 | 150 | False | 0 | cp 0 | f2f3 | False |
| QUIET_hm99 | 99 | False | 781 | cp 0 | g2g3 | False |
| QUIET_hm100 | 100 | False | 0 | cp 0 | f2f3 | False |
```

So on my own position the engine reproduces seat 01's numbers EXACTLY: 126 nodes and `mate 1` /
`a1a8` at halfmove 99, and 0 nodes / `cp 0` / `f2f3` at halfmove 100, on a board where python-chess
confirms a mate in one exists. The finding is **CONFIRMED**, down to the node count.

## Controls (a check without controls proves nothing)
- **Control 1 (the harness can see a mate):** `MATE_ROOK_hm99` gives `mate 1` and names a move that
  python-chess confirms is mate — so a "0 nodes, no mate found" answer at hm100 is not a blind harness.
- **Control 2 (0 nodes comes from the counter, not the harness):** `QUIET_hm99` searches 781 nodes and
  `QUIET_hm100` searches 0 on the SAME board with no mate available at either. Only the counter differs,
  so the 0-node short circuit is attributable to `halfmove >= 100`.

## Beyond the finding (my addition, not seat 01's claim)
1. **The short circuit is not mate-specific — it skips ALL search at halfmove >= 100.** `QUIET_hm100`
   searches 0 nodes and answers `f2f3`/`cp 0` where the same board at halfmove 99 searches 781 nodes.
   So the engine does not "adjudicate a draw", it answers without evaluating anything: the returned
   move is the first root candidate, and the score is a constant 0.
2. **The same fault exists in the OTHER term of the same expression.** `src/search.cpp:2250-2252`:
   ```cpp
   const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                              board.is_insufficient_material());
   ```
   `repetition_root.py` reaches the mate-in-one board a third time through legal moves
   (`position fen <base> moves a1b1 g8f8 b1a1 f8g8` twice), where python-chess reports
   `is_repetition() == True` and the mate still available:
   ```
   | case | bestmove | score | nodes |
   |---|---|---|---|
   | CONTROL: same board via `position fen`, no repetition history | a1a8 | mate 1 | 126 |
   | SAME board via `position fen BASE moves`, shuffle twice (3rd occurrence) | f2f3 | cp 0 | 0 |
   ```
   Identical board, identical mate, 0 nodes when the repetition history is present. This is the same
   fault as S-F5 through a second door; seat 01's patch removes only the `halfmove_clock() >= 100`
   term, so **as written that patch would leave the repetition door open**.

## Code (opened and read, not quoted from another seat)
`/agent/repos/base/forge-combo29/src/search.cpp:2249-2272` — `root_drawn` then
`if (root_candidates.empty() || root_drawn) { ... report without searching ... }`; the reported score is
0 unless the board is already mated (`-MateValue`) or `DrawJitter > 0`.

## How to see it again
```
cd forge-combo29/swarm/28/checks
python3 check_s01f5.py ~/build/base-release/forge /tmp/s01f5.tsv
python3 repetition_root.py ~/build/base-release/forge
```
Raw: `check_s01f5_out.txt`, `check_s01f5_out.md`, `repetition_root_out.txt`.

## What I did NOT do
- Did not test the insufficient-material term (that is area 5 job 2's ground).
- Did not apply anyone's patch; no engine source was changed by me.
- Did not test at depths other than `go depth 6`.
