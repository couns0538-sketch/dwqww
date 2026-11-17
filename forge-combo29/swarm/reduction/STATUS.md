# STATUS — reduction-count instrument (branch `swarm/reduction`)

Base commit: `6b98f2170a3210e71beed04bbd2553972c253ed7`
Branch: `swarm/reduction`
Deliverable: `forge-combo29/swarm/reduction/`

## State: COMPLETE

| item | state |
|---|---|
| instrument written (compile-time flag, default off) | done |
| flag-off pin gate (4 pins, plus byte-identical binary) | done |
| flag-on identity gate (40 positions, 4 fields each) | done |
| instrument's own arithmetic + negative control | done |
| 11 lone-king boards, base / cap-ON / cap-OFF, depth 8 and 10 | done |
| separation test with computed power and rank correlation | done |
| per-depth divergence, score ordering, clamp profile | done |
| ordinary-position reduction statistics | done |
| print path proved non-perturbing (counters-on-silent vs printing, 31 of 31) | done |
| visit-set fingerprints: same positions or different? | done |
| reduced-move fingerprints: which diverges first? | done — mixed, not a discriminator |
| line numbers in §3 corrected to positions, with the patch as the artefact | done |
| full pipeline re-run from a clean worktree | done |

Nothing is left running.

## Three additions after the first report

**The print path is now proved harmless, not asserted.** A third build state
(`FORGE_LMR_STATS=1, FORGE_LMR_STATS_PRINT=0`) runs every counter and prints nothing.
Silent = base is 40 of 40; printing = silent is 31 of 31 on bestmove, score, final nodes
**and every per-depth node count**. Nothing prints inside a search: the flush goes
immediately after the root loop's `emit` call, between completed iterations — the same
position as the engine's own `info depth` line. FINDINGS §3.

**The counters now have an explanation, not just a negative.** Per-ply fingerprints of
visited position keys show cap-ON and cap-OFF visit **genuinely different positions** at
the divergence depth on **9 of 11 boards, including both counter-cases** (2 boards are
same-set-different-multiplicity). So the reduction statistics average over different node
populations — which is precisely why equal-looking aggregates could not separate the
classes. FINDINGS §5.4.

**A third check, then a stop.** With the fingerprint machinery already in place I also ran
the §6 item-2 probe — reduced-move fingerprints, i.e. does the two builds' *reduction
decision* diverge before their visited positions do. It is **mixed** (7 same-ply, 2
MOVES-first, 2 positions-first) and **the two counter-cases do not share an ordering**, so
it is not the discriminator either. Recorded as a negative in FINDINGS §5.5, hand-verified
on one board, and the instrument stops here: the next candidate (TT hit rate) is a bigger
change and starting it late would have risked a half-finished third probe on top of two
clean ones.

**A correction to this report's own citations.** An earlier version gave the print
location as `search.cpp:2689`/`2532`/`2557`. Those are lines in the **instrumented** tree;
on base `6b98f217` (2,753 lines) 2689 is `seldepth_override = -1;`. The location is now
stated as a **position** — immediately after the root loop's `emit` call — with the patch
hunk as the artefact that pins it, and a `grep -n -B4` recipe instead of a number. The
numbers moved again while writing this (the flush went `:2718` → `:2745` when the
move-fingerprint diagnostic was added above it), which is the demonstration that a line
number is not the durable form.

The p = 0.0545 reversal lead was **not** pursued further; the probes that were run are the
cheap decisive ones, and they answered the prior questions rather than the p-value
question.

## The headline

**The instrument does not separate the two counter-cases.** Every reduction statistic —
count, magnitude histogram, mean, re-searches, guard rejections, and the same restricted
to `BARE_KING_LMR_CAP` nodes — puts both counter-case boards inside the 9-board range.
The counters do not move where the answer moves.

Two positives came out of chasing it:
- **The aspiration-cascade account is refuted**: the score never diverges before the node
  count, 0 of 11 boards.
