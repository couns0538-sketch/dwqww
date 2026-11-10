# PLAN: joint tuning of two untuned search families on combo29 (revised after M1 review)

Status: design and executable configuration only. **No games are played by this job; tuning is PENDING QA EXECUTION.** No value below is claimed to be optimal, and no Elo or strength interaction is claimed. The evidence behind the family choice, and the alternatives considered, are in `AUDIT.md` §3–6.

## 1. Selected families
Code references are to combo29's `src/search.cpp` in the frozen snapshot (manifest 3389cfe3).

**F1: Razoring** (`search.cpp:1196-1202`; non-PV, not in check, no excluded move, beta not a mate score). `eval` here is the corrected static eval, replaced by the TT score when the TT bound allows it (`:1181-1186`):
```
if (depth <= RazorDepth && eval + RazorBase + RazorMultiplier * depth < alpha) {
    razor = qsearch(board, ss, alpha - 1, alpha); if (razor < alpha) return razor; }
```
**F2: Qsearch pruning** (`search.cpp:1047, 1057-1065`; not in check, best_score > -MateInMaxPly). `static_eval` is the qsearch node's corrected static eval:
```
futility_base = static_eval + QsFutilityMargin;
if (!gives_check && !promotion && futility_base + capture_value(move) <= alpha) { best = max(best, futility_base + capture_value); skip; }
if (!see_ge(move, -QsSeeMargin)) skip;      // applies to checks and promotions too
```

**Coupling.** This is code-level only; whether it matters for strength is UNPROVEN.
- Razoring hands the node to `qsearch(alpha-1, alpha)` and returns that result, so F2's futility margin decides how much of the verification search actually runs.
- With M(d) = RazorBase + RazorMultiplier·d and `eval ≈ static_eval` (no TT adjustment), a razor trigger means `alpha − 1 − static_eval ≥ M(d)`. The verification qsearch then skips every non-checking, non-promoting capture with `capture_value ≤ M(d) − QsFutilityMargin`, roughly. That is a necessary condition only, and it depends on the TT adjustment and on stand-pat.
- F2 also acts at every leaf and inside ProbCut's verification.
- Bench-node 2×2 probes cannot show the interaction: a control pair with an unrelated mechanism is just as non-additive (`AUDIT.md` §6).

## 2. Tunable scalars (existing UCI names, unchanged)
| Scalar | Family | Lock | Engine range | Tuned bound | c_end | r_end | In SPSA |
|---|---|---|---|---|---|---|---|
| RazorBase | F1 | 150 | 0..1000 | 0..600 | 15 | 0.002 | yes |
| RazorMultiplier | F1 | 350 | 0..1000 | 100..800 | 35 | 0.002 | yes |
| QsFutilityMargin | F2 | 160 | 0..1000 | 40..400 | 16 | 0.002 | yes |
| RazorDepth | F1 | 2 | 0..6 | – | – | – | **no**, frozen at 2 (an integer with large jumps; a later fixed ±1 A/B at most) |
| QsSeeMargin | F2 | 40 | 0..500 | – | – | – | **no**, frozen at 40: in-flight DR06 rewrites its line, and its effect is a plateau in steps of 100 (`AUDIT.md` §6); a later discrete A/B of 140 vs 40 at most |

- c_end is about 10% of each lock value, the step size R3 used for sensitivity; on combo29 it moves bench nodes by 2–17%.
- r_end 0.002 is the OpenBench/Fishtest-style default; R9 used 0.012 and drifted at noise level.
- Whether N = 4000 pairs can move θ by a measurable amount is estimated with the synthetic model in `BENCH.md` (S3).
- These are proposals, not measured optima.
- The harness still supports discrete level parameters (tested), but the recommended config does not use them.

## 3. Coupled constraints: heuristic priors, not correctness constraints
- **C1, monotone margins:** `QsFutilityMargin ≤ RazorBase + RazorMultiplier·1`. The depth-0 futility allowance should not exceed the depth-1 razor margin.
- **C3′, depth-1 razor liveness:** `RazorBase + RazorMultiplier ≤ 1000`. Beyond about a queen's worth, depth-1 razoring practically never fires and F1 stops carrying gradient. This replaces the earlier C3, which bounded only depth 2; M(2) = M(1) + RazorMultiplier stays bounded by the box.
- The earlier C2 (QsSeeMargin ≤ QsFutilityMargin) is dropped together with QsSeeMargin.
- Both priors are inactive near the lock. At the first perturbation (±34.7, ±80.9, ±37.0 for N = 4000), the smallest M(1) is 384 against a largest QsFutilityMargin of 197, and the largest M(1) is 616 against 1000. They matter only if a run moves far.
- They can be switched off in the config, and they are stated as priors in the unproven-claims list.

