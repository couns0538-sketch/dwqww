#!/usr/bin/env python3
"""Build tests/syzygy_fixtures.tsv: known Syzygy answers for the C1 tests.

Positions: random legal positions per material (generated reproducibly by
`forge_syzygy_tests gen <material> <count> <seed> [ep]`), plus hand-written
special cases (mate, stalemate, en passant as the only legal move, castling
rights, 50-move counter boundaries).
Answers: the public lichess tablebase API (https://tablebase.lichess.ovh),
queried politely: one request at a time, at least 1 s apart, cached in
api_cache.jsonl.gz next to this script so a re-run asks nothing twice.

usage: make_fixture.py <forge_syzygy_tests binary> <out.tsv> <tablebase dir> [--offline]
"""
import gzip
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "api_cache.jsonl.gz")
API = "https://tablebase.lichess.ovh/standard?fen="
USER_AGENT = "forge-chess-engine-c1-tests (one request per second; contact via github couns0538-sketch/dwqww)"

# (material, count, seed, ep)
MATERIALS = [
    # 3 pieces
    ("KPvK", 16, 101, False), ("KQvK", 8, 102, False), ("KRvK", 8, 103, False),
    ("KBvK", 2, 104, False), ("KNvK", 2, 105, False),
    # 4 pieces
    ("KBNvK", 16, 201, False), ("KQvKR", 16, 202, False), ("KBBvK", 6, 203, False),
    ("KNNvK", 6, 204, False), ("KQQvK", 4, 205, False), ("KRRvK", 4, 206, False),
    ("KQvKQ", 8, 207, False), ("KRvKR", 6, 208, False), ("KPvKP", 16, 209, False),
    ("KPPvK", 8, 210, False), ("KRvKB", 6, 211, False), ("KRvKN", 6, 212, False),
    ("KQvKB", 4, 213, False), ("KQvKN", 4, 214, False), ("KQvKP", 8, 215, False),
    ("KRvKP", 8, 216, False), ("KBvKP", 4, 217, False), ("KNvKP", 4, 218, False),
    ("KBvKB", 2, 219, False), ("KNvKN", 2, 220, False), ("KBvKN", 2, 221, False),
    ("KRPvK", 4, 222, False), ("KQPvK", 2, 223, False), ("KBPvK", 4, 224, False),
    ("KNPvK", 4, 225, False),
    # 5 pieces
    ("KRPvKR", 24, 301, False), ("KQPvKQ", 8, 302, False), ("KBPvKB", 6, 303, False),
    ("KPPvKP", 10, 304, False), ("KRvKPP", 4, 305, False), ("KQRvKQ", 4, 306, False),
    ("KRBvKR", 4, 307, False), ("KRNvKR", 4, 308, False), ("KBBvKN", 3, 309, False),
    ("KBBBvK", 3, 310, False), ("KNNNvK", 2, 311, False), ("KQQvKQ", 3, 312, False),
    ("KPPPvK", 3, 313, False), ("KRPPvK", 3, 314, False), ("KBPvKN", 3, 315, False),
    ("KNPvKB", 3, 316, False), ("KQvKBN", 3, 317, False), ("KRRvKQ", 3, 318, False),
    ("KRPvKP", 4, 319, False),
    # en passant available
    ("KPvKP", 10, 401, True), ("KPPvKP", 6, 402, True), ("KRPvKP", 4, 403, True),
    ("KBPvKP", 3, 404, True), ("KQPvKP", 3, 405, True),
]

