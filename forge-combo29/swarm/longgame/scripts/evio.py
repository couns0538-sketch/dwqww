"""Shared evidence I/O. The committed evidence is gzipped JSONL with short keys.

Key map (also in evidence/keys.json):
    g game  p ply  m bestmove  s score  n nodes  d depth  e seldepth
    h hashfull  v pv[0]  w len(pv)  t wall_ms  b bail
"""
import gzip, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(HERE, "..", "evidence")


def open_jsonl(name):
    """Open evidence/<name>.jsonl.gz (or .jsonl). `name` is given without extension."""
    for ext in (".jsonl.gz", ".jsonl"):
        path = os.path.join(EVID, name + ext)
        if os.path.exists(path):
            return gzip.open(path, "rt") if path.endswith(".gz") else open(path, encoding="utf-8")
    raise FileNotFoundError(f"no evidence file for {name!r} in {EVID}")


def load_plies(name):
    """Return {(game, ply): record} with long keys restored."""
    out = {}
    for line in open_jsonl(name):
        r = json.loads(line)
        out[(r["g"], r["p"])] = {
            "bm": r.get("m"), "score": r.get("s"), "nodes": r.get("n"),
            "depth": r.get("d"), "sd": r.get("e"), "hf": r.get("h"),
            "pv0": r.get("v"), "npv": r.get("w"), "wall_ms": r.get("t"),
            "bail": bool(r.get("b")),
        }
    return out


def load_json(name):
    return json.load(open(os.path.join(EVID, name + ".json"), encoding="utf-8"))


def is_bail(r):
    """The drawn-root bail: 0 nodes, empty pv, and a REAL move.

    A terminal root also has 0 nodes and an empty pv but returns `0000` (mate 0) because
    there are no legal moves. Conflating the two inflated the count from 89 to 185 once.
    """
    return r["bail"] and r["bm"] not in (None, "0000")


def sig(r):
    """Full answer signature used for byte-identity claims."""
    return (r["bm"], r["score"], r["nodes"], r["sd"], r["npv"])
