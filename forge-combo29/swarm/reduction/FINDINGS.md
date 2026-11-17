# Reduction-count instrument, and what it says about the two lone-king counter-cases

Seat: owner-audit, branch `swarm/reduction`, base commit `6b98f217`.
Scope: build the instrument the findings call for, prove it is honest, then use it.

---

## The answer, first

**The instrument was built and it does not separate the two counter-cases.** On every
reduction statistic it reports — count, magnitude distribution, mean, re-search count,
rejection profile, and the same restricted to `BARE_KING_LMR_CAP` nodes — the two
counter-case boards fall **inside** the range spanned by the nine predicted boards. So
the counters do not move where the answer moves, and the two counter-cases are **not**
caused by the cap clamping a different share of reductions, at any depth I measured.

**Two things are positively established rather than left open.**

First, seat 08's handoff proposed that the clamp changes the tree, the tree changes the
score, the changed score changes the next iteration's aspiration window, and that window
change flips the node-count direction. That account has an observable signature — the
score at an intermediate depth must differ between the two builds **before** the node
counts diverge. On the 11 boards it never does: **0 of 11 went score-first**. The
aspiration-window channel is not the mechanism.

Second, and sharper: **the clamp's immediate effect is the same on the counter-cases as
on the predicted boards.** At the depth where the two builds first differ, cap-ON visits
*more* nodes on 2 of 2 counter-cases and 8 of 9 predicted boards — the direction "the
clamp removes reduction, so the capped tree is momentarily larger" holds everywhere. What
differs is only what happens afterwards: on both counter-cases the sign reverses by the
final depth, and on 8 of 9 predicted boards it does not. So the second mechanism is
**not in how the clamp acts at a node and not at the point of divergence** — it is
downstream, in how the two trees propagate after they first part.

The reversal rate (2 of 2 against 1 of 9, Fisher p = 0.0545) is a **lead, not a finding**:
it does not clear 0.05, it was chosen after seeing the full set, and one predicted board
reverses too. It is recorded with those three caveats attached so it cannot be quoted as
confirmatory.

**What that leaves** is narrower and more useful than "uncharacterised": the difference is
created inside an iteration's tree, before any score is published, and downstream of the
first divergence. §5 says what the next instrument should count, and why the cheapest of
the three probes is decisive.

**What is established** (measured, reproducible, with the exact command):
1. The instrument works, is off by default, and is honest under its own gate (§2).
2. On ordinary positions the engine applies **390 reductions per 1000 nodes**, mean
   magnitude **2.38**, and re-searches **2.66%** of them (§3). Nobody had published
   these.
3. The reduction profile is **the same on both trees** away from lone-king roots
   (390.09/1000 and r=2.377 on both), which is what the gate's definition predicts and
   is a control on the instrument (§3).
4. The counters do not separate the two counter-cases (§4).
5. The aspiration-cascade account is refuted, 0 of 11 (§4.2).

**What is inferred, not established:** the mechanism lives in the within-iteration
visit set rather than in any aggregate the current counters expose (§5). That is a
location, not a cause, and it is stated as a lead.

---

## 1. What was built

`patches/lmr_stats_nocap.patch.txt` and `patches/lmr_stats_cap.patch.txt` add a
compile-time switch **`FORGE_LMR_STATS` (default 0)** to `src/search.cpp` and
`include/forge/search.hpp`. With the flag off every original statement is reproduced
verbatim by the preprocessor, so the build is unchanged; with it on, each completed
depth iteration prints one line per root move plus a whole-search summary:

```
info string lmr depth 10 root all applied 2055 rmean 2.34 mag r-2=1 r-1=36 r0=201 r1=451
  r2=471 r3=416 r4=270 r5=144 r6=56 r7=9 research 36 rej 2148
  [mate 0 fifty 0 depth 1267 movecount 1615 baremode 0 pvcap 77]
  cap_gate 0 cap_clamp 0
```

- `applied` — reduced searches actually entered
- `rmean`, `mag r-2 … r10` — mean and histogram of the **final** `r`, signed: the LMR
  terms subtract for tt_pv, check and history, so `r` can be negative (an extension-like
  reduction). My first version clamped `r` into bins `0..15` and silently corrupted the
  distribution; the instrument's own arithmetic check caught it (§2). This is why the
  histogram is signed.