- **The clamp's immediate effect is identical on the counter-cases**: cap-ON visits more
  nodes at the first divergence depth on 2 of 2 counter-cases and 8 of 9 predicted
  boards. The second mechanism is downstream of the divergence, not at it.

One lead, explicitly not a finding: the sign reversal between divergence and final depth
is 2 of 2 counter against 1 of 9 predicted, Fisher p = 0.0545, post-hoc, with a named
false-positive board.

## New published numbers (ordinary positions, 40, depth 12, base tree)

| quantity | value |
|---|---|
| reductions per 1000 nodes | **390.09** |
| pooled mean reduction r | **2.377** |
| re-searches | **2.66%** of applied reductions |
| magnitude ≤ 0 | 10.79% of reductions |
| LMR rejections | 384.24 per 1000 nodes |

Identical on the cap tree with the cap off (390.09 / 2.377 / 2.66%) — a control on both
the gate and the instrument.

## Gates, verbatim

```
bench 11    312,866     bench 13    862,329
bench 16  3,024,920     perft 5   4,865,609
```
All four hold on all five builds (base, flag-off, flag-on, cap-ON, cap-OFF).
`evidence/raw/pins_*.txt`.

Flag-off binary is **byte-identical** to the unmodified base build:
`e06310eca3368556…` (`evidence/raw/binary_identity.txt`).

Flag-on changes only printed lines: `IDENTICAL 40 of 40; differing 0`
(`evidence/raw/identity40.txt`).

## Reproduce

```
git worktree add /tmp/base 6b98f2170a3210e71beed04bbd2553972c253ed7
cd forge-combo29/swarm/reduction && bash scripts/run_all.sh /tmp/base/forge-combo29
```

Takes about 72 s. Every number in `FINDINGS.md` comes out of that run; it was re-run from
a clean worktree to confirm, and the numbers reproduced identically.

Build trap handled inside `run_all.sh`: `-DCMAKE_CXX_COMPILER=/usr/bin/g++` and
`LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`.

## Files

```
FINDINGS.md                       the report
STATUS.md                         this file
patches/lmr_stats_nocap.patch.txt instrument, base tree      (FORGE_LMR_STATS, _PRINT, _KEYS, _MOVES)
patches/lmr_stats_cap.patch.txt   instrument, cap tree
patches/base_bare_king_on.patch   seat 03's ported r15 bare-king patch (input, sha256 bab0fc2964cd…)
scripts/make_lmr_stats.py         writes the instrumentation into a scratch tree
scripts/run_all.sh                the whole pipeline
scripts/identity40.py             flag-off vs flag-on identity gate
scripts/check_instrument.py       histogram arithmetic + negative control
scripts/loneking11.py             the 11 boards with counters
scripts/separation.py             range test + power + rank correlation
scripts/perdepth.py               per-depth profile, one board
scripts/divergence_depth.py       first divergence depth per board
scripts/score_trajectory.py       score vs node divergence per depth
scripts/cascade_test.py           score-first / node-first ordering test
scripts/clamp_profile.py          clamp share at the divergence depth
scripts/immediate_effect.py       immediate vs net sign
scripts/flip_test.py              does the reversal separate the classes
scripts/ordinary_stats.py         the position-set statistics
scripts/print_gate.py             print path cannot perturb the tree
scripts/visit_sets.py             same positions or different ones?
scripts/reduced_moves.py          which diverges first: reduced moves or positions?
scripts/run_search.py             one search, reads to bestmove
evidence/                         JSON per measurement
evidence/raw/                     raw text, pins, build logs, pasted outputs
```

## Not done

- **The next step**: **TT hit rate per depth** on both builds (FINDINGS §6 item 3). The
  builds visit different positions at the same ply, so they populate and read the table
  differently; that is now the leading hypothesis. It is a bigger instrument than the two
  probes already done — it needs counters on the probe path — and it was deliberately not
  started late in the run.
- Depth 12+ on the 11 boards. Depth 8 and 10 agree in direction; the counter-case gap
  grows with depth, so a deeper run is the first thing to try.
- Any claim about the owner's actual net. All of this is the built-in net.
