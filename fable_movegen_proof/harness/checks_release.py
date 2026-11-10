"""checks_release.py - checks on the exact release executables over UCI (job 3, standard library only).

  pins    TAG...   13 pins: bench 11/13/16/20/22 net on and net off, startpos perft 5, kiwipete perft 4 and 5
  divide  TAG...   go perft per root move on eight positions (ten runs), every line kept
  warm    TAG...   one process, Threads 1: repeated searches, ucinewgame, Hash changes, Clear Hash, net off/on,
                   a 40-ply game line, interleaved perft; a normalised transcript
  soak    TAG...   Threads 2, 3, 4: node-limited searches, option changes, stop during go infinite
                   (stability only: multithreaded search does not establish node identity)
  summary          compares every receipt with the lock's and prints the verdict per tag and check

Each run writes out\\job3\\runs\\<check>\\<TAG>.json with the exe hashes, the options and what the engine
printed. An existing receipt is never overwritten (use --redo to set the old one aside under a time stamp).
A harness error or a timeout is recorded as such; it is never a candidate verdict.
"""
import hashlib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard3  # noqa: E402
import uci_session  # noqa: E402

OUT = r"D:\forge_jobs_20261109\fable2\out\job3"
HARNESS = "checks_release-2"
BASE_OPTIONS = ["Threads=1", "Hash=16", "OwnBook=false"]
PINS_ON = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
PINS_OFF = {11: 375354, 13: 907205, 16: 2448617, 20: 13573040, 22: 24506465}
KIWI = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
PINS_PERFT = [("startpos_perft5", None, 5, 4865609), ("kiwipete_perft4", KIWI, 4, 4085603),
              ("kiwipete_perft5", KIWI, 5, 193690690)]
