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
