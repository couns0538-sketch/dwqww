#!/usr/bin/env python3
"""S10-2: which WAC300 positions flipped between the OFF reference and each rejected S10 idea (ON), from Sol's logs.

Inputs (all read-only, extracted from Sol's sealed archives on commit 17aa0cae):
  --off  DIR  Sol's S07 native WAC300 run of the Lprime build (OFF; `result.json` + `001_wac300_fixedtime.stdout`)
  --on   NAME=DIR  one per idea: `<idea>/Lprime/qualification/wac_ON` (`result.json` + `000_WAC300_1000MS.stdout`)
  --epd  the frozen WAC300 suite (sha256 9bfb7b42...)
All runs: Sol's S07 screen tool, `go movetime 1000`, Threads=1, Hash=16, OwnBook=false, Clear Hash before every position,
one process for all 300 positions. Solved = Sol's own `bestmove_allowed` flag (in bm, not in am); re-checked here
with python-chess. For every flipped position the tool reports the final `info depth` line of OFF and ON (depth,
score, nodes) and classifies the key move (capture / check / quiet / promotion) with python-chess.
Writes --out-json and --out-md (the table).
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path

import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+) .*?nodes (\d+) nps (\d+)")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_epd(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        board, ops = chess.Board.from_epd(line)
        bm = [m.uci() for m in ops.get("bm", [])]
        am = [m.uci() for m in ops.get("am", [])]
        rows.append({"id": ops["id"], "fen": board.fen(), "bm": bm, "am": am})
    return rows


def finals(stdout_path):
    """Per position (in order): last scored `info depth` line before each `bestmove`, plus the bestmove."""
    out, last = [], None
    for line in Path(stdout_path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = INFO.match(line)
        if m:
            last = {"depth": int(m[1]), "score": ("M" if m[2] == "mate" else "") + m[3], "nodes": int(m[4]), "nps": int(m[5])}
        elif line.startswith("bestmove "):
            out.append({"bestmove": line.split()[1], **(last or {})})
            last = None
    return out


def kind(fen, uci):
    b = chess.Board(fen)
    mv = chess.Move.from_uci(uci)
    tags = []
    if mv.promotion:
        tags.append("promo")
    if b.is_capture(mv):
        tags.append("capture")
    if b.gives_check(mv):
        tags.append("check")
    return "+".join(tags) if tags else "quiet"


def solved_set(result, epd):
    res = {r["id"]: r for r in result["results"]}
    solved = set()
    for row in epd:
        r = res[row["id"]]
        mv = r["bestmove_uci"]
        mine = (mv in row["bm"] if row["bm"] else True) and mv not in row["am"]
        if mine != bool(r["bestmove_allowed"]):
            raise ValueError(f"solved flag disagrees with python-chess for {row['id']}")
        if mine:
            solved.add(row["id"])
    return solved


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--off", required=True)
    ap.add_argument("--on", action="append", required=True, help="NAME=DIR")
    ap.add_argument("--epd", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    a = ap.parse_args(argv)
    epd = load_epd(a.epd)
    ids = [r["id"] for r in epd]
    by_id = {r["id"]: r for r in epd}
    off_dir = Path(a.off)
    off_res = json.loads((off_dir / "result.json").read_text())
    off_fin = finals(off_dir / "001_wac300_fixedtime.stdout")
    npos = len(epd)
    if len(off_fin) != npos:
        raise ValueError(f"OFF run has {len(off_fin)} bestmoves for {npos} positions")
    off_solved = solved_set(off_res, epd)
    report = {"epd": a.epd, "epd_sha256": sha256(a.epd), "off": {"dir": str(off_dir), "solved": len(off_solved),
              "result_sha256": sha256(off_dir / "result.json")}, "ideas": {}}
    md = [f"OFF reference (Sol S07 native WAC300, Lprime build, 1000 ms): **{len(off_solved)}/{npos}**.", "",
          "| idea | ON | delta vs OFF | lost (OFF ok, ON fail) | gained (OFF fail, ON ok) |", "|---|---:|---:|---|---|"]
    detail = []
    for spec in a.on:
        name, _, d = spec.partition("=")
        on_dir = Path(d)
        on_res = json.loads((on_dir / "result.json").read_text())
        on_fin = finals(on_dir / "000_WAC300_1000MS.stdout")
        if len(on_fin) != npos:
            raise ValueError(f"{name}: {len(on_fin)} bestmoves for {npos} positions")
        on_solved = solved_set(on_res, epd)
        lost = [i for i in ids if i in off_solved and i not in on_solved]
        gained = [i for i in ids if i not in off_solved and i in on_solved]
        rows = []
        for i in lost + gained:
            k = ids.index(i)
            key = by_id[i]["bm"][0] if by_id[i]["bm"] else None
            rows.append({"id": i, "change": "lost" if i in lost else "gained", "bm": by_id[i]["bm"], "am": by_id[i]["am"],
                         "key_move_kind": kind(by_id[i]["fen"], key) if key else "am-only",
                         "off": off_fin[k], "on": on_fin[k]})
        kinds_lost = {}
        for r in rows:
            if r["change"] == "lost":
                kinds_lost[r["key_move_kind"]] = kinds_lost.get(r["key_move_kind"], 0) + 1
        # speed/depth proxy over all 300 positions: nodes and depth of the final scored info line (about 1 s of search)
        ratios = sorted(on_fin[k]["nodes"] / off_fin[k]["nodes"] for k in range(npos)
                        if on_fin[k].get("nodes") and off_fin[k].get("nodes"))
        nps_on = sorted(on_fin[k]["nps"] for k in range(npos) if on_fin[k].get("nps"))
        nps_off = sorted(off_fin[k]["nps"] for k in range(npos) if off_fin[k].get("nps"))
        ddep = sorted(on_fin[k]["depth"] - off_fin[k]["depth"] for k in range(npos)
                      if on_fin[k].get("depth") and off_fin[k].get("depth") and on_fin[k]["depth"] < 64 and off_fin[k]["depth"] < 64)
        report["ideas"][name] = {"dir": str(on_dir), "result_sha256": sha256(on_dir / "result.json"),
                                 "solved": len(on_solved), "delta_vs_off": len(on_solved) - len(off_solved),
                                 "lost": lost, "gained": gained, "lost_key_move_kinds": kinds_lost,
                                 "median_final_nodes_ratio_on_off": ratios[len(ratios) // 2] if ratios else None,
                                 "median_final_nps_on": nps_on[len(nps_on) // 2] if nps_on else None,
                                 "median_final_nps_off": nps_off[len(nps_off) // 2] if nps_off else None,
                                 "median_final_depth_on_minus_off": ddep[len(ddep) // 2] if ddep else None,
                                 "mean_final_depth_on_minus_off": round(sum(ddep) / len(ddep), 3) if ddep else None,
                                 "rows": rows}
        md.append(f"| {name} | {len(on_solved)} | {len(on_solved) - len(off_solved):+d} | {', '.join(lost) or '-'} | "
                  f"{', '.join(gained) or '-'} |")
        detail += ["", f"### {name}: {len(lost)} lost, {len(gained)} gained; key move of the lost ones: "
                   + (", ".join(f"{k} {v}" for k, v in sorted(kinds_lost.items())) or "-"), "",
                   "| id | change | bm/am | key move | OFF move (depth, score) | ON move (depth, score) |",
                   "|---|---|---|---|---|---|"]
        for r in rows:
            o, w = r["off"], r["on"]
            detail.append(f"| {r['id']} | {r['change']} | {'bm ' + ' '.join(r['bm']) if r['bm'] else ''}"
                          f"{' am ' + ' '.join(r['am']) if r['am'] else ''} | {r['key_move_kind']} | "
                          f"{o['bestmove']} (d{o.get('depth')}, {o.get('score')}) | {w['bestmove']} (d{w.get('depth')}, {w.get('score')}) |")
    # flips shared by several ideas point at the OFF run (or run conditions), not at one idea
    names = list(report["ideas"])
    lost_count = {i: sum(i in report["ideas"][n]["lost"] for n in names) for i in ids}
    gain_count = {i: sum(i in report["ideas"][n]["gained"] for n in names) for i in ids}
    md += ["", "Cross-idea view (a flip shared by 3-4 of the 4 ideas is more likely run-to-run noise of the single OFF run"
           " than an effect of one idea):", "",
           "| idea | lost | gained | lost only by this idea | lost by >=3 ideas | gained by >=3 ideas |"
           " median NPS ON / OFF (final info line) | mean depth ON-OFF |", "|---|---:|---:|---|---:|---:|---:|---:|"]
    for n in names:
        r = report["ideas"][n]
        only = [i for i in r["lost"] if lost_count[i] == 1]
        r["lost_only_here"] = only
        r["lost_shared_ge3"] = [i for i in r["lost"] if lost_count[i] >= 3]
        r["gained_shared_ge3"] = [i for i in r["gained"] if gain_count[i] >= 3]
        md.append(f"| {n} | {len(r['lost'])} | {len(r['gained'])} | {len(only)}: {', '.join(only) or '-'} | "
                  f"{len(r['lost_shared_ge3'])} | {len(r['gained_shared_ge3'])} | "
                  f"{r['median_final_nps_on'] or 0:,} / {r['median_final_nps_off'] or 0:,} | {r['mean_final_depth_on_minus_off'] or 0:+.2f} |")
    report["lost_count_by_position"] = {i: c for i, c in lost_count.items() if c}
    report["gained_count_by_position"] = {i: c for i, c in gain_count.items() if c}
    Path(a.out_json).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    Path(a.out_md).write_text("\n".join(md + detail) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
