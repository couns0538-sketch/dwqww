# T12 sources (testing, tuning, measurement, correctness proofs)

Worker start 22:45 PC clock (PST -0800), research stop 23:45. One line per source: url or repo@sha | licence tier |
what it gave | card id.

## Own side (read-only, not counted in the 15-source cap)
- project skill forge-gate-stats/SKILL.md | own | fastchess 1.8.2 exact GSPRT (fishtest LLRcalc
  MLE), bounds +-ln(19)=+-2.944, pentanomial Elo/nElo formulas, net early stop rule, winner's-curse numbers | T12-01
- project skill forge-spsa-tuning/SKILL.md | own | R9 tuner schedule (c_k=c_end N^0.101, a_k,
  A=0.1N), 832 pairs at 8+0.08 -> 0 of 16 beyond 2 sigma, ~280 pairs/h at conc 4, r_end 0.002 vs 0.012 | T12-04
- user skill forge-o30-spsa/SKILL.md | own | 41+10 exposed lock constants + 22 more
  (o30_expose.py), tuner config keys, ~100 games/h at 10+0.1 conc 1 one CPU, O30Tuned packaging | T12-04
- user skill forge-gate-summary/SKILL.md | own | gate rate ~497 games/h (conc 4, Threads 2,
  10+0.1, CPUs 4-15), LLRcalc details (empty cells 1e-3, 10 MLE steps) | T12-01
- project skill forge-ltopgo-pgo/SKILL.md (lines 47-75) | own | lock pins, 12k-FEN identity,
  r12_speed palindromic blocks, per-file A/A -3.0 % at d16 | T12-03, T12-02
- project skill forge-opus-tools/SKILL.md (abba.py, lines 29-48) | own | ABBA slots, Student-t CI
  on log ratios, --identity, CPUs 2-3 = one physical core | T12-02
- project skill forge-engine-verify/SKILL.md (grep) | own | nps_opts_ab A/A -0.02 % [-2.24,
  +2.25] on the loaded PC; "count before timing" | T12-02
- notes/TRIED_GATES.md (109 gates) | own | caps 1000/1500/3000/6000, bounds [0,10] nElo, most caps inside +-2 LLR | T12-01
- F:/forge_push/uhoE3a_evalmatscale12_r6k_vs_AL1lp/RESULT.md + RUN_INFO.json | own | UHO gate settings (fastchess
  1.8.2, 10+0.1, Threads=2, Hash 16, conc 4, CPUs 4-15, UHO_Lichess_4852_v1.epd random start, SPRT [0,10] nElo, cap
  6000) and a 3000-pair pentanomial [30, 686, 1509, 744, 31] used as Forge's own variance profile | T12-01

## External (cap 15)
- E1 https://github.com/official-stockfish/fishtest/wiki/Fishtest-mathematics | GPL-3.0 repo, wiki page (docs, ideas
  only) | overview only: bounds in normalised Elo, pentanomial model "substantial saving", GSPRT = MLE in place of
  unknowns, expected duration depends only on the bounds (independent of draw ratio / book); numbers sit in linked
  PDFs (normalized_elo_practical, sprta, GSPRT_approximation, accounting_identity) | T12-01
- E2 https://github.com/official-stockfish/fishtest/wiki/Creating-my-first-test | GPL-3.0 repo, wiki (docs) |
  STC 10+0.1, LTC 60+0.6, SMP 8 threads; non-regression bounds <-1.75,0.25> in example commit messages; "Bench:"
  line / "No functional change"; speed-ups: several bench runs mean+sd, target ~0.5 %, "about 0.25 % speedup at STC
  and about 0.7 % at LTC for a 50 % passing chance", "1 % speedups pass with an 85 % chance"; SPSA usually at normal
  TC | T12-01, T12-02, T12-03
- (own analysis, not a source) sprt_plan.py (mirrored with its raw output in notes/T12/sprt_model.md) on C:/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.csv
  (110 gates with Ptnml): book profiles (UHO nElo/Elo 1.91, pair sd 0.185, pent/trin variance 0.618; 8moves 2.10,
  0.167, 0.90), unit check of the Brownian LLR vs printed LLR (82 of 85 capped gates within 0.15 at [0,10]), MC table of
  P(H1) / games / P(decided by cap) per bound, truncated-SPRT error rates | T12-01, PROTOCOLS.md
- (navigation, no card) https://github.com/official-stockfish/fishtest/wiki (page list: SPSA lives only as sections of
  Creating-my-first-test; no book or TC page); WebSearch "fishtest wiki SPSA ..." gave no SPSA page
- E2b https://github.com/official-stockfish/fishtest/wiki/Creating-my-first-test#tuning-with-spsa and #spsa-tests |
  same page as E2 (docs) | SPSA mechanics: params name,start,min,max,c_end,r_end; mini match at value -+ ck; update
  value += ck*rk*(W-L); ck = c0/(1+k)^gamma, ak = a0/(A+1+k)^alpha, rk = ak/ck^2 (1 iteration = 2 games); c must be
  "large enough to have a measurable Elo difference" (scale values x10 so c >= ~5); many values at once = random change;
  "values barely changing after a few thousand games -> useless, stop"; search params at normal TC (Hash 16 at 20+0.2,
  64 at 60+0.6); no numeric defaults on the page | T12-04
