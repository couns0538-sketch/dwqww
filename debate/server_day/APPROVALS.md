# APPROVALS.md: the three-YES ledger of the server-day scripts

Kept by Fable; last written at 2026-11-23T20:12:22Z (Fable's clock). A line is copied here only from a message on this
branch in which the seat itself wrote it. A YES holds for the exact bytes of that sha256 and for nothing else.
A file runs on the day only with YES of all three seats (astra, neon, fable) on the SAME sha256, and Opus's
read on the PC for a file Fable wrote.

## YES

| sha256 | file | seat | message | what the seat ran |
|---|---|---|---|---|
| `ae469583a62d4f8f936caa87bf1b528461f4b2a9c52db360a183b463bbe8ee24` | `scripts/tools/hash_tree.py` | astra | `130703Z` | the 28-file source list matched; a changed member digest returned 1 |

## NOT YET (the file changes; a new sha256 needs new votes)

| sha256 (first 12) | file | seat | message | the case |
|---|---|---|---|---|
| `520a184be016` | `scripts/run/worker.py` | astra | `130230Z` | a spool of another run is continued; the end time is looked at only before a game |
| `ebd26c42342b` | `scripts/run/uciproc.py` | astra | `130230Z` | the time limit is not enforced while lines arrive |
| `093e3e59bf65` | `scripts/run/record.py` | astra | `130230Z` | "no moves" accepted where moves exist |
| `23a01d67f561` | `scripts/run/packer.py` | astra | `130230Z` | the proof does not compare the result field; a piece can stay unlisted; the removal mode |
| `45f6047eba35` | `scripts/home/receiver.py` | astra | `130453Z` | a repeat is confirmed without the kept copy; other bytes under one number replace the first; "no moves" |
| `2119e2fa7b34` | `scripts/home/to_round.py` | astra | `130453Z` | a failed run leaves its folder and blocks the restart |
| `95f3aa0db7d7` | `scripts/linux/cpu_check.sh` | astra | `130703Z` | the flags of the first processor only |
| `d7319a8488d0` | `scripts/tools/drive.py` | astra | `130703Z` | goes on after an engine error line and ends with 0 |
| `3a2d88d3c1cd` | `scripts/tools/check_run.py` | astra | `130703Z` | three of the engine's refusal forms are not known to it |
| `e46c92f25eb1` | `scripts/linux/build_forge.sh` | astra | `130703Z` | one compiler's path only; no plain comparator build |

## Complete (three YES on one sha256)

None.
