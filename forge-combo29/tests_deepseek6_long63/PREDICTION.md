# deepseek6 long 63 — PREDICTION (written before the first stress cycle)

Item (file 15, long 63): **HASH RESIZE STRESS under ASan + UBSan.** One process, 300 cycles (seed 63): setoption
Hash 1..1024 (random), sometimes `ucinewgame`, a random G position, `go depth 8`. Then the same with a fresh
process per cycle. Table: crashes / sanitizer lines / illegal bestmoves / the largest resident memory seen against
the Hash set.

Model: DeepSeek V4.1 Flash 1017, chat 1794862262. Time: `stamps.txt`.

## Fixed now
- Build: **the ASan+UBSan build from my long 34**, `/tmp/ds6/long34/basan/forge`, sha256
  `41e592fa72246fb9fc1524ca8955c14c24f06e83ed95e61d4de6cfc93d9235b1`, plain 6b98f217 with
  `-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1`. Re-verified just now: `perft 4` = 197,281.
  No new build needed; the item tests a runtime path, not a patch.
- **Seed 63** for every random choice (Hash value, which G position, whether `ucinewgame`), so the 300 cycles are
  reproducible from the script.
- **Both process models**: (A) one process, 300 cycles; (B) a fresh process per cycle. 600 searches total.
- **Memory**: read `VmHWM` (peak resident) from `/proc/<pid>/status` after each cycle in model A, and after each
  process's exit in model B the same way before it dies — model B's peak is per process, so the table reports the
  maximum across cycles and says which model it came from.
- Legality of every bestmove with python-chess.

## Predictions, each with the range that kills it

**P1 — no crashes in either model.** Kill range: any signal death or nonzero exit not caused by a sanitizer report.

**P2 — no ASan or UBSan report in either model.** Resizing the table between searches is exactly the kind of thing
that could leave a dangling pointer, so this is the item's real question. Kill range: any report → headline.

**P3 — every bestmove legal, all 600.** Kill range: any illegal or missing bestmove.

**P4 — peak RSS grows with the Hash value but never exceeds it plus a modest overhead**: the largest Hash (1024 MB)
gives a peak between 1.0 GB and 2.0 GB, and a 1 MB Hash gives a peak below 100 MB. Kill range: a peak above 2.5 GB
(a leak or an over-allocation), or a 1 MB run above 200 MB.

**P5 — model A's peak is at least as large as model B's.** One long-lived process accumulates whatever the
allocator does not return; a fresh process starts clean each time. Kill range: model A's peak below model B's by
more than 10 %.

**P6 — budget.** 600 depth-8 searches under ASan: about 15–35 minutes. Kill range: one cycle over 300 s gets
killed and counted as a timeout, not as a result.

## What would make me report "not done"
A sanitizer build that fails `perft 4`, a run I cannot finish (then the report names the cycles completed and quotes
no global count), or a crash I cannot attribute — which would itself be the finding.
