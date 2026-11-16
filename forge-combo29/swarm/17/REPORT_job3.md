# REPORT job 3 — seat 17, area 7 (transposition table)

## What was asked / the answer / how sure

**What was asked.** Area 7 job 3: read the transposition table for faults — overflow, uninitialised value,
off-by-one, index out of range, a race — and give a TEST for every suspicious line, with anything untested
listed as unproven.

**The answer.** No fault found. The design has explicit guards for exactly the dangerous cases (stale slot,
foreign probe handle, generation ageing, epoch invalidation) and I exercised the ones reachable from the UCI
layer: resizing to the minimum, the maximum and toggling between searches, plus 18 searches under ASan+UBSan.
All clean, and `Hash` sizing behaves correctly (hashfull 440/58/10/0/0 across 1/8/32/512/2048 MB, node counts
converging once the table stops being the constraint, identical bestmove).

**How sure.** The negatives are certain within the scope below — single-threaded searches with resize between
searches. I did NOT test a resize *during* a search, which is the race the comments warn about, because the UCI
loop calls `stop_search()` before `setoption` (src/uci.cpp:259), so that path is not reachable from UCI.

## Step / done-partly-not done / evidence table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| Read `TTEntry`, `TTCluster`, `TTProbe`, `TranspositionTable` | done | this report | 16-byte entry, 64-byte cluster, `static_assert`s present |
| Read `probe_body`, `store_body`, `lock_stripe`, `resize`, `clear`, `new_search`, `hashfull` | done | this report | stale-slot re-find and epoch checks read line by line |
| `Hash` at min / max / toggled, 6 positions each, ASan+UBSan | done | `job3/hash_resize.json` | 18 searches, 0 sanitizer lines |
| `Hash` 1/8/32/512/2048 on one position, measuring hashfull and nodes | done | `job3/hash_sizes.json` | 440/58/10/0/0, nodes 53652 then 52591 x4 |
| Resize during a search (the real race) | not done | — | not reachable from UCI: `setoption` calls `stop_search()` first (src/uci.cpp:259) |
| `hashfull` sampling bias (only the first 1000 clusters) | not done by me | seat 27's S-F3 | already found by a seat with a better command; I did not duplicate it |

## Findings

None of my own in this job. Two verifications worth having:

**S-F9 — TT resize verified clean.** `Hash` 1/8/32/512/2048 MB changes only the pressure, not the answer:
hashfull 440 / 58 / 10 / 0 / 0, nodes 53652 then 52591 four times, identical bestmove; 18 ASan+UBSan searches
with Hash at min, max and toggled between searches gave 0 sanitizer lines.
Command: `cd forge-combo29/swarm/17/job1 && python3 -c "import json;[print(r) for r in json.load(open('job3/hash_sizes.json'))]"`

**S-F10 — my own method lapse, recorded.** My first Hash-size measurement pipelined `quit` into the search and
got `None` for all five sizes: the 19-F12 fabricated-answer trap, which I had already been warned about. Re-run
with the read-to-bestmove driver, the same five sizes measured properly. The correction is in FINDINGS because
the wrong version briefly existed.

## Suspicions, not proven

- `store_body`'s `admit` predicate uses `depth + 4 > entry->depth` as a replacement heuristic; the `+4` is a
  tuning constant with no test behind it that I could construct without changing engine behaviour.
- `hashfull()` samples only the first 1000 clusters (seat 27's S-F3 owns this); a table smaller than 1000
  clusters therefore reports a full scan and a large one reports a 1000-cluster sample, so the number is not
  comparable between sizes — which is exactly what my 440 vs 0 measurement shows and why I used node counts,
  not hashfull, as the real signal.

## What I did NOT do

- Did not test resize during a search (unreachable from UCI, see above).
- Did not test the multi-threaded TT under TSAN; that is area 4's job.
- Did not write a patch or change engine source.

## What I am NOT sure about

- Whether `lock_stripe`'s retry loop can spin indefinitely under a pathological interleaving; I read it as
  making progress (the exclusive owner drains every stripe) but did not build a stress test.

## Times

see `job3/…` logs and the `STATUS.md` blocks.

## Last commands' output

```
=== git status --short
(clean at the commit that adds this report)

=== ls job3
hash_resize.json  hash_sizes.json  hashsize_1.log .. hashsize_2048.log
hash_min_0.log .. hash_max_5.log  hash_toggle_0.log .. hash_toggle_5.log
```
