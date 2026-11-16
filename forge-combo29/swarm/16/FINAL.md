# SWARM SEAT 16 — FINAL REPORT (area 6, SYMMETRY)

Written at 2026-11-16T23:20Z. The 12-hour window ends 2026-11-17T10:19Z; this file is the consolidated record and
is kept current until then. Every number here is the pasted output of a committed script; every build is named.

**Builds used (all verified before use):**

| build | what it is | pins (none / S14 / PC20) |
|---|---|---|
| base | 6b98f217, release, g++ 13.3.0, `-march=x86-64-v4` | 312866 / 862329 / 3024920 / perft 5 4865609 |
| PC r15 | file 5 patch (sha256 `d6bd72c531f785f4` verified) + `-DFORGE_MATE_ALPHA_GUARD=1` | 312866 / 242796 / 278024 — all match file 5 |
| sym-PSQT | base with PSQT symmetrised by my own script | experiment: pins not claimed |
| PC sym-PSQT | PC r15 with PSQT symmetrised | experiment: pins not claimed |
| FW / REV | full-window root / reversed move list, base tree | experiment: pins not claimed |
| PC REV | PC r15 + reversed list | experiment: pins not claimed |

**Settings vocabulary:** `none` = default options; `S14` = the 14 tunables of file 1; `PC20` = S14 +
CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook false.
**Every score in this report is Threads 1, Hash 16** (the swarm rule). Harnesses that could have relied on a
default thread count were checked and, where they did, given an explicit `Threads 1`.

---

# PART 1 — THE AREA-6 CHAIN, AS ONE BLOCK

This is the organised result of the whole area: what the asymmetry is, what causes it, and which fix works on
which half. Each row names its finding id; the ids also appear in my FINDINGS.md with raw-file paths.

**1.1 The two asymmetries are DIFFERENT phenomena, and only one is fixable.**

| asymmetry | what it is | cause (established) | fixable? |
|---|---|---|---|
| **colour mirror** (position vs python-chess `mirror()`: colours swapped, board flipped) | the same position from the other side — this SHOULD be symmetric | **search order**, below the root; not the evaluation | **NO** — nothing I tried fixes it (see 1.5) |
| **left-right** (position vs `flip_horizontal`) | a DIFFERENT position, not the same one seen from the other side | **the tuned PSQT table**, entirely | **YES** — symmetrising the table takes it to 0 |

`S-F3`, `S-C3`, `S-F25`. The left-right half is settled by S-C3 (328/334 → 0/334 hce differences when the table is
symmetrised, perft 5 unchanged). The colour half is settled by S-F25 (the same table change leaves the colour
score gap at 11 cp → 19 cp median, i.e. no improvement) plus S-F23 (the gap does not shrink from depth 6 to 12).

**1.2 The evaluation itself is exactly colour-symmetric — so the gap cannot come from it.**

`S-F1`, `S-C2`: `eval` returns identical hce/nnue/total for a position and its colour mirror on all 853 pairs I
ran (353 G + 500 R), and on 25,532 pairs across four eval configurations. `S-F10`: `eval` also carries NO state,
so eval comparisons need no process discipline (5,853 pairs in ONE process gave 0 differences).
`S-C5`: `eval` is side-to-move relative, so a mirror must read the SAME number — a negation-based checker reports
853 false asymmetries (the trap seat 20 found).

**1.3 The search is not symmetric, and the asymmetry is created BELOW the root.**

`S-F4`: depth 10 over 353 G pairs — 101/353 bestmoves fail to mirror, scores equal on only 19/353.
`S-F8` (with `S-F12`): a full-window root (no accumulated alpha, no root fail-high) **restores exact node
symmetry at depth 1 only** (65 vs 65, from 25 vs 30) and fails from depth 2, at 2.4×–11.1× the nodes.
So root alpha accumulation is the whole story at one ply and none of it thereafter.
**AGREES with seat 06's S-F17** (same experiment, symmetry made worse, 101 → 149 mismatches at 31.4× nodes) and
is explained by its **S-F18/S-F19** (fresh process, original-first and mirror-first all identical, so the state is
carried WITHIN a single search). Two independent refutations settle the hypothesis.

**1.4 The named mechanism: the generated move order does not mirror.**