# name, FEN (None = start position), depth, published total (None = no published value used)
DIVIDE = [
    ("startpos", None, 6, 119060324),
    ("kiwipete", KIWI, 5, 193690690),
    ("position3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 6, 11030083),
    ("position4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 5, 15833292),
    ("position5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 5, 89941194),
    ("position6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 5, 164075551),
    ("castle_gives_check_d5", "5k2/8/8/8/8/8/8/4K2R w K - 0 1", 5, 120330),
    ("castle_gives_check_d6", "5k2/8/8/8/8/8/8/4K2R w K - 0 1", 6, None),
    ("check_with_castling_rights_d5", "r3k2r/8/8/8/8/4R3/8/R3K2R b KQkq - 0 1", 5, 2629267),
    ("check_with_castling_rights_d6", "r3k2r/8/8/8/8/4R3/8/R3K2R b KQkq - 0 1", 6, None),
]
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
WARM_POSITIONS = [
    START,
    KIWI,
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1",
    "r3k2r/8/8/8/8/4R3/8/R3K2R b KQkq - 0 1",
    "r1b1k1nr/pP3p1p/8/2pPp3/1p2P1p1/8/P1P2PpP/R1B1K1NR w KQkq c6 0 1",
    "4k3/pp3ppp/8/8/8/8/PP3PPP/4K3 w - - 0 1",
]
GAME_LINE = ("e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5 a4b3 d7d6 c2c3 e8g8 h2h3 c6a5 b3c2 c7c5 "
             "d2d4 d8c7 b1d2 c5d4 c3d4 a5c6 d2b3 a6a5 c1e3 a5a4 b3d2 c8d7 a1c1 c7b7 d1e2 f8e8 c2d3 a8b8 d4e5 c6e5").split()
STRIP_RX = re.compile(r" (nps|time) \d+")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 3600)) + " Vienna"   # CET = UTC+1 in November


def file_hash(path, alg):
    h = hashlib.new(alg)
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def exe_of(tag):
    return os.path.join(OUT, "bin", tag, "engine.exe")


def receipt_path(check, tag):
    return os.path.join(OUT, "runs", check, tag + ".json")


def base_receipt(check, tag):
    exe = exe_of(tag)
    return {"check": check, "tag": tag, "harness": HARNESS, "exe": exe, "exe_sha256": file_hash(exe, "sha256"),
            "exe_md5": file_hash(exe, "md5"), "placement": pinguard3.ensure(), "started": now(), "status": "RUNNING"}


def save(check, tag, data, redo):
    path = receipt_path(check, tag)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        if not redo:
            raise SystemExit(f"refusing: {path} exists (use --redo to set it aside)")
        os.replace(path, path[:-5] + time.strftime(".old_%H%M%S.json"))
    data["finished"] = now()
    with open(path, "w", encoding="ascii", newline="\n") as f:
        json.dump(data, f, indent=1)
    return path


def log_path(check, tag, part=""):
    d = os.path.join(OUT, "runs", check)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{tag}{part}.uci.log")


# ---------------------------------------------------------------- pins
def run_pins(tag):
    r = base_receipt("pins", tag)
    r["options"] = {"net_on": BASE_OPTIONS + ["UseNNUE=true"], "net_off": BASE_OPTIONS + ["UseNNUE=false"], "perft": BASE_OPTIONS}
    r["bench"], r["perft"] = {}, {}
    ok = True
    for net, expect in (("on", PINS_ON), ("off", PINS_OFF)):
        eng = uci_session.Engine([exe_of(tag)], log_path("pins", tag, "_net" + net))
        r["child"] = eng.pin
        eng.handshake(r["options"]["net_" + net])
        for depth, want in expect.items():
            nodes = eng.bench(depth, timeout=7200)
            r["bench"][f"net_{net}_d{depth}"] = {"nodes": nodes, "want": want, "match": nodes == want}
            ok = ok and nodes == want
        r[f"exit_net_{net}"] = eng.close()
    eng = uci_session.Engine([exe_of(tag)], log_path("pins", tag, "_perft"))
    eng.handshake(r["options"]["perft"])
    for name, fen, depth, want in PINS_PERFT:
        eng.position(fen)
        _, total, other = eng.perft(depth, timeout=7200)
        r["perft"][name] = {"nodes": total, "want": want, "match": total == want, "other_lines": other}
        ok = ok and total == want and not other
    r["exit_perft"] = eng.close()
    n = sum(1 for v in list(r["bench"].values()) + list(r["perft"].values()) if v["match"])
    r["matches"] = f"{n}/13"
    r["status"] = "MATCH" if ok and n == 13 else "MISMATCH"
    return r


# ---------------------------------------------------------------- perft divide
def run_divide(tag):
    r = base_receipt("divide", tag)
    r["options"] = BASE_OPTIONS
    r["positions"] = []
    eng = uci_session.Engine([exe_of(tag)], log_path("divide", tag))
    r["child"] = eng.pin
    eng.handshake(BASE_OPTIONS)
    for name, fen, depth, published in DIVIDE:
        eng.position(fen)
        moves, total, other = eng.perft(depth, timeout=7200)
        r["positions"].append({"name": name, "fen": fen or START, "depth": depth, "total": total, "published": published,
                               "published_match": None if published is None else total == published,
                               "divide": moves, "other_lines": other})
    r["exit"] = eng.close()
    r["status"] = "DONE"
    return r


# ---------------------------------------------------------------- warm transcript
def run_warm(tag):
    r = base_receipt("warm", tag)
    r["options"] = BASE_OPTIONS + ["UseNNUE=true"]
    t = []
    eng = uci_session.Engine([exe_of(tag)], log_path("warm", tag))
    r["child"] = eng.pin
    eng.handshake(r["options"])

    def step(text):
        t.append("# " + text)

    def opt(name, value=None):
        step(f"setoption {name}" + ("" if value is None else f" = {value}"))
        eng.send(f"setoption name {name}" + ("" if value is None else f" value {value}"))
        eng.isready()

    def search(fen, depth, moves=None):
        eng.position(fen, moves)
        info, best = eng.go(f"depth {depth}", timeout=3600)
        t.append("position " + (fen or "startpos") + (" moves " + " ".join(moves) if moves else ""))
        for ln in info:
            t.append(STRIP_RX.sub("", ln))
        t.append(best)

    step("phase 1: twelve positions, cold table, depth 16")
    eng.send("ucinewgame")
    for fen in WARM_POSITIONS:
        search(fen, 16)
    step("phase 2: the same twelve again, warm table and caches")
    for fen in WARM_POSITIONS:
        search(fen, 16)
    step("phase 3: after ucinewgame")
    eng.send("ucinewgame")
    eng.isready()
    for fen in WARM_POSITIONS[:4]:
        search(fen, 17)
    step("phase 4: Hash 1, then 64, then 16, no ucinewgame")
    opt("Hash", 1)
    for fen in WARM_POSITIONS[:6]:
        search(fen, 16)
    opt("Hash", 64)
    for fen in WARM_POSITIONS[:6]:
        search(fen, 16)
    opt("Hash", 16)
    step("phase 5: net off, then on")
    opt("UseNNUE", "false")
    for fen in WARM_POSITIONS[:8]:
        search(fen, 16)
    for fen in WARM_POSITIONS[:4]:
        search(fen, 16)
    opt("UseNNUE", "true")
    for fen in WARM_POSITIONS[:4]:
        search(fen, 16)
    step("phase 6: Clear Hash, searches with a perft between them")
    opt("Clear Hash")
    for fen in WARM_POSITIONS[4:8]:
        search(fen, 16)
        eng.position(fen)
        moves, total, _ = eng.perft(3, timeout=3600)
        t.append(f"perft3 {total} " + " ".join(f"{m}:{c}" for m, c in moves))
    step("phase 7: a 40-ply game line, one search per ply, tables kept")
    for k in range(len(GAME_LINE) + 1):
        search(None, 12, GAME_LINE[:k])
    step("phase 8: bench 13 at the end must still be the pin")
    b13 = eng.bench(13, timeout=3600)
    t.append(f"bench13 {b13}")
    r["exit"] = eng.close()
    r["bench13"] = b13
    r["bench13_is_pin"] = b13 == PINS_ON[13]
    r["illegal_or_invalid_lines"] = [ln for ln in t if "illegal" in ln or "invalid" in ln]
    text = "\n".join(t) + "\n"
    tpath = os.path.join(OUT, "runs", "warm", tag + ".transcript.txt")
    with open(tpath, "w", encoding="ascii", newline="\n") as f:
        f.write(text)
    r["transcript"] = tpath
    r["transcript_sha256"] = hashlib.sha256(text.encode("ascii")).hexdigest()
    r["transcript_lines"] = len(t)
    r["searches"] = sum(1 for ln in t if ln.startswith("bestmove"))
    r["status"] = "DONE"
    return r


# ---------------------------------------------------------------- Threads soak
def run_soak(tag):
    r = base_receipt("soak", tag)
    r["options"] = ["OwnBook=false", "UseNNUE=true", "Threads=2|3|4 per block", "go nodes 1000000"]
    # the legal moves of each soak position, from the lock exe at Threads 1
    ref = uci_session.Engine([exe_of("LOCK")])
    ref.handshake(BASE_OPTIONS)
    legal = []
    for fen in WARM_POSITIONS:
        ref.position(fen)
        moves, _, _ = ref.perft(1, timeout=600)
        legal.append([m for m, _ in moves])
    ref.close()
    eng = uci_session.Engine([exe_of(tag)], log_path("soak", tag))
    r["child"] = eng.pin
    eng.handshake(["OwnBook=false", "UseNNUE=true"])
    searches, ok = [], True
    for threads in (2, 3, 4, 3, 2, 4):
        eng.send(f"setoption name Threads value {threads}")
        eng.send(f"setoption name Hash value {16 * threads}")
        eng.isready()
        for i, fen in enumerate(WARM_POSITIONS):
            eng.position(fen)
            t0 = time.time()
            _, best = eng.go("nodes 1000000", timeout=1800)
            mv = best.split()[1]
            good = mv in legal[i] or (mv == "0000" and not legal[i])
            ok = ok and good
            searches.append({"threads": threads, "position": i, "bestmove": mv, "legal": good, "seconds": round(time.time() - t0, 2)})
        # stop during an infinite search
        eng.position(WARM_POSITIONS[1])
        eng.send("go infinite")
        time.sleep(0.4)
        eng.send("stop")
        best = eng.read_until(lambda s: s.startswith("bestmove"), 600, "bestmove after stop")[-1]
        mv = best.split()[1]
        good = mv in legal[1]
        ok = ok and good
        searches.append({"threads": threads, "position": "infinite+stop", "bestmove": mv, "legal": good})
        eng.send("ucinewgame")
        eng.send("setoption name Clear Hash")
        eng.isready()
    eng.send("setoption name Threads value 1")
    eng.send("setoption name Hash value 16")
    eng.isready()
    r["bench13_after"] = eng.bench(13, timeout=3600)
    r["exit"] = eng.close()
    r["searches"] = searches
    r["all_bestmoves_legal"] = ok
    r["status"] = "STABLE" if ok and r["exit"] == 0 and r["bench13_after"] == PINS_ON[13] else "UNSTABLE"
    r["note"] = "stability only: multithreaded search is not deterministic, so this run says nothing about node identity"
    return r


RUNNERS = {"pins": run_pins, "divide": run_divide, "warm": run_warm, "soak": run_soak}


def run(check, tags, redo):
    code = 0
    for tag in tags:
        if os.path.exists(receipt_path(check, tag)) and not redo:
            print(f"{check} {tag}: receipt exists, skipped (not run again, not counted twice)", flush=True)
            continue
        t0 = time.time()
        try:
            r = RUNNERS[check](tag)
        except (uci_session.EngineError, OSError) as e:
            r = base_receipt(check, tag)
            r["status"] = "HARNESS_ERROR"
            r["error"] = f"{type(e).__name__}: {e}"
            code = 2
        r["wall_seconds"] = round(time.time() - t0, 1)
        path = save(check, tag, r, redo)
        extra = r.get("matches") or r.get("transcript_sha256", "")[:16] or ""
        print(f"{check} {tag}: {r['status']} {extra} ({r['wall_seconds']} s) -> {path}", flush=True)
    return code


def load(check, tag):
    p = receipt_path(check, tag)
    return json.load(open(p, "r", encoding="ascii")) if os.path.exists(p) else None


def summary(tags):
    out = {"written": now(), "harness": HARNESS, "tags": {}}
    lock = {c: load(c, "LOCK") for c in RUNNERS}
    for tag in tags:
        row = {}
        # pins
        p = load("pins", tag)
        if p is None:
            row["pins"] = "NOT RUN"
        elif p["status"] == "HARNESS_ERROR":
            row["pins"] = "HARNESS_ERROR: " + p.get("error", "")
        else:
            bad = [k for k, v in list(p["bench"].items()) + list(p["perft"].items()) if not v["match"]]
            row["pins"] = f"MATCH {p['matches']}" if not bad else f"MISMATCH {p['matches']}: " + ", ".join(
                f"{k} expected {(p['bench'].get(k) or p['perft'].get(k))['want']} got {(p['bench'].get(k) or p['perft'].get(k))['nodes']}" for k in bad)
        # divide
        d, ld = load("divide", tag), lock["divide"]
        if d is None or ld is None:
            row["divide"] = "NOT RUN"
        elif d["status"] != "DONE" or ld["status"] != "DONE":
            row["divide"] = "HARNESS_ERROR"
        else:
            diffs = []
            for a, b in zip(ld["positions"], d["positions"]):
                if a["divide"] != b["divide"] or a["total"] != b["total"] or b["other_lines"]:
                    k = next((i for i, (x, y) in enumerate(zip(a["divide"], b["divide"])) if x != y), None)
                    diffs.append(f"{a['name']} d{a['depth']}: total {a['total']} vs {b['total']}"
                                 + (f", first differing line {a['divide'][k]} vs {b['divide'][k]}" if k is not None else ""))
            pub = [f"{b['name']}: {b['total']} != published {b['published']}" for b in d["positions"] if b["published_match"] is False]
            row["divide"] = (f"MATCH {len(d['positions'])}/{len(ld['positions'])} positions, every root move"
                             if not diffs and not pub else "MISMATCH: " + "; ".join(diffs + pub))
        # warm
        w, lw = load("warm", tag), lock["warm"]
        if w is None or lw is None:
            row["warm"] = "NOT RUN"
        elif w["status"] != "DONE" or lw["status"] != "DONE":
            row["warm"] = "HARNESS_ERROR"
        elif w["transcript_sha256"] == lw["transcript_sha256"] and w["bench13_is_pin"]:
            row["warm"] = f"MATCH {w['searches']} searches, {w['transcript_lines']} lines, bench13 pin kept"
        else:
            a = open(lw["transcript"], "r", encoding="ascii").read().splitlines()
            b = open(w["transcript"], "r", encoding="ascii").read().splitlines()
            k = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            step = next((a[j] for j in range(min(k, len(a) - 1), -1, -1) if a[j].startswith("# ")), "")
            pos = next((a[j] for j in range(min(k, len(a) - 1), -1, -1) if a[j].startswith("position ")), "")
            row["warm"] = (f"MISMATCH at transcript line {k + 1} ({step}; {pos}): expected [{a[k] if k < len(a) else 'END'}] "
                           f"got [{b[k] if k < len(b) else 'END'}]; bench13 {w['bench13']}")
        # soak
        s = load("soak", tag)
        row["soak"] = "NOT RUN" if s is None else (s["status"] + (f" {len(s['searches'])} searches, exit {s['exit']}, bench13 after {s['bench13_after']}"
                                                                 if s["status"] in ("STABLE", "UNSTABLE") else ": " + s.get("error", "")))
        out["tags"][tag] = row
        print(f"{tag:8} pins: {row['pins']}\n         divide: {row['divide']}\n         warm: {row['warm']}\n         soak: {row['soak']}", flush=True)
    path = os.path.join(OUT, "runs", "RELEASE_SUMMARY.json")
    with open(path, "w", encoding="ascii", newline="\n") as f:
        json.dump(out, f, indent=1)
    print("summary written to " + path)
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] not in list(RUNNERS) + ["summary"]:
        print(__doc__)
        return 1
    redo = "--redo" in argv
    tags = [a for a in argv[2:] if not a.startswith("--")]
    print(pinguard3.ensure(), flush=True)
    if argv[1] == "summary":
        return summary(tags or ["LOCK", "LOCKCOPY", "LOCKEQ", "EVL", "PCM", "CKL", "WNP", "KPC", "BUN"])
    return run(argv[1], tags, redo)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
