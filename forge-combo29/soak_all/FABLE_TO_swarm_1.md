# Opus to THE SWARM, file 1 (2026-11-16): no corrections yet. ALREADY KNOWN (do not report these as NEW)

Read at every cycle: the newest FABLE_TO_swarm_<N>.md (highest N) applies to every seat.

## Already known about the engine at 6b98f217 (each was reproduced on the PC; a finding that only repeats one of
## these is not NEW; a finding that goes BEYOND one of them is, say what is beyond)
- FEN: consecutive digits of a rank are ADDED ("17" and "44" read as 8 empty squares; "9" is refused).
- FEN: an impossible castling right is accepted and trusted (perft 3 differs from python-chess's 8,802 on the same
  board: the engine 8,902).
- FEN: a position no game can reach is accepted (a triple check by three knights); its moves are generated right.
- UCI: after an illegal move in `position ... moves`, the engine keeps the legal prefix (perft 1 = 29 after
  e2e4 e7e5 e1e3); after a refused FEN it keeps the previous position.
- UCI: `setoption name Hash value 0` and an option without a value answer `info string invalid value for option X`;
  an unknown command is ignored without a line.
- Search: a root restricted by `searchmoves` (even to every legal move) searches a different, mostly smaller tree:
  internal iterative reduction fires at the root, and no hash entry is stored for a restricted root.
- `bestmove 0000` on a position without legal moves (checkmate, stalemate) is the engine's answer, not a fault.

## Reminder
A "0 sanitizer lines" result needs the two proofs of the first message (nm count in the .meta, and one planted fault
counted by the same runner). A finding needs a command file that shows it again.
