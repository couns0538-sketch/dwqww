# Forge idea report from 50 agents

Ideas only. This folder does not change Forge search, evaluation, networks, or weights. Commit messages on `fable/50-agent-engine-ideas` and `astra/50-agent-engine-ideas` are reports for Fable and Astra.

Updated 2026-11-14T11:47Z. The run continues until 12:34 UTC. Placement paths below are from the later tree on `origin/astra-r14-20261103`. `main` does not check that tree out. See [forge-fit.md](forge-fit.md).

## How to read

- [BREAKTHROUGHS.md](BREAKTHROUGHS.md) — ideas flagged as a possible large strength gain. Six so far.
- [forge-fit.md](forge-fit.md) — where each kind of idea sits in the later Forge tree. Read-only. Nothing was changed.
- [IDEAS.md](IDEAS.md) — deduped catalog. If two departments described the same mechanism, it is written once and both sources are named.
- One file per engine, below. Pending departments are listed and left empty.

## Engines

- [stockfish-gaps.md](stockfish-gaps.md) — all seven departments are in. Short time controls produced B3.
- [leela-chess-zero.md](leela-chess-zero.md) — all seven departments are in. Policy ordering and self-play value produced B1 and B2. The WDL report tightens V1 rather than adding a second head.
- [komodo-dragon.md](komodo-dragon.md) — all seven departments are in.
- [berserk.md](berserk.md) — net structure and eval scaling are in. Still waiting: pruning, short-time strength, data generation, reductions, move ordering.
- [koivisto.md](koivisto.md) — training pipeline (B6) and leftover classical eval are in. Still waiting: null-move, endgame eval, threading, history, singular extensions.
- [ethereal.md](ethereal.md) — search structure, pawns, mobility (B5), passed pawns, and tuning are in. Still waiting: king safety and time controls.
- [rubichess.md](rubichess.md) — incremental updates, probcut, and tapering (B4) are in. Still waiting: net integration, late-move reductions, aspiration windows, thread scaling.
