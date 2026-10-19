# Forge 6.4.2 underpromotion candidate

This candidate fixes a move-completeness error: ordinary main search obtained
promotions through noisy generation, which emitted queens only, while its
quiet stage excluded all promotions. Rook, bishop and knight promotions could
therefore disappear from search unless already supplied by TT or check-evasion
handling. Noisy generation now emits all four choices for either color,
including captures. Evaluation, NNUE weights, SEE, TT policy and search tuning
are unchanged from the clock/stalemate candidate.

## Concrete behavior and checks

On `8/k1P5/2K5/8/8/8/8/8 w - - 0 1`, queen promotion stalemates,
whereas rook promotion retains a winning king-and-rook ending. With the root
restricted to the four promotion choices, old 6.4.1 selects `c7c8q` at 0 cp;
6.4.2 selects `c7c8r` at +467 cp. Both Linux and Windows-under-Wine reproduce
this and its color mirror. Full transcripts and the exact restriction are
in `tests/promotion-choice-comparison.json` and adjacent logs. Without the
restriction, the old Linux engine instead chooses `c6d6` at +379; the new
engine chooses the rook at +467. Do not describe that unrestricted old move
as a demonstrated drawn game.

Tests-first evidence: the new core checks produced **23 expected failures**
on the unchanged engine. The process UCI check also rejected its fallback
rook move because no searched PV existed. After the fix, all five Linux
CTest suites pass, including 15 existing match-tool tests and 19 Windows
validation-runner safety tests. Windows core, UCI and pondering checks pass
under Wine 10. No physical Ryzen or native Windows run was performed here.

The core checks cover quiet/capture promotions for both colors; cold forced
Q/R/B/N searches require a real child/PV; cold unrestricted searches choose
the winning rook. An independent source review found no actionable issue.
Final Linux and Windows binaries pass the emitted AVX2 arithmetic check.
The depth-11 signatures are **419798 Linux nodes / 351063 Windows nodes**.
An initial argv-style bench invocation only reached UCI EOF and emitted
nothing; empty attempt logs are preserved, followed by the correct stdin
`bench 11` checks. Timing/NPS in these signatures is not a speed comparison.

## Strength status

There is **no accepted Elo gain for 6.4.2**. The preceding 6.4.1 candidate's
frozen original-ZIP comparison completed 178 normal games and accepted H0
for [0,+20] at 10,000 nodes per move. That result is preserved under
`../clock-safety-9850x3d/`; it cannot be transferred to this changed candidate
or interpreted as an equal-clock result. Full-strength Stockfish superiority
is unproven.

The native Windows bundle is intended to measure complete delivered versions
on the user's Ryzen 7 9850X3D: exact original 6.4 Windows znver4 release
versus this Zen 5 candidate. Compiler/target differences are part of that
comparison. Its portable runner requires deterministic A/A calibration, a
clean paired timed pilot, then one serial native paired SPRT [0,+5], alpha
and beta .05, capped at 5000 pairs. It checks frozen hashes, complete normal
pairs, exact opening prefix, native counts and an independently computed
logistic likelihood. H1 is evidence under that protocol, not proof of gain
at least five Elo or superiority over Stockfish. Wine supports readiness
only; timed testing is deliberately gated to native Windows.
