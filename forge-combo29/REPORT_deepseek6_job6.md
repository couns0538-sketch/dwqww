# REPORT — deepseek6, job 6 (testing kimi5's job-13 dead/alive claims with rows)

for-fable-and-opus/deepseek6-work · folder `forge-combo29/tests_deepseek6_job6/`
clock: `job6_start.txt` = `Mon Nov 16 06:23:08 PM UTC 2026`; claim `18:23:13Z`; all runs done 18:34:59Z.

## 1. Three lines

**Asked:** kimi5's job-13 report claims 3 of the tuner's 35 settings are dead at one step and 32 alive. Test every claim with rows, with two controls first.
**Answer:** Step 0 met (four pins, O 9,500,069 with 41,311/24,872/28,574, G 18,466,239). **All 44 claim-runs hold — 12 dead-checks (3 settings × 2 values × 2 sets) all exactly equal to S14, and 32 live-checks all differing. Zero claim failures.** Both controls behaved as the job says they must on `NullMoveBase` (alive, 0 of 200 equal); **the `LmrHistoryDivisor` 5643→5644 control came out ALIVE (168 of 200 equal, 32 positions differ)** where I had predicted dead — my prediction is killed and the job's own parenthetical was the right reading.
**How sure:** certain of every number (44 rows files, one committed compare command). The one thing I got wrong is my own control prediction, which I report as a kill, not as a nuance.

## 2. Honesty numbers (raw files in this folder)

| line | want | got | file |
|---|---|---|---|
| `bench 11` | 312866 | **312866** | `honesty_bench11.txt` |
| `bench 13` | 862329 | **862329** | `honesty_bench13.txt` |
| `bench 16` | 3024920 | **3024920** | `honesty_bench16.txt` |
| `go perft 5` | 4865609 | **4865609** | `honesty_perft5.txt` |
| S14 on O | 9,500,069 (41,311/24,872/28,574) | **9,500,069** (41,311/24,872/28,574) | `O_S14.rows` |
| S14 on G | 18,466,239 | **18,466,239** | `G_S14.rows` |

Engine `/agent/repos/work/build-base/forge`, sha256 `e06310eca3368556…` — the plain build of 6b98f217.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| parse kimi5's 35-row table mechanically | done | `readkimi13.py`, `kimi13_table.txt` | **35 rows: 3 dead, 32 live** (agrees with kimi5's own count) |
| Step 0: pins + S14 on both sets | done | `honesty_*.txt`, `O_S14.rows`, `G_S14.rows` | **all met** |
| prediction as its own commit before any counted run | done | `PREDICTION.md`, commit `deepseek6 job 6 prediction` | committed before the controls |
| control: `LmrHistoryDivisor` 5643→5644 on O | done | `C_lhd5644.rows` | **sum 9,512,627, 168 of 200 nodes equal — ALIVE** (my prediction said dead: **killed**) |
| control: `NullMoveBase` 5→6 on O | done | `C_nmb6.rows` | sum 9,906,893, **0 of 200 equal — ALIVE** as the job requires |
| determinism check on the surprising control | done | `C_lhd5644_r2.rows`, `O_S14_r2.rows` | 5644 twice: **200 of 200 equal**; S14 twice: **200 of 200 equal** — the difference is real, not noise |
| 3 dead settings × 2 values × 2 sets = 12 runs | done | `runs/*_[QCF]*.rows`, `table.txt` | **12 of 12 equal to S14 on every position** |
| 32 live settings × (value+step) on O = 32 runs | done | `runs/O_*.rows`, `table.txt` | **32 of 32 differ from S14** |
| every claim verdict | done | `table.txt` | **44 holds, 0 fails** |

## 4. kimi5's table as I read it, and my verdict per setting

Parsed by `readkimi13.py` from `REPORT_kimi5_job13.md`; every value and step below is from that parse.

### The 3 "dead" claims — all HOLD on both sets

| setting | value | step | tested at | O | G | verdict |
|---|---|---|---|---|---|---|
| `QsSeeMargin` | 40 | 6 | 34, 46 | **200/200 equal** both | **353/353 equal** both | **claim holds** |
| `CaptureFutilityMultiplier` | 250 | 25 | 225, 275 | **200/200 equal** both | **353/353 equal** both | **claim holds** |
| `CaptureFutilityDepth` | 6 | 1 | 5, 7 | **200/200 equal** both | **353/353 equal** both | **claim holds** |

All twelve runs have sums 9,500,069 (O) and 18,466,239 (G) — literally the S14 sums — with best moves equal
200/200 and 353/353. `grep '^dead' table.txt` shows the twelve lines.

### The 32 "live" claims — all HOLD on O

```
grep -c '^live.*claim holds' table.txt     -> 32
grep -c 'CLAIM FAILS' table.txt            -> 0
```
Every one differs from S14 on at least one position; the extremes are `SingularMargin` (sum 8,186,451 at
value+step, 0 of 200 nodes equal) and `NullMoveEvalDivisor` (sum 9,537,690 at 220, 144 of 200 equal — still
differing). **These reproduce my own job-1 numbers exactly** — e.g. `LmrQuietBase` 101 → 9,314,278 and
`SingularMargin` 3 → 8,186,451, both identical to job 1's `table_O.txt` — which is expected, since kimi5's "live"
column quotes my job-1 counts. I say plainly: **this half of job 6 is a re-measurement of my own work, not an
independent confirmation of kimi5.**

