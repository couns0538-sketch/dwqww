# GUI HAZARDS AND RULES — for anyone writing a front end for this engine

> **The owner's match program is unaffected.** It drives the engine directly with well-formed positions, so
> neither hazard arises in the PC's self-play or matches. Everything here matters for anyone else writing a
> front end, and for analysis tools.

Seat 23, verified on **PC r15 under PC20, Threads 1, Hash 16, OwnBook false**. Both hazards are confirmed on the
build the owner's PC actually plays, and both share a single defensive rule at the end.

## The contract, in one table — read this first

Four situations produce output a front end can misread, and they are distinguishable **only** by the fields shown. Every
row is measured on the base build with Threads 1 / Hash 16 / `OwnBook false`, stdout drained to `bestmove`.

| situation | `#info depth` lines | nodes | `pv` | score | `bestmove` | `info string` | what it means |
|---|---|---|---|---|---|---|---|
| normal search | = depth (× MultiPV) | > 0 | **non-empty** | any | a legal move | none | search ran |
| **drawn root** (3-fold in the list, or halfmove ≥ 100, or insufficient material) | engine ceiling (10 at `go depth 10`; **64 under `go nodes`**), never × MultiPV | **0** | **empty** | **cp 0** | a legal move — the generator's first | none | nothing was searched |
| **empty/illegal `searchmoves`** | engine ceiling (same as above) | **0** | **empty** | **cp 0** | **`0000`** | `searchmoves restriction has no legal root moves` | caller error; **not a legal move** |
| **stalemated root + unsatisfiable restriction** | engine ceiling (same as above) | **0** | **empty** | **cp 0** | **`0000`** | **none at all** | caller error, **silently** |
| refused FEN or illegal token in the list | search runs on the WRONG board | > 0 | non-empty | plausible | plausible | one `info string` | the position is not what you sent |

**Three rules follow, and they are the whole page compressed:**

1. **`nodes == 0` with an EMPTY `pv` means nothing was searched** — never show its score. The empty `pv` is the reliable
   signal; the node count is a symptom and the two auto-draw rules share it. **And do not infer a search depth from the
   `info depth` line count here: on a bailed root it is the engine's ceiling (10 at `go depth 10`, 64 under `go nodes`),
   not the depth of any search, because there was none (23-F185).**
2. **`bestmove 0000` is never a move.** Treat it as an error, and do not rely on a diagnostic to explain it — on a
   stalemated root there is none (23-F159).
3. **Count the `info string` lines on every search.** They are the only signal that your position or your restriction was
   rejected, and a corrupted case is otherwise indistinguishable from a healthy one.

The sections below explain each row, with the measurements behind it.

## The detail that matters most

**A corrupted move list is DISCARDED from the first illegal token onward, not skipped.** One bad ply does not lose
one ply — a corruption at ply 3 loses the five good plies that followed it, and the engine then searches a board from
a different game entirely, without saying so beyond one line.

## Hazard 1 — a refused position is silently replaced by the previous game

Send a `position fen` the engine rejects, then ask for a move.

| step | what the engine does |
|---|---|
| `position fen <impossible castling right>` | prints `info string invalid FEN: castling right without king and rook` |
| `isready` | answers **`readyok`** — as if nothing happened |
| `go depth 6` | returns the **PREVIOUS game's move** |

Measured: base tree `d2d4` before and after the refusal; PC r15 `f1c4` before and after. So the refusal is
announced only on an `info string` line that most GUIs never read.

## Hazard 2 — one illegal token replaces the game from that point on

Send `position startpos moves <list>` with one illegal token in it.

| corruption | engine says | perft 1 | intended |
|---|---|---|---|
| illegal token at ply 3 of 8 | `info string illegal move e2e4` | **29** | 38 |
| illegal token at ply 5 | same | **27** | 38 |
| illegal token at ply 7 | same | **33** | 38 |
| clean list (control) | — | **38** | 38 |

The engine keeps the legal prefix, answers `readyok`, and searches that. This is the **more exposed** of the two,
because a GUI sends a move list on every move, whereas hazard 1 needs a malformed FEN.

