# IDEA_SOURCE - CutNoTtLmr (deep-research card T04D-01)

- Idea: a late move at a cut node whose TT probe gave no move is reduced one more ply by LMR, on top of the existing
  cut-node term (`if (cut_node) r += 2;`).
- Source of the idea: Stockfish commit 9cc15b3, GPL-3.0. Only the idea is used. The deep-research job read the
  commit's title, message and fishtest records:
  - STC 10+0.1 [0,2]: +2.72 +- 1.74, n=42,304, LLR 2.93;
  - LTC 60+0.6 [0.5,2.5]: +3.35 +- 1.81, n=32,334, LLR 2.95;
  - book UHO_Lichess_4852_v1, 1 thread.
- No Stockfish source was opened or copied for this port. The code is own code, written from the Forge spec below
  against the lock source.
- Spec: `opus_deepres/notes/SPEC_SEARCH2.md`, section "T04D-01 CutNoTtLmr", on branch `opus-deepres-20261104`
  (tip 2231439c, file md5 509b9e5a). Ranked RANKING_FINAL L5. The one-ply amount (CutNoTtLmr = 1) is the card's own.
- Forge estimate: 0 to +3 Elo at STC. This is **UNPROVEN**: no Forge game result exists.
- Licence: no third-party code, so no notice is needed. GPL / AGPL engines are ideas only (owner rule).
