# Claude deep research 2026-10-30: new ways to make Forge stronger or faster

Status: **STATUS: COMPLETE for this round** (2026-10-31 ~01:20 PC clock). At the owner's request
("use what deep research has already") the workflow was stopped after its search and fetch
phases, before the 3-vote verify phase, to save usage: section 11 holds its claims as read by
one agent each; sections 0-10 were checked by me against the sources and Forge's code. The run
can be resumed in the same Claude Code session (finished agents are cached) with
`Workflow({scriptPath: <session>/workflows/scripts/deep-research-wf_d04a0303-91b.js, resumeFromRunId: "wf_d04a0303-91b"})`.
Branch `claude-research-20261030` (from `main` 5176ddf7, report only, no engine code).
Method: the Claude Code `/deep-research` workflow (5 search angles, source fetch, 3-vote adversarial
claim check, synthesis; run `wf_d04a0303-91b`) plus my own direct checks: licence of every repo read
from the GitHub licence API / LICENSE file, and a grep of the newest Forge heads to drop ideas Forge
already has.

## Rules used for this list

- Skipped because Forge already has them or the user excluded them: transposition table, LMR, all
  pruning, singular extensions, history and correction history, SPSA, quantization-aware training,
  50-move hash cutoffs, the UHO book, the bullet trainer, relabeling/rescoring, output buckets,
  threat inputs, pawn pairs, the 2026 Stockfish search bundle. Also already in Forge or its branches
  (from the repo): HalfKA K32H3^ NNUE path (opus-r10-halfka), nnue-pytorch pipeline (opus-r11),
  Triton trainer kernels (opus-r6), LTO+PGO (opus-r12), SmpV2, TimeManV2, own datagen, fastchess
  gates, own SPSA tuner.
- Licences: only MIT / BSD / Apache-2.0 / CC0 (or public domain) code, tools and data are
  recommended for use. GPL/AGPL work is marked **[IDEAS ONLY]**: read the idea, never copy code.
- Every Elo or speed number below is the number reported by the cited source for *that* engine.
  None of them was measured on Forge; nothing here was gated. Treat each as a hypothesis for a
  Forge SPRT.

## 1. Top picks so far (ranked by expected gain per day of work)

| # | Idea | Expected gain (evidence) | Effort | Licence of what we use |
|---|---|---|---|---|
| 1 | E3 eval post-processing on the HalfKA path: material scaling, optimism, 50-move damping, draw jitter | Stockfish: about +8 to +12 Elo over 5 tests | 1 day + tuning | own code, ideas from GPL |
| 2 | S1 Windows large pages for the TT and the 66 MiB HalfKA weights | +5-10% NPS typical in Stockfish (up to 30%); weights alone +3.9 Elo STC in Stockfish | 0.5 day | own code from Microsoft docs |
| 3 | E2 reorder first-layer neurons by activation rate | ~2% NPS, bit-identical evals (about +4 Elo STC) | 0.5-1 day | own script, idea from GPL docs |
| 3a | S3 accumulator update kernel: tile several registers, no per-chunk branch | Stockfish: +4% to +17% NPS from one tile constant (compiler-dependent) | hours | own code, idea from GPL |
| 3b | T4 fastchess options gates do not use (`-check-mate-pvs`, draw/resign/TB adjudication, `-strict`) | faster gates (71% of gate125 games were draws), mate-PV checks | minutes | MIT, already installed |
| 3c | S2 one shared copy of the net weights for all engine processes | Stockfish: +4.7 Elo on mixed hardware, +24.8 Elo / +38% NPS with many concurrent games; helps gates and datagen throughput | 1-2 days | own code, idea from GPL/AGPL |
| 4 | D2 Lichess puzzles as a tactical regression gate | no Elo by itself, catches regressions before gates | 0.5 day | CC0 data |
| 5 | E1 small second net for lopsided positions | Stockfish: about +2 Elo STC and LTC, +1.5 more with re-eval | 2-4 days | own code + own data |
| 6 | D1 Lichess eval DB as validation (and maybe training) data | unproven for Forge | 1 day | CC0 data |
| 7 | T1 targeted CC0 books (endgames, closed, transpositions) | faster, sharper gates for targeted changes | none | CC0 |
| 8 | T2 Bayesian tuner for 2-6 parameters | unproven vs SPSA | 1 day | Apache-2.0 / MIT |
| 9 | M1 thread voting for the reported move | Stockfish +3.8 to +5.6 Elo at 8-31 threads; small at Forge's 2-3 threads | 0.5 day | own code, idea from GPL |
| - | E4 bigger L1 / L2 | loses or ties at STC, wins only at long TC | GPU days | - |

## Contents

1. Top picks (summary table)
2. Evaluation / NNUE ideas
3. Speed ideas
4. Search, time and SMP ideas outside the excluded list
5. Training data
6. Trainers and data tools
7. Testers and tuners
8. Tablebases
9. GPL / AGPL ideas only
10. Checked and dropped

(Sections are filled as findings come in.)

## 0. What Forge already has (repo grep, 2026-10-31 ~00:30 PC clock)

