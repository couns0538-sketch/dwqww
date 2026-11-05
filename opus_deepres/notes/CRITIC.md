# Cross-track critic (phase 2)

Started 23:43 PC clock (PST as printed by `date`); stop 00:23; finished 23:59. Inputs: the track briefs as relayed to the workers
(`tools/workflows/prompts_core2/research_T0{1,2,4,5}.md`, `prompts_extra/research_T{06,07,12}.md`; the owner's brief
itself was NOT in the critic's message, so these relayed track briefs are the question list; T2-card-1 from
FINAL_REPORT / RESUME / card T02-01), all cards, all notes, all VERIFY.md files, FINAL_REPORT.md (INTERIM, 23:40).
One line per finding. Part A rows: track | question | answered where | answer in one line | or NOT COVERED + reason.
Part B rows: where | claim | verdict (OK / MISMATCH / UNSOURCED / CONTRADICTION) | fix.

## Part A - coverage matrix
### T4 (brief: tools/workflows/prompts_core2/research_T04.md)
- T4 | correction-history keying / weighting that gained Elo (pawn, minor, non-pawn, continuation) | notes/T04/TABLE.md:67-86 (section D); cards T04-04, T04-05 | pawn + material HAS; non-pawn and continuation TRIED; minor PREPARED (CorrHistPlus bit 2, never gated alone) and major LACKS -> T04-04; SEE-losing-capture update -> T04-05; squared-depth weight A9 | COVERED
- T4 | multicut | notes/T04/TABLE.md:28 | HAS multicut (search.cpp:1105-1106, returns singular_beta); blended-score variant = queued crew line Sf26MulticutCorr + SingularV2 | COVERED
- T4 | double / triple extensions | card T04-06; notes/T04/TABLE.md:17, :29, :56 | double HAS (<= 7 per path, verifier correction), triple LACKS on the lock (PREPARED in SingularV2, never gated), both sources long-TC only | COVERED
- T4 | probcut in check | notes/T04/TABLE.md:30 | Forge never probcuts in check (search.cpp:952-1027); Patricia PR 160 removal was neutral (+0.16, non-reg) - nothing to gain | COVERED
- T4 | history-based LMR | notes/T04/TABLE.md:35 | HAS for quiets (search.cpp:1146, LmrHistoryDivisor tunable); captures TRIED (LmrCapVictim H0, LmrTtCapAll) | COVERED
- T4 | TT-move cutoff rules | notes/T04/TABLE.md:15 (A4), :50 | TT cutoff only from an entry >= 1 ply deeper for lower bounds (Caissa d39fcfb 40+0.4 +2.11 +- 1.55, no STC) LACKS - no card (cap); TT move kept in a non-overwritten entry HAS (:293) | COVERED (no card: A4 is the best uncarded T4 row)
- T4 | qsearch futility | notes/T04/TABLE.md:47, :44, :39 | QsFutilityMargin is a lock tunable (retune / SPSA only, Caissa b8d85fe +2.74); stand-pat blend dropped (< +1); qsearch move-count pruning PREPARED (R15 C2) | COVERED
- T4 | NMP / LMR / RFP tweaks | cards T04-02, T04-03; notes/T04/TABLE.md:37-38, :45, :48-49 | LMR deeper/shallower (T04-02), NMP few-cutoffs discount (T04-03); RFP opp-worsening and fail-firm RFP TRIED; fractional LMR and small LMR terms table-only | COVERED
- T4 | history gravity | notes/T04/TABLE.md:34 | HAS (`apply_history`, search.cpp:157-160, int16 gravity; BUG_CHECKLIST row 14) - the row has no source and no logged Elo for a gravity variant (e.g. a different divisor / combined-history gravity); answered as "has it" only | COVERED (thin: no source number)
- T4 | terms that scale with TC | notes/T04/TABLE.md:52-65 (section C) | NMP discount grows with TC (overlapping CIs, verifier), triple ext only at long TC, LTC-tuned set flat at STC, history carry-over STC-only | COVERED
- T4 | patches that passed STC and failed LTC, and why | notes/T04/TABLE.md:58-62 | Caissa 74a0957 (history carry-over: STC +4.34, LTC +0.81), 836ffcf (fixed-node gain vanished), 439f454 (too small for LTC), SF b261df9 (correct fix failed a gain-bounded LTC); the "why" is the worker's own reading, not the sources' | COVERED (reasons labelled own reading)
- T4 | staged move picker, SEE caching, lazy legality | notes/T04/TABLE.md:50, :18 (A7), :21 (A10) | all three HAS (staged picker search.cpp:321-380, capture-stage SEE reused :1082/:1113, pseudo-legal + is_legal per move); remaining ideas: history-adjusted SEE split (Patricia PR 209 bundle), binary-heap ordering (speed) - no cards | COVERED
- T4 | deliverable: TABLE.md columns incl. "start value and range written by you" and Elo per build-hour rank; BUG_CHECKLIST 15-25 patterns | notes/T04/TABLE.md:10-21; notes/T04/BUG_CHECKLIST.md (21 rows) | present; T04-02 range differs card 0-200 vs TABLE 30-150 cp (verifier flagged, TABLE not changed) | COVERED (one open inconsistency)
- T4 | find the Altair repo and check its licence | notes/T04/licences.md; VERIFY.md:20-22 | Alex2262/AltairChessEngine, MIT at b2447b825b and at 6bddce6de2 | COVERED
### T5 (brief: tools/workflows/prompts_core2/research_T05.md)
- T5 | which inference tricks are bit-exact, and how big each is | notes/T05/SPEED_LIST.md:12-23 (bit-exact column) | 10 rows: int16 w1 store, one hot path, 2 MB pages, column prefetch, AVX-512 output kernel, history large pages, earlier TT prefetch = exact; integer SCReLU, int8 w1 / int16 accumulators = not exact | COVERED
- T5 | what is left after find-nnz sparse L1, weight alignment and TT-prefetch work | notes/T05/SPEED_LIST.md:20, :23, :25-35 | find-nnz / FTP1 / AccumTile = HalfKA path only; 64 B alignment neutral; earlier TT prefetch "unknown, likely < 1 %" (R7 SPRT capped +2.78) | COVERED
- T5 | WHY v2p4 runs at 0.85-0.89x the lock | notes/T05/V2P4_GAP.md:7-37 | P1 build 0.980 x P2 KB4 table+refresh 0.948 (not significant, verifier) x P3 layout (KB8 0.988 / KB32 0.942) x P4 unmeasured ~0.95-0.97 | COVERED
- T5 | AVX2 vs AVX-512 / VNNI | notes/T05/SPEED_LIST.md:18 (row 5), :23 (row 10), :26, :37-44 | updates already zmm (compiler); AVX-512 output kernel +0.3-1 % (dropped alone); VNNI only on the HalfKA path | COVERED
- T5 | int8 vs int16 L1 | notes/T05/SPEED_LIST.md:14 (row 1), :22 (row 9); card T05-01 | int16 w1 store exact (all values k x 2^-12); int8 w1 impossible (15-bit weights); int16 accumulators fail the bound (342,331 > 32,767). The brief's "L1" read as the first layer: the lock / v2 nets have no hidden L1 (SPEED_LIST:4-5) | COVERED
- T5 | accumulator refresh caches | notes/T05/SPEED_LIST.md:27-28; V2P4_GAP.md:52-54 | v2 has a per-worker cache per (perspective, bucket, flip); lock has no king buckets; nothing new proposed | COVERED
- T5 | lazy updates | notes/T05/SPEED_LIST.md:28-30 | lock and v2 walk back to the nearest valid ancestor; v2 lazy-root bug fixed 2026-11-04; T05-04 adds a column prefetch for the lazy update | COVERED
- T5 | weight permutation | notes/T05/SPEED_LIST.md:4-5, :33 | applies only to a hidden-L1 net (HalfKA path); FTP1 done | COVERED
- T5 | 64 B vs 2 MB alignment | notes/T05/SPEED_LIST.md:31-32; card T05-03 | 64 B neutral (FORGE_ALIGN_WEIGHTS within ~3 % A/A), v2 tables already 64-B aligned; 2 MB pages for v2 tables = T05-03 | COVERED
- T5 | TT prefetch placement | notes/T05/SPEED_LIST.md:20 (row 7); card T05-04 | lock prefetches the child cluster after make_move (search.cpp:847, :1126); earlier placement unknown, < 1 % likely, re-judge by ABBA; no outside source number | COVERED (no source number)
- T5 | uops.info and Agner data for vpdpbusd and vpcompressd on Zen 5 | notes/T05/SPEED_LIST.md:37-44 | VPDPBUSD zmm lat 3 / TP 0.5; VPCOMPRESSD reg TP 1.0, store 8 uops TP 3 (Zen 4 144 uops); register-form and Agner rows not re-opened by the verifier (VERIFY.md:66) | COVERED (partly unverified)
- T5 | compiler: BOLT on MSYS2 / Windows yes/no with source | notes/T05/SPEED_LIST.md:46-48; card T05-02 | NO - bolt/README.md line 12 @b53763029964 "operates on X86-64 and AArch64 ELF binaries" | COVERED
- T5 | deliverables SPEED_LIST (item, nps %, bit-exact, file:line, licence, microbenchmark plan) and V2P4_GAP (measured vs not, what closes each part) | notes/T05/SPEED_LIST.md:12; V2P4_GAP.md:21-62 | present, every part labelled measured / not measured | COVERED
### T1 (brief: tools/workflows/prompts_core2/research_T01.md)
- T1 | king-bucket maps with measured Elo | notes/T01/recipes.md:25-28; card T01-04 | bucket COUNTS with Elo (V v84 4 mirrored; V v91 16 + L1 2048 together 25k +31.64; I PR 256 16 buckets + HMC decoupled STC +4.23 / LTC +2.17); ours KB4-KB32 rank maps offline only. Map SHAPES (rank vs file / mirrored / centre-weighted layouts at equal count) are not compared anywhere | COVERED (partial: counts, not map shapes)
- T1 | piece-count output buckets | notes/T01/recipes.md:29-30 | V v86 eight material output buckets 25k +19.76 / STC +23.89, confounded with a larger dataset; OB8 already in our v2 layout | COVERED
- T1 | threat encodings | card T01-01 (Mechanism); recipes.md:20-22 | bullet example encoding (59,808 geometric (from, to) pairs, kings excluded, mirrored), V PR 425 60,144; count-valued O6 must be re-encoded binary | COVERED
- T1 | pairwise multiplication | notes/T01/recipes.md:31-32 | V v92 pairwise after L1 LTC +9.44 +- 4.12, confounded (new layer stack + feature permutation); "out of this track", no card | COVERED (thin, confounded only)
- T1 | L2 / L3 sizes | notes/T01/recipes.md:13, :20 | the brief itself excludes L2/L3 sweeps; only incidental (V PR 425 widened L2 16 -> 32 inside the threat PR) | COVERED (excluded by the brief)
- T1 | data size / L1 size / nps cost PER feature set | notes/T01/recipes.md:18-42 | L1 sizes given (2560 -> 1024, 768, 2048); nps only for threats (~87 % of old speed, V PR 425) and merged accumulator (+6 %, I PR 266); data size "not stated" for every external lever except Integral's "hundreds of millions of games"; no per-feature-set table of the three quantities | NOT COVERED as asked (partly: sources do not state data size; write it as missing in one table row per feature set)
- T1 | sparse threat inputs on the TRAINING side (our dense bundle ~51x slower) | card T01-01 (Mechanism, Forge fit) | loader computes threat indices per position from the board, GPU sparse affine gathers only active columns (cost ~ active x L1); runs on our ROCm bullet already; "51x" explanation is the worker's reading, not measured | COVERED
- T1 | dead-end card first if no bullet/HIP sparse recipe within 2 sources | card T01-01 | not needed: a HIP-capable sparse recipe was found (bullet da426a49 sparse affine already trains on our ROCm build) | COVERED (N/A)
- T1 | at most 3 bullet configs, ~1 GPU-day each, offline score check before any SPRT | card T01-03; notes/T01/recipes.md:44-61 | R1 pure-WDL stage (~1.5 GPU h), R2 + sparse threats (GPU unmeasured, bound 25-37 min per 6.7G positions), R3 R2 + Ranger; paired S31 + jobA rule fixed before the run | COVERED
- T1 | side-by-side recipe table (OUR npt, OUR bullet, open recipes: WDL + schedule, LR schedule, sigmoid scale, batch, superbatches, data size, L1, inputs) | notes/T01/recipes.md:7-16 | 6 rows with all columns; the owner's own bullet "sb08" recipe is only mentioned, not tabulated ("its recipe is not restated here") | COVERED (sb08 row missing)
- T1 | ranked recipes with source, licence, claimed Elo, GPU-hours, inference cost | notes/T01/recipes.md:53-57 | R1 > R2 > R3 with all columns; R2/R3 GPU hours and threat inference cost unmeasured (said so) | COVERED
### T2-card-1 (the owner's own wording was not available to the critic; questions as restated in FINAL_REPORT:12-21 / RESUME:13-15)
- T2-card-1 | which key makes the 4,088-key train/holdout overlap 0 | card T02-01 Mechanism 1 | board + stm (J1 FPOS rows carry no castling / EP / clocks; this key subsumes raw and EP-normalised 4-field) | COVERED
- T2-card-1 | which rows to drop, and the minimum | card T02-01 Mechanism 2 | all 7,700 train rows of BOARDSTM_TRIAGE_ROWS.tsv (minimum 4,118); dropping the 7,612 holdout rows rejected (would move every S31 number) | COVERED (T2 verifier recounted)
- T2-card-1 | rebuild + proofs before any training | card T02-01 Mechanism 3, Test plan | copy 37 train .pos without the records, same converter, 304,991,873 records; 5 PASS proofs (count, decode 7,700/7,700, 0 shared keys on 3 keys, seams, seals) | COVERED
- T2-card-1 | game-level split without game IDs | card T02-01 Mechanism 4; notes/T02/block_rule_012_015.json | derived blocks (result change or non-increasing ply); both seams are breaks, so 013/014 is block-aligned; new data needs the .games sidecar | COVERED
- T2-card-1 | cost on grok-pc | card T02-01 Effort | crew ~2 h, < 30 CPU-min (block pass extrapolated from 17.6 s / 16.6M rows), 10.37 GB on C: (F: floor) | COVERED
- T2-card-1 | within-train board+stm duplicates | card T02-01 Mechanism 5 | not measured (crew; not needed for the overlap) | NOT COVERED (stated as open in the card)
### T2 (brief: tools/workflows/prompts_core2/research_T02.md)
- T2 | in-check filter with measured Elo at fixed net size | notes/T02/TABLE.md:26-29 (Xiangqi paper, no Elo); MIX.md:5-6 | no source Elo found; Forge's writer already drops in-check rows (9.3 % of searches, T02-04 H2) | COVERED (no source number; not stated as an explicit "not found" row)
- T2 | capture-best-move filter | card T02-02; notes/T02/TABLE.md:13, :17-18 | SF PR 4314 capture pre-filter + ply skip, filter-only retrain STC +2.9 / LTC +2.85 (verifier); Forge already drops all capture best moves at write time; SEE >= 0 variant (row 6) needs regeneration | COVERED
- T2 | |eval| caps | notes/T02/MIX.md:6 (fact only); MIX.md:34 (Caissa opening |eval| cap, not a row filter) | no TABLE row, no source Elo for a row |eval| cap; Forge drops |cp| > 3000 at write time - nobody asked whether 3000 is the right cap | NOT COVERED (no source searched; write "not found" or one search)
- T2 | ply limits | card T02-02; notes/T02/TABLE.md:13, :21 | ply <= 28 skip (SF PR 4314 / nnue-pytorch PR 222), 28 -> 30 confounded; J1 stores a constant ply 40, so the cut needs the true ply at conversion (own start P = 20) | COVERED
- T2 | WDL skew | card T02-03; notes/T02/TABLE.md:15, :19 | read as the WDL-consistency skip (npt PR 155, confounded STC -0.44 / LTC +3.30); OFF in every w4 run IF `--no-wld-filtered` is that switch (verifier: UNVERIFIABLE). A draw-ratio / result-balance skew of the data is not discussed | COVERED (as WDL skip; result-balance reading not covered)
- T2 | relabel by deeper search of the same engine at fixed net size | notes/T02/TABLE.md:26-29 | not found (one search); Forge's own 20k-node relabel pilot has no gate | COVERED (dead end)
- T2 | relabel by a stronger teacher | notes/T02/TABLE.md:24 (row 12); MIX.md:40-47 (G1) | no clean number (SF 72/28 own/Leela mix, hex-edited net); recommendation G1 = lock exe as the self-play teacher | COVERED
- T2 | distillation | notes/T01/recipes.md:39-41 (T1, not T2); FINAL_REPORT:101-102 | V v110 distillation from a larger teacher LTC +3.69 +- 2.35; no card (no teacher net beats the lock offline) | COVERED (in T1 notes only)
- T2 | how engines move from external data to self-play (games, nodes per move, adjudication, retrain cadence, mix ratio); pipeline histories of at most 2 engines | notes/T02/MIX.md:17-37 | Stockfish (self-play -> Leela teacher, 72/28, depth 9 / 5000 nodes, new master every 1-5 weeks) and Caissa (external net -> own self-play, 21k soft nodes, Syzygy adjudication <= 5, progressive purge); tested mix ratio at fixed net size: missing in both (MIX.md:66) | COVERED
- T2 | the Leela one-liner (licence, size, URL) | notes/T02/TABLE.md:31-34 | ODbL 1.0, storage.lczero.org raw + robotmoon binpacks, 514 GB / 328 GB sets (4 lines, not one) | COVERED
- T2 | the WAC300 card (hypotheses + cheapest separating test) | card T02-04 | H1 speed / H2 data filter / H3 margin scale / H4 noise; equal-node WAC run decides (crew 0.5 h); title range 263-269 vs 271-272 is the owner's summary, unverifiable (OFF2 = 273) | COVERED
- T2 | deliverables TABLE.md (filter | Elo with conditions | link | licence | cost on grok-pc) and MIX.md (mix, nodes per move, generations) | notes/T02/TABLE.md:11-24; MIX.md:39-64 | present; GPU wall time per run PENDING (crew) | COVERED
- T2 | context: 305M "Lichess plus self-play" rows | notes/T02/MIX.md:8-12; card T02-02 Status | 304,999,573 = exactly the self-play J1 binpack; w4 trains on it alone; where the Lichess rows are: PENDING (crew) | COVERED (premise corrected, owner item)
### T6 (brief: tools/workflows/prompts_extra/research_T06.md)
- T6 | material scaling of the net output, per engine | notes/T06/FORMS.md:20-22, :38-41, :63-64, :73-74; card T06-01 | E3 one-sided single slope; SF piece factor + pawn term (two effects), Caissa piece phase without pawns, Patricia total material; T06-01 = two signed terms (NPM, pawns) | COVERED
- T6 | optimism terms | notes/T06/FORMS.md:23-26, :44-52; card T06-03 (a) | SF optimism before scaling (gain only at LTC), complexity-weighted, asymmetric version removed; Forge EvalOptimism=40 rerun H0 -> (a) waits for a refit | COVERED
- T6 | 50-move-rule damping | notes/T06/FORMS.md:27-28, :34-37, :67, :75; card T06-05 | SF 7b06475 / 3af083a, Caissa and Patricia linear; E3 D=30 gated +1.51, held-out optimum ~81 > option max 60 | COVERED
- T6 | draw handling | notes/T06/FORMS.md:14, :29, :32-33; DEAD_ENDS.md:4 | draws return 0 in the lock; SF draw jitter under +1 at STC/LTC (VLTC +2.5) -> dropped, DrawJitter ungated | COVERED
- T6 | complexity / winnable scaling | notes/T06/FORMS.md:53-55; card T06-03 (b); DEAD_ENDS.md:7 | SF 4c4cb18 decay +0.85 / +1.30; C = |residual| own definition; winnable HCE terms out of track | COVERED
- T6 | any other post-net transform with logged Elo | notes/T06/FORMS.md:42-43, :56, :61-77; cards T06-02, T06-04 | level-material re-weighting (a2f01c0), eval grain (d212e66); Caissa / Patricia transforms without numbers. NOT read: Altair (MIT) and the GPL engines' logs (Berserk, Obsidian, Stormphrax, PlentyChess, Alexandria) - FORMS.md:79-81 marks them PENDING | COVERED (3 engines only; rest PENDING)
- T6 | fit recipe on licence-clean data, licence of every dataset | notes/T06/FIT_RECIPE.md:7-14, :31-57 | own gate PGNs D1 main set, own self-play D2, relabel D3; Lichess D4 "CC0 per database.lichess.org - NOT re-checked (PENDING)"; UHO book provenance not re-checked | COVERED (Lichess licence still PENDING in the note -> answered by the critic: CC0, section at the end)
- T6 | only forms E3 lacks, or a better fit / combination (joint fit, per-phase scaling) | cards T06-01..05; FIT_RECIPE.md steps | per-phase scaling = T06-01; refit strength = T06-05; joint fit of the retained terms = FIT_RECIPE step 8 (line 52), K alone and jointly with MatScale (line 45) | COVERED
### T7 (brief: tools/workflows/prompts_extra/research_T07.md)
- T7 | at most 2 TM cards that are neither tmfit nor node-fraction TM, each with logged STC/LTC Elo | cards T07-01, T07-02 | time-disadvantage scaling (SF 5ca4bfe72b STC +1.13 / LTC +1.08), score-stability soft-limit scaling (Alexandria PR 438 STC +1.42 / LTC +1.71) | COVERED
- T7 | best-move stability scaling | notes/T07/sources.md:20 | lock has it (search.cpp:1436-1438) - no card | COVERED
- T7 | score-drop / falling-eval extension | notes/T07/sources.md:21; card T07-02 variant B | lock has it vs the previous iteration (1451-1454); cross-move reference only as T07-02 B, no separate logged gain | COVERED
- T7 | complexity-based scaling | notes/T07/sources.md:23 | SF 2b03723 (+2.44 / +1.30) simplified away by 38a80c0 -> no card | COVERED
- T7 | move-overhead handling | notes/T07/sources.md:28; UCI_EDGE_CASES.md:48-60 | no logged gain found; clamps 0..1000 box-tested | COVERED
- T7 | soft / hard limit ratios | notes/T07/sources.md:27 | lock tunables TmSoftDivisor / TmIncrementPercent / TmHardPercent / TmHardSoftMultiple = SPSA territory | COVERED
- T7 | ponder-hit handling | notes/T07/sources.md:28; UCI_EDGE_CASES.md:99-105 | no logged gain; cannot be gated with fastchess; edge cases 34-36 | COVERED
- T7 | tmfit / node-fraction exclusion check (gates 227/228 in gates_20261103.html) | notes/T07/sources.md:19 | pointer stale: grep tmfit = 0 hits in the report and FORGE_RESULTS.csv; brief taken as given | COVERED (owner item)
- T7 | UCI_EDGE_CASES.md (winc/binc only, movestogo, tiny increments, very low time, movetime/nodes/depth combos, increment > base, negative / missing fields) with expected behaviour + one-line test | notes/T07/UCI_EDGE_CASES.md:27-105 | 36 cases in 7 groups, each E: + Test:; 3 formulas re-derived by the verifier | COVERED
### T12 (brief: tools/workflows/prompts_extra/research_T12.md)
- T12 | SPRT bounds: normalised vs logistic Elo, [0,5] vs [0,2] vs [-1.75,0.25], expected games | card T12-01; notes/T12/PROTOCOLS.md sections 1-2; sprt_model.md | own Brownian-GSPRT model: [0,10] nElo mean 6.6k games, [0,5] nElo 26k, [0,15] 2.95k, [0,2] / [-1.75,0.25] ~165k; UHO 1 Elo = 1.91 nElo; decision probabilities are own-model, UNVERIFIABLE (T12 VERIFY:17) | COVERED
- T12 | pentanomial statistics (why pairs, variance reduction) | card T12-01 Mechanism; T12-05 | pair variance 0.618 of independent games on UHO (38 % saved), 0.90 on 8moves_v3 | COVERED
- T12 | book and TC choice (UHO vs balanced, STC/LTC pairs) | card T12-05; PROTOCOLS.md | keep UHO STC + 8moves_v3 confirm, never pooled; which book decides faster: unresolved (paired 6k-per-book study proposed); LTC 30+0.3 [0,15] cap 6k | COVERED (open question stated)
- T12 | SPSA for the top 20 search parameters (games, wall time at our rate, step sizes, iterations, how to pick the 20) | card T12-04; PROTOCOLS.md section 4 | 20 of 63 exposed (live, frequent, steep), 16.7k pairs = 33k games, ~33-67 h; own c_end / r_end | COVERED
- T12 | nps protocol for 1 % at 2-5 % A/A noise (pairs, one core with idle SMT sibling, boost / thermal, runs, statistics) | card T12-02; PROTOCOLS.md section 5 | fresh copy per run against the per-file bias, n = 8.6 s^2 pairs (35 / 78 / 215 at s 2 / 3 / 5 %), PERFBOOSTMODE logged; "2k / 2k+1 share a core" general rule UNVERIFIABLE (VERIFY:26) | COVERED
- T12 | ONE checklist card: bench-signature + fuzz proof (positions, depths, saturation, FENs, what to compare) | card T12-03 | 9 levels (pins, per-position info lines, 12k FENs, warm-TT replay, Hash 1 / 1024, ISA, differential verify build) | COVERED
- T12 | quantify bounds / caps that would decide the capped gates | card T12-01 Forge fit / Expected gain | 79 of 110 capped (55 at 1,500, 14 at 3,000, 9 at 1,000, 1 at 6,000); [0,10] cap 12k decides ~88 % at the ends, ~4-6x the CPU per gate | COVERED
- T12 | sources: pentanomial / normalised-Elo papers, uops / thermal guides | notes/T12/sources.md:28-30 | the fishtest-mathematics wiki and its linked PDFs are listed (normalized_elo_practical, sprta, GSPRT_approximation); thermal: LLVM benchmarking doc + Windows PERFBOOSTMODE doc; no uops / thermal measurement guide beyond these | COVERED

