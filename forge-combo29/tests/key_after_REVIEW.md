# key_after and SEE audit evidence

Date: 2026-11-10 UTC. Read-only production audit. Tested board/bitboard sources match commit 55dc1b30a5741be87e6b5cb9fd1556ac368ffce9 (unchanged at 25d8bd9cc1832d72e27893c998d8f576b0006ff7).
Compiler: g++-14 (Debian 14.2.0-19) 14.2.0. All final audit runs use `-std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer`, with `ASAN_OPTIONS=detect_leaks=0`. No sanitizer diagnostics; no leak-check claim. No production edits or speed/strength claim.

## key_after

Reproduce: `tests/key_after_check.sh`. Equivalent individual compile/run commands were run for each mode. Compile links `tests/key_after_audit.cpp src/board.cpp src/bitboard.cpp`, with `-DFORGE_SPD_PREFETCH_EARLY=1`. Second configuration additionally sets KING_LINES=0 and NO_ZERO_MOVELISTS=2.

Both configurations produced:

`PASS positions=17470 moves=490569 fast=470876 fallback=19693 fast_promotions=3052 fast_castles=256 fast_double_pushes=14518 fast_ep=0 fallback_ep=57 seed=20261111`

For every legal move with key_after returning true, its predicted hash equals the actual made-position hash. Every move is unmade and the original FEN/key checked. The generator includes 100 seeded games up to 180 plies plus explicit white/black castling, quiet/capture promotions, EP checks and discovered-check EP, double pushes adjacent to enemy pawns, and a FEN EP field with no available capturing pawn. EP cases deliberately fall back; no claim is made that the fast path handles EP directly. This complements the earlier independent FEN-reconstruction hash audit.

## SEE differential diagnostic

Reproduce: `tests/see_exchange_check.sh`. The script was run successfully. It compiles SEE_HOIST=0 and =1, executes exhaustive legal moves at each sampled position (30 games up to 160 plies, seed 20261112), and compares diagnostic output. Final output for both modes:

`PASS threshold_consistency tested=134088 oracle_differences=18 oracle_nodes=274476 seed=20261112`

`PASS SEE_HOIST off/on diagnostic output identical`

Full differences and counts are saved in see_exchange_results.txt (one copy of the identical output).

Threshold checks sample -2000..2000 in increments of 25 and additionally the returned static_exchange boundary and boundary+1. They found no nonmonotonicity or inconsistency between static_exchange and see_ge at those points. This is bounded sampled threshold validation, not proof at every integer threshold.

The oracle independently recursively maximizes material gain over legal recaptures on the destination square, permitting either side to decline further exchanges. It uses the engine's pawn/minor/rook/queen values 100/300/500/900 and promotion deltas. It shares Board legal generation, so is not an independent move-legality oracle. Castling is excluded from this diagnostic. Legal target-square minimax is not identical to greedy least-valuable-attacker (LVA) SEE: differences are diagnostics, not automatically bugs. Pins and king safety follow legal move generation in the oracle.

Two minimized, manually explained differences demonstrate this semantic distinction:

1. FEN `8/3k4/8/2B5/3p4/8/3KP3/3n4 w - - 0 1`, move e2e3. Engine SEE=0, target minimax=-100. Greedy black d4xe3 has exchange value 0; black Nd1xe3 instead wins the pawn. Keeping the pawn on d4 blocks Bc5's recapture path and protects e3 against Kd2. This is a choice-of-attacker limitation, not a SEE_HOIST discrepancy.
2. FEN `8/4k3/8/3rN3/3Q4/8/2bK4/8 w - - 0 1`, move e5d3. Engine SEE=-300, target minimax=0. After Bc2xd3, Kd2xd3 breaks even because Qd4 still blocks Rd5. The SEE's non-king-before-king ordering instead considers Qd4xd3, exposing the rook recapture. Again this concerns exchange-choice policy, not a proven implementation defect.

The other differences are retained for further classification; this audit does not claim every difference has been individually explained. No SEE behavior change is proposed from these diagnostics. Treat any future change from LVA to stronger exchange choice as a search-behavior experiment needing the normal correctness and strength gates.

Follow-up classification is now complete for all 16 original random-position differences (and the two minimized fixtures). See see_exchange_classification.md and its complete traces. All 18 engine values equal a separate legal greedy-LVA recursion; the differences from target minimax are explained by attacker selection in these cases. The earlier unclassified status above is retained as the original audit record, not the latest conclusion.
