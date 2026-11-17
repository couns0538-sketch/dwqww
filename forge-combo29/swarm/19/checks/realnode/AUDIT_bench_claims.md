# 19-C57 — AUDIT: every finding that rests on a `bench` node count, and whether it survives

**Why this exists.** 19-C55 showed `bench` gets the **sign** of the aggregate PC20 node effect wrong
(bench 11 **+14.5 %**, bench 13 **−10.6 %**, bench 16 **+8.7 %**, real positions **−9.1 %**). Any claim of the form
"these switches reduce nodes by X %" measured on a bench therefore needs re-checking. This is that audit.

**Verdict legend:** **SURVIVES** (re-verified, or unaffected by construction) · **QUALIFIED** (part stands, the
generalisation does not) · **SUPERSEDED** (replaced by a real-position figure).

---

## MY findings

| finding | the bench-based claim | verdict | why |
|---|---|---|---|
| **19-C35** | per-node cost **1.0119** [0.9997, 1.0241], "at most ~1.2 % slower", bench 16 | **SUPERSEDED** | real positions: **median 1.071**, IQR [1.044, 1.110], 90 % of 180 pairs. Bench understates ~6×. → 19-C53/C54 |
| **19-F32** | `CorrHistV2` **saves 4.3 % of nodes**, bench 13 | **SURVIVES on magnitude, QUALIFIED on meaning** | real n=120: pooled **5.2 %** — agrees. But **only 54.2 % of positions favour it**, IQR 0.767–1.180 (28× the effect). Pooled property, not a per-position one. → 19-C56 |
| **19-F34** | `corrected_eval` "flat per-node tax", 5.75 % bench 13 / 5.77 % bench 16 | **QUALIFIED** | the two shares are genuinely equal, but those benches have **opposite-sign** node effects (0.894 vs 1.087), so a flat profile share is not evidence of a flat **real-position** per-node tax |
| **19-F33** | `CorrHistV2` changes the move in 22.0 % of positions — **measured on real positions** (set G, depth 12) | **SURVIVES** | not a bench claim. My 19-C56 independently got **20.8 %** of 120 — consistent |
| **19-C40** | PC20 node ratios "1.1893 / 0.4979 / 0.5722 / 1.0977 / 1.0904" | **SURVIVES** | measured on **set G at depth 14**, real positions, not bench |
| **19-F42** | TT scan hit distribution "already optimal, reordering gains 0 %", bench 16 | **SURVIVES as a structural result** | it is a **probe-order** measurement (hits by slot), not a node-magnitude claim; the hit distribution is a property of the probe sequence, not of bench's search tree. Would still be worth a real-position confirmation, but nothing here undermines it |
| **19-C19** | king-lines counts on bench 13 (804,371 / 779,027) | **SURVIVES** | a **counter** measurement (how often a function is called), not an effect size. Reproduces seat 29 exactly and was extended to bench 16 and PC20 |
| **19-F26** | `std::sort`→`stable_sort` moves pins: bench 11 −8.6 %, 13 +5.7 %, 16 −14.7 % | **SURVIVES** | it is an **ablation-direction** result, and the *point* of it is that the direction **varies by bench** — which is exactly the caution 19-C55 quantifies. Its conclusion ("pins are load-bearing on tie order") needs no real-position check |
| **19-C3** | fitted `bench` intercept 11.91 ms (time-vs-nodes across 7 benches) | **SURVIVES** | a **fixed-cost** measurement on bench, and explicitly a bench statement. It is not generalised to real positions |
| **19-F16 / 19-F17** | the four honesty pins, stable across compilers | **SURVIVES** | pins are bench by definition — that is what they are for |

## OTHER SEATS' findings that touch bench node counts

| seat / finding | claim | verdict | why |
|---|---|---|---|
| **29-F3** (confirmed by my 19-C3) | bench time-vs-nodes linear fit / fixed cost | **SURVIVES** | fixed-cost measurement, bench-scoped by construction |
| **29-F30/29-F31 area** (`_mm_prefetch`) | prefetch makes `bench 13` 9.43 % **slower in wall time** | **SURVIVES as a bench result; NEEDS REAL-POSITION CHECK as a general claim** | it is a **time** measurement on bench with a tight CI and 48 ABBA pairs, and it is honest about being bench 13. **But 19-C53/C55 now show bench misrepresents both per-node cost and node counts**, so "prefetch is 9.4 % slower" should not be read as a real-position figure until re-measured. **Recommend seat 29 or a successor redo it at fixed depth on real positions.** |
| **29-F42 / F53** | PC20 searches 10.7–11.9 % fewer nodes | **SURVIVES — and is corroborated** | seat 29 measured these on **real positions** (R_2911, depth 12), not bench. My 19-C53 got **12.4 %** on a different set. Two seats, two sets, same answer |
| **29-F56** | no wall-time difference, n=40 | **QUALIFIED** | underpowered (needs n≈87 for 12 %); the *conclusion* was right, the *sample* could not support it. My 19-C53 at n=119: ratio 0.9728 |
| **29-F58/F59/F60** (v3 path) | v3 family 19.75 % of bench 13; per-node ~1x | **F59 SURVIVES** (fixed-node ABBA on real positions, 3 independent harnesses agree); **F58 is a bench-13 PROFILE** | profile shares are bench-scoped; the family total 19.75 % is a bench-13 figure and should be quoted as such |
| **27's sign_600 series** | PC20/PC20-vs-S14 node and depth cells | **SURVIVES** | all on **600 real positions**, python-chess validated. I reproduced 600/600 cells exactly (19-C50) |
| **07's IIR `searchmoves` pin** (26329 → 36117 nodes) | node recovery at a restricted root | **SURVIVES** | a **`searchmoves`-restricted root** measurement, not a bench aggregate; the mechanism (IIR skipped) is structural |
| **05, 21, 25, 08, 10, 15, 24** | — | **no bench node-magnitude claims found** | grep over their FINDINGS for "bench N" + save/fewer/more/% nodes returned nothing qualifying. **Absence of a match is not proof of absence** — a claim phrased without the word "bench" would be missed |

## The pattern in one table
| measurement type | does bench transfer? |
|---|---|
| node **pins** / determinism | **yes, by definition** |
| **ablation direction** (sign of a change) | **yes, and even better than a single bench suggests — because it varies by bench** |
| **counter** counts (calls, probes, hit slots) | **yes** — structural, not tree-dependent |
| pooled node effect of **one isolated toggle** | **usually yes** (19-F32: 4.3 % → 5.2 %) |
| **per-node cost** | **NO — 6× too optimistic** (1.2 % vs 7 %) |
| **aggregate PC20 node effect** | **NO — sign flips across benches** |
| any pooled magnitude read as a **per-position** claim | **NO — 19-F32 is a coin flip per position** |

## The corrected rule (replaces the one I gave an hour ago)
> **Use `bench` for pins, determinism, ablation direction and structural counters. For an isolated single toggle,
> a pooled node effect usually transfers — but verify it once. Never use it for per-node cost, never for the
> aggregate PC20 set, and always report the per-position spread, because a pooled ratio can hide a coin flip.**

The first version ("never for magnitude") was **too broad**: 19-C56 shows a bench magnitude transferring correctly.
**Being wrong in the cautious direction is still being wrong, and it would have told seats to discard a valid
result.**
