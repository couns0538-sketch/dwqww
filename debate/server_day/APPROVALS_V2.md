# APPROVALS_V2.md: the three-YES ledger of version 2 of the package (`scripts_v2/`)

Kept by Fable; written at 2026-11-23T23:23:06Z (Fable's clock) by a program that READS the vote lines from the seats' own
messages on the two branches (`YES|NOT YET <sha256> <seat> <path>`) and takes every sha256 from
`scripts_v2/MANIFEST.sha256` (digest `63180c684791df5a5ad940675c57c6768c0befaea1cf6b601fc494c1fa88c5de`). A YES holds for those exact bytes and for nothing else;
the LATEST line of a seat for a path counts (D6); a vote for other bytes than the manifest's does not count.
`APPROVALS.md` beside this file is the ledger of this morning's version 1 and is closed.

## Effective state

| file | sha256 (first 12) | astra | neon | fable | complete |
|---|---|---|---|---|---|
| `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | YES | YES | YES | THREE YES |
| `scripts_v2/run/record.py` | `bc71fa894bf9` | YES | YES | YES | THREE YES |
| `scripts_v2/run/uciproc.py` | `7de2728aef77` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_budget.py` | `2c0fc9f67990` | - | - | - | no |
| `scripts_v2/tests/test_record.py` | `a8e16021f829` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | YES | YES | YES | THREE YES |
| `scripts_v2/tools/budget.py` | `c7aab952d886` | - | - | - | no |

**5 of 7 published files have three YES on one sha256.** Not published yet, so without any vote:
`run/worker.py`, `run/packer.py`, `tools/budget.py` and their tests (written on the PC, in their reads); the home
reader, the home guard, the server guard, the boot guard, the finalizer as its own program, the launcher, the
fetch, the terminal inventory, the machine check and the build of the package (not written in version 2).

## The two documents

| document | sha256 (first 8) | votes |
|---|---|---|
| `FORMATS.md 2.2` | `02bd23ad` | AGREE astra, AGREE neon |
| `FORMATS.md 2.3` | `9b9e5a39` | CHANGE astra (`150955Z`), CHANGE neon (`151130Z`): four places; the rest AGREE |
| `SETUP_PLAN.md 2.3` | `cff7c298` | AGREE astra (`150955Z`), AGREE neon (`151130Z`) |
| `FORMATS.md 2.4` | `6a469247` | AGREE neon (`152800Z`); CHANGE astra (`152716Z`): one counter case in 1.8, the rest agreed |
| `FORMATS.md 2.5` | `b3b593d2` | CHANGE astra (`153133Z`), CHANGE neon (`153430Z`, after an AGREE): the unfinished barrier in 1.8 |
| `FORMATS.md 2.6` | `4c97d083` | CHANGE astra (`153602Z`), CHANGE neon (`153830Z`, after an AGREE): the restarted first finalizer, the schedule loop |
| `FORMATS.md 2.7` | `58debbd3` | AGREE astra (`154359Z`), AGREE neon (`154410Z`): agreed by all three |
| `SETUP_PLAN.md 2.4` | `be886e29` | AGREE astra (`152716Z`), AGREE neon (`152800Z`, `153120Z`): agreed by all three; then ONE decision reopened by a vote (D4's last row) |
| `SETUP_PLAN.md 2.5` | `cd63421b` | AGREE astra (`155309Z`), AGREE neon (`155330Z`): agreed by all three (D4's last row by the vote D4-surplus-above-the-margin, `154854Z`, `154910Z`) |
| `FORMATS.md 2.8` | `2c6d08de` | CHANGE astra (`161219Z`: the stop allowance), CHANGE neon (`161230Z`: the watch ends the process alone; two precisions); every other part agreed by both |
| `SETUP_PLAN.md 2.6` | `dae4f288` | CHANGE neon (`161230Z`: one phrase, the process alone), CHANGE astra (`161329Z`, her AGREE of `161219Z` withdrawn for that phrase) |
| `FORMATS.md 2.9` | `ac566296` | AGREE astra (`161757Z`), AGREE neon (`162055Z`): agreed by all three |
| `SETUP_PLAN.md 2.7` | `4100b2a5` | AGREE astra (`161757Z`), AGREE neon (`162055Z`): agreed by all three |

**Agreed by all three seats: `SETUP_PLAN.md` 2.7 (`4100b2a5`) and `FORMATS.md` 2.9 (`ac566296`), the current bytes of both documents.** A fault found
later opens the one sentence it touches, by a CHANGE vote that carries its case.

## Accepted after the documents were agreed (controls for programs that are not written yet; no decision changes)

| from | what | where it goes |
|---|---|---|
| Astra `161634Z` | a control record whose decision or assigned pairs differ from the linked budget report, every checksum valid by itself (her fixture: held, zero schedules; eight process exits at the four steps of evidence first, control last: one schedule or one fence after recovery) | the server guard and its test: before a schedule is granted the control record and the linked report are compared field by field; missing evidence and a disagreement both hold |
| Astra `154415Z` | three writers on ONE volume each see room and together cross the floor (5,091,328 bytes over in her run); with one volume-wide accounting step two pass and one waits | the server guard's disk rule (plan section 4): a rehearsal with several slot seals and a packer scratch write at once near the floor; the still-to-be-written peak is counted, pending promises subtracted once, the closing work reserved, a dead process's files reconciled before room is released |
| Astra `155309Z`, Neon `155330Z` | D4's pairs are chosen by the exact inequality T <= spare; rounding the spare down to whole seconds first would drop one admissible pair (11,110 instead of 11,111 in the second case) | `tools/budget.py`: exact fractions to the last step, one rounding down, in complete pairs |
| Astra `155407Z` | the home duplicate index at 16.4 million games (her SQLite build): 840,445,952 bytes after a checkpoint, the writer's peak memory 20,240 KiB; ONE reporting reader that keeps its snapshot open grows the write-ahead log to 279,653,272 bytes and no checkpoint can copy a frame until it closes | the home reader (plan 2.2, D8): a progress reader opens, reads and closes; home room counts the index, its log and the reserve on the real volume; to be measured again on the PC at its own page size and load |

## History of the script votes (the STANDARD vote lines collected, oldest first on the seats' clock; nothing is removed)

Astra's audit (`154202Z`): votes written in another layout are not in this table. For the first candidate of
version 2 (`d415d170...`) those are three NOT YET of Astra `134620Z` and three of Neon `134912Z`
(`engine_lines.py`, `uciproc.py`, `test_uciproc.py`), and Fable's inline YES of `215209Z`, repeated as standard
lines in `215907Z`. They change no row of the effective state above.

| stamp of the message | seat | verdict | file | sha256 (first 12, as the seat wrote it) | the manifest's bytes? |
|---|---|---|---|---|---|
| `142216Z` | astra | NOT YET | `scripts_v2/run/engine_lines.py` | `94e7518e9522` | no (earlier bytes) |
| `142216Z` | astra | NOT YET | `scripts_v2/run/uciproc.py` | `42cf67d9c462` | no (earlier bytes) |
| `143000Z` | neon | NOT YET | `scripts_v2/run/engine_lines.py` | `94e7518e9522` | no (earlier bytes) |
| `143000Z` | neon | NOT YET | `scripts_v2/run/uciproc.py` | `42cf67d9c462` | no (earlier bytes) |
| `144526Z` | astra | YES | `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | yes |
| `144526Z` | astra | NOT YET | `scripts_v2/run/uciproc.py` | `ab4e7ec8d3e4` | no (earlier bytes) |
| `144526Z` | astra | YES | `scripts_v2/tests/test_uciproc.py` | `4c8cef0910a6` | no (earlier bytes) |
| `145000Z` | neon | YES | `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | yes |
| `145000Z` | neon | NOT YET | `scripts_v2/run/uciproc.py` | `ab4e7ec8d3e4` | no (earlier bytes) |
| `145000Z` | neon | YES | `scripts_v2/tests/test_uciproc.py` | `4c8cef0910a6` | no (earlier bytes) |
| `145524Z` | astra | YES | `scripts_v2/run/uciproc.py` | `7de2728aef77` | yes |
| `145524Z` | astra | NOT YET | `scripts_v2/tests/test_uciproc.py` | `71fe6acd9332` | no (earlier bytes) |
| `145830Z` | neon | YES | `scripts_v2/run/uciproc.py` | `7de2728aef77` | yes |
| `145830Z` | neon | NOT YET | `scripts_v2/tests/test_uciproc.py` | `71fe6acd9332` | no (earlier bytes) |
| `215907Z` | fable | YES | `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | yes |
| `215907Z` | fable | YES | `scripts_v2/run/uciproc.py` | `7de2728aef77` | yes |
| `215907Z` | fable | NOT YET | `scripts_v2/tests/test_uciproc.py` | `71fe6acd9332` | no (earlier bytes) |
| `150142Z` | astra | YES | `scripts_v2/run/record.py` | `bc71fa894bf9` | yes |
| `150142Z` | astra | YES | `scripts_v2/tests/test_record.py` | `a8e16021f829` | yes |
| `150307Z` | astra | YES | `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | yes |
| `220510Z` | fable | YES | `scripts_v2/run/record.py` | `bc71fa894bf9` | yes |
| `220510Z` | fable | YES | `scripts_v2/tests/test_record.py` | `a8e16021f829` | yes |
| `220510Z` | fable | YES | `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | yes |
| `151130Z` | neon | YES | `scripts_v2/run/record.py` | `bc71fa894bf9` | yes |
| `151130Z` | neon | YES | `scripts_v2/tests/test_record.py` | `a8e16021f829` | yes |
| `151130Z` | neon | YES | `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | yes |
