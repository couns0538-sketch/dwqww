# Classification of all saved SEE differences

2026-11-10 UTC. Follow-up to key_after_REVIEW.md. Original see_exchange_results.txt is unchanged. No production edits or SEE replacement.

## Result

All 16 original random-position differences, plus the two previously minimized fixtures, are explained by greedy exchange ordering in this sample. For every saved case the engine's static_exchange equals an independently recursive **legal greedy-LVA** exchange result. Full legal target-square minimax chooses a different attacker at one exchange step. No implementation defect, SEE_HOIST regression, or erroneous pin filter was reproduced in these 18 cases. This classification is limited to these cases, not a claim that SEE is bug-free everywhere.

Original cases fall into three groups:
- 7 pawn-before-knight choices.
- 1 rook-before-queen choice that unnecessarily releases a pin on a defender.
- 8 non-king-before-king choices.

All complete traces are retained in see_exchange_classification.txt. CASE numbers below are line numbers in see_exchange_results.txt. Cases 1–2 are minimized fixtures; cases 3–18 are the 16 original random-position findings. Each listed alternate was verified legal by the independent exchange recursion.

| Case | Move | Engine / legal LVA | Target minimax | Exchange choice explaining the difference |
|---|---|---:|---:|---|
| 1 | e2e3 | 0 | -100 | d4xe3 releases Bc5's line; Nd1xe3 instead keeps d4 blocking and wins the pawn. Minimized fixture. |
| 2 | e5d3 | -300 | 0 | After Bc2xd3, Qd4xd3 exposes Rd5; Kd2xd3 keeps Qd4 blocking. Minimized fixture. |
| 3 | e2e3 | 0 | -100 | Same pawn-before-knight mechanism as case 1. |
| 4 | e2e3 | 0 | -100 | Same pawn-before-knight mechanism as case 1. |
| 5 | g1e3 | -700 | -900 | Re1xe3 releases the pin of Bc1 to Ka1; Qc5xe3 keeps Re1 pinning Bc1 and wins the queen without recapture. |
| 6 | c4e4 | -500 | -400 | After f5xe4, Qd5xe4 exposes Ba8's diagonal; Kd3xe4 keeps Qd5 shielding e4. |
| 7 | e5d3 | -300 | 0 | Same queen-before-king mechanism as case 2. |
| 8 | d3d4 | 0 | -100 | e5xd4 releases Bg7's line to d4; Nc6xd4 instead retains e5 as blocker and wins the pawn. |
| 9 | d3d4 | 0 | -100 | Same pawn-before-knight mechanism as case 8. |
| 10 | d3d4 | 0 | -100 | Same pawn-before-knight mechanism as case 8. |
| 11 | d3d4 | 0 | -100 | Same pawn-before-knight mechanism as case 8. |
| 12 | d3d4 | 0 | -100 | Same pawn-before-knight mechanism as case 8. |
| 13 | a6d6 | -500 | -400 | After c5xd6, Qd5xd6 exposes Rd1; Kc7xd6 keeps Qd5 blocking the rook. |
| 14 | f1d3 | -300 | 0 | After Bc4xd3, Qd4xd3 exposes Rd6; Ke3xd3 keeps Qd4 blocking the rook. |
| 15 | e2d3 | -300 | 0 | After Bb1xd3, same queen-before-king mechanism as case 14. |
| 16 | b5c7 | 100 | -200 | Qd6xc7 allows Be5xc7, then Kc8xc7, a losing queen exchange; Kc8xc7 immediately wins the knight. |
| 17 | b5c7 | 100 | -200 | Same queen-before-king mechanism as case 16. |
| 18 | f3f4 | -100 | 0 | After g5xf4, Qf5xf4 exposes Rf6; Kg3xf4 keeps Qf5 blocking the rook. |

## Additional minimized distinct mechanisms

**Pin release through greedy attacker choice (case 5)**

FEN: `8/8/8/2q5/2k5/8/8/K1B1r1Q1 w - - 0 1`
Move: g1e3. Engine and legal LVA: -700. Target minimax: -900.

After Qe3, Black's Re1xe3 has value 700: Bc1xe3 becomes legal because the pinning rook left e1; Qc5xe3 then wins the bishop. Black's Qc5xe3 instead has value 900: Re1 still pins Bc1 to Ka1, so there is no legal recapture. The discrepancy persists when every simulated capture is independently legality-filtered. This identifies attacker selection, not failure to recognize the bishop pin.

**Immediate safe king capture instead of a losing queen exchange (cases 16–17)**

FEN: `2k5/2p5/3q4/1N2B3/8/8/8/4K3 w - - 0 1`
Move: b5c7. Engine and legal LVA: 100. Target minimax: -200.

Black Qd6xc7 has value -300 after Be5xc7 and Kc8xc7, so the greedy exchange declines that branch. Immediate Kc8xc7 is legal and has value 300. White first gained the c7 pawn (100), making the full result -200. No pin-handling discrepancy is needed.

## Trace method and limitations

The existing independent target-minimax recursion in see_exchange_audit.cpp was reused. A second scratch recursion implemented a single deterministic capture choice, independent of board.cpp's SEE occupancy/pin code:

1. Generate legal target captures.
2. Select lowest piece type in Pawn, Knight, Bishop, Rook, Queen, King order; within a type, select lowest origin square. Promotion order is the generator's queen-first order (these discrepancies contain no promotions).
3. Make the chosen capture, recurse, unmake; return max(0, immediate captured material plus promotion delta minus recursive reply).
4. For the initial forced move, return its immediate gain minus the recursive reply without clamping the initial result.

For every possible capture at each step of the selected LVA path, the trace prints both its continuation under full target minimax and under legal greedy LVA. Values on a trace line are from the capturing side's perspective. Traces continue the selected path for explanation even when its negative result would let that side decline; the numerical recursion itself always includes the decline option.

The scratch classifier was built with g++-14 using -std=c++20 -O1, then rebuilt with -g -fsanitize=address,undefined -fno-omit-frame-pointer and ASAN_OPTIONS=detect_leaks=0. All 18 saved-case traces were identical between the ordinary and sanitized runs; no sanitizer diagnostics. The two additional minimized FENs above were separately run through the same ordinary classifier and gave the documented values. The classifier was a scratch diagnostic; its algorithm and complete output are preserved here without changing the existing test sources.

Both recursions share Board legal move generation, so they do not establish independent move-legality correctness. No conclusion about playing strength follows. Changing these greedy choices would be a search experiment rather than a repair justified by this evidence, and needs the usual isolation and validation gates.

## Exact classifier artifact preserved

The original scratch source still existed and has now been copied byte-for-byte to see_exchange_classify_original.cpp. SHA-256 of both that saved original and the scratch source is `a19f63a571ad1aeeea154060620461cfb72ad047b566c9654d3eb9cb0f4c7101`. It was not reconstructed from the prose above.

see_exchange_classify.cpp is the runnable portable copy: it changes the absolute include to `see_exchange_audit.cpp` and adds an explanatory comment, with the classifier logic unchanged. Run `tests/see_exchange_classify_check.sh` from forge-combo29. The script compiles with ASan/UBSan, reproduces all 18 saved traces exactly (ignoring final blank lines), and checks the two additional minimized examples. Executed result: `PASS 18 saved classification traces and 2 additional minimized examples; ASan/UBSan`.
