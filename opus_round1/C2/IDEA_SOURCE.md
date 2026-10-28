# C2 IDEA_SOURCE — extended correction history (UCI `CorrHistPlus`)

Ideas only. No code, tables or constants were copied from any engine; the implementation
(`include/forge/correction_plus.hpp`, `src/search/correction_plus.inc`, the hooks in
`src/search/evaluation.inc`) is our own, written against Forge's existing pawn/material correction.

| idea used | public source (concept) | how Forge uses it (own design) |
|---|---|---|
| Static-evaluation correction history in general: learn search score minus static eval in tables keyed by a board feature and add the entry to later static evals | Chess Programming Wiki, "Static Evaluation Correction History", https://www.chessprogramming.org/Static_Evaluation_Correction_History (first introduced in Caissa, Oct 2023, by Witek902) | already in the AL1 s198 lock (pawn and material tables); CorrHistPlus keeps the lock's residual / depth-weight rule and update conditions and adds keys |
| Several feature keys blended into one correction | Caissa (Michał Witanowski, MIT), https://github.com/Witek902/Caissa (pawn and non-pawn correction tables; release notes mention a secondary continuation correction history); Stockfish (GPL-3), https://github.com/official-stockfish/Stockfish (`src/search.cpp`, `src/position.cpp`: pawn, minor-piece, per-colour non-pawn and continuation correction entries) — read as concept descriptions only | three new keys, one option bit each so each can be gated alone; weighted (x0.01 tunables) and summed, the sum clamped to +/-64 cp |
| Minor-piece key = king, knights and bishops | CPW page above ("Minor Piece Correction History ... location of King, Knights, and Bishops. Introduced by mcthouacbb in Sirius"); blog "Static Evaluation Correction History", https://int0x80.ca/posts/chess-engines/19-corrhist (notes that the king gains from being included) | bit 2: hash of the WN, WB, BN, BB, WK, BK bitboards, computed on demand |
| Per-side non-pawn key | CPW page above; Stockfish source (concept) | bit 4: one key per colour over that side's N, B, R, Q, K bitboards; both tables read at every node |
| Continuation correction keyed by the previous two moves | blog above ("a corrhist table indexed by the past 2 played moves"); Caissa release notes; Stockfish source (concept) | bit 1: directly indexed [side to move][our piece type][to][their piece type][to] (294 912 int16 entries); no key next to the root or after a null move |
| Gravity / decay of history entries (entry += bonus - entry * abs(bonus) / limit) | common history-table practice; Forge itself already uses it for move-ordering history (`apply_history` in include/forge/history.hpp) | the new entries add the lock's residual step and decay by entry * abs(step) / 8192, then clamp to +/-8192 |
| Hash finaliser for the on-demand keys | SplitMix64 output function, Sebastiano Vigna, public domain, https://prng.di.unimi.it/splitmix64.c | `corrplus::avalanche`; the per-piece multipliers are our own random odd 64-bit draw |
| Division by a constant as multiply + shift (exact) | T. Granlund, P. Montgomery, "Division by Invariant Integers using Multiplication", PLDI 1994 | `corrplus::div100` and `div_pow2`, because the cold (size-optimised) glue would otherwise use idiv; exact for every 32-bit input (swept) |

Forge history consulted (not code sources): `7_history/strength_packs/prior_corrhist/` (an earlier
single-previous-move "contcorr" on h256_e12, CR PASS, UNPROVEN) and `7_history/ideas/FORGE_IDEA_BOARD.md`
P1 (non-pawn correction, failed the crew's node screen on h256 at weight 100). CorrHistPlus is a new
implementation: the continuation key uses the previous TWO moves, the keys are computed from bitboards
(no Board change) and each key has its own option bit.

No Elo claim. All three keys are UNPROVEN until QA gates them (G-B1 continuation, G-B2 minor piece;
the non-pawn bit has no gate ID in the test plan yet).
