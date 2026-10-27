# S-IT idea sources

- **FIDE Laws of Chess, Article 9.2** (handbook.fide.com, chapter E012023). The game is drawn upon a correct
  claim by a player having the move when the same position, for at least the third time:
  - 9.2.1 is about to appear: the player writes the move on the scoresheet (it cannot be changed) and declares
    the intention to make it;
  - 9.2.2 has just appeared.
  - 9.2.3: positions are the same when the same player has the move, the same pieces occupy the same squares, and
    the possible moves are the same. En passant and castling rights that differ make the positions different.
  The engine already scores 9.2.2 (the current position repeated) as a draw. This job adds 9.2.1, the right of the
  side to move to claim before its next move.
- **GitHub issue #7** (this repository, "Forge experimental: intended-threefold (FIDE 9.2.1) missed by non-root
  qsearch"):
  - the reproduction: FEN `8/7k/8/8/8/8/8/K1R5 w - - 0 1`, positive history `a1a2 h7h8 a2a1 h8h7 a1a2 h7h8 a2a1`,
    control history `a1b1 h7h8 b1b2 h8h7 b2a2 h7h8 a2a1`;
  - the design: `Board::can_claim_threefold_by_next_move()`, genuine reversible history after the most recent
    null move, an exact duplicated key required before move generation (a bucket prefilter only skips work),
    legal non-pawn quiet moves checked by exact resulting key, the draw score as a floor in non-root search and
    quiescence, mate precedence, no TT score cutoffs or stores at claim-sensitive nodes.
  - The issue's code belongs to the unmerged run38-run49 lineage and was not applied. This is a fresh
    implementation on the AL1 s198 lock source (`d4f4312`), written from the issue text, behind a new UCI option.
- **Exact keys:** the resulting key is computed with the same Zobrist updates as `Board::make_move()` (side,
  castling rights, the en passant key only when a legal en passant capture exists). A make_move brute-force
  reference in the test checks it on 11,720 random shuffling positions.
- **fastchess-style tooling:** `nps_ab_opts.py` is opus-sol-S29's `nps_ab.py` with per-side UCI options added.
- **Code review of `fc3bd2a`** (2026-10-27; scratch evidence `F:\opus_scratch\review_sit`): seven findings (claim-check
  cost in shuffling positions, bare-king-only search fixtures, ungated regression checks, unchecked CI exit
  status, no hash move at claim nodes, fail-low bonus after the floor raised alpha, PV treatment of a collapsed
  window). The two material fixtures, the shuffling positions (`perf_claim_ab.py` cases `shuffle_hist`,
  `longwalk_hist`, `walk34_castle`) and the single-guard mutant edits (`review_sit/mut/make_single.py`,
  `make_qforced.py`, `make_mutant.py`) come from that review. The CPU-time probe in `perf_claim_ab.py` follows
  the review's `probe_claim_cost2.py` (GetProcessTimes between `readyok` and `bestmove`).
