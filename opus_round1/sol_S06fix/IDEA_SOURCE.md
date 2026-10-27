# IDEA_SOURCE — S06fix

- Base tool: Sol's S06 offline gate miner (`forge_sol_S06_{gatelog_miner,statistics,pgn,logs}_20261026.py`, branch
  `forge/sol-pack31-20261025` @ 17aa0cae); copied to v2 files and changed only as listed in README.md. Sol's own
  idea sources are in his S06 README (QA count/moment formulas, `pgn_stats.py`, `run_hourly_sprt.py`).
- Fix-up items: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, S06-1, S06-2, S06-3.
- Exact LLR: fastchess v1.8.2-alpha `app/src/matchmaking/sprt/sprt.cpp` (https://github.com/Disservin/fastchess,
  tag `v1.8.2-alpha`, file sha256 `cfca385c54c64b70300713c19fc7bfff131b7daddd7cac116871b134634c2d1f`; MIT License,
  Copyright (c) 2023 disservin). `fastchess_llr` and `_itp` are a Python translation of `SPRT::getLLR` (pentanomial),
  `getLLR_normalized`, `getLLR_logistic` and `itp`. The math behind it: M. Van den Bergh, "Comments on normalized
  Elo" (section 4.1) and "Comparing the approximations for the generalized log likelihood ratio of a multinomial
  distribution" (cited in that file); ITP root finder: Oliveira and Takahashi, ACM TOMS 47(1), 2021.
- Converged reference: `opus_round1/sol_S44/forge_sol_S44_elo_vs_epochs.py` (`_secular`, `_mle_tvalue`,
  `exact_llr`; Opus S44, validated on the PC gates), translated from numpy to the standard library.
- Display formulas (Elo +/- from the transformed 95% score interval, nElo +/-, LOS): fastchess output
  conventions, checked against 44 PC RESULT.md files (`.claude/skills/forge-gate-stats`).
- Book-move openings, orphan games and finished-game pairing: observed fastchess 1.8.2 gate output on the PC
  (gate38, G120 copies); original code.
- No engine code, tuned constant or code from another chess engine is used.
