# S-C4 hidden 768-1024 plan (G-C4)

- `forge_sol_SC4_hidden_768_1024_plan_20261027.md`: the plan, with the measured NPS cost of H512/H768/H1024.
- `forge_sol_SC4_queue_lines_20261027.txt`: PROPOSED queue lines (speed checks and the width ladder) plus 2 dry-parse
  negative controls.
- `opus_sc4_widen_inc.py`: zero-pads an H256 `nnue_weights.inc` to a wider hidden size. It is function-preserving and
  checks the round trip itself.
- `test_opus_sc4.py` (5 tests) and `mutation_check_sc4.py` (5 planted bugs).
- `nps_ab.py`: S29's paired NPS tool (copy). `opus_a7_dryparse.py`: A7's dry-parse tool (copy).

## Reproduce
```
# zero-padded trees (copy include/ and src/ of the lock tree, move the H256 inc aside, write the widened one)
python -I -B opus_sc4_widen_inc.py --inc <tree>/nnue_weights_h256_original.inc --hidden 1024 --out <tree>/src/nnue_weights.inc
# build with the box recipe and the hidden size as a variable (build_pc.sh with -DFORGE_NNUE_HIDDEN=${FORGE_HIDDEN})
FORGE_HIDDEN=1024 nice -n 19 bash build_pc_hidden.sh <tree> F:/opus_scratch/build/SC4/forge_sc4_h1024.exe
python -I -B <LA>/2_build/uci_check.py F:/opus_scratch/build/SC4/forge_sc4_h1024.exe --full     # lock pins: ALL OK
nice -n 19 python -I -B nps_ab.py forge_sc4_h256.exe forge_sc4_h1024.exe 6 16 20
```
`build_pc_hidden.sh` is `b/tools/build_pc.sh` with `-DFORGE_NNUE_HIDDEN=256` replaced by
`-DFORGE_NNUE_HIDDEN=${FORGE_HIDDEN:-256}`; the copy is `build_pc_hidden.sh`, its one-line diff `logs/step2b_build_wrapper.diff`.
