# REPORT_next — the symmetry fix attempt: the tie-break hypothesis is REFUTED

Seat 06, area 6 (SYMMETRY). Follow-up requested after job 3: make the ordering deterministic with a
mirror-invariant tie-break, re-run the depth-10 test, report cost, and compare against the weaker variant.

## The answer, first, because it is the opposite of what was asked for

**I was wrong about the mechanism, and the patch proves it.** The complete mirror-invariant tie-break was built,
measured and it makes the asymmetry *worse*:

| build | depth-10 G bestmove mismatches | depth-10 G score differences | depth-1 node counts equal |
|---|---|---|---|
| base (6b98f217, unpatched) | **101 of 353** | **334 of 353** | 15 of 40 |
| tie-break only (`pick_best` scan + AVX chunk + `stable_sort` + `seeded_`) = variant C | **117 of 353** | **339 of 353** | **7 of 40** |
| tie-break without the `seeded_` rule = variant A ("weaker" but see below) | 114 of 353 | 327 of 353 | 12 of 40 |
| tie-break plus pre-ordering the generated list = variant B | 104 of 353 | 327 of 353 | not measured |

So the requested deliverable — "how many of the 101 mismatches and 334 score differences survive" — is
**all of them and a few more**. The count went from 101 to 117 (variant C). No fix, no improvement, and every
variant **fails the honesty gate** (see cost, below).

**Finding S-F8 in my FINDINGS.md is REFUTED by this work and is recorded as such** (`S-C1` in FINDINGS.md). The
`std::sort` tie-break is a real code smell — an unstable sort with a strict `>` comparator does leave equal-scored
moves in an arbitrary order — but it is **not** what causes the colour-mirror asymmetry.

## What the patch actually is (and why "stable_sort at the root" does not exist here)

The request said "`std::stable_sort` at the root". **There is no root sort in this engine.** The root goes
through the same `MovePicker` as every other node: `Worker::search()` at `src/search.cpp:1553` sets
`root_node = ss->ply == 0`, and the ordering of root moves comes from `MovePicker::next()` exactly as everywhere
else. The only `std::stable_sort` already in the file is for MultiPV line ranking
(`src/search.cpp:2518`), which is not move ordering. So "stable_sort at the root" was implemented as what it can
only mean here: the ordering inside the shared `MovePicker`. That is stated so the difference from the request is
not hidden.

The patch changes four places, all in `src/search.cpp`:

1. **A canonical tie key** in the mover's own frame:
   `tie_key(move) = ((from ^ 56) << 8) | (to ^ 56)`. The `^ 56` is the board flip without touching the side to
   move, so a position and its colour mirror give the same key for corresponding moves. **This is why a key of
   `move index` or raw move bits could not have worked**, as the request suggested: a raw index or raw square is
   *not* mirror-invariant, so it would be deterministic but would still order a mirror differently. I chose the
   relative-frame key deliberately, and recorded the reason.
2. **`pick_best`'s first-four scan** (`src/search.cpp:817-856`) breaks score ties by `tie_key`, including inside
   the AVX2 four-at-a-time chunk (the chunk now walks its equal maxima in index order instead of taking the first).
3. **The tail sort** (`src/search.cpp:858-860`) becomes `std::stable_sort` with the lexicographic
   `(score desc, tie_key asc)` comparator.
4. **`push_scored`'s `seeded_` rule** (`src/search.cpp:899-906`) — the piece my first attempt missed and the
   reason variant A is *not* actually "the weaker variant": it records the **first arrival** of the maximum score
   and hands that move out first, so with ties the winner was decided by generator order. Variant C adds the
   `tie_key` comparison there too.

Variant B additionally pre-sorts the generated list by `tie_key` in `sort_moves()`, the closest thing here to a
canonical base order feeding the picker.

**Which of the two does the work: neither.** Variant A (without the `seeded_` rule) is not a weaker version of the
same idea — it is an *incomplete* one, and its numbers (114 mismatches) are not better than the complete version's
(117) in any meaningful sense; both are worse than the unpatched base (101). There is no ordering of the answers in
which the tie-break helps, so the comparison the request asked for has no winner to report.

