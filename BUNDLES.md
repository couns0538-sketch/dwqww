# forge-bundle-int: crew bundle candidates B1-B4 and Astra N1 (status: UNPROVEN, no Elo claim)

Base: `opus-r3-stack` da15814 + `fable-review-buffix` (bad_captures_ sized to MoveList::Capacity, CR Fable R1 P1 PASS),
plus the FB2-J3 search options CorrHistV2 / LmrTableV2 / TtPruneV2 ported from `fable-fb2-j3` 33e295b.
Astra R2 adds default-OFF SmpV2 and TmSoftHardClamp independently of presets, plus
SingularV2 (spin default0), mutually exclusive with CorrExt. See the respective
astra2_evidence records and PORT_NOTES.md for source provenance and qualification.
Not included: FB2-J4 TimeManV2, fable-nnue-arch / NNUE v3.
Gate plan (crew vote): [0,10] nElo, 6000-game cap, at most 2 gates in parallel; QA builds/queues after CR_PASS.

## IDEA_SOURCE
Ideas only; no code copied from other engines. Code is Fable's FB2-J3 (this repo, fable-fb2-j3) re-hooked onto the R3
split search, and the Opus R3 options already on the base.
- CorrHistV2 (FB2-J3): continuation correction history. Static-eval correction keyed by (moved piece, to-square) of the
  previous move and of the move before it, on top of the lock's pawn / material correction. Common public idea
  (continuation correction history in modern engines); same family as Opus C2 CorrHistPlus=1.
- LmrTableV2 (FB2-J3): LMR reduction from a logistic model fitted by FB2-J3 to its own `bench 16` LMR decisions
  (coefficients in src/search/fb2.inc, unchanged from J3); the fitted history slope replaces the clamped history term.
- TtPruneV2 (FB2-J3): never prune the TT move in futility / history / SEE pruning; IIR also on cut nodes whose TT move
  failed low (upper bound, not tt_pv); RFP margin a third step cheaper when the opponent's eval fell on their move
  ("opponent worsening"); quiet futility margin +FutilityBase/2 when improving; history pruning at 3/4 of the threshold
  when not improving. All public ideas.
- CorrHistPlus (Opus C2), HistRework (Astra A1), CuckooRep (Opus): unchanged from opus-r3-stack.

## Presets (UCI `BundlePreset`, combo, default OFF)
`setoption name BundlePreset value Bx` writes exactly these seven options (and prints `info string BundlePreset Bx: ...`
for the gate log). Later individual setoptions override it (subject to the exclusivity rule). `OFF` resets all seven to
their defaults.

| preset | CorrHistPlus | HistRework | CuckooRep | CorrHistV2 | LmrTableV2 | TtPruneV2 | SingularV2 | equivalent setoption list |
|---|---|---|---|---|---|---|---|---|
| B1 | 1 | 2 | true | false | false | true | 0 | CorrHistPlus 1, HistRework 2, CuckooRep true, TtPruneV2 true |
| B2 | 0 | 0 | true | true | true | true | 0 | CorrHistV2 true, LmrTableV2 true, CuckooRep true, TtPruneV2 true |
| B3 | 1 | 0 | true | false | true | true | 0 | CorrHistPlus 1, LmrTableV2 true, CuckooRep true, TtPruneV2 true |
| B4 | 0 | 2 | true | true | false | true | 0 | CorrHistV2 true, HistRework 2, CuckooRep true, TtPruneV2 true |
| N1 | 4 | 0 | false | false | false | false | 1 | CorrHistPlus 4, SingularV2 1 |

N1 is refused while CorrExt is active, before any preset-owned option changes. Setting SingularV2 while CorrExt
is active, or setting CorrExt while SingularV2 is active, is likewise refused. They count extension budgets
differently. CorrHistPlus is a separate evaluation-correction feature and is compatible with SingularV2.
Every OFF/B1-B4 selection sets SingularV2 to 0; N1 enables only its two named features.

Assumptions for QA/CR to confirm or override (single constants in `forge::fb2::bundle_settings`, include/forge/fb2.hpp):
- "Opus CorrHist" = `CorrHistPlus=1` (the continuation-correction key set, C2's counterpart of CorrHistV2, per
  OPUS_VS_FABLE_REVIEW_20261028.md). CorrHistPlus is a bitmask (1 continuation, 2 minor-piece, 4 non-pawn); N1 uses =4; for other =4/=2/=7 combinations
  use the setoption list instead of a preset.
- "HistRework" in B4 = level 2 (same as B1). Equivalent lists: B4 with another level = `BundlePreset B4` + `HistRework n`.

