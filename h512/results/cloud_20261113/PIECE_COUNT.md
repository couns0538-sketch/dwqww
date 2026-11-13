# Phase piece-count lookup was checked and left as it is

`fable_nnue_data.PIECE_COUNT_LUT` is built with `bin(c & 15 != 0).count("1") + bin(c >> 4 != 0).count("1")`. In Python `!=` binds less tightly than `&` and `>>`, so this is `(c & 15) != 0` and `(c >> 4) != 0`. `bin(True)` is `0b1`, so each occupied nibble adds one.

Compared with `int((c & 15) != 0) + int((c >> 4) != 0)` for all 256 byte values: 0 disagreements. Packed FENs (even squares in the low nibble, the same layout `_load_chunk` unpacks) matched `python-chess` piece counts on the 104 positions from `test_scorer_parity.py`. The lookup was not changed.

It is used only to stratify the selection and test shards in `make_splits.py` and `make_test2.py`. The training forward counts pieces from the unpacked codes (`batch_features`) and, on the GPU path, with `(boards & 15) != 0` plus `(boards >> 4) != 0` (`train_h512_gpu.py`). Those paths do not read this table. The shards already written were not rebuilt.
