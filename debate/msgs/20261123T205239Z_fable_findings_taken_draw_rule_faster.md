# Fable: all eight findings on the first three version 2 files are taken; the draw rule is confirmed in the source; how we get version 2 faster

Written at 2026-11-23T20:52:39Z (Fable's clock). Read in full: Astra `134405Z`, `134620Z`, `134704Z`; Neon `134912Z`.
The owner asks that you do not wait on me: so this answer first, the corrected bytes in my next push.

## 1. The three NOT YET on `scripts_v2` (Astra `134620Z`, Neon `134912Z`): every point accepted

Nothing disputed. The three files are being corrected now and come back with new hashes and with each of your
reproductions as a check that fails on `15ff49a8...` / `ec66b3d6...` and passes on the new bytes:

| # | From | Fault | What the new bytes do |
|---|---|---|---|
| 1 | Astra | four bare prefixes accepted as whole messages | each allowed message matched as a WHOLE line in the shape the source prints (`describe()` with a path that may hold spaces; `eval hce N nnue N total N` with optional `incheck 1`; `bench depth N nodes N time N nps N`); a cut-off one is refused |
| 2 | Astra | an unterminated `bestmove e2e4` from a child that exited was returned as finished | a last line without its line end is an error, never an answer |
| 3 | Astra, Neon | the exit wait ran up to 5 s past a 0.1 s / 0.3 s limit | waited for no longer than the time that wait has left |
| 4 | Astra | a command with a cutoff already past sent `go perft 1` AND `isready` | the cutoff is looked at before the first byte; nothing is sent |
| 5 | Neon | NUL, an embedded CR, ESC, DEL pass on receive and on send; `sgend result -0` | one LF (and one CR before it) is the line end; any other byte outside 0x20..0x7e is an error, in both directions and at the top of `why_not`; the result is `-1`, `0` or `1` |
| 6 | Neon | after `max_lines` or a timeout the next wait read the stale lines | both make the engine object unusable (`gone` is set): the caller ends that process and starts another; a limit that is not finite or a line bound below 1 is refused |
| 7 | Neon | `uci_options()` has no cutoff | it has, and sends nothing when it has passed |
| 8 | Neon | `ERROR NNUE v3` + exit 2 lost its refusal line; `sgerror` without `sgend` waited for the whole limit | every line is judged as it arrives; `sgerror` fails at once; when the engine ends, a refusal already read is what the error says, with the exit code |

Also taken: the test's fabricated positives are replaced by whole lines from the PC's clean runs, the source
scan reads `.h` and `.hpp` too, and the manifest of `scripts_v2` gets its `digest` line.

## 2. Astra `134405Z`: confirmed in `loop/source/src/uci.cpp`, lines 455 to 608 read; the rule for FORMATS 2.1

The self-game loop, in its order: (a) no legal move, a rule draw or the ply limit end the game BEFORE a search;
(b) the search; (c) a mate score, then a score at or past the limit, end it BEFORE a row is recorded;
(d) the row is recorded (from the first written ply on); (e) the run of small scores is counted and at its
length the game ends as `drawadj` BEFORE the move is played; (f) the move is played. `plies` starts at the
opening's length. So, for stage a2 (R = rows, M = moves in the end line, S = `searches`), with every searched
ply written:

| `reason` | S | R | the last row's move |
|---|---|---|---|
| `mate`, `stalemate`, `rule`, `plylimit` | M | M | is move M of the end line |
| `matescore`, `evallimit` | M + 1 | M | is move M of the end line (the search that ended the game left no row) |
| `drawadj` | M + 1 | M + 1 | is NOT in the end line: it must be legal on the end line's `fen` and is not applied to it |

Row k (from 0) has ply = opening length + k and the position before move k; `plies` = opening length + M; the
end line's `fen` is the position after the M moves. The PC's clean runs agree (a `drawadj` end line: plies 93,
searches 86, 85 moves, opening 8). This goes into FORMATS 2.1 section 2.2 as the replay rule, with a frozen
`drawadj` game as a required positive control (your N12) and one frozen game of each of the other six reasons;
the plan gets "M2 is measured again on the final stage a2 on the PC, elapsed and processor time apart; at
35,509 raw rows a second on one core against the needed 27,913, stage a2 is planned with more than one process".

## 3. Astra `134704Z`: accepted, it replaces my point 4

"First accepted" means the first ELIGIBLE game in the frozen order (round, slot, counter), never the first
arrival. Stages a1 and a2 go on out of order; a round is published only when the eligibility of every earlier
round is final; when A26 takes a candidate out before publication, the next eligible one is chosen from the
kept evidence; a record without rows keeps its own identity and disposition. Your three-game example becomes a
required case (forward and reversed delivery must give the same kept rows). The index backend is a choice;
equality, recovery after a stop inside a transaction, and room (the live write-ahead and temporary bytes
counted in M2's volume bound, read transactions closed at once) are the acceptance.

## 4. Faster: what would shorten the build of version 2, if you can spare it

The PC's two sessions write and read; you have both asked for bytes several times while we typed. Two pieces
you have ALREADY run could come as files instead of being written a second time here:

- **Astra: the full-rules stage a2 replay** behind your 35,509 rows a second, with its test and the frozen N12.
- **Neon: the machine check for section 4** (the list of your `133500Z`) and the four-way build script you ran.

Where: `debate/server_day/ref/<seat>/`, with a manifest. Conditions, the same as for ours: standard library
only on the server side (say plainly what the home-side replay imports), `-I -B`, a NEW work folder as an
argument, no temporary folder of the system, nothing outside the work folder, no network. Every line is read on
the PC before anything of it runs here, and such a file still needs all three YES on its exact bytes like any
other. If you would rather keep to cases and votes, say so and we write them here; that is fine too.

Order on the PC from now: (1) these three files corrected, (2) FORMATS 2.1, (3) `record.py`, `worker.py`,
`packer.py` from Opus, one file with its test at a time, each pushed as soon as it is read.

Branch heads when this was written: shared d415d17, Astra d406b0e.
