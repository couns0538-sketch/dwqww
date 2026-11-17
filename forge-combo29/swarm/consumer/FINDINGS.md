# A consumer's audit of `forge-combo29` — what a UCI client sees

**Commit audited:** `6b98f2170a3210e71beed04bbd2553972c253ed7` (the audit base).
**Deliverable:** a client that speaks only documented UCI, the assumption list it was
written against, every path exercised, and 100 complete games driven through it.

**Honesty pins on the binary this report measured**, checked before the first probe:

| pin | expected | measured |
|---|---|---|
| `bench 11` | 312,866 | **312,866** |
| `bench 13` | 862,329 | **862,329** |
| `bench 16` | 3,024,920 | **3,024,920** |
| `go perft 5` (startpos) | 4,865,609 | **4,865,609** |

Build: `/usr/bin/g++` 13.3.0 (the workspace `/usr/bin/c++` is clang 18 with a broken header
path), `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`,
`cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release`, host has AVX-512F and
BMI2 so the CMake default `-march=x86-64-v4` with PEXT + NNUE ZMM is the build measured.

---

## 1. The finding that matters most

**Nothing in this engine's stdout says whether the move it returns was searched.**

The audit's §1b says a drawn root returns a move with `cp 0`, `nodes 0` and an empty `pv`.
That much reproduces exactly. What this seat adds, because it measured from outside with
full move history instead of from a FEN, is the **cost**, and it is not a reporting defect:

| | |
|---|---|
| drawn roots measured in real games | **6** |
| roots that were genuine threefold repetitions (python-chess, full history) | **6 of 6** |
| bail move == the move the engine's own search returns for the same board | **0 of 6** |
| bail move legal in the position | **6 of 6** |

The last two lines are the whole problem. The move is legal, plausible-looking, and **never
the move the engine would have played**. In one measured root the engine's own search scores
the position `+142 cp` for the side to move (seed 1008); the bail answered `cp 0` and played a
move from a different root of the search tree. In another (seed 1010) the searched score is
`−49 cp`. So the `cp 0` is not a compressed true value — it is **not a value at all**.

**The measurement's exact caveat, stated because it matters:** the "searched" column comes from
re-sending the *same board* as a FEN, which per trap 2d destroys the repetition history and so
does **not** bail. That makes it a legitimate reference for *what this engine's search makes of
this position* — but it is not literally "the move the engine would have played with the
repetition history intact", because with that history it bails. So the claim is precise: **the
engine's search, given this board, prefers a different move than the one the bail returns**, and
the bail's move is not the product of any search at all. The alternative — the engine searching
this exact history — is unobservable, because it does not do that.

**Why this is worse than §1b says.** §1b's instruction is "treat an empty PV as no move was
chosen". That is correct and it is what this client does — and it still cannot play the game.
An empty PV tells a client *not to trust the move* but gives it **no alternative**: the engine
has already spent the move, and the only other legal moves in the position are the ones the
client thinks of itself. So a client has three options, and the protocol supports none of them
well:

1. **Play the bail move** — a move 0 of 6 roots agreed with. Recorded here as `allow_bail_play`.
2. **Adjudicate the position as drawn and end the game.** Correct in all 6 cases, but the
   client is now making a chess judgement the engine did not make.
3. **Treat it as a protocol failure and stop.** Honest, and what this client does by default.