## CorrHist exclusivity rule
CorrHistPlus (Opus) and CorrHistV2 (Fable) both read and update the shared pawn / material correction tables, so they
are **mutually exclusive options**, enforced twice:
1. UCI: `CorrHistV2 true` is refused while CorrHistPlus != 0 (`info string CorrHistV2 refused: ...`), and a nonzero
   `CorrHistPlus` is refused while CorrHistV2 is on (`info string CorrHistPlus refused: ...`). The value is unchanged.
   `CorrHistPlus 0` is always accepted. No preset sets both.
2. Search snapshot: `fb2::effective(requested, corr_hist_plus, corr_ext)` drops CorrHistV2 whenever CorrHistPlus != 0
   (CorrHistPlus wins), so no caller (UCI, bench, datagen, tests) can run both in one search.
The tables that are not shared are separate: CorrHistV2's continuation table is `ThreadData::continuation_correction_`,
CorrHistPlus's are `corrplus::Tables`; neither option touches the other's table.
Checked: `CorrHistPlus 1` then `CorrHistV2 true` benches exactly as `CorrHistPlus 1` alone (318363 at d11), and
`CorrHistV2 true` then `CorrHistPlus 1` exactly as CorrHistV2 alone (282082 at d11); forge_fb2_bundle_tests section 5.

## Threading: one snapshot per search (CR Fable R1 J3 LOW note)
`fb2::requested` is written only by the UCI thread (setoption stops and joins the search first). Every search, from
`go`, `bench` and `forge datagen` alike, enters through `Searcher::search`, which copies
`fb2::effective(fb2::requested, CorrHistPlus, CorrExt)` into `SearchLimits::fb2` once, before any helper starts (a caller's own
value is overwritten). Each Worker copies it into its member `fb2_` at the start of `Worker::search`; every hook
reads only `fb2_`. No search code reads a shared fb2 global. The other bundle options (CorrHistPlus, HistRework,
CuckooRep) are the R3 stack's existing globals, unchanged, and are protected by the same stop-before-setoption rule.

## Hooks (all search instances)
The hooks are runtime branches on `fb2_` in alphabeta.inc / qsearch.inc, so every instance gets them: default,
CorrMargins, CorrExt, CM+CE and the four CuckooRep instances, plus the FORGE_PROF duplicates of the pruning blocks.
In the CorrMargins instance, TtPruneV2's improving term is added to the corr_margins futility margin and the worsening
term to its RFP margin (J3 had no such instance). CorrHistV2 includes HistRework's joint term when HistRework is on (B4).

## Bench (box: g++-14 Release, -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256;
Threads 1, Hash 16, OwnBook false; FMA 0)
| config | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|
| OFF (= AL1 s198) | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| B1 | 280182 | 758456 | 3357587 | 11208630 | 20560049 |
| B2 | 255626 | 564279 | 1590154 | 7437797 | 12514517 |
| B3 | 211646 | 463170 | 1716168 | 5392451 | 9245839 |
| B4 | 276131 | 985600 | 2726927 | 16708424 | 34452707 |
| B2 then OFF | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| CorrHistV2 only | 282082 | 1001737 | 3236395 | 11950628 | 23775246 |
| LmrTableV2 only | 245666 | 494753 | 1430026 | 4835472 | 12933240 |
| TtPruneV2 only | 309157 | 736967 | 2960397 | 12062561 | 34293668 |
perft5 startpos 4865609, kiwipete 193690690 (uci_check.py --full: ALL OK).
Node counts are not strength; all bundles UNPROVEN until gated.

## Known deviations
- OFF nodes are exact, but the OFF binary is not byte-identical to opus-r3-stack (new runtime branches); OFF NPS may
  differ slightly (not measured; QA's speed check decides).
- Box ctest, pinned to one core (taskset -c 5): forge_tests fails only the 4 known lines; forge_smp_tests fails
  "SmpExactNodes: overshoot bounded by the publish cadence" (6-8 rounds), which the opus-r3-stack base build fails the
  same way under the same single-core pin (timing artifact, SmpExactNodes default off). CI is the reference.
- forge_nnue_v3_tests does not exist on this branch (NNUE v3 / fable-nnue-arch not merged).

## Astra R2 B5 qualification
The earlier bench table above records the original bundle, not a new N1 strength result. Current B5 commands,
source pins and raw results are in `astra2_evidence/B5/`; `PORT_NOTES.md` inventories the port and its interactions.
N1 remains a candidate requiring independent equal-time strength gating. No Elo improvement is claimed.
