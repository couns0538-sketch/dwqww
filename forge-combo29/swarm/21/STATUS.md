## 2026-11-16T22:41Z (from `date -u`)
seat 21, area 1 (FEN input / protocol edges). **Threads 1 in every run.** Builds: base 6b98f217 and
PC r15 (PC verified against file 5's three honesty rows).

# 21-F9 AND 21-F13 WITHDRAWN under handoff file 6

File 6's rule: a `cp 0` at a high halfmove counter is a defect **only** when a forced mate ends no
later than the 100th half-move, i.e. `2N-1 <= 100 - counter`.

- **21-F9**: counter 100 with a mate in 1 gives `1 > 0`, so the mate lands at half-move 101 and
  `cp 0` is CORRECT. In the window where the rule bites (counters 98, 99) the **base build already
  answers `mate 1`** at depth 6 and 20. Nothing fails. `job29/out/summary.md`.
- **21-F13**: a node-count shape observation at high counters; not a defect under file 6.
- **21-F9b** becomes moot (there was no defect to repair); 21-C6's measurement stands but file 6
  says seat 12's claimable-draw patch is not to be pursued and I do not recommend it.

This is the third claim of mine I have withdrawn or corrected this session (with 21-F11 `mate 0`
and the `go banana` "hang"). Each was caught by applying a rule I had not applied before, not by
someone else's contradiction.

**Still standing in my area, both on the PC build**: 21-F8 (`fullmove 0` refused while python-chess
accepts it) and 21-F2 (a refused `position fen` still answers `readyok` and the next search plays the
old game). Both are UCI/FEN-path issues, and file 6 ranks them *after* the PC's real path.

**Next, per file 6 item 4 and item 3**: move to `go softnodes N` on the PC build under PC20, Threads
1 — determinism run to run, does it stop at a finished depth, how far past N does it go. That is the
owner's self-play path, and it is where a find is worth most now.
Next command: `cd forge-combo29/swarm/21 && python3 job30/softnodes.py job30/out`