**And it does not merely keep going — it produces a FULL, NORMAL SEARCH of the wrong board (23-F95).** On a K+R v K
position, a list with an illegal ply 7 gives one `info string illegal move a1b1`, then 8 `info depth` lines, a score of
`cp -424` and **4,416 nodes** — against a legal 7-ply control list giving 8 info lines, `cp 391` and **4,957 nodes** on
the same harness. So the corrupted case is indistinguishable from a healthy one by any check that looks at the shape of
the output (info lines present, plausible node count, plausible score). The only reliable defence is what this page
already says: count the `info string` lines, and validate your own move list against an independent implementation
(python-chess rejected the same list instantly) rather than against the engine's willingness to answer.

## Hazard 3 — a `go` with only the opponent's clock never answers

Send `go wtime N` while it is **Black** to move (or `go btime N` while White is to move). The clock that was sent does
not belong to the side to move, so no limit is set:

| probe | PC r15 + PC20 | base |
|---|---|---|
| Black to move, `go wtime 1000` | **no bestmove within 3 s**, 0 diagnostics | same |
| Black to move, `go btime 1000` (own clock) | answered in 0.02 s | 0.04 s |
| White to move, `go btime 1000` | **no bestmove within 3 s**, 0 diagnostics | same |
| White to move, `go wtime 1000` (own clock) | answered in 0.03 s | 0.05 s |

This is the least diagnosable of the three: hazards 1 and 2 give you a **wrong board** with a diagnostic line
available; this one gives you **no move at all** and **no diagnostic**. A GUI that sends a partial clock simply stops
receiving moves with nothing in the engine's output to say why. Remedy (seat 02's design suggestion, not my
measurement): print an `info string` and fall back to a bounded default when neither clock belongs to the side to move.

## The rules that cover all three

> **After every `position` command, count the `info string` lines the engine emits. If any appeared, do not trust
> the position — rebuild it from scratch (`ucinewgame`, then a well-formed `position`).**

Validated by experiment, not recommended on theory. Same corrupted list, intended perft 1 = 38:

| protocol | diagnostics seen | perft 1 | outcome |
|---|---|---|---|
| **naive** — use whatever the engine searched | 1 | **29** | **wrong board, silently** |
| **detect** — abort the game if any diagnostic appears | 1 | not used | safe, plays nothing |
| **fixup** — `ucinewgame` + re-send the well-formed list | 0 | **38** | **exactly right** |

The naive protocol plays a different game; detect refuses to play a wrong move; fixup recovers. **Detect is the
minimum; fixup is what makes the engine usable.**


## A detection heuristic for a refused position: identical counts from different boards

Two independent incidents gave the same tell. When a position is REFUSED, the engine keeps the previous board, so:

> **If two DIFFERENT boards report the SAME node count, suspect a refused position.** Different positions essentially
> never share a node count; the same count means the same board was searched twice.

Both times this fired it was mine:

| incident | what happened |
|---|---|
| 23-C14/C23 | a refused FEN left the previous game on the board; the "new" position's numbers were the old one's |
| 23-F69 | two endgame boards with a pawn on the back rank are INVALID, were refused, and both reported **56,720** and **72,062** — identical, because both searches ran on the same previous board |

So this heuristic is worth adding to a driver's own checks even though it is not a substitute for counting the
`info string` lines: it catches the cases where the diagnostic was not read, and it is cheap — compare the node count
of consecutive positions and flag an exact match.

## Hazard 4 — an EMPTY `searchmoves` RESTRICTION returns `bestmove 0000`, and its structured fields look like a draw

This one is separate from the drawn-root material because **it has nothing to do with draws**: it is about an illegal or
empty `searchmoves` restriction, and it happens on any root, drawn or not (23-F153/F156).

Measured on the base build, `go depth 10 searchmoves e2e4` where `e2e4` is not legal on that board:

| root | `#info depth` lines | nodes | `pv` | score | `bestmove` |
|---|---|---|---|---|---|
| threefold (drawn) | 10 | 0 | **empty** | **cp 0** | **`0000`** |
| bare FEN (**not drawn**) | 10 | 0 | **empty** | **cp 0** | **`0000`** |

**`0000` is not a legal UCI move.** A front end will either raise, or worse, pass it on as though the engine had moved.

