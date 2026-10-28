# R3-3 Gate proposals for the opus-r3-stack features

One ready gate entry per feature, ranked, with a new srand each. **Proposals only:** no gate was started, and nothing was written to the gate queue (`autorestart\forge_gates.json`), `forge_push`, `F:\forge_push` or any lock folder. PC files were read through copies. Expectations are labelled as such; **there is no Elo claim.**

- **Stack:** the entries were checked on `opus-r3-stack` @ `2047348a` (probe build of the default recipe, sha256 `893ea34d…`, identity ALL OK, every runtime option's ON pins measured at d11-d22). Final head and exe sha256: section 6 (**pending: filled when the main session reports the final exes**).
- **Shape of every entry:** one change against the all-OFF engine. Candidate = `forge_r3_stack.exe` + one runtime option, or `forge_r3_<switch>.exe` (+ that switch's own option where it has one). Opponent = `forge_r3_base.exe` (the same default build) without options, named `base_r3_off`.
- **Files:** this document; `GATE_ENTRIES.json` (the same 29 manifest objects, ready to append by the owner); `SRAND_CHECK.md` (how the srands were checked).
- Machine exclusive: no (pins and scans ran at nice 19 next to a conc-8 gate, NNUE training and self-play).

## 1. Settings shared by every entry (from the live runner, read-only copy)

| setting | value | source |
|---|---|---|
| runner | `forge_queue.ps1 v3-6day r7` (`C:\Users\Administrator\grok-pc\forge_push\autorestart\forge_queue.ps1`, copy sha256 `636b6cca691d0707`) | runner header |
| fastchess | 1.8.2, `C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe` | runner `$FC` |
| time control | `tc=10+0.1 timemargin=1000` on both engines (entries may set a per-gate `tc`; none does) | Build-Args, `6_gate/GATE_RULES.md` |
| engines | `option.Threads=1 option.Hash=16 option.OwnBook=false` on both sides; SMP entries R3-21..23: `Threads=4 Hash=64` on both sides | Build-Args (hard-coded), O1 / O1-LTT REPORTs |
| openings | `C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn` (sha256 `5835239F…`, 34,700 openings) `format=pgn order=random start=<entry>`; starts 390001 + 3000·(n−1) (live manifest max 366001; 369001-387001 left for automatic confirm gates) | runner `$BOOK`, manifest convention (+3000 per gate) |
| games | `-games 2 -repeat -rounds 750`: **cap 1500 games** = 750 colour-reversed pairs, pentanomial | runner `$ROUNDS` |
| SPRT | `-sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized` (manifest `"sprt": {"elo0": 0, "elo1": 5, "nonreg": false}`); LLR bounds ±2.94 | user spec; PC alpha/beta/model |
| concurrency | 8, as G122-G125 and G28-G47 (SMP entries: 2, i.e. 2 games × 4 threads = the same 8 busy threads) | manifest |
| priority / CPUs | BelowNormal, affinity `0xFFF0` (CPUs 4-15; CPUs 0-3 belong to the NNUE trainer) | runner `$AFF` |
| output | `F:\forge_push\<tag>\` (new gate folders since 2026-10-27): `<tag>.pgn`, `<tag>.log`, `engine_io.log`, `RESULT.md`, `RUN_INFO.json` | runner `$DNEW` |
| other args | `-ratinginterval 10 -recover -event forge_<tag> -pgnout file=…\<tag>.pgn timeleft=true -log file=…\engine_io.log level=warn engine=true append=false` | Build-Args |
| exes | the runner only starts `C:\Users\Administrator\grok-pc\forge_push\bin\<exe>` and checks its sha256 (Preflight). The main session builds them in `F:\opus_scratch\r3\exe\`; **the owner copies them to `bin\`** (not done here) | Preflight |
| runner checks | pre-gate bench d11/13/16/20/22: cand OFF must equal `prebench.cand_off`, cand ON `prebench.cand_on`; `uci` must advertise each option; static arg check (base exactly Threads/Hash/OwnBook, candidate those plus exactly the entry's options); `engine_io.log` setoption check after game 1, game 10 and at the end (VOID rule) | Run-Gate, Static-ArgCheck, Void-Check |
| ok flag | each entry waits for `C:\Users\Administrator\grok-pc\forge_push\CR_PASS_r3_<slug>.ok` (Code Review writes it); without it the runner holds the gate | Gate-Status |
| held entries | SMP, blocked-net and pending-merge entries carry `"status": "HELD_…"`, so the runner holds them even if appended unchanged | Gate-Status (`^HELD`) |
| confirm | `confirm_first: true`: an H1 queues one confirm gate right after (fresh srand and openings, cap 1500); with `longer_tc_confirm_if_h1: true` the confirm runs at the runner's `$LONG_TC` = 60+0.6 | H1-Confirm |
| early stop | net entries only (crew rule): first block ≥ 750 games with Elo < −8 and LLR < −1.5 → H0-early | EarlyStop-Eval |

## 2. What happens at the cap, and what 1500 games at [0,5] can decide

- **At the cap:** after 1500 games with the LLR inside (−2.94, +2.94) the runner writes the verdict "Cap with no decision (LLR … inside (−2.94, 2.94)); nothing claimed", queues nothing and moves to the next gate. The Elo ± in RESULT.md is information only (GATE_RULES.md wording: "cap with no decision"). Results are never pooled; a re-run is a new gate with a new srand.
- **Approx model (not fastchess figures):** normal approximation of the normalized GSPRT, checked after every pair, 20000 simulated runs per true value (`tools/sprt_cap_model.py`, seed 20261027). fastchess uses the exact constrained-MLE GSPRT, which differs by up to about 0.1 LLR near H1 stops (forge-gate-stats skill).
- **Units:** the bounds are in normalized Elo (nElo). On this PC's draw-heavy gates nElo ≈ 2.1 × Elo (median of 45 ledger rows with |Elo| ≥ 3, range 1.5-2.4; e.g. G125: Elo 6.02, nElo 11.85).

| true nElo | [0,5]: P(H1) | P(H0) | P(cap) | mean games | [0,10]: P(H1) | P(H0) | P(cap) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| -20 | 0.000 | 0.004 | 0.996 | 1500 | 0.000 | 0.618 | 0.382 |
| -10 | 0.000 | 0.000 | 1.000 | 1500 | 0.000 | 0.217 | 0.783 |
| -5 | 0.000 | 0.000 | 1.000 | 1500 | 0.000 | 0.092 | 0.908 |
| +0 | 0.000 | 0.000 | 1.000 | 1500 | 0.002 | 0.032 | 0.967 |
| +5 | 0.000 | 0.000 | 1.000 | 1500 | 0.008 | 0.008 | 0.985 |
| +10 | 0.000 | 0.000 | 1.000 | 1500 | 0.030 | 0.002 | 0.968 |
| +20 | 0.001 | 0.000 | 0.999 | 1500 | 0.213 | 0.000 | 0.787 |
| +30 | 0.017 | 0.000 | 0.983 | 1498 | 0.624 | 0.000 | 0.376 |
| +50 | 0.537 | 0.000 | 0.463 | 1389 | 0.993 | 0.000 | 0.007 |

- To end with H1 **at** the cap, [0,5] needs an observed score of about **+50 nElo** (H0: -45); [0,10] needs +29 (H0: -19). With [0,5] the LLR moves about half as fast as with [0,10] for the same data.
- PC ledger (FORGE_RESULTS.csv copy, 57 rows, mostly [0,10]): option gates (candidate options set) ended cap 23, H0 1; all gates cap 44, H1 8, H0 3, H0-early 2.
- **Regressions:** a true −20 nElo (about −10 Elo here) ends H0 in 0.4% of [0,5] runs but 62% of [0,10] runs (approx model): with [0,5]/1500 the SPRT gives almost no early warning of a small regression, so read the final Elo ± of every capped run (RESULT.md) before acting on it.
- **Expectation (approx model):** for the effect sizes these features can plausibly have (node-exact speed-ups of 0-4%, small search changes), almost every entry is expected to end "cap with no decision"; only a large gain or loss decides. The crew held a [0,5] gate for this reason (manifest entry e32c: "needs a driver with per-gate cap_games", r7 hard-codes the 1500 cap). The owner keeps the user's [0,5]/1500 spec or changes it (section 7).
- On an H1 the runner's verdict text is hard-coded "H1 accepted (SPRT [0,10] normalized, …)"; the settings line and the LLR line of RESULT.md show the real [0,5] bounds.

## 3. Ranking and recommended run order

Ranked by expected gain against risk (expectations, not measurements). Tiers: **A** node-exact speed or no search change (small but safe), **B** tree-changing search/eval (uncertain), **C** SMP-only (needs Threads 4 on both sides), **D** needs a trained net (blocked). The run order is the ID order; IDs 01-20 can run in the r7 queue as they are (R3-15 conditional, R3-20 held), 21-23 need the runner change, 24-29 need nets.

| rank / ID | feature | tier | expected gain (expectation) | risk | status | reason |
|---|---|---|---|---|---|---|
| R3-01 | FORGE_NNUE_O2 (O2 NNUE accumulator kernels) | A | small positive (largest measured node-exact speed-up of the set) | low | ready for the r7 queue (after exe install + CR ok flag) | bit-identical NNUE output (1.3M-position parity, 0 differences), about +3.3% to +3.6% bench NPS on idle CI runners |
| R3-02 | FORGE_NOZERO_MOVE_BUFFERS (S14 follow-up: no zero-fill of the move buffers) | A | small positive | low (node-exact; relies on never reading an unwritten buffer slot, which was audited and tested) | ready for the r7 queue (after exe install + CR ok flag) | node-exact; +1.25% to +2.70% CPU NPS on four quiet-runner samples (5 of 8 CIs exclude 0) |
| R3-03 | CorrHistPlus=4 (non-pawn correction history, C2 bit 4) | B | uncertain, plausibly small positive | medium (ON cost about 1-3% NPS per bit; tree change) | ready for the r7 queue (after exe install + CR ok flag) | the related NonPawnCorr+PawnHist pack ended with a positive LLR in all 4 of its PC gates (0.63-2.48 at [0,10], all capped); no test-plan row |
| R3-04 | CorrHistPlus=1 (continuation correction history, C2 bit 1) | B | uncertain, plausibly small positive | medium (large deep-tree change: d22 -43%; ON cost about 1-3%) | ready for the r7 queue (after exe install + CR ok flag) | test-plan idea G-B1; related ContCorrectionWeight=60 gate (G87) capped at LLR 0.68 |
| R3-05 | CorrHistPlus=2 (minor-piece correction history, C2 bit 2) | B | uncertain | medium (d20/d22 trees grow +12.6% / +18.9%) | ready for the r7 queue (after exe install + CR ok flag) | test-plan idea G-B2; deep-tree growth is the crew flag for a longer-TC confirm |
| R3-06 | CuckooRep (upcoming-repetition detection, C6) | B | uncertain, plausibly small positive | low-medium (about 1% per-node cost; history-dependent draw bound) | ready for the r7 queue (after exe install + CR ok flag) | standard technique, contained effect (draw bound only); OFF path instruction-identical to the lock |
| R3-07 | SyzygyPath (own Syzygy WDL/DTZ probing, 3-4-5-man tables; SyzygyProbeDepth=1 and Syzygy50MoveRule=true stay at their defaults) | B | uncertain, plausibly small positive (acts only in positions with at most 5 pieces) | low-medium (probe cost in small endgames; table folder must stay readable) | ready for the r7 queue (after exe install + CR ok flag) | only the candidate probes (opponent has no tables), tablebase adjudication stays off as C1 asks |
| R3-08 | HistRework=2 (correction/history rework, A1) | B | uncertain | medium (tree change; d22 -16.1%) | ready for the r7 queue (after exe install + CR ok flag) | A1 plan: first gate of the three levels (smallest node change, passes the crew +10% screen at d13/d16) |
| R3-09 | CorrMargins=1 (correction-size pruning margins, O5) | B | uncertain | medium (four pruning margins move at once; d22 -34.5%) | ready for the r7 queue (after exe install + CR ok flag) | test-plan idea G-B3; O5 notes correction terms tend to gain more at longer TC |
| R3-10 | FORGE_SPEEDSTACK (S29: S11 material-key table + S13 child TT prefetch, compile time) | A | about zero (speed-up under 1%) | low | ready for the r7 queue (after exe install + CR ok flag) | node-exact; quiet runner +0.18% d16 / +0.50% d20; makes R3-16 and R3-17 redundant |
| R3-11 | NetScale=99 (eval-scale mapping, S41) | B | about zero | low (1% eval rescale; single bench depths move up to 14.6%, total tree size unchanged) | ready for the r7 queue (after exe install + CR ok flag) | S41 found the AL1 net +1.2% above h256_e12 scale; 99 maps it back |
| R3-12 | IntendedThreefold (FIDE 9.2.1 claim in search, S-IT) | B | about zero (fires only with repeated keys in the game history) | low-medium (1.10-1.17x CPU per node inside shuffling subtrees) | ready for the r7 queue (after exe install + CR ok flag) | bench positions have no game history, so ON bench = OFF; effect only in games with repetitions |
| R3-13 | HardDeadline=10 (watchdog bestmove deadline, C3) | A | about zero (no search decision changes while the engine answers on time) | low | ready for the r7 queue (after exe install + CR ok flag) | C3 expects a gate to measure only noise; its value is time safety on a starved machine |
| R3-14 | CorrExt=1 (correction-history extensions, O8) | B | uncertain, weak at 10+0.1 | medium (extensions compound with depth; the idea "lost at STC" in the source report) | ready for the r7 queue (after exe install + CR ok flag) | the test plan and O8 make 40+0.4 the primary gate; at the PC's usual 10+0.1 it is informational |
| R3-15 | HistRework=3 (A1, level 3) | B | uncertain | medium (d20 tree +26.4%: crew flag) | ready, conditional (see notes) | A1 plan: run only if R3-08 (HistRework=2) ends H1 or capped with Elo > 0 |
| R3-16 | MaterialKeyTable (S11 node-exact material key, runtime option) | A | about zero | low (key equality proven on all count vectors) | ready for the r7 queue (after exe install + CR ok flag) | no measurable speed effect on PC or runner; already contained in FORGE_SPEEDSTACK (R3-10): skip if R3-10 runs |
| R3-17 | FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true (S13) | A | about zero | low | ready for the r7 queue (after exe install + CR ok flag) | node-exact; quiet runner d16 +0.00%, d20 -0.11%; also contained in FORGE_SPEEDSTACK (R3-10): skip if R3-10 runs |
| R3-18 | FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true (S12 null-edge accumulator alias) | A | about zero (counted saving about 0.07% of bench time) | low (node-exact; the switch build also counts evaluations for its stats line) | ready for the r7 queue (after exe install + CR ok flag) | S12 itself proposes no gate: no measurable effect within +-0.4% on a quiet runner |
| R3-19 | HistRework=1 (A1, level 1) | B | uncertain | medium-high (fails the crew node screen: d13 +21.1%, d16 +12.4%) | ready, conditional (see notes) | A1 plan: last or skipped |
| R3-20 | FORGE_NNUE_INT16 + NnueInt16=true (S-A2 int16 inference, int32 accumulators) | B | negative expected at 10+0.1 (same eval within 1 cp, but slower) | high (-10.5% / -13.0% CPU NPS ON on the PC, CR measured -7%) | HELD: CR policy (H256 nets float-only) needs a crew vote | CR policy "H256 nets are float-only": turning it ON for a gate needs a crew vote; listed for completeness |
| R3-21 | SmpBestThread=true (O1: report the best worker, mate-aware ranking) | C | uncertain, plausibly small positive at Threads 4 | low-medium (review fix: a found mate is never replaced by a deeper non-mate) | HELD: needs Threads=4 on both sides (r7 runner change or a manual run) | the only SMP option that can change the played move; O1 asks for a 40+0.4 confirm after an H1 |
| R3-22 | LocklessTT=true (O1-LTT lockless shared TT) | C | uncertain, about zero on 4 vCPUs; unknown with 12 free cores | low-medium (torn writes become misses by design; 24/24 stress runs 0 corrupted, TSan 0) | HELD: needs Threads=4 on both sides (r7 runner change or a manual run) | acts only with Threads > 1 (at Threads 1 it costs about 2% NPS), so it is gated, and would be used, only with Threads > 1 |
| R3-23 | SmpExactNodes=true (O1 bug 1 fix: exact helper node counts) | C | about zero in timed games (it fixes go nodes and early info counts) | low | HELD: needs Threads=4 on both sides (r7 runner change or a manual run) | a correctness fix for node-limited play; O1 expects only a small effect at time controls |
| R3-24 | NNUEKingBuckets=N + NNUEFile=<trained king-bucket net> (C4) | D | uncertain; potentially the largest NNUE item once trained on enough data | medium (training cost; NPS with a real net unmeasured) | BLOCKED: needs a trained net | prerequisite: GPU training of a king-bucket net on the A1 data (C4 recipe), then v2_parity PASS and NPS d16/d20 |
| R3-25 | NNUEOutputBuckets=8 + NNUEFile=<trained 8-head net> (C5) | D | uncertain | medium (v2 path costs about 1-2% CPU on the lock tree) | BLOCKED: needs a trained net | prerequisite: GPU training of an 8-head net (lock recipe + --output-buckets 8) |
| R3-26 | NNUEPawnPairs=1 + NNUEFile=<trained pawn-pair net> (O7) | D | uncertain | high (-17% to -20% NPS on the same tree) | BLOCKED: needs a trained net | prerequisite: GPU training with pawn-pair inputs; the speed cost must be won back by eval quality |
| R3-27 | NNUEThreats=1 + NNUEFile=<trained threat net> (O6) | D | negative expected at 10+0.1 unless the net is much stronger | high (about -40% NPS) | BLOCKED: needs a trained net | prerequisite: GPU training with threat inputs; O6 makes 40+0.4 the primary gate |
| R3-28 | PureNnue=1 + NNUEFile=<GPU-trained pure net> (O4) | D | uncertain to negative at H256 (drops the HCE endgame scaling) | high | BLOCKED: needs a trained net | prerequisite: the O4 GPU recipe (pure, same data/width as the lock); the queue Build-Args cannot run it as-is |
| R3-29 | H512 build (S-A4: FORGE_NNUE_HIDDEN=512 + FORGE_NNUE_WEIGHTS=<trained H512 net>) | D | negative unless the trained net is clearly better (H512 costs -10% to -14% CPU NPS) | high | BLOCKED: needs a trained net | prerequisite: GPU training of an H512 net (GPU_RECIPE_H512.md; the S-A4 build flags are already on the stack); the widened lock net is exact and cannot show a gain |

**Run order notes.**
- R3-01/R3-02 first: the two largest node-exact speed-ups, zero search risk; a regression there would point at a build problem.
- R3-03..R3-09: the tree-changing features with the best prior evidence, the C2 correction keys first (each bit separately, as C2 asks).
- R3-10 FORGE_SPEEDSTACK contains R3-16 (MaterialKeyTable, compile-time form) and R3-17 (child TT prefetch): run R3-16/17 only if the owner wants the runtime forms gated too.
- R3-15 runs only if R3-08 ends with Elo ≥ 0 (`run_if`), R3-19 is last per the A1 plan, R3-20 waits for a crew vote (CR policy).
- R3-13 (HardDeadline) needs a candidate built from a head that contains the R3-1 fix 5792074a.
- R3-21..23 (SMP) wait for runner support; R3-24..29 wait for trained nets (order inside D = expected value: king buckets first, threats/pure/H512 last).

## 4. Entries

### R3-01 · FORGE_NNUE_O2 (O2 NNUE accumulator kernels)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier A, node-exact speed / no search change |
| candidate | `cand_r3_nnueo2` = `F:\opus_scratch\r3\exe\forge_r3_nnueo2.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_nnueo2.exe`; sha256 `FILL (main session)`; build: build_pc.sh ... -DFORGE_NNUE_O2=1 |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | none (the build switch is the change) |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=390001`; concurrency 8 |
| srand | **603959610** (new; checked in SRAND_CHECK.md); test-plan row G-B4 (srand 1894620847, not reused) |
| tag / ok flag | `gateR3_01_nnueo2_vs_r3base` / `CR_PASS_r3_nnueo2.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on a 2047348a switch build) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: small positive (largest measured node-exact speed-up of the set); risk: low; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O2/REPORT.md):
- bit-identical output: parity 1,303,743 positions (CTest) and 1,578,127 with the 5_nnue sample, 0 differences; bench identical at all 5 depths; FMA 0
- quiet runner (CI run 40462176391): AL1 -> O2 +3.57% CPU NPS d16 [+3.28, +3.86], +3.66% d20 [+3.10, +4.22]; O2's own share (O3 -> O2) +3.26% / +3.25%; loaded PC d20 +3.01% [+1.43, +4.59] (advisory)
- the O2 report proposed no gate (speed-only); the stack turned it into a build switch, so it is gated here as the user asked

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-01",
 "tag": "gateR3_01_nnueo2_vs_r3base",
 "cand": "cand_r3_nnueo2",
 "exe": "forge_r3_nnueo2.exe",
 "sha256": "<FILL: sha256 of forge_r3_nnueo2.exe>",
 "ok": "CR_PASS_r3_nnueo2.ok",
 "options": [],
 "srand": 603959610,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 390001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O2/REPORT.md.",
 "driver_note": "FORGE_NNUE_O2 (O2 NNUE accumulator kernels) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 390001, srand 603959610, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_nnueo2 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_nnueo2.exe option.Threads=1 option.Hash=16 option.OwnBook=false -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=390001 -srand 603959610 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_01_nnueo2_vs_r3base -pgnout file=F:\forge_push\gateR3_01_nnueo2_vs_r3base\gateR3_01_nnueo2_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_01_nnueo2_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-02 · FORGE_NOZERO_MOVE_BUFFERS (S14 follow-up: no zero-fill of the move buffers)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier A, node-exact speed / no search change |
| candidate | `cand_r3_nozero` = `F:\opus_scratch\r3\exe\forge_r3_nozero.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_nozero.exe`; sha256 `FILL (main session)`; build: build_pc.sh ... -DFORGE_NOZERO_MOVE_BUFFERS=1 |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | none (the build switch is the change) |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=393001`; concurrency 8 |
| srand | **409099654** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_02_nozero_vs_r3base` / `CR_PASS_r3_nozero.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on a 2047348a switch build) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: small positive; risk: low (node-exact; relies on never reading an unwritten buffer slot, which was audited and tested); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_S14/REPORT.md):
- switch on: bench d11-d22, perft5 and kiwipete ALL OK on the PC box recipe and on CI; pick order identical over 6 storage patterns
- quiet runners: +1.25% to +2.70% CPU NPS, 5 of 8 CIs exclude 0, every A/A control includes 0; loaded PC advisory +5.64% d16 / +4.62% d20
- uninitialised MoveList/MovePicker storage (UninitArray, C++20 implicit object creation): ASan+UBSan and TSan clean, valgrind memcheck 0 errors, clang MSan clean where it applies

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-02",
 "tag": "gateR3_02_nozero_vs_r3base",
 "cand": "cand_r3_nozero",
 "exe": "forge_r3_nozero.exe",
 "sha256": "<FILL: sha256 of forge_r3_nozero.exe>",
 "ok": "CR_PASS_r3_nozero.ok",
 "options": [],
 "srand": 409099654,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 393001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_S14/REPORT.md.",
 "driver_note": "FORGE_NOZERO_MOVE_BUFFERS (S14 follow-up: no zero-fill of the move buffers) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 393001, srand 409099654, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_nozero cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_nozero.exe option.Threads=1 option.Hash=16 option.OwnBook=false -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=393001 -srand 409099654 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_02_nozero_vs_r3base -pgnout file=F:\forge_push\gateR3_02_nozero_vs_r3base\gateR3_02_nozero_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_02_nozero_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-03 · CorrHistPlus=4 (non-pawn correction history, C2 bit 4)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_corrhistplus4` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.CorrHistPlus=4` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=396001`; concurrency 8 |
