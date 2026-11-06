# IDEA_SOURCE - NmpTtCaptureMin (deep-research card T04E-02)

- Idea: no null move when the TT move is a real capture of a valuable piece.
  - Form A: the victim's type is >= NmpTtCaptureMin (start 4 = rook or queen).
  - Variant B: `see_ge(tt_move, NmpTtCaptureSee)`. It is built in but not gated by this job.
- Sources of the idea (ideas only):
  - Reckless PR 671. There is **no licence file at the merge commit**, so nothing of it may be copied. Records: STC
    8+0.08 [0,3] +3.43 +- 2.31, n=22,374; LTC 40+0.4 [0,3] +3.67 +- 2.27, n=20,816.
  - Viridithas PR 412, read as ideas only. Record: LTC 40+0.4 [0,3] +1.88 +- 1.48, n=49,814.
  - Both used the UHO_Lichess_4852_v1 book with 1 thread. Their thresholds are unknown.
- No source of either engine was opened or copied for this port. The code is own code, written from the Forge spec
  below against the lock source.
- Safety detail from the spec's review: before the victim is read or `see_ge` is called, the TT move is checked with the
  lock's own `board.is_pseudo_legal` (the MovePicker's test). A colliding TT entry can carry another position's move.
- Spec: `opus_deepres/notes/SPEC_SEARCH2.md`, section "T04E-02 NmpTtCaptureMin", on branch `opus-deepres-20261104`
  (tip 2231439c, file md5 509b9e5a). Ranked RANKING_FINAL L8.
- Forge estimate: +1 to +3 Elo. This is **UNPROVEN**: no Forge game result exists.
- Licence: no third-party code, so no notice is needed.
