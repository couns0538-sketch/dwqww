# Reproducible fastchess testing

## Contents

- Separate the experiments
- Declare the protocol
- Construct commands from the installed tool
- Read statistical evidence correctly
- Compare with unrestricted Stockfish

Reviewed against official sources on 2026-10-19. Commands/options can change. Read the installed fastchess `-version`/`-help` and the [upstream manual](https://github.com/Disservin/fastchess/blob/master/man.md) before generating the actual command.

## Separate the experiments

| Experiment | Useful conclusion | Limitation |
| --- | --- | --- |
| Exact-output timed benchmark | Execution speed on the checked workload | Not Elo or universal correctness |
| Fixed-node/depth games | A search/evaluation diagnostic at that effort | Does not include runtime cost fairly |
| Small fixed-game screen | Whether a candidate merits more resources | Wide uncertainty; not an SPRT decision |
| Predeclared fastchess SPRT at equal time | Decision under its specified hypotheses/model | Not a universal rating or proof versus a different opponent |
| Fresh confirmation suite/opponents | Checks selection/interaction/generalization risk | Still scoped to tested conditions |

The official [Fishtest test workflow](https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html) separates speedups and functional changes and notes that node-budget tests do not replace real-clock tests. Adopt that distinction while retaining this project's acceptance rules instead of blindly copying Stockfish's numerical policy.

## Declare the protocol

Record before starting:

- Exact baseline/candidate source/build/runtime/network identities and complete UCI options.
- Runner version, command argv, working directories, and finite resource/game budget.
- Opening suite/hash/seed and paired color reversal. Use the same opening for both members of each pair. Preserve pair identifiers.
- Intended time control and equal assigned resources, including match concurrency, engine threads, hash, affinity, and priority. Include runtime overhead in the relevant clock conditions.
- Book, ponder, tablebase, resignation/draw/maxmove, and timeout policies. Avoid aggressive score adjudication before checking the engines' score scales. Preserve decisive endgame evidence rather than hiding it through early draws.
- Test purpose (positive improvement or tolerated-loss non-regression), SPRT elo0/elo1, alpha/beta, named Elo model, boundaries, and stop/resume policy. Recover the existing policy or choose a justified bounded protocol. Do not set thresholds after viewing results.

Do not oversubscribe benchmark cores with parallel agents or training. With pondering off, engines normally alternate search: budget roughly concurrency times the maximum active search threads per engine, plus measured runner/runtime overhead. Budget memory for both resident engines, including both Hash allocations, Node heaps, networks, and other state. If pondering or another mode permits simultaneous search by both engines, count both active search budgets. On the user's Windows machine retain established CPU reservations; do not repurpose CPUs 0-11 reserved for matches for data work.

## Construct commands from the installed tool

The current upstream manual documents these switches. Verify them in the installed version and build the actual argv using observed engine paths:

| Purpose | Switch family |
| --- | --- |
| Node engine | `-engine cmd=NODE_EXECUTABLE args=UCI_SCRIPT dir=ENGINE_DIRECTORY proto=uci name=IDENTITY` |
| Shared clock/options | `-each tc=SECONDS+INCREMENT` plus only supported `option.NAME=VALUE` |
| Complete paired rounds | `-games 2` or `-repeat`, with a finite `-rounds`; do not add `-noswap` |
| Openings and reproducibility | `-openings file=PATH format=epd order=random`, `-srand SEED` |
| Statistical protocol | `-sprt elo0=... elo1=... alpha=... beta=... model=normalized|logistic|bayesian` |
| Detailed games | `-pgnout file=PATH nodes=true nps=true` and optional supported fields |
| Pair statistics | `-report penta=true` |
| Engine protocol logs | `-log file=PATH level=trace engine=true` where the installed version supports it |

Also capture original stdout/stderr to a dedicated runner log; a logger file and match statistics output need not contain the same information. Query `uci` and verify configured options. For paths with spaces, use a structured argument list or correct PowerShell quoting; do not concatenate an unquoted shell command. Run a tiny startup/protocol check before spending the match budget.

Define tested source/net copies so edits cannot change a running candidate. On resume, use that runner version's supported state recovery and check hashes/config/pair counts first. Do not change bounds or merge unpaired statistics from incompatible runs. Keep original partial data if the run is interrupted.

## Read statistical evidence correctly

[Fishtest mathematics](https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html) describes five paired-game outcomes and generalized SPRT with named Elo models. Preserve the pair counts rather than treating correlated color-reversed games as independent Bernoulli trials. Normalized and logistic Elo numbers are not interchangeable.

Use the actual runner's recorded LLR, boundaries, state, and model. An informal success percentage, positive Elo estimate, LOS value, or a sentence saying PASS cannot substitute for those artifacts. If a predeclared limit is reached before a boundary, report **inconclusive**. An SPRT failure under practical hypotheses does not necessarily prove the true gain is exactly zero. A PASS under negative-Elo non-regression hypotheses supports only that protocol's tolerated-loss claim; require an improvement-oriented protocol before calling a candidate stronger. This does not impose an arbitrary minimum useful gain.

Keep descriptive score `(wins + draws/2)/games` separate from any interval or relative Elo estimator. Do not invent uncertainty from the game count alone, round away losses, or convert a limited-opponent score into FIDE Elo. Account for candidate selection: a promising winner from many exploratory changes needs the project's fresh confirmation gate.

A fastchess crash/time loss/illegal move remains part of the evidence and must be reported separately even if recovery lets the run continue. Preserve completed pairs and partial games; do not silently drop inconvenient outcomes.

## Compare with unrestricted Stockfish

Use the [official UCI manual](https://official-stockfish.github.io/docs/stockfish-wiki/UCI-Protocol-and-Stockfish-Commands.html) and the actual binary's `uci` response. Record `UCI_LimitStrength=false`, maximum Skill Level (normally 20), `MultiPV=1`, Threads, Hash, correct network, ponder/book/tablebase choices, and clocks. Ensure options were accepted and the engine initialized successfully.

Version-specific strength limiter calibrations are not a universal rating scale. Be explicit if the opponent was limited, old, constrained to unusual nodes, or configured with multiple PVs. A direct result can establish performance against that exact setup; broader claims need appropriate additional evidence.

