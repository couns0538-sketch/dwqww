# Claude deep research 2026-10-30: new ways to make Forge stronger or faster

Status: **WIP, partial** (appended in place; pushed about every 10 minutes).
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
NUMA code, `MultiPV`, `Chess960`, `UCI_ShowWDL`, a non-zero-chunk search for the sparse first
layer (`nnz`; the L1 loop at `src/nnue_halfka.cpp:222-241` still has to be read to confirm it is
dense). These are the open slots the research below targets.

Correction after reading the code: the HalfKA first dense layer already skips all-zero 4-byte
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
  raw net output, nothing else. A grep of all heads finds no `optimism`, no draw randomization
  (`nodes & 2`) and no 50-move damping in eval (the "scale" hits in `opus-r3-stack` /
  `opus-r5b-speed` are only the time manager's `falling_eval_scale`).
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

  Total in Stockfish: roughly +8 to +12 Elo. Forge's net, draw rate and eval scale differ, so
  each piece must be re-measured; the draw jitter mainly matters at long TC.
- **Forge fit:** all four live in `halfka_evaluate()` and the draw-return sites of
  `src/search.cpp`; keep the TT storing `raw_eval` as it does now and apply correction history
  after the scaling (Stockfish order). Constants need one SPSA pass afterwards (Forge's R9
  tuner can take them as new tunables).
- **Effort:** 1 day for all four behind one default-OFF option (`EvalPostV1`), plus tuning.
- **How to test:** OFF bench = lock pins; ON bench changes (expected); one SPRT per piece in the
  order of the table (material scaling first), STC [0, 2] then LTC [0.5, 2.5]; draw jitter
  needs a longer TC (Stockfish only saw it pass at 120+1.2).

## 3. Speed ideas

### S1. Windows large pages for the transposition table

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
- **Forge fit / caveat:** the account that runs gates needs the "Lock pages in memory" right
  (secpol.msc, then log off/on). Large pages are never paged out, so a 1 GB hash takes 1 GB
  away from the trainer and self-play for good; keep gate hashes small and keep the PC's
  free-RAM rule (6-8 GB). Fall back to normal allocation when the call fails and say so with
  an `info string`.
- **Effort:** 0.5 day.
- **How to test:** no functional change, so bench/perft identical to the pins; NPS ABBA at
  Hash 64 / 256 / 1024 MB, Threads 1 and 3 (skill `forge-engine-verify`); gate only if the A/B
  shows >= 1%.

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
- **Caveat:** these labels are Stockfish output. The CC0 licence allows any use, but some rating
  lists treat nets trained on another engine's evals as not original; decide this before
  training on them. Use (a) is safe either way.
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

## 10. Checked and dropped

- Block-sparse first dense layer: already in Forge (`block_affine()`), see section 0.
- Finny tables / accumulator refresh cache: in `fable-nnue-arch` (`nnue_v3`), so excluded by the
  "open branches" rule; note that the HalfKA line has none (Stockfish `49ef4c935a`, 2024-04-24).
- Syzygy, cuckoo upcoming-repetition, PEXT, VNNI, pairwise, node-effort time management,
  best-move stability: in Forge (section 0).
- NUMA / L3-domain thread pinning (Stockfish, ~4% NPS on multi-CCD CPUs per
  <https://anemato.de/blog/nuca>): only helps CPUs with several L3 domains; the PC's 16 logical
  CPUs point to one 8-core CCD, so no gain expected.
- LEB128 net compression (Stockfish `a46087e`): smaller binary only, no speed or Elo.
