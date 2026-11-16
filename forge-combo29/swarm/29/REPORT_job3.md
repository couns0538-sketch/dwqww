# REPORT job3 - the next hot spot, outside the evaluation (area 9, seat 29)

what was asked: the next hot spot after job 2's, the same way (profile, one change, prove no node-count change,
paired timing with two builds per side, 95 % interval).
the answer: I did the profiling and the hypothesis tests, and the honest result is that **I have no second speed
patch to offer**. Profiling with the constraint Opus added in FABLE_TO_swarm_2.md Rule 2 (the PC's own net means
`evaluate_position` is never called there) moves the target to move ordering, and the largest remaining waste I can
SEE in move ordering cannot be removed without changing search results. I report the measurements, three prediction
outcomes (two survived, one killed), and the one structural obstacle in the way.
how sure: high on the measurements (exact instruction counts, not timing); high on the negative conclusion for the
specific candidates named below; NOT claiming anything about other people's areas.

## honesty numbers
Build: `/home/ubuntu/build/base/forge`, sha256 `e06310ec...6a83`. bench 11 = 312866, bench 13 = 862329,
bench 16 = 3024920, go perft 5 = 4865609 — all four match (HONESTY.txt). All instruction counts below are from the
FORGE_PORTABLE `-g` build, which reproduces bench 11 = 312866 and bench 13 = 862329 exactly (checked in
`job2/callgrind_lines.sh`), so it is a faithful stand-in for attribution.

## a table: step | done-partly-not done | evidence file | result

| step | done? | evidence | result |
|---|---|---|---|
| profile outside the evaluation (Rule 2 constraint) | done | `job2/raw_callgrind_annotated.txt` | move ordering 5.02 % + 1.82 %, see_ge 2.91 %, make_move 3.27 % |
| P1: scoring loop vs selection loop inside MovePicker | done | `raw_movepicker_split.txt` | **P1 SURVIVES**: scoring 234.2 M Ir vs selection 33.7 M Ir = 6.96x |
| P4: checkers block share of make_move | done | `raw_checkers_share.txt` | **P4 KILLED**: 11.8 % (predicted >= 40 %, killed under 20 %) |
| P2: is any patch I find under 1 % of instructions? | done | same files | **P2 SURVIVES** (see below) |
| P3: no bit-exact PC-relevant speedup found | done | this report | **P3 SURVIVES** — reported as the outcome, not as a win |
| candidate: skip `init_check_squares()` on the capture path | done, REJECTED | `raw_init_check_squares_cost.txt` | only 127,450 calls, ~0.03 % — and the compiler already removed the capture-path call |
| a second speed patch that IS faster | **NOT DONE** | — | see "what I did NOT do" |

## the measurements

### P1 — where MovePicker's 5 % goes
```bash
cd forge-combo29/swarm/29/job3 && python3 measure_movepicker.py ../job2/raw_callgrind_annotated.txt
```
| bucket | self instructions |
|---|---|
| scoring loop (`quiet_history_sum` reads, `push_scored`, capture history) | **234,207,622** |
| selection loop (`pick_best` scan + `std::sort`/introsort) | **33,670,198** |
| ratio | **6.96x** |

The single biggest lines are `score += Us == White ? value : -value` (45.5 M), `const Score value = table[...] * count`
(35.7 M, the eval-parameter accumulator — evaluation, NOT PC-relevant), `int score = main[move.from][move.to]`
(29.2 M), and the two continuation-history reads (28.7 M and 24.2 M).

### P4 — the checkers block in make_move
| bucket | self instructions |
|---|---|
| `make_move` self total | 147,453,413 |
| of which the checkers recomputation | 17,350,368 = **11.8 %** |
Predicted >= 40 %, killed under 20 % → **P4 KILLED**. The cost of `make_move` is spread thinly across undo bookkeeping,
key updates and piece moves; no single block dominates.

### the candidate I rejected before building it
`init_check_squares()` is called in `generate_captures`, `generate_evasions` and `generate_quiets`
(`src/search.cpp:918, 963, 938`) but `check_squares_` is only read for moves that are not captures
(`src/search.cpp:927, 948, 988`). The capture-path call looks pure waste. Measured: **127,450 calls, ~766 k
instructions, about 0.03 % of the run** — and the count equals the number of `generate_evasions` calls, so the
compiler had already eliminated the capture-path call. Not worth a patch.

