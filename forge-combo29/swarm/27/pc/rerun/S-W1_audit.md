# S-W1 audit: every harness checked for the zero-info-line guard

Requested by the coordinator after seat 19 showed that a `bestmove` with zero `info depth` lines can be
recorded as if it were a search. Done by reading each harness's parse path, then **proving a guard fires**.

## Result: 15 of 15 harnesses guarded

| harness | guard |
|---|---|
| `check_05f58_mate_pv.py` | `if not infos: raise Missing(...)` |
| `check_15f35_clock.py` | added in this audit (`GUARD (S-W1)`) |
| `check_16f6_book.py` | added in this audit |
| `check_19f46_nodes.py` | `if not infos: raise Missing(...)` |
| `check_20f11_pc.py` | pre-existing |
| `check_29f3_pc.py` | **bench-line variant** added in this audit (it parses `info string bench depth`, not `info depth`) |
| `check_30f9_pc.py` | pre-existing |
| `check_50move_defect.py` | pre-existing |
| `check_clock_ignored.py` | added in this audit |
| `deep_mate_depth_sweep.py` | pre-existing |
| `label_reproducibility.py` | pre-existing |
| `pc20_rerun.py` | pre-existing |
| `process_policy.py` | added in this audit |
| `softnodes_probe.py` | added in this audit |
| `softnodes_vs_clock.py` | pre-existing |

Six harnesses were unguarded; five used `last = infos[-1] if infos else ""`, which does not abort but
silently produces a `None` score and node count — the exact failure class. `check_29f3_pc.py` needed a
different guard because it reads a bench line rather than an `info depth` line.

## The guard is proven to fire, not just present

A fake engine that answers every `go` with `bestmove a2a3` and **no info line** was run through
`check_clock_ignored.py`:

```
File ".../check_clock_ignored.py", line 92, in go
    raise Missing("no 'info depth' line for this search (zero-info-line signature; row aborted)")
Missing: no 'info depth' line for this search (zero-info-line signature; row aborted)
```

So the abort path is live. A guard that has never been shown to fire would be an assertion about code
rather than about behaviour.

## Which of my recorded results could have come from an unguarded row

The six unguarded harnesses produced these recorded results:

| result | could a zero-info row have slipped in? |
|---|---|
| S-C11 (clock drain) | **No** — it aggregates per-move wall times and node counts; a zero-info move would carry `nodes: None` and the median computation filters on `if r.get("nodes")`, so such rows were excluded, not counted. But the *move list* would be wrong if a fabricated move were played, so the run is worth the re-check below. |
| S-C11b (process policy) | Same shape as S-C11 — medians filter on node presence. |
| S-C14 (pos-90 warm) | **No** — every row reports explicit nodes 79,980 → 1,324, i.e. real searches. |
| S-C10 (book reachability) | **No** — the book rows are distinguished by `info string book move`, which is a different signature, and the analysis rows all carried info lines. |
| S-C17 (this board) | **WITHDRAWN** separately (S-W1) — the arithmetic makes the score impossible. |
| S-N2 (softnodes + clock) | **No** — all 12 cells reported node counts. |
| S-C9 (bench intercept) | `check_29f3_pc.py` was unguarded; the fit used reported `time` and `nodes` from a bench line, and a missing bench line would have raised a `StopIteration` on `next(...)` rather than recording a value — so no silent row. Now guarded explicitly. |

**What I am not claiming:** that the medians in S-C11/S-C11b are unaffected in every detail. A fabricated
move inside a long self-play game would corrupt the *move sequence* even if its node count were filtered
out, and I have not re-run those games with the guard in place. **That is the honest residual, and the
cheap fix is to re-run them now that every harness aborts on zero info lines.**

## The rule, now in METHOD_NOTES.md

A search with zero `info depth` lines aborts the row. It is the one error class that produces plausible
numbers, because a fabricated `bestmove` is a legal-looking move drawn from the generator's own order.
Two seats have now been caught by it.
