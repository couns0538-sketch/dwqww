# IDEA_SOURCE — Astra A1, UCI `HistRework` (UNPROVEN, no Elo claim)

Spec: Sol inventory `F:\opus_scratch\sol_inventory_17aa0cae.json`, `astra_jobs` id `A1` ("Correction-history /
history rework", tally 22; DR J5 + Strategist J6 + Strength S4). Code: written for this job on the AL1 s198 lock
tree. Ideas only; no code, comments, tables or tuned constants were copied from any engine.

## Public techniques used (ideas)
- **History heuristic and butterfly boards.**
  - Schaeffer's history heuristic and Hartmann's butterfly boards, a from x to table per colour.
  - https://www.chessprogramming.org/History_Heuristic, https://www.chessprogramming.org/Butterfly_Boards
- **History gravity** `h += b − h·|b|/D`. The lock already uses it for every history table (`apply_history`,
  D = 16384). A1 applies the same lock function to the new butterfly twin.
- **Threat-indexed quiet history.** Several modern open-source engines index the butterfly history by whether
  the from and to squares are attacked. A1 uses only the idea, with its own index definition below.
- **Lesser-attacker square sets.**
  - Stockfish's move picker computes squares threatened by pawns / by minors / by rooks to rank quiet moves
    (PR #3970, https://github.com/official-stockfish/Stockfish/pull/3970).
  - That PR is cited on Forge's own idea board as P14 (`7_history/ideas/FORGE_IDEA_BOARD.md`).
  - A1 uses only that square-set structure, as a learned-history **index**: no static bonus and no constants.
- **Correction history.** Static-eval correction tables keyed by position features are a public technique.
  The lock has pawn and material tables.
  - Gravity-style correction updates are also public; e.g. the Alexandria release notes: "Introduced
    gravity formula for correction history updates", https://github.com/PGG106/Alexandria/releases.
- **SplitMix64 finaliser.** Steele, Lea and Flood, "Fast splittable pseudorandom number generators" (2014),
  public-domain constants. Used to spread the non-pawn material signature over the 14 index bits.

## Own contributions (this job)
- **Lesser-attacker keying of the butterfly twin.** The threat bit depends on the mover's type:
  - pawn/knight/bishop: enemy pawns;
  - rook: + enemy minors;
  - queen: + enemy rooks;
  - king: none.
- **Blend.** A read blend of the lock table and the twin, in quarters, keeps the ±16384 scale of the lock's
  butterfly term.
- **Joint correction key.** Pawn placement (the lock's Zobrist pawn key) mixed with the non-pawn material
  signature (N/B/R/Q counts per colour).
  - It learns with a gravity update, because its sparse key aliases more than the lock's keys.
  - The lock's own correction tables keep their add-and-clamp rule.
- **Steps and limits.** Levels 1..3 = (50 %, 75 %, 100 %) threat-keyed read share and joint weight
  (50, 75, 100) x0.01. These are round values. The limits 16384 / 8192 and the grain 256 are the lock's.

## Forge history read before starting (and why A1 differs)
In the lock archive `D:\grok-pc-data\dwqww\.claude\worktrees\b\pkg\forge_LOCK_AL1_s198_FULL_20261026_1039`:
- `7_history/strength_packs/prior_corrhist/` and `7_history/cr_notes/CR_PASS_contcorr_h256e12.txt`
  (contcorr).
- `7_history/status/QUEUE_PENDING_rework_list_20261025_2005.md`:
  - NonPawnCorr / PawnHist (Pack A);
  - LmrCorrThreshold (P7);
  - S1 CorrGravity (`CorrUpdateMode`) and S3 ThreatHist (omni-s), gates G63/G64/G68, never run;
  - the omni-s patch `C:\Users\Administrator\grok-pc\forge_push\stage_omni_s\omni_s_h256.patch`, read only.
- `7_history/ideas/FORGE_IDEA_BOARD.md`: P14 ThreatOrderPct, parked; the "tactics loss, d22 +91 %" lesson.
- `7_history/TRIED_REJECTED_UNPROVEN.md`.

Branches:
- `opus-C2` REPORT.md (CorrHistPlus: continuation, minor-piece and per-colour non-pawn correction keys);
- `opus-O5` (CorrMargins);
- `opus-O8` (CorrExt).

Gate results read from `D:\grok-pc-data\forge_push\gate*\RESULT.md` (read only), all capped without an H1:

| gate | line | result |
|---|---|---|
| G87 | contcorr60 | +5.1 ± 8.6 |
| G34 | packa_w60 | +11.1 ± 7.9, LLR 2.48 |
| G38 | packa_w55 | +6.5 ± 8.2 |
| G37 | pawnhist_div4 | +4.6 ± 8.4 |

The item-by-item comparison is in `forge_astra_A1_design_20261027.md` section 3.
