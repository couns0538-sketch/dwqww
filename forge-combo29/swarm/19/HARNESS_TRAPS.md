# HARNESS TRAPS — one list, from the whole swarm's experience

seat 19 · area 9 · every harness defect found in this run, in one place, with the test that catches each.

The theme: **a harness that answers a different question than the one you asked still produces a plausible
number.** Each entry below produced, or nearly produced, a wrong result that looked real.

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

---

## The single question that catches all ten

**What would this look like if it were an artifact of my harness rather than a property of the engine?**

**The scoreline, honestly:** two were caught by the data's shape, one by a `n/a` in my own output, one by
identical results for different settings, one by measuring the return time on a fast case — and **three only by
another seat's correction** (trap 8 and 9 from seat 17's reply to my audit; trap 10 from seat 25's counter
sweep). **That distribution is the argument for the cross-checking rule, quantified: three of the ten defects
here would not have been found by the seat that made them.**

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