## Part B - report check (FINAL_REPORT.md sections 0-6, INTERIM of 23:40; line numbers of that file)
### Section 0
- FINAL_REPORT:15-16 | 7,700 rows = 0.0025 % of 304,999,573; minimum 4,118; 37 train shards | OK | T02-01 + T02 VERIFY:7-9 recounted | -
- FINAL_REPORT:17-18 | block rule "reproduces the R14 scan's break classes within 16 of 189k pairs" | CONTRADICTION | T02 VERIFY:11: 16 is the NET difference of all breaks (189,181 vs 189,197); per class the counts differ by 25 (result_mismatch) and 41 (ply gap), so >= 41 pairs are classified differently | write "reproduces the R14 break count within 16 of 189k (per class 25 / 41 apart)"
- FINAL_REPORT:19-20 | "under 30 CPU-minutes on one core (measured logs), 10.4 GB on C:, crew ~2 h" | OK with caveat | T02-01 Effort: convert 6:19 measured; block pass over 321M rows extrapolated from 17.6 s / 16.6M; probe re-scan 388 s UNVERIFIABLE (T02 VERIFY:14) | add "(block pass extrapolated)"
- FINAL_REPORT:20-21 | "The T2 verifier confirmed the card's numbers against the three files it cites" | OK (qualified) | T02 VERIFY:5-14: all confirmed except the net-only "16 pairs" and two effort figures not in those files | add "except the per-class split and two effort figures"
### Section 1 (metric, table, G-class list, gate order)
- FINAL_REPORT:26-27 | nps -> Elo "Elo_STC = 2.10 x for x % nps" | UNSOURCED in the cards | only in F:/odr/prev_research_20261030.md:89-91 (SF wiki "Useful data", which also gives Elo_LTC = 1.43 x); the only "2.10" in the notes (T12 PROTOCOLS.md:18) is the 8moves_v3 nElo/Elo ratio, a different quantity | cite the 30-Oct file + wiki URL; note the LTC factor
- FINAL_REPORT:32 (row 1 T06-05) | crew h 0.5 -> 3.0 per crew-h | UNSOURCED | the one-line card T06-05 has no effort field ("same exe, no rebuild" only) | put the hours in the card or mark them as the coordinator's estimate
- FINAL_REPORT:36, :40, :41 (T04-05 1 h, T04-06 2 h, T04-04 4 h) | crew hours | UNSOURCED | one-line cards carry no hours; notes/T04/TABLE.md:6 says "cards give both" but the table gives only "lines to touch" (1 / ~3 / ~40) | same
- FINAL_REPORT:38 (row 7 T05-04) | crew h 1.5 | UNSOURCED | the one-liner and SPEED_LIST row 4 have no effort | same
- FINAL_REPORT:37 (row 6 T04-03) | per crew-h 1.0 | MISMATCH (metric) | card ranges STC 0..+2 (midpoint 1 -> 0.5) and LTC +1..+4 (2.5 -> 1.25); 1.0 = midpoint of the union 0..+4 | say which range the rank uses
- FINAL_REPORT:37 + :54 | T04-03 "decide at LTC" / gate order "(4) T04-03 straight to the LTC decision" | CONTRADICTION | card T04-03 Test plan = STC [0,5] then LTC (do not stop on an STC H0); T04 VERIFY:49: the TC trend is only suggestive (95 % CIs 2.81-9.09 vs 0.59-3.41 overlap; both SPRT-stopped, biased up) | "STC as a no-loss check, LTC decides; the TC trend is suggestive only"
- FINAL_REPORT:35 (row 4 T05-01) | evidence "(P2 = 0.948 for KB4 tables)" | CONTRADICTION | T05 VERIFY:22, :71 and the card's verify note: a ratio of two single ~+-3 % probe runs; bench ABBA 0.968, CI 0.900-1.040, includes 1.0; the 30-h job read it as "cost little" | add "(not significant: size P2 with fresh copies before building)"; the ~1.7 per crew-h rests on it
- FINAL_REPORT:33 + :53 | T04-02 "best evidence: two engines, STC and LTC" | MISMATCH (minor) | an LTC run exists for Caissa 434bbda only; Patricia PR 137 is 8+0.08 only (card T04-02) | "two engines at STC, one at LTC"
- FINAL_REPORT:33-41 | source numbers of T04-01/02/03/04/05/06, T05-03, T06-05 | OK | T04 VERIFY:4-16; T05 VERIFY:34-38; T06 VERIFY:16, :21 | -
- FINAL_REPORT:44-45 | T01-06 "crew ~0.5 h, ~1.5 GPU h" | UNSOURCED (crew part) | ~1.5 GPU h = T01-03 R1 Effort (OK); T01-03 says R1 needs "no crew code", the T01-06 one-liner has no effort | add the crew figure to the card or mark it
- FINAL_REPORT:44-46 | T02-03 crew 0.5 h / 0..+3; T02-02 crew 2-4 h / 0..+5; T01-03 R2 crew 8-12 h / 0..+5 | OK | cards T02-03, T02-02, T01-03 Effort / Expected gain | -
- FINAL_REPORT:50 | gate rate 430-502 games/h (*_vs_AL1*, T07 verifier); 497 games/h at Threads 2 / conc 4 | OK | T07 VERIFY:44; T12 PROTOCOLS.md:85 | -
- FINAL_REPORT:50-51 | T12-01 [0,10] nElo cap 12k, mean ~6.6k games, ~13 gate-hours | OK (arithmetic) but own model | T12 VERIFY:17: decision probabilities UNVERIFIABLE (own model, not re-simulated) | label "model, not replayed"
- FINAL_REPORT:51-52 | "the gates as run (caps 1,500-3,000) left 79 of 110 undecided" | MISMATCH (minor) | T12-01 Forge fit and TRIED_GATES.md (recounted here): 55 capped at 1,500, 14 at 3,000, 9 at 1,000, 1 at 6,000 | "caps 1,000-6,000 (55 of the 79 at 1,500)"
- FINAL_REPORT:49-57 vs every card's gate route | "UHO SPRT [0,5] at STC, then LTC" | CONTRADICTION (cross-track: bound unit) | T12-01: [0,5] read as nElo = mean 26k games (53 h), "not reachable with any cap the queue has used"; T07-01 / T07-02 cost [0,5] at 7-12k / 7-18k games (i.e. logistic Elo, ~[0,9.5] nElo); the gates actually ran [0,10] nElo | state the unit of [0,5] and that the owner's bounds decision (item 6.2) replaces every card's route
- FINAL_REPORT:56-57 | "Before any npt or v2 retrain: the T02-04 WAC diagnostic (0.5 crew h)" | OK (minor wording) | T02-04 Effort 0.5 h; the card is about npt nets only | "before any npt retrain"
### Section 2
- FINAL_REPORT:60 | T06-04 "2 h" -> 0.63 | UNSOURCED | one-line card, no effort | as above
- FINAL_REPORT:61-62 | T06-01 4 h + ~14 h SPSA -> 0.5; T06-02 3.5 h -> 0.43; T06-03 4 h -> 0.19 | OK | cards: 2+2 h, 1.5+2 h, 2+2 h; the 437 games/h behind "~14 h" is a Threads=2 gate (T06 VERIFY:23, card notes) | -
- FINAL_REPORT:62-63 | T07-02 "+1 to +3; 3.5 h) 0.43" | MISMATCH (metric) | the midpoint of +1..+3 is 2 -> 0.57; 0.43 uses the card's "centre about +1.5" | one rule for all rows (midpoint, or the card's stated centre)
- FINAL_REPORT:64-65 | T07-01 numbers and 0.33 | OK | card T07-01 + T07 VERIFY:5-7 | -
- FINAL_REPORT:66-67 | T05-02 "0.71x -> 1.0x; +0 to +2 %; 4-8 h ~0.35" | OK | T05 VERIFY:48 (v2.5 1.066, CI 0.987-1.152, written ~1.0x) | -
- FINAL_REPORT:68-69 | G list: T01-04 ~0.5, T01-05 ~0.5, T02-06 ~0.75, T02-05 ~0.25 | UNSOURCED (crew hours) | the one-line cards carry no crew hours (T02-06 gives ~5 h of datagen only) | as above
- FINAL_REPORT:69 | "T01-01 / T01-03 R2 ~0.31" | OK for T01-01 (6-10 h, mid 8); T01-03 R2 says 8-12 h (mid 10 -> 0.25) | cards | name the card the hours come from
- FINAL_REPORT:68-69 | T02-03 ~3.0, T02-02 ~0.8, T01-02 ~0.33 | OK | cards (0.5 h / 0..+3; 2-4 h / 0..+5; 1-2 h / 0..+1 warm start) | -
- FINAL_REPORT:72 | T12-04 "~16.7k pairs to resolve 2 Elo" | OK | card T12-04 | -
### Section 3
- FINAL_REPORT:76-77 | "the ~1,000 games/h at conc 8 in the T04 cards and T12-04 is an older / unmeasured rate" | CONTRADICTION | T04 VERIFY:32 CONFIRMED it as measured (R7 J4: 996-1002 games/h at conc 8, Threads 1, 28.3 s per game); a third rate, ~437 games/h (Threads 2, conc 4), sits in T06-01/02/03 | "an older measured rate (R7 J4, Threads 1, conc 8), not the current UHO *_vs_AL1* setting"
- FINAL_REPORT:78-79 | "post-root-fix control -20.9 +- 18.5 (v2p4 + lock-as-KB4 vs the lock, 30-h report)" | UNSOURCED detail | D:/o30/FINAL_REPORT.md:28-29 says "the same exe playing the lock net itself = 47.0 %, -20.9 +/- 18.5; sanity only" - no "as KB4"; it is a ~400-game sanity match | drop "as-KB4" (or cite where it says so); add "sanity only"
- cards T01-01 / T01-03 (verify notes) vs notes/T05/V2P4_GAP.md:3-4 | T01 verifier: "no control of the root-fixed exe" exists; T05: v2p4 = patch 926ada2c WITH the root fix, and its control is the -20.9 | CONTRADICTION (cross-track, v2 control) | the report's reading (-20.9 = post-fix) is the consistent one; correct the two T01 verify notes
- FINAL_REPORT:80-82 | T5 decomposition P1 ~0.98 x P2 ~0.95 x P3 x P4 ~0.97, 60-80 % explained | OK (numbers) with missing caveats | V2P4_GAP.md:24-36; T05 VERIFY:22, :70-71: P2 not significant; P1 may hold the per-file effect (BH-8, up to 3-5 %); P4 is 0.95-0.97 depending on the P2 used | add both caveats
- FINAL_REPORT:83-84 | Zen 5: VPDPBUSD zmm lat 3 / 0.5 c; VPCOMPRESSD register 1.0 c; store 8 uops (Zen 4 144) | OK (register row not re-checked) | SPEED_LIST.md:40-42; T05 VERIFY:64-66 (register form + Agner rows UNVERIFIABLE in the time box) | mark the register row "not re-checked"
- FINAL_REPORT:84 | BOLT: "operates on X86-64 and AArch64 ELF binaries" @b5376302 | OK | T05 VERIFY:51 | -
- FINAL_REPORT:85-87 | data premise: J1 = 304,999,573 self-play rows; w4 lambda 1.0 / 1.0; the `--no-wld-filtered` identity unconfirmed | OK | MIX.md:8-12; T02 VERIFY:24, :85 | -
- notes/T01/VERIFY.md:38 vs card T02-01 / MIX.md:8 | "our data is 305M rows" UNVERIFIABLE (T01) vs 304,999,573 J1 rows (T02-01, from D:\a14) | OK cross-track (resolved) | T02-01 is the source the T01 verifier did not find | cite T02-01 in T01-03 / recipes.md:47, :60
- FINAL_REPORT:87-88 | npt nets at 0.47-0.58x the OFF nps; "a large share of their -86 to -116 Elo vs AL1 can be speed" | OK (hedged) | verifier-corrected range (T02 VERIFY:35); the speed share is T02-04's H1, untested | say "(H1 of T02-04, untested)"
- FINAL_REPORT:89 | self-play 6.2.0 HCE at 5,000 nodes; MIX.md's first recommendation = the lock as teacher | OK | MIX.md:4, :40-41 | -
### Section 4
- FINAL_REPORT:92 | "losing captures last (search.cpp:396-398)" | MISMATCH (minor) | notes/T04/TABLE.md:50: BadCaptures stage :397-398 (enum :433-435); lock: the bad-capture return is at :398 (re-grepped) | 397-398
- FINAL_REPORT:93-94 | qsearch TT 50-move guard TTEntry::score_usable search.hpp:83-86 | OK | BUG_CHECKLIST row 12; lock search.hpp:83 (re-grepped) | -
- FINAL_REPORT:97-98 | "Already tried or prepared (dropped): ... negative extensions, ..., IIR" | MISMATCH (wording) | TABLE.md:29, :41: the lock HAS negative extensions (-2/-1, search.cpp:1107-1111) and IIR (:1031); only variants are PREPARED (deeper negative extensions in SingularV2; IirShallowTt R15 C4) | "has negative extensions and IIR; their variants are prepared"
- FINAL_REPORT:91-98 (rest) | probcut never in check, history kept across moves, TT move kept, TM stability / falling eval, v2 refresh cache, writer drops, E3 options | OK | TABLE.md:30, :46, :50; T07 sources.md:20-21; SPEED_LIST.md:27; MIX.md:5-6; FORMS.md:18-29 | -
### Section 5
- FINAL_REPORT:105 | dead end "shared correction tables (SMP only)" | CONTRADICTION (cross-track: Threads) | TABLE.md:85 makes it conditional on gates with Threads > 1, and item 6.1 says the UHO gates' RUN_INFO use Threads=2 (Caissa 24fde49: +6.12 +- 3.34 at Threads=4, 5+0.05) | "dead only for Threads=1 gates; a candidate if the owner keeps Threads=2"
- FINAL_REPORT:101-105 (rest) | merged king planes, wider L1, distillation, from-scratch threat nets, same-engine relabel, complexity / eval-level TM, asymmetric optimism, draw jitter, int16 accumulators, int8 w1, BOLT | OK | recipes.md:28, :33-34, :39-41, :59-61; T02 TABLE.md:26-29; T07 sources.md:23-24; T06 DEAD_ENDS.md:3-4; SPEED_LIST.md:22, :46-48 | -
### Section 6
- FINAL_REPORT:108 | Threads: brief = 1, UHO gates' RUN_INFO and R15 INDEX = 2 (conc 4) | OK | T06 VERIFY:23 (RUN_INFO "threads": 2), T12 PROTOCOLS.md:4, :85, T04 TABLE.md:85 | add that the decision also changes the T04 card costs (Threads 1 / conc 8) and the T12-04 SPSA plan (Threads=1)
- FINAL_REPORT:109-118 | items 2-8 (bounds / caps, EvalOptimism=40 H0, Viridithas v20.0.0 MIT, lambda / Lichess rows, Syzygy files + tmfit pointer, bad_captures_, C:\o13) | OK | T12-01; T06 VERIFY:19-20; T01 VERIFY:64 + recipes.md:16; MIX.md:8-12; T02-05 + T07 sources.md:19; lock search.cpp:361 write and :453 64-entry std::array (re-grepped) + BUG_CHECKLIST row 9 OPEN; STATUS.md | item 7: the checklist says "likely unreachable; prove it or add the guard" - "crafted promoted-piece positions" is the coordinator's reading
### Header / other cross-track checks
- FINAL_REPORT:3-5 | "T12 is researched, its verifier was still running" | MISMATCH (stale) | STATUS.md track table: T12 VERIFIED (verify 23:30-23:40; notes/T12/VERIFY.md totals 51 checks) | update the state line
- FINAL_REPORT:139-140 (section 8, outside 0-6) | "the first (stopped) run and the extra workflow are not summed yet" | MISMATCH (stale) | STATUS.md: core + extra = 2,952,180 agent tokens | update
- card T04-02 vs notes/T04/TABLE.md:12 | LmrDeeperMargin range 0-200 cp vs 30-150 cp | CONTRADICTION (open) | T04 VERIFY:61 (TABLE not changed) | align TABLE and card
- card ids / titles cited in the report | 34 ids | OK | every id in sections 1-2 exists as a card file with the same idea (T01-01..06, T02-01..06, T04-01..06, T05-01..04, T06-01..05, T07-01..02, T12-01..05) | -

