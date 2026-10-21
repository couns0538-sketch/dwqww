---
name: validating-chess-strength
description: Use when evaluating chess-engine Elo or Stockfish claims, planning Fastchess paired matches or SPRT, encountering timeouts or incomplete pairs, or comparing fixed-node search quality with equal-clock strength.
---

# Validating chess strength

A match establishes evidence only for its frozen opponent, resource limit and stopping rule. Correctness, speed, fixed-node search quality and equal-clock playing strength are separate results.

## Freeze before play

Record source commits/diffs, original archive, network, compiler/flags, executable and runner SHA-256, runner version/source pin, settings, exact openings, seed, CPU allocation/affinity/cgroup and stopping rule. Preserve source-to-binary build provenance: a declared commit plus executable hash alone does not authenticate that relationship.

Choose the baseline for the question: the exact original archive measures the combined change; a reference containing shared clock fixes isolates a later search change. State which comparison is performed.

Preregister the A/A purpose and gate, using the same binary, resource policy, options and transport. For deterministic fixed-node A/A with unlimited clocks, require identical paired moves/results as well as normal complete color-swapped pairs. For timed operational A/A, use the frozen equal-clock settings: scheduling can change reached depth, moves and results, so require the preregistered normal-game, pairing, legality, fault and input-integrity checks. Different timed moves/results alone are not a harness fault without a preregistered, justified identity requirement. Neither mode establishes precise zero Elo; keep A/A separate from A/B. Do not retrospectively relax a frozen deterministic gate to rescue a failed attempt.

Use fresh unique opening positions, comparing their first four FEN fields. Exclude prior calibration/pilot/test selections. Set Threads=1, Hash equally, OwnBook=false and restart per game when isolating search. Freeze concurrency and settings before outcomes are visible.

Preregister en-passant representation handling: Fastchess may emit `-` for a non-actionable EPD target. The reference avoids this mismatch by selecting original corpus positions whose target is already `-`; it does not rewrite positions or erase legal en-passant rights. A failed opening audit stays failed; repair eligibility before a fresh calibration.

## Operational gates

Any timeout, crash, illegal move, warning, incomplete pair or changed input invalidates this strict acceptance protocol. Retain all attempted games, failed UCI exchanges and logs; do not discard faulty games, pool interrupted attempts or repeatedly restart until H1 appears. Preregister a fresh run after investigating failures.

Before launch, test readiness and acceptance parsers against byte-exact canonical output captured from the actual frozen producer and intended transport. Preserve capture provenance/hashes and distinguish original bytes from derived LF/CRLF cases. Synthetic GOOD fixtures must use the producer's real dialect. Check positive captures and malformed, duplicate, warning, stderr and nonzero-exit controls before freezing the harness.

Persist process observations before assertions: command/stdin, return code (or explicit unknown), stdout/stderr hashes and owned process-group observations. On failure or timeout retain distinct pre-verdict and post-cleanup observations, cleanup actions/errors and final return code/group state. A parser replay with an assumed exit code does not recover the original process status or rescue its failed experiment.

After any successful spawn, keep bounded cleanup/reaping of owned children or groups in an unconditional `finally` path independent of evidence hashing and status writes. Restore the caller's original affinity in an outer `finally`, even if cleanup or persistence fails. A hash/write exception invalidates the attempt: retain partial raw files and observable cleanup/errors wherever writable; keep unobserved exit, group and CPU facts explicitly unknown. Cleanup success, parser replay or a later passing run cannot rescue the original failure. Fault-inject both hashing and status-write failures before freezing the runner.

Require an explicit source/build evidence set before readiness processes: actual Git archive identity and complete source inventory, compiler/configuration/flags, core and executable hashes, original build commands/streams/status and exact named CTest passes. Missing evidence fails closed; optional file globs cannot establish completeness. Keep byte-equivalent historical validation labeled with its genuine source revision; build the actual frozen revision when the protocol requires it. Include every consumed proof and build-evidence file in the final rehash, rather than checking them only at startup.

Before adapting a proof consumer to another revision, record an explicit schema mapping: producer revision/hash, receipt path, exact field path/type, expected value and its evidentiary meaning. Read genuine producer output/source; revision19 names/counts are not revision20 facts. Keep profile attempt counts explicit. Missing required facts block the gate; never default absent attempts/failures to zero or fabricate aliases. Revalidate the adapter against retained receipts and missing/wrong-type controls using source-only checks before any engine execution. Preserve original receipts, failed checker/adapter versions and genuine revision/fixture labels; save corrected mappings and derived reports separately. An adapter correction does not change the original engine outcome, retry history or acceptance status.

Preserve executable permissions when copying native artifacts, and require executable access before probes. Inert artifact tests can verify mode preservation without running engines. Keep internal work deadlines below the outer job-step timeout to reserve bounded cleanup and evidence-finalization time; this headroom does not guarantee survival after infrastructure loss. Retain failure controls and actual process observations separately from later successful checks.

One successful traced game does not establish clock reliability. VM scheduling and engine time management require separate diagnosis; last reported search time omits unfinished work. Use actual available CPU allocation and stop owned competing workloads.

Pinned Fastchess `60d7a7a` sets `atomic::stop` at a native SPRT boundary. Other games can be interrupted, leaving a retained first game without its return game. Use **serial native SPRT** for this runner; fixed-size A/A may use concurrency 2. Do not trim an orphan to rescue acceptance.

## Reproducible fixed-node reference

From the repository root, use the [quality runner](../../../validation/clock-safety-9850x3d/run-quality-sprt.py):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 validation/clock-safety-9850x3d/run-quality-sprt.py --aa-only --out "$NEW_AA_DIR"
# Only after A/A passes; binary defaults require the prepared cloud environment:
PYTHONDONTWRITEBYTECODE=1 python3 validation/clock-safety-9850x3d/run-quality-sprt.py --out "$NEW_SPRT_DIR"
```

Inspect `--help` and recorded paths before launching. The reference uses 10,000 nodes/move, `tc=inf`, no move-cap/score adjudication, four A/A pairs, then paired logistic SPRT H0=0/H1=20 Elo, alpha=beta=.05, capped at 500 pairs/1,000 games. It periodically saves status; monitoring does not guarantee survival after session termination.

## Audit and report

Require every retained PGN game to belong to a normal, unique, color-swapped pair. Independently audit with `tools/match/pgn_stats.py`; match native pentanomial counts and frozen opening selection, and recheck input hashes. Preserve PGNs, native likelihood/acceptance, commands, statuses and failures.

Require exactly one explicit native acceptance for a decided run. Parse the **final** LLR token, including `nan`/`inf`, and require finiteness; never skip a non-finite final token and reuse an earlier finite value. Check played openings against the exact frozen selection prefix, not merely set membership.

| Outcome | Permitted conclusion |
|---|---|
| Native H1, finite likelihood, all audits pass | Evidence of gain under this protocol; H1 does not prove gain at least its design alternative. |
| Native H0 | Alternative not accepted; not proof of exact equality. |
| Positive interim estimate, cap or budget exhausted without boundary | Inconclusive; no accepted gain. |
| Fixed-node unlimited-clock H1 | Search quality at that node budget/opponent only; no equal-clock or Ryzen claim. |
| Wine runtime or limited Stockfish wins | Wine and specified limiter results only; native hardware/full-strength claims require separate tests. |

See [application scenarios and verification](scenarios.md). Broader claims need independent openings, longer controls and the actual target environment/opponent; full-strength Stockfish requires limiter off and documented resources.
