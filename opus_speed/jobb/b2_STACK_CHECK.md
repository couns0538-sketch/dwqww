# b2 stack check: the five Job-B part-2 patches applied together (chain E, 10:07-10:10 PC clock)

Worker b2mg (fable). Log `F:/ospd/jobb/b2/chain_e.log`; copy `F:/ospd/src/b2_applytest_stack`; exe + lp_check under
`F:/ospd/jobb/b2/stack/`. Not a timing: the coordinator's pipeline stacks and times.

1. Apply order b2_nnue_zmm, b2_no_zero_movelists, b2_matkey_fast, b2_pickbest, b2_slider_pext with `patch -p1` on one fresh
   lock copy: every patch rc 0, no `.rej`; one `.orig` (search.cpp: three patches touch it, hunks applied with an offset, no
   fuzz failure). Every patch only adds lines (192 / 44 / 54 / 26 / 46, 0 removed).
2. Switch lines after stacking (one `#define FORGE_SPD_<NAME> 0` per switch, by name):
   include/forge/nnue.hpp:29 FORGE_SPD_NNUE_ZMM, include/forge/board.hpp:41 FORGE_SPD_NO_ZERO_MOVELISTS,
   include/forge/bitboard.hpp:11 FORGE_SPD_SLIDER_PEXT, src/search.cpp:325 FORGE_SPD_PICKBEST, src/search.cpp:649
   FORGE_SPD_MATKEY_FAST (two different lines in search.cpp, each with its own name).
3. All five at 0: `g++ -E -P` of all eight .cpp files is byte-identical to the lock's preprocessed text.
4. All on (NNUE_ZMM=1, NO_ZERO_MOVELISTS=2, MATKEY_FAST=1, PICKBEST=1, SLIDER_PEXT=1), plain lock build line:
   `forge_stack_allon.exe` sha256 aedb654b..., warnings 0, vfmadd 0; lp_check net on vs the lock plain run with the pins:
   24/24 OK, NODE IDENTITY ALL OK (`stack_allon_neton.compare.log`).
Not run for the stack: net-off lp_check, the verify builds (each proof was run per switch), the kit LTO+PGO build.
Only the task's apply order was tested; the five patches are add-only with disjoint hunks, so another order should apply
too (untested). `patches/b2_nnue_zmm_verify.patch` is a record of the verify variant: do NOT apply it (it carries a second
define line and overlaps b2_nnue_zmm.patch).
