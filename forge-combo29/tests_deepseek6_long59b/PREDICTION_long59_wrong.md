# deepseek6 long 59 — PREDICTION (written before the first threaded run)

Item (file 15, long 59): **THREADS under ThreadSanitizer.** `Threads` 2, 4 and 8 on **all of G at depth 10**
(fresh `ucinewgame`), **S14 and plain defaults**. Report counts, legality of every bestmove, and the planted race
(long 22's) at 8 threads. Clear `TSAN_OPTIONS` first (long 22's lesson). Known: long 22 found 0 reports at 2 and 4.

Model: DeepSeek V4.1 Flash 1017, chat 1794862262. Time: `stamps.txt`, its first line is the claim.

## Fixed now

- **Build:** `/tmp/ds6/long59/btsan/forge`, plain 6b98f217 + `-fsanitize=thread -fno-omit-frame-pointer -g -O1`
  and **`-DFORGE_SPD_TT_NOTLS=0`** (the TT-not-thread-local speed switch off, so the shared table is instrumented
  rather than hidden behind a thread-local — without this a TT race could not be seen at all). sha256
  `40ec3ec5f3aa52de3936e66d652fd934423d8da1b46e97815d25a59086274f2d`.
  The build's `perft 5` = **4,865,609** and its `uci` handshake is clean with **0 ThreadSanitizer warnings**
  (`raw/uci.txt`, `raw/perft5.txt`).
- **`TSAN_OPTIONS`** = `halt_on_error=0 second_deadlock_stack=1` — do not halt on the first report, so one run can
  collect every report it has, and record the deadlock stack if a lock hangs (long 22's lesson was to clear the
  environment first; I set it explicitly instead of inheriting anything).
- **Runs:** 2 option bases (S14 and plain defaults) x 3 thread counts (2, 4, 8) = **6 runs over all 353 G
  positions at depth 10**, fresh `ucinewgame` + `isready` before every `go`, Hash 16, OwnBook false.
  Plus the **planted race at 8 threads**.
- Legality of every bestmove is checked with python-chess 1.11.2.

## Predictions, each with the range that kills it

**P1 — zero ThreadSanitizer reports in all six runs.** Long 22 found 0 at 2 and 4 threads; 8 threads is the new
case. Kill range: any report → that is the item's headline and I commit the raw log.

**P2 — every bestmove legal, all 2,118 searches (6 x 353).** Kill range: any illegal or missing bestmove.

**P3 — the planted race IS reported at 8 threads.** I plant two threads incrementing one non-atomic global without
a lock in a COPY of the tree; ThreadSanitizer must print a `data race` report and I must be able to point at the
line. Kill range: no report → the sanitizer is not live and P1 is meaningless, so I would then report the plant as
a failure of the harness, not a clean engine.

**P4 — the node totals are NOT identical across thread counts.** Search with 2+ threads is not deterministic in
this engine (helper threads share the table), so I predict 2, 4 and 8 threads give three different G sums, and
different again from the 1-thread reference. Kill range: all three identical → that would mean the helpers are
not doing anything, itself a finding.

**P5 — the runs are slow under TSAN: 20-50 minutes for the six.** TSAN costs 5-15x; G at depth 10 on 1 thread was
about 1.3 M nodes per position in long 58 at depth 14, and depth 10 is much cheaper, but 353 positions x 6 runs is
still large. Kill range: if a single run exceeds 1800 s I take the part done and report the rest as not done.

**P6 — the legality of bestmoves does not degrade with thread count** (a shared-table bug would more likely show
as a wrong node count than an illegal move). Kill range: an illegal move at 8 threads but not at 2 would be a real
finding against P6.

## What would make me report "not done"
A build that fails `perft 5`, a TSAN run that hangs (killed at 1800 s, counted as "hang"), or a plant that is not
reported (then P1's clean result is worthless and I say so).
