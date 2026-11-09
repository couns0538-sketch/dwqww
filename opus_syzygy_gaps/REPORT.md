# Report: Syzygy gaps in P6 (job opus-syzygy-gaps-20261107)

## Result
- **Seven evidenced gaps in the P6 Syzygy integration are closed**, each behind a default-off switch. Four more candidates were checked and rejected: no gap there.
- **Off means off.** With the macros off the build is byte-identical to the parent exe (150374ff). With the macros on and the options at 0, all pins match and 10 identity sets plus 3 warm runs are node-identical.
- **No strength claim.** No games were played. With an option on the search changes: SEARCH/EVAL CHANGE, UNPROVEN, QA's SPRT decides. Move quality is neutral on 198,507 cold roots (333 blunders against 336, p = 0.84). The switches remove false claims and fix boundary roots; whether that matters in games is unknown.
- **Ready for Code Review, with one blocker:** this session has no channel to Code Review or QA. Couns forwards the pack (`HANDOFF.md`).

Candidate: frozen head 989399b on the P6 tree. All on means `SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3`. Full numbers: `BENCH.md`. Gap by gap: `GAP_LEDGER.md`. Semantics: `README.md`.

## What was wrong, and what changed
"TB" = tablebase. The parent numbers are errors found against independent oracles; the all-on numbers are the same checks on the frozen head.

| gap | what happened on the parent | switch | parent | all on |
|---|---|---|---|---|
| G2 | shallow pruning kept running after a TB loss, so a fail-soft TB loss was stored and passed up as a proven result: false TB wins at parents and in the hash | `SyzygyTbBounds` bit 1 | on 3000 roots: 2991 wrong pruned fail-lows, 3532 false TB wins, 4176 wrong hash cuts | 0 |
| G3 | correction history learned from TB scores, while mate scores are excluded | `SyzygyTbBounds` bit 2 | 96,932 updates | 0 |
| G1 | a null move returned a TB score as proof, though passing can win in a zugzwang where moving does not | `SyzygyTbBounds` bit 4 | 12 wrong cuts in 8 of 1250 roots, after bits 1 and 2 | 0 |
| G5 | at exactly 50 moves (dtz + counter = 100) a win showed as a draw, and a move that draws was mixed with moves that lose. **A result could be thrown away** | `SyzygyRootExact` bits 1, 2 | 197 worse moves kept on decided roots, 430 wrong reports, 5 of 800 lines lost a draw | 0, 0, 0 on decided roots; see the limit below |
| G6 | with a DTZ table missing, the root showed a TB win or loss the 50-move clock had already ruled out | `SyzygyRootExact` bit 1 | 41 and 10 false scores on partial table sets, 2186 + 2169 on the clock fixture | 0 |
| G7 | a TB or mate score from the hash was used at a clock where it could no longer be completed. **A drawn root could be lost:** `8/q7/8/8/8/3Q1RK1/k7/8 b - - 87 44` | `SyzygyRule50` bit 1 | 5 false claims in 3000 warm rows, 1842 wrong hash cuts | 0, 0; the FEN keeps the draw |
| G8 | changing `Syzygy50MoveRule` kept TB scores stored under the old rule | `SyzygyRule50` bit 2 | 158 of 400 rows with another result than after a Clear Hash | 0 |

Rejected after checking: G4 (PV nodes return a TB bound), G9 (singular and ProbCut guards), G10 (`tbhits` output), G11 (en passant). Reasons in the ledger.

## What it costs, and what stays open
- **Boundary roots the walk cannot decide.** At dtz + counter = 100 with a rounded distance, `SyzygyRootExact` bit 2 walks the lines, at most 1000 moves per root, about 35 ms at worst. If that runs out it claims nothing, and shows the search score. On the purpose-built fixture that happens on **919 of 4569 rows**, mostly at clocks 60-89. The independent solver also gave up on 812 of those 919 within 8 s each. On the rows it finished: 107 undecided, 34 kept moves worse, and 4 engine moves worse at depth 8. How often such roots occur in games was not measured. An earlier version of the ledger said "54 of 2455", which is true only of the first 2500 rows, the high-clock part.
- **True claims withheld.** `SyzygyRule50` bit 1 withholds 20 of 308 true warm claims on the control rows (288 kept; cold finds 292).
- **Store-side rule not at a root and not in qsearch.** By reading, a root's entry could be read later at a clock it does not fit. No failing case was found, on purpose-built rows. Code Review should judge it.
- **WDL-only move filter.** With a DTZ table missing, the ranks cannot see the clock, so a kept move can be a 50-move draw. Only the report is corrected. Full table sets are not affected.
- **Damaged table bodies.** File checksums are not verified, so body damage that still parses can give wrong values. Verified: no crash, no out-of-range read (44 damaged-folder runs under ASan). Changing the reader was outside this job.