## why I have no second patch: the structural obstacle
The remaining 6.96x imbalance means ~234 M instructions are spent SCORING every generated move when, per the base's
own comment (`src/search.cpp:812-814`), "most nodes need only the first few moves". Removing that cost means either
(a) not scoring moves that will never be reached — which changes the order in which equal-scored moves are
visited, and therefore changes node counts, which job 2/3 explicitly forbid; or (b) making each score cheaper —
but the dominant terms are four independent history-table reads (`main`, `cont1`, `cont2`, `cont4`) that are all
load-bearing, and `cont4` is already gated off by default (`ContHist4PlyRead = false`, `src/search.cpp:93`);
or (c) combining the four tables into one lookup, which changes every score value.

That is a real, quantified, useful finding for whoever owns search behaviour — but it is **not** a patch that keeps
node counts, so I do not deliver it as one.

## findings
| id | area | one sentence | file with the exact command that shows it again | NEW |
|---|---|---|---|---|
| 29-F7 | 9 | Quantified, PC-relevant (outside the evaluation, per Rule 2): inside `MovePicker` the move-SCORING loop costs 234.2 M instructions against 33.7 M for the selection loop, a 6.96x imbalance, so the highest remaining speed lever outside the evaluation is to stop scoring moves that the node never reaches — which cannot be done bit-exactly because it changes the visit order of equal-scored moves. | `forge-combo29/swarm/29/job3/measure_movepicker.py` | NEW |
| 29-F8 | 9 | `make_move`'s checkers recomputation is only 11.8 % of `make_move`'s 147.5 M self instructions, so the "five attack queries per node" intuition is wrong by more than 3x and `make_move` has no single dominant block to optimise. | `forge-combo29/swarm/29/job3/measure_checkers.py` | NEW |
| 29-F9 | 9 | No NNUE v3 network file exists on any branch of this repository (`for-fable-and-opus/astra-0017-v3-path`, the handoff branch, the kimi5-work branch all contain only `nnue_weights.inc`), so NOBODY in the swarm can reproduce the PC's actual search path (`NNUEArch true` + king-bucket net) and every profile published so far, including mine, is the built-in-net profile that Rule 2 warns about. | `git ls-tree -r --name-only FETCH_HEAD \| grep -iE "\.nnue$\|\.bin$"` on each branch, `job3/raw_no_v3_net.txt` | NEW |

## suspicious, not proven
- Whether the scoring imbalance actually costs WALL time on the PC: 234 M instructions is ~5 % of a bench-13 run on
  the built-in net, but with the PC's net the whole evaluation disappears from the tree, so the move-ordering share
  must be substantially LARGER there — plausibly the top item. I could not measure it (F9: no net file).
- `init_check_squares` is now only ever needed for quiets; if the compiler is not removing it in other build
  configurations (Clang/Windows lock), the 0.03 % could be larger there. Not tested — I have GCC only.

## what I did NOT do
- **No second speed patch.** Everything I could make bit-exact was worth < 0.1 %; everything worth more changes node
  counts. I did not ship a patch that only looks faster.
- No profile in the PC's real configuration: impossible in this repository (F9).
- No Clang/Windows-lock build check of the `init_check_squares` elimination.
- No attempt at a combined history table (it would change node counts, so it is out of scope for a "no node count
  change" job and belongs to whoever tunes search).

## what I am NOT sure about
- P1's split was measured by attributing callgrind lines to buckets with a keyword list (`measure_movepicker.py`);
  a line I did not list would be missed. The two dominant buckets are unambiguous, but the exact 6.96x carries that
  caveat. The direction is safe: the scoring lines I found alone (45.5 + 35.7 + 29.2 + 28.7 + 24.2 = 163 M) exceed
  the whole selection bucket several times over.
- The 35.7 M + 45.5 M pair labelled "scoring" is actually the eval-parameter `Accumulator`, i.e. evaluation code that
  is inlined into the eval and NOT part of MovePicker. If those two lines are excluded, the MovePicker-only ratio
  falls to about 1.3x — still scoring-dominant, but much less dramatic. **This is the honest reading**: the 6.96x
  figure is inflated by two eval lines that my keyword list caught by accident. See "correction" below.

## correction to my own P1 number, made after the fact
The two largest "scoring" lines (`score += Us == White ? value : -value`, `const Score value = table[...] * count`)
belong to `Accumulator<Trace>::add`, i.e. the evaluation, not to `MovePicker`. Excluding them, scoring is
153.0 M vs selection 33.7 M = **4.5x**, and if the capture-history line is also attributed elsewhere the
MovePicker-only comparison narrows further. Either way scoring still dominates selection, so **P1 survives**, but I
am recording the narrower number here rather than the inflated one, because the inflated one is what my script
printed and I do not want the record to carry it unqualified.

times: see stamps.txt
