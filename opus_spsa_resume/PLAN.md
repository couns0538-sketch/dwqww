# PLAN: joint tuning of two untuned search families on combo29

Status: design and executable configuration only. **No games are played by this job; tuning is PENDING QA EXECUTION.** No value below is claimed to be optimal, and no Elo is claimed. The evidence behind the family choice is in `AUDIT.md`.

## 1. Selected families
Both families have no SPSA run (R9, O30, R3), no gate option line in `FORGE_RESULTS.md`, and no in-flight CR candidate on their code lines (`AUDIT.md` §3–4). Code references are to combo29's `src/search.cpp`, the frozen snapshot verified against manifest 3389cfe3.

**F1: Razoring** (`search.cpp:1196-1202`, non-PV, not in check, no excluded move, beta not a mate score):
```
if (depth <= RazorDepth && eval + RazorBase + RazorMultiplier * depth < alpha) {
    razor = qsearch(alpha - 1, alpha); if (razor < alpha) return razor; }
```
**F2: Qsearch pruning** (`search.cpp:1047, 1057-1065`):
```
futility_base = static_eval + QsFutilityMargin;
if (!gives_check && !promotion && futility_base + capture_value(move) <= alpha) { best = max(best, futility_base + capture_value); skip; }
if (!see_ge(move, -QsSeeMargin)) skip;
```

**Interaction.**
- Razoring hands the node to `qsearch(alpha-1, alpha)` and returns that verdict, so F2's margins decide whether a razor attempt cuts. With a razor trigger `eval + M(d) < alpha`, where M(d) = RazorBase + RazorMultiplier·d, a capture survives qsearch futility only if `capture_value > alpha − 1 − static_eval − QsFutilityMargin`. That is, roughly `capture_value ≥ M(d) − QsFutilityMargin`: QsFutilityMargin directly sets how much of the verification search razoring triggers.
- F2 also runs at every leaf and inside ProbCut's verification, so shifting F2 changes the trees that F1's margins are judged on.
- The families cannot be tuned one at a time without re-tuning the other.

## 2. Tunable scalars (existing UCI names, unchanged; all already exposed by the lock build)
| Scalar | Family | Lock | Engine range | Tuned bound | Kind | c_end | r_end |
|---|---|---|---|---|---|---|---|
| RazorBase | F1 | 150 | 0..1000 | 0..600 | continuous (rounded to int) | 15 | 0.002 |
| RazorMultiplier | F1 | 350 | 0..1000 | 100..800 | continuous (rounded to int) | 35 | 0.002 |
| QsFutilityMargin | F2 | 160 | 0..1000 | 40..400 | continuous (rounded to int) | 16 | 0.002 |
| RazorDepth | F1 | 2 | 0..6 | levels {1,2,3} | discrete, **off by default** | 1 level | 0.002 |
| QsSeeMargin | F2 | 40 | 0..500 | levels {40,140,240} | discrete, **off by default** | 1 level | 0.002 |

- c_end equals about 10% of each value. This is the same step size R3 used for sensitivity, and on combo29 it moves bench nodes by 2–17% (`AUDIT.md` §5).
- r_end 0.002 is the OpenBench/Fishtest-style default; R9 used 0.012 and drifted at noise level.
- These are proposals, not measured optima.
- QsSeeMargin is a step function (bands of 100 search identical trees), so small SPSA steps carry no signal. If QA enables it, it is a level dimension: level ℓ maps to engine value 40 + 100·ℓ, and plus/minus straddle a band.
- RazorDepth is a small integer with large jumps per step, handled the same way.

