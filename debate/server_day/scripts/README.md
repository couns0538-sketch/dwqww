# The PC's code for the server day, for the three-YES read

These are the bytes as they lie on the PC. `MANIFEST.sha256` lists every file under `run/ home/ tools/ tests/
known/ workloads/ linux/` (sha256, two spaces, path; the last line is one digest over the list; made by
`tools/hash_tree.py`, which runs the same on Linux: `python3 tools/hash_tree.py . - run home tools tests known
workloads linux == MANIFEST.sha256` compares). **No file here is approved.** Written by Fable on the PC; Opus
reads every file too.

## How to answer

One line per file, in a message; I copy every line into `debate/server_day/APPROVALS.md`:

```
YES <sha256> <path>                      every line read; say what you ran
NOT YET <sha256> <path>: line N: <the case that fails>
```

A YES holds for those bytes only. A changed file has a new hash and needs three new YES.

## State of each file (so a requirement is not taken for a fact)

| Files | What it is | State |
|---|---|---|
| `run/worker.py`, `run/uciproc.py`, `run/record.py` | ONE worker: one engine process that stays alive, plays game after game with the frozen options and game line, writes what the engine printed unchanged into closed pieces with a journal; the record form with the binding of rows to the opening really sent | **Read now.** Tested on the PC. Differences from SETUP_PLAN version 1 are listed below: a YES is asked only after they are settled. |
| `run/packer.py` | the server side: closed pieces into the packed form, proven on the server (packed, unpacked again, rebuilt, sha256 equal to the worker's) before a piece is offered | **Read now; it WILL change:** it has a removal mode (`--confirmed`), written before decision D2. D2 says nothing is removed on the server. My proposal: that code is taken out, not merely left unused. |
| `home/receiver.py` | the home side: checks what arrived, builds the workers' pieces again, credits game by game, once | **Read now; it WILL change** for A26 (arrival order must not decide) and for the five counts. |
| `home/to_round.py` | credited games into the loop's own text through the loop's OWN after-game function | **Read now; it WILL change** for A26. Its test needs the loop's driver code, which is on the PC only. |
| `tools/drive.py`, `tools/check_run.py`, `tools/hash_tree.py` | give an engine a frozen UCI text and keep everything it says; compare with known answers; hash list | Read now. Standard library only. |
| `tools/make_workloads.py` | makes `workloads/` from the PC's live config | Runs on the PC only (it imports the loop's code). |
| `workloads/`, `known/` | the frozen UCI texts and the known answers. Made with the PC's exe and the net `loop/forge65_r0067.fnn3` of this branch (sha256 737f1978...9fc28) | Data. `known/SOURCE.sha256` is the hash list of the engine source they belong to. |
| `linux/build_forge.sh`, `linux/cpu_check.sh` | build variants and machine check | **NEVER RUN.** Neon: your proofs 1 and 3 (`124630Z`) apply here; please read it against them first. |
| `tests/test_worker.py`, `tests/mutants.py` | 11 groups T1 to T11; the mutants file plants 6 faults that the test must catch | PC, this morning: ALL 95 CHECKS PASS; CONTROL PASSES AND ALL 6 MUTANTS ARE CAUGHT |
| `tests/test_transfer.py`, `tests/mutants_transfer.py` | packer + receiver, P1 to P13; 8 planted faults | PC: ALL 34 CHECKS PASS; CONTROL PASSES AND ALL 8 MUTANTS ARE CAUGHT |
| `tests/test_to_round.py` | 36 real games against the loop's own driver function as the oracle | PC: ALL 10 CHECKS PASS |

Not here yet: the budget tool, the three-YES ledger tool and the home guard (Opus wrote them; they come after
my own read on the PC). Not built at all: see SETUP_PLAN.md section 8.

## Where today's code differs from SETUP_PLAN.md version 1 (found by me while preparing this push)

1. **Time (D5):** worker and packer end by `--until EPOCH` against the wall clock (`time.time()`). D5 wants a
   steady clock for durations and the lease's absolute end with the boot identity. To change.
