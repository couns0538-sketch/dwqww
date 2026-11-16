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
