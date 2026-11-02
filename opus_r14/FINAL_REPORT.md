# R14 (Opus) - final report - everything UNPROVEN

Lock FD3A5190 (AL1 s198, kit v2.3 `-Expose`, znver5); OFF pins d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 /
34048354, perft 5 = 4865609 / 193690690. No Elo or speed claim: crew gates (UHO first, 8moves_v3 second, never pooled)
and QA's timing decide. No sub-agents in R14 (Couns): every review is a structured self-review, NOT independent, recorded
as "Review milestone R14-..." in the branch RESULTS.md. PC clock = PT + 9 h.

**Time (measured from commits, not estimated):** survey + plan from ~09:40 PC clock (plan mode, no commits); first R14
commit fa500c53 at 10:12:49, last work commit 2de7ac17 at 11:26:21 PC clock (25 commits; this report after it): ~1 h 15 min of commits,
~1 h 50 min in total, against a 15-hour budget. What the short time did not buy: no GPU training (no window), no full
relabel run and no E3 wide-range build (both outside R14 or owner items), no fits on the grown PGN set.

## Gate / handoff lines, suggested order (the crew queues; I queue nothing)
| # | item | engine A: exe sha256 + setoption | PC precondition | state |
|---|---|---|---|---|
| 1 | P6 Syzygy path | 150374ff4b9132b9... + `SyzygyPath D:\syzygy345` | bench 13 = 866959; `info string Syzygy: 145 WDL and 145 DTZ tables, up to 5 pieces` | crew: CR PASS, gate uhoP6syz_path_1503 queued (HELD 8moves confirm) |
| 2 | P6 Syzygy path + depth 4 | same exe + `SyzygyProbeDepth 4` | bench 13 = 847340 | crew: CR PASS, gate uhoP6syz_pd4_1503 queued |
| 3 | P3 singles | 029d58e8036aafa1... + `Sf26NmpPrior 1` / `Sf26LmrGap 1` / `Sf26MulticutCorr 1` | bench 13 = 931568 / 936607 / 849753 | crew: queued with HELD confirms |
| 4 | P3 combined, ONLY if 2+ singles reach H1 | 029d58e8... + all three switches | bench 13 = 727853 (= Sf26Bundle=14 in every number) | R14: prepared + proven |
| 5 | E3 Rule50Damp (fitted) | crew's E3 exe + `EvalRule50Damp 60` (the option's max; fit optimum ~81 lies past it) | crew's E3 bench | after the crew's E3 hand gate uhoE3c |
| 6 | E3 Optimism (weak evidence) | crew's E3 exe + `EvalOptimism 150`, never bundled with #5 | crew's E3 bench | optional |
| - | FORGE_SEARCH_SPEED2 (speed only) | de20653cea8ce610... (`D:\o14a\handoff\speed2\`), no setoption | every pin = lock | QA timing first; node-identical |

## Per item: deliverables, hashes, checks (evidence in each branch's RESULTS.md)
| item (branch, last commit) | deliverables | checks |
|---|---|---|
| A1 P5 relabel (opus-r13-p5-nnue-data, 2ed1750b) | RESULTS: job1 = 440,000 rows (22/461 shards, 353,917 pos/h, 20k nodes, CPU 3, Idle, 11:10-12:25 PC clock Nov 1) on RECONSTRUCTED FENs - 81.9 % of its rows lost castling / ep / halfmove state; fix = Astra's original FEN sidecar (`completed/full10m/forge_filtered.fen`, sha256 beb3c31d) + guard against new lossy jobs; prove_sidecar.py | archive 148803c5 + member beb3c31d verified; FEN carried 1000/1000; control rows 159/159 identical; castling rows 199/211 relabelled differently; full audit 9,206,371 rows PASS; old labels kept |
| A2 P6 Syzygy (opus-r13-p6-syzygy, 5e025387) | RESULTS: kit pass + load line + benches + checks + CR notes; CI config for ProbeDepth 10 | pc1 = pc2 = 150374ff; OFF ALL OK; bench 16 = 3024920 / 2460490 / 2563760; smoke 24/24; mate probe: TB-win scores, none lost; CI 41420554076 green |
| A3 P7 E3 fit (opus-r13-p7-e3fit, 360e49df) | CR 129d440e items ported; `fit_e3.py --bounds`; compare_sets.py; 6 PGN sha256 in inputs.sha256 | default-bound fit = R13 exactly; wide refit: Rule50Damp 81 (past max 60, 81 vs 60 -0.000318 [-0.000632, -0.000039]), Optimism 228 (vs 150 not separated), MatScale 0; razor PGN grew since R13 (1,093 -> 2,998 games), other 5 PGNs identical |
| A4 P4 v2 nets (opus-r13-p4-v2nets, d6da211e) | CR d884c23b applied (md5 9c124cc3 / 4246dfd5 / 9ede6e56); legal_fens.py; no-embedded-net harness builds; GPU_REQUEST + ROCm build | cargo 70cbae12 0 warnings; parity 10000/10000 exact AVX2 + SSE at H 256 / 768 / 1024 / 1536, planted bug fails; ROCm exe 0028dd9c links amdhip64 / hipblas / hiprtc |
| A5 P3 combined (opus-r13-p3-sf26split, 6502b1a4) | combined line proof + CI config comb | lp_check: combined = Sf26Bundle=14 in every number, OFF = pins; smoke 16/16; mate probe 21 vs 19; CI 41422747717 green |
| Main 1 v2 nets training | `opus_r14/b/GPU_REQUEST.md` (exact env + commands, a -> b -> c, H 768 / 1024 / 1536, seeds 14411/2, 14421/2, 14431/2, minutes, checks before every run) | BLOCKED: GPU booked by npt lines (keeper window to 2026-11-08, ~132 h queued); nothing started |
| Main 2 FORGE_SEARCH_SPEED2 (opus-r13-p2-sparse-l1, 2de7ac17) | build switch: TT prefetch after null move + ProbCut make, speedmp2 MovePicker hoist, table piece_type; port script + patch (+91 / -0) | plain 0/1 node identity ALL OK; codegen live (prefetch 3 -> 5); switch-0 kit build = FD3A5190 byte for byte; kit ON pc1 = pc2 = de20653c; uci identical; smoke 8/8; CI 41424824966 green; advisory ABBA d16 +3.0 % / d20 +2.8 % (A/A noise up to +2.6 %) |
| A6 / setup (opus-r13-status) | PLAN.md (blocks 1-2), TOOLS.md, AGENTS.md (Couns's review policy verbatim + Opus R14 rules), STATUS.md, this report | remote = local on all 8 branches (checked at the end) |

## What is UNPROVEN
All gate lines above; the E3 fitted values (calibration of a static eval, not strength; Optimism is a static stand-in);
the SPEED2 speed numbers (advisory, one core, A/A noise of the same size); the relabelled labels (Engine NNUE decides).

## Known risks
- P5: relabel_positions re-reads the 484 MB sidecar per shard (fine for proofs, ~5-10 s per shard in a full run).
- P7: Rule50Damp's best fitted value (~81) is outside the E3 option range; the gateable 60 is "the max allowed", not the
  optimum. Optimism overlaps with MatScale in the static fit (CR's finding).
- P4: any trained net needs a width-H engine whose compiled-in AL1 net is zero-padded (function-preserving) before a gate.
- SPEED2: speed only - a gate would test speed, not search changes; QA's official timing should come first.
- CR's LOW P6 crfix 4b537823 (test tooling) was not found on the PC: not applied.

## Leftover TODOs (owner / crew)
1. QA timing of SPEED2 de20653c vs FD3A5190; gate only if QA finds the speed worth it.
2. Engine NNUE: decide on job1's reconstructed labels; a full relabel with `--sidecar ... --sidecar-origin original_full_fen`
   when wanted (command in P5 RESULTS).
3. A GPU window for the v2 nets (GPU_REQUEST.md); the ROCm binary is ready.
4. After uhoE3c: if Rule50Damp helps, an E3 build with EvalRule50Damp max >= 81 for a line near 80.
5. Optional: P7 fits on the grown PGN set (`run_p7_r14b.sh` ready).

## Skills created / improved in R14 (live copies in `.claude/skills/`, committed under `skills/<name>/`)
| skill | change | committed on |
|---|---|---|
| forge-nnue-data | FPOS has no castling / ep / clocks; Astra's FEN sidecar member + extraction command; relabel with the sidecar; proof tool | opus-r13-p5-nnue-data |
| forge-candidate-checks | TB lines: TB-win scores vs mate notation; CI at an option's max; option-equivalence proof via lp_check compare; VCTIP / Start-Process -Wait pitfall | opus-r13-p6-syzygy, opus-r13-p3-sf26split |
| forge-speed-stack | node-identical switch on the lock: port pattern, codegen liveness, D: kit wrapper, switch-0 = lock identity, r12_speed launcher pitfall | opus-r13-p2-sparse-l1 |
| forge-ltopgo-pgo | kit reproduces FD3A5190 from a switch-0 source on D:; kit_build_r14.sh; plain-exe PE timestamp difference | opus-r13-p2-sparse-l1 |
| forge-pc-rules | R14 rules (no sub-agents, D:\o14a <= 10 GB, F: forbidden, trainer mask 0xF sharing CPUs 2-3, GPU window, CR patch folder) | opus-r13-status |
No new skill was needed: each lesson extended the existing skill on the same topic.
