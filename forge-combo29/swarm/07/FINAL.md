# FINDINGS — seat 07, area 7: FINAL BLOCK (window closes 2026-11-17T10:19Z; this file written 2026-11-17T01:10Z)

Seat 07, branch `for-fable-and-opus/swarm-07`, folder `forge-combo29/swarm/07/`. Every figure below is
Threads 1 unless a line says otherwise. Two builds were used throughout:

- **base** = commit `6b98f217`, GCC 13.3.0, plain CMake Release, `-march=x86-64-v4`.
- **PC r15** = base + `pc_r15.patch` from `FABLE_TO_swarm_5.md` (sha256 `d6bd72c5…`, applied in a
  separate worktree, `-DFORGE_MATE_ALPHA_GUARD=1`). All eight published PC numbers verified (07-C21).

Settings are named per line: **none** (no setoption), **S14** (the 14 settings of file 1), **PC20**
(S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true, OwnBook
false).

---

## Real findings, with state

| id | finding | state | build / settings |
|---|---|---|---|
| **07-F1** | `searchmoves` naming no legal root move, on a board that HAS legal moves, prints one fabricated `info depth D … score cp 0 nodes 0` line **per depth** (64 of them with no depth limit) and then `bestmove 0000`. The engine already computes the true cause at `search.cpp:2531` (`restricted_root_empty`). | **CONFIRMED by seat 10 (10-C15)** with its own harness, and by seat 17 as S-F1/S-F8 (independent observation, same defect). **Measured live on ALL SIX arms — base and PC × none/S14/PC20** (07-C77), so it is unfixed code on the shipping branch. **THE ONLY OUTSTANDING ENGINE CHANGE OF MINE.** Repaired by a **one-edit** shared-path patch, `job73/07f1_shared_report_v3.patch.txt`: all eight pins unchanged, seven zero-node paths verified, clean-tree rebuild byte-identical. Supersedes `job55` v1 and v2 (both marked DO NOT USE). | base and PC r15; **none, S14 and PC20**; Threads 1. |
| **07-F3** | On the **base** tree a fifty-move root with a counter-resetting move available is declared a draw **without being searched** (`cp 0`, **0 nodes**, 12 fabricated depth lines) while a forced mate exists. Example `8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1`: base `cp 0`/0 nodes vs PC **`mate 6`**/15,981 nodes. | **CLOSED BY THE PC BUILD** (07-C77: base fails in all three regimes, PC searches and finds mate in all three) — a justification for a fix already in the tree, **not outstanding work**. Now proved by replay (07-C75): three regimes, three different PVs, every one reaching actual checkmate. | base and PC r15; **none, S14, PC20**; Threads 1. |
| **07-F4** | The base tree declares a draw on **all 20** fifty-move-counter-100 positions in the targeted sample (0 nodes each), and the counter-reset reference shows a **decisive** result on 5 of 20 — **4 losses masked, 1 win thrown away**. | **MECHANICAL AND 20 OF 20** (07-C76: no counter-100 root is a genuine fifty-move draw, and all 80 counter-0 roots search). **Boundary exact at counter 100** (07-C80: base abandons a mate-1 at 100+, still wrong at 9,999; PC plays it at every counter). The 5-of-20 cost figure remains supporting colour — it needs a referee. | base; **none**; Threads 1; reference depth 18/24/30. |

### Withdrawn claims of my own (kept visible)