**Why this is the worst combination.** An ordinary drawn-root bail and an empty-restriction return have **identical
structured fields** — 10 `info depth` lines, `nodes 0`, `cp 0`, empty `pv` — and differ **only in the free text**:

    info string searchmoves restriction has no legal root moves

So a tool that inspects the structured fields cannot tell a null move from a legal first move played on a drawn position;
the only signal is an `info string` line. If you are writing a front end, **build your `searchmoves` list so it cannot be
empty** (check it against the legal move list before sending), and **treat `bestmove 0000` as its own error**, not as a
draw.

> Note for the driver page's first rule: this is another case where counting the `info string` lines is the difference
> between a diagnosis and a mystery.

## The drawn-root case is invisible to the diagnostic rule — a second check

The four rules above catch a **refused** position or a **truncated** move list, because both emit an `info string` line.
A **drawn root** does not: the position is accepted, no diagnostic appears, and the engine returns a move having
searched nothing. Measured (threefold-repetition root sent as a move list, `go depth 12`):

| build | `info string` lines | nodes | diagnostic rule fires? |
|---|---|---|---|
| base | **0** | **0** | **no** |
| PC r15 + PC20 | **0** | 44,269 | no (and it need not — the PC really searched) |

So add a fifth check, for tooling that may run on the un-repaired build:

> **A search that returns `bestmove` with 0 nodes is suspicious.** Either the root is drawn (repetition, fifty-move,
> insufficient material) or the position was refused. Either way the engine has not analysed anything and any score it
> printed is not a search result — **and the MOVE is not a search result either, which is the half that is easy to
> miss.**

**THE BETTER DETECTOR IS AN EMPTY PV, not a zero node count (23-F151).** Verified on the wire, base build, `go depth 10`:

| case | `info depth` lines | last score / nodes | PV plies | `bestmove` |
|---|---|---|---|---|
| threefold root (BAIL) | 10 | cp 0 / **0** | **0 (empty)** | d5d1 |
| same board, bare FEN (SEARCHES) | 10 | cp 381 / 7,581 | **11** | d5b5 |

**And the `cp 0` can be wrong about the POSITION even when it is right about the RULE.** On a genuine threefold root
where the side to move has mate in one (`6k1/5ppp/8/8/8/8/5PPP/1Q4K1 w`, 23-F171), the base reports `cp 0` and plays a
move that FORFEITS the mate, while the PC reports `mate 1` and mates. The draw is claimable, and a winning side would not
claim it — so `cp 0` is defensible under the rule and still tells a user the wrong thing about the game. Never present a
bailed root's `cp 0` as an assessment of the position.

An empty PV is the RELIABLE signal, and reliable for a structural reason rather than a convention: the terminal branch
never assigns `result.pv` (`search.cpp:2250-2271` contains no `pv` write, per the source reading), while every searching
path publishes a non-empty PV because a completed iteration always has at least one move. So a tool should test
**"did the last `info` line carry a PV?"** rather than "were there zero nodes" — the node count is a symptom, the empty PV
is the mechanism. Note also that a bailing root emits **one `info depth` line per depth**, not zero, so "no info lines"
is never the right test for this case (23-F146).

The second half is measured (23-F93, 23-F96): on a threefold-repetition root the un-repaired build answers `cp 0` with
**0 nodes** on EITHER side to move, and its `bestmove` is chosen without a search. On a won endgame that unsearched
move still wins — but on ONE measured root it turned a **mate in 10** into a capped `+529` that stayed capped at
depths 16, 18 and 20, so the RESULT survived while the METHOD degraded. **That mate loss is a ONE-ROOT result and must
not be generalised: a breadth test over three geometrically distinct threefold roots found no second instance (one root
had no short cycle at all, the other was a cp win with no mate available at any depth tested) — see 23-F97.** On the
board where 23-F60 caught it, the same kind of unsearched move LOST, which is a third distinct outcome and the worst
one. So for a tool the safe reading is the general one, which holds on every root tested: **the score is not a search
result and the move is not an analysed move.** If the root may be drawn, search the resulting position (or refuse the
root) before showing either.

