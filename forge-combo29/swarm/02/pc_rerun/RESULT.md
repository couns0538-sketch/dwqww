# My findings re-run on the PC r15 build under PC20 — per finding: repaired or not, and which switch

Builds and settings, stated per line as the owner asked:
- **base** = 6b98f217, release, sha256 `e06310ec…`, settings **S14 + Threads 1 + Hash 16 + OwnBook false**
  (the base build cannot take the PC20 switches: it answers `unknown option CuckooRep` etc., which my setup
  check treats as a hard failure — that is file 5's own warning).
- **PC r15** = 6b98f217 + the file 5 patch (sha256 `d6bd72c531f785f4…`, verified before building), built with
  `-DFORGE_MATE_ALPHA_GUARD=1`, sha256 of the exe in `../pc_build/`, settings **PC20**.
- **Threads 1 on every run** (seat 04: scores above Threads 1 are not reproducible). Every search is the first
  of a fresh process, so COLD (seat 10). Interactive driver, never piped (19-F12).

## the table

| finding | what it is | base (S14) | PC r15 (PC20) | verdict |
|---|---|---|---|---|
| **S-F4** | `go` naming only the OPPONENT's clock | Black to move + `go wtime 100`: **never ends** (2001 ms, stopped by me); White + `go btime 100`: **never ends** | **identical: never ends** (2000 ms, both directions) | **NOT REPAIRED — still present on the PC build** |
| **S-F3** | `ponderhit` on a non-ponder search is a no-op | runs on, no warning | **identical** | **NOT REPAIRED** (and, per GUI_GUIDANCE, not a defect) |
| **S-F5** | button `Clear Hash` given a value answers `invalid value` | 1 warning line, both `value 0` and `value true` | **identical** | **NOT REPAIRED** |
| **S-F2** | empty `searchmoves` → `bestmove 0000` on a board with legal moves | `0000` + the restriction line | **identical** | **NOT REPAIRED** |

So on the four findings I own, the PC build changes **nothing**. That is the answer to the owner's question, and
it is worth more than a repair would have been: these four are still live on the engine the PC actually plays.

## but FORGE_FIX_GO_PARSE does repair a case in the same family — I found which

File 5's comment for that switch names the defect: *"r9 let `go wtime btime 50` lose the clock"*. I tested the
keyword-follows-keyword cases on both builds (`go_parse_cases.py`, raw `go_parse_both_builds.json`):

| go line | base ended by itself | PC ended by itself | same? |
|---|---|---|---|
| `go wtime btime 50` | yes, 1.2 ms | yes, 2.2 ms | same |
| **`go btime wtime 50`** | **NO — 2000 ms, stopped by me** | **yes, 2.4 ms** | **DIFFERENT** |
| `go wtime 50 btime` | yes | yes | same |
| `go depth wtime 50` | yes | yes | same |
| `go wtime depth 3` | yes | yes | same |
| `go movetime wtime 50` | yes | yes | same |
| `go wtime 50 depth` | yes | yes | same |

**`go btime wtime 50` is repaired by FORGE_FIX_GO_PARSE.** On the base build the `wtime` keyword is taken as
`btime`'s value, `btime` is left unusable, and because White is to move there is no usable clock at all, so the
search never ends. On the PC build the parse keeps the keyword out of the value slot and the `50` reaches
`wtime`, so the search ends in 2.4 ms.

This is a **different mechanism from S-F4** and I am not merging them: S-F4 is "the clock named belongs to the
other side", which the patch does not touch (the table above proves it). This one is "a keyword was eaten as the
previous keyword's value". Both end in the same user-visible symptom — an unbounded search on a partial clock —
which is why it took a case-by-case comparison to separate them.

**Answer to "which switch": FORGE_FIX_GO_PARSE, and only for the eaten-keyword case, not for S-F4.**

### the control that makes this table trustworthy
My first version of this comparison left `OwnBook` at its default on the base build. Two base rows then
answered from the book in ~1 ms with `info string book move c2c4` — which reads exactly like "the partial-clock
defect is gone". I added `OwnBook false` to both builds and an assertion that aborts if any `book move` line
appears in these rows. Without that control I would have reported a repair that does not exist.

## state of each finding, for the FINAL block
- S-F2: open, still on the PC build (PC20). Also independently confirmed on the base tree by seat 20.
- S-F3: open, still on the PC build; correct UCI behaviour, filed as GUI guidance rather than a defect.
- S-F4: open, still on the PC build; the most consequential of the four (silent, unbounded).
- S-F5: open, still on the PC build; one branch, not a class.
- NEW (this file): the eaten-keyword `go` parse is repaired on the PC build by FORGE_FIX_GO_PARSE, while S-F4
  is not — a distinction the owner needs, because "the go-parse fix went in" does not mean partial clocks are
  safe.

---

# S-F6, mapped across the whole `go` keyword family (72 ordered pairs)

`go_family.py` sends `go X Y 50` for every ordered pair of the nine `go` parameters, on both builds, with
Threads 1 / OwnBook false and a fresh process per case (raw `go_family_results.json`).

| outcome | count | what it means |
|---|---|---|
| base hangs, **PC ends** | **25** | repaired by FORGE_FIX_GO_PARSE |
| hangs on BOTH | 23 | not repaired — see the caution below |
| ends on both | 19 | no defect in this dimension |
| appeared to regress on PC | 5 | **NOT a regression — investigated, explained below** |

## the 25 repaired pairs (the PC build's go-parse fix, enumerated)
`go btime wtime 50`, `go btime nodes 50`, `go btime movetime 50`, `go winc wtime 50`, `go winc nodes 50`,
`go winc movetime 50`, `go binc wtime 50`, `go binc nodes 50`, `go binc movetime 50`, `go nodes wtime 50`,
`go nodes btime 50`, `go nodes winc 50`, `go nodes binc 50`, `go nodes movetime 50`, `go nodes movestogo 50`,
`go movestogo wtime 50`, `go movestogo nodes 50`, `go movestogo movetime 50`, `go mate wtime 50`,
`go mate btime 50`, `go mate winc 50`, `go mate binc 50`, `go mate nodes 50`, `go mate movetime 50`,
`go mate movestogo 50`.

The pattern: on the base tree the SECOND pair member was eaten as the first one's value whenever the first
keyword wanted a number that was not there, so the real parameter was lost. On the PC build the number reaches
the keyword it belongs to.

## the 5 "possible regressions" — investigated and dismissed, with evidence
The automated pass flagged `go wtime depth 50`, `go movetime depth 50`, `go wtime mate 50`,
`go movetime mate 50` and `go depth mate 50` as "base ended, PC did not". A 1-second grace window made that look
like the PC build got worse. It did not. With the answers inspected
(`go_family_regression_check.txt`):

| go | base | PC |
|---|---|---|
| `go wtime depth 50` | ended 1.1 ms with **1** info line: `info depth 1 … cp 350 nodes 47 pv d4c5` | still searching at 3000 ms, **24** info lines, `info depth 24 … cp 137 nodes 2774379` |
| `go movetime depth 50` | ended 2.2 ms, **3** info lines, `depth 3 cp 135 nodes 936` | searching, 24 info lines, depth 24 |
| `go wtime mate 50` | ended 1.1 ms, **1** info line | searching, 8 info lines, 4.6 M nodes |
| `go movetime mate 50` | ended 2.2 ms, **3** info lines | searching, 8 info lines, 4.6 M nodes |
| `go depth mate 50` | ended 1.1 ms, **1** info line | searching, 8 info lines, 4.6 M nodes |

So on the base build these lines produce an answer after ONE ply of a 50-ply request — the parameter was eaten,
so the engine had no real limit and returned immediately with a shallow, wrong score. The PC build correctly
reads `depth 50` and searches on. **That is a repair, not a regression**, and my 1-second window was simply too
short for a depth-50 search. Recording it because the automated table said the opposite and a reader of that
table alone would draw the wrong conclusion.

## the 23 that still hang on BOTH builds — careful, most are NOT defects
These are lines like `go btime movestogo 50`, `go winc binc 50`, `go depth wtime 50`. Both builds search on
because, after the parse, no limit belongs to the side to move or no depth was named. Whether that is a defect
depends on what a GUI means by such a line, which I cannot know. What I CAN say, and what matters for the
owner: **the PC's go-parse fix does not end these**, so a GUI that sends a keyword with no value still gets an
unbounded search on the PC build. That is the same defensive rule from GUI_GUIDANCE.md — send every clock for
the side to move — and it is still needed on the PC build.
