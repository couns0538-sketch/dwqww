# IDEA_SOURCE - TtCutNodeDepth (deep-research card T04D-02)

- Idea: at shallow depth (depth <= TtCutNodeDepth), a main-search TT cutoff is also required to match the node type.
  - Form 1 (the source's stated half): a cutoff at >= beta needs a cut node.
  - Form 2 (the card's two-sided reading): `(tt_score >= beta) == cut_node`.
  - A refused cutoff searches the node normally. qsearch's TT cutoff is not changed.
- Source of the idea: Stockfish commit 43e100a, GPL-3.0, plus its follow-up a4edacb (depth limit only). Only the idea is
  used. The deep-research job read the title, message, PR text and fishtest records:
  - 43e100a: STC 10+0.1 [0,2] +2.72 +- 1.72, n=41,184; LTC 60+0.6 [0.5,2.5] +1.02 +- 0.62, n=270,888;
  - a4edacb: STC +1.63 +- 1.23, n=83,648; LTC +1.96 +- 1.25, n=68,160;
  - book UHO_Lichess_4852_v1, 1 thread. Their depth limits are unknown.
- No Stockfish source was opened or copied for this port. The code is own code, written from the Forge spec below
  against the lock source.
- Spec: `opus_deepres/notes/SPEC_SEARCH2.md`, section "T04D-02 TtCutNodeDepth", on branch `opus-deepres-20261104`
  (tip 2231439c, file md5 509b9e5a). Ranked RANKING_FINAL L6. The start value 6 is the card's own.
- Forge estimate: 0 to +3 Elo at STC. This is **UNPROVEN**: no Forge game result exists.
- Licence: no third-party code, so no notice is needed. GPL / AGPL engines are ideas only (owner rule).
