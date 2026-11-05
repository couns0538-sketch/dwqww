STATE: READY FOR TIMING

# b2_pickbest: FORGE_SPD_PICKBEST (card T05D-02: branch-free first-maximum scan in MovePicker::pick_best)

Worker b2mg (fable), job B part 2, branch opus-speed-20261105. Source edits 09:37-09:40 PC clock; value 2 added 09:57; builds
and checks of value 1 09:54-10:02 (chain log `F:/ospd/jobb/b2/chain_c.log`); value 2 checks 10:10-10:14 (`chain_f.log`); notes
finished 10:16 (`date`). Both values passed (a)-(c); time value 1 and value 2 separately (see Risks).
Patch: `F:/ospd/wt/opus_speed/patches/b2_pickbest.patch` (adds 26 lines, removes none; file search.cpp only; applies with
`patch -p1` to a fresh lock copy and reproduces `F:/ospd/src/b2_pickbest`: apply test in `F:/ospd/src/b2_applytest_pickbest3`).
One switch line `#define FORGE_SPD_PICKBEST 0` in search.cpp: 1 = key-max scan as the compiler emits it (it vectorises it,
see codegen), 2 = the same scan with `#pragma GCC novector` (scalar cmov chain) for the short lists. Verify variant (not for
stacking, no patch written): `F:/ospd/src/b2_pickbest_verify`. A 0-byte stray file `src/search.cpp.tmp.11464.e6e46568bd33`
(left by the interrupted session's editor at 09:31) sits in the two copies; it is excluded from the patch (`diff -x`) and was
not deleted (no-delete rule). Deliverable patches of this job: b2_nnue_zmm, b2_no_zero_movelists, b2_matkey_fast, b2_pickbest,
b2_slider_pext.

## Design (own words)
The lock's `pick_best` (search.cpp:488-503) scans [index_, count_) with a strict `>` and keeps the FIRST maximum, then swaps it
to index_ (only for the first 4 picks per stage; later picks come from one std::sort, untouched here). The switch replaces
only the scan: key_i = (uint32(score_i) << 32) | (0xFFFFFFFF - i) read as a signed int64. The high half orders by score
(signed), the low half by inverted index (unsigned; index < 256 fits), and no two keys are equal, so max_i key_i names the
element with the highest score and, among equal scores, the lowest index: exactly the lock's `best`. The loop is a plain
`best_key = std::max(best_key, key_i)` chain (no data-dependent branch), `best = 0xFFFFFFFF - uint32(best_key)`, and the
swap plus everything after it is the lock's text, so the array that std::sort later receives is byte-identical. Portable
C++, no intrinsics. Lists are at least one element long at every call (the callers test index_ < count_), so the first
key is valid. Value 2 differs only by the pragma (same values, same order).

## Lines touched (lock numbering)
- src/search.cpp: switch block before `class MovePicker` (:319); the helper `pick_key` under the switch before :486; :491-494
  (the scan) under `#if` / lock scan under `#else`; :495 swap and the rest untouched.
- Switch 0: `g++ -E -P` of src/search.cpp is byte-identical to the lock's (`F:/ospd/jobb/b2/pickbest/pp/`).

## Why node-identical
Same `best` at every pick (proof above; verified at every call by the verify build), same swap, same later sort input:
the move order is the lock's at every node.

## Checks (value 1)
(a) switch-0 exe `F:/ospd/jobb/b2/pickbest/forge_pb_off.exe` (sha256 6445f605...) vs the lock plain exe: `cmp -l` differs only at
    bytes 137 138 217 218. PASS.
(b) switch-on exe `forge_pb_on.exe` (795f9d92...): net on vs `lock_plain_neton.json` with the pins: 24/24 OK, NODE IDENTITY ALL OK
    (`pb_on_neton.compare.log`); net off (UseNNUE=false) with the net-off pins: 24/24 OK (`pb_on_netoff.compare.log`).
(c) verify exe `forge_pb_verify.exe` (89ab9c80...; the lock's scan runs next to the key-max at every pick, abort on a different
    index, count at exit): `bench 16` nodes 3024920 (= pin), "FORGE_SPD_PICKBEST_VERIFY: 3097163 selection scans compared,
    0 mismatches" (`pb_verify_bench16.log`, `.stderr`); first 2000 of the 12k FENs at depth 2 (trimmed to a short run per the
    coordinator's note): 2000/2000, engine exit 0, "190230 selection scans compared, 0 mismatches" (`pb_verify_2k_d2.run.log`,
    `.tsv.stderr`).
    codegen (plain -O3 znver5, `objdump/`): `MovePicker::next` (pick_best is inlined there only; `Worker::search` and `qsearch`
    listings are unchanged: 2414 / 811 lines, 43 / 7 cmov, 85 / 30 signed jumps in both exes): lock 1823 lines, 12 cmov,
    0 vpmaxsq; switch on 2487 lines, 20 cmov, 51 vpmaxsq (GCC vectorised the int64 max reduction with AVX-512 masked zmm
    loops plus scalar epilogues; signed jumps 44 -> 44, the data-dependent `jg` of the scan replaced by loop control).
    Whole exe: vpmaxsq 0 -> 51, cmov 1659 -> 1667. vfmadd 0 in every exe (build logs).

## Checks (value 2, scalar; chain log `F:/ospd/jobb/b2/chain_f.log`, 10:10-10:14)
(a) switch-0 exe rebuilt from the edited copy `forge_pb_off2.exe` (9d38f486...) vs the lock plain exe: `cmp -l` differs only at
    bytes 137 138 217 218. PASS.
(b) value-2 exe `forge_pb_on2.exe` (573d5a7b...): net on 24/24 OK, NODE IDENTITY ALL OK (`pb_on2_neton.compare.log`); net off
    24/24 OK (`pb_on2_netoff.compare.log`).
(c) verify exe `forge_pb_verify2.exe` (f92fa6f3..., value 2 + VERIFY): `bench 16` nodes 3024920 (= pin), "3097163 selection
    scans compared, 0 mismatches" (`pb_verify2_bench16.log`, `.stderr`) - the same scan count as value 1, as it must be.
    codegen (`objdump/pb_on2_next.dis`): `MovePicker::next` 1850 lines, 8 cmov, 0 vpmaxsq (the pragma holds), 44 signed jumps;
    whole exe vpmaxsq 0, cmov 1655. The scan loops are `cmp %rcx,%rax; cmovl %rax,%rcx` chains (one 64-bit compare + cmov per
    element and the loop-control branch, no data-dependent branch). vfmadd 0 (build log).

## Risks
- Stacking note: value 1's vectorised loop was verified with the lock's zero-filled `moves_`, and the no_zero poison build
  ran without pickbest; PICKBEST=1 on top of NO_ZERO_MOVELISTS was covered only by the all-on lp_check (b2_STACK_CHECK.md),
  not by a poison or sanitizer run. The source reads only [index_, count_) and the compiler must keep that (masked or
  epilogue lanes), so it is a CI ASan item, not a known problem; value 2 (scalar) raises no such question.
- Gain unknown (card: +1 to +3 % UNPROVEN, a static guess); the ABBA decides. Value 1's vector loop has a setup and an
  epilogue that may cost more than the lock's scan on the short capture / evasion lists (typically < 8 moves); value 2
  is the scalar hedge (1-cycle cmov dependency per element instead of mispredicted "new maximum" branches). Time both.
