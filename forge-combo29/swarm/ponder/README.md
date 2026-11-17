# Ponder protocol audit — `forge-combo29` @ `6b98f217`

The ponder cycle is the surface every match runner uses and the least tested
part of this engine. This folder is the audit: six protocol questions, measured
on a build whose four honesty pins are confirmed, with every wait bounded.

**Read `FINDINGS.md` first** — it carries the verdicts, the tables, and the
limits. `STATUS.md` is the one-page summary.

## The answer in one paragraph

`ponderhit` converts a ponder search into a normal clocked search, and the
budget is measured **from the `ponderhit`, not from the original `go`** — proved
by a ponder 26.7× longer than the hard limit still receiving a full fresh budget
(225.9 ms against a 225 ms limit) and by 16/16 offsets never returning in ~0 ms.
A `go ponder` with **no** `ponderhit` is unbounded **whether or not a clock was
supplied**, in two distinct regimes: a runaway search at 100% CPU, and a
finished search sitting idle on its answer. `stop` recovers either in under 1 ms
and returns the move the search had found, never `0000`. A stray `ponderhit` is
silent. The `Ponder` option is a formatting flag that only appends
` ponder <move>` — and it is **off by default**.

## Layout

```
FINDINGS.md          the audit: verdicts, 15 generated tables, limits, gaps
STATUS.md            one page: verdicts, the three timings, reproduction

scripts/
  uci_driver.py              bounded UCI client (deadline or SIGKILL, never a hang)
  probe_ponder.py            items 1-6 + the no-ponder control
  probe_ponder2.py           budget-origin sweep, mid-ponder interrupts, option path
  probe_ponder3.py           three clocks, self-ponder null, time-field origin
  probe_ponder4.py           self-limited ponder, terminal root, late ponderhit
  probe_ponder5_desync.py    runner desync when restarting without `stop`
  probe_ponder6_residuals.py stop-move, time field, zero-stop vs EOF artifact
  probe_ponder7_suffix.py    is the ` ponder` reply legal?
  probe_ponder8_hazard.py    RUNAWAY vs WITHHELD, and the two clocks
  probe_ponder9_bound.py     16-offset upper bound on the post-hit budget
  make_tables.py             regenerate FINDINGS.md tables from evidence
  check_claims.py            verify every prose figure against the evidence

evidence/
  pins/                      compiler, configure flags, pin output + its raw input
  probe*_results.json        every measurement
  probe*.log                 run transcripts, including re-runs after harness bugs
```

## Verify it

```
python3 scripts/check_claims.py     # 43 checks; exits 0 only if FINDINGS agrees
python3 scripts/make_tables.py      # reprints the tables (compare to FINDINGS.md)
```

`check_claims.py` exits 1 on any failure **and on its own crash**, and it reports
`UNKNOWN` rather than `PASS` for a claim it cannot evaluate. It checks three
kinds of claim: every figure quoted in the prose against its evidence row, every
count ("18 of 18", "12 of 14") against its array, and every `Tn` / `§n`
cross-reference against the tables and sections that actually exist — a
dangling reference is invisible to any numeric check, since each sentence stays
true while pointing at the wrong table.

It was shown to fail each way: a wrong figure planted in the document, a
corrupted evidence count, and a dangling `T99` reference — all exit 1, and the
document restored byte-identical afterwards.

## Rebuild the binary

`/usr/bin/c++` on this machine is clang with a broken header path, so:

```
cmake -S . -B /tmp/forge-build -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build /tmp/forge-build -j4
scripts/../../scripts/check_pins.sh /tmp/forge-build/forge   # expect PINS MATCH combo29
```

Then point any probe at `--exe /tmp/forge-build/forge`.