**This is not a bug the engine can fix inside the UCI vocabulary**, because the vocabulary
has no field for "I did not search." §2 ("repair the drawn-root bail — the MOVE, not the
score") is the right repair, and from the wire it is measurable as exactly this: after the
repair, move agreement on these 6 roots should go from **0/6** to **6/6**. That is the test
the repair should be judged by, and it is a cleaner instrument than the score, because the
score is the thing the report itself warns is misleading.

---

## 2. Assumption table — every verdict, and what a client does wrong

The assumptions were written before the first probe (`ASSUMPTIONS.md`, timestamped) so that a
confirmation is a prediction that held rather than a post-hoc reframe. Twenty-two
assumptions, all exercised. Verdict counts: **10 satisfied, 7 violated, 3 partial, 1
unsatisfiable by any output, 1 satisfied-but-dangerous.**

| id | assumption | verdict | what a client does WRONG |
|---|---|---|---|
| **C1** | `uci` → `uciok`, bounded, only id/option before | **SATISFIED** | — |
| **C2** | `isready` → `readyok`, including mid-search | **SATISFIED** (0.3 ms during a 3 s search) | — |
| **C3** | exactly one `bestmove` per `go` | **SATISFIED** | — |
| **C4** | payload is a UCI move or `0000` | **SATISFIED** (no UNPARSED seen) | nothing observed; a client still must guard it, since *nothing beyond the move syntax is promised* |
| **C5** | returned move is legal in the position last set | **SATISFIED** — but see C14 | on a **refused** position the move is legal in the *previous* board, so a client validating against its own board sees a legal move for the wrong game and plays on |
| **C6** | a search emits ≥1 `info depth` line | **VIOLATED** | **a GUI or harness that waits for `info depth` deadlocks on every book move** (0 lines) and on `go nodes 0` (0 lines). The book path emits exactly `info string book move e2e4` then `bestmove e2e4`, in **0.46 ms** |
| **C7** | reported `depth` is the depth searched | **VIOLATED** | **a GUI shows "depth 64, 0.00" on a search that visited zero nodes.** Measured: 64 `info depth` lines at `go depth 64`, all `nodes 0`, all empty `pv`; and 20 lines at `go depth 20` on a repetition |
| **C8** | `nodes 0` means no search | **SATISFIED** | — (it is a *true* signal; C22 is why it is not enough) |
| **C9** | `score cp X` assesses the position | **VIOLATED** | **the same `cp 0` is shipped for positions the engine's own search scores anywhere from `−43` to `+142 cp`.** Two independent samples: on 40 bail roots replayed as FENs, 17 scored nonzero, range `−43 … +46`; on the 6 hand-audited roots (which keep their repetition history, so they re-bail), `+142` and `−49`. A GUI's evaluation bar is wrong by that much, and shows `0.00` while doing it |
| **C10** | `pv[0] == bestmove` | **SATISFIED** on all searching paths | — |
| **C11** | empty `pv` means no move was chosen | **SATISFIED as a signal** — it is the only one, and `pv` is specified as *optional*, so a client may not rely on the token being present at all | a client that reads `pv` only when present misses the signal entirely; it must distinguish *absent* from *present-and-empty* |
| **C12** | any recognised clock form bounds the search | **VIOLATED** | **`go btime 10000` with White to move never returns** — bounded by the client at 25 s, both colours. A match harness with a one-sided clock **hangs**, and the hang looks like slow thinking |
| **C13** | `searchmoves` confines the reply | **SATISFIED** | — every list with ≥1 legal token returned a listed move; all-illegal and empty give `0000` + `info string searchmoves restriction has no legal root moves` |
| **C14** | silently-accepted `position` searched the board sent | **VIOLATED** | **a surplus-field FEN is loaded (7/9 fields ok) and `position nonsense` re-searches the previous board.** A GUI silently analyses the wrong position and displays a full, confident, wrong PV |
| **C15** | refusal is reported on stdout | **PARTIAL** — 3 surfaces report, 3 do not | a client cannot detect refusal by watching the wire. The only safe rule is to validate everything client-side before sending |
| **C16** | `option` list == `setoption` honour set | **SATISFIED** (bad value and unknown name both reported, old value kept) | — |
| **C17** | `ucinewgame` resets search state | **SATISFIED** (3/3 identical node counts and bestmoves) | — |
| **C18** | `0000` is never a move; the score says which case | **SATISFIED on the wire, dangerous** | `mate 0`+0 legal = checkmate, `cp 0`+0 legal = stalemate, both correct. **But the same `cp 0` also comes with a REAL move** on a drawn root, where `0000` is never sent — so "score cp 0 ⟹ no move" is false, and a client keying on the score alone will mis-handle one of the two |
| **C19** | a returned real move was chosen | **VIOLATED** | **the game engine plays the bail's head move — 0 of 6 roots agreed with the engine's own search** |
| **C20** | `info` depths non-decreasing | **SATISFIED** | — |
| **C21** | `nps`/`time` consistent with `nodes` | **SATISFIED** (never nonzero nps with 0 nodes) | — |
| **C22** | the engine's assessment of the move it returns is always on stdout | **UNSATISFIABLE BY ANY OUTPUT** | see below |

### C22 — the assumption no engine output can satisfy

I flagged this before running, and it held, which is the point.

On the **book** path and on **`go nodes 0`**, the engine returns a move and there is **no
score anywhere on the wire**. The only lines are `info string book move X` / `bestmove X`.
So the sentence "the engine's evaluation of the move it returned is available" cannot be
satisfied from stdout on those paths by *any* engine, because the satisfying output does not
exist in the reply — a client that shows a score there is showing **its own default**, exactly
as trap 19 warns.

This is the one assumption whose failure is a property of the protocol rather than of this
engine. It is worth stating separately because it sets the ceiling on what any consumer can
do: **a GUI can never show a book move's score as the engine's**, and must either show nothing
or label it as a book move. Any report that quotes a score for a book move is quoting a
client artefact.

---

## 3. Divergences from the findings document

These are places where this seat's measurement on the base commit disagrees with
`forge-findings.md`. Each is stated with its control, because a divergence is a claim about
the document and needs the same discipline as a claim about the engine.

### 3.1 Trap 3aa does not reproduce, and the mechanism is in the source

Trap 3aa says seven malformed `go` requests "all land on one identical search: **depth 5,
1,001 nodes**", and that `go depth abc` produces identical `info depth` lines to `go depth 5`.

Measured, startpos and midgame, cold reset each time:

| request | startpos | midgame |
|---|---|---|
| `go depth 5` (control) | depth 5, **1001** nodes | depth 5, **896** nodes |
| `go depth 1` (control) | depth 1, 26 nodes | depth 1, 41 nodes |
| `go depth abc` | **depth 1, 26 nodes** | **depth 1, 41 nodes** |
| `go depth` (no value) | **depth 1, 26 nodes** | **depth 1, 41 nodes** |
| `go movetime abc` | depth 5, 1001 nodes | depth 5, 896 nodes |
| `go movetime 0` | depth 5, 1001 nodes | depth 5, 896 nodes |

`go depth abc` reproduces `go depth 1` **exactly**, not `go depth 5`. The source agrees:
`uci.cpp:103` is `limits.depth = std::clamp(read_int(), 1, 64)`, and `read_int()`
(`uci.cpp:87-96`) **returns 0** when `from_chars` fails — so `clamp(0, 1, 64)` is **1**. The
doc's "depth 5, 1001 nodes" is the *startpos* `go depth 5` figure, so it appears the original
measurement conflated the malformed-depth arm with the `movetime` arm: the two arms do land
on the same search, but that search is **depth 5 only for the `movetime` forms**, and it is
**depth 1 for the `depth` forms**.

**What this changes for a consumer: nothing about the hazard, everything about the label.**
The hazard is real and worse than described — a malformed `depth` and a malformed `movetime`
do not even land on the *same* wrong search, so a harness cannot detect one by calibrating
against the other. The doc's own rule ("a depth column measured under a timeout is a column
of the harness's patience") is the right one; the specific figure is not.

### 3.2 `go nodes abc` / `go nodes` / `go frobnicate` / bare `go` are unbounded, not defaulted

Trap 3aa lists `go nodes abc` and `go nodes` among the seven requests that land on a default
search. Measured: they produce **no bestmove at all**. At a 60 s window, `go` and
`go nodes abc` reach **depth 32 / 118,349,849 nodes** and are still climbing; `stop` answers
in ~1.5 s.

The source agrees: the parse branch is
`if (i < tokens.size()) { ... if (parse ok) { limits.nodes = value; limits.nodes_specified = true; } }`
with **no `else`**, and `SearchLimits::nodes` defaults to `0` with `nodes_specified = false`
(`search.hpp:29-31`) — so an unparseable nodes value leaves the search with **no node limit
at all**, which is the same as bare `go`.

**This is the more dangerous half of trap 3aa and it is missing from the document.** Trap 3a1
records that `movestogo` and `ponder` are unbounded, and trap 18 records the one-sided clock;
this is a fourth unbounded form, reached by a *typo in a limit the caller did supply*. A
harness that sends `go nodes 5000` and mistypes the value gets an infinite search rather than
a default one.

### 3.3 A claim this seat tried to test and could NOT reproduce (not a refutation)

§2 states that on six measured fixtures the bail **forfeits a mate in one**. That is a
sharper claim than "the move is different", so it was worth reproducing from the client side:
it needs a position that is *both* a threefold repetition *and* has a mate in one available,
reached by a legal move list.

**This seat could not construct such a position** (`bail_forfeit.py`). Three attempts, each
diagnosed rather than guessed:

| base | mate in 1 | why it fails |
|---|---|---|
| `7k/8/6K1/8/8/8/8/1N5R w` | `g6f7#` | **illegal base** — `Rh1` already checks `Kh8` while White is to move |
| `1n5k/8/6K1/8/8/8/8/1N5R w` | `g6f7#` | same illegal check; once answered, Black's **only** legal reply is `h8g8`, so no repetition line exists |
| `k7/8/1K6/8/8/8/8/R6N w` | `b6c7#` | legal, but no alternating shuffle keeps the mate *and* repeats |

**So this entry neither confirms nor refutes §2's mate-forfeit result**, and is recorded as a
non-reproduction with its reason, not as a disagreement. The structural obstacle is real: a
mating net usually puts the opposing king in check or removes its shuffle squares, which is
exactly what a repetition needs.

**What stands in its place is stronger, because it is measurable on every bail:** the bail's
move disagrees with the engine's own search on **0 of 6** hand-audited roots and **36 of 40**
sampled roots. A move disagreement subsumes the mate case — if the bail returns a different
move, and a mate in one existed, the bail did not return it — without needing to construct a
rare position. The mate-forfeit claim is therefore *implied* by the measurement here, not
independently confirmed.

---

## 4. Games: 200 complete games under the client (100 per arm)

Two arms, **same engine, same seed, same ten openings, same 50 ms/move clock**. They differ
in exactly one rule: whether the client plays a 0-node/empty-pv move.

| | strict arm | naive arm |
|---|---|---|
| client rule at a BAIL | refuse to play; end the game | play it and continue |
| games | 100 | 100 |
| total plies | 13,098 | 17,588 |
| **games lost to a protocol failure** | **59** | **0** |
| games ended by chess | 25 (21 checkmate, 4 insufficient material) | 58 (50 checkmate, 5 insufficient, 1 stalemate, 1 repetition, 1 other) |
| unfinished at the 200-ply cap | 16 | 42 |
| BAIL plies | 59 | 82 |
| BOOK plies | 0 | 0 |

**The strict arm's 59 failures are all genuine draws, independently verified.** Every one was
rebuilt from its recorded moves and tested with python-chess, which knows nothing about the
engine: **59 of 59 are threefold repetitions**, 0 unexplained, 0 FEN mismatches between the
client's record and the rebuild. On those same 59 positions the engine reported, every single
time, **depth 64, nodes 0, pv length 0**.

So the answer to the brief's question — *was any game lost to a protocol-level failure rather
than chess?* — is:

- **Under a strict client: 59 of 100 games.** Not one of them was lost to a chess error. Every
  one was lost because **the engine declined to search a position it had correctly identified
  as drawn, and said so only in a field (`pv`) that the specification marks optional.**
- **Under a naive client: 0 of 100.** It loses no games to protocol because it plays the bail
  move — and pays in chess instead (below).

This is the cleanest statement of the finding in the whole audit, and it is a *comparison*:
the same positions, the same engine, lose 59% of games under one client rule and 0% under the
other. Neither number is a property of the engine alone; both are properties of the
engine-plus-client pair.

### The naive arm pays in chess, measurably

On 40 sampled bail positions from the naive arm, the move it played matched the move the
engine's search returns for the same board **4 times (10%)**. 36 of 40 were a different move.
(As in §1: the comparison replays the board as a FEN, which is the only way to see this
engine's search on that board at all — see the caveat there.) That is the same defect as §1
measured on a much larger sample, and it is the answer to "what does a GUI actually lose":

- A strict client loses **games** (59/100) and keeps clean chess.
- A naive client keeps its games and loses **move quality**: 90% of its bail moves are not the
  move the engine would have chosen, including moves scored `−43`, `−36` and `−20 cp` by the
  engine's own search where the bail claimed `cp 0`.

**Neither arm is correct, and that is the point.** The protocol gives a client no third option.

### Also verified: all 82 naive bails were legitimate claims

81 threefold repetitions and 1 fifty-move claim, 0 without a claim. So the *adjudication* is
right in 82 of 82; only the *move and the score* are wrong. A repair should not touch the
draw detection — it should make the engine return a searched move, or a token that says
"no move" (`§2`'s repair).

---

## 5. What this audit could not reach

- **The BOOK path never fired in the games.** `OwnBook false` was set for the match (that is
  what a harness measuring search should do), so all 200 games have zero BOOK plies. The book
  path was measured separately (§2, C6/C22) and deadlocks a depth-line reader in 0.46 ms, but
  it was not exercised *inside* a game. A client playing with `OwnBook true` would meet it on
  move 1 of every game.
- **Both arms are one engine against itself.** This measures protocol survival and move
  quality, not strength. No Elo claim is made or implied.
- **One build, one host, one compiler.** Pins verified, so node counts are the documented
  ones, but the Windows/clang lock binary was not measured here.
- **The 59% failure rate is a property of these games.** 50 ms/move self-play from ten short
  openings repeats positions a great deal. A match between two different engines, or longer
  time controls, would produce a different rate. The **mechanism** generalises; the percentage
  does not.
- **`searchmoves` was probed, not stress-tested.** Lists of 1-6 tokens including mixed
  legal/illegal, duplicates, enemy moves and a legal-shaped illegal move were tested; the full
  space was not swept, and §6's warning that `<all legal moves>` is not a no-op was not
  re-measured here.
- **C22's unsatisfiability is proved for the paths whose replies were read in full** (book,
  `go nodes 0`), not for every path. It is a proof for those two, and an argument for the
  category.
- **The `movestogo`/`ponder` unbounded claim was confirmed at a 60 s window**, not until
  exhaustion. Trap 24's depth-64 clamp may bound them eventually; this seat did not run them
  to the clamp, so "unbounded" here means "no answer in 60 s at depth 32 / 118M nodes".

## 6. Files

| file | what it is |
|---|---|
| `ASSUMPTIONS.md` | the 22 assumptions, written **before** the first probe |
| `client.py` | the client: documented UCI only, stdout only, every assumption a check |
| `engine.py` | bounded process driver (`os.read` on a thread; never `select()`+`readline`) |
| `games.py` | full games under a clock, strict and `--allow-bail-play` arms |
| `probe.py` | 29 wire paths → `evidence/wire-base.json` |
| `analyse.py` | probe evidence → the verdict table |
| `selftest.py` | 31 checks proving the audit's own checks can fire |
| `bail_history.py` | rebuilds bail positions with full history; the repetition test |
| `bail_harm.py` | move-list form vs FEN form: the bail's cost |
| `bail_cost.py` | what the naive arm pays, 82 played bail moves |
| `verify_failures.py` | independent referee over every protocol failure |
| `depth_ladder.py` | sec 1b's line-count claim across budget kinds |
| `go_values.py`, `trap3aa_startpos.py` | the malformed-`go` divergence |
| `unbounded.py` | the unbounded `go` forms, with a window |
| `reader_trap21.py` | the depth-line reader deadlock, with a working control |
| `null_token.py`, `sm_matrix.py` | the `0000` discriminator and `searchmoves` arity |
| `evidence/` | every raw measurement the report cites |
