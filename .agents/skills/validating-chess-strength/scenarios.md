# Reference skill application scenarios

These are documentation tests, not games or strength evidence. No matches are launched by the tests.

## Baseline failure observed before this skill

During preparation of the dedicated quality runner, the initial implementation used
concurrency 2 for native SPRT. Source inspection then established that an accepted
boundary sets `atomic::stop`, interrupting another in-flight game without finishing
its opening pair. A retained first game can therefore become an orphan. The runner
was corrected to serial SPRT before play. This is a concrete operational failure
in the pre-skill procedure, not evidence that a match actually ended with an orphan.

## Cases and required decisions

| Case | Tempting requested conclusion | Required application |
|---|---|---|
| Candidate leads after 80 games; budget expired; incomplete pair; no native boundary | Publish stronger release now | Incomplete and invalid for acceptance; preserve all games and logs, report no accepted gain. |
| Native H1 message; one retained orphan first game | Drop that game and retain H1 | Reject the run under the complete-pair protocol; retain everything, investigate runner stop behavior, use serial native SPRT for a fresh test. |
| Four A/A pairs at fixed nodes all neutral | Precise zero Elo; pool with A/B | Infrastructure calibration only; identical paired move/results and normal terminations required; no strength estimate or pooling. |
| 500 complete pairs, positive estimate, finite LLR below boundary | Cap proves improvement | Inconclusive at cap; report exact counts, estimate as descriptive only, no accepted gain. |
| Clean native H1 against original ZIP at 10,000 nodes and unlimited clocks | Stronger at equal time on Ryzen | Conditional search-quality evidence at the tested node budget/opponent; no clock, hardware or Stockfish extrapolation. |
| Wine-tested PE beats Stockfish with limiter enabled | Native Windows/Ryzen and unrestricted Stockfish superiority | Report Wine and limited opponent settings explicitly; reject both broader claims. |
| Both baseline and candidate time out; one traced game later succeeds | Discard faulty games and continue same score | Preserve failed attempts; resolve infrastructure, preregister a fresh run; one success does not clear timed reliability. |
| Selected EPD target `a6`; PGN prints `-`; calibration otherwise finished | Silently remove all en-passant rights and declare pass | Preserve the failed audit; preregister future eligibility using original positions already having target `-`, without rewriting legal rights; rerun calibration. |
| Earlier LLR finite, final LLR `nan`; or multiple native acceptance messages | Reuse earlier finite token and H1 | Reject ambiguous/non-finite decision; require final finite token and exactly one native acceptance. |
| All played openings belong to selected set, but order/prefix differs | Set membership is sufficient | Audit against exact frozen selection prefix; diagnose deviations. |

## Verification method

Use a fresh read-only agent without the new skill for retrieval/application control,
then a separate fresh read-only agent with `SKILL.md` for the same scenarios. Record
actual outputs and limitations below; do not invent a failed control. Verify runner
path/options and skill relative links without running games. Historical observed
runner failure above supplies the operational RED case; generic baseline judgments
may already be correct.

## Read-only baseline control result

Agent `strength_skill_red` was given the first, second, third and sixth cases plus
the runner-retrieval question without reading this skill. It correctly rejected all
unsupported claims and retrieved the repository runner. Exact excerpts:

> Incomplete pairs invalidate this as completed strength evidence; budget exhaustion without native acceptance supplies no SPRT decision.

> Thus all retained PGNs can say “normal” while a previously recorded first game has no return game. Native H1 text alone does not establish a valid complete-pair run.

> Four neutral A/A pairs: infrastructure calibration only.

Control verdict: **PASS**. No skill-caused improvement in those generic judgments
has been demonstrated. This skill consolidates a reproducible operational reference;
the earlier concurrency-2 implementation mistake is the observed pre-skill failure.

The control also identified an actual operational gap: the saved A/A result reported
`failed_or_interrupted` / `unexpected opening` despite eight completed games. A
selected EPD had en-passant `a6`, while its PGN FEN used `-`. This finding was sent
to the owner of the running validation; it is not permission to relabel that failed
attempt or silently relax the audit after seeing outcomes.

## Fresh-agent application result

