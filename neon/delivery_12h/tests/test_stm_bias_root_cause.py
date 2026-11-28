"""Opus/Fable STM-Bonus Root Cause Test (OPUS-2711-FABLE-NOTE-STM-BONUS-TEST, 18:10 PC).

Measures on r0202/data/filtered.plain (200k records) and on SF19-labelled r0202 / M4 sets:
  - label_stm, result_stm, static_r0067_stm, and (label - static) split by:
      1) QUIET vs NOISY (bestmove capture/promo)  <-- tests --keep-noisy hypothesis!
      2) White-to-move vs Black-to-move
      3) Output bucket ob0..ob7 (piece count)
      4) ply bucket (8..15 vs 16..39 vs 40+)
  - On SF19-scored positions (M4 + task1f r0202 sample if present):
      label - SF19 and static_r0067 - SF19 split by quiet/noisy, STM, and ob0..ob7.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import chess
import numpy as np

LAB = Path(r"C:\nnue-lab")
sys.path.insert(0, str(LAB / "pipeline"))
sys.path.insert(0, str(LAB / "neon/forge_fixes"))
import forge_v3  # noqa: E402

CMAP = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6, "p": 7, "n": 8, "b": 9, "r": 10, "q": 11, "k": 12}


def fast_eval_v3(net, fen: str) -> tuple[int, int, int]:
    """Return (cp_stm, stm_idx_0w_1b, ob)."""
    parts = fen.split()
    stm = 0 if parts[1] == "w" else 1
    codes = np.zeros(64, dtype=np.uint8)
    r, c = 7, 0
    pc = 0
    for ch in parts[0]:
        if ch == "/":
            r -= 1; c = 0
        elif "1" <= ch <= "8":
            c += ord(ch) - 48
        else:
            codes[r * 8 + c] = CMAP[ch]; c += 1; pc += 1
    ob = min(7, max(0, (pc - 2) // 4))
    cp = forge_v3.reference_eval(net, codes, stm == 0)
    return cp, stm, ob


def parse_plain_sample(path: Path, max_n: int = 100000):
    recs = []
    cur = {}
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if ln == "e":
                if "fen" in cur and "score" in cur and "result" in cur:
                    recs.append(cur)
                    if len(recs) >= max_n:
                        break
                cur = {}
            elif ln.startswith("fen "):
                cur["fen"] = ln[4:]
            elif ln.startswith("move "):
                cur["move"] = ln[5:]
            elif ln.startswith("score "):
                cur["score"] = int(ln[6:])
            elif ln.startswith("ply "):
                cur["ply"] = int(ln[4:])
            elif ln.startswith("result "):
                cur["result"] = int(ln[7:])
    return recs


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    lbl = np.array([r["score"] for r in rows], dtype=np.float64)
    st = np.array([r["static"] for r in rows], dtype=np.float64)
    res = np.array([r["result"] for r in rows], dtype=np.float64)
    out = {
        "n": len(rows),
        "mean_label": round(float(lbl.mean()), 2),
        "median_label": round(float(np.median(lbl)), 1),
        "mean_static_r0067": round(float(st.mean()), 2),
        "mean_label_minus_static": round(float((lbl - st).mean()), 2),
        "mean_result_stm": round(float(res.mean()), 4),
    }
    if "sf19" in rows[0]:
        sf = np.array([r["sf19"] for r in rows], dtype=np.float64)
        out["mean_sf19"] = round(float(sf.mean()), 2)
        out["mean_label_minus_sf19"] = round(float((lbl - sf).mean()), 2)
        out["mean_static_minus_sf19"] = round(float((st - sf).mean()), 2)
    return out


def main() -> int:
    net = forge_v3.read_net(str(LAB / "runs/forge/r0067/train/cand.fnn3"))
    r202_path = LAB / "runs/forge/r0202/data/filtered.plain"
    recs = parse_plain_sample(r202_path, max_n=25000)

    enriched = []
    for r in recs:
        b = chess.Board(r["fen"])
        mv_s = r.get("move", "")
        is_noisy = False
        if mv_s and mv_s != "0000":
            try:
                mv = chess.Move.from_uci(mv_s)
                is_noisy = b.is_capture(mv) or (mv.promotion is not None)
            except Exception:
                pass
        is_chk = b.is_check()
        st_cp, stm, ob = fast_eval_v3(net, r["fen"])
        enriched.append({
            "score": r["score"],
            "result": r["result"],
            "ply": r.get("ply", -1),
            "static": st_cp,
            "stm": stm,
            "ob": ob,
            "noisy": is_noisy,
            "in_check": is_chk,
        })

    # Check pair symmetry: for each position, compute net(pos_stm) + net(pos_flipped_stm) -> pure STM bonus!
    # Wait: flip side-to-move ONLY (not colors) on quiet non-check positions to measure exact STM tempo in net!
    stm_bonuses_by_ob = defaultdict(list)
    for r in recs[:4000]:
        parts = r["fen"].split()
        b = chess.Board(r["fen"])
        if b.is_check():
            continue
        # Test swapping only side to move (approximate tempo if legal)
        alt_parts = list(parts)
        alt_parts[1] = "b" if parts[1] == "w" else "w"
        alt_parts[3] = "-"
        alt_fen = " ".join(alt_parts)
        try:
            b2 = chess.Board(alt_fen)
            if not b2.is_valid():
                continue
        except Exception:
            continue
        e1, _, ob = fast_eval_v3(net, r["fen"])
        e2, _, _ = fast_eval_v3(net, alt_fen)
        stm_bonuses_by_ob[ob].append(0.5 * (e1 + e2))

    report = {
        "r0202_sample_n": len(enriched),
        "r0202_all": summarize(enriched),
        "r0202_quiet": summarize([x for x in enriched if not x["noisy"] and not x["in_check"]]),
        "r0202_noisy": summarize([x for x in enriched if x["noisy"]]),
        "r0202_in_check": summarize([x for x in enriched if x["in_check"]]),
        "r0202_white_stm": summarize([x for x in enriched if x["stm"] == 0]),
        "r0202_black_stm": summarize([x for x in enriched if x["stm"] == 1]),
        "r0202_quiet_white_stm": summarize([x for x in enriched if not x["noisy"] and not x["in_check"] and x["stm"] == 0]),
        "r0202_quiet_black_stm": summarize([x for x in enriched if not x["noisy"] and not x["in_check"] and x["stm"] == 1]),
        "r0202_by_ob_all": {f"ob{b}": summarize([x for x in enriched if x["ob"] == b]) for b in range(8)},
        "r0202_by_ob_quiet": {f"ob{b}": summarize([x for x in enriched if not x["noisy"] and not x["in_check"] and x["ob"] == b]) for b in range(8)},
        "r0202_by_ob_noisy": {f"ob{b}": summarize([x for x in enriched if x["noisy"] and x["ob"] == b]) for b in range(8)},
        "r0067_exact_stm_tempo_by_ob": {
            f"ob{b}": {
                "n": len(stm_bonuses_by_ob[b]),
                "mean_cp": round(float(np.mean(stm_bonuses_by_ob[b])), 2) if stm_bonuses_by_ob[b] else None,
            } for b in range(8)
        },
    }

    # Now check task1f SF19-labelled r0202 positions if available!
    t1f_candidates = [
        LAB / "neon/net_search_probe/task1f_sf19_r0202.jsonl",
        LAB / "neon/net_search_probe/task1f_r0202_sf19.jsonl",
        LAB / "neon/net_search_probe/task1f_sf19_labels.jsonl",
        LAB / "neon/filter_quest/m4_eval/m4_sf19_4000.jsonl",
    ]
    sf_results = {}
    for cand in t1f_candidates:
        if not cand.exists():
            continue
        rows = []
        for ln in cand.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            j = json.loads(ln)
            fen = j.get("fen")
            sf = j.get("sf19_cp", j.get("sf_cp", j.get("sf19_score")))
            lbl = j.get("r0202_score", j.get("score", j.get("label")))
            if fen is None or sf is None:
                continue
            if abs(int(sf)) > 2000:
                continue
            st_cp, stm, ob = fast_eval_v3(net, fen)
            b = chess.Board(fen)
            mv_s = j.get("move", "")
            is_noisy = False
            if mv_s and mv_s != "0000":
                try:
                    mv = chess.Move.from_uci(mv_s)
                    is_noisy = b.is_capture(mv) or (mv.promotion is not None)
                except Exception:
                    pass
            rows.append({
                "score": int(lbl) if lbl is not None else int(sf),
                "has_lbl": lbl is not None,
                "result": int(j.get("result", 0)),
                "static": st_cp,
                "sf19": int(sf),
                "stm": stm,
                "ob": ob,
                "noisy": is_noisy,
                "in_check": b.is_check(),
            })
        if rows:
            sf_results[cand.name] = {
                "all": summarize(rows),
                "white_stm": summarize([x for x in rows if x["stm"] == 0]),
                "black_stm": summarize([x for x in rows if x["stm"] == 1]),
                "quiet": summarize([x for x in rows if not x["noisy"] and not x["in_check"]]),
                "noisy": summarize([x for x in rows if x["noisy"]]),
                "by_ob": {f"ob{b}": summarize([x for x in rows if x["ob"] == b]) for b in range(8)},
            }
    report["sf19_sets"] = sf_results

    out_p = LAB / "neon/forge_fixes/stm_bias_root_cause.json"
    out_p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "r0202_all": report["r0202_all"],
        "r0202_quiet": report["r0202_quiet"],
        "r0202_noisy": report["r0202_noisy"],
        "r0202_in_check": report["r0202_in_check"],
        "r0202_quiet_w": report["r0202_quiet_white_stm"],
        "r0202_quiet_b": report["r0202_quiet_black_stm"],
        "r0067_exact_stm_tempo_by_ob": report["r0067_exact_stm_tempo_by_ob"],
        "sf19_sets_keys": list(sf_results.keys()),
    }, indent=2))
    if sf_results:
        for k, v in sf_results.items():
            print(f"--- SF19 SET {k} ---")
            print(json.dumps({"all": v["all"], "w": v["white_stm"], "b": v["black_stm"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
