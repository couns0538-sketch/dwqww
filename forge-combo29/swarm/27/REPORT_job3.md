# REPORT job 3 — area 7 (reading the code for faults): the position and move making (`src/board.cpp`)
seat 27 · branch `for-fable-and-opus/swarm-27` · base `6b98f217` · seed 2701

## What was asked / the answer / how sure

- **What was asked:** the same fault hunt on `src/board.cpp` (1429 lines) — FEN parsing, `make_move` /
  `unmake_move`, the move generator's legality — with a test for anything suspicious, and a repair only as a text
  patch whose honesty numbers are unchanged.
- **The answer:** move making and move generation are exact on everything I could measure: perft 1–4 on 12
  positions equals an independent python-chess perft in **12 of 12** cases, and reaching a position by a move
  list then running `go perft 2` equals giving the same position as a FEN in **10 of 10**. The FEN *validation*
  has a real hole: a half-move clock above 100 is accepted and clamped to 65535, so the engine believes the
  position is a finished fifty-move draw — `score cp 0`, `nodes 0`, empty pv, any legal move — in a middlegame
  where clock 99 searches normally. One patch fixes it, honesty unchanged.
- **How sure:** high on S-F6 (table of 18 clock values × 2 positions, with clock 99 and clock 0 as controls that
  search normally, and clock 100 as a *correct* draw that the patch leaves alone). High that the move generator
  is correct on these 12 positions and to depth 4 — that is a sample, not a proof. My first run of this job was
  **wrong and I withdrew it** (below), which is why the harness-failure proof is part of this job.

## Honesty numbers (base `e06310ec…`, half-move-clock patch `29e2d8f0…`)

| check | required | base | patched | pass |
|---|---|---|---|---|
| bench 11 | 312866 | 312866 | 312866 | PASS |
| bench 13 | 862329 | 862329 | 862329 | PASS |
| bench 16 | 3024920 | 3024920 | 3024920 | PASS |
| go perft 5 | 4865609 | 4865609 | 4865609 | PASS |

Raw: `job3/honesty_halfmove/` (patched), `honesty/` (base).

## Two harness faults found in this job, both fixed (and why they matter more than the finding)

1. **My first perft comparison reported "0 of 12 positions equal" — a harness fault, not an engine fault.**
   python-chess 1.11.2 has **no `Board.perft`** (`[m for m in dir(Board) if "perft" in m.lower()] == []`), my
   call raised `AttributeError`, I had wrapped it in a bare `except` that stored `None`, and `engine == None`
   was simply false. Twelve "differences" out of a missing attribute. Fixed by `job3/pyperft.py`, an independent
   perft over python-chess's own `legal_moves`, which **raises** instead of returning a sentinel.
   Recorded because seat 19 reported the same class of bug in another seat's check.
2. **The integrity rule (seat 19): a parsed line must be asserted.** Every script in this job now raises
   `Missing` when it cannot find the line it parses, and `job3/f2_harness_can_fail.py` proves the harness *can*
   report a failure:

```
a_engine_perft2_A = 215   a_python_perft2_A = 215   a_python_perft2_B = 1019
a_same_case_A_vs_A = true
a_planted_difference_A_vs_B_detected = true      <- comparing A against B IS caught
b_missing_line_raises = "Missing: no 'nodes N' line ... (last line: 'c3e4: 1472736')"
c_reference_startpos_perft4_197281 = true
c_planted_wrong_expectation_caught = true
verdict = HARNESS CAN FAIL (a and b and c all held)
```

So the "12 of 12" below is not a blind zero: the same code path sees a difference when one exists, and shouts
when a number is missing.

## Steps

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| read `board.cpp` whole: `set_fen`, `make_move`, `unmake_move`, `make_null_move`, `perft`, `is_repetition`, `is_insufficient_material` | done | this report | one finding (S-F6), one set of suspicions |
| perft 1–4 vs an independent generator, 12 positions | done | `job3/f1/SUMMARY.txt` | 12 of 12 equal |
| make/unmake identity: move list vs equivalent FEN, perft 2 | done | `job3/f1/SUMMARY.txt` | 10 of 10 identical |
| half-move clock extremes (0, 99, 100, 101, 150, 65534, 65535, 65536, 99999) | done | `job3/f3/table.txt` | S-F6 |
| prove the harness can fail (three planted cases) | done | `job3/f2/result.json` | HARNESS CAN FAIL |
| patch, `patch -p1`, rebuild, re-measure | done | `job3/halfmove_clock.patch.txt`, `job3/f3_patched/` | applies clean; S-F6 gone; honesty unchanged |
| whole-file review of the move generator's attack tables | **not done** | — | area 7's next job (the move generator) |

