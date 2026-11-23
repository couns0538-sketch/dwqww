# Forge 6.5 coordinated pipeline status

Status: INITIALIZED; no scheduled agent run or native test yet.

Pinned baseline: `forge6.5@d4651aeac344b9d838c63406abb95053cd968f9a`.
Shared coordination branch: `agents/forge65-7day-20261123`.
Repo documents: `agent_pipeline/PIPELINE.md`, `agent_pipeline/SOURCE_MANIFEST.md`.

## Baseline observations
- Original baseline branch unchanged; new branch contains only independent coordination documents.
- GitHub recursive tree had 88 blobs, including Windows executable, NNUE binary, legacy loop tree, main Forge65 source and build recipes.
- README contains prior bench/perft/strength claims; not reproduced in this task.
- Source inventory and representative full C++ core files/headers inspected via pinned GitHub connector; complete source audit and native validation reserved for scheduled roles. Do NOT describe this checkpoint as a full code review.

## Role ownership
- Coordinator at :00: STATUS, priority queue, conflict control, every-two-hour report.
- Researcher at :15: source-grounded one-proposal evidence and experiments.
- Investigator at :30: bugs, determinism, safety, test plans.
- Implementer/tester at :45: own experimental branch, real native tests, game evidence.

## Queue (unverified questions)
1. Build a reproducible Linux test setup for Forge 6.5 (existing CMake target may not set FORGE65 and NNUE v3 flags). Never run supplied build scripts until reviewed.
2. Establish exact source/NNUE/executable fingerprints, original bench pins/perft/uci and one-thread throughput at a fixed workload.
3. Investigate search correctness, state, concurrency and clocks; keep issues evidence-based.
4. Research one bounded search-speed or playing-strength proposal and independently compare against verified baseline.
5. Publish progress and raw PGNs/logs without overwriting earlier checkpoints.

## Run ledger
None yet. Read full previous cycle before introducing changes. No paid compute or external installation authorized.
