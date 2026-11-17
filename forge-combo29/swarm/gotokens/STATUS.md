# gotokens — status

**Seat:** malformed-`go` matrix, owner-audit follow-up to trap 3aa.
**Base:** `6b98f2170a3210e71beed04bbd2553972c253ed7`, folder `forge-combo29`.
**Branch:** `swarm/gotokens`. **PR:** against `main`.

## What this seat is

Trap 3aa says a malformed `go` value is replaced by "whatever `0` means to that
keyword". That is right about the mechanism and was incomplete about the blast
radius: it was measured on a handful of forms. This seat measures **every
keyword in `parse_limits`** across the six malformed shapes, then measures which
**combinations** leave a search unbounded, which malformed forms reach the
**book**, and states the **client-side rule** a harness can actually check.

## Build honesty

All four pins confirmed before any cell was measured:

| check | expected | got | verdict |
|---|---|---|---|
| `bench 11` (stdin) | 312866 | 312866 | MATCH |
| `bench 13` (stdin) | 862329 | 862329 | MATCH |
| `bench 16` (stdin) | 3024920 | 3024920 | MATCH |
| `go perft 5` (startpos) | 4865609 | 4865609 | MATCH |

`sha256(forge) = e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
— byte-identical to the base binary seat 29 recorded, so these numbers are from
the same artifact other seats measured.

Toolchain: `/usr/bin/g++` 13.3.0 (NOT `/usr/bin/c++`, which is clang 18 with a
broken header path), `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, default
`-DFORGE_MARCH=x86-64-v4` (host has avx512f + bmi2).

## Status — complete

- [x] build + four honesty pins
- [x] harness with a real deadline and no EOF during a search
- [x] keyword matrix, 75 cells
- [x] combination matrix, 19 cells
- [x] keyword-eating matrix, 11 cells
- [x] repeated-keyword asymmetry, 12 cells
- [x] book matrix, 14 cells + 24-run randomness check
- [x] forms outside the seat's list, 15 cells
- [x] corrected `searchmoves` pass, 11 cells
- [x] `nodes abc` vs `infinite` identical-window ladder
- [x] boundedness probes, 120 s, two boards
- [x] 0-ms race quantified, 30 processes per arm, interleaved
- [x] FINDINGS.md
- [x] `scripts/verify_claims.py` — 293 claims re-derived (numeric + table shape), both kinds proved able to fail

**Matrix cells measured: 157** (75 keywords + 19 combos + 11 eating + 12
lastwins + 14 book + 15 extra + 11 searchmoves), plus 24 book-randomness runs,
90 race runs, 8 boundedness probes, 4 huge-clock probes and 160 repeatability
runs. Matrix wall time: 1,193 s.

## Three harness bugs found and fixed (kept in the record)

1. **Bare FEN is not a position** — `position <fen>` without the `fen` keyword is
   an unknown type, silently ignored. My first 12-board scan measured startpos
   twelve times. Fixed with `as_position_command()` plus a setup assertion.
2. **Truncation helper duplicated short lists** — `lines[:12] + lines[-12:]`
   concatenates the whole list with itself when `len <= 24`, which fabricated a
   doubled depth ladder and a second `bestmove`. Fixed in `_head_tail()`.
3. **`wait_for` scanned from index 0** — a setup `readyok` satisfied the next
   command's wait, moving the measurement mark.

Plus one deliberate error kept visible: the first `searchmoves` block used
`e2e4` on a board where it is illegal, so all eight cells took the all-illegal
path. The corrected pass is `searchmoves.jsonl`; the wrong one stays in
`keywords.jsonl` rows 70-75.

## What is not established

- One build, one CPU — **did not measure the PC20 build**, so I cannot say which
  of these are base-only.
- **Could not reproduce the seat's 41/896 reference board.** Node counts are
  position-dependent (mine is `go depth 5` → 818). The shape of every row
  reproduced; those two absolute figures stay unverified here.
- The `movetime` race is quantified, not root-caused to an instruction.

## Files

`FINDINGS.md` (the deliverable), `STATUS.md`, `scripts/` (11 scripts + the
harness), `evidence/` (raw JSONL/JSON/MD per section).
