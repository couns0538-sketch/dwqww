# swarm/stability — is a fixed-depth score a usable training label?

Read `FINDINGS.md` first (the answer, then the evidence) and `STATUS.md` (conditions,
controls, limits). `scripts/tables.py` regenerates every table in FINDINGS from
`evidence/`.

## Reproduce

Build (from the repo's `forge-combo29/`), then run in this order. Nothing is recorded
unless the four honesty pins match, so the pins are step 1.

```sh
mkdir -p /tmp/build-stab && cd /tmp/build-stab
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 \
        -DCMAKE_BUILD_TYPE=Release <repo>/forge-combo29
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 make -j4

cd <repo>/forge-combo29/swarm/stability
python3 scripts/pins_probe.py /tmp/build-stab/forge            # gate: 4/4 must match
python3 scripts/fault_proof.py /tmp/build-stab/forge           # 9/9 planted faults fire
python3 scripts/make_corpus.py /tmp/build-stab/forge evidence/corpus.json
python3 scripts/meas_repeat.py /tmp/build-stab/forge "<moves>" --runs 30 --threads 1
python3 scripts/corpus_twice.py /tmp/build-stab/forge evidence/corpus.json evidence/m3_corpus_T1.json --threads 1
python3 scripts/order_batch.py  /tmp/build-stab/forge evidence/corpus.json evidence/m3_corpus_T1.json evidence/m4_order.json
python3 scripts/order_reset.py  /tmp/build-stab/forge evidence/corpus.json evidence/m4b_order_reset.json
python3 scripts/batch_resets.py /tmp/build-stab/forge evidence/corpus.json evidence/m3_corpus_T1.json evidence/m5_resets.json
python3 scripts/book_rng.py /tmp/build-stab/forge evidence/book_rng.json
python3 scripts/tables.py
```

## The one rule a caller must not get wrong

`ucinewgame` before **every** position, or one process per position. A batch without a
reset is wrong on 197 of 200 positions against a fresh process (`FINDINGS.md`, M5).
`Clear Hash` is not a substitute — it does not clear histories.