- `research` — full-depth re-searches after a reduced search failed high
- `rej`, `[mate/fifty/depth/movecount/baremode/pvcap]` — nodes where LMR was skipped,
  with a count of **each** failing guard. The guards overlap, so `rej` is not their sum;
  the script says so beside the number.
- `cap_gate`, `cap_clamp`, `cap_rmean`, `cap_mag` — the same statistics restricted to
  nodes where `BARE_KING_LMR_CAP` was true, and how many of those it actually lowered.

Two trees carry the instrument, because the cap exists only in the PC tree:

| tree | contents | why |
|---|---|---|
| `nocap` | base `6b98f217` | the honesty pins and the ordinary-position statistics |
| `cap` | base + seat 03's ported r15 bare-king patch (`patches/base_bare_king_on.patch`, sha256 `bab0fc2964cd…`) | gives the `BARE_KING_LMR_CAP` gate on the base tree, so cap ON vs OFF is a **single-switch** comparison |

Using base+cap rather than base-vs-PC-r15 is deliberate: the two variants then differ in
**one line**, so any difference is attributable to the cap. That the ported patch
reproduces the PC's behaviour is checked rather than assumed — see §2.4.

---

## 2. The honesty gate (mandatory)

### 2.1 Flag OFF is bit-identical

Not merely equal pins — **the same bytes**:

```
$ sha256sum /tmp/bld_off/forge /tmp/build_base/forge
e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83  /tmp/bld_off/forge
e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83  /tmp/build_base/forge
```

and the four pins on both builds:

| check | expected | flag off | flag on |
|---|---|---|---|
| `bench 11` | 312,866 | 312,866 | 312,866 |
| `bench 13` | 862,329 | 862,329 | 862,329 |
| `bench 16` | 3,024,920 | 3,024,920 | 3,024,920 |
| `go perft 5` | 4,865,609 | 4,865,609 | 4,865,609 |

The cap variants hold the same four (all five builds, §2.4).

### 2.2 Flag ON changes nothing but output lines

Proved by diffing, not by reading the patch: `scripts/identity40.py` runs the flag-off
and flag-on builds on 40 positions at `go depth 10`, Threads 1, Hash 16, OwnBook false,
one fresh process per search, reading stdout to `bestmove` before sending `quit`
(findings §7: an aborted search returns a fabricated bestmove).

```
IDENTICAL 40 of 40; differing 0
```

compared on **bestmove, final depth, score and node count** per position.

### 2.3 The instrument's own arithmetic, with a negative control

`scripts/check_instrument.py` verifies, on raw output: the magnitude histogram sums to
`applied`; recomputed `Σ(r·count)/Σcount` equals the printed `rmean`; `cap_mag` sums to
`cap_gate`; `cap_clamp ≤ cap_gate`; `research ≤ applied`; and the per-root blocks sum to
their iteration block. It also corrupts one histogram bin by +1 and **requires** the
check to fire.

```
evidence/raw/instrument_consistency_input.txt: examined 253 per-depth blocks, 10 depths, 0 failures
evidence/raw/perdepth_capON_cntr1_raw.txt: examined 44 per-depth blocks, 10 depths, 0 failures
NEGATIVE-CONTROL(histogram inflated by 1): examined 253 per-depth blocks, 10 depths, 1 failures
NEGATIVE CONTROL PASSED: the corrupted input was rejected
ALL CONSISTENT
```

**This check earned its place**: it is what found the negative-`r` binning bug in §1.

### 2.4 The cap variants reproduce the published behaviour

The 11 boards are seat 08's `check_s03f13.txt` divergence table, hard-coded and
re-parsed by python-chess before use. At `go depth 8`:

| build | base moves reproduced | PC moves reproduced |
|---|---|---|
| base `6b98f217` | **11 of 11** | 0 |
| PC r15 (r15 patch applied) | 0 | **11 of 11** |
| base + cap ON | 0 | **11 of 11** |
| base + cap OFF | **11 of 11** | 0 |