## 3. Coupled constraints (derived from the code; each can be switched off in the config)
- **C1, monotone margin:** `QsFutilityMargin ≤ RazorBase + RazorMultiplier·1`. The depth-0 (qsearch) futility allowance must not exceed the depth-1 razor margin, so pruning optimism grows with depth. Lock: 160 ≤ 500.
- **C2, consistent optimism** (only when QsSeeMargin is enabled): `QsSeeMargin ≤ QsFutilityMargin`. A capture losing more SEE than the futility allowance cannot be rescued by the same allowance. Lock: 40 ≤ 160.
- **C3, razor liveness:** `RazorBase + RazorMultiplier·RazorDepth ≤ 2000`. Beyond that razoring essentially never fires and F1 stops carrying gradient. Lock: 850.
- Per-scalar bounds come from the table above. Every plus, minus and updated θ must satisfy all bounds and active constraints.

## 4. Interaction-aware schedule
1. **Joint perturbation.** Each batch draws one ±1 vector over all enabled scalars of both families (stateless `seed:k`, as in R9). The SPSA gradient therefore contains the F1×F2 cross terms; coordinate-wise tuning would not.
2. **Per-family scaling.** c_end and r_end are set per scalar in each scalar's own units, so a step of one family does not swamp the other.
3. **Feasible perturbation.** If θ ± c_k∘Δ would break a bound or constraint, one common factor s ∈ (0,1] shrinks the whole perturbation so the direction is kept. s, the active constraints, and any clipping are recorded per batch. If s drops below s_min (0.25), θ is first projected onto the feasible set and the event is logged.
4. **No-information coordinates (fix of E-006).** When a scalar's rounded plus equals its rounded minus, that scalar gets no update in the batch.
5. **Update and projection.** `θ_i ← θ_i + (a_k/c_k)_i · R · Δ_i` with R = wins − losses of plus over the batch's pairs, as in R9. The result is projected onto the feasible set (bounds first, then C1/C3 by moving along the constraint normal in c-scaled units).
6. **Diagnostics.** Constraint activity, shrink factors and per-family drift (z against the R9-style null-gradient noise) are logged per batch.
7. **Run size (proposal for QA).** N = 4000 pairs, 4 pairs per batch, STC 8+0.08, Threads 1, Hash 16, α 0.602, γ 0.101, A = 0.1·N. The `8moves_v3` training partition only (`partition/`).

## 5. Default-OFF engine control (`patches/tune_gate_after_combo29.patch`)
- Two independent compile-time switches, `FORGE_RAZOR_TUNE` and `FORGE_QS_TUNE` (default 0). At 0 nothing is compiled in and no option is registered.
- At 1 each registers one runtime spin option (`RazorTune` / `QsTune`, 0..1, default 0).
  - While a switch is 0, setoption on that family's existing names (RazorDepth/RazorBase/RazorMultiplier or QsFutilityMargin/QsSeeMargin) is stored but not applied. `tune::` keeps the lock values captured at startup, so OFF stays node-identical even if a runner sends tuned values.
  - Switching to 1 applies the stored values. Switching back to 0 restores the lock values (deterministic rollback).
- Only `uci.cpp` and a new header change; `search.cpp` is untouched.
- In the gate build this changes setoption semantics for those five names only, and only while the switch is 0.
- Tuning itself can drive the unmodified lock exe, because the scalars are already UCI options. The gate build is the delivery and rollback vehicle for the confirmation and a later merge. Its equivalence to the lock exe with the same values is proven by bench equality (BENCH.md).

## 6. Baseline snapshot and rollback
- **Baseline:** the lock values above plus both switches at 0, recorded in `configs/baseline_combo29.json` with exe hashes.
- **Rollback to baseline:** `bin\rollback.ps1 -Baseline` emits the baseline option line. Deterministic.
- **Rollback of a run:** `bin\rollback.ps1 -RunDir <dir> -ToSeq <n>` writes a new checkpoint with θ from checkpoint n and logs it. It never rewrites history.

## 7. What is not claimed
No tuned values, no Elo, no speed effect. Any non-default value changes search nodes, so it is a **SEARCH CHANGE, UNPROVEN** that needs Code Review, then QA tuning, then the independent confirmation SPRT (`confirm/CONFIRM_PROTOCOL.md`).