Checked with `git grep` over the newest head `origin/opus-r12-pgo-net` 56cf4844 and over all 367
`origin/*` heads (`src/`, `include/` only). Ideas below that hit one of these are dropped.

| Feature | Where found | Verdict |
|---|---|---|
| AVX-512 VNNI int8 dot products (`_mm512_dpbusd_epi32`) | 56cf4844 `src/nnue_halfka.cpp:195-277` | have it |
| Pairwise multiplication after the feature transformer | 56cf4844 `src/nnue_halfka.cpp:172` (`pairwise()`) | have it |
| Node-effort time management (`TmEffortBase`, `root_move_nodes_`) | 56cf4844 `src/search.cpp:58`, `:1185-1225` | have it |
| Best-move stability in time management | 56 heads (r3/r5 engine line, astra-*) | have it |
| Syzygy probing (`include/forge/syzygy.hpp`, `src/search/syzygy.inc`, `tablebase.inc`) | 39 heads, e.g. `origin/opus-r5b-speed`; **not** in the R10-R12 HalfKA line 56cf4844 | have it (port to the HalfKA line is open) |
| Upcoming-repetition (cuckoo) detection | 39 heads (same r3/r5 line); not in 56cf4844 | have it (same port gap) |
| PEXT/PDEP move generation | 244 heads | have it |
| TT prefetch, aspiration windows, ponder, hashfull | 56cf4844 `src/search.cpp` | have it |

Not found in any of the 367 heads (no matching symbol): Windows large pages
(`MEM_LARGE_PAGES` / `SeLockMemoryPrivilege`), a second small net (`smallnet`), eval optimism,
NUMA code, `MultiPV`, `Chess960`, `UCI_ShowWDL`. These are the open slots the research below
targets.

