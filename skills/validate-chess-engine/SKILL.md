---
name: validate-chess-engine
description: Use when validating GrokChess, Forge or other UCI engines; investigating illegal moves, state or TT bugs; checking perft, UCI behavior or training-data conversion; comparing candidates with fastchess SPRT; interpreting Elo/Stockfish claims; or accepting search, evaluation, NNUE or speed changes.
---

# Validate Chess Engine Improvements

Return separate conclusions about correctness, speed, and playing strength. Choose the smallest evidence set that resolves the actual question, then complete the required gate. Keep original artifacts and make incomplete evidence explicit.

## Establish a reproducible comparison

Read the current source and task contract. Identify exact baseline/candidate source, build/runtime, network, options, fixtures, and hashes. Establish which changes are authorized and which checks already passed. Recover original results before repeating expensive work. A higher version number, a shared filename, or a prose claim does not identify the tested build.

For exact-speed work, use `optimize-grokchess-speed`. For source-guided development and GrokChess's project/training constraints, use `improve-grokchess`. Keep tests and clocks within the actual available CPU allocation.

## Reproduce and repair correctness

Read [correctness.md](references/correctness.md) for the affected subsystem. Capture a minimal FEN **and relevant history**, exact command/options, warm/cold state, and expected/actual behavior. Run the reproducer before editing, isolate the responsible mechanism, make a targeted repair, and rerun related regressions. Verify that the test exercises the original defect.

Perft covers move-tree counts, not evaluation, UCI responsiveness, search selectivity, or playing strength. Selective-search score differences are not automatically proof of an illegal bound. Do not disable all pruning or enforce universal warm/cold score equality to eliminate unexplained differences. Preserve existing move/SEE/promotion/rule-50 protections while diagnosing the specific interaction.

Run the relevant existing suite and report observed failures, including pre-existing ones. Expand tests only for remaining risk or a required gate. Record crashes, illegal moves, and time losses; never remove them from a match result to improve its score.

## Validate training-data conversions

For FPOS/FHCE, FEN sidecars, bulletformat, native label probes, or shard pipelines, read [training-data.md](references/training-data.md). Report format correctness, native search validity, trainer compatibility, throughput and playing strength separately. Use complete metadata and output accounting, retain original-state provenance, and remeasure storage before each shard.

## Test playing strength

1. Read [matches.md](references/matches.md), inspect the installed fastchess version/help, and recover the project's test policy. Use fastchess SPRT as the user's final strength acceptance gate. Fixed-game and fixed-node matches are useful screens; they do not become a retroactive SPRT.
2. Write the protocol before the match: exact builds/networks, balanced opening pairs with colors reversed, opening-suite hash/seed, clocks, threads/hash/affinity, adjudication, maximum budget, test purpose, SPRT hypotheses, alpha/beta, and Elo model. Use the intended equal wall-clock resources for the release decision. Distinguish an improvement test from a tolerated-loss non-regression test.
3. Preserve raw runner output, UCI logs as needed, PGNs, command/config, and stopping state. Inspect LLR and boundaries from the actual runner. Accept, reject, or leave inconclusive according to that predeclared protocol; budget exhaustion is not a pass. Match the claim to the hypotheses: a non-regression PASS does not by itself establish a positive Elo gain. Keep the maximum game count finite unless an explicitly authorized managed task owns the run.
4. Separate speed from strength: fewer nodes, more depth, better NPS, lower training loss, or wins at fixed nodes do not establish equal-time Elo improvement. Lower NPS can be acceptable if measured equal-time strength improves. Keep small demonstrated gains and promising inconclusive ideas with a revisit condition.
5. Recheck interactions when combining accepted changes. For a broad strength claim, confirm using fresh representative openings/time controls or a suitable opponent set after candidate selection; avoid repeatedly tuning to the reporting suite.

## Calibrate Stockfish claims

For a full-strength comparison, identify the actual official Stockfish version/build/network and query `uci`. Explicitly configure `UCI_LimitStrength=false`, maximum supported Skill Level (normally 20), `MultiPV=1`, and the intended resource/book/ponder/tablebase policy. Verify options were accepted. A limited opponent at `UCI_Elo=2000` does not establish superiority to unrestricted Stockfish or a FIDE rating. Do not convert self-play Elo into an external rating.

State precisely what a win rate or test proves under its conditions. A single win is not match superiority. A candidate-baseline SPRT is evidence about that pair and protocol; an unrestricted-Stockfish claim needs direct appropriate evidence.

## Report and preserve

Use [result-record.md](references/result-record.md). Report W/D/L, complete pair counts, games, time control, model, hypotheses, actual LLR/bounds/state, error/forfeit counts, evidence paths, and limitations. The installed provider's `scripts/check_match_counts.mjs` checks paired-count consistency only; it cannot verify an SPRT result or authenticate a log. That script could not be retrieved and is not included in this proposed bundle. Use an existing installed copy when available, or verify the constraints in [result-record.md](references/result-record.md).

Preserve tested revisions and all raw results in the authorized persistent project destination. Confirm the save succeeded. End with the accepted/rejected/inconclusive/blocked decision, the practical consequence, and the next useful action.

