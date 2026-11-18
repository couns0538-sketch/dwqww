# sol3 — Job 3 independent identity check of Carbon2’s ten-piece stack

**Step 0 and baseline passed.** All three r15d patches applied with zero fuzz and zero offsets. All 29 source hashes matched. On the rebuilt r15d with built-in evaluation, the required `bench 11`, `bench 13` and startpos `go perft 5` pins were **312866**, **862329** and **4865609** nodes. No F1 differences. [Patch output](sol3/job3/patch_step0.txt) · [Raw pins and settings](sol3/job3/preflight.summary.txt)

```text
CMakeLists.txt: OK
include/forge/b4.hpp: OK
include/forge/bitboard.hpp: OK
include/forge/board.hpp: OK
include/forge/book.hpp: OK
include/forge/clock_plan.hpp: OK
include/forge/eval.hpp: OK
include/forge/eval_params.hpp: OK
include/forge/nnue.hpp: OK
include/forge/nnue_v3.hpp: OK
include/forge/search.hpp: OK
include/forge/tm_finish.hpp: OK
include/forge/tm_node_share.hpp: OK
include/forge/uci.hpp: OK
include/forge/uci_clock.hpp: OK
include/forge/uci_output.hpp: OK
src/bitboard.cpp: OK
src/board.cpp: OK
src/book.cpp: OK
src/book_data.inc: OK
src/eval.cpp: OK
src/eval_params.cpp: OK
src/eval_params_table.inc: OK
src/nnue.cpp: OK
src/nnue_v3.cpp: OK
src/nnue_weights.inc: OK
src/polyglot_keys.inc: OK
src/search.cpp: OK
src/uci.cpp: OK
```

### Cumulative identity table

All rows used the Release build recipe below, the embedded AL1 s198 net, and PC20 at Threads 1, Hash 16 MiB and MultiPV 1. Each position was searched at depth 10. Node counts are the last search `info` before `bestmove`. [Independent raw UCI readback](sol3/job3/identity_readback.txt) · [Per-arm builds, commands, bench and search output](sol3/job3)

| Arm | Piece | Patch result | Executable SHA-256 | PC20 bench 11 | PC20 bench 13 | Rows equal to k=0 | First differing row |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 0 | r15d | Baseline | `bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6` | 278024 | 587276 | 389/389 | — |
| 1 | 01_S4 | Clean | `d4d22749f68f6407b743145143dd656609d3af405728398c73603cc1e981e068` | 278024 | 587276 | 389/389 | — |
| 2 | 02_S5 | Clean | `7564a995036a8914c2a4eae1dc0171c513d4179e58525c21f8e60436ead9c3b8` | 278024 | 587276 | 389/389 | — |
| 3 | 03_S5_assert | Clean | `7564a995036a8914c2a4eae1dc0171c513d4179e58525c21f8e60436ead9c3b8` | 278024 | 587276 | 389/389 | — |
| 4 | 04_S7 | Clean | `93f50109a59f759ac955e3126a0dd620b3e89565d4a9c562705e5f6fb3cda46b` | 278024 | 587276 | 389/389 | — |
| 5 | 05_G1 | Clean | `7357a7de5abe55599bec25c6fb770b7bccfa01fe47eb818f56f3f41f05a878ff` | 278024 | 587276 | 389/389 | — |
| 6 | 06_G2 | Clean | `ebee69e713b20ae962d4603a6a76068bdd20980ac5b0b347d84ff10a91246f05` | 278024 | 587276 | 389/389 | — |
| 7 | 07_G3 | Clean | `7605efdc95e96ad72dcc81e24a8bb29b98e03bb0075d6bcc0d54756652f68ba1` | 278024 | 587276 | 389/389 | — |
| 8 | 08_G4 | Clean | `690ac5e3128559e1e4fe7dcf942f6695dd37a5d3efcf375f3823603ad004a63d` | 278024 | 587276 | 389/389 | — |
| 9 | 09_W1 | Clean | `4d91d68e9f04362b27e2a2fc76d5ba8478f222d13f0f35f54fa45262d9d06f5f` | 278024 | 587276 | 389/389 | — |
| 10 | 10_W2 | Clean | `55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae` | 278024 | 587276 | 389/389 | — |
| P | planted key fault | Clean | `5a46f50b4356458683d29c3351d36014857f4ee08f73b1abff400f0443ff8629` | 271400 | 700935 | 0/389 | 1 (`6386 f1e2` → `6867 f1e2`) |

