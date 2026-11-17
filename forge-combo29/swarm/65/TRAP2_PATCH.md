# TRAP2_PATCH.md — the one-line fix for the book pre-empting drawn-root detection

Status: **measured, not merged.** The engine tree is untouched; the patch is a
diff in `patches/` plus a script that applies, builds, and verifies it.

Base: `6b98f217`. Every number below was measured on binaries built from that
commit, with all 11 documented pins verified first (see `BASE.md`).

---

## The defect

`src/uci.cpp:527` consults the opening book before the search is entered.
`src/search.cpp:2251-2268` has a drawn-root bail that answers a repetition,
fifty-move, or insufficient-material root with `score cp 0` and an **empty pv**,
without searching. That reply is the only in-band signal a caller gets that the
position is drawn.

When the position also has a book entry, the book answers first and that signal
never appears. Measured on the lock (`evidence/trap2-effect.txt`):

| root | drawn | book entry | lock reply |
| --- | --- | --- | --- |
| fifty-move (halfmove 100) | yes | yes | **BOOK e2e4** |
| threefold repetition | yes | yes | **BOOK e2e4** |
| insufficient material | yes | no | bail `cp 0`, empty pv |
| fifty-move, no entry | yes | no | bail `cp 0`, empty pv |

2 of 2 entry-bearing drawn roots were pre-empted; 0 of 4 without an entry. The
trigger is the book entry, not the drawn condition.

## The patch

`patches/trap2-drawn-root-before-book.patch`, one hunk in `src/uci.cpp`:

```diff
-                if (game_search && own_book && !book.empty() && game_ply(board) < book_depth) {
+                // A drawn root is reported by the search without searching (cp 0,
+                // empty pv). That report is the caller's only in-band signal that the
+                // position is drawn, so the book must not answer it first.
+                const bool root_drawn = board.is_repetition() || board.halfmove_clock() >= 100 ||
+                                        board.is_insufficient_material();
+                if (game_search && own_book && !book.empty() && !root_drawn &&
+                    game_ply(board) < book_depth) {
```

It is a predicate, not a reordering: the book is skipped when the search would
have bailed. That is why `search.cpp` is untouched and the node counts cannot
move.

The three conditions are copied verbatim from `src/search.cpp:2251-2252` so the
gate and the bail cannot drift apart into two different notions of "drawn".
Reusing a shared helper would be better engineering; it would also be a wider
change than this seat should make unasked.

## Verification

`bash swarm/65/scripts/patch_trap2_drawn_root.sh` — builds the base in a detached
worktree, builds it unpatched, checks pins, applies the patch, rebuilds, checks
pins again, then measures.

### Pins: unchanged by the patch

LOCK.md documents five bench depths at two net settings plus perft 5. All 11 were
verified on **both** builds (`evidence/trap2-pins-lock.txt`,
`evidence/trap2-pins-fix.txt`):

```
net    depth   expected        got  result        (identical on both builds)
true      11     312866     312866  OK
true      13     862329     862329  OK
true      16    3024920    3024920  OK
true      20   12389307   12389307  OK
true      22   34048354   34048354  OK
false     11     375354     375354  OK
false     13     907205     907205  OK
false     16    2448617    2448617  OK
false     20   13573040   13573040  OK
false     22   24506465   24506465  OK
perft5     -    4865609    4865609  OK
```

The script aborts if the unpatched build does not match the pins (so it cannot
patch an untrustworthy binary) and again if the patched build differs.

### Effect: the defect is gone and nothing else moved

`evidence/trap2-effect.txt`, same six roots on both builds:

| case | drawn | in book | lock | patched |
| --- | --- | --- | --- | --- |
| fifty-move, book entry | yes | yes | BOOK e2e4 | **bail cp 0, empty pv** |
| repetition, book entry | yes | yes | BOOK e2e4 | **bail cp 0, empty pv** |
| insufficient material | yes | no | bail cp 0 | bail cp 0 |
| fifty-move, no entry | yes | no | bail cp 0 | bail cp 0 |
| ordinary book position | no | yes | BOOK e2e4 | BOOK e2e4 |
| opening position, no entry | no | no | searches, `cp 91` | searches, `cp 91` |

```
drawn roots with a book entry pre-empted — lock 2, patched 0
[PASS] pre-emption removed by the patch
[PASS] book still fires: ordinary book position (control)
[PASS] unchanged, still searches: opening position, no entry (control)
```

The two controls matter as much as the fix: a patch that simply disabled the book
would pass the first four checks and fail the fifth.

### Traps 1 and 3 are untouched

`evidence/trap2-trap1-3.txt`, patched build:

```
white/btime  book=no  depth=22  e2e4        <- still does not book
white/wtime  book=YES depth=0   c2c4        <- control
black/btime  book=YES depth=0   c7c5        <- asymmetry preserved
black/wtime  book=no  depth=21  c7c5        <- mirror preserved
fullmove=1   Depth40 book=True  Depth41 book=True
fullmove=21  Depth40 book=False Depth41 book=True
```

Both behave exactly as on the lock, which is the point: this patch is the trap-2
fix and nothing else.

## What the patch does NOT fix

* **Trap 1** — the gate still reads only the mover's own clock, so `go btime` with
  White to move still searches rather than booking, and still has no time limit.
  That is a separate one-liner (`limits.time_ms >= 0` on either side of the
  move), and it has its own behavioural consequence (unbounded search), so it
  deserves its own measurement rather than being folded in here.
* **Trap 3** — the `Book Depth` derivation. **Not a defect**; the diagnosis was
  retracted. See `FINDINGS.md` §5.3.
* The `ponder` prediction on a book move, the `Book Variety` default, and MultiPV
  on the book path — all unchanged.

## If the owner applies this

Two things to decide that this seat did not decide:

1. **Whether a drawn root should still get a book move when the caller explicitly
   wants book play.** Some GUIs use `OwnBook true` to mean "move fast at the
   start", and a fifty-move-rule root at move 60 is not a book situation anyway —
   but a repetition at move 8 can be, in a forced-draw line. The patch chooses
   "always report drawn". The alternative is a new option, which is more surface
   than a one-line fix.
2. **Whether to share the predicate with search.cpp.** Now there are two copies of
   the three conditions. They agree today; they could drift. A shared helper is the
   better long-term shape and is intentionally outside this patch.