| id | what I claimed | why withdrawn |
|---|---|---|
| **07-R1** | search.cpp:2640 read `front()` of an empty `MoveList` (UB). | The early return at 2253 fires first; a two-branch marker build proved 2640 never sees an empty root. **This build also settled the three-seat contradiction (07-C2).** |
| **07-R2** | `LmrSignedCorrection` is dead code (bound ±32 cp, so `/64` is always 0). | `corrected_eval` **sums three** correction tables, so the bound is ±96 cp, not ±32. The repo's own `REPORT_r3_03.md` documents the option and the deliberate `/8 → /64` change. **Do not re-open.** |
| (intermediate) | "19 of 20 fifty-move positions are base errors (95 %)." | Conflated `cp −1601` with "a win exists". Corrected to 6/20 at depth 12, then **5/20 at depth 18–30** (07-C38/C39). |
| (intermediate) | "PC20's saving is two options cancelling." | The 40-position table had three of six options with the wrong sign. At 200 positions `TtPruneV2` alone is 85 % of the effect (07-C32). |

---

## Checks and confirmations (C-series), with build and settings

| id | result | build / settings |
|---|---|---|
| 07-C1 | REFUTES 17-S-F2's cause (no empty `front()`); symptom of 17-S-F1 real | base, none |
| 07-C2 | **Settles 01 vs 07 on search.cpp:2640**: 2640 is never reached with an empty root (both-branch markers) | base, none |
| 07-C3 | O depth 12 = **9,500,069** exact | base, **S14** |
| 07-C4 | G depth 12 = **18,466,239** exact | base, **S14** |
| 07-C5 | `go`/`stop` GUI cycle clean, 40 plies (after I fixed a blind test) | base, none |
| 07-C6 | O depth 14 = **21,812,100** exact | base, **S14** |
| 07-C7 | Clock: 9 controls, 0 overruns, 0 illegal; **book answers clock searches with no depth line** | base, none |
| 07-C8 | G depth 14 = **43,345,893** exact — all four published sums reproduced | base, **S14** |
| 07-C9 | `eval` is exactly colour-symmetric; **it is side-to-move-relative** (eval(P) == eval(mirror P)) | base, none |
| 07-C10 | Inline legality shortcut correct on 289,809 moves; control must be planted in **board.hpp** | base, none |
| 07-C11 | `gives_check` correct on 260,053 moves (header-planted control catches 3,999) | base, none |
| 07-C12 | TT invariants held; a header fault needs **every dependent TU recompiled** | base, none |
| 07-C13 | Shipped TT path (`TT_NOTLS=1` is the default) is pin-verified | base, none |
| 07-C14 | Book moves always legal (16 book plies); first control was inconclusive | base, none |
| 07-C15 | SEE oracle rebuilt and **validated against 5 hand-settled cases**; 150 positions clean | base, none |
| 07-C16 | Time-manager properties hold under UBSan (3 void controls before one fired) | base, none |
| 07-C17 | Increment-heavy clock never loses on time; 0.796 max share recorded as behaviour | base, none |
| 07-C18 | 07-F1 re-verified on a fresh build; patch still applies `--fuzz=0` | base, none |
| 07-C19 | **CONFIRMS 27-S-F7** on 82 options / 437 cases, both bug classes controlled | base, none |
| 07-C20 | `NonPawnCorrection` takes effect (56,720 → 33,066 nodes); matches seat 10's cold figure | base, none |
| 07-C21 | **PC r15 built; all 8 published numbers exact** in none/S14/PC20 | PC r15 |
| 07-C22 | The three reported symptoms are **two paths** (empty root vs abort fallback) | PC r15, PC20 |
| 07-C23 | **PC-tree patch cures 07-F1 on r15**, all 8 pins unchanged, controls identical | PC r15, PC20 |
| 07-C24 | `bestmove 0000` design answer: A/B/C/D measured, **recommend B**, written into the patch header | PC r15, PC20 |
| 07-C25 | One-candidate legal restriction searches normally (boundary is emptiness, not size) | base + PC r15, both regimes |
| 07-C26 | **PC20 baseline 8,315,168** with per-position digests, reproducibility proven | PC r15, PC20 |
| 07-C27 | All seven board-level checks hold on the PC tree | PC r15 |
| 07-C28 | PC20 vs S14 per position: **200/200 node counts change**, 60/200 bestmoves, 195/200 scores | both, both regimes |
| 07-C29 | The one unexplained base-vs-PC difference is **BARE_KING_LMR_CAP**, and the PC answer is better | both, none |
| 07-C30 | Four legs: **PC+S14 == base+S14 == 9,500,069**; the delta is an **interaction**, not a split | both, S14 + PC20 |
| 07-C31 | 40-position option table — **superseded by 07-C32** | PC r15, S14 + one option |
| 07-C32 | **200-position option table: TtPruneV2 = −1,002,190 = 85 % of PC20's effect**; CorrHistV2 +251,935; corrects 07-C31 | PC r15, S14 + one option |
| 07-C33 | 100-position differential = **0 differences**, with a proven control | both, none |
| 07-C34 | **Where the patch acts: targeted 50/100 differ (30 bare-king, 19 root-drawn), ordinary 0/100** | both, none |
| 07-C35 | The targeted differential shows **base failing** where PC succeeds | both, none |
| 07-C36 | **No bare-king regression** in 30; the 7 "worse" cases are all closer to depth-18 truth | both, none |
| 07-C37 | No mate-distance lengthening in this sample (base reports no mate at all) | both, none |
| 07-C38 | Fifty-move rate **tightened to 5/20**, one depth-12 artefact removed | base, none |
| 07-C39 | **Rate settled at depth 30**: 0 of 6 changed category | base, none |
| 07-C74 | **16-S-F35/F37 confirmed exactly: 34/120 stock → 120/120 canonicalised, residue zero** — after catching a false refutation from an inert build | both, PC20 + `-DFORGE_EXPERIMENT_MIRROR_ORDER=1` |
| 07-C75 | **07-F3 reduced to one hand-checkable case: base says `cp 0`/0 nodes on a board where a forced mate exists under all three regimes, and every PV replays to real checkmate** (job71/raw) | base + PC, depth 12 |
| 07-C76 | **Fifty-move fault is mechanical and 20 of 20: every counter-100 root declared drawn with 0 nodes, and python-chess says none is a fifty-move draw** — vs the 80 counter-0 roots, which all search | base, depth 12, 100 rows |
| 07-C77 | **The two faults separate on the ship build: 07-F1's fabricated lines live on ALL SIX arms; 07-F3's fifty-move fault is BASE-ONLY and the PC build fixes it in all three regimes** | base + PC, 3 regimes × 2 faults |
| 07-C78 | **My own live patch had the defect it was written to fix, in reduced form: v1 cut 64 fabricated lines to 1 but emitted that line at `depth 64` with `nodes 0`; v2 reports `depth 0`** (job73/raw_v2) | PC r15, 3 regimes, 7 zero-node paths |
| 07-C79 | **v2 of my patch could not apply to a pristine tree (diffed against my working copy); v3 applies clean, and a from-scratch rebuild in a clean checkout is byte-identical** (job73/raw_v3) | clean PC r15 checkout, g++-13, 3 regimes |
| 07-C80 | **Fix side confirmed with the exact boundary: base abandons a mate-1 from counter 100 onward (still wrong at 9,999), PC plays it at every counter; plus a wording correction on `is_fifty_moves()`** | base + PC, counters 0–9,999 |

