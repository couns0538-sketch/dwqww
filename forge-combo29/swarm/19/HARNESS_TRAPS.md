# HARNESS TRAPS — one list, from the whole swarm's experience

seat 19 · area 9 · every harness defect found in this run, in one place, with the test that catches each.

The theme: **a harness that answers a different question than the one you asked still produces a plausible
number.** Each entry below produced, or nearly produced, a wrong result that looked real.

**The single sharpest sentence in this document, from family E (trap 15):**
> **An unexecuted branch and a sub-resolution effect look identical in data and are opposite in meaning.**

**Read family E first.** Its three instances were each a case where **more data would have made the answer
worse** — the opposite of the instinct every one of us starts with. The rest of the page is mostly about catching
a number; family E is about knowing when not to collect another one.


**Three families, not fourteen unrelated items.** Every trap below is one of:

| family | traps | the question that catches it |
|---|---|---|
| **A. No search happened** (four disguises) | 1 (no `info` lines), 1b (`nodes 0` + empty PV), 13 (zero in output can't be classified without input), 14 (identical answers from unrelated inputs) | *is the move legal on THAT board, and did a positive node count with a non-empty PV precede it?* |
| **B. A number that is not evidence about what you think** | 10 (counter changes the question), 11 (a maximum does not validate a table), 12 (a zero feels like evidence) | *what would this look like if it were an artifact of my instrument?* |
| **C. Auditing the wrong thing** | 8 (`ls-files` vs `ls-tree`), 9 (committed ≠ currently used) | *did I check the thing I actually meant to check?* |
| **E. The code says why** | 15 (a uniform result is a reason to read the source) — with 5 and 19-F23 as its other instances | *what line does this setting control, and can its guard be true on my inputs?* |
| **D. Harness mechanics** | 2 (`select` on a buffered pipe), 3 (warm state), 4 (malformed `setoption`), 5 (`bench` hardcodes 16 MB), 6 (play-out is not a solver), 7 (oracle missing the halfmove window) | fixed by the specific test in each entry |

**Family A is the one that produces plausible output most reliably** — in every one of the four, the engine prints
a `bestmove` and looks like it answered. Family B is the one that survives longest, because the numbers are
internally consistent.

---

## 1. A terminator during a running search fabricates a move (19-F12 / 19-F25)

**The bug:** sending `quit` (or closing stdin) while a search runs makes the engine print a `bestmove` that is the
**position's first generated move**, with **zero `info` lines**. The search is discarded.

**What it looks like:** `bestmove a2a3` on startpos, instantly. Plausible as an opening choice.

**The tell:** **zero `info depth` lines.** No search ever reported.

**The test:** `printf 'position startpos\ngo depth 12\nquit\n' | forge` → `bestmove a2a3`, no `info`. Then
`printf 'position startpos\ngo depth 12\n' | forge` with stdin held open → `info depth 12 ... nodes 56720`.

**The fix:** read stdout until `bestmove` before sending anything else. **The sub-case that matters:** `go perft`
is **synchronous** and unaffected — `go perft 5` + `quit` still prints `nodes 4865609`.

### 1b. The sibling: `info` lines that exist but describe nothing (19-C25)

**The bug:** a search that never ran can still emit `info depth` lines — with **`nodes 0` and an EMPTY `pv`**.

**Measured** on the base tree at `6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60` with
`go searchmoves e1e8 depth 4` (a drawn-root shortcut):

```
info depth 1 seldepth 1 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 2 seldepth 2 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 3 seldepth 3 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 4 seldepth 4 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
```

Four depth lines, **zero nodes, empty PV** — the engine announcing progress while searching nothing. (On PC r15
the same command gives `mate 1` at 8 nodes with a real PV, which is why the two builds differ here.)

**What it looks like:** a harness that checks *"did a depth line appear?"* reads four depth lines and concludes
the search ran.

**The tell:** a PV that is empty, or `nodes 0`, on a line that claims a depth.

**The test:** assert **`nodes > 0` AND the PV is non-empty** — not the presence of an `info` line. A search that
produced nothing is indistinguishable from a successful one by depth lines alone.

**The relation to trap 1:** trap 1 is *zero* `info` lines; this is *empty* ones. Together they mean the only
reliable evidence of a search is **a positive node count plus a move in the PV**, and that check should be in
every harness that reads engine output.

---

## 2. `select()` on a buffered text pipe is not a timeout (08-N2)

**The bug:** `select([proc.stdout])` then `.readline()`. `readline()` reads ahead into Python's buffer, so
`select` reports "not ready" while complete lines sit in the buffer, and a timeout expires with data available.

**What it looks like:** "the search HANGS" — on a search that answers in 194 ms.

**The tell:** a timeout firing on a case you know is fast.

**The test:** run the timeout mechanism against a search that must return instantly (mate-in-1, depth 1) and prove
it does not fire. Mine: 1.5 ms on two such cases.

**The fix:** a reader thread with a deadline, or `os.read(fd)` on a raw fd — **`os.read` goes straight to the fd
with no Python buffer, so nothing is read ahead.** The distinction is what reads afterwards, not the `select()`.

---

## 3. Warm state between searches (19-R1, and seat 10's 10-F21/F22)

**The bug:** running many positions in one process with nothing between them. The transposition table carries
entries across positions.

**What it looks like:** a full-table replacement rate of 54.7 % of probes that collapses to 0.001 % cold.

**The tell:** a contrast so large it needs a story — and I supplied one instead of checking.

**The test:** run the same sweep with `ucinewgame` before each position and compare the node total. Warm
15,238,023 vs cold 13,925,108.

**The fix:** a fresh process, or `ucinewgame` + `isready` before every position. **`Clear Hash` is NOT cold** — it
gives a third value, deterministically. And note: **`bench` is self-clearing** (`Searcher(16)` + `clear()` before
each position), so multiple `bench` lines in one process are fine — the trap is specific to `go`.

---

## 4. Malformed `setoption` silently not applying

**The bug:** `setoption name Hash 16` instead of `setoption name Hash value 16`. The parser reads `name`, then
looks for the literal token `value`; without it nothing is applied.

**What it looks like:** nothing. The setting silently does not take effect.

**The tell:** **two runs with supposedly different settings giving byte-identical results.** I hit this twice; the
second time the identical counters were the only clue.

**The test:** `isready` after every `setoption` and **scan every answer line** for `unknown option` /
`invalid value`.

**The fix:** the `value` keyword, and read the refusal lines rather than discarding them.

---

## 5. `bench` hardcodes a 16 MB table (19-F37)

**The bug:** `src/uci.cpp:773` builds `forge::Searcher bench_searcher(16)`. The `Hash` option resizes the **UCI**
searcher at line 777 and never reaches the bench searcher.

**What it looks like:** identical counters at Hash 16 / 64 / 256 / 1024 — a "no effect" result that is actually
"no application".

**The tell:** see trap 4 — identical results for different settings.

**The test:** any hash-size conclusion needs a real `go` search, not `bench`.

---

## 6. A play-out is not a solver

**The bug:** playing out an ending against a fallible opponent "wins" positions that are drawn — the opponent
errs, not the position.

**What it looks like:** a win 3/3 on a position where no move forces mate inside the available plies.

**The tell:** the win depends on the opponent's move quality rather than on the position.

**The fix:** exhaustive minimax inside the halfmove window (see trap 7).

---

## 7. An oracle missing the halfmove window (19-C10)

**The bug:** a distance-to-mate solver that ignores the 50-move rule calls a position won when the rules call it
drawn.

**What it looks like:** "win in 23 plies" (fine) or "win in 23" when only 13 remain (wrong).

**The tell:** a known maximum disagreeing — or another seat's example.

**The fix:** `win only if DTM <= 100 - halfmove_counter`.

---

## 10. Two runs differing only in halfmove counter are not the same measurement (19-C22)

**The bug:** comparing scores or node counts across runs whose FENs differ in the halfmove counter.

**Why it is not a detail:** the counter feeds the **fifty-move horizon** and the **rule50 transposition-table
gating**, so a search at counter *c* is solving a **slightly different problem** — not the same problem with a
different budget.

**What it looks like:** seat 25's sweep of `6k1/8/5K2/8/6r1/8/8/8 w`, depth 24, PC20:

| counter | score | nodes |
|---|---|---|
| 0 | mate −16 | 7.6 M |
| **1** | **mate −16** | **15.7 M** |
| 12 | mate −15 | — |
| 50 | mate −19 | — |
| **99** | **cp 0** | **120** (root-draw shortcut) |

- The spread across **0..50 is four moves**, so I was wrong to call the counter's effect "one ply" — that was
  true only of the 0-vs-12 pair I happened to compare.
- **At 99 the answer changes character**: the fifty-move horizon fires and the engine answers `cp 0` in 120 nodes.

**And the broader consequence: identical scores can cost 2x the nodes** (counter 0 vs 1, both mate −16, 7.6 M vs
15.7 M). **So node counts are not a proxy for "the same search happened" when the counter differs.** Any
comparison that assumes equal nodes means equal work is unsound here.

**The tell:** two "identical" positions whose only difference is a counter, giving different answers.

**The test:** hold the counter fixed. If a comparison needs two positions, state both counters and check the
window (`100 − counter`) against the mate distance.

**The fix:** normalise the counter, or treat the run as a different question.

**Same class as warm-vs-cold state (trap 3): both are cases where the engine is solving a different problem than
the one you think you are measuring.**

### The sentence that reconciles two apparently opposite findings

**The counter is inert until the search can reach the horizon.** At **depth 20**, counters 0, 1, 12 and 50 give
*identical* scores at *identical* node counts (232,803) and only 99 differs; at **depth 24** the 2× node swing
appears. So a shallow sweep concludes "the counter does nothing" and a deep sweep concludes "it changes
everything", and **both are true — they are about different depths.** Any counter comparison must state the depth
alongside the counter, or it is reporting a property of its own choice of depth.

---

## 11. Validating a summary statistic does not validate a table (19-R2)

**The bug:** I validated my distance-to-mate solver by checking that its **maximum** DTM matched theory — KQvK
19 plies, KRvK 31 plies — both of which passed exactly. Then I read **individual cells** from the same table and
reported them as facts.

**What it looked like:** an oracle giving `DTM 9` for a position where an independent brute force gives
**5 plies**. Over-stating by 4. And an engine score (`mate +5`) that was **closer to the truth than my own
instrument**.

**Two symptoms that were visible and I did not look at:**
- a **mate-in-1** position returned `dtm = None` — absent from the table entirely;
- a position I queried raised `KeyError` — also absent.

**The tell:** every "over-claim" I measured was **exactly 2 plies**. **A uniform offset across unrelated
positions is a property of the instrument, not the subject.** That is the same tell as a rate too high to
believe.

**The test:** brute-force **one** position and compare it to the table's cell. One position, once. I had a
brute-force routine written for the KQvK validation already.

**The fix:** spot-check individual cells, not just aggregates. Then, and only then, quote cells.

**Consequence when I did check:** 19-F55, 19-F58 and 19-C24 were withdrawn, and 19-C24 had been actively
backwards — I had called another seat's finding "arithmetically impossible" on the strength of a wrong table.

---

## 12. A zero feels like evidence and gets less scrutiny than a percentage (19-C28)

> **The nulls that hide best are the ones phrased as conclusions.**

That is the strongest form of this trap, and it came from auditing my own work (19-C32) — **a mechanical pass
over 58 findings, of which 15 were null-shaped: 4 real absences and 11 my own filter's false alarms.** In that
audit, the ones worded as *results* — "not measurably faster", "no effect", "unchanged", "neutral" — escaped
the Rule 1 question entirely, while the ones worded as *absences* — "0 of 40" — got it immediately.
**The wording decides whether you ask.** A number that looks like zero invites "did you prove you could see one?";
a phrase that looks like a finding invites "what was the effect?" and nobody asks about the instrument.

**The trap:** "**0 of 60**" reads as a strong, clean result — stronger than "10 of 27", which invites argument
about sampling. So the zero gets foregrounded and the percentage gets hedged.

**Why that is backwards:** a zero has a specific failure mode that a positive count does not — **an instrument
that cannot see the thing reports zero.** A harness that fails to detect a deep mate reports *exactly* 0 of 60,
indistinguishable from "no board has the defect". A non-zero count is self-evidently seeing *something*; a zero
might be seeing nothing.

**What I found:** 08-F31's "0 of 60" has **no planted case through its own harness** — its evidence report and
script contain no plant, fake-engine mode, or control run. Seat 08 owns two genuinely good controls elsewhere
(one a `/bin/cat` fake engine that answers `readyok` but never a number), so this is a **coverage gap, not
carelessness** — and the zero is **not thereby wrong**, only "not shown".

**The rule this restates (Opus's Rule 1):** a zero needs a planted case through the **same harness, unchanged**.
That is not bureaucracy — it is the only thing that distinguishes "I looked and found none" from "I could not have
found one".

**Practical form:** when you find yourself more confident about a zero than about a percentage, that is the moment
to check whether the zero has a plant. The confidence is coming from the shape of the number, not the evidence.

### 12b. A zero in EVERY arm means the metric, not the engine (19-C47)

**The plant answers "could the harness have seen one?" It does not answer "could the METRIC have shown one?"**
Those are two different questions, and 12 covers only the first.

**The case (mine, 19-C47).** To test whether raising the self-play budget 2,000 -> 3,000 improves *decision
quality*, I compared each arm's score against a depth-18 reference and counted agreements. Result: **`0 of 8` in
all four arms** — 2k S14, 2k PC20, 3k S14, 3k PC20. I nearly wrote it up as "no budget improves quality".

**Why that reading is empty.** A 2,000-node search *legitimately* disagrees with a depth-18 score. The comparison
could never have returned anything but zero, for any engine, at any setting. **`0 of 8` four times is not four
null results — it is one statement about the instrument: this metric does not discriminate at this budget.**
The engine was never under test.

**The tell is uniformity, and it is the same tell as trap 15.** One arm at `0 of 8` is a candidate null. **Every
arm at the same zero is the metric hitting its floor.** Trap 15 says a uniform *result* means read the code;
12b says a uniform *zero* means replace the measure. A test that returns its floor in every condition is
reporting on its own floor.

**The distinction in one line:** a zero needs a **plant**; a **uniform** zero needs a **better metric**. Applying
Rule 1 to a broken metric just proves the metric is reliably broken.

**The fix that worked:** swap to *move agreement against a depth-16 reference* — a measure with actual headroom —
and it discriminated immediately (5/8, 4/8, 6/8, 4/8). Still too small to settle anything, which is a separate and
honest limit; but no longer vacuous.

### Soft nulls hide better than hard zeros (19-C32)

**A systematic pass over my own 15 null-shaped findings found that the ones phrased as *conclusions* are the ones
that escape scrutiny.**

- **"0 of 40"** announces itself as an absence. It got the Rule 1 question immediately, and I planted it (19-C29).
- **"not measurably faster"** reads like a *finding*. It escaped the question entirely — and when I finally
  audited it, it had no positive control proving the timing could detect a real speedup (19-C31).

**So the shape of the sentence decides whether you ask the question.** A number that looks like zero invites "did
you prove you could see one?"; a phrase that looks like a result invites "what was the effect?" and nobody asks
about the instrument.

**Practical form:** when a null is written as a *conclusion* — "not faster", "no effect", "unchanged", "neutral" —
treat it as a zero and ask for the planted case. **The softer the wording, the more likely it is unplanted.**

**I then applied this to my own worst zero** (19-C29). 19-F54 reported "0 of 40" with no plant — its one
mate-bearing board exercised only the "no defect" path, because the engine *played* the mate. So I built one: on
`6K1/8/1r4k1/8/8/2p5/8/8 b - - 13 186` (18 legal moves, exactly **1** mates), the same scoring code returns
**`False`** for the mating move and **`True`** for a legal non-mating one. **The zero survives — but only because
I checked, and it would have been unshown had I not.**

---

## 13. A zero in an output file cannot be classified without the input (19-C33)

**The trap:** to find aborted searches across 49 branches, sweep committed **output** for `nodes 0` or an empty
PV. Mechanically this works perfectly — it is immune to indentation and to interleaved `readyok` lines.

**Why it still cannot produce a defect count:** **`nodes 0` with an empty PV is the engine's *correct* answer on
any drawn or terminal root.** A drawn root and an aborted search are **byte-identical in the output**. Verified:
seat 21's `asan_raw_031.txt` contains `info depth 1 ... score cp 0 nodes 0 ... pv` (empty) then a real
`bestmove` — on positions the seat deliberately constructed, because **it is the area-1 seat that studies exactly
those**.

**The tell:** a sweep whose largest count belongs to the seat that *specialises* in the behaviour you are
flagging. Seat 21's 469 of 6,770 claimed searches were the majority of the whole sweep, and it is the
terminal-position seat.

**The test:** replay the position. For each zero-node search, ask whether its root is drawn or terminal. If it is,
the zero is correct.

**The fix:** the distinguishing information is **the position, not the output**. A usable version needs either
the positions replayed or the driver's own command stream.

**Three sweeps, three instructive failures** (all kept in the record):
1. **input files** (19-C13) — flags *suspicion*, not defect; and "committed" is not "currently used" (19-C21);
2. **output files, zero `info` lines** (19-C14) — broke on indentation, then on `bestmove`-block boundaries
   (19-C16);
3. **output files, zero node counts** (19-C33) — mechanically sound, semantically blind.

**A sweep of outputs can tell you where to look. Only a replay can tell you what you found.**

---

## 14. Identical answers from unrelated inputs mean the INPUT is wrong (19-C39)

**The trap:** comparing three different boards and getting the same move from all three.

**What happened:** building FENs by appending `- 0 1` to a string that already contained a counter produced an
**invalid FEN** for all three cases. The engine refused each one, kept its previous position (startpos), and
answered `e2e4` every time.

**The tell, and it is decisive:** the third board was a **K+P versus K** ending. `e2e4` is not even a legal move
there. **Three unrelated positions answering identically is not a coincidence — it is a property of the input.**

**Why this matters beyond FENs:** the same shape appears in several other traps:
- trap 1 — *no* `info` lines at all (the search never ran);
- trap 1b — `info` lines with `nodes 0` and an empty PV (a drawn-root shortcut);
- a refused `position fen` leaving the **previous** board in place (19-C21's neighbour, 21-F2);
- **this** — the refused FEN's *previous board* producing a plausible-looking move.

**All four are "the engine answered a question you did not ask."** The shared defence: **when results across
independent inputs agree more than they should, suspect the input before the engine.** A per-input sanity check
(the move must be legal on *that* board) catches every one of them in a line.

**The test:** for each row of a multi-board comparison, assert the engine's move is legal in that row's position.
My severity script now does exactly that.

---

## 15. A uniform result is a reason to READ THE CODE, not to sample more (19-C42)

**The trap:** an option, setting or condition that changes **nothing** across every input. The reflex is to call it
"an effect below resolution" and plan a bigger experiment.

**Three times tonight that reflex was wrong and the source said why:**

| uniform result | what the code said |
|---|---|
| `MateAlphaGuard` exactly **1.000** on four unrelated positions | it gates futility pruning only when **`alpha` is a MATE score** (`search.cpp:2134, 2159`) — an **unexecuted branch**, so it will keep returning 1.000 forever |
| **identical** counters at Hash 16 / 64 / 256 / 1024 (19-F37) | `bench` builds its own `Searcher(16)`; the `Hash` option never reaches it |
| five `bench 13` lines in one process all giving **862,329** (19-F23) | `bench` calls `clear()` before each position, so it is self-clearing |

**In all three the uniform number was correct and the *interpretation* would have been wrong.** A bigger sample
would have confirmed the uniformity and taught nothing.

**The tell:** a result that is **exactly** the same — to the last digit, not approximately — across inputs that
should differ.

**The test:** find the line of code the setting controls. If the condition guarding it cannot be true on your
inputs, you have your answer and no experiment will improve it.

**The fix:** for any uniform result, spend the next two minutes in the source before spending twenty in the sample.
**An unexecuted branch and a sub-resolution effect look identical in data and are opposite in meaning.**

---

## The single question that catches all eleven

**What would this look like if it were an artifact of my harness rather than a property of the engine?**

**The scoreline, honestly:** two were caught by the data's shape, one by a `n/a` in my own output, one by
identical results for different settings, one by measuring the return time on a fast case, **one by noticing a
uniform 2-ply offset and suspecting my own instrument rather than the engine** (trap 11) — and **four only by
another seat's correction** (traps 8 and 9 from seat 17; trap 10 from seat 25; and the *shape* of trap 11 first
came from seat 05's finding I was trying to check). **That distribution is the argument for the cross-checking
rule, quantified: four of the eleven defects here would not have been found by the seat that made them.**

**The closing sentence, which is the whole of Rule 1 in one line:**
> **A planted case is the only thing that distinguishes "I looked and found none" from "I could not have found
> one".**

**And the one check that belongs in every harness, from traps 1 and 1b together:** a search happened only if
**`nodes > 0` and the PV is non-empty**. Neither "an `info` line appeared" nor "a `bestmove` arrived" is
sufficient on this engine.

## See also

`METHOD_INDEX.md` (the four method notes), `NOTE_three_traps.md`, `NOTE_halfmove_window.md`,
`NOTE_pernode_vs_perdepth.md`.

---

## 8. `git ls-files` is not the tool for auditing a branch (19-C21)

**The bug:** concluding a file does not exist on a branch because `git ls-files | grep X` is empty. **`git
ls-files` lists the index of the tree you are in** — your own checkout — not another branch's contents.

**What it looks like:** two seats both correct and disagreeing. Seat 17's `ls-files | grep -i unbounded` was empty
(it is not in its working tree's index); the file **is** on its branch at `bb0b312ce`.

**The tell:** a "does not exist" that is contradicted by someone else's `git show`.

**The test:** `git ls-tree -r --name-only origin/<branch> | grep -i <name>`.

**The fix:** `ls-tree` on the ref for "what does this branch contain", `ls-files` for "what is in my working copy".
Different questions.

## 9. "Committed" is not "currently used" (19-C21)

**The bug:** an audit that finds a defect in a committed file and reports the seat as "EXPOSED", when the file may
be superseded history that the seat no longer runs.

**What it looks like:** a true finding about a file, presented as a claim about a harness.

**The tell:** the finding does not say which file the seat *currently* drives its measurements with.

**The test:** find the seat's current driver (the one its newest report cites) and check that, not the folder.

**The fix:** word the finding as "file X contains Y", not "seat N is exposed", unless you have confirmed X is in
current use. My own `profR` scripts are exactly this kind of superseded history.
