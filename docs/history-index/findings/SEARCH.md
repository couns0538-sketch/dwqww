# Search findings

This file is thin on purpose. The search-gap, speed-lane, and movegen branches have not been read yet. What is here is only what the lock record and the H512/fair-eval reports say about search, plus the inventory of where the unread reports sit.

## Read

`forge-combo29/LOCK.md`, `forge-combo29/README.md`, `forge-combo29/docs/overnight/RANKED.md`, `forge-combo29/docs/context/HANDOFF.md`, and the search-related sections of the H512 and fair-eval reports. Blobs are in `COVERAGE.md`.

Combo29's overnight table is NPS against trial_w6, one thread, core 4, 10 blocks, one outlier dropped. Median deltas that won, from the table:

- combo29 (KING+SEE+EQ32+CLANG) +10.191% (CI 10.099..10.409)
- combo28 (SEE+EQ32+CLANG) +9.667%
- clang_four (KING+BADCAP+SEE+EQ32+CLANG) +9.516%
- Down to gcc_badcap +0.444% and combo6 +0.273%, still marked win
- Losses: combo9 (KING+EQ32) -0.427%; combo3 (KING+BADCAP) -5.965%
- Errors, no delta: gcc_see, combo25 (KING+EQ32+CLANG)

The lock text says combo29 is bit-exact with trial_w6 on nodes and on 12,000 FENs, and that the +10.19% NPS has no Elo claim. The handoff for three further candidates (clang_four as a scoped bundle, clang_only, gcc_king) says builds were not run: no exe, no pins, no match. Logs marked HISTORICAL are not results for those candidates.

H512 does not change move generation when the v3 switch is off. When the switch is on, bench node counts change because the evaluation changes. That is a different tree, not a search-patch speedup. Equal-node matches are the report's way of taking speed out. Candidate 1 loses that comparison; candidate 3 wins it. See `NNUE.md`.

Job D's U8 and run 5 NPS gaps versus the replica, on the same code, are tree effects. The per-evaluation microbenchmark says their inference cost matches the replica.

## Read at checkpoint 2

Full reads, blobs in `COVERAGE.md`. None of the percentages below were re-benched.

### Search gap: no mechanism to hand off

`fable52-search-gap-20261109` @ `56a76b153bb88026f2d83d65df6e422b0f3298f9`. Verdict in `fable_search_gap/NO_QUALIFIED_GAP.md`: **no qualified gap**. Twenty search ideas were checked. Nineteen were already in the lock, already built or gated, or already in the crew notes. The one unowned idea is enhanced transposition cutoffs (a child table entry ends the node). A replica that links the lock board and evaluation, and is not the lock search, did not show a node saving. The pre-committed rule required the 95% range of the node ratio to lie entirely under 1.00.

| Set | Node ratio, mechanism vs plain | Range | Placebo |
|---|---|---|---|
| 91 positions, 6 plies | 0.95 | 0.83 to 1.07 | 0.98 (0.88 to 1.08) |
| 91 positions, 8 plies | 0.92 | 0.81 to 1.03 | same placebo family |
| 336 positions, 48 openings, 6 plies | 0.987 | 0.954 to 1.022 | 0.999 (0.962 to 1.037) |

With more than six pieces the second set is about 1.02, range 0.98 to 1.05: no saving. With six or fewer, 0.94, range 0.87 to 1.01: up to about 13% would still fit. Lookup time on a loaded machine was the same order as the possible saving. The report says this is "not shown", not "refuted". A smaller than 5% average saving could not have been seen.

On Fine 70 the lock plays Kb1 from depth 22. Three of eight mechanism settings in the replica play the drawing move Kb2 at some depth. The plain replica keeps Kb1 under ten placebo-size changes. The cause is not established. The report does not claim Elo.

The optional next measurement is a counting-only switch inside the real lock search, default off, pins unchanged. Thresholds are fixed in `FALSIFICATION.md` section 3: close the idea if the share of nodes under such cutoffs is smaller than the lookup time; write a spec if it is larger by at least 2 points; otherwise leave it undecided. This job did not build that switch.

Its dedupe is a snapshot of 387 branch tips on 2026-11-09, plus named PC folders, and it says the combo29 search source was not in the repository then. `lock/combo29-20261110` later holds that source. Re-check `DEDUPE.md` against tips pushed after 2026-11-09 22:19 PT before calling the idea still unowned. `DEDUPE.md` itself was not read in this pass; the verdict file's table of the nineteen owned ideas was.