| srand | **1141420168** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_03_corrhistplus4_vs_r3base` / `CR_PASS_r3_corrhistplus4.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 340927/734347/2794671/12132495/37005405 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain, plausibly small positive; risk: medium (ON cost about 1-3% NPS per bit; tree change); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C2/REPORT.md):
- bench ON vs OFF: d11 +9.0%, d13 -14.8%, d16 -7.6%, d20 -2.1%, d22 +8.7%
- ON-path cost about 1-3% per bit (same-tree weight-0 A/B, wide CIs)
- related ledger rows (different implementation, NonPawnCorr+PawnHist vs h256_e12): G34 LLR 2.48, G38 1.11, G39 0.63, G43 2.32, all "cap with no decision"

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-03",
 "tag": "gateR3_03_corrhistplus4_vs_r3base",
 "cand": "cand_r3_corrhistplus4",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_corrhistplus4.ok",
 "options": ["option.CorrHistPlus=4"],
 "srand": 1141420168,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 396001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [340927, 734347, 2794671, 12132495, 37005405]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C2/REPORT.md.",
 "driver_note": "CorrHistPlus=4 (non-pawn correction history, C2 bit 4) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 396001, srand 1141420168, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_corrhistplus4 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.CorrHistPlus=4 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=396001 -srand 1141420168 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_03_corrhistplus4_vs_r3base -pgnout file=F:\forge_push\gateR3_03_corrhistplus4_vs_r3base\gateR3_03_corrhistplus4_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_03_corrhistplus4_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-04 · CorrHistPlus=1 (continuation correction history, C2 bit 1)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_corrhistplus1` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.CorrHistPlus=1` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=399001`; concurrency 8 |