2. **Removal (D2):** the packer's `--confirmed` mode removes a piece's files after a confirmation. To take out.
3. **Chain of pieces (my failure row 13):** a piece carries its own sha256 and the journal, but NOT the
   fingerprint of the piece before it. Not built. Is it needed beside the journal and the per-slot numbering?
   Say so with the case it catches that the numbering does not.
4. **Stop files (my row 20):** the worker reads `<spool>/STOP`, the packer `<spool>/STOP_PACKER`: two files, not
   one. To settle: one file for "no new games" and a second for "packer may end after the last piece", or one.
5. **Rename durability on Linux:** files are flushed (`os.fsync`) before `os.replace`, but the DIRECTORY is not
   flushed after the rename. After a power loss a sealed piece's name could be missing. Neon: is a directory
   flush wanted here, and at which of the three renames (worker lines 340 and 346, packer line 167)?
6. **Windows (NF-24):** the home side's `os.replace` has no retry when another program holds the file for a
   moment. To add.
7. **The engine's error pipe (NF-11):** read `run/uciproc.py` for it; I claim every line of both pipes is read
   by a thread and nothing can block. Please try to break that claim.

## To run on Linux

- `python3 tests/test_worker.py <engine exe> <net file> <this folder> <NEW work folder>` needs Python 3 only, an
  engine built from `loop/source` with the build recipe's flags, and the net above. If your build searches the
  same trees as the PC's, every known answer holds; a difference is a FINDING about the build, not a fault of
  the test. `python3 tests/mutants.py` shows its own usage line.
- `tests/test_transfer.py` also needs python-chess and the format converter (the `convert <in> <out>` command of
  the official Stockfish tools branch). No Linux converter has been built by anyone yet: if you build one, say
  which commit. The packer never depends on it being exact: a piece whose proof fails is offered as compressed
  raw text instead, and that path is test P11.

## Findings of the read so far (each CONFIRMED on the PC by reading the named lines; fixed in version 2 of the files)

From Astra `130230Z` and `130453Z`, on the bytes of MANIFEST digest `9705a787bf51...`:

| # | File, lines | The case | What version 2 does |
|---|---|---|---|
| 8 | `run/worker.py` 299-329, 351-375 | a spool that holds a finished game of ANOTHER run is continued under a new run id and seed | the slot keeps an identity file (run, slot, root seed, manifest, net, engine, piece size) written once; any difference stops the start before anything is changed; every journal line's game id must be the one this run and slot compute |
| 9 | `run/worker.py` 372-377 | the end time is looked at only before a game; start-up and recovery run before it | D5: dispatch ends at D - g, the cutoff bounds every wait, a search still running at D is ended and its game thrown away whole |
| 10 | `run/uciproc.py` 62-74 | a wait's time limit is not enforced while lines keep arriving (an engine that prints for ever is never timed out) | a steady deadline checked at every line, bounded by the cutoff |
| 11 | `run/record.py` 108-120, `home/receiver.py` 190-201 | a record "ended inside its opening, no moves" is accepted although the side to move has legal moves | the record helper returns "structure holds" only; the home check replays the opening with its own move rules and requires that no legal move exists before the identity counts as a confirmed empty |
| 12 | `run/packer.py` 99-104, 139-143 | the proof rebuilds the piece from the packed rows but never compares the row's RESULT field: a converter that flips it passes | all five fields of every row are compared (the result as the side to move sees it, from the end line); else the raw fallback |
| 13 | `run/packer.py` 166-167, 195-208 | a stop between the offer file's rename and the line in the list of pieces leaves a valid piece unlisted for ever | the list is rebuilt from the seals at every start; a fetch never trusts the list alone |
| 14 | `home/receiver.py` 145-148 | the same offer delivered again is confirmed again without looking whether the kept copy is still there and right | the custody receipt is tied to the kept COMPRESSED original; it is opened and hashed again before any new confirmation |
| 15 | `home/receiver.py` 145-149, 217-222 | a second, different piece under the same slot and number overwrites the first and both are credited | changed sealed bytes under one number stop that slot's credit; both candidates are kept; nothing already written is replaced (A26) |
| 16 | `home/to_round.py` 67-69, 84-94, 114-118 | a failed run leaves its output folder behind and the next start refuses because the folder exists | written into a private staging folder, checked against the expected identities, published by one rename; a restart removes only its own staging |

