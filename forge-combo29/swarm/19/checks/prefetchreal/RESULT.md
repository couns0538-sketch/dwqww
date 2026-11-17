# 19-C58 — the prefetch slowdown IS general. It is not a bench artefact, and my prediction was wrong.

## Answer
**On real positions at a fixed node budget, `_mm_prefetch` of the NNUE weight columns makes the engine
9.80 % slower (pooled), median 1.087 per position, and it is slower on 121 of 130 positions (93.1 %).**
**The bench figures were 8.1 % (19-F10, mine) and 9.43 % (29-C4, seat 29).** The real-position figure is the
**largest of the three**. **So 19-F10 and 29-C4 both stand as general speed claims — this is the one place in my
record where bench UNDERSTATED nothing and generalised correctly.**

## The control — and why this is a clean result rather than another mixed one
**Both builds pass all four honesty pins with IDENTICAL node counts:**

| pin | CTRL | PF |
|---|---|---|
| bench 11 | 312,866 | **312,866** |
| bench 13 | 862,329 | **862,329** |
| bench 16 | 3,024,920 | **3,024,920** |
| perft 5 | 4,865,609 | **4,865,609** |

**That equality is the control, and it is what makes this measurement unambiguous.** Because the patched build
walks **the same tree** as the control and reaches **the same node count**, every millisecond of the difference is
**per-node cost** — there is no node-count difference to confound it, and no need to infer per-node cost from two
noisy ratios as 19-C53 had to. The measured ratio **is** the quantity being claimed.

- **CTRL** = unpatched `6b98f217` tree, g++ 13.3.0, `-DFORGE_MATE_ALPHA_GUARD=1`, `FORGE_MARCH=x86-64-v4`,
  **0 `_mm_prefetch` in `nnue.cpp`**.
- **PF** = same tree, same flags + `job3/prefetch_columns.patch.txt`, **17 prefetch calls**.

**Reinforced at run time:** the fixed `go nodes 50000` budget produced an achieved **node ratio of 1.0000** across
all 130 pairs, so the same-tree property held in the measured sessions too, not just in the pins.
- Fixed `go nodes 50000`, Threads 1, Hash 16, ABBA, fresh process per search, **130 pairs**.
- **Node ratio achieved 1.0000** — the fixed budget held, so the time ratio is the per-node cost.

## The distribution (what I was asked to report instead of a pooled figure)
| | min | Q1 | **median** | Q3 | max |
|---|---|---|---|---|---|
| per-node ratio PF/CTRL | 0.469 | 1.062 | **1.087** | 1.119 | 3.227 |

- **IQR 0.057**, sd 0.230, **93.1 % of positions slower**
- **pooled 1.0980 (9.80 %)**, geometric 1.0991 (9.91 %), mean 1.115
- **robustness: removing the single 3.2× outlier gives pooled 1.0787 (7.87 %)** — still well above bench-scale doubt
- **so the effect is present on nearly every position, not driven by a tail.** This is the same shape as
  19-C54's per-node result (tight IQR, wide node ratios) and the opposite of a coin flip.

## My prediction, and that it failed
I predicted **1.02–1.06**, on the reasoning that bench 13's fixed position mix is cache-friendly and would
**overstate** a cache-polluting penalty; the kill condition I set was "if pooled ≥ 1.08, seat 29's result is
general and I will say so".
**Pooled is 1.0980. The kill condition fired.** I was wrong, and wrong in the specific way the rule I wrote an
hour ago should have prevented: I assumed the *direction* of bench's bias from one prior case (19-C35, where bench
understated) and applied it to a different patch. **The bench-vs-real bias is not a constant sign; it is a property
of the patch.** 19-C35 understated (1.2 % vs 7 %); 19-C58 overstated nothing (9.4 % vs 9.8 %).

## Third instance of the small-sample trap, and the smoke number again
My **6-position smoke gave 13.19 %** against the true **9.80 %** at n=130 — **an overstatement of 35 %**, in the
same direction as 19-C56's 6-position smoke (21.5 % against 5.2 %, **4.1×**). **Noticed and not published**, and
this time the full run was already running before I read the smoke.

## The corrected rule (third revision, and the one I now believe)
> **Bench's bias is not directional — it is patch-specific.** Bench may understate (19-C35: 1.2 % vs 7 %),
> overstate, or match (19-C58: 9.4 % vs 9.8 %). **So "bench generalises" and "bench does not generalise" are both
> wrong as blanket rules; the only safe practice is to MEASURE the thing on real positions once if the number
> matters.** Bench remains valid for pins, determinism, ablation direction and structural counters — where the
> question does not depend on the position distribution at all.

## For the owner
**Do not ship the weight-column prefetch.** Three independent measurements (19-F10 8.1 %, 29-C4 9.43 %, 19-C58
9.80 % on real positions) agree it is slower, on 93 % of positions individually, with node counts unchanged — so
it is pure wasted per-node time. **This is now one of the better-supported negative results in the run.**