SPECIAL = [
    ("k7/1Q6/1K6/8/8/8/8/8 b - - 0 1", "mated KQvK"),
    ("R3k3/8/4K3/8/8/8/8/8 b - - 0 1", "mated KRvK"),
    ("k7/8/1Q6/8/8/8/8/1K6 b - - 0 1", "stalemate KQvK"),
    ("k7/P7/K7/8/8/8/8/8 b - - 0 1", "stalemate KPvK"),
    ("8/8/8/8/3pP3/1Q1K4/8/k7 b - e3 0 1", "ep is the only legal move KQPvKP"),
    ("8/8/8/8/8/8/8/K1k5 w - - 0 1", "bare kings"),
    ("K7/N7/k7/8/3p4/8/N7/8 w - - 0 1", "cursed win KNNvKP"),
    ("4k3/8/8/8/8/8/8/4K2R w K - 0 1", "castling rights KRvK"),
    ("r3k3/8/8/8/8/8/8/4K3 b q - 0 1", "castling rights KvKR"),
    ("4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1", "castling rights KRRvK"),
    ("r3k2r/8/8/8/8/8/8/4K3 w kq - 0 1", "castling rights KvKRR"),
    ("4k3/8/8/8/8/8/8/4K2R w - - 0 1", "KRvK reference dtz 21"),
    ("4k3/8/8/8/8/8/8/4K2R w - - 75 60", "rule50 KRvK hm75 win"),
    ("4k3/8/8/8/8/8/8/4K2R w - - 79 60", "rule50 KRvK hm79 boundary"),
    ("4k3/8/8/8/8/8/8/4K2R w - - 80 60", "rule50 KRvK hm80 boundary"),
    ("4k3/8/8/8/8/8/8/4K2Q b - - 84 60", "rule50 KQvK hm84 loss"),
    ("4k3/8/8/8/8/8/8/4K2Q b - - 85 60", "rule50 KQvK hm85 blessed"),
]

PIECE_ORDER = "QRBNP"


def material_of(fen):
    placement, side = fen.split()[0], fen.split()[1]
    white = "".join(c for c in placement if c.isupper())
    black = "".join(c.upper() for c in placement if c.islower())

    def name(s):
        return "K" + "".join(sorted(s.replace("K", ""), key=PIECE_ORDER.index))

    return name(white), name(black)


TB_DIR = None


def table_name(a, b):
    """The Syzygy file name of a material, as present in the local tablebase folder."""
    for name in (a + "v" + b, b + "v" + a):
        if os.path.exists(os.path.join(TB_DIR, name + ".rtbw")):
            return name
    raise SystemExit("no table for %sv%s in %s" % (a, b, TB_DIR))


def needs(fen):
    """Tables a full check of this row needs beyond the 3-4 piece set."""
    w, b = material_of(fen)
    out = set()
    if len(w) + len(b) == 5:
        out.add(table_name(w, b))
        # promotions explored by the DTZ / root move checks
        for side, other in ((w, b), (b, w)):
            if "P" in side:
                for promo in "QRBN":
                    s = side.replace("P", "", 1) + promo
                    s = "K" + "".join(sorted(s[1:], key=PIECE_ORDER.index))
                    out.add(table_name(s, other) if side is w else table_name(other, s))
    return sorted(out)