## Finding

### S-F6 — a half-move clock above 100 is accepted and silently turned into "already drawn" (area 7, `src/board.cpp:351`)
One sentence: `set_fen` reads the field into a `long long` and stores `std::min(halfmove, 65535)` into a
`std::uint16_t`, so any clock above 100 is accepted and every later `halfmove_clock() >= 100` test
(`src/search.cpp:1303`, `:2251`) declares a fifty-move draw that never happened; the search then reports
`score cp 0` with `nodes 0` and an empty pv and plays any legal move.
Shows it again:

```
python3 forge-combo29/swarm/27/job3/f3_halfmove_cap.py /agent/repos/base/build-release/forge /tmp/f3h
```

| clock in FEN | refused | info lines | last info | bestmove |
|---|---|---|---|---|
| 0 (control) | no | 6 | `depth 6 … score cp 806 nodes 1292 … pv c7c5 …` | c7c5 |
| 99 (control) | no | 6 | `depth 6 … score cp 0 nodes 1347 … pv c8d7` | c8d7 |
| 100 (correctly a draw) | no | 6 | `depth 6 … score cp 0 nodes 0 … pv` (empty) | d6d5 |
| 101 | no | 6 | `depth 6 … score cp 0 nodes 0 … pv` (empty) | d6d5 |
| 150 | no | 6 | same | d6d5 |
| 65534 | no | 6 | same | d6d5 |
| 65535 | no | 6 | same | d6d5 |
| 65536 | no | 6 | same | d6d5 |
| 99999 | no | 6 | same | d6d5 |

(Middlegame `r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R b KQkq - N 8`; the K+R-vs-K rows in
`job3/f3/table.txt` show the same split.) The 101 row is the fault: no game can reach clock 101, so the position
is *illegal*, and answering it with a confident "cp 0, I have searched nothing" is worse than refusing it.

**Why this is not just pedantry:** tooling round-trips FENs and increments the clock itself; a single +1 bug in a
GUI or a training-data script turns every such position into an instant draw score, and a PGN with a clock of 101
is silently scored as a draw rather than flagged.

## The repair (text patch only)

`job3/halfmove_clock.patch.txt` against `6b98f217`: refuse `halfmove > 100` with
`info string invalid FEN: invalid FEN fields: half-move clock above 100`, matching how the same function already
refuses pawns on rank 1/8, two kings of one colour and an inconsistent ep square. `patch -p1 --dry-run` and
`patch -p1` both return 0.

| measurement | base | patched |
|---|---|---|
| clocks above 100 accepted | 101, 150, 65534, 65535, 65536, 99999 | **none** |
| clock 100 (a true draw) | draw, 0 nodes | draw, 0 nodes (unchanged) |
| clock 99 / 0 | search normally | search normally |
| bench 11 / 13 / 16 / perft 5 | 312866 / 862329 / 3024920 / 4865609 | identical |

Raw: `job3/f3_patched/table.txt`, `job3/honesty_halfmove/`.

## Suspicions, not proven

- `plies_from_null_` is capped at 1024 and used as the repetition window (`board.cpp:1237`). After a null move
  the window restarts, which is right; whether 1024 is enough for every real game I did not test.
- `is_repetition(std::size_t root_index)` returns true on a **twofold** repetition inside the search
  (`++count >= 2`, `board.cpp:1244`). Consistent with job 2's note; no test here proves a wrong move from it.
- `fullmove_` is `std::uint16_t` with its own 65535 clamp (`board.cpp:352`) but nothing reads it in search, so I
  did not pursue it.

## What I did NOT do

- Did not review the move generator's attack tables (`attacks::bishop/rook`) — that is the next area-7 job.
- Did not run the 20 000-FEN mutation stress of area 1 (that is area 1's job); my FEN work is only the fields
  named here.
- Did not test the patch against a full game in a GUI.

## What I am NOT sure about

- Whether the owner prefers refusing clock > 100 or clamping to 100. Refusing matches the file's other
  impossible-field checks and cannot hide a fault; clamping would accept the FEN but silently change it. I chose
  refusing and said so here.
- How many real FENs in the wild carry a clock above 100. It is illegal, but illegal FENs are common in training
  data, which is exactly why the answer matters.

## Times
`job3/stamps.txt`.

## Last command's output

`git status --short` and `ls` of `forge-combo29/swarm/27/job3/` are in `job3/last_commands.txt`.
