# SOURCE FINDINGS — the drawn-root bail, read from the code

Source-reading seat, branch `for-fable-and-opus/swarm-23`, folder `forge-combo29/swarm/23/`.
Read against `forge-combo29/` at `e795c6ed0` (source identical to base `6b98f217` — `git diff 6b98f217 HEAD --
forge-combo29/src forge-combo29/include` is empty), plus the PC r15 patch from
`handoff/fable-opus-combo29-all-20261114:forge-combo29/soak_all/FABLE_TO_swarm_5.md` (sha256 `d6bd72c531f785f4…`
verified before applying).

I read 23-F122/F123 and the STOP notice first. **Every claim below is about the one remaining question**: why the
zero-node path publishes a move at all, and where that path sits relative to root ordering.

Everything I measured myself used Threads 1, Hash 16, `OwnBook false`, a fresh process per line, stdout drained to
`bestmove` (19-F12 cannot intrude), and — after a fixture error of my own, §6 — a python-chess validity assertion on
every FEN before any engine call. Three builds:

| build | how | exe sha256 (mine) |
|---|---|---|
| BASE | `6b98f217` source, `-DFORGE_PORTABLE=ON`, g++ 13.3 | `bbae91a2…` |
| FIX (one hunk) | BASE with only the `root_drawn` predicate changed to r15's | `d2269320…` |
| r15 (full patch) | `pc_r15.patch` applied `-p1`, no fuzz, built with `-DFORGE_MATE_ALPHA_GUARD=1` | `34c45117…` |

(My hashes are not the handoff's — I built portable with g++ 13.3 here, not the lock's x86-64-v4/znver5 toolchain, so
the binaries differ while the source does not. Node counts on the cells below agree with the handoff's where they
overlap, which is the check that matters: E2 depth 10 = 0 nodes base, M7 = 11,390, C1 = 17,601.)

---

## 1. The bail path, and every guard on it

**One site.** `forge-combo29/src/search.cpp:2250-2271`, in `Worker::search`:

```2250:2271:forge-combo29/src/search.cpp
    // Terminal or adjudicated roots: report without searching.
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
    if (root_candidates.empty() || root_drawn) {
        int score = 0;
        if (legal.empty() && board.in_check()) score = -MateValue;
        else if (DrawJitter > 0 && (board.is_repetition() || board.halfmove_clock() >= 100)) {
            score = draw_leaf_score(board);
        }
        for (int depth = 1; depth <= max_depth; ++depth) {
            result.depth = depth;
            result.score = score;
            emit(depth, score, {});
            if (should_stop()) break;
        }
        if (!root_candidates.empty()) result.best_move = root_candidates.front();
        result.nodes = total_nodes();
        nodes_.store(local_nodes_, std::memory_order_relaxed);
        result.elapsed_ms = ...;
        return result;
    }
```

The guards, in the order the code evaluates them:

1. **`!legal.empty()`** (`:2251`) — the disjunction is gated on at least one legal move. On a mated or stalemated
   root this is false, so `root_drawn` is false there and the branch is entered by the *other* term below. The gate
   exists so that `is_repetition()` / `is_insufficient_material()` are not consulted on a terminal root, where the
   correct answer is mate or stalemate, not a draw.
2. **`board.is_repetition()`** (`:2251`) — the full-history overload, `board.cpp:1224-1233`: needs
   `key_history_.size() >= 5` (`:1225`), then scans the last `min(halfmove_, size-1)` positions for two matches of
   the current key (`:1227-1232`). Three occurrences is exactly `matches >= 2` (`:1232`). **This is the term that
   fires on every cell in the handoff's bailing set.**
3. **`board.halfmove_clock() >= 100`** (`:2251`) — the fifty-move branch. Same branch, disjoint trigger.
4. **`board.is_insufficient_material()`** (`:2252`) — `board.cpp:1250-1257`; no pawns/rooks/queens and at most one
   minor, or only same-colour bishops. This is the term 23-F71 identified on the bare-K-vs-K game.
5. **`root_candidates.empty()`** (`:2253`) — entered by the branch but *not* by the drawn arm; that is the
   `searchmoves` case, `result.restricted_root_empty` at `:2210`. It matters here only because it shares the
   `return`; it is the reason the guard's body is not simply "the position is drawn".
6. **`DrawJitter > 0`** (`:2256`) — only *re-scores* inside the branch, does not select it. Default 0
   (`src/search.cpp:39`, `int DrawJitter = 0;`; range set by `DrawJitterMax = 8` at
   `include/forge/search.hpp:85`), so on a default build the score is the literal `0` from `:2254` and the emission
   is `score cp 0`.

**What it publishes.** `result.best_move = root_candidates.front()` (`:2265`), and `result.nodes = total_nodes()`
(`:2266`) which is 0 because nothing has incremented `local_nodes_` — the whole body runs before the tree is ever
entered. `root_candidates` is filled at `:2203-2209` by walking `legal` in generator order and copying, so
`front()` is **the first move `Board::legal_moves()` produced**. There is no ordering between those two statements
and `front()`: the list is the raw generator output.

I verified that mechanically rather than by reading: `go perft 1` prints legal moves in generator order, and on all
six bailing cells in the handoff its first line equals the bail's `bestmove` — E1 `a4a3`, E2 `d5d1`, E3 `f2f3`,
E4 `h8g7`, M1 `e5e4`, M4 `c2c3`, 6 of 6. So 23-F98's "the head of the generated list" is confirmed exactly, and it
is a *copy* of the generator's order, not a coincidence of a 1-move board.

**The intended contract.** The comment states it: "Terminal or adjudicated roots: report without searching"
(`:2250`). The design intent is that a root whose game is already over needs no search and should be answered
cheaply. The contract is enshrined in two tests that will fail if you change it:

- `tests_r3fu_17/reused_searcher.cpp:71-76` asserts a fifty-move root gives `nodes == 0` **and** `score == 0`;
- `tests_r3_13/quiet_extinction.cpp:99-102,114` recomputes the very same `ruled_draw` predicate and asserts
  `info.nodes > 0` only when it is false.

So the 0-node answer is not an accident of a missing `search()` call — it is a deliberate, tested contract. **What
is not deliberate is the move.** `SearchInfo` has no field distinguishing "I searched and this is best" from "I did
not search and this is whatever the generator emitted first" (`include/forge/search.hpp:58-69`). `best_move` is a
plain `Move` with a default of `{}` and the branch fills it with a list head to avoid returning a null move to the
GUI. Nothing in the header, the branch, or the tests says that move was chosen; it is a legality placeholder, and
that is why it can be a move that walks into mate (23-F72). The contract is "we answered the protocol"; the
misfiling is that the same field carries a *judgement* on the search path and a *placeholder* on this one.

