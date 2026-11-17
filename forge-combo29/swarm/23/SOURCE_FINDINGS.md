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