---

## The five things I would put in front of the owner

**Where to start: items 4 and 5.** Those two are **procedural** — no patch, no decision about defaults,
no re-run — so they are actionable the moment they are read and cost nothing to apply. **Item 1 is the
only outstanding engine change of the five**: 07-C77 measured it live on all six arms including the PC
build under all three settings, while item 3's fault is already fixed on the PC build and needs nothing.
Item 2 is a tuning observation whose strength question I did not measure.

1. **07-F1 is the ONLY engine defect of mine that is live on the PC build** — and that is now measured
   rather than assumed: `go depth 12 searchmoves a1a8` emits its fabricated per-depth lines on **all six
   arms (base and PC × none/S14/PC20)**, identical to the line, with `bestmove 0000` throughout (07-C77).
   It is confirmed by another seat and has a ready patch that changes no node count on any published
   bench (07-C23, 07-C24). Recommendation: ship the "honest `0000`" form; if a playable move is wanted
   instead, that is a separate decision that must print that the restriction was ignored. **Note added
   later (07-C54, 07-C55): it is not a `searchmoves` defect at all** — every path that reports without
   searching emits a fabricated `score cp 0 nodes 0` line per depth. The shared-path patch
   (`job73/07f1_shared_report_v3.patch.txt`) fixes all seven paths with one edit, **all eight pins
   unchanged — the eight being none 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20
   278024 / 587276**, and supersedes my own narrower `job2`/`job29` patches AND both earlier versions of
   this one** — v1 cut 64 fabricated lines to 1 but printed that line at `depth 64` for a bare
   `go searchmoves`, repeating the same lie once instead of 64 times (07-C78); v2 had the right
   content but was diffed against the already-patched tree, so it could not apply to a pristine one
   (07-C79). **v3 is diffed against pristine PC r15 and a from-scratch rebuild in a clean checkout
   gives a byte-identical binary** (`2db028fa…`), so the patch alone determines the build.