`S-F11`: the engine's move generation order is not mirror-corresponding in **40 of 41 positions**
(`g3f1 g3h1 g3e2 g3e4` against the mirror's `g6e5 g6e7 g6f8 g6h8`), and `pick_best` breaks ties by the first
maximum with **no randomness anywhere in search.cpp** — so mirror positions walk different trees deterministically.
`S-F12`: reversing the generated list **changes the node counts but does not equalise the pair** — the gap
widens (depth 2: 336/334 gap 2 → 320/357 gap 37). So order is **necessary but not sufficient**.
`S-F21`: the mechanism **transfers unchanged to the PC build** (same node counts on the same probe).

**1.5 What does NOT fix the colour gap (all tested, all negative).**

| tried | result | finding |
|---|---|---|
| full-window root (no root alpha) | depth 1 fixed, depth ≥2 not; 11× the nodes | `S-F8` |
| reversing the generated move list | counts change, gap widens | `S-F12` |
| symmetrising the PSQT table | 11 cp → 19 cp median, no improvement | `S-F25` |
| Hash 1 / 16 / 2048 | identical, 351 vs 363 at depth 2 — table size irrelevant | `S-F11` |
| zeroing history bonuses, history pruning off, LMR-history down | gap narrows 12 → 3 nodes, never closes | `S-F11` |
| deeper search | median gap flat 14/17/11/20 cp at depths 6/8/10/12 | `S-F23` |
| the four PC options | see 1.6 | `S-F13`, `S-F20`, `S-F22` |

**1.6 On the PC build (r15) under PC20, the asymmetry survives — and the settings, not the code, add to it.**

`S-F13`: at depth ≤2 only 2/20 pairs have equal node counts and 14/20 equal scores.
`S-F14`: full 353 pairs at depth 10 — **120/353 bestmove mismatch, 0/353 node-equal, 22/353 score-equal.**
`S-F15`: **the split** — swapping the code alone (base → PC at fixed S14) moves the count 101 → **102**; the PC20
**settings** take it to 120. So the extra asymmetry is the options, not the PC code.
`S-F20`: **TtPruneV2 alone gives 113** of 353 (verified with the other four explicitly off; that run is identical
to the default-off run on 353/353 positions). Turning it off restores the base level.
`S-F22`: but the lever is narrow — it changes **which** positions mirror, not **how far** scores diverge
(score-equal 20 → 19; median gap 18 → 19 cp). **It is not a strength lever.**

**1.7 One-line answer for the owner.**

The colour asymmetry is real, survives every settings change, is not the evaluation, is not fixable by any
search-window or table change I tried, and is inherited from the move-generation order; `TtPruneV2` moves the
*move-mirroring count* back toward base level but not the ~18 cp score disagreement.

---

# PART 2 — THE PC PATH (what the owner's PC actually does)

**2.1 `go softnodes 2000` (self-play).** `S-F16`: fully **deterministic** (1 distinct result over 20 runs on each
of 4 positions), always stops at a **finished depth**, and **overshoots the budget** — 2,314–4,121 nodes at
N=2000 (median 1.66×). `S-F17`: the overshoot is bounded **relatively** (~2.06× max over 12 positions, no
counterexample found while hunting one) but **not absolutely** — at N=200000 one quiet position reaches 353,498
nodes (1.767×).

**2.2 The match clock, 6 s + 0.06 s.** `S-F18`: the **move** is reproducible (1 distinct bestmove over 20 runs on
each of 4 positions; bestmove inside its own PV 80/80) but the engine uses only **156–325 ms** of the 6060 ms
allowed. `S-F19`: that fraction is a **time-manager soft limit, not a hardware ceiling** — across a 30× clock
range (1/3/6/30 s) it uses 28/72/159/1312 ms, i.e. 2.38 %–4.33 % every time, scaling with the clock instead of
hitting a ceiling.
`S-F26` (ten games, 600 moves): the fraction **drifts upward** across a game — median 3.64 % (first third) →
4.32 % → **4.70 %** (last third) — and the per-move maximum reaches **21.90 %**, correcting my earlier 2.6–5.3 %.
`S-F29` (ten more games from varied starts) extends the extremes to **0.02 %** (a move that took essentially no
time) and **32.24 %** (a tactical position), so the full observed band is **0.02 %–32.24 %** with a **median of
about 4 %** — quote the median. **0 overruns in 1,000 moves across both studies.**
`S-F28`: with an **identical** 6000 ms clock every move the engine's own use ranges **166–416 ms (2.51×)**, so
"6 s per move" does not buy a consistent effort; `go movetime` does not leak into a following clock search.

**2.3 The match node budgets 20000 / 50000 / 250000.** `S-F24`: **0 illegal moves in 120 searches**; the move is
identical at all three budgets on 31 of 40 real-game positions; the 8 that change are ordinary depth effects
(largest +125 cp from the 20k budget to the 250k one, one −70 cp self-assessment drop in a lost position). No
blunder found at any real budget.

**2.3b Two measurement-discipline results that others can use directly.**
`S-F6`: the built-in book **cannot affect an analysis search** — `src/uci.cpp:524-528` probes it only when
`game_search` holds, i.e. only for a `go wtime/btime` or `go movetime` search, never for `go depth`, `go nodes` or
`go infinite`. Verified twice over: 3 opening positions at depth 10 produced no book line, and 30 G positions gave
identical depth-10 bestmove and score with `OwnBook` true vs false. So analysis harnesses do not need to disable
the book (they should anyway, and mine now do).
`S-F9`: my published symmetry numbers are **not a warm/cold artefact**. On 12 mirror pairs, COLD (fresh process per
search) and WARM (one process with `ucinewgame` before each search) give IDENTICAL verdicts (bestmove mismatch
2/12, score mismatch 12/12), while the WRONG discipline (nothing between searches) gives a different count (10/12)
— so the confound is live and would have changed the number, and my runs escaped it. `eval` is additionally
stateless (S-F10), so eval comparisons need no process discipline at all.

**2.4 Self-play diversity — and the fix, which is simple.** `S-F27`: ten deterministic self-play games from the
same start produced only **THREE distinct final positions — seven of the ten identical** — because the engine is
fully deterministic at Threads 1 with fixed limits. Not a defect; a consequence: self-play from one fixed start
re-collects the same game. The one diverging game diverged only because millisecond clock drift occasionally
changed the depth reached.
**`S-F29` answers the actionable question: varying the start is SUFFICIENT.** Ten games from **ten different
real-game positions** gave **TEN distinct final positions and TEN distinct move sequences** (0 illegal moves,
0 overruns). So the advice to the owner is simply **vary the openings** — determinism does not prevent varied
starts from producing varied games, and the earlier convergence was entirely the fixed starting point, not a
deeper property of the search. If the training loop already varies openings there is nothing to do; if it plays
one start many times, that is the one change worth making before the next data run.

---

# PART 3 — CHECKS OF OTHER SEATS' FINDINGS

| id | verdict | one line |
|---|---|---|
| `S-C1` | CONFIRMS seat 06 S-F2 | ep-square FEN refusal, exact message reproduced; found a SECOND message (`invalid en-passant square`) the finding omitted, and that a refused FEN keeps the previous position |
| `S-C2` | CONFIRMS seat 06 S-F1 | colour symmetry on 25,532 pairs across 4 configurations; DeadMaterial changes 30/30 dead-material boards but 0/353 game positions |
| `S-C3` | CONFIRMS seat 06 S-F3 | PSQT symmetrisation takes hce to 0/334; **also corrected my own r=0.35 claim** (my predictor was MG-only against a phase-blended eval) |
| `S-C4` | CONFIRMS seat 06 S-F5 | `total = hce + nnue` on 745/745; exactly 3 positions cancel to bit-identical totals, each with Δhce = −Δnnue |
| `S-C5` | CONFIRMS seat 20 S-F14 | `eval` is side-to-move relative: 4211 / 4211 / −4182 exact; a negation checker reports 853 false asymmetries |
| `S-C6` | CONFIRMS + EXTENDS seat 06 S-F12 | 25 vs 30 nodes reproduced; beyond it, the per-move counts **sum to 57 on both sides**, so the difference is entirely the root loop |
| `S-C7` | **RECONCILED** with seat 28 S-F1 / seat 08 08-F2 | the M−10 rule IS true of the **wall clock** (plan + 0.45–0.57 ms in 6/6 rows) and false only of the **kept iteration** (2–45 ms below plan); my original refutation measured the iteration field and called it the stop — **my error** |

**Measurement-integrity audit** (`REPORT_audit.md`): all 7 confirmations + honesty re-verified **8/8** under a
parser that RAISES on a missing line. None of my data hit the pipelined-`quit` trap (0 occurrences of
`bestmove a2a3`; job-3 re-run 12/12 identical bestmove and score with real node counts).
`S-F7` records the three ways my own audit harness reproduced seat 19's vacuity bug (wrong executable, discarded
setup output, field-position parsing) — all caught only because the parser was made to raise.

