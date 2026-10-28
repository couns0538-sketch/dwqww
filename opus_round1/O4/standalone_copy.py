#!/usr/bin/env python3
"""O4: writes a copy of a v2 net with the residual flag cleared: identical weights, header "stand-alone".
With the lock replica r1 (tools/nnue/forge_nnue_v2.py from-inc ... --replica r1) this gives two nets whose
network part is bit-identical, so one identical walk evaluated with each (nnue_engine_eval --walk) measures
exactly what PureNnue saves: the hand-crafted evaluation and its PSQT accumulator.
usage: standalone_copy.py <in.fnn2> <out.fnn2>"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "nnue"))
import forge_nnue_v2 as V2  # noqa: E402

n = V2.read_v2(sys.argv[1])
checksum = V2.write_v2(sys.argv[2], hidden=n["hidden"], king_buckets=n["king_buckets"], residual=False, mirror=n["mirror"],
                       king_map=n["king_map"], w1=n["w1"], b1=n["b1"], w2=n["w2"], b2=n["b2"],
                       output_buckets=n["output_buckets"], output_map=n["output_map"])
print(f"wrote {sys.argv[2]}: the weights of {sys.argv[1]} (residual {n['residual']}) flagged stand-alone, fnv1a {checksum:016x}")
