# The CPU trainer now refuses a final-test file

Date: 2026-11-13. No final-test file in the repository was opened. This is not an Elo result.

`train_h512_gpu.py score` refused a file name containing `final_test` unless `--final-test-unlock` was passed, and it appended `FINAL_TEST_ACCESS.log` beside that file. `fable_nnue_train.py score` and `train` read any FPOS path, including `--pos-glob`, `--val-pos`, and `--exact-pos`.

`refuse_final_test` is the shared check. The CPU `train` command runs it before `import torch`. The GPU train plan checks the `train_glob` string and each `score_sets` path before it asks for a GPU. GPU `selfcheck` and `parity_h512.py --select-pos` use the same helper. The check does not create a file from those paths. SonarQube Cloud reported a path-traversal vulnerability on the new helper that wrote `FINAL_TEST_ACCESS.log` beside a command-line path and beside a path taken from the training plan. That write is gone. The GPU `score` command still appends its own `FINAL_TEST_ACCESS.log` beside the file it was given, which is the line it had before this gate.

`h512/train/test_scorer_parity.py` (exit 0):

- the helper refuses `final_test_2m.pos` and accepts `fb2_013.pos`
- `score --pos final_test3_2m.pos` exits with the refuse message
- `score --pos holdout.pos` does not
- `train --pos` a temporary `final_test3_2m.pos` refuses before torch is imported
- `train --pos-glob` of a directory that also contains that file refuses the same way
- `score --final-test-unlock` passes the name check and does not write `FINAL_TEST_ACCESS.log` beside that file

The same run still reports 520 scorer rows, 0 mismatches, and the b2 clip limit. Torch is not installed, so `clip()` was not executed.