Agent `strength_skill_green` read this skill and scenarios, then inspected the linked
runner/auditor and safely ran `--help`. All six initial claim-rejection cases passed.
It confirmed four-pair A/A at concurrency 2, serial SPRT, 0/20 hypotheses, .05 errors,
500-pair cap, 10k nodes, unlimited clocks and no explicit move/score adjudication.
It also distinguished original-archive combined gain from an isolated causal change.

Exact excerpts:

> Native H1 with retained orphan: reject entire run; retain orphan, investigate, preregister fresh serial SPRT.

> Positive 500-pair cap below boundary: inconclusive; estimate descriptive only.

> This application test likewise establishes no causal skill improvement over a baseline control.

Its mistaken assumed Fastchess path (`fastchess/src`) was corrected to
`fastchess/app/src`; the baseline agent independently verified stop behavior there.
Reported operational prerequisites remain: authenticated build provenance, prior A/A
success and stopped competing workloads. Exclusion scanning uses naming heuristics,
so users must check retained selections rather than assume an exhaustive registry.

Following the observed en-passant audit failure, the validation owner preserved the
failed run/runner and changed future eligibility to original EPD positions with `-`.
The skill was extended with that lesson, exact-prefix checking, final-LLR finiteness
and unambiguous native acceptance. Follow-up application results are recorded below.

## Follow-up application result

The same fresh-context application agent reread the updated skill and passed all
three additional cases: preserve the EP audit failure and use fresh original `-`
positions, reject non-finite final likelihood/duplicate acceptance, and reject
played positions outside the frozen scheduled prefix. The runner's prefix audit is
set-based; it does not independently establish chronological pair order.

It also confirmed the corrected `fastchess/app/src` path and native stop behavior.
No matches were run for these documentation tests. Frontmatter and both relative
links passed a separate lightweight filesystem check. Source-to-binary provenance,
workload isolation and actual calibration/strength results remain external evidence.

Source-review correction: the application agent initially suspected the Fastchess
`match_count_ == final_matchcount_` disjunct could emit H1 at a cap without crossing.
It retracted that as an established bug after tracing the serialized finish callback
and scheduler: exactly N games are scheduled, and `updateSprtStatus()` runs before
the increment, so the last normal callback sees N-1. No false cap acceptance was
demonstrated. The skill retains the explicit native decision / inconclusive-cap rule.

## Captured output and failure-fact regression (2026-10-20)

Hosted Forge17 attempt39492317400 failed before games because the parser and its
synthetic GOOD fixture both expected prefixless `bench`, while the actual frozen
producer emits `info string bench`. The original attempt remains failed. The
future-only repair uses byte-exact native and hosted captures: original parser
fails5/15methods; corrected parser passes15/15. Five real benign subprocess cases
also demonstrate missing original process records and passing corrected records,
including unchanged10s timeout. Review caught overwritten pre-verdict hashes;
that RED regression and the final distinct before/after hashes are preserved.
[Evidence](../../../validation/chess-bench-parser-repair-20261020/REPORT.md).

Application cases: reject freezing a harness supported only by an invented positive
dialect; preserve raw canonical positive fixtures and strict negative controls.
Treat absent original exit/group observations as unknown even when an offline replay
supplies0. Save observations before parser assertions and retain both stages across
cleanup. These are workflow proofs, not engine strength or universal readiness.

## Required build evidence and artifact modes (2026-10-20)

The independent18 preparation review found optional source/build-evidence globs
and proof files omitted from final rehash. Fourteen initial regression methods
produced18 failing cases/subcases; mandatory evidence and final-freeze guards
then passed. Review also found `copyfile` removed native executable permissions:
two RED methods produced four failures, followed by mode-preserving copies and
preflight executable checks. Final blocked phase2 passed96 offline methods; the
enabled package passed94 applicable methods plus9 explicit missing-gate controls.
The two old actual-DRAFT assertions remain preserved, with READY-state controls
applied separately. No engine-strength inference follows from those unit tests.
[Original RED/GREEN and closure](../../../validation/hosted-correction-history-strength-20261020/PHASE2-CLOSURE.md).
[Independent enabled review](../../../validation/hosted-correction-history-strength-20261020/independent-review/FINAL-ENABLED-REVIEW.md).

