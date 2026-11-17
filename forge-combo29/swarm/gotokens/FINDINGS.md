# The malformed-`go` matrix — what a harness author needs

**Seat:** gotokens. **Base:** `6b98f2170a3210e71beed04bbd2553972c253ed7`, `forge-combo29`.
**Branch:** `swarm/gotokens`. Every figure here is from this build, measured by
this seat; nothing is quoted from another seat's run.

**Build identity.** `sha256(forge) = e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
— the same binary seat 29 recorded for the base, so these numbers and theirs are
the same artifact. All four pins MATCH: `bench 11` 312,866 · `bench 13` 862,329 ·
`bench 16` 3,024,920 · `perft 5` 4,865,609.

---

## The answer in eight lines

1. **Thirteen keywords, five distinct failure modes.** Every malformed form is
   silent. Which mode you get depends on the keyword, not on the malformedness.
   The five: **1-ply search** (`depth`, and any clock that fails to 0),
   **"no search at all"** (`nodes 0`, `softnodes 0`), **unbounded**
   (`nodes`, `softnodes`, `mate`, `movestogo`, and every clock for the wrong
   side), **a real but arbitrary short search** (`movetime` — non-reproducible,
   §3), and **a book move** (any of the above that leaves a clock in place on a
   book-eligible position, §4).
2. **The two unbounded families are wider than reported.** Not just `nodes` and
   `mate`: **`softnodes`, `movestogo`, `btime`, `winc`, `binc` and bare `go` are
   unbounded too**, and `wtime`/`btime`/`winc`/`binc` are unbounded when the
   keyword names the side that is NOT to move.
3. **A malformed value does not merely fail to set a limit — it can ERASE a
   well-formed limit on a different keyword.** `go nodes depth 5` is unbounded,
   because `nodes` eats the literal token `depth` as its value and `5` is then a
   stray. **Every individual token in that command is well-formed.**
4. **The sharpest hazard is not a malformed value at all: it is a `go` line with
   no limit keyword whatsoever.** Bare `go`, `go foo`, `go Depth 5` and
   `go depth=5` are all `go infinite`. A misspelled keyword is unbounded, not
   defaulted.
5. **`go nodes abc` is NOT `go infinite`.** Same shape on a real board (no
   `bestmove` in 120 s), different termination class: `nodes abc` **returns on
   its own at the depth-64 clamp** on a small board (46 s, `c1c3`), while
   `go infinite` **never returns** without `stop`. The earlier "identical"
   claim is right only inside a time window.
6. **`go movetime 0` is not reproducible.** 3 distinct outcomes in 30 fresh
   processes (depth 5 / depth 4 / depth 3, two different bestmoves). This is a
   race between the root time check and search setup, not a default.
7. **The book is detectable — but only if you read `info string`.** A
   book-answered search emits `info string book move <m>` before `bestmove`.
   A harness that filters for `info depth` sees zero lines and **cannot tell a
   book reply from the `go nodes 0` no-search path**, which also emits zero
   `info depth` lines and a legal bestmove. **The book move is also random
   between processes** (2 distinct moves in 24 runs), so it must never be
   asserted as a fixed value.
8. **The client-side rule is five assertions on the `go` string plus one on the
   harness, and one of them is "send a limit you can name".** Details in §6.

---

## Method (and the three harness bugs this seat had to fix first)

Every cell is a **fresh process**, `OwnBook` set explicitly, `Hash 16`,
`Threads 1`, stdin held open until `bestmove` arrives, 20 s cap (120 s for the
boundedness probes). Board: `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1`
(midgame, white to move, 36 legal moves), except the book section (startpos) and
the boundedness probes (K+R v K).

**Three harness defects were found and fixed here, and they are the reason the
first pass is not the published pass:**

- **A bare FEN is not a position.** `position <fen>` without the `fen` keyword
  is an unknown position TYPE, silently ignored, previous board kept (trap 3ab).
  My first scan of twelve candidate boards measured **startpos twelve times**
  and returned one identical row per board. The fix is a wrapper that prefixes
  `fen` and a **setup assertion** (`scripts/go_probe.py: as_position_command`,
  `expect_move`).
- **A truncation helper that duplicates its input.** Reporting an unbounded
  cell's wire as `lines[:12] + lines[-12:]` concatenates the whole list with
  itself whenever the list is short. It made `go infinite depth 5` look like it
  emitted a **doubled depth ladder and two `bestmove` lines**. The engine sends
  neither; a direct run shows one ladder, one `bestmove`. Fixed in
  `_head_tail()`, which is why that function exists as a function.
- **`wait_for` scanning from index 0.** A `readyok` from setup satisfied the
  wait for the next command's `readyok`, moving the measurement mark. Now every
  wait passes the mark it is waiting past.

**One deliberate error is kept in the record.** The first `searchmoves` block
used `e2e4` as its "valid" control on a board whose e-pawn is already on e4, so
all eight cells exercised the all-illegal path (`keywords.jsonl`, rows 70-75).
The corrected pass is `searchmoves.jsonl`; the wrong one is not deleted, because
a table whose control was illegal is exactly the kind of thing that should stay
visible.

**`go bench N` prints nothing and exits 0** — confirmed; `bench 11` must go over
stdin as a UCI command. All pins above were taken that way.

---

## 1. Keyword × malformed-form matrix

`parse_limits` is `uci.cpp:80-135` on this base. Cell contents are
**depth / nodes / bestmove**; `CAP` means no `bestmove` within 20 s;
`NOINFO` means it returned with zero `info depth` lines. Full raw rows in
`evidence/keywords.jsonl` and `evidence/keywords.md`.

### Numeric keywords

| keyword | no value | `abc` | `-1` | 2^63 | 2^64 | `0` | valid control |
|---|---|---|---|---|---|---|---|
| `depth` | 1/42/`e1g1` | 1/42/`e1g1` | 1/42/`e1g1` | 1/42/`e1g1` | n/a | 1/42/`e1g1` | **5/818/`a2a3`** |
| `nodes` | **CAP** | **CAP** | **CAP** | **CAP** | **CAP** | NOINFO/`a2a3` | 12/38,459/`e1g1` |
| `softnodes` | **CAP** | **CAP** | **CAP** | **CAP** | **CAP** | NOINFO/`a2a3` | 13/84,245/`e1g1` |
| `movetime` | 4/302/`e1g1` ⚠ | 5/818/`a2a3` | 5/818/`a2a3` | **CAP** (§2d) | n/a | 3/174/`e1g1` ⚠ | 13/84,245/`e1g1` |
| `movestogo` | **CAP** | **CAP** | **CAP** | **CAP** | n/a | **CAP** | **CAP (20)** |
| `wtime` | 1/42/`e1g1` | 1/42/`e1g1` | 1/42/`e1g1` | **CAP** | n/a | 1/42/`e1g1` | 13/84,245/`e1g1` |
| `btime` | **CAP** | **CAP** | **CAP** | **CAP** | n/a | **CAP** | **CAP (1000)** |
| `winc` | **CAP** | **CAP** | **CAP** | **CAP** | n/a | **CAP** | **CAP (100)** |
| `binc` | **CAP** | **CAP** | **CAP** | **CAP** | n/a | **CAP** | **CAP (100)** |
| `mate` | **CAP** | **CAP** | **CAP** | **CAP** | n/a | **CAP** | 5/53,074/`e1g1` (3) |

Read the `btime`/`winc`/`binc` rows carefully: **their valid controls are also
CAP.** That is not a malformedness result — on a white-to-move board those
keywords name the wrong side, so they set nothing and the search has no clock.
The keyword is well-formed and still leaves the search unbounded (§2).

**⚠ marks a cell whose value is NOT reproducible.** The `movetime` row's single
observations come from the 0-ms race in §3 and must not be read as defaults; the
distribution is 27/2/1 across three outcomes for `go movetime 0`. Every other
cell in this table repeated identically where it was repeated (16 runs per form
in `evidence/repeatability.json`).

### Flag keywords

| keyword | form | result |
|---|---|---|
| `infinite` | `go infinite` | **CAP** (by definition) |
| `infinite` | `go infinite abc` | **CAP** — junk token ignored |
| `infinite` | `go infinite depth 5` | depth 5 ladder completes, then **blocks** — depth still bounds the search, but `infinite` suppresses the `bestmove` until `stop` |
| `ponder` | `go ponder` | **CAP** — waits for `ponderhit`/`stop` |
| `ponder` | `go ponder abc` | **CAP** |
| `ponder` | `go ponder wtime 1000` | **CAP** — `ponder` suppresses the clock rather than being bounded by it |

### `searchmoves` (corrected pass, `evidence/searchmoves.jsonl`)

| form | result |
|---|---|
| `go searchmoves` (nothing) | `0000`, 64 lines, 0 nodes, `info string` |
| `go searchmoves abc` | identical |
| `go searchmoves a7a8` (illegal) | identical |
| `go searchmoves d2d4` (LEGAL) | **CAP — unbounded.** A restriction is not a limit |
| `go searchmoves d2d4 depth 8` | 8/702/`d2d4` — depth binds |
| `go searchmoves d2d4 a7a8` (mixed) | **CAP**, silently restricted to `d2d4` — no diagnostic |
| `go searchmoves abc depth 8` | `0000`, 8 lines, 0 nodes |
| `go searchmoves d2d4 e1g1 depth 4` | 4/64/`e1g1` — two legal moves, searches both |

`go searchmoves <legal>` with no other limit is **unbounded**. That is a
plausible harness idiom ("just this move, think as long as you like") that
never returns.

---

## 2. Which combinations are unbounded

This is the part the per-keyword matrix cannot see, and it is where the danger
actually is.

### 2a. A malformed keyword ERASES a well-formed limit on another keyword

| command | result | what happened |
|---|---|---|
| `go nodes depth 5` | **CAP** | `nodes` eats the token `depth` as its value; `5` is stray. **No limit at all** |
| `go mate depth 5` | **CAP** | same shape through `read_int` → `mate 0` |
| `go softnodes depth 5` | **CAP** | same |
| `go movestogo depth 5` | **CAP** | same |
| `go wtime depth 5` | 1/42/`e1g1` | `wtime` eats `depth`; `depth 5` never happens |
| `go movetime depth 5` | 3/174/`e1g1` | `movetime` eats `depth`; 0-ms race (§3) |
| `go depth nodes 50000` | 1/42/`e1g1` | `depth` takes `nodes` as its value → 1 ply |

**The mechanism is one line of the parser.** `read_int` takes its value with
`tokens[i++]` at `uci.cpp:91` *before* `from_chars` decides it was not a number;
`read_clock` does the same at `:101`; and the `nodes` branch at `:106`. **Each
advances the index unconditionally, so a keyword with no numeric value consumes
the next keyword.** `go nodes depth 5` therefore parses as: `nodes` takes
`depth` (`:106`), fails (`:109`), sets no limit; `5` is a stray token matching no
keyword. So "the caller wrote a good `depth 5`" and "the search had no limit"
are the same command line.

### 2b. A bad value beside a good value: the good one usually still binds

| command | result | verdict |
|---|---|---|
| `go depth 5 nodes abc` | 5/818/`a2a3` | depth binds; the bad node budget is simply absent |
| `go nodes abc movetime 100` | 13/84,245 | movetime binds |
| `go nodes abc mate 3` | 5/53,074 | mate binds |
| `go depth 5 softnodes abc` | 5/818 | depth binds |
| `go wtime 1000 nodes abc` | 13/84,245 | clock binds |
| `go movestogo abc wtime 1000` | 19/665,334 | clock binds |
| `go depth 5 mate abc` | 5/818 | depth binds |
| **`go depth abc nodes 50000`** | **1/42/`e1g1`** | **the 1-ply depth still applies** — the node budget never gets used because depth 1 finishes first |
| **`go depth 5 wtime abc`** | **1/42/`e1g1`** | **a failed clock is a 0-ms clock, and it CRUSHES depth 5** |
| `go depth 5 wtime 0` | 1/42/`e1g1` | same, written out |
| **`go depth 5 nodes 0`** | **NOINFO/`a2a3`** | **an explicit `nodes 0` overrides depth** |

So: a malformed *node* limit is harmless when a good limit exists. A malformed
*clock* is not — `read_clock` fails to **0**, and 0 ms is a limit that binds
harder than anything else on the line. **`go depth 5 wtime abc` is a 1-ply
search, not a depth-5 search.** And **`go depth 5 nodes 0` returns zero info
lines and the first legal move** — a caller who wrote a depth gets no search.

### 2c. Unbounded on a real board, depth-clamped on a small one

`evidence/boundedness.json`, 120 s cap, measured on two boards:

| command | K+R v K (small) | middlegame |
|---|---|---|
| `go nodes abc` | **returns**, 46 s, depth 64, `c1c3` | CAP at 120 s (depth 36) |
| `go mate abc` | **returns**, 47 s, depth 64, `c1c3` | CAP at 120 s (depth 36) |
| `go nodes` | **returns**, 48 s, depth 64, `c1c3` | CAP at 120 s (depth 37) |
| `go infinite` | **never returns** (120 s) | never returns |

**So the precise claim is: these forms apply no limit, and the only thing that
ends them is the depth-64 clamp.** On a middlegame that clamp is unreachable in
any practical budget, so they behave as `go infinite`. **`go infinite` is a
different thing again: it reaches the clamp and then blocks waiting for `stop`,
so it returns only when the caller stops it.** The earlier "`go nodes abc` is
`go infinite`, identical depth ladder" claim is true **within a window** and
false as a statement about termination — the two are distinguishable on a small
board, and a harness author relying on "it will eventually come back" is relying
on something that holds for `nodes abc` and not for `infinite`.

### 2d. A huge value is also "no practical limit", by a different route

Worth separating because it is the same table symbol (`CAP`) for the opposite
reason. `parse_clock_ms` **clamps** an over-large magnitude to `kMaxClockMs`
rather than rejecting it (`uci_clock.hpp`, `result_out_of_range` branch), so:

| command | on middlegame, 20 s | on K+R v K, 90 s |
|---|---|---|
| `go wtime 9223372036854775808` | CAP (climbing) | **returns, 45.6 s, depth 64, `c1c3`** |
| `go movetime 9223372036854775808` | CAP (climbing) | **returns, 45.3 s, depth 64, `c1c3`** |

**A huge clock is a valid huge clock, not a dropped one** — the limit is set,
it is just ~1.1 million years. **A malformed clock is 0, which is the opposite
extreme.** Both appear as `CAP` on a real board, and a harness cannot tell them
apart from the wire alone. That is a reason to validate before sending, not a
reason to guess after.

---

## 3. `go movetime 0` is a race, not a default

`go movetime 0`, `go movetime abc` and `go movetime -1` all reach
`limits.movetime_ms == 0`; `search.cpp:2192` turns that into
`hard_limit_ms_ = max(1, 0 - 10) = 1`, and the root check
`elapsed_ms() >= hard_limit_ms_` at `search.cpp:2320` then races search setup.
(There is a second reader of the same field in `should_stop_with`,
`search.cpp:1285-1288`.) **Three forms, one field value, and the value is 1 ms —
which is short enough that whether the root check fires before or after setup
decides the whole shape of the answer.**

`evidence/movetime_zero_interleaved.json`, **30 fresh processes per arm,
interleaved** so machine load cannot masquerade as a form difference:

| arm | distinct outcomes | distribution |
|---|---|---|
| `go movetime 0` | **3** | 27× depth 5/818/`a2a3`, 2× depth 3/174/`e1g1`, 1× depth 4/302/`e1g1` |
| `go movetime abc` | 2 | 29× depth 5/818/`a2a3`, 1× depth 4/302/`e1g1` |
| `go movetime 1` | 1 | 30× depth 5/818/`a2a3` |

`go movetime -1` is not in that interleaved run, but `evidence/keywords.jsonl`
and `evidence/repeatability.json` record it 17 times: **17 of 17 at depth
5/818/`a2a3`**, the modal outcome. So the three arms that set the same field are
modal-identical and differ only in how often they miss the mode — **and that is
the point: the distribution, not the mode, is the measurement.**

**Two forms that set the identical field value produce different
distributions, and one of them is not stable at all.** Any single cell in a
matrix for `movetime 0` is a coin flip presented as a fact — the first pass of
this very table recorded depth 3 for `go movetime 0`, the second recorded depth
5. **Report the distribution or do not report the cell.**

Also note `go movetime 0` is *not* "stops at once": the most likely outcome is a
**full depth-5 search** taking ~2 ms, because the 1-ms check is evaluated at
nodes that land before it fires. Only the `NOINFO` outcome (2 of 16 in an
earlier block) is the "stopped at once" shape, and it is the *minority*.

---

## 4. The book interaction

The seat found that on startpos with `OwnBook true`, `go movetime abc` returns
`e2e4` with zero `info` lines, which looks like a default search and is the book.
**Confirmed — and the case is wider than that: every malformed form that leaves
a clock in place reaches the book.**

`evidence/book.jsonl`, startpos, `OwnBook true`. **The book move itself is
RANDOM between processes** — `book_rng` is seeded from
`steady_clock::now()` (`uci.cpp:190-192`), so `go wtime 1000` on startpos gives
`e2e4` 14 times and `c2c4` 10 times in 24 fresh processes. **Every book row
below is therefore cited by its wire shape, not by its move**; the move column
shows what one run gave, and a harness must not assert on it.

| command | one observed result | book? |
|---|---|---|
| `go wtime 1000` | `e2e4`/or `c2c4`, 0 lines, `info string book move …` | **YES** |
| `go movetime abc` | `c2c4`, 0 lines, book string | **YES** |
| `go movetime 0` | `c2c4`, 0 lines, book string | **YES** |
| `go wtime abc` | `c2c4`, 0 lines, book string | **YES** |
| `go movetime 100` | `e2e4`, 0 lines, book string | **YES** |
| `go movetime abc depth 5` | `e2e4`, 0 lines, book string | **YES** — depth 5 beside it does not stop the book |
| `go btime 1000` (wrong side) | **CAP** — no clock, so no book | no |
| `go depth abc` | 1/26/`d2d4`, real search | no |
| `go depth 5` | 5/1,001/`c2c4` | no |
| `go nodes abc` | **CAP** | no |
| `go mate abc` | **CAP** | no |
| `go searchmoves e2e4 wtime 1000` | 14/41,260/`e2e4` | no — restriction disables book |
| `go infinite wtime 1000` | **CAP** | no |
| `go ponder wtime 1000` | **CAP** | no |

**The rule is the `game_search` predicate at `uci.cpp:525-527`, not the
malformedness:** book requires a clock *or* movetime that is `>= 0`, and no
`infinite`, no `ponder`, no `searchmoves`, and `mate_moves == 0`. A malformed
clock parses to **0**, and **0 is `>= 0`** — so the malformed clock is not
merely "still a game search", it is *more* eligible for the book than a valid
one with `mate` beside it.

**And the book is visible on the wire.** My earlier expectation that it was not:

```
info string book move c2c4
bestmove c2c4
```

**A harness that greps for `info depth` cannot see this, and cannot distinguish
it from `go nodes 0`,** which emits:

```
bestmove a2a3
```

with no `info string` at all. **Two paths, both zero `info depth` lines, both a
legal move, and the ONLY discriminator is the `info string book move` line.**
That is the finding: the book is not silent, but it is silent *to the reader
trap 1 and trap 21 tell you to build* — the one that waits for `info depth`.

**And the book is nondeterministic, which is a second reason not to read it as a
search result.** `uci.cpp:161-162` seeds the book RNG from the wall clock, so the
same command returns different opening moves in different processes. Measured:
`go wtime 1000` on startpos, 24 fresh processes → **2 distinct bestmoves**
(`c2c4` 14×, `e2e4` 10×), **every one carrying the `info string book move`
line** (`evidence/book_randomness.json`). A harness comparing two arms and
seeing different bestmoves cannot tell a book-randomness difference from an
engine difference, **and both arms had `info depth` count 0, so the usual "it
searched differently" reading is unavailable.**

---

## 5. Forms outside the seat's list

`evidence/extra.jsonl`:

| command | result | note |
|---|---|---|
| **`go`** (nothing) | **CAP** | **no limit keyword at all → unbounded** |
| **`go foo`** | **CAP** | unknown keyword ignored → unbounded |
| **`go depht 5`** | **CAP** | typo → unknown token → unbounded |
| `go wtime 1000 depht 5` | 13/84,245 | typo harmless when a clock exists |
| **`go Depth 5`** | **CAP** | wrong case → unbounded |
| **`go depth=5`** | **CAP** | shell-style `=` → unbounded |
| `go depth 10 depth 3` | 3/174 | last wins |
| `go nodes 50000 nodes abc` | 12/38,459 | **first survives** (see below) |
| `go xyz depth 5` | 5/818 | junk before a keyword is skipped |
| `go depth 5 xyz` | 5/818 | junk after a keyword is skipped |
| `go depth 5.5` | 1/42 | not an integer |
| `go depth 0x10` | 1/42 | not decimal |
| `go depth +5` | 1/42 | `read_int` rejects `+` (unlike `read_clock`) |
| `go depth 5 0` | 5/818 | stray token |
| `go movetime 1` | 5/818 (15 of 16) | **race-affected** — see §3 for the 2-outcome distribution |

**Bare `go` being `go infinite` is the most likely real harness bug in this
whole document** — it does not require a malformed value, an overflow, or an
unusual keyword. A harness that builds a command string from a config object
and drops an empty limit set sends `go` and hangs.

### Last-wins is asymmetric

`evidence/lastwins.jsonl`:

| command | result | |
|---|---|---|
| `go nodes 50000 nodes abc` | 12/38,459 | **first budget survives** — a failed parse does not write |
| `go nodes 50000 nodes 0` | **NOINFO** | but an explicit 0 does |
| `go depth 8 depth abc` | **1/42** | **a malformed second value destroys depth 8** |
| `go depth 8 depth 0` | **1/42** | same for an explicit 0 |
| `go wtime 2000 wtime abc` | **1/42** | clock destroyed |
| `go movetime 200 movetime abc` | 5/818 | movetime destroyed |
| `go mate 2 mate abc` | **CAP** | mate destroyed → 0 → unbounded |

**A repeated keyword behaves differently by keyword**: `nodes` keeps the first
good value when the second is unparseable, while `depth`, `mate` and the clocks
overwrite the good value with 0. "Last wins" is not a rule this parser has.

---

## 6. The client-side rule

Given only what UCI promises — nothing about this engine — a harness that types
`go` must validate its own token string before sending it. **Five assertions on
the string (A1-A5) plus one on the harness (A6)**, each named with the failure it
prevents. A6 is stated separately because it is not a property of the `go` line
at all — it is the only defence for the case where the string is valid and the
engine still does not answer (`go infinite`, `go ponder`).

### A1. Every limit keyword in your string has a value, the value is a plain non-negative decimal integer, and it is inside the keyword's usable range.

> For each token in `depth nodes softnodes movetime movestogo mate wtime btime winc binc`, assert the next token exists and `re.fullmatch(r'[0-9]+', next)` — **no sign, no `+`, no `0x`, no `.`** — then assert the range: `depth` in 1..64, `mate` in 1..32, `movestogo` in 1..50, `nodes`/`softnodes` in 1..2^63-1, clocks in 0..2^63-1. For `infinite` and `ponder`, assert nothing follows that you expected to be a value.

**Prevents:** the whole unbounded family — `go nodes`, `go nodes abc`,
`go mate abc`, `go softnodes abc`. Also prevents *keyword-eating* (§2a), where
`go nodes depth 5` is unbounded with every token individually well-formed: the
assertion catches it because the token after `nodes` is not a number.

**The range half is not decoration, and the measured rows are why:**

| value you might send | what the engine does | what asserting the range prevents |
|---|---|---|
| `depth -1` | clamped to **depth 1**, 42 nodes | a 1-ply "result" where you asked for depth |
| `depth 0` | clamped to **depth 1** | same |
| `depth 2^63` | `read_int` fails → 0 → **depth 1** | same |
| `movestogo 0` | `max(1, 0)` = 1, and no clock → **unbounded** | a hang |
| `mate 0` | `mate 0` = no mate limit → **unbounded** | a hang |
| `nodes 0` | **returns with zero info lines** and the first legal move | a fabricated result |
| `wtime 2^63` | clamps to a **valid** ~1.1-million-year clock | a hang that looks like a slow search |

**A permissive `-?\d+` check passes six of those seven.** Malformedness is not
the only thing to validate; **a value the engine accepts and then reinterprets
is the same hazard with a cleaner parser.**

### A2. At least one of `depth`, `nodes`, `movetime`, `wtime`/`btime` (for the side to move), `mate`, or `searchmoves`-plus-a-limit is present and well-formed.

> Assert `("depth" in toks) or ("nodes" in toks and is_int(nodes)) or ("movetime" in toks and is_int(movetime)) or (clock_for_side_to_move in toks and is_int(...)) or ("mate" in toks and int(mate)>0)`. `infinite` and `ponder` count only if you intend to send `stop`.

**Prevents:** bare `go`, `go foo`, `go depht 5`, `go Depth 5`, `go depth=5` — all
`go infinite` (§5). Also catches `go movestogo 20` and `go btime 1000` on a
white-to-move board, where the keyword is **valid** and still sets no limit.

### A3. If you sent a node budget, assert the reply's node count is under it; if you sent a depth, assert the last reported depth EQUALS it.

> `assert last_info_nodes <= requested_nodes` (for `softnodes`, allow the
> iteration-boundary overshoot up to 4×) and
> `assert last_info_depth == requested_depth`, unless the search was stopped
> early by a clock, `stop`, or a mate score — in which case record it as
> **cut short** rather than as a completed fixed-depth search.

**Prevents:** silently accepting a search that did not do what you asked. This is
**the assertion that would have caught `go depth 5 wtime abc`**: it returns depth
1, correctly, because the failed clock is a 0-ms clock. **A `<=` check passes it**
— depth 1 really is at most 5 — so the strength has to be `==` plus an explicit
not-cut-short condition. A `<=` depth check is a check that cannot fire on the
exact case this table is about.

### A4. Treat zero `info depth` lines as "no search happened", and require a reason.

> If `info depth` count is 0, then **assert one of**: a `info string book move`
> line, or the node budget was explicitly 0, or the position is terminal.

**Prevents:** counting a book reply as a search result, and counting the
`nodes 0` no-op as one. These are the two zero-`info-depth` paths, they look
identical to a reader that filters for `info depth`, and **only the `info string
book move` line separates them** (§4). This is the assertion that makes trap 21
("a reader that waits for `info depth` deadlocks") into something you detect
rather than something that hangs you. **It also tells you not to compare the
bestmove against another arm:** the book move is random between processes, so a
book row's move is not a measurement of anything.

### A5. `searchmoves` is not a limit: if you restrict the root, you must also send a budget, and you must intersect your move list with the legal move set yourself.

> Assert a limit (A2) whenever `searchmoves` is present. Assert every move in
> your list is legal in the position you are about to send.

**Prevents:** `go searchmoves d2d4` hanging forever (§1), and prevents relying on
the engine to reject a bad restriction: a **mixed** list silently drops the
illegal move with no diagnostic (re-confirmed here —
`go searchmoves d2d4 a7a8` behaves exactly like `go searchmoves d2d4`), so the
check has to be client-side.

### And one assertion about the harness, not the string

**A6. Every read has a deadline, and a missed deadline is a reported failure, not a retry.**

> `bestmove` must arrive within `min(your_budget * k, hard_cap)`. On timeout:
> send `stop`, record the cell as `CAPPED`, and **do not record its depth or
> nodes as a result**.

**Prevents:** the failure this seat's own table would have produced — a capped
cell and a returned cell are different facts, and a depth column measured under
a timeout is a column of the harness's patience.

---

## 7. What this seat did not establish

Stated so it is not mistaken for a clean bill:

- **One build, one CPU.** Everything is `6b98f217` on this host. I did not
  measure the PC20 build, so I cannot say which of these are base-only. On the
  evidence of §1b ("all four are present on the PC build as well"), I would
  expect none to be, but **I did not check.**
- **One board for the numeric matrix.** Node counts are position-dependent:
  the seat's `go depth 5` → 896 nodes and mine → 818 on a different midgame.
  **I could not reproduce the seat's exact 41/896 board**, so those two absolute
  numbers remain unverified here. The *shape* of every row reproduced. I
  searched twelve candidate boards and a set of random lines
  (`scripts/find_reference_fen.py`, `scripts/search_reference_board.py`) and did
  not find it.
- **`movetime` cells have a race**, quantified in §3 at 30 processes per arm.
  I did not chase the race to its instruction; I located the sites that
  consume the field (`search.cpp:2192` clamp, `:2320` root check, `:1285-1288`
  `should_stop_with`) and measured the distribution.
- **The 2^63 clock rows are a different failure class and are now explained
  (§2d), not open.** `parse_clock_ms` clamps an over-large magnitude to
  `kMaxClockMs` — a *valid* ceiling of about 3.6e16 ms — so `wtime
  9223372036854775808` is not a dropped limit, it is a budget of roughly 1.1
  million years. Measured on K+R v K it returns at depth 64 in 45.6 s, exactly
  like `go infinite` minus the blocking. **A huge value and a malformed value
  are both "no practical limit" and they are not the same defect**, which is
  why the table separates them.
- **No source patch.** This seat measures and specifies; it changes no engine
  code. The `parse_limits` else-branch fix is named in §8 as a recommendation
  only.

---

## 8. What to do about it (recommendation, not a patch)

`parse_limits` has no failure path. `setoption` already demonstrates the shape
the engine knows how to do: **detect, report on the wire, keep the old state.**

Concretely, for each keyword: if a value was required and did not parse, emit
`info string invalid value for limit <keyword>` and leave that field at its
sentinel. That single change converts every row in §1 from "silently a different
search" to "a search plus one line saying why your request was not honoured" —
and it makes A1/A2/A5 in §6 unnecessary rather than merely advisable.

The two things a client cannot fix on its own, and which belong in the engine:

1. **`nodes` with a malformed value should not mean "no limit".** Absent and
   unparseable must differ.
2. **Bare `go` should not mean `go infinite`.** It is the single most likely
   accidental hang in this document.

---

## Evidence index

| file | contents |
|---|---|
| `evidence/keywords.jsonl` / `.md` | 75 cells, every keyword × form (+ the erroneous `searchmoves` block, rows 70-75) |
| `evidence/combos.jsonl` / `.md` | 19 cells, cross-keyword combinations |
| `evidence/eating.jsonl` | 11 cells, keyword-eating |
| `evidence/lastwins.jsonl` | 12 cells, repeated-keyword asymmetry |
| `evidence/searchmoves.jsonl` | 11 cells, corrected `searchmoves` pass |
| `evidence/book.jsonl` / `.md` | 14 cells, startpos `OwnBook true` |
| `evidence/book_randomness.json` | 24 fresh processes: the book move is nondeterministic |
| `evidence/extra.jsonl` / `.md` | 15 cells, forms outside the seat's list |
| `evidence/ladder.json` / `.md` | `nodes abc` vs `infinite`, identical 6 s window |
| `evidence/boundedness.json` | 120 s probes on two boards: which forms return on their own |
| `evidence/huge_clock.json` | the 2^63 clock as a valid huge budget, with `infinite` beside it |
| `evidence/repeatability.json` | 16 fresh processes per 0-ms form |
| `evidence/movetime_zero_interleaved.json` | 30 fresh processes per arm, interleaved |
| `evidence/build_and_run.log` | the matrix run log, build label on every line |
| `scripts/` | `go_probe.py` (the harness), `matrix.py`, `keyword_eating.py`, `lastwins.py`, `searchmoves_pass.py`, `boundedness.py`, `huge_clock.py`, `repeatability.py`, `movetime_zero.py`, `book_randomness.py`, `find_reference_fen.py`, `search_reference_board.py` |
| `scripts/verify_claims.py` | re-derives 293 checkable claims (numeric + table shape) from the evidence |
| `scripts/verify_anchors.py` | re-reads all 19 cited `path:line` source anchors from `6b98f217` |
| `scripts/check_all.sh` | runs both verifiers; non-zero if either fails |

## How the figures here are checked

`./scripts/check_all.sh` runs two independent verifiers and exits non-zero if
either fails.

**`scripts/verify_claims.py` — 293 claims**, two kinds: numeric (figures against
the JSON/JSONL evidence) and structural (every markdown table row against its
header's cell count).

**`scripts/verify_anchors.py` — 19 source anchors**: each `path:line` this
document cites is re-read from `6b98f217` and must still contain the construct
the document says it does.

**All three checks were proved able to fail.**
- Numeric: planting `999` for `go depth 5` nodes gives
  `§1 go depth 5 nodes :: 999 != 818`, exit 1; restoring gives exit 0.
- Structural: deleting one cell from the `depth` row gives
  `table shape at line 106 :: 7 cells, header has 8`, exit 1; restoring gives
  exit 0.
- Anchors: shifting one citation by a line gives
  `uci.cpp:107 should mention tokens[i++] … found: 'std::uint64_t value = 0;'`,
  exit 1; restoring gives exit 0.

**Each check earned its place on its first run.**
- The structural check caught **two** mangled tables that no numeric check could
  see, both introduced by my own edits after the tables had been written
  correctly.
- The anchor check caught **two wrong citations in this document**: the
  `uci_clock.hpp` clamp was cited at line 30 and is at **35**, and the
  `game_search` book predicate was cited as **`uci.cpp:521-523`** and is at
  **525-527**. Both had been written from a recalled reading rather than from the
  file. **A line number is the cheapest claim to make and the most expensive to
  be wrong about, because it looks checked.**

**What none of them check is the prose**, and two defects in this document were
found by writing it rather than by the scripts:
- a **book move cited as fixed** when the book is random (the script first
  flagged the move, then I measured the randomness — the script was right);
- a **section-scoped key collision** in `verify_claims.py` itself, where
  `go depth abc` appeared in both the midgame and startpos matrices and the flat
  dict returned whichever was loaded last. **A checker keyed on a command string
  must key on (section, command)**, or it reports the other section's row as a
  mismatch — which is what its first run did, six times.
