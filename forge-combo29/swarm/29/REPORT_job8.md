# REPORT_job8 - a provably-identical speed patch in the TT replacement path (area 9)

what was asked: my own follow-up after 29-F11 / 29-C1 showed the transposition table is a bigger share of real
search than `bench` suggests (2.6x), and that is outside the evaluation, so it is PC-relevant under Rule 2.
the answer: I found and proved one genuinely redundant comparison in the TT replacement path. It removes
**9,081,823 instructions (-0.201 %)** per `bench 13` with all four node counts unchanged and 40/40 search results
bit-identical. It does **not** show a measurable wall-clock win on `bench 13` (ratio 1.0090, 95 % CI [0.9931,
1.0297]) — the effect is below what this shared machine can resolve. So: a real, tiny, provably-safe optimisation,
not a speed claim.
how sure: high that the patch is behaviour-identical (three independent proofs); high that the instruction saving
is real; explicitly NOT claiming a measured speedup.

## the redundancy
`TranspositionTable::probe_body` seeds the replacement candidate from slot 0, then loops over **all four** slots and
compares each against that seed. Slot 0 is compared against a score computed from slot 0 itself:

```cpp
TTEntry* replace = &cluster.entries[0];
int replace_score = replace->occupied() ? replace->depth - 4 * age0 : 0;
for (TTEntry& entry : cluster.entries) {        // includes entries[0]
    if (!entry.occupied()) return snapshot(entry, false);
    const int score = entry.depth - 4 * age;
    if (score < replace_score) { replace = &entry; replace_score = score; }   // never true for entry 0
}
```

For slot 0, `score == replace_score`, so `score < replace_score` is false: the comparison can never fire. The patch
starts the loop at slot 1 and performs slot 0's unoccupied check before the loop, which preserves the exact order in
which unoccupied slots are chosen (0 first, then 1..3) and the exact tie-breaking (`<` keeps the earliest slot).

## honesty numbers
Clean base `e06310ec...6a83`: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609.
Patch build `ttA`: **312866 / 862329 / 3024920 / 4865609 — all four identical.**

## a table: step | done-partly-not done | evidence | result

| step | done? | evidence | result |
|---|---|---|---|
| patch as a text diff against 6b98f217 | done | `tt_replace_skip_slot0.patch.txt` | applies with `patch -p1`, no fuzz |
| build twice | done | `~/build/ttA`, `~/build/ttB` | both build clean |
| four honesty node counts unchanged | done | `raw_tt_ir.txt` | 312866 / 862329 / 3024920 / 4865609 |
| search output bit-identical, 40 positions x depth 10 | done | `raw_tt_equiv.txt` | **40/40 agree**, 852,430 nodes compared, score+PV+bestmove identical |
| exact instruction count | done | `raw_tt_ir.txt` | 4,513,768,543 -> 4,504,686,720 = **-9,081,823 (-0.201 %)** |
| paired wall-clock, 2 builds per side, interleaved | done | `raw_tt_paired.txt` | ratio 1.0090, CI [0.9931, 1.0297] = INDISTINGUISHABLE |
| a measurable speed win | **NOT DONE** | — | effect is below this machine's resolution |

## findings
| id | area | one sentence | file with the exact command that shows it again | NEW |
|---|---|---|---|---|
| 29-F12 | 9 | `TranspositionTable::probe_body` compared slot 0 of the cluster against a replacement score derived from slot 0 itself, a comparison that can never be true; skipping it removes **9,081,823 instructions (-0.201 %)** per `bench 13` with all four node counts identical and 40/40 search results bit-identical, at no measurable wall-clock change on this shared machine. | `forge-combo29/swarm/29/job8/tt_replace_skip_slot0.patch.txt` | NEW |

## suspicions, not proven
- The saving should be worth MORE on the PC than on `bench`: `probe_body` is 1.4-2.0 % of a bench run but 3.65-4.86 %
  of a deep search (my 29-F11 / 29-C1), and the replaced comparison executes on every probe that misses. I cannot
  test the PC's net (29-F9).
- The 0.201 % is ~2 comparisons per probe-miss; a deeper cluster (more slots) would amortise better, but the cluster
  size is pinned at 64 bytes by a `static_assert`.

## what I did NOT do
- No claim that this is faster in wall time. It is below resolution here, and I am not repeating my job-2 mistake of
  reading drift as a win.
- Did not touch the probe's lock path, the generation refresh, or the aging arithmetic (all behaviour-bearing).
- No PC-net measurement (impossible: 29-F9).

## what I am NOT sure about
- Whether the compiler had already removed part of this comparison in the non-portable lock build (the instruction
  count was measured on the portable `-g` build); the source-level redundancy is real either way.
- Whether `entries[0]`'s occupied check being hoisted out of the loop changes anything for a cluster where slot 0 is
  the only unoccupied slot — it does not, because that path returns `snapshot(entries[0], false)` exactly as the old
  loop did on its first iteration.

times: see stamps.txt