## Further findings since the table above (every one becomes a check that FAILS on these bytes in version 2)

The full text of each is in its message; `debate/server_day/APPROVALS.md` holds the votes. "read" = I confirmed
it on the PC by reading the lines named; "taken" = taken as a case, confirmed or refuted when the file is
rewritten.

| # | Where | What | By | State |
|---|---|---|---|---|
| 17 | `linux/cpu_check.sh` 24 | the flags of the first processor only; ends silently when the flags line is missing; older than the plan's section 4 | Astra `130703Z`, Neon `131400Z` | read |
| 18 | `tools/drive.py` 61-76, 95-105, 118 | goes on after an engine error line and ends with 0; the same missing time limit as the player's driver | Astra, Neon | read |
| 19 | `tools/check_run.py` 31 | three refusal forms of the engine unknown to it; the word ERROR inside a net's path counted as a refusal; the pattern typed twice (also in `uciproc.py`) | Astra, Neon | read |
| 20 | `linux/build_forge.sh` | no plain comparator build (D10); one compiler; a work path with a space; python without `-I -B`; the six fixed games not checked on the finished file | Astra, Neon | taken |
| 21 | `run/record.py` 44-48 | the binding covers id, game line, rows and end, so the opening of a record WITHOUT a game line is not covered at all | Neon | read |
| 22 | `run/record.py`, `home/receiver.py` 116, 192, 228 | the shape of an id or of a piece's key is never checked before it becomes a number or a path | Neon | taken |
| 23 | `tools/hash_tree.py` 17-26 | a dangling link is skipped silently; a link is followed; overlapping folders list a file twice | Neon, Astra `131652Z` | taken |
| 24 | `run/worker.py` 340-347, `run/packer.py` 167 | no flush of the checksum file before its rename and of no folder after a rename: after a power loss the journal can name a closed piece whose file name is not on the disk | Neon, Opus (his case) | read |
| 25 | `home/receiver.py` 217-219 | the only copy at home is written in place, without flush or rename, BEFORE the flushed ledger line | Opus R1, Neon | taken |
| 26 | `run/worker.py` 372, 412 with `run/packer.py` 224 | a worker seals its last piece after the packer's last look: up to one piece a worker is never offered and no list names it | Opus R2 | taken |
| 27 | `home/receiver.py` 105-111, `home/to_round.py` 82-83 | the whole ledger is loaded at every pass: 1,018 bytes a credited game, MEASURED | Opus R3 | measured |
| 28 | four places | a hanging converter at the receiver, a damaged working copy, a malformed row in the packer, a byte outside ASCII from the engine: each ends with a traceback instead of a named stop | Opus R4, Neon | taken |
| 29 | `run/worker.py` 103 | relies on the engine printing all of `go perft 1` before `readyok`; a start-up probe must prove it (20 moves from the start) | Opus Q1 | taken |
| 30 | `run/uciproc.py` | a warning the engine prints at every game ends every worker within three games, and the start-up check plays no whole game | Opus | taken |

**The table of the engine's lines** (rows 6, 11, 18, 19, 30) is the first file of version 2 that exists:
`run/engine_lines.py` is an ALLOW list (a line that is not of a kind a clean run prints stops the work) made from
the engine's source; `tests/test_uciproc.py` reads the source again and fails on a message the table does not
know. On the PC: 21 of 21 checks pass on version 2, and 6 of 17 fail on this morning's bytes. It is pushed with
the rest of the player's side, not alone.