## Answered by the critic (one source)
- T6 | Lichess database licence (notes/T06/FIT_RECIPE.md:13 D4 "CC0 ... NOT re-checked, PENDING") | https://database.lichess.org/ fetched 23:56 PC clock | page-wide statement "Database exports are released under the Creative Commons CC0 license."; the standard-games section itself was not in the part of the page read (first 100k of 267k characters) | answered by the critic: D4 = CC0 confirmed at the source; the FIT_RECIPE row can drop PENDING

## Uncovered or partly covered questions (pulled out of Part A)
- T1: data size / L1 size / nps per feature set as one table - NOT COVERED (sources state no data size; write "missing" per row).
- T1: king-bucket map SHAPES at an equal bucket count - partial (bucket counts only).
- T1: pairwise multiplication - one confounded number (V v92 LTC +9.44), no card.
- T1: the owner's bullet "sb08" recipe is not a row of the side-by-side table.
- T2: |eval| caps - NOT COVERED (no row, no search; Forge's |cp| > 3000 drop is stated only as a fact).
- T2: in-check filter - no source Elo found, but not written as an explicit "not found" row.
- T2: WDL skew - read only as the WDL-consistency skip; a result-balance (draw-ratio) skew is not discussed.
- T2-card-1: within-train board+stm duplicates - NOT COVERED (open by design, a crew measurement).
- T4: history gravity - "has it" only; no source number for a gravity variant.
- T5: TT prefetch placement - no outside number (only the R7 capped SPRT +2.78).
- T5: VPCOMPRESSD register-form and Agner rows - not re-checked by the T05 verifier.
- T6: Altair (MIT) and the GPL engines' logs for post-net forms - PENDING (FORMS.md:79-81).
- T12: which book decides a patch faster - unresolved (a paired 6k-games-per-book study is proposed).

## Summary
The owner's brief text was not in the critic's message; the track briefs relayed to the workers
(tools/workflows/prompts_*/research_T*.md) served as the question list, T2-card-1 as restated in FINAL_REPORT / RESUME.
Part A: 82 rows over 8 tracks; 3 NOT COVERED (T1 per-feature-set table, T2 |eval| caps, T2-card-1 within-train
duplicates), about 20 covered with a qualifier (thin, partial, no source number). Part B: 51 rows - 27 OK (several
with a caveat), 8 MISMATCH, 8 UNSOURCED, 8 CONTRADICTION. Findings that change the ranking or the gate route, not only
the wording: (a) T05-01's P2 = 0.948 is not significant per the T05 verifier, and rows 4 and 7 (~1.7 per crew-h) rest
on it; (b) T04-03's 1.0 per crew-h uses the union range 0..+4, and the gate order "straight to LTC" overrides the
card's STC-then-LTC route although the T04 verifier calls the TC trend only suggestive; (c) the unit of "[0,5]" -
every card's route vs T12-01 (26k games mean at [0,5] nElo, never reachable) vs T07 (7-18k games) - is the one
cross-track item the owner must settle before any line is queued; (d) 11 ranked items (T06-05, T04-04/05/06, T05-04,
T06-04, T01-04/05/06, T02-05/06) use crew hours that no card states (one-line cards have no effort field); (e) the
"~1,000 games/h unmeasured" wording contradicts the T04 verifier (measured in R7 J4), and the cards use three rates
(1,000 / 437 / 430-502 games/h); (f) the "shared correction tables (SMP only)" dead end contradicts owner item 1
(UHO gates run Threads=2); (g) "break classes within 16 pairs" is a net figure (per class 25 / 41 apart); (h) the v2
control "lock-as-KB4" is not in the 30-h report, and the T01 verify notes contradict V2P4_GAP on whether a root-fixed
control exists. Answered by the critic from one source: the Lichess database exports are CC0.
Finished 23:59 PC clock (`date`); temporary files only in F:/odr/work/CRITIC/ (partB.md, partB_rows.txt).
