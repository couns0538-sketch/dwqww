# gotokens — status

**Seat:** malformed-`go` matrix, owner-audit follow-up to trap 3aa.
**Base:** `6b98f2170a3210e71beed04bbd2553972c253ed7`, folder `forge-combo29`.
**Branch:** `swarm/gotokens`. **PR:** opened against `main`.

## What this seat is

Trap 3aa in `forge-findings.md` says a malformed `go` value is replaced by
"whatever `0` means to that keyword". That is right about the mechanism and was
incomplete about the blast radius: it was measured on a handful of forms. This
seat measures **every keyword in `parse_limits`** across the six malformed
shapes, then measures which **combinations** leave a search unbounded, which
malformed forms reach the **book**, and states the **client-side rule** a
harness can actually check.

## Build honesty

All four pins confirmed on this build before any cell was measured:

| check | expected | got | verdict |
|---|---|---|---|
| `bench 11` (stdin) | 312866 | 312866 | MATCH |
| `bench 13` (stdin) | 862329 | 862329 | MATCH |
| `bench 16` (stdin) | 3024920 | 3024920 | MATCH |
| `go perft 5` (startpos) | 4865609 | 4865609 | MATCH |

`sha256(forge) = e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`,
which is byte-identical to the base binary recorded by seat 29, so the numbers
here are from the same artifact other seats measured.

Toolchain: `/usr/bin/g++` 13.3.0 (not `/usr/bin/c++`, which is clang 18 with a
broken header path), `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`,
`-DFORGE_MARCH=x86-64-v4` default (host has avx512f + bmi2).

## Status

- [x] build + four honesty pins
- [x] harness (`scripts/go_probe.py`) with a real deadline, no EOF during search
- [x] keyword matrix, 75 cells
- [x] combination matrix, 19 cells
- [x] book matrix, 14 cells
- [x] forms outside the seat's list, 15 cells
- [x] `nodes abc` vs `infinite` identical-window ladder
- [x] searchmoves corrected pass (11 cells)
- [x] repeatability of the 0-ms forms, 12 fresh processes each
- [ ] FINDINGS.md written
