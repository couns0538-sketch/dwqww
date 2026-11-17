# STATUS — opening book, two-sided game audit

Last updated: run in progress. This file is the live state; `FINDINGS.md` is the
report and is only written up from numbers that are already in `evidence/`.

---

## Build and honesty pins

Built from `6b98f217` in a detached worktree.

```
cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++     # /usr/bin/c++ is a broken clang 18
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
```

**All four honesty pins confirmed on this build before any result was recorded:**

| pin | expected | measured |
|---|---|---|
| bench 11 | 312,866 | **312,866** |
| bench 13 | 862,329 | **862,329** |
| bench 16 | 3,024,920 | **3,024,920** |
| perft 5 startpos | 4,865,609 | **4,865,609** |

The same four pins were re-checked on the **patched** build (trap-1 clock gate
applied) and are identical, so the two arms are comparable.

Engine: Chess Engine Forge 6.4.24 candidate, `id author OpenAI`.

---

## Runs

| arm | purpose | games | status |
|---|---|---|---|
| `default` | Q1/Q2 at `Book Depth` 30 | 320 | **complete** |
| `depth100` | Q2 at `Book Depth` 100 (max) | 200 | **complete** |
| `depth0` | Q2 at `Book Depth` 0 (book off) | 200 | running |
| `depth6var100` | Q2 low depth, max variety | 200 | queued |
| `patched` | Q4 games on the trap-1 build | 200 | queued |

Time control for every arm: `3000+50` with 3 workers. Chosen after timing one game
at 11.5 s, so the whole set is affordable; the clock form is the one that reaches
the book.

---

## Measurements complete

| script | question | result |
|---|---|---|
| `book_paths.py` | book graph: cycles, depth, leaf ply | **16-ply DAG**, 199 leaves all at ply 16, no cycle, planted-cycle control fires, diamond control silent |
| `play_games.py` | two-sided games | 520 games so far: **0 illegal, 0 engine errors, 0 drawn-root book events, 0 re-entries**; every game exits at **ply 16** |
| `analyse_games.py` | termination / repetition / exit distribution | 0 games over threefold; 3 ply-cap stops, both inspected by hand and both far past book exit |
| `q1b_exit_quality.py` | do games leave the book into a lost position | **0 of 63 lines** ≤ −200 cp; worst exit **−50 cp** |
| `q3_book_vs_search.py` | book vs depth-18 choice, material | 589 played book moves: 13 concede material |
| `q3b_depth18_verdict.py` | are those 13 actually worse | **0 condemned at depth 18**; noise floor max 18 cp; worst gap 51 cp |
| `q4_clock_gate.py` | book from the opponent's clock alone | lock: 2 forms unbounded; **patched: all 7 forms answer**, incl. a no-book position in 0.399 s |
| `reentry_drawn.py` | can play re-enter the book on a drawn root | 122 of 199 leaves: **empty** returnable set (complete at any depth); other 77 bounded |
| `test_material_judge.py` | is the material judge trustworthy | 6 cases + negative control, all pass |

---

## Withdrawn during this audit (all apparatus, none about the engine)

1. "45 book moves lose material" — one reply ply, no recapture. Count fell to 13.
2. "27 book moves lose material" — `-side` on a bool colour. Count fell to 13.
3. "77 re-entry repetitions" — lines built from a FEN, so no move history. Phantom.
4. A threefold test that could never fire — same FEN habit. Now uses `startpos moves`.
5. Book decoder emitted `e1h1` for castling, which the engine rejects. Fixed;
   verified it did not touch the game result (all king-takes-rook moves are at
   ply 37+, book exit is ply 16).
6. Four self-test fixtures were not legal positions; two expectations were wrong.
7. A re-entry search that timed out silently, and one that reported a node cap as
   a clean null. Both replaced by a bounded result labelled as bounded.

---

## Not done, and why it is stated rather than skipped

* **`Book Variety` RNG cannot be seeded.** The book RNG is seeded from the clock
  inside the engine and is not exposed as a UCI option, so per-process seeding is
  not available. Diversity was obtained through `Book Variety` (up to 100) instead.
  Recorded as a limit in `scripts/play_games.py`.
* **The re-entry search is only partly exhaustive.** Closed completely for 122 of
  199 leaves; the other 77 are covered by a bounded search plus 1,120 games.
* **`Book Depth` derivation was not examined.** The brief says the diagnosis is
  correct and must not be patched; it was not patched and no claim is made about it.
