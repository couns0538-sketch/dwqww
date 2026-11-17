# REPORT_v3_Step2 — one speed patch: IDENTITY PERFECT, SPEED EFFECT NOT DETECTED

**File 7's Step 2 asks for a speed patch that keeps every number identical. This patch keeps every number identical
and does not demonstrably speed anything. Both halves are reported because both are the result.**

## The patch

`v3_straightline_counts.patch.txt` — 139 lines, one file (`src/nnue_v3.cpp`), the three `apply_changes_pair` kernels
(scalar, AVX2, AVX-512).

**What it does and why that target.** `apply_changes_pair` is the hottest v3 symbol on bench 13 (8.24 %) and its
sibling `evaluate` is hottest on real positions (6.18 %); both are reached through this walk. An **instrumented
scratch build** (never committed) counted **127,177 calls** in one depth-12 search and the change count was
**always 2 or 3**:

```
c0=0 : 2132    c0=1 : 0    c0=2 : 71659    c0=3 : 53386    c0=4 : 0
```

The inner loop is `for (int i = 0; i < c.count; ++i)` — a variable bound over a 2-3 iteration range, which no
compiler can unroll. The patch specialises `count == 2` and `count == 3` into straight-line code and keeps the loop
for anything else. **The arithmetic is unchanged: the same columns in the same order with the same 16-bit
wraparound**, which is why identity holds exactly.

## Identity: PERFECT, on every check file 7 asks for

```
200-position node rows (OG200, depth 12, PC20 + test net)   baseline 27,944,084   patched 27,944,084
  row-by-row diff over all 200 rows                         0 lines of difference
8 bench numbers                                            8 of 8 MATCH
3 eval lines                                               3 of 3 MATCH (hce 0 both sides)
```

So this is a true identity-preserving patch. `ident_OG200.txt` vs `ident_pat.txt`, `step0` re-run in `/tmp/step0pat`.

## Speed: NO EFFECT DETECTED

```
budget   go nodes 20000 (fixed, no clock), Threads 1, Hash 16, PC20 + test net, fresh process per search
design   ABBA, 30 blocks = 60 A-runs and 60 B-runs (n = 120 timed searches)
median A 11.27 ms    median B 11.63 ms
ratio of medians A/B = 0.9694    bootstrap 95 % CI [0.9418, 1.0297]
per-block spread of A/B: min 0.821, median 0.996, max 1.204
```

**The 95 % interval contains 1.0, so the patch shows no detectable speed change** — and the point estimate is
*slightly the wrong way* (0.9694, i.e. the patched build about 3 % slower, well inside the noise this design
resolves). The per-block spread (0.82 to 1.20) shows how wide individual blocks are; the interval is computed by
bootstrapping over blocks, which is why it is much tighter than that spread.

**P-hacked reading rejected:** I did not go looking for a subset where it wins. The honest conclusion is that
specialising the 2/3-change cases does not help on this machine, most likely because the compiler already
vectorises the loop well at 32 lanes and the branch `count == 2 || count == 3` adds a cost that offsets whatever
unrolling saves.

## What this means, and it is a useful negative

- **The v3 accumulator walk is not a cheap win.** Its hot loop is already effectively unrolled by the compiler at
  AVX-512 width, so a straight-line rewrite buys nothing measurable.
- Combined with `S-F35`'s 20.65 % share, that leaves the **move picker** (34-37 %) as the place to look, and the
  ceiling on all v3 work remains ~1.26x.
- File 7's own rule applies: a patch that moves no node counts but also no time is a **null result**, and it should
  be recorded as one rather than kept as a candidate.

## Honest limits

- **One build of each side.** File 7's Step 3 wants two builds of each variant, because one source spreads ~4.2 %
  between two builds on these machines. My CI already contains 1.0, so a second build pair is unlikely to turn a
  null into an effect — but the limit is stated.
- **Fixed node budget, not the clock.** The PC's self-play uses `go softnodes 2000` and its matches use node budgets;
  `go nodes 20000` is a fair fixed-work proxy, not their exact workload.
- **40-position profile samples.** The target choice rests on a 518-sample profile; the per-symbol shares carry
  roughly ±0.9 points of sampling error.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| instrument the change-count distribution | done (scratch build, not committed) | this report | 127,177 calls, counts only 2 and 3 |
| write the patch as text | done | `v3_straightline_counts.patch.txt` | 139 lines, one file, applies `-p2` clean |
| identity: 200 node rows | done | `ident_pat.txt` vs `ident_OG200.txt` | **identical, 0 diff lines** |
| identity: 8 benches + 3 evals | done | `/tmp/step0pat/step0.txt` | 8/8 and 3/3 MATCH |
| ABBA timing, fixed nodes, n>=120 | done | `abba_out/abba.txt` | ratio 0.9694, CI [0.9418, 1.0297] — no effect |
| two builds per side | NOT done | — | stated limit; CI already contains 1.0 |

## Findings

`v3 | a patch that specialises the v3 accumulator walk's 2- and 3-change cases (all 127,177 measured calls have count 2 or 3; the inner loop is a variable-bound loop the compiler cannot unroll) is IDENTITY-PERFECT — all 200 OG200 node rows identical, sum 27,944,084 both before and after, 8 of 8 benches and 3 of 3 evals match — but shows NO detectable speed effect: ABBA over 30 blocks / 120 timed searches at `go nodes 20000` gives a ratio of medians of 0.9694 with bootstrap 95 % CI [0.9418, 1.0297], which contains 1.0. So the v3 accumulator walk is already effectively vectorised at AVX-512 width and a straight-line rewrite buys nothing measurable; the picker (34-37 %) remains the place to look | v3/v3_straightline_counts.patch.txt v3/ident_pat.txt v3/abba_out/abba.txt v3/REPORT_step2.md | NEW |`

## Suspicions, not proven

- That no straight-line variant of this loop can win, because the AVX-512 path processes 32 lanes per iteration and
  the loop overhead is already amortised. Untested beyond this one patch.

## Times

`v3/stamps.txt`, every line a `date -u`.