## 5. Findings

### 5.1 The three dead claims survive, and the reason is the one the source gives

- `QsSeeMargin`: `board.cpp:24` `SeeValue{0,100,300,300,500,900,0}` — every SEE result is a multiple of 100, so
  every margin in 0..99 is the same comparison. 34, 40 and 46 are all in that band. Confirmed at 34 and 46 on both
  sets: 200/200 and 353/353 equal.
- `CaptureFutilityMultiplier`, `CaptureFutilityDepth`: their only reads sit behind `CaptureFutilityBase > 0`
  (`search.cpp:1893`) and that base is 0 (default, not in S14). Confirmed at both ends of each step on both sets.

**But the scope of "dead" is narrower than the word suggests**, and this is my one substantive reservation about
kimi5's table: these two are dead **at the engine's current configuration**, not dead in the engine. My job 3b
counted what happens when the gate is opened: with `CaptureFutilityBase 230` the multiplier prunes 11,236 times on
O, and at multiplier 100 it prunes 25,098 times out to `lmr_depth` 9. A reader who takes "dead" as a property of
the setting rather than of the configuration would be misled.

### 5.2 My control prediction was wrong, and it is the most useful result in this report

I predicted `LmrHistoryDivisor` 5643→5644 would be **dead** on 200 positions. It is **alive**:
sum 9,512,627 against 9,500,069, with **32 of 200 node counts different** and 2 best moves different. I then
confirmed it is not noise (both the 5644 run and the S14 run reproduce exactly on a second process).

The job's own parenthetical said "dead for every history below 5643 in absolute value" — i.e. it did NOT claim
one step was dead, it described the term's shape. **I read the parenthetical as a prediction and tested it as one;
it was a description and it was right.** What the measurement adds is the size: a ONE-UNIT move of the divisor
changes a third of the node counts' positions, which is what a `clamp(history/divisor, -2, 2)` should do where
`|history|` sits near 5643.

### 5.3 The claim count

| | kimi5's claim | my result |
|---|---|---|
| dead settings | 3 | **3 hold** |
| live settings | 32 | **32 hold** |
| total | 35 | **35 of 35** |

**I predicted 3 of 3 dead claims would survive. That part held.** I also predicted the divisor control would be
dead; that part was killed.

### Suspicions, not proven

- That a one-unit divisor move changes 32 of 200 node counts because of the clamp boundary rather than because the
  history values are densely spread near 5643. I have the count, not the distribution of `|history|`.

## 6. What I read from my colleagues

- **kimi5** (`REPORT_kimi5_job13.md`): its three dead claims, its 32 live claims, its citations to
  `board.cpp:24`, `search.cpp:1893`, `search.cpp:1894`, `search.cpp:1898`, `search.cpp:1500`. Every one of those
  line references matches what I opened in this session (`search.cpp:1893` is the gate I instrumented in job 3b).
  Its "live" counts are my job-1 numbers, which I say above rather than let stand as independent.
- **glmflash5** (`NOTES_glmflash5.md`): nothing on this job.
- No note is an order; where a note's number and mine differ, mine is in `table.txt` with its file.

## 7. What I did NOT do

- I did not test kimi5's dead settings at values OUTSIDE the intervals it claims (0 and 99 for `QsSeeMargin`;
  0 and the maximum for the two capture-futility settings). kimi5 already did that and matched the job's known
  answers; the job's wording for me is the ±step check.
- I did not run the live settings on G (the job names O for those).
- I did not compare against kimi5's own rows files position by position — it has `rows/*.json` for only the
  endpoints it tested; where it gives a node sum I compared sums in `table.txt` (all equal to mine).
- I did not measure strength.
- I did not commit engine source; no source was changed for this job at all.
- I did not open a pull request.

## 8. What I am NOT sure about

- The mechanism behind 5.2's 32 positions (see Suspicions).
- Whether "dead" in kimi5's table should be read as "dead at this configuration" — I argue it should in 5.1, but
  that is a reading of its table, not something it states.

## 9. A better way

A control whose expected result is a *description* of a term's shape ("dead for every history below 5643") is not
a control — it is a hypothesis about that shape. I should have taken the job's parenthetical as the hypothesis and
predicted what it actually says: **a one-unit divisor move bites exactly where `|history|` crosses 5643**, so it is
alive, and the interesting number is how many positions. Predicting "dead" tested my own intuition instead of the
job's claim. The lesson: read a parenthetical in a job file as data to be tested, and predict what it says, not
what seems likely.

## 10. times / model

times: see `stamps.txt` (`date -u` after every part).

**Model: DeepSeek V4.1 Flash 1017** (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`CLAIM.txt`, `kimi13_table.txt` (the parsed table), `readkimi13.py`, `job6_run.py`, `table.txt` (44 verdicts),
`runs/` (44 rows files with `.meta`), `C_lhd5644*.rows`, `C_nmb6.rows`, `honesty_*.txt`, `precommit_evidence.txt`.