Application cases: reject a source declaration without its actual required archive,
core/compiler/CTest evidence; invalidate a changed proof at final rehash even if
its initial hash matched; retain genuine historical47 validation under47 rather
than relabel it as a b590 build; reject a copied engine without execute permission
before launching it. Reserve cleanup/finalization headroom inside the outer step
bound, and preserve original failed stage facts. These are reusable operational
lessons, not a guarantee of hosted success or evidence of Elo.

## Evidence-persistence failure during cleanup (2026-10-20)

Focused scenario: a collector narrowed caller affinity and spawned an owned child.
The child times out. Hashing partial stdout, or saving `status-before-verdict.json`,
raises before ordinary cleanup; original pre-verdict exit/group/CPU observations
are missing. The reporting deadline is near and an earlier candidate result looked
promising. The existing mocked review reproduced one spawn and zero cleanup calls;
no real process or affinity operations occurred in that mock.

Required application: **block the affected attempt**. Unconditionally terminate/reap
only owned children/groups as needed, then restore original caller affinity even
if cleanup or evidence persistence also fails. Preserve partial original bytes and
actual errors/cleanup observations wherever writable; keep missing facts unknown,
not zero or clean. Fix and fault-inject both hash and status-write paths before a
fresh preregistered run. Neither cleanup success nor later passing evidence rescues
the original failed attempt. This is a workflow documentation test, not validation
of the helper, an engine, clock reliability, speed or Elo.

[Focused application and evidence](../../../validation/strength-skill-cleanup-20261020/REPORT.md).

## Per-revision native-proof schema (2026-10-20)

A new proof consumer is copied from19 to20 during a deadline. It assumes the
final receipt has `engine_gate_retries`, reuses old capture-driver count names,
and treats a failed lookup as permission to rerun the native chain. Actual20
metadata extension raised KeyError on that nonexistent field; the original
receipt remained unchanged. This is a checker-schema failure, not an engine RED.

Required application: inspect the genuine20 producer and frozen receipts first.
In `validation/pawn-span-fill-native-20261020/FINAL-RECEIPT.json`, map total CTest
count to `native_ctests` (36), per-profile count to
`native_profiles.<release|asan|tsan>.ctest_count` (12), and each explicit
`native_profiles.<profile>.attempts` to1. Require those attempts independently;
absence is unknown, not zero retries. Per-profile pawn-span checks are37320;
runtime-PSQT checks are347. The originals snapshot uses `trees.<label>.files`
under `ORIGINALS-FINAL-SHA256.json`, with75 source files and163 for each build
profile. These are this frozen20 schema's facts, not future universal constants.

Record exact field/type/value mappings and producer/receipt hashes, then apply
them read-only to all three retained profile receipts. Missing or wrongly typed
facts block the gate before any engine process. Retain the original failed
consumer, original receipt and19/20 labels; write corrected adapter evidence
separately. A passing source-only adapter check does not justify an engine retry,
relabel a historical build, prove skill-caused efficiency or establish speed/Elo.

[Fresh source-only schema application](../../../validation/strength-skill-schema-20261020/REPORT.md).

## Fixed-node determinism versus timed operational A/A (2026-10-21)

The22 preregistration uses four serial baseline21/baseline21 pairs at1+0.01,
Threads1/Hash32/OwnBookfalse/restart, nodes0, and
`identical_moves_required=false`. The actual producer calls
`pgn_stats.summarize(..., require_identical_pairs=False)` and labels success
operational readiness only. Eight normal games, complete swapped-color pairs,
legal play, exact scheduled openings, fault-free execution and frozen inputs are
still required. This package remains gated until its actual readiness clears.

Application: different reached depths, moves or results in this timed A/A do not
alone fail the harness or justify a retry. Conversely, four fixed10000-node pairs
with unlimited clocks and a frozen identity gate must reject differing paired
moves/results. Do not relabel that failed deterministic attempt as timed A/A after
seeing it fail. A small timed A/A score imbalance is neither an Elo acceptance nor
precise zero Elo; timeout/illegal/crash/warning/orphan/input-change still fails the
strict operational gate. Never pool either A/A with A/B.

[Source-only distinction checks](../../../validation/strength-skill-aa-20261021/REPORT.md).