2. **`TtPruneV2` carries 85 % of PC20's node effect** on 200 positions (07-C32), while `CorrHistV2`
   costs 2.7 %. Whether that saving is strength is a games question I did not measure.
3. **`FORGE_FIX_ROOT_DRAWN` earns its place on one undeniable board — AND IT IS ALREADY FIXED ON THE PC
   BUILD, so this is a justification rather than an outstanding task.** *(Closed by 07-C77: base answers
   `cp 0`/0 nodes in all three regimes; the PC build searches in all three and finds mate. Nothing further
   is needed from anyone.)* The board is
   `8/6qk/8/8/8/1p4p1/4K3/8 b - - 100 1` — the base build answers **`cp 0` with 0 nodes**, declaring a
   draw without searching. It is not a fifty-move draw: python-chess finds **25 legal moves, two of them
   pawn moves (`b3b2`, `g3g2`)**, so the counter resets on the move actually played. The PC build finds a
   **forced mate under all three settings** (no-options `mate 6`, S14 and PC20 `mate 5`), and **every one
   of those three PVs replays on a python-chess board to actual checkmate** — 11, 9 and 9 plies (07-C75).
   So this needs no rate, no referee and no second build: the FEN, the two pawn moves and a nine-ply line
   you can play yourself are the entire argument. **And the whole class is mechanical, 20 of 20:** across
   all 100 rows of the targeted set, exactly the 20 counter-100 roots answer with **0 nodes** while the 80
   counter-0 roots all search (8,066–113,601 nodes), and **python-chess says not one of those 20 is a
   genuine fifty-move draw** — every one has a capture or pawn move available (07-C76). That is
   `nodes == 0` and `not (halfmove ≥ 100 and no reset available)`: no referee, no threshold. **One
   wording correction worth stating plainly: `python-chess`'s `is_fifty_moves()` returns TRUE on these
   boards** — it tests only `halfmove ≥ 100 and any(legal_moves)` and does not look for a
   counter-resetting move, so the verdict needs the extra `and not resets` (07-C80). **And the fix side
   is now measured too (07-C80), which is what actually prices the fix:** on
   `6k1/5ppp/8/8/8/8/5PPP/R5K1 w` the base plays `a1a8` = `mate 1` at counters 0/50/99, then from
   **counter 100 onward — including 9,999 — answers `cp 0` at 0 nodes with the quiet `f2f3`, throwing
   away a mate in one**, while the PC build plays the mate at every counter. The boundary is a hard
   step at exactly 100 and never recovers. On two of seat 19's three boards the declared draw was
   hiding a **mate** — which states the fix's value better than any rate: a rate says how often, this
   says the missed result was decisive. **The cost estimate (5 of 20
   decisive, 1 thrown-away win, 07-F4/07-C38/07-C39) is a separate and softer question** — it needs a
   depth-12 re-search as referee and was revised downward twice, so treat it as supporting colour rather
   than the claim.
