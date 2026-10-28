# OPUS R3 report (job pack R3, Forge AL1 s198) — IN PROGRESS

Branch `opus-r3-stack` (base `d4f4312`). Machine exclusive: no (gates, self-play and NNUE training ran
throughout; my work at nice 19, one process at a time). No Elo claims: no gate was run.

## Status

| job | state | where |
|---|---|---|
| R3-1 integration stack | IN PROGRESS: all O/C branches merged; opus-sol engine features next; then the ON/OFF self-play checks | `opus-r3-stack`, `opus_r3/R3-1/` |
| R3-2 interaction matrix | not started | |
| R3-3 gate proposals | not started | `F:\opus_scratch\r3\GATE_PROPOSALS.md` |
| R3-4 SPSA tool | not started | |
| R3-5 regression test suite | not started | |
| R3-6 Lazy SMP scaling | not started | |

## R3-1 so far (numbers from `F:\opus_scratch\r3\logs`)
- Base: `d4f4312` fast-forwarded to `opus-O3` (`c7eb247`: the no-op module split every O/C branch is built on,
  plus the CI baseline `0d99f02`). Then merged: O1-LTT (contains O1), C1, C2, C3, O7 (contains C4 and O6), C5, O4,
  O5, O8, C6, O2, and the evidence-only heads of O1 and O6. One merge commit per branch.
- After every merge: PC-recipe build (0 warnings, FMA 0) and bench d11/13/16 + perft5 + kiwipete = lock: ALL OK.
- Semantic merges (details in the merge commit messages):
  - **NNUE v2 options** (C4 king buckets, C5 output buckets, O6 threats, O7 pawn pairs, O4 PureNnue): one combined
    selection and fail-loud rule; each branch's test phrases kept. Tools (replica writer, trainer copy,
    v2_parity) support the flags together.
  - **Search instances** (O5 CorrMargins, O8 CorrExt, C6 CuckooRep each compiled their own copy of
    alphabeta.inc): unified into one macro scheme with one instance per option combination (8 alpha-beta, 2
    quiescence). Each option alone runs its branch's instance: the branches' ON pins reproduce exactly
    (CorrMargins d11 343365 d13 858019 d16 2522546 d20 12894582; CorrExt 312961 / 838790 / 2891507 / 12313394;
    CuckooRep 324211 / 790682 / 3148570).
  - **O2** (no option on its branch) is behind the new build switch `FORGE_NNUE_O2` (default off). Switch off:
    exe byte-identical to the pre-O2 stack exe (PE timestamp aside); on: byte-identical to the merged O2 exe.

## Left
- R3-1: port the opus-sol engine features (S04fix, S08fix, S11, S12, S13, S14, S29, S32, S37, S41, A1, S-A2,
  S-A4, S-IT) onto the module layout; full identity (d20/d22), CMake + CTest; 500 self-games per option ON
  alone and all ON with an illegal-move / double-bestmove checker; CI.
- R3-2 to R3-6.
