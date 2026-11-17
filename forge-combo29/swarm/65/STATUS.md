# STATUS.md — swarm/65, opening-book characterisation

Branch `for-fable-and-opus/swarm-65`, work in `forge-combo29/swarm/65/`.
Base `origin/integrate/combo29-all`. Engine build: `-DCMAKE_BUILD_TYPE=Release
-DFORGE_MARCH=native`, g++ 13.3.0, x86-64 with AVX-512F/BMI2.

## State

**Complete**, including the two follow-ups: a measured comparison of four
`game_ply` derivations (which retracted the `Book Depth` defect), and drawn-root
pre-emption split by drawn condition and by book state. All seven original
questions answered with measurements; deliverables written; whole audit
re-runnable in one command.

Deliverables in `forge-combo29/swarm/65/`:

| file | content |
| --- | --- |
| `FINDINGS.md` | source map with line numbers, all measurements, defect table, fix arithmetic, and one retraction |
| `BOOK_WIRE.md` | exact reply shapes, the deadlock proof, the `go`-form matrix, harness rules |
| `STATUS.md` | this file: claim → command index, what is not done |
| `scripts/` | 27 files: 3 C++ probes, 1 shared UCI driver, 1 SEE self-test, 1 pipeline runner, 1 `.gitignore`, and 20 Python scripts (several are imported as helpers by the others) |
| `evidence/` | 26 captured outputs, one per step of `run_all.sh` |

## Reproduce

```bash
cd forge-combo29
bash swarm/65/scripts/run_all.sh          # ~5 min, includes building three patched binaries
```

The runner builds the engine, the three C++ probes, and three patched copies of
the tree (for the `game_ply` comparison), then runs every measurement in order. It
**aborts** on a failed SEE self-test, a failed score-absence check, or a failed
drawn-root check, so a green run means those three load-bearing assertions held.

## Claim → command index

Every claim in `FINDINGS.md` and `BOOK_WIRE.md`, with the exact thing that
produces it. All commands run from `forge-combo29/`.

### Book exists, where, keyed how

| claim | command | evidence |
| --- | --- | --- |
| 2616 entries, 2230 keys, 2520 distinct key-move pairs, 96 duplicates | `/tmp/book_census` | `evidence/census.txt` |
| key agrees with `chess.polyglot` on 2429/2429 walked positions | `python3 swarm/65/scripts/q7_soundness.py /tmp/book_full.txt` | `evidence/soundness.txt` |
| key agrees on 60/60 random en-passant positions | `python3 swarm/65/scripts/key_conformance.py` | `evidence/key_conformance.txt` |
| walk reaches 2230/2230 book keys | `python3 swarm/65/scripts/coverage_check.py` | `evidence/coverage.txt` |
| consult site, gate, two-line emit | `sed -n '369,391p' src/uci.cpp` | quoted in `FINDINGS.md` §1.2 |

### Wire shapes

| claim | command | evidence |
| --- | --- | --- |
| two lines, 0 info depth, no score | `python3 swarm/65/scripts/q3_score_absence.py` | `evidence/score_absence.txt` |
| naive `info depth` reader times out on book, passes off-book | `python3 swarm/65/scripts/q2_cost_and_deadlock.py` | `evidence/cost_deadlock.txt` |
| five `go` forms split, per position | `python3 swarm/65/scripts/q1_go_matrix.py` | `evidence/go_matrix.txt` |
| book p50 ~0.02 ms vs search p50 ~440 ms (four orders of magnitude) | `python3 swarm/65/scripts/q2b_latency.py --runs 200` | `evidence/latency.txt` |
| 154/154 castle positions exercised, 0 king-takes-rook strings on the wire | `python3 swarm/65/scripts/q1b_castles.py` | `evidence/castles.txt` |

### Interactions

| claim | command | evidence |
| --- | --- | --- |
| pre-emption follows the book entry, not the drawn condition: 2/2 with an entry, 0/4 without | `python3 swarm/65/scripts/q9_drawn_conditions.py` | `evidence/drawn_conditions.txt` |
| pre-emption never happens with `OwnBook false`: 6/6 drawn roots answer `cp 0` + empty pv | `q9_drawn_conditions.py` book-off arm | `evidence/drawn_conditions.txt` |
| `game_ply` sums the counter implied by the input plus the moves `position` appended; exact 14/14 | `python3 swarm/65/scripts/q8c_derivation_compare.py` (builds three patched binaries) | `evidence/game_ply_derivations.txt` |
| the two candidate `game_ply` "fixes" are worse: NAIVE 4/14 wrong, HYBRID 2/14 | `q8c_derivation_compare.py` | `evidence/game_ply_derivations.txt` |
| the lock is exact on 2486/2486 real book lines | `python3 swarm/65/scripts/q8_game_ply_fix.py` | `evidence/game_ply_fix.txt` |
| the naive fix books 8/8 bare-FEN positions past Book Depth | `python3 swarm/65/scripts/q8b_fix_cost.py` | `evidence/game_ply_fix_cost.txt` |
| 2/3 drawn roots pre-empted in the first, narrower sample | `python3 swarm/65/scripts/q4c_drawn_root.py` | `evidence/drawn_root.txt` |
| MultiPV ignored on the book path | `python3 swarm/65/scripts/q4_interactions.py` block B | `evidence/interactions.txt` |
| `go btime` with White to move searches | transcript in `FINDINGS.md` §4.3 | reproduced inline |
| clock magnitude irrelevant (`wtime 0`, `movetime 0` both book) | `q4_interactions.py` block C | `evidence/interactions.txt` |
| `searchmoves` and `mate` also exclude the book | `q4_interactions.py` block D | `evidence/interactions.txt` |
| boundary: ply 15 book → ply 16 search, one ply wide | `python3 swarm/65/scripts/q5_boundary.py --plies 24` | `evidence/boundary.txt` |
| `Book Depth` gate: exact on 14/14 cases (claim of a defect retracted, see `FINDINGS.md` §5.3) | `python3 swarm/65/scripts/q8c_derivation_compare.py` | `evidence/game_ply_derivations.txt` |
| variety 0 deterministic, variety 30 not, both across and within process | `q4b_gates_and_rng.py` block B, `q6_determinism.py` | `evidence/gates_rng.txt`, `determinism_v{0,30}.txt` |