4. **DO NOT PLAY A ZERO-INCREMENT TIME CONTROL.** *(Procedural — no patch, no re-run.)* The clock floor
   that protects the engine is
   `MoveOverhead + increment · 100/TmHardPercent` = `10 + increment · 5/3` ms (28-S-F44, reproduced
   exactly in 07-C57). At the owner's `6 s + 0.06` that is **111 ms**, and I verified the engine's real
   spend falls *inside* the 60 ms increment once the clock drains, so it is safe. **But at `winc 0` the
   formula gives a floor of about 10 ms, i.e. `Move Overhead` alone — there is no margin and nothing
   protects the engine from flagging.** Every clock control I ran with an increment had zero overruns
   (07-C7); that safety comes *from* the increment, not from the clock path.
5. **VARY THE OPENINGS IN SELF-PLAY, OR THE SET IS TEN COPIES OF ONE GAME.** *(Procedural — no patch, no
   re-run.)* With a node budget (which
   is exactly reproducible — 07-C49) ten games from startpos gave **one** distinct final position and
   **one** distinct move sequence: all ten identical. Ten games from ten different positions gave ten
   distinct finals and ten distinct sequences (07-C68). So with fixed starts the **effective sample size
   is one per start**, not ten — and varying the opening is the only thing that makes a self-play set
   non-degenerate. Seat 16 measured 7-of-10 identical on a clock and blamed millisecond drift; removing
   the clock made the duplication total, which confirms their explanation. **This one needs no patch, no
   decision about defaults and no re-run — it is actionable the moment it is read**, which is why it is on
   this list at all: if self-play currently uses fixed starts with node limits, the data set is smaller
   than it looks by whatever factor the starts repeat. **And there is a cheap mechanical guard for the
   labels themselves**: a printed PV shorter than `2|N|−1` (`2|N|` for a mate against the side to move)
   means the mate was **not delivered** — 24 of 24 on my positions, 39 of 39 on seat 05's, 63 of 63
   combined, no exception (07-C73). Compute the number, compare it with the PV length, discard the short
   ones; no replay and no tablebase needed. **Together these two close the self-play data question:**
   varying the openings fixes the *inputs* (ten games that are actually ten games) and the PV-length
   check fixes the *labels* (a mate that was reported is a mate that was delivered). Neither needs
   anything from the engine — no patch, no rebuild, no re-run. That is the whole answer to "is my
   self-play set worth training on": make the games distinct, then throw away the labels whose own PV
   says they are fiction.

## Audit method: how to check a seat's scope without raising a phantom alarm

My STATUS corruption (an 84,000-line `git diff` injected by a backtick in a shell echo) was **real**,
and the handling that caught it was mechanical: check the file's line count and tail immediately after
writing, rebuild from the known-good prefix, verify no stray diff markers remain, re-check that the
status headers survived, and push the repair as its own commit so corruption and fix both stay visible.

But the *same class of alarm* is easy to raise falsely, and another seat has now shown why: **in a
shallow clone, `git show` on a seat's first commit prints the entire tree as added**, so it reports tens
of thousands of files and millions of insertions that are not that seat's work at all. Anyone auditing
scope that way will "find" a catastrophic breach in every seat, including innocent ones.

**The correct audit is a diff against the base commit, excluding the seat's own folder:**

    git diff 6b98f217 <tip> -- . ':(exclude)forge-combo29/swarm/<NN>'

If that prints nothing, the seat committed only its own files. I ran exactly this on my own branch and
it is empty, which is the claim worth quoting — not a file count.

## The twenty-three standing rules, grouped by the question they answer

