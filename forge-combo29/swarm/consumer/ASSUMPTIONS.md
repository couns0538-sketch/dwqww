# Client assumptions — written BEFORE the first probe run

Commit under test: `6b98f2170a3210e71beed04bbd2553972c253ed7` (`forge-combo29`, base for this audit).
Build: `/usr/bin/g++` 13.3.0, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`,
`cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release` (CMakeLists defaults:
`-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, PEXT + NNUE ZMM on).

Honesty pins on *this* binary, checked before any assumption was tested:

| pin | expected | measured |
|---|---|---|
| `bench 11` | 312,866 | 312,866 |
| `bench 13` | 862,329 | 862,329 |
| `bench 16` | 3,024,920 | 3,024,920 |
| `go perft 5` (startpos) | 4,865,609 | 4,865,609 |

Written 2026-11-17T05:12Z, before `probe.py` was executed. Any later edit to this file is
recorded in `STATUS.md`; a verdict added next to an assumption is added *after* the run and is
dated there.

## What "the spec" means here

The UCI protocol as documented (Meyer-Kahlen's specification): the command set
`uci/isready/setoption/ucinewgame/position/go/stop/quit`, the reply vocabulary
`id/option/uciok/readyok/info/bestmove`, the `info` sub-tokens
`depth/seldepth/time/nodes/pv/multipv/score cp|mate/currmove/hashfull/nps/tbhits/string`,
and `bestmove <move> [ponder <move>]`.

**The spec promises less than most clients assume.** In particular it does *not* promise:

- that any `info` line appears before a `bestmove`;
- that `pv` appears on an `info` line, or is non-empty;
- that a reply to a malformed request is an error, or is visible at all;
- that an engine which cannot answer will say so.

## Design note: what "stdout only" excludes

The client's *protocol decisions* come only from engine stdout. It keeps a chess board of its own
(a UCI client cannot even build a `position ... moves` line without remembering the moves), and it
uses that board only to (a) generate legal moves when it must choose what to send, and (b) score the
game afterwards. It never reads engine source, never inspects engine memory, never uses the
`bench`/`perft` extensions, and never infers a search outcome from anything but stdout.

## The assumptions

Each is stated so that a single observation can refute it.

| id | assumption a client must make to function | what the spec promises |
|---|---|---|
| **C1** | `uci` is answered with `uciok` in bounded time; every line before it is `id`, `option` or `info string`. | yes, explicitly |
| **C2** | `isready` is answered with `readyok` in bounded time, **including while a search runs**. | yes, explicitly |
| **C3** | Every `go` produces **exactly one** `bestmove` line — not zero, not two. | implied, not stated |
| **C4** | The `bestmove` payload is either a syntactically valid UCI move or the null token `0000`. | `0000` is the conventional null, not spec text |
| **C5** | A returned move is **legal in the position the client last set**. | implied |
| **C6** | A search that did work emits **at least one `info` line carrying `depth`**. | **no** — nothing requires `info` at all |
| **C7** | The `depth` value is the depth the engine actually searched. | implied by the token's name |
| **C8** | `nodes` counts nodes visited, so `nodes 0` means no search happened. | implied |
| **C9** | `score cp X` is the engine's assessment of the position, from the mover's side. | implied |
| **C10** | When `pv` is present, its first move equals the move returned in `bestmove`. | implied |
| **C11** | An **empty `pv`** means no line was searched, so the move is not a chosen move. | **no** — `pv` is optional |
| **C12** | A `go` carrying **any** recognised time form is bounded: it returns a `bestmove` on its own. | yes for `movetime`/both clocks; **no** for one-sided |
| **C13** | `searchmoves` confines the reply to the listed moves. | yes |
| **C14** | When `position` is accepted **silently**, the board searched is the board sent. | implied |
| **C15** | A refused request is **reported on stdout**, so refusal is detectable by the client. | **no** — nothing requires a diagnostic |
| **C16** | The `option ...` list from `uci` is the set of names `setoption` will honour. | yes |
| **C17** | `ucinewgame` resets search state: identical `position`+`go` gives identical output. | yes, that is its stated purpose |
| **C18** | `bestmove 0000` never means "play a move"; the `info` score says which no-move case it is. | `0000` conventional; the score discriminator is **not** spec text |
| **C19** | A returned **real move** is one the engine chose and would stand behind. | implied |
| **C20** | `info` lines arrive in non-decreasing `depth` order. | implied |
| **C21** | `time`/`nps` are consistent with `nodes`; a nonzero `nps` implies nodes were visited. | implied |
| **C22** | The engine's **own evaluation of the move it returns** is always available on stdout. | **no** — nothing requires a score |

**C22 is flagged in advance as the one likely to be unsatisfiable by *any* output.** It is not a
hypothesis about this engine; it is the shape of the protocol. If a path returns a move with no
score, then no output on the wire can satisfy C22 for that path, because the satisfying output does
not exist in the reply — it would have to be invented by the client. I expect one path to prove it
(the opening book, which per the findings emits two lines and nothing else). Recording it here
before the run means a confirmation is a prediction that held, not a post-hoc reframe.

## How each assumption is exercised

| path | how the client reaches it |
|---|---|
| book move | `position startpos` + `go wtime 10000 btime 10000` (mover's own clock present) |
| drawn root (insufficient material) | bare `K` vs `k` |
| drawn root (threefold, by move list) | repetition reached through `position startpos moves ...` |
| drawn root (fifty-move) | halfmove clock 100 |
| normal search | middlegame FEN, `go depth 12` |
| illegal position | short FEN, surplus-field FEN, `position nonsense` |
| off-book position | a middlegame FEN with `OwnBook true` |
| `go` with one clock missing | `go btime 10000` with White to move, bounded by the client's own deadline |
| `searchmoves` | legal-only, mixed legal+illegal, all-illegal, empty |

Every read is bounded by a wall-clock deadline in the client. A path that does not answer is
recorded as `NO_BESTMOVE` with its deadline, never waited on indefinitely (trap 18/19/21/24).

---

# Post-run addendum (2026-11-17, after the probes)

The list above is unchanged from before the run. This addendum records only the verdicts, and
the full evidence is in `FINDINGS.md` §2.

**Counts: 10 satisfied, 7 violated, 3 partial, 1 unsatisfiable by any output, 1
satisfied-but-dangerous.**

An edit made to this file after the run: none to the assumption list. The one correction to
this seat's own reasoning is recorded below.

## The prediction that held

C22 was flagged before the run as the one assumption no engine output could satisfy. It was
confirmed: on the book path and on `go nodes 0` the engine returns a move and there is **no
score anywhere on the wire**. That is a property of the protocol, not of this engine: the
satisfying output does not exist in the reply, so a client showing a score there is showing its
own default (which is exactly what trap 19 warns about).

## The four that matter for a client

| id | verdict | consequence |
|---|---|---|
| C6 | VIOLATED | a reader that waits for `info depth` deadlocks on every book move (0 lines, reply in 0.46 ms) and on `go nodes 0` |
| C7 | VIOLATED | a drawn root reports depth up to 64 with `nodes 0`; the reported depth is not a depth |
| C9 | VIOLATED | `cp 0` is shipped for positions the search scores `−43 … +142` |
| C19 | VIOLATED | the returned move is not a searched move: 0/6 and 36/40 disagreement |

## A mistake this seat made and corrected

An early reading of the `searchmoves` probes concluded the engine returned `0000` for a single
**legal** restricted move, contradicting the findings document. That was **this seat's error**:
the token used (`g1f3`) was illegal in the test position, because the knight was already on f3.
The arity matrix (`evidence/sm-matrix.txt`) shows the document is right: every restriction with
at least one legal token returns a listed move. Recorded because a contradiction of the
document must meet a higher bar than a confirmation of it, and this one did not.
