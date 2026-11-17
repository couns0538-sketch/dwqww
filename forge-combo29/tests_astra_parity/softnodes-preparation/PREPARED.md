# Paired UCI sanitizer self-play with soft-node labels

Prepared for Fable answer 0012 at shared commit 7188f6b5f8ecc0ba88d4ec1997aaf2dd1161a82d. No engine was run during preparation. Root must complete the source gates before the final-tree workload. The absolute Job A deadline stays **2026-11-15 02:19:40 UTC**.

The current harness is softnodes_play_v3; DRIVER-PINS-v3.txt pins its source, headers, frozen Board/bitboard objects and executable. The harness is unsanitized and launches the separately instrumented final engine through UCI. Thus the real engine process, including UCI and search helpers, receives ASAN/UBSAN or TSan. Legal-move and game-terminal decisions use the frozen baseline Board implementation; no speed-branch test or engine change was imported into the oracle.

The copied uci_process.hpp is byte-identical to the timing-only transport supplied by the equality recorder, SHA256 606bd7cd54e94acba10da32bacc9c2620b7e5d8882b360e2492294ac197d40d2. Its measured quit-to-exit interval begins immediately before writing quit and ends at successful waitpid observation. Unavailable measurements are JSON null. The harness uses the existing 250 ms total shutdown budget and records actual status, signals, timing and budget. It does not replace original unmeasured events with inferred times.

## Workload and checks

One warm engine process serves a batch. Each pair plays one usual-limit game and one go softnodes 2500 game, from the same eight-ply seeded random opening. Which limit goes first alternates by pair index. ucinewgame is sent between games, never between moves. Normal termination is mate, stalemate, repetition, 50-move rule, insufficient material or the 300-ply cap. An opening that terminates before eight plies counts as a terminal game and is explicitly counted; it is not an engine fault.

The 180-second target is checked only between complete pairs. Accepted counters are snapshots taken after each completed pair, guaranteeing equal usual/soft game counts. Observed counters separately retain searches and completed games from an interrupted or faulty pair. Internal searches have a 15-second response limit and the batch has a 420-second hard deadline; the external recorder bounds the command at 440 seconds with a two-second kill allowance. A batch with no completed pair or no searches under either limit provides no accepted coverage.

Every search logs its seed, pair, order, thread count, ply, FEN, full move-history command, limit command and complete UCI transcript. A readiness barrier after bestmove exposes queued late/duplicate labels. Soft searches enforce all requested properties:

- Exactly one well-formed softnodes-X line before bestmove.
- Bestmove equals the first PV move from the last exact-score info line; bounded lines cannot replace it.
- That same line has at least 2,500 nodes, a mate score, or X at least 10,000.
- Decimal node counts reject negatives and overflow. Items 3/4 cause an immediate stop before any further search or move.

Ordinary games do not inherit the soft-only exact-PV or node-threshold requirements. Their last available score line, including a bound, supplies the score-range check. If a legal early abort emits no score, the harness records usual_score_not_observed with label_fault=false, keeps the transcript and reports that score validation could not be performed. It does not call this a soft-label fault.

Score-range and independent legal-move checks remain active. Whole-process diagnostics are scanned even when a label failure is the primary reason, including startup, game reset, partial search and shutdown. Soft-label lines outside checked search slices are retained and flagged. Raw logs remain authoritative for listing every sanitizer report and distinct TSan source-line pair.

## Build prerequisite and commands

Build final instrumented engines using the earlier sanitizer preparation commands, with compile guard FORGE_MATE_ALPHA_GUARD=1, x86-64-v4, Release, and the relevant sanitizer flags:

    /workspace/work/parity-run/builds/final-asan/forge
    /workspace/work/parity-run/builds/final-tsan/forge

No linked self-play driver rebuild is needed for this UCI workload. Root freezes the final source commit and starts one batch at a time:

    node /workspace/work/parity-softnodes-preparation/control.mjs declare FINAL_SOURCE_COMMIT --freeze-authorized
    node /workspace/work/parity-softnodes-preparation/control.mjs run 0 --execute-authorized
    node /workspace/work/parity-softnodes-preparation/audit.mjs 0

Replace FINAL_SOURCE_COMMIT with the reviewed 40-character source commit. Declaration compares every current engine source/header/CMake byte to that commit, checks both sanitizer/guard build flags, and pins binaries, objects, oracle, harness, plan and tools. It never changes Git or root state. The declaration and each run directory are immutable.

Use indices 0 through 11 from plan.txt. Eight ASAN/UBSAN groups cover Threads 1/2 × usual nodes 2000/20000 × both options off/on. Four TSan groups cover Threads 2/4 × usual depth 9 × both options off/on. Every group includes equal soft-node games within the same batch; it does not add another twelve batches. Enabled options are HindsightDepth and MateAlphaGuard together. Other options remain default, Threads/Hash/OwnBook are explicitly configured, and the transcript records their commands.

Seeds are 202611155001 through 202611155012. Each launch checks 475 seconds remain before the absolute deadline. The twelve targets account for 36 minutes plus pair completion, build and audit overhead; actual coverage depends on remaining time. A timeout/partial attempt is retained; a retry needs a new explicit declaration and label, with the original unchanged.

## Evidence, accounting and faults

Raw output and exact command metadata go under /workspace/work/parity-run/softnodes-batches/LABEL/, not the root logs directory. This avoids its 16 MiB copy guard; transcripts can be large. Root should use its immutable text chunk packager, publish only approved text evidence under tests_astra_parity, save audit stdout, update state/report, and checkpoint. Do not commit executables or live scripts; inert .mjs.txt copies are supplied.

The read-only auditor checks command hashes/options, game/pair/search counts, soft-X sums and cap counts, all raw diagnostics, timing and pair snapshots. It scans diagnostics before deciding whether a command completed, so a label fault or killed run does not erase sanitizer findings. Its complete field describes a finalized record; passed additionally requires actual paired coverage and zero findings. It reports accepted and observed partial-pair counts separately; root must not double count them.

For mean X, add soft_x_sum numerators and soft_x_count denominators across batches, then divide once. Report soft_hard_cap_reached separately. Quit timing includes observed/unavailable counts, maximum, and count above 100 ms. Any item 3/4 failure outranks remaining Job A work: preserve the position and full raw record and send the finding before another engine run.

Parser tests and synthetic auditor fixtures are preparation checks only. They are not native engine games, sanitizer runs or evidence that the final tree passes. Earlier preparatory source/build versions and concrete peer-review findings remain retained.

## Verification actually run

The final v3 harness compiled successfully with the frozen baseline Board objects. All 18 synthetic parser cases passed, including ordinary-bound-score acceptance and distinct missing-score classification. Four synthetic auditor fixtures passed: complete paired workload, concurrent label/sanitizer finding, timed-out sanitizer output, and zero coverage. Both current JavaScript helpers passed syntax checks. Earlier preparation builds and fixtures remain retained. No real engine was launched; no final-tree sanitizer game is claimed.
