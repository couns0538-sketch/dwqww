#!/usr/bin/env python3
"""A2 memory and cache footprint of king-bucketed input layers (arithmetic only, no measurement).

usage: a2_footprint.py [hidden=256] [l2_kib_per_core=1024] [l3_kib=98304]

Layout of the lock engine (src/nnue.cpp, include/forge/nnue.hpp): weights are int16 (x 4096) in the file and
float32 in memory (Weights::w1 is float[768*H]); the accumulator is float[2][H] per search-stack ply. A
king-bucketed net multiplies only the first-layer weight block (768 x H) by the number of weight blocks; the
accumulator size does not change. A refresh cache holds, per worker, one accumulator half (H floats) plus the 12
piece bitboards for every (perspective, key) pair (C4's RefreshCache layout).
Default cache sizes: AMD Ryzen 7 9850X3D, Win32_Processor L2CacheSize 8192 KB (8 cores -> 1024 KiB per core),
L3CacheSize 98304 KB (see logs/cpu_caches.log).
"""
import sys

H = int(sys.argv[1]) if len(sys.argv) > 1 else 256
L2 = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
L3 = int(sys.argv[3]) if len(sys.argv) > 3 else 98304
KIB = 1024.0
# name, weight blocks, refresh keys (distinct (bucket, flip) pairs over the 64 own-king squares)
LAYOUTS = [("lock (no buckets)", 1, 1), ("M4", 4, 8), ("U8 (= C4 rm8)", 8, 8), ("M8", 8, 16), ("U16 (= C4 rm16)", 16, 16),
           ("M16", 16, 32), ("U32", 32, 32), ("M32", 32, 64), ("U64", 64, 64), ("R4", 4, 4), ("R8", 8, 8)]


def fmt(kib):
    return f"{kib / KIB:.2f} MiB" if kib >= KIB else f"{kib:.1f} KiB"


def main():
    col = H * 4                     # one weight column (one feature) in float32 bytes
    acc_half = H * 4
    entry = acc_half + 12 * 8       # one refresh-cache entry: H floats + 12 bitboards
    print(f"hidden H = {H}; one weight column = {col} B float32 ({col // 64} cache lines); accumulator per ply "
          f"= 2 x {H} x 4 = {2 * acc_half} B (unchanged by king buckets); L2 {L2} KiB per core, L3 {L3} KiB\n")
    print("| layout | weight blocks | W1 float32 in memory | W1 int16 in the file | x L2 per core | x L3 | refresh keys "
          "| refresh cache per worker (2 x keys x (H floats + 12 bitboards)) | refresh cache, 16 workers |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, blocks, keys in LAYOUTS:
        w_kib = blocks * 768 * col / KIB
        f_kib = blocks * 768 * H * 2 / KIB
        cache_kib = 0.0 if keys == 1 else 2 * keys * entry / KIB
        print(f"| {name} | {blocks} | {fmt(w_kib)} | {fmt(f_kib)} | {w_kib / L2:.2f} | {w_kib / L3:.3f} | {keys} "
              f"| {fmt(cache_kib) if cache_kib else '-'} | {fmt(16 * cache_kib) if cache_kib else '-'} |")
    print(f"\nPer refresh from scratch: about 32 columns x {col} B = {32 * col / KIB:.0f} KiB of weights read per "
          f"perspective (plus the bias); per incremental update: 2-4 columns = {2 * col / KIB:.0f}-{4 * col / KIB:.0f} KiB.")
    batch = 16384
    print(f"\nTrainer (v3b-style dense one-hot input, as C4's king_dense; float32; batch {batch} = the production bs):\n")
    print("| layout | weight blocks | one-hot input per perspective per batch | both perspectives | FT weights + factor block, "
          "with Adam m and v (x3) |")
    print("|---|---|---|---|---|")
    for name, blocks, _ in LAYOUTS:
        x_kib = batch * blocks * 768 * 4 / KIB
        p_kib = 3 * (blocks + (1 if blocks > 1 else 0)) * 768 * H * 4 / KIB
        print(f"| {name} | {blocks} | {fmt(x_kib)} | {fmt(2 * x_kib)} | {fmt(p_kib)} |")


if __name__ == "__main__":
    main()
