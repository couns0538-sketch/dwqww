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

## Follow-up (2026-10-27): FORGE_NOZERO_MOVE_BUFFERS, no zero-fill of the move buffers — DONE except two CI profile items being re-run

Branch `opus-sol-S14` = `9dca2a54` + `88021c40` (engine switch, tools, CI workflow `opus-sol-s14fu`, PC logs) + the
evidence commit. Folder: `followup_zerofill/`. Work by a sub-agent; this section is its hand-back, completed by the
main session with the CI jobs that finished after it (asan, tsan, nps-1, profile). Machine exclusive: no. Speed
figures are quoted only from quiet GitHub runners; the PC numbers are advisory.

**The patch.** A compile-time switch `FORGE_NOZERO_MOVE_BUFFERS`, default 0 (`-DFORGE_NOZERO_MOVE_BUFFERS=1`, or the
CMake option `-DFORGE_NOZERO_MOVE_BUFFERS=ON`).
- With the switch on, three buffers become `UninitArray<T, N>`: `MoveList::data_`, `MovePicker::moves_` and
  `MovePicker::bad_captures_`.
- `UninitArray` is `std::byte` storage. C++20 implicit object creation (P0593R6) creates the `T[N]` array in it, and
  it is read through `std::launder`; `T` must be trivially copyable and destructible (static_assert). This is
  well-defined behaviour, not a compiler-specific trick.
- `Move` is unchanged, so no other use of `Move` changes behaviour.
- `MoveList::resize` becomes shrink-only (it asserts this). Its only caller, `legal_moves`, only shrinks.
- Every MoveList and picker read was audited: all reads stay below `size_`, `count_` or `bad_count_`. Every
  `root_candidates.front()` is guarded by a non-empty check.

| line | result | evidence |
|---|---|---|
| (a) callgrind memset caller attribution, bench 13 | **Re-run pending.** In run 40527244836 both callgrind runs completed (bench 13, nodes 862,329 = pin), but the attribution script crashed on Linux `nm` output: undefined dynamic symbols have no address, and `'' in "tTwW"` is true in Python. Fixed by a strict line regex with a unit test (9/9); the profile job runs again | `logs/ci_40527244836/profile/`; parser `callgrind_callers.py`, 8/8 unit tests (`logs/step6_unit_tests.log`) |
| (b) switch off = lock | **PASS**: the PC box build differs from the lock exe `5d4df7f1…` only in the 6 PE timestamp/checksum bytes; the CI CMake switch-off build is byte-identical to the lock build (sha256 `6635d4d1…`) | `logs/step1_pc_builds.log`; `logs/ci_40527244836/check/builds.log`; opus-ci release |
| (b) no new warnings, FMA 0 | **PASS**: PC 0 warning lines. CI shows the lock's existing 6 `-Wconversion` lines in `search.cpp`, shifted 8 lines by the insertion; FMA 0 for lock, off and on | `logs/step1_pc_builds.log`, `logs/ci_40527244836/check/build_*.log` |
| (c) bench d11/13/16/20/22 + perft5 startpos/kiwipete exact, switch on | **PASS, ALL OK** on the PC box recipe (znver5) and on CI (x86-64-v3), switch off and on | `logs/step2_identity_on_pc.log`; `check/identity_on.log`, `check/identity_off.log` |
| (c) pick-order identity | **PASS**: identical for switch off and on × 6 storage patterns (`zero a5 01 ff random heap`), on PC g++ 15.2 znver5 and on CI g++-14 x86-64-v3; all 18 CI outputs have one body sha256 (scope below) | `logs/step4_oracle_pc.log`; `check/oracle.log`; `ci_40527244836/oracle_outputs_sha256.log` |
| (c) planted bugs | **PASS, 3/3 caught** on PC and CI; the unmutated control reproduces the reference | `logs/step5_mutation_check_pc.log`; `check/mutation_check.log` |
| (c) ctest, switch on | **PASS**: only the 4 known forge_tests lines | `check/known_on.log` |
| (c) ASan+UBSan, switch on | **PASS**: ctest known-only, 0 report files; uci_check bench d11/13/16 + perft ALL OK; oracle MATCH for switch off and on × zero/random/heap storage (digest `46501e4f2dc86508`) | `logs/ci_40527244836/asan/` |
| (c) TSan, switch on | **PASS**: ctest known-only, 0 reports; uci_check ALL OK | `logs/ci_40527244836/tsan/` |
| (c) valgrind memcheck and clang MSan, switch on | **memcheck PASS; MSan re-run pending.** Run 40527244836, memcheck with `--track-origins=yes --expensive-definedness-checks=yes`: bench 11 0 errors for the lock and the switch-on build (nodes 312,866 = pin); the pick-order oracle with heap storage (138,096 sequences) 0 errors with the switch off and on, outputs MATCH. The best-effort MSan oracle (200 roots) then ran until the job's 120-minute cap, and the job was cancelled. Each MSan run now has a 10-minute limit and uses 20 EPD roots | `logs/ci_40527244836/profile/` |
| (c) switch off (default) under sanitizers | **PASS** (release, asan, tsan) | opus-ci 40527244204, `logs/ci_40527244204/` |
| (d) codegen diff | **DONE** (details below) | `logs/step3_codegen_pc_lock_vs_on.log`; `check/codegen_lock_vs_on.log`, `check/codegen_diffs/` |
| (e) quiet-runner NPS A/B lock vs on, two runners | **DONE**: +2.0% to +2.7% CPU NPS on both, A/A controls include 0 (numbers below) | `nps-1/`, `nps-2/` (`nps_lock_vs_on.log`, `nps_lock_vs_lock_AA.log`) |
| PC NPS (advisory, loaded PC) | not quoted as a result (numbers below) | `logs/step7_nps_pc_advisory.log` |