| srand | **942416262** (new; checked in SRAND_CHECK.md); test-plan row G-B1 (srand 885637590, not reused) |
| tag / ok flag | `gateR3_04_corrhistplus1_vs_r3base` / `CR_PASS_r3_corrhistplus1.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 318363/915778/2347193/9687762/19269711 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain, plausibly small positive; risk: medium (large deep-tree change: d22 -43%; ON cost about 1-3%); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C2/REPORT.md):
- bench ON vs OFF: d11 +1.8%, d13 +6.2%, d16 -22.4%, d20 -21.8%, d22 -43.4%
- EVAL change: the test plan asks for a 40+0.4 confirm after an H1

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-04",
 "tag": "gateR3_04_corrhistplus1_vs_r3base",
 "cand": "cand_r3_corrhistplus1",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_corrhistplus1.ok",
 "options": ["option.CorrHistPlus=1"],
 "srand": 942416262,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 399001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [318363, 915778, 2347193, 9687762, 19269711]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C2/REPORT.md.",
 "driver_note": "CorrHistPlus=1 (continuation correction history, C2 bit 1) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 399001, srand 942416262, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_corrhistplus1 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.CorrHistPlus=1 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=399001 -srand 942416262 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_04_corrhistplus1_vs_r3base -pgnout file=F:\forge_push\gateR3_04_corrhistplus1_vs_r3base\gateR3_04_corrhistplus1_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_04_corrhistplus1_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-05 · CorrHistPlus=2 (minor-piece correction history, C2 bit 2)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_corrhistplus2` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.CorrHistPlus=2` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=402001`; concurrency 8 |
| srand | **1201666468** (new; checked in SRAND_CHECK.md); test-plan row G-B2 (srand 2115600525, not reused) |
| tag / ok flag | `gateR3_05_corrhistplus2_vs_r3base` / `CR_PASS_r3_corrhistplus2.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 296553/824640/2914749/13945117/40489211 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; risk: medium (d20/d22 trees grow +12.6% / +18.9%); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C2/REPORT.md):
- bench ON vs OFF: d11 -5.2%, d13 -4.4%, d16 -3.6%, d20 +12.6%, d22 +18.9%

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-05",
 "tag": "gateR3_05_corrhistplus2_vs_r3base",
 "cand": "cand_r3_corrhistplus2",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_corrhistplus2.ok",
 "options": ["option.CorrHistPlus=2"],
 "srand": 1201666468,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 402001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [296553, 824640, 2914749, 13945117, 40489211]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C2/REPORT.md.",
 "driver_note": "CorrHistPlus=2 (minor-piece correction history, C2 bit 2) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 402001, srand 1201666468, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_corrhistplus2 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.CorrHistPlus=2 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=402001 -srand 1201666468 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_05_corrhistplus2_vs_r3base -pgnout file=F:\forge_push\gateR3_05_corrhistplus2_vs_r3base\gateR3_05_corrhistplus2_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_05_corrhistplus2_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-06 · CuckooRep (upcoming-repetition detection, C6)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_cuckoorep` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.CuckooRep=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=405001`; concurrency 8 |
| srand | **537949450** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_06_cuckoorep_vs_r3base` / `CR_PASS_r3_cuckoorep.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 324211/790682/3148570/10326301/31204053 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain, plausibly small positive; risk: low-medium (about 1% per-node cost; history-dependent draw bound); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C6/REPORT.md):
- ON bench d11-d22 324211/790682/3148570/10326301/31204053 (d20 -16.7%)
- per-node cost about 1% on the same tree

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-06",
 "tag": "gateR3_06_cuckoorep_vs_r3base",
 "cand": "cand_r3_cuckoorep",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_cuckoorep.ok",
 "options": ["option.CuckooRep=true"],
 "srand": 537949450,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 405001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [324211, 790682, 3148570, 10326301, 31204053]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C6/REPORT.md.",
 "driver_note": "CuckooRep (upcoming-repetition detection, C6) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 405001, srand 537949450, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_cuckoorep cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.CuckooRep=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=405001 -srand 537949450 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_06_cuckoorep_vs_r3base -pgnout file=F:\forge_push\gateR3_06_cuckoorep_vs_r3base\gateR3_06_cuckoorep_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_06_cuckoorep_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-07 · SyzygyPath (own Syzygy WDL/DTZ probing, 3-4-5-man tables; SyzygyProbeDepth=1 and Syzygy50MoveRule=true stay at their defaults)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_syzygy345` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.SyzygyPath=D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=408001`; concurrency 8 |
| srand | **1007365962** (new; checked in SRAND_CHECK.md); test-plan row G-B6 (srand 739447198, not reused) |
| tag / ok flag | `gateR3_07_syzygy345_vs_r3base` / `CR_PASS_r3_syzygy345.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 313631/866959/2460490/11465604/31972996 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: uncertain, plausibly small positive (acts only in positions with at most 5 pieces); risk: low-medium (probe cost in small endgames; table folder must stay readable); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C1/REPORT.md):
- 36,513 known-answer checks, 0 failures; 17/17 planted bugs caught; TB scores keep their TT distance (review fix)
- bench with the 3-4-5 set loaded: d11 313631, d13 866959, d16 2460490 (C1), d20/d22 measured here
- tables: 290 files, 939 MiB, read-only at D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345
- Note: the candidate processes need read access to the table folder; 8 concurrent candidate engines share the memory-mapped files
- Note: tablebase adjudication stays off in fastchess (config tb_adjudication disabled), so endgames are played out

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-07",
 "tag": "gateR3_07_syzygy345_vs_r3base",
 "cand": "cand_r3_syzygy345",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_syzygy345.ok",
 "options": ["option.SyzygyPath=D:\\grok-pc-data\\dwqww\\.claude\\worktrees\\syzygy345"],
 "srand": 1007365962,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 408001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [313631, 866959, 2460490, 11465604, 31972996]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C1/REPORT.md.",
 "driver_note": "SyzygyPath (own Syzygy WDL/DTZ probing, 3-4-5-man tables; SyzygyProbeDepth=1 and Syzygy50MoveRule=true stay at their defaults) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 408001, srand 1007365962, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_syzygy345 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.SyzygyPath=D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=408001 -srand 1007365962 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_07_syzygy345_vs_r3base -pgnout file=F:\forge_push\gateR3_07_syzygy345_vs_r3base\gateR3_07_syzygy345_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_07_syzygy345_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-08 · HistRework=2 (correction/history rework, A1)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_histrework2` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.HistRework=2` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=411001`; concurrency 8 |
| srand | **1063419569** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_08_histrework2_vs_r3base` / `CR_PASS_r3_histrework2.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 320427/881902/3041041/12218938/28571078 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; risk: medium (tree change; d22 -16.1%); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_A1/REPORT.md):
- bench ON vs OFF: d11 +2.4%, d13 +2.3%, d16 +0.5%, d20 -1.4%, d22 -16.1%
- the A1 code costs about 1% NPS even OFF (quiet runner): it is in both the candidate and the opponent here, so this gate does not see it

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-08",
 "tag": "gateR3_08_histrework2_vs_r3base",
 "cand": "cand_r3_histrework2",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_histrework2.ok",
 "options": ["option.HistRework=2"],
 "srand": 1063419569,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 411001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [320427, 881902, 3041041, 12218938, 28571078]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_A1/REPORT.md.",
 "driver_note": "HistRework=2 (correction/history rework, A1) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 411001, srand 1063419569, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_histrework2 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.HistRework=2 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=411001 -srand 1063419569 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_08_histrework2_vs_r3base -pgnout file=F:\forge_push\gateR3_08_histrework2_vs_r3base\gateR3_08_histrework2_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_08_histrework2_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-09 · CorrMargins=1 (correction-size pruning margins, O5)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_corrmargins` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.CorrMargins=1` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=414001`; concurrency 8 |