No `nnz` symbol either, but reading the code shows the HalfKA first dense layer already skips all-zero 4-byte
input blocks (`block_affine()`, 56cf4844 `src/nnue_halfka.cpp:223-245`, "blocks whose 4 inputs are
all zero are skipped"), so Stockfish's block-sparse layer is **already in Forge**. Only the cheap
neuron-reordering add-on (E2 below) is new.

How to read the Elo numbers: Stockfish's own rule of thumb for small speed-ups (< ~5%) is
**Elo_STC = 2.10 x, Elo_LTC = 1.43 x** for an x% NPS gain
(<https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html>, "Elo from speedups").

## 2. Evaluation / NNUE ideas

### E1. Second small net for lopsided positions (dual NNUE)

- **Source:** Stockfish commit `584d9efedc` "Dual NNUE with L1-128 smallnet" (2024-01-07)
  <https://github.com/official-stockfish/Stockfish/commit/584d9ef>, engine code by mstembera
  (PR #4898); follow-up `0b08953174` "Re-evaluate some small net positions" (PR #5238).
- **Licence:** Stockfish GPL-3.0 -> **[IDEAS ONLY]**. The data filter script it cites
  (`linrock/nnue-data`) has **no licence** on GitHub -> do not copy it; a filter
  `|material eval| > 1000 cp` is ten lines to write ourselves.
- **Evidence:** small net = L1 128, trained only on positions with `abs(simple_eval) > 1000`;
  switch in eval: `smallNet = abs(simpleEval) > 1100`. STC <0,2>: 62,432 games
  W 15875 L 15521 D 31036 (+1.97 Elo), LTC <0.5,2.5>: 64,830 games W 16118 L 15738 D 32974
  (about +2.0 Elo by score). The re-eval follow-up (use the main net when the small net's eval is
  close to balance) added STC 92,320 games W 23941 L 23531 (about +1.5) and LTC 98,934 games
  W 24907 L 24457 (about +1.6).
- **Forge fit:** the R11 pipeline (`opus-r11-nnue-pipeline`) can train an L1-128 K32H3^ net from a
  filtered binpack; the engine needs a second HalfKA weight set and a threshold switch in eval.
  Gain in Stockfish was small (~2 Elo); it pays more if Forge's L1-1024 net is the main NPS cost.
- **Effort:** 2-4 days (filter + training run + second net path + parity tests).
- **How to test:** exact parity of the small net vs nnue-pytorch (skill
  `forge-halfka-parity-test`), OFF bench = lock pins, NPS ABBA on the lopsided half of the bench,
  then SPRT STC [0, 2] and LTC [0.5, 2.5].

### E2. Reorder first-layer neurons so non-zero inputs cluster (free speed, same eval)

- **Source:** Stockfish commit `38e61663d8` "Use block sparse input for the first layer"
  (2023-06-12, PR #4612) <https://github.com/official-stockfish/Stockfish/commit/38e6166>: "This
  commit includes a net with reordered weights, to increase the likelihood of block sparse
  inputs, but otherwise equivalent"; nnue-pytorch docs, "Linear layer with sparse input, alternative
  approach": reordering "is a minor (~2%), but essentially free, speedup"
  <https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html>.
- **Licence:** GPL-3.0 (Stockfish, nnue-pytorch docs) -> **[IDEAS ONLY]**; the permutation is
  a few lines of numpy on our own exporter output.
- **Evidence:** ~2% NPS per the docs (the 9.9% / +10 Elo STC in the same commit is the sparse
  kernel itself, which Forge already has). By the rule above, 2% is about +4 Elo STC / +3 LTC.
- **Forge fit:** log how often each pairwise output byte is non-zero over a bench run, sort the FT
  neurons (and the matching L1 weight columns) so frequently-active ones share 4-byte blocks,
  write the permuted net. Bit-identical evals, so it is testable without games.
- **Effort:** 0.5-1 day (activation logger + permute script + loader unchanged).
- **How to test:** eval of every bench position identical before/after (parity), bench node count
  identical, NPS ABBA with `--copies` (skill `forge-engine-verify`); no gate needed if evals are
  bit-identical and NPS rises.

### E3. Eval post-processing on the HalfKA path (material scaling, optimism, 50-move damping, draw jitter)

- **What Forge does now:** `Worker::halfka_evaluate()` returns
  `std::clamp(halfka::evaluate(...), -30000, 30000)` (56cf4844 `src/search.cpp:661-692`): the
  raw net output, nothing else. A grep of all 367 heads finds no `optimism` and no draw
  randomization (`nodes & 2`); the R12, `opus-r3-stack` and `opus-r5b-speed` heads have no
  50-move damping or material scaling in eval (their "scale" hits are only the time manager's
  `falling_eval_scale`).
- **What Stockfish master does today** (`src/evaluate.cpp:59-79`, read 2026-10-31):
  `v = nnue + (nnue + optimism) * correl / 65536` (correl = agreement of NNUE and material),
  then `v += material * v / 90649` (scale by material left), then `v -= v * rule50 / 189`; and
  `value_draw(nodes) = VALUE_DRAW - 1 + (nodes & 0x2)` in search (`src/search.cpp:146`).
- **Licence:** Stockfish GPL-3.0 -> **[IDEAS ONLY]**; each piece is one or two lines of our own
  arithmetic.
- **Evidence (Stockfish fishtest, Elo from the W/L/D score):**

  | Piece | Commit | STC | LTC / VLTC |
  |---|---|---|---|
  | NNUE scaled by material ("keep more material") | `1dbd2a1ad5` 2020-09-27 | 14,744 games, about +4.1 | 8,912 games, about +4.6 |
  | Include pawns in that scaling | `5af09cfda5` 2020-09-28 | 15,072 games, about +3.7 | 25,880 games, about +2.0 |
  | Optimism (root-score dependent offset before scaling) | `a5a89b27c8` 2021-11-21 | yellow (+0.2) | 121,656 games, about +1.4 |
  | Optimism scaled by NNUE-vs-material "complexity" | `1066119083` 2021-12-30 | 88,392 games, about +1.5 | 37,848 games, about +2.5 |
  | Random +-1 draw score (3-fold blindness) | `97d2cc9a9c` 2018, `770c8d92f3` 2019 | yellow (+1.0) | VLTC 120+1.2 2 threads: 51,902 games, about +2.0 |

  Total in Stockfish: roughly +8 to +12 Elo (sums of SPRT estimates overstate the real total,
  per the Fishtest FAQ). Forge's net, draw rate and eval scale differ, so each piece must be
  re-measured; the draw jitter mainly matters at long TC.
- **Forge fit:** all four live in `halfka_evaluate()` and the draw-return sites of
  `src/search.cpp`; keep the TT storing `raw_eval` as it does now and apply correction history
  after the scaling (Stockfish order). Constants need one SPSA pass afterwards (Forge's R9
  tuner can take them as new tunables).
- **Effort:** 1 day for all four behind one default-OFF option (`EvalPostV1`), plus tuning.
- **How to test:** OFF bench = lock pins; ON bench changes (expected); one SPRT per piece in the
  order of the table (material scaling first), STC [0, 2] then LTC [0.5, 2.5]; draw jitter
  needs a longer TC (Stockfish only saw it pass at 120+1.2).

### E4. Bigger L1 or L2: only worth it if Forge targets long time controls

- **Forge now:** HalfKA K32H3 net with L1 1024; L1/L2/L3 are read from the net file (engine
  limits `MaxL1 = 4096`, `MaxL2 = 64`, `MaxL3 = 64`, 56cf4844 `include/forge/nnue_halfka.hpp:25-27`),
  so a bigger net needs a new training run but no engine change.
- **Evidence (Stockfish, architecture history
  <https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue_architecture_history.html>):**
  - L1 1024 -> 1536 (`c1fff71650`, 2023-05-31): **failed STC** (13,728 games, about -6 Elo),
    failing LTC (about -0.8), passed VLTC 180+1.8 (47,616 games, about +2.3) and VLTC SMP 60+0.6
    8 threads (19,942 games, about +4.2).
  - L1 1536 -> 2048 (`915532181f`, 2023-07-01): failed STC, LTC +0.68 +- 1.5 (40,000 games),
    passed VLTC 180+1.8.
  - L2 16 -> 32 at L1 1024 (`a6d055d7e2`, 2026-02-18, the same L1 as Forge): **failed STC**
    (189,184 games, +0.0), passed LTC (37,902 games W 9833 L 9509, about +3.0) and VLTC SMP.
- **Verdict:** every size step lost or tied at STC and won only at long TC, because the slower
  net costs more search than it gains in accuracy at short TC. Do it only if Forge's target is
  long TC; then L2 32 is the cheapest step (L1 stays at 1024, so NPS drops least).
- **Licence:** ideas only (Stockfish GPL); the training change is a config value in Forge's own
  R11 pipeline (nnue-pytorch is GPL, run-only, as today).
- **Effort:** one R11 training run per size (GPU days), no engine code.
- **How to test:** gate at the TC Forge cares about (STC alone would reject it, as it did in
  Stockfish), plus NPS ABBA to know the speed cost.

## 3. Speed ideas

### S1. Windows large pages for the transposition table and the net weights

- **Source:** Stockfish commit "Add support for Windows large pages" (Sami Kiminki, 2020-05-13,
  PR #2656) <https://github.com/official-stockfish/Stockfish/pull/2656>; Microsoft "Large-Page
  Support" <https://learn.microsoft.com/en-us/windows/win32/memory/large-page-support>.
- **Licence:** Stockfish GPL-3.0 -> **[IDEAS ONLY]**; the implementation is plain Win32
  (`AdjustTokenPrivileges(SeLockMemoryPrivilege)` + `VirtualAlloc(MEM_LARGE_PAGES)`) written
  from Microsoft's documentation.
- **Evidence:** commit message: "might improve speed, 5% - 30%, depending on the hardware, the
  number of threads and hash size. More for large hashes, large number of threads and NUMA";
  Stockfish readme: "Typical increases are 5..10% in terms of nps, but speed increases up to 30%
  have been measured". 5% is about +10 Elo STC by the rule above. Not found in any Forge head.
  **The net weights matter as much as the TT:** Stockfish `485d517c68` "Add large page support
  for NNUE weights" (2020-09-21, PR #3081, "No functional change") passed STC {-0.25,1.25} with
  14,896 games W 1854 L 1686 D 11356 (about +3.9 Elo); Stockfish master today also puts history
  tables and thread data in large pages (`LargePagePtr` in `src/history.h`, `src/thread.h`).
  Forge's HalfKA feature transformer is int8 with 96 buckets x 704 planes = 67,584 features x
  L1 1024 = **66 MiB** of weights read at random rows on every accumulator update, so this
  applies even when a gate runs with a tiny hash.
- **Forge fit / caveat:** the account that runs gates needs the "Lock pages in memory" right
  (secpol.msc, then log off/on). Large pages are never paged out, so a 1 GB hash takes 1 GB
  away from the trainer and self-play for good; keep gate hashes small and keep the PC's
  free-RAM rule (6-8 GB). Fall back to normal allocation when the call fails and say so with
  an `info string`.
- **Effort:** 0.5 day.
- **How to test:** no functional change, so bench/perft identical to the pins; NPS ABBA at
  Hash 64 / 256 / 1024 MB, Threads 1 and 3 (skill `forge-engine-verify`); gate only if the A/B
  shows >= 1%.

## 4. Search, time and SMP ideas outside the excluded list

The exclusion list (TT, LMR, all pruning, singular extensions, history and correction history,
50-move hash cutoffs, the 2026 Stockfish search bundle) plus what Forge already has (aspiration,
ProbCut, prefetch, ponder, node-effort and falling-eval time management, best-move stability,
cuckoo repetition in the r3/r5 line, SmpV2 helper diversification) leaves little on the search
side. The draw-score jitter is listed under E3 because it is one line next to the eval
post-processing. One SMP item remains:

### M1. Stockfish-style thread voting for the reported best move

- **Forge now:** SmpV2 (`origin/fable-fb2-j5`, `src/search.cpp:1563-1564`) reports "the deepest
  completed result of any thread"; R12 56cf4844 has no thread-result selection at all. (A grep
  hit for "vote" in `origin/astra2-smpv2-mate` is only the comment "crew vote: gated
  separately".)
- **Source:** Stockfish `d96c1c32a2` "Introduce voting system for best move selection"
  (2018-08-08) and `67ae53b020` "New voting formula for threads" (2018-12-18, quadratic votes:
  each thread votes for its best move with weight `(score - minScore + c)^2 * depth`, the move
  with most votes wins, then the deepest thread voting for it reports).
- **Licence:** Stockfish GPL-3.0 -> **[IDEAS ONLY]**.
- **Evidence:** `67ae53b020`: 8 threads 5+0.05, 20,202 games W 4031 L 3813 (about +3.8 Elo);
  8 threads 20+0.2, 14,330 games W 2290 L 2115 (about +4.3); 31 threads 5+0.05, 20,000 games
  +5.63 +- 2.8. The gain grows with thread count; at Threads 2 (Forge's gate setting) expect
  little.
- **Effort:** 0.5 day (votes collected when each thread finishes an iteration).
- **How to test:** an SMP SPRT at the thread count Forge will play with (Threads 3 on a 3-CPU
  mask under the PC rules); Threads 1 bench must stay identical.

## 5. Training data

### D1. Lichess evaluation database (CC0)

- **Source:** <https://database.lichess.org/> (Evaluations): "Database exports are released under
  the Creative Commons CC0 license"; 416,442,401 positions evaluated with Stockfish
  (`lichess_db_eval.jsonl.zst`, updated 2026-10-05), each with depth, knodes and several PVs.
  Parquet mirror: <https://huggingface.co/datasets/Lichess/chess-position-evaluations>
  (licence `cc0-1.0`, 1,003,347,246 rows, 44.1 GB).
- **Licence:** CC0 (data). Exception: Lichess *broadcast* games are CC BY-SA 4.0 (Lichess 2025
  end-of-year post), so leave those out.
- **Use for Forge:** (a) an outside validation set for every new net (mean error of Forge's
  eval vs a deep Stockfish eval, by phase) next to the 013/014 holdout; (b) extra training
  positions in eval-only mode (no game result, so lambda = 1.0 for these rows); (c) opening
  positions from real games for datagen.
- **Caveat:** these labels are Stockfish output. The CC0 licence allows any use, but originality
  rules differ between rating lists and engine communities; check the policy of any list Forge
  will enter before training on them. Use (a) is safe either way.
- **Evidence:** none for Forge (**unproven**). Size and licence are verified.
- **Effort:** 1 day for a jsonl -> plain/binpack converter (keep the deepest eval, first PV).
- **How to test:** R11 pipeline A/B: same recipe with and without a slice, compare the 013/014
  holdout loss, then a gate.

### D2. Lichess puzzles as a tactical regression set (CC0)

- **Source:** <https://database.lichess.org/> (Puzzles): 6,157,341 rated and tagged puzzles,
  CC0.
- **Use:** a much larger WAC: solve rate at fixed nodes per rating band and theme (mate-in-N,
  promotion, ...), run on every engine or net candidate before a gate. Catches tactical
  regressions in minutes (the R5D mate bug class).
- **Effort:** 0.5 day (CSV -> EPD with best move + a fixed-node runner).
- **How to test:** run old vs new engine on the same 10k-puzzle sample; a drop beyond the
  binomial error blocks the gate.

### D3. Leela (Lc0) training data: licence is ODbL, not on the allowed list

- **Source:** lczero.org blog "The importance of open data" (2021-06-14)
  <https://lczero.org/blog/2021/06/the-importance-of-open-data/>: "made available under the Open
  Database License ... Database Contents License".
- **Verdict:** ODbL/DbCL is a share-alike database licence, not MIT/BSD/Apache/CC0, so it is
  **excluded** by the rules of this report, even though Stockfish's nets are trained on it.
  Ask the owner before any use.

### D4. Lichess opening names/lines (CC0)

- **Source:** <https://github.com/lichess-org/chess-openings> (licence **CC0-1.0**, 579 stars,
  pushed 2026-10-29): every named opening as a move list (ECO A-E TSV files).
- **Use:** a balanced, human-opening seed set for datagen and for a non-UHO sanity gate.
- **Effort:** none beyond a TSV -> EPD/PGN step.

## 6. Trainers and data tools

- **No mature permissive NNUE trainer besides bullet** (which is excluded). GitHub search on
  2026-10-31 (`nnue trainer license:mit`, `nnue license:apache-2.0`, `nnue train
  license:bsd-3-clause`, by stars) found only small or old projects:
  `amanjpro/zahak-trainer` (MIT, 7 stars, last push 2022), `nicotina04/noru` (Apache-2.0, Rust
  library, 4 stars), `github-jimjim/nnue-trainer` (MIT, 1 star). Other trainers are GPL
  (`official-stockfish/nnue-pytorch`, `jnlt3/marlinflow`) or have no licence (`Luecx/Grapheus`).
  Verdict: keep nnue-pytorch run-only (as R11 does); nothing permissive is worth switching to.
- `Disservin/fast-datagen` (MIT, 2023): small datagen tool by the fastchess author; Forge's own
  R8 native driver already does this job, so only worth a read.
- More permissive engines to read (adds to T3): `MinusKelvin/frozenight` (Apache-2.0, NNUE-only
  Rust engine), `Timmoth/Sapling` (Apache-2.0, C#).

## 7. Testers and tuners

### T1. Stockfish books repo: CC0 books other than UHO

- **Source:** <https://github.com/official-stockfish/books> (licence **CC0-1.0**, GitHub API).
- **Useful non-UHO files:** `8moves_v3.pgn`, `noob_3moves.epd` (balanced), `endgames.epd` and
  `endgames_cdb95105.epd` (endgame-only gates, e.g. for TB or small-net work),
  `closedpos.epd`, `stalemates_200d30_v1.epd`, `transpositions_cdb95105.epd` (TT-heavy
  positions), `popularpos_lichess_v3.epd` (real-game openings for datagen),
  `Drawkiller_balanced_big.epd`.
- **Use:** targeted gates for targeted changes (an endgame-only SPRT for E1 or TB work needs far
  fewer games than a UHO gate to see an endgame effect), and opening diversity for datagen.
- **Effort:** none (download); **test:** compare the gate's Elo on UHO vs the targeted book.

### T2. Bayesian / gradient-free tuners for few parameters (Apache-2.0 / MIT)

- **chess-tuning-tools** <https://github.com/kiudee/chess-tuning-tools> - licence Apache-2.0
  (LICENSE file; GitHub shows NOASSERTION). Gaussian-process Bayesian optimisation driving
  game matches; fits 2-6 parameters with far fewer games than SPSA (e.g. time-management or
  small-net threshold constants).
- **Lakas** <https://github.com/fsmosca/Lakas> - MIT; tunes engine parameters with
  Facebook's **nevergrad** (MIT) optimisers. **optuna** (MIT) is the other generic choice.
- **Evidence:** no published Elo comparison vs SPSA found yet (**unproven**); value is in
  sample efficiency for low-dimensional problems where Forge's SPSA (R9) showed 0 of 16 params
  beyond 2 sigma.
- **Effort:** 1 day to wire one of them to fastchess with Forge's load governor.
- **How to test:** tune one 2-parameter problem with both tuners for the same game budget, then
  SPRT the two results against each other.

### T3. Permissive engines whose code may be read and reused (with the licence notice)

| Engine | Licence (GitHub API) | Note |
|---|---|---|
| Caissa <https://github.com/Witek902/Caissa> | MIT | strong C++ NNUE engine, pushed 2026-10-28 |
| Patricia <https://github.com/Adam-Kulju/Patricia> | MIT | C++, aggressive style |
| akimbo <https://github.com/jw1912/akimbo> | MIT | Rust, small and readable |

Not usable as code: Reckless, Monty, Viridithas (AGPL-3.0); Stockfish, Berserk, Obsidian,
Stormphrax, PlentyChess, Alexandria, Halogen, Ethereal, Weiss, Koivisto, Clover, RubiChess,
Quanticade, Smallbrain (GPL-3.0); Integral, Sirius, Grapheus, viriformat (**no licence**, so no
rights granted at all).

## 8. Tablebases

- Syzygy probing is already in Forge's r3/r5 line (see section 0). Permissive probers if the
  HalfKA line needs one: **Fathom** <https://github.com/jdart1/Fathom> (MIT) and **Pyrrhic**
  <https://github.com/AndyGrant/Pyrrhic> (MIT, LICENSE file; GitHub shows NOASSERTION). The
  generator `syzygy1/tb` is GPL-2.0 (run-only).
- Expected gain is small for an NNUE engine: Stockfish's wiki measured 6-man TB vs none at STC
  as about +15 Elo for SF6-SF11 but only **+2.7 Elo for SF15** (NNUE)
  (<https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html>, "Elo gain using
  syzygy").

## 9. GPL / AGPL: ideas only, or run as a separate tool (never copied into Forge)

| Tool | Licence | Why it is useful |
|---|---|---|
| `vondele/matetrack` <https://github.com/vondele/matetrack> | GPL-3.0 | mate-finding regression suite (positions with known mates); fits the R5D "forced mate reported as cp" bug class |
| `AndyGrant/OpenBench` <https://github.com/AndyGrant/OpenBench> | GPL-3.0 | distributed SPRT/SPSA server if more machines join the testing |
| `michiguel/Ordo` | GPL-3.0 | rating lists from many PGNs (cross-checks gate Elo) |
| `lucasart/c-chess-cli` | GPL-3.0 | alternative match runner (fastchess, MIT, is already used) |
| `official-stockfish/WDL_model` | GPL-3.0 | fitting a win-rate model to show WDL / normalise eval to "100 cp = 50% win" |
| `syzygy1/tb` | GPL-2.0 | Syzygy generator (the tables themselves are free to use) |

All Stockfish-derived ideas in sections 2-4 also belong here: the idea is used, the code is
written fresh.

## 11. Added from the deep-research workflow (partial results)

Taken from run `wf_d04a0303-91b` at 01:15 PC clock: 5 search agents done, 16 source fetches done,
claims extracted from primary sources (GitHub PRs/commits, Stockfish wiki, Lichess, Hugging Face).
The workflow's 3-vote adversarial check had **not** run yet, so these are single-reader claims;
licences marked "checked" were re-read by me from the GitHub API / LICENSE file.

### S2. Share the net weights between engine processes (gates and datagen run many copies)

- **Source:** Stockfish shared-memory weights, fishtest STC
  <https://tests.stockfishchess.org/tests/view/69074a49ea4b268f1fac236c> (2025-11); idea from
  Monty PR #62 "Implement mmap" <https://github.com/official-monty/Monty/pull/62> and fishtest
  issue #2077.
- **Licence:** Stockfish GPL-3.0, Monty AGPL-3.0 -> **[IDEAS ONLY]**. On Windows it is a named
  file mapping (`CreateFileMappingA`, Stockfish passes `SEC_LARGE_PAGES`) keyed by a hash of the
  weights + exe, written from Microsoft's documentation.
- **Evidence (workflow claim):** fixed 60,000-game STC on fishtest's mixed hardware
  +4.69 +- 1.4 Elo; with many concurrent 1-thread games NPS rose by up to 38%, measured
  +24.8 +- 1.9 Elo over 73,728 games; 8 threads per side only +5.2 +- 3.5 (18,432 games); a single
  process gains nothing (-0.16% on one NUMA speed test). Stockfish's version is big (24 files,
  +1,885 lines) because of NUMA and Linux paths; a Windows-only Forge version is much smaller.
- **Forge fit:** the PC runs gate engines at concurrency 4 plus self-play engines, all with the
  same 66 MiB HalfKA weights, on one 96 MB L3. One shared copy should raise NPS under that load,
  i.e. more gate games and more datagen positions per hour. It does not make a single engine
  stronger in a rating-list match.
- **Effort:** 1-2 days. **How to test:** bench identity; NPS of N concurrent copies with and
  without sharing (`--copies` A/A first, skill `forge-engine-verify`); datagen positions/hour
  beside the live pipeline (skill `forge-selfplay-datagen`).

### S3. Accumulator update kernel: tile several registers and drop the per-chunk add/sub branch

- **Forge now:** `halfka::apply()` (56cf4844 `src/nnue_halfka.cpp:446-480`) walks the L1 row one
  register at a time (32 int16 lanes on AVX-512, 16 on AVX2), widens int8 weights with
  `cvtepi8_epi16` and picks `add` or `sub` with `adds[c] ? ... : ...` inside the inner loop for
  every chunk.
- **Source:** Stockfish PR #4796 (mstembera, commit 95fe2b9, 2023-09-22)
  <https://github.com/official-stockfish/Stockfish/pull/4796>: one constant, the number of SIMD
  registers per accumulator tile on AVX-512, 32 -> 16.
- **Licence:** GPL-3.0 -> **[IDEAS ONLY]**.
- **Evidence (workflow claim):** +13.3% NPS on an i9-7980XE (avx512, 100 runs), +12.6% on an
  i7-11800H (vnni512, 50 runs); on AMD Zen 4 (Ryzen 7 Pro 7840U) +17.3% +- 0.4% with gcc 13 but
  only +4.0% +- 0.4% with clang 17. No Elo test (fishtest had too few AVX-512 workers); the cause
  (register spills) was never proven, so the best tile must be measured per compiler.
- **Forge fit:** try 4/8/16-register tiles and a split into "all adds, then all subs" loops (no
  branch), for both the AVX2 gate build (`x86-64-v3`) and the znver5 build.
- **Effort:** hours. **How to test:** exact (no functional change): bench node count identical,
  incremental == refresh check (skill `forge-halfka-parity-test`), NPS ABBA per tile size.

### T4. fastchess options Forge's gates do not use yet (fastchess is MIT, already installed)

From the workflow's read of the fastchess docs and of gate125's RESULT.md ("fastchess 1.8.2,
10+0.1 timemargin=1000 ... SPRT normalized [0,10] ... -recover"):
- `-check-mate-pvs`: checks that every reported mate PV has the announced length and ends in
  mate. Fits the R5D "forced mate reported as cp" bug class; costs nothing.
- `-tb PATHS -tbadjudicate BOTH|WIN_LOSS|DRAW` (`-tbpieces`, `-tbignore50`): Syzygy adjudication,
  needs only WDL files.
- `-resign movecount=3 score=600 -draw movenumber=34 movecount=8 score=20`: the Fishtest
  adjudication rules. gate125 played all 1,500 games to the end and 1,068 (71%) were draws, so
  draw/resign adjudication should cut gate wall time noticeably (not measured here).
- `-show-latency`, `-pgnout timeleft=true latency=true`: per-move clock and latency for
  time-management checks.
- `--compliance` and `-strict` (exit 1 on any warning; PR #1028, v1.8.2-alpha 2026-07-26): a CI
  UCI smoke test.
- **Effort:** minutes per option. **How to test:** for adjudication, an A/A gate with and without
  it on the same engines should give the same Elo within error, at fewer minutes per game.

### T5. chess-library (MIT, checked): fast C++ PGN/FEN parsing for data tools

- <https://github.com/Disservin/chess-library> (MIT, 193 stars, pushed 2026-10-27; single header
  `chess.hpp`, C++17, by the fastchess author). Workflow claims: streaming PGN parser 413 MB/s on
  a Lichess monthly dump (Ryzen 9 5950X), perft 355M nps; 24-byte packed board.
- **Use:** the converter for the Lichess CC0 games/evals (D1) and any PGN -> training-data tool,
  instead of python-chess (GPL-3.0). Caveat (workflow): the PGN reader does not validate moves and
  skips NAGs; check legality separately.

### T6. Arasan test suites (MIT, checked)

- <https://github.com/jdart1/arasan-chess> `tests/`: the LICENSE puts the "doc, prj, tests, and
  network directories" under the MIT text (GitHub shows NOASSERTION). Suites (workflow count):
  `arasan2026.epd` 200, `ecmgcp.epd` 183, `iq4.epd` 183, `wacnew.epd` 300, `pet.epd` 48,
  `eet.epd` 100, `bt2630.epd` 30, `lapuce2.epd` 35, with reference results in `tests/RESULTS`.
- **Caveat:** solve counts swing a lot between Arasan releases on the same hardware (26.0 -> 26.1:
  arasan2026 152 -> 110 of 200), so use them as a tactical smoke check next to D2, never instead
  of an SPRT.

### Details the workflow added to existing entries

- **S1 large pages:** PR #2656 author measured 13.8 -> 14.6 Mnps (+6%, 32 GB hash, depth 30);
  a Threadripper 3970X gained +8.9% (2 GB hash, 64 threads); one 1,000-game match at 60+1
  gave +12.3 +- 11.3 Elo; with small hashes on an 8-node Opteron it regressed. Windows
  fragments memory over time, so large pages can silently fail on a PC that is never rebooted:
  check that they were really granted (Sysinternals RAMMap) before trusting an NPS A/B. Print
  the status only after the `uci` handshake (Stockfish issue #3052 broke GUIs).
- **E2 neuron reordering:** the sparse kernel's gain depends on the instruction set and is
  smallest on AVX-512 (Xeon 8272CL: avx512 +0.6%, vnni512 +2.1%, vnni256 +7.2%, bmi2 +4.1%);
  the reordering was about 2 percentage points of the total. Expect most of the gain on the
  AVX2 gate build, little on znver5.
- **E4 bigger L1:** at a fixed 25k nodes per move the L1-1536 net was **+26.9 +- 1.6 Elo** over
  the L1-1024 net; it lost at STC only because it is slower. So a fixed-node match is the cheap
  first test for any wider Forge net, and the NPS cost decides the gate result.
- **D1 Lichess evals:** labels come from assorted in-browser Stockfish builds (depth 1 to 245,
  knodes up to ~593M, no engine version column); FENs have no move counters; `cp` is from
  **White's** point of view (convert to side-to-move for nnue-pytorch formats); mates are in a
  separate column. Filter on depth/knodes before using rows as targets.
- **D2 Lichess puzzles:** mined from 600M analysed games, re-checked by Stockfish NNUE at 40
  meganodes, every solution move is an "only move". Broadcast games (1,263,913) are CC BY-SA 4.0.
- **T2 tuners:** `fsmosca/Optuna-Game-Parameter-Tuner` (MIT, checked; TPE or CMA-ES, drives
  fastchess, 32 games per trial by default, trinomial scoring). The author's own comparisons are
  mixed: tuned results from -23.7 to +21.2 Elo at depth 6, and neither tuned set beat Deuterium's
  hand-tuned piece values. Stockfish once merged a constant tuned locally with nevergrad4sf
  (`vondele/nevergrad4sf`, GPL-3.0): +0.61 +- 0.35 Elo STC over 1,047,424 games and +0.82 +- 0.36
  LTC over 796,236 games. Verdict: real but tiny gains; not a priority.
- **Section 8 tablebases:** 6-man TB in RAM at STC: SF12 +7.2, SF13 +11.1, SF14 +7.3, SF15
  +2.7 Elo; Stockfish 17.1 with TBs on a fast M.2 SSD: +1.26 +- 1.46 Elo over 50,000 games (not
  significant). Pre-NNUE: 6-man about +20 over none, 5-man about +9, 4-man about 0.
- **Dropped:** ChessBench / `google-deepmind/searchless_chess` - code Apache-2.0 but the data is
  partly CC-BY-4.0 (not on the allowed list) and the README gives no evidence for alpha-beta
  engines.

## 10. Checked and dropped

- Block-sparse first dense layer: already in Forge (`block_affine()`), see section 0.
- Finny tables / accumulator refresh cache: in `fable-nnue-arch` (`nnue_v3`), so excluded by the
  "open branches" rule; note that the HalfKA line has none (Stockfish `49ef4c935a`, 2024-04-24).
- Syzygy, cuckoo upcoming-repetition, PEXT, VNNI, pairwise, node-effort time management,
  best-move stability: in Forge (section 0).
- NUMA / L3-domain thread pinning (Stockfish, ~4% NPS on multi-CCD CPUs per
  <https://anemato.de/blog/nuca>): only helps CPUs with several L3 domains. The PC's CPU is an
  AMD Ryzen 7 9850X3D (8 cores / 16 threads, one CCD, 96 MB L3; `Win32_Processor`, 2026-10-31),
  so there is nothing to gain.
- LEB128 net compression (Stockfish `a46087e`): smaller binary only, no speed or Elo.
- Stockfish data on Hugging Face, licence not on the allowed list:
  `official-stockfish/fishtest_pgns` (LGPL-3.0), `official-stockfish/master-binpacks` (ODbL),
  `official-stockfish/master-smallnet-binpacks` (no licence tag).
- Code with no licence at all (no rights granted): `linrock/nnue-data`, `Luecx/Grapheus`,
  `cosmobobak/viriformat`, `aronpetko/integral`, `mcthouacbb/Sirius`. GPL-3.0:
  `jnlt3/marlinflow` (trainer), `Disservin/binpack-rust`, `official-stockfish/WDL_model`.
- Evaluation grain of 16 + random +-1 (Stockfish `d212e663bb`, 2024: STC about +0.9, LTC about
  +2.4): not in Stockfish master's `evaluate.cpp` any more (2026-10-31), so it was apparently
  removed later; not recommended without finding out why.