**The planted fault was detected.** Removing the side-to-move XOR from `Board::key_after` in the completed stack changed both bench pins. All 389 node counts and 126 best moves changed. The first difference was position 1, with 6386 nodes at k=0 and 6867 in P, both returning `f1e2`. [Exact fault diff](sol3/job3/plant.diff) · [Raw control benches](sol3/job3/bench_P.txt) · [Control rows](sol3/job3/rows_P.txt)

## Facts

- Case A, Codex Cloud Linux x86_64. The clean r15d reconstruction used Forge base `6b98f2170a3210e71beed04bbd2553972c253ed7`, the three pinned source patches, and Carbon2’s cumulative stack from `efd4ec76e933ec83dbfe35cddf77821e2c911931`. I verified each downloaded patch digest and applied each patch to a separate scratch copy of the preceding tree. No patch offsets, fuzz or rejects appeared in the ten build receipts. [Source identities](sol3/job3/sources_step0.txt) · [Stack patch hashes](sol3/job3/stack.expected.sha256.txt)
- Every build used CMake 4.2.3, GCC 14.2.0 (Debian `14.2.0-19`), libstdc++ `6.0.33`, glibc 2.41, Release, x86-64-v4, `FORGE_NNUE_V3=1` and the exact prescribed flags. Build parallelism was four per the CPU quota. The full compile lines, executable SHA-256 and engine ID are in `build_*.txt`. The embedded weights source SHA-256 is `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. The active evaluator used those embedded weights. [Build recipe](sol3/job3/build_one.sh) · [Baseline compilation log](sol3/job3/build_0.txt)
- The five supplemental r15d checks also matched. Default `bench 16` was 3024920 nodes, S14 `bench 11/13` was 242796/656517, and PC20 `bench 11/13` was 278024/587276. All eight preflight checks sent the options, waited for `readyok` and ran in fresh processes. [Preflight comparison](sol3/job3/preflight.summary.txt) · [Preflight driver](sol3/job3/preflight.py)
- The fixture SHA-256 is `d0630396e9e937318bf83e542d2f168c6216831e0dd83283875172d6ff72a2b2`. It starts with the first 100 official UHO opening lines verbatim. I then took the first 100 games in file order from Sol’s seed-7113 E2 PGN, starting at each game’s FEN, and appended 100, 99 and 90 positions at plies 20, 50 and 80 respectively, in game order and then ply order. The extractor writes the six standard FEN fields, with an en-passant target after a double pawn push. [Positions](sol3/job3/positions.txt) · [Input hashes and extraction provenance](sol3/job3/positions_provenance.json)
- The search harness sent PC20 options through `readyok`, used a fresh process for each bench and a single process per arm for depth-10 rows with `ucinewgame` and `isready` before each FEN. It captured stdout, stderr and exact commands for each arm. A second parser reconstructed evidence directly from command transcripts and raw stdout and reproduced all records. [Harness](sol3/job3/identity.py) · [Readback script](sol3/job3/readback.py)
- I opened Carbon2’s original identity only after the blind table was committed and pushed at `71da60024866c3212b79709cd4245ac5f9997c09`. Carbon2 reports exact identity after each piece with net512 and net768 bench checks and a 250-position depth-9 suite. The independent result agrees on per-piece identity for the embedded-net, 389-position depth-10 contract here. The fixtures, nets and depths differ. [Carbon2 identity summary](https://github.com/couns0538-sketch/dwqww/blob/efd4ec76e933ec83dbfe35cddf77821e2c911931/forge-combo29/carbon2/job13/stack_identity_raw.txt) · [Blind table commit](https://github.com/couns0538-sketch/dwqww/commit/71da60024866c3212b79709cd4245ac5f9997c09)

## Suspicions

The identical executable hashes for k=2 and k=3 are consistent with the new debug-only Zobrist check compiling out in Release. The fault control verifies that these benches and positions are sensitive to the side-to-move key error targeted by piece 02. It supplies no direct coverage of other possible faults.

## What I did not do

I ran no speed timing experiment, strength matches, or tests on the owner’s PC. Builds and the planted control stayed in scratch. The remote branch contains the text reports, scripts and evidence.

## What I am not sure about

The net code that piece 08 changes (nnue_v3) is not run with the built-in evaluation; more than one thread; time controls (depth searches only); the debug asserts (a Release build compiles them out; carbon2 runs those).

Search identity is verified for the 389 FEN-only depth-10 searches and both benches under this build and options. The check does not quantify a speed gain. [Clock stamps](sol3/job3/stamps.txt)
