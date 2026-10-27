# S14 Allocation-free MovePicker + mailbox piece_type — DONE: nothing is left to do for either goal in AL1 (report and static audit tool; no engine change)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2. Branch `opus-sol-S14` = `d4f4312` + `0d99f02` cherry-picked (`fb0f913b`) +
`eb0d3081` (tool, tests, logs) + this report. No engine file changes, so no CI run (`[skip ci]`). No timed run was
made (machine exclusive: no). No speed claim.

## Acceptance
| line | result | evidence |
|---|---|---|
| no heap allocation in the MovePicker | **PASS: already in AL1** (source, plus the machine code of the PC lock exe) | sections 1-2 |
| O(1) piece_type via a mailbox | **PASS: already in AL1** | section 1 |
| patch, 64-pick dump vs base, nodes identical | not applicable: there is nothing to patch. With no code change the dump is identical by construction. Sol's C++ pick oracle was not compiled (UNVERIFIED). | section 3 |
| Sol's 47 pure tests | **47/47 PASS** run unmodified with MSYS2 ucrt64 Python 3.14.4 (which uses `/` as path separator); 30/47 on Windows CPython 3.14.7, because of a path-separator bug in his tool | section 3 |
| audit tool tests and planted bugs | 8/8 OK; mutation check PASS | `logs/step3_unit_tests.log`, `logs/step4_mutation_check.log` |

## 1. Source references (lock tree `d4f4312`)
- **`MoveList`:** a fixed `std::array<Move, 256>` (`include/forge/board.hpp:49-73`, `data_` at :71). `push_back`
  asserts the capacity (:55); `reserve` does nothing (:56).
- **`MovePicker`** (`src/search.cpp:319-556`). Every member is a fixed array:
  - `moves_` `std::array<Scored, 256>` (:450);
  - `bad_captures_` `std::array<Move, 64>` (:453);
  - `buffer_` `MoveList` (:456);
  - `check_squares_` (:459).
- **Sorting:** `std::sort` (:497) is GCC's in-place introsort, not `stable_sort`, which can allocate a buffer.
- **Construction:** the picker is a stack object at :824 (qsearch), :1004 (ProbCut) and :1033 (main search).
- **Mailbox:**
  - `squares_` `std::array<Piece, 64>` (board.hpp:170);
  - `piece_at` reads one entry (:145);
  - `moved_piece` (:163) and `captured_piece` (:164-167) use it;
  - `piece_type` is a `constexpr` O(1) function (:199).

## 2. Static machine-code audit (`picker_audit.py`)
The PC lock exe `b/base/forge_h256_s198.exe` (sha256 `5d4df7f1…`, which has symbols) was disassembled with
`objdump -d --no-show-raw-insn -C` (binutils 2.46). The 16.8 MB disassembly stays in
`F:\opus_scratch\sol_s14\lock_exe.dis` (sha256 `32883b15…`).

The tool starts from `MovePicker::next`, the `std::sort` code for `MovePicker::Scored`, and
`Board::is_pseudo_legal` (the only out-of-line call made by the inlined constructor). It follows every direct
call and jump to another function, transitively:
- **8 functions are reachable:** `next`, `is_pseudo_legal`, `see_ge`, `attackers_to`, `generate_pseudo_legal`,
  `square_attacked_with_occupancy`, the introsort loop, and `memmove`.
- **None of them calls an allocator or anything related** (`operator new`, `malloc`, `calloc`, `realloc`,
  Heap/Virtual alloc, vector growth or string creation, exception allocation).
- **The 3 indirect transfers are all accounted for:**
  - `MovePicker::next` dispatches its stages through a 15-entry switch table, and `is_pseudo_legal` uses a 7-entry
    one. The tool read both tables from the exe's `.rdata`; every target lands inside its own function.
  - The third is the import thunk for the C runtime's `memmove`, which does not allocate.

**Negative controls:** an `operator new` call planted in the real `MovePicker::next` makes the audit report CHECK
(exit 1). Four tool mutants each fail the tests.

**Limits:** this checks direct calls in this one exe; it does not cover other builds.

## 3. Sol's prepared tests
Run unmodified from a scratch extract of
`17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_S14_validation_prepared_20261026`, using his README
command `python -B -m unittest discover -s . -p 'test_forge_sol_S14_*.py' -v`.
- **Windows CPython 3.14.7:** 30 pass, 17 fail (13 failures, 4 errors). All 17 stop at "source inventory differs":
  `forge_sol_S14_build_plan_20261026.py` `verify_source()` builds keys with `str(p.relative_to(root))`, which gives
  `src\search.cpp` on Windows, while the inventory keys are POSIX `src/search.cpp`.