The FINDINGS header carries sixteen rules; the table there is ordered by when I learned them, which is
the wrong order to read them in. Grouped by what they are for:

### Is the thing I am measuring actually the thing I meant to measure?

- **If the answer does not belong to the position, the position was not accepted.** The engine refuses an
  invalid FEN and keeps the previous board, so a move that could not occur on your board means your board
  was rejected. (Caught me with `e2e4` on a position holding a lone black king on h8.) **`readyok` does not
  save you: a refused position still answers it** (07-C70). The guard that survives that lying handshake is
  `go perft 1` compared with python-chess for the intended board.
- **Assert your harness settings explicitly and record them: `Threads 1`, `MultiPV 1`, `OwnBook false`.**
  `MultiPV 2` silently costs 3 plies on startpos at `go nodes 20000`, with no error and a plausible node
  count.
- **A fabricated-move check needs a position where the engine's first move is not alphabetically first.**
  startpos: both `a2a3`, blind. **kiwipete**: engine `a2a3`, alphabetical `a1b1`, discriminating.
- **A deep search on a high-halfmove-counter position needs a node budget or a timeout.** An untimed
  `go depth 20` there can take ~250 M nodes and look hung.

### Is this number reproducible at all?

- **A node count under a clock stop is not reproducible until you prove it is.** Repeat the same cell on
  the same binary first; mine gave 412 nodes once and 971 on five other runs.
- **A small-sample rate does not order anything.** Two disjoint 100-position samples flipped a budget
  ordering ten points apart; 353 positions showed it was nothing.
- **Read a clock result by its move and wall time, not its node count.** Node *stops* are deterministic
  (16/16 cells exact); node counts under a clock are not.

### Is my comparison right?

- **When the complaint is "this number is a lie", the fix must make the number true, not just
  rarer.** My own patch cut 64 fabricated `nodes 0` lines to 1 and emitted that one at `depth 64` —
  the same contradiction, once instead of 64 times (07-C78). A count-based check cannot see it,
  because the count moved the right way. **Read the surviving output's content, not its
  multiplicity.**

- **Before quoting a count, check that each item is a distinct instance.** I wrote "three occurrences" of a
  refused FEN and the number was **one** — the illustrative example *in the rule itself* was already one of
  the three, so quoting it again double-counted one incident. Every item was real; two were the same item.
  That is a different fault from mis-counting a list (07-C71).
- **When my summary line and my raw data disagree, believe the data.** Caught three wrong verdicts; each
  was a wrong comparison, and a summary is a second implementation that gets less review.
- **If a defect should vanish with more budget and it does not, suspect the checker** — and if it does
  vanish with more depth, it was a horizon artefact. One sweep decides which, in either direction.
- **Before calling someone's number wrong, run it on their own sample.** Mine put 29-F45 thirty points
  away and running *their* set reproduced it to the digit — the number was right and the generalisation
  was not.
- **For a side-to-move-relative score under a colour mirror, the invariant is equality, not negation.**
  The tell for a wrong checker: its "asymmetric" pairs share the same sign.
- **A damage table must exclude incomparable pairs.** `mate −12` against `cp −2196` is two losses;
  subtracting them invents ~9,800 cp of damage.

### Can anyone re-check what I claimed?

- **Before citing a library function as your evidence, read what it actually computes.** I said
  `python-chess`'s `is_fifty_moves()` was False on the boards proving 07-F3, in two findings. It
  returns **True** — its body is only `halfmove_clock >= n and any(legal_moves)`, with no test for a
  counter-resetting move (07-C80). My numbers were right because my scripts used
  `is_fifty_moves() and not resets`; **only my prose was wrong, which is the more dangerous case,
  because the data survives scrutiny and the sentence does not.** State the condition in full rather
  than naming a function that approximates it.
