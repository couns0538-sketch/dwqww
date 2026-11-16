# WHICH fabrication is 19-F12 on PC r15? — not a stale bestmove, and not what `FORGE_FIX_ABORT_PUBLISH` fixes

seat 19 · area 9 · build **PC r15** (patch from FABLE_TO_swarm_5, sha256 `d6bd72c531f785f4…`) · settings
**none** (no setoption) · **Threads 1**.

## 1. The three lines

**What was asked.** 19-F12 survives to PC r15 even though the PC carries `FORGE_FIX_ABORT_PUBLISH`. Pin down
which path still fabricates: the same bestmove-from-an-unstarted-search, or a stale bestmove from a previous
search? One position, `go depth 12` then immediate quit, then check whether `a2a3` is the first root candidate
or the previous search's bestmove.

**The answer.** **Neither a stale bestmove nor a fixed literal: the engine publishes the FIRST MOVE ITS OWN
MOVE GENERATOR EMITS for the current position.** Proven by changing the position to one where `a2a3` is not
legal at all — Black to move after 1.e4. The aborted answer there is `a7a6`, and `a7a6` is exactly the first
line of that position's own `go perft 1` divide. So the fabrication is "position's first generated move", and
`a2a3` seen on startpos was a coincidence of that rule, not a hardcoded value.

**How sure.** Certain. Three separate experiments discriminate the hypotheses, plus an independent check
against the engine's own generator ordering rather than against python-chess's lexicographic ordering (which
differs, and that difference is what makes the result conclusive).

## 2. The discriminating experiments (PC r15, no setoption, Threads 1, fresh process each)

Two positions where the answer must differ if the rule is "first generated move":

- **P1** = `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1` (Black to move — `a2a3` is **not legal**)
- **P2** = `rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2` (White to move — `a2a3` **is** legal)

| experiment | result | what it rules out |
|---|---|---|
| **A.** P1 only, `go depth 12`, immediate quit | 0 `info depth` lines, `bestmove a7a6` | a fixed literal (would be `a2a3`); also confirms no search ran |
| **B.** completed startpos search (returned `d2d4`), *then* P1, aborted | 0 `info depth` lines, `bestmove a7a6` — **not** `d2d4` | **H2 (stale from the previous search): refuted.** The previous bestmove was `d2d4` and the answer is unrelated to it |
| **C.** P1 alone → `a7a6`; P2 alone → `a2a3` | two **different** answers, each specific to its position | H3 (fixed literal `a2a3`): refuted |

**The independent confirmation that settles which "first move":** python-chess's lexicographically-first legal
move for P1 is `a7a5`, but the engine answers `a7a6`. The engine's own `go perft 1` divide for P1 prints
`a7a6` first. So the fabrication reproduces *the engine's generator order*, not python-chess's ordering — which
is why `a7a6` rather than `a7a5`, and it is what makes this a positive identification rather than a guess.

## 3. Why `FORGE_FIX_ABORT_PUBLISH` does not cover it

Read from the PC patch's own comment at `src/search.cpp:65` onward:

- `FORGE_FIX_ABORT_PUBLISH` **defaults to 0** in this patch — it is not even compiled in unless a build turns
  it on. So "the PC carries the fix" is inaccurate: the PC carries the *code*, switched off.
- Its comment scopes it to "a search stopped by the clock or by `stop` **in the middle of an iteration**", and
  says explicitly: "**Searches that run to a depth or node limit are not touched** (the node counts do not
  move)."
- 19-F12 is not that path. The search never starts an iteration at all — there are **0 `info depth` lines** in
  every aborted case. The engine is answering before the search loop produces anything.

So the defect is in the **publish path for a search that never produced a result**, not in the
mid-iteration-abort publish path that `FORGE_FIX_ABORT_PUBLISH` repairs. A fix for 19-F12 would have to sit
where `bestmove` is emitted when no iteration has completed, and either search first or emit a documented
no-result answer.

## 4. Table: step | done-partly-not-done | evidence | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| reproduce 19-F12 on PC r15, none regime | done | `pcver/quitabort_pc/RESULT.txt` | aborted `a2a3`/0 nodes; searched `e2e4`/56,720; plant control YES |
| reproduce under PC20 | done | `pcver/quitabort_pc20/RESULT.txt` | aborted `a2a3`/0 nodes; searched `d2d4`/21,600; plant control YES |
| discriminate H1 vs stale vs literal | done | `pcver/f12path/RESULT.txt` | H1 (first generated move); stale and literal both refuted |
| confirm against the engine's own generator order | done | this file §2; perft-1 divide of P1 | `a7a6` is first in the engine's own divide; python-chess says `a7a5` |
| read what FORGE_FIX_ABORT_PUBLISH actually does | done | `pcbuild/forge-combo29/src/search.cpp:65-82` | defaults to 0; scoped to mid-iteration clock/`stop`; depth/node-limit searches untouched |
| find the exact emit site to point a fixer at | **not done** | — | I did not trace the `bestmove` emission path for a never-started search; §3 names the condition, not the line |
| test `go nodes` / `go movetime` / `go infinite` aborted | **partly** | job1b's base-tree run covered `go nodes` | on PC r15 I tested `go depth` only |

## 5. Finding

**19-F25 — 19-F12 on PC r15 publishes the current position's first move in the engine's generator order, not a
stale bestmove and not a literal. `FORGE_FIX_ABORT_PUBLISH` does not address it and defaults to 0.**
Black-to-move P1 aborted → `a7a6` (its own first divide move); White-to-move P2 aborted → `a2a3`; after a
completed search returning `d2d4`, an aborted search on P1 still gives `a7a6`, so nothing is carried over.
Every aborted case shows 0 `info depth` lines, so the search never begins an iteration — which is precisely
the case the patch's own comment excludes ("searches that run to a depth or node limit are not touched").

### Suspicions, not proven

- That the emit site is the same one that fires on `reserve_empty` (a clock search with no time left), since
  that is the other path known to answer without searching. Not traced.
- That the behaviour is identical on the base tree's `go nodes` path. job1b showed 0 nodes there too, but I
  did not run the P1/P2 discrimination on the base tree, so the "generator order" identification is proven
  for PC r15 only.

## 6. What I did NOT do

- I did not locate the exact source line that emits `bestmove` when no iteration completed. That is the next
  concrete step for whoever fixes it, and I would rather name the condition precisely than guess at a line.
- I did not test `go movetime` or `go infinite` aborted on PC r15.
- I did not build with `FORGE_FIX_ABORT_PUBLISH=1` to see whether the defect survives a build that actually has
  the fix compiled in. That would be worth doing: the patch says the switch exists, and my claim is about the
  default build, not about the switched-on one.

## 7. Files

`pcver/f12_which_path.py`, `pcver/f12path/RESULT.txt`, `pcver/f12path/{A_only_P1,B_search_then_P1,C_P1_alone,C_P2_alone}.txt`,
`pcver/quitabort_pc/RESULT.txt`, `pcver/quitabort_pc20/RESULT.txt`.
