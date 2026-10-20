# Bounded SEE coverage followup

Executed only the existing immutable prototype baseline/candidate diagnostics;
no source, build, compiler, production, Git or original-prototype edits.
The fixed corpus contains12 legal initial moves:10 targeted controls and two
separately classified inherited recapture-promotion limitations. Inputs and
complete python-chess1.11.2 same-target capture trees were frozen before either
diagnostic ran. Both executables returned0 and retained their original hashes.

All10 targeted controls match the candidate's exact exchange value and all20
available `see_ge` thresholds. First legal recapture sets and initial legality
also match. Nine of these controls disagree with the baseline and are corrected;
the legal king fallback remains correct. The executable has a fixed threshold
grid; this followup does not add new adjacent-threshold brackets or recompile it.

| Controls | Baseline | Candidate / legal oracle |
|---|---:|---:|
| Mirrored EP removing two rank blockers opens pin | 0 | +100 |
| Mirrored legal ordinary quiet move with pinned recapturer | -900 | 0 |
| Mirrored three-recapture exchange releases pin midline | -600 | -200 |
| All non-kings rejected, legal king recapture remains | -800 | -800 |
| All non-kings rejected, pinned geometric defender forbids king | -800 | +100 |
| Initial capture evades check, recapturer remains pinned | -100 | +500 |
| Initial knight move reveals unrelated bishop check | -200 | +100 |

`mechanism-checks.json` independently documents the opened ray, initial and
released pin states, three legal recaptures, initial check evasion, actual
discovered bishop checker, and both king outcomes. The three-recapture white
line is Qd4xd1 Qd8xd1 Re1xd1 Ne3xd1; Ne3 cannot recapture on the first ply,
but can after the pinning rook leaves e1. In the king control, pinned Nh3
continues to attack g5 geometrically and forbids Kf6xg5.

The reviewer-provided recapture-promotion limitation was actually reproduced
for both colors, separately from the10 green controls. For
`7k/8/8/8/8/1Q5K/p7/1r6 w - - 0 1`, Qb3xb1, both builds report -400 while the
promotion-aware legal oracle reports -1200. Both answer `see_ge(-500)==true`
although the oracle answer is false. The black mirror does the same. These
are preserved correctness mismatches, not passing exact-SEE controls.
`known-limitation.json` records them explicitly. No repair is attempted here.

One invalid authored discovered-check attempt was rejected by python-chess
before any engine ran: a queen used as the blocking piece already attacked the
black king. The original script, input validity report, exception and rc1 are
preserved. Replacing it with a knight, its legal capture target and the unrelated
recapturer produces the intended discovered-check mechanism; this correction
was made before any diagnostic outcomes were seen.

`record.json` preserves all commands, return codes, thresholds, fixture hashes,
both executable hashes before/after and every mismatch. Both raw stdout/stderr
files are present. Total engine execution was0.231seconds for budget accounting
only; there is no performance or strength inference. Full candidate gates and
unmeasured hot-path cost remain outside this followup.