**Two other paths publish an unsearched head, and they are NOT this one.** `:2275` (explicit `go nodes 0`) and
`:2321` (hard time limit already passed, `result.best_move = root_candidates.front()`), plus `:2636` (`emergency_ply`
with `depth < 1`) and `:2640` (`best_move.is_none()` fallback). All four publish `root_candidates.front()` for the
same reason. They are distinct entry conditions, and none of them is reached on a drawn root — the drawn branch
returns first. Worth naming because a fix aimed at "the first-legal-move answer" must decide about all five sites,
and file 5's repair touches only one of them (`:2321` is covered separately by `FORGE_FIX_HARD_LIMIT_EMERGENCY`).

---

## 2. Where the guard sits relative to root ordering

**Before.** The guard at `:2253` precedes the entire iterative-deepening loop, which begins at `:2391`. Root move
ordering does not exist yet at that point, and — this is the part that matters — **root ordering in this engine is
not a pre-search sort at all**. It is lazy, inside `MovePicker`:

- the root node's picker is constructed at `search.cpp:1786`
  (`MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Main)`), i.e. on the first call into
  `Worker::search` from the ID loop;
- scoring happens in `generate_captures` (`:889-910`) and `generate_quiets` (`:917-959`), each of which ends by
  calling `sort_moves()`;
- `sort_moves()` (`:875-878`) only *marks* the list unsorted (`list_start_ = index_; sorted_ = false`);
- the real ordering is `pick_best()` (`:817-863`), which for the first four moves does a **selection** (and AVX2
  chunked max at `:830-848`) rather than a full sort, and only at `:857-859` falls back to `std::sort` of the
  remainder once the search has got that far. The comment at `:811-812` states this: "Most nodes need only the first
  few moves: select those on demand and sort the remainder once if the search gets that far."

Consequences, and they answer 23-F98's "how can a searching cell return index 5 while a bailing cell returns index
0":

- **On the bail path**, `MovePicker` is never constructed and `pick_best()` is never called, so no ordering stage
  has run. `root_candidates.front()` (`:2265`) is the generator's first legal move. That is the whole explanation of
  index 0, and it needs no separate mechanism.
- **On the search path**, the first iterate of `pick_best()` is seeded/selected, so the emitted PV is the result of
  TT move + capture scores + quiet history, which is why M7's `d5e6` sits at index 5 of its `perft 1` divide while
  the divide head is `b2b3`. The two indices measure two different things: divide index is generator order,
  `bestmove` is picker order.

So: **the guard sits before root move generation for ordering purposes and after root move generation for
legality purposes.** `legal_moves()` and `root_candidates` (`:2202-2209`) exist; ordering does not. That asymmetry is
the correct place for a terminal test — you cannot order moves you have not generated, and you cannot answer the
protocol without a legal move — but it is also exactly why the branch has nothing but raw order to publish.

---

## 3. Does `FORGE_FIX_ROOT_DRAWN` address the same path, and does its depth limit follow from the guard's position?