---

# PART 4 — WHAT I GOT WRONG, IN WRITING

**Nine self-corrections are listed below — two of them were refutations of my own published numbers by my own
later work, three were bugs in my own harness code, and one was an inverted sign that made a rook-winning move
score as the worst blunder of a run. A reader who sees only the successes in Part 1 should weigh them against
this list.**

1. **S-C7** — I called the kept iteration's `time` field "the stop". Seat 08's reconciliation was correct.
2. **S-F3 (mine)** — I claimed PSQT explained only r=0.35 of the left-right difference; my predictor was MG-only
   against a phase-blended evaluation. My own S-C3 then refuted me.
3. **P1 of `softnodes/stress`** — I predicted a quiet position would exceed the 2.06× overshoot bound. It did not.
4. **P3/P4 of `softnodes`** — I predicted a 10–60 % overshoot and that it would not grow with N. Actual maximum
   was 106 %, and at N=200000 one position reached 1.767×.
5. **P4 of `nodebudget`** — I predicted no budget change would improve by more than 100 cp; idx 12 improved 125.
6. **P3 of `clockseq`** — I predicted identical-clock variation within 2×; measured 2.51×.
7. **First `clockseq` run** — my harness never sent `position`, so move 2 answered from startpos and failed its
   own legality check. The harness caught it; I fixed the harness, not the conclusion.
