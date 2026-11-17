"""Score-vs-depth ladders and a mate-distance sanity scan (measure 5 and 2).

Two things this is built to catch, because both are visible on the wire:

1. A fail-high / fail-low ARTEFACT in the score ladder: a score that jumps and
   comes back as depth rises. A bound published as a value looks exactly like
   that, so every rung is compared against the never-narrow reference.

2. A mate distance the search could not have earned. `score mate N` is 2N-1
   plies, so if a reported mate distance exceeds the deepest ply the search
   actually reached (`seldepth`), the score claims more than the tree contains.
   `seldepth` is the engine's own number, so this is checkable without trusting
   the mating line.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import asp_paths  # noqa: E402
from uci import Engine  # noqa: E402

EVIDENCE = asp_paths.EVIDENCE
BUILDS = {name: str(asp_paths.binary(name)) for name in asp_paths.BUILD_FLAGS}
BASE = {"OwnBook": "false"}


def ladder(build, opts, fen, max_depth):
    """One row per depth, as the engine printed it."""
    merged = dict(BASE)
    merged.update(opts or {})
    with Engine(BUILDS[build], merged) as eng:
        eng.newgame()
        eng.position(fen)
        res = eng.search(f"go depth {max_depth}", collect_trace=(build == "trace"))
    rows = {}
    for r in res["info"]:
        if r["depth"] is not None:
            rows[r["depth"]] = r
    traces = {t.get("depth"): t for t in res["traces"]}
    out = []
    for d in sorted(rows):
        r = rows[d]
        t = traces.get(d)
        out.append({
            "depth": d,
            "score_kind": r["score_kind"],
            "score": r["score"],
            "mate_plies": (2 * r["score"] - 1) if r["is_mate"] and r["score"] > 0
                          else None,
            "seldepth": r["seldepth"],
            "nodes": r["nodes"],
            "pv_len": len(r["pv"]),
            "pv": r["pv"],
            "bestmove": r["pv"][0] if r["pv"] else None,
            "trace_inside": t.get("inside") if t else None,
            "trace_exit": t.get("exit") if t else None,
            "trace_tries": t.get("tries") if t else None,
        })
    return {"rows": out, "bestmove": res["bestmove"]}


def main():
    corpus = json.loads((EVIDENCE / "corpus.json").read_text())
    # The 4 positions where the arms disagreed, plus a spread of ordinary ones.
    probe = [
        ("KQK-dtm7-a", "8/8/8/5KQ1/8/5k2/8/8 w - - 0 1", 7),
        ("KQK-dtm7-b", "8/8/8/3K4/6Q1/8/8/4k3 w - - 0 1", 7),
        ("KQK-dtm5-a", "6Q1/8/8/k7/8/2K5/8/8 w - - 0 1", 5),
        ("KQK-dtm5-b", "8/3K4/8/k7/8/8/8/2Q5 w - - 0 1", 5),
        ("KQK-dtm3-a", "8/8/8/8/7Q/5K2/8/6k1 w - - 0 1", 3),
        ("KQK-dtm3-b", "8/Q7/7k/4K3/8/8/8/8 w - - 0 1", 3),
    ]
    for pos in corpus["depth_positions"][:10]:
        probe.append((pos["label"], pos["fen"], None))

    arms = [
        ("asp_default", "trace", {}),
        ("asp_off", "noasp", {}),
        ("delta200", "trace", {"AspirationDelta": 200}),
        ("capped_reopen", "trace", {"AspCappedReopen": "true"}),
        ("arm_late", "trace", {"AspArmLate": "true"}),
        ("both_switches", "trace", {"AspCappedReopen": "true", "AspArmLate": "true"}),
    ]

    payload = {"positions": [], "arms": [a[0] for a in arms]}
    over_claims = []
    for label, fen, dtm in probe:
        entry = {"label": label, "fen": fen, "dtm_plies": dtm, "arms": {}}
        for arm, build, opts in arms:
            lad = ladder(build, opts, fen, 16)
            entry["arms"][arm] = lad
            for r in lad["rows"]:
                if r["mate_plies"] is not None and r["seldepth"] is not None \
                        and r["mate_plies"] > r["seldepth"]:
                    over_claims.append({
                        "label": label, "arm": arm, "depth": r["depth"],
                        "mate_plies": r["mate_plies"], "seldepth": r["seldepth"],
                        "excess": r["mate_plies"] - r["seldepth"],
                        "trace_inside": r["trace_inside"],
                        "trace_exit": r["trace_exit"],
                    })
        payload["positions"].append(entry)

    (EVIDENCE / "score_ladders.json").write_text(json.dumps(payload, indent=2) + "\n")

    print("=== score ladders: mate distance vs seldepth ===")
    for entry in payload["positions"]:
        print(f"\n{entry['label']}  dtm={entry['dtm_plies']}  {entry['fen']}")
        for arm in ("asp_default", "asp_off", "delta200", "capped_reopen"):
            lad = entry["arms"][arm]
            cells = []
            for r in lad["rows"]:
                if r["score_kind"] == "mate":
                    cells.append(f"d{r['depth']}:M{r['score']}(sd{r['seldepth']})")
                else:
                    cells.append(f"d{r['depth']}:{r['score']}")
            print(f"  {arm:14s} {' '.join(cells)}")

    print(f"\n=== mate distances exceeding the tree the search reached ===")
    if not over_claims:
        print("none")
    for c in over_claims:
        print(f"  {c['label']:14s} {c['arm']:14s} d{c['depth']:<2} "
              f"mate_plies={c['mate_plies']} seldepth={c['seldepth']} "
              f"excess={c['excess']} inside={c['trace_inside']} exit={c['trace_exit']}")
    (EVIDENCE / "mate_overclaims.json").write_text(json.dumps(over_claims, indent=2) + "\n")


if __name__ == "__main__":
    main()