## Proof that off means off
| check | result |
|---|---|
| preprocessed source, macros off, against the parent | equal |
| Build A (macros off) | byte-identical to parent exe 150374ff |
| Build B (macros on, options 0), built twice | byte-identical, db91700e |
| pins, no tables and with tables | all equal |
| 10 identity sets, up to 30,000 rows each, 5.0 billion nodes | 0 rows differ |
| warm-table identity, 3 runs, 2000 searches each | identical |
| fresh tree from the pack alone | same tree, same exes |

## The trial_w6 line
The live lock line is trial_w6, so QA needs the change on that source: `patches/syzygy_port_and_gaps_after_w6.patch`.

- The first attempt failed for a real reason: one hunk did not apply, because trial_w6 wraps a line of its context. A fail-closed check added after review R3 stopped it. With the old script, the build would have gone on without two of the fixes.
- The merged patch has the same 234 changed lines, and no changed line sits inside a speed-switch block.
- **Every check passes.** With options 0: byte-identical Build A', pins equal, identical nodes against both parents. With all options on: identical nodes to the frozen P6-line build on the bench, 30,000 roots, all root fixtures, 4569 boundary roots and 2000 warm searches. So the suite's results carry over. UBSan is clean. ASan was not run on this line, and the clang recipe of the live exe was not built here: that recipe is QA's.

## How far to trust this
- **Reviews were this job's own, not Code Review.** Three by one Opus subagent, R1 to R3, the last with nothing at BLOCKER, HIGH or MEDIUM.
- **Bug hunter.** One Fable subagent hunted bugs next to the final work (`review/H1.md`). It found no engine bug. Its one MEDIUM finding was a test gap: deliberately broken copies of two read rules of `SyzygyRule50` bit 1 passed every fixture. New rows now catch both (239,790 and 18 wrong claims), with 0 on the frozen head (`REVIEW_LOG.md`, H1). Its other broken copies were caught by the existing fixtures.
- **Own errors found on the way**, all in `REVIEW_LOG.md`: a signed overflow in the walk's cap, and a rule-50 gate missing on one code path, both fixed test-first (B1, B2). Then the rejected hunk above (B3), a check of mine that cut off its own verdict (B4), a script reading the wrong column behind one claim, which turned out to hold (B5), and a checker skipping rows (B6): a new per-move check on those rows found 0 errors on the frozen head and real ones on the parent.
- **Not measured:** strength, speed, frequency of boundary roots in games, 6-piece tables (none on this PC; the interior fixtures use 5-man roots with 3-4 piece tables as the same situation one piece lower).

## Next steps
1. Couns forwards this folder to Code Review (`HANDOFF.md` has the checks and five judgement calls).
2. After Code Review, QA decides the gates. P6's own gates have no results yet, so P6 itself is unproven too.
3. Nothing here was queued, published or locked.

## Where everything is
| what | where |
|---|---|
| patches | `patches/` |
| numbers, hashes, logs | `BENCH.md`, `logs/` |
| gaps, limits, rejected candidates | `GAP_LEDGER.md` |
| semantics, switches, tools | `README.md` |
| reviews, own bug checks | `REVIEW_LOG.md`, `review/` |
| hand-off | `HANDOFF.md` |
| state, rulings, resume | `STATUS.md` |
| licences of ideas and oracles | `IDEA_SOURCE.md`, `tools/THIRD_PARTY_NOTICES.md` |
| checksums | `MANIFEST.md5`, `MANIFEST.sha256` |