def load_cache():
    cache = {}
    if os.path.exists(CACHE):
        with gzip.open(CACHE, "rt", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    cache[d["fen"]] = d["response"]
    return cache


_last = [0.0]


def query(fen, cache, offline):
    if fen in cache:
        return cache[fen]
    if offline:
        raise SystemExit("not cached (offline): " + fen)
    for attempt in range(6):
        wait = 1.0 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(API + urllib.parse.quote(fen), headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(30 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            time.sleep(10 * (attempt + 1))
    else:
        raise SystemExit("API failed for " + fen)
    cache[fen] = data
    with gzip.open(CACHE, "at", encoding="utf-8") as f:
        f.write(json.dumps({"fen": fen, "response": data}, sort_keys=True) + "\n")
    return data


def moves_field(data):
    toks = []
    for m in data.get("moves", []):
        dtz = "-" if m.get("dtz") is None else str(m["dtz"])
        toks.append("%s,%d,%d,%s,%s" % (m["uci"], 1 if m.get("zeroing") else 0, 1 if m.get("checkmate") else 0,
                                         m.get("category", "unknown"), dtz))
    return " ".join(toks) if toks else "-"


def main():
    global TB_DIR
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    binary, out_path, TB_DIR = sys.argv[1], sys.argv[2], sys.argv[3]
    offline = "--offline" in sys.argv
    cache = load_cache()
    positions = []  # (fen, note)
    for material, count, seed, ep in MATERIALS:
        args = [binary, "gen", material, str(count), str(seed)] + (["ep"] if ep else [])
        fens = subprocess.run(args, capture_output=True, text=True, check=True).stdout.split("\n")
        for fen in fens:
            if fen.strip():
                positions.append((fen.strip(), ("ep " if ep else "") + material))
    positions += SPECIAL
    rows = []
    seen = set()
    for fen, note in positions:
        if fen in seen:
            continue
        seen.add(fen)
        rows.append((fen, note, query(fen, cache, offline)))
    # 50-move counter boundaries: |dtz| + counter = 100 (still decisive) and 101 (cursed / blessed).
    boundary = []
    for fen, note, data in rows:
        if len(boundary) >= 40:
            break
        if data.get("category") in ("win", "loss") and data.get("dtz") is not None and fen.split()[4] == "0" \
                and " - - " in fen and 2 <= abs(data["dtz"]) <= 99:
            d = abs(data["dtz"])
            for hm in (100 - d, 101 - d):
                parts = fen.split()
                parts[4], parts[5] = str(hm), "80"
                boundary.append((" ".join(parts), "rule50 boundary " + note + (" precise" if data.get("precise_dtz") is not None else " rounded")))
    for fen, note in boundary:
        if fen not in seen:
            seen.add(fen)
            rows.append((fen, note, query(fen, cache, offline)))
    # Boundary rows from positions whose DTZ is exact in these files (the engine prober's own
    # rounding flag, `forge_syzygy_tests probe`) and equal to the API's: decided at |dtz| + counter
    # = 100 and 101 for wins and for losses.
    base = [fen for fen, note, data in rows if fen.split()[4] == "0"]
    out = subprocess.run([binary, "probe", TB_DIR], input="\n".join(base) + "\n", capture_output=True, text=True,
                         check=True).stdout
    exact = {}
    for line in out.splitlines():
        f = line.split("\t")
        if len(f) == 4 and f[3] == "0":
            exact[f[0]] = int(f[2])
    exact_boundary = []
    taken = {1: 0, -1: 0}
    for fen, note, data in list(rows):
        d = exact.get(fen)
        if d is None or " - - " not in fen or data.get("dtz") != d or not 2 <= abs(d) <= 99:
            continue
        sign = 1 if d > 0 else -1
        if taken[sign] >= 8:
            continue
        taken[sign] += 1
        for hm in (100 - abs(d), 101 - abs(d)):
            parts = fen.split()
            parts[4], parts[5] = str(hm), "80"
            exact_boundary.append((" ".join(parts), "rule50 exact-dtz boundary " + note))
    for fen, note in exact_boundary:
        if fen not in seen:
            seen.add(fen)
            rows.append((fen, note, query(fen, cache, offline)))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Syzygy known answers for tests/syzygy_tests.cpp, from the public lichess tablebase API\n")
        f.write("# (https://tablebase.lichess.ovh/standard), built by opus_round1/C1/make_fixture.py.\n")
        f.write("# fen\tcategory (with the FEN's 50-move counter)\tdtz\tprecise\troot moves (uci,zeroing,mate,category,dtz)\tnote [needs: 5-piece tables]\n")
        for fen, note, data in rows:
            dtz = "-" if data.get("dtz") is None else str(data["dtz"])
            precise = "1" if data.get("precise_dtz") is not None else "0"
            moves = moves_field(data) if fen.split()[4] == "0" else "-"
            need = needs(fen)
            note_full = note + (" needs: " + " ".join(need) if need else "")
            f.write("\t".join([fen, data.get("category", "unknown"), dtz, precise, moves, note_full]) + "\n")
    cats = {}
    for _, _, d in rows:
        cats[d.get("category")] = cats.get(d.get("category"), 0) + 1
    print("rows", len(rows), "categories", cats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
