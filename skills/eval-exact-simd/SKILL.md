---
name: eval-exact-simd
description: Use when validating a floating-point NNUE SIMD port that must preserve evaluations and search nodes exactly.
---

# Eval-exact SIMD check

Freeze the accepted source, network and production executable before changing the
kernel. Use the user's build recipe and current pins; this guide grants no permission
to build, run matches, alter other jobs, or publish artifacts beyond the task.

An equal final integer evaluation can hide different intermediate floats. Map old
and new lane membership, index visitation, clamp operands, multiply/add rounding
points, reduction order and conversion explicitly. Replacing two independent
8-lane groups with one 16-lane group can preserve that contract; a horizontal
reduction, FMA, or integer requantization needs a separate proof.

For diagnostic builds, capture every output lane and the sum before conversion.
Compare float bits, not epsilon tolerances. Remove instrumentation from production
through a build guard. Check the optimized disassembly, including all FMA families.
Use unaligned wide loads unless the actual objects guarantee wide alignment.

Compare a separate unchanged-source reference with candidate OFF and ON. Exercise
fresh refresh, incremental updates, make/unmake, null moves, all special moves,
both perspectives, and long legal sequences. A one-ply sweep does not cover long
incremental state. Record actual coverage and first mismatch, rather than inferring
coverage from corpus size. Prove ON executes; matching OFF can also mean dead code.

Distinguish NNUE output, HCE, combined residual evaluation, and search integration.
An HCE-only API is not a final residual-evaluation oracle. Corpus search-score/node/
bestmove equality is useful production evidence but does not replace static float
bit checks. Production node pins, reproducible executable hashes, sanitizer proof,
and performance evidence remain separate gates.

This repository provides a worked diagnostic harness at
`../../astra_r9/tools/eval_exact.cpp`, the arithmetic mapping at
`../../astra_r9/ARITHMETIC.md`, and the independent review findings/fixes at
`../../astra_r9/REVIEW_LOG.md`. Adapt paths and architecture to the current task;
do not reuse its old pins, hashes or acceptance status. The harness's private Worker
incremental-PSQT path is covered by production checks, not by its static HCE oracle.

Only claim the exactness tested. Samples support the arithmetic proof; they are not
a proof for every possible input or network. Keep speed advisory and Elo unproven
unless the user has supplied the corresponding independent evidence.
