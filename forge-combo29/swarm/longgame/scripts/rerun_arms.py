#!/usr/bin/env python3
"""Re-run every recording arm, storing engine diagnostics this time, and compact as we go.

Why a full re-run rather than trusting the earlier files. The first compaction dropped the
`diag` field, so the committed JSONL cannot answer "did the engine refuse any FEN or illegal
move?" -- a scan of them returns zero for lack of data, not for lack of faults. The brief's
rule 2 says a null needs two proofs, and this is the second one: the path must have RUN and
stored its result. So the arms are replayed with the field preserved.

Writes short-key gzipped JSONL straight to evidence/, and a diagnostics.json counting every
`info string` the `position` command produced.
"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine
from replay import run_search, pos_cmd, rss_kb

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")
MAP = [("game", "g"), ("ply", "p"), ("bm", "m"), ("score", "s"), ("nodes", "n"),
       ("depth", "d"), ("sd", "e"), ("hf", "h"), ("pv0", "v"), ("npv", "w"), ("wall_ms", "t")]


def short(r):
    c = {}
    for long, s in MAP:
        if r.get(long) is not None:
            c[s] = r[long]
    if r.get("bail"):
        c["b"] = 1
    if r.get("diag"):
        c["i"] = " | ".join(r["diag"])
    return c


def main():
    corpus = json.load(open("evidence/games.json"))["games"]
    sample_ids = set(json.load(open("evidence/divergence_sample.json"))["games"])

    arms = [
        ("session", corpus, None, "none"),
        ("session2", corpus, None, "none"),
        ("session_rev", list(reversed(corpus)), None, "none"),
        ("uncgame", corpus, None, "game"),
        ("fresh", [g for g in corpus if g["id"] in sample_ids], "fresh", None),
        ("unc", [g for g in corpus if g["id"] in sample_ids], None, "ply_unc"),
        ("clearhash", [g for g in corpus if g["id"] in sample_ids], None, "ply_clear"),
        ("hashresend", [g for g in corpus if g["id"] in sample_ids], None, "ply_hash"),
    ]
    diag_total, scanned, per_arm = 0, 0, {}

    for name, games, mode, reset in arms:
        path = f"evidence/{name}.jsonl.gz"
        rows, glb, ndiag = 0, 0, 0
        if mode == "fresh":
            out = gzip.open(path, "wt")
            for g in games:
                for k in range(1, len(g["moves"]) + 1):
                    e = Engine(ENG); e.uci(); e.sync()
                    r = run_search(e, pos_cmd(g, k)); e.quit()
                    r.update(game=g["id"], ply=k)
                    if r["diag"]:
                        ndiag += 1
                    out.write(json.dumps(short(r)) + "\n")
                    rows += 1
            out.close()
        else:
            e = Engine(ENG); e.uci(); e.sync()
            if reset == "ply_hash":
                e.send("setoption name Hash value 32")
            out = gzip.open(path, "wt")
            rss_rows = [{"plies": 0, "rss_kb": rss_kb(e.p.pid)}]
            game_times = []
            for g in games:
                if reset == "game":
                    e.send("ucinewgame"); e.sync()
                g0 = __import__("time").time()
                for k in range(1, len(g["moves"]) + 1):
                    if reset == "ply_unc":
                        e.send("ucinewgame")
                    elif reset == "ply_clear":
                        e.send("setoption name Clear Hash")
                    elif reset == "ply_hash":
                        e.send("setoption name Hash value 32")
                    r = run_search(e, pos_cmd(g, k))
                    glb += 1
                    r.update(game=g["id"], ply=k, glb=glb)
                    if r["diag"]:
                        ndiag += 1
                    out.write(json.dumps(short(r)) + "\n")
                    rows += 1
                    if glb % 100 == 0:
                        rss_rows.append({"plies": glb, "rss_kb": rss_kb(e.p.pid)})
                game_times.append({"game": g["id"], "plies": len(g["moves"]),
                                   "wall_s": round(__import__("time").time() - g0, 3)})
            out.close()
            e.quit()
            if reset in ("none", "game"):
                json.dump({"plies": rows, "rss": rss_rows, "game_rss_end": game_times},
                          open(path.replace(".jsonl.gz", ".jsonl.meta.json"), "w"))
        per_arm[name] = {"plies": rows, "diagnostics": ndiag}
        scanned += rows
        diag_total += ndiag
        print(f"  {name:12s} plies {rows:6d}  diagnostics {ndiag}")

    json.dump({"searches_scanned": scanned, "diagnostics_total": diag_total, "per_arm": per_arm},
              open("evidence/diagnostics.json", "w"), indent=0)
    print(f"\nTOTAL searches {scanned}, diagnostics {diag_total}")


if __name__ == "__main__":
    main()