`data/gate_table_summary.md` summarises 126 gate rows and 194,360 games, with 70 time losses. Classes: 80 capped, 18 H0, 14 H1, 8 NOT CLEAN, 4 H0 early, 1 non-regression H1, 1 trial. This is the dossier's summary of a CSV, not a re-score of the games. Two results that must both be kept:

- `option.EvalOptimism=40`: UE3B capped at +6.95 Elo over 3,000 games (LLR 2.08), then UE3B-R6K H0 at -5.30 over 2,360 games.
- `option.EvalFileV2` for the U8 net: UO30U8 H1 at +16.50 over 2,528 games, then UO30U8c capped at +3.04 over 4,000 games. Job D's later reading is that the confirm used a slow exe. The summary alone does not say that.

Eight NOT CLEAN rows from 2026-10-30 through 2026-11-09 include the HalfKA 1024 finishes (about -96 to -124 Elo) and are void by the dossier's own rule. Do not cite them as strength.

### Speed lane: bit-exact patches, no gain under load

`fable52-speed-lane-20261109` @ `08897a88e11c707c0ac4e39c19e44c06e1360bdd`. Four new `board.cpp` switches, default 0: `WITNESS_NOPIN`, `EVADE_LEGAL`, `PAWN_CAPMASK`, `CHECKERS_KL`. `KING_PAWN_CACHE` is not new: the same shelter cache is commit `928f1ff7a10a` on `cursor/chess-engine-elo-8295` (2026-10-13).

Identity checks that finished found no difference from the lock. The full 12,000-position cold runs were stopped incomplete on the owner's instruction. `BUNDLE4`'s verify engine did cover all 12,000 rows with 0 differences. No item was marked FAIL.

Speed, called INDICATIVE, one shared CPU under gate load, a new exe copy per arm:

| Item | Median | Interval | Blocks |
|---|---|---|---|
| `WITNESS_NOPIN` | -1.02% | -1.25 to -0.86 | 60, resolved slower |
| `BUNDLE4` (all four) | -0.70% | -0.99 to -0.39 | 100, resolved slower |
| `BUNDLE3` (without witness) | -0.22% | -0.90 to +0.47 | 34, stopped |
| `EVADE_LEGAL` | -0.63% | -0.99 to +0.37 | 34, stopped |
| `PAWN_CAPMASK` | -0.39% | -1.14 to +0.46 | 34, stopped |
| `CHECKERS_KL` | -0.59% | -0.95 to +0.48 | 34, stopped |
| lock vs lock | -0.02% and 0.00% | | 40 and 36 |

The same two exe files read -3.65% over 30 blocks and +0.30% two hours later. The report says a fixed pair of files can be several percent off, which is why later timings used a fresh copy per arm. `BENCH.md` was not read; these figures are from STATUS and README only.

`WITNESS_NOPIN` skips king-line builds that overlap the transposition-table wait, and rebuilds some of them after the probe. The report offers that as a reading, not a shown cause. At hash 1 / 16 / 256 MB it read -0.85%, -0.61%, -1.56%, intervals overlapping.

As of this job's fetch (08:11 and again 15:48 on 2026-11-10) six combo29 headers were on no fetched branch. That statement is historical. `lock/combo29-20261110` @ `16833ecc03b425586f91f4c8834dea8807bf4c22` holds the source, and the CPU job below cloned it the same afternoon.

### Move-generation proof: identity pass, not a speed result

`fable52-movegen-proof-20261110` @ `2ff77f98927cf19d55d6cac5cf182a81eb0d71e6`, cut from the speed-lane tip. Six candidates (the four board patches, the old king-pawn cache, and `BUNDLE3`) PASS a two-tier rule: 20,000,000 auxiliary positions and 20,000,000 release-exe positions each, 0 differences. Checkers and static eval were compared on probes because the release exe does not print them. Release exes were compared on legal moves, order, and reply counts. Pins 13/13, perft divide, warm transcript, and a threads soak (stability only) matched. The status says a PASS does not authorise a lock change. `PROOF.md` and `DONE.md` were not read.

### CPU lane: two sub-2% screenings, two slowdowns, sanitizers clean

