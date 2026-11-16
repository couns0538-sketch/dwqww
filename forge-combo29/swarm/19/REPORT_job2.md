# REPORT job 2 — AREA 9 (SPEED): one speed change as a text patch

seat 19 · area 9 · seed 1901 · branch `for-fable-and-opus/swarm-19`

## 1. The three lines

**What was asked.** AREA 9 job 2: ONE speed change as a TEXT PATCH that changes NO node count (bench 11, 13,
16 and perft 5 identical) and is faster, measured with 10 alternating runs of `bench 13`, nodes per second,
mean and a 95 % interval of the ratio, with each side built TWICE.

**The answer.** I wrote the patch (`job2/optimize_material_key.patch.txt`): `Board` keeps the material-key
hash in a member instead of `corrected_eval` re-deriving it from ten `popcount`s on every call — 750,427
calls per `bench 13`. It applies with `patch -p1` without fuzz, and **every node count is identical**
(bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, checked on the patched build).
But it is **NOT shown to be faster**: mean nps ratio patch/base = **1.0059**, 95 % CI **[0.9680, 1.0454]**,
which contains 1.0. My own control (base build A vs base build B, same protocol) gave a CI of
[0.9488, 1.0543] — the machine's noise floor is about ±5 %, and the effect I am chasing is ~1 %. So this
patch is a correctness-neutral change with no measurable speed win, and I will not claim one.

**How sure.** Total certainty on "node counts unchanged" (four numbers, fresh process each, pasted below)
and on "the patch applies cleanly and the cache is correct" (4,736 positions, zero mismatches against an
independent reference). Very sure that *this measurement cannot resolve a 1 % effect* — the control run
proves it. Not sure whether the patch helps at all on the owner's PC, where the machine is quieter.

## 2. Honesty numbers

Both sides, fresh process per line, raw output in `job2/honesty_patched/` and `honesty/`.

| what | expected | base build | patched build |
|---|---|---|---|
| bench 11 | 312866 | 312866 | 312866 |
| bench 13 | 862329 | 862329 | 862329 |
| bench 16 | 3024920 | 3024920 | 3024920 |
| go perft 5 | 4865609 | 4865609 | 4865609 |

Patched build `id name` = `Chess Engine Forge 6.4.24 candidate`; exe and sha256 in
`job2/honesty_patched/honesty.meta`.

## 3. Table: step | done-partly-not done | evidence file | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| find a target from the profile, not from taste | done | `job2/annot/global_by_line.txt` | `material_key()` is 2.71 % of total self time (three top entries), 750,427 calls per bench |
| count the calls | done | `job2/counts.txt` | `corrected_eval` 691,753, `material_key` 750,427 |
| write the change as a TEXT PATCH | done | `job2/optimize_material_key.patch.txt` | unified diff against 6b98f217, 3 files, 12 hunks |
| patch applies with `patch -p1`, no fuzz | done | `job2/patch_apply.txt` | dry run then real apply: no fuzz, no rejects |
| node counts identical with the patch | done | `job2/honesty_patched/` | all four equal |
| prove the cache is correct, not merely self-consistent | done | `job2/selftest/key_selftest.txt` | 4,736 positions: cached == computed == independent Python reference, 0 mismatches |
| each side built TWICE | done | `job2/four_builds_times.txt` | baseA 443 ms median, baseB 425, patchA 424, patchB 424 — **build-to-build spread 4.2 %** |
| 10 alternating base/patch runs, mean + 95 % CI of ratio | done | `job2/pairs/nps.txt`, `job2/pairs/ratio_ci.txt` | ratio 1.0059, CI [0.9680, 1.0454] |
| a control run to size the noise | done | `job2/pairs_control/` | baseA vs baseB ratio 1.0002, CI [0.9488, 1.0543] — noise ±5 % |
| the patch is faster | **NOT SHOWN** | — | the CI contains 1.0; with a ±5 % noise floor a 1 % effect is unresolvable here |
| more pairs to shrink the CI | **not done** | — | see §6; I chose to spend the time on job 3 rather than grind one null |
| `-fno-omit-frame-pointer`-free measurement | partly | `job2/pairs/` | the paired runs use plain release builds (no -g), but `prof`-annotated runs elsewhere do use `-g` |

## 4. The numbers, each pasted from the script that produced it

### 4a. Four builds, `bench 13` x15 per build, median internal ms (`job2/four_builds_times.txt`)

| build | median ms | min | max |
|---|---|---|---|
| baseA (pristine) | 443 | 424 | 453 |
| baseB (pristine, rebuilt) | 425 | 423 | 456 |
| patchA (patched) | 424 | 420 | 448 |
| patchB (patched, rebuilt) | 424 | 417 | 479 |

Two builds of *identical* source differ by 443 vs 425 ms = **4.2 %**. This is exactly the effect the brief's
"build each side TWICE" warning is about, and it is bigger here than the effect I was measuring.

### 4b. Paired alternating runs — the formal measurement

Command: `bash job2/pair_bench.sh ~/h/baseA/build/forge ~/h/patchA/build/forge job2/pairs 10`
(one fresh engine process per run, alternating base/patch, ten pairs.)

```
base:  n 10  nodes ['862329']  mean nps 1901487  sd 81031  min 1700846  max 1968787
patch: n 10  nodes ['862329']  mean nps 1912336  sd 70579  min 1767067  max 1982365
ratio of mean nps (patch/base): 1.0059  95 % CI [0.9680, 1.0454]  df 18  t 2.101
speed change: +0.59 %   95 % CI [-3.20 %, +4.54 %]
node counts identical on both sides: YES
```