## The decisive experiment that explains why the tie-break could not work

`probe_root_moves.py` searches **each root move on its own** with `go depth 1 searchmoves <move>`, for a position
and its colour mirror, and compares the node counts of corresponding moves. Position
`R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1`:

- whole-position depth-1 search: **25 nodes** vs the mirror's **30 nodes** — it differs;
- but **0 of 18** root moves have a different node count from their mirror (every one matches exactly:
  2/2, 2/2, 2/2, 2/2, 2/2, 3/3, 3/3, 7/7, 3/3, 3/3, 3/3, 3/3, 3/3, 5/5, 5/5, 3/3, 3/3, 3/3).

**No single move's subtree differs, yet the sum differs.** That is only possible if the difference is produced by
the *accumulation across the root loop* — alpha-beta's cutoffs and the aspiration window acting on the sequence of
root moves as a whole — not by any node's internal ordering. A tie-break inside the picker cannot touch that,
which is exactly what the measurements show. The honest conclusion is that my job-3 finding S-F7 (the depth-1
node-count evidence) is correct as a *measurement* but my S-F8 *explanation* of it was wrong: the order dependence
is real, but it is not the sort's tie-break.

## Cost, honestly

**Every variant fails the honesty gate. None of them may be used.**

| build | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| base | 312866 | 862329 | 3024920 | 4865609 |
| variant A | 304239 | 721622 | 2689823 | 4865609 |
| variant B | 363736 | 1016091 | 2746595 | 4865609 |
| variant C | 321734 | 859647 | 2768005 | 4865609 |

perft 5 is identical everywhere (4865609) — the move generator is untouched, as it should be. **bench 11, 13 and
16 all change on every variant**, which is expected for a change that reorders the tree: a different order is a
different tree. But the pins require them unchanged, so **the patch is not a candidate**, and I say so rather than
presenting a passing-looking number.

Speed (bench 13, three runs each, from `nps_bench13.txt`):

| build | nps runs | median nps | nodes |
|---|---|---|---|
| base | 2,000,763 / 2,029,009 / 1,982,365 | 2,000,763 | 862329 |
| variant A | 1,884,130 / 1,904,015 / 1,899,005 | 1,899,005 | 721622 |
| variant C | 1,809,783 / 1,848,703 / 1,678,998 | 1,809,783 | 859647 |

So the patch is **slower** (about −5 % to −9 % nps) as well as less symmetric. The `stable_sort` plus the extra
`tie_key` comparisons cost more than the reordering saves.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read the ordering code and find the real site | done | this report; `src/search.cpp:817-906` | no root sort exists; ordering is in `MovePicker` |
| canonical tie key in the mover's frame | done | `fix/make_variant_c.py`, patch | `(from^56, to^56)` |
| `std::stable_sort` on the tail + tie-break in the first-four scan | done | `FORGE_swarm06_asymmetry.patch.txt` | applies with `patch -p1`, no fuzz |
| `seeded_` first-arrival rule patched (the piece variant A missed) | done | same patch | variant C |
| patch applies cleanly to a clean 6b98f217 tree | done | `/tmp/ptest2` dry run | "APPLIES CLEANLY", no fuzz |
| weaker variant (without `seeded_`), measured | done | `FORGE_swarm06_asymmetry_tiebreak_only.patch.txt`, `table_G_vA.txt` | 114 mismatches, also applies cleanly |
| re-run depth-10 G symmetry, complete tie-break | done | `table_G_vC.txt` | **117 of 353 mismatch (base 101)** — worse |
| re-run depth-10 G symmetry, weaker variant | done | `table_G_vA.txt` | 114 of 353 — worse |
| depth curve, variants | done | `table_vA.txt`, `table_vC.txt`, `table_base.txt` | depth-1 node equality 15 → 12 (A) / 7 (C) |
| honesty pins on every variant | done | `honesty_variants.txt` | **all three FAIL** (bench 11/13/16 change); perft 5 identical |
| speed before/after | done | `nps_bench13.txt` | base 2.00 M nps, A 1.90 M, C 1.81 M — slower |
| localise why the tie-break cannot help | done | `probe_root_moves.py`, `root_moves_R7.txt` | 0 of 18 root subtrees differ while the whole search differs |
| correct my own finding | done | this report, FINDINGS.md `S-C1` | S-F8 refuted |

