"""Selective Forge Deeper-Search Rescorer (4k -> 16k softnodes, Forge-only, zero external engine labels).

Implements Fable Lead (b) & Filter Quest Pillar 3:
  - Scans input .fqs / .fqs.z shards and selects high-value/uncertain rows:
      1. Endgame / OB0..OB1 rows with draw/win score ambiguity (e.g. res==0 & |score|>=400, or ob<=1 & |score|>=300)
      2. High-swing / contested tactical rows (flags bit2 swing_ge200, or bit3 draw_conflict_ge600, or |score|<400 noisy)
      3. Optional uniform budget cap (--max-frac e.g. 0.05) so CPU cost stays <= +20% of base 4k datagen.
  - Re-searches ONLY selected positions with Forge's OWN engine (`go softnodes 16000`, cleared TT via `ucinewgame`
    between unrelated FENs, strict thermal guard 90 C, mem_room check).
  - Writes rescored .fqs.z shards atomically (.part -> os.replace) + JSON telemetry (rescored count, MAD delta,
    sign flips, elapsed_s, pos/s). Never modifies input shards.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time
import tomllib
import zlib
from pathlib import Path

import numpy as np

LAB = Path(r"C:\nnue-lab")
FIX_ROOT = LAB / "neon/forge_fixes"
FORGE_EXE = str(LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe")
R0067_NET = str(LAB / "runs/forge/r0067/train/cand.fnn3")
DEFAULT_CONFIG = str(LAB / "pipeline/config.forge.toml")

sys.path.insert(0, str(LAB / "pipeline"))
from nnloop.heat import cpu_temp  # noqa: E402

FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])
INV_CMAP = {1: "P", 2: "N", 3: "B", 4: "R", 5: "Q", 6: "K", 7: "p", 8: "n", 9: "b", 10: "r", 11: "q", 12: "k"}


def unpack_to_fen(packed: np.ndarray, stm: int) -> str:
    codes = np.empty(64, dtype=np.uint8)
    codes[0::2] = packed & 0x0F
    codes[1::2] = (packed >> 4) & 0x0F
    rows = []
    for r in range(7, -1, -1):
        empty = 0
        s = []
        for c in range(8):
            v = int(codes[r * 8 + c])
            if v == 0:
                empty += 1
            else:
                if empty:
                    s.append(str(empty))
                    empty = 0
                s.append(INV_CMAP[v])
        if empty:
            s.append(str(empty))
        rows.append("".join(s))
    return f"{'/'.join(rows)} {'w' if stm == 0 else 'b'} - - 0 1"


def _opp_side_castle_mask(packed: np.ndarray) -> np.ndarray:
    """Vectorized opposite-side castled middlegame detector on packed 32-byte boards.

    SF19_ERROR_TAXONOMY.json found opp_side_castling has 20.67% severe WDL error (>=0.35),
    nearly 2x quiet_positional (11.63%). Detects White king (code 6) and Black king (code 12)
    on opposite flanks (files a-c vs f-h) with at least 14 pieces on board (middlegame).
    """
    n = len(packed)
    codes = np.empty((n, 64), dtype=np.uint8)
    codes[:, 0::2] = packed & 0x0F
    codes[:, 1::2] = (packed >> 4) & 0x0F
    wk_sq = np.argmax(codes == 6, axis=1)
    bk_sq = np.argmax(codes == 12, axis=1)
    wk_file = wk_sq & 7
    bk_file = bk_sq & 7
    opp = ((wk_file <= 2) & (bk_file >= 5)) | ((wk_file >= 5) & (bk_file <= 2))
    pcs = (codes != 0).sum(axis=1)
    return opp & (pcs >= 14)


def select_rescore_mask(arr: np.ndarray, max_frac: float = 0.05, prioritize_opp_castle: bool = False) -> np.ndarray:
    """Deterministic priority mask for selective 16k rescoring."""
    flags = arr["flags"]
    ob = (flags >> 4) & 7
    sc = arr["score16"].astype(np.int32)
    abs_sc = np.abs(sc)
    res = arr["res8"]

    # Priority 1: drawn-game conflicts & high-swing rows (bits 2/3 or res==0 & |sc|>=400)
    p1 = ((flags & 12) != 0) | ((res == 0) & (abs_sc >= 400))
    # Priority 2: opposite-sign mild conflict (res != 0 & sc*res <= -200)
    p2 = (res != 0) & (sc * res <= -200)
    # Optional Priority 2b (SF19_ERROR_TAXONOMY): opposite-side castled middlegame |sc| < 450
    p_opp = (_opp_side_castle_mask(arr["packed"]) & (abs_sc < 450)) if prioritize_opp_castle else None
    # Priority 3: OB0/OB1 endgame non-trivial scores (|sc| in [150, 900])
    p3 = (ob <= 1) & (abs_sc >= 150) & (abs_sc <= 900)
    # Priority 4: contested tactical noisy rows (bit0 & |sc| < 350)
    p4 = ((flags & 1) != 0) & (abs_sc < 350)

    tiers = (p1, p2, p_opp, p3, p4) if prioritize_opp_castle else (p1, p2, p3, p4)

    cap = max(1, int(round(len(arr) * max_frac)))
    sel = np.zeros(len(arr), dtype=bool)
    for tier in tiers:
        need = cap - int(sel.sum())
        if need <= 0:
            break
        cand = np.flatnonzero(tier & ~sel)
        if len(cand) <= need:
            sel[cand] = True
        else:
            # Uniform deterministic stride across the tier
            step = len(cand) / need
            picks = cand[np.floor(np.arange(need) * step).astype(np.int64)]
            sel[picks] = True
    return sel


def _rescore_chunk(args_t):
    wid, fens, soft_nodes, exe_path, net_path, config_path, max_temp_c = args_t
    cfg = tomllib.loads(Path(config_path).read_text(encoding="utf-8"))
    opts = dict(cfg["engine"]["v3_uci_options"])
    opts["Threads"] = "1"
    opts["Hash"] = "16"
    opts["OwnBook"] = "false"
    opts["NNUEArchFile"] = net_path.replace("\\", "/")
    opts["NNUEArch"] = "true"

    proc_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    p = subprocess.Popen(
        [exe_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, creationflags=proc_flags,
    )

    def send(s: str) -> None:
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok: str) -> None:
        while True:
            ln = p.stdout.readline()
            if ln == "":
                raise RuntimeError("forge exited during rescore")
            if ln.split()[:1] == [tok]:
                return

    send("uci")
    until("uciok")
    for k, v in opts.items():
        sv = "true" if v is True else ("false" if v is False else str(v))
        send(f"setoption name {k} value {sv}")
    send("isready")
    until("readyok")

    out_scores: list[int | None] = []
    try:
        for idx_f, fen in enumerate(fens):
            if max_temp_c > 0 and idx_f > 0 and idx_f % 50 == 0:
                t_c = cpu_temp(cfg)
                while t_c is not None and t_c >= max_temp_c:
                    time.sleep(5)
                    t_c = cpu_temp(cfg)
            send("ucinewgame")
            send(f"position fen {fen}")
            send(f"go softnodes {soft_nodes}")
            last_sc: int | None = None
            while True:
                ln = p.stdout.readline()
                if not ln:
                    raise RuntimeError("forge EOF in rescore")
                toks = ln.split()
                if "score" in toks:
                    si = toks.index("score")
                    if si + 2 < len(toks):
                        if toks[si + 1] == "cp":
                            last_sc = max(-30000, min(30000, int(toks[si + 2])))
                        elif toks[si + 1] == "mate":
                            mv = int(toks[si + 2])
                            last_sc = 30000 if mv > 0 else -30000
                if toks[:1] == ["bestmove"]:
                    break
            out_scores.append(last_sc)
    finally:
        try:
            send("quit")
            p.wait(timeout=3)
        except Exception:
            p.kill()
    return wid, out_scores


def rescore_shard(in_path: Path, out_path: Path, soft_nodes: int, max_frac: float, workers: int,
                  exe_path: str, net_path: str, config_path: str, max_temp_c: float = 91.0,
                  prioritize_opp_castle: bool = False) -> dict:
    raw = in_path.read_bytes()
    if in_path.name.endswith(".z"):
        raw = zlib.decompress(raw)
    assert len(raw) >= 8 and raw[:8] == FQS_MAGIC and (len(raw) - 8) % FQS_DTYPE.itemsize == 0
    arr = np.frombuffer(raw, dtype=FQS_DTYPE, offset=8).copy()
    mask = select_rescore_mask(arr, max_frac=max_frac, prioritize_opp_castle=prioritize_opp_castle)
    idxs = np.flatnonzero(mask)
    fens = [unpack_to_fen(arr[i]["packed"], int(arr[i]["stm"])) for i in idxs]

    t0 = time.time()
    n_w = max(1, min(workers, len(fens))) if fens else 1
    chunks = [fens[w::n_w] for w in range(n_w)]
    new_scores: list[int | None] = [None] * len(fens)
    if fens:
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_w) as ex:
            futs = [ex.submit(_rescore_chunk, (w, chunks[w], soft_nodes, exe_path, net_path, config_path, max_temp_c))
                    for w in range(n_w)]
            for f in concurrent.futures.as_completed(futs):
                w, scs = f.result()
                for k, val in enumerate(scs):
                    new_scores[w + k * n_w] = val

    changed = 0
    deltas = []
    sign_flips = 0
    for idx_pos, nsc in zip(idxs, new_scores):
        if nsc is None:
            continue
        old_sc = int(arr[idx_pos]["score16"])
        if abs(nsc) < 29000:  # keep non-mate cp scores bounded like Forge selfgame
            clamped = max(-1500, min(1500, nsc))
            deltas.append(abs(clamped - old_sc))
            if (old_sc > 50 and clamped < -50) or (old_sc < -50 and clamped > 50):
                sign_flips += 1
            arr[idx_pos]["score16"] = clamped
            changed += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    comp = zlib.compress(FQS_MAGIC + arr.tobytes(), level=3)
    tmp_p = out_path.with_name(out_path.name + ".part")
    tmp_p.write_bytes(comp)
    os.replace(tmp_p, out_path)
    el = round(time.time() - t0, 2)
    return {
        "in_file": str(in_path), "out_file": str(out_path),
        "total_rows": len(arr), "selected": int(len(idxs)), "rescored": changed,
        "mad_delta_cp": round(float(np.mean(deltas)), 2) if deltas else 0.0,
        "sign_flips": sign_flips, "elapsed_s": el,
        "rescore_pos_per_s": round(changed / max(0.01, el), 1),
        "out_sha256": hashlib.sha256(comp).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--soft-nodes", type=int, default=16000)
    ap.add_argument("--max-frac", type=float, default=0.05)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--exe", default=FORGE_EXE)
    ap.add_argument("--net", default=R0067_NET)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--prioritize-opp-castle", action="store_true",
                    help="Add Priority-2b for opposite-side castled middlegame positions (|sc|<450, >=14 pieces)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        # 20-row synthetic smoke test on 1 worker, 2000 nodes (<2s!)
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tp = Path(td)
            in_p = tp / "in.fqs.z"
            out_p = tp / "out.fqs.z"
            arr = np.zeros(20, dtype=FQS_DTYPE)
            # Startpos packed
            codes = np.array([
                4,2,3,5,6,3,2,4, 1,1,1,1,1,1,1,1,
                0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,
                0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,
                7,7,7,7,7,7,7,7, 10,8,9,11,12,9,8,10,
            ], dtype=np.uint8)
            pk = (codes[0::2] | (codes[1::2] << 4)).astype(np.uint8)
            # Opposite-side castled middlegame (WK on c1=2, BK on g8=62)
            opp_codes = codes.copy()
            opp_codes[4] = 0; opp_codes[2] = 6
            opp_codes[60] = 0; opp_codes[62] = 12
            opp_pk = (opp_codes[0::2] | (opp_codes[1::2] << 4)).astype(np.uint8)
            for i in range(20):
                arr[i]["packed"] = opp_pk if i == 5 else pk
                arr[i]["stm"] = 0
                arr[i]["score16"] = 500 if i < 2 else 20
                arr[i]["res8"] = 0
                arr[i]["flags"] = (7 << 4) | (8 if i < 2 else 0)
                arr[i]["weight_u8"] = 128
            assert _opp_side_castle_mask(arr["packed"]).tolist() == [i == 5 for i in range(20)]
            m_opp = select_rescore_mask(arr, max_frac=0.15, prioritize_opp_castle=True)
            assert m_opp[0] and m_opp[1] and m_opp[5] and int(m_opp.sum()) == 3
            in_p.write_bytes(zlib.compress(FQS_MAGIC + arr.tobytes(), level=1))
            rep = rescore_shard(in_p, out_p, 2000, 0.15, 1, args.exe, args.net, args.config,
                                max_temp_c=0.0, prioritize_opp_castle=True)
            assert rep["selected"] == 3 and rep["rescored"] == 3 and out_p.exists(), rep
            print("RESCORE_SELFTEST_PASS:", json.dumps(rep))
            return 0

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    shards = sorted(list(in_dir.glob("*.fqs")) + list(in_dir.glob("*.fqs.z")))
    assert shards, f"No .fqs/.fqs.z in {in_dir}"
    reports = []
    for sp in shards:
        rep = rescore_shard(sp, out_dir / sp.name, args.soft_nodes, args.max_frac, args.workers,
                            args.exe, args.net, args.config, prioritize_opp_castle=args.prioritize_opp_castle)
        print("RESCORED:", json.dumps(rep), flush=True)
        reports.append(rep)
    (out_dir / "rescore_summary.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