- **A change is not verified until it is verified where the next person will apply it.** Both of my
  near-misses were "it worked where I built it": a patch whose switch defaulted to 0 (07-C74), and a
  patch diffed against my own already-patched tree so it could not apply to a pristine one
  (07-C79). Generating a deliverable from a working copy is how that gap is created, and only a
  clean-tree application plus a from-scratch rebuild catches it. The proof of a good patch is not
  that it works for you — it is that the **binary is byte-identical when built anywhere from the
  patch alone.**
- **An exact match to someone's baseline is the fingerprint of having changed nothing.** Replicating
  16-S-F35, my first run reproduced their baseline **to the digit (34/120)** while my treatment arm was
  **identical, case for case** — which felt like two seats measuring the same thing and was the proof the
  treatment had not been applied. **When your treatment arm matches your control arm exactly, do not
  conclude the effect is absent; conclude you have not yet run the experiment** (07-C74). The baseline
  is by construction the unmodified path, so matching it is **not** a check on your build — only a number
  the treatment must move can be that check.
- **Before reporting that a patch did nothing, prove the patch is in the binary — with an observable the
  code path must move.** A patch that ships its own switch (`#ifndef X / #define X 0`) is not applied by
  applying and building it; you compile stock and measure stock against stock. Rebuilt with `-DX=1` the
  same claim gives **120/120, residue zero** (07-C74). **`perft` is the wrong control for a move-order
  patch** — it is precisely what such a patch leaves alone, so it passes on an inert build and reassures
  falsely; the control that must move is **bench nodes, 312866 → 376974.**
- **Regime plus binary is a complete citation; settings alone are half of one.** Nine of my own jobs
  cited settings with no `sha256` — the gap was in the record, not the work, and it is now closed in
  `job65/BINARY_PROVENANCE.md`. **This is the difference between a discrepancy and a mystery**: two seats
  disagreed by ~26× on the same board with the same counters, and because neither named its binary it read
  as a dispute about node accounting and cost a seat a full investigation. With the builds named it was a
  two-minute comparison — one seat's figures matched the PC arm to the digit, the other's matched neither
  (07-C72).
- **A convenient listing is not the tool for the question you asked.** `git ls-files` cannot tell you what
  a branch contains; `git ls-tree -r --name-only origin/<branch>` can.
- **A warning from a harness that has not validated its own input is not a finding.** Five of my controls
  were blind until their own planted fault exposed them.

## Method debts I incurred, recorded so they are not repeated

Five of my controls were initially **blind** and each was caught by its own planted fault, not by me:
the go/stop cycle, the eval-symmetry relation, the SEE oracle, the option surface, and the UBSan
overflow (three attempts). A sixth lesson: a header-planted fault needs every dependent translation unit
recompiled (07-C12), and the legality shortcut lives in `board.hpp`, not `board.cpp` (07-C10). One
false warning I printed came from my own illegal test move, caught with python-chess.

> **A warning from a harness that has not validated its own input is not a finding.**

### Every number in this file was measured under zero machine load, and that is now proven rather than assumed

A loaded machine does not merely slow this engine down — at **full** saturation it searches a ply shallower
and its node count collapses (30-F64). I confirmed the threshold on my own 4-core box with CPU burners
(07-C65):

| busy processes | bestmove | depth | nodes |
|---|---|---|---|
| 0 | `a2a3` | 17 | **362,362** |
| 1 | `a2a3` | 17 | **362,362** |
| 2 | `a2a3` | 17 | **362,362** |
| **4** (all cores) | `a2a3` | **16** | **241,976** |

**0, 1 and 2 hogs are identical to the node; only full saturation costs a ply.** My box read `loadavg 0.10`
with zero `forge` processes whenever these measurements were taken, so **every figure in this file sits in
the 0-hog regime** — the regime this ladder shows is indistinguishable from the ideal. That is the
certification the night's numbers needed and, until this check, did not have.

### 100-position rates cannot order three budgets, or anything else that close

