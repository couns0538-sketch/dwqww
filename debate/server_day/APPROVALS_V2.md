# APPROVALS_V2.md: the three-YES ledger of version 2 of the package (`scripts_v2/`)

Kept by Fable; written at 20261125T232106Z (the PC's clock) by a program that READS the vote lines from the seats' own
messages on the two branches (`YES|NOT YET <sha256> <seat> <path>`) and takes every sha256 from
`scripts_v2/MANIFEST.sha256` (digest `bbf8bd6ab708c577173eda222e13c4d8d57289de0f34826c107021af1ea8d204`). A YES holds for those exact bytes and for nothing else
(D6): a cell shows the seat's LATEST line on the manifest's bytes, by the full stamp of its message; a
line on other bytes neither helps nor harms, and `for other bytes` stands only where the seat has no line on
the manifest's bytes. The stamps of messages written on the PC (`_fable_`, `_opus_`) run 7 hours ahead of UTC
(the PC's clock); they are put 7 hours back before anything is ordered, and the history shows both times.
`APPROVALS.md` beside this file is the ledger of version 1 and is closed.

## Effective state

| file | sha256 (first 12) | astra | neon | fable | complete |
|---|---|---|---|---|---|
| `scripts_v2/home/content.py` | `0e9cbb2825ed` | for other bytes | for other bytes | YES | no |
| `scripts_v2/home/credit.py` | `0b06ca51b33b` | - | - | - | no |
| `scripts_v2/home/custody.py` | `1079a8a6c268` | for other bytes | for other bytes | YES | no |
| `scripts_v2/home/deliver.py` | `2da1b3070d78` | - | - | - | no |
| `scripts_v2/home/drain.py` | `3b88fcbd0053` | - | - | - | no |
| `scripts_v2/home/fetch.py` | `9d8942ba93bf` | - | - | - | no |
| `scripts_v2/home/publish.py` | `834ae853cb2b` | - | - | YES | no |
| `scripts_v2/known/SOURCE.sha256` | `6e54cd3b5923` | YES | YES | - | no |
| `scripts_v2/known/n12_batch.json` | `6036d1896f5c` | YES | YES | NOT YET | no |
| `scripts_v2/known/n12_no_newgame.json` | `900a7fa78f93` | YES | YES | NOT YET | no |
| `scripts_v2/known/n12_writeminply9.json` | `d3e38d0a444e` | YES | YES | NOT YET | no |
| `scripts_v2/known/profile.json` | `2acaa7917c35` | YES | YES | NOT YET | no |
| `scripts_v2/known/rules_records.txt` | `d30ef62f137a` | YES | YES | - | no |
| `scripts_v2/known/startup.json` | `b242e6e0df8a` | YES | YES | NOT YET | no |
| `scripts_v2/known/startup_hash32.json` | `b59ac8d71f03` | YES | YES | NOT YET | no |
| `scripts_v2/known/verify.json` | `b157be9e7589` | YES | YES | NOT YET | no |
| `scripts_v2/run/admit.py` | `428773a45a5d` | - | - | - | no |
| `scripts_v2/run/bind_exec.py` | `a85c30e99e6d` | - | - | - | no |
| `scripts_v2/run/bootguard.py` | `61aa78d45ac7` | for other bytes | for other bytes | YES | no |
| `scripts_v2/run/clockwatch.py` | `b55857dc5200` | YES | YES | YES | THREE YES |
| `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | YES | YES | YES | THREE YES |
| `scripts_v2/run/guard.py` | `93064476daca` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/run/launcher.py` | `a669beeb15fe` | for other bytes | for other bytes | YES | no |
| `scripts_v2/run/machine.py` | `48b7ba29c9d5` | - | - | - | no |
| `scripts_v2/run/packer.py` | `3a5716b22acf` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/run/record.py` | `bc71fa894bf9` | YES | YES | YES | THREE YES |
| `scripts_v2/run/terminal.py` | `1de45eb6da2b` | for other bytes | for other bytes | YES | no |
| `scripts_v2/run/uciproc.py` | `d9d2b9913419` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/run/worker.py` | `b99ac8f9e249` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/tests/fake_transport.py` | `754988251dc3` | - | - | - | no |
| `scripts_v2/tests/test_admit.py` | `913972e281e3` | - | - | - | no |
| `scripts_v2/tests/test_bootguard.py` | `9c1ab4f423db` | for other bytes | for other bytes | - | no |
| `scripts_v2/tests/test_budget.py` | `52ef5a1454be` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_clockwatch.py` | `c103d0c2a22e` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_content.py` | `e319128fd886` | for other bytes | for other bytes | - | no |
| `scripts_v2/tests/test_credit.py` | `29f034a508e0` | - | - | - | no |
| `scripts_v2/tests/test_custody.py` | `f6b446692515` | for other bytes | for other bytes | YES | no |
| `scripts_v2/tests/test_deliver.py` | `2dfae6f44a0a` | - | - | - | no |
| `scripts_v2/tests/test_drain.py` | `bce458e1fa07` | - | - | - | no |
| `scripts_v2/tests/test_fetch.py` | `514763587d7a` | - | - | - | no |
| `scripts_v2/tests/test_guard.py` | `1b20c0383e8f` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/tests/test_launcher.py` | `c2e66748e971` | for other bytes | for other bytes | - | no |
| `scripts_v2/tests/test_machine.py` | `39b79530bc42` | - | - | - | no |
| `scripts_v2/tests/test_make_control.py` | `5738a21baf1c` | for other bytes | for other bytes | - | no |
| `scripts_v2/tests/test_packer.py` | `c76f8453a4d8` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/tests/test_publish.py` | `728c193a3594` | - | - | - | no |
| `scripts_v2/tests/test_record.py` | `a8e16021f829` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_terminal.py` | `985d84d4ccea` | for other bytes | for other bytes | - | no |
| `scripts_v2/tests/test_uciproc.py` | `5b790c6bf1cf` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/tests/test_unit.py` | `57d018bbef8d` | YES | YES | YES | THREE YES |
| `scripts_v2/tests/test_worker.py` | `f116645bbe0c` | for other bytes | for other bytes | for other bytes | no |
| `scripts_v2/tools/budget.py` | `76817badf22c` | YES | YES | YES | THREE YES |
| `scripts_v2/tools/make_control.py` | `8ddf2a67662e` | for other bytes | for other bytes | - | no |
| `scripts_v2/unit/forgeday.service` | `e389cd998305` | YES | YES | YES | THREE YES |
| `scripts_v2/workloads/MANIFEST.json` | `4ad65b32de0d` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/n12_batch.uci` | `b68eb978741b` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/n12_no_newgame.uci` | `e202ce2dc369` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/n12_writeminply9.uci` | `9cd2ff9dbc63` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/options.uci` | `c51740f9f8c2` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/profile.uci` | `d4bd708f16b7` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/selfgame_line.txt` | `5cf2b0ff6dc4` | YES | YES | YES | THREE YES |
| `scripts_v2/workloads/startup.uci` | `263d10958395` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/startup_hash32.uci` | `f212e4bfb8cc` | YES | YES | NOT YET | no |
| `scripts_v2/workloads/verify.uci` | `496e7c09aa27` | YES | YES | NOT YET | no |

**10 of 64 published files have three YES on one sha256.**

## The documents

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
| `specs/ (all 14 files, sorted set hash)` | `430a52d6` | AGREE astra, AGREE neon (Neon's closing note `20261124T012200Z`, section 1); AGREE fable (his vote message of 25 Nov 2026): agreed by all three |
| `FINAL_FOR_THE_OWNER.md` | `b7f00182` | AGREE astra, AGREE neon (the same note, section 1); AGREED fable (his check of 24 Nov 2026 on the PC, given on the branch in his vote message of 25 Nov 2026): agreed by all three |

**Agreed by all three seats: `SETUP_PLAN.md` 2.7 (`4100b2a5`) and `FORMATS.md` 2.9 (`ac566296`), the current bytes of both documents.** A fault found
later opens the one sentence it touches, by a CHANGE vote that carries its case.

## Accepted after the documents were agreed (controls for programs that are not written yet; no decision changes)

| from | what | where it goes |
|---|---|---|
| Astra `161634Z` | a control record whose decision or assigned pairs differ from the linked budget report, every checksum valid by itself (her fixture: held, zero schedules; eight process exits at the four steps of evidence first, control last: one schedule or one fence after recovery) | the server guard and its test: before a schedule is granted the control record and the linked report are compared field by field; missing evidence and a disagreement both hold |
| Astra `154415Z` | three writers on ONE volume each see room and together cross the floor (5,091,328 bytes over in her run); with one volume-wide accounting step two pass and one waits | the server guard's disk rule (plan section 4): a rehearsal with several slot seals and a packer scratch write at once near the floor; the still-to-be-written peak is counted, pending promises subtracted once, the closing work reserved, a dead process's files reconciled before room is released |
| Astra `155309Z`, Neon `155330Z` | D4's pairs are chosen by the exact inequality T <= spare; rounding the spare down to whole seconds first would drop one admissible pair (11,110 instead of 11,111 in the second case) | `tools/budget.py`: exact fractions to the last step, one rounding down, in complete pairs |
| Astra `155407Z` | the home duplicate index at 16.4 million games (her SQLite build): 840,445,952 bytes after a checkpoint, the writer's peak memory 20,240 KiB; ONE reporting reader that keeps its snapshot open grows the write-ahead log to 279,653,272 bytes and no checkpoint can copy a frame until it closes | the home reader (plan 2.2, D8): a progress reader opens, reads and closes; home room counts the index, its log and the reserve on the real volume; to be measured again on the PC at its own page size and load |

## History of the script votes (the STANDARD vote lines collected, oldest first in UTC; nothing is removed)

Astra's audit (`154202Z`): votes written in another layout are not in this table. For the first candidate of
version 2 (`d415d170...`) those are three NOT YET of Astra `134620Z` and three of Neon `134912Z`
(`engine_lines.py`, `uciproc.py`, `test_uciproc.py`), and Fable's inline YES of `215209Z`, repeated as standard
lines in `215907Z`. They change no row of the effective state above.

| UTC | stamp of the message | seat | verdict | file | sha256 (first 12, as the seat wrote it) | the manifest's bytes? |
|---|---|---|---|---|---|---|
| `20261123T142216Z` | `20261123T142216Z` | astra | NOT YET | `scripts_v2/run/engine_lines.py` | `94e7518e9522` | no (other bytes) |
| `20261123T142216Z` | `20261123T142216Z` | astra | NOT YET | `scripts_v2/run/uciproc.py` | `42cf67d9c462` | no (other bytes) |
| `20261123T143000Z` | `20261123T143000Z` | neon | NOT YET | `scripts_v2/run/engine_lines.py` | `94e7518e9522` | no (other bytes) |
| `20261123T143000Z` | `20261123T143000Z` | neon | NOT YET | `scripts_v2/run/uciproc.py` | `42cf67d9c462` | no (other bytes) |
| `20261123T144526Z` | `20261123T144526Z` | astra | NOT YET | `scripts_v2/run/uciproc.py` | `ab4e7ec8d3e4` | no (other bytes) |
| `20261123T144526Z` | `20261123T144526Z` | astra | YES | `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | yes |
| `20261123T144526Z` | `20261123T144526Z` | astra | YES | `scripts_v2/tests/test_uciproc.py` | `4c8cef0910a6` | no (other bytes) |
| `20261123T145000Z` | `20261123T145000Z` | neon | NOT YET | `scripts_v2/run/uciproc.py` | `ab4e7ec8d3e4` | no (other bytes) |
| `20261123T145000Z` | `20261123T145000Z` | neon | YES | `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | yes |
| `20261123T145000Z` | `20261123T145000Z` | neon | YES | `scripts_v2/tests/test_uciproc.py` | `4c8cef0910a6` | no (other bytes) |
| `20261123T145524Z` | `20261123T145524Z` | astra | NOT YET | `scripts_v2/tests/test_uciproc.py` | `71fe6acd9332` | no (other bytes) |
| `20261123T145524Z` | `20261123T145524Z` | astra | YES | `scripts_v2/run/uciproc.py` | `7de2728aef77` | no (other bytes) |
| `20261123T145830Z` | `20261123T145830Z` | neon | NOT YET | `scripts_v2/tests/test_uciproc.py` | `71fe6acd9332` | no (other bytes) |
| `20261123T145830Z` | `20261123T145830Z` | neon | YES | `scripts_v2/run/uciproc.py` | `7de2728aef77` | no (other bytes) |
| `20261123T145907Z` | `20261123T215907Z` (PC) | fable | NOT YET | `scripts_v2/tests/test_uciproc.py` | `71fe6acd9332` | no (other bytes) |
| `20261123T145907Z` | `20261123T215907Z` (PC) | fable | YES | `scripts_v2/run/engine_lines.py` | `a82eb9c85f28` | yes |
| `20261123T145907Z` | `20261123T215907Z` (PC) | fable | YES | `scripts_v2/run/uciproc.py` | `7de2728aef77` | no (other bytes) |
| `20261123T150142Z` | `20261123T150142Z` | astra | YES | `scripts_v2/run/record.py` | `bc71fa894bf9` | yes |
| `20261123T150142Z` | `20261123T150142Z` | astra | YES | `scripts_v2/tests/test_record.py` | `a8e16021f829` | yes |
| `20261123T150307Z` | `20261123T150307Z` | astra | YES | `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | no (other bytes) |
| `20261123T150510Z` | `20261123T220510Z` (PC) | fable | YES | `scripts_v2/run/record.py` | `bc71fa894bf9` | yes |
| `20261123T150510Z` | `20261123T220510Z` (PC) | fable | YES | `scripts_v2/tests/test_record.py` | `a8e16021f829` | yes |
| `20261123T150510Z` | `20261123T220510Z` (PC) | fable | YES | `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | no (other bytes) |
| `20261123T151130Z` | `20261123T151130Z` | neon | YES | `scripts_v2/run/record.py` | `bc71fa894bf9` | yes |
| `20261123T151130Z` | `20261123T151130Z` | neon | YES | `scripts_v2/tests/test_record.py` | `a8e16021f829` | yes |
| `20261123T151130Z` | `20261123T151130Z` | neon | YES | `scripts_v2/tests/test_uciproc.py` | `690b3243764c` | no (other bytes) |
| `20261123T162055Z` | `20261123T162055Z` | neon | NOT YET | `scripts_v2/tests/test_budget.py` | `2c0fc9f67990` | no (other bytes) |
| `20261123T162055Z` | `20261123T162055Z` | neon | NOT YET | `scripts_v2/tools/budget.py` | `c7aab952d886` | no (other bytes) |
| `20261123T162624Z` | `20261123T162624Z` | astra | NOT YET | `scripts_v2/tests/test_budget.py` | `2c0fc9f67990` | no (other bytes) |
| `20261123T162624Z` | `20261123T162624Z` | astra | NOT YET | `scripts_v2/tools/budget.py` | `c7aab952d886` | no (other bytes) |
| `20261123T165352Z` | `20261123T165352Z` | astra | NOT YET | `scripts_v2/run/clockwatch.py` | `15e76dafaa18` | no (other bytes) |
| `20261123T165352Z` | `20261123T165352Z` | astra | NOT YET | `scripts_v2/tests/test_clockwatch.py` | `20458abd7601` | no (other bytes) |
| `20261123T165415Z` | `20261123T165415Z` | astra | NOT YET | `scripts_v2/tests/test_budget.py` | `b419d5bb16bd` | no (other bytes) |
| `20261123T165415Z` | `20261123T165415Z` | astra | NOT YET | `scripts_v2/tools/budget.py` | `24b6adedafc1` | no (other bytes) |
| `20261123T170114Z` | `20261123T170114Z` | neon | NOT YET | `scripts_v2/run/clockwatch.py` | `15e76dafaa18` | no (other bytes) |
| `20261123T170114Z` | `20261123T170114Z` | neon | NOT YET | `scripts_v2/tests/test_budget.py` | `b419d5bb16bd` | no (other bytes) |
| `20261123T170114Z` | `20261123T170114Z` | neon | NOT YET | `scripts_v2/tests/test_clockwatch.py` | `20458abd7601` | no (other bytes) |
| `20261123T170114Z` | `20261123T170114Z` | neon | NOT YET | `scripts_v2/tools/budget.py` | `24b6adedafc1` | no (other bytes) |
| `20261123T171731Z` | `20261124T001731Z` (PC) | fable | YES | `scripts_v2/run/clockwatch.py` | `d21930a14093` | no (other bytes) |
| `20261123T171731Z` | `20261124T001731Z` (PC) | fable | YES | `scripts_v2/tests/test_budget.py` | `52ef5a1454be` | yes |
| `20261123T171731Z` | `20261124T001731Z` (PC) | fable | YES | `scripts_v2/tests/test_clockwatch.py` | `507883bafae0` | no (other bytes) |
| `20261123T171731Z` | `20261124T001731Z` (PC) | fable | YES | `scripts_v2/tools/budget.py` | `76817badf22c` | yes |
| `20261123T172109Z` | `20261123T172109Z` | astra | YES | `scripts_v2/tests/test_budget.py` | `52ef5a1454be` | yes |
| `20261123T172109Z` | `20261123T172109Z` | astra | YES | `scripts_v2/tools/budget.py` | `76817badf22c` | yes |
| `20261123T172124Z` | `20261123T172124Z` | astra | NOT YET | `scripts_v2/run/clockwatch.py` | `d21930a14093` | no (other bytes) |
| `20261123T172124Z` | `20261123T172124Z` | astra | NOT YET | `scripts_v2/tests/test_clockwatch.py` | `507883bafae0` | no (other bytes) |
| `20261123T172517Z` | `20261123T172517Z` | neon | NOT YET | `scripts_v2/run/clockwatch.py` | `d21930a14093` | no (other bytes) |
| `20261123T172517Z` | `20261123T172517Z` | neon | NOT YET | `scripts_v2/tests/test_clockwatch.py` | `507883bafae0` | no (other bytes) |
| `20261123T172517Z` | `20261123T172517Z` | neon | YES | `scripts_v2/tests/test_budget.py` | `52ef5a1454be` | yes |
| `20261123T172517Z` | `20261123T172517Z` | neon | YES | `scripts_v2/tools/budget.py` | `76817badf22c` | yes |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | NOT YET | `scripts_v2/run/guard.py` | `67384d4b5e3d` | no (other bytes) |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | NOT YET | `scripts_v2/tests/test_guard.py` | `a08023048ccf` | no (other bytes) |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | YES | `scripts_v2/run/clockwatch.py` | `b55857dc5200` | yes |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | YES | `scripts_v2/run/packer.py` | `1db134622736` | no (other bytes) |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | YES | `scripts_v2/run/worker.py` | `218f7eae73e0` | no (other bytes) |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | YES | `scripts_v2/tests/test_clockwatch.py` | `c103d0c2a22e` | yes |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | YES | `scripts_v2/tests/test_packer.py` | `ee1e0db676d5` | no (other bytes) |
| `20261123T200453Z` | `20261124T030453Z` (PC) | fable | YES | `scripts_v2/tests/test_worker.py` | `a602037e7b83` | no (other bytes) |
| `20261123T213401Z` | `20261123T213401Z` | astra | YES | `scripts_v2/run/clockwatch.py` | `b55857dc5200` | yes |
| `20261123T213401Z` | `20261123T213401Z` | astra | YES | `scripts_v2/tests/test_clockwatch.py` | `c103d0c2a22e` | yes |
| `20261123T213447Z` | `20261123T213447Z` | astra | NOT YET | `scripts_v2/tests/test_unit.py` | `57d018bbef8d` | yes |
| `20261123T213447Z` | `20261123T213447Z` | astra | NOT YET | `scripts_v2/unit/forgeday.service` | `e389cd998305` | yes |
| `20261123T213621Z` | `20261123T213621Z` | astra | NOT YET | `scripts_v2/home/custody.py` | `d46817f23f72` | no (other bytes) |
| `20261123T213621Z` | `20261123T213621Z` | astra | NOT YET | `scripts_v2/tests/test_custody.py` | `a42965f17d50` | no (other bytes) |
| `20261123T213704Z` | `20261123T213704Z` | astra | YES | `scripts_v2/tests/test_unit.py` | `57d018bbef8d` | yes |
| `20261123T213704Z` | `20261123T213704Z` | astra | YES | `scripts_v2/unit/forgeday.service` | `e389cd998305` | yes |
| `20261123T214130Z` | `20261123T214130Z` | astra | NOT YET | `scripts_v2/tests/test_make_control.py` | `14ed7d71cb6a` | no (other bytes) |
| `20261123T214130Z` | `20261123T214130Z` | astra | NOT YET | `scripts_v2/tools/make_control.py` | `5f8dacae4ccf` | no (other bytes) |
| `20261123T214602Z` | `20261123T214602Z` | astra | NOT YET | `scripts_v2/run/terminal.py` | `9d640c11b8fa` | no (other bytes) |
| `20261123T214602Z` | `20261123T214602Z` | astra | NOT YET | `scripts_v2/tests/test_terminal.py` | `51702bf85909` | no (other bytes) |
| `20261123T214616Z` | `20261123T214616Z` | astra | NOT YET | `scripts_v2/run/launcher.py` | `f95453041fd5` | no (other bytes) |
| `20261123T214616Z` | `20261123T214616Z` | astra | NOT YET | `scripts_v2/tests/test_launcher.py` | `2cf7e0f42649` | no (other bytes) |
| `20261123T214759Z` | `20261123T214759Z` | astra | NOT YET | `scripts_v2/run/bootguard.py` | `fa8ab1b53013` | no (other bytes) |
| `20261123T214759Z` | `20261123T214759Z` | astra | NOT YET | `scripts_v2/tests/test_bootguard.py` | `06fb0c248e06` | no (other bytes) |
| `20261123T214929Z` | `20261123T214929Z` | astra | NOT YET | `scripts_v2/run/packer.py` | `1db134622736` | no (other bytes) |
| `20261123T214929Z` | `20261123T214929Z` | astra | NOT YET | `scripts_v2/tests/test_packer.py` | `ee1e0db676d5` | no (other bytes) |
| `20261123T215151Z` | `20261123T215151Z` | astra | NOT YET | `scripts_v2/run/guard.py` | `67384d4b5e3d` | no (other bytes) |
| `20261123T215151Z` | `20261123T215151Z` | astra | NOT YET | `scripts_v2/tests/test_guard.py` | `a08023048ccf` | no (other bytes) |
| `20261123T215331Z` | `20261123T215331Z` | astra | NOT YET | `scripts_v2/run/worker.py` | `218f7eae73e0` | no (other bytes) |
| `20261123T215331Z` | `20261123T215331Z` | astra | NOT YET | `scripts_v2/tests/test_worker.py` | `a602037e7b83` | no (other bytes) |
| `20261123T220400Z` | `20261123T220400Z` | neon | YES | `scripts_v2/run/clockwatch.py` | `b55857dc5200` | yes |
| `20261123T220400Z` | `20261123T220400Z` | neon | YES | `scripts_v2/tests/test_clockwatch.py` | `c103d0c2a22e` | yes |
| `20261123T220400Z` | `20261123T220400Z` | neon | YES | `scripts_v2/tests/test_unit.py` | `57d018bbef8d` | yes |
| `20261123T220400Z` | `20261123T220400Z` | neon | YES | `scripts_v2/unit/forgeday.service` | `e389cd998305` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/SOURCE.sha256` | `6e54cd3b5923` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/n12_batch.json` | `6036d1896f5c` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/n12_no_newgame.json` | `900a7fa78f93` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/n12_writeminply9.json` | `d3e38d0a444e` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/profile.json` | `2acaa7917c35` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/startup.json` | `b242e6e0df8a` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/startup_hash32.json` | `b59ac8d71f03` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/known/verify.json` | `b157be9e7589` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/n12_batch.uci` | `b68eb978741b` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/n12_no_newgame.uci` | `e202ce2dc369` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/n12_writeminply9.uci` | `9cd2ff9dbc63` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/options.uci` | `c51740f9f8c2` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/profile.uci` | `d4bd708f16b7` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/selfgame_line.txt` | `5cf2b0ff6dc4` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/startup.uci` | `263d10958395` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/startup_hash32.uci` | `f212e4bfb8cc` | yes |
| `20261123T221646Z` | `20261123T221646Z` | astra | YES | `scripts_v2/workloads/verify.uci` | `496e7c09aa27` | yes |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/run/bootguard.py` | `fa8ab1b53013` | no (other bytes) |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/run/launcher.py` | `f95453041fd5` | no (other bytes) |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/run/terminal.py` | `9d640c11b8fa` | no (other bytes) |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/tests/test_bootguard.py` | `06fb0c248e06` | no (other bytes) |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/tests/test_launcher.py` | `2cf7e0f42649` | no (other bytes) |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/tests/test_make_control.py` | `14ed7d71cb6a` | no (other bytes) |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/tests/test_terminal.py` | `51702bf85909` | no (other bytes) |
| `20261123T222600Z` | `20261123T222600Z` | neon | NOT YET | `scripts_v2/tools/make_control.py` | `5f8dacae4ccf` | no (other bytes) |
| `20261123T222736Z` | `20261123T222736Z` | astra | YES | `scripts_v2/known/rules_records.txt` | `d30ef62f137a` | yes |
| `20261123T222736Z` | `20261123T222736Z` | astra | YES | `scripts_v2/workloads/MANIFEST.json` | `4ad65b32de0d` | yes |
| `20261123T222809Z` | `20261123T222809Z` | astra | NOT YET | `scripts_v2/home/content.py` | `dcf85129d917` | no (other bytes) |
| `20261123T222809Z` | `20261123T222809Z` | astra | NOT YET | `scripts_v2/tests/test_content.py` | `31bcabad3880` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/home/content.py` | `dcf85129d917` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/home/custody.py` | `d46817f23f72` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/run/guard.py` | `67384d4b5e3d` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/run/packer.py` | `1db134622736` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/run/worker.py` | `218f7eae73e0` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/tests/test_content.py` | `31bcabad3880` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/tests/test_custody.py` | `a42965f17d50` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/tests/test_guard.py` | `a08023048ccf` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/tests/test_packer.py` | `ee1e0db676d5` | no (other bytes) |
| `20261123T223800Z` | `20261123T223800Z` | neon | NOT YET | `scripts_v2/tests/test_worker.py` | `a602037e7b83` | no (other bytes) |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/SOURCE.sha256` | `6e54cd3b5923` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/n12_batch.json` | `6036d1896f5c` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/n12_no_newgame.json` | `900a7fa78f93` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/n12_writeminply9.json` | `d3e38d0a444e` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/profile.json` | `2acaa7917c35` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/rules_records.txt` | `d30ef62f137a` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/startup.json` | `b242e6e0df8a` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/startup_hash32.json` | `b59ac8d71f03` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/known/verify.json` | `b157be9e7589` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/MANIFEST.json` | `4ad65b32de0d` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/n12_batch.uci` | `b68eb978741b` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/n12_no_newgame.uci` | `e202ce2dc369` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/n12_writeminply9.uci` | `9cd2ff9dbc63` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/options.uci` | `c51740f9f8c2` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/profile.uci` | `d4bd708f16b7` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/selfgame_line.txt` | `5cf2b0ff6dc4` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/startup.uci` | `263d10958395` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/startup_hash32.uci` | `f212e4bfb8cc` | yes |
| `20261123T225200Z` | `20261123T225200Z` | neon | YES | `scripts_v2/workloads/verify.uci` | `496e7c09aa27` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/known/n12_batch.json` | `6036d1896f5c` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/known/n12_no_newgame.json` | `900a7fa78f93` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/known/n12_writeminply9.json` | `d3e38d0a444e` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/known/profile.json` | `2acaa7917c35` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/known/startup.json` | `b242e6e0df8a` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/known/startup_hash32.json` | `b59ac8d71f03` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/known/verify.json` | `b157be9e7589` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/MANIFEST.json` | `4ad65b32de0d` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/n12_batch.uci` | `b68eb978741b` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/n12_no_newgame.uci` | `e202ce2dc369` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/n12_writeminply9.uci` | `9cd2ff9dbc63` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/options.uci` | `c51740f9f8c2` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/profile.uci` | `d4bd708f16b7` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/startup.uci` | `263d10958395` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/startup_hash32.uci` | `f212e4bfb8cc` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | NOT YET | `scripts_v2/workloads/verify.uci` | `496e7c09aa27` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/home/content.py` | `0e9cbb2825ed` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/home/custody.py` | `1079a8a6c268` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/home/publish.py` | `834ae853cb2b` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/run/bootguard.py` | `61aa78d45ac7` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/run/clockwatch.py` | `b55857dc5200` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/run/launcher.py` | `a669beeb15fe` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/run/terminal.py` | `1de45eb6da2b` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/tests/test_clockwatch.py` | `c103d0c2a22e` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/tests/test_custody.py` | `f6b446692515` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/tests/test_unit.py` | `57d018bbef8d` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/unit/forgeday.service` | `e389cd998305` | yes |
| `20261125T161345Z` | `20261125T231345Z` (PC) | fable | YES | `scripts_v2/workloads/selfgame_line.txt` | `5cf2b0ff6dc4` | yes |
