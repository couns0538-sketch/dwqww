# REPORT — seat 07, job 24: `LmrSignedCorrection` is dead code

## What was asked / the answer / how sure

**Asked:** the area-7 read continued into the UCI option surface. Job 23 verified every boolean
option **by effect** and found five that changed nothing; four were explainable (they only matter on
a clock, or in a dead-material position), but **`LmrSignedCorrection`** should have mattered and did
not.

**Answer:** `LmrSignedCorrection` **can never have any effect.** Its adjustment arithmetic computes
`delta = correction_cp / 64` from a quantity that is mathematically bounded to `[-32, 32]`, so
`delta` is always **0**, and the function returns the untouched reduction. This is a real defect — an
advertised, tunable, gated option that is inert — though a *harmless* one: turning it on does not
make the engine worse, it does nothing.

**How sure:** proven two independent ways — an exhaustive enumeration of the whole reachable
`(correction, reduction)` space, and an end-to-end measurement showing identical node counts with the
option off and on at three searches. Plus a control showing the arithmetic *would* bite if the
divisor were smaller.

## The defect, exactly

    include/forge/search.hpp:389   constexpr int CorrectionGrain = 256;
    include/forge/search.hpp:390   constexpr int CorrectionLimit = 32 * CorrectionGrain;   // 8192
    include/forge/search.hpp:362   inline int apply_lmr_signed_correction(int reduction_plies, int correction_cp) {
    include/forge/search.hpp:363       int delta = correction_cp / 64;      // <-- always 0
    include/forge/search.hpp:366       const int adjusted = reduction_plies - delta;
    include/forge/search.hpp:367       return adjusted > 0 ? adjusted : 0;

    src/search.cpp:1226   return std::clamp(raw_eval + correction / CorrectionGrain, ...);
    src/search.cpp:2005   const int correction_cp = ss->static_eval - ss->raw_eval;

The chain: `corrected_eval` adds `correction / 256` to the raw eval, so
`correction_cp = static_eval - raw_eval = correction / 256`. With `correction` clamped to ±8192,
`correction_cp` is confined to **±32**. Then `32 / 64 == 0` in C++ integer division, for every
possible correction, positive or negative.

`src/search.cpp:2006` guards with `if (correction_cp != 0)`, so the call is sometimes made — but the
call cannot change `r`.

## Proof 1: exhaustive over the reachable space

job24/lmrdead.cpp copies the constants and the function verbatim and enumerates every reachable
`correction` in `[-8192, 8192]` against every reduction `0..30`:

    correction range [-8192, 8192]
    correction_cp range [-32, 32]
    values of correction giving a NONZERO delta: 0
    (reduction, correction) pairs where the reduction CHANGES: 0 of 507935

**Control:** changing only the divisor, `/64` → `/8`, gives

    values of correction giving a NONZERO delta: 12290
    (reduction, correction) pairs where the reduction CHANGES: 374845 of 507935

so the zero is a property of the chosen constant, not of my enumeration.

## Proof 2: end-to-end, the node count does not move

job23/run.log, cold process each time, startpos `go depth 12`:

    LmrSignedCorrection      false   56720  true   56720  NO EFFECT

and extended on purpose to deeper and non-starting positions:

    LmrSignedCorrection    midsgame d14 : false 149295 true 149295 NO EFFECT
    LmrSignedCorrection    stpos d16    : false 267839 true 267839 NO EFFECT

For contrast, options that *do* work in the same harness: `ThreatHistory` 56720→32209,
`EvasionOrdering` 56720→28490, `AspArmLate` 56720→29009, `SoundMatePruning` 56720→80946,
`EvalRule50Damp` 56720→62247, `UseNNUE` 68426→56720.

## A repair, as a text patch (NOT applied, and NOT honesty-neutral)

The obvious repair is to divide by a constant small enough to act — `/8` would make
`correction_cp = -4..4` give `delta = 0..1`. **I did not write that patch**, deliberately:

- any change to this function changes the search tree, so it would fail the brief's requirement that
  a patch keep the honesty numbers identical (312866 / 862329 / 3024920 / 4865609);
- a repair therefore needs a strength test against a real opponent, which is Fable/Opus's call, not a
  text patch I can validate here.

What I can say is that the *current* code is inert, so the tuner's reported optimum for
`LmrSignedCorrection` — whatever it is — was measured with an option that did nothing. Anyone tuning
it again should know that before spending games on it.

## Findings

**07-F2** in FINDINGS.md — my second real finding, and the first that is purely a defect rather than
a reporting issue.

## Suspicions, not proven

- Whether the intended divisor was `/8` or whether `correction_cp` was meant to be the raw
  `correction` (in which case `/64` would give a range of ±128, still mostly saturated by the ±1
  clamp). Both readings are guesses; I did not find a commit that shows the intent.
- `NullThreatVerify` also showed no effect at startpos d12 but **does** differ on a middlegame at d14
  (149295 → 149315) and at startpos d16 (267839 → 267855), so it is live — a depth/position
  coincidence, not a defect. Recorded so nobody re-reports it.

## What I did NOT do

- Did not fix `LmrSignedCorrection` (reasons above).
- Did not test `TmFinishIteration`, `TmNodeShare` or `DeadMaterial` further; the first two need a
  running clock (`time_managed_` is false for `go depth`) and `DeadMaterial` needs a drawn-material
  position, so their null result on this harness is expected rather than suspicious.

## What I am NOT sure about

- Whether some other caller reaches `apply_lmr_signed_correction` with a `correction_cp` outside the
  range I derived. `grep` shows exactly one call site, `search.cpp:2006`, fed by
  `ss->static_eval - ss->raw_eval` at line 2005, so the bound holds.

## Times

See job24/stamps.txt.
