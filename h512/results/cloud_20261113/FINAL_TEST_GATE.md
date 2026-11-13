# The CPU trainer now refuses a final-test file

Date: 2026-11-13. No final-test file in the repository was opened. This is not an Elo result.

`train_h512_gpu.py score` refused a file name containing `final_test` unless `--final-test-unlock` was passed, and it appended `FINAL_TEST_ACCESS.log` beside that file. `fable_nnue_train.py score` and `train` read any FPOS path, including `--pos-glob`, `--val-pos`, and `--exact-pos`.

`refuse_final_test` is the shared check. The CPU `train` command runs it before `import torch`. The GPU train plan checks `train_glob` and each `score_sets` path before it asks for a GPU. GPU `selfcheck` and `parity_h512.py --select-pos` use the same helper. An unlocked read writes one line to `FINAL_TEST_ACCESS.log`. The GPU score command still writes its own line, which includes the net path.

`h512/train/test_scorer_parity.py` (exit 0):

- the helper refuses `final_test_2m.pos` and accepts `fb2_013.pos`
- `score --pos final_test3_2m.pos` exits with the refuse message
- `score --pos holdout.pos` does not
- `train --pos` a temporary `final_test3_2m.pos` refuses before torch is imported
- `train --pos-glob` of a directory that also contains that file refuses the same way
- `score --final-test-unlock` passes the name check and the log line names `final_test3_2m.pos`

The same run still reports 520 scorer rows, 0 mismatches, and the b2 clip limit. Torch is not installed, so `clip()` was not executed.
