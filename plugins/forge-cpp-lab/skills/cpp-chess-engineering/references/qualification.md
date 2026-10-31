# Qualification and handoff

Follow the current project's accepted protocol. Build pins belong to a specific baseline/net/platform; historical Forge numbers are not a universal fixture. Capture current accepted revision and all uncommitted changes before selecting a candidate branch. Do not discard a newer accepted engine because an older report is easier to reproduce.

## Before changing code

Freeze source/net/binary hashes, compiler/version/flags, C++ standard, CPU/OS, options, hash/threads, position/opening-suite hashes and exact commands. Prefer new external build directories. Check disk/RAM/CPU budgets and other running workloads. Do not access or alter a production trainer/gate/queue remotely unless authorized. The plugin cannot provide continuous execution or scheduled reporting after the session ends.

## Gate sequence

1. Reproduce the actual defect; run the regression against base and candidate. Cheap checks precede expensive matches.
2. Compile Release and diagnostic configurations. Run applicable existing tests, perft, UCI/lifecycle and sanitizers; report precise known failures and startup limitations. Distinguish Linux, native Windows, Wine and standalone harness results.
3. Under an exact-behavior contract, compare pinned deterministic benches with all options OFF **on the candidate binary**, then each ON feature as required. Check scores/PVs/evaluation parity where the contract needs them. Show the option is active. A changed node count blocks an exact-speed claim until explained.
4. Profile/benchmark with the project's calibration, run order and resource limits; record raw times/NPS/counts, median ratios and variation. Keep speed separate from search quality.
5. For search/evaluation strength, preregister paired equal-wall-clock Fastchess SPRT: H0/H1, alpha/beta, Elo model, openings/seed, time control, concurrency, threads/hash, adjudication and bounded stop budget. Use supported runner flags from its installed help. A non-regression test is not proof of positive Elo. Tiny screens remain screens; interrupted runs stay incomplete. Keep faults, illegal moves and time forfeits in the record. Preserve every original PGN/log and the runner's actual decision; do not reconstruct missing games.
6. Review interactions before integrating. If the task authorizes correctness-only acceptance with inconclusive strength, label it precisely. Otherwise keep the candidate isolated. Publish only within existing authorization, verify remote SHA/artifact bytes, and preserve the accepted branch.

No external rating transfer: a limited Stockfish setting, self-play Elo, NPS, deeper search or lower training loss does not establish unrestricted Stockfish superiority or a FIDE rating.

## End-of-cycle record

Record ID/date; baseline/candidate SHAs; hypothesis; exact diff and IDEA_SOURCE; build/test commands; original exit/status/log paths and hashes; pins; correctness failures; native platform coverage; timing statistics; match W/D/L and complete pairs, actual SPRT/uncertainty; decision; open blocker; next action. Statuses are PASS/FAIL/UNVERIFIED or ACCEPT/REJECT/INCONCLUSIVE/BLOCKED with scope. Do not silently turn missing checks into PASS.

Use the bundled offline checker to detect malformed evidence records, changed artifact bytes and explicit node-pin mismatches. It cannot authenticate that a log is truthful, inspect test semantics, reproduce a command, verify sanitizer coverage or accept an SPRT. Even its PASS leaves `strength_claim=UNVERIFIED`. Native engine tests and independent review remain necessary.

Checkpoint code and evidence at the user's cadence; include failed approaches and unfinished work. Retained indexes/logs consume real disk. New output should be sealed without overwriting old evidence, and capacity checked before each shard. Newer plugin guidance is not permission to delete old data or bypass review.
