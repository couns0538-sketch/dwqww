# T12 adversarial verify (Testing, tuning, measurement and correctness proofs)

Verifier start 23:30 PC clock (PST -0800), planned stop 23:50. One line per check:
card | claim | CONFIRMED / CORRECTED / UNVERIFIABLE / VIOLATION | evidence.

## 1. Source numbers (top 3 full cards; 2 one-liners spot-checked)
| card | claim | verdict | evidence |
|---|---|---|---|
| T12-01 | Fishtest-mathematics: bounds in normalised Elo, pentanomial "substantial saving", GSPRT = MLE for unknowns, expected duration depends only on the bounds | CONFIRMED | https://github.com/official-stockfish/fishtest/wiki/Fishtest-mathematics (sections "Pentanomial Model", "Normalized Elo for Bounds") |
| T12-01 | STC 10+0.1, LTC 60+0.6; non-regression <-1.75,0.25> in the example commit messages | CONFIRMED | https://github.com/official-stockfish/fishtest/wiki/Creating-my-first-test ("STC: Short time control (10+0.1)", "LTC: Long time control (60+0.6)", two "LLR ... <-1.75,0.25>" examples) |
| T12-01 | Fishtest bounds STC <0,2>, LTC <0.5,2.5>, LLR +-2.94 (5c617e579c message) | CONFIRMED | https://github.com/official-stockfish/Stockfish/commit/5c617e579c ("<0.00,2.00>", "<0.50,2.50>", "(-2.94,2.94)") |
| T12-01 | 110 gates with Ptnml; 79 "Cap with no decision" (55 at 1,500, 14 at 3,000, 9 at 1,000, 1 at 6,000); 4 by the net early stop; 25 decided | CONFIRMED | recount of C:/Users/Administrator/grok-pc/forge_push/FORGE_RESULTS.csv (110 rows, all LLR bounds -2.94/2.94; verdicts 79 cap, 12 H1, 12 H0, 1 H1 non-regression, 4 H0-early, 1 NOT CLEAN, 1 TRIAL-ONLY) |
| T12-01 | capped nElo 10/50/90 % = -9.0 / +7.4 / +18.2 | CONFIRMED | same CSV, the 79 capped rows, linear-interpolated quantiles -9.0 / 7.4 / 18.2 |
| T12-01 | Brownian LLR matches the printed LLR within 0.15 on 82 of the 85 undecided gates at [0,10] | CONFIRMED | independent recompute (pairs x dt x (t_hat - t_mid), dt = 10 nElo x sqrt2 x ln10 / 800): 82 of 85; the 3 misses are gate 101 (speed), R5D-MF (non-regression), R7-PFE (fixed 1000) |
| T12-01 | UHO nElo/Elo 1.91 (n=6), 8moves 2.10 (n=63), pent/trin variance 0.618 / 0.90, draws 0.56 / 0.75 | CONFIRMED | notes/T12/sprt_model.md:111-112 (own model output) |
| T12-01 | MC means: [0,10] 6.6k games at the ends, 11.1k at +5; [0,5] 26k; [0,15] 2.95k; [0,20] 1.65k; [0,2] ~165k | CONFIRMED (approx) | sprt_model.md table, lines 123-150; analytic Brownian cross-check E[N] = (2b/dt^2) tanh(b/2) pairs with b = ln19 gives 6.40k / 25.6k / 2.84k / 1.60k / 160k games, and b^2/dt^2 = 10.5k at the [0,10] midpoint; the MC is 2-6 % longer, as discrete overshoot predicts |
| T12-01 | P(decided by cap) and truncated-rule error rates (0.20 by 3k, 0.88 by 12k; 0.22/0.78, 0.13/0.86, 0.07/0.93) | UNVERIFIABLE (own model) | only in sprt_model.md; not re-simulated in the 20-minute window; no external source exists for them |
| T12-01 | S44 replay ~75 min per 23 gates single-threaded | CONFIRMED | <cfg>/skills/forge-gate-stats/SKILL.md:41 |
| T12-01 | gate rate 497 games/h | CONFIRMED | user skill forge-gate-summary SKILL.md:31 (conc 4, Threads 2, 10+0.1, CPUs 4-15) |
| T12-02 | LLVM: "variations of less than 0.1%"; "low noise is required, but not sufficient. It does not exclude measurement bias"; SMT pair, Turbo Boost and ASLR off, cset shield, perf stat -r 10; Mytkowicz pointer | CONFIRMED | https://llvm.org/docs/Benchmarking.html ("perf variations of less than 0.1%") |
| T12-02 | PERFBOOSTMODE index 0 = Disabled (GUID be337238-0d82-4146-a960-4f3749d470c7) | CONFIRMED | https://learn.microsoft.com/windows-hardware/customize/power-settings/options-for-perf-state-engine-perfboostmode (index table: 0 = Disabled in all three columns; 2 = Aggressive only for non-autonomous CPPC/PEP) |
| T12-02 | fishtest: target ~0.5 %; "about 0.25% speedup at STC and about 0.7% speedup at LTC for a 50% passing chance"; "1% speedups pass with an 85% chance"; bounds not stated | CONFIRMED | Creating-my-first-test, speed-up section (one paragraph; no bounds given there) |
| T12-02 | exe vs its own byte copy -3.0 % at d16 (R12) | CONFIRMED | <cfg>/skills/forge-ltopgo-pgo/SKILL.md:70 |
| T12-02 | A/A -0.02 % [-2.24, +2.25] on the loaded PC | CONFIRMED | <cfg>/skills/forge-engine-verify/SKILL.md:77 |
| T12-02 | CPUs 2-3 = one physical core | CONFIRMED | <cfg>/skills/forge-opus-tools/SKILL.md:48 |
| T12-02 | "logical CPUs 2k and 2k+1 share a core" (general rule) | UNVERIFIABLE | only CPUs 2-3 are stated in the cited skill; the general pairing is not traced to a file |
| T12-02 | n = 8.6 x s^2 pairs (one-sided 95 %, power 90 %, 1 % effect); 35 / 78 / 215 pairs at s = 2 / 3 / 5 % | CONFIRMED | (1.6449 + 1.2816)^2 = 8.56; 34.3 / 77.1 / 214.1 rounded up (a z-test; a t-quantile adds ~3 % at n = 35) |
| T12-02 | 215 pairs ~25 min at bench 16 (~2-3 s per run) | CONFIRMED (approx) | 430 A/B runs x 2-3 s = 14-22 min; with the A' arm (3 arms) 21-32 min; the 2-3 s per run itself is not traced to a file |
| T12-03 | OpenBench: bench prints final nodes + nps; "All engines must be deterministic across multiple runs, on all supported machines"; "the same nodes result every time"; AVX vs AVX2 non-determinism | CONFIRMED | https://github.com/AndyGrant/OpenBench/wiki/Requirements-For-Public-Engines (bullets 1-2) |
| T12-03 | fishtest: "Bench: XXXXXXX" / "No functional change" as the last line; a speed-up too small for fishtest but verifiable from asm -> PR | CONFIRMED | Creating-my-first-test ("If the speedup is too small to be verified on fishtest but is otherwise verifiable (i.e. inspecting asm changes) a PR can be opened instead.") |
| T12-03 | Stockfish a06e7004c1 "Port instrumented testing to python", 73018a0337 "Detect search explosions" | CONFIRMED | commit messages via gh api (titles and gist match; no test file opened by the verifier either) |
| T12-03 | lock bench at src/uci.cpp:377-408: 8 FENs, one depth, 16 MB TT cleared before each FEN, prints only the total | CORRECTED (minor: content CONFIRMED, range 377-410; card annotated) | lock src_al1s198_clean src/uci.cpp:377-410 (8-entry fens array; Searcher bench_searcher(16) with Searcher(std::size_t hash_mb, ...) at include/forge/search.hpp:375; bench_searcher.clear() per FEN; one "info string bench depth .. nodes .. time .. nps" line); the print ends at line 410, not 408 (immaterial) |
| T12-03 | pins d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354; perft 4865609 / 193690690 | CONFIRMED | <cfg>/skills/forge-ltopgo-pgo/SKILL.md:48 (the skill does not say "perft 5" / "kiwipete 5"; these are the standard startpos and kiwipete perft(5) counts) |
| T12-03 | Forge already has a depth-2 version of level 4 (12k FENs) | CONFIRMED | forge-ltopgo-pgo SKILL.md:50 (r12_fens12k.py, go depth 2 per FEN) |
| T12-03 | levels 3-5 ~250M nodes each at ~1.5 Mnps | UNVERIFIABLE | 12k x 20k = 240M and 50 games x ~100 plies x 50k = 250M follow from the card's own settings; ~1.5 Mnps is not traced to a cited file |
| T12-04 (spot) | 5c617e5 "VVLTC Search Tune": +5.2 Elo n=15,788 <0,2>; +6.4 Elo n=13,622 <0.5,2.5>; LLR 2.94 / 2.95 | CORRECTED | the numbers are right (W/L/D 4106/3868/7814 -> +5.24; 3620/3368/6634 -> +6.43), but both runs were played at VVLTC ("Passed VVLTC with STC bounds" / "Passed VVLTC with LTC bounds"): "STC"/"LTC" name the bound sets, not the TC; the VVLTC TC itself is not in the message. Card annotated. |
| T12-04 (spot) | OpenBench SPSA defaults alpha 0.602, gamma 0.101, A-ratio 0.1, R_end 0.0020, C_end ~1/20 of the range, 8 pairs per point | CONFIRMED (note) | https://github.com/AndyGrant/OpenBench/wiki/SPSA-Tuning-Workloads; the 8 pairs is stated "for LTC tunes" (raise it for very fast tunes); the card uses it at 10+0.1 |
| T12-04 | 41 + 22 = 63 exposed constants; R9 832 pairs -> 0 of 16 beyond 2 sigma | CONFIRMED | user skill forge-o30-spsa SKILL.md:12-14; <cfg>/skills/forge-spsa-tuning/SKILL.md:67-68 (at 8+0.08) |
| T12-04 | 33k games ~33 h at an assumed ~1,000 games/h (conc 8) | CONFIRMED (note) | labelled "not measured"; the measured rate is ~100 games/h per conc-1 slot at 10+0.1 (forge-o30-spsa SKILL.md:37) -> ~800/h at conc 8 -> ~41 h, still inside the card's 33-67 h |
| T12-05 (spot) | books README @a804a97e70: UHO_Lichess_4852_v1 2,632,036 (1,457,270 / 1,174,766, plies 2-16); 8moves_v3 34,700 (16 plies) | CONFIRMED | README.md at a804a97e70 via gh api (table rows) |
| T12-05 | Sf26Bundle=14: -8.5 vs -6.6 nElo at 1,500 games, both +-17 | CORRECTED (clarified) | FORGE_RESULTS.csv: SF26B14 gate_sf26bundle14_vs_AL1 (8moves_v3) nElo -8.52 and UT2 uhoT2_sf26b14 (UHO) -6.62, 1,500 games each; the card's order read as UHO first; 95 % half-width at 750 pairs = 1.96 x 347.4 / sqrt(1500) = 17.6 nElo. Card annotated. |
| T12-05 | LTC 30+0.3 [0,15] cap 6k: ~18 h mean, ~36 h at the cap at ~166 games/h | CONFIRMED (arithmetic) | 2.95k / 166 = 17.8 h; 6,000 / 166 = 36.1 h; 166 = 497 / 3 (the 3x per game is an assumption, not measured) |