| srand | **350087856** (new; checked in SRAND_CHECK.md); test-plan row G-B3 (srand 1162618901, not reused) |
| tag / ok flag | `gateR3_09_corrmargins_vs_r3base` / `CR_PASS_r3_corrmargins.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 343365/858019/2522546/12894582/22287047 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; risk: medium (four pruning margins move at once; d22 -34.5%); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O5/REPORT.md):
- bench ON vs OFF: d11 +9.75%, d13 -0.5%, d16 -16.6%, d20 +4.1%, d22 -34.5%
- sub-gates without a rebuild are possible later (one of CorrRfpPct/CorrFutilityPct/CorrNullMovePct/CorrLmrPct at a time)

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-09",
 "tag": "gateR3_09_corrmargins_vs_r3base",
 "cand": "cand_r3_corrmargins",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_corrmargins.ok",
 "options": ["option.CorrMargins=1"],
 "srand": 350087856,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 414001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [343365, 858019, 2522546, 12894582, 22287047]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O5/REPORT.md.",
 "driver_note": "CorrMargins=1 (correction-size pruning margins, O5) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 414001, srand 350087856, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_corrmargins cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.CorrMargins=1 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=414001 -srand 350087856 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_09_corrmargins_vs_r3base -pgnout file=F:\forge_push\gateR3_09_corrmargins_vs_r3base\gateR3_09_corrmargins_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_09_corrmargins_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-10 · FORGE_SPEEDSTACK (S29: S11 material-key table + S13 child TT prefetch, compile time)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier A, node-exact speed / no search change |
| candidate | `cand_r3_speedstack` = `F:\opus_scratch\r3\exe\forge_r3_speedstack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_speedstack.exe`; sha256 `FILL (main session)`; build: build_pc.sh ... -DFORGE_SPEEDSTACK=1 |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | none (the build switch is the change) |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=417001`; concurrency 8 |
| srand | **341349245** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_10_speedstack_vs_r3base` / `CR_PASS_r3_speedstack.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on a 2047348a switch build) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero (speed-up under 1%); risk: low; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_S29/REPORT.md):
- switch ON: bench equals the AL1 pins at all 5 depths; UCI option list unchanged
- quiet runner ABBA: d16 +0.18% [-0.53, +0.89], d20 +0.50% [+0.04, +0.97]; loaded PC within noise
- Sol's design: one non-regression SPRT [-3,1] for the stack (gated here at [0,5] as the user asked)

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-10",
 "tag": "gateR3_10_speedstack_vs_r3base",
 "cand": "cand_r3_speedstack",
 "exe": "forge_r3_speedstack.exe",
 "sha256": "<FILL: sha256 of forge_r3_speedstack.exe>",
 "ok": "CR_PASS_r3_speedstack.ok",
 "options": [],
 "srand": 341349245,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 417001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_S29/REPORT.md.",
 "driver_note": "FORGE_SPEEDSTACK (S29: S11 material-key table + S13 child TT prefetch, compile time) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 417001, srand 341349245, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_speedstack cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_speedstack.exe option.Threads=1 option.Hash=16 option.OwnBook=false -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=417001 -srand 341349245 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_10_speedstack_vs_r3base -pgnout file=F:\forge_push\gateR3_10_speedstack_vs_r3base\gateR3_10_speedstack_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_10_speedstack_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-11 · NetScale=99 (eval-scale mapping, S41)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_netscale99` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NetScale=99` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=420001`; concurrency 8 |
| srand | **450325920** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_11_netscale99_vs_r3base` / `CR_PASS_r3_netscale99.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 308948/917342/2601047/14196959/32409747 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero; risk: low (1% eval rescale; single bench depths move up to 14.6%, total tree size unchanged); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_S41/REPORT.md):
- S41: AL1 @99 every bench depth within +-14.6%; 100-position totals at depth 12 within 0.6%
- OFF path costs nothing measurable (quiet runner)

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-11",
 "tag": "gateR3_11_netscale99_vs_r3base",
 "cand": "cand_r3_netscale99",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_netscale99.ok",
 "options": ["option.NetScale=99"],
 "srand": 450325920,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 420001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [308948, 917342, 2601047, 14196959, 32409747]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_S41/REPORT.md.",
 "driver_note": "NetScale=99 (eval-scale mapping, S41) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 420001, srand 450325920, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_netscale99 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NetScale=99 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=420001 -srand 450325920 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_11_netscale99_vs_r3base -pgnout file=F:\forge_push\gateR3_11_netscale99_vs_r3base\gateR3_11_netscale99_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_11_netscale99_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-12 · IntendedThreefold (FIDE 9.2.1 claim in search, S-IT)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_intendedthreefold` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.IntendedThreefold=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=423001`; concurrency 8 |
| srand | **981103760** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_12_intendedthreefold_vs_r3base` / `CR_PASS_r3_intendedthreefold.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero (fires only with repeated keys in the game history); risk: low-medium (1.10-1.17x CPU per node inside shuffling subtrees); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_SIT/REPORT.md):
- option off: trees identical everywhere; on: no cost measured on bench (quiet runner CIs include 0)
- in shuffling positions with duplicated keys the option costs 1.10-1.17x CPU per node
- Note: ON bench equals the OFF pins; the runner accepts this (its "option did not apply" test compares with the old h256_e12 numbers, not AL1)

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-12",
 "tag": "gateR3_12_intendedthreefold_vs_r3base",
 "cand": "cand_r3_intendedthreefold",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_intendedthreefold.ok",
 "options": ["option.IntendedThreefold=true"],
 "srand": 981103760,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 423001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_SIT/REPORT.md.",
 "driver_note": "IntendedThreefold (FIDE 9.2.1 claim in search, S-IT) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 423001, srand 981103760, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_intendedthreefold cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.IntendedThreefold=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=423001 -srand 981103760 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_12_intendedthreefold_vs_r3base -pgnout file=F:\forge_push\gateR3_12_intendedthreefold_vs_r3base\gateR3_12_intendedthreefold_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_12_intendedthreefold_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-13 · HardDeadline=10 (watchdog bestmove deadline, C3)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier A, node-exact speed / no search change |
| candidate | `cand_r3_harddeadline10` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.HardDeadline=10` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=426001`; concurrency 8 |
| srand | **647180553** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_13_harddeadline10_vs_r3base` / `CR_PASS_r3_harddeadline10.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero (no search decision changes while the engine answers on time); risk: low; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C3/REPORT.md):
- 0 forced answers in 3,600 normal-load searches with HardDeadline 10 (C3)
- Windows starvation demo: lateness 3,750-4,651 ms without, max +28.8 ms with the option
- R3-1 fix 5792074a: after a watchdog bestmove the stopped search could still print a late "info depth" line (33 such lines in about 140 all-ON self-play games); exactly one bestmove per go always held. The fix closes search output under uci_output_mutex once the watchdog answers; with HardDeadline 0 nothing changes (uci_check --full ALL OK)
- Note: **the candidate exe must be built from a head that contains 5792074a** (check `git merge-base --is-ancestor 5792074a <final head>` before install); the 2047348a probe used for the pins predates the fix, which does not touch fixed-depth bench
- Note: fixed-depth bench is unaffected, so cand_on = cand_off (accepted by the runner, see R3-12)
- Note: watch_time stays on: a late move would pause this gate, which is exactly what the option should prevent

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-13",
 "tag": "gateR3_13_harddeadline10_vs_r3base",
 "cand": "cand_r3_harddeadline10",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_harddeadline10.ok",
 "options": ["option.HardDeadline=10"],
 "srand": 647180553,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 426001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C3/REPORT.md.",
 "driver_note": "HardDeadline=10 (watchdog bestmove deadline, C3) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 426001, srand 647180553, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_harddeadline10 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.HardDeadline=10 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=426001 -srand 647180553 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_13_harddeadline10_vs_r3base -pgnout file=F:\forge_push\gateR3_13_harddeadline10_vs_r3base\gateR3_13_harddeadline10_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_13_harddeadline10_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-14 · CorrExt=1 (correction-history extensions, O8)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_corrext` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.CorrExt=1` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=429001`; concurrency 8 |
| srand | **306251564** (new; checked in SRAND_CHECK.md); test-plan row G-C5 (srand 113016036, not reused) |
| tag / ok flag | `gateR3_14_corrext_vs_r3base` / `CR_PASS_r3_corrext.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 312961/838790/2891507/12313394/33298237 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain, weak at 10+0.1; risk: medium (extensions compound with depth; the idea "lost at STC" in the source report); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O8/REPORT.md):
- bench ON vs OFF: d11 +0.03%, d13 -2.73%, d16 -4.41%, d20 -0.61%, d22 -2.20%
- Note: owner choice: run this entry with "tc": "40+0.4" instead (the r7 runner supports a per-gate tc field) if the LTC-primary rule of the test plan should apply

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-14",
 "tag": "gateR3_14_corrext_vs_r3base",
 "cand": "cand_r3_corrext",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_corrext.ok",
 "options": ["option.CorrExt=1"],
 "srand": 306251564,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 429001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312961, 838790, 2891507, 12313394, 33298237]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O8/REPORT.md.",
 "driver_note": "CorrExt=1 (correction-history extensions, O8) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 429001, srand 306251564, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_corrext cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.CorrExt=1 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=429001 -srand 306251564 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_14_corrext_vs_r3base -pgnout file=F:\forge_push\gateR3_14_corrext_vs_r3base\gateR3_14_corrext_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_14_corrext_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-15 · HistRework=3 (A1, level 3)

| field | value |
|---|---|
| status | ready, conditional (see notes); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_histrework3` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.HistRework=3` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=432001`; concurrency 8 |
| srand | **1520453741** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_15_histrework3_vs_r3base` / `CR_PASS_r3_histrework3.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 336192/869621/3052885/15664938/35705218 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; risk: medium (d20 tree +26.4%: crew flag); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_A1/REPORT.md):
- bench ON vs OFF: d11 +7.5%, d13 +0.8%, d16 +0.9%, d20 +26.4%, d22 +4.9%
- Note: queue it with "run_if": {"gate_tag": "<R3-08 tag>", "min_elo": 0}: the r7 runner then skips it when R3-08 ends below 0 Elo

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-15",
 "tag": "gateR3_15_histrework3_vs_r3base",
 "cand": "cand_r3_histrework3",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_histrework3.ok",
 "options": ["option.HistRework=3"],
 "srand": 1520453741,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 432001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [336192, 869621, 3052885, 15664938, 35705218]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "run_if": {
  "gate_tag": "gateR3_08_histrework2_vs_r3base",
  "min_elo": 0
 },
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_A1/REPORT.md.",
 "driver_note": "HistRework=3 (A1, level 3) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 432001, srand 1520453741, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_histrework3 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.HistRework=3 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=432001 -srand 1520453741 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_15_histrework3_vs_r3base -pgnout file=F:\forge_push\gateR3_15_histrework3_vs_r3base\gateR3_15_histrework3_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_15_histrework3_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-16 · MaterialKeyTable (S11 node-exact material key, runtime option)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier A, node-exact speed / no search change |
