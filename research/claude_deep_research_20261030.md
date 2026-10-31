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

## Candidate queue (not yet verified; each gets a full entry with source, licence, evidence, effort, test)

- Windows large pages for the TT (and NNUE weights) - speed.
- Sparse first-layer propagation (skip zero 4-byte input chunks, SF "find_nnz") - speed.
- Second small net for clearly won/lost positions (SF 16.1 style) - speed/Elo.
- Port Syzygy + cuckoo from the r3/r5 line to the HalfKA line - strength (no new code needed).
- Data: Lichess CC0 game and eval databases; licence of Leela-derived binpacks.
- Tools: permissive trainers other than bullet, Bayesian tuners, Fathom/Pyrrhic (MIT) probers.