- **MSYS2 ucrt64 Python 3.14.4** (path separator `/`): 47/47 OK (`logs/step5_sol_pure_tests.log`).
- A one-line `.as_posix()` would fix his tool if it is ever used on Windows. His file was left unchanged (a
  section 3 fix-up candidate).
- His C++ pick oracle and allocation counter (bound to his L/L′/B bases) were not compiled. No native allocation
  or dump run was made.

## 4. Related findings (outside the two S14 goals; not fixed here)
1. **The bad-capture buffer has no bounds check.** `bad_captures_` holds 64 moves and is written at
   `search.cpp:361` with no check.
   - The CR-passed, node-identical buffix is not in AL1, although the lock archive says it "applies to AL1":
     `7_history/strength_packs/buffix_node_identical/fc_sol_buffix_h256e12_vs_lock.patch`, sha256 `9ce56b3d…`. It
     raises the capacity to `MoveList::Capacity`, adds a `static_assert`, and adds `tests/bad_capture_tests.cpp`.
   - QA's two nine-queen stress positions reach 50 and 45 SEE-losing noisy moves (recorded output:
     `BAD_CAPTURE_FEN qa-1 … see_losing=50`, `qa-2 … see_losing=45`), so no position with more than 64 is known.
   - This is a latent risk of undefined behaviour. Merging the buffix as a bench-identical bug fix is CR/QA's call.
2. **Every picker construction zero-fills 3,328 bytes.**
   - It calls `memset` for 2,048 B (`moves_{}`) and for 1,024 B (the `MoveList` data; this happens because `Move`
     has default member initializers), plus 256 B of `zmm` zero stores (`bad_captures_{}`).
   - This happens at all three construction sites: qsearch `0x14001dfab`/`0x14001e017`, and search
     `0x14001f118`/`0x14001f18b` and `0x140020ec3`/`0x140020f3e`.
   - The picker only reads entries it has already written (below `count_`, `bad_count_`, `size_`), so leaving that
     storage uninitialised would keep node counts exact.
   - O2's callgrind of AL1 `bench 13` lists `memset` at 323,735,626 instructions (6.46%), which O2 put under
     start-up. Its callers were not recorded, so how much of that is the per-search TT/history clears and how much
     is per-node picker zeroing is UNVERIFIED.
   - This is a candidate node-exact speed patch; it would need a codegen diff and an NPS A/B. If the buffix is
     merged as it is, this zeroing grows from 256 B to 1 KiB.
   - **Resume steps:** a CI callgrind run with caller attribution of `memset`; then the patch, bench at all 5
     depths, the codegen diff, the NPS A/B, and Sol's pick oracle ported to AL1 for pick-order identity.
3. **Context only:** `Board::key_history_` (a `std::vector`) reserves 512 entries (board.cpp:176) and grows at
   board.cpp:788 and :838. A copied Board (`Worker::search` takes it by value) can reallocate a few times per
   search. That is outside the picker and not per node; not measured.

## Reproduce
```
objdump -d --no-show-raw-insn -C forge_h256_s198.exe > lock_exe.dis
python -I -B picker_audit.py lock_exe.dis --exe forge_h256_s198.exe --json logs/picker_audit.json
python -I -B test_picker_audit.py
python -I -B mutation_check.py <scratch> --dis lock_exe.dis --exe forge_h256_s198.exe
```
Main-session spot check (2026-10-27): the cited lock-tree lines (`search.cpp` 361, 450-456, 497, 824, 1004, 1033;
`board.hpp` 55-56, 71, 145, 170, 199) match `git show d4f4312:…`.

## UNVERIFIED
- Any native allocation-count run, and the 64-pick dump.
- The NPS cost of the zero-fill.
- Whether more than 64 SEE-losing noisy moves can occur.
- Other builds (Linux, AVX2).

## Files
`REPORT.md`, `picker_audit.py`, `test_picker_audit.py`, `mutation_check.py`, `logs/step1_disassemble.log`,
`logs/step2_picker_audit.log`, `logs/picker_audit.json`, `logs/step3_unit_tests.log`, `logs/step4_mutation_check.log`,
`logs/step5_sol_pure_tests.log`, `FILES.txt`, `SHA256SUMS`. No .tar.gz archives.