- (navigation) https://github.com/AndyGrant/OpenBench/wiki (page list) and README.md@230ed46e47 (10 lines, points to
  the wiki) | GPL-3.0 (docs only) | no card
- E3 https://github.com/AndyGrant/OpenBench/wiki/Requirements-For-Public-Engines | GPL-3.0, docs | "./binary bench" must
  print final nodes + nps; "All engines must be deterministic across multiple runs, on all supported machines"; every
  client benches and "must produce the same nodes result every time"; bench used "to affirm that the build is correct"
  and "to determine the relative speed of the clients CPU"; AVX vs AVX2 machines can be a source of non-determinism
  | T12-03
- E4 https://github.com/AndyGrant/OpenBench/wiki/SPSA-Tuning-Workloads | GPL-3.0, docs | alpha 0.602, gamma 0.101,
  A-ratio 0.1; "ideal R_end 0.0020"; "C_end about 1/20th the reasonable range"; integer C at least 0.50 (OpenBench
  raises it); 8 pairs per point for LTC tunes; Batched reporting + Single distribution; "hundreds of thousands of games"
  | T12-04
- E5 https://github.com/AndyGrant/OpenBench/wiki/SPRT-and-Fixed%E2%80%90Game-Workloads | GPL-3.0, docs | bounds +
  confidence [alpha, beta] fields, 0.05 "generally a good value", calculator link uses elo-model=Normalized elo-0=0
  elo-1=2; workload size in game pairs; 250 ms time margin; no default bounds stated | T12-01 (support), T12-05
- E6 https://llvm.org/docs/Benchmarking.html | LLVM docs (Apache-2.0 with LLVM exception) | disable the SMT pair of
  the benchmark CPUs; disable frequency scaling, Turbo Boost and ASLR; reserve cores (cset shield, kernel threads
  moved out); avoid storage (tmpfs); run multiple times (perf stat -r 10); "variations of less than 0.1%" with all
  of this; "low noise is required, but not sufficient. It does not exclude measurement bias" (Mytkowicz et al. 2009)
  | T12-02
- E7 official-stockfish/Stockfish commit titles + logged results since 2023-06-01 (tools/mine_commits.py --grep
  'spsa|tune', 1,200 commits cached, 56 shown) | GPL-3.0, commit messages only | SPSA-tune commits pass with a few
  Elo, e.g. 5c617e5 "VVLTC Search Tune" STC ~+5.2 n=15,788 / LTC ~+6.4 n=13,622; 94e6c04 LTC ~+6.7 n=12,800;
  738ac2a "tuned TM values" STC ~+0.3 n=491,872 / LTC ~+1.0 n=154,824 (~ = Elo computed from W/L/D by the tool) | T12-04
- E8 https://github.com/official-stockfish/Stockfish/commit/5c617e579c (full message) | GPL-3.0, commit message |
  STC bounds <0.00,2.00>, LTC bounds <0.50,2.50> (normalised), LLR +-2.94; Ptnml [0, 1324, 5009, 1560, 1] at 15,788
  games; Bench line; SPSA game budget not stated in the message | T12-01, T12-04
- E9 https://github.com/official-stockfish/books/blob/a804a97e70/README.md | CC0-1.0 (data + docs) | book sizes:
  UHO_Lichess_4852_v1.epd 2,632,036 positions (1,457,270 white / 1,174,766 black to move, 2-16 plies); 8moves_v3.pgn
  34,700 (16 plies); UHO_4060_v4 241,670; noob_3moves 150,932 | T12-05
- E10 https://learn.microsoft.com/windows-hardware/customize/power-settings/options-for-perf-state-engine-perfboostmode
  (MicrosoftDocs commit 3879557abb, docs) | vendor docs, ideas only | powercfg alias PERFBOOSTMODE (GUID
  be337238-0d82-4146-a960-4f3749d470c7, hidden): index 0 = Disabled (no boost above nominal), 1 Enabled, 2
  Aggressive (CPPC); applies to Windows 11 x64 | T12-02
- (dead end) https://dl.acm.org/doi/10.1145/1508244.1508275 (Mytkowicz et al., ASPLOS 2009) | HTTP 403; cited only
  through E6's pointer, no number taken from it
- E11 official-stockfish/Stockfish commit messages a06e7004c1 ("Port instrumented testing to python": CI test suites
  that assert the engine's output, run as tests/instrumented.py against a binary) and 73018a0337 ("Detect search
  explosions": pathological positions where double extensions stop the search finishing) | GPL-3.0, commit messages
  only (no test file read) | T12-03 (output-assertion suite, pathological-position class)
