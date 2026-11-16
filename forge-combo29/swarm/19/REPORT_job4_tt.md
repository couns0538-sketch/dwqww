# REPORT job 4 — the TT probe, measured: `bench 13` hides a cost that a real workload exposes

seat 19 · area 9 · branch `for-fable-and-opus/swarm-19`

## 1. The three lines

**What was asked.** Continue job 4 on the transposition table (the second-largest PC-relevant symbol,
`probe_body<false>` 5.77 % self). My first prediction — that the miss path redundantly rescans the cluster —
died on inspection, because the first-empty short-circuit is already at `src/search.cpp:424`. So I did what
the report of that failure said I should have done first: **counted, before proposing anything.**

**The answer.** The probe splits very differently on the two workloads, and the difference is the finding:

- **`bench 13`: the table never fills.** Only **50 of 861,904** probes (0.006 %) find a full cluster; 66.9 %
  of probes miss and land on an empty slot, which the existing short-circuit handles immediately.
- **R_1911, depth 12 x200: 44.1 % of all probes find a FULL cluster** (6,515,608 of 14,786,994) and therefore
  run the age/depth replacement scan. That is a cost `bench 13` cannot show.
- Hits are skewed on bench 13 (**93.1 % land in slot 0**) and flat on R_1911 (26/26/25/23 %).
- The generation-refresh write on a hit is essentially free on bench 13 (**0 of 285,437**) but real on
  R_1911 (24,383 = 0.5 % of hits).

**How sure.** Certain of the counts (instrumented build, two independent runs, cross-check `empty_none = 0`
on both, so no probe path was missed). The inference "bench 13 understates the TT's real cost" follows
directly from 44.1 % vs 0.006 % and does not depend on any timing.

## 2. The counters

| quantity | bench 13 (Hash 16) | R_1911, Hash 16 | R_1911, Hash 32 |
|---|---|---|---|
| probes | 861,904 | 15,184,039 | 14,786,994 |
| hits | 285,437 = **33.1 %** | 5,334,400 = **35.1 %** | 5,197,101 = 35.1 % |
| misses | 66.9 % | 64.9 % | 64.9 % |
| misses on a FULL table (age/depth scan ran) | **50 = 0.006 %** | **8,310,172 = 54.7 %** | 6,515,608 = 44.1 % |
| misses that found an empty slot | 576,417 = 66.9 % | 1,539,467 = **10.1 %** | 3,074,285 = 20.8 % |
| hits whose generation was stale (a write happened) | **0** | 23,278 = 0.4 % of hits | 24,383 = 0.5 % |
| hit slot distribution (0/1/2/3, %) | **93.1 / 6.4 / 0.5 / 0.0** | 26.0 / 25.4 / 24.9 / 23.7 | 26.1 / 25.7 / 25.0 / 23.2 |
| cross-check `empty_none` (should be 0) | 0 | 0 | 0 |

The Hash 16 column is the like-for-like one: `bench` builds `Searcher(16)`, so 16 MB is the fair comparison.
At the same table size the R_1911 full-table rate is **54.7 %**, and only 10.1 % of probes find an empty
slot — against bench's 66.9 %. The gap is therefore not a table-size artifact; it is the workload.

Both runs from `job4/instrument_tt.py` in a scratch build; raw lines in `job4/tt_bench13.err`,
`job4/tt_R1911_hash16.err`, `job4/tt_R1911_hash32.err`.

## 3. Findings

**19-F18 — `bench 13` almost never fills the transposition table, so it cannot measure the TT's real cost;
a random-game workload fills it on 54.7 % of probes at the SAME table size.**
At Hash 16 (which is what `bench` builds, `Searcher(16)`), bench 13 reaches the age/depth replacement scan on
50 of 861,904 probes (0.006 %), while R_1911 at the same Hash 16 reaches it on 8,310,172 of 15,184,039
(**54.7 %**), and only 10.1 % of its probes find an empty slot against bench's 66.9 %. Any speed work on
`probe_body`'s miss path validated on `bench` alone is measuring the wrong workload. This also explains why
`TT probe_body`'s self share jumped from 2.09 % (bench 13, job 1) to 5.77 % (R_1911, job 1b) — not noise: it
is 54.7 % of probes doing work that 0.006 % of bench's probes do.
Show it again: build with `job4/instrument_tt.py`, then
`printf 'bench 13\nquit\n' | ~/tt_build/forge` and
`python3 job4/drive_hash16.py ~/tt_build/forge job1b/R_1911.fens out.err 16`.

**19-F19 — `bench 13`'s probes almost always hit slot 0 (93.1 %) and never refresh a generation (0); R_1911
is flat across slots (26/26/25/23 %) with 0.5 % of hits doing a generation write.** A bench-only profile
therefore cannot see the cost of a spread cluster or of the generation-refresh store, both of which a real
game produces.

### Suspicions, not proven

- That the 54.7 % full-table rate is what makes the R_1911 probe share 5.77 % rather than 2.09 %. It is the
  obvious reading of the counters, but I did not run a timing experiment that holds everything else fixed.

## 3b. A second `setoption` bug of my own, caught by the control

My first Hash-controlled run produced **byte-identical counters** to the uncontrolled one, which was the
signal that the option never applied. The cause was the same mistake I made in `job1b/profile_R.sh`: I sent
`setoption name Hash 16` without the `value` keyword required by the UCI parser at `src/uci.cpp:263-268`.
I then confirmed the option works at all with a direct probe — Hash 1/4/16/64 give `hashfull` 979/446/106/23
at depth 14 — and rewrote the driver to send `setoption name Hash value N`. The three counter columns above
are all from after that fix.

That is twice in this session that a harness of mine silently failed to apply S14-style options because of a
malformed `setoption`. The general lesson for the swarm: **if two runs with supposedly different settings give
identical numbers, suspect the settings were never applied** — and the brief's `isready`-and-read-every-line
rule is what catches it, when it is actually read for a refusal line rather than discarded.

## 4. What the counters say about the obvious next step

The replacement scan is the only sizable redundant-looking work left, and it fires 6.5 M times on R_1911. But
19-F15 (tie order is load-bearing) is a warning that touching selection order is dangerous, and the
replacement choice is exactly such an order. Before anyone optimises it: **any patch must keep the four
honesty numbers identical**, and the honest way to validate it is on a workload that actually fills the
table, not on `bench`. I did not write that patch in the time available and I am not going to propose one
from counters alone a second time in one job.

## 5. What I did NOT do

- No patch.
- No timing experiment isolating the replacement scan.
- I did not test Threads > 1, where the probe takes the lock path instead (`TakeLock=true`), which is a
  different function body entirely.
- I did not re-run `bench 13` with a table small enough to fill, which would be the cleanest way to show
  that a bench-shaped workload *can* reach the replacement path.

## 6. What I am NOT sure about

- Whether `stale_gen = 0` on bench 13 is structural (bench's eight positions are searched once each, so
  nothing is ever revisited across a generation bump) or incidental. Likely structural, untested.
- Whether the 54.7 % would be even higher with a deeper search or a longer game sequence. The trend from
  Hash 32 (44.1 %) to Hash 16 (54.7 %) suggests the rate is table-pressure-driven, which predicts yes.

## 7. Files

`job4/prediction.txt` (committed alone, unedited — and wrong, see `REPORT_job4.md`),
`job4/instrument_tt.py`, `job4/tt_bench13.err`, `job4/tt_R1911.err`.