| candidate | `cand_r3_materialkeytable` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.MaterialKeyTable=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=435001`; concurrency 8 |
| srand | **303395056** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_16_materialkeytable_vs_r3base` / `CR_PASS_r3_materialkeytable.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero; risk: low (key equality proven on all count vectors); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_S11/REPORT.md):
- ON nodes == OFF at all refs (PC AVX2 + scalar, Linux)
- NPS ON/OFF: no effect measurable (CIs include 0)

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-16",
 "tag": "gateR3_16_materialkeytable_vs_r3base",
 "cand": "cand_r3_materialkeytable",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_materialkeytable.ok",
 "options": ["option.MaterialKeyTable=true"],
 "srand": 303395056,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 435001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_S11/REPORT.md.",
 "driver_note": "MaterialKeyTable (S11 node-exact material key, runtime option) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 435001, srand 303395056, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_materialkeytable cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.MaterialKeyTable=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=435001 -srand 303395056 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_16_materialkeytable_vs_r3base -pgnout file=F:\forge_push\gateR3_16_materialkeytable_vs_r3base\gateR3_16_materialkeytable_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_16_materialkeytable_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-17 · FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true (S13)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier A, node-exact speed / no search change |
| candidate | `cand_r3_ttprefetch` = `F:\opus_scratch\r3\exe\forge_r3_ttprefetch.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_ttprefetch.exe`; sha256 `FILL (main session)`; build: build_pc.sh ... -DFORGE_S13_TT_CHILD_PREFETCH=1 (adds UCI TtChildPrefetch, default false) |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.TtChildPrefetch=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=438001`; concurrency 8 |
| srand | **1816646849** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_17_ttprefetch_vs_r3base` / `CR_PASS_r3_ttprefetch.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on a 2047348a switch build) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on a 2047348a switch build, sha256 733170ac9000…) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero; risk: low; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_S13/REPORT.md):
- switch-on exe, option ON: bench 312866/862329/3024920/12389307/34048354, perft and kiwipete exact
- ON prints "info string TtChildPrefetch active" once per Searcher (visible in engine_io.log)

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-17",
 "tag": "gateR3_17_ttprefetch_vs_r3base",
 "cand": "cand_r3_ttprefetch",
 "exe": "forge_r3_ttprefetch.exe",
 "sha256": "<FILL: sha256 of forge_r3_ttprefetch.exe>",
 "ok": "CR_PASS_r3_ttprefetch.ok",
 "options": ["option.TtChildPrefetch=true"],
 "srand": 1816646849,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 438001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_S13/REPORT.md.",
 "driver_note": "FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true (S13) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 438001, srand 1816646849, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_ttprefetch cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_ttprefetch.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.TtChildPrefetch=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=438001 -srand 1816646849 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_17_ttprefetch_vs_r3base -pgnout file=F:\forge_push\gateR3_17_ttprefetch_vs_r3base\gateR3_17_ttprefetch_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_17_ttprefetch_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-18 · FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true (S12 null-edge accumulator alias)

| field | value |
|---|---|
| status | ready for the r7 queue (after exe install + CR ok flag); tier A, node-exact speed / no search change |
| candidate | `cand_r3_lazyacc` = `F:\opus_scratch\r3\exe\forge_r3_lazyacc.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_lazyacc.exe`; sha256 `FILL (main session)`; build: build_pc.sh ... -DFORGE_NNUE_LAZY_ACC=1 (adds UCI NnueLazyAcc, default false); name given by the main session |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NnueLazyAcc=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=441001`; concurrency 8 |
| srand | **1851462305** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_18_lazyacc_vs_r3base` / `CR_PASS_r3_lazyacc.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on a 2047348a switch build) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on a 2047348a switch build, sha256 4552b83e63a5…) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero (counted saving about 0.07% of bench time); risk: low (node-exact; the switch build also counts evaluations for its stats line); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_S12/REPORT.md (branch opus-sol-S12)):
- node-exact: uci_check --full ALL OK with the option off and on (PC and Linux)
- copies avoided per bench: d20 183,232 = 1.4-2.7% of evaluations; quiet runner on/off -0.16% / -0.12% CPU NPS, CIs include 0
- ON prints "info string NnueLazyAcc active" and one stats line per search

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-18",
 "tag": "gateR3_18_lazyacc_vs_r3base",
 "cand": "cand_r3_lazyacc",
 "exe": "forge_r3_lazyacc.exe",
 "sha256": "<FILL: sha256 of forge_r3_lazyacc.exe>",
 "ok": "CR_PASS_r3_lazyacc.ok",
 "options": ["option.NnueLazyAcc=true"],
 "srand": 1851462305,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 441001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_S12/REPORT.md (branch opus-sol-S12).",
 "driver_note": "FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true (S12 null-edge accumulator alias) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 441001, srand 1851462305, conc 8, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_lazyacc cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_lazyacc.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NnueLazyAcc=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=441001 -srand 1851462305 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_18_lazyacc_vs_r3base -pgnout file=F:\forge_push\gateR3_18_lazyacc_vs_r3base\gateR3_18_lazyacc_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_18_lazyacc_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-19 · HistRework=1 (A1, level 1)

| field | value |
|---|---|
| status | ready, conditional (see notes); tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_histrework1` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.HistRework=1` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=444001`; concurrency 8 |
| srand | **759711708** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_19_histrework1_vs_r3base` / `CR_PASS_r3_histrework1.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 373261/1043893/3399770/13180132/35699757 (measured on the 2047348a probe build, probe_2047348a_pins.json; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; risk: medium-high (fails the crew node screen: d13 +21.1%, d16 +12.4%); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_A1/REPORT.md):
- bench ON vs OFF: d11 +19.3%, d13 +21.1%, d16 +12.4%, d20 +6.4%, d22 +4.9%
- Note: A1 plan: run it last or skip it (owner decision); it has no run_if, so it runs when the queue reaches it

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-19",
 "tag": "gateR3_19_histrework1_vs_r3base",
 "cand": "cand_r3_histrework1",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_histrework1.ok",
 "options": ["option.HistRework=1"],
 "srand": 759711708,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 444001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [373261, 1043893, 3399770, 13180132, 35699757]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_A1/REPORT.md.",
 "driver_note": "HistRework=1 (A1, level 1) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 444001, srand 759711708, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_histrework1 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.HistRework=1 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=444001 -srand 759711708 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_19_histrework1_vs_r3base -pgnout file=F:\forge_push\gateR3_19_histrework1_vs_r3base\gateR3_19_histrework1_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_19_histrework1_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-20 · FORGE_NNUE_INT16 + NnueInt16=true (S-A2 int16 inference, int32 accumulators)

| field | value |
|---|---|
| status | HELD: CR policy (H256 nets float-only) needs a crew vote; tier B, tree-changing search/eval (Threads 1) |
| candidate | `cand_r3_nnueint16` = `F:\opus_scratch\r3\exe\forge_r3_int16.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_int16.exe`; sha256 `FILL (main session)`; build: build_pc.sh ... -DFORGE_NNUE_INT16=1 (adds UCI NnueInt16, default false; S-A2 merged as 97b01454); name given by the main session |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NnueInt16=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=447001`; concurrency 8 |
| srand | **1404525608** (new; checked in SRAND_CHECK.md); test-plan row G-A2 (srand 869014820, not reused) |
| tag / ok flag | `gateR3_20_nnueint16_vs_r3base` / `CR_PASS_r3_nnueint16.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on a ba03edf9 switch build) |
| prebench cand_on | 330610/858175/2760596/9564588/21638970 (measured on a ba03edf9 switch build, sha256 2aa9055b713d…; matches the job REPORT) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: negative expected at 10+0.1 (same eval within 1 cp, but slower); risk: high (-10.5% / -13.0% CPU NPS ON on the PC, CR measured -7%); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_SA2/REPORT.md (branch opus-sol-SA2)):
- parity 10000/10000 vs an exact integer reference; max 1 cp difference to the float path
- ON changes the tree: d11 +5.7%, d13 -0.5%, d16 -8.7%, d20 -22.8%, d22 -36.4%
- merged into the stack behind the build switch FORGE_NNUE_INT16 (97b01454); the main session reports the ON pins d11-d20 330610/858175/2760596/9564588 on the stack
- Note: remove the HELD status after a crew vote; the switch build with the option off must give the AL1 pins (S-A2: option OFF = lock identity)

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-20",
 "tag": "gateR3_20_nnueint16_vs_r3base",
 "cand": "cand_r3_nnueint16",
 "exe": "forge_r3_int16.exe",
 "sha256": "<FILL: sha256 of forge_r3_int16.exe>",
 "ok": "CR_PASS_r3_nnueint16.ok",
 "options": ["option.NnueInt16=true"],
 "srand": 1404525608,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 447001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [330610, 858175, 2760596, 9564588, 21638970]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "nps": true,
 "status": "HELD_NEEDS_CREW_VOTE: CR policy (S-A2 REPORT) says H256 nets are float-only; remove this status after a crew vote",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_SA2/REPORT.md (branch opus-sol-SA2).",
 "driver_note": "FORGE_NNUE_INT16 + NnueInt16=true (S-A2 int16 inference, int32 accumulators) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 447001, srand 1404525608, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_nnueint16 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_int16.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NnueInt16=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=447001 -srand 1404525608 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_20_nnueint16_vs_r3base -pgnout file=F:\forge_push\gateR3_20_nnueint16_vs_r3base\gateR3_20_nnueint16_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_20_nnueint16_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-21 · SmpBestThread=true (O1: report the best worker, mate-aware ranking)

