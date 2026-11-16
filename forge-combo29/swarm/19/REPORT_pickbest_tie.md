# REPORT — tie order in `pick_best` is LOAD-BEARING: a stable sort changes every bench node count

seat 19 · area 9 · branch `for-fable-and-opus/swarm-19`

## 1. The three lines

**What was asked.** Follow-on from my own `pick_best` attribution: I reported that the 5 % of calls taking
`std::sort` hold ~23 % of `pick_best`'s local samples, and that "whether a different selection order changes
node counts is exactly the question a patch would have to test". This is that test.

**The answer.** Tie order in that sort is **load-bearing**. Replacing `std::sort` with `std::stable_sort` —
same range, same comparator, only the algorithm changed — moves three of the four honesty numbers:
bench 11 **312,866 → 292,627** (−6.5 %), bench 13 **862,329 → 939,494** (+8.9 %), bench 16
**3,024,920 → 2,925,608** (−3.3 %); perft 5 is unchanged at 4,865,609 (perft does not use the picker).
So the sort branch **cannot** be freely replaced, and any speed work there must preserve `std::sort`'s exact
tie behaviour — which is unspecified by the standard, so it must be preserved *for this libstdc++ version*
rather than in principle.

**How sure.** Certain of the measurements (four numbers, fresh process each, pasted below). Very sure of the
conclusion: the node counts moved, so tie order demonstrably reaches the tree. Not sure *which* ties matter —
I did not identify a specific position where two equally-scored moves swap.

## 2. The numbers

| check | committed base | with `std::stable_sort` | change |
|---|---|---|---|
| bench 11 | 312,866 | **292,627** | −20,239 (−6.5 %) |
| bench 13 | 862,329 | **939,494** | +77,165 (+8.9 %) |
| bench 16 | 3,024,920 | **2,925,608** | −99,312 (−3.3 %) |
| `go perft 5` | 4,865,609 | 4,865,609 | unchanged |

Command: `bash job2/headroom.sh stable job1b/../pickbest/edit_stable_sort.py`, then the four lines above
pipelined individually. Base build for comparison is `~/build_rel/forge` (sha256 `e06310ec…`, the same binary
two independent rebuilds produce — see 19-C2).

Note also that the variant was *slower* (median 485 ms vs base 431–443 ms), so stable_sort is not even a
speed candidate; the point is the node counts, not the time.

## 3. Table: step | done-partly-not done | evidence | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| state the question as a falsifiable test | done | this report §1 | "does tie order reach the tree?" |
| one edit, algorithm only, comparator unchanged | done | `pickbest/edit_stable_sort.py` | `std::sort` → `std::stable_sort`, nothing else |
| run all four honesty numbers on the variant | done | §2 above | three of four moved |
| find a specific position where a tie swaps | **not done** | — | see §5 |
| a speed patch for the sort branch | **not done, and now shown to be risky** | — | any change must preserve `std::sort`'s exact tie order |

## 4. Findings

**19-F15 — tie order in `MovePicker::pick_best`'s `std::sort` changes node counts, so that branch cannot be
optimised by changing the sort.** `std::stable_sort` gives bench 11 = 292,627, bench 13 = 939,494,
bench 16 = 2,925,608 against the committed 312,866 / 862,329 / 3,024,920, with perft 5 unchanged. Show it
again: `bash forge-combo29/swarm/19/job2/headroom.sh stable forge-combo29/swarm/19/pickbest/edit_stable_sort.py`
then `printf 'bench 13\nquit\n' | ~/h/stable/build/forge`.

**19-F16 — this makes Opus's file 3 the *reason* the sort branch is untouchable, and sharpens it.**
File 3 says "equal-scored moves are sorted by `std::sort`, whose order for ties is not fixed: a search is not
exactly colour-symmetric in node counts — known and harmless." My measurement says something stronger: the
tie order is not merely *unsymmetric*, it is **directly load-bearing on the node counts**, because making the
order deterministic in a different way moves bench 13 by 8.9 %. So "known and harmless" is right about
*correctness* and wrong about *freedom to change*: the node-count pins depend on libstdc++'s current
`std::sort` tie behaviour, not just on the comparator. Any future compiler or standard-library change to
`std::sort`'s tie handling would silently move the honesty numbers. That is worth knowing for build
reproducibility.

### Suspicions, not proven

- That the +8.9 % at depth 13 comes from the search exploring a different-but-equal-scored subtree early,
  and that the effect could go the other way at another depth (bench 11 went *down*, bench 16 also went down,
  so the direction is not even consistent across depths — which itself argues this is tree-shape noise, not a
  strength change). Not proven.
- That libstdc++'s `std::sort` tie order is stable in practice for small ranges (it uses insertion sort for
  short runs), which would explain why *some* ties never swap. Untested.

## 5. What I did NOT do

- I did not find a concrete position where two equally-scored moves swap and thereby change the searched
  tree. That would be the airtight demonstration, and it needs instrumentation of `Scored` values at the
  moment of sorting.
- I did not test any *other* tie-breaking scheme (e.g. stable by insertion index, or reverse-index), so I
  cannot say which part of the current order matters.
- I did not check whether a different libstdc++ version changes these numbers. Cannot without another
  toolchain.

## 6. What I am NOT sure about

- Whether the effect is on the *root* move choice or deep in the tree. The counters I have are totals.
- Whether the numbers would move back if the comparator were made a strict weak order over a tie-break key
  (e.g. compare score, then compare `move`), which is the one change that might make the sort both fast and
  reproducible. That is a *behaviour* change — it would need the four pins re-baselined, which is the owner's
  call, not mine.

## 7. Times and files

`pickbest/stamps.txt`. Files: `pickbest/edit_stable_sort.py` (the one-line edit),
`pickbest/summarize_pickbest.py` (the counter table), this report.