### Soundness

| claim | command | evidence |
| --- | --- | --- |
| SEE is correct (6 hand-computed cases + regression) | `python3 swarm/65/scripts/see_selftest.py` | `evidence/see_selftest.txt` |
| 0/2520 illegal, 0/2429 bad FEN, 0/2429 key mismatch | `q7_soundness.py /tmp/book_full.txt` | `evidence/soundness.txt` |
| 0/135 SEE flags survive engine verification at depth 12 | `python3 swarm/65/scripts/q7b_verify.py --depth 12` | `evidence/soundness_verified.txt` |
| max gap 103 cp, 0/2520 above 150 cp | `python3 swarm/65/scripts/q7c_exhaustive_gap.py --depth 10` | `evidence/gap_depth10.txt` |
| noise floor up to 66 cp | `python3 swarm/65/scripts/q7d_noise_floor.py 10` | `evidence/noise_floor.txt` |
| outliers shrink with depth (horizon artifact) | `python3 swarm/65/scripts/q7e_deep_check.py --depths 10,14,18` | `evidence/deep_check.txt` |

## Traps for other seats (measured here, in rank order)

1. **`go btime` with White to move does not book.** The gate tests the mover's own
   clock (`src/uci.cpp:108-109`, `371`). Any asymmetric clock harness sees the book
   on one colour only. This is why "the clock form hits the book" is not safe to
   tell a seat as a rule.
2. **The book pre-empts drawn-root detection.** A drawn root with the book on emits
   a book move with no score and no pv; with the book off it emits `score cp 0` and
   an empty pv. The deciding variable is the **book entry**, not the drawn
   condition: 2/2 entry-bearing roots pre-empted, 0/4 without, and 0/6 with
   `OwnBook false`.
3. **A reader that waits for `info depth` deadlocks on every book move.** Wait for
   `bestmove`, with a timeout; the book path is ~0.02 ms and the search path is
   hundreds of ms, so one timeout must serve both.
4. **No info depth does not mean the book fired.** Scan for the literal
   `info string book move ` and, separately, for `invalid FEN` in *both* the
   position window and the go window — a refused FEN leaves the previous board in
   place and the book then answers the previous position.
5. **SEE written against `board.legal_moves` must set the side to move first.**
   Testing recaptures against the wrong side reported 929/2520 false material
   losses here; the true answer is 0. Hand-computed cases in a self-test are the
   only cheap defence.
6. **A `Book Depth` claim you may have heard from me was wrong.** The derivation
   reads the fullmove counter *after* `position` has applied its moves, so it is
   the total ply count; a FEN carries no history, so the counter is the only depth
   information that exists. Measured 14 cases: lock correct 14/14, both proposed
   "fixes" worse (4/14 and 2/14 wrong). Do not patch it.

## Not done / limits of these results

* Depth for the quality sweep is 10, with outliers re-checked at 14 and 18. This is
  a soundness screen, not a strength measurement; it cannot tell a 15 cp
  inaccuracy from a 5 cp one.
* The soundness audit covers the **embedded** book only. A user-supplied `.bin`
  via `Book File` is read by the same code path and decoded by the same
  `decode_move` (which drops illegal entries), but its contents are not audited
  here. Nothing in the code distinguishes an external book's `Entry` fields, so
  the legality guarantee still holds; the *quality* guarantee does not.
* The weighted-choice distribution is measured at n=10 per cell. Enough to show
  which moves appear and that variety 0 is stable, not enough to verify the
  weights statistically.
* Latency was measured on this host only (4 vCPU, no contention control). The
  order-of-magnitude claim is safe; the individual percentiles are host-specific.
* `Book File` with a path containing spaces is handled by a `getline`+`value_text`
  concatenation (`src/uci.cpp:260-265`); it works for the repo's own
  `tests_t16/start h2h4.book` but was not audited further, as it is outside the
  book-behaviour question.
* No code was changed in the tree under test. The `q8*` scripts build three
  patched copies in `/tmp` to measure what each candidate derivation would do;
  those builds are comparison artifacts, not a proposed patch, and the lock build
  is the one all other results come from.
* The `game_ply` matrix covers 14 cases: both counter directions, all three
  `position` forms, at depths either side of the gate. It does not test a
  mid-game FEN whose counter is wrong *and* whose position is absent from the
  book; there the gate decides nothing either way, so the case has no observable
  output to compare.
* The drawn-condition matrix uses one root per cell, plus two entry-bearing
  controls. Six roots is enough to show pre-emption tracks the book entry rather
  than the condition, but the per-cell counts are small; a seventh condition added
  later should be assumed to inherit the hazard until measured.
