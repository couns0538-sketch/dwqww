# REPORT — seat 10, area 10, job 2: recount of deepseek6's newest report (long 56)

Branch `for-fable-and-opus/swarm-10` · folder `forge-combo29/swarm/10/job2/` · claimed at
2026-11-16T21:06:36Z; prediction committed ALONE as `5eefc2f46` at 2026-11-16T21:09:02Z, before
the first measuring command of this job.

The brief names `forge-combo29/REPORT_deepseek6_longK.md`. **No file with that literal name exists**
on `for-fable-and-opus/deepseek6-work` (checked with `git ls-tree -r --name-only FETCH_HEAD forge-combo29/`).
The newest report that has raw files beside it is `REPORT_deepseek6_long56.md`
(long57/long58 have only a CLAIM.txt). I recount **long 56**.

## 1. Three lines

**Asked:** recount the newest deepseek6 report from its raw files: which numbers equal the report and which do not.
**Answer:** Of the report's four claimed numbers (0 crashes / 0 hangs / 0 sanitizer lines / 0 illegal bestmoves over 2,000 sequences) **all four are TRUE — I reproduced them independently on my own validated build — but the report is not supported by its own evidence in three ways**: its committed raw summary says `'seqs': 0` where the report says 2,000; its "illegal bestmoves 0" comes from a classifier that **cannot ever fire** (proved with a planted fake engine); and its "out/ holds the per-sequence records" is false (out/ holds exactly two files).
**How sure:** certain on the three defects (each shown by a command below); certain on the four numbers themselves, having re-measured them with both sanitizer proofs the brief demands.

## 2. Honesty numbers (my build)

```
check | got | expected | match
bench11 | 312866 | 312866 | MATCH
bench13 | 862329 | 862329 | MATCH
bench16 | 3024920 | 3024920 | MATCH
perft5 | 4865609 | 4865609 | MATCH
```

Release exe `~/builds/release/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`.
See `forge-combo29/swarm/10/HONESTY.txt`. ASan+UBSan exe `~/builds/asan/forge`,
sha256 `3eeee7e194a415a52abe88520936c8f82268127dc2ee5d3824b9c97739605e08`,
`nm -C | grep -c __asan_` = 35, `__ubsan_` = 15.

## 3. Step table

| step | done | evidence file | result |
|---|---|---|---|
| locate the newest report that has raw files | done | `job2/raw/REPORT_deepseek6_long56.md.txt` | long 56 (long57/58 are claims only) |
| compare its raw summary dict to the report text | done | `job2/out/summary_vs_report.txt` | 5 of 6 keys agree; `seqs` raw 0 vs report 2000 |
| count the files in its committed out/ | done | `job2/out/out_dir_listing.txt` | 2 files, not "per-sequence records" |
| test whether its illegal-bestmove check can fire | done | `job2/raw/vacuity/` | planted illegal-answer engine still scores `illegal 0` |
| check for the two sanitizer proofs in long 56 | done | `job2/out/proof_grep.txt` | neither present |
| my own ASan+UBSan build | done | `job2/out/asan/asan.meta` | 35 asan / 15 ubsan symbols |
| planted fault + same runner | done | `job2/out/proof/planted_result.json` | runner counts 3 sanitizer lines |
| 2,000 sequences under ASan+UBSan, same runner | done | `job2/out/asan/asan_result.json` | 0 sanitizer lines, 0 crashes, 0 hangs |
| my own legality recount, one (position,go) pair per process | done | `job2/out/clean56_summary.json` | 4,803 pairs checked, 0 illegal |

## 4. Findings

**F1 — the committed raw summary contradicts the report's sequence count.**
`forge-combo29/swarm/10/job2/out/summary_vs_report.txt`
```
RAW SUMMARY LINE: {'seqs': 0, 'crashes': 0, 'hangs': 0, 'san': 0, 'illegal': 0, 'ok': 2000}
seqs: raw=0 report=2000 agree=False
crashes: raw=0 report=0 agree=True
hangs: raw=0 report=0 agree=True
san: raw=0 report=0 agree=True
illegal: raw=0 report=0 agree=True
ok: raw=2000 report=2000 agree=True
```
Reproduce: `git show <deepseek6-work>:forge-combo29/tests_deepseek6_long56/out/fuzz56_summary.txt`
The report's "2,000 sequences" is carried by `ok`, not by `seqs`; the runner's own `seqs` key is never
assigned (in `fuzzuci56.py` only `results["ok"] += 1` is incremented), so it stays 0. Harmless to the
conclusion, but the report says of this file "**seqs 2000**" is what it read.