**Pick-order oracle scope.** Adapted from Sol's S14 oracle on `17aa0cae`.
- 10,012 roots: 12 built-in positions (including QA's 9-queen bad-capture positions) plus the 10,000 EPD
  positions, together with all their legal children: 325,285 positions.
- In total 2,276,995 complete pick sequences (35,120,970 moves) with their SEE flags.
- The digest `46501e4f2dc86508` is the same on PC and CI.
- Built-in checks: every returned move is pseudo-legal, every sequence terminates, every move is returned exactly once.

**Planted bugs.** M1: the picker scans past `count_`. M2: `MoveList::end` runs past `size_`. M3: the bad-captures stage
reads past `bad_count_`.

**Codegen (d).**
- PC znver5, memset calls removed:
  - `Worker::search` 4→0 (zmm stores 20→12);
  - `qsearch` 2→0 (zmm 4→0);
  - `has_legal_move`, `perft`, `legal_moves`, `pseudo_legal_moves` 1→0 each;
  - root driver 2→1.
- PC znver5, instruction counts: search 2412→2379, qsearch 809→792.
- Changed but not just shrunk: `MovePicker::next` 1821→1848 (register allocation and loop shape around the
  buffers); `generate_pseudo_legal` 820→778 (stores merged differently).
- Byte-identical after normalisation: static_evaluate, TT probe/store, history updates, nnue update/evaluate/refresh,
  make/unmake, see_ge, is_pseudo_legal.
- CI AVX2: search memset 5→1 (ymm stores 30→14); qsearch 2→0 (ymm 12→4); `has_legal_move` 3→0. The memset left in
  search is the `quiets_tried`/`captures_tried` fill, which the switch does not touch.

**NPS (e).** Welch 95% CI of the difference; ABBA, fresh processes, 10 runs per side; nodes matched on every run.

| runner | lock→on CPU NPS d16 | d20 | A/A control (lock vs lock copy) d16 | d20 |
|---|---|---|---|---|
| nps-1 | **+2.00%** [+0.85, +3.15] | **+2.16%** [+1.27, +3.05] | +0.16% [−1.87, +2.19] | −0.93% [−2.46, +0.60] |
| nps-2 | **+2.26%** [+1.50, +3.03] | **+2.67%** [+1.90, +3.45] | +0.14% [−0.79, +1.07] | −0.71% [−1.90, +0.47] |

- Wall-time NPS agrees (nps-1 +2.10% / +2.17%, nps-2 +2.33% / +2.70%).
- PC advisory only (loaded PC, nice 19, box recipe znver5), CPU-time NPS: d16 +5.64% [+2.32, +8.96], d20 +4.62%
  [+2.36, +6.87]. All 40 runs had the lock node counts.

**Findings**
- The switch removes the per-construction zero-fill of every picker (3,328 B) and of every MoveList (1 KiB)
  without changing any search result. The MoveList part also covers per-node `has_legal_move` (called from
  `is_draw`) and `perft`.
- On two quiet runners the gain is +2.0% to +2.7% CPU NPS with both A/A controls including 0. That is the speed
  claim, within those CIs. No Elo claim: a node-exact speed-up still needs a gate to show strength.
- The project's speed-eligibility rule (95% CI lower bound ≥ +2% at d16 and d20, as applied in S11 and S49) is not
  met: the lower bounds are +0.85% / +1.27% (nps-1) and +1.50% / +1.90% (nps-2). The rule is meant for the PC;
  S49's tool can measure it there once a core is free of gates.
- The switch is meant for QA to gate or adopt. With it off, the build is the lock binary.

**Left / UNVERIFIED**
- Not covered by the switch: `quiets_tried{}` / `captures_tried{}` still zero 768 B per main-search node (12 zmm
  stores on the PC build, ahead of null-move pruning; one memset on CI AVX2). They are also write-before-read, so
  this is a possible follow-up; not measured.
- MSVC build of the switch not tested.
- No gate.

**Process notes (from the hand-back).**
- One Bash command was denied: a heredoc that edited the unit test's temp-file cleanup (`os.unlink`) and ran the
  tests in one call. The cleanup had never run; the edit was redone with the Edit tool and the test now leaves its
  temp files in `F:\opus_scratch\sol_S14fu\tmp`. Nothing was deleted.
- `run_picker_oracle.sh` was edited while a background run of it was executing, which broke that run's final
  comparison; it was re-run from a frozen copy, byte-identical to the committed script.
- Two empty folders from before the scope change (`F:\opus_scratch\build\S12fu`, `F:\opus_scratch\sol_S12fu`) are
  left in place.
- CI logs are in `logs/ci_40527244836/<job>/` and `logs/ci_40527244204/<job>/`; the 18 oracle outputs (~390 KB
  each) stay in `F:\opus_scratch\sol_S14fu\ci_40527244836` with their sha256 in `oracle_outputs_sha256.log`.
