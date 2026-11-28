"""Independent Read-Only Verifier for Held-Out 4,000 Syzygy Labels & Zero Anchor Overlap.

Directly verifies the two open checks Opus noted in OPUS-2711-HELDOUT-RECOUNTED:
  1. Re-probes every position in anchors/heldout_syzygy_4k.json against C:/nnue-lab/syzygy/3-4-5
     and asserts 100% exact WDL label agreement (draws == 0, wins == +2/-2 matching res8).
  2. Computes all 4 board symmetries (identity, file-mirror, rank-flip+color-swap, both) for:
       - heldout_syzygy_4k.json (4,000 pos)
       - dead_draws_20k_clean.fqs.z (20,000 pos)
       - dead_draws_20k_s5disjoint.fqs.z (20,000 pos)
       - won_endings_syzygy_20k.fqs.z (20,000 pos)
       - all 6 S5/S7 net_sanity v2 FENs
     and reports exact & symmetry overlap counts + full SHA-256 digests.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zlib
from pathlib import Path

import chess
import chess.syzygy
import numpy as np

LAB = Path(r"C:\nnue-lab")
ANCHORS = LAB / "neon/forge_fixes/anchors"
TB_DIR = LAB / "tablebases/syzygy345"

FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)),
    ("stm", np.uint8),
    ("score16", np.int16),
    ("res8", np.int8),
    ("flags", np.uint8),
    ("weight_u8", np.uint8),
])

S5_S7_FENS = {
    "S5_K-K": "8/8/8/4k3/8/8/4K3/8 w - - 0 1",
    "S5_KN-K": "8/8/8/4k3/8/8/3NK3/8 w - - 0 1",
    "S5_KB-K": "8/8/8/4k3/8/8/3BK3/8 w - - 0 1",
    "S5_KNN-K": "8/8/8/4k3/8/8/2NNK3/8 w - - 0 1",
    "S7_KQ-K": "8/8/8/4k3/8/8/3QK3/8 w - - 0 1",
    "S7_KR-K": "8/8/8/4k3/8/8/3RK3/8 w - - 0 1",
}

CODE_TO_PIECE = {
    1: chess.Piece(chess.PAWN, chess.WHITE),
    2: chess.Piece(chess.KNIGHT, chess.WHITE),
    3: chess.Piece(chess.BISHOP, chess.WHITE),
    4: chess.Piece(chess.ROOK, chess.WHITE),
    5: chess.Piece(chess.QUEEN, chess.WHITE),
    6: chess.Piece(chess.KING, chess.WHITE),
    7: chess.Piece(chess.PAWN, chess.BLACK),
    8: chess.Piece(chess.KNIGHT, chess.BLACK),
    9: chess.Piece(chess.BISHOP, chess.BLACK),
    10: chess.Piece(chess.ROOK, chess.BLACK),
    11: chess.Piece(chess.QUEEN, chess.BLACK),
    12: chess.Piece(chess.KING, chess.BLACK),
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def board_from_packed(packed: np.ndarray, stm: int) -> chess.Board:
    b = chess.Board.empty()
    for i in range(32):
        byte = int(packed[i])
        c0 = byte & 0xF
        c1 = (byte >> 4) & 0xF
        if c0:
            b.set_piece_at(2 * i, CODE_TO_PIECE[c0])
        if c1:
            b.set_piece_at(2 * i + 1, CODE_TO_PIECE[c1])
    b.turn = chess.WHITE if stm == 0 else chess.BLACK
    return b


def sym_keys(b: chess.Board) -> tuple[str, set[str]]:
    def epd2(x: chess.Board) -> str:
        parts = x.fen().split(" ")
        return parts[0] + " " + parts[1]

    b_m = b.transform(chess.flip_horizontal)
    b_f = b.mirror()  # vertical flip + color swap + turn flip
    b_fm = b_f.transform(chess.flip_horizontal)
    exact = epd2(b)
    return exact, {exact, epd2(b_m), epd2(b_f), epd2(b_fm)}


def load_fqs_keys(path: Path) -> tuple[set[str], set[str], int]:
    raw = zlib.decompress(path.read_bytes()) if path.name.endswith(".z") else path.read_bytes()
    assert raw[:8] == FQS_MAGIC
    arr = np.frombuffer(raw, dtype=FQS_DTYPE, offset=8)
    exacts: set[str] = set()
    syms: set[str] = set()
    for row in arr:
        b = board_from_packed(row["packed"], int(row["stm"]))
        ex, sy = sym_keys(b)
        exacts.add(ex)
        syms.update(sy)
    return exacts, syms, len(arr)


def main() -> int:
    ho_path = ANCHORS / "heldout_syzygy_4k.json"
    ho = json.loads(ho_path.read_text(encoding="utf-8"))
    rows = ho["positions"] if isinstance(ho, dict) and "positions" in ho else ho
    assert len(rows) == 4000, f"Expected 4000 held-out rows, got {len(rows)}"

    # 1. Verify every single Syzygy WDL label
    tb = chess.syzygy.open_tablebase(str(TB_DIR))
    n_draws = 0
    n_wins = 0
    wdl_mismatches = []
    ho_exact: set[str] = set()
    ho_syms: set[str] = set()
    try:
        for idx, rec in enumerate(rows):
            b = chess.Board(rec["fen"])
            assert b.is_valid() and not b.is_check(), f"Invalid/in-check heldout row {idx}: {rec}"
            ex, sy = sym_keys(b)
            ho_exact.add(ex)
            ho_syms.update(sy)

            # Handle both 2-piece K-K (not in 3-4-5 TB; FIDE dead draw) and 3-5 piece TB
            n_pcs = chess.popcount(b.occupied)
            if n_pcs <= 2 or b.is_insufficient_material():
                tb_wdl = 0
            else:
                tb_wdl = tb.probe_wdl(b)

            exp_wdl = int(rec["wdl_stm"])
            if rec["kind"] == "draw":
                n_draws += 1
                if tb_wdl != 0 or exp_wdl != 0:
                    wdl_mismatches.append((idx, rec["fen"], exp_wdl, tb_wdl))
            else:
                n_wins += 1
                # heldout_syzygy_4k.json encodes wdl_stm as -1/+1 (sign of Syzygy WDL -2/+2)
                if abs(tb_wdl) != 2 or (1 if tb_wdl > 0 else -1) != exp_wdl:
                    wdl_mismatches.append((idx, rec["fen"], exp_wdl, tb_wdl))
    finally:
        tb.close()

    # 2. Verify zero overlap against all anchor shards & S5/S7
    s5_exact = {}
    s5_syms = {}
    for k, fen in S5_S7_FENS.items():
        ex, sy = sym_keys(chess.Board(fen))
        s5_exact[k] = ex
        s5_syms[k] = sy

    anc_report = {}
    for fn in ("dead_draws_20k_clean.fqs.z", "dead_draws_20k_s5disjoint.fqs.z", "won_endings_syzygy_20k.fqs.z"):
        p = ANCHORS / fn
        ex_set, sy_set, n_rows = load_fqs_keys(p)
        s5_ex_hits = [k for k, ex in s5_exact.items() if ex in ex_set]
        s5_sy_hits = [k for k, sy in s5_syms.items() if (sy & sy_set)]
        anc_report[fn] = {
            "rows": n_rows,
            "unique_exact": len(ex_set),
            "sha256": sha256_file(p),
            "heldout_exact_overlap": len(ho_exact & ex_set),
            "heldout_sym_overlap": len(ho_exact & sy_set),
            "s5_s7_exact_hits": s5_ex_hits,
            "s5_s7_sym_hits": s5_sy_hits,
        }

    rep = {
        "heldout_file": str(ho_path),
        "heldout_sha256": sha256_file(ho_path),
        "total_rows": len(rows),
        "unique_exact": len(ho_exact),
        "draws_checked": n_draws,
        "wins_checked": n_wins,
        "syzygy_wdl_mismatches": len(wdl_mismatches),
        "sample_mismatches": wdl_mismatches[:5],
        "heldout_vs_s5_s7_sym_hits": [k for k, sy in s5_syms.items() if (sy & ho_syms)],
        "anchors": anc_report,
    }
    out_p = ANCHORS / "heldout_integrity_verification.json"
    out_p.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print("SYZYGY_HELDOUT_VERIFICATION:", json.dumps(rep, indent=2))
    assert rep["syzygy_wdl_mismatches"] == 0, f"WDL mismatches: {wdl_mismatches[:5]}"
    assert anc_report["dead_draws_20k_s5disjoint.fqs.z"]["heldout_sym_overlap"] == 0
    assert anc_report["dead_draws_20k_s5disjoint.fqs.z"]["s5_s7_sym_hits"] == []
    assert anc_report["dead_draws_20k_clean.fqs.z"]["heldout_sym_overlap"] == 0
    assert anc_report["won_endings_syzygy_20k.fqs.z"]["heldout_sym_overlap"] == 0
    print("SYZYGY_HELDOUT_INTEGRITY_100PCT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
