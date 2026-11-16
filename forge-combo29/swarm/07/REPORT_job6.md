# REPORT — seat 07, job 6: reading src/board.cpp (castling, en passant, king square)

## What was asked / the answer / how sure

**Asked:** spend the window on the board.cpp read, prioritising faults that would show in normal
play, in this order of severity: (1) castling rights surviving a rook capture on its home square,
(2) en-passant squares set after a double push when no capturer exists, (3) a king position going
stale after a null move. If nothing is found, say so with the probes run.

**Answer:** **all three are clean, and the probes are shown to be able to fail.** Beyond the three,
I found and closed one *real* latent weakness that is not a wrong answer today but is an unguarded
invariant in shipped code: `Board::key_after()` (the early TT-prefetch key) is verified in-tree
only by an `assert` that `NDEBUG` removes, and it is on by default. I proved the function itself is
correct over 1,520,927 move cases, so this is a robustness finding, not a bug.

**How sure:** high for all three areas — each probe has a positive control that makes it fail on a
planted fault, so "pass" is meaningful. High for the key_after correctness result (exhaustive over
random legal play, with a planted fault detected 608 times). Medium that `key_after`'s missing
runtime check ever matters, since nothing currently consumes a wrong key.

## Honesty numbers

Base build (6b98f217, GCC 13.3.0, plain CMake Release): bench 11 = 312866, bench 13 = 862329,
bench 16 = 3024920, perft 5 = 4865609 (job0/raw/summary.txt). No engine source was modified for any
probe here; every program below is a standalone `.cpp` compiled against the unmodified
`src/board.cpp` + `src/bitboard.cpp`.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read set_fen / make_move / unmake_move / null-move / repetition / see_ge | done | this report cites line numbers | see "what the read covered" |
| perft vs python-chess on castling / ep / promotion positions | done | job4/perft_board.py, job4/raw/all.json | 14 positions, every total and every divide line equal, no stderr |
| probe 1: castling right after a rook is captured on its home square | done | job6/board_probes.cpp, job6/board_probes_run.txt | pass, with a planted-fault control that fails |
| probe 2: ep square set with no legal capturer | done | job6/board_probes.cpp + job6/epkey_probe.cpp, job6/epkey_run.txt | pass, with controls in both directions |
| probe 3: king square across a null move | done | job6/board_probes.cpp, job6/board_probes_run.txt | pass |
| key_after vs make_move over random legal play | done | job6/key_after_test.cpp, job6/key_after_run.txt | 1,520,927 checked, 0 mismatches, planted fault caught 608 times |

## Probe 1 — castling rights vs. a rook captured on its home square

`CastlingMasks` (board.cpp:166-177) clears a side's right on any move **from** or **to** the corner.
The dangerous case is a capture landing on the corner, so the test is a real capture.

    position r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1, then a8a1
    rights after = 5  ->  1 (White king-side) + 4 (Black king-side)
    fen after    = 4k2r/8/8/8/8/8/8/r3K2R w Kk - 0 2

White's queen-side right is gone (its rook was captured on a1), White's king-side right survives,
and Black's king-side right survives because only the **queen-side** rook left a8. `unmake_move`
restores the original FEN byte for byte.

Note honestly: my first version of this probe asserted that right 4 must also be cleared. That was
my error — a8 is the queen-side rook — and the corrected assertion is in the committed file with a
comment saying so.

**Control:** rebuilding with `masks[0] = 0xFF` (a planted fault: a1 no longer clears White's
queen-side right) makes this probe fail with `FAIL probe1 White queen-side right cleared by Rxa1
[4k2r/8/8/8/8/8/8/r3K2R w KQk - 0 2]`. So the probe detects the class of bug it is aimed at.

## Probe 2 — en-passant square set with no capturer

`make_move` sets `ep_square_` on every double push (board.cpp:1086), which is lawful; the thing that
must not drift is the **key**, which includes the ep term only when a legal ep capture exists
(board.cpp:1040-1042, 1090-1092, and `has_legal_en_passant_capture` at 979-993).

- A double push with no enemy pawn at all (`4k3/8/8/8/8/8/4P3/4K3 w`, play `e2e4`) leaves the FEN
  showing `- e3` but the key **identical** to the same board written with `- -`:
  both `14344340005152966589`.
