# REPORT_job7 - CHECK of 19-F6 (the material key's cost)

what was asked: 19-F6 says the material key is re-derived 750,427 times per `bench 13`, is 2.71 % of total self
time, and that the value "changes only on a capture or a promotion".
the answer: **the call count is exactly right (750,427), the time share is not reproducible on my build (0.153 %,
about 18x less)**. I also could not test the "changes only on capture/promotion" clause, and I explain why that
matters for anyone acting on 19-F9.
how sure: high on the count (measured by instrumentation, not estimation); high on the 0.153 % line attribution;
medium that this refutes their 2.71 %, because we may be attributing differently (see caveats).

## honesty numbers
Build `/home/ubuntu/build/base/forge`, `e06310ec...6a83`, bench 13 = 862329 on every run. The instrumented copy
prints the same 862329, so the counter did not perturb the search.

## method 1 - the count, by instrumentation (decisive)
Line attribution cannot see an inlined function, so I made a scratch copy of the source with a counter:

```cpp
// src/search.cpp, at namespace scope (NOT inside the anonymous namespace, so the symbol links)
std::uint64_t g_material_key_calls = 0;
...
[[nodiscard]] std::uint64_t material_key(const Board& board) {
    ++g_material_key_calls;
    ...
```
```bash
printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nbench 13\nquit\n' \
  | ./forge 2>&1 >/dev/null | grep MATERIAL_KEY_CALLS
# MATERIAL_KEY_CALLS 750427
```

**750,427 — exactly the number 19-F6 states.** The count is CONFIRMED. (My first attempt at this failed to link
because I put the counter inside the anonymous namespace, which gives it internal linkage; the error is recorded in
the transcript rather than hidden.)

## method 2 - the time share, by line attribution
| line | instructions | % of the 4,513,768,536-instruction run |
|---|---|---|
| `correction += (*material_correction_)[side][material_key(board) & mask] * w / 100` | 6,917,530 | **0.153 %** |
| `apply((*material_correction_)[side][material_key(board) & mask])` (update site) | 234,696 | 0.005 % |

19-F6 says 2.71 %. Mine is 0.153 % on the read site. Both cannot be right about the same quantity.

## method 3 - the test I attempted and my harness REFUSED to run
The obvious way to bound the cost is to switch it off: `setoption name MaterialCorrectionWeight value 0` disables
exactly the read (`src/search.cpp:1218`) and the write (`src/search.cpp:1237`). I ran 10 alternating pairs of
weight 100 vs weight 0 and got:

| setting | nodes | median |
|---|---|---|
| weight 100 | **862,329** | 441.0 ms |
| weight 0 | **792,487** | 415.5 ms |

The node counts DIFFER, so the two settings search different trees and no timing comparison between them can be
attributed to the key. My harness printed exactly that and declined to conclude
(`measure_material_key.py`, `raw_material_key.txt`). This also means **19-F9's neutral result cannot have been
obtained by toggling the weight** — their patch caches the key inside `Board`, keeping the search identical, which
is the right design and is not what I tested.

## a table: step | done-partly-not done | evidence | result

| step | done? | evidence | result |
|---|---|---|---|
| count by instrumentation | done | `raw_material_key_count.txt` | **750,427 — CONFIRMS 19-F6 exactly** |
| share by line attribution | done | `raw_material_key.txt` | 0.153 % — does NOT match 2.71 % |
| toggle test | attempted, REFUSED | `raw_material_key.txt` | node counts differ (792,487), so no valid timing |
| "changes only on capture/promotion" | **NOT DONE** | — | see below |

## findings
| id | area | one sentence | file | type |
|---|---|---|---|---|
| 29-C5 | CONFIRMS the count in 19-F6, DISPUTES its share | `material_key` is called exactly **750,427** times per `bench 13` (measured by an instrumented counter), but the line that uses it is **0.153 %** of the run's instructions on my build, not 2.71 %. | `job7/measure_material_key.py`, `raw_material_key_count.txt` | mixed |

## what makes this finding weak, stated plainly
- **Attribution method differs.** Seat 19 reports "2.71 % of total self time" from a perf sample set; I report
  0.153 % from callgrind instruction counts on a `-g` portable build. If their profile was taken with the
  **non-portable** build, `material_key`'s ten-popcount chain may not be inlined the same way, and a call could be
  more expensive there. I did not test the non-portable build's attribution.
- **My 0.153 % is a lower bound**, because the compiler may have hoisted parts of the key computation into other
  lines. The function is inlined in both cases, which is precisely why line attribution is untrustworthy here — so
  I lean on the COUNT as the solid part and treat the share as contested rather than settled.

## what I did NOT do
- Did not verify "changes only on a capture or a promotion": that needs a position-by-position comparison of
  `material_key` before/after each move type, which is a separate job. It matters, because if the key also changes
  on a non-capture (it is a hash of the six piece COUNTS, so a promotion and a capture change it and a quiet move
  does not — this seems right by inspection) then 19-F9's cache would be wrong; by inspection it does look
  capture/promotion-only, but I did not test it and I am not asserting it.
- Did not build the non-portable variant to compare attribution.

## what I am NOT sure about
- Whether 2.71 % is right for the lock build and 0.153 % right for the portable one. Both could be true of
  different binaries, which is why I record this as "not reproduced on mine" rather than "wrong".

times: see stamps.txt
