# REPORT job 3 — AREA 9 (SPEED): the next hot spot

seat 19 · area 9 · seed 1901 · branch `for-fable-and-opus/swarm-19`

## 1. The three lines

**What was asked.** AREA 9 job 3: "the next hot spot, the same way" as job 2 — one speed change as a TEXT
PATCH that changes no node count, measured with alternating runs and a 95 % interval of the ratio, each side
built twice.

**The answer.** The next hot spot after job 2's material key is the NNUE fused kernel: `nnue::apply_and_evaluate`
is 11.84 % of self time and its top three source expressions are the packed add (2.77 %), the packed multiply
(1.97 %) and the horizontal sum (1.54 %), with `nnue::update` adding 1.92 % in the same arithmetic. I wrote the
change that cannot alter a value — software prefetch of the next 16-float weight-column block, six requests per
iteration — and it is **8.10 % SLOWER** (ratio 0.9190, 95 % CI [0.8841, 0.9552], 20 alternating pairs). A
half-strength variant (two prefetches instead of six) is **+0.21 %**, i.e. indistinguishable from the control
(-1.11 %). So: node counts identical, and the optimisation is rejected on measurement.

**How sure.** Certain that both patches leave all four honesty numbers identical (checked on the patched
builds). Certain that the full prefetch is slower: the CI upper bound 0.9552 is below 1.0, and both builds of
it were slower by 8 % and 14 % in the build-to-build timings. Confident that the lite variant is neutral, not
helpful: its interval spans 1.0 and so does the control's.

## 2. Honesty numbers

| what | expected | base | prefetch patch |
|---|---|---|---|
| bench 11 | 312866 | 312866 | 312866 |
| bench 13 | 862329 | 862329 | 862329 |
| bench 16 | 3024920 | 3024920 | 3024920 |
| go perft 5 | 4865609 | 4865609 | 4865609 |

Raw: `job3/honesty_patched/`. Exe and sha256 there too.

## 3. Table: step | done-partly-not done | evidence file | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| identify the next hot spot from data | done | `job2/annot/global_by_line.txt` | NNUE fused kernel, 11.84 % self; three top expressions inside it |
| one change that cannot alter a value | done | `job3/prefetch_columns.patch.txt` | `_mm_prefetch` on the next block of each weight column, 4 hunks, `src/nnue.cpp` only |
| patch applies with `patch -p1`, no fuzz | done | `job3/patch_apply.txt` | clean; the applied tree is byte-identical to the measured `pfA` tree |
| node counts identical with the patch | done | `job3/honesty_patched/` | all four equal |
| each side built twice | done | `job3/build_times.txt` | baseC 435 ms, pfA 471, pfB 496 — the patch is slower in BOTH builds |
| 20 alternating pairs, mean + 95 % CI | done | `job3/pairs/ratio_ci.txt` | **ratio 0.9190, CI [0.8841, 0.9552] → SLOWER** |
| half-strength variant, 15 pairs | done | `job3/pairs_lite/ratio_ci.txt` | ratio 1.0021, CI [0.9726, 1.0324] → neutral |
| a control pair to size the noise | done | `job3/pairs_control/ratio_ci.txt` | baseC vs baseA: ratio 0.9889, CI [0.9588, 1.0199] |
| 40 pairs as the prediction said | **not done (20 used)** | — | see §6; 20 pairs already settled it decisively, and the effect went the wrong way |
| P5 (bigger win at bench 16 than bench 11) | **not done** | — | the main change failed at bench 13, so testing the depth trend of a slower patch would be wasted work; stated, not hidden |

## 4. The measurements

### 4a. Build-to-build, `bench 13` x15 per build, median internal ms (`job3/build_times.txt`)

| build | median ms | min | max |
|---|---|---|---|
| baseC (pristine) | 435 | 425 | 506 |
| pfA (full prefetch) | 471 | 461 | 481 |
| pfB (full prefetch, rebuilt) | 496 | 474 | 513 |
| pfLite (2 prefetches) | 450 | 433 | 492 |

Both builds of the full patch are slower than the base, and by more than the build-to-build spread of 4.2 %
measured in job 2. This one is not noise.

### 4b. The formal measurement (`job3/pairs/nps.txt`, 20 alternating pairs, fresh process per run)

```
base:  n 20  nodes ['862329']  mean nps 1878390  sd 109480  min 1582255  max 1986933
patch: n 20  nodes ['862329']  mean nps 1726085  sd 98377   min 1469044  max 1815429
ratio of mean nps (patch/base): 0.9190  95 % CI [0.8841, 0.9552]  df 38  t 2.024
speed change: -8.10 %   95 % CI [-11.59 %, -4.48 %]
node counts identical on both sides: YES
```