### 4c. The control — base build A vs base build B, same protocol

Command: `bash job2/pair_bench.sh ~/h/baseA/build/forge ~/h/baseB/build/forge job2/pairs_control 10`

```
base:  n 10  nodes ['862329']  mean nps 1883962  sd 127205  min 1550951  max 1955394
patch: n 10  nodes ['862329']  mean nps 1880856  sd 59776  min 1785360  max 1955394
ratio of mean nps (patch/base): 1.0002  95 % CI [0.9488, 1.0543]  df 18  t 2.101
speed change: +0.02 %   95 % CI [-5.12 %, +5.43 %]
node counts identical on both sides: YES
```

The control's interval is *wider* than the treatment's, and its point estimate is +0.02 % on two builds that
are the same code. That is the honest scale of this machine: any "gain" below ~5 % measured here is
indistinguishable from rebuild noise.

## 5. Findings

**19-F6 — the material key is re-derived 750,427 times per `bench 13` and is 2.71 % of self time.**
`Worker::corrected_eval` (`src/search.cpp:1219`) and `Worker::update_correction` (`:1237`) both call a free
function that walks ten `popcount`s through a ten-deep multiply chain. The value depends only on the ten
piece counts, so it changes only on a capture or a promotion. Show it again:
`printf 'bench 13\nquit\n' | ~/build_scratch/forge 2>&1 | tail -1` on the instrumented scratch build described
in `job2/counts.txt`, and see `job2/annot/global_by_line.txt` for the 2.71 %.

**19-F7 — on this machine the build-to-build spread of one source is 4.2 %, larger than the brief's 1.5 %.**
baseA median 443 ms vs baseB median 425 ms, same source, same flags, same CMake cache settings, built minutes
apart on the same 4-core VM. Any seat measuring a speed change below ~5 % here is measuring the machine.
Show it again: `bash job2/headroom.sh x ""` twice and compare the medians.

**19-F8 — `perf annotate --stdio` reports *local* percentages, not global ones.**
The leading column of `perf annotate` is the instruction's share of the *symbol's own* samples ("percent:
local period", printed in its header). Multiplying by the symbol's global self share is required before
comparing two symbols; without that, `fill_pseudo_legal` looks like it owns 100 % of the engine. Show it again:
the header line `Percent | ... (N samples, percent: local period)` in any `perf annotate --stdio` output, and
`job2/global_by_line.py`, which does the multiplication and reports how many symbols it could and could not
match.

**19-F9 (negative result, still a result) — caching the material key is correct but not measurably faster.**
See §4b. The patch is kept as an artifact because it is correctness-neutral and might help on a quieter
machine, but on this VM the interval spans 1.0 and its own control run spans ±5 %.

### Suspicions, not proven

- That the missing win is because the compiler already hoists most of the ten `popcount`s well, and the
  remaining serial multiply chain is hidden behind the NNUE work in the same iteration.
  Not proven: I did not look at the patched build's assembly for `corrected_eval`.
- That a real win exists but needs a quieter machine to see. Likely, not proven — no access to the PC.
- That `bench`'s 431 ms is dominated by memory behaviour (the NNUE accumulator streams and the TT) rather
  than by instruction count, so ALU-level fixes like this one cannot show up. Not proven.

## 6. What I did NOT do

- I did not run 100 pairs to shrink the CI to ±1.5 %. With the measured per-run sd (~4 %), ten pairs give
  ±4.4 %; 100 pairs would give about ±1.4 %, i.e. roughly 20 more minutes of machine time per side. I judged
  that a better use of the remaining time was to do job 3 and to keep checking other seats. **This is the
  single biggest weakness of this job and I am stating it rather than hiding it.**
- I did not test the patch's effect on an actual game-playing workload (only `bench 13`).
- I did not try any second speed change; job 2 is one change by definition.
- I did not measure the patch under Threads > 1.

## 7. What I am NOT sure about

- Whether `material_key_` staying 0 until `set_fen` runs could matter for a `Board` built by the default
  constructor. `Board()` calls `set_fen` on the start position (`src/board.cpp`), and every search board is
  copied from one that went through `set_fen`, so I believe it is always set — but I did not add an assertion,
  and a `Board` default-constructed and searched *without* `set_fen` would read 0. I checked the constructor
  path by reading the code, not by a test.
- Whether the two places that read the key are the only readers. `job2/material_key_readers.txt` is the
  `grep -n "material_key" src/ include/` output on the patched tree: the new member, its accessor,
  `compute_material_key`, its definition, four maintenance sites in `board.cpp`, and exactly the two call
  sites in `search.cpp`. That is a grep, not a proof.

## 8. Times

see `job2/stamps.txt`. Prediction committed alone at `e30da72d1`, before the first formal measurement.

## 9. The last command's output

```
$ git status --short -- forge-combo29/swarm/19/job2
(clean)
$ ls forge-combo29/swarm/19/job2
annot
annotate.sh
by_source.py
counts.txt
edit_key_selftest.py
edit_material_cache.py
edit_material_key.py
edit_parallel_key.py
exploratory_before_prediction.md
four_builds_times.txt
global_by_line.py
headroom.sh
honesty_check.sh
honesty_patched
hot_lines.py
key_selftest.py
optimize_material_key.patch.txt
pair_bench.sh
pairs
pairs_control
prediction.txt
ratio_ci.py
selftest
stamps.txt
