# PREDICTION — deepseek6, long 7 (sanitizer build: planted fault, then clean)

Written before the first measuring command of long 7. Never edited after this commit.

## The builds

| build | what | exe |
|---|---|---|
| planted | a scratch copy of 6b98f217 (`/agent/repos/p11`) with ONE added block: a heap read one element past an `new int[8]`, at the top of `Worker::search` when `root_node` | `/agent/repos/work/build-l7plant/forge` |
| clean | 6b98f217 untouched (`/agent/repos/p10`) | `/agent/repos/work/build-l7san/forge`, sha256 `9e3de2e5a1b12c1dfcf57be52fc49fd301a4d92da010f62c08b9f45156776cab` |

Both are `RelWithDebInfo`, g++ 13.3.0, with `-fsanitize=address,undefined -fno-omit-frame-pointer` on both the
compile and the link. The planted change is committed as TEXT (`planted/planted_fault.patch.txt`), never as
source.

## The planted fault must be reported

Engine run: `position startpos` / `go depth 6`, stderr captured separately.

| expected | killed by |
|---|---|
| `AddressSanitizer: heap-buffer-overflow` on a `READ of size 4`, with a frame naming `Worker::search` at the planted line (~1561) | no ASan line at all, or an ASan line pointing somewhere else |

## The clean build must be silent

| expected | killed by |
|---|---|
| `go depth 10` on each of the 200 positions of O and 353 of G under S14, **0** AddressSanitizer and **0** `runtime error` lines from UndefinedBehaviorSanitizer across every process | any ASan or UBSan line, which is a finding and gets its own table with the position and the report text |

I expect 0 because nothing in this build has been changed; the point of the run is to establish that the
base engine is clean under both sanitizers on these 553 positions, so that long 8's patched builds have a
baseline to be compared against.

Also predicted: the sanitizer build's node counts are the SAME as the release build's, because the sanitizers
do not change integer arithmetic or the search order. I will report the O/S14 and G/S14 sums from the clean
sanitizer build and compare them to 9,500,069 and 18,466,239. **If they differ I will NOT call it a
finding about the patch — it would be a finding about this build's arithmetic** (a sanitizer changing a node
count would mean UB in the base engine, which is exactly what long 7 is meant to detect), so I predict
**equal** and treat a difference as the most interesting possible result.

| run | predicted sum |
|---|---|
| clean sanitizer, O/S14, depth 10 | NOT predicted — long 1 measured depth 12, and depth 10 was not measured on the release build, so there is no known answer to compare against. I will record the sum and the sanitizer count; the SUM is not a known-answer test at depth 10. |
| clean sanitizer, G/S14, depth 10 | same |

**I wrote that last table deliberately.** The brief for long 7 asks for `go depth 10` on O and G under S14
and for a count of sanitizer lines — not for a node sum identity, because no depth-10 sums exist in the
brief. So the known answer for long 7 is "zero sanitizer lines"; the sums are recorded as data for long 8's
comparison, and I will not pretend they are a known-answer check.