**Two disjoint 100-position samples disagreed about which budget is safest.** Seat 10 measured
`nodes 50000` agreeing with `nodes 250000` on 92/100 positions and recommended 50000 as the cheapest
safe budget; on the **last** 100 positions of the same set I measured **78/100**, with the 20000 budget
agreeing *better* (82/100) — the opposite ordering (07-C42).

Neither measurement is wrong. 24 disagreements against 19, in 100 positions, is well inside binomial
noise. **The lesson is that a rate of that size does not carry a ranking**: if two samples of 100 can
flip the order of two budgets ten percentage points apart, then no 100-position comparison should be
used to choose a default, and any such choice needs a sample large enough that the ordering is stable
under resampling.

This is the fourth number tonight that moved when I enlarged or changed the sample (the fifty-move rate
went 95 % → 30 % → 25 %; the PC20 option table had three of six signs flip between 40 and 200
positions). **The pattern is consistent: small samples produce confident orderings that do not survive
a different sample.** Report a rate with its sample size and say whether it orders anything.

### The mirror invariant, stated once so nobody pays for it again

**For a side-to-move-relative score under a colour mirror, the invariant is EQUALITY, not negation.**
`python-chess`'s `Board.mirror()` swaps colours *and* the side to move. This engine's `eval` and search
scores are reported from the side to move's point of view (07-C9; `src/eval.cpp:509`). So a +255
advantage for White becomes a +255 advantage for Black in the mirror — and Black is the side to move
there — which reads **+255**, not −255.

**The tell that catches a wrong checker:** if the pairs it calls "asymmetric" have the **same sign**
(`orig cp −304` against `mirror cp −301`), the checker is using negation and is wrong. A genuine
asymmetry shows as a gap *within one sign* or as a sign change under equality.

My first version of 07-C41 used negation and reported 4 of 120 pairs symmetric; the correct invariant
gave 7 of 120, and 25 of the first 40 pairs it had failed were carrying the *correct mirrored move*.
This is the trap seat 16 documented in its own C5 ("a negation-based symmetry checker would report a
false 8422 cp difference per position") — **I walked into a trap another seat had already written
down**, which is the strongest argument for reading the other seats' checks before writing one.

**And the residue has a single cause, now confirmed rather than assumed.** The mirror asymmetry looks
like a search property and is entirely a **move-generation-order** artefact: seat 16 canonicalised the
generation order and got 120/120 equal pairs, and I reproduced it — my own harness, my own build,
**34/120 stock against 120/120 canonicalised, residue zero** (07-C74). So the equality invariant above
is the right statement of the property, and any residual asymmetry you measure in node counts is
ordering, not search, until proven otherwise.


## Times

`git log` on the branch is the authority; each job's `stamps.txt` carries a `date -u` read taken at the
time of the run. The most recent commits, newest first, with the times git recorded:

```
e262de1ec  01:10Z  seat 19 fix-side confirmed with exact boundary; is_fifty_moves wording corrected; consistency pass
0cbf014e2  01:08Z  job73 v3: clean-tree verification, and v2 was not shippable
bd6f30613  01:01Z  job73: verifying my own live patch found the same defect in the patch
a1f8a44ca  00:50Z  job72: only ONE of my two faults is live on the PC build
d332b6132  00:50Z  job71: 07-F3/F4 turned from a rate into a mechanical per-position claim
66a974f43  00:48Z  job70: S-F35/S-F37 CONFIRMED (34/120 -> 120/120, residue 0), plus a false refutation
```

**One thing about this file's own timeline worth being explicit about:** the header previously said
"written 2026-11-17T09:35Z", which was a placeholder and is **earlier than the window closes
(10:19Z) but later than the actual writing time** — it was corrected to the real read
(01:10Z) during the final consistency pass. A wrong timestamp in a document whose whole argument is
"record the regime and the binary" would have been a poor joke, so it is noted here rather than
silently fixed.
