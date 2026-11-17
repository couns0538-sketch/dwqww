# forge-combo29 — findings and recommendations for the owner

Consolidated from the swarm run of 2026-11-16T22:20Z → 2026-11-17T10:08Z. Every figure here is
traceable to a finding in one of the `swarm/*` branches of `couns0538-sketch/dwqww`.

**One thing to know before any figure in this report: the gate is narrower than it looks.** Every number
here was accepted only if four `bench` pins reproduced, and those pins have now been audited. **They move
when an eval or search constant changes and they do not move for anything else** — 5 of 5 mutants that
should move them do, 5 of 5 source-only mutants leave them untouched, and **6 of 9 real behaviour changes
pass a green 4/4**, including `Threads` and the drawn-root bail. So **"pins matched" means "this change is
invisible to this instrument", never "this change is safe"**, and the two are only distinguishable where a
probe proves the change was live. The measurement is in §6, the blind-spot list in §10.

**A companion file enumerates the whole run as a matrix rather than an argument**:
[`test-matrix.md`](test-matrix.md) — **130 rows**: 29 areas tested and correct, 30 tested and wrong, 15
tested with a conditional answer, 21 never tested (each with the reason), and **35 instruments in this
audit that reported something false**, with what caught each one. Start there if you want the checklist;
start here if you want the reasoning.

**Start here — the ten decisions, in the order they cost you if you get them wrong.**

| # | decision | verdict | section |
|---|---|---|---|
| 1 | NNUE weight-column prefetch patch | **do not ship** — 8.1–9.8 % slower on real positions across **four independent measurements**, 90–93 % of positions individually slower, node counts identical. A **fifth** attempt by the coordinator, deliberately trying to refute it, agreed in direction (**5.5% fewer nodes at fixed time**) but is weaker than the rest and is not folded into the headline | §1 |
| 2 | Drawn-root bail (a legal move is played without being searched) | **ship both patches, but for a narrower reason than this report first gave.** They compose byte-identically, cost 5–10 µs on a drawn root and never run on 125 of 125 ordinary roots — **but on 2,457 real drawn roots the repair changes the MOVE in 0 of them**, because it only cancels when the mover has a mate in one, which real drawn roots never have. **It fixes the reporting and the mate-in-one case; it does not fix the move on real games** | §2 |
| 3 | `Threads > 1` for anything measured | **keep 1** — measured finally, and it is worse than the inherited rule said: at fixed depth **Threads 4 costs 1.24× wall for the same ply** and Threads 8 costs 2.00×; only Threads 4 gains depth in a fixed second (+1.4 ply, p = 0.0033). **The honesty pins cannot detect any of this** | §3 |
| 4 | `MultiPV > 1` with a large Hash | **cap Hash by line count**: 48 MB at 2 lines, 24 MB at 3–6 — the alternate table is **full size**, so MPV 2 doubles the memory | §3 |
| 5 | Any harness that types `go` limits | **validate your own tokens first** — a malformed `nodes` or `mate` value applies **no limit**, and a malformed `depth` is a 1-ply search. **Worse, a keyword with no numeric value eats the NEXT keyword**, so `go nodes depth 5` is unbounded with every token well-formed, and **a failed clock becomes a 0 ms clock that crushes a good `depth`** (`go depth 5 wtime abc` = 1 ply) | §1b, trap 3aa |
| 6 | Any harness that re-sends its option block per game | **an unchanged `Hash` re-send clears the table** (same as `Clear Hash` as measured, but it leaves a **cold table with warm histories**). **Costs nothing around `ucinewgame`; costs +157% nodes between moves; changes 4 of 30 answers on a resume path without `ucinewgame`** | §3, trap 3 |
| 7 | `AspirationDelta` and the two aspiration switches | **leave the delta at 18 and do not enable either switch without re-screening.** Changing the delta moves the score on **126 of 133** positions and the move on **95 of 133** for a **12–15% median node saving**; one position's `cp 517` becomes a **true `mate 2`** at delta 200, so the default window misses a forced mate a wider one finds. Both switches lose a mate the default finds at fixed depth | §3 |
| 8 | `SoundMatePruning` (the option named for mate safety) | **do not enable it on the evidence so far** — it costs **2–3 plies of effective depth** on forced mates and is **the only thing on this engine measured to lose a mate the default finds**. On 30 verified fixtures it changes 9 verdicts, helps 4, **harms 5**. **It does converge**: every harm recovers by depth 9 or 10, so the cost is depth-efficiency, not soundness | §3 |
| 9 | `ContHist4PlyRead` | **never enable it for anything that reads mate scores** — it reports **`mate 12` for a mate in 5 plies**, a claim 7 plies wrong whose printed PV cannot deliver it. **Default is `false` and the default build is correct on the same position**, so this is a hazard for whoever turns it on, not a live defect. Scope 1 of 30 mate fixtures; mechanism unknown | §1b |
| 10 | **Playing a won endgame with this engine** | **do not rely on it to convert — and the fix is the §2 clock band, not the drawn-root bail.** KRK converts **10 of 20**, KBNK **3 of 20**, KQK 18 of 20, KPK 167 of 192 won cells, against an **exact-table oracle control at 20 of 20 / 20 of 20 / 192 of 192**. The score collapses to **`cp 0` at halfmove clock 90** on a won three-piece board (101 million nodes to answer what 93,585 answered at clock 60), so the engine **decides the position is drawn and shuffles correctly for a drawn position.** **Zero of the 37 attributable failures involved the bail**, so patching the bail fixes none of them | §10 |

**The one thing to take away if you read nothing else:** this engine returns a well-formed answer to a
question that was not asked, in **five** distinct ways, and three of the five are indistinguishable from
success (§1b). The reliable discriminator is an **empty `pv`** — not a `0000`, not a zero node count,
and not a missing score. **A caller that checks `pv` catches all four of the shapes that RETURN; a caller
that checks the score catches none of them.** The fifth shape does not return in usable time, so no
reader-side check can catch it: **a malformed `nodes` or `mate` value applies no limit, and the only
defence is to validate your own tokens before sending.**

**Everything still open is listed in §10, with a name on each gap** — including nine classes that had
never been tested at all when this run began, each now being measured by a seat rather than merely noted.

**And a field-by-field audit of the `info` line found FOUR fields wrong, two unfalsifiable and three
clean.** This is the strongest form of the protocol finding in this report, because each verdict is about
one field against its own definition:
| field | verdict |
|---|---|
| `score` | **CONFORMANT** — side-to-move relative both ways; `mate ±N`, and `mate 0` appears only at a real mate |
| `pv` | **CONFORMANT** on searching paths — 17 of 17 final `pv[0] == bestmove`, 0 illegal moves |
| `nps` | **CONFORMANT arithmetic** — 28 of 28 exact; `0` is a sentinel at `time 0` even with 1,001 nodes on the line |
| `multipv` | CONFORMANT on searching paths; the book emits none and the bail degrades to `multipv 1` |
| **`depth`** | **NON-CONFORMANT — two distinct lies** |
| **`seldepth`** | **NON-CONFORMANT on a bail**; ordering is unfalsifiable because it prints `max(seldepth, depth)` |
| **`nodes`** | **PARTLY NON-CONFORMANT** — exact at Threads 1, but **falls across depth boundaries at MultiPV ≥ 2** |
| **`hashfull`** | **NON-CONFORMANT — new finding, and both proofs come from ONE run** |
| **`time`** | **NON-CONFORMANT on ponder** — counts from `go` while the budget counts from `ponderhit` |

- **The `depth` lie is provable WITHIN a single run, which is the strongest kind of evidence and needs no
  cross-run comparison.** `search.cpp:2440-2451` **re-emits an UNFINISHED iteration's pv under that
  iteration's depth, carrying the last FINISHED iteration's score.** On one board, depth 21 completes at
  cp 112 and depth 22 at cp 104; an abort publishes **`info depth 22 … score cp 112 nodes 1817600 …
  time 950`** — **depth 22 labelled with depth 21's score.** Five of eight stop times in 0.96–1.10 s hit
  it, and **zero hits on a position whose pv head does not change mid-iteration**, which is the negative
  control that makes it a measurement.
  - **Independently reproduced on my own build, and the limit of that reproduction is worth stating**:
    `go infinite` for 1.05 s then `stop` gives a final line of **`info depth 20 seldepth 33 … pv`** whose pv
    is **18 plies**. **But a short pv does NOT by itself prove this defect**: a *clean* `go depth 20` on the
    same position produces **2 of 20 lines with pv shorter than their depth** (depth 10 with a 9-ply pv,
    depth 20 with 18) — **TT cutoffs shorten pvs legitimately**, so `len(pv) >= depth` **is not a valid
    checker** and was tested and rejected as one. **What makes the abort case a defect is that the line is
    internally inconsistent as to WHICH iteration it reports** — the score carried forward from the previous
    completed iteration — **and only the score-comparison instance identifies that**, not the pv length.
    **So the pv-shortness observation is evidence only because of where it sits, not because shortness
    means anything.**
- **`hashfull` counts only the CURRENT GENERATION**, because `hashfull()` filters
  `entry.generation() == generation_` and every search bumps the generation. **Both proofs from one run**: a
  table warmed by a prior search finished depth 18 in **30,940 nodes against 702,673 cold** — so the path
  ran — **yet reported `hashfull 10`**. And under MultiPV ≥ 2 the last line reports the **alternate
  worker's** table (`[185, 104]` at MultiPV 2 against `[185]` at MultiPV 1). **So `hashfull` is a
  per-search counter wearing a whole-table name**, and a GUI's hash meter is reporting the wrong thing.
- **`nodes` regresses at MultiPV ≥ 2**: `info depth 3 multipv 3 … nodes 74` followed by
  `info depth 4 multipv 1 … nodes 54` — **9 drops in 35 transitions at MultiPV 3, 6 in 23 at 2, and 0 in 11
  at MultiPV 1**, so the control is the single-line case. **And two node totals coexist in one search**:
  the last depth line says `nodes 141326` while `info string softnodes nodes 259405` — a **118,079 node
  gap** between two fields both called nodes.

**And the client view, measured by a consumer that speaks only documented UCI and was written against 22
assumptions stated BEFORE the first probe** (so each satisfying result is a prediction that held rather
than a post-hoc reframe): **10 satisfied, 7 violated, 3 partial, 1 unsatisfiable by any output, 1
satisfied-but-dangerous.** The violations are the ones a GUI actually meets:
- **C6 — a search need not emit any `info depth` line.** Book moves emit exactly `info string book move
  e2e4` then `bestmove e2e4` in **0.46 ms**, and `go nodes 0` emits none. **A reader that waits for
  `info depth` deadlocks on every book move.**
- **C7 — the reported depth is not the depth searched.** 64 `info depth` lines at `go depth 64`, **all
  `nodes 0`, all empty `pv`**: a GUI displays "depth 64, 0.00" on a search that visited nothing.
- **C9 — `score cp X` does not assess the position.** **The same `cp 0` is shipped for positions the
  engine's own search scores from −43 to +142 cp.** An evaluation bar is wrong by that much while showing
  0.00.
- **C12 — a recognised clock form need not bound the search**: `go btime 10000` with White to move never
  returns, and **the hang looks like slow thinking.**
- **C14 — a silently-accepted `position` need not be the board sent**: a surplus-field FEN is loaded and
  `position nonsense` re-searches the previous board, so a GUI analyses the wrong position and shows a
  full, confident, wrong PV.
- **C19 — a returned real move need not have been chosen**: the bail's head move **agreed with the
  engine's own search on 0 of 6 roots.**
- **C22 — UNSATISFIABLE BY ANY OUTPUT, and it is the useful ceiling**: on the book path and on
  `go nodes 0` there is **no score anywhere on the wire**. So "the engine's evaluation of the move it
  returned is available" **cannot be satisfied by any engine**, because the satisfying output is not in
  the reply. **A client showing a score there is showing its own default**, and **any report quoting a
  score for a book move is quoting a client artefact.**
- **C11 is the sharpest practical one**: empty `pv` is a real signal, **but `pv` is specified as optional,
  so a client must distinguish ABSENT from PRESENT-AND-EMPTY** — a client that only reads `pv` when it
  appears misses the signal entirely.
  - **A later seat measured which one this engine actually emits, and the answer is reassuring: it always
    emits the token.** `pv` is **present-and-empty** at every terminal and drawn root it tested — a bare-king
    bail prints `… score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` with the token and nothing after it, and a
    mated root prints `… score mate 0 nodes 0 … pv`. **I confirmed both myself on the audit base.** So the
    SPEC allows absence but this engine never uses that allowance, **which turns the client rule from "handle
    two shapes" into "check for the token being empty"** — simpler, and it means the report's earlier framing
    overstated the hazard. The absent form remains something a client should tolerate, because it is legal,
    but a client facing **this** engine only ever meets the empty one.
  - **The book path is the one place with no `pv` at all**, because it emits no `info depth` line to carry
    one — a book reply is `info string book move <m>` then `bestmove`, and that is the shape a reader must
    handle separately. **A reader that treats "no pv field" and "empty pv" as the same
  thing will miss every drawn root.**
- **And the same seat put a NUMBER on the consequence, by playing 200 complete games — the single most
  concrete result in this report.** Two arms, **same engine, same seed, same ten openings, same 50 ms
  clock**, differing in exactly one client rule — whether to play a 0-node/empty-pv move:

  | | strict arm (refuses to play a bail) | naive arm (plays it) |
  |---|---|---|
  | games | 100 | 100 |
  | **lost to a protocol failure** | **59** | **0** |
  | ended by chess | 25 | 58 |
  | BAIL plies | 59 | 82 |
  | of 40 sampled bail moves, matched the engine's own search | — | **4 of 40 = 10%** |

  **The strict arm's 59 failures are all genuine draws, independently verified**: every one was rebuilt
  from its recorded moves and tested with **python-chess**, which knows nothing about the engine —
  **59 of 59 are threefold repetitions**, 0 unexplained, 0 FEN mismatches. On those same 59 positions the
  engine reported **depth 64, nodes 0, pv length 0** every single time.
  **So the same positions, the same engine, lose 59% of games under one client rule and 0% under the
  other** — and **neither number is a property of the engine alone; both are properties of the
  engine-plus-client pair.** A strict client loses **games** and keeps clean chess; a naive client keeps
  its games and loses **move quality, 90% of the time.** **That trade-off is the finding**, and it is why
  the recommendation is "ship the repair" rather than "tell clients to check `pv`" — **the client-side
  check is a workaround that costs 59 games in 100, not a solution.**

**How many hands each headline number passed through.** Not decoration — it is the property that
distinguishes the findings here that held up from the ones that were withdrawn. **Prefetch: three
independent measurements plus a fourth the coordinator ran** (8.1 / 9.43 / 9.80 / 8.93 % slower, all with
identical node counts). **The drawn-root repair: two seats plus an independent composition and rebuild by
the coordinator**, which reproduced the same `search.cpp` sha256 and the same before/after move. **PC20's
slowness: one long run, checked at four growing denominators and finally at n = 10,774 with a CI that
excludes 1.0.** **By contrast, every claim this report WITHDREW had been measured once, by one seat, and
not re-derived** — the "completely disjoint branches", the "KNN vs K is a draw", the "Book Depth
diagnosis", the "FEN field-count silence". **A single measurement is how a claim starts; it is not how
one ends.**

**And one measurement bias applies to EVERY ABBA ratio in this report, including several of the numbers
above.** The portable-build seat ran the A/A control its design implies — **the same binary in both
slots** — and got **0.9890, not 1.0**: a **1.10% bias** in the alternating design itself. That is an
uncomfortable number in a report whose speed claims are 4–10%, and it is worth stating plainly:
- **The correction is validated against a value the estimator cannot tune**: it agrees to **≤0.43% on all
  seven pairs**, so the bias is a property of the harness rather than of any one comparison.
- **It does not overturn the large claims** — 9.8% and 16.1% are far outside a 1.1% bias and both have
  sign-shares above 90%. **It does matter for the small ones**: the "+1.4% with PEXT enabled" and "+2.3%"
  rows are **inside or near the bias**, which is exactly why that seat labelled them approximate. **A ratio
  under about 1.5% from an ABBA design with no A/A control is not a measurement of a difference.**
- **And it is the sort of thing that makes a difference to how every other number here should be read.**
  **An A/A control costs one extra arm and it is the only way to know your estimator's floor.** Three
  seats quoted ratios in the 1–2% range in this run without one.
- **A clean A/A control is necessary but NOT sufficient, and the coordinator demonstrated why by failing at
  it.** Attempting to reproduce that 1.10% here gave **1.0000 at 50k nodes (resolution too coarse), +16.08%
  at 200k and −5.53% at 800k** — which are not biases but **contention**: this VM has **4 cores at
  `loadavg` 4.23 with 17 concurrent audit workers on it**. **The tell is that a design bias has ONE sign
  and a scheduler has both**, and the spreads were 1.66× and 1.30×. **So the seat's number stands on its
  own clean machine and mine was never a measurement of anything** — and every timing figure in this report
  should be read with the load it was taken under, which for the coordinator's own runs is "saturated".

**How the document is organised, because it is lopsided on purpose.** **§1–§5b and §8–§10 are about the
engine** — what to ship, what to avoid, what it costs, what is broken. **§6 and §7 are about measuring
it**: 109 KB of method rules and 86 KB of harness traps, which is **just over half the document** and is
not about the engine at all. That imbalance is deliberate and it is the honest shape of this run: the
largest single output was not a list of defects but a list of ways a measurement of this engine goes
wrong, because **the defects were mostly found by the instruments that were built to check other
claims.** If you are reading this to decide something, read §1–§5b and skip §6 entirely; if you are
reading it to run your own measurements, §6 and §7 are the part that will save you time.

**Two companion documents exist and this one is the authority where they disagree.** A per-seat summary
lives at `forge-combo29/swarm/73/OWNER_SUMMARY.md` on branch `for-fable-and-opus/swarm-73`, organised by
decision with its own provenance table; **it was assembled from committed branch content only and
re-measured nothing**, so where its figures and this report's differ, this report's are the ones that were
checked against artefacts. It is useful as a cross-check on the two reports having the same shape of
conclusion, and it is not a second measurement.

**What is waiting on you, and nothing here is merged.** Seats opened pull requests for the work they did
and stopped there, so the default branch still contains none of it. **A PR being open is
not a claim that anyone else reviewed it** — the cross-checking in this run happened between seats on
branches, and the merge decision is yours.

- **But do not read those PRs as diffs against `main`, because `main` does not contain this engine.**
  `origin/main` is **10 files** — a zip, some loose notes, `verify.py` — and **zero files under
  `forge-combo29/`**. **`main` IS an ancestor of `6b98f217`** (verified: `git merge-base origin/main
  6b98f217` returns main's own tip, and the audit base is **328 commits ahead**), so this is not a diverged
  history — **it is a tree that never had the engine, with the engine added 328 commits up the same line.**
  An earlier version of this paragraph said the two had **no merge base at all**, and **that was wrong**;
  the command fails when given a branch that is itself based on the engine tree, which is what I ran. **The
  difference matters because it names the fix**: a branch cut at `6b98f217` inherits a tree containing the
  whole engine, so its PR shows that engine as an addition — **which is exactly what the tree-swap below
  corrects, and it has now been applied to all 23 branches.** Before the fix, PR #59 reported 13,289
  changed files and 25.3 million insertions, #55 reported 13,306, #65 reported 95. **The file count in a PR
  body is a property of the base branch, not of the work.**
- **And there IS a fix, found and verified by one seat: a TREE-SWAP commit — and it has now been applied to
  EVERY deliverable branch, so the state is closed rather than described.** This repo blocks force-push and
  branch deletion repo-wide, so a rebase is impossible — **but a normal fast-forward commit whose TREE is
  `main` plus only the seat's own folder collapses the diff.** Final state, **verified mechanically on all
  23 `swarm/*` branches: 23 clean, 0 contaminated, sizes 10 to 102 files**, where "clean" means
  `git diff --name-only origin/main...<branch>` returns **nothing outside `forge-combo29/swarm/<seat>/`**.
  - **Each swap was checked three ways before its push**: the new tree differs from `main` by **exactly**
    the number of files under the seat's folder; **seat-folder content old→new differs by 0 files**, so the
    swap moved no bytes of work; and nothing outside the engine folder and the seat's folder existed on the
    old tree, so nothing was dropped. **Those three checks are the whole reason to trust a history edit**,
    and the middle one is the one that matters — a tree swap that silently lost a file would look exactly
    like a successful one from the PR page.
  - **The sizes**: figures 10 · provenance 23 · aspiration 29 · leaf 30 · qsearch 30 · timeman 32 · multipv
    33 · ponder 36 · gotokens 37 · hashgap 39 · hashresize 40 · exposure 42 · stability 45 · portable 46 ·
    infofields 47 · benchvalid 48 · gomat 48 · soak 48 · consumer 64 · threads 65 · claimable 72 · optpairs
    72 · reduction 102.
  - **And the audit that found the last five was done through `git diff` rather than the GitHub API, which
    was returning HTTP 502 for several minutes.** The local diff is the better source anyway: it cannot be
    rate-limited, and it reports the same number the PR page renders — spot-checked afterwards against the
    API on eight PRs once it recovered, all matching.
  - **The tree-swap itself has a trap that nearly cost one seat its branch**, worth recording because the
    damage would have been self-inflicted and permanent. Building the swap tree needs a throwaway
    `GIT_INDEX_FILE`; **exporting it in the shell session makes every later `git status` in the real
    checkout read the SWAP index**, which reported **13,279 staged deletions**. Nothing was lost — but a
    seat that reacts to that status with `git checkout .` or `reset --hard` **destroys an in-flight
    branch**. **`GIT_INDEX_FILE` must be set per-command or unset immediately, never exported in a session
    that also touches the real checkout.**
  - **And a residue the reader should know about**: branch **deletion is blocked repo-wide**, so temporary
    swap branches cannot be cleaned up by an agent. One exists on the remote and nothing references it.
    **That needs a human or a rule exception, and it is better flagged than called clean.**
- **The `for-fable-and-opus/*` branches are deliberately NOT swapped**: an earlier phase of this
  repository, 60+ branches, many still showing 13,000+ files and many showing 0. **They are not this run's
  deliverables, and rewriting 60 branches of history at close is not a service to the owner.** Where this
  report cites one of them, it is citing content, not a reviewable diff.
- **And the deliverable PRs' CI is mostly RED for a reason that is a property of the harness, not of the
  work — stated here so a reader who clicks a PR is not surprised.** Of the first five `swarm/*` PRs checked,
  **SonarCloud fails on four** (and **passes on the report's own PR**, which contains only markdown). The
  failures are **guarded argv-path sinks** — a measurement harness takes a filesystem path as its interface,
  so a static analyser flags the sink even though the path is validated — and the **same failure is
  pre-existing on the older `#52`–`#59` set**. One seat took its annotations from **15 → 5 → 3** and its
  Reliability rating from **R to A** by actually fixing what could be fixed, and **deliberately did not add
  `nosonar` to turn the gate green**. That refusal is the right call: **a suppression would have made the
  check pass without changing anything, and a green badge earned that way is exactly the kind of number this
  report spends §6 warning about.** Read the PR content, not the check mark.
- **What to do instead of reading the diff**: each PR's `FINDINGS.md` is the deliverable, and the paths
  in it are relative to `forge-combo29/` at `6b98f217`. **A reader who wants a real diff should compare a
  seat branch against `6b98f217`, not against `main`** — the same branch that shows 13,289 files against
  `main` shows **10** against the audit base.
- **And do not take `integrate/combo29-all` as a merge target**, even though one seat based its PR there
  deliberately so the diff would show only its own work. It is **277 commits behind** the audit base and
  **predates code the base contains**: it has **zero `DrawJitter` and zero `draw_leaf_score`**, so seat
  27's reporting patch **cannot apply to it at all** (its hunk context is a `DrawJitter` line), while seat
  12's applies with a **565-line offset**. **A branch that predates your patch can accept the patch text
  and still not be the tree the patch was measured against** — the first patch applying is not evidence
  that the second will, and neither is evidence about the behaviour.
- **And the two repair patches are self-contained**, so nothing about this depends on merging anything:
  `swarm/12/job1/two_doors_mate.patch.txt` and `swarm/27/job1/drawn_root_reporting.patch.txt`, applied
  `-p1` from the repo root and from inside `forge-combo29/` respectively, give a verified `search.cpp`.

---

## 1. Do not ship the weight-column prefetch patch

Four independent measurements agree it is slower, and a fifth agrees in direction:

| measurement | result |
|---|---|
| bench 13 (seat 29, 48 ABBA pairs) | 9.43 % slower, tight CI |
| bench (seat 19, 19-F10) | 8.1 % slower |
| **real positions (n=130, `go nodes 50000`, ABBA)** | **pooled 1.0980 → 9.80 % slower** |
| coordinator, independent rebuild (reported above) | 8.93 % slower, 18/20 positions, **nodes identical 20/20** |
| **coordinator, fifth attempt, deliberately adversarial** | **5.5 % fewer nodes at fixed time after a 4.7 % A/A correction** — consistent, and **weaker than all four**; see below |

On real positions both the patched and control builds pass all four honesty pins with **identical
node counts**, so this is pure per-node cost. **93.1% of positions (121/130) are individually
slower.** Median 1.087, Q1 1.062, Q3 1.119. Without the single 3.2× outlier, 7.87%.

The bench figures stand as general speed claims. This is the one case in the run where bench
generalised correctly.

**A fifth measurement, run by the coordinator specifically to try to break this conclusion, agrees in
direction but not in magnitude — and its own bias is part of the result.** On a **different build**
(`c279fb8f…`, verified to contain the patch: `objdump | grep -c prefetch` gives 23 against the base's 8),
a **different harness** and a **different machine-day**, 20 real positions × 3 ABBA blocks at a fixed
**200 ms**, measured as **nodes achieved in that time** rather than wall time:

- raw **A/B: geomean 0.9896**, i.e. only 1.0% fewer nodes — **which is inside noise and is NOT the result**;
- **A/A control, the same binary in both slots: geomean 1.0467**, so **this harness's floor is 4.7%** and a
  1% reading means nothing;
- **bias-corrected: 0.9896 / 1.0467 = 0.9454 — 5.5% fewer nodes for the prefetch arm.**

**So the direction survives a fifth attempt by someone trying to refute it, at roughly two-thirds the
magnitude and from a different starting point.** It is **not** folded into the 8.1–9.8% headline: a 4.7%
floor cannot certify a 5.5% effect, and **the honest statement is that this measurement is consistent with
the others and weaker than all of them.**

**And the first version of that attempt was the wrong instrument**: `go movetime N` forces both arms to the
same wall time **by construction**, so a wall-clock ratio cannot measure throughput at all. It returned
0.9968 and would have read as "no difference" — the same defect as timing a stopwatch rather than counting
the work. **The instrument had to be nodes-in-fixed-time, and the control had to be the same binary in both
slots.** One of the report's own rules (§6, "an ABBA ratio under about 1.5% needs an A/A control") is what
caught it, applied to the person who wrote the rule.

---

## 1b. If you consume this engine's output, treat an empty PV as "no move was chosen"

At a drawn root the engine answers with a legal-looking move it never searched, and the protocol
carries no field saying so. Worse, **`go depth 64` on such a position reports `depth 64`,
`seldepth 64`, `nodes 0`, cp 0** — a GUI displays "depth 64, 0.00" on a search that visited no nodes,
and nothing in the protocol says so. All four shapes below were measured on the wire:

| what you receive | what it means |
|---|---|
| `0000` with `mate 0` | checkmate |
| `0000` with `cp 0` | stalemate, or an empty `searchmoves` restriction. **In the stalemate case there is no `info string` at all** |
| a legal move, empty `pv`, `nodes 0` | **adjudicated draw — do not play the move** |
| zero `info` lines | the search never ran (`go nodes 0/1`, `go` followed by `quit`) |

**The score is the discriminator: `mate 0` means checkmate, `cp 0` means stalemate or an empty
restriction.** A blanket "treat `0000` as an error" rule is **wrong for a GUI** — it rejects a correct
checkmate — and right only for a harness that never sends a mated position. **Both halves of that
distinction are needed; the blanket rule alone would have been a defect in this report.**

**All four are present on the PC build as well as the base** — every GUI hazard in this report was
measured on both, so none of them is a base-only artefact.

**The parser surfaces are not uniform, and the differences are the finding.** **Eight rows over six
surfaces**, each with a verdict:

| surface | what a bad input does | reports the fault? |
|---|---|---|
| `setoption` | keeps the old value | **YES — every malformed form** |
| `position fen` (illegal / short) | refuses, previous board kept | **YES** |
| `position fen` (too many fields) | **loads the board, drops the surplus** | **no** |
| `position` type unknown | re-searches the previous board | **no — nothing on the wire** |
| `go` limits | **substitutes whatever `0` means to that keyword — a 1-ply search for `depth`, `wtime` and `movetime`, and NO LIMIT AT ALL for `nodes` and `mate`** | **no** |
| move list, illegal token | **truncates at the token, keeps the prefix** | **YES — `illegal move`** |
| `searchmoves`, all-illegal or empty | `0000` + `info string` + 0 nodes | **YES** |
| `searchmoves`, mixed list | drops the illegal move, runs the legal one | **no** |

**Four report the fault and four do not** over eight rows, and **two surfaces appear twice** because their
branches disagree with themselves: `position fen` speaks on a short FEN and is silent on a surplus field, and
`searchmoves` reports an all-illegal list but drops an illegal token from a mixed one. **So there is no
one-line rule: verifying one surface's refusal behaviour tells you nothing about the others, and on two of
them it tells you nothing about the same surface.**

**These are not four anecdotes: this engine has FIVE ways of returning a well-formed answer to a
question that was not asked.** (1) `bestmove 0000` for "no legal move" or a restriction; (2) zero
`info depth` lines for "the search never ran"; (3) **a refused FEN searching the previous position**,
with a legal move, a plausible score and a full PV for the wrong board; (4) **an unknown `go` token
silently ignored**, so the setting you asked for is absent; (5) **a malformed `go` VALUE replaced by
whatever `0` means to that keyword**. **In all five the protocol says nothing, and in three of the five
the output looks exactly like a success.**
- **The fifth one deserves more than a clause, because it is the only shape a reader cannot defend
  against**: a malformed `go` VALUE is replaced by whatever `0` means to that keyword, and for `nodes` and
  `mate` that meaning is **"no limit"**. `go nodes abc` applies **no limit at all** — and here the report
  has to be precise, because an earlier version of this paragraph said it "is `go infinite`", which is
  **true within a window and false about termination**. Measured on the audit base with stdin held open:

  | command | K+R v K (small board) | middlegame |
  |---|---|---|
  | `go nodes abc` | **returns on its own**, 38.7 s, depth 64 | no `bestmove` at 120 s |
  | `go mate abc` | returns, 47 s, depth 64 | no `bestmove` at 120 s |
  | `go nodes` (no value) | returns, 48 s, depth 64 | no `bestmove` at 120 s |
  | `go infinite` | reaches depth 64 at 38.5 s, **then blocks** | **never returns** without `stop` |

  **So the three "no limit" forms run into the engine's depth-64 clamp and stop; `go infinite` runs into
  the same clamp and then waits for `stop` forever.** The two are indistinguishable inside a time window,
  which is exactly what my earlier 6-second comparison measured, and they are distinguishable in
  termination class on a small board. **A harness cannot rely on either coming back**: on a middlegame all
  four are still running at 120 s, because depth 64 is unreachable in any practical budget. A mistyped
  node budget therefore produces a search that **does not return in usable time**, while a mistyped
  `depth` produces a **1-ply** search that looks like a result. Two keywords, one parser, opposite failure
  modes, nothing on the wire. **And the same parser bug has a worse shape than a bad value — see trap
  3aa's "keyword eats keyword" below.**
- **A malformed value can ERASE a well-formed limit on a different keyword, and every token can be
  correct.** `read_int` and `read_clock` advance the token index **before** `from_chars` decides the token
  was not a number (`uci.cpp:91`, `:101`, `:106`), so a keyword with no numeric value **consumes the next
  keyword**. `go nodes depth 5` therefore parses as `nodes` taking the literal token `depth`, failing, and
  setting no limit — plus a stray `5`. **`go nodes depth 5` is unbounded and the caller wrote a perfectly
  good `depth 5`.** Same shape through `mate`, `softnodes` and `movestogo`.
- **And a failed clock is a ZERO-ms clock, which outranks a good depth.** `go depth 5 wtime abc` gives
  **depth 1, 42 nodes** — the failed clock becomes 0 and crushes the depth-5 request. An explicit
  `go depth 5 nodes 0` returns **zero info lines and the first legal move**. **So the "a good limit usually
  survives a bad one beside it" rule is true for node and mate keywords and false for the clock**, and the
  reason is that a parse failure's default value is not neutral for every keyword.

- **Reliable check: `pv` is empty.** Guaranteed rather than conventional — no `pv` write exists in
  the bail branch, while every searching path sets it. Holds for a search stopped mid-iteration and
  at MultiPV 1, 2 and 3 (10 of 10 bailing cells, no searching cell).
- `nodes == 0` also works but is shared with three other unsearched paths.
- **On a drawn root MultiPV silently degrades:** one `info` line per depth regardless of the setting,
  only `multipv 1` ever appearing. A GUI waiting for alternate lines waits forever; the empty `pv`
  tells it none exist.
- **Sharpest case: bare king vs bare king** returns a legal move with cp 0, `nodes 0` and an empty
  `pv`. Nothing in the `bestmove` line says the game is over.
- **Never read the `info` line count on a bailed root as a depth.** The terminal branch emits one line
  per depth up to the engine's ceiling: **10 lines at `go depth 10`, but 64 lines under both
  `go nodes 1000` and `go nodes 100000`**, because the depth field defaults to 64 and the clamp
  passes it through. The count is `min(requested depth, 64)` and nothing was searched. The bail is
  budget-independent across all three budget kinds (depth, nodes, clock/movetime).
- **None of this is documented** in `README.md`, `LOCK.md` or `docs/`.

---

## 2. Repair the drawn-root bail — the MOVE, not the score

**The whole defect in one sentence, from the seat that proved it:** *the drawn-root defect's score is
largely sound and its cost is in the MOVE — on a genuine threefold root the base returns `cp 0` and
plays the generator's first move without looking, which on six measured fixtures forfeits a mate in
one — so a tool must distrust the move, and must not present that `cp 0` as an assessment of the
position, because a winning side never claims the draw that makes it true.*

**Shorter form: `cp 0` is right about the rule and wrong about the position.**

- **Headline sentence, now the most-tested claim in the seat. The base returns 0 nodes iff the
  position at the END of the sent move list has occurred at least three times in that list.** The
  verdict follows the **searched position's own count**, not the root's:
  - 1 ply past a repetition (searched position once) → searches, 12,978 nodes
  - 3 plies past (searched position 3×) → **bails, 0 nodes**
  - 5 plies past (once) → searches, 11,691 nodes

**Practical exposure: a tool sending a long move list can have the engine bail at the end of it,
regardless of where the game started.** A tool that plays through a repetition and then asks about a
fresh position gets a normal search.

**A middlegame root is reachable — one constructed case proves it — but the population that actually fires
is ENDGAMES, and the "MIDDLEGAMES, not endgames" reading this section used to carry is WITHDRAWN.**
The constructed case is real: a genuine opening (e2e4…e8g8) plus a legal knight-and-queen cycle, **32
pieces still on the board, 24 plies**, gives **`0 nodes, cp 0, a2a3`** at `go depth 8`, `12`, `14` **and
at `go nodes 50000` and `500000`**; the same board as a bare FEN answers `b3e6` / cp 32, and the repaired
build answers `b3e6` from the move list too. **So the trigger is not endgame-specific — but "reachable" and
"where it happens" are different questions, and the second now has a measured answer**:

| material | share of played positions | share of firings | ratio |
|---|---|---|---|
| **bare-minimum** | **0.04%** | **4.84%** | **128×** |
| 3–5 pieces | — | — | **2.8×** |
| 18+ pieces | — | — | **0.2×** |

**55.4% of all firings occur at ≤ 5 pieces**, and **20 opening families span only 38.9%–52.9% of games
(47% mean), so no opening-specific fix is indicated.** **The practical reading is the opposite of the
middlegame framing**: the bail is concentrated in endgames and *under*-represented in middlegames, which is
also what the fifty-move and threefold predicates predict, since both need a long quiet sequence. **A
single 32-piece construction is a demonstration of reachability, not evidence about the distribution** —
and generalising from it was the error.

**The trigger is THREE occurrences, not two.** At exactly **2** prior occurrences both builds agree with
the FEN form; at **3** they diverge. An ordinary twofold is harmless.
- **And the source says the same thing, which is worth one line because the measurement and the reading
  agree here rather than one standing in for the other.** `Board::is_repetition()` (`board.cpp:1224-1233`)
  counts matches against the current key inside the reversible window and returns **`matches >= 2`** —
  that is, the current position has already appeared **twice**, so including the present occurrence the
  position stands at **three**. The threshold that reads as "two" in the code is the threefold rule in
  the position, and a reader who quotes the literal `>= 2` as "the engine bails on the second
  occurrence" gets the behaviour wrong in the direction that makes it look more dangerous than it is.
  - **The separate root-relative overload behaves differently on purpose**: `is_repetition(root_index)`
    (`board.cpp:1235-1248`) steps back in twos from `size - 5` and returns true either on a single match
    at or after the root index or on **two** matches below it. So there are two repetition predicates
    with two thresholds in one file, and **a report that says "the engine's repetition rule" without
    naming which one has not said anything.**

**Who is actually exposed — and it is narrower than "any harness":** **0 threefolds in 600 random games
of 60/120/200 plies, and 0 in 4,000 further 160-ply seeds.** So **a harness sampling random positions is
essentially never affected. A harness REPLAYING REAL GAMES to a threefold is affected, and it gets a
silently wrong move with no error.** **The FEN-vs-move-list trap is not a general hazard; it is specific to
game replay, and it is silent when it hits.**

- **But that zero is measured on a population that cannot reach the condition, and the report has to say
  so rather than let the number stand as an exposure estimate.** Random play mates long before a
  fifty-move counter fills or a position repeats three times: **random play produces decisive games, and
  the bail needs a drawn root.** So 0 in 4,600 is **a true count about random games and a vacuous
  statement about exposure.** **The real rate has now been measured on the population that reaches it** —
  1,500 engine self-play games at fixed depth 10:

  | corpus | games | plies | firings | **games with ≥1 firing** |
  |---|---|---|---|---|
  | depth 10, production | 1,500 | 279,737 | **2,457** | **706 = 47.1%** |
  | depth 10, replication | 1,000 | 188,714 | 1,773 | **485 = 48.5%** |
  | depth 6 | 500 | 79,763 | 680 | 144 = 28.8% |

  **So the guard fires once per ~114 plies — 8.78 per 1,000, cluster-bootstrap 95% CI [7.80, 9.82] — and
  47% of engine games contain at least one firing.** **Name the artefact when quoting these, because the
  seat ships two and they disagree**: these figures come from `final_numbers.json`'s production run
  (2,457 firings over 279,737 plies, `plies_per_firing` **113.85**), while `rates.json` pools all six runs
  and gives **9.14 per 1,000 with CI [8.07, 10.24]** — a different corpus, not a correction. **I spent a
  check on that discrepancy myself before finding both files, which is exactly what a reader would do.** The
  cluster interval is the one to quote: consecutive
  plies in one game are not independent, since a persisting threefold fires every ply until something
  changes, and resampling whole games gives a design effect near 3. **Even the wide end is three orders of
  magnitude from "never".**
  - **Why the random corpus could not see it, measured rather than assumed**: over 4,600 random games,
    **no game ever reached halfmove ≥ 100; the maximum halfmove reached across ALL of them was 73.** And
    4,064 of 4,600 hit the ply cap rather than ending in mate — so the report's own explanation ("random
    play mates first") **is not the mechanism**. The real reason is that **random play resets the counter
    constantly**: a capture or pawn move occurs a mean of **50.5 times per game**, so the **longest quiet
    run averages 19.3 plies and never exceeded 49** — against the 100 an unbroken run would need.
  - **Which arm fires matters**: of the 2,457 firings, **1,032 are threefold only, 961 halfmove only, 258
    both, 206 insufficient material** — so **the repetition arm, the one the random corpus found 3 times in
    4,600 games, is the single largest contributor.**
  - **The cost of the move, measured objectively from the OPPONENT's best reply**: on 1,251 threefold roots,
    **median 3 cp, mean 204, p90 680, max 2,957**, with **538 unchanged and 75 where the bail did BETTER.**
    Half the firings cost nothing because the position really is drawn and any move draws — **the median
    hides the tail, and the tail is where the damage is.**
  - **And the sharp end**: **41 of 2,251 roots (1.8%) are cases where the bail plays into a FORCED MATE the
    search avoids** (against 6 where both moves allow one and 2 the other way). Eight were re-verified at
    depth 16 with python-chess agreeing, e.g. base `h5h4` where the searched move `f2e2` avoids a `mate 1`,
    and base `f7f2` where `g1h1` avoids a `mate 2`.

**The sharpest case: a genuine threefold root where the side to move has mate in one.** The base build
reports `cp 0`, searches nothing and plays `f2f3` — **forfeiting the mate** — while PC r15 reports
`mate 1` and mates.

**The chain is closed as one measurement, not three findings that rhyme.** On each of the six boards,
`go perft 1` on the searched position names the first generated move, and the base's bail returns
**exactly that move** — `f2f3` on all six — while the mates being ignored were `b1b8`, `a1a8`, `c1c8`
and `e1e8`. So: **the bail returns the head of the generated list → on these boards the head forfeits
a mate in one → the forfeit is the mechanism doing exactly what it says**, not an incidental bad move.

**Scope: 6 of 6 fixtures across two distinct mate types** (back-rank and a direct adjacent queen
mate). Still untested: breadth beyond two — all six have Black's king on g8 or h8 with pawns intact.

**And a seat that could not reproduce it was attempting a DIFFERENT fixture, which is worth recording so
the finding is not read as contested.** A consumer seat reported "§2's forfeits-a-mate-in-one did not
reproduce" after three failed fixture constructions, each diagnosed — **its mating nets put the opposing
king in check, so the base was illegal or no repetition line existed.** Its attempts were **repetition-root
fixtures**; the six here are **fifty-move roots**, where the construction is trivial because the counter
alone triggers the bail. **Verified again on my own build while checking this**:
`8/8/8/8/8/1R6/8/k1K5 w - - 100 1`, 17 legal moves, **exactly one mating move (`b3a3`)**, engine plays
**`b3b1`, which is not a mate** — the forfeit, reproduced for the third time by a third hand.
**The lesson is about fixture difficulty rather than about the claim**: a fifty-move root needs only a
counter, while a repetition root needs a legal, neutral, mating-net-compatible shuttle, **and the fact
that one is easy to build is why the six are easy to build and the thirteen attempts at a
search-requiring mate all failed.**

**Verified as one chain on 6 of 6 boards: the forfeited move is exactly the first generated move**,
confirmed by comparing `go perft 1`'s head against the bail's bestmove on each board (mates ignored
were `b1b8`, `a1a8`, `c1c8`, `e1e8`).

**Untested, and labelled as such: whether the base also forfeits a mate that needs SEARCH.** It very
likely does, by the same mechanism, but the test cannot be built: **repetition cycles live in quiet
positions and short mates live in busy ones.** Quiet positions that admit a clean neutral cycle have no
forced mate within 7 plies; positions with short mates rarely admit a clean shuttle. Thirteen
candidates across two rounds, all defeated. This is the second axis closed for that same tension, and
it is recorded as untested with a reason rather than as a negative result.

Calibrated honestly: the `cp 0` is defensible only in the narrow sense "drawn if the draw is claimed",
and a winning side never claims — so it is **right about the rule and wrong about the position**. A
tool showing that `cp 0` tells the user a game is drawn that is won in one. **Never present a bailed
root's `cp 0` as an assessment of the position.** The move cost here is sharper than the general cost
below: that loses material, this loses a forced mate. It is also the cleanest cell proving the repair
helps — base bails, PC does not, nothing else differs.

**What it does.** When the position at the **end of the sent move list** has occurred at least three
times in that list, the base build returns **0 nodes, cp 0, and the head of the generated move list**
as `bestmove`. It does not search and it does not report that it did not search.

- Monotone in occurrence count: 2 occurrences searches (7,581 nodes); 3, 4, 5 and 6 all bail at 0.
- **Confirmed at a realistic branching factor:** a dense middlegame board with ~30 legal moves → 2
  occurrences **29,994 nodes, searched**; 3 → **0, bailed**; 4 → **0, bailed**. Every earlier
  confirmation was on an endgame with a handful of moves.
- **Confirmed on a long move list:** a 10-ply preamble with the repetition at the end, searched
  position never the start position → 2 occurrences **17,399 nodes, searched**; 3/4/5 → **0, bailed**.
  List length and root position are irrelevant.
- Settings-independent: byte-identical under the PC20 option set.
- Halfmove threshold is **100**, not 75: counters 74/75/76 all search; **99 searches 200 nodes with
  cp 0** (the search sees the draw one counter early and searches anyway); 100 and above bail.
  The seventy-five-move rule is therefore **subsumed, not ignored** — 100 is stricter than 75.
- History-gated: the bare position of the same board searches normally. The bail needs the
  repetition in the move list, which is what a GUI sends.
- **8 of 10 clock self-play games reached a genuine third occurrence** (PC r15 + PC20, 6 s + 0.06,
  up to 250 plies, ten distinct openings) — but the 95% Wilson interval is **49% to 94%**, so quote
  the interval, not the 80%: the frequency is "common", not "four in five".
- **At the owner's actual match clock the asymmetry repeats:** on a validated threefold root at
  `go wtime 6000 btime 6000 winc 60 binc 60`, the base returns **`cp 0` with 0 nodes and consumes
  none of its six seconds**, while PC r15 returns **`mate 9`**.
- **Counterweight, and it bounds who is exposed: an organised match never plays the move.** The match
  program ends the game at the third occurrence, so a move chosen on a drawn root is never reached.
  **The exposure is to analysis tools and other front ends** that ask the engine about a position and
  play what comes back. Both halves belong together — quoting the mate-in-one forfeit without this
  reads as a playing-strength defect, which it is not.

**What the score is worth, measured against ground truth independent of both builds.** The family
separates into three cases and only the third was ever about the engine:

| case | base | PC r15 | verdict |
|---|---|---|---|
| bare kings — an automatic draw, no claim exists | cp 0, 0 nodes | cp 0, 0 nodes | **both correct** |
| threefold root, halfmove 100 — claimable | cp 0 | cp 425, 40,801 nodes | both defensible; the PC is finding the win, not declining the claim |
| same, at a **1 s movetime / 6 s clock** | cp 0 | **mate 8 / mate 9** | the mate arriving |
| **repetition draw with no forced win for either side** | cp 0, 0 nodes | **cp 0**, 1-ply pv, searched move | **the PC claims the draw too — correct behaviour** |

**Correction to an earlier reading: the repaired build does not decline repetition draws.** Both
earlier claimable roots had a forced mate available, so "found the mate" and "declined to claim" were
indistinguishable — a confound, not a finding. On a repetition draw with no forced win, the PC returns
cp 0 with a searched move. **It finds the win where one exists and reports the draw where none does.**

**The PC's score on a drawn root is a function of the budget; the base's is not.** The base bails
identically under `go depth 10`, `go movetime 1000` and a 6 s clock — 0 nodes, `d5d1`, **0 ms
elapsed, it does not spend the budget**. The PC returns cp 377 at depth 10, `mate 8` at a one-second
movetime, `mate 9` at a six-second clock.

**So the build comparisons in this report are depth-matched, not strength-matched.** "base cp 0, PC
cp 377" does not mean the repair reports a win where the base reports a draw.

**One candidate case was excluded rather than tabulated, and the reason matters**: a root that looked
like "a draw that does not exist" turned out to be **a defective fixture, not engine behaviour**. It was
dropped from the table above rather than given a verdict row, because **a row in a verdict table implies
the engine was measured**, and here only the fixture was wrong. That is why the table has four cases and
not five.

Control: a counter-0 position that is not drawn → both winning (cp 348 / cp 391), so the bail does
not leak into non-drawn positions.

**So repair the MOVE, not the score.** The score is largely sound. The damage is that the zero-node
path plays the unsearched first generated move, which **leaves an existing threat unanswered** — it
does not create a new weakness, it fails to address one already on the board. **Cost, measured on two
disjoint 12-position samples, deterministically sampled: a median of roughly 600–1,000 cp, with nine
or ten of twelve positions at or above 300 cp, worst 2,222, 0/12 equal to the searched best, and one
missed forced mate.**
- **"Hangs a piece" is the wrong verb, and the correction took three attempts — the mechanism is now
  measured rather than told.** On the −805 board the piece is the **queen on b6** and **it was already
  attacked before Black moved** — White's knight on a4 attacks b6 at the root. But **the queen is
  capturable after BOTH moves**: after the bail's `e6e5` White takes with the **knight** and Black
  recaptures with a **pawn**, netting **+6**; after the repair's `b6b4` the queen is still attacked,
  White takes it, and Black recaptures with the **bishop** — a queen **trade**, netting **+0**.
  **So the cost is the RECAPTURE BALANCE, not the queen's safety, and the repair does not save the
  queen.** It converts a losing capture sequence into an equal trade.
- **Two intermediate stories were wrong before this one, and both were wrong in the same way.** "Hangs a
  piece" and the repair "walks the queen away" are *each* consistent with the checked fact "attacked at
  the root" — which is why **the check that exposed the first error would have blessed the second
  one.** A verb demands a causal story, so a plausible one is always available. **The relation the claim
  actually asserts — what the recapture takes back — needed its own predicate**, which now asserts it
  in 10 assertions and was verified by planting the wrong story.
- **And it does not generalise in either direction**: across five fixtures the opponent's reply
  captures an already-attacked piece twice, captures a **not-attacked** pawn once (a genuinely new
  hang), and captures nothing twice. **The verb has to be checked per fixture, not applied to the
  class.**

**Three qualifications, each blocking a specific misreading:**
- **it is a cost of the MOVE, not of the score** — the score's `cp 0` is defensible under a rule that
  lets a draw be claimed, while the move it pairs with is not;
- **one self-play board lost 6 pawns**, so the largest figures are the sharp end rather than typical;
- **on one of two measured boards the repair is material-neutral**, so what the repair demonstrably
  buys is **the removal of the 0-node path**, not reliable material safety.

**And what the PC r15 repair does about that move — two boards, not one.** On board 1: base plays
`e6e5`, cp 0, 0 nodes, after which White's best is **+6**; PC plays `b6b4`, cp 0, 19,976 nodes,
after which White's best is **+0**. On board 2: base plays `c6c5` and loses **+1**; PC plays `e4e8`
and also loses **+1** (3,608 nodes). The mechanism reproduces on both, so both fixtures are sound.

**So the accurate statement is: the PC build removes the zero-node path, and that path is what
produced both losses. On one of two measured boards it also picks a materially better move. It does
not reliably buy material safety** — where the searched move is as bad as the unsearched one, the
repair buys honesty about the score rather than material.

**Do not re-cast the claimable-draw case as a defect.** On claimable threefold roots the PC reports
`cp 425` (K+R v K) and `mate 1` (pawns+rook) where the base reports `cp 0`. That is not a refusal to
claim: both those roots had a forced mate available, and a winning side need not claim a repetition
draw. On a winless repetition draw the PC returns `cp 0` with a searched move, so it **does** claim
when claiming is all there is. **It finds the win where one exists and reports the draw where none
does — correct behaviour.** On an automatic draw (bare kings) neither build is wrong.

**PROVENANCE OF THE "PC r15" COLUMNS IN THIS REPORT — and this banner was WRONG for most of the run, in
the direction that told the reader not to bother checking.** Earlier versions said the flag
`FORGE_FIX_ROOT_DRAWN` "is not committed as SOURCE anywhere" and that `068f0927` **did not exist**. Both
statements came from honest commands and wrong conclusions: **`068f0927` is the sha256 of the r15
EXECUTABLE**, not a commit — so `git rev-list --all` could never find it — **and the patch IS committed**,
embedded as a fenced diff in `forge-combo29/soak_all/FABLE_TO_swarm_5.md` on
`handoff/fable-opus-combo29-all-20261114`. **Rebuilt from that document: patch sha256 `d6bd72c5…` (matches
the recorded prefix exactly), applies `-p1` to a clean `6b98f217` with no fuzz, builds, and the binary is
byte-identical to `068f0927…` with all four pins matching.** **So every "PC r15" column here is
reproducible**, and the caveat is withdrawn.
- **The one real trap that remains is `-DFORGE_MATE_ALPHA_GUARD=1`.** A build with only that flag is
  **byte-identical to a control build** and **still bails on a threefold root** (0 nodes, cp 0, `d5d1`).
  **It is a build flag the patch's own instructions ask for; it is not the repair.**
- **What the rebuild actually changed in this report**: the malformed-`go` behaviour. The base's two
  **unbounded** forms (`go nodes abc`, `go mate abc`) are **bounded on r15**, because the patch carries
  `FORGE_FIX_GO_PARSE`. **That comparison existed nowhere in this report until the binary was rebuilt**,
  and it is the kind of thing a provenance caveat stops you from finding.

**PC r15 `FORGE_FIX_ROOT_DRAWN`:** disarms the guard entirely, so the root becomes an ordinary
searched position at every depth. **This has now been verified against the ACTUAL r15 BINARY, rebuilt from
the committed patch** (sha256 `068f0927…`, four pins matching), rather than quoted from a handoff document:

| fixture | base | **PC r15 (rebuilt)** |
|---|---|---|
| fifty-move root with exactly one mate (`8/8/8/8/8/1R6/8/k1K5 w - - 100 1`) | **`b3b1`, cp 0, 0 nodes** | **`b3a3`, mate 1, 145 nodes** |
| two-mate root (`8/8/8/8/8/8/1R2R3/K1k5 w - - 100 1`) | `b2b1`, cp 0, 0 nodes | **`b2b1`, mate 1, 192 nodes** |
| stalemate-only root, no mate available (`8/8/8/8/8/8/Q7/K1k5 w - - 100 1`) | `a2b1`, cp 0, 0 nodes | **`a2b1`, cp 0, 168 nodes — searches and correctly finds no mate** |

**So the three numbers this report has been quoting from a handoff — 145, 192 and the "stalemate root
searches" control — are exact.** The third row is the one that matters as a control: r15 does **not** claim
a mate where none exists; it searches, spends 168 nodes, and returns cp 0 with the same move.

### But on REAL drawn roots the shipped repair changes the move in 0 of 2,457 — and that bounds the verdict

**This is the most important qualification in this section, and it arrived late enough that the ship
verdict originally rested on a stronger reading than the evidence supports.** A seat measured **2,457 real
drawn roots from 1,500 engine self-play games** and ran three arms on each — base, the composed shipped
repair, and a bail-compiled-out instrument arm that can answer "what would the search have played":

| measurement | result |
|---|---|
| roots reproduced and confirmed bailing (0 nodes, empty pv) | **2,457 / 2,457** |
| **the shipped repair changes the MOVE** | **0 / 2,457** |
| base move is the engine's own generated head | **2,457 / 2,457** |
| the searched arm would have played something else | **1,425 / 2,457** |
| **roots with a mate-in-1 available to the mover** | **0 / 2,457** |

**The mechanism is exact and I verified it on my own build**: seat 12's patch cancels the adjudication
**only when the side to move has a move that mates immediately**. On a fifty-move root with one mate,
base plays `b3b1` (0 nodes) and the patched build plays `b3a3` with `mate 1` (145 nodes) — **different**.
On a fifty-move root with no mate available, both play `a2b1` with 0 nodes — **identical**. **And real drawn
roots never have a mate in one, because a position where a claim coexists with a mate is constructed, not
reached.** So on real roots the repair **changes only the reported depth (8 → 1) and the number of `info`
lines.**
- **"The repair removes the zero-node path when a mate exists" is what the evidence supports. "The repair
  fixes the move" is not**, and that distinction was missing from every earlier version of this section.
- **The rest of the section stands**: the mate-in-one forfeit is real on the six fixtures, the scan cost is
  real, the composition is real. **What changed is what the repair buys on real games, and the answer is
  reporting honesty rather than move quality.**
- **The honest form of the recommendation is therefore**: ship both patches because they are free and they
  remove a misleading `depth` label, **not** because they recover moves. **The claimable-draw rule in the
  next section is the change that would fix real moves** — and it is also free, which makes it the better
  buy.
- **And what the remaining defect is worth, on the population that reaches it**: **disarming the bail
  changes the result of 59% of the games that reach one (66 of 111), overwhelmingly toward draws (48 to
  0)** — **and the 48 split by who was to move at the first firing: that side LOST the base game in 34 and
  WON it in 14.** **That is not the same sentence as "the bail loses games it would win"** — it is that the
  unsearched move **measurably changes outcomes** on the population that reaches the guard, **rescuing lost
  positions into draws about as often as it costs them**, and on **1.8% of roots the change is a forced
  mate.** **The minimal change consistent with this evidence is to make the drawn-root path play a
  SEARCHED move rather than the generated head**, which is what the instrument arm does and which changes
  the move on **1,425 of 2,457 roots** — **a design change with its own pin cost, which was not attempted
  and is a recommendation rather than a result.**
  - **The paired-game measurement is the sharpest form of it, and it carries its own caveat.** **111 games
    reached a firing, 66 of 111 (59%) changed result, and 97 of those 111 diverged at EXACTLY the first
    firing ply** — a clean onset rather than a drift, which is what makes the attribution credible. **But
    of the 48 that moved to a draw, the side to move at the firing LOST 34 and WON 14** — so **it is not
    uniformly "the bail conceded"**, and the claim is stated at that strength rather than as "the bail
    loses 48 games". **The side that benefits from the unsearched move is the one that was losing.**

**An earlier "shallow-only, misses mate-in-2 at depth 4/10/nodes
20k/200k" claim has been WITHDRAWN** — it was contradicted by the source (the guard sits outside the
ID loop, `search.cpp:2253` vs `:2391`) and by two independent measurements on validated threefolds:
14 roots 14/14 correct at depth 10 and nodes 200000 (13/14 at nodes 20000), and a second seat's 8
boards searching at depth 4 on all eight, minimum 38 nodes, three reporting mate 1 at depth 4. It
leaves the scoring question alone (see below).

**What a caller sees, and why it is worse than a bad move.** Nothing in `SearchInfo` marks the move
as unchosen, and `depth` actively misleads: **`go depth 64` on a drawn root reports `depth 64`,
`seldepth 64`, `nodes 0`, cp 0 — a GUI displays "depth 64, 0.00" on a search that visited no nodes,
and nothing in the protocol says so.** It is unfalsifiable from outside.

- **Reliable caller-side check: `pv` is empty.** Guaranteed rather than conventional — no `pv` write
  exists in the bail branch, while every searching path sets it. Holds even for a search stopped
  mid-iteration (0.8–1.8 ms). **Holds at MultiPV 1, 2 and 3 — 10 of 10 bailing cells, no searching cell**
  (the same count §1b relies on; an earlier note here said "untested for MultiPV > 1", which was stale
  and contradicted §1b on the same page).
  - **Confirmed on a second build by a second reader**: on `8/8/8/8/8/1R6/8/k1K5 w - - 100 1` the base
    emits **8 `info` lines, all `cp 0 nodes 0`, pv empty**, and the repaired build on the same position
    emits **8 lines with `mate 1` and pv `b3a3`**. **The empty pv and the zero node count travel
    together and the depth field is the one that lies** — both said depth 8.
- `nodes == 0` works here but is also true for three other unsearched paths.
- A GUI receiving an empty `pv` should ignore the move and report the game state.
- **This behaviour is undocumented** — no mention of `info depth`, PV semantics or `SearchInfo` in
  `README.md`, `LOCK.md` or `docs/`.

**Two existing tests constrain the repair, and one of them is mis-pointed:**

- **`forge-combo29/tests_r3fu_17/reused_searcher.cpp:71-76`** (full path, because the bare filename does
  not resolve from the repo root) **passes on base and FAILS under the repair** (`nodes 380`). The binding
  assertion is `expect(drawn_info.nodes == 0, ...)` on a **halfmove-100** position at line 75, though the
  file's stated purpose is a stale-count guard — the neighbouring assertions at 68 and 76 are what it says
  it is testing. **Re-point it before writing the patch**, or someone will revert the assertion without
  knowing it protects the invariant.
- **`forge-combo29/tests_r3_13/quiet_extinction.cpp:99-114`** never reaches the branch (0 of 200 positions
  drawn). Its `ruled_draw` predicate at 99-100 is the same three conditions as the bail, and its binding
  assertion is `if (!ruled_draw) ok = ok && info.nodes > 0;` at line 114 — so on a drawn position the node
  check is **skipped**, which is why a repair can pass this file without being exercised. **The repetition
  arm is tested by neither file.**

**After repair, `nodes == 0` is right and `score == 0` is wrong on the same position** — the repaired
build searches a halfmove-100 root via the leaf rule (380 nodes, same cp 0), not the root branch.
That is the concrete argument for a one-field fix.

### Verdict on the repair: SHIP BOTH PATCHES — but read what they buy, because it is not the move

**The verdict survives and its REASON has narrowed.** The patches compose, cost nothing and pass every pin;
**on 2,457 real drawn roots they change the reported depth and nothing else.** This section's original
argument was that the repair fixes the move, and **that argument is wrong** — see "on REAL drawn roots"
below, which is the qualification the heading now carries.

**This verdict was independently reproduced on a clean checkout of the anchor commit by the coordinator,
not by the seats that wrote the patches, and the reproduction is the strongest evidence in this section.**
From `git archive 6b98f217` on a separate machine, g++ 13.3.0, `FORGE_MARCH=x86-64-v4`:

| check | result |
|---|---|
| compose order A, then order B | **both give sha256 `24912a43…a26671`; `diff` says the two files are identical** |
| the `-p` trap | `-p0` and `-p2` each print "can't find file to patch" / "1 out of 1 hunk ignored" and **exit 1** |
| four honesty pins on the composed build | **312,866 / 862,329 / 3,024,920 / perft 5 4,865,609** — all four match |
| decisive single-mate root `8/8/8/8/8/1R6/8/k1K5 w - - 100 1` | base: `b3b1`, **cp 0, 0 nodes, empty pv**; composed: **`b3a3`, `mate 1`, 145 nodes** |
| leaf defect untouched | hm 99 → **cp 0, 36 nodes**; hm 97 → **mate −1, 63 nodes** |

- **So the before/after contrast is reproducible by someone who did not write the patch**, including which
  move forfeits the mate, and the one-ply-down defect is confirmed to survive the repair on a second build.
- **A trap found in that reproduction, worth one line because it cost a near-miss report**: `bench N` must
  be sent over **stdin as a UCI command**. Running `./forge bench 11` as an argument prints nothing and
  **exits 0** — a quiet way to "run" a pin and record no number. **Verified on my own build: argv form
  exit 0 with no output; stdin form prints `info string bench depth 11 nodes 312866 time 160
  nps 1955412`.** So the failure has no error message, no stderr, and a success exit code — the only
  signal is a missing line that a harness reading `stdout` for numbers would never notice.
- **And the two-binary test has its own failure mode**: a run of the stalemate fixture showed 8 `info`
  lines where the patched build shows 1, and that was the BASE binary, not a regression. **In a two-build
  comparison the build label is part of the measurement**, and it is the field nobody re-reads.

**The shippability question was whether the repair's per-move scan is paid on every search.** It is not,
and that is a count rather than a reading:- **0 of 125 non-drawn roots entered the scan** (5 constructed at 14–48 legal moves; 120 random real
  positions, **76 of them at 30+ legal moves**).
- **13 of 13 drawn roots did** (6 constructed; 7 real KQvK/KRvK endgames at halfmove 100, mobility 19–31).
- **Cost when it runs: 177–319 ns per legal move (median ~240), so 5–10 µs per drawn root**, against a
  **20–80 ms** depth-12 search. **The original band was 220–280 ns from six constructed roots; a second
  seat's seven real endgames reached 319**, so the range is quoted from all ten measurements.
- **Base rate, and it bounds the benefit**: **0 drawn roots in 13,707 plies of 60 random games** (random
  play mates first), but **7 in 1,943 plies of endgames built to reach the fifty-move rule.** **Rare, and
  reachable exactly where the rule decides games.**
- **Provenance, checked file by file, because a count this load-bearing should not rest on a summary.**
  The **125 non-drawn** half is fully evidenced in committed artefacts: `job1/scan_cost.json` carries
  **5 constructed normal roots with `scanned_roots: 0`**, and `job1/out/deeper.txt` carries
  **`searches=120, searches that entered the scan=0`**. The **drawn** half was **6 of 13 evidenced**, and
  the gap has now been **CLOSED by measurement rather than by argument**:
  - **A second seat rebuilt the probe and measured the seven real endgames: `scanned_roots == 1` in 7 of 7**
    (build sha256 `8b1dc48a…`, all four honesty pins passing). Per-FEN `scan_ns`: 8338 / 5472 / 5552 /
    7108 / 6849 / 7660 / 4568 on 31 / 31 / 28 / 24 / 30 / 24 / 19 legal moves. **So "13 of 13" is now a
    measurement** — six constructed plus these seven.
  - **With the control that makes it mean something, on the same binary: 12 ordinary non-drawn roots give
    `roots=1, scanned_roots=0` in 12 of 12.** The counter is reached on every root and only the drawn
    branch increments `scanned_roots`, so it is not returning 1 by default. **A count with no control is
    a number; this one has the split demonstrated on one binary.**
  - **The cost range widens: 177–319 ns per legal move, median ~240**, against the 220–280 originally
    quoted. **Three of the seven sit at or above the original top of 280**, so the honest band across all
    ten measurements is **~177–319 ns/legal**, which is still 5–10 µs against a 20–80 ms search and does
    not change the verdict.
  - **And one provenance fact that reframes the number**: on the PC r15 tree **`FORGE_FIX_ROOT_DRAWN`
    defaults to 1, which compiles the entire scan block OUT** — so on a default r15 build the scan **is
    never reached** (`roots=0`, not `scanned_roots=0`) and the drawn roots emit no `info depth` at all.
    Reproducing the measurement **required setting it to 0**. **So 177–319 ns/legal is the cost of the
    PROPOSED CHANGE, not of any shipped engine** — which is exactly the right frame for a ship decision,
    and it was not stated in the source report.

**Adversarial families, all seven correct.** The decisive case: halfmove 100 with exactly one mate
available → **base plays `b3b1`, which is not a mate (cp 0, 0 nodes); patched plays `b3a3` with
`score mate 1`.** Two-mate roots likewise (base 0 nodes, patched 192). **Near-misses correctly do NOT
cancel**: stalemate-only (the `in_check` test works), non-mating check, mate-in-2, insufficient material.
**And a threefold root that also has a mate is repaired too** — base `h1f2` (draw) vs patched `b3a3` /
mate 1, so the repetition path is covered as well as the fifty-move path.

**Depth contract: 16 observations, no violation.** Base claims **depth 8**, or **depth 64 with 0 nodes**
under `go infinite`/`movetime`/`nodes`; **patched claims depth 1**. Normal searches after a drawn root are
**node-identical (16,646)**.

**Two cosmetic items, neither a blocker.** The patch comment "the adjudication is exactly as before" is
slightly too strong: **with `searchmoves` restricted to a non-mating move on a drawn root, the patched
build really searches (16 nodes, cp 0) where the base adjudicated** — same move and score, different
nodes and depth. And `std::min(1, max_depth)` is inert since `max_depth` is clamped to ≥ 1; plain `1`
would read better.

### Two patches exist, they compose, and one more fix must not be layered onto them

- **`swarm/12/job1/two_doors_mate.patch.txt` closes both doors** (halfmove and repetition): at a drawn
  root it first scans the legal moves and cancels the adjudication if one mates immediately, which is
  correct because a mate ends the game and no claim is available after it. **0 regressions on 12
  draw/mate cases, and all four honesty pins bit-identical on release and on ASan+UBSan**
  (312,866 / 862,329 / 3,024,920 / perft 4,865,609).
- **`swarm/27/job1/drawn_root_reporting.patch.txt` fixes the reporting**: one `info` line at depth 1
  instead of claiming `max_depth` depths the search never reached.
- **The two compose in either order to a byte-identical `src/search.cpp`** (sha256 `24912a43…`,
  verified independently on both seats). **The trap is the `-p` level, not the order**: seat 12's
  hunks name `a/forge-combo29/src/…` so it is `-p1` from the repo root, seat 27's name `a/src/…` so
  it is `-p1` from inside `forge-combo29/`. **One flag for both silently skips a hunk** — check every
  `patch` exit code.
- **The general claimable-draw fix (claim only when no legal move resets the clock) must NOT be
  layered on the PC build AS IT WAS ORIGINALLY WRITTEN** — i.e. as a change to the LEAF rule. It moves all
  three bench pins (312,866 → 353,312; 862,329 → 979,723;
  3,024,920 → 2,893,009) and, layered on r15, turns three correct answers wrong: cp −1,237 on a
  losing-side-at-threefold, cp −501 on a clock-100 root, and a correct `mate 1` into cp 488. With
  `FORGE_FIX_ROOT_DRAWN` compiled off, the same rule lands all of them correctly. **The pin cost is
  in the repetition half of the LEAF rule, not the fifty-move half** — so it must be merged inside the
  root-drawn path. **Two bullets below show that moving it there removes the cost entirely**, and the
  word "as originally written" is what separates a prohibition from a redirection.
- **And it CAN be, for free — the pin cost has now been attributed to a build and the rule ships.**
  A seat implemented the rule **inside the root path** (one hunk, 18 added lines, placed *after* the
  mate-first scan so both arms stay live) and every pin is **bit-identical to the lock on release AND on
  ASan+UBSan** — 312,866 / 862,329 / 3,024,920 / perft 5 4,865,609. **Two independent measurements say
  why**:
  - **The root gate is unreachable from every bench position.** Instrumented over the exact pin workload
    (8 FENs × 10 runs = **80 root visits**): **`adjudicated roots: 0`, `claim-test entries: 0`.** All eight
    bench FENs carry **halfmove clock 0** and a FEN carries **no repetition history**, so no bench *root*
    can be drawn. **The 80 ROOT lines are what make the zero a real zero rather than an unreached
    branch** — a counter that never fires and a counter that fires on nothing produce the same output.
  - **The documented pin triple comes from the LEAF rule, and that was isolated by deleting one arm.**
    Removing **only** the repetition arm of `Worker::is_draw` reproduces **353,312 / 979,723 / 2,893,009
    exactly**, while disabling the root path entirely leaves all eleven pins **bit-identical.** So the
    root path *cannot* move a pin, and the seat's patch **does not touch `Worker::is_draw`** — verified by
    diffing the whole function, byte-identical, still at line 1300.
  - **Correctness: candidate 20 of 20 fixtures, lock 12 of 20**, and the lock's eight failures are the
    attribution control. The families include the near-misses that must NOT cancel: stalemate-only,
    check-without-mate, mate-in-2, insufficient material, same-colour bishops — all correct on both
    builds — plus the two that must: **a threefold root WITH a mate returns `mate 1`, and a threefold root
    where the clock can be reset now searches (cp 22, 34,047 nodes) instead of adjudicating.**
  - **The insufficient-material arm is explicitly excluded from the reset test**, because insufficient
    material is an automatic draw rather than a claim, and it can offer a capture that resets the clock
    without changing the fact that nobody can mate. **The instrumented counter shows K v K entering the
    root block with `adjudicated=1` and NEVER entering the claim test** — an exclusion demonstrated as a
    measured fact rather than as a comment.
  - **And a defect in the rejected patch itself, found while trying to reproduce it**: the committed
    general-rule patch **does not compile**. It contains
    `board.piece_at(move.from).type != Pawn`, and `Piece` is a plain `enum Piece : int` with no member
    `type`. **So the documented "353,312 / 979,723 / 2,893,009 + three wrong answers" was measured on a
    hand-corrected variant, not on the committed file.** The numbers reproduce exactly once corrected, so
    no conclusion moves — **but anyone re-running the artifact as committed gets a compiler error rather
    than a result**, which is the quietest way for a patch to be unshippable.

### What is still broken after either repair: the rule is one ply lower too

`6k1/8/5PPP/8/8/8/8/R6K b - - 99 40` — Black has two moves and both allow `Ra8#`. At halfmove 99 the
base answers **`cp 0` in 36 nodes**, where counters 97 and 98 give the true `mate −1`. It is still
`cp 0` / 36 nodes on PC r15, still `cp 0` on the composed seat 12 + seat 27 tree, and **no depth fixes
it** (depth 24 still `cp 0`). The control proves it is the missing escape and not the counter itself:
`6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40` is correctly `cp 0`, because Black there has six pawn moves
that reset the clock and the draw is real.

**The cause is the LEAF rule, not the root guard, and that was measured with an instrumented build.**
`root_drawn` reads **0 at both hm=98 and hm=99** and only fires at hm=100. What actually happens is that
**every child of the hm=99 root sits at clock exactly 100 and is not checkmate**, so the leaf rule at
`search.cpp:1302-1304` returns "draw" and the child returns before the mate at ply 2 is reachable. At
hm=98 that same node IS checkmate at ply 2 and is scored correctly. **This is why neither repair patch
can help**: seat 12's tests for mate *before* the root guard, which is not the cause here, and seat 27's
changes only how many `info` lines a drawn root prints. **Both leave the ply-1 leaf rule untouched** —
verified by running them, not by reading them.

**Depth cannot help either, and the node ladder shows why:** nodes grow by exactly **3 per depth step**
(3 / 6 / 18 / 36 / 72 / 96 at depths 1 / 2 / 6 / 12 / 24 / 32), because both children return before
expansion.

**And the defect is NOT "halfmove 99" — it is a BAND whose start depends on the mate's length, and that
band was measured rather than derived.** A second seat built an independent mate oracle (alpha-beta,
ply-exact, self-tested against the engine's own scores *and* a plain minimax, with a planted-fault proof
that it can fail) and swept 80 (position, clock) pairs:

| mate length | first clock at which it is MISSED | pairs predicted | prediction matched |
|---|---|---|---|
| mate in 1 against the side to move (p = 2) | **H = 99** | 40 | **40 / 40** |
| mate in 2 against the side to move (p = 4) | **H = 97** | 40 | **40 / 40** |

**The rule is `missed iff H > 100 − p`, where `p` is the ply of the mating move.** So a repair written
against the reported board — mate in one, H = 99 — **fixes exactly one cell: one mate length at one
clock.** The seat measured both named patches against this and found them **node-for-node identical to
base on 18 cells**, which is the same conclusion this report reached from the other direction.
- **And the BOUNDARY ITSELF was one ply too low, which a third seat derived from FIDE rather than from
  the engine.** The fifty-move draw is a **claim**, and FIDE 9.3 makes a claim **optional**; a move that
  **mates ends the game immediately**, so the opponent never gets to claim. Therefore **the correct rule is
  `found iff p ≤ 101 − H`, not `p ≤ 100 − H`** — one cell wider than the base's band at every mate length.
  Verified with an independent claim-model solver (exact-value TT, no bound storage): **`p = 2` is a genuine
  mate through H = 99 and a genuine draw at H = 100; `p = 4` is a genuine mate through H = 97 and a draw at
  H = 98.** **So the base's band is not "the draw rule applied correctly, one ply late" — it is one cell
  wider than the true miss at every length**, and a repair aimed at the base's boundary would leave those
  cells wrong. **That is a second, independent reason a one-cell fix is not enough.**
- **The boundary cells are what make it a band rather than a threshold.** At p = 2, H = 98 is **found**
  and H = 99 is missed; at p = 4, H = 96 is found and H = 97 is missed. So the miss does not begin at a
  clock, it begins at a **distance**: **for a mate in three it starts at H = 95**, five clocks earlier
  than the reported board suggests. **A "halfmove 98–99" description understates the width by the very
  thing that makes it reproducible.**
- **The direction asymmetry survives and is explained by the same rule**: a mate DELIVERED by the root
  side at clock 100 is checkmate on the board and beats the draw, while a mate AGAINST the root side at
  clock 100 has the losing side to move and the leaf rule returns draw first. **`H > 100 − p` is the
  general form of both halves**, and it is why the miss is not symmetric about the root.
- **One control class had to be separated out, and it is a correction to a plausible reading**: a bare
  king returning `cp 0` is the **ROOT guard** (0 nodes), **not** this defect. A real control with a clock
  reset available **searches 23k–99k nodes and returns real scores**, so the two `cp 0` shapes are
  distinguishable by node count and must not be pooled. **The leaf seat put a number on the separation**:
  the six-pawn control `6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40` returns a **searched** `cp 0` at **227 nodes**,
  against a root-guard `cp 0` at **0 nodes** — and its harness only counts band cells whose base node count
  is above zero, which is how the two paths stay apart.

**And the repair for this band exists, ships on top of both root patches, and costs zero pins.** A seat
patched `is_draw` into a thin wrapper over a new `leaf_score`: a clock-100 node is worth **mate** if the
side to move has a move that mates at once, and a draw otherwise, with `has_mating_move` scanning only the
**checking** moves since only a check can mate. All **11 documented pins are bit-identical on four builds**
including ASan+UBSan, and the sanitizer is proved to have run by a planted heap overflow **inside the new
`has_mating_move`** that the same runner reports by name.
- **It fixes the whole band, not one cell: 14 of 14 band cells correct against an independent oracle, where
  base and the two-patch tree are both 12 of 14 and miss exactly the two cells a one-cell repair would also
  have missed.** The two decisive rows: `p=2, H=99` goes from `cp 0` at 36 nodes to **`mate −1`**, and
  `p=4, H=97` from `cp 0` at 634 nodes to **`mate −2` at 506**. **Both search real nodes, so neither is the
  root guard.** On the seven-family adversarial set it scores **7 of 7 where the two-patch tree scores 6 of 7
  and base 3 of 7**, and the one-cell delta is exactly the leaf cell — **the three families the root repair
  owns are node-and-score IDENTICAL under this patch, so the two changes do not interfere.**
- **Two verifications that make "this is exactly your two patches plus this change" a measurement**:
  **both composition orders give a byte-identical `search.cpp` (sha256 `257f177c…`), and REVERSE-APPLYING the
  leaf patch restores the shipped baseline `24912a43…` byte-for-byte.** A patch that reverses cleanly to a
  known file hash is the strongest available statement of "nothing else changed".
- **And it is not buying its correctness by searching one ply deeper**, which is the obvious way to cheat on
  a depth-boundary defect: **40 ordinary positions (the 8 bench FENs plus 32 real opening lines) at depth 14
  are 40 of 40 node-and-score identical, max |Δ| 0.0000%, zero positions with any delta.** So the fix is
  localised to the band rather than to the search.
- **And the seat recorded the error it made getting there, which is the instructive part**: its **first
  version returned a draw for a checkmated node** at clock ≥ 100, which regressed `H=98/p=2` from `mate −1`
  to **`cp −3331`** and `H=96/p=4` from `mate −2` to **`cp 0`**. **The band sweep caught it and reading the
  code had not** — a fix that looks locally right and breaks the adjacent cell is exactly what a
  multi-cell acceptance table is for. **Checkmate must stay with the caller's move loop**, and that is now
  said in the patch's own notes so the next person to try a variant here knows.

**Depth cannot help, and the node ladder shows why:** nodes grow by exactly **3 per depth step**
(3 / 6 / 18 / 36 / 72 / 96 at depths 1 / 2 / 6 / 12 / 24 / 32), because both children return before
expansion. **The band is a property of the leaf rule, so no depth reaches past it.**

**And a later seat found WHY no depth reaches it, which is the mechanism this section did not have: the
clock boundary in qsearch can only be crossed by a QUIET EVASION.** A capture resets the half-move clock,
so a qsearch **capture chain cannot cross the clock boundary at all** — the seat confirmed that the hard
way, by finding that every one of its first capture-chain fixtures reported `max_clock == root clock`. The
only way a qsearch node reaches clock 100 is an **in-check evasion** at clock 99. Instrumented: on
`4k3/8/8/8/8/2b5/8/1B2K3 w - - 99 60`, **4 of 4** clock-100 nodes are the `in_check → evasion` path
(`c100_outchk=4`, `c100_inchk=0`). **So the band and the qsearch check-evasion path are the SAME code
path**, and that is why no depth escapes: the defect lives in a node type that only occurs in check near
the boundary.

**A second, wider false draw was then found in a position with NO MATE ON THE BOARD — this one is outside
the band above, and it is a different defect.** Fixture `6k1/5ppp/8/8/8/8/8/R5NK b - - H 40`: Black is down
a rook with six pawn moves available, so the fifty-move draw is **not** available on Black's best line, and
there is no mate for either side. Measured on the audit base at `go depth 12`, and **I reproduced every row
on my own build**:

| H | base score | base nodes | truth (two independent models) |
|---|---|---|---|
| 95 | −507 | 80,489 | — (both models at depth-4 resolution, not evidence of a defect) |
| 96 | **−531** | 106,852 | −620 |
| **97** | **`cp 0`** | **1,061** | **−620** |
| 98 | `cp 0` | 487 | **0 — correct** |
| 99 | `cp 0` | 227 | **0 — correct** |

- **So the defect is ONE CLOCK UNIT WIDE and its direction is "claims a draw one ply too early"**: the
  engine is roughly right at H=96 (−531 against −620), **collapses to `cp 0` at H=97**, and is correctly
  drawn at 98 and 99. It is the same family as the band above with `p = 1` rather than `p = 2`, and
  **being reachable with no mate on the board is what makes it a separate defect** rather than a member of
  the band.
- **The mechanism is a forced clock reset, and this is the part I got wrong first.** My initial reading was
  that Black, who has the pawns and wants the draw, could shuffle and let the clock run, which would make
  H=96 the false cell instead. **That is wrong: White forces a capture that resets the clock.** The line is
  `g8f8 a1a7 f8e8 a7f7`, and replaying it against python-chess gives the clock 97 → 98 → 99 → 100 → **0**
  on the `a7f7` capture, so **Black never gets a turn at clock ≥ 100 and the claim never becomes
  available**. `Ra7` hits f7; Black cannot save the pawn without a pawn move, which is also a reset.
- **Two independent models agree on −620**, which is why the cell is published: the seat's own claim model,
  and an independent python-chess minimax written by the coordinator (claim tested on the side to move at
  `halfmove_clock >= 100`, value `max(0, continuation)` because the claim is optional, material-only leaf)
  giving **H=96 −620, H=97 −620, H=98 0**. **The second model was written specifically to try to refute
  the first, and it did not.**
- **The repair closes both wrong cells and leaves the correct ones alone**: H=97 goes to **−525** against a
  model value of −620, the H=99 mate cell goes to **mate −1**, genuine draws stay at `cp 0`, it changes
  **0 of 90** low-clock cells, and it costs **zero pins**. **The cost is stated as a cost: the H=97 cell
  goes from 1,061 nodes to 86,268 — 81×.**
- **Not shipped**, on purpose: it changes `Worker::is_draw`, which the main search and the §2 drawn-root
  work share, so it needs the owner's decision and the full 14-cell sweep. **The ~20 lines are in the
  seat's FINDINGS.**

**A separate TT defect the same seat found, and its severity bounds are worth keeping:** qsearch **stores**
as well as probes (`search.cpp:1541`, and a stand-pat lower-bound store at `:1477`), and `store_body`'s
`admit = bound == BoundExact || !same_position || depth + 4 > entry->depth` (`search.cpp:465`) means **a
depth-0 qsearch store with `BoundExact` always admits**, writing `depth = 0` over a depth-24 entry
(`before depth=24 score=250 Upper` → `after depth=0 score=−76 Exact`). **The probe side is correct**, proven
against a bound-ignoring mutant that takes both invalid cuts the base refuses, so the checker demonstrably
fires. **Two bounds on the harm, both measured**: a deep **mate** entry is *not* destroyed (qsearch reads
it, returns it and stores the same mate back), and suppressing all qsearch stores costs **+13.4% qsearch
nodes on Kiwipete and 0% on four other positions**, with full-game cost unmeasured.

- **Exposure, measured rather than assumed, and it is the honest limit of this finding.** Three lines, each
  with literal denominators:
  - **Every real game in the repository**: 13 PGNs, **5,689 games, 792,081 plies**, of which **798 plies
    sit in the band**, **503** of those with no clock reset available, and exactly **one distinct FEN** has
    a forced mate — `3k4/5Q2/1K6/8/8/8/8/8 b - - 98 105`, and the engine answers it **correctly**
    (`mate −1`, 54 nodes, the FOUND cell). **So 0 were exposed in 792,081 plies of real play.** **Checked
    independently on my own build: base and the composed repair both answer `mate −1` in 30 nodes with pv
    `d8c8 f7c7`** — a different node count from the seat's 54 because the depth differs, and the same
    verdict, which is what matters.
  - **Engine self-play into the band**: reaching a high clock is easy — **11 positions at clock ≥ 93 in
    2 games** — but **0** of those had a forced mate. **The band is easy to reach; reaching it WITH a mate
    available is the rare part**, and that is the precise reason the defect is real but did not surface.
  - **A 5,689-game sweep at the WIDER band (`p` = 2, 4, 6 instead of "clock 98 or 99") found the same
    thing, and it also produced a near-miss worth recording.** Funnel: 3,825 plies at clock ≥ 93 → 2,305
    with ≤ 6 pieces → 1,673 with no clock-resetting move → 1,220 distinct FENs tested for a mate → **4 with
    a forced mate → 1 "in band" → and that one was NOT the defect.**
    - **The four are the tail of a single game**, a K+Q conversion: H=94 p=6, H=96 p=4, H=98 p=2, and then
      **H=100 p=2 with zero legal moves** — `2k1Q3/8/1K6/8/8/8/8/8 b - - 100 106` is **already checkmate**
      and the engine answers `mate 0`, 0 nodes, `bestmove 0000`. **That is the terminal-root path, not the
      fifty-move rule**, and the scan was counting it because "mated within p" is trivially true when every
      move loses and a checkmated board has no moves to iterate.
    - **Two filter bugs, both fixed in the scanner rather than argued away**: a **terminal** position is now
      excluded (`mate_distance` returns `None` when there are no legal moves), and the scan now **requires
      `j0 = 100 − H ≥ 1`** — because at H=100 **the side to move can claim the draw itself**, which is the
      root-guard case where returning 0 is *correct*. **So the honest count from the wide corpus is 0
      exposed, and the one candidate was an artefact of the scanner.** The seat found it by measuring the
      "hit" instead of trusting the label.
  **The honest claim for any repair is therefore "it fixes a rare miss correctly", not "it recovers lost
  games"** — and the pin cost has to be weighed against that, which is the argument for the two small
  patches over the general claimable-draw rule.

---

## 3. Settings that matter

- **`Threads 1` for anything reproducible or measured.** **This rule survived the audit as advice rather
  than as a measurement, and that distinction is worth knowing**: not one harness in this audit sends
  `Threads`, so every figure in this report is at the engine's default of 1, and the claim that
  "above it, every position differs between runs" is **inherited, with no evidence file behind it in this
  tree.** **It has now been measured, it holds at maximum strength, and measuring it turned up five things
  the rule did not say:**
  - **The four honesty pins cannot detect a `Threads` problem at all.** `bench` builds its **own**
    searcher — `forge::Searcher bench_searcher(16)` (`uci.cpp:611`) — and `Searcher`'s `threads` parameter
    defaults to 1, so **`bench` never reads the `Threads` option**. Measured: **bench 11/13/16 and perft 5
    are bit-identical at Threads 1, 2, 4 and 8**, 16 of 16 cells, 3 repeats each. **So a threaded bench
    number cannot move, which means it also cannot fail, which means it certifies nothing** — the "a label
    is not a measurement" trap, in the one gate this whole audit relies on.
  - **Above Threads 1 every position differs in node count, 40 of 40, at every thread count and both
    limits** — and the *magnitude* matters more than the rate: median score swing across three repeats of
    the same command is **24–38 cp, max 2,109 cp**, with node ratio max/min up to **2.01**. **Against the
    42 cp noise floor recorded elsewhere in this report, a threaded score is not a label a training corpus
    can use.** Threads 1 spread is exactly **0 cp, ratio 1.00** — the control.
  - **At FIXED DEPTH, threading is a pessimisation at every value above 1**, and more threads is worse:
    Threads 4 needs **1.24× the wall time** of Threads 1 because it searches **3.68× the nodes** to buy
    **2.96× the node rate**; Threads 8 needs **2.00×** for 5.34× nodes and 2.68× rate (the rate *falls*
    from Threads 4, which is what oversubscription looks like). The decomposition
    `wall_cost = inflation / rate_ratio` closes to 1.1e-16, printed as a check.
  - **At FIXED TIME only Threads 4 is resolved, and it is genuinely deeper**: T4 vs T1 gives **+1.375 ply
    mean, 24 deeper / 9 same / 7 shallower, p = 0.0033** on 40 positions at `go movetime 1000`. T2
    (p = 1.000) and T8 (p = 0.736) are **near-even splits and the honest reading is "no effect detected at
    n=40", not "no effect"**. **Both arms are true at once** because the extra nodes go to parallel
    overhead rather than to depth — which is the whole finding in one line.
  - **And Threads 8 is 2× oversubscribed on this box** (4 cores, no SMT). Every T8 row is a claim about
    eight threads on four cores, and the seat says so in its own header rather than in a footnote.
  - **`Threads × MultiPV > 1` silently runs single-threaded**, confirmed by behaviour as well as source:
    a Threads-4 MultiPV-3 search is **identical to Threads 1** on 5 of 5 repeats, while the MultiPV-1
    control differs on 5 of 5. **Anyone with a MultiPV corpus should assume their `Threads` setting did
    nothing.**
  - **The drawn-root path is the one behaviour threading leaves completely alone**: **20 of 20 bail cells
    identical** in move and score across 5 repeats at all four thread counts, because the bail returns
    from `Worker::search` before the iterative-deepening loop and only the main worker's `SearchInfo` is
    returned. **The 16 SEARCH cells on the same boards still vary** — and the seat's first version claimed
    "40/40 identical", which was **false for the search cells and was caught by re-deriving the figures
    from the evidence, not by reading them.**
  - **Book behaviour is thread-invariant, and the seat had to withdraw a "book differs" row to say so**:
    the book's move comes from a **clock-seeded RNG** with `Book Variety` defaulting to 30, so it varies on
    repeat runs **at Threads 1 too** (measured: **3 of 5 vary at Threads 1**, 0 of 5 at `Book Variety 0`).
    **A harness comparing book moves across runs must pin `Book Variety 0` or it will measure its own
    RNG.**
- **Never use a zero increment.** The clock floor collapses from 111 ms to ~10 ms with no margin.
  With a 60 ms increment the floor is stable at 111 ms and the clock cannot be lost by searching.
- **And NEVER raise `Move Overhead` to "add margin" — it is a CLIFF, not a shift, and it is the one
  direction that is actively unsafe.** `time <= overhead` makes `plan_clock_budget` return
  `reserve_empty`, which routes to the **emergency path: 1 ply, 47 nodes, no time management at all.**
  Measured at a 200 ms clock: **overhead 195 still plans 3 ms and searches 7 plies; overhead 200 returns
  47 nodes at depth 1.** Below the cliff the plan is honoured and wall time barely moves (**overhead
  0 / 10 / 50 all 64 ms**). **So a harness that adds overhead "just to be safe" converts a full search into
  a one-ply answer at exactly the setting where it was trying to be careful.**
- **`Book Depth` decides WHETHER, `Book Variety` decides WHICH, and the boundary is exact**:
  `book plays iff game_ply < Book Depth`, **24 of 24 cells including six straddling it by one ply.** So
  **`Book Depth 1` books only startpos**, and a harness thinking in fullmove numbers is **off by up to a
  ply.** `Book Variety 0` is deterministic **12 of 12**, and distinct moves run **0 → 1, 5 → 1, 30 → 2,
  100 → 3.**
- **`eval` and the search disagree about `UseNNUE`, and that matters because `eval` is how a tuning harness
  confirms a setting took effect.** With `UseNNUE false` and a v3 net loaded, **the search uses the
  hand-crafted evaluation — 6 of 6 positions match the UseNNUE-false-no-net arm exactly and 0 of 6 match
  the NNUE arm — while `eval` still reports `nnue_v3`, 6 of 6.** Cause: `uci.cpp:575-582` gates on
  `v3::active()` **without consulting `nnue::enabled`**, which `search.cpp:1076` checks first. **A
  one-predicate fix, and the owner's call** — but until it is made, **`eval` is not evidence that a setting
  took effect.**
- **Three settings that look like no-ops and are not**: `setoption name Hash value <its current value>`
  **wipes the table and is byte-identical to `Clear Hash`** (trap 3 has the four-state table); a malformed
  `go nodes` **value removes the limit entirely** rather than shortening the search (trap 3aa); and
  `MultiPV > 1` **silently runs single-threaded** regardless of `Threads`, because helpers only start when
  `multipv <= 1` (`search.cpp:2711`, `:2736`). **Each is a setting a harness sends in order to be
  careful, and each changes the search in the opposite direction from what it looks like.**
- **MultiPV > 1 with a large Hash collapses throughput** — between-line `tt.clear()` plus a second
  full-size alternate table. Nodes/ms 559 → 183 → 2 at MPV 3 versus a flat ~1,500 at MPV 1. **The
  earlier advice "`MultiPV 1` at any Hash, or `Hash 16` MB with multiple lines" was too coarse**, and the
  correct boundary is a **Hash ceiling keyed on the line count**, not a product (below).
- **The cost is NOT Hash, not MultiPV, and not their product.** Four cells share `Hash × MPV = 96` and
  measure **1.30×, 1.35×, 1.37× and 1.55×** — no constant separates them. Fitted forms against a
  1.5×-unsafe threshold over 48 cells:

  | predicate | misclassified | false-safe |
  |---|---|---|
  | `Hash × MPV ≤ 144` | 4/48 | 3 |
  | `Hash × (MPV−1) ≤ 120` | 3/48 | 3 |
  | **`Hash ≤ Hmax(MPV)`**, Hmax = {1:256, 2:48, 3:48, 4:24, 5:24, 6:24} | **1/48** | 1 |
  | the same, capped conservatively (3–6 lines ≤ 24 MB) | **1/48** | **0** |

  **MultiPV 1 is flat in Hash** (114.0–139.3 ms across Hash 8–256, a 1.22× spread with no trend,
  8 of 8 within 1.5×, **node counts identical from Hash 16 to 256**) — so **no product form can express it,
  because `Hash × 1` grows and the measurement does not.** **At Hash 8 the counts are NOT identical**: four
  of six positions differ by **1–428 nodes** (up to 0.23%), so the range carrying the flatness claim and
  the range carrying "identical" are different ranges, and the sentence needs both said. The cost is
  `Hash × wipes`, where `wipes = depth × (MPV−1)`,
  and **reported depth itself falls as MultiPV rises**: **15 at MPV 1, 13 at MPV 2, 11 at MPV 6** by
  **maximum over 18 runs per cell** (Hash 16 control; MPV 2 holds depth 13 at **every** Hash, so the wipe
  count is constant across the Hash range and only the table size varies). **The estimator has to be
  named**: the median over the same 18 runs gives **14 / 12 / 10**, the mode gives **14 / 13 / 10**, and
  the per-position median gives **14 / 12 / 10** — **no single estimator produces the 14 / 13 / 11 this
  paragraph used to quote, and 14 was the one element that was not the maximum.** The source grid prints
  `max` and says 15 / 13 / 11, so that is what is quoted here. **The claim being supported is true under
  every one of the four estimators**, because all four are non-increasing in MPV — which is why the
  figure defect never showed up as a finding defect. **That coupling is what breaks the
  product, and the product model gets both directions backwards: big-Hash-2-lines is NOT fine (Hash 64,
  MPV 2 = 1.57×) and small-Hash-6-lines IS fine (Hash 8, MPV 6 = 1.18×).**
- **Recommended: `MultiPV 1` at any Hash; otherwise cap Hash by LINE COUNT — 48 MB at 2 lines, 24 MB at
  3–6.** The invariant behind the recommendation is **"the stated ceiling is never more permissive than
  the fitted one"**, and it is enforced by a check that expands every "N MB at M lines" clause into an
  effective per-line ceiling and fails if any stated ceiling exceeds the fitted value — proved by
  planting the permissive version, which fails with the exact clause and ceiling named.
  - **State the invariant, not the count.** "Zero false-safe" is a snapshot that a later re-fit
    invalidates silently; **"never more permissive than the fit"** survives the re-fit and is the
    property a check can enforce.
  - **The fitted ceiling is `Hmax = {1:256, 2:48, 3:48, 4:24, 5:24, 6:24}`, which carries 1 false-safe
    cell of 48 (`Hash 32`, MPV 3, 1.55×); the conservative form carries 0 and differs on exactly
    2 of 48 cells**, both at MPV 3 and both straddling the 1.5× line. **Ship the conservative form.**
  - **This is a HASH CEILING KEYED ON LINE COUNT, not a "per-line cap" and not a product.** "Per-line
    cap" reads as a cap on the NUMBER of lines, and it echoes the "per-line cost" hypothesis these
    measurements refute — the Hash 256 residual is **flat** across 2–6 lines. **A name that sounds
    like the refuted cause invites a skimmer to read the refutation as support.**
- **The `tt.clear()` patch rescues 17 of 22 unsafe cells** (22/48 → 5/48), every one at Hash ≤ 128. **The
  residual 5 are all Hash 256, MPV 2–6, at 1.90–1.99× and FLAT in MultiPV** — a per-line cost would
  keep climbing, so it is not per line. **It is the alternate table's ALLOCATION**, visible directly in
  time-to-first-`info`: **1.4 ms at MPV 1 versus 105.9 ms at MPV 2**, Hash 256.
  - **And the alternate table is FULL SIZE, not a small auxiliary** — which is what makes the doubling
    matter for memory as well as time. `search.cpp:2385-2386` computes its size from the MAIN table's
    cluster count, `hash_mb = cluster_count * sizeof(TTCluster) / 1 MiB`, and `sizeof(TTCluster)` is 64
    bytes (`search.hpp:122-126`), so the quotient returns the main table's own MB. **So `MultiPV 2` at
    `Hash 256` holds two 256 MB tables at once, ~512 MB total**, and the ~105 ms is the page-fault cost of
    touching the second one. **The 105 here is milliseconds and it is not megabytes**: a size in MB read
    off a number in ms would be a coincidence that happens to land near the right magnitude at this Hash,
    and one summary of this audit did carry it as "~105 MB". The table is ~256 MB; the delay is 104–106 ms.
    - **The allocation is freed at the end of the search** — it is a `std::unique_ptr` owned by the search
      frame (`search.cpp:2381-2391`) — so this is peak memory during a MultiPV search, not a leak. A soak
      seat is confirming the peak and the return with RSS.
    - **And it is ONE table however many lines you ask for**: the guard is `if (multipv > 1 && is_main())`
      (`search.cpp:2384`) and a single `alt_shared` serves every secondary line, so the memory cost is
      **2× Hash for any MultiPV above 1**, not N× Hash for N lines. **That is worth stating because the
      opposite is the natural assumption** — "six lines, six tables" would predict 3.5× the measured
      footprint at MPV 6 and would make the fitted 24 MB ceiling look far more conservative than it is.
      The cost that DOES rise with line count is the wipe count, `depth × (MPV−1)`, which is why the
      ceiling falls from 48 MB to 24 MB between 2 lines and 3–6 lines while the memory factor does not
      change at all.
  - **The robust statement is a RATIO, not a subtraction.** Allocation-only predicts **1.72×**
    (143.6 + 104 over 143.6); **1.94× is observed**, so **~0.22× of the total is search.** That is a
    **bound on a small residual, not a measurement of it**, and it holds whichever position or sampling
    convention is used.
  - **An earlier version of this paragraph read "135.4 ms = 104.5 allocation + 31 search", and it
    overstated the evidence in two unstated ways**: the two terms come from **different samples** (a
    median over cell medians against one position's time-to-first-`info`), and the excess is **not
    position-independent** — per position it ranges **135.0–195.6 ms, median 140.5**, which puts the
    search residual at **~36 ms, not ~31**. Both are inside the safe region so **nothing downstream
    changes**, but **"31 ms" reads as a measurement to three significant figures when it is the
    difference of two noisy quantities.**
  - Re-measured allocation over **6 positions × 2 repeats: 104.2 ms median, range 100–109**, so the
    single-run slope was not an outlier.
  - **The patch is NOT output-preserving, and the honest claim is "equal nodes, deeper".** MultiPV 1 is
    6 of 6 identical (the control holds); **MPV > 1 is 15 of 18 identical best moves and reaches deeper
    depth at the same budget.** Any harness that pins depth and compares moves must be re-run after it.
- **MultiPV's effect on the answer is conditional, not flat.** Changing MultiPV changes the best move
  in ~18% of positions overall (44/250 = 17.6%, replication 47/250 = 18.8%). The split is by search
  stability, where stability means a free MultiPV-1 search chose a different best move at depth 12
  than at depth 16 — a selection that never looks at the MultiPV outcome it predicts:

  | stratum | R4 | R6 (nearly doubled) | 95% CI (R6) |
  |---|---|---|---|
  | unstable | 16/30 = 53.3% | **31/58 = 53.4%** | [40.8, 65.7] |
  | stable | 31/220 = 14.1% | **35/342 = 10.2%** | [7.5, 13.9] |

  **The rate did not move when the stratum nearly doubled, and the interval tightened from 33.7 to
  24.9 points wide** — still 25 points wide, and the report says so: **±5 points needs roughly 350
  unstable boards, about 2,400 positions at the 14.5% incidence.** That incidence is consistent across
  draws (12.0%, 14.5%), so **"unstable is about 1 in 7" is a usable planning number.** 0 score ties in
  66 disagreements.
  **A display setting can only change an answer that is not settled.** The usable advice is "distrust
  near-horizon positions", the same conclusion as the depth-18 instability result reached from the
  other side, not "distrust MultiPV". **MultiPV does not rescue an unsettled position.**
- **But "unsettled" measured by a changing best move misses a search that keeps its move and revises
  its evaluation.** One board was stable by that rule yet its mate number moved by 3 between depths.
- **Select on MOVE change; do not rely on SCORE change in either direction.** The move signal is
  overwhelming: **move-unstable boards disagree 33.3% (8 of 24) against 13.2% for the remainder**,
  **Fisher p < 1e-6**, replicated on a second position set.
  - **The score signal is weaker than it was first reported.** The published comparison
    **7/109 against 21/156 is Fisher p = 0.0712** — **not significant at 0.05**, with overlapping
    intervals — so it cannot establish the specific ordering "score-change enrichment is worse than no
    criterion at all". A replication on a smaller set gives **4/23 against 7/53, p = 0.726, pointing the
    other way**, and **its strata are 4.7× smaller, so the honest statement is "this sample could not
    detect an inversion of that magnitude", not "the inversion fails to reproduce."**
  - **The move signal is now measured against both others and is decisive: 20/35 against 21/156 is
    Fisher p = 2.05e-07, and 20/35 against 7/109 is p = 7.9e-10.** So **move change beats score change**,
    not merely "score change is unestablished".
  - **An overstated inference was withdrawn, and its error class is worth naming: every number in the row was
    correct and the row parsed fine, so compliance and arithmetic both passed. It was a CORRECT NUMBER WITH
    AN OVERSTATED INFERENCE ATTACHED** — harder to catch than a wrong number, because every mechanical
    check confirms it. The withdrawn claims were a "less than half the rate" ordering and "score-change
    enrichment would have been worse than no criterion at all"; both are absent from this report.
  - **A prediction whose falsification was guaranteed by its own definitions is worse than a wrong guess,
    because a wrong guess informs.** One seat predicted 60–100% overlap between two strata that the same
    document defines as **mutually exclusive**, and reported KILLED for a prediction dead when written.
  - **And a "cannot resolve" is a result: a third candidate mate board stays a CANDIDATE, not a third
    instance.** Board 106 reports mate 10 at depth 12 and mate 7 at depth 16 with legal right-length
    checkmating PVs; exhaustive search **excluded mate in 5 or fewer** (n=5 took 419.7 s, 4.6 M memo
    entries) and **n=6 did not complete** across two runs inside ~18 CPU-minutes. **The demonstrated
    instance count therefore stays at two.** The seat's pruned-solver shortcut **failed a known mate-in-7 in
    KQ-vs-K**, and was kept and marked abandoned — because **a pruned search whose "not found" is
    indistinguishable from a timeout would have produced a confident-looking wrong answer.**
  - **The usable form: select on move change, and treat score change as unestablished rather than as
    harmful.** The mechanism that motivated score change is real (one board kept its move and revised its
    mate number by 3); what is missing is evidence about how it behaves as a selection criterion.
- **Hash below 8 MB changes node counts** (1 MB shifts them 5.6%). But **"8 MB upward is flat" is only
  true at SMALL node budgets** — the two sizes are not interchangeable at match budgets:

  | budget | Hash 16 vs 64, cells differing |
  |---|---|
  | `go nodes 50000` | **0 of 24** |
  | `go nodes 200000` | 2 of 24 |
  | `go nodes 500000` | **17 of 24** |
  | `go nodes 1000000` | **24 of 24** |
  | `go nodes 2000000` | **40 of 40** |

  **Of 178 differing cells, 15 also changed the best move.** Hash 1 differs even at 50k (11 of 24). **So
  a harness that fixes a node budget below ~200k can treat Hash 16 and 64 as equivalent, and anything
  larger cannot** — and a search over a million nodes will differ **every time**.
- **"Fewer collisions" was WRONG IN BOTH DIRECTIONS, and the divergence has two separable components.** A
  seat built the TT-overwrite instrument and measured 24 positions at `go nodes 2000000`, all against
  Hash 64:

  | size | disagree | 95% CI | mean real evictions (depth ≥ 1) | vs 64/65 |
  |---|---|---|---|---|
  | 16 | **23/24** | [80%, 99%] | 16,117 | p = 0.00026 |
  | 32 | **23/24** | [80%, 99%] | 1,909 | p = 0.00026 |
  | **65** | **11/24** | [28%, 65%] | **162** | baseline |
  | 96 | 15/24 | [43%, 79%] | 39 | p = 0.39 |
  | 256 | 14/24 | [39%, 76%] | 1 | p = 0.56 |

  - **Component 1 — a LOAD-INDEPENDENT baseline.** **Hash 64 versus 65 is a 1.02× step at equal load
    (0.270 / 0.265) and equal collision pressure, and still disagrees 11 of 24.** Cause, measured on the
    engine's own occupied keys: the index is multiply-high, `(key * cluster_count) >> 64`, so **99.996% of
    keys move cluster for ANY size change**, while cluster-sharing is identical at 37.8% both ways. **A
    size change reshuffles the table; it does not merely relieve pressure.**
  - **Component 2 — a genuine load increment.** Hash 16 and 32 add **12 more disagreements over that
    baseline at p = 0.00026 with 100× the real evictions.** So collisions do contribute — **they are just
    not the whole story**, and the ordering is **non-monotone (32 ties 16; 96 ties 256)**, which a
    pressure-only account predicts should not happen.
  - **The null control is what licenses all of it**: with the probe result prevented from reaching the
    search (`no_read`), **0 of 16 cells differ at every size and budget.** A cell repeated in two fresh
    processes also gives **0 of 16** differing in bestmove, score and nodes. **And the false-hit claim was
    repaired rather than inflated**: the seat had written "4×10¹⁴ probes" and replaced it with the measured
    **330,895,390**, narrowing "none possible" to **"none observed"**.
  - **The practical answer, which is what the owner asked for**: at `bench` ≈ 1.6 M nps on 40 real
    game-walk positions, bestmove differs 0/40 at 0.25 s (~400k nodes), **1/40 at 0.5 s (~800k)**, 3/40 at
    1 s and 3/40 at 5 s. **The threshold is ~750k nodes.** Below 500k the two sizes are near-identical;
    **at 750k two-thirds disagree on SCORE (median |Δ| 5 cp, worst 46).**
    **Recommendation: Hash 64 minimum for fixed-node work above 500k. For play, Hash 16 is not a
    correctness risk (1–3 moves in 40) but makes reported SCORES unreproducible above 750k** — which
    matters for label, eval and score-SPRT pipelines and not for move-only ones.
- **MultiPV's OUTPUT is well-formed in every way except PV length, and the one defect has a measured
  mechanism.** 1,920 depth blocks at MultiPV 1/2/3/6, all at fixed depth, against a checker whose
  selftest is 26 checks over 13 planted faults with 0 failures:
  - **Ordering and score monotonicity are clean and are ONE guarantee, not two.** 0 emission-order
    violations and 0 index-order violations. **Say it once, because the engine sorts its root lines
    before printing them** — `std::stable_sort` over `lines` by score at `search.cpp:2518`, ahead of the
    print loop. **A pass on ordering and a pass on monotonicity are the same fact observed twice, and
    neither one says anything about whether the scores are RIGHT.** Read them as "the print order is
    sorted", not as "the search agrees with itself".
  - **PV-length monotonicity is violated in 116 of 160 final depth blocks, and in 80 of the 160 the
    first line is not the longest** — two different measures, both on the same 160 blocks: 116 violate
    monotonicity somewhere in the block, 80 have line 1 strictly shorter than some line it is telling the
    client is worse. The mechanism is measured rather than asserted, and it follows directly from the
    memory finding above: **the primary line's PV is truncated by transposition-table hits on a table the
    search has been filling, while each alternate line runs against a freshly cleared table
    (`alt_shared->tt.clear()` at `search.cpp:2502`) and reaches its own nominal depth plus extensions.**
    Line 1's PV is shorter than its own seldepth in **40 of 40** blocks, is the longest in only **16 of
    40**, and is the strictly shortest in **8**.
    - **Client impact, which is where this becomes a real defect: a GUI that sizes its PV pane from
      line 1 truncates the BEST line.** The first alternate can show more of its own continuation than
      the primary does.
    - **The caveat has to travel with the number**: the claim rests on the convention
      `len(pv_1) >= len(pv_2)`. What is measured is the violations and the mechanism. **Whether a
      standard GUI actually requires that ordering was not established.**
  - **Completeness is exact at fixed depth and short under a budget.** 0 missing, 0 duplicate and 0 extra
    lines at fixed depth across all 1,920 blocks; 0 overflow when N exceeds the number of legal moves
    (5 sparse positions × 2 MultiPV settings × 2 budgets). **Under a budget the FINAL depth block is
    short**: a node budget produced **32, 32, 32** of 40 lines over three repeats, which is stable because
    it stops on a counter, while `movetime` produced **35, 35, 31** and is **not** stable — quote it as a
    range. **One single-pass figure of 32 of 40 circulates in the seat's own document and it is the one not
    to trust**, because it mixes the two budget kinds. The shape matters more than the count: **the engine
    starts a new depth block, emits part of it, and stops mid-block, so the truncated block is the LAST
    thing on screen** — a client that redraws on every `info depth` ends on the incomplete block.
    `bestmove` is never wrong under either budget, and it always agrees with the printed `multipv 1`
    `pv[0]`.
  - **A client asking for more lines than the position has moves must not wait for them**, and there is no
    end-of-block marker to tell it so: the only signal is that the block ends and `bestmove` arrives. The
    engine never emits an index above the legal move count, so on a 2-move position `MultiPV 6` gives 2
    lines and stops — the same for `searchmoves` narrowed to one move at MultiPV 3.
  - **The usable client rule, from the seat's own list: size the PV pane from the LONGEST line in the block,
    never from `multipv 1`**, because line 1 is not the longest in half the blocks and it is the line a
    user most wants to read. **And on `bestmove`, fall back to the last FULL block**, since a budget stop
    truncates the final one. Rely on ordering and monotonicity without re-checking them; they are
    guaranteed by the sort.
  - **`multipv 1`'s chosen line equals `bestmove` in 160 of 160 searches** — but equals the plain
    single-PV search's answer in only **22 of 40 positions**. The 18 disagreements were adjudicated by a
    deeper full-width search (depth 16 against depth 12) that confirms the single-PV move in **9**, the
    MultiPV move in **3**, and picks a third move in **6**. **A depth-only control with no MultiPV
    involved changes the move in 12 of 40**, so most of that 18 is unsettled positions rather than a
    MultiPV defect. **That control is what stops this being reported as a finding.**
  - **On a drawn root, MultiPV produces no alternate lines at all**: a book reply carries **no `multipv`
    line even at MultiPV 2, 3 or 6** (trap 19c), with `OwnBook false` controls at 16+ info lines proving
    the zero is not a dead path, and the bail emits exactly **1 line per depth, always `multipv 1`, never
    an index above 1**, across four drawn shapes (insufficient material, stalemate, checkmate, fifty-move)
    at four MultiPV settings. **A GUI waiting for its requested line count waits forever** on both paths;
    the empty `pv` is the only signal that none exist.
  - **New, and it sharpens trap 19a: the BOOK pre-empts the bail, and its gate is the FEN's FULLMOVE
    counter, not the halfmove clock.** The same 100-ply board **books at fullmove 1 and bails at fullmove
    16** — identical position, identical halfmove clock, opposite verdicts. So on a book-covered position
    the drawn-root path is never reached at all.
- **`SoundMatePruning=true`, the option whose whole purpose is mate safety, costs 2 to 3 plies of effective
  depth on forced mates — and that is the ONLY thing on this engine measured to lose a mate while the
  default finds it.** 30 fixtures (mates in 1, 2 and 3), every distance verified by three independent
  solvers, 90 cells at depths 8/10/12 plus a 240-row depth sweep. Against the default engine it changes the
  verdict in **9 cells, helps 4 and HARMED 5**, and the five harms are cells where **the default is right and
  the option makes it wrong**.
  - **The harm is depth-bounded, and I established that myself because the seat's table said otherwise.**
    Its table listed each harm at depths 8, 10 and 12; **on my build every one of the five recovers by depth
    10**. The seat had not re-run when this report closed, so **the per-cell depths below are mine and the
    only thing I take from its table is the cell count and the fixtures**. First fixture,
    `8/8/8/8/8/7Q/k7/2K5 w`, `OwnBook false`, `Threads 1`:

    | depth | default | `SoundMatePruning=true` |
    |---|---|---|
    | 6 | cp 1023 | **cp 1164** (wrong move) |
    | 7 | cp 1152 | wrong |
    | **8** | **mate 2**, `h3e3` | **`h3h8` cp 1230** |
    | 9 | mate 2 | **mate 2** |
    | 10, 12 | mate 2 | mate 2 |

    **All five fixtures behave identically**: harmed at depth 8, both arms correct at 10 and 12. On the mate-
    in-3 fixtures the default finds the mate at depth 7 and the option is still wrong at 7 **and 8**, right by
    9. **So the honest characterisation is a 2–3 ply depth cost, not a permanent failure** — the same class
    as the two aspiration switches, and it converges for the same reason.
  - **Why the narrower claim is the better one, and it is the third time tonight**: "materially worse"
    invites the owner to re-run one cell, see `mate 2` at depth 12, and dismiss the whole result. **"Costs 2–3
    plies" survives that check** and is actionable. **A wrong frame is worse than a smaller true claim** —
    the same correction that had to be made to the clock planner's "+2.1 ms".
  - **And the default engine's own wrong answers on this corpus are all fixed by MORE DEPTH on the same
    engine**, so they are horizon limits rather than pruning bugs. **Null-move, razor, RFP, move-loop, LMR
    and singular were not shown to lose or mis-distance a forced mate anywhere on this corpus** — which is
    the right shape for a null: every miss has a depth at which it stops being a miss.
  - **Scope of that null, stated because it is a null**: 30 fixtures, mates in 1–3, depths 8–12, one build.
    It does not cover mates longer than 3, positions where the pruning cascade interacts with a forced
    sequence beyond the horizon, or any threaded search.
- **Aspiration windows never publish a bound, so the question "can a fail-high leak a wrong-bound score"
  is unanswerable from the wire.** The engine prints **no `lowerbound` or `upperbound` token anywhere**.
  Measured instead by instrumenting the root loop to report, per finished iteration, whether the
  returned score was strictly inside its final window: **5,320 traced iterations (1,330 at each of four
  deltas 4/18/50/200, 133 positions × depth 10), 0 iterations with `inside == 0`, 0 bounds published.**
  The zero is real because a planted-fault build that publishes a fail-high bound is caught **6 of 6**
  on exactly the positions where the fault fires, and because **133 of 133 positions engage aspiration**
  (a narrowed window, up to 14 re-searches in one iteration) so the corpus reaches the condition instead
  of dodging it.
  - **Mate windows are clean on the same instrument**: 190 positive mate claims, 180 with a PV long
    enough to test, **all 180 play out to checkmate, 0 false, 0 distances exceeding `seldepth`.** The
    other 10 have a PV **shorter** than the distance claimed (`mate 10` reported against a 13-ply PV), so
    they are **unverifiable from the wire rather than wrong** — an independent AND/OR proof confirms a
    real mate exists inside the claimed distance in every one. `go mate N`, the one path where an empty
    window returns alpha at `search.cpp:1431-1435`, gave an exact mate on **8 of 8**, 0 bound iterations.
  - **The mate fixtures are labelled by proof, not by eye, and that correction is worth keeping.** The
    seat's first pass labelled eight positions as mate-in-2/3/4 **by inspection and all eight were mate in
    1**. The labels now come from an AND/OR search that does not involve the engine. **Eight fixtures
    that are all one ply short of what they claim is exactly the manufactured pass this document warns
    about.**
  - **The protocol gap is a finding in its own right: the engine has no field saying whether a score is
    exact.** Harmless today only because no bound is ever published, so **the guarantee lives in the
    implementation and not in the protocol** — any future change that starts emitting bounds breaks every
    reader silently.
  - **The window width is not a free parameter, and this is the part to act on.** `AspirationDelta` is
    **18** (range 4–200) and changing it to 50 or to 200 moves the published score on **126 of 133**
    positions and the best move on **95 of 133**. Aspiration buys **12–15% fewer nodes at the median**
    (aspiration/wide node ratio 0.852 at depth 8, 0.865 at 10, 0.879 at 12) and costs up to **2.56×** on
    individual positions. **Worst measured case: one position reports `cp 517` at delta 18 and `mate 2` at
    delta 200, and `g3g6` really is mate in 2, independently proved** — so the default window misses a
    forced mate that a wider window finds. Count this as a tuning and instability issue independent of
    the bound question: **the delta is a strength parameter that nobody has tuned, and its default is
    demonstrably worse than a wider setting on at least one position.**
  - **Neither aspiration switch is sound-and-inert, so neither is a drop-in.** `AspCappedReopen`'s
    bound-publishing break is **arithmetically unreachable** — with the fixed ±13 step, the branch is
    entered only when `x >= beta`, beta is then set to `x`, so the test becomes `x >= x + 13` — **0
    `high_break`/`low_break` exits in 448 iterations against a live counter that registered 15 planted-fault
    exits in the same channel.** Its *reopen* path does run and changes windows heavily: **5 re-search
    tries with the switch off versus 13 with it on**, at the same board and depth, with a different window
    sequence. It still **moves published scores on 114 of 141 positions and loses a mate at fixed depth**,
    so "cannot publish a bound" is not the same as "does not change the answer". `AspArmLate` fires, runs,
    publishes **0** bounds, and changes scores on **111 of 141** positions. **Both lose a mate the default
    finds at fixed depth**: on `8/8/8/5KQ1/8/5k2/8/8 w` (DTM 7 plies) the default is **M4 at depth 10**,
    `AspCappedReopen` gives **M7 at depth 11**, and `AspArmLate` needs **depth 14** and reports M17 on the
    way. **That is a depth-efficiency cost, not unsoundness** — the engine still gets there, so keep the
    distinction.
  - **And the existing switch tests cannot see the difference**: `AspArmLate`'s unit test in `tests_r3_09`
    asserts only that `bench 13` *changes* when the switch is on. It does. **That test cannot tell a speed
    change from a verdict change, and the verdict does change.**
  - **Three of this seat's own claims were withdrawn before they reached this report, and the second is the
    most instructive**: (1) eight fixtures labelled mate-in-2/3/4 by eye were **all mate in 1**; (2) an
    eight-row "false mate" finding was **wrong** — those PVs were **shorter than the claimed distance**, not
    false, so the correct classification is **0 false, 10 unverifiable-but-true**, since a truncated PV
    cannot disprove a mate; (3) a reported pin mismatch on all builds was **its own parser reading `nps`
    instead of `nodes`** — the pins were correct all along. **The pin one is the reason every seat's gate is
    a hand-check of the four figures rather than a script's verdict.**

---

## 4. Training data

- **Discard mate labels whose PV is too short for the score.** Rule: valid iff PV length is
  `2|N|−1` for a win and `2|N|` for a loss. Verified on 133 lines: 114 complete all mated,
  19 short none mated. Works at MultiPV 3, both signs, depths 6–20. A mate score
  can be reported with a PV too short to deliver mate at the first depth reporting a mate, and
  repaired one depth later.
- **The PV-length filter catches only SHORT PVs. It cannot catch a right-length PV that proves a
  different mate than its score claims.** Two independent demonstrations, and they fail in **opposite
  directions**, so no direction is claimed:

  | board | failing report | true distance | error |
  |---|---|---|---|
  | R5 222 | depth 12, **MultiPV 3** said mate −6 with a 12-ply PV (MPV 1 said mate −5) | exactly 5 | **over by 1**, on the setting with MORE lines |
  | R6 121 | depth 12, **MultiPV 1** said mate 7 (depth 16 said mate 4, same first move) | exactly 4 | **over by 3**, on the single-line search at the shallower depth |

  In both, **the PVs replay legal, are exactly the length the score implies, and end in checkmate**;
  exhaustive engine-independent search settled each true distance. So a PV that passes the length
  filter is **"not rejected", never "verified"**.
  - **And "settled by exhaustive search" needed its own audit, which found the verifier was asking the
    expensive question.** A `mate N` claim in UCI means the shortest forced mate is **exactly** N, so it
    splits into two halves: **(A)** some legal first move forces mate within N — cheap, because the engine
    hands you its move, so it is **one pinned subtree**; and **(B)** **no** legal first move forces mate
    within N−1 — a full search, but at a **lower** budget. **The verifier was doing the full search at
    budget N instead: the expensive half, done at the wrong price.** On the board that had timed out at
    600 s: half (B) at n=3 took **7.0 s** and half (A) pinned to the engine's own move took **109.2 s**,
    total **116 s**, confirming exactly mate 4. **The asymmetry is the usable result** — this is cheap
    only when the claim under test is the LONGER one. Board 106's `mate 7` still needs the full n=6
    exclusion, which timed out at 900 s with 9.0 M memo entries, **so that board stays unresolved and the
    reason is now specific: one half of the verification is expensive and the other is not.**
  - **Its own claim "the verifier handles up to mate-in-5" was FALSE as stated, and 46 committed claims
    say so**: |N| = 1 → 13/13, |N| = 2 → 9/9, |N| = 3 → 5/5, **|N| = 4 → 2/3 with one timeout**, |N| = 5 →
    **0/3**. **The measured ceiling is 4 and it is not safe there**; **|N| ≤ 3 is genuinely safe at 27/27.**
    **The limit depends on position WIDTH at least as much as on distance**, so "handles up to mate-in-N"
    is not a sentence anyone should write — **the table is.**
  - **And a state-leak bug in the replacement verifier, which is the most dangerous shape in this whole
    report**: it ran half (B) and then pushed the engine's move **on the same board object**. When (B) hit
    its timeout, the recursion unwound **without popping its moves**, leaving the board several plies deep,
    and the next `push()` asserted. **It could only ever surface on the timeout path** — i.e. on exactly
    the hardest boards, where the answer matters most and there is no second run to catch it. **A
    timed-out claim would have looked like a crash rather than a result.** Fixed with throwaway copies per
    timed phase and regression-tested against the board that still confirms at 112 s.
  - **The seat then flagged its own base-rate error rather than banking the good news.** It had predicted
    1–4 wrong verdicts from two known-bad boards and measured **0 wrong in 29**, and said so as an error of
    its own rather than as evidence the engine is better: **the two bad boards were found by SEARCHING FOR
    DISAGREEMENTS, not by random sampling, so they cannot supply a base rate.** **A sample drawn from the
    failures of a search is not a sample of the population**, and "0 wrong" here means "the 29 easy claims
    I could verify are right", nothing more.
  **What the pair establishes is stronger than either board:** board 121's contradiction is between two
  depths of the SAME setting with the SAME best move, so the error there is in the distance, not the
  move choice — **the right-length-wrong-mate class is not a MultiPV artefact at all.**
  A separate trap on the first board: a checker that assumes **the side to move is the attacker** is
  backwards for any negative mate score. Resolve the attacker from the sign and print which one it
  chose, or the checker will report true claims as false.
- **A decreasing `mate N` is not a defect, but the pre-screen needs two halves in order.** **Pin the
  move** (`searchmoves`) to separate "the distance changed" from "the engine changed which move";
  **then check the pinned number against the true distance** to separate a real but slower mate from a
  false one. Used alone, pinning cannot tell you whether the final number is right, and the distance
  check mis-attributes a move-choice drop to genuine revision.
- **The falling distance is configuration-specific.** On one board the base build reports mate 6 then
  mate 4, while PC20 reports mate 4 from the first depth and never reports mate 6. **Every
  mate-distance finding must name its build.** A true distance is a property of the *position*; the
  reported number is a property of *position plus configuration*.
  - **And in that case PC20 was right.** Exhaustive engine-independent search on the rich middlegame
    board gives an exact distance of mate in 4 — forced against every defence, with no mate in 3
    possible. PC20 reports mate 4 from depth 12; the base reports mate 6 first and converges to 4 two
    plies later. **A genuine ordering improvement, the opposite of a defect.**
- **Self-play variety comes only from openings.** Ten games from one start produce **one** distinct
  game, on both builds, at fixed limits. 1,000 openings × 2 colours = **1,000 independent pairs
  (2,000 games)**, not 2,000 samples.
- **`go nodes N` and `go softnodes N` are not the same experiment at the same N — measured at two budgets
  on a new board.** `go nodes 20000` gives `d4c5` at depth 8 / 9,359 nodes (**0.47×** of N) while
  `go softnodes 20000` gives **a different move and a different score**, `e2e3` at depth 9 / 20,800
  (**1.04×**); at N = 200000 both give `d2e1` but differ in score (−64 vs −58) and in nodes
  (182,349 vs 200,399). **`go nodes` undershoots because it stops when the next iteration would exceed N;
  `softnodes` finishes the iteration that passes N and hard-stops at 4N.** So **a corpus mixing `nodes` and
  `softnodes` at the same N mixes two experiments** — the second place in this report where "same N" does
  not name the same search.
- **Do not compare a hard-budget result with a soft-budget result.**
  - `go nodes N` picks the last completed iteration **at or below** N; median spend **74%** of N
    (measured 52,472–199,619 nodes for N=200,000). **The budget is shared across alternate lines**, which
    is why reported nodes FALL as MultiPV rises — so `go nodes N` is not a fixed workload once
    `MultiPV > 1`.
  - `go softnodes N` picks the first iteration **at or above** N; hard cap 4N.
  - A soft budget of N is **not** N: identical search at 2000 vs 3000 in **44–47%** of positions.
  - **`softnodes N` has a FLOOR as well as a ceiling, and the floor is the depth clamp.** On a small
    tree the engine reaches **depth 64 at 1,344 nodes and stops**, so every budget above that produces
    *fewer* nodes than requested: `softnodes 20000` and `softnodes 100000` both return **1,344 nodes**,
    a **14.9× under-shoot**, with the correct answer.
  - **So the overshoot ratio is not a property of the switch but of the tree.** Three populations, and
    they must be kept apart:
    | population | ratio range | note |
    |---|---|---|
    | 40 positions × 2 budgets (80 cells), budgets 500 and 2,000 | **1.008× – 3.503×**, median 1.577×, p75 2.257× | **29 of 80 cells outside** the earlier four-board band (1.02–1.95×) |
    | one K+R v K mating board, budget 20,000 | **0.067×** (1,344 of 20,000) | the depth-64 floor |
    | 60 real-game positions at budget 2,000 | **min 1.022×**, median 1.567×, max 3.987× | **0 of 60 undershot** |

    **The 0.067× belongs to the floor probe, not to the 80-cell sweep** — the lowest cell of that sweep is
    1.008×, and a 1,344-node floor against a 2,000 budget would be 0.672×. **A sentence spanning "0.07× to
    3.50×" splices two populations together**, which is how a range that sounds like one measurement
    comes from three. **Four positions are not a sample of a distribution, and the floor case could not
    have appeared in the forty either, because none of them reached depth 64.**
  - **The practical rule, with both halves: on a mating or small-tree position a soft budget can do
    nothing at all — and on 60 real-game positions at `softnodes 2000` it NEVER undershot.** Ratio min
    **1.022**, p10 1.097, median 1.567, p90 2.417, max 3.987; **0 of 60 undershoots, 0 of 60 reached the
    depth-64 clamp.** So the floor is confined to sparse or mating positions, where the tree is small
    enough that depth 64 arrives before the budget is spent.
  - **State both halves or the finding inverts.** *"A soft budget can do nothing on a mating position"*
    is true; **"a soft budget is unreliable" would be FALSE on this evidence**, and someone reading the
    14.9× figure without the scope would reasonably conclude the second. **This is the original error
    with the sign flipped** — an overshoot band generalised from four boards that could not reach depth
    64, replaced by an undershoot floor that must not be generalised from one mating board either. **The
    honest form: the ratio is bounded by the tree, and on real positions at these budgets the bound
    never binds.**
- **Every per-node figure must divide by the reported count, not the requested budget.**
- **Sparse endgames can turn a cp score into a mate at greater depth** (18/73 vs 0/73 middlegame
  pooled). Label risk is conditional on which field is stored: the move was stable 4/4, score and
  mate flag were not.

---

## 5. PC20 switch set — what it buys and what it costs

**Buys:** **8.7% fewer nodes at match depths on real positions, pooled over n=464** (the earlier
n=119 estimate of 12.4% shrank as the sample grew — quote 8.7%). At matched **nodes**, PC20 reaches a
greater depth at the 8k–20k budgets. Move quality over 600 positions: PC20 49 / S14 36 / tie 11 — no
disadvantage, possibly a small advantage.

**Costs:** **~6.4% more time per node on real positions** (pooled **1.0643, 95% CI [1.0531, 1.0748]**
— pooled bootstrap, same estimator as the point estimate; median 1.071, **162 of 180 positions strictly
above 1.0 = 90.0%, with 2 exact ties and 16 below**, node-matched subset n=16 at 1.074).
- **The earlier row said "163 of 180 at or above 1.0, with one exact tie", and that is a different
  claim.** The source figure is **162 strictly above** (`swarm/19/STATUS.md` line 1103, "90.0 %
  (162/180) above 1.0"); **the file also has TWO exact ties at 1.000, so the at-or-above count is
  164, not 163** — **so the original row was wrong twice: it named neither the strict count nor the
  inclusive one.** **"N of M above" and "N of M at or above" are different numbers unless you also report
  the tie count**, and a sign-share without its tie count cannot be recomputed from the share. **This
  correction itself carried the same fault in its first version** — it added one tie to 162 when there
  are two — which is the clearest evidence available that the fault is in the habit, not in one table.
- **A recheck found this row paired a point estimate with a DIFFERENT ESTIMATOR'S interval, and the row
  said so in prose for a while without the table changing.** `+6.4%` is the pooled ratio (**1.0643**), but
  the interval it carried, **[1.0670, 1.0876]**, is a mean-of-log interval centred on **1.0736** — **so the
  pooled estimate lay outside its own interval.** Neither bound reproduces exactly (mean-of-log gives
  **[1.0613, 1.0861]**; pooled bootstrap gives **[1.0531, 1.0748]**).
  **The conclusion survives in every construction, because all of them exclude 1.0**, so this was a pairing
  fault rather than a dead finding — and **it is now FIXED in the table below, not merely described beside
  it**: the row prints the pooled ratio with a pooled bootstrap interval, **1.0643 [1.0531, 1.0748]**, and
  the mean-of-log form is quoted separately with its own centre. **The general lesson is that a point
  estimate and an interval from two different estimators cannot be quoted as one row**; the specific
  lesson is that **describing a fault in prose next to a table does not fix the table** — the same shape as
  correcting an announcement but not the index, run in reverse. So **an equal-node S14-vs-PC20
  match is not an equal-time match.**

**The mechanism is fully accounted for arithmetically: `wall_ratio = node_ratio × per_node_ratio`.**
The n=119 pair closes to 0.27%: node **0.8761** × per-node 1.0693 = **0.9368** against an observed
**0.9343**. The n=464 run reproduces each factor separately (node **0.9131**, implied per-node
**1.0640**, product 0.9715 against observed 0.9715), so the decomposition does not depend on the
sample it was first computed on. A second build and harness independently imply 1.0472 per node
against 1.0693 measured directly. **Per-node cost is uniform and the node ratio is bimodal, so wall
time ≈ node count × per-node cost** — which is why the tail positions move means and not medians.

- **A number in this section was fabricated by a plausible pairing and caught only by a label check.**
  An earlier version of this paragraph multiplied **0.9090** — a node ratio that appears in *neither*
  of seat 19's columns — by the per-node cost, and got 0.9720 within 0.1% of an observed 0.9728.
  **The arithmetic closing was the accident, and the consistency check could not see it**: a number
  that makes the identity work is the most dangerous kind, because the identity's own closure is what
  it was manufactured to satisfy. What caught it was comparing the label against the number:
  `1 − 0.9090` is 9.1%, not the 12.4% written beside it. **A decomposition is only as good as the
  pairing of each term to its column, and that pairing needs a label check, not an arithmetic one.**

**The node saving is session-level.** PC20 searches ~9% fewer nodes, **as an average over positions**,
which does not license a per-position prediction. Every individual switch wins on only 47–61% of
positions (table below).

**The often-quoted "+3 ply at a 20,000-node budget" is wrong by 8× per position, and this one matters
because it is the figure a node-budgeted match would be planned on.** The original came from **six**
positions and read as +3 ply in total (+0.5/position). At **n=130** the same comparison gives:

| budget | PC20 deeper | **tie** | shallower | ply/position | wins/decided |
|---|---|---|---|---|---|
| `nodes 20000` | 44 | **65 (50.0%)** | 21 | **+0.062** | 67.7% |
| `nodes 50000` | 46 | **55 (42.3%)** | 29 | **+0.031** | 61.3% |

**Half of all pairs are exact ties because depth is an integer**, and the **median depth difference is
exactly 0.0** at both budgets. So the defensible statement is not "PC20 is deeper" but **"PC20 is rarely
shallower"** — same depth on about half of positions, deeper on about a third, shallower on about a
sixth, deeper-or-equal on ~84% while averaging +0.06 ply. **The effect lives in the tail of positions
where PC20 gains a ply; the typical position is unchanged.**
- **This is the timer-resolution trap on a different quantity**: a sign-share computed from an
  integer-valued measure is a share of that measure's granularity. The lesson transfers exactly — report
  wins/ties/losses, and use the share rather than the sum.

The node saving is **bimodal**: median 0.926, but mean 1.214 with a tail to 18.4×; on the 61 pairs
where PC20 used ≥5% fewer nodes the median wall ratio is 0.750. 59.5% of positions individually
favour PC20, IQR 6.1× the effect size.

Per switch: **MateAlphaGuard does nothing on ordinary positions** (unexecuted branch; alpha must be
mate-valued). Swings come from TtPruneV2 (carries ~85% of the node reduction), HistRework and
CorrHistV2.

**Every switch individually is a small pooled effect inside a huge per-position spread (19-C60, replicated
by 27-S-C77 on an independent 120-position set at depth 12):**

| switch | pooled (19) | pooled (27) | sign-share ON<OFF (19) | (27) | sign test, two-sided (19) |
|---|---|---|---|---|---|
| TtPruneV2 | 0.9528 | 0.8992 | 60.8% | **61.7%** | **p = 0.022** |
| CuckooRep | 0.9914 | 0.9768 | 52.5% | **60.0%** | p = 0.648 |
| CorrHistV2 | 0.9478 | 0.9368 | 54.2% | 52.5% | p = 0.411 |
| HistRework | 1.0311 | 0.9702 | 46.7% | 50.0% | p = 0.523 |

**Correction to the earlier reading of this table: THREE of the four p-values were wrong, not two, and
the cause was a bug in the sign test rather than a transcription slip.** The test computed
`2·Σ_{i≤k} C(n,i)/2ⁿ` without the `min(k, n−k)` reflection, so for any share **above** half the tail
sums to ≈1.0 and the p-value saturates at 1.000. It was correct only for below-half shares, which is
exactly why HistRework (56/120, p = 0.523) agreed and made the function look validated. Verified
independently: the buggy form returns 1.0000 for 73/120, 63/120 and 65/120, and 0.5230 for 56/120 —
matching every published cell.

**The fix commits the test rather than the answer.** `checks/sign_test.py` carries a **symmetry
self-test** (`p(k, n) == p(n−k, n)`, which the buggy form violates above half) and a floor assertion,
and every row now prints its count beside its p. **The deeper fault was that the p-values had no
committed source at all** — they came from inline shell arithmetic absent from the record, so no reader
could recompute them; the independent replication found it, not a review of the original.

**The consequence is a reversed published conclusion.** "No switch's per-position direction clears a
sign test" is **false**: TtPruneV2's direction is significant (61% of positions, p = 0.022, and the
replication agrees at 61.7%, p = 0.013) while its **pooled magnitude is still not established**
(CI [0.8814, 1.0307] includes 1.0). **The two tests answer different questions — the sign test asks
"is the direction consistent?", the paired-effect test asks "is the average size distinguishable from
zero?" — and this row answers yes to the first and no to the second. Report both; neither substitutes
for the other.** CuckooRep's sign agreement does **not** replicate (52.5% vs 60.0%), so "the coin-flip
shape is the general pattern" now carries **one real exception, TtPruneV2**, rather than none.

**This qualifies the depth result: "PC20 searches ~9% fewer nodes" and "PC20 is rarely shallower"
are both session-level facts.** They hold as averages over positions and **do not license a
per-position prediction** — which is exactly what a fixed-node depth comparison is built from. For all
four switches, "PC20 will be cheaper here" is ~50/50.

- **Trap: a comparison at a fixed node budget cannot show a node saving.** Both engines stop in the
  same place by construction, so any residual is the stopping rule's granularity. A 50.6% sign-share
  measured there was a correct measurement of an effect that does not exist.

**Report a pooled effect size with its sign-share, always.** A pooled effect says nothing about the
fraction of cases sharing its sign. **But first check the comparison can vary at all:** node counts
at a *fixed node budget* stop in the same place by construction, so any residual there is the
stopping rule's granularity, not a saving.

**And a sign-share computed from a QUANTISED measure is a share of that measure's granularity.** Two
measured cases, one with a clock and one with no timer at all — which is why the rule is about
quantisation rather than about timing: **wall time, 1 ms resolution on 19 ms searches → 64.6% exact
ties**; **integer depth, no timer → 50.0% exact ties.** One arm at
`go nodes 50000` had a 19 ms median reported at 1 ms resolution, and **84 of 130 pairs were exact
ties** — 64.6% — so a strict win count was measuring the clock, not the patch. Decomposing the same
130 positions at both budgets:

| budget | median | faster | **exact tie** | slower | strict share | **wins/decided** |
|---|---|---|---|---|---|---|
| `nodes 50000` | 19 ms | 30 | **84 (64.6%)** | 16 | 23.1% | **65.2%** |
| `nodes 500000` | 218 ms | 71 | **9 (6.9%)** | 50 | 54.6% | **58.7%** |

**Once ties are excluded the two budgets agree.** So: **report wins/ties/losses together, check the tie
fraction against the resolution, and LENGTHEN the measurement rather than redefining the share** —
50k → 500k took ties from 64.6% to 6.9% without changing the effect's direction. **Quote a sign-share
with its budget**, never as a bare property of the patch.

**The trap is local, and that was checked rather than assumed:** exact **node** ties are **0.0%** in the
n=464 wall run and **0.8–1.7%** across the four per-switch arms; wall-time ties are **3.7%** at a 31 ms
median. It bit only where searches were ~19 ms, and on depth at every budget.

**Prefer the SHARE to a SUM of the differences, because the sum is the seductive one.** The same
comparison reads "+3 ply over 6 positions" (+0.500/position) or "+8 ply over 130" (+0.062/position);
**the second sounds like progress and is compatible with half the positions being identical and a median
difference of exactly zero.** The share — deeper-or-equal ~84%, deeper ~34% — is the number that
describes what a user will see.

**The sign-share audit, which reorders everything above:**

| claim | pooled | 95% CI | sign-share | reading |
|---|---|---|---|---|
| PC20 per-node cost | 1.0643 (**+6.4%**) | **[1.0531, 1.0748]** — pooled bootstrap, same estimator as the point estimate | **90.0%** (162/180 strictly above, 2 exact ties, direct n=180 arm) | **REAL — a per-position tax** |
| NNUE prefetch | +9.80% | tight, excludes 1.0 | **93.1%** (121/130) | **REAL — nearly every position** |
| **PC20 node count, aggregate** | **0.9131** | **[0.8752, 0.9528]** | ~60% | **REAL pooled saving (8.7%), session-level per position** |
| PC20 net wall time | 0.9715 | **[0.9273, 1.0151]** | ~53% | **NOT ESTABLISHED — CI includes 1.0** |
| TtPruneV2 alone | 0.9528 | [0.8814, 1.0307] | 60.8% | not established |
| CorrHistV2 alone | 0.9478 | [0.8887, 1.0108] | 54.2% | not established |
| CuckooRep alone | 0.9914 | [0.9376, 1.0487] | 52.5% | not established |
| HistRework alone | 1.0311 | [0.9567, 1.1106] | 46.7% | not established |
| bench per-node | +1.2% | [0.9997, 1.0241] | not computable | bench-specific, 6× optimistic |

**The node and time rows are now n=464, quadrupled from the n=119 run that first produced them.** The
shrinkage is why they are quoted here rather than the earlier row: **node saving 12.4% → 8.7%, and the
time ratio moved toward 1.0** while the interval stayed across it. A true 7% speedup would have been
detected at n=464; it was not, so no larger n is worth buying.

**Three statements, each classified by its own CI — this is the sentence to rely on:**
1. **PC20 costs ~6.4% more per node, on 90% of positions. Real and per-position.** The 90% sign-share
   is **162/180 from the direct fixed-node n=180 arm**; the n=464 figure is implied from two pooled
   ratios and can supply no per-position sign-share at all. **A sign-share cannot be borrowed across
   methods**, only within the arm that measured the positions individually.
2. **PC20's node reduction is real at the pooled level (CI excludes 1.0) but session-level per
   position (~60% sign-share) — it does not predict any single position.**
3. **PC20's net speed is a measured LOSS on the full population, and the reading has now survived every
   stage of the run.** The final checkpoint is **n = 10,774 of 11,192 pairs**: **wall median 1.0370,
   geometric mean 1.0513 with a 95% CI of [1.0422, 1.0604] — which EXCLUDES 1.0.** The stride sample
   (116 pairs) gave wall 0.9698, about 3% faster, so **the sign flips**, and the identity closes:
   **0.9618 × 1.0712 = 1.0302 against wall 1.0370.**
   - **Both the median (1.0370) and the geometric mean (1.0513) are quoted because they differ by 1.4
     points and the headline depends on which you take** — "3.7% slower" or "5.1% slower". The CI is on
     the geometric mean and it is the stronger of the two claims.
   - **The CI is robust to the sequence structure, which had to be checked because these are consecutive
     game positions, not independent draws.** Lag-1 autocorrelation of `log(wall ratio)` is **0.0344**, and
     a block bootstrap is **flat from B = 1 to B = 200** ([1.0423, 1.0605] → [1.0429, 1.0607]). **So
     excluding 1.0 does not depend on pretending the positions are independent** — which is the obvious
     objection to a CI computed over a game sequence and it is answered before it is raised.
   - **The estimate moved AWAY from 1.0 as n grew**: 1.035 at n = 2,643 → 1.051 at n = 10,774, with the
     node median pinned at **0.9618 at every checkpoint from 2,643 onward**. **The median did not drift;
     the denominator and the mean did.** A reader who saw only the early checkpoint would have read a
     hedged "about 3.5% slower" where the final answer is a CI that excludes no-effect.
   - **This supersedes the n=464 arm's "not established"** rather than contradicting it: that interval
     included 1.0, and the population establishes the side it could not resolve. **Both readings agree
     that no speed gain exists; the population turns the best guess into a bound.**
   - **Which factor moves with phase was measured on SIX slices, and the first answer was backwards.**
     Six slices of 4,135 pairs separate the terms where thirds could not (a 0.3% factor against a 1.3% one).
     **The slice medians are read for their SPREAD, not as new central estimates**, and each slice here is
     a stratum of the same run whose final total is 10,774 pairs above:

     | term | six values | spread |
     |---|---|---|
     | **per-node** | 1.0696 / 1.0719 / 1.0699 / 1.0720 / 1.0690 / 1.0721 | **0.29%** |
     | node | 0.9489 / 0.9618 / 0.9618 / 0.9618 / 0.9588 / 0.9618 | 1.36% |
     | wall | 1.0000 / 1.0476 / 1.0204 / 1.0476 / 1.0238 / 1.0175 | 4.76% |

     **Spread is (max−min)/min; with (max−min)/max the same data gives 0.29% / 1.34% / 4.54%.** The
     ordering and every conclusion are identical, **but a spread figure has to name its estimator** — two
     seats computed the same three numbers and got two sets of percentages for that reason alone.

     **So per-node cost is nearly a CONSTANT of the engine — 0.3% across the whole population — and the
     phase-dependence lives in the NODE ratio.** An earlier reading that "only the per-node factor moves
     with game phase" is **withdrawn**; thirds were too coarse to see it.
   - **The corrected mechanism is the stronger statement, and it explains a cross-seat agreement**: per-node
     cost is a property of the **code** and is stable to 0.3% in every game phase, while the node ratio is a
     property of the **search interacting with the position**. **That is why three samples across two
     builds gave per-node figures of 1.0640, 1.0693 and 1.0709 — it is the one term that does not depend
     on what you sampled.**
   - **Caution on reading the table as a per-slice identity**: individual slice MEDIANS do not multiply
     through (slice 2 gives 0.9618 × 1.0719 = 1.0310 against a wall median of 1.0476). **The identity
     closes on the aggregate, not on each slice**, because a median of a product is not the product of
     medians.

**The two components are internally consistent across methods and sample sizes — three routes, two
builds, two harnesses, three sample sizes:**

| route | per-node | sample |
|---|---|---|
| direct, fixed `go nodes` | **1.0693** | n=180 |
| implied from the decomposition | **1.0640** | n=464 |
| implied, second build and harness | **1.0472** | n=116 |

All three inside a 2% band, and **two of the three are derived, not measured — which is why this is a
decomposition rather than a fitted identity.** What moved as the sample grew was the node saving
(12.4% → 8.7%); **the per-node cell did not move**. **Quote the components, never a "PC20 speedup".**
The nearly-cancelling components are also why a larger sample keeps failing to establish a net gain:
that failure is the prediction the decomposition makes, not evidence against it.

**No individual switch is established as a node saving at n=120** — all four pooled CIs include 1.0.
The aggregate is established; the components are not.

**And a switch's contribution depends on which ablation answers the question (27-S-C78).** Both designs
run on the same 120 positions:

| switch | ADD to S14 | DROP from PC20 |
|---|---|---|
| TtPruneV2 | 0.8992 (saves 10%) | 1.0853 (removing costs 8.5%) |
| **CorrHistV2** | **0.9368 (saves 6.3%)** | **0.9998 (removing changes NOTHING)** |

**CorrHistV2 does real work alone and is fully redundant inside the bundle.** So "how much does
TtPruneV2 save" has two true answers, 10% from a bare baseline and 8.5% of the bundle, and the two
seats' 5% and 10% figures were never in conflict — they measure different things. **The actionable
version: CorrHistV2 can be kept or dropped and nothing measured changes.** This is the drop-one
necessity versus add-one sufficiency distinction applied to a switch set, and it is why a bundle
ablation alone under-reports a redundant option.

**A sign-share alone cannot classify a claim; the interval decides first.** 50.6% with no established
effect and 60.5% with a real pooled effect are closer to each other than either is to 90%.

**CorrHistV2:** 5.2% pooled node saving but wins on **54.2%** of positions with an IQR **28×** the
effect size. This is not a measurement artefact — it is what the switch does. True of a session,
unusable as a per-position predictor.

- **Bench is not a proxy.** Node ratio PC20/S14 flips sign across benches (+14.5% bench 11,
  −10.6% bench 13, +8.7% bench 16) against −9.1% on real positions.
- **Independently reproduced** (separate seat, own measurement): bench 11 242,796 → 278,024 **(+14.5%)**; bench 13 656,517 → 587,276 **(−10.5%)**; bench 16 2,155,620 → 2,343,893 **(+8.7%)**; real positions n=40 depth 12, 2,836,869 → 2,643,393 **(−6.8%)**. Percentages agree with the original to **0.1 of a point**; the real-position gap (−6.8 vs −9.1) is sample size, not sign. The real arm was measured **in the same invocation** as the benches, so the contrast is within one set of conditions.

---

## 5b. Where the time actually goes — and why there is no v3 patch to write

**A perfect v3 kernel caps at ~1.26× on this engine**, and that is not a benchmark artefact: the net is
**20.85%** on bench 13 and **20.65%** on 200 real openings at depth 12, agreement within 0.2 points. The
picker plus generation is the larger lever in both arms: **40.27% on the bench and 34.17% on real
positions.** **An earlier "~37%" for the picker was a hand-typed average of the two** — the block now
states both, because **the real-position arm is the one that governs** and it is the smaller of the two.
- **A stale file in that folder would have answered "the net is cheap" persuasively and wrongly.**
  `v3/prof_open/summary.txt` recorded **nnue 0.00%**, because it came from the **first** profile whose
  `perf.data` was **empty** (blocked by `perf_event_paranoid`). It is now renamed to
  `summary_BROKEN_emptyperfdata.txt` so it cannot be mistaken, and a single parser (`perf_shares.py`, branch
  `for-fable-and-opus/swarm-16`, `forge-combo29/swarm/16/v3/`) is the
  only source — **because perf's demangled symbol names WRAP onto following lines, and naive parses gave
  0.96% and 2.06% on the same data.**
  - **This is the empty-profile trap sitting live in the folder of the seat that documented it** — and the
    reason it matters is that **a zero agreeing with your prior is the most persuasive kind of wrong
    answer.**

**Profile (bench 13, PC20 + test net, Threads 1; the instrumented `-pg` build reproduces bench 13 =
3,652,372 exactly, so the profiler does not measure itself):**

| group | self % |
|---|---|
| search proper | **38.41%** |
| all `nnue::v3` | 21.46% |
| movegen / legal / make / see | 15.80% |
| update `apply_changes_pair` | 8.47% |
| refresh `refresh_from_pieces` | 6.78% |

- **A correction on the `evaluate` row, which was `7.34%` and belongs to a different function.**
  `7.34%` is **`MovePicker::generate_evasions()`**, the line directly below in
  `gprof_flat.txt` (branch `for-fable-and-opus/swarm-08`, `forge-combo29/swarm/08/v3/profile/`). **Two
  independent facts fix which is which**: the `nnue::v3` group is stated as **21.46%**, and
  **21.46 only closes with 5.08** (`8.47 + 6.78 + 5.08 + 1.13 = 21.46`; substituting 7.34 gives 23.72);
  and the row's own **call count 2,556,881 is `v3::evaluate`'s** in that file, **so the row's call column
  contradicts its percentage.** The error is **inherited from seat 08's report**, whose prose quotes
  `generate_evasions` at 7.34 and `evaluate` at 5.08 one line apart — **the prose is right and the table
  is wrong in the source.** The advice does not move (largest is `apply_changes_pair` at 8.47%), which is
  exactly why it survived: **a wrong number that supports a right conclusion is the one nobody checks.**

**No single v3 function exceeds 8.5%, so there is no hot spot large enough to justify a v3
micro-patch on the strength of its percentage alone.** The larger shares are search and movegen, not the
v3 novelty. **That advice was then qualified by a patch that succeeded anyway** — see below: the win camenot from the share being large but from the function's work being removable without touching identity.

A prediction that the incremental update would dominate at 35–50% was killed by the **call counts**, not
by the percentage: `evaluate` is called 2,556,881 times against the update's 2,382,071, because the v3
path evaluates at nearly every node rather than only at leaves. The premise was false, not the estimate.

**A v3 patch now exists that keeps every identity row and is measurably faster** — the first in this
report, and it changes the "no v3 micro-patch" advice only for this one hot path:
- `v3/v3_pair_count_dispatch.patch.txt` (67 lines, `patch -p1 --fuzz=0`) **dispatches once on the pair
  count (1..4)** into unrolled specialisations instead of re-testing it inside the 32-lane loop, so the
  arithmetic and slot order are unchanged by construction.
- **Identity EXACT on a build from a clean base plus file 5**: all eight bench numbers, all three evals,
  and the **200-opening node sum 27,944,084**.
- **Speed**: bench 2126 → 2092 ms (**+1.6%**); **n=120 real positions, ABBA, fixed `go nodes 200000`,
  node counts matched 120 of 120**: median ratio **0.9878 (+1.2%)**, **107 of 120 positions faster**,
  sign test **p = 1.5e-19**.
- **Recommendation carries its own limit: the author's build is g++ with no `-march` while the owner's is
  clang + `znver5` + PGO**, so this is evidence the patch is *worth* timing on the PC, not a substitute
  for that timing. **+1.2–1.6% is small enough that the real build decides.**

**A withdrawal in the conservative direction, which is the rarer kind.** The same seat first ruled the
patch **NOT MEASURABLE** on the reasoning "the per-position spread (1.30×) is much larger than the
median effect (1.2%), so it cannot be separated from position variation". **That is a category error:
the spread describes how positions differ from EACH OTHER, and a paired ABBA design cancels exactly
that** — each position is its own control, and the correct test is a sign test within pairs.
**Rejecting a result looks like rigour, so this error would have survived review.** The rule: **in a
paired design, between-subject spread is context and the sign test is the test — say which variation a
number describes before comparing two variances.**

**200-opening identity baseline: node sum 27,944,084**, per-position rows committed. Any future patch
must reproduce it exactly. **Pinned provenance, because a second seat could not reproduce it:** it is
seat 08's Step 1b arm, `swarm/08/v3/profile/openings_baseline.txt` (200 per-position rows) and
`swarm/08/v3/REPORT_v3_steps01.md`, measured by `swarm/08/v3/profile_openings.py`. Conditions:
**first 100 of O + first 100 of G**, `ucinewgame` + `isready` before each, `go depth 12`, Threads 1,
Hash 16, PC20's 20 option values plus OwnBook false, test net loaded NNUEArchFile-then-NNUEArch. The
position set is committed as `swarm/08/job1/OG200.fens` (its first two FENs are rows 1 and 2,
110,540 / 126,001). **A reproduction on "the first 200 of set_G" gives 27,762,950 — a 0.65% gap that
is the position set, not a discrepancy, so name the set with the number.** Note the harness
hard-codes `/tmp/o100.fens` as its input path, so a re-run must place `OG200.fens` there.

---

## 6. Measurement rules worth keeping

- **A verifier must be pointed at the document it is verifying, and you prove that by planting a fault in
  that document.** I wrote a seven-check script for this report's own close: tables, trap references,
  section references, citations, row counts, decision rows. It passed cleanly. **Then I planted seven faults
  in a copy and it caught none of them**, because it resolved the report's path from a hardcoded absolute
  location rather than from its own position — **so every copy of the document was equivalent to the
  original and the injection tested the original seven times.** Fixed by resolving relative to the script,
  after which it caught **7 of 7** and passed the clean copy.
  - **This is the "a check that cannot fail is not a check" rule, broken by the script written to enforce
    it**, and it is the most embarrassing instance in this document because the checker looked *more*
    systematic than the one-liners it replaced and was strictly worse: the one-liners used relative paths and
    operated on whatever was in hand.
  - **The form that survives**: plant the fault **in the input the checker is supposed to open**, and
    confirm it fails. Not in a copy you assume it reads — in the one it actually reads, and then verify the
    failure message names the right file and line.
- **`e3b0c442…` is the sha256 of an EMPTY string, and seeing it means your checker produced nothing.**
  Three times in this run a comparison reported that hash against a real file's, and every time the cause
  was the **tool**, not the artefact: a `git cat-file` that errored on a path that did not exist, a missing
  file, an empty `$(...)`. **A hash comparison is a two-sided assertion and only one side was checked.**
  Print both sizes, or assert non-empty before comparing — **an empty artefact and a correct artefact look
  identical to a checker that only compares digests.**
- **And the same lesson in its artefact form: a dry run of your own publish script is worth more than a
  reading of it.** Writing the final report to a git index, I used mode `120000` — a **symlink** — instead of
  `100644`. The script's own assertion ("3 paths differ from `main`, 0 outside the folder") **passed**, because
  a symlink is still a path. The tree would have shipped two broken links and **zero bytes of report**. It was
  caught by running the script and looking at `git ls-tree`, which printed `120000` in a column nobody reads
  until it is wrong. **The blob SIZE is the check: a 400 KB document cannot be a 0-byte symlink target.**
- **A gate you have never tried to move is not a gate, and this audit had never tried.** Four `bench`
  numbers gated every figure in this report, so a seat asked both halves of the question and measured
  each. **The pins are a valid instrument and an invalid certificate.**
  - **They move when they should.** 5 of 5 behavioural mutants shift them, and the shifts are large
    enough to leave no doubt: all 64 `PawnPsqt` weights +40 → `bench 13` **1,003,472** (from 862,329,
    +16.4%); `LmrQuietBase` 85 → 125 → **881,235**; `RfpMargin` 72 → 40 → **601,295** (−30.3%);
    `NullMoveMinDepth` 3 → 99 → **815,534**; `SeePieceValue[Pawn]` 100 → 260 → **901,998**. **Two of
    those are search-behaviour changes rather than eval constants, so the pin is not merely an eval
    checksum.**
  - **They do not move when they should not.** 5 of 5 source-only mutants leave all four pins identical:
    a comment block, two struct members swapped, a local renamed, a dead function added, whitespace
    only. **So the pin is measuring behaviour rather than the build, which is the property that makes it
    worth having at all.**
  - **But 6 of 9 REAL behaviour changes pass a green 4/4 gate**, each with a probe proving the change is
    live. Five of the six are `OwnBook` defaulted off (book lines 20 → 0), `Book Variety` 30 → 0 (book
    reply stable across 20 runs: no → yes), `Threads` default 1 → 2 (Kiwipete d11 **50,541 → 111,175**
    nodes), `Move Overhead` 10 → 200 ms (a 100 ms clock: **depth 6 / 2,789 nodes → depth 1 / 60**), and a
    fifty-move leaf rule moved **one ply** (a clock-98 leaf: **6,064 nodes → 66**). **The sixth is
    `decision #2` in this report** — a drawn root returning the *last* generator move instead of the
    first, invisible because all eight bench FENs carry halfmove clock 0 with no history.
    **The other two blind spots are this report's own shipping decisions: `Threads` (decision #3) and the
    drawn-root bail (decision #2). The instrument that certified both is silent on both.**
  - **The cause is structural, not accidental, and each part is checkable in the source**: `bench`
    constructs `Searcher bench_searcher(16)`, so it **never reads `Hash`, `Threads` or `MultiPV`**; it
    **never enters the UCI `go` branch**, so `parse_limits`, the book probe and the `game_search` gate are
    unreachable; and its eight FENs are all halfmove 0, so the drawn-root path cannot run.
  - **So state the ceiling exactly**: a green pin means *"the evaluation and search constants still
    produce the same tree on 8 middlegame/endgame positions at depth 13"*. It does **not** mean the engine
    still plays chess. **Every "pins matched" line in this report is evidence of invisibility, not of
    safety — the check either could not see the change or was measured not to — and the two are only
    distinguishable where a probe proves the change was live.** That distinction is the difference between
    a control and a decoration, and it is the single most transferable rule in this document.
  - **What the pin still cannot see, as a list of subsystems a reviewer should keep**: the book (all of
    it), threading, the clock (no time-management parameter is read on a depth-limited search), the
    drawn-root path, the entire UCI surface including `parse_limits` and `apply_position`, `MultiPV` and
    the alternate table, any table-size question, and anything above depth 13 on those eight positions.
    Coverage is **63.0% of lines and 59.6% of functions** for `bench 13`, and the missing 37% is not
    random: **22 named functions are reachable by an ordinary client workload and unreachable by the
    pins** — the whole book, `parse_limits`, `apply_position`, `move_to_uci`, `clock_plan_for`,
    `clear_hash`, `perft`.
  - **The Hash trap is the cleanest single demonstration, because it has a live control.** The pin is
    **862,329 at Hash 1, 16, 64, 256 and 1024** — five sizes, one number — while the *same* `setoption`
    sequence moves a real `go depth 14` from **109,247 to 101,640 nodes**. **The control needs its shape
    stated, though, because it is a STEP rather than a trend**: every size from 16 up gives exactly
    101,640, so what it proves is that `setoption` reaches the engine and the first step off Hash 1 is
    real. **The finer-grained evidence is Kiwipete at depth 15, which keeps moving across the whole
    range** — 407,876 at Hash 1, then **402,719 / 402,708 / 402,707 / 402,707** at 16/64/256/1024, so
    the option survives 12 further nodes between 16 and 256 while the pin does not move at all. **So the
    option path is live, `bench` is simply not listening, and a harness that "verified Hash" through
    `bench` verified nothing.**
  - **A replacement gate exists and is cheap**: seven checks in one process, **2.4 s wall**, of which
    **1.9 s is the four pins as they stand**. The five additions cost half a second and cover the drawn
    root, the book, a 100 ms clock, `Threads` liveness, and the fifty-move band. **Every one is proven to
    fire on its own planted fault and on no other check's pass set, and the drawn-root check is proven
    able to PASS** on a repair that costs zero pins — because **a check that can only fail is as useless
    as one that can only pass.** It is a Python harness driving a process, not an engine subcommand, for
    a good reason: editing `uci.cpp` to add one would invalidate the pins the gate reads.
- **`go depth N` node counts are NOT pinnable in a session, and this invalidates a whole class of
  harness.** One FEN, one depth, one process, **four distinct answers**: first search of a fresh process
  **50,541 nodes**; the *same* search issued twice in one process **50,541 → 11,696**; after three
  unrelated searches **72,365**; first target, other searches, then target again **50,541 → 13,235**. A
  **6.19× swing from search order alone** (72,365 over 11,696; the seat writes 6.4×, and the
  max/min over its own five rows is 6.19, so use the computed figure), with a fresh process plus
  `ucinewgame` plus `Clear Hash` returning 50,541. **`bench` is pinnable only because it clears between its
  eight positions — and that clear is load-bearing, proven three ways rather than read from the source**:
  forward and reverse order give 862,329, a fresh searcher per position gives 862,329, and **removing the
  clear gives 956,783**, changes 6 of 8 bestmoves and leaks a mate score (`31997`) from one position into
  the next. **So any harness that pins a `go` node count has pinned the session's history, not the
  engine** — and the 6.19× is what that costs. This report's own rule "one fresh process per cell" (§9b)
  is the same fact from the other side.
- **Adjacency is a check.** Two claims that contradict each other cannot sit next to each other without
  being noticed; separation is what let them survive. **A claim and its correction must be adjacent,
  never separated by sections.** Reordering three sections of one report exposed three contradictions
  the long layout had hidden, including a withdrawn policy reading still stated in the judgement.
  - **But adjacency is a reading discipline, not an automated check.** A grep for figures appearing
    with two values produced only false positives after tuning, because the same words correctly
    describe a *different* defect. **A token-level check cannot separate a claim from a quotation of a
    claim.** Not every good rule automates, and a check that fires on correct usage is worse than none.
  - **A keyword sweep for retired claims is evidence, not proof, and its limit belongs beside the
    result.** Before a close, one seat grepped a reader-facing summary for the keywords of every
    withdrawn claim ("distance", "shallow", "overstates", "endgame only") and got zero — worth having,
    but **a retracted claim phrased without any of those words passes the same sweep.** Say that
    beside the zero rather than letting it read as a clean bill.
- **One phrase can be doing the work of three results, and no audit can see it.** A summary cited three
  findings for the single phrase "costs up to mate-in-5" — but they were a **material loss** (−805 cp,
  robust across four depths), a **mate-in-5 claim whose own solver had failed its control** (the caveat
  never travelled), and a **separate mate-in-ONE** verified by replay against the board.
  **Every individual statement was true and sourced; the error was the joining phrase.** A first-page
  reader took the mate-in-5 as established and could not have known the mate-in-one was a different
  measurement. **This is not an oversight of those checks, it is structural: a citation audit verifies
  existence, a count verifies uniqueness, an exit code verifies execution — each is a claim about a
  different object than the sentence's meaning, so adding more checks of those kinds can never close the
  gap.**
  - **Demonstrated: the same defect was replanted after the fix and all three checks returned exit 0** —
    the citation audit, the document check and the rule check — then the file was restored
    byte-identical. **Every citation in the offending sentence pointed at a real row that says what it
    says.** Nothing in that seat reads joinings.
  - **But a different KIND of check does close part of it, and the distinction matters.** The gap above
    is closed by adding more checks of the same kind; it is **not** closed by a check aimed at a
    different object. When one summary claimed to quote another document "verbatim", the table matched
    byte-for-byte and **the rules were a paraphrase** — the page had grown a longer rule and the summary
    still carried an older wording. **A document asserted a relationship to another document and nothing
    had ever compared the two.** A cross-document comparison closed it, and it was proved by planting a
    one-word paraphrase (`and` → `;`): table YES, rules NO, fail, exit 1.
  - **So the correct statement is narrower than "checks cannot see meaning", and narrower again than
    "equality is mechanisable".** Three boundaries, each measured rather than argued:
    1. **Within a sentence, meaning is not mechanisable by pattern** (the joining-phrase defects).
    2. **A claim relating TWO documents IS mechanisable when the relation is byte equality** — the
       `verbatim` check, proved by a one-word paraphrase.
    3. **But the mechanisable relation is "does this NUMBER agree with that MEASUREMENT", not "does this
       document agree with that document" in general.** When the same page made a second equality claim
       in prose — that a nine-cell eval curve "reproduces exactly" — re-measuring all nine cells settled
       the numbers (every cell matched, zero disagreements) **while the page's own table remained
       asserted**. **A number can be verified against the engine without the prose around it being
       verified against anything.**
  - **The generalisable step is to ENUMERATE the equality claims and check each, rather than stopping at
    the one you tripped over.** That seat found two such claims in one summary; the first was already
    mechanised and the second had never been checked.
  - **Cold reading is therefore the only instrument here with a demonstrated hit rate on this class** —
    three defects in five blocks. It is not a substitute for the checks; it covers what they cannot
    reach.
- **A check written against the sentence you just corrected is satisfied by the sentence you correct it
  to.** The fix is **not** evidence for its replacement. What closes it is a check on **the relation the
  claim asserts**, which is a different predicate from the one that exposed the error — here, "what
  does the recapture take back", not "is the piece attacked".
- **A prose verb can be a decidable predicate over a fixture, which makes the third boundary
  mechanical.** "The piece is attacked before the move" reduces to `is_attacked_by(WHITE, b6)` — true
  at the root, no engine search needed. One seat turned that into 13 assertions (five of them controls
  that must come out the opposite way) and **verified the check can fail** by planting "the queen is a
  knight". **So the boundary has three parts, and the third is the one that stayed closed:**
  1. **within a sentence**, not mechanisable by pattern;
  2. **against an independent source**, mechanisable when the claim reduces to a predicate;
  3. **against the document itself, nothing is mechanisable, because there is no third thing to hold
     two of its own sentences against.** That is where arrangement defects like the implied control
     live, and why they can only be found by reading.
- **A TRUE NUMBER, IN A TRUE SENTENCE, CAN IMPLY AN EXPERIMENT NOBODY RAN.** A table showed
  "4 occurrences → 0 nodes → bail" beside rows for 2 and 3, which reads as a deliberate threshold test
  at 4. **Those cells were failed attempts to hold the count at 3 that produced 4 instead** — the
  source output annotates both with "want 3", and the spacing cannot be varied independently of the
  count. **The number was measured and correct; the table's arrangement implied a control that did not
  exist.** The fix is a label saying the 4 was an attempt at 3.
- **This is a shape, not three incidents: a true number, a true sentence, and a false impression from
  their arrangement.** One phrase doing the work of three results; three true sentences with the
  ordinals running backwards; a table row whose neighbours imply a control that did not exist. **All
  three were invisible to every automated check and all three were found by reading cold** — four
  defects in six blocks, which makes cold reading the highest-yield instrument in the run on this class.
- **ORDINALS ARE A CLAIM ABOUT SEQUENCE, and a section can tell its story out of order with every
  sentence true.** One section described four instances of a defect while labelling only the third and
  fourth, so a reader met "**A third instance**" and then "**A second, smaller instance**" below it, and
  the first two existed as unnumbered prose. **Same family as the joining phrase: each sentence was true
  and the arrangement was wrong.**
  - **The fix took three passes, each found by looking at what the previous pass had done.** Swapping
    and renumbering left the ordinals dangling with no predecessors; labelling the first two then
    exposed that the new "second instance" repeated verbatim what the paragraph below already said;
    merging left one statement instead of two. **Append-in-place, in the editing of a document about
    append-in-place.**
  - **Rule: when renumbering, check that every ordinal has a predecessor, and re-read after each
    edit** — the second edit is where the duplication appears, not the first.
- **A document can pass every consistency check and still support its least important claim best.**
  One reader-facing summary cited **13 findings in its mechanism section and exactly 1 in its cost
  section** — and the cost was the page's headline. **Count the citations per section and look for the
  thin one**; the section whose evidence you never assembled is usually the one you are most sure of.
  - **The limit: citation count is not evidence quality.** A section can cite many findings that do
    not support it. What the count catches is an imbalance, not a proof of adequacy — state it that
    way.
  - **The same figure written two ways in one document is the smallest instance of a number outliving
    its correction** (a range appearing three times, twice hyphenated and once with an en-dash). One
    command removes it, and it is worth one command.
- **A guard that reports a confident wrong answer is worse than one that reports nothing**, because the
  wrong answer looks like verification. **Make "found nothing that looks like the subject" a failure, and
  identify the subject by its contents against what the engine advertises, never by its source shape.**
- **`searchmoves <all legal moves>` is not a no-op control.** It changed the reported best move in 6 of 25
  at depth 10 and **5 of 15 (33%) at depth 12** — the effect grows with depth — and two of the cases were
  score-tied and still picked differently. The restriction reorders equal-scoring moves, so it perturbs
  search order rather than evaluation. **Its failure is silent: the baseline looks like the unrestricted
  search and is not.** Any harness that used it as a no-op baseline has a broken control.
- **A pinned move cannot verify a move.** Pinning the expected best move makes the "same move" check
  vacuous by construction, and the score is wrong in every position tested (0 of 25 agreed, |Δ| ≥ 10 cp in
  14 of 25). **A corpus built by "pin the move, record the score" has a move check worth nothing and a
  score that is not the engine's score.**
- **A fix that makes a CONTROL valid does not make a MEASUREMENT valid — now measured, not argued.**
  Restoring the root TT store makes `<all legal>` a true no-op (60 of 60). **It does NOT repair a pinned
  score**: 53 positions, 265 pairs, depth 12 — `pinned − intree` is identical in **9 of 265** after the
  patch against **10 of 265** before (the control reproduces the original), **mean −5.5 vs −7.6, sd 47
  cp**; exact McNemar on discordant pairs **8 fixed, 9 broken, p = 1.0000.**
  - **So the patch is a control-restorer, not a measurement-restorer**, and a single-move root remains a
    different search. **A one-line fix that rescues your baseline is not evidence it rescues your numbers**
    — those are two separate measurements and only the first had been run.
  - **And it does not rescue a 3- or 5-candidate RANKING either**, measured paired on the 51 positions both
    builds validate (each run's own reference filters, so the sets differ and pairing is mandatory):

    | ref | k | pairs | base | patched | fixed | broke | McNemar p |
    |---|---|---|---|---|---|---|---|
    | R1 | 3 | 122 | 110 | 112 | 7 | 5 | 0.7744 |
    | R3 | 3 | 122 | 110 | 115 | 9 | 4 | 0.2668 |
    | R1 | 5 | 386 | 367 | 367 | 11 | 11 | 1.0000 |
    | R3 | 5 | 386 | 366 | 368 | 14 | 12 | 0.8450 |

    **Every patched interval stays below 1.0 and every discordant split is near even**, so the ranking defect
    lives in the one-move root's **score**, not in the root TT store.
  - **The null is stated with its own limits rather than over-claimed**: **power is low at k=2 (39 pairs)**,
    and **the two references disagree on direction at k=3** (R1 +2, R3 +5), so the file says **"no effect
    detected at these sample sizes"**, not "no effect exists". **A null is exactly what an author is most
    tempted to over-claim.**
  - **And the seat's handling of a near-significant subgroup is the model**: the top move alone moved
    1/53 → 6/53 (5 fixed, 0 broken, **two-sided p = 0.0625**), which does **not** clear 0.05, **and the
    subgroup was chosen after seeing the full-set result.** Recorded as a **lead for a pre-registered run on
    a fresh position set**, explicitly not a finding, **with the tool printing that warning beside the
    number so it cannot be quoted as confirmatory.**
- **A comparison of two candidates, both pinned identically, is sound ONLY AT A LARGE GAP — and the
  "8 of 8" that supported it was a large-gap sample.** Measured properly over 3- and 5-candidate sets:
  **3 candidates agree 142/159 pairs (CI 0.835–0.932); 5 candidates 486/530 (0.890–0.938); both intervals
  exclude 1.0, so pinning does NOT preserve rank order beyond two candidates.** The two-candidate case is
  sound when the gap is wide — **313/317 = 0.987 at ≥100 cp, 478/511 = 0.935 at ≥10 cp, and the k=2
  interval reaches 0.959 so a true 0.95 is not excluded** — but it does not license 3-way or 5-way
  comparison, nor the top pair at 10 cp.
  - **Reference-free confirmation**: pinning each of the top 5 alone makes the plain bestmove the
    top-scoring candidate in only **49/60**, and in **11/60** some other candidate beats it.
  - **`mate` is the ONLY limit flag that changes the search tree, which makes the node ratio a diagnosable
    fingerprint.** On one board at the same reported depth 7: `go depth 7` gives `d4c5` cp −33 / 3,411
    nodes; **`go depth 7 ponder` gives the SAME tree and the same numbers** (only the bestmove is withheld);
    **`go softnodes 1000000` and `go nodes 1000000` both search deeper exactly as asked**; **`go mate 4` gives
    a different move at 556,387 nodes — 163×.** **So a node count 100× above its depth peers is a usable
    after-the-fact fingerprint for spotting a mate-labelled row in an existing corpus**, without any
    provenance of the run that produced it.
  - **The mechanism is not tie-reordering: it is ONE LINE. `search.cpp:2093` suppresses the root TT store
    under a restriction.** Restoring that line in a scratch build gives **60 of 60 bestmoves and 60 of 60
    scores** identical to the unrestricted search (IIR alone: 51/60 and 7/60).
  - **And a pin is fully distorted at k=1 — there is no "pin just the winner" escape.** |Δ| ≥ 10 cp in
    48/47/45/44/46 of 60 for k = 1/2/4/8/all; a pinned score equals its in-tree score in only **10 of 265**
    pairs (sd 44 cp).
  - Know which of the three uses you are making: absolute recording (unusable), move verification
    (vacuous), **two-candidate comparison with both arms pinned at a ≥100 cp gap (usable)**. Anything wider
    is not established.
- **A cap test needs a rising-series control.** "Respected the cap" is equally consistent with "ignored
  the budget and searched a fixed amount" unless rising budgets produce rising work. **The controls are
  the product; the numbers are downstream of them.** Seven checks in one seat in a few hours were made
  meaningful by their control rather than their result.
- **A control must search for a case that differs, and a run that cannot demonstrate a difference must
  invalidate itself rather than having the control waived.** A first version assumed "one move later"
  guarantees a different perft, got the identical value, and the script printed VOID and refused to
  report the zero — only after the control searched until it found 400 vs 440 was the result admissible.
  A control that is assumed rather than found is the same family as a matcher that prints "2 options"
  and an exit status read through a pipe: all three appear to run and do not.
- **A defect's blast radius is a different question from the defect, and has to be measured rather than
  inferred.** Two questions to keep separate: **(1) what does it corrupt? (2) who consumes exactly that?**
  The second is an empirical question about the consumers and it is cheap to answer — but it is the one
  most likely to be skipped, because the first feels like it implies the second.
  - Two cases in one night where the same shortcut failed in OPPOSITE directions. **False alarm:** "any seat using `searchmoves` is affected" — measured, a two-candidate comparison with both arms pinned is sound (rank order 8/8), so the alarm would have voided a valid cross-seat result. **False comfort:** "the base cells agree, so the harnesses are identical" — true only for the one axis those cells can see.
- **A static checker certifies the CONFIGURATION A HARNESS BUILDS, not that it is the configuration the
  FINDING NEEDS.** An honest silence and a false negative are indistinguishable from the tool's output;
  the difference lives in the claim, not the code. Five harnesses reported "no option list" in a sweep,
  and one of them legitimately sends only Hash and Threads because its finding compares three builds.
  **Pair every sweep with one line of the accompanying finding** — the tool establishes what was built,
  the claim establishes whether that was the right thing to build.
- **"I could not evaluate this" must never be reported as "this is fine".** A count checker silently
  skipped a number word outside its own vocabulary, so neither a pass nor a fail was produced — and the
  silence read as a pass. **A check that declines to evaluate has not cleared anything**, and the
  distinction has to be a third verdict rather than folded into either existing one.
  - **The same holds for a test of the check itself**: a negative test passes for the wrong reason when
    the planted fault is written in a form the checker never parses, because no comparison ran. Both
    failures are the scope half of this section, one level up.
- **A drop-one ablation tests NECESSITY in the bundle; an add-one ablation tests SUFFICIENCY from the
  baseline.** A drop-one design cannot see a redundant option, and a bundle result cannot name the
  option responsible. Run both directions before attributing an effect to a switch.
- **Before looking at the numbers, state for each row whether "unchanged" supports or refutes the
  hypothesis.** A table can be arithmetically correct and read backwards — three instances in one night.
- **A crash in a detection harness manufactures positive evidence.** A vacuous pass at least leaves the
  honest reading available ("no problem found"); a harness that was built to prove it can detect, and
  instead dies on an undefined name, looks like a detection. **That is the worst thing a broken check can
  do, and it is why the rule written for other seats must be run over the author's own folder.**
- **A RULE HEADLINE IS A SUMMARY OF THE RULE, and the summary is where the hedge gets dropped.** Judging a
  rules section by its headlines counts **what the rules are called**, not **what they establish** — a
  keyword pass over one 67-rule section classified **12 as imperative and 4 as evidence-phrased**, which read
  as a condemnation, while **counting bodies showed 66 of 67 cite a concrete case or figure.**
  **Measure the layer that carries the property.**
- **A checker that judges the TEXT of a thing instead of the thing has failed in four media:** a
  configuration judged by its **variable name**; a configuration judged by a **sentence** claiming
  "22 options asserted"; an option list judged by its **Python shape**; and an undefined exception
  judged by **raw text** including docstrings, which reported a checker and its own documentation as
  broken because the comments *described* the bug.
  - **Every one was caught by running the checker on a case whose answer was already known** — an
    object defined on a known line, a planted failure, four measured engine cells, a file with no
    option list. **None was caught by reading the checker.** *A checker is tested by giving it a case
    you already know the answer to, never by reviewing its logic.*
- **A checker only guards the FORMS it knows, and the most load-bearing figure is often written in a
  form nobody taught it.** One seat's arithmetic checker scanned `A -> B = Rx` in one directory; the
  decomposition carrying the report's headline per-node number was published as a **product** and a
  **quotient** in another. **The two figures the report leans on hardest were the two with no
  automatic check**, while the same numbers inline on other pages were checked.
  - **And the arithmetic check would not have saved this section even once it existed.** The product
    that was published closed to 0.1% using a node ratio that appears in **neither** of the source's
    columns. **Arithmetic closure is not evidence that the terms are the right terms** — the pairing
    of each term to its column needs a separate label check, and that is what caught it.
  - **Fix is a form audit, not more patterns**: enumerate the ways a claim of this kind can be written
    and teach the checker each. Seat 01 enumerated **five forms and what checks each**:

    | form | example | checked by |
    |---|---|---|
    | difference | `A − B = C` | nothing (no instance; no untested branch added) |
    | product | `A × B = C` | `check_identities.py` (seat 01, branch `for-fable-and-opus/swarm-01`, `forge-combo29/swarm/01/`) |
    | quotient | `A / B = C` | `check_identities.py`, same path |
    | ratio in prose | "the saving is 8.69%" with the operands three lines away | **nothing** |
    | table row | the terms and the result on separate lines | **nothing** |

    **The two script names in this table, and the profile parser and `gprof` listing cited earlier in this
    section, live on the earlier `for-fable-and-opus/*` lineage rather than on this run's `swarm/*`
    branches, and their exact paths are given so the citation resolves** — a filename with no branch is a
    pointer that cannot be followed, which is the same defect as a figure with no artefact.

    **Form 4 was attempted, abandoned, and then rebuilt successfully — the sequence is the finding.**
    The first attempt produced 16 findings on the author's own pages; all were assumed false positives,
    two were hand-checked, and **one was real** — a headline ratio paired with a savings percentage
    that does not follow from it. The other 15 were the checker's own error, so it was deleted on the
    reasoning that **a checker whose output is mostly its own error teaches the reader to skip it**.
    **The abandonment was wrong, and the reason it was wrong is the transferable part:**
    - The first attempt **inferred the relation from PROXIMITY** (a ratio and a percentage near each
      other), which is inventing an identity from adjacency. **The rebuilt version reads the relation
      from the GRAMMAR**: it matches only `ratio (percent direction)` — one parenthetical — after
      stripping quoted regions. The three false-positive shapes are excluded by construction, not by
      tolerance: `92.7%` beside a count of `92.7` (a count is not a ratio), a range with no single
      percentage, and a first decimal mistaken for the ratio.
    - It now examines 6 claims and gates. **Proven by restoring the fabricated pair into the source
      page:** it reports `ratio 0.9090 with 'fewer' implies 9.10%, but the line says 12.40%` and exits
      1; corrected, exit 0. **The checker that found the error now prevents its return.**
    - **The lesson is not "prose cannot be checked" but "prose can be checked where the grammar states
      the relation."** Only the operands-elsewhere sub-form remains a named gap, because there the
      relation genuinely must be inferred.
  - **And the complement, established by a second attempt that was deleted BEFORE shipping: a claim
    whose truth depends on the MEANING of a sentence is not mechanisable by pattern.** That seat tried
    three models to find "is this finding retired?" and all three failed on the same root cause, that
    its vocabulary did not match how the table records retirement:
    | model | assumption | failure |
    |---|---|---|
    | 1 | a retirement word in a row retires that row's id | flagged a row that retires **one of five** positions |
    | 2 | the marker sits in the row's head cell | found **1** id — **no row retires itself** |
    | 3 | a later row naming an earlier id with a retirement phrase | found **64**, because `CONFIRMS` and `corrects` both match `CORRECT` |

    Model 3 is the decisive one: **"retired" and "confirmed with a correction" are different states, and
    no regex separates them without reading the sentence.**
  - **The decision rule between the two outcomes, which is worth more than either: delete the checker
    when the sample is mostly its own error; keep it when the true positive is real and the false ones
    are separable by GRAMMAR.** Form 4 was the second case and survives; the retirement checker was the
    first and was withdrawn before it could mislead anyone.

    **The two forms that seat used MOST are the two nothing verifies**, and it had not noticed until
    the list was written down. Coverage was then **verified rather than asserted** — each pattern was
    tested against a sample line: matching the product, not matching a table row, not matching a
    difference.
  - **Split across table rows is the same defect as unformatted**: when the decomposition was broken
    into three table cells, no checker could see the identity at all. **A page's central claim should
    appear in its checkable form at least once**, with the reason stated beside it.
  - **The enumeration found the same defect in the tooling that was meant to catch it:** a page-shape
    checker's `DEFAULT` was a hand-written list of 11 pages, so the new notes page would have been
    invisible to any manual run — **the generated-list omission in its mildest form, inside a tool
    written to catch that class.** The gate was never affected because it globs explicitly; the
    default now derives from a glob and covers 19 pages. **Deriving a default finds an import bug
    that a hard-coded list never would.**
- **A doubled count is the same class as a zero count: a number that does not mean what it says.** A
  glob over `.` plus each subdirectory examined every identity twice and printed every defect twice.
  Most checkers carry a zero-guard and almost none carry a double-guard. **Assert the exact expected
  count, not a minimum.**
- **An arithmetic checker proves the arithmetic closes, not that the terms are the right terms.** A
  correct product of wrong inputs passes. That limit belongs in the tool's own output, where its
  silence will be read as a verdict.
- **A control cell proves only what its axis can see.** A cell invariant across the configurations under
  test shows those configurations differ nowhere that cell is sensitive — no more. Base-build cells
  could not differ under the PC switches because the base build does not advertise those options at all;
  the same cells would have agreed across a Hash difference and licensed the wrong conclusion.
  **When quoting a control cell, say which axis it controls for.**
- **A guard that lives beside the pipeline instead of inside it is worse than a missing guard: its
  existence makes the claim feel verified.** Fix is proximity, not diligence.
- **A wrong label does not stay in its own file.** It propagates through whoever trusts it, including
  the coordinator.
- **Bench is valid for** pins, determinism, ablation direction, structural counters, and the pooled
  effect of one isolated toggle. **Not valid for** per-node cost or the aggregate PC20 set.
  Always report the per-position spread, on the headline line.
- **Bench's bias is patch-specific, not directional** — it may understate, match or overstate.
  Measure on real positions once if the number matters.
- **Three measured bench failure modes, each with its own case:**
  | quantity | bench says | real positions say | case |
  |---|---|---|---|
  | per-node cost | ~1.2% | **~6.4%** (6× optimistic) | 19-C35 vs 19-C53 |
  | aggregate node-count sign | +14.5 / −10.6 / +8.7 across benches 11/13/16 | **−8.7%** | 19-C55 |
  | a profile's self-time share | 2.71% | **0.66%, CI [0.9845, 1.0023]** | 19-F6 vs 19-C64 |

  **A self-time percentage is not a transferable cost unless someone removes the code and measures
  it.** Any seat reasoning from a profile share should read that row before quoting it.
- **An underpowered null that happens to be correct is still correct.** One seat criticised its own
  earlier null as underpowered, then found the effect it "should" have detected does not exist on real
  positions. **The criticism of the power was right and the conclusion was wrong — those are
  independent facts about a null.**
- **Any speed number from fewer than ten positions is a hypothesis, never a result.** Two out of
  two small samples in this harness erred upward, once by 4×.
- **A check must report how many rows it examined.** A pooled-spread check examined zero lines and
  passed because its regex matched only the literal word "pooled".
- **The mechanism is rarely the problem; the scope is.** Check failures tonight split into two
  families: **status did not propagate** (the check examined the right thing and its verdict never
  reached the caller) and **selector too narrow** (a markdown glob while evidence is `.txt`,
  membership without pairing, a regex matching a word the files never use).
- **Discriminant: feed the check an input you know is bad and confirm it still fails.** Passes → the
  fault is in the status. Fails but misses a real defect → the fault is in the scope.
- **A check can print failure and still exit zero, and a gate that tests `$?` then believes it
  passed.** One seat's document checker ended with `print("VERDICT: ...")` and no `sys.exit`, so its
  exit status was always 0; a section was deleted, the checker printed `DROP (was 9)` and **the commit
  landed anyway**. **A failing report read as a pass** — the check's output said failure while the gate's
  own status said success, which is the same defect class as a guard that lives beside the pipeline.
  - **Why it survived a "gate proved" claim:** that proof exercised a malformed findings row, caught by
    a *different* checker which does exit nonzero. **The gate was proved on the one failure mode that
    happened to work**, and the claim generalised from it. **Prove a gate once per checker it invokes,
    not once per gate.**
  - **The fix is one line** (`sys.exit(0 if ok else 1)`) and the proof is the same deletion now
    printing `VERDICT: FAIL`, `pre-commit: BLOCKED`, and `git log` showing the commit did not land.
    **A gate claim is only as broad as the number of its members that have been individually shown to
    fail.**
  - **It happened twice, in two seats, on the same night**: a second seat found **two of its three**
    structural checkers never exited nonzero on failure, so "gate live and proved" was true for one of
    three until it was checked member by member.
  - **And the test of the fix can pass for the wrong reason.** Proving a checker could fail, one seat's
    *test* used a number word **outside that checker's vocabulary** ("thirty" absent from its finite
    word list), so the regex matched no number, **no comparison happened at all**, and the test passed
    at exit 0. **A negative test has to be shown to have reached the comparison**, which means the
    planted input must use a form the checker actually parses — the same scope question as ever, one
    level up.
  - **A PARSER fault is silent unless the ROW COUNT is asserted, and the guard existing in one script but
    not another is what makes it visible.** A bulk re-indent left `rows.append(...)` **outside** its `if m:`,
    so two scripts parsed **1 and 8 rows instead of 180 and 464** — and one of them **still printed a
    complete, plausible set of ratios from the survivors.** The other script's `expected 180` guard caught
    it; the second had **no row-count assertion at all** and was fixed by adding `expected 464` and proving
    it with a truncated fixture.
    - **Any seat parsing a committed artefact should assert its `n`.** This is the
      "declines-to-evaluate-reads-as-a-pass" rule at the parsing layer.
  - **A static analyser found a fault that running the harness did not.** A SonarCloud Reliability gate
    failed on **six lines of unreachable code after a `return`**, including a **second `_scan_fen(...)`
    call that never executed** — a duplicate of the guard that aborts on an invalid-FEN line. **The live
    copy above the return kept behaviour correct, so no verdict was affected**, and it was removed rather
    than suppressed. **An unreachable duplicate of a safety check is the "appears to run and does not"
    class**, and it is the fourth fault in that seat's own code, the first found by analysis rather than
    by a timeout.
  - **The same audit one level out found two scripts the report tells a reader to RUN that could not
    fail**: both printed `FAIL`/`NO` and exited 0, so a stated result ("11 of 11 agree") was a sentence
    no code produced. **Any script cited as evidence must be tested for its exit code, not just its
    output.**
  - **And five scripts had verdicts that depended on the DIRECTORY they were run from - including all
    three gate checkers**, via `HERE = os.path.abspath(os.getcwd())`, which reads like path hygiene and
    is precisely the bug. **The git hook `cd`s first, so the gate was never affected; a reader following
    the documented one-liners was.** In that state a document checker read the summary through
    `open(p).read() if os.path.exists(p) else ''`, so it **compared an empty string to an empty string
    and reported verbatim agreement.**
    - **A verdict that depends on where you stand is not a verdict.** The fix is to anchor every script
      to `__file__`, and to run each one **twice - from its own directory and from `/tmp` - failing if
      either run fails or the two verdicts disagree.**
    - **The empty-string fallback is the general form of the danger**: any `exists() else ''` turns a
      missing subject into a vacuous agreement, which is the absence-read-as-success trap in a single
      expression.
- **The family has three members and one rule.** A selector that matched **zero rows**, a list that
  **lost a member**, and a vocabulary that **lacks the word** are the same defect: **all three report
  PASS where they should report UNKNOWN, and all three are fixed by making the absence visible.**
  - **The rule in the form that implies a fix: "Any finite vocabulary has a boundary, and past it the
    check reports PASS rather than UNKNOWN."** The weaker phrasing — "the selector was the problem" —
    names the *location* of the fault instead of its *behaviour at the edge*, and implies no fix.
  - **Applied to a real checker:** a ratio checker had a silent `continue` for a matched pattern whose
    number is not a ratio. The skip is now **counted and reported** — a crafted input prints
    `matched but not evaluable …: 1` beside the zero-count FAIL — so "nothing matched" and "it matched
    and I could not evaluate" are distinguishable numbers rather than the same silence.
  - **The same distinction applied to one result, and it is the sharper form: a check proven only
    against an INJECTED defect is a proof of FUNCTION, not of NEED.** Three instruments point at one
    decomposition — two identity checkers that have never fired on a real defect, and a ratio checker
    that caught a fabricated term. **So the honest count is three instruments, one of which has fired,
    and a reader should weigh the result by that rather than by how many checks stand behind it.**
    Said plainly this is more useful than implying three; it does not weaken the two, it locates them.
- **The gate self-test is the bad-input test applied to every checker on every run**, which is why
  the status family cannot return unnoticed.
- **Passes are not evidence of equal strength, and a gate's uniform output hides that.** One gate of 14
  checks: **12 have caught something real** in the record, and **2 have never fired on anything but a
  planted defect**. Neither is grounds for deletion — **an unproven checker and a proven-clean subject
  look identical from outside**, and the difference is whether the check has ever fired on something it
  did not plant. **Report the split, or the gate's list of `ok`s implies fourteen equally-evidenced
  checks.** The output that matters is the one telling you what a check has *done*, not the one telling
  you it found nothing.
- **Reliance and verification are independent, and the most correct rule can have zero coverage.** One
  seat audited the three things its summary leans on and got three different states: the decomposition
  (two checkers with **0 real catches**, one with **1** — proof of function); the **gate self-test**
  (ten assertions whose three recorded fires were **all the author's own deliberate regressions**, so it
  has worked three times and **never been necessary**); and the **bench rules**, which are
  **enforced by nothing at all**.
  - **The bench case is the clearest in the record of a correct rule with no check behind it.** The
    summary states what bench may and may not be used for, the sign flip was measured to a tenth of a
    point — and **no check reads a bench claim**; the gate's only bench step is an opt-in determinism
    pin. **Not building the enforcement was the right call, because it needs the intent-parsing that
    failed three times tonight; recording the gap is the honest alternative to a bad check.**
  - **A self-test firing only on deliberate regressions is a proof of function, not of need** — and
    regression is rare by construction, so this is expected rather than damning. **The point is to say
    which of the two you have.**
- **When a checker misfires on your text, the first question is whether your text is the problem.**
  One seat spent **four rounds** narrowing a page-shape pattern — end-anchoring, start-anchoring, a dash
  lookahead, an explicit subject list — before realising its new heading simply **contained the words
  the rule looks for**. **Each attempt was a judgement about meaning dressed as a pattern**, and one of
  them **regressed an existing page**, caught only by running the gate over all pages. **The correct fix
  was renaming the heading.** The rule was fine; the text collided with its vocabulary.
- **An update covering the occurrences you thought of will miss the one you did not — including inside
  the tool written to prevent it.** One seat's count-sync script rewrote **two of the three** places its
  summary stated the row count and left the third at the old value; the checker missed it because **it
  compares only the sentence shape it knows**. A tool built because prose counts go stale had a stale
  count of its own.
  - **The repair is the transferable part: after rewriting, print every surviving candidate for
    human review** — that seat now prints all 28 remaining bare 3-digit figures and notes which are
    legitimate. **Reporting the population rather than claiming completeness is stronger than "done".**
- **A count is itself a claim, and it can be false while every item it counts is true.** A findings
  table reported 228 rows against a reported 227; `uniq -d` on the id column found one id twice — a
  stale draft beside its fuller replacement, same board and same conclusion, so both rows were valid
  and only the total was wrong. **No existing check looked for it**: the shape check counts cells and
  the evidence check resolves paths, and neither cares whether two rows share a name. The audit now
  hard-fails on a duplicate id, proved by planting one.
  - **The tell that was present and dismissed:** the count had crept by one between two messages and
    the seat attributed it to a double-write rather than checking. **A count that changes without an
    accountable operation is a symptom, not a rounding error.**
  - **And say what the count measures, or a reader will over-read it.** One summary states its totals
    as **separate row types** — `F` rows are that seat's own measurements, `C` rows are checks of other
    seats' claims — **additive as rows, not as findings**, with the letter agreeing with the row shape
    (F rows carry an area column, C rows do not). Beside it: **"N rows, 0 duplicates" is a claim about
    the FILE, checked mechanically on every commit — not a claim that N separate claims are each
    correct.** That second thing is what the evidence cells are for, and they are checked only to the
    extent that a path resolves.
  - **A total written INSIDE the row that changes the total is wrong by one whichever value you
    choose.** The row that documents the count also increments it, so at the moment the row is written
    the stated figure cannot be right: it was either counted before the row existed, or the correction
    itself changed the number again. **There is no correct value for such a row to state, so it should
    state none and say why.** The only stable forms are a count computed after the row exists, or a
    figure a script printed.
  - **Every one of seven observed count drifts was in a MESSAGE, never in a file.** A file has a check
    comparing its sentence against the source on every commit; a message has nothing, and the author
    carries the number in working memory across twenty minutes of edits. **The practical rule is
    narrow: recompute immediately before quoting, or quote what a script just printed.**
  - **A running count moves, so it must be checked WHERE IT IS QUOTED.** That seat's total went
    230 → 232 → 234 → 236 within twenty minutes, and a summary quoting a stale figure is wrong for the
    same reason a stale number always is. Its checker **recomputes the summary's stated counts and fails
    on a mismatch.**
  - **It has now blocked its own author three times**, and each time for the same reason: the commit
    adding a row that documents count-staleness also incremented the count, so the summary's sentence
    about the count became false **in the same edit that added the row about it**. **A rule whose own
    documentation keeps tripping it is a rule that is actually being enforced.** The fix each time was
    to recompute from the file rather than edit the number by hand, which is what the check enforces.
- **Mutation testing automates the scope half for CONTENT; file and directory coverage stay
  imagination-only.** A file a check already tests contains correctly-shaped instances: lift one,
  mutate it in a way that must flip the verdict, require the check to fail. The subject supplies the
  input that its author could not imagine. A mutation cannot reveal a file the check never opened.
  - **Recipe:** take a real line from a file the check passes; apply the **smallest** change that must
    flip the verdict (a large change can trip any selector for the wrong reason); assert the check
    fails; restore and confirm it passes. Classes implemented: numeric off-by-one, cell added, marker
    stripped, token substituted.
  - **Path substitution is now implemented and gating, for its automatable half.** Place a defect at a
    path a check is asked to scan but in a format it might not glob, and require the check to find it.
    Proven to fire: reverting the probe to a `*.md`-only selector fails with `the glob lost *.txt
    again (found: [])` — the same empty list that demonstrated the original shipped-artifact cost.
    Four cases, each reporting a **verdict kind** rather than a bare pass: found; **known limit**
    (two levels deep, one-level glob cannot see it); fails via its zero-count guard; and **N/A by
    shape** (a check taking its file as an argument, so coverage is the caller's choice). A literal
    `EXPECTED_CASES = 4` makes a dropped case fail rather than pass quietly.
  - **The residual is stated rather than hidden:** this tests whether a check reaches a given
    **format** in a given **directory**. It cannot tell whether a check **ought** to scan a directory
    nobody thought of. **Format-and-directory reach is now testable; which directories should exist
    is still imagination.**
- **A correction that adds without removing is not a correction.** Same mechanism as the stale
  number: the new claim is written, the old one stays standing in the same section, and the reader
  meets both. **Three separate instances are recorded below, which is itself an instance** — and the
  first two were standing next to this one until a duplicate check found them.
  - **The coordinator did it while writing this very rule.** A defect entry was rewritten from
    "splices" to "truncates" by **replacing the heading and appending the new evidence, while the old
    sentence ("and then applies `e7e5` anyway") stayed standing three lines above the perft-3 result
    that refutes it** — so **a reader who stopped at the first sentence got the opposite answer from a
    reader who continued.** Two further cosmetic survivors in the same edit: a count list printed
    twice in adjacent sentences, and a range label that only made sense if the reader inferred the
    sequence length. **The tell: after correcting an entry, read it TOP TO BOTTOM as a stranger**,
    because the editor's eye skips the sentence it did not touch.
  - **The row ABOUT the correction is where the survivor hides**, because a row that documents its own
    correction **makes the finding look maintained** and a skimmer reads the qualifier as a footnote.
    **The pattern is self-camouflaging, which is why it needs a tool rather than attention**: one seat
    fixed the exact sentence it was shown and **left a second instance three sentences later in the
    same row**, which a sweep for rows asserting an unqualified absolute while pointing at a later
    finding id then caught.
  - **And a detector for this will always fire on the text that retires it**, because the corrected
    sentence contains the offending words inside the clause explaining why they are wrong. The
    qualifier set had to accept self-rejecting forms (`not … none`, `often no`, `only N of M`).
  - **An edit has two operations and the second is the one that gets skipped: adding is an authoring
    act, removing is a search act, and a search only works if you look for what you wrote.** Write
    both in one edit so no window exists where both stand; then grep for the phrase you contradicted.
  - **The same failure exists inside the edit itself, and that is where it is hardest to see.** An
    *insert that is not a checked insert* silently replaces rather than adds — the markdown stays
    valid, the section still reads fluently, and only the missing paragraph knows. It happened while
    editing the section about this very rule, which is the tell rather than the exception.
  - **The mechanical guard: an add-only edit cannot decrease a count.** Keep a heading-count baseline
    per document and fail on a drop (a rise is fine — documents grow). Proven by deleting a whole
    section: the check prints the old baseline, the new count and `<-- DROP`, and restores the file
    byte-identical. **Its two limits belong beside it**: a baseline is a snapshot, so a section deleted
    before it was recorded is invisible, and a **paragraph deleted inside a surviving section still
    needs a re-read** — the count catches a missing section, not a missing paragraph.
- **Forcing a claim into an enumerated form is a verification act.** The missing item has no function
  to point at, which is why enumerating found a table row that was never built. Generate the list
  from the work, never recall it. But **enumeration only proves an item was built, not that it is
  correctly stated** — that needs cross-checking against something on disk. A generated list's own
  failure is a silent omission, so apply the zero-count guard to the generator too.
- **The artifact examining fewer things than you thought is one class, not several.** A selector that
  matched zero rows and a list that holds fewer items than expected are the same failure: the output
  reads as success, and the only evidence is a number the report states about itself.
- **Fix: print the count of things examined beside the verdict.** When a test enumerates its cases,
  assert the length against an **expected count written as a literal, never computed from the list it
  guards** — otherwise the count always matches and the bug is rebuilt somewhere new.
- **A check satisfied by construction reads exactly like a check that passed.** `if len(results) !=
  len(results)` printed `classes run: 3 (expected 4)` and returned success: the guard passed while its
  own output showed it should not have. Write the literal once and use it in both the report line and
  the assertion.
- **When two habits are offered, the preventing one goes first.** Write the correction and the removal
  in one edit (which prevents the stale claim existing at all); grep for the phrase you contradicted
  (which detects it if you did not).
- **An `&&` chain is a claim that every step ran, and it can be true by omission.** A failed clone
  short-circuited the steps that mattered, and a trailing fallback printed success. **Print what ran,
  not just whether anything failed** — inside a work tree? which branch? what did the config read
  back? — so a short-circuit shows as a missing line rather than a confident negative.
- **The same failure exists without `&&`.** A Python heredoc raised an error, wrote nothing, and a
  `git commit` in the same invocation succeeded carrying only the script. **Repair: put the edit in a
  named script that asserts the old text is present, run it separately, verify the result before
  committing.**
- **In-band versus out-of-band decides which check can see a defect.** Three pipe defects were
  in-band and a cell-wise check caught them; a leaked line of shell script is in no cell, so no
  cell-wise check could ever see it. Repairing that needs a check on out-of-band content.
- **A guard that fires on documentation is worse than none, because it trains you to ignore it.**
  A leak guard had to become fence-aware for exactly this reason, and the extremum check had to be
  narrowed to rows that make an extremum claim. Same object at different sizes.
  - **A narrowed check that is not re-proved is indistinguishable from a removed one.** Narrowing is
    the operation that looks like progress and can silently disable; re-prove every direction after.
  - **The documented-example false positive:** a check flags the sentence that describes the check.
    Tell: the offending line is always one you just wrote. Fix: narrow, then re-prove.
  - **A control built for a condition NOBODY HAS EVER HIT will contain a bug on that path, because it is the
  only path never exercised.** A provenance tool gained a branch for "no common ancestor" — and that
  branch had a one-line unpacking bug (`mb, _out, _err = git(...)` put the **exit code** into `mb`), which
  crashed with `'int' object is not subscriptable` **the first time a genuinely disjoint history was
  constructed to test it**. The code that handles the rare condition is the code that has never run.
  - **This is why a control for a rare condition has to be CONSTRUCTED, not waited for**: an orphan-branch
    repository takes a minute to make, and it was the only thing that could have found that line.
  - **It is also the fourth time a checker in this seat reproduced the defect class it exists to catch**,
    and the first where the bug lived in the branch written to handle the very condition the control
    creates.
- **A TOOL THAT REPRODUCES THE DEFECT IT WAS BUILT TO DETECT is the run's most repeated pattern, and it
  always happens on the first run.** A provenance checker built to catch a wrong-commit build reported
  STALE BUILD against a good binary, because its exclusion list named five build directories by hand and
  walked into a sixth. **That is the third such case in one seat** (a DTM solver's empty tables, an
  output-collision detector's own filter, the provenance tool's false staleness), and every one was found
  by running it on a case with a known answer.
  - **The specific lesson: exclude build output by PREFIX, never by naming the directories you happen to
    have.** A hand-listed set is the generated-list omission again, and here it fired on a file CMake
    writes at configure time — **later than the binary**, which is exactly what the staleness test reads.
- **A checker written in the same language as the documents it inspects is always vulnerable, so
    the stable defence is a planted failing case that runs every time, not cleverer patterns.**
  - **A checker that only parses the form the GENERATOR produces cannot catch a human edit to the
    generator's output — and that is the only edit that ever creates this defect.** One advice checker
    recognised only "N MB at M lines" and **missed 2 of 6 hand-written permissive phrasings**; the
    serious miss was a comparison-first clause (`at 6 lines, Hash <= 256`), **exactly how a person would
    hand-edit a boundary**. It now parses number-first, comparison-first and bare-number forms.
  - **Its selftest rejects six permissive phrasings AND accepts two correct ones — the second half
    matters.** A checker that rejects everything is as useless as one that misses everything, and the
    same seat had already hit that trap earlier in the task, where its first PV check rejected a legal
    line.
  - **One hole is printed on every run rather than left implicit: a spelled-out line count ("six
    lines") is not parsed.** That is a real constraint on how the prose must be written, not a bug to
    fix in the pattern, and **saying so in the output is what keeps the trust chain honest.**
  - **The trust chain has a fourth link: a checker must not conflate QUOTING a bad rule with ASSERTING
    it.** Widening the parser made that checker **fail this very report**, because the lessons paragraph
    quotes `at 6 lines, Hash <= 256` while explaining why it is bad, and whole-document scanning scored
    the quotation as a live recommendation. **Every findings section that documents a defect quotes it,
    so a checker with no notion of quotation systematically fails exactly the documents that do the most
    careful work** — and the easy fix, silently skipping ambiguous text, recreates the original blind
    spot one level up. **Print the ambiguity instead**: it now reports clauses outside a recommendation
    line as `noted (not a failure)`.
  - **And the fix that answered the false alarm CREATED a false pass, so it was less precise rather than
    more.** Blanking the quotation lines instead of recognising them let a correct recommendation plus a
    permissive table row (`| 6 | 256 |` under a `MultiPV | Hash` header) pass **entirely silently** —
    **no failure and no note, which is strictly worse than the false alarm it replaced.** The working fix
    **blanks quotation lines without deleting them**, because a table's column header lives on an earlier
    line and deletion broke table parsing into nothing.
    - **A checker's precision claim is itself a measurement, and it can fail the same way any other
      measurement does.** This one was asserted in prose before it was tested, and the test refuted it.
    - **Three further misreads, all measurement tables read as ceilings**: an allocation row
      `| 3 | 124.7 | 259.7 | 135.0 |` parsed as a Hash cap of 1 at 3 lines; `133 lines: 114` (a mate-line
      count) parsed as 114 MB at 133 lines; and `MultiPV 1 at any Hash` parsed as a 48 MB cap at MPV 1.
      Guards are mechanical: a **Hash floor of 8 MB** (the grid's smallest column), a **two-column row
      whose header names both Hash and a line count**, and an explicit **any-Hash-is-unbounded** rule.
      **But the floor guard was dead code when it was first added**: every Hash quantifier was
      `\d{2,4}`, so a single-digit value never matched, and **the floor could not parse its own value**
      — `8 MB` and `9 MB` were skipped, `10 MB` was the real floor, and the constant **read like a
      guarantee while controlling nothing.** It is now asserted in code: the parser must accept `8 MB`
      and must not accept `7 MB`, and the line-count bound must be at least the grid's largest column.
      - **A bound that skips input must be proven to skip only input that could not matter, and the proof
        has to be an assertion in the code, not a sentence in a docstring.** The reason the floor was
        attractive — it uses a property of the GRID rather than of the text — is exactly why it
        needs an assertion: **a grid property can change under a re-run and nothing would notice.**
  - **A failure must be the RIGHT failure.** The selftest now requires each escape case to fail
    **specifically with "MORE permissive"**, not merely to fail — because a case that errors for an
    unrelated reason (no clause parsed, a crash) counts as a detection and makes the selftest's passing
    evidence of nothing. **Same shape as "exits 1 is not evidence", one level in.**
  - **"It exits 1" is not evidence the check is right.** Of three defects found in that one checker,
    **two were already exiting 1 — just unreadably or on the wrong input** — so a green-to-red signal
    proves only that the process noticed something. **Only the two-sided selftest distinguishes a checker
    that works from one that happens to complain**, which is why accepting correct cases is a permanent
    part of the test rather than an illustration.
- **A count printed is not a count checked.** A checker can print a total while holding no view of the
  thing it counts, which reads exactly like a check. **The count must be compared against the prose,
  not merely printed.**
- **Anything a final report quotes verbatim is copied by script, not retyped** — retyping is where a
  paraphrase enters silently — and verified intact after the append.
- **A check that only inspects the shape it expects cannot see content it does not expect.** A heredoc
  lost its terminator and five lines of shell landed in a findings table; every check passed and the
  row count even incremented. Repairing this needs a check on **out-of-band content**, not a better
  selector for in-band content.
- **A COUNTING claim about a table must be computed, and a HUMAN counting it from a summary LIST gets it
  wrong in the direction of the list they were shown.** A reviewer flagged a table's prose as inverted
  — "three report and four do not" called wrong — while quoting a bulleted list of **three** reporting
  surfaces against **four** silent ones, which is exactly what the sentence said. **The rows were never the
  problem; the reviewer's own summary of them was.**
  - **Both the table and the sentence were correct because both were generated from the same source list**,
    which is the property to aim for: **generate the count from the rows rather than typing either.** A
    second seat's prose about its own identical table *was* wrong, because it reached its total by
    double-counting a row that appears on both sides.
  - **The tell is that a counting dispute is decidable by a script in one command.** **Do not settle one by
    reading.**
  - **And the dispute is itself the defect signal**: if either party had run the count there would have been
    nothing to argue about. **Confidence on both sides of an arithmetic question is a reason to compute, not
    a reason to argue politely.**
  - **SUMMING cannot detect a missing row; GROUPING can.** A total that disagrees with a table has two
    possible causes — a mistyped number or a missing row — and they look identical in prose. **Group the
    rows by subject and flag any subject that appears once when it is known to have disagreeing branches.**
    **That is the operation to add to "compute the count", because adding rows up answers only the first
    cause.**
  - **Two tables collapsed the SAME surface in OPPOSITE directions** — one kept the silent mixed-list branch
    and under-counted the truthful side, the other kept the reporting all-illegal branch and under-counted
    the silent side. **Neither error was visible by summing; both were found by grouping.**
  - **But the MECHANISM first offered for that ("each kept the branch matching the prose total already
    written") is UNVERIFIED and is recorded as such.** On this side the table and its sentence were written
    in the same edit and were **consistent with each other** — the sentence correctly counted an
    **incomplete** table. On the other side the row and the total landed in the **same commit**, so the
    ordering is not recoverable from the log. **Neither party can confirm that the sentence preceded the
    table, so the persuasive version does not go in.**
  - **The remedy does not depend on the mechanism, which is why it survives:** **write the prose total FROM
    the table, never beside it.** A total stated first is a **hypothesis about** the table rather than a
    report of it, and a hypothesis is exactly what will quietly select the rows that confirm it — **whether
    or not it did so here.**
  - **A table can be UNDER-COUNTED by a collapsed row, which is the harder failure to see than a wrong
    arithmetic claim.** Two `searchmoves` cases — an all-illegal list that **does** report, and a mixed list
    that does **not** — had been merged into one row, which hid the worst silent surface: the mixed list is
    **byte-identical to pinning the legal move alone, with nothing on either stream to filter on.** **A
    surface whose branches disagree with each other needs one row per branch.**
  - **And a checker written to compare rows to prose FALSE-POSITIVED on a passage that CITES another
    section's count rather than carrying its own table** — a script looking for a local table finds zero
    rows and reports a mismatch. **A check that cannot tell a local claim from a citation of one is the same
    class as a checker that judges text instead of the thing.**
- **A correction to one claim has DEPENDENT SENTENCES elsewhere, and the ones that break are the SUMMARIES.**
  Four separate instances in one night of a corrected claim leaving a stale restatement behind — a table
  heading, a section restatement of the same count, a cross-reference, and a rule number — **all found by
  reading, none by a check.**
  - **"Grep for the COUNT in the corrected claim" is a distinct habit from "grep for the phrase you
    contradicted."** The claim's count is usually carried in a **summary table whose heading nobody re-reads
    after the body changed.** One such heading claimed *"two of five refuse safely, three improvise, and one
    surface does both"* — **six of five** — while the table underneath was missing the very surface that had
    just been reclassified.
  - **And re-check the JUDGEMENT the correction touches, not only the number.** A behaviour reclassified from
    hazard to truthful reverses any prose that called it a defect: here "a malformed position silently becomes
    a real one" became *"the command is honoured with the junk dropped"*, and **whether that is wrong is a
    judgement the measurement does not reach.** **Record the behaviour; do not let the old verdict survive
    the new fact.**
- **A POINTER IS A CLAIM, and nothing compares it against its target.** A cross-reference that says "the same
  check §45 needs" — an invented example, and this report has no §45 — is asserting **three** things: that
  the section exists, that it is the one intended, and
  that it still holds the content named. **A renumber breaks the second and third while leaving the first
  true.** In one summary a reference to the decomposition rule survived several editing rounds pointing at a
  rule about corrections, and in this report a "same family as trap 14" survived pointing at a trap about
  summary statistics while the intended one was trap 15. **Both were found by machine-checking that every
  reference resolves to the content it names, not merely that the number exists.**
  - **Mechanically: extract every pointer, resolve it, and print what it now points at** — then read that
    list. A bare "all references resolve" check passes in both of the cases above.
- **A fault COUNT can disagree with itself across the documents that describe it, and the entry count is
  not the fault count.** One seat's final accounting had **8 numbered entries, a STATUS saying "seven" and a PR
  body saying "eight"**, and the reconciliation gave **nine numbered entries covering ELEVEN distinct faults**,
  because two entries each described a pair. **All three places now state the same pair of numbers.**
  - **And the seat's closing observation is the one to generalise: its last two turns produced ZERO new engine
    findings and THREE documentation inconsistencies.** The engine result was stable from the fixtures onward;
    what kept changing was the accounting of it. **Re-derive every headline from its saved artefacts rather
    than re-reading prose** — that is cheaper than review and it is the only check that catches drift in
    either direction.
  - **A cross-reference is a claim and can be false.** A PR body cited "details in FINDINGS §6" where §6 did not
    contain the item — **the two documents disagreed about what was documented**, which no content check
    compares. **Check that a pointer lands.**
- **AN UNDERCLAIM does not trip anything, because every guard is built to catch overclaims.** A reported
  total omitted **one of three runs** it had just listed in the table above it — **understating the work,
  which is why no check fired.** It surfaced only when the three saved JSON files were **added up** instead of
  trusting the figure carried forward from prose. **Re-derive a total from its artefacts in either direction;
  a sanity check that only bounds the number from above is half a check.**
- **A number retyped through human hands drifts even when the rule forbids it.** One seat wrote the rule
  "never retype a number", then typed a real computed value wrong **twice in one day** — first **5.05%**,
  then **5.0508%**, against a computed **5.0547%**. **The habit is stronger than the note; the only fix that
  works is generating the figure INTO the text mechanically** rather than proofreading it afterwards.
- **A SPREAD figure has to name its estimator.** The same six numbers give **1.36% and 4.76% as
  (max−min)/min**, or **1.34% and 4.54% as (max−min)/max**. Two seats computed the same table and
  reported two sets of percentages for that reason alone — no error on either side, and the ordering was
  identical. **A range expressed as a percentage is ambiguous until the denominator is stated.**
- **A MECHANISM claim you cannot check gets FLAGGED, not adopted because it is persuasive.** One seat offered
  a tidy explanation of how two tables came to collapse the same row in opposite directions — *"each kept
  the branch that matched the prose total already written"* — and the receiving seat **checked its own
  history and could not confirm the ordering, because the row and the total landed in the same commit.**
  It recorded the mechanism as **"reported by the other party, unverified on my side"** rather than
  adopting it. **That is the same standard applied to a persuasive story as to a number.**
  - **And the remedy was kept anyway, because a remedy does not depend on the mechanism that motivated it.**
    **Write a prose total FROM its table, never beside it** — a total stated first is a **hypothesis about**
    the table rather than a report of it, and a hypothesis is what will quietly select confirming rows,
    **whether or not it did so in the case at hand.**
- **TO SHOW A CODE PATH DOES NOT MATTER, SHOW IT RAN AND NOTHING FOLLOWED — and that takes two separate
  proofs.** First a **footprint**: an instrumented build establishing the branch executed (here **31 roots,
  1–24 executions per search**). Then a **test of the alternative that would mimic a null**: a position
  scoring badly while the branch fires could be a **real loss** or a **missed draw**, and those separate under
  deepening — **a missed draw trends toward 0, a real loss goes further negative.** Three positions went
  **−550 → −1,010**, **−536 → −560** and **−546 → −559**, so they were confirmed losses.
  - **Inverting the order is what made the null honest**: run the instrumented build **first**, keep only the
    roots where the branch fired, then compare. The earlier scan measured the outcome on a corpus that could
    not reach the code and read the resulting zero as evidence.
  - **The two proofs in order, because either alone is a null that reads like a finding:** **(1) show the code
    path ran and nothing followed** — instrument it and report a counter the path would MOVE, not the
    outcome it would change; **(2) show that what it did not change was not the thing you would have needed it
    to change.** **The first proof shows you looked somewhere the code COULD have shown something; the second
    shows that what it showed was not the absence you needed.**
  - **And the counter that exposes an empty null is usually NOT the metric the null was about.** Here the null
    was a **score** result; the check that showed it was empty was **node counts**. **When a null needs a
    footprint, expect the footprint to live in a different counter from the one you were measuring** — which
    is why "I looked and saw nothing" needs a second instrument rather than a longer look.
  - **And the qualifier is earned rather than assumed.** "Mechanism present, no verdict-changing fixture found"
    is a different claim from "no effect", and only the footprint lets you say which you have.
- **A NULL FROM A CORPUS THAT CANNOT REACH THE CODE IS VACUOUS, and the way to tell is to look at a counter
  the code path would MOVE, not at the outcome it would change.** A 199-position scan for a repetition effect
  found **0 score diffs and 0 node-count diffs** — and the **identical node counts prove the branch never
  executed**, because an opening position has no forced repetition near the best line. **The zero was empty,
  not exculpatory.**
  - **So before believing a null, ask which counter would differ if the mechanism ran at all.** A branch that
    executes leaves a footprint even when its verdict is unchanged (here: **4,187 vs 4,186 nodes** with the
    repeating move forced).
- **A PROSE COUNT SITTING BESIDE A COMPUTED TABLE is a stale claim waiting for its next regeneration.** One
  report carried a hand-typed refusal total that **survived two regenerations** of the table next to it,
  because the table was recomputed and the sentence was not. **Failing counts were tallied three times before
  the enumeration was written down (six, then eight, then ten)** — **a wrong total in a section about wrong
  totals.**
  - **The fix is a checker that parses every STATED count out of the report and compares it to the evidence**,
    failing on mismatch — the same discipline as a harness self-test, applied to the document. **It found a
    real stale count in the very prose that introduced it**, which is the best available evidence it works.
  - **And an asymmetry worth preserving rather than smoothing**: two harness patterns were deliberately
    unequal (**30 against 66 cases**) because later cases were added to only one. **Saying why is more useful
    than evening the numbers.**
- **DUPLICATE IDS make two cases indistinguishable and silently corrupt every cross-run lookup.** An edit
  orphaned one block outside its loop, so it leaked a variable and produced **two cases with the identical id
  and no counterpart for the other arm** — **the kind of thing that produces a plausible diff table from half
  the intended coverage.** The harness now **hard-fails on duplicate ids (exit 2) rather than running.**
  - **A corpus is an input like any other: assert its identity is unique** before drawing conclusions from a
    comparison over it.
- **A CONTROL THAT SILENTLY DOES NOTHING IS WORSE THAN NO CONTROL, because it launders an unchecked claim
  into a checked-looking one.** A seat planted a wrong figure to prove its number-audit could fail — the
  run returned **exit 0**, because the planting was a string replace whose **target did not match, so nothing
  was planted.** **The control reported green on an unchanged file**, which is precisely the silent-pass defect
  the audit exists to catch, occurring **inside the audit's own control.**
  - **Fix both halves**: the planting **asserts the target exists and that the text actually changed**, and the
    negative control is **built into the script and runs on EVERY invocation**, printing that it planted,
    that the planted run exited non-zero, and that the message names the planted value. **It no longer depends
    on remembering to test the test.**
  - **This was the third process fault of the night that produced a PLAUSIBLE output** — and the common
    thread matters more than the count: **the empty table printed a clean six-column table with no rows in it;
    the unverified claim was true; the unplanted control printed a green line. None of them looked wrong, and
    none would have been caught by reading.**
  - **Only one question separates all three from a passing artefact: "would this have failed if it were
    false?"** It is **cheap to ask and expensive to omit**, and it does not require knowing what the failure
    looks like — which is why it works where familiarity does not.
- **A CLAIM ABOUT AN ARTEFACT MADE FROM MEMORY OF THE ARTEFACT is the same defect one level up**, and it is
  how a corrected defect reappears in the correction. Two rules were reported as "in the report"; a grep showed
  one existed only as a table row recording the bug and the other appeared nowhere — **both were in the chat
  message ABOUT the deliverable.** The seat fixed it and wrote the second rule's text so it records that it
  earned itself this way, **so the next reader sees the mechanism rather than a tidy assertion.**
  - **"In the report" is ambiguous when there are TWO reports.** The claim was **true of one and false of the
    other**, and neither party was lying — **which is precisely the ambiguity that produced the fault.** Name
    the file, not the genre: **"in `X.md`"**, never "in the report".
  - **And a number you are proud of getting right is still a number that can go stale.** An asymmetry
    deliberately kept (30 against 66 cases) had been hand-typed in prose; it is now **computed from the
    evidence and checked**, because being *right on the day* is not the property at issue.
- **A CORRECTION RECORD KEPT ONLY IN CONVERSATION is not in the record.** A seat had listed six net
  corrections in a chat message and nowhere else; asked to move them into the deliverable it also
  **enumerated them properly and found ten**, five wrong engine claims (four of them the coordinator's) and
  five harness defects (all its own). **The missed item was one of its own.**
  - **And it corrected its own framing of how the errors were caught**: it had written that *"each was caught
    by someone who did not share the author's assumption"*, which is **false for the self-caught ones** — and
    it had **repeated one of the coordinator's errors in its own hands in the same turn it diagnosed that
    error in the coordinator's.** **Implying all the faults were someone else's would have been the least
    useful version of the section.**
- **A TRUE CLAIM STATED BEFORE IT IS VERIFIED is indistinguishable to a reader from a false one.** A seat
  reported that a `--tag` change "left the base outputs unchanged and still reproducing" **before checking
  it**. The claim was true — and it said so itself: **an unverified claim that happens to be true looks
  exactly like one that is false, because the reader has only the sentence.** It then verified with a
  committed test (tagged and default names disjoint; re-running leaves both base files **byte-identical**,
  sha256 unchanged) and checked its own **provenance** so the comparison could not be circular — the baseline
  was last written 28 minutes before the edit, and the edit touched only the script.
  - **A correct outcome must not launder a bad process.** The correction is worth recording precisely
    **because nothing went wrong**: a process fault that produces the right answer is the one nobody reports.
  - **And the failure it guards is silent**: a tagged run that also rewrote the default filenames would
    **overwrite the base evidence while looking like it worked** — the filename-collision family again,
    which is why "I checked it once in a shell" is not enough.
- **A NULL is exactly what an author is most tempted to OVER-CLAIM**, because "no effect exists" is a
  stronger and more satisfying sentence than "no effect detected at this sample size". **State a null with
  its power, its discordant splits, and any disagreement between its references on direction** — one
  seat reported **"no effect detected at these sample sizes"** rather than a clean negative, because its
  k=2 cell had only **39 pairs** and its two references pointed **opposite ways** at k=3 (**+2 and +5**).
- **When two runs validate different subsets, compare them PAIRED on the intersection.** A patched build's
  reference kept **51** positions where the base kept **53**; quoting `143/153` against `142/159` would
  **confound the position change with the patch.** **Pairing on the 51 common positions is the only
  comparison that isolates the patch**, and the unpaired version was available and would have looked fine.
- **A claim that REVERSES TWICE is evidence about the TEST, not about the engine.** The move-list behaviour
  went **splice → truncate → splice → truncate**, and each reversal tracked the experimenter's belief
  rather than the engine, because the first two fingerprints could not separate the hypotheses. **Record the
  reversal path and its cause, so the final version is known to come from a test that COULD distinguish
  rather than from another guess.**
  - **And a claim with a reversal history needs independent measurement MORE than a fresh one does, not
    less.** A reviewer who takes a twice-corrected figure on trust repeats the condition that produced the
    reversals. **Ask of any source: could its own test have told the two answers apart?**
- **A FINGERPRINT test needs a depth at which the candidate hypotheses make DIFFERENT predictions.** A perft
  count used to separate "truncate at the bad token" from "skip it and continue" **could not**, because at
  perft 2 the two-move prefix and a four-move spliced line **collide on 835** — two different boards, one
  count. The collision made the wrong hypothesis look confirmed. **At perft 3, where all five prefixes are
  distinct, the answer was immediate and reversed the conclusion.**
  - **And a fingerprint must be able to tell the two states apart even when nothing is wrong.** A `perft 1`
    check on a lone-king board gives **3** both before and after a move, **by construction** — so it
    confirmed nothing while looking like evidence. **Before using a fingerprint, compute what it would read
    under each hypothesis.**
- **A COUNT comparison cannot see a substitution, and a green on counts is therefore not a green on
  behaviour.** A perft suite that compares node counts passes a movegen bug that **swaps one legal move for
  another at equal count** — both trees have the same size. **Comparing move SETS at every node closes it**,
  and the honest limit stays explicit: a set comparison at shallow depth is **not** a proof over every node of
  a deep run, so it replaces a blanket caveat with a specific one rather than removing it.
  - **The self-test for such a check must plant exactly that bug** — swap one move for another at an
    identical count — or a count-based selftest passes a set-based check for the wrong reason.
- **A control on which the parameter CANNOT BIND cannot distinguish "it works" from "it is ignored".**
  Testing whether `go mate N` respects N on a **mate-in-1 board** gives depth 1 for N = 1, 2, 5 and 10 —
  because the mate is found immediately regardless of the cap. **Run only that control and the conclusion
  is "N is ignored", the opposite of the truth**; the parameter binds only on a board where the search
  would otherwise run past the cap.
  - **When testing whether a LIMIT is honoured, pick an input that would exceed it.** The control needs the
    parameter to be the binding constraint, not merely present.
  - **A framing trap has TWO extremes, and only one is usually guarded.** A perft reader that stopped at a
    bare `nodes N` line was guarded against extra output following it, but the same rule then **refused a
    checkmate position**, which correctly prints `nodes 0` with **no divide table at all** — and had been
    **silently deleting the "generates nothing" case**, the one where a movegen failure matters most.
    **Cover both extremes: perft 0 prints `nodes 1` with no divide, mate prints `nodes 0` with no divide,
    and everything between must add up.**
- **A control must be demonstrated to fail when the input is wrong**, not merely observed to pass when
  it is right. The three most natural ways to write one all pass vacuously: `max()` of nothing, `all()`
  of nothing, and a lookup falling through to a default.
  - **A control that returns a plausible wrong number is worse than one that crashes** — a crash is
    visible, a wrong number passes review. Implementing this rule exposed two live vacuous controls
    (a no-legal-capture FEN and an illegal-move FEN returning `got 3`) in the tool that had just
    produced the seat's cleanest result.
  - **A control that cannot REACH the code path it names is a vacuous control wearing a different
    hat.** A probe's new control for the no-`isready` path called the library's `search()` helper, which
    **always sends `isready`** — so it exercised the same path as the control above it and passed for
    the same reason, while claiming to test the opposite case. Fixed by driving the engine by hand, and
    **proven able to fail** against a fake engine that omits the diagnostic.
    - **This is the variant most likely to recur in a suite somebody else reads**, because the control
      passes, is named correctly, and tests nothing. **The question to ask of every control is not "did
      it pass" but "which line of the harness did it actually execute".**
- **A relative path that looks local and is not.** `>> ../FINDINGS.md` from inside a `job*/` folder looks
  local and is not. Same family as an `&&` chain that reported success from a step that never ran, and
  a fixture key that silently omitted castling: **in each case the tool did exactly what it was told
  and the instruction was wrong.** Convention: write a seat's files from the seat root, with no `..`.
- **Every absence looks like success.** A check that examined nothing, a list that omitted an item, a
  chain that skipped a step, and a guard that compares a value to itself all report cleanly. **Make
  the count visible and make it a literal.**
- **After a test passes, ask what it would have printed had the fault been present — and confirm the
  plant was somewhere the checker actually looks.** Three failures in one seat came from this: a
  clone that could not see the remote branch, a counter that counted the wrong position, and a guard
  proven by a plant in the wrong directory. In each, the pass came from the fault never being in
  scope.
- **A gap with a documented failure in the record is a different object from a gap that might
  matter.** The unimplemented mutation class was verified to be the one that would have caught a
  shipped defect: the old scan opened zero files, so it passed silently.
- **For every check, name the file types, directories and row shapes it does not scan**, and ask
  last whether the pattern matches how the subject is actually written rather than how you imagine
  it. A defect found in evidence already committed is the serious case, because nobody will
  re-read it.
- **An evidence rule that refuses the CONVENIENT citation is the rule earning its place.** One gate
  refused three findings in a single session for citing nothing resolvable: a bare commit SHA, a `sed`
  line-range over source, and a path written without its directory prefix. **Each time the convenient
  form was the wrong form** — a SHA is uncheckable without the repository, a line range names no file,
  an unprefixed path resolves to nothing. **A rule that only ever rejects things is the first one
  someone removes**, so the rule has to be worth its friction; this one is, and the friction is the
  point.
  - **Its limit belongs beside it: the audit checks that SOME path resolves, not that the path supports
    the claim.** A row citing an unrelated file that exists passes — the same shape as a checker that
    cannot tell a claim from a quotation of it.
- **State what the comparator is before comparing.** A validation gate and the thing it validates
  can share the same broken key, in which case no assertion can ever disagree with it.
- **"Why" claims need the test more than "what" claims do.** A wrong description looks wrong; a
  wrong explanation is plausible by construction.
- **Determinism of a mechanism is not consistency of its effect.** A pruning gate is deterministic
  *given a node*; whether it fires depends on the node, and which nodes the search visits depends on
  everything else. **Mechanism tells you what happens at a node; nothing about variance across
  nodes.**
- **A broken tool becomes a reason to skip the check.** Name the tool's dependants when it breaks
  ("the prover is unreliable" is not "therefore no mate-distance claim in this seat"); defer a claim
  needing unobtained ground truth rather than softening it.
- **A hard cap inside a checker becomes a filter that rejects the truth.** Print every constant
  bound beside the verdict, and self-test at the bound and one beyond it.
- **Separating a confound from a refutation is a distinct skill.** Run the same cell with the
  variable under test removed: if the outcome persists, you have measured the confound. (Bare kings
  return 0 nodes at two occurrences only because insufficient material is an automatic draw.)
- **Two explanations, one observation.** A conclusion phrased as a **disposition** — "it does not
  claim", "it prefers", "it avoids" — drawn from cases where a **capability** produces the same result
  is unsupported. **Before concluding "X does not do Y", name the fixture where Y is the only option
  and run it.** The tell is in the grammar of the claim, so it can be caught while writing.
- **A sample of two with one exclusion stated is honest; with the exclusion silent it is a sample a
  reader will assume was chosen.**
- **The measurements held on the first full run; the MACHINERY built to check them failed five times.**
  In one seat's thread the grid never changed — the boundary, the patch numbers and the residual all
  survived — while five separate checkers failed: one that parsed only its own generator's form, one
  that could not tell a quotation from a claim, one that treated a missing input as a pass, a floor that
  could not parse its own value, and a subtraction given more precision than its two samples allowed.
  **Five failures, zero of them in the measurement itself.**
  - **The reason is structural rather than personal: a measurement has an EXTERNAL reference that can
    disagree with it, and a checker has only itself.** That is why "a failure must be the right failure"
    and "a bound must prove what it skips" are the load-bearing rules, and why the two-sided selftest
    outweighs any single verdict.
- **A DERIVED claim is where a plausible figure outruns its evidence.** Every other claim in a section of
  comparisons is a single number against a threshold, and one comparison has one number to check. **A
  decomposition has three numbers, two samples and one subtraction** — and it is the derived claim, not
  the observed ones, that gets quoted to three significant figures.
  - **State the terms' provenance before subtracting.** Two operands from **different experiments** — a
    median over cell medians against a single position's single run — cannot be subtracted unless both
    are declared, and **the difference inherits every weakness of the weaker one.**
  - **Then prefer a RATIO to a subtraction.** "Allocation predicts 1.72×; 1.94× is observed; ~0.22× is
    therefore search" is a **bound that holds under any sampling convention**, where "31 ms of search"
    is a difference of two noisy quantities dressed as a measurement.
  - **And check whether the excess is position-independent before quoting a single figure for it**: here
    it ranged 135.0–195.6 ms across six positions, so the quoted residual was the low end of a spread
    that had not been measured.
- **An ADVICE SENTENCE is the part of a section that drifts, because it is the only part that is
  derivation rather than measurement.** One shipped section had every measured claim intact and **its
  recommendation reinstated the coarse advice the same section had just refuted, two paragraphs later.**
  **The recommendation was one `print` away from provable consistency**: the analysis script already
  emitted the fitted table, so the sentence could have been generated from it instead of written. **Have
  the script print its own recommendation, and the advice cannot drift from the fit.**
  - **And the drift runs in the permissive direction when the prose is written by hand and the rule by
    machine.** Here the generated advice was conservative and correct; **the prose ABOUT the generated
    advice drifted, and it drifted toward permitting more** — the same failure as the original defect,
    one level down from it. **Two more instances of the same claim were in the same file's findings.** A
    hand-written "zero false-safe" beside a fitted ceiling that has one is a sentence no script produced.
  - **Also: name a rule for what it constrains.** "Per-line cap" for a Hash ceiling keyed on line count
    reads as a cap on the number of lines, **and it echoes the "per-line cost" hypothesis the same
    measurements refute** — so a skimmer can read the refutation as support for the rule.
- **"I checked the other branch" is a check that can return a wrong negative.** Three attribution questions
  arose in one night — a finding id assigned to the wrong seat, a caveat routed to a seat that never wrote
  it, and a result reported as absent from a branch that has it in nine files. **The third is the
  instructive one**: the checker did open the branch, and still got a negative, most plausibly because
  its fetch predated the push. **Opening the branch is the right check and it is not sufficient; the
  fetch has to be current**, and the figure should be quoted with the commit it was seen at.
  - **What stays true regardless: relaying a figure across a swarm this size without the branch open is
    where attribution errors come from**, and the fix is a lookup per figure rather than more care in the
    relaying.
  - **And the command that opens the branch must ENUMERATE the branch.** The seat that raised the
    false negative then found its own cause, and it is the best instance of the selector family in the
    record: it ran `git show <ref> --name-only`, which answers **"what did this commit touch?"** and
    returned **7 paths**, while `git ls-tree -r --name-only <ref>` answers **"what is on this branch?"**
    and returns **22**. **It read the first as the second.**
    - **It failed convincingly, which is what makes it distinct.** Every earlier instance failed silently
      or loudly; this one ran cleanly and produced a specific, confident, wrong claim about another
      seat's work. **A negative claim about a branch must name a command that enumerates the branch**,
      the fetch must be immediately before, and **the tip SHA should be recorded so staleness is visible
      afterwards.**
    - **Prefer the positive form**: *"does it contain this file?"* can succeed, while *"does it contain
      nothing about X?"* cannot be distinguished from a bad read by its own output.
- **A build whose PROVENANCE was assumed rather than checked produces a confident wrong measurement.** A
  coordinator measurement of FEN field counts contradicted a seat's; the difference was that the coordinator
  had built `integrate/combo29-all`, which is **277 commits behind** the audit's base commit `6b98f217` and
  shares a common ancestor with it (`e04556ddc`).
  - **An intermediate claim that the two histories were "COMPLETELY DISJOINT, no common ancestor" is
    WITHDRAWN — it was false.** `git merge-base` returns `e04556ddc`, `6b98f217` has a parent (it is not a
    root commit), **277 commits are unique to the base** and **1 docs-only commit** is unique to the other
    branch. So it is an **older tree**, not an unrelated engine, and the difference is measurable where it
    matters: `search.cpp` differs by **+923 lines** (where the drawn-root bail lives) and `uci.cpp` by
    **+181** (where the book gate lives).
  - **Both versions of the story agree on the operative point and disagree on the remedy.** The binary was a
    different engine, so the FEN measurement was invalid either way; but **"behind" implies re-measurement
    can converge and "disjoint" implies it cannot — and the truth is the former.** **The lesson is
    narrower and more useful than the version first written: a `merge-base` that exists is one command away,
    and claiming otherwise removed a remedy that was actually available.**
  - **And the two stories coexisted in this run for over an hour because each seat checked a different
    thing**: one compared commit *dates* and concluded "behind", another ran `rev-list --parents` on a
    shallow clone and concluded "root commit, disjoint", and neither ran `merge-base` on a full clone.
    **A relationship claim needs the relationship check, not an inference from a proxy for it.** **The rebuild verified bench 11 = 312,866 on the
  same binary before recording a single row**, and then agreed with the seat.
  - **The check is one command and it is the same one every harness trap in this section ends at**: confirm
    the artefact is what you think it is, before interpreting what it says. **A build is an input.**
  - **A provenance tool now exists and is the right form**: check the worktree HEAD against an expected
    commit (equal or ancestor), flag a binary **older than its newest ENGINE source**, and **print the
    binary's checksum to quote**. Exit codes 0/1/2, all three exercised.
  - **And its first run was confidently wrong, in the class it exists to prevent.** It reported
    **STALE BUILD against a good binary**, because its build-directory exclusion listed five names by
    hand and walked into a sixth, where **CMake's generated `CMakeCXXCompilerId.cpp`** — written at
    configure time, *later* than the binary — was the newest `.cpp` in the tree. **The mtime of a generated
    probe file is not evidence about the engine's source**, and **a staleness check that fires on a build
    artefact trains you to ignore it.** Fixed to exclude by prefix.
  - **The tempting shortcut when two measurements disagree is to prefer the more recent or the more
    authoritative-looking one.** Both would have been wrong here: the seat's version was right and the
    coordinator's was measured on the wrong commit with a plausible-looking `BUILD_OK`.
- **A presence match is not a provenance check.** A figure was almost certified as sourced because its
  **digits appeared inside a different, genuinely-sourced number** — a `11` and a `13` that belonged to
  another ladder entirely. **Matching a numeral is not finding a source**: the test is whether the source
  STATES the claim, not whether it contains the characters.
  - **And a provenance audit against a remote cannot see a branch that has not landed yet.** In one run,
    four figures read as unsourced because they came from a seat whose push arrived minutes after the
    audit's fetch. **A figure produced in the last few minutes will always look unsourced**, so a
    provenance pass should record the commit it audited against rather than report a bare count.
- **A number in a summary must carry the position it came from.** An uncheckable number stays wrong
  indefinitely, because nobody re-runs a claim they already believe.
- **A CORRECT NUMBER WITH AN OVERSTATED INFERENCE is harder to catch than a wrong number, because every
  mechanical check confirms it.** A row can have every figure right, parse fine, and still carry a conclusion
  its statistics do not support — compliance, arithmetic and count checks all pass. **The tell is an
  ordering asserted from a comparison whose p-value does not support one**: here "less than half the rate"
  and "worse than no criterion at all" rested on a comparison at **p = 0.0712**.
  - **A verdict function that refuses to state an ordering below p = 0.05, and prints "the comparison did not
    resolve" instead, is the mechanical defence** — built and probed four ways (known-significant pair,
    identical rates, same proportion at different n, interval sanity) before being trusted.
- **A prediction whose falsification is guaranteed by its own definitions is worse than a wrong guess**,
  because a wrong guess still informs. One seat predicted **60–100% overlap between two strata that the
  same document defines as mutually exclusive**, and recorded KILLED for a prediction dead when written.
- **"Cannot resolve" is a result, and a pruned solver's silence is not evidence.** An exhaustive mate search
  that **excludes mate in ≤5 and cannot complete n=6** leaves a candidate board a **candidate**, not a
  third instance. A pruned shortcut that **failed to find a known mate-in-7 in KQ-vs-K** was abandoned and
  kept as an abandoned branch, **because a "not found" indistinguishable from a timeout would have produced
  a confident-looking wrong answer.**
- **A p-value must be recomputable from the counts printed in its own row.** Three of four sign-test
  p-values were published as `1.000` when the counts beside them give 0.022, 0.648 and 0.411; the
  fourth (0.523) reproduced exactly. **The cause was a saturated function, not a mis-copy** — the test
  lacked a `min(k, n−k)` reflection and so returned 1.000 for every share above half. **The one
  correct row was the only below-half one, which is why a working-looking test made three wrong cells
  read as computed.** Print the count and the p together, or print neither.
- **A single correct-looking row can be a coincidence of the failure's shape.** The one p-value that
  reproduced was the one case the bug could not reach. **When a test's failures cluster on one side of
  a threshold, the passing case is the one to interrogate, not the one to trust.**
- **The scoreboard is a measurement and it drifts the same way.** A seat that spent the night saying
  "read the file, don't trust the prose" over-reported its own check count by four, because it
  incremented the number in prose. **Generate every tally from the artifact, or let the gate compare it
  against the artifact** — a corrected number is not an auditable one. The most durable kind of wrong
  is a stale number that survived a correction of the claim around it.
- **The claim most likely to violate a rule is the summary of the rule, because summaries are where
  hedges get dropped.** Five times in one seat tonight, a rule caught an error in the sentence
  written beside it — including two rules catching each other's summary inside one section.
- **A rule about classification is itself an unclassified claim until someone applies it.** When you
  write a rule that sorts claims into categories, immediately sort the sentence you just wrote with
  it.
- **"Coin flip" must mean exactly one thing: a real pooled effect that is per-position random.** A
  result whose CI includes 1.0 is **unresolved**, which is a different state — neither real nor null.
  Never label a result by its sign-share before its interval exists.
- **A statistical test with no committed source is an anecdote with a decimal point.** Four
  sign-test p-values were published as inline shell arithmetic, in no file, so no reader could
  recompute them; a replication found three of the four were wrong. **The bug was a missing
  `min(k, n−k)` reflection, so the test saturated at 1.000 for every share above half and was correct
  only below it — the one correct row was the below-half one, which made the function look validated.**
  - **Commit the test, not the answer, and give it a symmetry self-test**: `p(k, n) == p(n−k, n)`
    holds for a correct two-sided exact test and fails for the buggy form above half. A floor
    assertion catches the saturation separately. **Both checks are properties of the test rather than
    of the data, so they run on every use without a fixture.**
  - **The tell is a cluster of identical p-values at a round number.** Three cells reading exactly
    1.000 is a saturated function, not three nulls.
- **A rule catalogue is as prone to fabricated illustration as any other prose.** An example is the
  one part of a rule that feels free, because it is only there to help, so it gets the least
  checking. **Every illustrative example names its source file and line in the same sentence, or it
  is deleted.**
- **The number/prose staleness is symmetric and both directions happen at the same instant:** claim
  corrected with the number left stale, and number corrected with the sentence left describing the
  old behaviour. **One pass over the corrected passage: is every number produced by something I
  could re-run, and does every sentence still describe what the number now says.**
- **A number can outlive the correction of the claim around it.** Revising a figure feels like
  changing evidence; revising the sentence feels like editing. So the prose moves and the number
  stays. **When a claim is corrected, re-run every number inside the corrected passage in the same
  edit** — the correction is exactly the moment a figure is least likely to be looked at again.
- **An anchor re-verified is not a bulk re-verified.** Say what was not re-run.
- **A presumption sitting in a results file reads exactly like a measurement.** Worse than a
  fabricated illustration, because it sits in the finding rather than in a supporting sentence.
  **Mechanical consequence: a results file contains only sentences a command produced; any "would
  presumably" is deleted or moved into a numbered prediction with its kill condition.**
- **A phrase list is a spot check.** A phrase search finds the wording you changed, not the sentences
  that depend on the thing you changed. When a claim changes, list the *dependent* claims and read
  them. Worked case: a grep found 4 documents, a concept-level read found 6 — including a handoff
  whose STOP notice sat at the top while the body beneath still told the old story. **When a document
  is superseded, rewrite the body; a caption does not fix it.**
- **Before shipping a BOUND, measure the population where it might NOT bind.** A ceiling needs a sample
  that can reach high; **a floor needs one that can reach low.** If the sample cannot contain the
  extreme, you have measured the middle and extrapolated, in whichever direction the sentence happens to
  point. **One quantity, both directions, one night:**
  - **Ceiling too high** — an overshoot band of 1.02–1.95× from **4 positions**; at 40 positions it is
    1.008–3.503× with **29 of 80 cells outside** the band, because the ceiling comes from an iteration
    boundary landing late in a LARGE tree and none of the four had one.
  - **Floor too low** — the same quantity also has a floor: a 14.9× under-shoot on a small tree at the
    depth-64 clamp. Shipped unscoped this becomes *"a soft budget is unreliable"*, which is **false** for
    real-game use (**0 of 60** positions undershot at `softnodes 2000`).
  - **The guidance is therefore not "use more positions".** It is: **name the two extremes of the
    population and check the sample contains cases near each.** Four middlegame boards contained
    neither; sixty real positions contained the second but not the first, and the small-tree case needed
    exactly **one** mating board.
  - **A bound published without its non-binding population is worse than a wrong one, because a reader
    applies it where it fails.** "A soft budget is unreliable" would have been real harm to an owner
    deciding whether to trust his self-play labels — the exact decision that bound was meant to settle.
- **An absence in the engine's favour needs the same proof as a defect: find the WITNESS.** "KNN vs K is a
  draw" was recorded as a defect because a source line required `knights == 0`; **the source line was right
  and a legal checkmate exists** (`8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1`). **The rule that settles such a claim
  is not an argument about FIDE but a search for a mate witness**, and it took an exhaustive placement
  search to produce one. **Nine material sets were decided that way rather than by reasoning**, and all nine
  agreed with the engine.
  - **So the defect that survived is a different one**: a wrong static score in a position that is
    **genuinely playable**, not a missed adjudication. **When a refutation lands, re-scope the finding rather
    than deleting it** — the surviving half is usually the part with a consequence.
- **A one-fixture sentence is a hypothesis.** Before a general sentence goes anywhere, name the
  second fixture that would break it and run it; if none exists, say "on this board" and nothing
  more.
  - **The most common disguise is a sparse endgame described as "a normal position".** A claim that
    `go infinite` self-terminates was measured on a drawn root and a bare K+R v K twin, both of which
    exhaust the depth ceiling; on **startpos it ran 75 seconds to depth 30 and needed `stop`.** The
    fixture that breaks the sentence was the one the *sentence itself* called normal.
- **Test the CLAUSE, not the claim.** A finding can pass every test its author runs **because the finding
  is right**, while a supporting caveat inside it is never tested at all. One seat's finding was correct
  and verified on both builds; the sentence *"a fresh session gives no diagnostic"* was false, and it
  was the sentence that determined what harness authors would do.
  - **A caveat is a claim and gets tested like one.** *"You cannot detect X"* and *"this only works when
    Y"* are assertions about the engine. **A reader trusts a caveat without checking it, which makes an
    untested one MORE dangerous than an untested conclusion, not less.**
  - **When a claim contains "only", "never" or "cannot", that word IS the claim.** The caveat above
    carried a universal negative, and the author had tested the *positive* half of the same sentence.
    **The test for the negative is narrow and cheap**: "is there a case where the thing is missing?"
  - **The mechanism, which belongs beside the defect it mis-described:** the author concluded the engine
    omitted the diagnostic **because it was absent from the lines the probe was reading.** *A harness that
    reads one stream misses the diagnostic; a researcher who reads one stream misses the engine.*
- **A defect named after its REPRODUCTION is not named after its CAUSE.** "The halfmove-99 miss" was
  described for hours by the counter in its fixture; the actual rule is **direction-dependent at the draw
  boundary** — a mate *delivered by* the root side at clock 100 beats the draw, a mate *against* it does
  not — so the same clock loses mates in one direction at hm=98 and in both at hm=99. **The fixture name
  hid the asymmetry**: a reader who fixes "halfmove 99" fixes one cell of a two-direction rule.
  - **The general form: when a defect's name contains a number from the reproduction, check whether the
    rule behind it has a second direction or an adjacent range.** Names are cheap and they become the
    specification by default.
- **A comparison you cannot see the whole of is not yours to make.** A seat declined a ranking I offered
  it — "more transferable method than any other seat" — on the ground that it had seen only its own area
  and my reports, so it had no visibility into the rest. **That refusal is correct and is the standard:
  a claim about the run as a whole is the coordinator's to make, because only the coordinator sees the
  whole; a seat's honest claim is narrower and often stronger** — in that case, "every defect in this
  thread was in a guard rather than in the measurement."
- **A calibration table is not the model; re-measure the model when the hardware changes.** A boundary
  fitted on one machine (a Hash cap per line count) rests on a **physical** statement underneath it —
  here, cost is `Hash × wipes` with `wipes = depth × (MPV−1)`. **If the machine changes, re-measure
  the model, not the table**, because a fitted cap encodes the old machine's constants.
- **A scope sentence should be written with the boundary it does not cover, not only the range it
  does.** Three instances of the failure it prevents: "the repair fixes the move" (true on one board
  of two), "castling is a conditioner" (true in one direction only), "a board busy enough"
  (necessary, not sufficient). Such a sentence gets longer and stops being quotable as more than it
  is.
- **A slice count is a resolution, and too few slices can invert a conclusion.** "Which factor moves with
  game phase" answered **backwards** on thirds and correctly on sixths, because the per-node term varies by
  **0.29%** and the node term by **1.36%** — **thirds could not separate a factor four times smaller than
  the other.** Before splitting a population by phase, ask how large the smaller variation is relative to
  the number of slices.
- **A claim about a heavy-tailed distribution must not be carried by its MEAN.** On a heavy-tailed node
  ratio, the population gives **median 0.9618** and **mean 1.0941**; the 1% stride sample gave **0.9305**
  and **0.9714**. **The mean's error is four times the median's** (0.123 against 0.031), because the mean
  is dragged by extremes the sample does not contain — max **18.37** in the population against **2.60**
  in the sample. On a fresh same-size subsample the mean came out **0.971** — **unstable in both
  directions, which is worse than a bias.** **The median and the tail were right; the mean was the least
  reliable number on the line.**
- **A prefix is a PHASE, not a sample.** A convergence test that took `rows[:rung]` — the first N rows of
  a game sequence — showed **spurious drift that vanished under a seeded random subsample.** Checking
  convergence on an ordered set measures where you stopped, not how much you collected.
- **Print median and geometric mean labelled, side by side.** Three statistics on one distribution
  gave three different conclusions tonight, and the distribution was the finding.

---

## 7. Harness traps that fabricate results

**Read this section by NUMBER, not by position: the numbers run in discovery order and the inserted
suffixes (`3a000`, `5a0`, `14b`, `19a`–`19e`, `19c0`, `20a00`) are later findings attached to the family they
belong to, so they sit beside their parent rather than at the end.** Renumbering is deliberately avoided —
a renumber breaks every cross-reference in this document and in the branch reports, and it breaks them
silently while leaving "the reference resolves" true.

1. A terminator or EOF during a search fabricates a `bestmove` with zero info lines. `perft` is
   synchronous and unaffected.
2. `select()` + `.readline()` on a buffered pipe is not a timeout; use `os.read(fd)`.
2d. **`position fen` and `position startpos moves` are NOT interchangeable: a FEN cannot carry repetition
   history and a move list can.** They agree at **0 and 1 repetitions (0 of 4 cells)** and **diverge at 2
   and 3 (4 of 4 cells)**. Consequence for cross-build work: **on a threefold root reached BY MOVE LIST,
   the base answers `0 nodes, cp 0, a2a3` (the bail) and PC answers `34,047 nodes, cp 22, e2e4`; via
   `position fen` BOTH answer `56,720 / e2e4 / cp 30`.** So **a harness that delivers game positions by
   move list sees a build divergence that the FEN form does not show** — and a harness that uses FENs
   cannot test the repetition path at all.
2d0. **`wtime 0` IS NOT A 0-NODE REPLY, and that matters because a 0-node reply and a piped abort look
   identical.** Cold table → `info depth 1 … nodes 26 … pv d2d4`; **warm table (after one
   `go depth 8`) → 0 nodes and the hash move.** 12 of 12 each way, so **it is TT-dependent and
   deterministic.** **The `a2a3` with no info line that a `printf … | ./forge` pipe produces is the EOF
   abort, not a clock reply** — and **any 0-node / `a2a3` row in this run's tables should be re-checked
   against which of the two it came from.**
2e. **python-chess validation closes all but ONE field: `fullmove 0`.** Of 1,086 python-chess-valid mutants,
   **249 (22.9%) are refused by the engine and all 249 are `fullmove 0` and nothing else**; every other
   mutation class is **0%**. Control: **0 of 553 real positions refused.** So a reference-library validator
   is necessary and **one field still needs its own check.**
3. Warm process state shifts scores by up to 55 cp on identical requests — **and a corpus-level measurement
   raises that to 433 cp, which is the number to plan a labelling pipeline around.** On 200 positions run
   twice in one process with **the same order**, the two runs agree **0 of 200** — a real, deterministic
   state leak rather than noise. In **two different orders** they disagree on **194 of 200** (66 also on
   bestmove), **worst case 433 cp**. **`ucinewgame` before every position fixes it completely: 0 of 200
   against the fresh reference and 0 of 200 order dependence, in the same script whose no-reset arm reports
   194.** **So the rule generalises from one position to a whole labelling pipeline: a corpus that reuses a
   process without `ucinewgame` between positions is not measuring the engine, it is measuring the order it
   walked.**
   - **At fixed depth with a reset, the score IS a usable label**: **30 fresh processes on the same position
     give 1 distinct score, 1 bestmove and identical node counts** — 4 positions, 120 launches, **0 cp
     range** — and a 200-position corpus run twice in fresh processes disagrees on **0 of 200** in score,
     depth, bestmove **or node count**. **At `Threads 4` the same test is unusable**: **19–27 distinct
     scores out of 30** per position, spread 22–84 cp, up to 6 distinct bestmoves, node ratio to 2.78×.
     Across the corpus at T4: **score differs 189 of 200, bestmove 58 of 200, nodes 200 of 200, and depth
     0 of 200** — **the instability is in which tree was explored, not how far the search got.**
   - **`ucinewgame` IS a cold
   reset: 0 of 25 searches differ from a fresh process. `Clear Hash` is NOT: 24 of 25 differ**, because
   `ucinewgame` calls `Searcher::clear()` (`search.cpp:2679`, wiping histories AND the table) while
   `Clear Hash` calls `clear_hash()` (`:2667`) then `clear_caches()`, which is only `evaluator_.clear()`
   (`search.hpp:452`). **The same drift reproduces on `position startpos moves`: 5 of 6 differ, 0 of 6
   with `ucinewgame`.**
   - **And the drift is REPRODUCIBLE — 3 of 3 independent processes replayed identically.** So a reused
     harness does not get noise, it gets **a stable-looking wrong number.** That is worse than
     nondeterminism, because nothing about the output suggests a problem.
   - **There is a THIRD state, and it is the one a match runner hits without meaning to: re-sending the
     SAME `Hash` value is a table wipe, equal to `Clear Hash` as measured.** Measured at Hash 32, depth 12,
     one midgame, 3 repeats per arm, fresh process each:

     | state between the two searches | move | nodes |
     |---|---|---|
     | nothing (warm) | `e1g1` | **14,581** |
     | **`setoption name Hash value 32`** (the value it already had) | **`d2d4`** | **86,959** |
     | **`Clear Hash`** | **`d2d4`** | **86,959** |
     | `ucinewgame` (true cold) | `e1g1` | 113,145 |
     | fresh process (cold control) | `e1g1` | 113,145 |

     **So the same-value resend is not a no-op and not a cold reset — it is the `Clear Hash` state.** A
     second seat reproduced the relations on its own position and then **extended it to 30 positions at
     depth 18 in both sizes: same-value resize equals `Clear Hash` 30 of 30**, identical bestmove, nodes,
     score and depth. **And it does fire on an ALREADY-EMPTY table** — `resize` has no early return, so it
     always allocates and always resets the generation — **but there it is unobservable**: cold
     `Hash 32; Hash 32` is identical to cold `Hash 32` on **12 of 12**, while the same re-send after a
     search differs **12 of 12**. **The positive control is what makes that null admissible** — the
     instrument sees the wipe when there is something to wipe.
   - **But it is deliberately not the SAME operation, and the difference is a state nobody had named.**
     `resize` allocates a new array and drops the old one, so it clears **the table only**; `Clear Hash`
     also empties the evaluator's pawn cache (`clear_caches()` → `evaluator_.clear()`, `search.hpp:452`);
     `ucinewgame` clears **all histories** as well (`search.cpp:2679`). **So a resize is a third state:
     a COLD TABLE WITH WARM HISTORIES**, and the two node deltas it produces have **opposite signs**,
     which is the consistency check rather than a contradiction:
     - against the **WARM** arm (same position twice, table intact): **+157%** nodes, because the wipe
       destroys a table that was doing real work and the search must re-derive it.
     - against a **FRESH** process (different position, both tables empty): **−7.8%**, because the resized
       process kept its warm histories while the fresh one has none.
     **Neither comparison alone describes the state, and a reader who meets `+157%` and `−7.8%` in one
     document will otherwise suspect one of them.**
   - **The sign matters operationally**: the wiped state **searches FEWER nodes for the same depth
     (−7.8%)**, so **a node-count or nodes-per-second metric reads that as an improvement.** It is not —
     it is the cost of re-deriving what was thrown away, **and the answers differ in 4 of 30 positions.**
   - **Where a runner actually pays**: re-sending options around `ucinewgame` costs **nothing** (30 of 30
     identical to clean, because `ucinewgame` masks the wipe), re-sending between **moves** costs
     **+157% nodes**, and re-sending **between games without `ucinewgame`** puts the engine in the warm-history
     state above. **So the hazard is narrower than "any re-send" and specific: a resume path that does not
     send `ucinewgame`.**
3a000. **A FUZZ of 167 protocol cases on two builds found ZERO crashes, ZERO hangs and ZERO sanitizer lines,
   with the engine usable afterwards — so the crash hazard at this boundary is PROTOCOL-LEVEL, not
   memory-safety.** 70 KB tokens, embedded NULs, newlines inside tokens, 500 legal moves, unicode, truncated
   and over-long FENs all ran clean under ASan+UBSan. **A negative result, stated as one.** **8 searches
   were unbounded rather than hanging**, which the seat reports as a separate class and which is the
   `go infinite` behaviour, not a fuzz finding.
   - **The denominator was wrong in the safe direction and that is why it survived.** This entry said
     **142** cases; the evidence files say **167 on each build**, with 167 result rows each, and **the number
     142 appears nowhere in `swarm/67`** — not in `FUZZ.md`, not in `STATUS.md`, not in a script. **Every
     guard in this run is built to catch an overclaim, so an UNDERSTATEMENT passes all of them** — and it
     still matters, because **a reader planning a fuzz corpus will size it from this number.** It is the
     cleanest case in the report of a wrong figure that no check was looking for.
   - **And a trap in the reporting**: **the engine ECHOES attacker bytes into its diagnostics**, so a NUL in a
     `setoption` value made a generated markdown file **binary**. **Escape control characters in any generated
     document that quotes engine output.**
3a00. **A MIXED `searchmoves` LIST silently drops the illegal move with NO diagnostic.** An empty list and
   an all-illegal list both give `0000` + `info string` + 0 nodes, but **a list containing one legal and one
   illegal move behaves byte-identically to pinning the legal move alone, and says nothing.** **Byte-identical
   means there is no signal to filter on after the fact** — same bestmove, same score, same node count, no
   diagnostic on either stream. **So neither a `0000` nor a diagnostic marks a partially-invalid restriction,
   and the check has to live in the CLIENT**: intersect your own token list against the legal move set before
   sending, because the engine's reply cannot tell you.
3a0. **`go mate N` is NOT a depth cap with extras — it is a DIFFERENT SEARCH, and labels from it are not
   comparable with `go depth` labels.** It does report depth `2N−1`, but **`mate_moves_ > 0` changes seven
   heuristics plus the TT cutoff**: the window narrows to `[mated_in(ply), mate_in(ply+1)]` and returns alpha
   when it empties (`search.cpp:1431-1435`), **the TT cutoff is disabled unless alpha/beta are already mate
   scores (`search.cpp:1452`)**, and null-move/reverse-futility (`1493`, `1639`), **IIR** (`1784`), quiet
   extinction (`1805`), the sound-mate case (`1841`), **singular extensions** (`1929`) and **check
   extensions** (`1955`) are all off. **Every one of those eight line numbers was re-resolved against
   `6b98f217` and each line carries a `mate_moves_` guard in the form the claim describes** — the TT line
   reads `mate_moves_ == 0 || (!is_mate_score(alpha) && !is_mate_score(beta))`, the IIR line reads
   `mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && ...`. **A list of eight bare numbers is
   exactly the kind of claim that rots silently, so it was checked line by line rather than spot-checked.**
   - **Measured on 12 real positions: 11 of 12 cells differ between `go mate N` and `go depth 2N−1`, and the
     score can flip SIGN at identical depth** — `c2c3` at depth 3 gives **cp −53** under `go mate 2` and
     **cp +117** under `go depth 3`, same move, same reported depth.
  - **The cost is a giveaway in the right direction but the "163×" figure is an OUTLIER, not a
    representative value — and that correction came from measuring real positions.** On a **proven-DTM
    corpus, 166.9× against a median of 1.19×** is indeed an outlier. But on **400 REAL positions at
    `go mate 4`, the MEDIAN is 188× and 279 of 400 cells sit between 100× and 1,000×.** **So "163× is an
    outlier" does not hold on real positions; the true statement is that mate mode costs 100–500× on
    ordinary positions as a rule**, and the single board this report has been quoting happened to sit at
    the low end. **1140 of 1600 cells differ from `go depth 2N−1`, and 571 differ in the MOVE.**
   - **Owner-facing consequence: a corpus labelled under `go mate N` is labelled by a mate-hunting search,
     not by depth `2N−1`, and mixing those labels with `go depth` labels mixes two incomparable searches.**
  - **A measured defect in the reporting, with a mechanism.** On a board whose true distance is mate in 5,
    **`go mate 4` reports `mate 6`** — a score implying 11 plies from a search that reported **depth 7,
    seldepth 8, and a 7-ply PV that does not replay to mate.** **A mate in 6 moves cannot be established by a
    7-ply search; it needs 11.** The mechanism: **qsearch clamps `alpha = max(alpha, mated_in(ply))` and
    `beta = min(beta, mate_in(ply+1))`, so a fail-high stores a mate-ENCODED value, and the iteration break
    `score >= mate_in(2N−1)` passes it on by its encoding rather than by its meaning.** **Scan of 1,200
    requests: 6 hits — 4 where the distance was TRUE but exceeded N (an unhonoured request) and 2 where the
    distance was WRONG (a false claim).** Controls at the truth's own N are correct **6 of 6**, so it is
    **edge-local rather than pervasive.** **And `search.cpp:1434`'s window-empty branch is UNREACHABLE** —
    it needs `2*ply >= 63999` against `MaxPly 128` — so that guard has never protected anything.
  - **Which heuristics actually change a mate answer, measured with 19 distinct binaries**: **the TT gates
    change 0 of 148 answers while halving or doubling nodes**, so TT is a speed question and not a
    correctness one. **`Lmr` + `FutilityPrune` change 55 of 148 and enabling them LOSES mates** — one board
    goes from `mate 2 / g1b1 / 894 nodes` to **`cp 831 / g2h1 / 331`**. **`SingularExt` and
    `QuietExtinction` are inert**, and only in endgames.
  - **And a ninth false-mate mode, found later, is a SWITCH rather than a parser bug: `ContHist4PlyRead`
    reports `mate 12` for a mate in 5 plies.** On `3k4/8/6K1/1Q6/8/8/8/8 w - - 6 4` at `go depth 12`:
    **59228 nodes and `g6f7` with the switch on, against `cp 1203` / `b5b7` / 80842 nodes with it off.
    I reproduced both arms myself and verified the claim three ways**:
    - **`mate 12` implies 23 plies and the PV it prints is 14**, so the PV cannot deliver the score it
      claims — and replaying it against python-chess ends at `3Q4/3K4/k7/8/8/8/8/8`, **not checkmate**.
    - **The true distance is 5 plies**, established by an exhaustive AND/OR search (none in 1 or 3, mate in
      5). So the **distance is wrong by seven plies** while a mate really does exist: **this is a wrong
      distance, not a missed mate and not a mate where there is none.**
    - **It requires the switch.** `ContHist4PlyRead` is `default false` and **the default build is correct
      on this position**, so the blast radius is exactly "whoever turned it on" — a shipping decision, not
      an emergency.
    - **Scope measured by the seat: 1 of 30 mate fixtures.** Narrow and position-specific, **not a collapse
      of mate detection**, and **the mechanism is not established and is not claimed** — a reproducible
      wrong answer with an unproven cause is the honest form.
  - **Three mate-defect classes now have to be kept apart, and a checker that conflates them will report one
    as another**: a **wrong distance where a mate exists** (this one, off by 7 plies); a **false mate where
    none exists**; and a **PV too short to verify the score** (10 of 190 claims in one corpus, which an
    earlier draft of this report wrongly called false mates). **Only the first two are defects.**
  - **And a short clock silently costs the mate**: **3 of 7 clock forms changed the answer on a
    mate-in-4 board.** Separately, **5 of 21 clocked cells publish a score the clockless search does not
    give at the same reported depth**, because `emit(depth, result.score, …)` prints the **unfinished
    iteration's depth beside the last finished iteration's score** — the same label/quantity mismatch the
    ponder audit found in `info time`.
3a1. **`movestogo` and `ponder` WITHOUT a clock are UNBOUNDED.** With a 20 s cap: `go movestogo 20` and
   `go ponder` both give **no `bestmove` after 20 s**, still climbing (depth 28). `movestogo` only sets a
   field the **clock planner** consumes, and `ponder` only *suppresses* the clock — **neither token is a
   limit on its own and neither says so.** Same family as an absent `btime`, which is also no clock.
   **A match harness sending `go ponder` or a clockless `movestogo` gets a search that never returns.**
   - **A `movestogo` audit found that the WIDELY-REPEATED "`movestogo 0` means sudden death, 8.4× the
     plan" claim is FALSE IN THIS TREE, and it was mine.** The reading came from `clock_plan.hpp`'s
     `if (moves_to_go > 0)` branch, but **the parser clamps first**: `uci.cpp:117` is
     `limits.moves_to_go = std::max(1, read_int())`, so **`0` and `-1` are rewritten to `1` before the
     planner ever sees them.** Measured against the engine's own header at a 2000 ms clock:

     | token | parsed | soft | hard |
     |---|---|---|---|
     | `movestogo 0` | **1** | **995 ms** | 1,592 ms |
     | `movestogo -1` | **1** | **995** | 1,592 |
     | `movestogo 1` | 1 | **995** | 1,592 |
     | `movestogo 50` | 50 | 39 | 156 |
     | `movestogo 100` | 100 | 39 | 156 — **the 50-clamp is real** |
     | *(absent)* | 0 | **90** | 450 — **the true sudden-death plan** |

     **And the wall-clock measurements follow the plan**: `movestogo 0` returned in **735 ms**, `-1` in
     **713 ms**, `1` in **892 ms** — one regime — while **omitting the token returned in 122 ms.** **So
     `movestogo 0` is not sudden death; it is the `movestogo 1` branch, which is the MOST AGGRESSIVE
     plan the option offers** (soft 995 ms against a 90 ms sudden-death default). **A reader who acted on
     the old claim would have expected 8.4× the plan and got 11× in the other direction** — the two
     readings are opposite, not merely different. **The practical rule survives and inverts**: **omit the
     token to get sudden death; sending `0` is the loudest possible request for a short, evenly-spread
     budget.**
   - **A ponder audit found this rule UNDERSTATED the problem in two separate ways.** First, **a ponder
     with BOTH clocks is still unbounded**: `go ponder wtime 10000 btime 10000` gives **no `bestmove` at
     20 s (depth 28, 24.8 M nodes, 99.9% CPU) or at 45 s (depth 32, 61.2 M nodes)**. The rule above only
     claimed the clockless case, and the clocked case is what a match harness actually sends.
   - Second, **there are TWO KINDS of "unbounded" and they look identical from outside**: a clocked or
     clockless `go ponder` is a **runaway** (100% CPU, depth rising), while **`go ponder depth N` or
     `go ponder nodes N` is a search that FINISHED and is idling on its answer** (0.1% CPU, depth flat).
     **Both stop at `stop` in under 1 ms, both print nothing to say what is happening, and a monitor
     cannot tell a full core from an idle process.**
   - **And when the ponder DOES end, the budget starts at the `ponderhit`, not at the `go`.** Measured
     decisively: a ponder **6 s long against a hard limit of 225 ms** — 26.7× over — still received
     **225.9 ms** afterwards. A `go`-based budget would have been exhausted 5.8 s before the hit and
     returned in about 0 ms. Across 16 offsets at two clocks: **0 rows returned in ~0 ms**, worst excess
     over hard **0.9 ms**. (An upper bound, not an equality: 10 of 16 rows stop below 60% of hard at
     iteration boundaries.)
   - **But the two clocks disagree about what they are measuring**: `info time` counts from the `go` while
     the budget counts from the `ponderhit`, so after a 3 s ponder you see **`time 4140` against 1141 ms
     of actual thought**, with the gap equal to the ponder length on three cells. **The budget is right and
     the label is wrong** — which is the worst combination for anyone who trusts `time` as a duration.
   - **`stop` without `ponderhit` returns the move it found, never `0000`** (18 of 18, stop-to-bestmove
     0.7–1.0 ms) — **except at 0 ms of thinking, where it returns the first legal move, byte-identically to
     the piped-abort artefact**, so that case is reported as undecided rather than as an answer.
   - **And `Ponder` itself only appends ` ponder <move>` to the bestmove line**: identical node counts on
     both arms (17,804 each), no self-pondering, and it does not gate the token. **It defaults to false, so
     a GUI gets no ponder hint at all unless it sets it**, and the hint is omitted when the PV has one move.
3aa. **An unparseable `go` VALUE is replaced by a default, silently — but which default is NOT one value,
   and on the BASE two of the seven forms are UNBOUNDED.** **An earlier version of this rule said all seven
   malformed requests "land on one identical search: depth 5, 1,001 nodes", and that is WRONG on the audit
   base in the direction that understates the hazard.** Re-measured on `6b98f217`, midgame, `OwnBook false`,
   fresh process per cell, 20 s cap:

   | command | what happens on the BASE |
   |---|---|
   | `go depth 5` | depth 5, 896 nodes, 3 ms — the well-formed reference |
   | `go depth abc`, `go depth` (no value), `go depth 0` | **depth 1, 41 nodes** — `std::clamp(0,1,64)` = 1 |
   | `go wtime abc`, `go wtime 0` | **depth 1, 41 nodes** — `read_clock()` returns 0 on failure |
   | `go movetime abc` | depth 4, 312 nodes — a *different* short search |
   | **`go nodes abc`, `go nodes` (no value)** | **NO `bestmove` in 20 s — UNBOUNDED** |
   | `go nodes 0` | returns at once, **zero `info` lines** |
   | **`go mate abc`** | **NO `bestmove` in 20 s — UNBOUNDED** |

   - **`go nodes abc` applies no limit — but it is NOT `go infinite`, and the difference is termination
     class.** An earlier version of this bullet said they were the same, verified over a 6 s window. **They
     are the same inside a window and different at the end, and I re-measured both with stdin held open:**
     on a bare K+R v K, `go nodes abc` **returns on its own in 38.7 s at depth 64** while `go infinite`
     reaches that same depth-64 clamp at 38.5 s and then **blocks waiting for `stop` forever**. On a
     middlegame neither returns inside 120 s, because depth 64 is unreachable in any practical budget.
     **So a harness that mis-types a node budget gets a search that will not come back in usable time**,
     and one that relies on "it eventually returns" is relying on a property that holds only where the
     depth clamp is reachable.
   - **The mechanism is in `parse_limits` and it explains why the forms differ.** `nodes` sets
     `limits.nodes` **only when the parse succeeded** (`uci.cpp:108-113`), so a malformed count leaves
     **no limit at all** — and with no limit and no clock the search runs to the depth clamp. `depth`
     instead goes through `read_int()`, which returns **0** on failure, and `std::clamp(0, 1, 64)` makes
     that **1**. **Two keywords, one parser, opposite failure modes: one degenerates to the smallest legal
     search and the other to no limit at all.**
   - **And the parser has a worse shape than a bad value: a keyword with no numeric value EATS THE NEXT
     KEYWORD.** `read_int`, `read_clock` and the `nodes` branch each advance the token index
     **unconditionally** before `from_chars` decides the token was not a number (`uci.cpp:91`, `:101`,
     `:106`). So **`go nodes depth 5` parses as: `nodes` takes the literal token `depth`, fails, sets no
     limit; `5` matches no keyword and is stray.** The command is unbounded and **every token in it is
     well-formed.** Same shape through `mate`, `softnodes` and `movestogo`, and the mirror case
     `go depth nodes 50000` is a **1-ply** search because `depth` eats the token `nodes`.
   - **A good limit beside a bad one does NOT reliably survive, and the clock is the case that inverts the
     rule.** `go nodes abc movetime 100` → movetime binds (13/84,245); `go nodes abc mate 3` → mate binds
     (5/53,074); `go depth 5 nodes abc` → depth binds. **But `go depth 5 wtime abc` → depth 1, 42 nodes**,
     because a failed clock becomes **0 ms** and 0 ms binds harder than anything else on the line. And
     **`go depth 5 nodes 0` → zero `info` lines and the first legal move**, so an explicit zero overrides a
     depth. **The generalisation "a good limit wins" is true for node and mate keywords and false for
     anything whose parse failure defaults to zero rather than to absent.**
   - **The unbounded family is also wider than `nodes` and `mate`**: `softnodes`, `movestogo`, and bare
     `go` with no limit keyword at all are unbounded, and `wtime`/`btime`/`winc`/`binc` are unbounded
     **when the keyword names the side that is not to move** — so a well-formed `btime` on a white-to-move
     board sets nothing. **A misspelled keyword is unbounded rather than defaulted**: `go foo`, `go Depth 5`
     and `go depth=5` are all `go infinite`.
   - **So the five-shapes framing needs its distinguishing feature re-stated.** It is not "a DEFAULT
     value"; it is **"whatever `0` means to that keyword"** — the floor for `depth`, the wall clock for
     `wtime`, and *unlimited* for `nodes`.
   - **ALL OF THIS IS FIXED ON THE PC BUILD, AND I VERIFIED THAT BY REBUILDING IT.** `FORGE_FIX_GO_PARSE`
     in the r15 patch changes the parser, and on the rebuilt r15 binary
     (sha256 `068f0927…`, all four pins matching) the same eight commands give:

     | command | BASE | **PC r15** |
     |---|---|---|
     | `go depth abc` / `go depth` / `go wtime abc` | depth 1, 41 nodes | **depth 1, 41 nodes** — unchanged |
     | **`go nodes abc`** | **unbounded** | **depth 1, 41 nodes — bounded** |
     | **`go nodes` (no value)** | **unbounded** | **depth 5, 896 nodes** |
     | `go movetime abc` | depth 4, 312 | **depth 5, 896** |
     | `go movetime 0` | 3/4/5, unstable | **depth 6, 1,683** |
     | `go mate abc` | **unbounded** | *(not re-run; the parser fix covers the value path)* |

     **So the base's two unbounded forms are a BASE defect that the owner's own PC build already fixes**,
     and a harness targeting the base must guard against them while one targeting r15 need not. **That
     distinction was missing from every version of this trap**, and it took rebuilding r15 to see it.
   - **The `go depth abc` — `go depth 5` identity in the earliest version is false on BOTH builds.** On
     the base the two produce **different** `info` streams (depth 1 / 41 nodes against depth 5 / 896); on
     r15 they also differ. **The row that claimed they were identical named `068f0927`, which turns out to
     be the sha256 of the r15 BINARY rather than a commit — so the number was checkable all along and the
     claim does not survive the check.**
   - **`go movetime 0` is not an identity with anything, on either build.** On the base, 10 fresh processes
     gave **depth 3 (215 nodes) three times, depth 4 (404) three times, depth 5 (1,001) four times, and
     occasional runs with no `info depth` at all** — a zero wall clock stops at the first iteration boundary
     the clock check sees, so **the outcome depends on process startup time and is not a property of the
     command.** On r15 it gave depth 6 / 1,683 in one run. **Do not use it as a control for anything.**
   - **What survives, and it is still the right lesson:** the engine **says nothing** on any of these
     forms. `setoption` reports every malformed form — bad value, out of range, missing `value` keyword,
     unknown name — and leaves the old value in place, so **the engine already knows how to refuse a bad
     request; `parse_limits` simply has no else branch on the base.** **A refused option preserves intent
     and shows an error; an improvised limit runs on a number the caller never supplied — or on no number
     at all.**
   - **The harm is two experiment arms silently becoming one**, with no error and no after-the-fact
     detection — the same mechanism that made `go depth 16 multipv 3` mean MultiPV 1.
   - **A depth column measured under a timeout is a column of the harness's patience.** One matrix first
     reported `go depth 123 → depth 26`; that was an 8-second cap, and the same command reaches depth 29
     at 49 s and is still searching. **Separate `RETURNED` from `CAPPED` in any such table**, which is
     exactly what makes the two unbounded base rows visible at all.
3ab. **An unrecognised `position` TYPE is silently ignored and the previous position is re-searched**,
   with **nothing on the wire at all** (re-confirmed on the base commit: `position nonsense` after a
   book-answered K+R v K position returns `d2d4` with no diagnostic, while the six-field form returns
   `a1a8`) — because the type keyword is never validated, so the FEN
   validator never runs. `position nonsense` after a K+R v K position answers the predecessor's `a1a8` /
   mate 1 / 126 nodes with no diagnostic; after a middlegame it answers that position's move with a
   slightly different score. **The `fen` path is thorough and the type validator does not exist** — that
   asymmetry is the finding.
3ac0. **Junk before the `moves` keyword does NOT drop the moves — the moves still apply, silently.** On the
   base build, `position fen <K6k> moves a1a2` gives **perft 2 = 15**, and **`position fen <K6k> bogus moves
   a1a2` also gives 15** — the moves were applied. The board-only form gives **9**. **So a malformed position
   silently becomes a real one.**
   - **A `perft 1` fingerprint CANNOT see this, and an earlier version of this entry used one.** Bare K6k has
     **3** moves; after `a1a2` it is Black to move with a lone king, which also has **3**. **Identical by
     construction.** **Perft 2 separates them (9 vs 15); perft 1 does not.**
   - **On the older tree the behaviour is the opposite**: the whole command is dropped and the engine stays
     on startpos (perft 2 = 400). **So this one is tree-specific, and the "junk drops the board" reading was
     the older tree's behaviour, not the base's.** **A junk token is
   discarded and the list applies**, which is one defect with two positions, not two defects.
   - **Reading note for this family: `0000` can be CORRECT.** On a root that is already won (a mate in
     one available and the game effectively over for the search), `0000` is a legitimate answer, not a
     failure — **which is why every row in these tables needs a reference row beside it.**
3ac. **A corrupted move list TRUNCATES at the bad token, and the position searched is the legal prefix.**
   `position startpos moves e2e4 zzzz e7e5` reports `illegal move zzzz` and then **stops** — the moves after
   the bad token are **not** applied.
   - **Confirmed at perft 3, where every prefix has a DISTINCT count.** The startpos prefixes of
     `e2e4 e7e5 g1f3 b8c6` are **8902 / 13160 / 24825 / 23193 / 24079** for 0, 1, 2, 3 and 4 plies. An illegal
     token inserted at index **0, 1, 2 and 3** returns **exactly the prefix value for that index**.
   - **Index 4 is AMBIGUOUS and is reported as such rather than counted as a fifth confirmation:** inserting
     the bad token at the end returns **24079**, and **24079 is also what a splice would give**, because there
     is nothing after the token for the two hypotheses to disagree about. **Four of five indices discriminate;
     the fifth cannot, and the table says so** — which is the same discipline that made the perft-2 test
     fail, applied one level in.
   - **A SPLICE claim was made and WITHDRAWN, and the reason is a perft-2 COLLISION.** `e2e4 e7e5` and
     `e2e4 e7e5 g1f3 b8c6` **both give perft 2 = 835** — two different boards, one count — so at perft 2 a
     spliced four-move sequence lands on the same number as a two-move prefix and the two hypotheses are
     indistinguishable. **Perft 3 separated them and reversed the conclusion.** **A fingerprint test needs a
     depth at which the candidate hypotheses make DIFFERENT predictions; otherwise it confirms whichever one
     you already believed.**
   - **Practical consequence: the warning is truthful, so a harness CAN trust it.** `illegal move zzzz` means
     the position is the legal prefix — not the intended one, and not a splice. **That is a usable signal
     rather than a hazard**, which is the opposite of what an earlier version of this entry said.
3a. **A PIPED harness measures nothing — and a legality check will not catch it.** The fabricated
   `bestmove` is **per-position, not fixed**: **13 distinct fabricated moves across 60 positions, 0 of 60
   equal to the real answer, and ALL 60 LEGAL.** **A legality check accepts 60 of 60**, so a piped run is
   not detectable by its move. **The only reliable detector is an `info depth` line count of zero**, which
   held **60 of 60**. It is budget-independent too — the same fabrications for the same positions at depths
   4, 8, 12 and at 50k and 500k nodes — so **the fabrication is a function of the position alone, not of
   the search**. `printf '…go depth 8\n' | forge` gives **zero `info depth`
   lines and a fabricated `bestmove a2a3`**, because EOF aborts the search — and it is perfectly
   reproducible, so it looks like a measurement. **Same class as a silently refused FEN**, and the same
   fix: do not let EOF reach a running search.
3b. **A python-chess validator does not make a harness safe.** `4k3/8/8/8/8/8/8/R3K2R w K - 0 0` (fullmove
   `0`) is **valid to python-chess and REFUSED by the engine**. Validation and acceptance are different
   gates and both must be checked.
3c. **Memory pressure never changes an answer; it kills the process.** Stepping `ulimit -v` from 1 GB
   down to 16 MB: **every cap that ran gave 0 of 12 differing**, and below the cliff **12 of 12 died.**
   Bisected exactly: **Hash 16 — 59 MB dies, 60 MB works; Hash 256 — 290 MB dies, 300 MB works.** **No
   silent middle band** — which is the reassuring shape, and it was checked rather than assumed. **The
   rule of thumb the seat derived is "the cliff is roughly the table size plus ~40 MB", and it holds at
   both sizes measured.**
   - **A paraphrase of this trap was once written as "dies at 56" and that is not what the source says** —
     56 is the largest cap in the stepped series that died, not the bisected boundary; the bisection
     reports **59**. Both are true statements about different measurements, and a reader comparing the two
     would have seen a contradiction. **Quote the bisected pair or the series, and name which.**
   - **The 59-versus-56 discrepancy in this trap is itself an example, and a seat caught me on it.** My
    first paraphrase merged the stepped series and the bisection into "dies at 56", which contradicts the
    bisected 59. **Two true statements about different measurements, compressed into one number, become a
    contradiction** — and the seat that was going to quote the pair noticed and pre-registered a direct
    test of 59 rather than inheriting either version. **A paraphrase is where a measurement loses its
    label.**
  - **And the consequence for a harness is the operational half**: **"engine exited without `bestmove`"
     must be a hard failure and never a missing cell**, because an out-of-memory kill looks exactly like a
     short read. The failure is loud in the process table and silent in the output stream.
  - **The soak seat's first version of this check reported 13 of 15 caps "not identical", and every one was
     a timing field.** The answer key included `nps`; re-keyed to `(bestmove, score, nodes)` it was **0 of
     18 differ**. **An identity comparison must be keyed on fields that cannot vary with load**, and `nps`,
     `time`, and any derived rate are the ones that do — on a memory-capped run they vary because the run
     is slower, which is the variable under test. **A memory verdict keyed on `nps` measures the cap.**
4. A malformed `setoption` without the `value` keyword is **silently ignored**. Read the reply to
   every setoption and assert the applied option count and value.
4a. **An unknown `go` token is ALSO silently ignored, with nothing printed.** `go depth 10` and
   `go depth 10 nonsense_token 3` give **identical depth, nodes and score** (10, 9,575, cp 21) on a fresh
   process each. **This is the mechanism behind a real near-miss: `go depth 16 multipv 3` means MultiPV 1**,
   because MultiPV is a `setoption` here and the `go` token is discarded — so two arms of a replication
   ran **identical configuration** and produced **0 disagreements in all three strata**. **Only a
   "must be non-zero" sensitivity control caught it**; without that control the finding would have been
   published as "MultiPV never changes the move." **Assert the configuration from the engine's own reply
   before comparing two arms.**
5. A mid-search `setoption` silently stops the search.
5a0. **The ep-fen defect can MANUFACTURE A FALSE ASYMMETRY in a symmetry check, which is the worst place
   for it.** A symmetry test that re-emits `m.fen()` to build the mirror can lose the ep square on one
   side but not the other, because **a mirror has a different king-safety situation from its original** —
   so the two sides disagree about whether an ep capture is legal, and one is evaluated **without** the
   ep square. **A check whose whole job is detecting asymmetry would have reported asymmetry that the
   engine does not have.** Reproduced: `4r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1` parses with
   `has_legal_en_passant() == False` and `.fen()` emits `-` where the input had `d6`.
   - **The fix is to take the ep field from `board.ep_square`, not from `fen()`'s decision.** Verified a
     **no-op on the current data (0 of 60 unchanged)** — the path was closed before a corpus with ep used
     it, which is the right time to close it.
5a. **A GENERATED en-passant test can lose the edge on the way to the engine, and pass vacuously.**
   `python-chess`'s `Board.fen()` **silently drops the ep square when no legal ep capture exists** —
   which is **precisely the ep-exposes-king position** the test is trying to build. So a generated fixture
   for "ep that would expose the king" arrives at the engine **without its ep square**, the engine
   correctly finds no ep capture, and the test passes without ever testing the edge.
   - **A second and worse case of the same family: the library's REPETITION rule can be STRICTER than the
     engine's, and it cuts your corpus at the first TWOFOLD.** A seat building a threefold corpus with
     `python-chess`'s claim logic found **17 of 31 games affected** — the repetition arm was being truncated
     before the engine ever saw a third occurrence. **That is a corpus defect that produces a clean-looking
     run and a confident zero**, and it is the same shape as the vacuous random-games null: the data could
     not reach the condition.
   - **So the reference library is not a neutral oracle in either direction.** It can drop a field the
     engine would accept (ep) and it can refuse a position the engine would play on (repetition). **Both
     failures are silent, and both make a test pass.** The rule is to **use the library to CHECK the engine
     and never to CONSTRUCT the input**, and where construction is unavoidable, **compare the constructed
     FEN against the string you intended, field by field** rather than trusting the library's canonical
     form.
   **Hand-written FEN literals are safe; generated ones are not.** Measured: the engine accepts the square
   when present and agrees with the reference (`nodes 6`).
5b. **A refused FEN manufactures false movegen bugs.** After a kiwipete position, a refused FEN answered
   `go perft 1` with **`nodes 48`** — **kiwipete's count, for the wrong board**, one `info string` earlier.
   **Any perft harness without a board-identity check will report that as a movegen defect.** The gate:
   `go perft 1` must match the reference in **count AND move set**, plus `go perft 2` at depth ≥ 3.
5c. **`go perft` ends with a bare `nodes N` line, not `bestmove`.** A reader waiting for `bestmove` blocks
   on it; a harness that checks for one reports the perft as a hang.
6. **A refused `position fen` still answers `readyok`, the engine keeps the previous board, and a
   search then returns a normal-looking result for that previous position.** Measured on both builds:
   an illegal FEN (adjacent kings) produces `info string invalid FEN: kings may not be adjacent`
   followed by a **complete search of the PREVIOUS position** — a legal `bestmove`, a plausible
   ±30 cp score, a full PV, correct-looking node counts. **The only notice is one `info string` line,
   which is the line class most harnesses skip.**
   - **Worse than a startpos fallback, because it depends on session history.** After a valid K+R v K
     position, the illegal FEN returned **the previous position's `mate 1` and the same move again**.
   - **The discriminator that proves it is "the previous position" rather than "startpos": send the SAME
     invalid FEN after two DIFFERENT valid positions.** A startpos fallback predicts the same answer both
     times; a refusal predicts no `bestmove`; "previous position" predicts **each predecessor's own
     answer, differing**. Measured: after position A the invalid FEN answers `a1a8` / mate 1; after
     position B (after 1.e4) it answers `e7e5`. **The answers follow their predecessors and differ from
     each other, so startpos is excluded.** Bit-identical across three runs on PC r15, and identical on
     the base build, so it predates the patch.
   - **The fabricated row OFTEN has no duplicate signature — but not always, and the partial signature
     cannot be relied on.** Measured over five predecessors, the invalid-FEN answer against its
     predecessor's:
     | predecessor | its answer | invalid-FEN answer | |
     |---|---|---|---|
     | K+R v K mate | `a1a8` / mate 1 | `a1a8` / mate 1 | **DUPLICATE** |
     | middlegame A | `f1e2` / cp 95 | `f1e2` / cp 100 | differs |
     | middlegame B | `e1g1` / cp 28 | `e1g1` / cp 28 | **DUPLICATE** |
     | endgame K+P | `e1f2` / cp 200 | `e1f2` / cp 209 | differs |
     | startpos | `d2d4` / cp 14 | `d2d4` / cp 24 | differs |

     **So comparing a row against its predecessor would catch about 40% of these, and 60% carry no
     signature at all.** Where the score does differ it differs because the re-search runs on a restored
     board with different TT and history state, so **a row keyed on `(fen, bestmove, score)` looks like a
     FRESH measurement** — a different score for a different FEN is exactly what a real measurement looks
     like.
   - **Predecessor-comparison is therefore an UNRELIABLE mitigation, and it is the "clever" one someone
     will reach for.** The only defence that works on all of them is **confirming every FEN was
     accepted** — `readyok` is not a statement about the position.
   - **Two mechanical defences, both needed:** validate every FEN before sending it, **and scan both reply
     streams for `invalid FEN` and abort.** The engine gives a per-position verdict; a harness that
     ignores it has no defence at all.
   - **But the diagnostic arrives in response to `position`, BEFORE `readyok` — not during the search.**
     So **any harness that sends `isready` between `position` and `go` — the normal defensive pattern —
     consumes the diagnostic and never sees it.** Reading the *search* reply for the error finds nothing.
     **It has to be the position reply.** A seat found this only because its own control failed against
     a real engine: a probe scanning the `go` output reported a startpos result with no error at all.
   - **There are TWO fallbacks, not one.** With no predecessor the invalid FEN is answered from
     **startpos**; with a predecessor it is answered from **that predecessor**. A four-cell matrix over
     (isready sent? × predecessor present?), every cell with a legal control so "absent" cannot mean
     "never fires", gives the diagnostic **in all four cells and never for the control** — identically
     on both builds:
     | isready? | predecessor? | diagnostic? | bestmove |
     |---|---|---|---|
     | no | no | **YES** | `d2d4` (**startpos**) |
     | no | yes | **YES** | `a1a8` (**the predecessor**) |
     | yes | no | **YES** | `d2d4` (**startpos**) |
     | yes | yes | **YES** | `a1a8` (**the predecessor**) |

     **So the answer is "the last VALID board", which in a fresh session is startpos** — a description
     that covers both cells, where "the previous position" describes only one. **It is one rule, not two
     falls back to**: startpos is not a separate fallback, it is what "last valid" means when nothing has
     been established.
   - **And it was tested as a rule rather than adopted as a sentence, with a sharp prediction that could
     fail:** if the answer is the last *valid* board, **an invalid FEN must not displace it**, so two
     consecutive invalid FENs should both answer the same predecessor. Measured — legal predecessor
     `a1a8`, invalid (kings d5/e5) **`a1a8`**, invalid (kings a1/b1) **`a1a8`**. **Both answer the
     predecessor, so an invalid FEN never displaces the last valid board.**
   - **The first attempt at that refutation was the author's own instrument error**: the second "invalid"
     FEN put kings on d5 and f1, which are **not adjacent**, so the board was legal and the engine
     searched it correctly. **Verify the input is what you believe before interpreting the engine's
     response to it** — the check is one line, and it is now the fourth time tonight that a discrepancy
     about to be reported was the measuring instrument.
   - **It is emitted EXACTLY ONCE per command — it MOVES rather than duplicating.** With `isready`, the
     position reply carries it and the search output does not (`position=1 go=0`); without, the search
     output carries it (`go=1`). **So scan both streams, but assert ONE occurrence**: a checker that
     required it in both would always fail.
   - **THE LOCATION IS FIXED, NOT MOVING — and an earlier statement to the contrary is WITHDRAWN.** The
     diagnostic is emitted **synchronously on the `position` command, always**, whether or not `isready`
     follows. Re-measured directly on a fresh build with four harness patterns: with `isready` after
     `position` it arrives **before the next `readyok`**; **without** `isready` it still arrives
     **immediately on `position`**, not in the `go` output. A prior claim that it "moves into the `go`
     output when `isready` is not sent" is **refuted** — it came from a probe that read the wrong slice,
     which is the same error the probe was built to detect.
     **Scan the position reply. Scanning the `go` output alone will not find it.**
   - **TOO FEW FIELDS IS REFUSED WITH A DIAGNOSTIC; TOO MANY IS ACCEPTED AND THE SURPLUS DROPPED.**
     Measured on the base commit `6b98f217` (bench 11 = 312,866 verified on the same binary), two boards:

     | fields | diagnostic | board honoured? |
     |---|---|---|
     | 6 | none | **yes** |
     | 5, 4, 3, 2 | `invalid FEN: FEN must contain six fields` | **no — previous kept** |
     | 7, 8, 9 (`… 0 1`, `… bogus`, `… w`) | **none** | **YES — surplus dropped, board loaded** |

     **So "malformed is silent" is false in both directions**: short FENs speak, long FENs are honoured.
     Both halves matter for a harness — a 5-field FEN is **refused loudly and then searches the previous
     board**, while an 8-field FEN is the position you meant.
   - **An earlier version of this section claimed "any field count other than six is refused in silence and
     searches startpos". That is WITHDRAWN.** It was measured on the wrong commit —
     `integrate/combo29-all`, which does **not** contain `6b98f217` — and on the base the surplus is
     accepted. **A build whose provenance was assumed rather than checked produced a confident wrong
     result**, which is the same class as the defects it was measuring. The rebuild verified its pin
     (bench 11) before any of these rows were recorded.
   - **The engine's silence is not a guide to whether the answer is about your position — in either
     direction.** Two findings are opposite in consequence and must not be reported as one class:
     | | an ILLEGAL FEN (adjacent kings) | a MALFORMED-but-ACCEPTED FEN (adjacent digits in a rank) |
     |---|---|---|
     | diagnosed? | **yes** | **no** |
     | board searched | **the previous one** | **the intended one** |
     | severity | **high — a fabricated row** | **low — the correct answer** |
     **So the engine says nothing for the parse that is fine and says something for the one it then
     searches wrongly.** A reader who treats "no diagnostic" as "safe" and "diagnostic" as "refused" gets
     both cases backwards.
   - **Verified on the accepted side: 38 of 38** adjacent-digit FENs give the same `perft 2` as their
     canonicalised form — **0 differ** — so a tolerated malformation is a *different* defect class
     from a refused one, and treating them together would inflate the smaller finding into the larger.
   - **The fingerprint needs TWO comparisons, because they answer different questions.**
     **Engine vs engine** (the FEN sent against its canonicalised form) isolates the **parser**: same
     board means the parser read the intent. **Engine vs an independent implementation** (python-chess)
     isolates **move generation**, and is the stronger claim — two independent legal-move generators
     agreeing to depth N is hard to fake. **Both are needed: the first can pass while movegen is broken,
     since both sides run the same engine; the second only runs where the other library accepts the FEN.**
   - **Skips are counted and reported, not silently passed**: where the reference refuses the FEN, the
     tool prints `movegen=SKIPPED` and a skip count, so "nothing to compare" is distinguishable from
     "compared and agreed".
   - **And it self-tests every run against two DIFFERENT boards, requiring a difference.** **A fingerprint
     tool that has only ever said AGREES is indistinguishable from one whose comparison cannot fail** —
     the proof-of-need rule applied to a measurement instrument rather than to a checker.
   - **But there is a stronger rule that removes the whole class rather than answering it: ACCUMULATE THE
     RAW STREAM, THEN PARSE THE BUFFER.** "Read until the line I expect, discard the rest" is
     **placement-sensitive** by construction; accumulating everything the engine said and parsing it
     afterwards makes the question of *where* the diagnostic appears irrelevant. A harness built that way
     was **placement-proof without anyone telling it about the placement** — which is why its file
     reproduced the behaviour on a second machine. **Prefer this to any placement caveat.**
   - **This correction is itself the defect it describes, one level up.** The seat that found the
     placement first concluded "a fresh session gives no diagnostic", because it had tested with a probe
     that read one slice of output; **the diagnostic was absent from the lines it read, not from the
     engine.** Inferring engine behaviour from the slice of output a harness captured is exactly the
     S-C84 shape.
   - **An ad-hoc probe is where this bites.** A seat that validates FENs in its committed harnesses
     validated nothing in the throwaway probes typed for a new test — **the third instance of "a guard
     you have to remember to run is not a guard."**
   - Verify a stale board with `go perft 1` against an independent generator, and **choose a previous
     position whose move count differs from the refused board's**, or the test cannot fire: one attempt
     failed because both boards had 33 legal moves and would have passed either way.
7. **When two different limits produce IDENTICAL output, suspect the input never arrived.** A seat
   testing whether `go depth 200` exceeds the documented depth clamp used a near-empty board for speed;
   `go depth 70`, `go depth 200` and `go infinite` all returned **exactly 34 lines with identical
   timings**. **That is impossible for different limits, and the impossibility was the tell** — the
   board was illegal and had been refused, and the engine had said so on line 1. **A limit with no
   effect is more likely a refused input than a broken limit.**
8. An illegal move in a `position ... moves` list does not refuse: the engine searches the legal
   prefix and answers normally.
9. A test that cannot fire returns the same answer as one that found nothing.
10. Uniform results across unrelated inputs mean the input is wrong.
11. A bare node count names no search: same command, build, settings and counter required.
12. Any precision claim is bound to its measurement; the noise floor is a property of the workload.
13. Zeros are the easiest claims to leave unplanted. A planted case distinguishes "looked and found
    none" from "could not have found one".
14. Validating a summary statistic does not validate a table.
15. A settings **name** in a finding is not evidence the settings were sent. One harness's option list
    was named `S14` while containing the five PC20 switches: its behaviour was PC20, its name said S14,
    and the finding published the name. **Have a tool parse the harness (never import it) and print its
    option list plus the count of regime switches, ready to paste into the finding** — a list printed by
    the code cannot disagree with the code.
14b. **A column heading is a claim about what the column measures.** An arm labelled "time per identical
    node budget" had 0 of 120 positions with equal node counts — the last row of the output said so, and
    the heading was written anyway. The ratio then describes unequal work and supports no cost claim.
    **A cost check must compare a patch against its own base with identical node rows.**
16. A check must report how many rows it examined.
17. A discriminator is a hypothesis test: compute its power before announcing it as decisive. 103
    same-move cells with only 14 decided means the effective n is 14.
18. A one-sided clock (only the opponent's time sent) is **no clock**, and at a real budget it simply **does
    not terminate**: `go wtime 300000` with Black to move **never printed `bestmove` in a 330 s allowance**,
    reached **depth 39 / seldepth 56 / 416,554,567 nodes**, and was **still searching** — only an explicit
    `stop` ended it, with **zero `info string` lines.** Same position with its own clock: **13.1 s / depth
    31**. **So an unguarded harness hangs rather than playing badly.**
    - **The first published figure for this was 288.7 s and it was wrong, in the direction that understated
      the defect.** The seat's driver timed a search from the arrival of the last line it had READ, not
      from `bestmove`. For a search that answers those are the same event, so every other case was
      unaffected; for one that never answers, the measurement stops at the last completed iteration. **The
      engine's own `time` field said 238,847 ms at its last output and it then spent a further ~91 s inside
      one deep iteration emitting nothing** — which is exactly why the two clocks disagree. **The tell is
      structural rather than numeric: a duration must be measured from the event you are waiting for, and
      a timeout reported as "the age of the last output line" is the failure being measured, not the
      measurement.**
    - **Fixed by making the timeout impossible to express**: four separate fields (`bestmove_ms`, `wait_ms`,
      `last_output_ms`, and a `wall_ms` that picks the right one), plus a planted fake engine that prints
      one line and goes silent. **The self-test reports `wall=500ms last_output=0ms` for the fake; the old
      code called that a 0 ms search.** 12 of 12 on the real engine, 11 of 12 exit 1 against the liar.
      **Every committed number was then re-run on the fixed harness**, and the 1000+100 floor data was
      checked rather than assumed unaffected: **all 3,071 moves answered with a `bestmove`**, so the old
      measure was the bestmove arrival in every one of them.
    - **The 3+2 control is now a COMPLETE result and it still cannot test the floor** — that is measured,
      not argued. Both matches are 20 of 20 games:

      | match | plies | max used/available | overshoot of the HARD plan | lowest clock | moves at ≤200 ms |
      |---|---|---|---|---|---|
      | **1000+100** | 3,071 | 0.5937 | **+2.1 ms** | **176 ms** | **63** |
      | **3000+2000** | 2,604 | 0.5997 | +1.7 ms | 3000 ms | **0** |

      **So 0 of 2,604 moves in the 3+2 match were played at a clock below 200 ms and the clock never fell
      below its 3000 ms start** — the control cannot reach the floor, and its own analysis reports **8 of 9
      with the floor check as the one FAIL**, left failing rather than suppressed. **That is the correct
      verdict for a control that measures the wrong regime, and reporting it as a pass would have been the
      more comfortable error.**
    - **But "the formula reproduced every move within +2.1 ms" is the WRONG frame for that column, and a
      second seat measured why.** In those matches the **hard** plan is a ceiling that is essentially never
      reached — utilisation peaks at 0.596 — so "worst overshoot of the hard plan" is a statement about a
      bound nobody pushes against. **What the column actually shows is that the bound was never exceeded**,
      which is the useful claim. Measured independently at three time controls over **146 games and 19,084
      plies**: **exactly ONE move out of 19,084 exceeded its hard plan** (681 ms against a 680 ms plan,
      ratio 1.0015, +1 ms — the 1024-node poll edge), with **0 forfeits, 0 hangs, 0 illegal**.
      **So state it as "the plan was never exceeded" rather than "wall time equals the plan".**
    - **And the agreement *within ±2 ms* is an artefact of scale, which is why the same claim looked strong
      and is not.** Of moves landing within ±2 ms of their plan: **84.5% at 200+0** but **2.2% at 1000+100**
      and **1.1% at 3000+200**. At 200+0 the **median soft plan is 1 ms**, so ±2 ms is *larger than the plan
      itself* — the "agreement" there is a tolerance wider than the quantity. **This is the quantisation trap
      from §6 in its purest form: a tolerance must be small relative to the thing it measures, and here it
      was twice as large at one control and meaningless at the others.**
    - **And the worst single move in the whole set is the formula rather than a runaway**: 3+2's most
      expensive move takes **11,107.2 ms from an 18,521 ms clock** against a predicted cap of **11,106 ms**
      — a 1.2 ms miss on an eleven-second budget.
    - **`movetime` is the exception among the limits**: 10/30/60 s terminate at 9.99/29.99/59.99 s and never
      reach the depth clamp, so the two limits do not collide. **The 60% hard limit is a CLOCK-path rule**;
      on the movetime path soft equals hard.
    - **An increment larger than the clock does not over-draw**: clock 1000 / inc 2000 plans **594 ms
      (59.4%)** with soft pulled down to match, flat from 500 ms to 3e9. **No row plans the whole clock.**
    - **The floor needed a control the seat had to design.** At **3+2 the clock GROWS** (spend is below the
      2 s increment; remaining rises 3000 → ~3900), so that control confirms zero forfeits but **cannot**
      confirm the floor — **and across the complete 20-game match that is a count rather than an
      inference: 0 of 2,604 moves were played at a clock below 200 ms.** A **1000+100** match does test it:
      **20 games, 3,071 plies, 0 forfeits, 0 hangs, 0 illegal,
      0 refused positions**, max move-time ÷ clock **0.5937**, **max 114.5 ms at a ≤200 ms clock** —
      which is `0.6 × (200 − 10) = 114.0` to the millisecond. **And across that match and two others
      (146 games, 19,084 plies, three time controls) exactly ONE move exceeded its hard plan** — so the
      honest form is **"the plan was never exceeded"**, not "wall time equals the plan".
    - **And the clock can always be spent**: a 2× overcharge reaches an equilibrium of 1376 ms rather than
      draining; a **10×** one reaches **clock 0**, where the engine still answers legally in 0.1–0.6 ms,
      **60 of 60 plies.**
19. **The opening book fires on a narrower condition than "the clock form": it fires on the
    SIDE-TO-MOVE'S OWN clock, or on `movetime`.** **Re-verified on the base commit `6b98f217` with the pin
    checked (bench 11 = 312,866) on the same binary, because the seat that found it had built from a
    disjoint branch:** `go btime 10000` with White to move **does not book and produces no bestmove within
    the window**, while `go wtime 10000` books `c2c4` and `go movetime 100` books `e2e4`. **The mirror case
    also holds: `go wtime` with Black to move does not book.**
    - **And the consequence is worse than "does not book": with no recognised clock for the mover there is
      NO TIME LIMIT AT ALL** — one probe searched **90 s unattended, 33 depth lines**, and answered only
      after an explicit `stop`. **So an unguarded `go` with only the opponent's clock is a hang, not a
      mis-set option.**
    - **The line numbers were re-resolved against `6b98f217` and two of them had drifted.** On the audit
      base the book emit is **`src/uci.cpp:539-540`** (not 385-386 from another tree), the book gate is
      **`uci.cpp:525-527`**, and `time_ms` is assigned **only for the side to move** at
      **`uci.cpp:121-122`** (`wtime` sets it iff side is White, `btime` iff Black). The bail branch is
      **`search.cpp:2251-2271`**. **Code citations in this report point at the base commit; a citation
      from another tree will not land**, and a citation from this report that was never re-resolved will
      not land either — which is what happened to the gate and the `time_ms` lines until this check.
      The consequence stands: **`go btime 10000` with White to move does NOT reach the book and searches;
      the same command with Black to move books.** A depth, nodes or infinite harness can never hit the
      book; on the clock forms `OwnBook false` is needed **only when the moving side's clock is sent**.
    - **What the book emits is two lines and nothing else** (`uci.cpp:539-540`):
      `info string book move <uci>` then `bestmove <uci>`. **No `info depth`, no score, no node count.**
      A GUI showing a score for that move is showing its own default.
    - **Latency separates the paths by four orders of magnitude**: book **p50 0.024 ms, max 0.44 ms over
      200 round trips**, off-book **p50 442 ms** in the same harness. **A reader waiting for an `info
      depth` line times out on every book move**, proved with a passing off-book control.
    - **The `go infinite` arm was measured with a `stop` after 1.5 s**, so it is a short-search arm
      rather than evidence that `go infinite` terminates on its own (trap 24: on a real position it does
      not, and `stop` is what ends it).
19a. **The book PRE-EMPTS the drawn-root detection — verified on the base build, with the exact
    contrast.** **A one-hunk patch fixes it, and it is a PREDICATE rather than a reordering:** add
    `!root_drawn` to the book condition, using **the same three tests as the bail** (repetition, halfmove
    ≥ 100, insufficient material). **Because it only gates the book, `search.cpp` is untouched and node
    counts cannot move** — which is why the pin check is a real test rather than a formality: **all 11
    documented pins reproduce on both builds** (five depths × two net settings, plus perft 5).
    **Note the two pin counts used across this report are DIFFERENT SETS, not a stale number**: the **four
    honesty pins** quoted for most patches are bench 11/13/16 and perft 5, while the **11 pins** here are the
    full documented set in `LOCK.md` (5 depths × 2 net settings = 10, plus perft 5). **Both are pinned and
    neither moves** — **two pin counts side by side with no explanation is exactly the shape a reader assumes
    is a stale figure.**
    - **Effect on six roots, lock versus patched**: fifty-move + book entry **BOOK → bail cp 0, empty pv
      (FIXED)**; repetition + book entry **FIXED**; insufficient material **unchanged**; fifty-move with no
      entry **unchanged**; an ordinary book position **still books**; an opening with no entry **still
      searches cp 91**. **Pre-emption 2 → 0.**
    - **The two controls are what make it a fix rather than a removal**: a patch that simply disabled the
      book would pass the first four rows and **fail the fifth**, so the test can tell the two apart.
    - **Traps 1 and 3 are unchanged on the patched build**, checked explicitly rather than assumed.
    - **Two decisions are the owner's, not the seat's**: whether a drawn root should EVER book (a repetition
      at move 8 in a forced-draw line is arguably a book situation, so "always report drawn" is a policy
      choice), and whether to share the predicate with `search.cpp`, where the same three conditions now
      exist in two copies that agree today with nothing enforcing it. A halfmove-100 startpos with `OwnBook true` emits `info string book move c2c4` and
    `bestmove c2c4` with **no `info depth` line at all**; **the same position with `OwnBook false` gives
    `info depth 1 ... score cp 0 nodes 0 ... pv` and `bestmove a2a3`** — the bail's signature. **So the
    book decides before any draw adjudication runs**, and a drawn position ships a book move with none of
    the warnings a caller uses to detect a drawn root.
    - **A bare-kings position escapes, and the reason matters:** it is an automatic draw with **no book
      entry**, so with `OwnBook true` it still returns the `cp 0 / nodes 0` bail with `bestmove e3d2`.
      **The pre-emption needs the position to be in the book** — so a drawn position that a book
      happens to cover is exactly the dangerous case.
    - **The pre-emption's gate is the FEN's FULLMOVE counter, not the halfmove clock, and that is the
      sharpest form of the trap.** The **same 100-ply board books at fullmove 1 and bails at fullmove 16** —
      identical position, identical halfmove counter, opposite verdicts, decided by a field that has
      nothing to do with why the position is drawn. **So `Book Depth` and the drawn-root test are keyed on
      two different notions of "how far into the game we are"**, and a FEN with a doctored move number
      silently selects which of the two you get. This is why the predicate patch above has to gate the
      book on the **draw tests** rather than on depth.
19b. **`Book Depth` reads the FEN's fullmove counter, and the observed behaviour is real — but the
    DIAGNOSIS attached to it was WRONG and is withdrawn.** Sweeping the counter on an identical board does
    change the reply: fullmove **1, 5, 10 book `e2e4`, 15 books `c2c4`, 20 and 21 do not book at all.** What
    was wrong is the claim that this is a defect in how the depth is *derived*.
    - **`game_ply()` is evaluated AFTER `position` applies its moves, and `make_move` increments the counter,
      so it equals the total ply count** — which is what a book depth limit should mean. A 14-case matrix
      across three candidate derivations: **the current expression is correct 14/14, a "hybrid" 2/14 wrong,
      and the naive "use the history size instead" 4/14 wrong.**
    - **So DO NOT PATCH IT.** The naive fix lets the book fire in resumed games legitimately past `Book
      Depth`. **The observable behaviour I measured is real; the inference from it was not** — the same
      shape as the KNN case, and the second finding in this report that needed withdrawing rather than
      re-scoping. **It also means a FEN written with a wrong move number changes whether the book is
      consulted — which is a harness fact, not an engine defect.**
19c. **MultiPV is ignored on the book path**: a book reply carries no `multipv` line even at MultiPV 2
    or 3, so a caller expecting `MultiPV` lines on every search must handle the book case separately.
19c0. **The book is NONDETERMINISTIC across processes, and no harness in this run accounted for it.**
    `uci.cpp:161-162` seeds the book RNG from the wall clock (`steady_clock::now()... | 1ULL`), so the same
    command returns **different opening moves in different processes**. Measured: `go wtime 1000` on
    startpos over 24 fresh processes → **2 distinct bestmoves, `c2c4` 14× and `e2e4` 10×**, every one
    carrying the `info string book move` line. **I re-confirmed it independently**: six fresh processes
    gave `c2c4` four times and `e2e4` twice.
    - **Why this is a whole class of harness failure and not a curiosity**: an A/B comparison on any
      book-eligible position can differ **because of the RNG and not because of the change**, and **both
      arms show `info depth` count 0**, so the usual "one arm searched differently" reading is
      unavailable to rule it out. `Book Variety 0` pins the choice (one move, repeatable); the default 30
      does not.
    - **And it means a book move must never be asserted as a fixed expected value.** Two of this run's own
      seats had to withdraw an "arm changed" row for exactly this — one read its own clock-seeded RNG at
      n=5, and another was probing **startpos, which is booked**, so three fresh runs gave three different
      moves and pure RNG looked like a signal.
    - **The diagnostic that separates them is `info string book move`**: if it appears, the move came from
      the book and the RNG, not from a search. A harness filtering for `info depth` sees zero lines and
      **cannot tell a book reply from the `go nodes 0` no-search path**, which also emits zero `info depth`
      lines and a legal `bestmove`.
19d. **The book itself is SOUND — a clean bill, with the counts that make it one.** **2,520 of 2,520 book
    moves legal** against an independent generator; **2,429 of 2,429 polyglot keys match**; the walk
    covers **2,230 of 2,230 book keys**. **No book move loses material:** 135 moves were flagged by a
    static exchange check and **0 of 135 survived verification by an engine search at depth 12.**
    - **A maximum-gap sweep at depth 10: 1 of 2,520 above 100 cp, 0 of 2,520 above 150 cp**, against a
      noise floor of up to **42 cp** for the same measurement, and the worst offenders' gaps **shrink at
      depth 18** — **horizon artefacts, not book defects.**
    - **The "0 of 135" is worth more than a clean number because the checker first reported 929 false
      material losses**, from testing capture legality against the wrong side. **A hand-computed
      self-test on one position caught it**, and that is why the final figure is believable.
19e. **The clock-gate repair for traps 18 and 19 is MEASURED, not pending — and its effect is a single
    number.** `parse_limits` now records `wtime`/`btime`/`winc`/`binc` under their own names and resolves
    the budget once the command is parsed: **the mover's clock if given, the opponent's otherwise**, the
    increment following the same rule. **Callers that send their own clock take the first branch
    unchanged**, so nothing that already worked moves.
    - **The conversion, on a position with NO book entry where only the time manager can produce an
      answer** (White to move, `btime 10000` only): **lock: 25.00 s, no answer → patched: 0.33 s,
      answered `a4c6`**, against a both-clocks control of **0.35 s / 0.36 s**. So an unbounded search
      becomes an answer matching the control **to within 20 ms**.
    - **The seat's FIRST attempt at that number was wrong and the tell was the number itself**: it
      measured "answered on its own" on *book* positions and got **0.0 s**, which is the book
      short-circuit returning before the time manager is ever consulted. **It proved the book gate fixed
      and said nothing about the time limit.** A suspiciously fast success is a claim about which code
      path ran.
    - **This patch is the one that could in principle move a timed budget**, because `limits.time_ms`
      feeds the time manager. **Node-neutrality is NOT automatic here, unlike the book predicate.**
      Checked: **all 11 documented pins verified on the lock first, then on the patched build, then the
      two files diffed — identical.** Six clock forms agree; **not checked on a long game, and the
      `movestogo`-plus-fallback interaction is unmeasured.** Stated as a limit.
    - **Composed with the drawn-root predicates, all three repairs hold at once**: on a fresh worktree at
      `6b98f217`, **all 11 pins reproduce, the pre-emption fix holds, this clock fix holds, and the
      engine books from the opponent's clock alone — which needs both fixes live simultaneously.** The
      same probes still fail on the lock, so the improvement is attributable rather than coincident.
      **The seat's own report calls its three book items "trap 1", "trap 2" and "trap 3"; in THIS
      document those same items are 19, 19a and 19b.** The numbers collide because each document numbered
      its own findings, and "trap 1" means a fabricated `bestmove` here and the book clock gate there.
      **Cite the file, not the number.**
    - **Trap 1's own table (25 s window)**: White with only `btime` and Black with only `wtime` both
      **time out → then book at 0.0 s**; White with only `wtime` books `c2c4` and Black with only
      `btime` books `c7c5`, **unchanged**; both clocks, twice, **unchanged**. A harness control that
      requires a well-formed clock to answer **runs first**, so the run is void if the harness itself
      cannot produce one.
20a1. **A parse of profiler output has a built-in self-check: the accounted shares must sum to about 100%.**
   One report gave **0.96%, 2.06% and 20.85%** from three parses of the same data, because **perf's demangled
   symbol names wrap onto following lines**. **There is no "roughly right" parse** — either
   `accounted_pct ≈ 100` or the parse is wrong. **That is why one parser must be the only source rather
   than one option among several.**
20a2. **Correct the figure where OTHER SEATS READ IT, not only where it was announced.** A hand-typed average
   was fixed in a summary, then found again **in two rows of the findings index that other seats actually
   consult**. **The index is the propagated copy**; the announcement is not.
   - **And leave the historical job reports alone.** A report's own record of when it made an approximation is
     worth more than a retrofit: **correct the index, and say where the number came from.** Rewriting a past
     report to look as though it always said the right thing destroys the evidence that the correction was
     needed.
20a00. **A RULE IS CHECKABLE THROUGH ITS EVIDENCE, NOT THROUGH ITS GRAMMAR.** Two rules phrased as what a
   reader infers — *"two counts side by side with no label read as a stale number"*, *"a pending repair must
   be labelled pending"* — were **applied within one round and found three further unlabelled sites**, where
   author-facing rules had needed several rounds. **The apparent reason was the phrasing; the real reason is
   the body.**
   - **Tested against a 67-rule section: a keyword pass over HEADLINES classified 12 as obligation-form and 4
     as inference-form, which looked like a condemnation. Counting BODIES instead: 66 of 67 cite a concrete
     case or figure.** *"Never use a zero increment"* is an imperative and **fully checkable**, because its
     body names the 111 ms floor and the collapse to ~10 ms. **The form lives in the evidence attached to the
     rule, not in the mood of its first verb.**
   - **So the rule is: attach a concrete case or figure to every rule, and state the failure as what a reader
     would conclude.** The inference phrasing helps because it makes the reader's reading testable; **the
     evidence is what makes it checkable.** **A headline-only test measures the wrong layer** — which is this
     document's most repeated mistake, caught here in the act of applying it to its own rules section.
20a0. **TWO COUNTS SIDE BY SIDE WITH NO EXPLANATION is exactly the shape a reader assumes is a stale figure.**
   A summary cited **four honesty pins** in its opening section and **11 documented pins** in its repair
   section — **different sets** (bench 11/13/16 + perft 5 against 5 depths × 2 net settings + perft 5), both
   pinned, neither moving. **Say they are different sets**, or a reader who cannot reconcile two counts trusts
   neither — and the correct reading looks identical to the drift this report spends its rules on.
   - **And a PENDING fix must be labelled pending.** A repair that may land after the document closes is **not
     "fixed"**; writing it as fixed is **the same error as a figure with no committed source.**
20a. **A number that AGREES WITH YOUR PRIOR is the most persuasive kind of WRONG.** A summary file recorded
   the net at **0.00% of runtime** — from the first profile, whose `perf.data` was **empty**. It agrees with
   "the net is cheap", it looks like a clean measurement, and **it sat live in the folder of the seat that had
   documented this very trap.** **Rename or delete such an artefact; never leave it beside the correct one.**
   - **And the correct parse is not obvious**: perf's **demangled symbol names wrap onto following lines**, so
     naive parses of the same data gave **0.96% and 2.06%** before a single parser became the only source.
20b. **Generate a summary block from its sources, not from memory of them.** Doing this by script caught two
   errors on its first run: a hand-typed **"~37%"** that was **40.27% on one workload and 34.17% on the
   other** — an average of two numbers that should have been stated separately, **where the arm that
   governs is the smaller one** — and the stale zero above. **The script paid for itself immediately.**
20. A profiler report generated from **empty data** looks like a real profile. A zero-byte
    `perf.data` (recording blocked by `perf_event_paranoid=2`) produced a report of only kernel
    symbols. Check the data, not the reporting options: `ls -la perf.data`, and grep the report for
    a known user symbol — if `nnue::` is absent from a profile of an engine with a net loaded, the
    recording is broken.
21. **A reader that waits for `info depth` lines deadlocks on every fast path.** The opening book
    answers instantly with zero info lines, and `go nodes 0`/`1` emits none either. One reader held an
    engine process for 20 minutes on the book path. **Exercise every reader against a no-info path**
    (book, `go nodes 0`) **and put a timeout on every read** — a hang is a harness fact to report, not
    a mystery. (The drawn-root bail is **not** a no-info path: it emits a line per depth.)
21a. **`bench` never consults the book, and a seat's claim that it does would have thrown doubt on the
    audit's own gate.** The aspiration seat wrote that "`bench N` sent on stdin, `OwnBook false` (it
    defaults true, and a bench with the book on gives 1,919,423 at depth 11 — a wrong number that looks
    plausible)", and carried that as a build rule. **The book is loaded and gated in the `go` handler, and
    `bench` is a separate branch that builds its own `Searcher`, its own `Board` per FEN and its own
    `SearchLimits`** — there is no book call anywhere on that path (`uci.cpp:590-620` against the book gate
    at `uci.cpp:525-540`).
    - **Measured, not just read**: on the base build `bench 11` gives **312,866 with `OwnBook true`**, with
      the option never sent, and **312,866 with `OwnBook false`**, three ways to the same figure. The
      `1,919,423` is real but it belongs to some other command in that seat's harness, not to `bench 11`.
    - **Why this matters more than a wrong number in one seat's notes**: "the gate is conditional on a
      setting nobody records" would mean **every pin in this report is conditional on an option**, and the
      four honesty pins are the only thing standing between 874 findings and unattributable builds. **The
      pins are unconditional.** The one setting that is recorded as invisible to them is `Threads`
      (`bench` builds a one-thread searcher, §3), and that is a different and correctly documented case.
    - **The seat also warned that a bench number "looks plausible" when it is wrong, and that warning is
      sound in general** — it is only its application to `bench` that fails. Keep the habit, drop the row.
22. **`$?` after a pipe is the LAST command's status, not the tool's.** `cmd | tail` reports `tail`'s
    exit code. Three instances in one seat in one block. **Use `cmd > out; rc=$?`, or `set -o pipefail`
    — never a bare `$?` after a pipe.** The same shape as a check that cannot fire: the status you read
    belongs to something else.
23. **A mate checker that assumes the side to move is the attacker is backwards on every negative mate
    score.** It reports both true claims false and looks like a finding. **Resolve the attacker from the
    sign of the score and print which attacker it chose**, so the assumption is auditable in the output.
    Three of one seat's tools carried this error in different places; **the exhaustive check caught all
    three, reading the code caught none.** Same family as trap 15: a name or a shape is not the thing.
24. **`go infinite` is bounded by `stop` or depth 64, whichever comes first — and on a real position it
    is `stop` that matters.** The `max_depth ≤ 64` clamp binds only where depth 64 is reachable: on a
    drawn threefold it returns at 64 in 0.0 s, on a bare K+R v K twin it exhausts 64 in ~19 s, and on
    **startpos it ran a 75-second cap and reached only depth 30** (93,981,191 nodes), needing `stop`
    to return at all. **Do not conclude from the sparse endgame case that `go infinite` ends by
    itself.** A harness must send `stop` and assert the reply — which is reliable: **`stop` returns a
    legal move in 0–1 ms** (1 s and 3 s into an infinite search on startpos, at depths 20 and 23),
    and `go movetime` stops within 0.8 ms of its request.
    - **The original claim was a one-fixture generalisation in its most familiar form**: a sparse
      endgame was described as "a normal position", and the resulting advice would have told harness
      authors it is safe to run `go infinite` with no stop path. Corrected by running the quiet
      position that had been asked for.
25. **Text formatted for a terminal is not data.** A `|` in a terminal is a character, not a column
    separator, and `tail -6` is a filter, not a truncation notice. One seat's own pipeline turned 64
    `info` lines into what looked like one and nearly published "one line" as a mechanism. **Generate
    table content from a list of fields, and count lines in process rather than through a pipeline.**
    This is the same root cause as trap 22: the shell did what it was told and the instruction was the
    wrong shape.
26. **A figure from a run that is still growing goes stale silently, and both versions look like a
    measurement.** The PC20 population run was cited as "2,643 pairs and climbing", then the seat's own
    artifact showed **2,794**, then its status showed **4,718 of 11,192**. **None of those three is wrong
    and a reader cannot tell which is final**, because a checkpoint and a completion have the same shape
    on the page — a number with a decimal point. The medians did not move as n grew (0.9618 at 2,643,
    0.962 at 2,794), so **the denominator was the stale part, not the result**, and the cost of the
    omission is that the one figure a replicator needs is the one that drifted. **Write the word
    "checkpoint" and the denominator in the same clause as the number, or the number will be read as
    final.** This is trap 20a0's family — two counts side by side with no label — with the extra twist
    that here the two counts are the SAME figure at two times. **The final figure for that run is
    n = 10,774, wall geometric mean 1.0513, 95% CI [1.0422, 1.0604] excluding 1.0** — so the finished
    result is stronger than every intermediate version of it.
27. **A state leak across phases of your own tool shows up ONLY on the failure path, so the failure path
    is the one that never gets tested.** A verification tool ran a timed phase and then reused **the same
    board object** for the next phase; when the timed phase hit its timeout, the recursion unwound
    **without popping its moves**, leaving the board several plies deep, and the next `push()` asserted.
    **It had been correct on every run that completed** — the leak needs the timeout to happen, so it
    appears on exactly the hardest inputs, where the answer matters most and there is no second run to
    catch it. **And it disguises itself**: the result would have been read as "the verifier crashed on
    board 106", not "the verifier's state was wrong".
    - **The fix is structural rather than a careful review**: give each timed phase **its own throwaway
      copy** of the state, so an abnormal exit cannot touch what the next phase sees. **Verify that by
      regression-testing the case that still succeeds, not only the case that timed out** — the board that
      timed out proves the crash is gone, and the board that completes proves the fix did not change the
      answer.
    - **And the same seat logged a second instance of the family in the same night**: its consistency
      checker **passed 4 of 5 planted table-cell faults** because it compared only prose, and its MultiPV-4
      answer check compared against a **MultiPV-2** reference, so **6 of 6 "differences" were two different
      searches.** **Both were in the checker, and both would have produced a green run over a wrong
      report** — which is why "a checker is tested by a known-answer case, never by reading it" is in §6
      and keeps being earned.
28. **A check that flags EVERYTHING is as useless as one that never fires, and it looks more thorough.**
    While auditing this report I ran a scan for "N of M" appearing near a percentage and it flagged **54
    pairs**. Narrowed to pairs where the fraction and the percentage are **adjacent and explicitly
    paired**, it left **6, with zero mismatches** — **the 54 were a fraction in one clause compared
    against an unrelated percentage in the same sentence**, e.g. "162 of 180 positions" beside "6.4% more
    time per node". Neither number was wrong; **the comparator had no notion of which numbers were
    supposed to relate.**
    - **This is the same defect as trap 14 ("validating a summary statistic does not validate a table")
      and trap 20a0, and it appeared in the very act of auditing for it.** The tell is a failure count
      large relative to the corpus: when a check flags 54 of a few hundred candidates, the check is the
      thing under suspicion, not the corpus.
    - **So "the arithmetic check passes" is not one claim but two**: that the comparisons it makes are
      meaningful, and that they hold. **Both have to be established, and only the second can be
      mechanised.** The citation check in this report is worth more than its count of 27 because the line
      is printed and read.
29. **A build identifier that appears not to resolve may simply be a HASH OF A BINARY, not a commit — and
    treating one as the other produced the most embarrassing error in this report.** "PC r15" is quoted in
    a dozen columns of §2, and for most of this run the report said its identifier `068f0927` **did not
    exist, because `git rev-list --all` has no object starting with that prefix.** That command was
    answered honestly and the conclusion drawn from it was wrong: **`068f0927` is the sha256 of the built
    EXECUTABLE**, and `d6bd72c5` is the **sha256 of the patch text** — neither is a commit, so neither
    could ever have been found in the commit graph.
    - **The artefact was in the repository the whole time**, in
      `forge-combo29/soak_all/FABLE_TO_swarm_5.md` on branch `handoff/fable-opus-combo29-all-20261114`: the
      patch is embedded as a fenced diff, with the instruction that its sha256 starts `d6bd72c5`. **I
      extracted that block, hashed it, and got `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`
      exactly; applied it `-p1` to a clean `6b98f217` with no fuzz and no rejects; built it; and the
      resulting binary is byte-identical to `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`.**
      **So the PC build is fully reproducible and every "PC r15" column in this report is checkable**, which
      is the opposite of what the previous version of this trap said.
    - **The general rule survives in corrected form: "does this id resolve" is a question you must ask of
      the RIGHT KIND of object.** Three kinds were in play here — a commit, a file digest, and a binary
      digest — and the enumerating command is different for each (`git rev-list --all`,
      `git cat-file --batch-all-objects`, `sha256sum` on a rebuild). **Asking the commit question of a
      binary digest returns a confident "no" that means nothing.** The correct procedure is to search the
      TREE for the identifier's context before concluding it is absent: `git grep` for `068f0927` finds
      `pc20 sha256 068f0927…` in a seat's evidence file in one second.
    - **A separate, independent provenance audit then did this properly and found both halves**: it
      rebuilt BOTH binaries byte-exact from committed text (r15 `068f0927…` and base `e06310ec…`, pins
      matching), and it also produced the census this trap was missing — **14 real build identifiers across
      874 findings, 9 resolved and 5 genuinely unresolved.** **`PC r15` covers 393 findings and is
      RESOLVED**; the 45 findings that are not re-derivable sit on **descriptors, not hashes** — see the
      entry below, which is the part of this audit an owner should act on.
    - **The general rule, corrected a second time: a provenance audit must CENSUS the identifiers, not test
      the one you were handed.** The brief named a single suspect build and the suspicion was misplaced;
      **the real gap was 45 findings across 8 seats riding on "the TSan build", an identifier with no flags,
      no compiler line and no hash.** A test aimed at the named suspect would have returned a confident
      answer and missed all of them.
30. **The builds nobody hashed are the ones whose numbers cannot be attributed to the engine, and they are
    prose descriptors rather than identifiers.** A full census of every build reference in this corpus
    found **14 real build identifiers**: nine resolve, and **five do not — and every one of the five is a
    description rather than a hash.**
    - **"TSan build": 27 findings across 8 seats, and no flag set, no compiler line, no hash anywhere.**
      **Worst offender in the audit**, and not because of the count: its most load-bearing row is a
      **~1,000× wall-clock outlier** (348,278 ms and 376,680 ms against 0.8–2.0 s in fresh processes) —
      **a timing statistic measured inside a ThreadSanitizer process, on a build whose flags nobody
      recorded.** The finding may well be true; **a 1,000× factor quoted from an unrecorded instrumented
      build is a property of "the engine under TSan at whatever flags were used", and the flags are
      missing.** A reader cannot separate the defect from the instrumentation.
    - **"ASan+UBSan build": 12 findings across 7 seats, same problem** — but with a distinction that
      matters and is easy to lose: **a sanitizer FINDING (a crash, a leak, a data race, an out-of-bounds)
      is safe to keep**, because it is behaviour the source can be re-instrumented to reproduce. **It is
      the sanitizer TIMING and RATE numbers that die with the build.** So the rule is not "discard
      sanitizer results", it is **"a time measured under a sanitizer is a property of the sanitizer
      run."**
    - **"The owner's PC" net: 3 findings, unresolved BY DESIGN and correctly so** — the handoff states the
      PC plays with its own trained net and cloud seats keep the built-in evaluation, so those rows are
      honestly owner-machine-only rather than a gap in the record.
    - **The re-measurement list is short and specific, which is what makes it usable**: every TSan
      wall-clock row (starting with the 348 s outlier, `24-F3`), every row whose headline number appears
      only against a sanitizer descriptor, and the three owner-net rows. **One row (`07-C38`) rests on
      TSan, ASan+UBSan AND `-D_GLIBCXX_DEBUG` simultaneously** — the least checkable support in the
      corpus, listed as its own item.
    - **And the census answered a question nobody asked**: **rows citing `integrate/combo29-all` or the
      handoff branch as though they were the base** were searched for, and only one retraction existed
      (the FEN field-count row). **A genuine negative about a class this report had already been burned
      by**, and worth stating as one.
    - **The seat's own census had a self-reference bug, and how it found it is the transferable part.** It
      was counting **its own audit branch** among the refs, so the published commit/ref totals **grew with
      every push the audit made** — the measurement moved because the instrument was inside the thing it
      measured. Fixed with an explicit ref list, the self-ref excluded **by name and printed beside the
      result** (8,898 commits / 615 refs), because `rev-list --all --exclude=` silently does nothing here.
    - **And a second instance, which is the cleanest example of motivated reasoning in this run**: it had
      written that the hash→path map **undercounted**. That was **wrong** — the map was counting **its own
      evidence files**, which quote the hashes they discuss. **The count climbed on every re-run (30 → 32 →
      38) until it excluded `/swarm/provenance/`, at which point it returned 22 — the original one-off had
      been right all along.** **A number that moves in the direction of your hypothesis, every time you
      re-measure it, is evidence about the measurement.** The seat recorded it as having fitted a story to
      two numbers that moved toward what it expected, and explicitly noted that no published finding
      depended on it — **which is the distinction that matters: the sentence was wrong and the results were
      not.**
    - **And one CI fix it REFUSED, correctly**: a security linter flagged a regex for backtracking, and
      rewriting it **changed the audit's answer (874 → 871 findings, 45 → 42 unresolved)**. It reverted the
      change and accepted the warning. **A lint warning is not worth changing the product for**, and a
      cleanup that silently moves your denominators is the most dangerous kind of tidy.

---

## 8. Clock behaviour

- **Floor 111 ms**, converged from every start ≥ 111 at a 60 ms increment; MoveOverhead 10. **The clock
  cannot be lost by searching.**
- **Two different 60%-looking relationships, and conflating them is the trap.** The **floor** is
  `0.6 × (clock − overhead)` and that is measured: **114.5 ms at a ≤200 ms clock against 114.0 predicted,
  over 63 such moves.** But the **planner's soft→hard multiple is `5 × soft`, NOT 60% of soft**:
  `TmHardPercent = 60` and `TmHardSoftMultiple = 5` are both in play and **the multiple binds at every clock
  from 2000 ms down to 60 ms** — at 2000 ms soft is 90 and hard is 450, where `0.6 × available` would be
  1194. **The 60% term only binds where `available` is small relative to soft, which sudden death never
  reaches.** **A reader who takes "hard = 60% of soft" as a rule predicts the hard limit 55% too high at a
  2000 ms clock** — and this report carried that phrasing. **Both numbers are 0.6 and they describe
  different things.**
- **The load-bearing number is a TWO-REGIME result: 5,675 moves across two complete 20-game matches, 0
  forfeits in either, and the HARD PLAN WAS NEVER EXCEEDED — worst overshoot +2.1 ms, with utilisation
  peaking at 0.596 so the bound is a ceiling nobody pushes against.** Extended to **146 games and 19,084
  plies at three time controls: exactly ONE move over its hard plan** (681 ms on 680 ms, the 1024-node poll
  edge), **0 forfeits, 0 hangs, 0 illegal.** **The two matches hold in opposite regimes** (one where the
  clock falls toward the floor, one where it rises throughout), which is what makes it stronger than either
  alone.
- **NOT "wall time equals the plan", and that distinction was measured.** Moves within ±2 ms of plan:
  **84.5% at 200+0 but 2.2% at 1000+100 and 1.1% at 3000+200.** At 200+0 the **median soft plan is 1 ms**,
  so ±2 ms is *wider than the plan* — an agreement measured with a tolerance larger than its own subject.
  **A plan is a bound, not a prediction**, and the bound is what holds.
- **0 forfeits** at 12 clocks from 1 to 600 ms, real accumulating games, 20 and 60 plies; 0 flags
  in 600 moves; 0 flags on worst boards at 200 ms.
- **Utilisation 2.5–13.7% per position, median ~4%** at a 6-second soft limit. Tail ≤ 8 pieces can
  rise to the hard plan.
- **A clock move costs its last completed iteration; wall time is a step function. And NEITHER `info …
  time` NOR wall time is "the clock"** — a seat measured both and found them different: **`info … time` is
  the last completed iteration's END, not the search duration** (at `movetime 2000` it reads
  453–1,988 ms against a 1,990 ms call), while **wall time carries harness round trip**. So a
  forfeit or utilisation claim has to name its basis.
  - **Two of that seat's own rows were conflated and are WITHDRAWN**: a "max 295.1 ms" that was a **wall
    tail over a 254 ms search**, and a "1 of 9 over clock" at a 1 ms clock that was a **fallback
    comparison — 8 of 9 runs there emit no timed `info` line at all, and under engine time it is 0 of 9.**
  - **The forfeit result is shown under BOTH bases and agrees**: 0 flags, utilisation maxima **0.596 by
    engine time and 0.597 by wall** — so the conclusion does not depend on which one you pick, which is
    the right way to settle it.
- Determinism: fixed node and depth searches are bit-identical at `Threads 1` on both builds
  (40/40 positions). Wall-clock-limited searches are not.
- **Fullmove number and halfmove counter are part of a position's identity**: 5 different mate
  values across counters 0–99, and a 2× node swing for an identical score.
- **The one-sided clock is the only form that does not terminate.** `go wtime 300000` with Black to move
  **emitted no `bestmove` in a 330 s allowance** — 30 s of grace past the whole budget — after **depth 39 /
  416,554,567 nodes**. It now has a measured repair: a no-book position with only the opponent's clock went
  from **no answer in 25 s to 0.33 s**, against a both-clocks control of 0.35 s. Cause and patch are in
  traps **18/19/19e**; the same repair is what lets the book fire from the opponent's clock alone.
- **A clock measurement is only as good as the event it is timed from**, and this one was wrong first: the
  driver timed a non-answering search by its last output line, so a 330 s non-answer was published as
  288.7 s — **41 s short, 12.5% below the true value.** **The two clocks agree on every search that
  answers**, which is why six of the seven cases were unaffected and only the one that never answers was
  understated. Details and the planted-fake self-test are in trap 18.

---

## 9. Base-versus-PC divergence

Confined to a single class, confirmed at **100% outside its condition**: 11 of 40 lone-king roots
differ, **0 of 60** non-lone-king roots differ.

**Confirmed at population scale and at two budgets:** `go depth 12`, non-lone-king positions —
**0 differing of 200** (`set O`) and **0 of 341** (`set G`), in **both node counts AND bestmoves**, with
the lone-king control **12 of 12 differing**. Reproduces at `go nodes 200000`. **So on a non-lone-king
position the two builds are interchangeable, and that is now a population result rather than a sample.**

Cause isolated by single-switch variants (pins verified identical at 312,866):
**`BARE_KING_LMR_CAP` off restores the base move on 11 of 11.** `BARE_KING_ONE_THREAD` on restores
6 of 11. Ordering was hypothesised and killed.

Mechanism: cap-off visits fewer nodes on 9 of 11 boards (by 3,356–14,040) and more on 2 (+621,
+10,981); identical on none. The gate fires on **100% of nodes** in every tree on every board, so
the two counter-cases are a second mechanism — most plausibly clamped reductions
propagating through the pruning cascade. **That hypothesis was then tested with the per-depth reduction
counter, and it survives only in a narrowed form**: the counter does **not** separate the counter-cases
on any aggregate (§10 has the table), the aspiration-cascade variant is **refuted 0 of 11**, and the
clamp's immediate effect is the **same on the counter-cases as on the predicted boards**. What differs is
what happens **after the first divergence**, so the lead is now **a location inside an iteration's tree**
rather than "clamped reductions" in general.

Evaluation itself is **bit-identical** across builds on 120 positions.
---

## 9b. Two evaluation defects, and one of them reaches search

**A bare-minor ending is scored as a LOSS for the side with the extra piece, and for two knights that
wrong score is carried into the search.**

- **Adding a bishop to a bare king LOSES 149 cp.** K vs K scores **+2**; KB vs K scores **−147**;
  KN vs K scores **−144** — both below an empty board. **1 inversion in 16 material steps.**
- **The cause is not ambiguous**: the handcrafted term is right (hce **+16**); the **NNUE residual is
  −163 and dominates**, because `scale_factor()` (`src/eval.cpp:389-412`) returns **0/12 for bare
  minors** and nearly erases the handcrafted term. Systematic across six bishop squares, always
  −127 to −159.
- **Scope is precise, and it is the endgame only**: with pawns present the same ladder is monotonic
  (18 / 434 / 461 / 859 / 1614), and in a real middlegame a bishop is worth a normal **+477**.
- **`KNN vs K` IS NOT A DRAW, and an earlier version of this report was wrong to say so.** Two knights can
  mate: **`8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1` is a legal checkmate** (valid, checkmate, and *not*
  insufficient material, confirmed independently). FIDE 5.2.2 draws only when **neither side can mate by any
  legal series**, and here a legal mate exists — so the `knights == 0` requirement in
  **`board.cpp:1257`** (inside `is_insufficient_material`, `board.cpp:1250-1258`) is
  **correct**, and the engine returning not-draw for KNN vs K agrees with FIDE. The same holds for
  **KNN vs KN, KB vs KN and KNN vs KB**; **all nine material sets agree with FIDE**, each decided by
  searching for a mate witness rather than by argument.
  - **What survives is the static score, not the adjudication**: the bare-minor ladder inversion
    (`KB vs K` = −147, `KN vs K` = −144, both below `K vs K` = +2) is real, and for **KNN vs K** that
    wrong static score is **not masked** by a draw verdict because there is no draw verdict to mask it.
    **So the defect is "a wrong static score in a position that is genuinely playable", not "a missed
    adjudication".**
- **The v3 incremental accumulator is confirmed correct at scale: 54,379 DISTINCT positions, 0
  mismatches**
  against a fresh full refresh, covering every unit of both perspectives (2×512), both king keys, both
  king squares, and the network output against a reference — at every ply of every sequence. Root FENs
  all validated independently, engine refused none.
  - **BUT THE MOVE-GENERATION CLEAN BILL EXCLUDES EN PASSANT, and that was checked rather than assumed:
    zero of the 353 `set_G` positions carry an ep square at all.** So the population never exercised ep
    even where the code preserved it. **"353 of 353" is a clean bill for move generation EXCLUDING ep**,
    and it is stated that way here rather than left to imply full coverage. The perft seat's four
    targeted 500-position families are what cover that edge, and the two results complement each other
    without either implying the other.
  - **The coverage point is the reason to believe it**: quiet games almost never cross a **king-bucket
    boundary**, which is the only branch where the incremental path abandons the update and rebuilds the
    bitboards by undoing later plies. Purpose-built walks produced **5,012 king-key transitions, 0
    mismatches** — **a branch a normal position set leaves untested.**
  - **Independent arm: the engine's own verification build** (which aborts the search on disagreement)
    ran 200 positions at depth 12, 37.5M nodes, 0 mismatches.
  - **The distinct count is a UNION, not a sum, and an earlier version of this report quoted the wrong
    one.** The three sequence fixtures are **nested** — each takes the first N rows of the same corpus
    with the same 40-ply prefix — so `deep` already contains `large` entirely (7,761 of 7,761) and
    `small` entirely (479 of 479). **54,379 = seq_deep 47,418 ∪ kingwalk 6,961**, and **kingwalk's
    overlap with every other fixture is 0**, which is why the coverage argument is unaffected: the
    5,012 king-key transitions are all in the union and disjoint from everything else. **Adding
    per-fixture counts is the error; the count is now machine-computed and enforced by a script so the
    literal cannot drift.**
  - **Corrupt and truncated nets are refused, each with a specific reason**: 12 damage cases, 11 refused,
    and the one accepted is a bit flip with a **recomputed checksum**, which must load — **a checksum
    detects accident, not intent.** Nothing loads and silently produces garbage.
- **The picker is NOT a speed target, and the reason is the strongest ordering result in the run.** Replacing
  `pick_best`'s full `std::sort` (5.03% of bench-13 time) with repeated find-max-and-swap changes the 200-row
  identity **massively**: total **27,944,084 → 26,531,587 (−5.05%)**, **200 of 200 rows differ**,
  median per-row change **32.9%**, max **224%**, 94 rows up and 106 down. **So it is a SEARCH CHANGE, not a
  speed patch — the sort's exact tie order IS part of the search's definition**, exactly what the
  colour-asymmetry result implied when it turned out to be move-generation order.
  - **So the 5.03% is not algorithmic overhead; it is the price of the ordering the engine depends on.** A
    legitimate patch would have to reproduce `std::sort`'s tie order exactly — sort on
    `(score, original index)` — **which is a harder, separate experiment, named as the next step rather
    than claimed.**
  - **The prediction rule was applied to its author**: a pre-registered **"moves the total by under 5%"** came
    out at **5.0547%** and is recorded as a **miss rather than rounded into a hit.**
- **Straight-lining a loop whose trip count is 2 or 3 buys NOTHING, and that is a measured null.** A patch
  specialising the v3 accumulator walk's 2- and 3-change cases was justified by instrumentation rather
  than guesswork — a scratch build counted **127,177 calls in one depth-12 search, and the change count
  was ALWAYS 2 or 3** (2: 71,659; 3: 53,386; everything else zero), over a variable-bound loop no compiler
  can unroll. **Identity perfect** (all 200 OG200 rows identical, sum 27,944,084, 8/8 benches, 3/3 evals).
  **Speed: no effect detected** — ABBA n=120, **ratio of medians 0.9694, CI [0.9418, 1.0297] contains
  1.0**, point estimate slightly the wrong way.
  - **The reason is that the walk is already vectorised at 32 lanes per iteration**, so loop overhead is
    not the cost. **A null result recorded as a null, with the subset search not attempted** — "I did not
    go looking for a subset where it wins" is the sentence that makes it usable.
- **Not every removable per-lane operation is worth removing, and the size distinction is measured.**
  A second v3 patch removed a 32-lane store-and-scalar-sum tail (`output_sum_avx512`) and is **bit-identical
  but not faster**: ratio **0.9995, CI [0.9984, 1.0005] — includes 1.0** — **+0.05%, under a
  pre-registered 0.5% bar, so REJECTED with numbers.**
  - **The "7.34% profile share" attached to that function in an earlier version of this entry is WRONG, and
    the way it is wrong is worth one line**: 7.34% is **`MovePicker::generate_evasions()`**, and
    **`output_sum_avx512` does not appear in the profile at all** — it is a `static` function in
    `nnue_v3.cpp` and gprof records no row for it, so **no share can be quoted for it from that artefact.**
    The misattribution is inherited from the step-4 report, which carries the same 7.34 against
    `output_sum_avx512`. **The decision is unaffected** — the patch was rejected on a measured 0.9995 ratio,
    not on its profile share — but the number that motivated attempting it is unsourced, and **an argument
    for "this is worth trying" resting on a share nobody measured is how a low-value patch gets written.**
  - **The reasoning behind the estimate was corrected twice, and the second correction is the instructive
    one.** The correct physical fact is that **independent lanes are bounded by ALU port throughput
    (~4 adds/cycle), not by a per-add cost** — a microbenchmark confirms the scalar tail really does cost
    ~7.4 ms, matching the 6.8–8.5 ms port prediction.
  - **But that number is the COST OF THE EXISTING TAIL, not the SAVING from replacing it** —
    `saving = old − new`, never `old − 0`, and the replacement fold is not free: it still costs
    ~5.7 of the ~7.4 ms it removes. **So there was never a discrepancy to explain.** Measured directly on
    the exact tail (2×512-bit → 32-lane sum, 2,566,881 iterations, distinct inputs so nothing hoists):
    scalar **7.07–9.20 ms**, fold **5.38–7.33 ms**, saving **1.50–1.87 ms = 0.070–0.088%**, against a
    bench measurement of **+0.05%, CI −0.05% to +0.16%** — **they agree.** An earlier framing of
    "wrong by an order of magnitude" is therefore **withdrawn**; the estimate was off by roughly **2×**,
    and the residual is inside the interval.
  - **The generalisable rule is sharper than a cost-model error, because the cost model was fine: a
    correct cost model applied to the WRONG QUANTITY produces a number that looks rigorous and is off by
    the size of the term you forgot. The tell is needing a SECOND MECHANISM to reconcile it** — here an
    invented "the tail overlaps surrounding work" story, which was that second mechanism.
  - **And the replacement was structurally capped: the fold is LATENCY-bound where the scalar tail is
    port-bound.** Measured by chaining: N folds chained **17.55 ms** vs N/2 independent pairs **14.37 ms**,
    ratio **0.819**. Near 1.0 is latency-bound, near 2.0 port-bound; at 0.82 the fold's four dependent
    shuffle-add steps pay latency, and **the floor sits only ~20% under the original.** **When replacing a
    reduction, check whether you are trading a throughput-bound form for a latency-bound one — that caps
    the gain regardless of how few instructions you write.**
  - **So "removable per-lane work" is not one category**: a per-lane **BRANCH** with misprediction and
    dispatch overhead (the shipped patch, count 1..4) is worth orders of magnitude more than a per-lane
    **ADD** on independent lanes, which is a few cycles of a 4-wide port.
  - **And the first attempt at that rejected patch was NOT bit-identical** — bench 965,454 → 201,580 —
    because a `_mm512_shuffle_i32x4` fold selected the wrong 128-bit quarters. **It compiled clean, ran the
    full bench and returned a plausible number; only the identity gate caught it.** A timing run alone
    would have reported a speedup for a different engine.
- **Move generation is confirmed clean over the population the area-1 findings use: 353 positions × 2
  builds = 706 comparisons, 0 parser mismatches, 0 movegen disagreements with an independent generator
  at `perft 4`, 0 FENs refused.** Run on PC r15 and identically on base, 256 s per build.
  - **A COUNT comparison cannot see a substitution, so move SETS were compared too — 290,623 nodes, 0
    differences.** `go perft 1` at every node, engine moves against the reference's: **2,000 positions at
    depth 2 (28,940 nodes), 1,200 at depth 3 (196,916), 400 targeted (64,767) — the sum of THREE runs, not
    one traversal, so quote it as a volume of comparison and not as a single walk.** **A bug that
    swaps one legal move for another at equal count is invisible to a count-only perft**, and this is what
    closes it.
    - **The check is proven able to fire on exactly that bug**: the self-test **swaps one engine move for
      another at an identical count** and requires the set comparison to catch it — it reports
      `engine-only ['a1a8'], python-only ['a2a3']`.
    - **Coverage inside the walk measured rather than assumed**: 100 nodes with a legal ep capture, 248 with
      an ep right suppressed as illegal, 17,787 with a promotion, 57 with castling.
    - **And the ep trap bit inside the fix for this different gap**: child FENs had to go through
      `fen_with_ep()`, because `board.fen()` would have **silently compared a weaker position at every node
      whose ep capture is illegal.**
    - **Honest limit, narrower than the one it replaces**: a per-node set comparison at shallow depth, **not**
      a proof over every node of the deep runs — a substitution deeper in those trees would still survive.
  - **Depth 4, not 3, deliberately**: a pinned-piece or en-passant interaction commonly needs the fourth
    ply, so depth 3 would have been a weaker claim for the same setup.
  - **The instrument's self-test fired in both runs** (two different boards differ), so the comparison is
    **shown** capable of failing rather than assumed to be. **That is the difference between "no
    disagreements found" and "the comparison works and found none."**
  - **What it does not say: nothing about evaluation, pruning, or the move chosen.** Perft agreement is
    not silent agreement about play, and the limit is written into the tool.
- **Evaluation symmetry is clean on BOTH evaluation paths — 0 asymmetric pairs, twice, on different
  code and different weights.**
  - The built-in net: **0 asymmetric pairs of 420** (20 hand-picked + 400 seeded), `hce` and `nnue`
    separately, on the static evaluator so no movegen is involved.
  - **A loaded FORGENN3 net through the v3 path**, which the owner actually runs and which had never been
    tested: **mirrored all 353 `set_G` positions (colour flip + board flip, side preserved), 353 pairs
    evaluated, 0 skipped, 0 asymmetric pairs** for `hce`, `nnue` and total.
    - **AND THE v3 PATH IS NOT IN THE AUDITED BINARY AT ALL, which changes what every v3 row in this report
      means.** `nnue.hpp:10-12` defaults `FORGE_NNUE_V3` to **0**, the brief's CMake recipe never defines
      it, and **a default build answers `unknown option NNUEArch`** — **I confirmed that on my own build:
      `UseNNUE` is advertised and `NNUEArch` is not.** So **all v3 work in this tree is unreachable from
      the locked binary**, every v3 row here was measured on a **second binary built with
      `-DFORGE_NNUE_V3=1`**, and `tests_astra_v3/` exercises a build the audit does not ship.
      **This is a scope fact, not a defect — but a reader who takes "the owner actually runs the v3 path"
      from this section would be wrong about the binary the pins describe**, and the v3 performance
      patches (the shipped pair-count dispatch, the rejected fold) ship into a path that the default
      build compiles out.
  - **This is a property of the ENGINE, not of one net, and that is stronger than either result alone.**
    Symmetry is a property of the **weight layout** as much as of the code — `feature_index`
    reindexes by king bucket and flips squares by perspective — so a net written for one convention
    could be asymmetric where the two kings sit in different buckets. **And startpos cannot show it**,
    because both sides are identical there, which is why the test has to run on real positions.
  - **The comparison is proven able to fail**: two different positions evaluate 968 vs 1320, so 0 of 353
    is a measurement rather than a broken equality test.
- **So the evaluation is NOT the source of the colour-mirror search asymmetry** — that is
  move-generation order. **Limit: `eval` only.** A symmetric static evaluation can still be *used*
  asymmetrically by the search, which neither test exercises.
- **Sign convention is correct**: 4 of 4, side-to-move relative, and an inverted-sign stub was detected
  4 of 4, so the test is not a magnitude check.
- **The stale-transposition-table trap that found this is worth keeping**: on the same KBN board, three
  searches in one process scored **cp 274 / 285 / 293**, while a cold process scored **cp 272 three times
  identically**. **A warm table changes fixed-depth scores, which would manufacture a fake depth trend.**
  Every measurement in this report that compares depths uses one fresh process per cell.

## 10. What is not established

Every claim above is calibrated where it is stated, but the open items are scattered across sections.
Collected here so a reader does not mistake a closed behaviour for a closed mechanism.

**Closed as behaviour, open as mechanism**
- **The drawn-root bail.** Its exact trigger, its threshold, its score and its move are all measured.
  **Why the bail publishes the generator's head is sourced** (`root_candidates.front()`), but **why the
  guard exists at all, and which of three candidate code paths produced it, is not ranked.** Do not read
  the behaviour as a diagnosis.
- **The base-versus-PC lone-king divergence.** `BARE_KING_LMR_CAP` off restores the base move on 11 of
  11, so the cause is isolated **at the switch**. But the cap fires on **100% of nodes in every tree**,
  so it cannot be what distinguishes the two counter-cases. **A second mechanism remains, and it is now
  LOCATED rather than merely admitted**: the per-depth reduction counter was built, and it shows the
  clamp's immediate effect is identical everywhere (cap-ON visits more nodes on 2 of 2 counter-cases and
  8 of 9 predicted boards at the first divergent depth), **refutes the aspiration-cascade account 0 of
  11**, and puts the difference **downstream of the first divergence, inside an iteration's tree.** See
  §10's item of the same name for the numbers and the caveat that the 2/2-versus-1/9 reversal is
  **p = 0.0545 and not a finding**.

**Measured as untestable within the run, or settled since**
- **Whether the base also forfeits a mate that needs SEARCH.** Very likely by the same mechanism, but
  repetition cycles live in quiet positions and short mates live in busy ones; thirteen candidates
  across two rounds were defeated. **Recorded as untested with a reason, not as a negative result.**
- **PC20's net wall-time gain — SETTLED, and it is a measured LOSS.**
  The population run finished at **n = 10,774 of 11,192**: wall **median 1.0370**, **geometric mean 1.0513,
  95% CI [1.0422, 1.0604] excluding 1.0**, node median **0.9618**, per-node median **1.0712**. A 1% stride
  sample had said ~3% **faster**, so **the sign flips**, and the identity `wall = node × per-node` closes
  on the population. **Treat "PC20 is faster" as refuted and "PC20 is about 4–5% slower, from a per-node
  tax that outweighs a real node saving" as established**, with the CI robust to the game-sequence
  autocorrelation that a skeptical reader should ask about. **The residual open item is not the sign but
  the switch decomposition** — see the next entry.
  - **A reproduction attempt on a shared machine failed, and that is recorded rather than hidden.** Sixteen
    ABBA blocks at 250 ms gave a PC/base geomean of **0.8637** — but the **A/A control, the same binary in
    both slots, gave 1.1710**, so that harness's floor was a 17% swing and the bias-corrected figure
    ("26% slower") is an artefact of the correction, not a measurement. **A small re-run against a 4–5%
    effect needs a floor well under 4.5%, and this one had 17%.** The n = 10,774 run with its CI excluding
    1.0 is the measurement of record; **"independently checked" means nothing without the floor it was
    checked against, so both numbers are here.**
- **Every individual PC20 switch as a node saving.** All four paired-effect CIs include 1.0. The
  aggregate is established and the components are not; TtPruneV2's *direction* is significant while its
  *magnitude* is not.

**Known scope limits that a reader might otherwise over-read**
- **The engine cannot reliably convert won endings, and the cause is the FIFTY-MOVE CLOCK, not the
  bare-minor inversion — this is the single most consequential finding in the report for anyone who plays
  the engine.** Measured with an **exact-table oracle as the control, which converts 20 of 20 in KQK and 20
  of 20 in KRK and 192 of 192 won KPK cells**, so the harness is proven able to convert:

  | family | engine, depth 12 | engine, `nodes 12000` | oracle |
  |---|---|---|---|
  | KQK | **18 / 20** | 19 / 20 | **20 / 20** |
  | KRK | **10 / 20** | **8 / 20** | **20 / 20** |
  | KBNK | **3 / 20** | **3 / 20** | not run (no 4-piece table) |
  | KPK (192 won cells) | 142 / 192 | **167 / 192** | **192 / 192** |

  - **Every attributable failure ends in a fifty-move claim with ZERO drawn-root bails**: 2 KQK + 10 KRK +
    25 KPK = **37 failures, `n_bails = 0` on all 37.** So **a repair aimed at the bail would fix none of
    them**, and that negative is the most useful part of the result — it contradicts the natural hypothesis.
  - **The mechanism is the already-documented leaf band, and I verified it independently on the seat's own
    board.** `8/8/8/8/8/2k5/8/KQ6 w - - H 1` at `go depth 12`:

    | halfmove clock | score | nodes |
    |---|---|---|
    | 0 and 60 | **cp 1220** | 93,585 |
    | 80 | cp 1129 | 711,846 |
    | 85 | cp 1085 | 18,784,716 |
    | **90** | **cp 0** | **101,428,235** |
    | 95 | cp 0 | 156,416 |

    **The band is at clock 90 and the score there is exactly `cp 0` — not "small", the same value a real
    draw returns**, which is why the engine cannot distinguish a won position from a drawn one at that
    clock. **And the node count to answer a question it answered in 93,585 nodes at clock 60 is 101
    million.** The engine does not fail to see the win; **it decides the position is drawn and then
    shuffles correctly for a drawn position.**
  - **The seat is careful about what it proves**: it **did not instrument the leaf**, so this is
    "consistent with the documented `H > 100 − p` rule", not a proof. **KBNK is a measurement without a
    mechanism** — 3 of 20, 17 ended in a fifty-move claim, and **the seat explicitly refuses to attribute it
    to the bare-minor inversion because it built no KBNK table**. That refusal is the right call.
  - **The bare-minor inversion's game-level cost is SMALLER than the static number suggests, and that is a
    second null**: as the defender the engine **held 20 of 20 in both KBK and KNK**, because
    `is_insufficient_material()` short-circuits the root and it plays the generator's first move. **The
    −147/−144 score never costs a draw.** What it does cost is a **bail storm**: **2,152 bails across 20 KBK
    games and 2,064 across 20 KNK games**, about 100 per game, and 100+ plies of shuffling a bare minor.
    **So the defect is "it cannot win a won ending" and "it makes a drawn one tedious", not "it loses drawn
    ones".**
  - **One KRK game shows the two mechanisms compounding, which is why they must be described separately**:
    the engine held the win for 100 plies, the clock reached 99, its score collapsed to `cp 0` in 320
    nodes, it played **`Kxh3`, giving up the rook**, and the remainder is K vs K with the bail firing every
    ply. **The clock defect created the material bail, not the reverse.**
  - **Horizon does not rescue it**, and the ladder belongs with the numbers: at depth 12 the exact KQK
    positions that fail need depths in the tens to convert, and the node counts at clock 90 (101 million on
    a three-piece board) show why that is not a practical answer. **The report's §2 band repair is the
    relevant fix, not more depth and not the bail patch.**
- **The mate-in-one forfeit breadth.** 6 of 6 fixtures, two mate types — and all six have Black's king on
  g8/h8 with pawns intact. Breadth beyond two structures was not tested.
- **The MultiPV instability split.** The rate held when the stratum nearly doubled, and the interval is
  **still 25 points wide**; ±5 points needs roughly 350 unstable boards, about 2,400 positions.
- **The right-length-wrong-mate class.** Two boards, opposite directions, so the class is established and
  no direction is. **One failing case came from a single-line search at the shallower depth**, so it is
  not a MultiPV artefact.
- **The 8-of-10 threefold frequency.** Interval 49% to 94%. It is "common", not "four in five".
- **PC20's depth advantage.** +0.062 ply/position at n=130, with the median difference exactly 0.0. It is
  "rarely shallower", not "deeper" — and a six-position sample overstated it 8×.
- **How much the bare-minor evaluation defect costs in games.** The static inversion is measured and the
  KNN-vs-K case reaches search, but **no game-level cost was measured**: no SPRT, no Elo claim.
  - **And a boundary seat established the sharper bound on it: the wrong static score does NOT reach a
    client, because every position that shows it is a drawn ROOT and the bail returns `cp 0` with 0 nodes.**
    On this build `eval` reports **−138** for K+N vs K, **−155** for K+B vs K and **+107** for the mirrored
    K vs K+B, while the search returns **`cp 0` at 0 nodes** — **I confirmed the shape myself**:
    `8/8/8/8/8/8/8/K1k1N3 w` gives `info string eval hce 8 nnue −84 total −76` and then
    `info depth 8 … score cp 0 nodes 0 … pv`, so the static number is computed and then discarded by the
    bail. **Add pawns and the defect vanishes** (a KP-vs-KP version with a knight evaluates **+300** and
    searches **cp 298**), because pawns change `scale_factor()`'s branch.
    **So the honest scope is "a wrong static score in a position whose root is drawn anyway"** — which is
    why it has no game-level cost to measure, and why the KNN-vs-K case is the only one where it survives:
    there is no draw verdict there to mask it.
- **The aspiration window's scope is narrower than its headline.** Four limits, all named by the seat
  rather than left for a reader to infer: single-threaded only; **no clock arm**, so every aspiration number
  is a fixed-depth or fixed-node one; **the delta sweep is four points (4/18/50/200), not a curve**, so
  "12–15% fewer nodes" is a statement about those four values and the shape between them is unmeasured;
  and **the corpus cannot place a narrowed window directly on a mate score**, because mates in it resolve
  by depth 3 and narrowing only starts at depth 4 — so the mate-window evidence is **indirect**, coming
  from `go mate N` and deep KQK ladders, and is labelled that way.
- **Whether in-tree repetition detection AFFECTS PLAY.** The mechanism is **present and live**: the branch
  **executes below the root** (8 hits at depth 6, 158 at depth 10 from an occurrence-№2 root) and it
  **changes the search tree** (with the repeating move forced, an ablated build visits **4,187 nodes against
  4,186** at depth 6). **But no score changed on any constructible fixture, because none is
  repeat-dependent.** So the honest form is **"mechanism present, no verdict-changing fixture found"**.
  - **And a 199-position scan was correctly DISCOUNTED as evidence.** Each root was placed on occurrence №2
    by a verified reversible cycle and searched at depth 8; result **0 score diffs and 0 node-count diffs**.
    **Identical node counts prove the repetition branch never executed** — an opening position has no
    forced repetition near the best line, so **the corpus could not exercise the code path.**
    **A null from a corpus that cannot reach the code is vacuous**, and it is **the second instance tonight of
    an absence needing the same proof as a defect** — the check that showed it was empty was the node
    counts, not the scores.
  - **Then the ORDER was inverted and the null became real.** Run the instrumented build **first**, keep only
    roots where the branch actually fired, and compare scores only on those — over **600 generated endgames**
    (rook endings, queen endings, bishop pairs with pawns, each root on occurrence №2):
    **62 roots had a playable cycle, 31 had a repetition footprint below the root, footprint range 1–24
    executions per search, and 0 of those 31 showed a score difference** between stock and ablated builds.
    **That is a genuine null rather than an empty one.**
  - **And the null was then tested against the alternative that it is a MISSED DRAW**, which deepens: a missed
    draw trends toward 0 while a real loss goes further negative. Three representative positions scored
    **−550 → −564 → −571 → −1,010** and **−536 → −544 → −553 → −560** and
    **−546 → −552 → −558 → −559** — **all deepen, so they are confirmed losses, not draws the
    engine failed to find.** **That is what makes the null mean something rather than merely exist.**
  - **Final state for this item: mechanism present, live, and demonstrably executing (footprint 1–24 per
    search); removing it changed no score on 31 positions where it ran. Not shown load-bearing** — and the
    qualifier is now **earned rather than assumed.**
  - **A perpetual fixture must keep material constant**, or the line is really a winning capture rather than a
    repetition — a verifier that missed that would produce a false accusation.
- **Evaluation symmetry is evidence, not proof.** 420 positions, 0 asymmetric pairs — strong, and not a
  proof over all positions.
- **The identity baseline.** 27,944,084 on the O+G set; a reproduction on a different 200 positions gives
  27,762,950, so **the number is meaningless without its position set**.

**Never tested at all when this run began, and each now has a seat on it**

**Status of the seats still running at close.** Twelve areas were dispatched in the final hours; **nine are
still open and three closed before the deadline**. They are listed here as untested-with-reason rather than
held open. **A reader should treat each open row as an open question, not as a clean bill** — the same
discipline that makes the vacuous nulls elsewhere in this section honest applies here: an area nobody
reached is not an area that was cleared.

**CLOSED since this list was written — the three that reported, with their numbers:**

| area | result |
|---|---|
| **The NNUE v3 net loader under malformed input** | **Sound.** **53 of 60 hand-built mutants refused, and the 7 that load are exactly the 7 that must** — one residual-flags case the loader accepts by format and the **UCI layer then refuses and unloads**. Plus **1,819 swept header mutations** and **0 sanitizer lines** under ASan+UBSan. Header mutants were **re-checksummed**, so the field guard is what refuses them rather than the checksum. **The one defect is a resource bug, not corruption** — see §10's B29. **The v2 loader remains open** (different path, magic `FORGENET`, its own size cap) |
| **The fifty-move clock inside TT entries** | **Sound, and the null is earned.** All four `score_usable` branches are reached in live search (**262M / 681k / 143k / 37M** verdicts over 76 searches), so none is dead code. Warming at clock 10 and probing at 90 changed the score on **6 of 7 boards — and the same-clock warm control changed it on the same boards**, so the drift is the ordinary warm-table effect, **not clock provenance**. The mate-distance branch is verified against a separately generated expectation set: **43 cells, 0 mismatches**, with controls that must fire and do. **Limit stated by the seat**: 7 boards, depth 12, one clock pair |
| **Book play inside a full two-sided game** | **Clean.** **1,120 games over five arms**: 0 illegal moves, 0 engine errors, **0 games left the book into an illegal position**, and the move after book exit is a legal searched move. **Every game exits at exactly ply 16** (the book's deepest leaf) and **the position graph is acyclic, so no book line can reach a repetition** — a structural fact, not a sampling result. 13 of 589 played book moves concede material, **0 condemned at depth 18**, largest gap 51 cp against an 18 cp noise floor |
| **Mate scores through the transposition table** | **Correct, and verified against the exact failure modes.** `score_to_tt` adds `ply` on store and `score_from_tt` subtracts it on probe (`search.cpp:179-199`), applied at **all 10 store sites and both score-bearing probes** — checked by enumeration, with a grep for a store lacking the wrapper returning **nothing**. The probe-side clamp **discards** a score that would decode into the centipawn band (returns `ValueNone`) rather than clamping it, which is the right direction: clamping would report a mate at a distance that does not exist. **The named experiment passes**: a DTM stored at ply 4 and re-probed at ply 8 keeps the distance BELOW the node unchanged (1→1, 3→3, 5→5, 7→7, 9→9). **Exhaustive sweep: 118,332 cells, 0 failures**, and two planted-wrong pairs — no adjustment, and an inverted one — produce **234,608 failures**, so the checker demonstrably fires |

**STILL OPEN — these are the rows that are genuinely unreached:**

| area | what is untested, and why |
|---|---|
| **Quiescence TT store depth guard** | The defect is measured (a depth-0 store overwrites a depth-24 entry), **the fix is not**: a guard on `store_body` is a design change with unmeasured strength impact, deliberately left to the owner rather than shipped |
| **The qsearch false-draw repair** | ~20 lines, closes both wrong cells, costs zero pins — but it changes `Worker::is_draw`, shared with the main search and the drawn-root work. **Needs the owner's decision plus the full 14-cell sweep** |
| **Pruning features against forced mates, at feature level** | Only the switch-level screen exists: `Lmr+FutilityPrune` change 55 of 148 answers and **lose mates**, and **`SoundMatePruning` costs 2–3 plies** (§3). **Which of the individual features does it, and under what conditions, is not established** — the corpus-level null for null-move, razor, RFP, move-loop, LMR and singular is a null about those paths *as configured*, not a proof they cannot interact with a forced sequence beyond the horizon |
| **ThreadSanitizer with recorded flags** | The prior TSan work is this audit's worst provenance gap — **27 findings across 8 seats with no flag set, compiler line or hash recorded**, and its most-quoted row is a ~1,000× wall-clock outlier measured inside that process. **A proper run needs the flags written down before the numbers mean anything.** The seat dispatched for it **was lost before pushing anything** — it is no longer reachable — so this area is **untouched**, not merely unfinished |
| **A full undefined-behaviour sweep — PARTIAL, and honestly recorded** | The seat is **mid-work at close**, and what it has pushed is the **right shape**: `STATUS.md` records the **exact flags** (`-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g`, resolved `CXX_FLAGS` copied from `flags.make`), the **runtime options** (`UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0:report_error_type=1`), the **binary sha256** (`3104e9a5…`) against the baseline `e06310ec…`, and the proof the sanitizer is **linked** (`nm | grep -c __ubsan_` = 15 versus 0). **12 planted UB classes, one per check class, all caught, control clean**, and **four pins match on the sanitizer build**. **What is missing is the 12-phase workload result and the widened arithmetic arm** (`float-cast-overflow`, `float-divide-by-zero`, which GCC's plain `-fsanitize=undefined` excludes). **So this is a provenance-complete partial, and it is recorded as exactly that** — the opposite of the TSan situation above, where nothing was recorded and the numbers cannot be attributed
| ~~**Long-game replay position identity**~~ **— CLOSED, and it is clean where it matters** | **200 games, 27,788 plies** replayed in one process at `go depth 8`, with a 40-game / 5,401-ply fresh-process arm drawn before measuring. **Position identity: 5,401/5,401 at perft 4 and 1,852/1,852 at perft 5** — the move-list board IS the FEN board. **Halfmove clock agreement 5,369/5,369, boundary exactly at 100.** **RSS 42.2 MiB at all 277 samples from ply 300 to the end, +1.6 MiB total.** **But in-process vs fresh-process bestmove differs on 46.0% of plies (2,486/5,401)** — and scored against a depth-14 fresh oracle that is **better 85 / equal 37 / worse 78, median 0 cp**, so it is **the same engine making equally good moves off a warm table, not a defect and not a strength claim.** **`ucinewgame` between plies makes it byte-identical, 5,401 of 5,401.** **Bails: 0 differences out of 5,401, and all 89 bails predicted independently 89/89.** **So the thing that would have been a defect — accumulating state or a diverging board — is absent, and the 46% is a property of depth-8 move identity across processes, which the report now says plainly because it is the number most likely to be quoted wrongly** |
| **Endgame conversion at game level** | The static inversion is measured (KB vs K = −147, KN vs K = −144, both below K vs K's +2) and reaches search for KNN vs K, but **no conversion rate exists**: nobody measured whether KBNK or KPK is actually won at a real budget |
| **`bestmove 0000` consistency across mate roots** | A checkmate root answers `mate 0` / 0 nodes / `bestmove 0000` on the fixtures tested. **Whether that holds at every mate root** matters because an inconsistency breaks every client's mate detection, and it was not swept |
| **Mate labels over a corpus** | Two labelling errors are recorded (eight by-eye fixtures all one ply short; ten "false" mates that were merely unverifiable). **A corpus-level rate with an oracle's provenance does not exist**, and a handful of examples is not a rate |
| ~~**The 51 tunables behind `FORGE_EXPOSE_TUNABLES`**~~ **— CLOSED, and it is the cleanest row in the audit** | **All 51, five values each, 255 cells, every one correct.** Each tunable was sent its advertised `min` and `max` (accepted silently), `min−1` and `max+1` (reported **and clamped**), and `abc` (refused, old value kept) — **and then a search was run**, so "accepted" is behaviour rather than a `setoption` reply. **0 crashes, 0 hangs, 0 non-conforming rows.** **And all 51 moved the probe search at some value**, so none is a dead option — which is the field a clamp-only check would have missed entirely. The count is sourced: `tune::parameters()` at `search.cpp:114-148` lists 51 entries, and 51 + the four non-tunable spins (`Hash`, `Threads`, `MultiPV`, `Move Overhead`) = the 55 advertised |

- **Three items on this list are CLOSED**: the lone-king second mechanism now has an instrument and a
  measured negative, `Threads` above 1 has been measured end to end (including the finding that the
  honesty pins cannot see it), and a portable build at a lower ISA has been pinned, timed and found
  correct. All three are below with their numbers.
- **`Threads` above 1 — CLOSED, and it invalidated the gate for this one setting.** The inherited rule holds
  at maximum strength (0 of 40 positions differ at Threads 1; 40 of 40 differ in node count above it), and
  the measurement added four things the rule did not say: **at fixed depth Threads 4 costs 1.24× wall for
  the same ply and Threads 8 costs 2.00×**; **only Threads 4 gains depth in a fixed second (+1.4 ply,
  p = 0.0033)** while T2 and T8 are "no effect detected at n=40"; the **drawn-root path is thread-invariant
  at 20 of 20 cells**; and **the four honesty pins cannot see any of it**, because `bench` builds its own
  single-threaded searcher and never reads the option. **So the one gate this whole audit relies on is a
  Threads-1 gate and nothing else** — a harness running threaded searches has no pin it can trust.
- **Time-manager accounting under a real game.** The floor and the planner formula are measured on fixed
  controls; **increment accumulation over hundreds of games, `movestogo` meeting the new fallback clock,
  and `movetime` accuracy across four orders of magnitude are not.**
- **Why `Hash 16` and `Hash 64` diverge above ~200k nodes — CLOSED, and the guess was wrong in both
  directions.** It is **not** "fewer collisions" alone: there are **two separable components** — a
  **load-independent baseline** (Hash 64 vs 65, a 1.02× step at equal load, still disagrees **11 of 24**,
  because `(key * cluster_count) >> 64` moves **99.996% of keys to a different cluster** for any size
  change) and a **genuine load increment** (Hash 16/32 add 12 more at p = 0.00026 with 100× the evictions).
  The ordering is **non-monotone**, which a pressure-only account cannot produce. **Practical threshold
  ~750k nodes: below 500k the sizes are near-identical; at 750k two-thirds disagree on score.** See §3.
- **The second lone-king mechanism — instrument now BUILT, and it narrows the search rather than closing
  it.** `BARE_KING_LMR_CAP` off restores the base move 11 of 11, but the cap fires on 100% of nodes and
  **two of eleven counter-cases go the other way**. A seat has now built the per-depth reduction counter
  that this section said was missing, gated it (flag off is **byte-identical** to the plain build, sha256
  match, and flag on changes **0 of 40** positions in bestmove, depth, score or node count), and used it:

  | what the counter says | result |
  |---|---|
  | does it separate the two counter-cases from the nine predicted boards? | **NO** — both counter-cases fall **inside** the predicted range on count, magnitude, mean, re-search rate, rejection profile, and the same restricted to cap nodes |
  | the seat's proposed aspiration-cascade account | **REFUTED, 0 of 11** — the score never diverges before the node counts, which the account requires |
  | the clamp's *immediate* effect at the first divergent depth | **the same everywhere**: cap-ON visits **more** nodes on **2 of 2** counter-cases and **8 of 9** predicted boards |
  | what differs | only what happens **afterwards** — the sign reverses by the final depth on **both** counter-cases and on **1 of 9** predicted boards |

  **So the mechanism is not in how the clamp acts at a node and not at the point of divergence: it is
  downstream, in how two already-divergent trees propagate.** That is a **location, not a cause**, and the
  seat labels it that way. The reversal rate (2/2 against 1/9) is **Fisher p = 0.0545**, chosen after
  seeing the full set, so it is **a lead and not a finding** — the seat records all three caveats so it
  cannot be quoted as confirmatory.
  - **And the negative now has an EXPLANATION, which is what turns it from "my counter cannot see it" into
    "here is why a counter of this kind cannot see it".** Per-ply fingerprints of the visited position keys
    show **cap-ON and cap-OFF visit genuinely DIFFERENT positions at the divergence depth on 9 of 11
    boards, including both counter-cases** (the other 2 are the same set at different multiplicity). **So
    the reduction statistics are averages over different node populations**, and two aggregates taken over
    different populations are not expected to separate the boards — **the counters were not insensitive,
    they were measuring different things and being compared as if they were the same thing.** That is the
    same defect as trap 14 at a lower level, and it is why the negative is worth more than a failed test.
    - **The classifier discriminates and the fingerprint does not perturb**: it produced **two distinct
      verdicts across the set (9 versus 2)**, so it is not returning one answer by construction, and the
      key counters themselves change nothing (`FORGE_LMR_KEYS=1` versus `=0`: **identical 20 of 20**).
      **Stated as a fingerprint, not as proof of set equality** — XOR agreement could in principle collide,
      and the seat says so rather than calling it a proof. **The next step is now narrow and named: first
      divergence in MOVE identity, using the same machinery.**
  - **And it published the first reduction statistics anyone has for this engine**: on 40 ordinary
    positions at depth 12, **390 reductions per 1,000 nodes** (per-position median 392, range 344–450),
    **mean magnitude 2.38**, **2.66% re-searched**, with a signed histogram — `r` can be negative because
    the LMR terms subtract for `tt_pv`, check and history. **The profile is identical on both trees away
    from lone-king roots (390.09/1k and r = 2.377 on each), which is the control that makes the counter
    trustworthy.**
  - **The instrument's own arithmetic check found a real bug in the instrument**: the first version
    clamped `r` into bins `0..15` and **silently corrupted the distribution** by folding negative
    reductions into bin 0. It was caught by requiring the histogram to sum to `applied` and the recomputed
    mean to equal the printed one, plus a negative control that inflates a bin by 1 and **must** be
    rejected. **A counter that has never failed is not evidence that it counts.**
  - **And the print path is proved harmless rather than asserted**, which is the question that separates a
    trustworthy instrument from a plausible one. A third build state (`FORGE_LMR_STATS=1`,
    `PRINT=0`) runs every counter and prints nothing; **silent equals base on 40 of 40, and printing equals
    silent on 31 of 31** in bestmove, score, final nodes **and every per-depth node count**. **Nothing
    prints inside a search** — the flush is **between completed iterations**, at the same point the engine
    emits its own `info depth` line. **So "changes nothing but output" is now a measurement with its own
    three-arm control, not a claim about a patch the reader has to trust.** **The seat's line number for
    that flush (`search.cpp:2689`) is from ITS instrumented tree and does not resolve on `6b98f217`** —
    line 2689 there is inside `Searcher::search`'s clock setup — which is why the claim is stated by
    POSITION ("between completed iterations") rather than by line: **an instrumented tree's line numbers
    are not the base's, and a citation into a tree nobody can check is the trap this report keeps
    recording.**
  - **And the gate's own first run passed 11 of 11 VACUOUSLY, which the seat caught and recorded.** Every
    one of those 11 boards reported the **same 13,102 nodes and the same `d2d4`** — a uniform result across
    unrelated inputs, which is trap 10's tell. Cause: the board list was `(fen, cls)` and the harness
    unpacked it as `(name, fen)`, **so it searched for the literal string `pred`** and got the same answer
    eleven times. **What caught it was a control that was supposed to be trivial**: the printing arm's
    line count was startpos-shaped (**191**) on all 11. **So the uniform answer was not the detection — the
    cross-check against a known-shaped output was**, which is trap 13's "zeros are the easiest claims to
    leave unplanted" with a 13,102-node answer instead of a zero.
- **A whole build at a lower ISA — CLOSED, and it is portable.** The engine has a `FORGE_PORTABLE` CMake
  option (it drops `FORGE_SPD_SLIDER_PEXT` and `FORGE_SPD_NNUE_ZMM`); nothing had to be invented. **Every
  pin, perft count, eval value and searched node count is identical across the three builds, so the
  engine's correctness does not depend on the ISA and the entire cost of a portable build is speed.**
  - **`-march=x86-64-v3 -DFORGE_PORTABLE=ON` is the recommended portable build**: all **11 LOCK.md pins
    exact**, perft exact, identical search on 120 positions, **+4.2% wall (CI 1.0372–1.0450, slower on 106
    of 120)**.
  - **`-march=x86-64-v2` is correct but expensive: +16.1%, slower on 120 of 120.**
  - **A lower `-march` ALONE does not compile** — with `FORGE_PORTABLE=OFF` the source fails with an
    explicit `#error` rather than a miscompile. **That is the right failure**, and it is worth saying
    because the alternative (a silent miscompile at a lower ISA) is what a portability claim usually has
    to rule out.
  - **And the option leaves performance on the table at v3**: it disables PEXT unconditionally, but
    `x86-64-v3` **includes BMI2**. Enabling PEXT at v3 cuts the cost from **+4.2% to +1.4%** — a one-line
    fix the seat supplies, and the clearest kind of finding: **the portable path is not slow because
    portability is expensive, but because one switch is gated on the wrong condition.**
- **Memory stability — CLOSED, and clean.** A soak seat ran **5,000 depth-12 searches in one process** and
  the process does not leak: **RSS moves +1.5 MB in total and 0.000 MB per 1,000 searches** across
  searches 1,000–5,000, plateau **42.1 MB** at Hash 32. **RSS tracks the `Hash` option to within 0.1%** at
  16 / 64 / 256 / 1024 MB, and every non-table byte is a **constant 10.1 MB at all five sizes** — which is
  the shape that says "the table is the allocation and nothing else is growing". 5,000 `ucinewgame` and
  `Clear Hash` loops return to their starting RSS, and 1,000 MultiPV-4 searches at Hash 64 show **no
  ratchet**. ASan+UBSan with `detect_leaks=1`: **no leaks**, and the detector was proven live on a planted
  fault through the same runner.
  - **It independently confirmed the alternate-table finding I derived from source, and did it better than
    my derivation could**: at Hash 256 with MultiPV 2 the process peaks **259.6 MB above** its MultiPV-1
    peak — one more full-size table, as `search.cpp:2385-2386` says — and **returns within +3.6 MB after
    `bestmove`**, so it is peak memory and not a leak. **A source reading and an RSS measurement agreeing
    to within the allocator's slack.**
    - **The decisive form was a SLOPE, not a cliff**: **2.001 MB of peak RSS per MB of Hash at MultiPV 2
      against 1.000 at MultiPV 1.** A slope asks how memory scales; a threshold asks where a boundary sits,
      and a boundary moves with whatever else is resident. **The seat predicted the `ulimit` threshold
      would double, measured 1.41× and 1.99× at two Hash sizes, called its own prediction KILLED, and then
      found the right instrument.** The cliff turned out to be `peak resident + however much address space
      glibc has reserved at that instant` — 10.1 MB at Hash 64 but 70.5 MB at Hash 256 — which is exactly
      the shape that makes a threshold-based test unrepeatable and a slope-based one robust.
    - **And the resize transient is real, measured with `VmHWM` rather than a sampler**: 16 → 256 peaks at
      **281.9 MB** against a predicted 280, and the **same-size control 256 → 256 peaks at 521.9 MB**
      against a predicted 520 — confirming that `resize` holds **old + new** (`search.cpp:365-366`) and
      that the allocator does **not** reuse the freed block. **A sampler would have missed it; the kernel's
      high-water mark cannot.** That control is the one that makes the number interpretable: without it,
      281.9 MB proves only that something happened.
  - **Not established, in the seat's own words**: no run exceeds ~5 minutes of engine time or 5,000
    searches, so this is not evidence about multi-day uptime beyond "nothing is accumulating"; and no arm
    used more than one thread, so **per-thread worker memory at `Threads 8` is unmeasured** — which is the
    one place this clean bill has a hole, and it is the seat's own gap, not a reader's inference.
- **MultiPV's OUTPUT — CLOSED, and the interesting result is that the two properties everyone checks are
  true by construction.** A client-side audit of 1,920 depth blocks found **ordering and score monotonicity
  perfect — 0 emission-order and 0 index-order violations — but only because the engine sorts before it
  prints** (`std::stable_sort` by score at `search.cpp:2518`), so those two properties **tell a client
  nothing.** What is not guaranteed:
  - **PV-length monotonicity, the standard expectation, is violated in 116 of 160 final blocks**, and in
    **80** the **first** line is not the longest. **A GUI that sizes its PV pane from line 1 silently
    truncates the best line.** **The mechanism is measured rather than asserted**: the **primary line's PV
    is truncated by TT hits** while **each alternate runs in a freshly cleared table**
    (`alt_shared->tt.clear()`) **and reaches its seldepth** — **line 1's PV is below its own seldepth in
    40 of 40 blocks.** **The comparison to `seldepth` is what makes it specific: the primary line's PV is
    below its own `seldepth` in 40 of 40 blocks, so the truncation is visible in a single line and does
    not need the alternates to expose it.** **The seat's own document goes one step further and I do not
    repeat that step, because the sentence is ambiguous and contradicts its own rule two sections later**:
    it reports "against `seldepth` the count is `0` at MultiPV>1, and `480` of `480` blocks at MultiPV 1",
    which cannot be read as a violation count without contradicting its later line "PV longer than
    `seldepth` never happens". **So the PV-versus-`seldepth` question is quoted here only in the form that
    is unambiguous — line 1 against its own `seldepth` — and the seat's 0/480-versus-480/480 pair is
    flagged as needing a re-read before anyone cites it.** **The caveat is
    part of the finding**: this rests on the convention
    `len(pv_1) >= len(pv_2)`, which the seat did **not** establish as a requirement any standard GUI has —
    **it measured the violation and the mechanism, not the obligation.** **Full denominators and the
    client-impact statement are in §3 with the rest of the MultiPV work.**
  - **Completeness is perfect at fixed depth (0 of 1,920) and routinely violated under a budget**:
    **32, 32, 32 of 40** on a node budget and **35, 35, 31** on a wall-clock one across three repeats — **a
    range, because a movetime stop is not reproducible**, and the node-budget figure is stable across
    repeats where the movetime one is not. **The SHAPE is the part that matters**: the engine opens a new
    depth block, emits part of it, and stops mid-block, so **the truncated block is the last thing on
    screen** — not a short block buried mid-output. `N > legal moves` is handled correctly and never
    over-claims.
  - **The multipv-1 line equals `bestmove` in every search** but **equals the single-PV search's answer in
    only 22 of 40 positions.** In the **18** that differ, a deeper search **confirms the single-PV answer 9
    times, confirms the MultiPV answer 3, and picks a THIRD move 6** — and **a depth-only control changes
    the move in 12 of 40 without MultiPV being involved at all.** **So the disagreement is mostly the
    position being unsettled, not MultiPV distorting it** — which is the same conclusion §3 reached from the
    other direction.
  - **The book path emits zero `multipv` lines at MultiPV 2, 3 and 6** (with `OwnBook false` controls at
    16+ info lines, so the zero is not a dead path), and the bail emits **exactly one line per depth, never
    an index above 1**, across **four drawn shapes × four MultiPV settings**. **And the book PRE-EMPTS the
    bail, gated on the FEN's FULLMOVE counter rather than the halfmove clock** — **the same 100-ply board
    books at fullmove 1 and bails at fullmove 16.** That sharpens trap 19a: the pre-emption's trigger is a
    field that has nothing to do with why the position is drawn.
- **`go mate N`'s full surface.** Established as a different search (11 of 12 cells differ from
  `go depth 2N−1`), not established: what it does when no mate exists, whether it obeys a clock, and which
  of the seven disabled heuristics actually changes a mate answer.
- **Aspiration windows — CLOSED as behaviour, and the answer is that the question cannot be put to the
  engine at all.** The engine **publishes no `lowerbound` or `upperbound` token on any path**, so "does a
  fail-high leak a wrong-bound score" has no wire-visible answer; a bound-publishing build was planted to
  prove the instrument can see one (**6 of 6**), and on the real build **5,320 traced iterations produced 0
  bounds and every score strictly inside its final window.** The mate arm is clean on the same instrument
  (180 testable mate claims, all deliver, 0 false, 0 distances above `seldepth`; `go mate N` exact on 8 of
  8). **What the seat could NOT establish, in its own words**: single-threaded only; no clock arm; a
  four-point delta sweep rather than a curve; and **the corpus cannot put a narrowed window directly on a
  mate score**, since its mates resolve by depth 3 and narrowing starts at depth 4, so that part is
  covered indirectly through `go mate N` and deep KQK ladders. **The finding that survives all four limits
  is the delta sensitivity** — score moves on 126 of 133 positions and the move on 95 of 133, for a 12–15%
  median node saving and a 2.56× worst-case cost, with one position's `cp 517` becoming a true `mate 2` at
  delta 200.
- **What a client sees.** Every finding was made with source access and a bespoke harness; **no test drives
  the engine purely from documented UCI output across book, drawn root and normal search in a real game.**