| field | value |
|---|---|
| status | HELD: needs Threads=4 on both sides (r7 runner change or a manual run); tier C, SMP only (Threads 4) |
| candidate | `cand_r3_smpbestthread` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.SmpBestThread=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=4 Hash=64 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=450001`; concurrency 2 |
| srand | **938441364** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_21_smpbestthread_vs_r3base` / `CR_PASS_r3_smpbestthread.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain, plausibly small positive at Threads 4; risk: low-medium (review fix: a found mate is never replaced by a deeper non-mate); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O1/REPORT.md):
- inert at Threads 1 (bench identical)
- 500 self-play games at Threads 4 with SmpExactNodes+SmpBestThread on: 0 illegal, 0 crashes, 0 stalls
- Note: the r7 runner cannot run this entry as is: Build-Args, Static-ArgCheck and Void-Check hard-code Threads=1/Hash=16 for both engines (a Threads=4 option on the candidate alone would be VOID and would not be the SMP test). It needs a per-gate threads/hash field in the runner (owner/CR decision) or a manual run of the command below while the queue is idle (the runner launches nothing while any fastchess.exe is alive). At concurrency 2 a 1500-game gate needs about 4 times the slot time of a conc-8 gate (r7 budgets 2.75 h per gate, so roughly 11 h).

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-21",
 "tag": "gateR3_21_smpbestthread_vs_r3base",
 "cand": "cand_r3_smpbestthread",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_smpbestthread.ok",
 "options": ["option.SmpBestThread=true"],
 "srand": 938441364,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 450001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 2,
 "threads": 4,
 "hash": 64,
 "status": "HELD_NEEDS_RUNNER_THREADS: r7 hard-codes Threads=1/Hash=16 (Build-Args, Static-ArgCheck, Void-Check); this gate needs Threads=4 Hash=64 on both sides",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O1/REPORT.md.",
 "driver_note": "SmpBestThread=true (O1: report the best worker, mate-aware ranking) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T4 H64 OwnBook false, 8moves_v3 random start 450001, srand 938441364, conc 2, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (runner change or manual run; same priority/affinity/output conventions):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_smpbestthread cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=4 option.Hash=64 option.OwnBook=false option.SmpBestThread=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=4 option.Hash=64 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=450001 -srand 938441364 -games 2 -repeat -rounds 750 -concurrency 2 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_21_smpbestthread_vs_r3base -pgnout file=F:\forge_push\gateR3_21_smpbestthread_vs_r3base\gateR3_21_smpbestthread_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_21_smpbestthread_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-22 · LocklessTT=true (O1-LTT lockless shared TT)

| field | value |
|---|---|
| status | HELD: needs Threads=4 on both sides (r7 runner change or a manual run); tier C, SMP only (Threads 4) |
| candidate | `cand_r3_locklesstt` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.LocklessTT=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=4 Hash=64 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=453001`; concurrency 2 |
| srand | **1199191854** (new; checked in SRAND_CHECK.md); test-plan row G-B5 (srand 1325124880, not reused) |
| tag / ok flag | `gateR3_22_locklesstt_vs_r3base` / `CR_PASS_r3_locklesstt.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: uncertain, about zero on 4 vCPUs; unknown with 12 free cores; risk: low-medium (torn writes become misses by design; 24/24 stress runs 0 corrupted, TSan 0); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O1-LTT/REPORT.md):
- Threads 1: bench identical, same-binary NPS -2.25% d16 / -2.06% d20
- CI 4 vCPUs: on/off NPS 0.990 / 1.014 / 1.013 at T2/T4/T8, time-to-depth differences inside one sd
- setoption true prints "info string LocklessTT active" (visible in engine_io.log)
- Note: the r7 runner cannot run this entry as is: Build-Args, Static-ArgCheck and Void-Check hard-code Threads=1/Hash=16 for both engines (a Threads=4 option on the candidate alone would be VOID and would not be the SMP test). It needs a per-gate threads/hash field in the runner (owner/CR decision) or a manual run of the command below while the queue is idle (the runner launches nothing while any fastchess.exe is alive). At concurrency 2 a 1500-game gate needs about 4 times the slot time of a conc-8 gate (r7 budgets 2.75 h per gate, so roughly 11 h).

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-22",
 "tag": "gateR3_22_locklesstt_vs_r3base",
 "cand": "cand_r3_locklesstt",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_locklesstt.ok",
 "options": ["option.LocklessTT=true"],
 "srand": 1199191854,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 453001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 2,
 "threads": 4,
 "hash": 64,
 "status": "HELD_NEEDS_RUNNER_THREADS: r7 hard-codes Threads=1/Hash=16 (Build-Args, Static-ArgCheck, Void-Check); this gate needs Threads=4 Hash=64 on both sides",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O1-LTT/REPORT.md.",
 "driver_note": "LocklessTT=true (O1-LTT lockless shared TT) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T4 H64 OwnBook false, 8moves_v3 random start 453001, srand 1199191854, conc 2, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (runner change or manual run; same priority/affinity/output conventions):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_locklesstt cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=4 option.Hash=64 option.OwnBook=false option.LocklessTT=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=4 option.Hash=64 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=453001 -srand 1199191854 -games 2 -repeat -rounds 750 -concurrency 2 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_22_locklesstt_vs_r3base -pgnout file=F:\forge_push\gateR3_22_locklesstt_vs_r3base\gateR3_22_locklesstt_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_22_locklesstt_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-23 · SmpExactNodes=true (O1 bug 1 fix: exact helper node counts)

| field | value |
|---|---|
| status | HELD: needs Threads=4 on both sides (r7 runner change or a manual run); tier C, SMP only (Threads 4) |
| candidate | `cand_r3_smpexactnodes` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.SmpExactNodes=true` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=4 Hash=64 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=456001`; concurrency 2 |
| srand | **1127627755** (new; checked in SRAND_CHECK.md) |
| tag / ok flag | `gateR3_23_smpexactnodes_vs_r3base` / `CR_PASS_r3_smpexactnodes.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | 312866/862329/3024920/12389307/34048354 (measured on the 2047348a probe build, probe_2047348a_pins.json) |
| confirm | H1 → confirm right after at 10+0.1 |
| expectation (not a claim) | gain: about zero in timed games (it fixes go nodes and early info counts); risk: low; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O1/REPORT.md):
- AL1 lock: 4/5 rounds of go nodes 20000 at Threads 3 played an unsearched move; with the option 0/5
- Note: the r7 runner cannot run this entry as is: Build-Args, Static-ArgCheck and Void-Check hard-code Threads=1/Hash=16 for both engines (a Threads=4 option on the candidate alone would be VOID and would not be the SMP test). It needs a per-gate threads/hash field in the runner (owner/CR decision) or a manual run of the command below while the queue is idle (the runner launches nothing while any fastchess.exe is alive). At concurrency 2 a 1500-game gate needs about 4 times the slot time of a conc-8 gate (r7 budgets 2.75 h per gate, so roughly 11 h).

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-23",
 "tag": "gateR3_23_smpexactnodes_vs_r3base",
 "cand": "cand_r3_smpexactnodes",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_smpexactnodes.ok",
 "options": ["option.SmpExactNodes=true"],
 "srand": 1127627755,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 456001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": [312866, 862329, 3024920, 12389307, 34048354]
 },
 "longer_tc_confirm_if_h1": false,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 2,
 "threads": 4,
 "hash": 64,
 "status": "HELD_NEEDS_RUNNER_THREADS: r7 hard-codes Threads=1/Hash=16 (Build-Args, Static-ArgCheck, Void-Check); this gate needs Threads=4 Hash=64 on both sides",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O1/REPORT.md.",
 "driver_note": "SmpExactNodes=true (O1 bug 1 fix: exact helper node counts) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T4 H64 OwnBook false, 8moves_v3 random start 456001, srand 1127627755, conc 2, watch_time, confirm_first."
}
```

fastchess command as the r7 Build-Args would build it (runner change or manual run; same priority/affinity/output conventions):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_smpexactnodes cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=4 option.Hash=64 option.OwnBook=false option.SmpExactNodes=true -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=4 option.Hash=64 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=456001 -srand 1127627755 -games 2 -repeat -rounds 750 -concurrency 2 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_23_smpexactnodes_vs_r3base -pgnout file=F:\forge_push\gateR3_23_smpexactnodes_vs_r3base\gateR3_23_smpexactnodes_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_23_smpexactnodes_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-24 · NNUEKingBuckets=N + NNUEFile=<trained king-bucket net> (C4)

| field | value |
|---|---|
| status | BLOCKED: needs a trained net; tier D, trained net needed |
| candidate | `cand_r3_kingbuckets` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NNUEFile=<KB_NET.fnn2>` `option.NNUEKingBuckets=<N of that net>` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=459001`; concurrency 8 |
| srand | **1602272685** (new; checked in SRAND_CHECK.md); test-plan row G-C1 (srand 1352390606, not reused; "gate only on A1 data") |
| tag / ok flag | `gateR3_24_kingbuckets_vs_r3base` / `CR_PASS_r3_kingbuckets.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | FILL (needs the trained net: measure on the final exe with the net before install) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; potentially the largest NNUE item once trained on enough data; risk: medium (training cost; NPS with a real net unmeasured); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C4/REPORT.md):
- lock replicas r1/r4/rm2/rm8/rm16 reproduce the AL1 pins (function-preserving, cannot show a gain)
- BLOCKED: no trained net exists. Every .fnn2 on the PC is a lock replica, an identity net or a CPU smoke net (find over F:\ and D:\grok-pc-data, nothing under F:\forge_nnue_train).
- Note: replace `<…NET.fnn2>` by the absolute path of the trained net (no spaces, readable by the engine) and fill `cand_on` with its 5 bench pins; the engine exits with status 2 if the net and options do not match (fail-loud rule), so a wrong path shows up as a start-up failure, never as a lock-vs-lock match.

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-24",
 "tag": "gateR3_24_kingbuckets_vs_r3base",
 "cand": "cand_r3_kingbuckets",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_kingbuckets.ok",
 "options": ["option.NNUEFile=<KB_NET.fnn2>", "option.NNUEKingBuckets=<N of that net>"],
 "srand": 1602272685,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 459001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": "<FILL: 5 ON pins measured with the trained net>"
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "early_stop": {
  "games": 750,
  "elo_max": -8,
  "llr_max": -1.5,
  "rule": "net-only early stop, crew vote 8/8 2026-10-25: first block >= 750 games with Elo < -8 AND LLR < -1.5 -> H0-early; net goes on the rework list, never dropped; re-gate fresh, never pooled"
 },
 "nps": true,
 "status": "HELD_NEEDS_TRAINED_NET: no trained net exists; fill NNUEFile/exe, cand_on pins and sha256 first",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C4/REPORT.md.",
 "driver_note": "NNUEKingBuckets=N + NNUEFile=<trained king-bucket net> (C4) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 459001, srand 1602272685, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_kingbuckets cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NNUEFile=<KB_NET.fnn2> option.NNUEKingBuckets=<N of that net> -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=459001 -srand 1602272685 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_24_kingbuckets_vs_r3base -pgnout file=F:\forge_push\gateR3_24_kingbuckets_vs_r3base\gateR3_24_kingbuckets_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_24_kingbuckets_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-25 · NNUEOutputBuckets=8 + NNUEFile=<trained 8-head net> (C5)