and at `go depth 10` the node counts are seat 08's V0/V1 columns exactly — 27,188 /
17,208, 20,418 / 10,990, 14,095 / 25,076, … (evidence `raw/loneking_d10_capON.txt` and
`raw/loneking_d10_capOFF.txt`; all 11 pairs checked against seat 08's published table,
11 of 11 match). So the single-switch build is a faithful stand-in for the PC build on
this question.

---

## 3. Reduction statistics for ordinary positions — nobody had published these

40 ordinary positions (the first 40 of seat 08's `OG200`), `go depth 12`, Threads 1,
Hash 16, OwnBook false, base tree with the flag on.

| quantity | value |
|---|---|
| positions | 40 |
| nodes searched | 2,175,091 |
| reductions applied | 848,471 |
| **reductions per 1000 nodes (pooled)** | **390.09** |
| per-position reductions/1k | median 391.99, min 344.22, max 449.99 |
| **pooled mean reduction r** | **2.377** |
| per-position mean r | median 2.370, min 1.960, max 2.610 |
| **re-searches** | **22,536 = 2.66%** of applied reductions |
| LMR rejections | 835,766 = 384.24 per 1000 nodes |

Magnitude distribution, pooled over 848,471 reductions:

| r | share | r | share |
|---|---|---|---|
| −3 | 0.00% | 3 | 19.44% |
| −2 | 0.20% | 4 | 13.59% |
| −1 | 1.67% | 5 | 6.56% |
| 0 | 8.91% | 6 | 3.08% |
| 1 | 22.61% | 7 | 0.85% |
| 2 | 22.91% | 8–10 | 0.17% |

**So 10.79% of reductions have magnitude 0 or less** — LMR is entered but reduces nothing,
or reduces by a negative amount, close to one in nine — and the distribution is centred
on 1–2 plies with a thin tail to 10.

Guard rejections (overlapping; percentages are of the 835,766 rejected nodes):

| guard | nodes | share of rejected |
|---|---|---|
| movecount | 632,334 | 75.66% |
| depth | 500,510 | 59.89% |
| pvcap | 15,921 | 1.90% |
| mate / fifty / baremode | 0 | 0.00% |

Two facts worth having: **`fifty` never rejects a reduction** on this set (the
halfmove-clock guard `halfmove_clock + new_depth < 100` never bound at depth 12 from
these positions), and the two dominant reasons LMR is skipped are simply "not enough
moves yet" and "not deep enough".

At `go depth 8` on the same set the pooled rate is 389.62/1000 and mean r 2.125 — so
the rate per node is flat in depth while the mean magnitude rises, which is what the
`log(depth)·log(moves)` reduction table implies.

**Control that the instrument is not manufacturing a number:** the same 40 positions on
the **cap tree with the cap OFF** give **390.09/1000, r = 2.377, re-search 2.66%** —
identical to the base tree. The cap is inert here, exactly as its gate definition
(`root_bare_king_ && node has a lone side`) requires, and this is an independent check
that neither tree nor the instrument is drifting.

---

## 4. The 11 lone-king boards: what the counters say

Depth 10, Threads 1, Hash 16, OwnBook false, cap ON vs cap OFF, both instrumented.
`dNodes` is capON − capOFF. The two `CNTR` rows are the boards where cap-OFF visits
**more** nodes.

| board | cls | dNodes | applied ON | applied OFF | rmean ON | rmean OFF | cap gate | clamp | clamp% | cap rmean |
|---|---|---|---|---|---|---|---|---|---|---|
| `8/8/2B1k3/…` | pred | +9,980 | 8,233 | 4,118 | 0.80 | 2.29 | 8,233 | 5,260 | 63.9% | 1.97 |
| `8/8/2k5/4P3/…` | pred | +9,428 | 5,670 | 1,964 | 0.84 | 2.01 | 5,670 | 3,975 | 70.1% | 1.99 |
| **`8/2k5/4P3/8/3P4/PR6/3K4/8`** | **CNTR** | **−10,981** | 2,636 | 6,217 | 0.88 | 1.80 | 2,636 | 1,529 | **58.0%** | 1.79 |
| `8/4k3/8/6R1/…` | pred | +14,040 | 7,628 | 2,849 | 0.92 | 2.10 | 7,628 | 5,207 | 68.3% | 2.11 |
| `1R6/8/k7/…` | pred | +7,526 | 3,488 | 660 | 0.91 | 1.74 | 3,488 | 2,164 | 62.0% | 1.93 |
| **`8/8/8/4R3/2k5/P7/8/2K5`** | **CNTR** | **−621** | 1,232 | 907 | 0.85 | 1.89 | 1,232 | 830 | **67.4%** | 1.98 |
| `8/8/8/1R6/1K6/…` | pred | +6,547 | 6,659 | 3,273 | 0.90 | 2.33 | 6,659 | 4,809 | 72.2% | 2.20 |
| `8/8/P7/…/1k6/8` | pred | +3,356 | 1,314 | 1,718 | 0.79 | 1.56 | 1,314 | 747 | 56.8% | 1.87 |
| `6K1/2b5/p1k5/…` | pred | +9,605 | 5,743 | 2,392 | 0.88 | 2.07 | 5,743 | 3,810 | 66.3% | 2.15 |
| `8/2k5/p7/…` | pred | +13,946 | 6,975 | 2,554 | 0.95 | 2.28 | 6,975 | 4,941 | 70.8% | 2.05 |
| `2k5/8/p7/…` | pred | +8,191 | 7,993 | 5,487 | 0.91 | 2.18 | 7,993 | 6,205 | 77.6% | 2.38 |

### 4.1 The counters do not separate the classes

`scripts/separation.py` asks the lead's question directly: a statistic separates the
classes if **both** counter-case values fall outside the 9-board range. It also computes
the test's power by enumerating all 55 ways of choosing which 2 boards are the
counter-cases.

```
POWER of the range test: a statistic with NO relation to the classes still
  'separates' them in 5% of random assignments of 2-of-11,
  so its power is 95%.

counter            sep  in             pred range  counter-case vals rho vs dNodes       p
dNodes             YES   0      [3356, 1.404e+04]   -1.098e+04, -621        +1.000  0.0000
nodes_capON        YES   0 [1.454e+04, 2.916e+04]     1.41e+04, 5785        +0.882  0.0009 (tree-scaled)
applied            no   1           [1314, 8233]         2636, 1232        +0.764  0.0087 (tree-scaled)
rmean              no   2             [0.79, 0.95]           0.88, 0.85        +0.411  0.2086
research           no   1              [35, 198]               86, 22        +0.636  0.0398 (tree-scaled)
rej                no   1            [958, 5546]            2648, 747        +0.736  0.0136 (tree-scaled)
cap_gate           no   1           [1314, 8233]           2636, 1232        +0.764  0.0087 (tree-scaled)
cap_clamp          no   2            [747, 6205]            1529, 830        +0.718  0.0170 (tree-scaled)
cap_rmean          no   1           [1.87, 2.38]             1.79, 1.98        +0.455  0.1644
clamp_share        no   2       [0.5685, 0.7763]         0.58, 0.6737        +0.373  0.2603
clamp_per_node     no   2      [0.04887, 0.2577]         0.1085, 0.1435        +0.427  0.1886
gate_per_node      no   2      [0.08596, 0.3466]           0.187, 0.213        +0.455  0.1623
applied_per_node   no   2      [0.08596, 0.3466]           0.187, 0.213        +0.455  0.1623
rej_per_node       no   2      [0.06267, 0.2532]         0.1879, 0.1291        +0.264  0.4301
rmean_drop         no   2           [0.77, 1.49]             0.92, 1.04        +0.564  0.0747
applied_delta      no   1           [-404, 4779]         -3581, 325        +0.909  0.0004 (tree-scaled)
```

**Not one reduction statistic separates them.** The two that do — `dNodes` and
`nodes_capON` — are node counts, which define the classes; they are the control.

**The rank-correlation column needs care and I nearly misread it.** `applied`, `rej`,
`cap_gate`, `cap_clamp` and `applied_delta` all correlate strongly with `dNodes`
(ρ = 0.72–0.91, p ≤ 0.017). That looks like a mechanism and is not: **every one of those
counts scales with the size of the tree it was counted in**, so a board whose tree is
bigger applies more reductions for the same reason it visits more nodes. The columns
that are *not* mechanically tied to tree size — `rmean`, `cap_rmean`, `clamp_share`,
and every `*_per_node` — all have |ρ| ≤ 0.46 and no significant association. The script
flags the tree-scaled columns in its output for exactly this reason.

**The power caveat is real and goes in the same paragraph as the result.** At 95% power
a non-separation is a strong negative with respect to *these* statistics; it is not a
proof that no reduction-shaped statistic could separate them. What it does establish is
that the specific instrument the findings asked for — per-depth reduction counts, their
magnitudes, re-searches and rejections, and the cap's own share — **does not contain the
answer**.

### 4.2 The per-depth view, and one hypothesis killed

Totals are dominated by the largest iteration, so I also compared the **iteration where
the two builds first diverge**, and the per-depth profile.

First divergence depth and the clamp profile at that depth:

| board | cls | 1st divergence | clamp% there | r ON | r OFF | drop | dNodes there |
|---|---|---|---|---|---|---|---|
| `8/8/2B1k3/…` | pred | 4 | 52.3% | 0.64 | 1.77 | 1.13 | −51 |
| `8/8/2k5/4P3/…` | pred | 5 | 38.8% | 0.78 | 1.08 | 0.30 | +87 |
| **`8/2k5/4P3/8/…`** | **CNTR** | **5** | **30.7%** | 0.61 | 1.25 | 0.64 | +4 |
| `8/4k3/8/…` | pred | 4 | 57.1% | 0.67 | 1.32 | 0.65 | +10 |
| `1R6/8/k7/…` | pred | 5 | 45.5% | 0.65 | 1.64 | 0.99 | +128 |
| **`8/8/8/4R3/2k5/…`** | **CNTR** | **4** | **50.0%** | 0.73 | 1.37 | 0.64 | +61 |
| `8/8/8/1R6/1K6/…` | pred | 4 | 25.8% | 0.67 | 0.92 | 0.25 | +7 |
| `8/8/P7/…` | pred | 6 | 27.5% | 0.83 | 1.09 | 0.26 | +20 |
| `6K1/2b5/…` | pred | 6 | 37.2% | 0.86 | 1.37 | 0.51 | +24 |
| `8/2k5/p7/…` | pred | 5 | 40.8% | 0.84 | 1.24 | 0.40 | +51 |
| `2k5/8/p7/…` | pred | 4 | 28.7% | 0.64 | 1.44 | 0.80 | +213 |

At the divergence depth: `clamp%` predicted range [25.8, 57.1] vs counter
{30.7, 50.0} — **2 of 2 inside**; `r drop` [0.25, 1.13] vs {0.64, 0.64} — **2 of 2
inside**; `r_OFF` [0.92, 1.77] vs {1.25, 1.37} — **2 of 2 inside**. The divergence
depth itself is {4, 5} against {4, 4, 4, 4, 5, 5, 5, 6, 6} — **overlapping, not ordered**.

**A trap this table sets, stated because I nearly walked into it.** On the counter-case
`8/2k5/4P3/…`, cap-OFF visits **more** nodes at the final depth (−10,981 difference) but
at the depth where the two builds first differ the difference is only **+4 nodes**, and
cap-OFF's reduction count is *identical* (75 vs 75). The large final gap is generated
**after** the first divergence, by the two trees evolving differently — not at the point
of divergence. Reading the final `dNodes` as "where the cap did its work" is wrong on
this board, and the per-depth trace is what shows it.

**The cascade hypothesis, killed.** Seat 08's handoff proposed the clamp changes the
tree → changes the score → changes the next iteration's aspiration window → flips the
node-count direction. That predicts the score diverges **before** the node count. It does
not, anywhere:

```
ordering counts
                score-first  node-first   same
pred                      0           5      4
CNTR                      0           1      1
```

**0 of 11 boards went score-first.** So the divergence is created within a single
iteration, before any score is published, and the aspiration channel is not the
mechanism. (Fisher p = 1.0000 on the 2×2 — the ordering does *not* separate the classes
either; what the result kills is the hypothesis, not a classifier.)

### 4.3 The clamp's immediate effect is the same on every board; only the later evolution differs

This is the sharpest thing the instrument found, and it comes from splitting the effect
into the depth where the builds *first* differ and the *final* depth
(`scripts/immediate_effect.py`, `scripts/flip_test.py`).

| | cap-ON larger at first divergence | at the final depth |
|---|---|---|
| predicted (9) | 8 of 9 | 9 of 9 |
| counter (2) | **2 of 2** | **0 of 2** |

```
cap-ON visits MORE nodes at the first divergence: 10 of 11
  boards where it does not: [('8/8/2B1k3/...', -51)]
counter-cases: immediate signs ['+', '+'], net signs ['-', '-']
```

**The clamp can only remove reduction, and at the moment the builds part it makes cap-ON's
tree larger — on both counter-cases exactly as on the predicted boards.** So the clamp
does *not* behave differently on the counter-cases at the point of divergence. What
differs is what happens **after** it: on the counter-cases the sign reverses between the
divergence depth and the final depth, and on the predicted boards it does not (8 of 9).

**That reversal is a lead, not a rule, and it has a named false positive.** One predicted
board (`8/8/2B1k3/8/3PP3/P7/4K3/7R b`) also reverses, from −51 at divergence to +9,980
net:

```
counter-cases that flip     2 of 2
predicted boards that flip  1 of 9
2x2 [[2,0],[1,8]]  two-sided Fisher p = 0.0545
```

p = 0.0545 does not clear 0.05, **and the subgroup was defined after seeing the full
set**. By the rule in findings §6 this is recorded as a lead for a pre-registered run on
a fresh board set, explicitly not a finding — a near-significant post-hoc split is
exactly what gets quoted as confirmatory if the warning is not printed beside it.

**What survives without the p-value**: the clamp's *immediate* direction is identical on
the counter-cases and the predicted boards (2 of 2 and 8 of 9 positive). That is a
statement about where the second mechanism is **not** — it is not in how the clamp acts
at a node, and it is not at the point of divergence. It is downstream, in how the two
trees propagate after they first part.

---

## 5. What this establishes, and where the next instrument points

**Established by measurement**
- The instrument exists, is off by default, and flag-off is byte-identical (§2.1).
- Flag-on changes only printed lines: 40 of 40 positions identical on bestmove, depth,
  score and nodes (§2.2).
- Ordinary positions: **390.09 reductions per 1000 nodes, mean magnitude 2.377, 2.66%
  re-searched**, with the magnitude distribution and guard profile in §3. These are new
  numbers and they are reproducible from the scripts here.
- The reduction profile away from lone-king roots is **identical on the base tree and
  the cap tree** (390.09/1000, r=2.377 both), which is a control on both the gate and
  the instrument.
- **No reduction statistic separates the two counter-cases** at the final depth or at
  the divergence depth (§4.1, §4.2). This is a strong negative at 95% power for the
  statistics tested.
- **The aspiration-cascade account is refuted**: the score never diverges before the
  node count, 0 of 11 (§4.2).
- **The clamp's immediate effect is identical on the counter-cases and the predicted
  boards** — cap-ON is the larger tree at the first divergence on 2 of 2 counter-cases
  and 8 of 9 predicted boards (§4.3). So the second mechanism is not in how the clamp
  acts at a node, and not at the point of divergence.

**Inferred, not established**
- The mechanism is created **inside a single iteration's visit set**, before a score is
  published, and **downstream of the first place the two trees differ** (§4.2, §4.3).
  This is a location derived from a refuted alternative plus two negatives, not a cause.
- The sign reversal between divergence and final depth is **2 of 2 counter-cases against
  1 of 9 predicted** (Fisher p = 0.0545, post-hoc) — a **lead**, not a finding, and it
  carries a named false-positive board (§4.3).
- The most plausible thing left is that the clamp changes *which* nodes are reached at
  the same nominal depth (a different move ordering downstream), so the same `r` profile
  produces a different tree. The current counters are blind to that by construction:
  they count reductions, and a reduction count is not a node identity.

**What the next instrument should count, concretely** — this is the deliverable of a
negative result, and §4.3 sharpens it: the mechanism is **downstream of the first
divergence**, so the instrument must follow the two trees *after* they part rather than
describe the moment they part.

1. **Per-depth node identity, not counts.** A hash of the sorted set of visited keys per
   iteration would show whether cap ON and OFF visit the *same* set with different sizes,
   or *different* sets. The counter-case at depth 5 parts with an identical reduction
   count (75 vs 75) and a 4-node difference — at that moment the trees are still almost
   the same, so the informative comparison is the set at depth 6 onward.
2. **The first ply at which the two trees differ, in move identity.** On the
   counter-case above the trees part at depth 5 with the same reduction count, so the
   question is which *move* was reduced and what it reached.
3. **TT hit rate per depth** on both sides. A clamp that changes visited nodes changes
   what the table has seen; if counter-case boards show a different TT hit trajectory
   *after* the divergence depth, the mechanism runs through the table.

**The cheapest decisive probe of the three is (1)**, because it answers the prior
question — whether a reduction-counting instrument could ever explain this at all. If
the visited sets are identical and only their sizes differ, the counters should have
worked and the negative here is a puzzle; if the sets differ, the counts were the wrong
instrument from the start and (2) is the next step.

**What I did not do, and would want read as a gap:** I did not build that second
instrument, and this report should not be read as saying the mechanism is in the table
or in move ordering — only that it is not in any reduction statistic I could count.

---

## 6. How to reproduce everything

```
git worktree add /tmp/base 6b98f2170a3210e71beed04bbd2553972c253ed7
cd forge-combo29/swarm/reduction && bash scripts/run_all.sh /tmp/base/forge-combo29
```

The build trap is handled inside `run_all.sh`: `-DCMAKE_CXX_COMPILER=/usr/bin/g++` (the
default `/usr/bin/c++` is clang 18 with a broken header path) and
`LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`. Every build is a copy under `/tmp`;
the repository's engine source is never modified, and the instrument reaches it only as
the two text patches in `patches/`.

Individual scripts, each self-describing:

| script | what it does |
|---|---|
| `make_lmr_stats.py SRC [cap\|nocap]` | writes the instrumentation into a scratch tree |
| `identity40.py A B FENS` | bestmove/depth/score/nodes identity gate |
| `check_instrument.py RAW…` | histogram arithmetic + negative control |
| `loneking11.py EXE` | the 11 boards, with reduction counters |
| `separation.py ON OFF` | range test + power + rank correlation |
| `perdepth.py EXE FEN` | per-depth profile for one board |
| `divergence_depth.py ON OFF` | first divergence depth per board |
| `score_trajectory.py ON OFF` | per-depth score vs node divergence |
| `cascade_test.py traj.json` | the score-first / node-first ordering test |
| `clamp_profile.py ON OFF` | clamp share at the divergence depth |
| `divergence_depth.py ON OFF` | first divergence depth per board |
| `immediate_effect.py div.json` | immediate vs net sign per board |
| `flip_test.py div.json` | does the sign reversal separate the classes, and its false positive |
| `ordinary_stats.py EXE FENS` | the position-set statistics of §3 |

Raw outputs are in `evidence/raw/`, JSON in `evidence/`.

## 7. Limits of this report

- **n = 11, and only 2 counter-cases.** Every class comparison here is 2-against-9. The
  range-test power is computed (95%) and stated with each verdict, and the rank
  correlation uses all 11 — but a third counter-case could change the picture, and the
  honest reading of §4.1 is "these counters do not explain *these two boards*", not "no
  counter could".
- **Depth 10 is the deepest measured on all 11 boards.** The counter-case gap *grows*
  after the divergence (§4.2), so a deeper run could in principle make a difference
  visible that depth 10 does not. I measured depth 8 and 10 and they agree in direction.
- **The `fifty` guard reads 0 everywhere** in §3 because the halfmove clock never binds
  at depth 12 on that set. That is a property of the sample, not a claim that the guard
  is dead code — a position with a high halfmove clock would exercise it, and no such
  position is in these 40.
- **The ordinary-position statistics are on 40 positions.** They are a first published
  number, not a population result. The per-position spread is reported (344–450 per 1k)
  precisely so the number is not read as a constant.
- **The cap-tree figures rest on seat 03's ported patch**, which I verified reproduces
  the PC's 11 moves and node counts at depths 8 and 10 (§2.4) but which is not the PC's
  source. Where the two could differ I did not measure.
