# S42 Higher-variance opening book study — DONE (proposal + stats only; box sample UNVERIFIED by instruction)

`SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 24. Branch `opus-sol-S42` = `d4f4312` + `0d99f02` cherry-picked (`91b5441f`) + `d38ef0bc`.
Tool-only job: no engine change, `[skip ci]`, no CI run. No games were played; no gate, lock, queue or live book was touched.
Worktree `F:\opus_scratch\worktrees\opus_sol_s42`, scratch `F:\opus_scratch\sol_S42`. Machine exclusive: no. Work and results by
a sub-agent; this report text is its hand-back.

**Spec (Sol, verbatim):** build a candidate book whose exits sit at about |eval| 0.6-1.2, scored at a fixed depth by OUR
engine only, both colours per pair, to cut games-to-decision (58 % of G119 pairs were 1-1). Deliver: forge_sol_S42_book_v2_<date>.epd
+ build script + report with the eval histogram and the S33 planner's power estimate from a ≤ 200-game box sample (single
process, nice). Pass: no duplicates with the current book; fixed-seed rerun gives the same sha256. Tool only.

## Acceptance
| item | result | evidence |
|---|---|---|
| book | `book/forge_sol_S42_book_v2_20261027.epd`: 1,000 positions (6-field FENs, fastchess `format=epd`).<br>Scoring: AL1 lock exe (`forge_h256_s198.exe`, sha256 `5d4df7f1…`), depth 12, Threads 1, Hash 16, `ucinewgame` before every position, Idle.<br>Every exit has 60 <= abs(eval) <= 120 cp (mean 84.8).<br>566 White-favoured, 434 Black-favoured; deviation at ply 16 (560) or ply 17 (440). | `book/`, `logs/step5a_*` |
| build script | `forge_sol_S42_book_v2_20261027.py` (`build`, `sample`, `gate`). One seeded random legal deviation per current-book line, then scoring and the band filter. | |
| no duplicates with the current book | PASS.<br>0 of 1,000 equal any of the 34,700 current exits.<br>0 appear anywhere along the current lines (164,203 positions).<br>0 repeats; all valid, none in check (independent checker).<br>The builder itself skipped 44 deviations that landed exactly on a current exit. | `logs/step5d_*` |
| fixed-seed rerun, same sha256 | PASS. Run 2 = run 1 for the EPD (`b038cce9…`), the metadata, all 5,193 scored candidates and the summary. | `logs/step5c_*` |
| eval histogram | Current book (2,000 seeded exits, same engine/depth): 0-20 cp 45.1 %, 20-40 32.6 %, 40-60 15.8 %, 60-120 6.6 %, >120 0.05 %.<br>Scored candidate pool: 0-20 662, 20-40 667, 40-60 609, 60-120 990, 120-200 526, >200 1,739 (10 accepted have exactly 120).<br>New book: all in band. | `results/current_sample_d12/`, `book/build_summary.json` |
| G119 facts | PGN parsed: pentanomial [9,130,435,163,13] == RESULT; 58.0 % 1-1 pairs.<br>By our exit eval, pairs / % 1-1 / % decisive games:<br>0-20 cp: 323 / 58.8 / 26.2<br>20-40: 245 / 56.7 / 25.5<br>40-60: 128 / 58.6 / 29.3<br>60-120: 51 / 54.9 / 39.2 (candidate score 0.539 vs 0.510) | `results/gate119_d12/` |
| S33 planner power estimate | Sol's planner is used unchanged (sha `008819d5…`, sha-pinned), through a numpy-only SciPy shim (the venv has no SciPy). The shim reproduces Sol's six frozen validation cells exactly (MC) and within 7.5e-15 (analytic).<br>Profiles come from an ordered-logistic game model fitted on G119's 1,500 games: opening slope c = 1.75 ± 0.31 Elo/cp (likelihood ratio χ² 31.1 on 1 df); goodness of fit χ² 0.43 on 4 df.<br>Books are compared at equal model strength (identity tilt). Table below. | `results/power/`, `logs/step1b_*`, `logs/step8_*` |
| ≤200-game box sample | NOT RUN (instruction: no engine games). UNVERIFIED. | |
| tests / planted bugs | 6/6 tests (synthetic engine); unmutated control + 8/8 mutants caught. | `logs/step6_*`, `logs/step7b_*` |

Power estimate, [0,10] nElo. Cap 1500 uses Monte-Carlo (20,000 runs per cell, fixed seeds); cap 3000 uses the analytic
approximation. "Δ model" is the model's strength unit; Δ 20 ≈ G119's fit, about logistic +9.2 on the current book.

| book | Δ model | 1-1 pairs | nElo | P(H1) c1500 | P(cap) c1500 | mean games | P(H1) c3000 |
|---|---|---|---|---|---|---|---|
| current book sample | 0 | 0.574 | 0.00 | 0.0014 | 0.967 | 1492 | 0.011 |
| candidate v2 | 0 | 0.536 | 0.00 | 0.0017 | 0.967 | 1491 | 0.011 |
| current book sample | +10 | 0.573 | +8.97 | 0.024 | 0.974 | 1493 | 0.173 |
| candidate v2 | +10 | 0.536 | +9.39 | 0.026 | 0.972 | 1492 | 0.189 |
| current book sample | +20 | 0.572 | +17.94 | 0.157 | 0.843 | 1454 | 0.663 |
| candidate v2 | +20 | 0.534 | +18.78 | 0.181 | 0.819 | 1445 | 0.709 |

Reference: the planner's own convention (G119 measured profile tilted to +9.5) gives P(H1) 0.182 and P(cap) 0.818.

## Findings
- nElo rises 4.7 % at equal strength, which means about 9 % fewer games for equal power. The 1-1 share falls only from 0.573
  to 0.536. Unbalanced openings turn many DD pairs into WL pairs, which are also 1-1; the gain comes from the stronger
  side converting more often.
- Model sensitivity (every opening at ±E cp, Δ = 10): the gain peaks at E = 150-200 cp, with 0.81-0.82 × the games for equal
  power. Above ~300 cp it reverses (1.09 × at 300, 2.1 × at 400). A wider band needs no code change
  (`--lo 150 --hi 200`).
- The current book is very balanced by our engine: 78 % of exits are within 40 cp.

## Left / UNVERIFIED
- The ≤200-game box sample, by instruction. Suggested design: the same engine pair on the old and the new book (e.g. 100
  pairs each, single process, Idle). Then compare the pentanomial, the 1-1 share and nElo with this model.
- The model is calibrated on one gate (G119: concurrency 5, s197 vs h256_e12), with games independent given the opening.
  ADVICE only: no Elo or strength claim, no book adoption (that needs a crew vote and a validation replay).
- "0.6-1.2" is read as 60-120 cp of the AL1 lock at depth 12. The deviations are random legal moves.

## Files
- Tools: `forge_sol_S42_book_v2_20261027.py`, `forge_sol_S42_power_20261027.py`, `check_book_v2_s42.py`, `check_scipy_shim_s42.py`,
  `scipy_shim/`, `sol_S33/` (Sol, unchanged); tests `test_forge_sol_S42_20261027.py`, `fake_uci_engine_s42.py`, `mutation_check_s42.py`.
- Book: `book/` (EPD, metadata CSV, all candidates .csv.gz 163,252 bytes, build summary). Evidence: `results/`, `logs/`.
- Docs: `README.md`, `IDEA_SOURCE.md`. Index: `FILES.txt`; checksums: `SHA256SUMS`.