| field | value |
|---|---|
| status | BLOCKED: needs a trained net; tier D, trained net needed |
| candidate | `cand_r3_outputbuckets` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NNUEFile=<OB8_NET.fnn2>` `option.NNUEOutputBuckets=8` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=462001`; concurrency 8 |
| srand | **1153287325** (new; checked in SRAND_CHECK.md); test-plan row G-C6 (srand 817455375, not reused) |
| tag / ok flag | `gateR3_25_outputbuckets_vs_r3base` / `CR_PASS_r3_outputbuckets.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | FILL (needs the trained net: measure on the final exe with the net before install) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; risk: medium (v2 path costs about 1-2% CPU on the lock tree); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/C5/REPORT.md):
- C5 smoke nets (CPU, synthetic/sample data) are not playing nets
- BLOCKED: no trained net exists. Every .fnn2 on the PC is a lock replica, an identity net or a CPU smoke net (find over F:\ and D:\grok-pc-data, nothing under F:\forge_nnue_train).
- Note: replace `<…NET.fnn2>` by the absolute path of the trained net (no spaces, readable by the engine) and fill `cand_on` with its 5 bench pins; the engine exits with status 2 if the net and options do not match (fail-loud rule), so a wrong path shows up as a start-up failure, never as a lock-vs-lock match.

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-25",
 "tag": "gateR3_25_outputbuckets_vs_r3base",
 "cand": "cand_r3_outputbuckets",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_outputbuckets.ok",
 "options": ["option.NNUEFile=<OB8_NET.fnn2>", "option.NNUEOutputBuckets=8"],
 "srand": 1153287325,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 462001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": "<FILL: 5 ON pins measured with the trained net>"
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "early_stop": {
  "games": 750,
  "elo_max": -8,
  "llr_max": -1.5,
  "rule": "net-only early stop, crew vote 8/8 2026-10-25: first block >= 750 games with Elo < -8 AND LLR < -1.5 -> H0-early; net goes on the rework list, never dropped; re-gate fresh, never pooled"
 },
 "nps": true,
 "status": "HELD_NEEDS_TRAINED_NET: no trained net exists; fill NNUEFile/exe, cand_on pins and sha256 first",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/C5/REPORT.md.",
 "driver_note": "NNUEOutputBuckets=8 + NNUEFile=<trained 8-head net> (C5) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 462001, srand 1153287325, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_outputbuckets cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NNUEFile=<OB8_NET.fnn2> option.NNUEOutputBuckets=8 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=462001 -srand 1153287325 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_25_outputbuckets_vs_r3base -pgnout file=F:\forge_push\gateR3_25_outputbuckets_vs_r3base\gateR3_25_outputbuckets_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_25_outputbuckets_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-26 · NNUEPawnPairs=1 + NNUEFile=<trained pawn-pair net> (O7)

| field | value |
|---|---|
| status | BLOCKED: needs a trained net; tier D, trained net needed |
| candidate | `cand_r3_pawnpairs` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NNUEFile=<PP_NET.fnn2>` `option.NNUEPawnPairs=1` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=465001`; concurrency 8 |
| srand | **461303726** (new; checked in SRAND_CHECK.md); test-plan row G-C3 (srand 1319449387, not reused) |
| tag / ok flag | `gateR3_26_pawnpairs_vs_r3base` / `CR_PASS_r3_pawnpairs.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | FILL (needs the trained net: measure on the final exe with the net before install) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain; risk: high (-17% to -20% NPS on the same tree); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O7/REPORT.md):
- zero-pawn-pair replica: CI -17.6% wall / -17.3% CPU d16
- BLOCKED: no trained net exists. Every .fnn2 on the PC is a lock replica, an identity net or a CPU smoke net (find over F:\ and D:\grok-pc-data, nothing under F:\forge_nnue_train).
- Note: replace `<…NET.fnn2>` by the absolute path of the trained net (no spaces, readable by the engine) and fill `cand_on` with its 5 bench pins; the engine exits with status 2 if the net and options do not match (fail-loud rule), so a wrong path shows up as a start-up failure, never as a lock-vs-lock match.

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-26",
 "tag": "gateR3_26_pawnpairs_vs_r3base",
 "cand": "cand_r3_pawnpairs",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_pawnpairs.ok",
 "options": ["option.NNUEFile=<PP_NET.fnn2>", "option.NNUEPawnPairs=1"],
 "srand": 461303726,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 465001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": "<FILL: 5 ON pins measured with the trained net>"
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "early_stop": {
  "games": 750,
  "elo_max": -8,
  "llr_max": -1.5,
  "rule": "net-only early stop, crew vote 8/8 2026-10-25: first block >= 750 games with Elo < -8 AND LLR < -1.5 -> H0-early; net goes on the rework list, never dropped; re-gate fresh, never pooled"
 },
 "nps": true,
 "status": "HELD_NEEDS_TRAINED_NET: no trained net exists; fill NNUEFile/exe, cand_on pins and sha256 first",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O7/REPORT.md.",
 "driver_note": "NNUEPawnPairs=1 + NNUEFile=<trained pawn-pair net> (O7) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 465001, srand 461303726, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_pawnpairs cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NNUEFile=<PP_NET.fnn2> option.NNUEPawnPairs=1 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=465001 -srand 461303726 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_26_pawnpairs_vs_r3base -pgnout file=F:\forge_push\gateR3_26_pawnpairs_vs_r3base\gateR3_26_pawnpairs_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_26_pawnpairs_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-27 · NNUEThreats=1 + NNUEFile=<trained threat net> (O6)

| field | value |
|---|---|
| status | BLOCKED: needs a trained net; tier D, trained net needed |
| candidate | `cand_r3_threats` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NNUEFile=<THREAT_NET.fnn2>` `option.NNUEThreats=1` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=468001`; concurrency 8 |
| srand | **1084240214** (new; checked in SRAND_CHECK.md); test-plan row G-C2 (srand 2139766817, not reused; 40+0.4 primary) |
| tag / ok flag | `gateR3_27_threats_vs_r3base` / `CR_PASS_r3_threats.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | FILL (needs the trained net: measure on the final exe with the net before install) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: negative expected at 10+0.1 unless the net is much stronger; risk: high (about -40% NPS); at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O6/REPORT.md):
- zero-threat replica: CI -41.0% wall / -40.6% CPU d16
- BLOCKED: no trained net exists. Every .fnn2 on the PC is a lock replica, an identity net or a CPU smoke net (find over F:\ and D:\grok-pc-data, nothing under F:\forge_nnue_train).
- Note: owner choice: "tc": "40+0.4" for this entry (O6 and the test plan: 10+0.1 is informational only)
- Note: replace `<…NET.fnn2>` by the absolute path of the trained net (no spaces, readable by the engine) and fill `cand_on` with its 5 bench pins; the engine exits with status 2 if the net and options do not match (fail-loud rule), so a wrong path shows up as a start-up failure, never as a lock-vs-lock match.

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-27",
 "tag": "gateR3_27_threats_vs_r3base",
 "cand": "cand_r3_threats",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_threats.ok",
 "options": ["option.NNUEFile=<THREAT_NET.fnn2>", "option.NNUEThreats=1"],
 "srand": 1084240214,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 468001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": "<FILL: 5 ON pins measured with the trained net>"
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "early_stop": {
  "games": 750,
  "elo_max": -8,
  "llr_max": -1.5,
  "rule": "net-only early stop, crew vote 8/8 2026-10-25: first block >= 750 games with Elo < -8 AND LLR < -1.5 -> H0-early; net goes on the rework list, never dropped; re-gate fresh, never pooled"
 },
 "nps": true,
 "status": "HELD_NEEDS_TRAINED_NET: no trained net exists; fill NNUEFile/exe, cand_on pins and sha256 first",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O6/REPORT.md.",
 "driver_note": "NNUEThreats=1 + NNUEFile=<trained threat net> (O6) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 468001, srand 1084240214, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_threats cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NNUEFile=<THREAT_NET.fnn2> option.NNUEThreats=1 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=468001 -srand 1084240214 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_27_threats_vs_r3base -pgnout file=F:\forge_push\gateR3_27_threats_vs_r3base\gateR3_27_threats_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_27_threats_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-28 · PureNnue=1 + NNUEFile=<GPU-trained pure net> (O4)

| field | value |
|---|---|
| status | BLOCKED: needs a trained net; tier D, trained net needed |
| candidate | `cand_r3_purennue` = `F:\opus_scratch\r3\exe\forge_r3_stack.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe`; sha256 `FILL (main session)`; build: the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | `option.NNUEFile=<PURE_NET.fnn2>` `option.PureNnue=1` |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=471001`; concurrency 8 |
| srand | **1158455101** (new; checked in SRAND_CHECK.md); test-plan row G-A5 (srand 1065932896, not reused) |
| tag / ok flag | `gateR3_28_purennue_vs_r3base` / `CR_PASS_r3_purennue.ok` |
| prebench cand_off | 312866/862329/3024920/12389307/34048354 (AL1 pins, measured on the 2047348a probe build, identity ALL OK) |
| prebench cand_on | FILL (needs the trained net: measure on the final exe with the net before install) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: uncertain to negative at H256 (drops the HCE endgame scaling); risk: high; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/O4/REPORT.md):
- material-trained smoke net: bench d16 5,669,969 (+87% nodes); trees depend on the net
- BLOCKED: no trained net exists. Every .fnn2 on the PC is a lock replica, an identity net or a CPU smoke net (find over F:\ and D:\grok-pc-data, nothing under F:\forge_nnue_train).
- Note: replace `<…NET.fnn2>` by the absolute path of the trained net (no spaces, readable by the engine) and fill `cand_on` with its 5 bench pins; the engine exits with status 2 if the net and options do not match (fail-loud rule), so a wrong path shows up as a start-up failure, never as a lock-vs-lock match.

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-28",
 "tag": "gateR3_28_purennue_vs_r3base",
 "cand": "cand_r3_purennue",
 "exe": "forge_r3_stack.exe",
 "sha256": "<FILL: sha256 of forge_r3_stack.exe>",
 "ok": "CR_PASS_r3_purennue.ok",
 "options": ["option.NNUEFile=<PURE_NET.fnn2>", "option.PureNnue=1"],
 "srand": 1158455101,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 471001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": [312866, 862329, 3024920, 12389307, 34048354],
  "cand_on": "<FILL: 5 ON pins measured with the trained net>"
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "early_stop": {
  "games": 750,
  "elo_max": -8,
  "llr_max": -1.5,
  "rule": "net-only early stop, crew vote 8/8 2026-10-25: first block >= 750 games with Elo < -8 AND LLR < -1.5 -> H0-early; net goes on the rework list, never dropped; re-gate fresh, never pooled"
 },
 "nps": true,
 "status": "HELD_NEEDS_TRAINED_NET: no trained net exists; fill NNUEFile/exe, cand_on pins and sha256 first",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/O4/REPORT.md.",
 "driver_note": "PureNnue=1 + NNUEFile=<GPU-trained pure net> (O4) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 471001, srand 1158455101, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_purennue cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_stack.exe option.Threads=1 option.Hash=16 option.OwnBook=false option.NNUEFile=<PURE_NET.fnn2> option.PureNnue=1 -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=471001 -srand 1158455101 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_28_purennue_vs_r3base -pgnout file=F:\forge_push\gateR3_28_purennue_vs_r3base\gateR3_28_purennue_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_28_purennue_vs_r3base\engine_io.log level=warn engine=true append=false
