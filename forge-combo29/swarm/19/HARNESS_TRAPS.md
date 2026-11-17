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

## The single question that catches all seven

**What would this look like if it were an artifact of my harness rather than a property of the engine?**

Two were caught by the data's shape, one by a `n/a` in my own output, one by identical results for different
settings, one only by another seat's warning. **The cross-checking rule exists because of that last column.**

## See also

`METHOD_INDEX.md` (the four method notes), `NOTE_three_traps.md`, `NOTE_halfmove_window.md`,
`NOTE_pernode_vs_perdepth.md`.
