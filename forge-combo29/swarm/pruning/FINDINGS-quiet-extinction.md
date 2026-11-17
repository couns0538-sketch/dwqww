# `QuietExtinction` loses forced mates — a wider, deeper band than `SoundMatePruning`

**Answer: yes, and worse.** `QuietExtinction` (off by default) loses or
mis-distances forced mates across **depths 6–16**, on **12 of 300 cells**, with
one fixture still wrong at depth 16 and correct only from 17. It is a sharper
mate-safety defect than `SoundMatePruning`, whose band closed at depth 10.

| | |
|---|---|
| Base | `6b98f217`, four pins verified (312,866 / 862,329 / 3,024,920 / 4,865,609) |
| Build | `build/clean/forge` — **no probe instrumentation**, so this is not an instrument artefact |
| Settings | `Threads 1`, `Hash 64`, `OwnBook false`, `QuietExtinction false` vs `true`, `go depth N` |
| Corpus | the 30 verified fixtures from `corpus/mates.json` × 10 depths, plus 3 dedicated unique-quiet fixtures |
| Verdict | **do not enable `QuietExtinction`**; its default (off) is correct |

## Why this rule is the one to worry about

`QuietExtinction` is narrower and more mate-relevant than the rest of the prune
set. After **two** quiet moves miss `alpha` by `>= QuietWideGap`, it calls
`close_quiet_tail()` and **drops every remaining non-checking quiet move** at
that node (`search.cpp`). Before that, one wide miss halves the futility slack
for later ordinary quiets (`futility_tight`), which is a second chance to drop
the same move.

A mating move that is **neither a check nor a capture** is exactly the kind of
move move-ordering puts late — and exactly the move this rule discards. That is
not a hypothesis about search shape; it is the rule's stated mechanism applied
to the class of move under test.

## 1. Counter evidence — the rule fires

Sampled on the dedicated deep fixtures (`evidence/quiet_extinction.json`):

| counter | max observed |
|---|---|
| `quiet_tail_closed` | **4,302** |
| `futility_tight_set` | **4,899** |
| `extinguish_futility_skip` | **590** |

**A first version of this check sampled `entries[:8]` and got 0 for all three**,
which would have supported a vacuous "the rule never fires". The first eight
corpus entries are mates in one: the search resolves the position and the quiet
tail never closes. The counters are now sampled where the rule is reachable.
This is the same kill-condition trap the brief names, caught in my own script.

## 2. Per-cell, with the depth beside every harm

The three dedicated fixtures have a **unique** mating move verified by three
solvers, so "wrong" here means the engine does not play the only move that
mates — not merely that it prefers a slower one.

| fixture | true | unique mating move | OFF arm correct | ON arm wrong at depths |
|---|---|---|---|---|
| `8/8/8/8/8/8/6KQ/4k3 w` | m3 | `g2f3` | 8–16 | **8, 9, 10, 11, 12, 13** |
| `8/8/8/8/8/K7/3R4/1k6 w` | m3 | `a3b3` | 9–16 | **9** |
| `K7/8/8/8/8/8/7k/Q7 w` | **m7** | `a1g7` (quiet queen move) | 10–20 | **10, 11, 12, 13** |

The mate-in-7 row is the one the coordinator asked for, and it is the clearest:
a **mate in seven** with a single quiet mating move, lost for four consecutive
depths. `a1g7` is neither check nor capture — precisely the move
`close_quiet_tail()` drops.

## 3. Corpus rate

30 fixtures × 10 depths = 300 cells.

| state | cells |
|---|---|
| both-right | 261 |
| both-wrong (horizon, neither arm found it) | 23 |
| **HARM** (default right, option wrong) | **12** |
| help (option fixed a default failure) | 4 |

Per depth, HARM cells: d6 1, d7 1, d8 1, d9 2, d10 2, d11 2, d12 1, d13 1,
d16 1, d14 0.

**The harm band is depths 6–16 and does not simply close.** The
`3KR3/5R2/8/k7/8/8/8/8 w` fixture is wrong at d15 and d16 (`e8e4` reporting
mate 6 and mate 5 instead of `f7b7` mate 3) and correct only from d17:

```
d15 OFF f7b7 m3 | ON e8e4 m6   HARM
d16 OFF f7b7 m3 | ON e8e4 m5   HARM
d17 OFF f7b7 m3 | ON f7b7 m3   ok
```

Deterministic — reproduced twice at depth 16. **Unlike `SoundMatePruning`,
this defect is not bounded at depth 10**, and an earlier draft of this section
said it closed at 14 on the strength of the three dedicated fixtures alone. The
corpus row contradicted that, and the contradiction was real.

## 4. Right move, wrong distance (§4's documented class)

Three cells give the correct mating move with the wrong mate number:

| depth | fixture | ON reports | truth |
|---|---|---|---|
| 7 | `8/8/8/3K4/k7/8/4Q3/8 w` | `d5c4`, no mate score | m3 |
| 10 | `8/8/8/8/8/K7/3R4/1k6 w` | `a3b3` **m4** | m3 |
| 11 | `8/7k/8/5K2/8/4R3/8/8 w` | `f5f6` **m4** | m3 |

These are the class §4 already documents, and they are the cases a
move-only checker would miss entirely.

## 5. What this does NOT establish

- **No depth control was run to separate "the rule is wrong" from "the tree
  shape reached the answer later"** for the corpus HARM cells. For
  `SoundMatePruning` I ran that control and it dissolved the attribution; here
  the dedicated fixtures already show a *unique mating move* being missed, which
  no amount of search depth excuses at the depth where it happens — but the
  12-cell count should be read as fixed-depth differences, not as 12 proven
  pruning defects.
- **Three dedicated fixtures is a small demonstration set**, not a rate. Two are
  KQ-vs-K conversions.
- **No strength claim.** Nothing here says `QuietExtinction` is bad for play,
  only that it costs mates on these positions.
- **`QuietExtinction` is off by default**, so this is a do-not-enable result,
  not a shipped defect.

## Reproducing

```bash
cd forge-combo29/swarm/pruning
bash scripts/build.sh all
python3 scripts/check_probe_identity.py     # pins must match in all three arms
python3 scripts/verify_corpus.py            # 30/30 accepted, distances re-derived
python3 scripts/quiet_extinction_test.py    # writes evidence/quiet_extinction.json
```
