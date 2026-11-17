# REPORT job73 — verifying my own live patch found a defect in the patch

Date: 2026-11-17 (see `job73/stamps.txt`)
Seat 07. Branch `for-fable-and-opus/swarm-07`.

## What I set out to do

07-F1's patch (`job55/shared_report_oneline.patch.txt`) is the **only** outstanding engine change
in my list after 07-C77. Task: verify it against the published PC r15 pins, because a one-line edit
to the emit loop is exactly the kind of change that can move a bench number silently.

## The pins were fine

All eight published PC r15 numbers unchanged, on both v1 and v2:

| regime | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| none | 312866 | 862329 | 3024920 | 4865609 |
| S14 | 242796 | 656517 | — | — |
| PC20 | 278024 | 587276 | — | — |

The patch touches the reporting path only, and identical pins are the positive evidence of that.

## But the patch had the same defect it was written to fix

v1 replaced the per-depth loop with one emit — correct, 64 fabricated lines became 1. **It emitted
at `max_depth`**, which is 64 when no depth is given:

```
v1:  go depth 12 searchmoves a1a8  ->  info depth 12 ... nodes 0
v1:  go searchmoves a1a8           ->  info depth 64 ... nodes 0
```

`depth 64` with `nodes 0` **is the self-contradiction 07-F1 is about** — a search that never ran
claiming a completed depth. v1 printed it once instead of 64 times, which is a much smaller version
of the same lie. A GUI or harness that sorts or filters on reported depth would rank a zero-node
non-search as the deepest thing it had seen.

I only found this because I ran the six zero-node paths on the patched build instead of trusting
that "1 line instead of 64" was the whole requirement. The patch header said *"each goes to 1 line"*
and that was true and insufficient.

## Revision 2

`job73/07f1_shared_report_v2.patch.txt` — reports **depth 0**, which is truthful: no iteration
completed.

```
v2:  go depth 12 searchmoves a1a8  ->  info depth 0 seldepth 0 score cp 0 nodes 0 ... pv
v2:  go searchmoves a1a8           ->  info depth 0 seldepth 0 score cp 0 nodes 0 ... pv
```

Verified on **seven** zero-node paths, each exactly one line and `bestmove 0000`:
`searchmoves` with no legal root move, empty `go searchmoves`, `go nodes 100 searchmoves <none>`,
an illegal move name, a mate root, a stalemate root, and `go searchmoves` with no depth limit
(`job73/raw_v2/zero_paths.txt`, 0 failures). All eight pins unchanged on v2
(`job73/raw_v2/pc_pins.json`). Applies to the PC r15 tree with `patch -p1 --fuzz=0`, exit 0.

## Build note worth writing down

The box's default `c++` cannot link — `cannot find -lstdc++`. Every configure attempt fails at the
compiler probe unless **`-DCMAKE_CXX_COMPILER=g++-13` is named explicitly**. I lost two builds to
this before noticing, and the second failure was worse than the first: a rebuild that reused a stale
`CMakeCache.txt` from a copied tree produced a binary **byte-identical** to the old one while
reporting `[100%] Built target forge` and `EXIT=0`. That is the header's own rule firing on me —
**the treatment was not applied** — and the tell was again an exact sha256 match.

## The rule

**A patch that fixes a symptom can reproduce the symptom's essence in reduced form.** v1's "1 line
instead of 64" was a real improvement and still asserted a completed depth in 0 nodes. When the
complaint is *"this number is a lie"*, the fix has to make the number true, not just make it rarer.
Check the surviving line's content, not only its count.

## Files

- `job73/07f1_shared_report_v2.patch.txt` — the deliverable (v2, depth 0)
- `job73/raw_v2/pc_pins.json` — eight pins, all OK
- `job73/raw_v2/zero_paths.txt` — seven paths, one line each, 0 failures
- `job73/raw_v2/v1_vs_v2.txt` — the depth claim before and after
- `job73/stamps.txt`
- binary `2db028fa9ade74d7c80110d6ab23c73bd06e43333305a10ec32615682b345939`
