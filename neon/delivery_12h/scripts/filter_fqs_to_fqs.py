"""Server-Day & Filter Quest FQS1 (.fqs.z) -> FQS1 (.fqs.z) Tier-2 Dedup & Quality Filter.

Operates natively on compressed 38-byte FQS1 shards (zero .plain decompression!):
  - Tier-1 Mandatory Integrity (always enforced):
      * Valid FQS1 magic & exact 38-byte record framing
      * Valid stm in {0, 1}, res8 in {-1, 0, 1}, |score16| <= 30000
      * Optional --skip-in-check (default True, drops flags bit 1)
  - Tier-2 Reversible Quality & Cross-Round Dedup:
      * --skip-noisy: drop flags bit 0 (captures/promotions)
      * --drop-draw-conflict N: drop res8 == 0 & |score16| >= N (e.g. 600)
      * --drop-swing: drop flags bit 2 (ply-to-ply swing >= 200)
      * --hs800-keep-pct P1,P2: deterministic hash downsampling of |score| in [800,1199] (P1%) & >=1200 (P2%)
      * --dedup-mode {none, first, avg}: exact cross-shard deterministic blake2b(packed+stm) dedup!
          - first: keep first occurrence (weight_u8 = 128)
          - avg:   merge exact duplicates -> rounded mean score16, majority res8, weight_u8 = clip(rint(128*sqrt(k)), 128, 192)
  - Atomic .part -> os.replace writes + JSON accounting summary. Built-in --selftest!
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
import time
import zlib
from pathlib import Path

import numpy as np

FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])


def read_fqs(path: Path) -> np.ndarray:
    raw = path.read_bytes()
    if path.name.endswith(".z"):
        raw = zlib.decompress(raw)
    if len(raw) < 8 or raw[:8] != FQS_MAGIC or (len(raw) - 8) % FQS_DTYPE.itemsize != 0:
        raise RuntimeError(f"Corrupt FQS1 shard: {path}")
    return np.frombuffer(raw, dtype=FQS_DTYPE, offset=8).copy()


def write_fqs_atomic(path: Path, arr: np.ndarray, level: int = 3) -> tuple[int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    comp = zlib.compress(FQS_MAGIC + arr.tobytes(), level=level)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(comp)
    os.replace(tmp, path)
    return len(comp), hashlib.sha256(comp).hexdigest()


def filter_and_dedup(
    in_paths: list[Path],
    out_dir: Path,
    skip_in_check: bool = True,
    skip_noisy: bool = False,
    drop_draw_conflict: int = 0,
    drop_swing: bool = False,
    hs800_p1: int = 100,
    hs800_p2: int = 100,
    dedup_mode: str = "none",
    shard_rows: int = 500_000,
) -> dict:
    t0 = time.time()
    stats = {
        "in_shards": len(in_paths),
        "raw_rows": 0,
        "t1_corrupt": 0,
        "t1_in_check": 0,
        "t2_noisy": 0,
        "t2_draw_conflict": 0,
        "t2_swing": 0,
        "t2_hs800": 0,
        "t2_dedup_merged": 0,
        "kept_rows": 0,
    }

    # For dedup_mode != none, map 16-byte blake2b(packed + stm) -> index in kept lists
    seen_first: set[bytes] = set()
    # For mode=avg: key -> [first_rec_bytes_33, score_sum, res_sum, count, flags_or]
    avg_table: dict[bytes, list] = {}
    out_bufs: list[np.ndarray] = []
    out_shards: list[dict] = []
    shard_idx = 0

    def flush_chunk(chunk: np.ndarray) -> None:
        nonlocal shard_idx
        if len(chunk) == 0:
            return
        sp = out_dir / f"fqs_s{shard_idx:04d}.fqs.z"
        nb, sha = write_fqs_atomic(sp, chunk)
        out_shards.append({"file": sp.name, "rows": int(len(chunk)), "bytes": nb, "sha256": sha})
        shard_idx += 1

    pending = []
    pending_n = 0

    for sp in in_paths:
        arr = read_fqs(sp)
        stats["raw_rows"] += len(arr)

        # Tier-1 mandatory integrity
        valid = ((arr["stm"] <= 1) & (arr["res8"] >= -1) & (arr["res8"] <= 1) & (np.abs(arr["score16"].astype(np.int32)) <= 30000))
        stats["t1_corrupt"] += int((~valid).sum())
        arr = arr[valid]

        if skip_in_check:
            m = (arr["flags"] & 2) == 0
            stats["t1_in_check"] += int((~m).sum())
            arr = arr[m]

        if skip_noisy:
            m = (arr["flags"] & 1) == 0
            stats["t2_noisy"] += int((~m).sum())
            arr = arr[m]

        if drop_draw_conflict > 0:
            m = ~((arr["res8"] == 0) & (np.abs(arr["score16"].astype(np.int32)) >= drop_draw_conflict))
            stats["t2_draw_conflict"] += int((~m).sum())
            arr = arr[m]

        if drop_swing:
            m = (arr["flags"] & 4) == 0
            stats["t2_swing"] += int((~m).sum())
            arr = arr[m]

        if hs800_p1 < 100 or hs800_p2 < 100:
            abs_sc = np.abs(arr["score16"].astype(np.int32))
            # Fast vectorized deterministic hash from packed board + stm
            h_val = (arr["packed"][:, 0].astype(np.uint32) * 1315423911
                     ^ arr["packed"][:, 7].astype(np.uint32) * 2654435761
                     ^ arr["packed"][:, 15].astype(np.uint32) * 2246822519
                     ^ arr["packed"][:, 23].astype(np.uint32) * 3266489917
                     ^ arr["stm"].astype(np.uint32) * 668265263) % 100
            keep_hs = np.ones(len(arr), dtype=bool)
            b1 = (abs_sc >= 800) & (abs_sc < 1200)
            b2 = abs_sc >= 1200
            keep_hs[b1] = h_val[b1] < hs800_p1
            keep_hs[b2] = h_val[b2] < hs800_p2
            stats["t2_hs800"] += int((~keep_hs).sum())
            arr = arr[keep_hs]

        if dedup_mode == "none":
            pending.append(arr)
            pending_n += len(arr)
            stats["kept_rows"] += len(arr)
            if pending_n >= shard_rows:
                cat = np.concatenate(pending, axis=0)
                while len(cat) >= shard_rows:
                    flush_chunk(cat[:shard_rows])
                    cat = cat[shard_rows:]
                pending = [cat] if len(cat) > 0 else []
                pending_n = len(cat)
        elif dedup_mode == "first":
            keep_idx = []
            for i in range(len(arr)):
                k = hashlib.blake2b(arr[i]["packed"].tobytes() + bytes([int(arr[i]["stm"])]), digest_size=12).digest()
                if k in seen_first:
                    stats["t2_dedup_merged"] += 1
                else:
                    seen_first.add(k)
                    keep_idx.append(i)
            if keep_idx:
                sub = arr[keep_idx]
                pending.append(sub)
                pending_n += len(sub)
                stats["kept_rows"] += len(sub)
                if pending_n >= shard_rows:
                    cat = np.concatenate(pending, axis=0)
                    while len(cat) >= shard_rows:
                        flush_chunk(cat[:shard_rows])
                        cat = cat[shard_rows:]
                    pending = [cat] if len(cat) > 0 else []
                    pending_n = len(cat)
        else:  # avg
            for i in range(len(arr)):
                pk_b = arr[i]["packed"].tobytes()
                stm_i = int(arr[i]["stm"])
                k = hashlib.blake2b(pk_b + bytes([stm_i]), digest_size=12).digest()
                sc_i = int(arr[i]["score16"])
                res_i = int(arr[i]["res8"])
                fl_i = int(arr[i]["flags"])
                ent = avg_table.get(k)
                if ent is None:
                    avg_table[k] = [pk_b, stm_i, sc_i, res_i, 1, fl_i]
                else:
                    ent[2] += sc_i
                    ent[3] += res_i
                    ent[4] += 1
                    stats["t2_dedup_merged"] += 1

    if dedup_mode == "avg":
        n_u = len(avg_table)
        stats["kept_rows"] = n_u
        buf = np.empty(min(n_u, shard_rows), dtype=FQS_DTYPE)
        bn = 0
        for pk_b, stm_i, sc_sum, res_sum, cnt, fl_i in avg_table.values():
            buf[bn]["packed"] = np.frombuffer(pk_b, dtype=np.uint8)
            buf[bn]["stm"] = stm_i
            buf[bn]["score16"] = max(-30000, min(30000, int(round(sc_sum / cnt))))
            buf[bn]["res8"] = 1 if res_sum > 0 else (-1 if res_sum < 0 else 0)
            buf[bn]["flags"] = fl_i
            buf[bn]["weight_u8"] = min(192, max(128, int(round(128.0 * math.sqrt(cnt)))))
            bn += 1
            if bn >= len(buf):
                flush_chunk(buf[:bn])
                bn = 0
        if bn > 0:
            flush_chunk(buf[:bn])
    else:
        if pending_n > 0:
            flush_chunk(np.concatenate(pending, axis=0))

    el = round(time.time() - t0, 2)
    summary = {
        **stats,
        "dedup_mode": dedup_mode,
        "elapsed_s": el,
        "rec_per_s": round(stats["raw_rows"] / max(0.001, el), 1),
        "out_shards": out_shards,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def selftest() -> int:
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        in_p = tp / "in.fqs.z"
        arr = np.zeros(10, dtype=FQS_DTYPE)
        # Rows 0,1,2: exact duplicate board+stm with scores 100, 140, 120 -> avg 120, weight_u8 = round(128*sqrt(3)) = 192 (clipped)
        for i, sc in enumerate([100, 140, 120]):
            arr[i]["packed"][0] = 0x61
            arr[i]["stm"] = 0
            arr[i]["score16"] = sc
            arr[i]["res8"] = 1
            arr[i]["flags"] = 0
            arr[i]["weight_u8"] = 128
        # Row 3: in_check (bit1) -> dropped
        arr[3]["packed"][0] = 0x62; arr[3]["flags"] = 2
        # Row 4: draw conflict (res=0, score=750) -> dropped
        arr[4]["packed"][0] = 0x63; arr[4]["score16"] = 750; arr[4]["res8"] = 0
        # Row 5: noisy (bit0) -> kept when skip_noisy=False
        arr[5]["packed"][0] = 0x64; arr[5]["score16"] = 50; arr[5]["flags"] = 1
        # Rows 6..9: distinct clean rows
        for i in range(6, 10):
            arr[i]["packed"][0] = 0x70 + i; arr[i]["score16"] = 10 * i; arr[i]["res8"] = 0; arr[i]["weight_u8"] = 128
        write_fqs_atomic(in_p, arr, level=1)

        s_first = filter_and_dedup([in_p], tp / "out_first", drop_draw_conflict=600, dedup_mode="first")
        assert s_first["t1_in_check"] == 1 and s_first["t2_draw_conflict"] == 1 and s_first["t2_dedup_merged"] == 2 and s_first["kept_rows"] == 6, s_first

        s_avg = filter_and_dedup([in_p], tp / "out_avg", drop_draw_conflict=600, dedup_mode="avg")
        out_a = read_fqs(tp / "out_avg/fqs_s0000.fqs.z")
        dup_row = out_a[out_a["packed"][:, 0] == 0x61][0]
        assert int(dup_row["score16"]) == 120 and int(dup_row["weight_u8"]) == 192 and int(dup_row["res8"]) == 1, dup_row
        print("FILTER_FQS_TO_FQS_SELFTEST_PASS:", json.dumps({"first": s_first["kept_rows"], "avg_score": int(dup_row["score16"]), "avg_w": int(dup_row["weight_u8"])}))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--keep-in-check", action="store_true")
    ap.add_argument("--skip-noisy", action="store_true")
    ap.add_argument("--drop-draw-conflict", type=int, default=600)
    ap.add_argument("--drop-swing", action="store_true")
    ap.add_argument("--hs800-p1", type=int, default=100)
    ap.add_argument("--hs800-p2", type=int, default=100)
    ap.add_argument("--dedup-mode", choices=["none", "first", "avg"], default="none")
    ap.add_argument("--shard-rows", type=int, default=500_000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    in_p = Path(args.in_dir)
    shards = sorted(list(in_p.glob("*.fqs")) + list(in_p.glob("*.fqs.z")))
    assert shards, f"No shards in {in_p}"
    rep = filter_and_dedup(
        shards, Path(args.out_dir),
        skip_in_check=(not args.keep_in_check), skip_noisy=args.skip_noisy,
        drop_draw_conflict=args.drop_draw_conflict, drop_swing=args.drop_swing,
        hs800_p1=args.hs800_p1, hs800_p2=args.hs800_p2,
        dedup_mode=args.dedup_mode, shard_rows=args.shard_rows,
    )
    print("FILTER_FQS_DONE:", json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
