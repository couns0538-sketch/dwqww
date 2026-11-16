# PREDICTION — seat 05 (area 5) job 1 — committed before any measuring command

Written and pushed BEFORE the first measuring command of job1. Never edited afterwards.

Job as written: "every search of a rows run on O and G at depth 12, S14: the LAST `info ... pv` line played by
python-chess: all legal? A `mate N` score: does the PV end in checkmate after 2N - 1 plies (N > 0) or 2|N| plies
(N < 0)? Control: a PV with its last move made illegal must be caught by your checker."

Build: Release /tmp/build-rel/forge sha256 e06310ec...a83 (honesty 4/4 in ../HONESTY.txt).
Settings: S14, Threads 1, Hash 16, `ucinewgame` + `isready` before every `go`.
Positions: O = data/O.fens (200), G = data/G.epd (353).

## Numbers

| # | what | predicted | killed if |
|---|------|-----------|-----------|
| 1 | searches completed with a `bestmove` | 553 of 553 | any position ends without bestmove, or a crash/hang is not explained |
| 2 | searches whose transcript has at least one `info ... pv` line | 553 | fewer than 550 |
| 3 | moves in the LAST pv line that python-chess refuses (illegal) | 0 | 1 or more |
| 4 | PVs that end in a position where the side to move is checkmated | 0 (a PV need not end in mate) | no kill: informational |
| 5 | positions whose final score is `mate N` with N > 0 | between 1 and 60 | 0, or more than 60 |
| 6 | positions whose final score is `mate -N` with N > 0 | between 0 and 40 | more than 40 |
| 7 | of the mate scores with N > 0 and N <= 5, share whose PV really ends in checkmate at exactly 2N-1 plies | 100 % | any single one fails |
| 8 | of the mate scores with N > 0 and N >= 6, share that ends in checkmate at exactly 2N-1 plies | 50 % — I expect the stored PV to be cut short (TT-based PV with a lower depth than the score) | no kill; I name the shortfall instead |
| 9 | of the mate scores with N < 0 (mated side to move at the root), share whose PV ends mated at exactly 2|N| plies | 60 % | no kill; named |
| 10 | Control: my checker, given the same PV with its LAST move replaced by an illegal move, reports it as illegal | 100 % catches | a control PV passes the checker |
| 11 | Control: my checker, given the PV of a position against itself twice, gives the same verdict | identical both times | differs |

## What would change my mind about the engine
A single illegal move inside a pv line breaks a promise UCI makes ("the pv is a line of legal moves from the
root"); that is finding-worthy on its own. A `mate N` score whose PV is NOT a mate in 2N-1 is only a finding when
the PV is shorter than 2N-1 plies yet still claims mate — a PV cut short at the mate distance is a reporting
weakness, and I will say so but mark it as such, not as a rule breach.

## Method (fixed before measuring)
- One fresh engine process per position; all output captured raw into out/O.raw.txt / out/G.raw.txt with a
  `### pos <n> <fen>` delimiter line before each block. Parsed copy in out/rows.jsonl.
- "Last info ... pv line" = the last line containing " pv " before the block's `bestmove`.
- Score = the score of that same last pv line (`score cp X` or `score mate N`), read from `info ... score ...`.
- python-chess 1.11.2 parses the FEN, plays each pv move in order with `board.push_san`-free `board.parse_uci` +
  `push`; the first refusal is the illegal move. Mate check: after playing all pv moves, `board.is_checkmate()`,
  and the ply count is the number of pushes.
