# Step 2 — the v3 count-specialised accumulator patch: identity PASSES, speed pending — seat 08

## The patch (text only, `v3/v3_pair_count_dispatch.patch.txt`)

`apply_changes_pair_avx512` is the hot v3 function (2,382,071 calls, 8.47 % of bench-13 self time). Its reference shape
re-tests `i < c.count` **for every 32-lane step of the h loop**, for both perspectives. The patch dispatches **once on
`c.count`** (1/2/3/4, the maximum `collect_changes` can produce) into fully unrolled specialisations, so each slot's
liveness is decided outside the h loop.

**The arithmetic per element and its order are unchanged** — same adds, same lanes, same slots in the same sequence —
so the result must be bit-identical. That is the property the identity check tests.

## Identity check: PASSES COMPLETELY

| check | required | patched build | verdict |
|---|---|---|---|
| bench 11, no setoption | 312866 | **312866** | exact |
| bench 13, no setoption | 862329 | **862329** | exact |
| bench 11, PC20 | 278024 | **278024** | exact |
| bench 13, PC20 | 587276 | **587276** | exact |
| bench 11, test net | 965454 | **965454** | exact |
| bench 13, test net | 4151906 | **4151906** | exact |
| bench 11, PC20 + net | 625258 | **625258** | exact |
| bench 13, PC20 + net | 3652372 | **3652372** | exact |
| eval startpos | nnue 968 | **968** | exact |
| eval position 2 | nnue 1176 | **1176** | exact |
| eval endgame | nnue 31 | **31** | exact |
| **200-opening node sum** | **27,944,084** | **27,944,084** | **exact** |

**Every identity row reproduces, including the 200-opening sum.** Per file 7 Step 2's rule, that means the patch is a
legitimate speed patch and not a behaviour change.

## Speed: measured, and the answer is a REJECTION

See `REPORT_v3_step2_speed.md`. The short version: **the bench shows a small gain, the real-position arm does not
separate it from the per-position spread.** Under the rule the coordinator restated — no recommendation from the bench,
a fixed-budget ABBA at n ≥ 120 with the spread shown — **this patch is reported as a rejection with its numbers**, not
as a win.

## What the patch is, stated so it can be reused
It is in the folder as `v3_pair_count_dispatch.patch.txt`, a unified diff against file 5's tree, applies with
`patch -p1` without fuzz, builds with the same flags, and keeps every identity row. **A later reader can take it and
measure it on the PC** even though I am not recommending it: the identity work is done and the code is small.

## What is NOT established
- That the patch helps on the PC's **clang + `-march=znver5` + PGO** build. My measurement is g++ 13.3.0 with no
  `-march`, and a different compiler can turn an unrolling hint into nothing or into something.
- That it helps on the PC's **real net** — I used the shared-shape test net.
- Anything about strength: node counts are identical by construction, so any strength difference would be pure noise.
