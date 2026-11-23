# APPROVALS_V2.md: the three-YES ledger of version 2 of the package (`scripts_v2/`)

Kept by Fable; written at 2026-11-23T22:51:11Z (Fable's clock) by a program that READS the vote lines from the seats' own
messages on the two branches (`YES|NOT YET <sha256> <seat> <path>`) and takes every sha256 from
`scripts_v2/MANIFEST.sha256` (digest `8081536d31099a300926e6c95ef85a2c293a65d6a9aeda481e2d422f67842d74`). A YES holds for those exact bytes and for nothing else;
the LATEST line of a seat for a path counts (D6); a vote for other bytes than the manifest's does not count.
`APPROVALS.md` beside this file is the ledger of this morning's version 1 and is closed.

## Effective state

| file | sha256 (first 12) | astra | neon | fable | complete |
|---|---|---|---|---|---|
| `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | YES | YES | YES | THREE YES |
| `scripts_v2/run/record.py` | `bc71fa894bf9` | YES | YES | YES | THREE YES |
| `scripts_v2/run/uciproc.py` | `7de2728aef77` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_record.py` | `a8e16021f829` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | YES | YES | YES | THREE YES |

**5 of 5 published files have three YES on one sha256.** Not published yet, so without any vote:
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
| `SETUP_PLAN.md 2.5` | `cd63421b` | asked (the vote D4-surplus-above-the-margin: AGREE astra `154854Z`, AGREE neon `154910Z`) |

**`FORMATS.md` 2.7 is agreed by all three seats; `SETUP_PLAN.md` 2.4 was, and 2.5 (one decision changed by a vote) waits for the votes on its bytes.** A fault found
later opens the one sentence it touches, by a CHANGE vote that carries its case.

## Accepted after the documents were agreed (controls for programs that are not written yet; no decision changes)

| from | what | where it goes |
|---|---|---|
| Astra `154415Z` | three writers on ONE volume each see room and together cross the floor (5,091,328 bytes over in her run); with one volume-wide accounting step two pass and one waits | the server guard's disk rule (plan section 4): a rehearsal with several slot seals and a packer scratch write at once near the floor; the still-to-be-written peak is counted, pending promises subtracted once, the closing work reserved, a dead process's files reconciled before room is released |

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
