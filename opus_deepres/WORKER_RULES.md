# Rules for every research worker of this job (read fully before the first search)

You research one track for Forge, a C++ UCI chess engine, and write cards. You only research and write: no engine
edits, no builds, no engine runs, no training, no process changes, no posts or messages to anyone outside.

## Save as you go (the low-usage rule depends on this)
**Write each card file the moment its first source is read (fields not yet known say PENDING), and append one line
to `notes/T<nn>/sources.md` after every source read (url or repo@sha, licence tier, what it gave, card id or "no
card"). Nothing may exist only in your conversation.** The coordinator commits your folders every ~10 minutes and may
stop you at any moment; whatever is on disk is what survives.

## Where to write (all under `F:\odr\wt\opus_deepres\`)
- Temporary files (downloads, listings, helper scripts, PDF text): ONLY `F:\odr\work\T<nn>\` (create it). Not the
  session scratchpad, not C:, not D: (added 23:38 after three first-round workers used the scratchpad on C:).
- Only `cards/T<nn>/<id>.md` and `notes/T<nn>/*.md` of YOUR track. Licence checks go to `notes/T<nn>/licences.md`
  (one `tools/licence_at.py --row` line per repo). Never touch STATUS.md, FINAL_REPORT.md, RESUME.md, LICENCES.md,
  WORKER_RULES.md, other tracks' folders, the tools, or anything outside `F:\odr\`. Never write to D: or C:.
- Card format: `cards/TEMPLATE.md` (8 fields in that order, Status line, <= 60 lines). After the track's top 3 cards
  the rest are one-line cards (`ONE-LINE | idea | source link | licence | source Elo | Forge has it | gate route |
  Forge estimate UNPROVEN`). A card whose source gain is under 3 Elo at STC with no LTC is a one-liner. At most 6
  cards per track. Check every card with `python -I -B tools/card_lint.py cards/T<nn>/*.md` before you finish.

## Licences and reading (binding)
- MIT / BSD / Apache (Caissa, Altair, Patricia, bullet; check Fathom): source may be read (copy only with notice).
- GPL-3.0 (Stockfish, Berserk, Obsidian, PlentyChess, Stormphrax, Alexandria, Koivisto, Ethereal, Halogen, RubiChess,
  fishtest, nnue-pytorch), AGPL (Viridithas, Reckless), no licence (Integral): read ONLY README, docs, wiki,
  changelogs, commit titles, PR text and test logs - never a source file. Stockfish and nnue-pytorch source: skip
  entirely (their commit titles, PR text and test pages are fine).
- Record the LICENSE at the exact commit you read: `python -I -B tools/licence_at.py OWNER/REPO [SHA] --row`.
- Describe mechanisms in your own words; never paste, translate or paraphrase code; never propose another engine's
  tuned constants as Forge values (write your own start value and range). State the licence of every dataset/tool.

## Caps (per track)
- Stop after 2 sources in a row give no new card. At most 15 sources, at most 5 forum threads, deep-read at most 3
  engines. One web search per question before reading. Per engine: commit titles plus the test logs of the top
  gainers only (`tools/mine_commits.py OWNER/REPO --top 15`, then `--show SHA` for the few you cite), never whole
  histories. Never clone a repo. Fetch only a named file at a named commit (raw or API), at most ~300 lines per fetch.
- "Does Forge have it" = one grep of the lock source: `bash tools/forge_has.sh 'REGEX'` (+ one line in the card).

## Numbers
- No Elo claim for Forge. Quote the source's number with link, TC, book, games, LLR / bounds, engine. Label every
  Forge-side estimate **UNPROVEN**. Every card has a gate route: UHO SPRT [0,5] at STC, then LTC; node-identical
  speed changes = nps ABBA only. Anything under +1 Elo (or +1 % nps) expected is dropped.
- Crew decision (7-0 vote, received 2026-11-05 before 02:37): every search gate runs Threads=1; SPRT [0,5] in normalized Elo (not BayesElo), alpha = beta = 0.05, pentanomial, cap 3,000 games; a run that hits the cap without a decision is logged UNPROVEN / no decision (not H0, not a pass), and if its Elo is positive it gets exactly one extension.
- Board: read `D:/grok-pc-data/dwqww/WORKER_BOARD.md` first; claim your slot at your start with
  `python -I -B tools/board.py start S<n> "<worker>" "<task>"` and release it as your last step with
  `python -I -B tools/board.py done S<n> "<worker>" "<task>" "<result path>"` (three slots: never more than 3
  active workers). This board file is the only file outside F:/odr that a worker may write.
- Missing evidence is written as missing, never invented. If a number cannot be found, say so.

## Names
- No AI vendor or model-company names anywhere (files, cards, notes). The machine name grok-pc is fine. Local paths
  through the agent configuration folder are written with `<cfg>` for that folder name (e.g.
  `D:/grok-pc-data/dwqww/<cfg>/skills/forge-nnue-data/SKILL.md`), or name a skill by its name only. (The
  coordinator's git clean filter also does this for everything committed.)
- No licence or copyright headers in anything you write.
- Never type or run any name that starts with `train_res` followed by `id` (a crew supervisor adopts such
  processes); call it "the residual trainer".

## Forge facts you need
- Lock FD3A5190 = AL1 s198, source (read-only): `C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\src_al1s198_clean`
  (search: `src/search.cpp` 1,531 lines, `include/forge/search.hpp`; eval: hand-crafted eval `src/eval.cpp` PLUS a
  residual NNUE `src/nnue.cpp`: 768 piece-square inputs -> 256 hidden, int16 weights loaded as float32, float
  accumulators, SCReLU, one output; `include/forge/nnue.hpp`). Build: LTO+PGO, -march=znver5; gates use Threads=1.
- PC: AMD Ryzen 7 9850X3D (Zen 5, 8 cores / 16 threads, one CCD, 96 MB L3), RX 7900 XT GPU (ROCm/HIP), Windows.
- Tried gates (do not re-propose without a new angle): `notes/TRIED_GATES.md` (from the crew's FORGE_RESULTS.csv;
  regenerate with `python -I -B tools/tried_gates.py --grep REGEX`).
- Already done (drop, or add only what changes how it should be done): near-miss ports to the lock (69B1c, packa
  NonPawnCorr w50/w60, bundle 68, packc 28, EvalOnlyStore 49); speed: R12 bundle (+2.5-3.6 % nps), LargePages (kept),
  AccumTile and SharedWeights (lost), FTP1 L1 permutation, LTO+PGO lock build, find-nnz sparse L1, net-path PGO
  workload v2, weight alignment, TT prefetch at make_move, MovePicker hoist; Sf26Bundle bits 2/4/8 + local SPSA
  retune; razor (bit 1) alone; E3 eval post-processing fit (EvalMatScale, EvalOptimism, EvalRule50Damp gated);
  CorrSignedKey; CorrHistPlus, CorrExt; LmrTtCapAll, LmrCapVictim; QsEvasionSeeNonPv; tmfit (TmFitModel) and
  node-fraction TM; Syzygy prober port; bullet (MIT, HIP) configs + exporter for v2 features (output buckets, king
  buckets KB4/8/16/32, threats, pawn pairs), staged training, export parity; relabel pipeline (92,523-position pilot
  at 20k nodes); faster npt loader; net soups (Y8, U8, Z32, V16 packaged, UNPROVEN). Lambda decided (Lichess 1.0,
  self-play 0.7-0.9). UHO default gate book, 8moves_v3 second, never pooled. Gates Threads=1.
- 30-Oct research round (already reported, do not re-propose): eval post-processing, large pages, neuron reordering,
  accumulator tiling, fastchess adjudication options, shared weights, Lichess puzzles / eval DB, small second net,
  bigger L1, CC0 books, Bayesian tuners, thread voting, chess-library, Arasan suites.

## Round 2 (from 23:55; the owner asked for more improvements and more agents)
- Sub-track folders `cards/T04B/` ... `cards/T05D/` etc. (your prompt names yours). At most 4 cards per sub-track
  (top 2 full, the rest one-liners), at most 15 sources, at most 3 engines deep-read, same licence rules.
- Before writing a card, check the 34 existing cards (`ls cards/*/`, `notes/T04/TABLE.md`, `notes/T05/SPEED_LIST.md`,
  `notes/T02/TABLE.md`, `notes/T01/recipes.md`) and `notes/TRIED_GATES.md`: no duplicates. A better number for an
  existing card's idea goes into your notes as "evidence for <card id>", not into a new card.
- Gate rate for any cost estimate: 430-502 games/h measured for the crew's `*_vs_AL1*` gates (497 at Threads 2 /
  conc 4); one SPRT at [0,10] nElo cap 12k means ~6.6k games (~13 h). The v2 identical-eval control is -20.9 +- 18.5
  (post root fix), not -32.2.

## Hand-back (your final answer)
A short list: card id | title | status | source number with conditions | Forge estimate (UNPROVEN) | effort; then
dead ends (one line each), sources used (count), licence rows written, and anything left PENDING.