8. **`selfplay_cost`'s cost sign was inverted** (`S-F30`) — I computed `score(low) − score(ref)` from the mover's
   view, so a POSITIVE value meant the low budget was BETTER, not worse. Every sign in my first summary was
   backwards. Caught only because the largest "cost" was `h8h1`, a move I already knew **wins a rook**; verified at
   depth 14, then corrected throughout. A result that contradicts something you already know is the cheapest
   available bug detector.
9. **First `loud_reverify` run** — three of my eight checks reported NOT VERIFIED because of bugs in MY audit code
   (wrong build passed, setup output discarded, `seldepth` parsed as nodes), not in the findings. Fixed, then 8/8.

# PART 4b — TRANSFERABLE: ONE SCRIPT THAT CATCHES THE SILENT RECORD-LOSS FAULTS

A wrong relative path in an append (`cat >> ../../FINDINGS.md`) silently creates a file one directory short of
intent, and `git add <dir>` stages it — so 20 of my findings sat in four files while my own FINDINGS.md stopped at
S-F15. Nothing errored. The checks that catch it are now one runnable script:
**`forge-combo29/swarm/16/check_folder.py`** (`python3 check_folder.py 16 /agent/repos/dwqww`):

1. **Table well-formedness** — every `| S-` row must split into exactly **4 fields for a C-row** or **5 for an
   F-row**. This catches a pipe inside a cell (which silently shifts every later cell) AND reports the id gaps a
   stray row leaves behind. This check is the novel part and the one I would keep.
2. **Nothing staged outside your folder** — `git log --diff-filter=A` from your seat commit, which is stronger than
   inspecting the working tree, because a stray file that was once staged still appears after deletion.
3. **Text-only** — no NUL bytes, no invalid UTF-8.

**It was validated against planted faults**, because a green result from an unchecked script is worth nothing (the
seat-19 rule applies to audits too). In a scratch repository I planted both failures I had suffered — a row
containing `median |gap|` and a `FINDINGS.md` outside the seat folder — and the script reported both, with the exact
fields and the stray path. On my real folder it prints `34 rows, 34 ids, malformed none, OUTSIDE your folder: none,
non-text 0, ALL CHECKS PASS`.

Full write-up, including two same-family traps I hit (a pipe inside a table cell, and `grep -c` with an alternation
pattern miscounting twice), in **`forge-combo29/swarm/16/WARNING_stray_paths.md`**.

# PART 5 — WHAT I DID NOT DO

- No sanitizer builds anywhere. Nothing in this report is a memory-safety claim.
- Did not use the PC's trained net (not shared); every evaluation-dependent question here is the built-in eval.
- Did not read the time manager, and the clock findings describe behaviour, not cause.
- Did not prove the generation order is *sufficient* — only necessary (S-F12), and the correct next transform
  would be a mirror-order permutation, not a reverse.
- Did not run the PC build's 353-pair sweep under S14 alone (to isolate code vs settings at that scale) — though
  the S-F15 depth-10 cells cover the same ground.