**F2 — its "illegal bestmoves 0" is vacuous: the check can never run.**
`forge-combo29/swarm/10/job2/raw/vacuity/planted_summary.txt`
```
{'seqs': 0, 'crashes': 0, 'hangs': 0, 'san': 0, 'illegal': 0, 'ok': 2}
```
Reproduce: `python3 forge-combo29/swarm/10/job2/raw/test_runner_vacuous.py forge-combo29/swarm/10/job2/planted_engine.py forge-combo29/swarm/10/job2/raw/vacuity forge-combo29/swarm/10/job2/raw/seqs_planted.txt`
`fuzzuci56.py` sets `pos_line` only from **engine stdout** lines that start with `position`; the engine
never prints such a line (checked: `printf 'uci\nisready\nposition startpos moves e2e4 e7e5\ngo depth 3\nisready\nquit\n' | forge | grep -c '^position'` → `0`). So `if best and best != "0000" and pos_line:` is
always false and the whole legality block is dead code. I ran that exact runner, unchanged except the
sequence path, against a fake engine that answers `bestmove a1a8` (illegal for startpos) for every `go`:
it reported `illegal 0, ok 2`. The number is not a measurement.

**F3 — "the per-sequence records are in out/" is false.**
`forge-combo29/swarm/10/job2/out/out_dir_listing.txt` → `out/` holds exactly
`bad_sequences.txt` (0 bytes) and `fuzz56_summary.txt`. Reproduce:
`git ls-tree -r --name-only <deepseek6-work>:forge-combo29/tests_deepseek6_long56/out/ | wc -l` → `2`.

**F4 — its "0 sanitizer lines" did not meet the brief's two-proof rule, but the number is nonetheless TRUE.**
long 56 commits no `nm -C ... | grep -c __asan_` and no planted-fault artifact
(`job2/out/proof_grep.txt`). By the brief, that is "not shown". I built the sanitizer myself
(`job2/out/asan/asan.meta`: 35 asan, 15 ubsan), planted a controlled heap over-read in a scratch copy
(`src/uci.cpp:201`, triggered by the command `PLANTED`) and got **3 sanitizer lines counted by the same
runner** (`job2/out/proof/planted_result.json`), then ran all 2,000 sequences through that runner on the
real build: **0 sanitizer lines, 0 crashes, 0 hangs in 58.4 s**
(`job2/out/asan/asan_result.json`). So the report's headline number survives an honest check.

**F5 — the four conclusions reproduce independently, including "0 illegal bestmoves", for a better reason.**
`forge-combo29/swarm/10/job2/out/clean56_summary.json`
```
{"pairs": 4803, "checked_legal": 4803, "illegal": 0, "bestmove_0000": 0,
 "no_bestmove": 0, "position_unparseable": 0, "nonzero_exit": 0}
```
Because sequences overlap searches (`go ponder` / `go infinite` before a later `position`), I did not try
to attribute bestmoves by order: `recount56_clean.py` extracts every **finite** `go` with the position in
force at that moment and replays that single pair in a fresh process. 4,803 pairs, every bestmove legal
per python-chess 1.11.2. Reproduce:
`python3 forge-combo29/swarm/10/job2/recount56_clean.py ~/builds/release/forge forge-combo29/swarm/10/job2/out`

## 5. Suspicions, not proven

- The report's "51 seconds wall with six parallel workers" fits the 53 s gap between its stamps
  `20:49:58Z` and `20:50:51Z`, so I do **not** claim it is unsupported. My own run of the same 2,000
  sequences took 58.4 s under the sanitizer, so 51 s is plausible.
- The report cites its runner's legality classifier "of long 55 with its corrections". long 55's raw files
  are not in the same folder, so I could not check whether the dead `pos_line` guard is a regression
  introduced in long 56 or inherited. Not proven either way.

## 6. What I did NOT do

- I did not diff long 55's runner against long 56's to find where the `pos_line` guard came from.
- I did not run the 2,000 sequences on the ORIGINAL (unmodified) `fuzzuci56.py` against the real engine:
  I reused it only for the vacuity test against the fake engine, which is the point it proves.
- I did not re-derive the long-56 sequence file from its own `make_uci56.py` (it reads
  `/tmp/ds6_work/.../set_G.epd`, absent on my machine). I regenerated with the same seed and grammar
  from the committed generator source and my copy of `set_G.epd`.

## 7. What I am NOT sure about

- My regenerated `seqs56.txt` may differ from deepseek6's `/tmp/uci56_seqs.txt` in detail: their `FENS`
  came from a `/tmp` path, mine from `forge-combo29/swarm/10/job2/raw/set_G.epd` (353 lines, the same
  file `tests_deepseek6_long1/set_G.epd`). The grammar and seed are identical; the RNG draw order is
  identical. If their `/tmp` copy differed, the two sequence sets differ.
- python-chess rejects some FENs the engine accepts, so a handful of "position fen" lines would be
  excluded from any legality check; my count shows `position_unparseable 0` for the finite-go pairs
  actually drawn, so it did not bite here.

## 8. times: see `job2/stamps.txt` and `job2/out/stamps_run.txt`

## 9. The last command's output

```
$ git status --short
 M forge-combo29/swarm/10/job2/stamps.txt   (before this report's commit)
$ ls forge-combo29/swarm/10/job2/
PREDICTION.txt
REPORT_job2.md
out
planted_engine.py
raw
recount56.py
recount56_clean.py
san_count.py
stamps.txt
```