**Same path: yes, and it is a one-line change to the predicate.** The macro is defined at
`FABLE_TO_swarm_5.md:1041-1043` (default **1**, i.e. on) and its whole effect is the hunk at `:1882-1899`. That
file is not in this checkout — it lives on `origin/handoff/fable-opus-combo29-all-20261114` at
`forge-combo29/soak_all/FABLE_TO_swarm_5.md`, which is where I read it (line numbers below are that file's):

```
1882: +#if FORGE_FIX_ROOT_DRAWN
1886: +    const bool root_drawn = !legal.empty() && board.is_insufficient_material();
1887: +#else
1889:      const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
1890:                                                 board.is_insufficient_material());
1891: +#endif
1892:      if (root_candidates.empty() || root_drawn) {
1895: +#if !FORGE_FIX_ROOT_DRAWN
1896:          else if (DrawJitter > 0 && (board.is_repetition() || board.halfmove_clock() >= 100)) {
1899: +#endif
```

It removes guards 2 and 3 from the disjunction and leaves guards 1 and 4. Nothing else in the branch changes; `:2265`
still publishes `root_candidates.front()`, which is now only reached when the position really is terminal. **The
repair is therefore not a search change and not an ordering change — it is a re-scoping of when the branch is
allowed to fire.** That is why the node counts in `bench` do not move (the patch's own comment, `:1036-1037`) and
why it is invisible in a match that ends at the third occurrence.

**Its limit is explained by the guard's position — but the limit is NOT "shallow-only".** This is the one place
where I have to correct the premise of the question.

*The claim as given* was: the repair misses mate-in-2 at depth 4, depth 10, nodes 20k and 200k. **On the cells I
built and validated, it does not.** Fourteen randomly found boards with a genuine threefold root (validated the
F123 way: `fen.split()[:3]` key, occurrence count recomputed by independent code, asserted `== 3`, and side-to-move
at the root equal to the start FEN) and a verified mate in 2, on the repaired build:

| limit | reports `mate 2` and a verified mating move |
|---|---|
| depth 2 | 0 / 14 |
| depth 4 | 7 / 14 |
| depth 10 | 14 / 14 |
| nodes 20000 | 13 / 14 |
| nodes 200000 | 14 / 14 |

The depth-2 failures are not a defect: `mate 2` needs three plies and the ID loop starts at depth 1, so depth 2
cannot see it. Depth 4 finding 7 of 14 is an ordinary search-horizon property, not a repaired-path truncation —
**control: the same 7 boards with the move list stripped (bare FEN, so no repetition, no bail, an ordinary root)
miss the same mate in 2 at the same depth 4** (all 7 report cp ~1435-1554, none reports `mate 2`; 368-808 nodes).
So depth 4 is too shallow on those boards whether or not the root is drawn, and the gap between 7/14 and 14/14 is
the horizon, not the repair. At depth 10 and at 200k nodes the repair finds all 14. The one `nodes 20000` miss is
the same effect (`go nodes` stops at a finished depth, 23-F17/S-F34).

And directly on the question "is the fix shallow-only" — the two builds on two genuine-threefold mate-in-2 roots:

| root | limit | BASE | FIX (`FORGE_FIX_ROOT_DRAWN=1`) |
|---|---|---|---|
| `8/k7/8/1r6/2K5/6Q1/1R6/8 w - - 0 1`, root ×3, true m2 `b2b5` | depth 4 | cp 0, **0 nodes**, `b2b1` | mate 2, 740 nodes, `b2b5` |
| same | depth 10 | cp 0, **0 nodes**, `b2b1` | mate 2, 1130 nodes, `b2b5` |
| same | nodes 20000 | cp 0, **0 nodes**, `b2b1` | mate 2, 5312 nodes, `b2b5` |
| same | nodes 200000 | cp 0, **0 nodes**, `b2b1` | mate 2, 5312 nodes, `b2b5` |
| `5r2/8/6Q1/K1k5/8/3R4/8/8 w - - 0 1`, root ×3, true m2 `g6b6` | depth 4 | cp 0, **0 nodes**, `d3d1` | mate 2, 465 nodes, `g6b6` |
| same | depth 10 | cp 0, **0 nodes**, `d3d1` | mate 2, 857 nodes, `g6b6` |
| same | nodes 20000 | cp 0, **0 nodes**, `d3d1` | mate 2, 4721 nodes, `g6b6` |
| same | nodes 200000 | cp 0, **0 nodes**, `d3d1` | mate 2, 4721 nodes, `g6b6` |

Depth **4** finds it. Nodes **200,000** finds it. So on these cells the limit in the question does not reproduce,
and the *reason* is structural, not lucky: the guard sits **outside** the ID loop entirely (`:2253` vs `:2391`), so
once it is disarmed for a repetition root the root is an ordinary root at every depth and every budget. **There is
no depth at which this guard re-arms.** A "shallow-only" limit would be the signature of a guard *inside* the
search — e.g. `is_draw` at `:1425`/`:1569`, which returns 0 from a node with no move published — and that is a
different path with a different symptom (nodes counted, cp 0, PV present).

**Where a real depth-dependence does survive the repair, and why.** The *fifty-move* arm behaves differently from
the repetition arm, and I measured it because it is the same branch:

| root (halfmove forced to 100, true mate-in-2 exists) | limit | BASE | FIX |
|---|---|---|---|
| `8/8/6R1/8/5QK1/8/6k1/8 w - - 100 1` | depth 10 | cp 0, 0 nodes, `g6g5` | cp 0, 380 nodes, `f4f1` |
| same | nodes 200000 | cp 0, 0 nodes, `g6g5` | cp 0, 2432 nodes, `f4f1` |
| `1k6/8/8/R1K5/4Q3/8/8/1r6 w - - 100 1` | depth 10 | cp 0, 0 nodes, `a5a1` | **mate 4**, 933 nodes, `e4b1` |

The first board still reports `cp 0` at every budget after the repair, even though a mate in 2 exists. **That is
correct and is not the defect**: at halfmove 100 the game is drawn, so no side can improve on 0, and the search
returning 0 is right. The repair's benefit is the *node count and the move*, not the score — which is why the patch
comment (23-F43) calls the fifty-move case a formality rather than a misreport. The second board reports `mate 4`
because *it* is reachable only while the counter is still short of 100 inside the tree.

So: **the repair is on the same path, it removes the repetition arm completely, and its residual behaviour is the
fifty-move arm's, which is a *rule* correctness question (can a mate fit in the remaining slack, 23-C26's
`100 - depth` horizon) and not a defect in this branch.** If the reader has a measurement showing the repair missing
a mate in 2 at depth 4 / nodes 200k, it is either (a) a `mate 1` board — where "mate 2" is my phrasing and the
engine's is `mate 1`, and the two are not the same claim — or (b) a board whose mate is not reachable within the
remaining fifty-move slack. I could not construct (a) or (b) as a failure, and I state that rather than claim the
limit is explained.

---

## 4. What in the code contradicts the measured table

One real contradiction, and it is a reporting detail, not the effect:

**The handoff says "0 `info depth` lines".** The code emits one `info depth` line **per depth**, from the loop at
`:2258-2264`, before returning — `emit(depth, score, {})` with an empty PV. On every bailing cell I measured, the
base build prints **10 info lines at `go depth 10`** and **64 at `go nodes 20000` / `go nodes 200000`**, every one
of them `score cp 0 nodes 0 ... pv` with an empty pv tail:

```
info depth 1  seldepth 1  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 10 seldepth 10 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
```

So the accurate statement is **"0 nodes and an empty PV at every depth"**, not "0 info lines". The distinction
matters because "0 info lines" is also the signature of a *different* defect (23-F8 / 19-F12: `go` pipelined with
`quit`, which I reproduced here — `printf '...go depth 12\nquit\n'` on the base gives `bestmove a2a3` and exactly
0 info lines). A source reader who takes "0 info lines" literally would look for the abort path (`uci.cpp:553-572`,
`stop_search` joined before the worker publishes) instead of the drawn-root branch. **23-F98's index-0 observation
and every node/score/move value in the table are unaffected by this; only the "info lines" phrasing is wrong.**

Everything else in the table is consistent with the code, and in particular:

- the halfmove sweep (M1/M4 bail at 0/1/2, M7 searches at 0/1/2) is consistent *once the roots are honestly
  counted*, because the trigger is `is_repetition()` — and its scan window is the last `min(halfmove_, size-1)`
  positions (`board.cpp:1227`), i.e. the window is the **whole** reversible history, which for these fixtures is the
  full 8-ply move list. Every index in it is examined (`:1229`), so both earlier occurrences are seen regardless of
  the FEN's halfmove field. Measured on E2 with the cycle sent twice: nodes 0 and `bestmove d5d1` at FEN halfmove
  0, 1, 2, 10, 20 and 40, which produce engine halfmoves 8, 9, 10, 18, 28 and 48 — the field moves the window and
  the verdict does not. So "halfmove does not select the verdict" is what the code says too.
- the bare-FEN controls search because `key_history_` holds exactly one entry (`board.cpp:365`,
  `candidate.key_history_.push_back(candidate.key_)` in `set_fen`), and `is_repetition()` returns false at
  `key_history_.size() < 5` (`:1225`). No history, no repetition, no bail — exactly as measured.

I did **not** find any code that would explain a bail on a root whose castling-neutral cycle does not return to the
root's identity, and 23-F122 already established there are none.

**Three findings that landed while I was writing this confirm the source reading and tighten one of my sentences.**
23-F125 and 23-F133 measured the trigger as a monotone threshold: 2 occurrences search, 3/4/5/6 all bail, across
nine board-level tests. 23-F140 then refined *which* position's count matters — the position at the **end of the sent
move list**, not the game's first position — and 23-F141/23-F142 extended that to long lists and a dense middlegame.

The code agrees with all of it, and says why in one line: the guard tests `board` (`search.cpp:2251`), and `board` at
that point is *the position the search is about*, i.e. the end of the move list, not the FEN's start. `set_fen` seeds
`key_history_` with one entry (`board.cpp:365`, `:357-358`), and `apply_position` replays every listed move through
`make_move` (`uci.cpp:59-69`), each of which pushes the resulting key (`board.cpp:1104`). So `key_history_` is the
key of the FEN's position followed by one key per sent move, and `is_repetition()` compares `key_` — the current key —
against that trace. The count that decides the verdict is therefore necessarily the count of the **last** position.
**"At least three" rather than "exactly three" is also what the code says:** `:1232` is `matches >= 2`, so 4, 5 and 6
occurrences all satisfy it, with no upper bound anywhere in the predicate. My §1 wording ("the full-history
overload") was right but under-specified; 23-F140's sentence is the precise one, and the code supports it as written.

---

## 5. Direct answers

1. **The bail path and its guards:** `search.cpp:2250-2271`. Guards are `!legal.empty()` (`:2251`),
   `board.is_repetition()` (`:2251` → `board.cpp:1224-1233`), `board.halfmove_clock() >= 100` (`:2251`),
   `board.is_insufficient_material()` (`:2252` → `board.cpp:1250-1257`), `root_candidates.empty()` (`:2253`,
   the `searchmoves` arm), and `DrawJitter > 0` (`:2256`, a re-score, not a selector).
2. **What it publishes and why:** `result.best_move = root_candidates.front()` (`:2265`) with
   `result.nodes = total_nodes()` (`:2266`) = 0. `root_candidates` is a generator-order copy made at `:2203-2209`,
   and no ordering stage has run, because ordering in this engine is lazy inside `MovePicker::pick_best()`
   (`:817-863`) which the branch never reaches. Verified: `go perft 1`'s first move equals the bail's `bestmove` on
   6 of 6 bailing cells. The intended contract is "terminal root: answer the protocol without searching"
   (`:2250` comment; asserted by `tests_r3fu_17/reused_searcher.cpp:71-76` and
   `tests_r3_13/quiet_extinction.cpp:99-114`); `best_move` carries a placeholder there, with no field in
   `SearchInfo` (`include/forge/search.hpp:58-69`) marking it as unchosen.
3. **Guard vs ordering:** the guard is **before** the ID loop (`:2253` vs `:2391`) and before any ordering, but
   **after** legal-move generation (`:2202`). That is why a bailing cell returns the generator index 0 while a
   searching cell returns picker index 5.
4. **`FORGE_FIX_ROOT_DRAWN`:** same path, same branch, one predicate changed (`FABLE_TO_swarm_5.md:1041-1043`
   definition, `:1882-1899` hunk). It does not re-enter the branch at any depth, so it cannot be "shallow-only" by
   construction. On 14 validated genuine-threefold mate-in-2 roots it reports `mate 2` on 14/14 at depth 10 and at
   `nodes 200000`, 13/14 at `nodes 20000`; on the two roots I tabled against BASE it converts `0 nodes / cp 0 /
   list head` to `mate 2 / hundreds of nodes / the mating move` at depth **4** already. The residual
   depth-dependence in this branch belongs to the *fifty-move* arm, where `cp 0` is the correct answer, not to the
   repair.

---

## 6. My own fixture error, recorded

My first broad sweep reported "MISS" for moves that were in fact correct mate-in-2 alternatives — my
`mate_in_2_exact()` returned only the *first* mating move and I scored the engine's (also correct) choice as a
miss. Three of five fixtures in an earlier cut had a **mate in 1** available, so "mate 2" was never the engine's
obligation on them. Both are the 23-F123 failure mode in miniature: a validation that shares the assumption of the
thing it validates. Fixed by scoring on the reported `score mate 2` *and* membership in the full verified set of
mating moves, with every FEN asserted through python-chess before the engine is called. The §3 table is from the
corrected harness; the discarded numbers are not reported.

Also recorded: one intermediate table in this session showed BASE and FIX agreeing, which was a string-formatting
bug in my own harness (`"position fen %s" % fen` where `fen` for the M1 row was the label `"M1"`, so the engine
rejected the FEN and answered from the *previous* game). It is exactly the 19-F12 family: a rejected `position`
leaves the old board and the harness reports a plausible answer. The corrected harness asserts no
`info string invalid FEN` / `illegal move` was printed.

---

## 7. Reproduce

Source-reading pass; the only builds needed are one and three. No new files under `swarm/23/` beyond this page.

```
cd forge-combo29 && cmake -S . -B /tmp/bld -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON \
  -DCMAKE_CXX_COMPILER=g++-13 && cmake --build /tmp/bld -j8          # BASE
# FIX: change search.cpp:2251-2252 to `!legal.empty() && board.is_insufficient_material()`, rebuild
# r15: git show origin/handoff/fable-opus-combo29-all-20261114:forge-combo29/soak_all/FABLE_TO_swarm_5.md \
#        | sed -n '56,2374p' > /tmp/pc_r15.patch && patch -p1 < /tmp/pc_r15.patch   (sha256 d6bd72c531f785f4…)
```

---

# ADDENDUM — the API gap, the two tests, and the halfmove path

Three follow-ups requested in the same session. Everything here is measured on the same three builds and the same
harness discipline as §0-§7, except §A2 which is a **compilation** result: I built the two tests in question against
both sources and ran them, rather than reasoning about what they would do.

---

## A1. The `SearchInfo` gap is an API finding — what a caller can check, and whether it is documented

**The gap, stated exactly.** `SearchInfo` (`include/forge/search.hpp:58-69`) has eight fields and one flag:

```58:69:include/forge/search.hpp
struct SearchInfo {
    Move best_move{};
    Move ponder_move{};
    int score = 0;
    int depth = 0;
    int seldepth = 0;
    std::uint64_t nodes = 0;
    std::uint64_t elapsed_ms = 0;
    std::vector<Move> pv;
    // A searchmoves intersection with no legal moves is not checkmate or stalemate.
    bool restricted_root_empty = false;
};
```

The flag that exists is for the `searchmoves` case only (`:68`), and it is set at `search.cpp:2210`. **There is no
`bool searched`, no `bool root_adjudicated`, no sentinel on `best_move`.** So on the terminal branch
(`search.cpp:2253-2271`) the returned struct is populated with a *legal* move (`:2265`), a *plausible* score
(`:2254`, the literal `0`), a *depth* that equals the requested limit (`:2259-2260`), and `nodes = 0`
(`:2266`). Four of those five fields describe a search that did not happen, and the fifth is the only one that says
so.

**What a caller CAN check, and how well each works.** I measured both candidates on the UCI wire, base build,
`go depth 10`, three cases that differ only in whether the branch fires:

| case | #`info depth` lines | last info line | `pv` empty? | `nodes == 0`? | `bestmove` |
|---|---|---|---|---|---|
| E2 threefold (**BAIL**) | 10 | `… score cp 0 nodes 0 nps 0 …` | **yes** | **yes** | `d5d1` |
| E2 bare (**SEARCHES**) | 10 | `… score cp 381 nodes 7581 nps 2527000 …` | no | no | `d5b5` |
| E2 halfmove 100 (**BAIL**) | 10 | `… score cp 0 nodes 0 nps 0 …` | **yes** | **yes** | `d5d1` |

- **`pv` being empty is the reliable one, and it is reliable because of a guarantee, not a convention.** The branch
  never assigns `result.pv` — I grepped the whole span `2250-2271` and there is no `pv` write in it, so `pv` keeps its
  default-constructed empty state from `search.hpp:66` — and every *searching* path publishes a non-empty PV because
  the ID loop copies `ss->pv` at `search.cpp:2458` and a completed iteration always has `pv_length >= 1`. The
  emission itself carries the evidence: `emit(depth, score, {})` at `:2262` passes an empty vector, so the wire line
  ends in a bare `pv` token with nothing after it.
  **I tested the guarantee against the case most likely to break it** — a search that is *stopped* mid-iteration,
  which is where a truncated PV would naturally appear. Fine sweep of the stop delay on startpos: at 0.8/1.0/1.2/1.5/
  1.8 ms the engine emits 4/5/5/6/6 info lines with 404/1,001/1,001/1,703/1,703 nodes and **`pv` non-empty in every
  one**. At 0.5 ms it emits **no info line at all** (`bestmove a2a3`, 0 lines). So on this build there is no state in
  which an info line carries `nodes > 0` and an empty `pv` — the dichotomy is clean: **info line present ⇒ `pv`
  non-empty; `pv` empty ⇒ nothing was searched.**
- **`nodes == 0` also works on these cells, but it is the weaker test and I would not rely on it alone.** It is
  correct here, and it is correct by construction (`total_nodes()` at `:2266` before the tree is entered). But zero
  nodes is also what a *searched* root can legitimately report under three other conditions in the same function:
  `go nodes 0` (`:2275`), an empty clock reserve whose TT hit answers unsearched (`:2301-2308`), and the
  hard-limit-passed path (`:2321`). All of those set `nodes = 0` and publish a head, and none of them is the drawn
  branch. So `nodes == 0` says "nothing was searched" — which is true — but it does not say *why*, and a caller that
  treats it as "this position is drawn" will be wrong on a clock-exhausted answer.
- **`depth` is worse than useless as a discriminator — it is actively misleading.** The loop at `:2259` emits once per
  depth up to `max_depth`, so the reported depth is whatever the caller asked for:

| `go depth` | info lines | last depth reported | nodes | bestmove |
|---|---|---|---|---|
| 1 | 1 | 1 | 0 | `d5d1` |
| 4 | 4 | 4 | 0 | `d5d1` |
| 10 | 10 | 10 | 0 | `d5d1` |
| 30 | 30 | 30 | 0 | `d5d1` |
| 64 | 64 | 64 | 0 | `d5d1` |

  A `go depth 64` on a threefold root reports **`depth 64`, `seldepth 64`, `nodes 0`, `cp 0`**. A GUI that displays
  "depth 64, score 0.00" is showing the user a fully-searched drawn position. That is the sentence the owner needs:
  **the engine reports the maximum depth it was asked for, on a search that visited no nodes, and there is no field
  that says so.**

**Is either documented? No.** `grep` over `README.md`, `LOCK.md` and every file under `docs/` finds no mention of
`info depth`, of PV semantics, or of `SearchInfo` at all. The only place the empty-PV behaviour is written down is
inside this engine's own source comment at `:2250` ("Terminal or adjudicated roots: report without searching"), which
is not visible to a caller. So a consumer of this engine has **no documented way** to distinguish the two cases, and
the two things it might try are (a) an undocumented invariant that happens to hold, and (b) a heuristic that is true
here but false for three other unsearched paths.

**A third case a caller must not confuse with the bail, found by the same control.** `go nodes 0` and `go nodes 1`
emit **zero** info lines and answer `bestmove a2a3`; `go nodes 42` emits one line with 26 nodes and a non-empty PV.
So there are three distinct wire shapes for "little or nothing was searched", and only one of them means *drawn*:

| wire shape | what it is | site |
|---|---|---|
| info lines present, `pv` empty, `nodes 0`, `cp 0` | **the drawn-root branch** — a real adjudication | `search.cpp:2253-2271` |
| **no** info lines, `bestmove` `a2a3` | nothing searched: `go nodes 0/1`, or `go`+`quit` (19-F12) | `:2275`; `uci.cpp:553-572` |
| info lines present, `pv` non-empty | genuinely searched | `:2458` |

The empty-PV invariant is what separates row 1 from row 3, and nothing separates row 1 from row 2 *except* the
presence of the info lines — which is why §4's correction ("0 info lines" is the wrong description of the bail) is
not pedantry: it is the one field that distinguishes an adjudicated draw from a search that never started.

**The API change that would close it** is one field — something like `bool searched` or an enum
`RootDisposition { Searched, Terminal, Emergency }` — set at `:2253` alongside `best_move`, and one extra token on
the `info` line when the disposition is not `Searched`. I am not proposing to write it here; the point is that this
is a one-field fix and that **without it the protocol cannot express the difference**, which is why 23-F72's
"`cp 0`, `0` nodes, and a move that walks into mate in 5" was invisible to every harness in this project for hours.
Note the cost of *not* changing it, measured elsewhere in this folder: the 23-F122 fixture bug and my own §6 FEN bug
are both instances of a caller inferring engine state from fields that do not mean what they look like.

---

## A2. The two tests encode the contract — quoted, and what a repair must keep true

I built both test files against **both** sources (base and the `FORGE_FIX_ROOT_DRAWN=1` predicate change) with the
same flags, and ran them. This is a compilation result, not an inference.

### `tests_r3fu_17/reused_searcher.cpp:71-76` — **BREAKS under the repair**

```71:76:forge-combo29/tests_r3fu_17/reused_searcher.cpp
    const forge::Board drawn = board_from(Drawn);
    expect(!drawn.legal_moves().empty() && drawn.halfmove_clock() >= 100, "drawn root is a fifty-move position");
    const forge::SearchInfo drawn_info = searcher.search(drawn, limits, false);
    std::cout << "drawn nodes " << drawn_info.nodes << " score " << drawn_info.score << '\n';
    expect(drawn_info.nodes == 0, "drawn root does not count old helper nodes");
    expect(drawn_info.score == 0, "drawn root scores a draw");
```

with `Drawn = "8/8/8/8/4k3/8/3R4/4K3 w - - 100 1"` (`:37`). Note the position: halfmove 100, **no repetition**, so
this is the other arm of the same disjunction.

| source | result | output |
|---|---|---|
| BASE | **PASS**, exit 0 | `drawn nodes 0 score 0` — all 13 assertions ok |
| FIX (`FORGE_FIX_ROOT_DRAWN=1`) | **FAIL, exit 1** | `drawn nodes 380 score 0` → `FAIL drawn root does not count old helper nodes` |

The `score == 0` half **still passes** under the repair — the fifty-move position really is drawn, so the search
returns 0 anyway (as §3 showed: `cp 0` at every budget on a halfmove-100 root). **What fails is `nodes == 0`.** So the
assertion that actually encodes the contract is `drawn_info.nodes == 0`, and its stated *purpose* is narrower than
its effect: the name says "does not count old helper nodes", i.e. it is guarding against a stale node count leaking
from the earlier Threads-4 searches in the same `Searcher`, but the only way to satisfy it is to not search at all.
**A repair that searches a halfmove-100 root cannot pass this test as written**, even though the repair is correct
and the score is unchanged. Someone should know that before writing the patch: the test is protecting a
resource-counting invariant with a mechanism (do not search) that is stronger than the invariant needs, so the fix is
to re-point it at the real invariant — e.g. assert `drawn_info.nodes < <the previous search's node count>` or assert
`nodes == 0 || nodes < stale_count`, i.e. "no *stale* nodes", which is what the name claims.

### `tests_r3_13/quiet_extinction.cpp:99-114` — **does NOT break, and it is a latent guard, not a live one**

```99:114:forge-combo29/tests_r3_13/quiet_extinction.cpp
        const forge::MoveList legal = board.legal_moves();
        const bool ruled_draw = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                                    board.is_insufficient_material());
        ...
        bool ok = info.depth == 10;
        if (legal.empty()) ok = ok && info.best_move.is_none();
        else {
            ok = ok && listed(legal, info.best_move);
            forge::Undo undo;
            ok = ok && board.make_move(info.best_move, undo);
            if (!ruled_draw) ok = ok && info.nodes > 0;
        }
```

| source | result | output |
|---|---|---|
| BASE | **PASS**, exit 0 | `searches 200 illegal 0 nodes 3744188` |
| FIX | **PASS**, exit 0 | byte-identical output (`diff` empty) |

**It passes because it never reaches the branch.** This test re-derives `ruled_draw` with *the same predicate the
engine uses* and then only requires `nodes > 0` when the predicate is false — so it agrees with whatever the engine
does by construction. I instrumented the 200 positions it actually walks and counted:

| over the 197 `walked(...)` positions + 3 hand-picked | count |
|---|---|
| with legal moves | 197 |
| `is_repetition()` true | **0** |
| `halfmove_clock() >= 100` | **0** |
| `is_insufficient_material()` | **0** |
| terminal (no legal move) | 0 |

Zero of 200 satisfy any disjunct, so `ruled_draw` is false everywhere, `nodes > 0` is required everywhere, and the
assertion is never exercised in the state it was written to permit. **This is the 23-F123 pattern again, in a test**:
a check that shares the definition of the thing it checks cannot disagree with it, and here it also never reaches the
case that would make the shared definition matter. The three hand-picked positions (`4k3/8/8/3p4/3P4/8/8/4K3`,
`4k3/8/8/8/8/8/8/4QK2`, startpos) are equally clean.

**So the answer to "what must a repair keep true":** of the two tests, only `reused_searcher.cpp:71-76` constrains a
repair, and what it constrains is `nodes == 0` on a **halfmove-100** root — not the repetition arm at all. The
repetition arm is untested by both. A patch that fixes only the repetition case (as r15 does for repetition) and
leaves the fifty-move case alone would pass both tests; r15 removes *both* arms, which is why it fails the first.
That is a design decision, not a bug, but it is invisible from the tests and should be stated in the patch.

---

## A3. Is the branch reachable from the halfmove counter alone? — confirmed on the same site, not inferred

**Yes, and it is the same statement, same line, same disjunction.** The counter is the second operand of the
`||` at `search.cpp:2251`, so there is no second code path to find: the branch is entered by whatever makes that
disjunction true. I confirmed reachability three ways rather than by reading the line.

1. **By construction:** at `:2251` the three operands are `||`-joined inside one `root_drawn` expression, and the
   `if` at `:2253` tests that one variable. Every other `halfmove_clock()` use in `search.cpp` is inside the tree,
   not at the root — the full list above line 2251 is `:1302` (`is_draw`'s fifty-move leaf rule), `:1317`
   (`draw_leaf_score`), `:1426`/`:1570` (MaxPly), `:1444-1447` and `:1594-1597` (the `near50` TT guards),
   `:1640` (TT cutoff blocked near 50), `:1467`/`:1656` (eval damping), `:1681`, `:1806`, `:1841`, `:1991` (the
   `halfmove + depth < 100` pruning guards) and the TT stores. The root-level tests are exactly `:2251` and `:2256`,
   both the same disjunction.
2. **On the wire, with no history at all** — so repetition cannot be the trigger: bare FEN
   `1K6/8/8/3R4/8/8/8/k7 w - - 100 1`, no move list, `go depth 10` → `10` `info depth` lines, `nodes 0`,
   `score cp 0`, `bestmove d5d1`. The same FEN at halfmove 0 searches 7,581 nodes. The only field that differs is the
   counter, so the counter alone reaches the branch. (This also reproduces 23-F43's halfmove-150 case and 23-C26's
   onset, from the source side.)
3. **By the repair's own behaviour on it:** the FIX build on that root gives `nodes 380, score cp 0` at depth 10 and
   `2,432` nodes at `go nodes 200000` — non-zero nodes with the same `cp 0` score, i.e. the branch stopped firing and
   the search ran and reached the same (correct) conclusion. That is only possible if the counter was what had been
   firing.

**One consequence worth flagging, because it cuts against a natural assumption.** §3 reported that a halfmove-100
root can still show `cp 0` after the repair, and I said that was correct. It is — but the *reason* is the fifty-move
**leaf** rule at `:1302` (`if (board.halfmove_clock() >= 100) { return !board.in_check() || board.has_legal_move(); }`),
not the root branch. So after the repair, the same `cp 0` arrives by a different route with `nodes > 0` and a real
PV. **That is precisely the case where a caller using `nodes == 0` as its discriminator would be correct and a caller
using `score == 0` would be wrong**, which is the concrete argument for A1's one-field fix.

---

## A4. Summary of the three answers

| # | question | answer |
|---|---|---|
| 1 | Can a caller tell an unsearched root from a searched one? | **`pv` empty** is the reliable signal (guaranteed: no `pv` write in `:2250-2271`, non-empty on every searching path via `:2458`, and I confirmed it stays non-empty even for a search stopped after 0.8 ms); **`nodes == 0`** works here but is also true for three other unsearched paths (`:2275`, `:2301-2308`, `:2321`); **`depth` is actively misleading** and reports the requested limit up to 64. Neither signal is documented anywhere in the repo. And the bail is distinguishable from `go nodes 0/1` (no info lines at all) **only** by the info lines being present, which is why the §4 correction matters. |
| 2 | What do the two tests require of a repair? | `reused_searcher.cpp:71-76` requires `nodes == 0` on a **halfmove-100** root and **fails** under r15 (380 nodes); its `score == 0` half still passes. `quiet_extinction.cpp:99-114` passes unchanged and never reaches the branch (0 of 200 positions are drawn, measured), so it is a latent guard that agrees with the engine by construction. The repetition arm is untested by both. |
| 3 | Reachable from the counter alone? | **Yes** — same `\|\|` at `:2251`, same `if` at `:2253`; confirmed by bare FEN at halfmove 100 giving `nodes 0 / cp 0` with no history at all, and by the repaired build searching that same root (380 nodes, same `cp 0`, which arrives via the leaf rule at `:1302`). |

No new files; this addendum is appended to `forge-combo29/swarm/23/SOURCE_FINDINGS.md`.

---

# ADDENDUM B — GUI advice, and a second protocol defect filed separately

Two items requested after the owner read the first addendum. All measurements on the same base build, Threads 1,
Hash 16, `OwnBook false`, drained to `bestmove`.

The first is advice and is now ordered to **lead with the case that proves the point** rather than the one that is
easiest to state. The second was originally written as a footnote under the discriminator; it is a distinct defect
with a distinct symptom and its own cause, so it is filed on its own below.

---

## B1. What a GUI should do — leading with the bare-kings case

### The case that makes the argument: a legal move, in a finished game

Bare K vs K, `8/8/8/8/8/8/8/k2K4 w - - 14 72`, `go depth 10`:

```
info depth 1  seldepth 1  score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
…
info depth 10 seldepth 10 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
bestmove d1c1
```

**The engine answers `d1c1` — a legal move — in a position that is a dead draw by insufficient material, with
`cp 0`, `nodes 0` and an empty PV.** Nothing in the `bestmove` line says the game is over. A GUI that plays it
continues the game; both kings shuffle until the fifty-move counter or the GUI's own draw detection stops it. That
is 23-F71's finding arriving from the protocol side, and it is the sharpest available demonstration of the API gap:
**the protocol has no way to say "no move was chosen", so the engine says "here is a move" instead.**

Two properties make this worse than a merely suboptimal move, and both are in the code:

- the move is `root_candidates.front()` (`search.cpp:2265`) — the generator's first legal move, never scored and
  never compared against any alternative, so it carries no evaluation at all;
- the score beside it is the literal `0` from `search.cpp:2254`, and the depth beside *that* is the depth the
  caller asked for (`:2259-2260`). Three of the four fields a GUI displays describe a search that did not happen.

In a won position the same mechanism can be actively harmful, not merely wasteful: 23-F72 measured the base playing
into a forced mate in 5 against itself while reporting `cp 0` with `nodes 0`.

### What to do, in priority order

1. **Do not play the move in a game.** This is the one thing that is definitely wrong on this path. Nothing about
   the answer is a judgement; playing it converts an adjudication into a bad move.
2. **Check the `pv`, not the move and not the score.** An empty `pv` on an `info` line means the engine adjudicated
   the position and did not search. That is the signal, and it is reliable (see below for why it holds, including
   under MultiPV).
3. **Check `0000` next, but do not read it as "game over".** A null move is printed as `0000` by `uci.cpp:562-563`.
   Two different things produce it: a genuinely terminal root (checkmate or stalemate, where `legal` is empty), and
   a `searchmoves` restriction that names no legal move, which shares this branch through
   `root_candidates.empty()` at `:2253` and sets `restricted_root_empty` at `:2210`. Measured:

   ```
   go depth 4 searchmoves a1a2      (on a board where a1a2 is not legal)
   info string searchmoves restriction has no legal root moves
   info depth 1 seldepth 1 score cp 0 nodes 0 … pv
   bestmove 0000
   ```

   So `0000` means "no move was selected", and the two causes separate by the score — checkmate arrives as
   `score mate 0`, the empty restriction as `cp 0` — plus an `info string` diagnostic for the restriction case.
4. **Report the game state, not the move.** On the empty-`pv` path the engine has adjudicated a draw by repetition,
   fifty-move or insufficient material, and **which of the three is not on the wire**. Only the caller's own `board`
   state has it. A GUI that owns the position should apply its own draw detection and say so.
5. **Distinguish it from "no search happened".** `go nodes 0` / `go nodes 1` and the `go`+`quit` path emit **zero**
   `info depth` lines and answer `a2a3`. If there is no `info depth` line at all, the answer is not an adjudication —
   it is a search that never started. An adjudicated draw is a fact about the position; a never-started search is a
   harness fault, and conflating them is how 19-F12 hid for hours.

### The matrix a GUI actually has to discriminate

One run each, `go depth 10`, base build:

| root | `bestmove` | `#info` | last score | nodes | `pv` |
|---|---|---|---|---|---|
| checkmated | `0000` | 10 | `mate 0` | 0 | **EMPTY** |
| stalemate | `0000` | 10 | `cp 0` | 0 | **EMPTY** |
| `searchmoves` naming no legal move | `0000` | 10 | `cp 0` | 0 | **EMPTY** |
| **bare K vs K** | **`d1c1`** | 10 | `cp 0` | 0 | **EMPTY** |
| threefold (repetition) | **`d5d1`** | 10 | `cp 0` | 0 | **EMPTY** |
| fifty-move (halfmove 100) | **`d5d1`** | 10 | `cp 0` | 0 | **EMPTY** |
| searched (same board, no history) | `d5b5` | 10 | `cp 381` | 7,581 | present |

Which yields four wire shapes, and only one of them is a search result:

| wire shape | meaning | action |
|---|---|---|
| `0000` + `mate 0` | checkmate | game over — report the result |
| `0000` + `cp 0` | stalemate, or an empty `searchmoves` | game over or caller's own restriction fault |
| legal move + **empty `pv`** + `nodes 0` | **adjudicated draw** — repetition, fifty-move, insufficient material | **do not play; report the draw** |
| **no** `info depth` lines | the search never ran | harness fault, not a position fact |
| `pv` present | genuinely searched | play the move |

**The one sentence for the owner:** *an empty `pv` on an `info` line means the engine adjudicated the position and
did not search; the `bestmove` beside it is the first legal move in generation order and must not be played; `0000`
means no move was selected (checkmate, stalemate, or an empty `searchmoves` restriction — the score and the preceding
`info string` tell you which); and no info lines at all means the search never ran.*

**Why the `pv` test is the right one to standardise on**, given that `nodes == 0` also happens to be true here: it is
guaranteed rather than incidental. There is no write to `result.pv` anywhere in the branch
(`search.cpp:2250-2271` — checked by grep, not by inference), so it keeps its default-empty state from
`search.hpp:66`, while every searching path assigns it at `:2458`. And I tried to break the guarantee with the case
most likely to: a search **stopped** mid-iteration. At 0.8/1.0/1.2/1.5/1.8 ms the engine emits 4/5/5/6/6 info lines
with 404/1,001/1,001/1,703/1,703 nodes and a **non-empty `pv` every time**; at 0.5 ms it emits **no info line at
all**. `nodes == 0`, by contrast, is also true of three other paths that are not adjudications (`:2275`,
`:2301-2308`, `:2321`), so a GUI that keys on it alone will misread a clock-exhausted answer as a drawn position.

---

## B2. FILED FINDING — MultiPV silently degrades to one line per depth on the bail path

*(Filed as its own finding rather than as a footnote to the discriminator. It has its own cause, its own symptom,
and its own caller-visible failure. **Numbering note:** I am the source-reading seat and `23-F153` onward belongs to
the measuring seat's sequence, so I am not minting an F-number here — I have called it `23-SRC-B2` and left the
F-assignment to the coordinator rather than take a number that would collide.)*

**The finding.** With `MultiPV N > 1` on a root that the drawn-root branch adjudicates, the engine emits **one line
per depth, with only `multipv 1` ever appearing**, instead of `N` lines per depth. A caller that asked for three
lines per depth gets one, forever, and nothing in the output says why.

Measured, `go depth 10`, MultiPV swept:

| root | MultiPV | `#info depth` lines | nodes | `pv` empty? | `multipv` field present? | bestmove |
|---|---|---|---|---|---|---|
| E2 threefold (**BAIL**) | 1 | 10 | 0 | **yes** | no | `d5d1` |
| E2 threefold (**BAIL**) | 2 | **10** | 0 | **yes** | yes | `d5d1` |
| E2 threefold (**BAIL**) | 3 | **10** | 0 | **yes** | yes | `d5d1` |
| E2 bare (**SEARCHES**) | 1 | 10 | 7,581 | no | no | `d5b5` |
| E2 bare (**SEARCHES**) | 2 | **20** | 16,916 | no | yes | `b8c7` |
| E2 bare (**SEARCHES**) | 3 | **30** | 23,178 | no | yes | `b8c7` |
| M1 threefold (**BAIL**) | 1 / 2 / 3 | 10 / 10 / 10 | 0 | **yes** | — | `e5e4` |

A searching root emits `depth × multipv` lines (10 → 20 → 30). **The bail emits exactly 10 regardless of MultiPV** —
it never multiplies. Per depth, on the bail root at MultiPV 3 (`go depth 4`):

```
info depth 1 multipv 1 score cp 0 seldepth 1 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 2 multipv 1 score cp 0 seldepth 2 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 3 multipv 1 score cp 0 seldepth 3 nodes 0 nps 0 hashfull 0 time 0 pv
info depth 4 multipv 1 score cp 0 seldepth 4 nodes 0 nps 0 hashfull 0 time 0 pv
```

**The cause, and it is the same structural fact as §1-§2: the guard returns before the MultiPV machinery is built.**

- the alternate-line workers are constructed at `search.cpp:2384`, `if (multipv > 1 && is_main())`;
- the emit that consumes them is gated at `:2462`, `if (alt_worker && !result.pv.empty())`;
- **the bail returns at `:2271`, 113 lines before either line is reached.**

So `alt_worker` is null and `result.pv` is empty — *both* halves of the `:2462` gate are false, and the block could
not run even if the workers had been constructed. The lines the branch does emit come from the plain
`emit(depth, score, {})` at `:2262`, which reads `pv_index` from its initialiser at `:2222` (`int pv_index = 1;`) and
never updates it. There is no special-casing of MultiPV on this path; the branch simply exits before the feature
exists.

**The caller-visible failure.** A GUI that requested `MultiPV 3` expects three lines per depth, and the natural
implementations do one of two wrong things: it waits for alternate lines that never arrive (a stalled PV panel, or a
timeout that reports the engine as unresponsive), or it pads the table with the previous position's entries because
it indexes by `multipv` into a fixed three-row view. Either way the display is wrong while every individual line is
arithmetically correct — reporting one line is the honest answer when there is one answer.

**Why this is worth filing separately from B1's discriminator.** It is not a symptom of the empty PV; it is a second
consequence of the same positional fact (the guard sits before everything the search would have set up). The
discriminator survives it — that is the reassuring half — but a reader who only knows "check the pv" would not know
why their MultiPV panel has gone quiet, and might reasonably conclude the engine had crashed or hung.

**The advice does not change: still check the `pv`.** The `pv`-empty test resolves this case completely, because it
tells the GUI the position is adjudicated and that **no alternate lines exist to wait for** — so the correct action
is to stop waiting, render a single adjudicated row, and report the draw. That the discriminator closes a defect it
was not designed for is the strongest evidence that it is the right signal to standardise on: it is a fact about
whether the search ran, so everything downstream of "did the search run" — line count, PV length, depth, nodes —
follows from it rather than having to be checked separately.

**Discriminator still holds under MultiPV: 10 of 10 bailing cells** across two boards × MultiPV 1/2/3 show an empty
PV, and no searching cell does. The caveat I raised in the first addendum (`:2520-2531` untested) is closed.

---

## B3. Status of the additions

| item | status |
|---|---|
| bare-kings case | leads B1 — legal `d1c1`, `cp 0`, `nodes 0`, empty `pv`, nothing on the wire saying the game is over |
| GUI advice | four wire shapes in B1; standardise on the empty `pv`, use `0000` + score to split terminal from `searchmoves`, treat zero info lines as a harness fault |
| `pv`-empty discriminator under MultiPV | **holds** — 10 of 10 bailing cells across 2 boards × MultiPV 1/2/3, no searching cell; survives the mid-iteration `stop` sweep |
| MultiPV on the bail path | **filed as `23-SRC-B2`** — one line per depth instead of `multipv`; `alt_worker` built at `:2384`, bail returns at `:2271`, `:2462` gate false on both halves |

No new files; appended to `forge-combo29/swarm/23/SOURCE_FINDINGS.md`.