### 4c. The half-strength variant (`job3/pairs_lite/nps.txt`, 15 pairs)

```
base:  n 15  nodes ['862329']  mean nps 1862408  sd 89936
patch: n 15  nodes ['862329']  mean nps 1866264  sd 81215
ratio of mean nps (patch/base): 1.0021  95 % CI [0.9726, 1.0324]  df 28  t 2.048
speed change: +0.21 %   95 % CI [-2.74 %, +3.24 %]
node counts identical on both sides: YES
```

### 4d. The control (`job3/pairs_control/nps.txt`, 10 pairs, two pristine builds)

```
ratio of mean nps (patch/base): 0.9889  95 % CI [0.9588, 1.0199]  df 18  t 2.101
speed change: -1.11 %   95 % CI [-4.12 %, +1.99 %]
```

## 5. Findings

**19-F10 — software prefetching the NNUE weight columns makes the engine 8 % SLOWER.**
Adding `_mm_prefetch` for the next 16-float block of each of the (up to six) weight columns in
`nnue::fuse_columns` / `nnue::update` costs 8.10 % of nps (95 % CI [-11.59 %, -4.48 %], 20 pairs), with all
node counts identical. Both independent builds of it were slower. Reducing the request count from six to two
removes the loss (ratio 1.0021, CI [-2.74 %, +3.24 %]). The likely cause is that the columns are streamed
exactly once per evaluation and are already covered by the hardware prefetcher plus the 4-way out-of-order
window, so the extra requests only consume load-buffer slots and L1 fill bandwidth. Show it again:
`bash forge-combo29/swarm/19/job2/headroom.sh x /path/to/job3/prefetch_columns.py` twice, against a base build
with `.../headroom.sh y ""`.

**19-F11 — the NNUE kernel is memory-latency limited in a way an extra prefetch does not fix, so the next
lever must reduce work, not hide latency.** The lite variant showed that *some* prefetching is free (no loss)
while full-strength prefetching is expensive — the cost scales with the number of requests, not with the
memory traffic. That is the signature of a request-throughput limit rather than a latency limit. Not proven:
I did not read the PMU counters (`perf stat`) for L1 misses or load-buffer stalls, and I say so.

### Suspicions, not proven

- That `centipawns_from_lanes`'s 16-way ordered sum (1.54 % global self time) is the next thing worth
  attacking, and that it can be shortened without changing a single bit — it cannot, by inspection: the
  comment at `src/nnue.cpp:390` says the association is deliberately fixed so every target produces
  bit-identical results. Any re-association changes bits, so it is out of bounds for a "no node count change"
  job and needs an SPRT instead.
- That the honest speed lever left in the NNUE kernel is *fewer evaluations* (a cache of the last evaluated
  accumulator per thread), not a faster evaluation. Not proven and not attempted: it changes the search.

## 6. What I did NOT do

- I ran 20 pairs, not the 40 my prediction named. 20 pairs already gave a CI excluding 1.0 by a wide margin
  in the *wrong* direction; doubling the sample would only narrow an interval that has already decided the
  question. This is a deviation from my own prediction and I am recording it rather than quietly doing it.
- I did not test P5 (the bench 16 vs bench 11 depth trend). Testing the depth-dependence of a change that is
  8 % slower at depth 13 has no value.
- I did not run `perf stat` to count L1 misses / load-buffer stalls, so the *explanation* in 19-F11 is a
  hypothesis, not a measurement.
- I did not try to reduce the number of NNUE evaluations; that changes search behaviour and is not a
  "same nodes" job.

## 7. What I am NOT sure about

- Whether the owner's PC (different CPU, different cache sizes, possibly different prefetcher) would show the
  same 8 % loss. The direction is likely the same — the mechanism is request throughput — but I have no access
  to that machine.
- Whether the AVX2 `fuse_columns` path (which I also patched, though this machine takes the AVX-512 path) has
  the same cost. Not measured: this CPU has AVX-512, so the AVX2 code is compiled but never executed here.

## 8. Times

see `job3/stamps.txt`. Prediction committed alone before the first measuring command of job 3.

## 9. The last command's output

```
$ git status --short -- forge-combo29/swarm/19/job3
(clean)
$ ls forge-combo29/swarm/19/job3
build_times.txt
honesty_check.sh
honesty_patched
pairs
pairs_control
pairs_lite
patch_apply.txt
prefetch_columns.patch.txt
prefetch_columns.py
prefetch_lite.py
prediction.txt
stamps.txt
```
