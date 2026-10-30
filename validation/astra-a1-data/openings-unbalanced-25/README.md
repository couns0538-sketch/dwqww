# Native unbalanced opening book, minimum absolute score 25 cp

This is a separate cohort from `../openings-native`, whose default minimum was zero. All earlier source/evidence/books are preserved. No engine or generator source behaviour changed.

One standard R8-format book contains 64 unique final board+STM positions, accepted from 338 attempts with seed 20261030, 1024 fixed nodes, Hash 1 MB and 6–16 random early plies. It ran on CPU 0 at nice 19. Every selected position, including the initial one, was checked against ±150 cp. Final positions are nonterminal and not in check, with absolute scores 25–148 cp (mean 67.578125), split 32 White and 32 Black advantages. Original commands, hashes, raw probe requests/responses and exits are retained.

Fresh native replay passed: 562 legal plies and 626 fresh score/depth/node comparisons, zero mismatches, every intermediate trajectory covered, no final-board duplicates. The independent audit reused the same Forge probe implementation, not an independent chess library. Its audit took 1.155395 CPU seconds. Original native executable SHA256: ad2fa25e384d71fc30bf5c22108da0336675d93a21fd9b11604964acb771c498.

Generation took 29.407022 CPU seconds (54.040994 wall); the optional second generation and optional 16-position 960-style cohort were not run because their combined generation budget would exceed 30 CPU seconds. Deterministic second-run equality for this min-25 cohort is UNVERIFIED; the earlier min-zero control has its own verified two-run comparison. The generation supervisor's pending optional audit plan was narrowed before execution; audit receipts list the actual scope.

`standard-one/SUCCESS.json` and its manifest are the output seal authority; `generation.json` deliberately retains its earlier generation-stage status. This folder's SHA256SUMS.txt covers every copied evidence file except itself. Runtime timing/log files are not claimed deterministic. All files were copied from /tmp/astra-a1-openings-unbalanced-25; the originals remain there. To rerun, adapt saved scripts to NEW output directories; never overwrite this evidence.

R8 Windows execution is UNVERIFIED. Standard book syntax matches the exact R8 source contract; no driver was launched. No speed, training-quality or Elo claim.

IDEA_SOURCE: user Astra A1 bounded-unbalanced opening request; this repository's original generator and native probe API.
