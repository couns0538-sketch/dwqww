# Lichess input review — implemented and tested, UNPROVEN

Current status at 07:28 UTC: the full corpus admission union closed before any
records.py edit. The repair below is implemented. Twelve selected RED failures
were preserved, followed by 116 affected test passes and 542 full-suite passes
plus 11 subtests. Focused independent recheck approved broader verification.
The castling RED cases showed accepted but unnormalized aliases, not rejected
castling. The old four-field case already rejected input; its diagnostic is now
explicit. Remaining text describes the original finding and chosen design.
Fresh legacy/native-admission/v8 handoff proofs remain pending. No Lichess data
was added to either recipe, and four-field input remains blocked.

The official evaluation dump has four-field FENs: it omits both move counters.
Its PV moves use UCI_Chess960 notation. Evaluation entries are ordered by PV
count; Lichess recommends choosing the deepest entry and then its first PV.
These details were checked against the [official export format](https://database.lichess.org/#evals)
on 2026-11-03. The current recipes contain zero Lichess rows.

The existing six-field synthetic tests did not expose two parser defects:
selection always used evals[0], and castling was interpreted as ordinary UCI
without converting king-to-rook notation. The running corpus admission audit
pins records.py, so repairs must wait until both partitions finish. Planned
repair: deepest known depth, earliest entry on ties, first PV only; strict score
and depth types; legal castling decoding; retained selection/move provenance.
Missing depth remains explicitly unknown and ranks below any known depth.

Four-field input remains **BLOCKED**. Appending `0 1` would manufacture known
ply and rule-50 state. The existing native consumer needs a complete FEN and
integer ply, and the converter's game-over test depends on counters. The focused
review confirmed that a partial-state schema would require explicit downstream
admission guards, coverage changes and metadata-preserving publication. That
is not part of this repair. Use only six-field records with genuinely known
counters; never append invented clocks to make the public dump pass.

The parser will give an explicit missing-counter diagnostic. A future partial
state import needs its own schema/consumer review before it can become training
input. Neither licensing nor successful board-only parsing supplies those clocks.

Score orientation is confirmed White-relative in Lichess's own
[BSON reader](https://github.com/lichess-org/lila/blob/master/modules/evalCache/src/main/BSONHandlers.scala)
and [JSON serializer](https://github.com/lichess-org/lila/blob/master/modules/evalCache/src/main/JsonView.scala).
Inspected Git blobs were fa305ab668701175cf6127fc53cd060cf2a9c08c and
378df41a4212ba60faf8f4730e2672173c3a43f8 respectively. The
[exporter](https://github.com/lichess-org/database/blob/master/src/main/scala/Evals.scala),
blob f399a632da4aa42b737d1251cd044f45fa612bd8, writes stored evaluations for
standard chess. These AGPL sources were inspected for semantics only; no code
was copied. Unknown game results stay null with has_result=false and lambda=1.

The installed python-chess 0.31.4
[parse_uci API](https://python-chess.readthedocs.io/en/v0.31.4/core.html#chess.Board.parse_uci)
accepts both move notations and can also return a null move. The repair must
reject null explicitly and keep standard-chess board rules; UCI_Chess960 move
notation alone does not make the position a Chess960 game.

Required regressions cover four-field rejection, unchanged original full FEN,
both colors and sides of castling, missing/blocked/attacked castling rights,
null moves, later deeper evaluations, deterministic depth ties, unknown depth,
empty PVs, noninteger scores/depths, ambiguous cp+mate, White/Black score signs,
unknown outcomes, normalized provenance tampering, filter behavior and converter
sidecar alignment. All existing self-play and legacy-byte proofs must remain
valid. This document is a design finding, not a claim that the repair has run.