- **Control that this is not vacuous** (`job6/epkey_probe.cpp`): the same position pair differing
  *only* in the ep field, with a legal ep capture available, gives **different** keys
  (`631853344440671074` vs `13845825276157828580`). So the ep term really is included when it should be.
- **Control in the other direction:** with the capturing pawn pinned (black pawn d4 pinned to its
  king on d8 by a rook on d1), the ep field is present but the capture is illegal, and the keys are
  **equal** (`10860499126821786208` both ways). That is exactly the documented rule.

## Probe 3 — king square across a null move

`make_null_move` / `unmake_null_move` (board.cpp:1145-1180) deliberately do not touch
`king_squares_`; the king does not move. Verified: `king_square(White)` = 4 before, during and after
a null move, equal to the square the bitboard scan reports, and the FEN round-trips exactly.
Then the case that could actually go stale: after `e1e2`, the square is 12; a null move keeps 12;
`unmake_null_move` keeps 12; `unmake_move` restores 4 and the original FEN.

## The one thing worth Opus's attention: `key_after` has no runtime check in Release

`Board::key_after` (board.cpp:996-1020) predicts the child position's Zobrist key **without making
the move**, so the search can prefetch the right TT cluster a few instructions earlier. It is used
at search.cpp:1504 and 1964, and it is **enabled in the shipped build**
(`FORGE_SPD_PREFETCH_EARLY=1` in the CMake definitions; the header default at board.hpp:30 is 0).

Its only verification in the tree is

    search.cpp:1505 / :1965   assert(!early_key || child_key == board.key());

and the Release build defines `NDEBUG`, so in the shipped engine that assertion does not exist. If
`key_after` were ever wrong, the search would prefetch the wrong cluster — a silent slowdown, and a
landmine for anyone who later trusts the value as a key.

**I tested the function itself:** `job6/key_after_test.cpp` walks 200 random legal games, and for
every legal move at every ply compares `key_after(move)` against `make_move(move).key()`.

    games 200 seed 701
    key_after checked 1520927  refused 40778
    mismatches 0

The 40,778 refusals are the documented conservative cases (an ep square present, an ep capture, or a
double push next to an enemy pawn) where the function correctly declines.

**Control:** with the rook term removed from the castling branch of a scratch copy
(`next ^= 0;` replacing the rook piece_key pair), the same test reports **608 mismatches** and names
the first one precisely: `fen 2bk1bn1/5r2/p1Pp1q2/5pp1/3pPP2/NP1BQ2r/P1RB3P/R3K3 w Q - 2 32 move e1c1
got 13247982611084509182 want 3430718038044698871`. So the zero above is a real zero.

**Why I am not filing this as a fault:** the function is correct on 1.52M cases and nothing consumes
the predicted key; the defect is that a compiled-out assertion is the only guard on an optimisation
that shipping code relies on. That belongs in "suspicions / hardening", not in FINDINGS as a bug.

## Findings

Nothing new for FINDINGS from the three probed areas — they are clean. The `key_after` observation
is recorded here as a hardening note, with the full control evidence, rather than as a finding,
because it does not produce a wrong answer.

## Suspicions, not proven

- `key_after`'s missing Release-time check (above). Concretely: a `Debug`/`RelWithDebInfo` CI run
  would exercise the assertion; a Release-only CI would not.
- `is_repetition(std::size_t root_index)` (board.cpp:1235-1248) counts a repetition as a draw when
  it has seen the same key twice *or* when a match lies at or after the root index. I read this as
  intentional (twofold within the search, repetition at/below the root) and did not test it; it is
  the kind of rule that silently changes play strength, so it is worth a dedicated check.

## What I did NOT do

- Did not test `see_ge`'s exchange walk beyond the perft agreement (SEE does not affect perft).
- Did not test the repetition rule (see suspicions).
- Did not run the probes under a sanitizer; they are deterministic logic checks with controls, and a
  sanitizer would not add to what the planted-fault controls already establish.

## What I am NOT sure about

- Whether any future caller will trust `key_after`'s output as a key. Today none does.

## Times

See job6/stamps.txt (and job4/stamps.txt for the perft part).
