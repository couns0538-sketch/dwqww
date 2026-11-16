# CHECK of seat 21's finding 21-F1 — seat 13, own build, own harness

## Verdict
**CONFIRMS 21-F1.**

Seat 21 claimed: the brief's "an impossible-castling FEN is ACCEPTED (perft 3 8,902 against
python-chess 8,802)" is a misdiagnosis — this build REFUSES that FEN, 8,902 is startpos perft 3
(perft of the position left on the board by the refused command), and 8,802 is python-chess's
perft 3 of the refused FEN itself.

My own runner (`check_21f1.py`, written from the finding's description, not from seat 21's script)
reproduces every part of that on my own release build.

## Evidence
Raw output: `out_21f1/*.txt`, one file per case, each with the exe path, sha256, every line sent,
stdout, stderr and returncode. Summary: `out_21f1/VERDICT.md`.

| case | engine nodes | refusal line | verdict |
|---|---|---|---|
| A: castling FEN alone, perft 3 | 8902 | `info string invalid FEN: castling right without king and rook` | HOLDS |
| B: castling FEN, then K v K FEN, perft 3 | 170 | same refusal | HOLDS |
| C: castling FEN, then startpos, perft 3 | 8902 | same refusal | HOLDS |
| D: legal castling FEN, perft 3 | 13744 | (none — ACCEPTED) | HOLDS |
| E: startpos, then castling FEN, perft 3 | 8902 | same refusal | HOLDS |

python-chess perft 3, computed by me in the same script:

- refused FEN `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1` = **8,802**
- startpos = **8,902**
- legal castling FEN `r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1` = **13,744**
- K v K = **170**

So both numbers in the brief are exactly explained: 8,902 = startpos perft 3 (the stale board),
8,802 = python-chess perft 3 of the FEN that was refused. The FEN was never accepted.

## Why this is a check and not a copy
- Different runner: mine sends `uci`/`isready` around every command and records refusal lines
  per case; I did not run or import seat 21's `f1_8902.py`.
- Case D is my own control: a legal castling FEN must be ACCEPTED with perft 3 = 13,744, so my
  reading of "refused" cannot be a runner that refuses everything.
- Case B is my own second control: after a refusal the NEXT successful `position fen` must take
  effect (170, K v K), so the 8,902 is not a permanently frozen board.

## Beyond the finding
Nothing beyond it on this point. But note the consequence for the brief's other FEN ground truth:
the brief's parenthetical was the only stated proof that "an impossible castling right is accepted
and trusted". On this build it is refused, so that half of the Opus "already known" list does not
hold as written for commit 6b98f217 — I flag it here rather than as a new finding, since it is
seat 21's finding, not mine.
