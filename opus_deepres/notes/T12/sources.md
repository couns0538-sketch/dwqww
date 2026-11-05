# T12 sources (testing, tuning, measurement, correctness proofs)

Worker start 22:45 PC clock (PST -0800), research stop 23:45. One line per source: url or repo@sha | licence tier |
what it gave | card id.

## Own side (read-only, not counted in the 15-source cap)
- D:/grok-pc-data/dwqww/<cfg>/skills/forge-gate-stats/SKILL.md | own | fastchess 1.8.2 exact GSPRT (fishtest LLRcalc
  MLE), bounds +-ln(19)=+-2.944, pentanomial Elo/nElo formulas, net early stop rule, winner's-curse numbers | T12-01
- D:/grok-pc-data/dwqww/<cfg>/skills/forge-spsa-tuning/SKILL.md | own | R9 tuner schedule (c_k=c_end N^0.101, a_k,
  A=0.1N), 832 pairs at 8+0.08 -> 0 of 16 beyond 2 sigma, ~280 pairs/h at conc 4, r_end 0.002 vs 0.012 | T12-04
- C:/Users/Administrator/<cfg>/skills/forge-o30-spsa/SKILL.md | own | 41+10 exposed lock constants + 22 more
  (o30_expose.py), tuner config keys, ~100 games/h at 10+0.1 conc 1 one CPU, O30Tuned packaging | T12-04
- C:/Users/Administrator/<cfg>/skills/forge-gate-summary/SKILL.md | own | gate rate ~497 games/h (conc 4, Threads 2,
  10+0.1, CPUs 4-15), LLRcalc details (empty cells 1e-3, 10 MLE steps) | T12-01
- D:/grok-pc-data/dwqww/<cfg>/skills/forge-ltopgo-pgo/SKILL.md (lines 47-75) | own | lock pins, 12k-FEN identity,
  r12_speed palindromic blocks, per-file A/A -3.0 % at d16 | T12-03, T12-02
- D:/grok-pc-data/dwqww/<cfg>/skills/forge-opus-tools/SKILL.md (abba.py, lines 29-48) | own | ABBA slots, Student-t CI
  on log ratios, --identity, CPUs 2-3 = one physical core | T12-02
- D:/grok-pc-data/dwqww/<cfg>/skills/forge-engine-verify/SKILL.md (grep) | own | nps_opts_ab A/A -0.02 % [-2.24,
  +2.25] on the loaded PC; "count before timing" | T12-02
- notes/TRIED_GATES.md (109 gates) | own | caps 1000/1500/3000/6000, bounds [0,10] nElo, most caps inside +-2 LLR | T12-01
- F:/forge_push/uhoE3a_evalmatscale12_r6k_vs_AL1lp/RESULT.md + RUN_INFO.json | own | UHO gate settings (fastchess
  1.8.2, 10+0.1, Threads=2, Hash 16, conc 4, CPUs 4-15, UHO_Lichess_4852_v1.epd random start, SPRT [0,10] nElo, cap
  6000) and a 3000-pair pentanomial [30, 686, 1509, 744, 31] used as Forge's own variance profile | T12-01

## External (cap 15)