## 2. Reading rule
| card | claim | verdict | evidence |
|---|---|---|---|
| all | no link to a /blob/ or raw source file of a GPL / AGPL / unlicensed repo | CONFIRMED | every URL in cards/T12 and notes/T12 listed by grep: fishtest and OpenBench wiki pages, Stockfish commit pages, llvm.org docs, learn.microsoft.com, books repo; the only /blob/ link is books README.md @a804a97e70 (CC0-1.0, and a README) in sources.md:74 |
| all | Stockfish read only as commit messages / titles (5c617e579c, a06e7004c1, 73018a0337, mine_commits titles); nnue-pytorch not read | CONFIRMED | sources.md E7, E8, E11; no Stockfish or nnue-pytorch file path in any card or note (based on the worker's log; what was opened cannot be checked beyond it) |
| T12-03, T12-04 | OpenBench (GPL-3.0) read only as wiki pages + README.md (10 lines) | CONFIRMED | sources.md E3-E5 and the navigation line; the Requirements page points to Client/bench.py, which is not cited or read |
| T12-01, T12-02, T12-04, T12-05 | fishtest (no root licence found; listed GPL-3.0) read only as wiki pages | CONFIRMED | sources.md E1, E2, E2b |
| all | no pasted or paraphrased code from GPL / AGPL / unlicensed sources | CONFIRMED | mechanisms are described in prose; the only code-level description is of Forge's own lock bench (uci.cpp) |
| T12-04 | no other engine's tuned constants proposed as Forge values | CONFIRMED (note) | alpha 0.602 / gamma 0.101 / A-ratio 0.1 / R_end 0.002 are SPSA tuner hyperparameters that OpenBench documents as its defaults (taken "from some of the original SPSA academic papers"), not an engine's tuned search constants; c_end is own (max(range/20, 1 unit)); no Stockfish search value is proposed |

## 3. Licence rows (tools/licence_at.py --row re-run 23:31)
| card | claim | verdict | evidence |
|---|---|---|---|
| T12-01..05 | official-stockfish/fishtest 5a8a229a52: root licence absent, api none | CONFIRMED | re-run row identical |
| T12-03, T12-04 | AndyGrant/OpenBench 230ed46e47: LICENSE, GPL-3.0 | CONFIRMED | re-run row identical |
| T12-02 | llvm/llvm-project f7d11195ab: LICENSE.TXT, row said "MIT (tool guess ...)" | CORRECTED | the re-run prints spdx guess "Apache-2.0 WITH LLVM-exception" (the card's own licence text was already right); notes/T12/licences.md row annotated |
| T12-01, T12-04 | official-stockfish/Stockfish 5c617e579c: Copying.txt, GPL-3.0 | CONFIRMED | re-run row identical |
| T12-05 | official-stockfish/books a804a97e70: LICENSE, CC0-1.0 | CONFIRMED | re-run row identical |
| T12-03 | Stockfish a06e7004c1 and 73018a0337 (cited commits): no row existed | CONFIRMED (added) | both GPL-3.0 (Copying.txt); two rows added to notes/T12/licences.md, and the table moved above its Notes block so it renders as one table |

## 4. "Forge has it"
| card | claim | verdict | evidence |
|---|---|---|---|
| T12-03 | `forge_has.sh 'bench\|perft'`: bench and perft only | CONFIRMED | re-run: 14 hits, bench at src/uci.cpp:377 (395 Searcher(16), 401 clear), perft at src/board.cpp:872 and src/uci.cpp:292; no per-position compare, warm-TT replay or differential verify build in the lock |
| T12-01, T12-02, T12-04, T12-05 | "Forge has it" cites tools / skills (fastchess GSPRT, abba.py, r12_speed.py, r9_spsa.py, tune_spsa.ps1, books) | CONFIRMED (N/A for a lock grep) | runner / tooling / method cards; the lock source does not hold these tools; the skill lines are checked in section 1 |

## 5. Labels, names, lint
| card | claim | verdict | evidence |
|---|---|---|---|
| all | every Forge-side estimate labelled UNPROVEN | CONFIRMED | T12-01 / 02 / 03 "**UNPROVEN**" in Expected gain, T12-02 cause "(UNPROVEN)", T12-04 and T12-05 one-liners end "UNPROVEN"; PROTOCOLS.md has 3 labels and no unlabelled Forge Elo claim (its "8-9 Elo swings" line is a resolution limit, not a gain) |
| all | no AI-vendor / model-company names | CONFIRMED (note) | no hit from the lint list; "Microsoft" appears only as the publisher of the Windows PERFBOOSTMODE docs (T12-02 lines 7 and 12, PROTOCOLS.md:141, sources.md:77-78); it is not on the lint's list - left for the coordinator to decide |
| all | tools/card_lint.py cards/T12/*.md | CONFIRMED | 0 findings, 0 PENDING on all 5 cards at the start and in the final state (the first verify edit made T12-03 61 lines; merged back to 60 and re-linted at 23:39) |

## 6. Note for the coordinator (not a violation)
- Gate route: WORKER_RULES name "UHO SPRT [0,5] at STC, then LTC"; all five T12 cards route through "[0,10] nElo, cap
  12k (or [0,15] cap 6k)" instead. T12-01 argues it (model: [0,5] needs ~26k games at the ends, 0.00 decided by 3k).
  This is the track's own proposal, not an error; the binding route stays the coordinator's call.
- "No gate ran [0,5]" (T12-01): supported for 82 of the 85 undecided gates by the LLR match at [0,10]; the 25 decided
  gates were not re-checked.

## Totals
51 checks: 44 CONFIRMED (incl. approx / notes / 2 added licence rows), 4 CORRECTED (T12-04 VVLTC TC, T12-05 book
order of the Sf26 pair, T12-03 line range, llvm spdx guess), 3 UNVERIFIABLE (T12-01 own-model decision probabilities,
T12-02 general SMT pairing rule, T12-03 ~1.5 Mnps), 0 VIOLATION. No card Status changed.

Verifier end 23:40 PC clock. Downloads for the checks went to the session scratchpad (outside the repo), nothing else written outside cards/T12 and notes/T12. The T12-01 row on 5c617e579c bounds checks the hand-back / PROTOCOLS.md citation; the T12-01 card itself cites only the two fishtest wiki pages.