The 2-vs-3 occurrence control is what makes this a statement about the repetition rule rather than the fifty-move
counter: the same board and side to move, one more cycle of the same shuffle, 22,108 nodes become 0.

On the PC build this check never fires for the drawn-root case because the repair makes it a real search — which is
the correct behaviour, and the reason the check is a detector for the un-repaired build rather than a general rule.

## What a well-behaved driver looks like, end to end

Three seats were bitten by DRIVER SHAPE rather than by engine behaviour (the FEN-vs-moves difference in 23-C20, the
refused-FEN stale board, the illegal-token truncation). Here is the whole protocol in one block, in the order that
avoids every hazard on this page.

```
startup      uci  ->  read until "uciok"
             for each option you set:   setoption ...
                                        isready  ->  read EVERY line until "readyok"
                                        (stop on "unknown option" / "invalid value")
             ucinewgame         ONCE, before any position        <- see 23-C1: it DISCARDS a position sent before it
position     ALWAYS send the move list when you have one:
                 position startpos moves e2e4 e7e5 g1f3 ...
             only use `position fen` when there is no history
             then:  isready  ->  read EVERY line until "readyok"
             **count the `info string` lines you just read.**
                 if ANY appeared  ->  the position was refused or truncated.
                                       do not search it. `ucinewgame` and rebuild.
search       send BOTH clocks for the current game, every time:
                 go wtime <ms> btime <ms> winc <ms> binc <ms>
             never one clock alone (hazard 3: no answer, no diagnostic)
             read until "bestmove" — never send the next command first (19-F12: a pipelined `quit`
                 makes this build answer `bestmove a2a3` with 0 nodes)
shutdown     quit, only when no search is running
```

The four rules, which are the whole of it:

1. **`ucinewgame` before the first `position`, never between a `position` and its search.**
2. **Send the move list, not a FEN, when history exists** — the FEN form can change the answer (23-C20).
3. **Count `info string` lines after every `position`; rebuild if any appeared.** The line is the only signal that
   the engine is not on the board you think it is.
4. **Send both clocks, and read to `bestmove` before the next command.**

Rule 4 is not a nicety — a violation does not perturb the answer, it **replaces** it. Sending `position startpos`
straight after `go` on a Ruy Lopez position, with no drain, returns the fabricated **`bestmove a2a3` at 0 nodes**,
where the ordered run returns **`f1b5` at 89,103 nodes** (23-F77). So a pipelining driver is not merely slower or
noisier: it gets a legal-looking move that was never searched, and nothing in the stream says so.

Every one of those maps to a hazard measured on the PC build on this page, and to a seat that lost time to it.
**Claim strength, stated plainly:** this driver shape is **validated for all three hazards**, each with a control
showing what a naive driver does instead — H1: the naive driver searches the *stale* board; H2: it searches a *third*
board (the truncated prefix); H3: it never gets a move at all, while the compliant driver gets one in 30 ms.

## A sixth trap: `eval` and `go` contradict each other on a drawn position

`eval` scores the BOARD statically and knows nothing about move history; `go` searches, and on the base build a
repetition root is short-circuited to cp 0 with 0 nodes. On the same position the two therefore disagree:

| build | `eval` total | `go depth 12` |
|---|---|---|
| base | **+406** | **cp 0, 0 nodes** |
| PC r15 (no PC20 switches) | +406 | cp 425, 40,801 nodes |

**NUMBERS RE-VERIFIED (23-F135).** An earlier version of this table read "PC r15 + PC20, cp 507, 44,269 nodes". The
fixture is sound — validated as a genuine threefold (`counted=3 python-chess=3`) — but the PC row had drifted from the
current builds/options; re-measured on PC r15 with default options it is **cp 425 / 40,801 nodes**. The CONCLUSION is
unchanged (the two interfaces still disagree by 406 cp, and the PC still searches where the base returns 0 nodes), which
is exactly why a stale number in a summary is dangerous: it survives because nobody re-runs a claim they already believe.

So a GUI that shows `eval`'s number for the position while taking its move from `go` displays a winning score (+406)
next to a move chosen from a draw with no search at all — a 406 cp contradiction, with no diagnostic anywhere.

> **Do not mix the two interfaces.** If you display `eval`, say that it is a static board score that ignores repetition,
> and do not present it as the engine's opinion of the game state.

