# Step 2 - the net file

## Generator

`h512/train/fable_nnue_v3.py` taken from branch `fable/standalone-h512-20261111`
(commit `efb2ff960037087299332bc6a44baea69441a17a`). It was read in full first. A
verbatim copy is committed as `step2/fable_nnue_v3.py.txt` so the exact generator
used is part of the evidence. It needs `numpy` and, for `eval`/`compare`
subcommands only, `python-chess`; the `random` subcommand uses `numpy` alone.

## Command

Run with `python -I` from `/tmp/ds/netgen`, which is outside the repository:

```
cd /tmp/ds/netgen
python3 -I /tmp/ds/fable_nnue_v3.py random /tmp/ds/netgen/random_h512.fnn3 \
        --hidden 512 --king-buckets 8 --output-buckets 8 --mirror
```

Output (verbatim, also in `step2/netgen-command-output.txt`):

```
wrote /tmp/ds/netgen/random_h512.fnn3 hidden 512 kb 8 ob 8 flags 2 checksum d80a4532f35587f
```

`flags 2` is `FLAG_MIRROR`.

## Size and sha256

```
6309096  random_h512.fnn3
e3ef99b7264d9c079f1c1e5ea8732bd576803e7bbfb2b00d138e53465dc8b375  random_h512.fnn3
```

The net file is deliberately not committed (it is a binary).

## Note on reproducibility

The generator draws from `numpy.random.default_rng(seed)` with the default seed 1
(no `--seed` was given, so the default applies) and the job's command was used
unchanged. A rerun on a different numpy version may produce different weights and
therefore a different sha256; the value above is for numpy 1.26.4 on this machine.

## Load check

The engine accepted the file and reported the AVX-512 kernel:

```
info string NNUE v3: loaded v3 /tmp/ds/netgen/random_h512.fnn3 hidden 512 king_buckets 8
mirrored output_buckets 8 standalone eval_scale 400 checksum d80a4532f35587f max|w1| 40
max|b1| 200 max|w2| 127 kernel avx512
```

Full line in `step2/load-check.txt`.