Commands that show each result again:

```
python3 fix/make_variant_c.py /agent/repos/base/forge-combo29/src/search.cpp /tmp/vC/src/search.cpp
cd /tmp/ptest && patch -p1 --dry-run < fix/FORGE_swarm06_asymmetry.patch.txt
python3 job3/harness_search.py /tmp/bld/vC/forge job3/G_353.fens job3/out_G_vC.txt job3/meta_G_vC.txt 10 S14
python3 job3/analyse_search.py job3/out_G_vC.txt
python3 fix/probe_root_moves.py ~/bld/release/forge "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1"
```

## Findings

**F1 (correction) — the `std::sort`/`pick_best` tie-break is NOT the cause of the search asymmetry. The complete
mirror-invariant tie-break makes both symmetry and speed worse.** This refutes my own S-F8; recorded as `S-C1`.

**F2 — the depth-1 whole-position node-count difference is not in any move's subtree: 0 of 18 root moves differ
when searched alone, while the whole-position search gives 25 vs 30 nodes.** So the asymmetry is created by the
root loop's accumulation (cutoffs, aspiration across the root sequence), not by per-node move ordering. This is
the sharpest available statement of where the asymmetry lives.
Shows again: `python3 fix/probe_root_moves.py ~/bld/release/forge "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1"`.

**F3 — a mirror-invariant tie-break cannot be free: `stable_sort` plus a `tie_key` comparison costs 5-9 % nps and
changes the bench node counts, failing the honesty pins.** Worth knowing before anyone tries this repair again.

## Suspicions, not proven

- ~~That the accumulation effect is the aspiration window.~~ **TESTED AND REFUTED** after writing the paragraph
  above (`probe_aspiration.py`, `aspiration_d8.txt`, depth 8, 40 positions):
  S14 default `AspirationDelta 18` mirrors 34/40 bestmoves with 1/40 scores equal; `AspirationDelta 200`
  (near-full window) gives **28/40 and 2/40** — worse, not better; adding `AspCappedReopen false` and
  `AspArmLate false` changes nothing (28/40, 2/40). Node-count equality is 0/40 in all three. So widening the
  window does not restore symmetry, and the asymmetry is not an aspiration artifact.
- The remaining candidate, not tested: the root loop's own accumulation of `alpha` from move to move
  (`best_score > alpha → alpha = best_score`, `src/search.cpp:2043-2044`) combined with the order in which the
  root walks its moves. That is the mechanism the probe localises to, but I have not isolated it further. Whoever
  picks this up should start there, not at the sort.

## What I did NOT do

- I did not run the 353-position depth-10 test with the aspiration window widened; I ran 40 positions at depth 8
  (`aspiration_d8.txt`), which is enough to refute the aspiration hypothesis but is not the full set at depth 10.
- I did not commit a patch as a *candidate*: all variants fail the honesty pins, so the patches are evidence of
  the attempt, not a proposed change. Both `.patch.txt` files are present because the request asked for them and
  because a refuted hypothesis is worth keeping as a reproducible negative; the report says plainly they must not
  be applied.
- No threading, no sanitizer, no R set for this follow-up (the question was about the G set and the 353/101/334
  numbers).

## What I am NOT sure about

- Whether Opus wants the asymmetry fixed at all. If it is an artifact of aspiration plus cutoffs, "fixing" it means
  giving up speed for a property that does not make the engine stronger.
- Whether a `tie_key` in a different frame (e.g. rank-first rather than file-first) would fare differently. I doubt
  it: the probe shows no per-move subtree differs at all, so any per-node key is the wrong lever.

## Times

`date -u` lines in `fix/stamps.txt`.