`fable52-cpu-20261110` @ `ea3759a9ec3b17c58e3daeab8ff31af53e7ae6ab`, based on the lock commit. Pre-registered bar was +2% median. None reached it.

| Flag | Screening median | Spread of pairs | Outcome |
|---|---|---|---|
| `FORGE_SPD_NNUE_FUSE_EVAL` | +0.93% (repeat +1.46%) | -0.99 to +4.60; repeat -1.62 to +6.13 | stopped, below the bar |
| `FORGE_SPD_PREFETCH_PICK` | +0.72% | -2.17 to +4.57 | stopped, below the bar |
| `FORGE_SPD_EVAL_PIPELINE=2` | -1.53% | -3.47 to +1.12 | slower |
| `FORGE_SPD_NNUE_WPREFETCH=16` | -4.42% | -9.18 to -2.21 | slower |
| lock vs lock | -0.30% | -5.19 to +7.68 | noise floor |

The report itself says a single lock-against-lock pair can read from -5% to +8%, and that QA's quiet ABBA is the real test. Do not treat +0.93% as a measured speed lock. Both small-gain candidates matched the lock on 48,000 release search rows (`go depth 12`, net on and off, flag 0 and 1). The harness does not exercise `PREFETCH_PICK`. Fusing update and evaluate is listed in an O2 note as not done and expected to be small; this job found no earlier build. The two patches touch different code and were not combined.

Profile, net on, `bench 22`, one thread, instruction-pointer samples: hand-crafted eval 20.9%, make/unmake and legality 17.9%, move ordering 16.6%, search 15.6%, accumulator update 8.3%, movegen 7.3%, table 7.3%, output layer 5.4%, refresh 0.0%. Two runs, 20,265 samples. `PROFILE.md` was not read.

ASan and UBSan full benches matched the pins with no report. ThreadSanitizer is blocked on the installed Windows compilers. Determinism: 13,000 of 13,000. Table stress: 480 of 480, and the ASan run clean. Threads 2-9 showed no crash and no illegal move, and say nothing about races. Static-eval parity against the lock exe is blocked because the exe has no such command. A 25-minute bug hunt on the lock source and exe found no defect. `DONE.md` was not read; the counts above are from the README.

Duplicate check on this branch is incomplete: the job was not allowed to fetch other history.

## Still not read on these branches

| Branch | Tip | Still closed |
|---|---|---|
| `fable52-search-gap-20261109` | `56a76b153bb88026f2d83d65df6e422b0f3298f9` | `DEDUPE.md`, `EVIDENCE.md`, `REVIEW_LOG.md`, `COVERAGE.md` |
| `fable52-speed-lane-20261109` | `08897a88e11c707c0ac4e39c19e44c06e1360bdd` | `BENCH.md`, `DUPCHECK.md`, `PROFILE.md`, `QA_ABBA_PROTOCOL.md` |
| `fable52-movegen-proof-20261110` | `2ff77f98927cf19d55d6cac5cf182a81eb0d71e6` | `PROOF.md`, `DONE.md`, `evidence/TABLES.md` |
| `fable52-cpu-20261110` | `ea3759a9ec3b17c58e3daeab8ff31af53e7ae6ab` | `DONE.md`, `PREREG.md`, `PROFILE.md` |
| `cursor/speed-and-search-patches-c7cb` | `2cf370d3e7672c18692bfa044ec376e6e584eff6` | whole tree (JS patches). Subject says node-identical speed patches |
| `cursor/smp-threads-fixes-c7cb` | `c4314e3bde6e8372419227cc22b032319487aa71` | subject only: `search/smp.js` patch paths |

## Source inventory, not a review

`inventory/KEY_SOURCE_BLOBS.tsv` lists unique blobs whose basename is `search.cpp` or a neighbour. There are 95 `search.cpp` blobs and 71 `search.hpp` blobs across tips. None of those blobs were diffed in this checkpoint. A later pass should diff only the pairs a report names.

October `forge/` hourly branches are mostly repeated tips. Shared commit `356e863dbd86d2ce24b8ee9486d7406f1d525480` is the tip of 29 branches whose subjects are "Fix Forge 6.4 native CI to compare pinned pre-fix commit". Branch names about terminal-zero nodes, qsearch, and later hours do not add a commit. Read that commit once if the CI fix matters, and do not read it 29 times.
