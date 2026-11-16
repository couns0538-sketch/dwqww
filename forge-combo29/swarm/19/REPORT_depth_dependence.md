# Depth dependence — `corrected_eval` is FLAT, but the transposition table triples by depth 16

seat 19 · area 9 · build **PC r15** · settings **PC20** · **Threads 1** · `bench 13` ×40 and `bench 16` ×12.

## 1. The three lines

**What was asked.** Does the `corrected_eval` share grow with depth — is 5.75 % at bench 13 very different at
depth 16, making it a natural target for the next round?

**The answer.** **No: `corrected_eval` is flat — 5.75 % at depth 13, 5.77 % at depth 16.** The depth-sensitive
symbol is a different one: **the transposition table probe, 2.68 % at depth 13 and 8.47 % at depth 16**, moving
from outside the top ten to **fourth hottest**. That is the depth-driven target, not `corrected_eval`.

**How sure.** High. Both runs are cold (`bench` self-clears, 19-F23), both reproduce their own pins exactly
(depth 13: 40/40 runs at 587,276; depth 16: 12/12 at 2,343,893), zero refusal lines, 26 K and 33 K samples.
The `corrected_eval` flatness is a 0.02-point difference, i.e. measurement identity — it is not a small growth,
it is no growth.

## 2. The comparison

| family / symbol | depth 13 | depth 16 | change |
|---|---|---|---|
| **`corrected_eval`** | **5.75 %** | **5.77 %** | **+0.02 — flat** |
| all evaluation | 36.53 % | 34.40 % | −2.13 |
| NNUE accumulator work | 13.39 % | 12.17 % | −1.22 |
| HCE term walk | 14.96 % | 14.36 % | −0.60 |
| move ordering | 18.33 % | 17.12 % | −1.21 |
| static exchange (`see_ge`) | 5.25 % | 4.88 % | −0.37 |
| **transposition table** | **2.68 %** | **9.10 %** | **+6.42** |
| ↳ of which `probe_body` | (not in top 10) | **8.47 %, 4th hottest** | — |
| main search recursion | 12.46 % | 12.73 % | +0.27 |
| quiescence | 3.89 % | 3.20 % | −0.69 |

Depth-16 top five by self time: `evaluate_position` 14.36 %, `Worker::search` 12.73 %,
`nnue::apply_and_evaluate` ~12.2 %, **`probe_body` 8.47 %**, `MovePicker::next` 6.47 %.

## 3. Findings

**19-F34 — `corrected_eval`'s cost is depth-INDEPENDENT (5.75 % at depth 13, 5.77 % at depth 16), so it is a
flat per-node tax, not a growing one.** That matters for how it should be attacked: a fixed share per node means
saving time there scales with total nodes and depth does not change the case for doing it — but it also means it
will never dominate, and it is not the thing that gets worse with deeper search. Build PC r15, PC20, Threads 1.

**19-F35 — the transposition table becomes the fourth hottest symbol by depth 16: 2.68 % → 8.47 % for
`probe_body` alone, +6.42 points for the family.** This is the depth-driven cost, and it is the opposite of what
my retracted 19-F18 claimed and of what 19-F18's *workload* argument would predict: here the growth comes purely
from **depth**, on the same eight cold positions, with no warm-state confound anywhere (both runs cold, both at
their pins). Deeper search probes the table far more per node, and the table's cost scales with it.

### Suspicions, not proven

- That the TT growth is a *capacity* effect (deeper search fills more of the 16 MB table, so more probes take
  the age/depth replacement scan) rather than a pure call-frequency effect. I did not count probes at depth 16,
  so I cannot split frequency from miss cost. **This is the clean next experiment**: run the TT counters
  (`job4/instrument_tt.py`) at depth 16 cold and compare the full-table rate against depth 13's 142/13.9M.
- That `Hash 16` makes this worse than the owner's real setting would. `bench` builds `Searcher(16)`; a
  larger hash in real play would fill more slowly, so 8.47 % may be a bench-specific ceiling rather than the
  owner's number. Untested — and worth saying loudly, because it means this finding is about *bench at depth 16*
  and not automatically about the owner's games.

## 4. What I did NOT do

- I did not count TT probes at depth 16 (see above), so the mechanism is a hypothesis.
- I did not test Hash 32/64 at depth 16 to see whether the TT share shrinks with a bigger table.
- I did not run depth 14 or 15, so "grows with depth" is interpolated from two points.

## 5. What this means for the next round

`corrected_eval` is a **flat** 5.8 % — worth attacking only as a per-node constant. **The transposition table is
the depth-growing cost and the better target**, and 19-F35 gives a clean, cold, pin-anchored reproduction of it
on the build the owner runs. The caveat to carry: it is measured at `Hash 16` under `bench`, and the owner plays
with a different hash size, so the *share* will differ even if the trend holds.

## 6. Files

`pcspeed/profile_pc20.sh` (now takes a depth argument), `pcspeed/prof20/` (depth 13, 26 K samples),
`pcspeed/prof16/` (depth 16, 33 K samples), `pcspeed/summary20.txt`, `pcspeed/summary16.txt`.
