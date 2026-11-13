# Numpy scorer versus the integer reference

Date: 2026-11-13. No training shard and no test set were opened. This is not a loss and not Elo.

`score_net_numpy` now goes through `_centipawns_from_features`, and `centipawns()` is the same function for a whole batch. `h512/train/test_scorer_parity.py` builds synthetic nets with `fable_nnue_v3.random_net` and positions by playing 12 random legal plies from eight FENs (seed 20261113), then compares every centipawn with `fable_nnue_v3.evaluate`.

Command and result, CPython 3.12, numpy 1.26.4, python-chess 1.11.2:

```
python3 h512/train/test_scorer_parity.py
b2 write: in-range bytes unchanged, overflow and non-integers rejected
scorer vs python reference: rows 416 mismatches 0 negative 253
ok
```

The four shapes were H32/1 bucket, H32/8 mirrored buckets, H64/4 mirrored buckets, and H64/1 bucket with every `w2` and `b2` forced negative. 253 of the 416 centipawns were negative, so the truncating division was not only exercised on positive values.

The same 104 FENs were then given to the engine tool rebuilt from this branch's `nnue_v3.cpp` (object sha256 `ef932159b5de8a617715a827843f01d9e9e793142ea38ee03911bb984da2f320`, tool sha256 `a3698b4221e62ce5b91c192d4c155fa1c8ec6692fee045aaa5567687749b7d4b`):

```
python3 h512/train/test_scorer_parity.py /tmp/forge-nnue-build/forge_nnue_v3_tool
engine tool vs reference and scorer: rows 104 mismatches 0
```

The tool also checks its fast path against its scalar reference and did not report a mismatch. The tool binary is local and is not in git.

`as_i32` is what `write_net` uses for `b2`. For every in-range sample in the test, including `2147483647` and `-2147483648` and integer-valued float32, the little-endian bytes match `numpy` casting that value to `<i4`. `2147483648`, `-2147483649`, `1.5` and infinity raise `ValueError`. `export_net` now passes the rounded float through to that check. Torch is not installed in this environment, so `export_net` was not called.
