# Pilot epoch-1 native inference parity

Status: **PASS — pilot parity only.** Actual compile/link and parity processes all exited 0; all captured stderr streams are empty.

Candidate residual network: `433ad84802b4543c3ff672f551569956202e77728d26e19a5076222db0fa3b8b` (fresh-only 14,895-row/20-epoch training pilot, selected epoch 1). Native and shared Python trainer final NNUE integer scores matched exactly on **2048/2048** legal positions; maximum error **0 cp**, 0 feature mismatches. HCE-only records and Python-chess legal/filter flags agreed. Three invalid-input controls were rejected.

Private unchanged `nnue.cpp` and candidate `nnue_weights.inc` were compiled outside the checkout with the recorded strict Release flags. The candidate object preceded the immutable existing core archive in the link command; the old archive NNUE member was absent from the link map. Original engine source, header, shipped network, probe source, core and candidate include hashes remained unchanged after execution. No accepted engine source or network was edited.

The deterministic corpus contains {'bundled_sample': 916, 'special_start': 18, 'special_first_move': 262, 'legal_walk': 852}. It includes {'castles': 8, 'en_passant': 2, 'promotions': 8, 'captures': 26}. Activation categories: {'below_zero': 244099, 'at_zero': 836, 'between': 279353, 'at_one': 0, 'above_one': 0}. Full raw FENs, probe JSON, invalid controls, HCE-only records, commands, build logs, link map, hashes and exit receipts are preserved here. Executable/source/object artifact: `/workspace/forge-nnue-handoff-20261023/pilot-fresh14895-epoch1-native-parity-artifact-attempt1.zip` (SHA256 `9426dc84c2021521980af503548fd89fa2a19fbd05648006c068da28dcedcfb6`).

This verifies native inference parity for this exact pilot network. It establishes no speed, held-out-loss, search correctness, Elo or acceptance result; a later full-data network requires its own native parity run. No Fastchess matches were run by this task.