```

### R3-29 · H512 build (S-A4: FORGE_NNUE_HIDDEN=512 + FORGE_NNUE_WEIGHTS=<trained H512 net>)

| field | value |
|---|---|
| status | BLOCKED: needs a trained net; tier D, trained net needed |
| candidate | `cand_r3_h512` = `F:\opus_scratch\r3\exe\forge_r3_h512.exe` → install as `C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_h512.exe`; sha256 `FILL (main session)`; build: build_pc.sh ... -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS="<trained H512 .inc>" (S-A4 flags merged as a4fa82bb); no H512 net exists |
| opponent | `base_r3_off` = `forge_r3_base.exe` (no options); sha256 `FILL (main session)` |
| UCI option(s), candidate only | none (the build switch is the change) |
| SPRT / cap | `elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized`; 1500 games max (`-rounds 750 -games 2 -repeat`); at the cap: "Cap with no decision", nothing claimed |
| TC / engines | `10+0.1 timemargin=1000`; Threads=1 Hash=16 OwnBook=false on both sides |
| book / concurrency | 8moves_v3.pgn `order=random start=474001`; concurrency 8 |
| srand | **794186013** (new; checked in SRAND_CHECK.md); test-plan row G-A4 (srand 507544535, not reused) |
| tag / ok flag | `gateR3_29_h512_vs_r3base` / `CR_PASS_r3_h512.ok` |
| prebench cand_off | FILL (NOT AL1: the H512 exe compiles its own net; fill with its 5 bench pins before install) |
| confirm | H1 → confirm right after at 60+0.6 (`longer_tc_confirm_if_h1`) |
| expectation (not a claim) | gain: negative unless the trained net is clearly better (H512 costs -10% to -14% CPU NPS); risk: high; at [0,5]/1500 the expected outcome is "cap with no decision" unless the effect is large (section 2) |

Evidence (opus_round1/sol_SA4/REPORT.md (branch opus-sol-SA4)):
- widened H512 vs H256 on the same tree: NnueInt16 ON -12.1% / -13.7%, float -10.1% / -11.5% CPU NPS (loaded PC)
- BLOCKED: no trained net exists. Every .fnn2 on the PC is a lock replica, an identity net or a CPU smoke net (find over F:\ and D:\grok-pc-data, nothing under F:\forge_nnue_train).
- Note: replace `<…NET.fnn2>` by the absolute path of the trained net (no spaces, readable by the engine) and fill `cand_on` with its 5 bench pins; the engine exits with status 2 if the net and options do not match (fail-loud rule), so a wrong path shows up as a start-up failure, never as a lock-vs-lock match.

Manifest entry (append-ready; the owner adds it, not this job):

```json
{
 "gate": "R3-29",
 "tag": "gateR3_29_h512_vs_r3base",
 "cand": "cand_r3_h512",
 "exe": "forge_r3_h512.exe",
 "sha256": "<FILL: sha256 of forge_r3_h512.exe>",
 "ok": "CR_PASS_r3_h512.ok",
 "options": [],
 "srand": 794186013,
 "runner": "forge_queue.ps1 v3-6day r7",
 "base_override": {
  "name": "base_r3_off",
  "exe": "forge_r3_base.exe",
  "sha256": "<FILL: sha256 of forge_r3_base.exe>",
  "options": []
 },
 "openings_start": 474001,
 "prebench_depths": [11, 13, 16, 20, 22],
 "prebench": {
  "cand_off": "<FILL: 5 bench pins of forge_r3_h512.exe (its own net)>"
 },
 "longer_tc_confirm_if_h1": true,
 "watch_time": true,
 "sprt": {
  "elo0": 0,
  "elo1": 5,
  "nonreg": false
 },
 "confirm_first": true,
 "concurrency": 8,
 "early_stop": {
  "games": 750,
  "elo_max": -8,
  "llr_max": -1.5,
  "rule": "net-only early stop, crew vote 8/8 2026-10-25: first block >= 750 games with Elo < -8 AND LLR < -1.5 -> H0-early; net goes on the rework list, never dropped; re-gate fresh, never pooled"
 },
 "nps": true,
 "status": "HELD_NEEDS_TRAINED_NET: no trained net exists; fill NNUEFile/exe, cand_on pins and sha256 first",
 "notes": "R3-3 proposal 2026-10-27 (branch opus-r3-gates): one change vs the all-OFF default build of opus-r3-stack; new srand (opus_r3/R3-3/SRAND_CHECK.md); UNPROVEN, no Elo claim. Source: opus_round1/sol_SA4/REPORT.md (branch opus-sol-SA4).",
 "driver_note": "H512 build (S-A4: FORGE_NNUE_HIDDEN=512 + FORGE_NNUE_WEIGHTS=<trained H512 net>) vs base_r3_off (forge_r3_base.exe, no options). 10+0.1, SPRT [0,5] normalized a=b=0.05, cap 1500, T1 H16 OwnBook false, 8moves_v3 random start 474001, srand 794186013, conc 8, watch_time, confirm_first, LTC confirm on H1."
}
```

fastchess command as the r7 Build-Args would build it (started by the queue at BelowNormal, affinity 0xFFF0, working dir = the gate folder, stdout → `<tag>.log`):

```
C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe -engine name=cand_r3_h512 cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_h512.exe option.Threads=1 option.Hash=16 option.OwnBook=false -engine name=base_r3_off cmd=C:\Users\Administrator\grok-pc\forge_push\bin\forge_r3_base.exe option.Threads=1 option.Hash=16 option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings file=C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn format=pgn order=random start=474001 -srand 794186013 -games 2 -repeat -rounds 750 -concurrency 8 -sprt elo0=0 elo1=5 alpha=0.05 beta=0.05 model=normalized -ratinginterval 10 -recover -event forge_gateR3_29_h512_vs_r3base -pgnout file=F:\forge_push\gateR3_29_h512_vs_r3base\gateR3_29_h512_vs_r3base.pgn timeleft=true -log file=F:\forge_push\gateR3_29_h512_vs_r3base\engine_io.log level=warn engine=true append=false
```

## 5. Not gated

| item | why no gate |
|---|---|
| S32 self-play datagen v2 (FORGE_DATAGEN, `forge datagen` mode) | data generation only; no search change (main session: no gate) |
| S37 NNUE inference microbench (forge_nnue_microbench target) | tool target; the engine is unchanged |
| S04fix FORGE_ATTACKS_INIT_ONCE (synchronised first attack-table init) + cold-start probe ctest | init synchronisation, no search change (main session: no gate) |
| S08fix FORGE_PROF profiling counters (stack 9588a109) | diagnostic build switch; the main session marked it "no gate" |
| O3 search.cpp module split | no behaviour change (bench/codegen identical) |
| C2 CorrHistPlus=7 (all three keys) | three changes in one gate; C2 does not propose it (one option per gate) |
| NetScale 90 / 110 | cross-check values only; S41 proposes 99 for the lock |

## 6. Exes (built by the main session from the final opus-r3-stack head)

Final head: `FILL (main session)`.

| key | file in F:\opus_scratch\r3\exe | build | sha256 | entries |
|---|---|---|---|---|
| base | `forge_r3_base.exe` | default PC recipe build (build_pc.sh, no -D switch); used without options as the opponent of every gate | `FILL` | all (opponent) |
| stack | `forge_r3_stack.exe` | the same default build (carries every runtime option, all default OFF); candidate of the runtime-option gates | `FILL` | R3-03, R3-04, R3-05, R3-06, R3-07, R3-08, R3-09, R3-11, R3-12, R3-13, R3-14, R3-15, R3-16, R3-19, R3-21, R3-22, R3-23, R3-24, R3-25, R3-26, R3-27, R3-28 |
| nnueo2 | `forge_r3_nnueo2.exe` | build_pc.sh ... -DFORGE_NNUE_O2=1 | `FILL` | R3-01 |
| nozero | `forge_r3_nozero.exe` | build_pc.sh ... -DFORGE_NOZERO_MOVE_BUFFERS=1 | `FILL` | R3-02 |
| speedstack | `forge_r3_speedstack.exe` | build_pc.sh ... -DFORGE_SPEEDSTACK=1 | `FILL` | R3-10 |
| ttprefetch | `forge_r3_ttprefetch.exe` | build_pc.sh ... -DFORGE_S13_TT_CHILD_PREFETCH=1 (adds UCI TtChildPrefetch, default false) | `FILL` | R3-17 |
| lazyacc | `forge_r3_lazyacc.exe` | build_pc.sh ... -DFORGE_NNUE_LAZY_ACC=1 (adds UCI NnueLazyAcc, default false); name given by the main session | `FILL` | R3-18 |
| int16 | `forge_r3_int16.exe` | build_pc.sh ... -DFORGE_NNUE_INT16=1 (adds UCI NnueInt16, default false; S-A2 merged as 97b01454); name given by the main session | `FILL` | R3-20 |
| h512 | `forge_r3_h512.exe` | build_pc.sh ... -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS="<trained H512 .inc>" (S-A4 flags merged as a4fa82bb); no H512 net exists | `FILL` | R3-29 |

Before install, per exe: identity (bench d11-d22, perft5, kiwipete) for the default and node-exact switch builds, and the ON pins of each entry; the runner repeats the bench before every gate and aborts on any mismatch.

## 7. Owner decisions (noted, not applied)

1. **[0,5] with a 1500 cap decides only large effects** (section 2). Options: keep it (most entries end "cap with no decision", the Elo ± is still useful), raise the cap (r7 hard-codes 1500; e32c precedent), or use the PC's usual [0,10]. `6_gate/GATE_RULES.md` specifies a non-regression SPRT [−3,1] for node-identical speed changes (R3-01, 02, 10, 13, 16, 17, 18; S29 and S11 proposed the same).
2. **SMP entries** need Threads=4/Hash=64 on both sides: a runner change or manual runs (R3-21..23 notes).
3. **Confirm TC:** `longer_tc_confirm_if_h1` makes the r7 confirm 60+0.6 (`$LONG_TC`); the test plan asks for 40+0.4 after an H1 of an EVAL change. O8 (CorrExt) and O6 (threats) want 40+0.4 as the primary gate: set `"tc": "40+0.4"` on R3-14/R3-27 if that rule should apply.
4. **Runner blind spot for node-exact options:** the "option did not apply" test compares ON pins with the h256_e12 numbers (`$LOCKBENCH` 308972/…), not AL1; for options whose ON pins equal AL1 (R3-12, 13, 16, 17, 18, 21-23) it cannot fire. The setoption/advertise VOID check still runs, and LocklessTT, TtChildPrefetch and NnueLazyAcc print an "info string … active" line into engine_io.log.
5. **Srand bookkeeping:** `common_autonomy.ps1` Used-Srands reads RUN_INFO only under `D:\grok-pc-data\forge_push`; gate folders made since 2026-10-27 are on `F:\forge_push`, so retry srands recorded there are outside its set (SRAND_CHECK.md). The test-plan srands of these features (G-B1 …) were not reused, because the user asked for new ones.
6. **Opponent:** every entry uses `forge_r3_base.exe` (OFF stack build), not the AL1 lock exe. The stack's default build is node-identical to AL1 but carries the OFF-path costs of the merged runtime options (e.g. A1 about 1% on a quiet runner), which both sides share here; a gate against the AL1 exe would include them.

## 8. Provenance

- Read-only copies (in `F:\opus_scratch\r3\R3-3\pc_copies\`):
  - `FORGE_AUTORESTART.md` sha256 `d10ec436007c659eaa891ea3fd3427acff446867dca4b79c8bc1abae7971e6b1`
  - `FORGE_RESULTS.csv` sha256 `328b22d3c5a07272e02581d416c1d9a85e1700aaf629b04cd336478b4f698a8b`
  - `FORGE_RESULTS.md` sha256 `2357b490c0f8fca2255cd4134d552fd941149d4893725bc45de06ac0a0f8e437`
  - `INSTALL_6D_20261024.txt` sha256 `88fe800d8e3d74f2f9c08956e26ff85e68906e5ad5cf3248a794d2333225fe71`
  - `forge_gates.json` sha256 `09c995b682040ce74bb84ab10eb363346927cc6c2b6f6378bc8b93205dc2728b`
  - `forge_gates.json.PROPOSED_conc7_20261025_123500` sha256 `d1ca12066565076e2aaf774a33fbfa6b7f26941dc29d81dab6f3de3a5c1672a4`
  - `forge_queue.log` sha256 `966bfb3d88d99158b618b568b515f5a20b85ec4cf4f9be9a83a2b9c7be9dbf6e`
  - `forge_queue.ps1` sha256 `636b6cca691d0707449147fce1cafc42c3235c22a4419b05e0b2307e1fc2c168`
  - `forge_queue_state.json` sha256 `0e73a6757d54365e6c63da17746618c9457c275d3c1de00a1e584dbb9662881f`
- Job REPORTs: `opus_round1/<JOB>/REPORT.md` on opus-r3-stack (O1, O1-LTT, O2, O4-O8, C1-C6, sol_A1, sol_S11, sol_S13, sol_S14, sol_S29, sol_S41, sol_SIT), `opus_round1/sol_S12|sol_SA2|sol_SA4/REPORT.md` on their branches; R3-1 cross-checks `opus_r3/R3-1/logs/` @ 2047348a.
- Tools: `opus_r3/R3-3/tools/` (`srand_scan.py`, `make_cands.py`, `choose_srands.py`, `measure_pins.py`, `run_pins.sh`, `sprt_cap_model.py`, `entries.py`, `render.py`, `summarize_scan.py`, `dump_manifest.py`, `show_entries.py`).
