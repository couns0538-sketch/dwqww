# CONFIRM_PROTOCOL: independent confirmation of the joint razoring + qsearch candidate (pre-registered)

Frozen in this pack **before any fitting**: no tuning game has been played by anyone for this configuration. Nothing in this file is a result. The tuning itself is **PENDING QA EXECUTION**.

## 1. What is confirmed
- **The candidate** is produced by `select_candidate.py` from a **COMPLETE** training run of `configs/joint_razor_qs.json` (N = 16000 pairs; the run size was set from the synthetic qualification before any game, `PLAN.md` §4.7).
  - Rule: the final θ of the run, as the engine integers recorded in its `complete` record. Bounds and C1/C3′ are re-checked.
  - No intermediate checkpoint may be chosen, and nothing seen in a screen or holdout may influence the choice.
  - The spec is hashed (`spec_sha256`).
- **Tuned options:** RazorBase, RazorMultiplier, QsFutilityMargin. RazorDepth = 2 and QsSeeMargin = 40 stay at their lock values.

## 2. Engines and option lines
- **Baseline and rollback artifact:** the lock exe `forge_clang_combo29_trial_w6.exe`, SHA256 e1284f7f…802e. It gets only Threads 1, Hash 16 and OwnBook false, which is QA's base rule.
- **Candidate, preferred:** the gate build of `patches/tune_gate_after_combo29.patch` (`-DFORGE_RAZOR_TUNE=1 -DFORGE_QS_TUNE=1`, QA's PC rebuild after Code Review) with `option.RazorTune=1 option.QsTune=1 option.RazorBase=<v> option.RazorMultiplier=<v> option.QsFutilityMargin=<v>`.
- **Candidate, equivalent:** the lock exe with only the three value options. The equivalence is evidenced by bench equality in `BENCH.md`.
- All options are advertised by `uci`, so QA's advertised-option check applies. This avoids the 6.x A/A trap, where fastchess drops unadvertised options.

## 3. Openings (holdout, no overlap with training)
- **Primary (QA's runner):** `uho_lichess_v1`, `C:\Users\Administrator\grok-pc\coder-fuzz\UHO_Lichess_4852_v1.epd`, SHA256 7A7F6470…5644A.
  - Played with `order=random`, a QA-assigned `-srand` that must differ from the tuning seed 20261110, and an `openings_start` clear of the in-flight ranges 1507501–1560001 and 1700001–1705001. This pack proposes 1800001.
  - Tuning read only `8moves_v3`'s training partition (`partition/PARTITION_MANIFEST.json`). Compared on pieces, side and castling, only 50 of 2,632,036 UHO lines match a training position, so a 2,500-opening confirm is expected to meet about 0.05 of them.
  - **Leakage audit, mandatory:** after the gate, run `bin\confirm.ps1 -Command audit -Protocol <p> -Candidate <c> -Pgn <gate.pgn>`. It recomputes the result with and without pairs whose start position is a training or screen position.
- **Alternative (this pack's runner):** holdout group G1 of `8moves_v3`: 2,408 positions, `holdout_G1.pgn`, SHA256 cfe81bf7…, regenerated and verified by `partition/opening_partition.py`. QA would have to add it as a book key, so this route needs a QA decision.
  - Each pair uses one opening, so G1 allows at most 2,408 pairs (4,816 games) without replaying an opening. The runner refuses a larger cap in every mode, including dry-run (exit 10), unless the protocol sets `allow_opening_reuse`, which needs a written QA decision. Example: `configs/confirm_protocol_G1_example.json` (cap 4,816).
  - At that cap the synthetic power is about that of QA's 5,000-game cap (table below), so G1 alone decides only large effects. The 40,000-game cap needs the UHO route.
- **Use once.** One confirmation per holdout group, ever: the registry refuses a second run, whether for another candidate or a re-run of the same one. G2 and G3 are reserved for a protocol change that QA approves in writing before any game.

## 4. Statistics and stop rule (fixed)
- Pentanomial normalized-Elo SPRT, H0: 0, H1: 5, α = β = 0.05. LLR bounds ±2.944, which is QA's combo29 convention.
- **Game cap: 40,000 recommended. QA's standard 5,000 is allowed but almost never decides at tuning-sized effects.** Synthetic operating characteristics, from `POWER_TABLE*.json` (draw rate 0.6, 200–300 runs; model effects, not measurements):

| model nElo | P(H1), cap 5,000 | P(H1), cap 40,000 | mean games, cap 40,000 |
|---|---|---|---|
| 0 | 0.003 | 0.010 | 22,055 |
| 2.5 | 0.003 | 0.370 | 28,467 |
| 5 | 0.027 | 0.840 | 22,396 |
| 7.5 | 0.037 | 0.980 | 14,306 |
| 10 | 0.110 | 1.000 | 10,157 |
| 20 | 0.800 | 1.000 | 4,068 |

- **Verdicts:**
  - **H1 accepted:** the candidate passed this confirm. QA's rule then requires the longer-TC confirm (40+0.4) before any lock consideration.
  - **H0 accepted:** rejected; roll back to the baseline.
  - **Cap without a decision:** **no claim**; roll back to the baseline.
- A crash, time loss or illegal move invalidates the run. QA reruns with a fresh srand under its own rules; the new srand is reported and the holdout stays single-use.
- No bound decision is evaluated before 50 pairs in this pack's recomputation (audit rule against degenerate early variance).
- **A claim is made only if** QA's verdict is H1, this pack's independent recomputation of the raw pairs agrees, and the leakage audit finds ≤ 1% of pairs on training or screen positions.

## 5. Rollback
- **Lock exe:** use it with no options.
- **Gate exe:** `option.RazorTune=0 option.QsTune=0` restores the lock values whatever else is set.
- **Tuning run:** `bin\rollback.ps1 -RunDir <run> -ToCkpt <n>`.

See `ROLLBACK.md`.

## 6. Controls that this pack already passed (synthetic, no Elo; `TESTS.md`)
- **A/A, true nElo 0:** H1 in 0 of 300 runs.
- **Fake optimizer:** best of 20 equal candidates, which looks better in training; H1 in 0 of 300 runs.
- **Positive control, nElo 25:** H1 in 96–97% (cap 5,000).
- **Refusals and recovery:** holdout reuse and peeking refused; changed exe or protocol refused; a cap needing more pairs than the holdout has openings refused; corrupt checkpoint, duplicate and incomplete pairs refused; crash at 7 boundaries recovered with identical records; the leakage audit finds a planted training position.
