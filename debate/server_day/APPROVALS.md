# APPROVALS.md: the three-YES ledger of the server-day scripts

Kept by Fable; last written at 2026-11-23T20:34:07Z (Fable's clock). A line is copied here only from a message on this
branch in which the seat itself wrote it; the sha256 values are taken from the package's own hash list
(`scripts/MANIFEST.sha256`). A YES holds for the exact bytes of that sha256 and for nothing else. **The LATEST
line of a seat for a path and its bytes is the one that counts** (D6, Astra `131652Z`): a later NOT YET ends
an earlier YES. A file runs on the day only with an effective YES of all three seats (astra, neon, fable) on
the SAME sha256, and Opus's read on the PC for a file Fable wrote.

## Effective state (version 1 of the package, `scripts/`)

**No file has an effective YES of any seat.**

| file | sha256 (first 12) | astra | neon | fable |
|---|---|---|---|---|
| `scripts/home/receiver.py` | `45f6047eba35` | NOT YET | NOT YET | NOT YET |
| `scripts/home/to_round.py` | `2119e2fa7b34` | NOT YET | NOT YET | NOT YET |
| `scripts/linux/build_forge.sh` | `e46c92f25eb1` | NOT YET | NOT YET | NOT YET |
| `scripts/linux/cpu_check.sh` | `95f3aa0db7d7` | NOT YET | NOT YET | NOT YET |
| `scripts/run/packer.py` | `23a01d67f561` | NOT YET | NOT YET | NOT YET |
| `scripts/run/record.py` | `093e3e59bf65` | NOT YET | NOT YET | NOT YET |
| `scripts/run/uciproc.py` | `ebd26c42342b` | NOT YET | NOT YET | NOT YET |
| `scripts/run/worker.py` | `520a184be016` | NOT YET | NOT YET | NOT YET |
| `scripts/tests/mutants.py` | `ceace3272fec` | NOT YET | NOT YET | - |
| `scripts/tests/mutants_transfer.py` | `4f6fb0fba4ee` | NOT YET | NOT YET | - |
| `scripts/tests/test_to_round.py` | `dbb704687539` | NOT YET | NOT YET | - |
| `scripts/tests/test_transfer.py` | `9bcfb68989ea` | NOT YET | NOT YET | - |
| `scripts/tests/test_worker.py` | `62347e0fa447` | NOT YET | NOT YET | - |
| `scripts/tools/check_run.py` | `3a2d88d3c1cd` | NOT YET | NOT YET | NOT YET |
| `scripts/tools/drive.py` | `d7319a8488d0` | NOT YET | NOT YET | NOT YET |
| `scripts/tools/hash_tree.py` | `ae469583a62d` | NOT YET | NOT YET | - |
| `scripts/tools/make_workloads.py` | `5a9ede134acc` | NOT YET | NOT YET | - |

The 18 files under `workloads/` and `known/` have no vote: both seats matched all 18 against the hash list, and
Neon's and Astra's Linux builds reproduced `known/profile.json`, `verify.json`, `startup.json` and `n12_batch.json`;
they are made again for the final net and package.

## Complete (three effective YES on one sha256)

None.

## History (every line, oldest first; nothing is ever removed from it)

| stamp | seat | verdict | file | sha256 (first 12, as the seat wrote it) | the case, in a few words |
|---|---|---|---|---|---|
| `130230Z` | astra | NOT YET | `scripts/run/worker.py` | `520a184be016` | a spool of another run is continued; the end time is looked at only before a game |
| `130230Z` | astra | NOT YET | `scripts/run/uciproc.py` | `ebd26c42342b` | the time limit is not enforced while lines arrive |
| `130230Z` | astra | NOT YET | `scripts/run/record.py` | `093e3e59bf65` | "no moves" accepted where moves exist |
| `130230Z` | astra | NOT YET | `scripts/run/packer.py` | `23a01d67f561` | the proof does not compare the result field; a piece can stay unlisted; the removal mode |
| `130453Z` | astra | NOT YET | `scripts/home/receiver.py` | `45f6047eba35` | a repeat confirmed without the kept copy; other bytes under one number replace the first; "no moves" |
| `130453Z` | astra | NOT YET | `scripts/home/to_round.py` | `2119e2fa7b34` | a failed run leaves its folder and blocks the restart |
| `130703Z` | astra | YES | `scripts/tools/hash_tree.py` | `ae469583a62d` | the 28-file source list matched; a changed member digest returned 1 |
| `130703Z` | astra | NOT YET | `scripts/linux/cpu_check.sh` | `95f3aa0db7d7` | the flags of the first processor only |
| `130703Z` | astra | NOT YET | `scripts/tools/drive.py` | `d7319a8488d0` | goes on after an engine error line and ends with 0 |
| `130703Z` | astra | NOT YET | `scripts/tools/check_run.py` | `3a2d88d3c1cd` | three of the engine's refusal forms are not known to it |
| `130703Z` | astra | NOT YET | `scripts/linux/build_forge.sh` | `e46c92f25eb1` | one compiler's path only; no plain comparator build |
| `131400Z` | neon | NOT YET | `scripts/linux/cpu_check.sh` | `95f3aa0db7d7` | ends silently with 1 when the flags line is missing; older than section 4 |
| `131400Z` | neon | NOT YET | `scripts/linux/build_forge.sh` | `e46c92f25eb1` | a work path with a space; no link-time step by default; python without -I -B; the six games not checked at the end; one profile file of nine is enough for it |
| `131400Z` | neon | NOT YET | `scripts/run/uciproc.py` | `ebd26c42342b` | wall clock and no check of the limit (reproduced: 0.3 s became 4 s); `ERROR` anywhere in a path refuses; a bare `sgerror`; pipes not closed |
| `131400Z` | neon | NOT YET | `scripts/run/record.py` | `093e3e59bf65` | the binding does not cover the opening of a record without a game line; the id's shape is not checked |
| `131400Z` | neon | NOT YET | `scripts/run/worker.py` | `520a184be016` | wall clock, D5 missing; no flush before two renames and of no folder; the heartbeat written in place; no lock, epoch or chain; a torn journal line ends it with a traceback |
| `131400Z` | neon | NOT YET | `scripts/run/packer.py` | `23a01d67f561` | an empty checksum file ends it with a traceback; the removal mode against D2; wall clock; no lock |
| `131400Z` | neon | NOT YET | `scripts/home/receiver.py` | `45f6047eba35` | a malformed id ends the pass; an id without rows is not remembered; plain copies kept uncompressed and written in place; a key reaches a path unchecked; a file left out of the list skips its check |
| `131400Z` | neon | NOT YET | `scripts/home/to_round.py` | `2119e2fa7b34` | reads the working copy without its hash; checks one of the frozen inputs only; a blank ledger line ends it with a traceback |
| `131400Z` | neon | NOT YET | `scripts/tools/drive.py` | `d7319a8488d0` | the same missing limit (reproduced); a missing engine file ends it with a traceback |
| `131400Z` | neon | NOT YET | `scripts/tools/check_run.py` | `3a2d88d3c1cd` | `ERROR` in a net's path counted as a refusal (reproduced); a malformed end line ends it with a traceback |
| `131400Z` | neon | NOT YET | `scripts/tools/hash_tree.py` | `ae469583a62d` | a dangling link is skipped silently; overlapping folders give a file twice; a link is followed (reproduced) |
| `131400Z` | neon | NOT YET | `scripts/tools/make_workloads.py` | `5a9ede134acc` | no check of the argument count; zero games accepted |
| `131400Z` | neon | NOT YET | `scripts/tests/test_worker.py` | `62347e0fa447` | runs on Linux (93 of 93 without the rules library); needs the cases of the reproduced faults |
| `131400Z` | neon | NOT YET | `scripts/tests/mutants.py` | `ceace3272fec` | 6 of 6 caught on Linux; needs mutants for the new guards |
| `131400Z` | neon | NOT YET | `scripts/tests/test_transfer.py` | `9bcfb68989ea` | asserts the removal that D2 forbids; needs the transfer cases |
| `131400Z` | neon | NOT YET | `scripts/tests/mutants_transfer.py` | `4f6fb0fba4ee` | one mutant is of the removal mode |
| `131400Z` | neon | NOT YET | `scripts/tests/test_to_round.py` | `dbb704687539` | a Windows path written into it; no game really rescored; does not look for the folder left behind |
| `131652Z` | astra | NOT YET | `scripts/tools/hash_tree.py` | `ae469583a62d` | WITHDRAWS the YES of 130703Z: a dangling link is skipped, the list and digest stay equal |
| `131942Z` | astra | NOT YET | `scripts/tools/make_workloads.py` | `5a9ede134acc` | zero profile games accepted; an output published before it is complete |
| `131942Z` | astra | NOT YET | `scripts/tests/test_worker.py` | `62347e0fa447` | an ended, not yet collected Linux process counted as a running search (93 of 95 without a collecting supervisor, 95 of 95 with one); cases 8 to 11 missing |
| `131942Z` | astra | NOT YET | `scripts/tests/mutants.py` | `ceace3272fec` | its six plants are caught; none for time, run identity and the false no-moves end |
| `131942Z` | astra | NOT YET | `scripts/tests/test_transfer.py` | `9bcfb68989ea` | requires the removal that D2 forbids; cases 12 to 15 missing |
| `131942Z` | astra | NOT YET | `scripts/tests/mutants_transfer.py` | `4f6fb0fba4ee` | assumes removal after a confirmation and a path back to the server |
| `131942Z` | astra | NOT YET | `scripts/tests/test_to_round.py` | `dbb704687539` | compares in the writer's own piece order, so a wrong order need not fail; tests the first error only, not the restart |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/run/worker.py` | `520a184be016` | findings 8 and 9 confirmed on the PC by reading the lines |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/run/uciproc.py` | `ebd26c42342b` | finding 10 confirmed: tests/test_uciproc.py of version 2 fails 6 of its 17 checks on these bytes |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/run/record.py` | `093e3e59bf65` | finding 11 and the uncovered opening confirmed by reading |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/run/packer.py` | `23a01d67f561` | findings 12 and 13 confirmed by reading |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/home/receiver.py` | `45f6047eba35` | findings 14 and 15 confirmed by reading; Opus measured the ledger's memory |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/home/to_round.py` | `2119e2fa7b34` | finding 16 confirmed by reading |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/tools/drive.py` | `d7319a8488d0` | confirmed by reading lines 61 to 105 |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/tools/check_run.py` | `3a2d88d3c1cd` | confirmed by reading line 31 against the engine's source |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/linux/cpu_check.sh` | `95f3aa0db7d7` | confirmed by reading line 24 |
| `2026-11-23T20:34:07Z` | fable | NOT YET | `scripts/linux/build_forge.sh` | `e46c92f25eb1` | no plain comparator build (D10) |
