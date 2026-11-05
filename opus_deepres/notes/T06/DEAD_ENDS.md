# T06 dead ends (one line each, with the reason)

- Asymmetric optimism (separate root-side / opponent strengths; Stockfish 908811c ~+1.46 STC / ~+1.76 LTC): removed two weeks later by f9d8717 "Symmetrize optimism" at no loss (non-regression STC 271,104 / LTC 198,954 games) - no card.
- DrawJitter gate (E3 option, ungated): Stockfish draw randomisation 97d2cc9 STC ~+0.71 / LTC ~+0.58 (VLTC ~+2.49), 770c8d9 ~+1.04 / ~+0.30 (VLTC ~+1.97): under +1 at Forge's 10+0.1 gate TC - dropped (free to gate if CPU is idle; no card).
- Null moves not advancing the rule50 clock (Stockfish 7684b6e ~+0.98, then ~-0.11; lock board.cpp:823-835 advances it): under +1 - dropped.
- Drawish / opposite-bishop scaling of the residual net: ruled out by the lock FORGE_IDEA_BOARD (double count, per the E3 README) - not proposed.
- Classical "winnable / dynamic complexity" HCE terms (Stockfish 6d0eabd, 1d3efff): an HCE change under a residual net needs a retrain, not a post-net transform - out of track.
- Lazy eval / hybrid thresholds (Stockfish 3dca13a, 16b4578, b25d68f, 7831131): speed policy; Forge's 768x256 residual is cheap next to its HCE, so skipping it saves little (own estimate under +1 % nps) - dropped (T05 territory).
- Caissa soft saturation of large evals and post-net castling-rights bonus: no logged Elo in Caissa's commit log - no card.
- Patricia sacrifice-path style bonus and root-relative anti-trade-down cut: style terms; only the combined material-scale rewrite has a number (PR 135, vs its own old form) - folded into T06-01, no own card.