This is not an `eval` defect — a static evaluator has no history and is right to score the board. It is a trap in how
a front end combines the two answers (23-F78).

**The gap has a precise boundary, which tells you where to be careful:** it is large exactly for draws caused by
**history** and small for the draw caused by **material** —

| draw type | `eval` total | `go` | gap |
|---|---|---|---|
| threefold repetition | +406 | cp 0 | 406 cp |
| fifty-move rule | +406 | cp 0 | 406 cp |
| insufficient material, `8/8/8/8/8/8/8/K6k w` | **+76** | cp 0 | **76 cp** |
| insufficient material, `k7/8/8/8/8/8/8/7K w` | +17 | cp 0 | 17 cp |

**RE-MEASURED (23-F135/F136) — and the change of figure is itself the point.** The insufficient-material row previously
read `+20`, and **that `+20` had NO PROVENANCE**: the row never named the position it came from, and it reproduces on
NONE of five bare-king positions tried (76, −5, 17, −50, 9). So `+20` was a real measurement from some board that was
never recorded, and by the time it reached this page there was no way to check it — which is why it survived: nobody
re-runs a claim they already believe. Re-measured against named boards it is **+76** for `8/8/8/8/8/8/8/K6k w` and
**+17** for `k7/8/8/8/8/8/8/7K w`. **The number changed because it was uncitable, not because the finding did.** **The CONCLUSION is
unchanged and is what the table is for: for insufficient material the eval/go gap is small (tens of cp) while for
history draws it is the whole eval total (406) — but the specific figure a reader might quote was wrong, and quoting it
would have been quoting an unattributable number.**

So the contradiction you must guard against is repetition and the fifty-move rule — the two a static evaluator
cannot see. For insufficient material the two interfaces nearly agree in ABSOLUTE terms (tens of cp against 406), though the exact figure is board-dependent — 76 on one bare-king board, 17 on another (23-F136).

**Where the contradiction appears, as a curve.** Sweeping the fifty-move counter on a won K+R v K board (base build,
`go depth 10`), the gap between `eval` and `go` is not constant — it opens at the search horizon:

| counter | 40 | 60 | 80 | 88 | 90 | **92** | 95 | 99 | 100 |
|---|---|---|---|---|---|---|---|---|---|
| gap (cp) | 25 | 25 | 32 | 45 | 135 | **406** | 406 | 406 | 406 |

`eval` stayed at exactly 406 across all nine counters (0 cp spread — it genuinely has no move counter). So near the
end of the fifty-move count the two interfaces diverge completely, and earlier in the game they roughly agree: a GUI
showing `eval` is most misleading exactly when a game is heading for a counter draw (23-F80). The onset in that table is the same one found independently by sweeping the counter directly (23-C26) — **one mechanism seen from two directions**: the search's own horizon, and the gap between two interfaces.

## Why this is safe for the owner's PC games

The match program drives the engine directly and sends well-formed positions, so neither hazard arises in the PC's
own self-play or matches. These matter for **anyone else writing a front end**, and for analysis tools.

## Where the evidence lives

| hazard | raw evidence |
|---|---|
| refused FEN -> previous game's move | `forge-combo29/swarm/23/check21/RESULT.txt`, `forge-combo29/swarm/23/check21/refused_readyok.out` |
| illegal token -> truncated game | `forge-combo29/swarm/23/check11/RESULT_SF57.txt`, `forge-combo29/swarm/23/check11/s57.out` |
| the defence, three protocols | `forge-combo29/swarm/23/check11/gui_defence.out` |
| partial clock -> no answer, no diagnostic | `forge-combo29/swarm/23/check02/RESULT.txt`, `forge-combo29/swarm/23/check02/partial_clock.out` |
| illegal move in a move list -> full normal search of the wrong board | `forge-combo29/swarm/23/job45/RESULT.txt`, `forge-combo29/swarm/23/job45/illegal_move_repro.out` |
| related, same family | 23-C23 (refused FEN keeps previous board), 23-C24 (illegal token truncates), 23-C25 (partial clock hangs), 23-F53 (the defence), 23-F95 (the same hazard with its search numbers) |
