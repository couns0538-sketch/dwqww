# Job C generator and integer reference: source review

2026-11-15 04:37 UTC. Read-only preparation; no Python, generator, reference evaluation or engine run occurred.

Retrieved the exact authorized path `h512/train/fable_nnue_v3.py` from `fable/standalone-h512-20261111`, then checked it at the observed immutable commit `efb2ff960037087299332bc6a44baea69441a17a`. Git blob `d7a5040133c3cf7b64d14fc9aa5c113e5041cf0c`; exact UTF-8 file SHA256 `f7b0d5dc72f7831ea103311adff38a26f24cbaedb3c942fa0c9a95244deb5005`. All lines were read. The saved `.py.txt` is inert VM evidence and is not imported into engine source.

Imports are argparse, random, struct, sys, NumPy, and lazy python-chess. No subprocess, shell, network, dynamic code execution or repository imports appear. Commands read the explicitly supplied net/FEN/output files; random, positions and widen write the explicitly supplied output path. Execution will use `python3 -I` outside every repository, after dependency versions and paths are recorded. The tool itself stays unchanged.

The authorized random invocation supports explicit `--seed`, hidden512, king-buckets8, output-buckets8, `--mirror`, and standalone default (no residual flag). Default evaluation scale is400. Input weights are in[-40,40], biases[-200,200], output weights[-127,127], output biases[-5000,5000]. It writes FORGENN3/version3,192-byte header, little-endian arrays and a trailing FNV1a64 checksum.

The eval subcommand emits six integer fields per FEN: cp, output bucket, White king bucket, White flip, Black king bucket, Black flip. It recomputes both accumulators using int64 arrays, clips to0..255, squares before the output dot products, applies truncation toward zero in the two divisions, and clamps to[-30000,30000]. With the specified hidden512/bounds, intermediate sums fit int64. No numerical result or bucket coverage is claimed before execution.

Readiness memo's earlier local-tool-missing observation is historical; this separate retrieval resolves availability. Required imports remain only the two exact C++ blobs. Persistent20k timing ambiguity in the readiness erratum is unchanged.