## 4. Interaction-aware schedule
1. **Joint perturbation.** Each batch draws one ±1 vector over all three scalars (stateless `seed:k`, as R9). Every gradient component is therefore evaluated at the other family's current value, and the run tracks the joint optimum. A coordinate-wise tuner stops at a conditional optimum instead. The synthetic interaction test shows both behaviours; first-order SPSA does not estimate cross terms explicitly.
2. **Per-family scaling.** c_end and r_end are set per scalar in its own units.
3. **Feasible perturbation, shrink first.** If θ ± c_k∘Δ, as engine values, would break a bound or C1/C3′, the whole perturbation shrinks by the largest common factor s ≤ 1, keeping the direction. Only if s < s_min = 0.25 is θ projected inward by s_min·c_k plus rounding slack. s and any projection are recorded per batch.
4. **No-information coordinates (E-006 fix).** When a scalar's rounded plus equals its rounded minus, that scalar gets no update.
5. **Update and projection.** `θ_i ← θ_i + (a_k/c_k)_i · R · Δ_i` with R = wins − losses of plus, as R9. Then θ is projected onto the feasible set.
6. **Diagnostics.** Constraint activity, s, and per-family drift are logged per batch.
7. **Run size (proposal for QA).** N = 4000 pairs, 4 pairs per batch, 10+0.1 (QA's combo29 gate time control), Threads 1, Hash 16, α 0.602, γ 0.101, A = 0.1·N, on the `8moves_v3` training partition only (`partition/`).

## 5. Staleness rule (enforced by the identity pin)
- The configuration is tuned for combo29 (E1284F7F), and the tuner refuses any other exe.
- If DR04, DR06, DR12 or any other qsearch or razoring change becomes the lock, the pin fails. The tuning and the confirmation must then be redone against the new parent.
- DR12 (stand-pat firmness) and DR04 (TT extension before qsearch) change the qsearch results that razoring consumes, so this rule covers both families.

## 6. Default-OFF engine control (`patches/tune_gate_after_combo29.patch`)
- Two independent compile-time switches, `FORGE_RAZOR_TUNE` and `FORGE_QS_TUNE` (default 0). With both at 0, the patched `uci.cpp` preprocesses to exactly the parent's text, and no option is registered.
- At 1 each registers a runtime spin option, `RazorTune` / `QsTune` (0..1, default 0), following the repo's `option.X=1` gate convention and R9Tune's semantics.
  - **Switch 0:** setoption on that family's existing names (RazorDepth/RazorBase/RazorMultiplier or QsFutilityMargin/QsSeeMargin) is remembered but not applied, and the search keeps the lock values captured at start. **Consequence, as with R9Tune:** while the switch is 0, `uci` still advertises the lock value as the default even after such a setoption.
  - **Switch 1:** applies the remembered values.
  - **Back to 0:** restores the lock values, a deterministic rollback. Each switch change prints one `info string` with the effective values.
- Only `uci.cpp` and a new header change; `search.cpp` is untouched.
- Tuning can drive the unmodified lock exe, because the scalars are already UCI options. The gate build is the delivery and rollback vehicle for the confirmation and a later merge. Its equivalence to the lock exe with the same values is evidenced by bench equality (BENCH.md).

## 7. Baseline snapshot and rollback
- **Baseline:** the lock values with both switches at 0, recorded with exe hashes in `configs/baseline_combo29.json`.
- **Baseline rollback:** `bin\rollback.ps1 -Baseline` prints the baseline line and writes nothing.
- **Run rollback:** `bin\rollback.ps1 -RunDir <dir> -ToSeq <n>` writes a new logged checkpoint with θ and k of checkpoint n.

## 8. Unproven (stated so nobody reads them as results)
- **Tuned values:** none exist. Tuning is PENDING QA EXECUTION.
- **C1 and C3′:** heuristic priors.
- **F1–F2 interaction:** code-level coupling only; no strength measurement.
- **Run-size adequacy:** synthetic estimate only.
- Any non-default value is a **SEARCH CHANGE, UNPROVEN**. It needs Code Review, then QA tuning, then the independent confirmation SPRT (`confirm/CONFIRM_PROTOCOL.md`).
