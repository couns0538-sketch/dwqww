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

---

# ADDENDUM (same report) — root-window experiment AND the closing explanation from seat 19

## Part 1 — the bounded root-window experiment: 2043-2044 is ALSO ruled out

**What was built.** `make_variant_d.py` → `FORGE_swarm06_asymmetry_rootwindow.patch.txt` (applies with
`patch -p1`, no fuzz, verified on a clean 6b98f217 tree). At a root node every root move is searched **once with
a true full window** (`-Infinite, Infinite`), bypassing the PVS/LMR/full-depth-re-search ladder, and the root
**never accumulates alpha and never takes a fail-high cutoff** (`src/search.cpp:2039-2060`). Nothing else changes.

**The three numbers asked for** (same 353 G positions, depth 10, S14, Threads 1, Hash 16):

| build | mismatched bestmoves | score differences | total nodes (353 pos, both sides) |
|---|---|---|---|
| base (6b98f217) | **101** of 353 | **334** of 353 | **14,181,783** |
| root-window purity (variant D) | **149** of 353 | 335 of 353 | **445,115,035** |

- **Symmetry did NOT return** — it got substantially worse (101 → 149 mismatched bestmoves).
- **Node cost: 31.4× the base tree** (+3,038.6 %). Root-window purity is astronomically expensive and buys
  no symmetry.
- Depth-1 node-count equality did improve (15/40 → 24/40), and depth-2 scores improved (30 → 32 of 40), so the
  root window *is* doing what it was meant to do locally — it simply does not make the whole search symmetric,
  because the asymmetry does not come from the root window.

**Conclusion, stated plainly as requested: `src/search.cpp:2043-2044` (accumulated root alpha) is ruled out as
the cause. Together with the tie-break (ruled out) and the aspiration window (ruled out), the three mechanisms
I could name are all refuted by direct experiment. I am stopping this thread.** The measured facts S-F6/S-F7
(the search is not colour-symmetric; the difference is not in any root subtree when searched alone) stand and
are worth keeping; the *explanation* remains unknown, and I am not going to offer a fourth guess.

Honesty: variant D fails the pins grossly (bench 11 12,742,773 · bench 13 31,196,587 · bench 16 125,106,216;
perft 5 unchanged at 4,865,609). Speed 1,760,294 / 1,712,047 / 1,781,458 nps on bench 11 — similar nps to base,
but 14× the nodes, so wall time is ~14× on bench 11. **Evidence only, not a candidate.**

## Part 2 — why the three tie-break variants could never have passed the pins (seat 19's 19-F15)

Seat 19 proved something that closes this whole episode and that I should have known before writing the patch:

> **19-F15** (seat 19, area 9): tie order in `MovePicker::pick_best`'s `std::sort` is **load-bearing** for the
> node counts. Replacing `std::sort` with `std::stable_sort` — **same range, same comparator, only the algorithm
> changed** — moves three of the four honesty numbers: bench 11 312,866 → 292,627, bench 13 862,329 → 939,494
> (+8.9 %), bench 16 3,024,920 → 2,925,608, with perft 5 unchanged at 4,865,609.

Verified on seat 19's own branch (`FINDINGS.md`, `19-F15`, evidence `bash forge-combo29/swarm/19/job2/headroom.sh
stable forge-combo29/swarm/19/pickbest/edit_stable_sort.py`), not taken on trust from the message.

**This closes S-C1 with a mechanism.** My variants A/B/C all changed tie order — that is what a tie-break *is* —
and 19-F15 shows that changing tie order in this exact sort necessarily moves the benches, which are the honesty
pins. So:

1. **No symmetry fix through the `pick_best` ordering route could ever have kept the pins.** The failure was not
   a flaw in how I wrote the patch; it was structural. Any correct tie-break would have been rejected by the
   honesty gate, exactly as mine was, for a reason that has nothing to do with symmetry.
2. **The direction is not even predictable**: bench 11 and 16 move *down* while bench 13 moves *up* (+8.9 %).
   So the effect cannot be compensated or reasoned about per-depth.
3. **The pins are therefore not purely a property of the source.** bench 11/13/16 depend on libstdc++'s current
   `std::sort` tie behaviour — an implementation detail of the standard library, not of the engine. A GCC or
   libstdc++ upgrade that changes introsort's internals could silently break the honesty gate on unmodified
   source, and would look like an engine regression. That is a **build-reproducibility risk** and it applies to
   every seat's HONESTY.txt, not just mine.
4. It also means **tie order is a genuine speed lever** (seat 19's area): 8.9 % on bench 13 from the sort alone,
   in one direction, though not a controllable one.

### Corrected accounting of my failed fix

| hypothesis | test | verdict |
|---|---|---|
| `std::sort`/`pick_best` tie-break is the cause of the asymmetry (my S-F8) | variants A, B, C built and measured | **REFUTED** (101 → 114 / 104 / 117 mismatches) |
| ...and could at least be made without breaking the pins | 19-F15 + my own honesty runs | **IMPOSSIBLE IN PRINCIPLE** — any tie-order change moves the benches |
| the aspiration window | `probe_aspiration.py` | **REFUTED** (34/40 → 28/40 bestmoves) |
| accumulated root alpha (2043-2044) | variant D above | **REFUTED** (101 → 149 mismatches, 31× nodes) |
| **cause of the asymmetry** | — | **UNKNOWN**; I stop here rather than guess a fourth time |

## Findings for this addendum

**F4 (addendum) — root-window purity does not restore colour-mirror symmetry and costs 31.4× the nodes
(101 → 149 mismatched bestmoves on 353 G positions at depth 10). Accumulated root alpha is ruled out.**
Shows again: `python3 job3/harness_search.py /tmp/bld/vD/forge job3/G_353.fens job3/out_G_vD.txt job3/meta_G_vD.txt 10 S14`
then `python3 job3/analyse_search.py job3/out_G_vD.txt`.

**F5 (addendum, closing S-C1) — the tie-break route was impossible in principle: per seat 19's 19-F15, tie
order in `pick_best`'s `std::sort` is load-bearing for bench 11/13/16, so any tie-break change moves the honesty
pins by construction. The pins therefore depend on libstdc++'s current tie behaviour, which is a
build-reproducibility risk for every seat.**
Shows again: seat 19's evidence command above, plus `honesty_variants.txt` in this folder.

## What I did NOT do (addendum)

- I did not chase the asymmetry further. Three named mechanisms have now been refuted by direct experiment; a
  fourth guess without a new diagnostic idea would be exactly the "guess presented as a result" the rules warn
  about.
- I did not re-run variant D on the R set or at other depths beyond the 1–4 curve — the 353-position depth-10
  answer is the one asked for, and at 31× nodes a wider run is not proportionate.
- I did not test whether a *different* sort implementation in the pins' own build (e.g. a GCC 14 build) reproduces
  the pins. That is a concrete way to test the reproducibility risk in F5, and it belongs to whoever owns the
  build matrix.
