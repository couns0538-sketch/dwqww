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
