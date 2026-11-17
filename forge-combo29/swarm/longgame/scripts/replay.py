#!/usr/bin/env python3
"""Long-game replay: in-process vs fresh-process answers over real games, ply by ply.

Arms (all `go depth 8`):
  session   ONE process replays every game back to back; no reset between plies or games.
            This is the shape of a GUI/analysis tool that opens a process and plays on.
  fresh     a NEW process per ply (state ground truth).
  unc       session arm with `ucinewgame` between plies (table + histories + eval cache cold).
  clearhash session arm with `Clear Hash` between plies (cold table + cold pawn cache, WARM histories).
  hashresend session arm re-sending `setoption name Hash value 32` between plies
            (cold table, warm histories, warm pawn cache) -- the fourth TT state.

A bail is recorded when the reply has 0 nodes and an empty pv (the drawn-root path).
Every bail gets a fresh-process re-check and a `go perft 1` head check, whichever game it is in.
"""
import sys, os, json, time, argparse, subprocess, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci import Engine, parse_info_lines

ENG = os.environ.get("FORGE_BIN", "forge-combo29/build/forge")
GO = "go depth 8"


def rss_kb(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except OSError:
        return None
    return None


def run_search(eng, pos_cmd, go=GO, timeout=900.0):
    """Send position + go, read to bestmove. Returns a per-ply record."""
    t0 = time.time()
    eng.send(pos_cmd)
    eng.send(go)
    lines = eng.read_until(lambda l: l.startswith("bestmove"), timeout=timeout)
    wall_ms = (time.time() - t0) * 1000.0
    diag = [l for l in lines if l.startswith("info string")]
    best = lines[-1].split()
    bm = best[1] if len(best) > 1 else None
    infos = parse_info_lines([l for l in lines if l.startswith("info depth")])
    last = infos[-1] if infos else None
    nodes = last["nodes"] if last else None
    pv = last["pv"] if last else []
    return {
        "bm": bm,
        "score": last["score"] if last else None,
        "nodes": nodes,
        "depth": last["depth"] if last else None,
        "sd": last["seldepth"] if last else None,
        "hf": last["hashfull"] if last else None,
        "pv0": pv[0] if pv else None,
        "npv": len(pv),
        "ninfo": len(infos),
        "wall_ms": round(wall_ms, 2),
        "diag": diag,
        "bail": (nodes == 0 and len(pv) == 0 and bm is not None),
    }


def pos_cmd(game, prefix_len):
    mv = " ".join(game["moves"][:prefix_len])
    return f"position fen {game['start_fen']} moves {mv}" if mv else f"position fen {game['start_fen']}"


def perft_head(eng, pos):
    """Head of the generated move list, via `go perft 1` in a fresh process."""
    eng.send(pos)
    eng.send("go perft 1")
    lines = eng.read_until(lambda l: l.startswith("nodes "))
    heads = [l.split(":")[0].strip() for l in lines if ":" in l and not l.startswith("info")]
    return heads[0] if heads else None


def do_session(games, out_path, rss_every=100):
    """One process, all games, no resets. Writes JSONL per ply."""
    eng = Engine(ENG)
    eng.uci(); eng.sync()
    pid = eng.p.pid
    f = open(out_path, "w")
    glb = 0
    rss_rows = [{"plies": 0, "rss_kb": rss_kb(pid)}]
    game_times = []
    for gi, g in enumerate(games):
        g0 = time.time()
        n = len(g["moves"])
        for k in range(1, n + 1):
            rec = run_search(eng, pos_cmd(g, k))
            glb += 1
            rec.update(game=g["id"], ply=k, glb=glb)
            f.write(json.dumps(rec) + "\n")
            if glb % rss_every == 0:
                rss_rows.append({"plies": glb, "rss_kb": rss_kb(pid)})
        game_times.append({"game": g["id"], "plies": n, "wall_s": round(time.time() - g0, 3),
                           "rss_kb": rss_kb(pid)})
        f.flush()
    rss_rows.append({"plies": glb, "rss_kb": rss_kb(pid)})
    f.close()
    eng.quit()
    return {"plies": glb, "rss": rss_rows, "game_rss_end": game_times}


def do_reset_arm(games, out_path, mode):
    """One process for the whole arm; a reset of the named kind before each ply."""
    eng = Engine(ENG)
    eng.uci(); eng.sync()
    if mode == "hashresend":
        eng.send("setoption name Hash value 32")
    f = open(out_path, "w")
    glb = 0
    for g in games:
        for k in range(1, len(g["moves"]) + 1):
            if mode == "unc":
                eng.send("ucinewgame")
            elif mode == "clearhash":
                eng.send("setoption name Clear Hash")
            elif mode == "hashresend":
                eng.send("setoption name Hash value 32")
            rec = run_search(eng, pos_cmd(g, k))
            glb += 1
            rec.update(game=g["id"], ply=k, glb=glb)
            f.write(json.dumps(rec) + "\n")
        f.flush()
    f.close()
    eng.quit()
    return {"plies": glb}


def do_uncgame(games, out_path):
    """The realistic GUI shape: ONE process, `ucinewgame` between games, NOT between plies.
    A GUI replaying a game move by move looks exactly like this."""
    eng = Engine(ENG)
    eng.uci(); eng.sync()
    pid = eng.p.pid
    f = open(out_path, "w")
    glb = 0
    rss_rows = [{"plies": 0, "rss_kb": rss_kb(pid)}]
    for g in games:
        eng.send("ucinewgame"); eng.sync()
        for k in range(1, len(g["moves"]) + 1):
            rec = run_search(eng, pos_cmd(g, k))
            glb += 1
            rec.update(game=g["id"], ply=k, glb=glb)
            f.write(json.dumps(rec) + "\n")
            if glb % 100 == 0:
                rss_rows.append({"plies": glb, "rss_kb": rss_kb(pid)})
        f.flush()
    f.close()
    eng.quit()
    return {"plies": glb, "rss": rss_rows}


def do_fresh(games, out_path):
    """New process per ply. The state-free ground truth."""
    f = open(out_path, "w")
    glb = 0
    for g in games:
        for k in range(1, len(g["moves"]) + 1):
            eng = Engine(ENG)
            eng.uci(); eng.sync()
            rec = run_search(eng, pos_cmd(g, k))
            eng.quit()
            glb += 1
            rec.update(game=g["id"], ply=k, glb=glb)
            f.write(json.dumps(rec) + "\n")
        f.flush()
    f.close()
    return {"plies": glb}


def load_jsonl(path):
    out = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            out[(r["game"], r["ply"])] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arm", choices=["session", "session_rev", "fresh", "unc", "uncgame", "clearhash",
                                    "hashresend", "bailcheck"])
    ap.add_argument("--games", default="evidence/games.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", default="evidence/divergence_sample.json")
    ap.add_argument("--bails", default="evidence/session.jsonl")
    args = ap.parse_args()

    corpus = json.load(open(args.games))["games"]
    if args.arm in ("session",):
        meta = do_session(corpus, args.out)
        json.dump(meta, open(args.out + ".meta.json", "w"))
        print("session plies:", meta["plies"])
    elif args.arm == "fresh":
        ids = set(json.load(open(args.sample))["games"])
        games = [g for g in corpus if g["id"] in ids]
        print("fresh games:", len(games), "plies:", sum(len(g["moves"]) for g in games))
        print(do_fresh(games, args.out))
    elif args.arm == "uncgame":
        meta = do_uncgame(corpus, args.out)
        json.dump(meta, open(args.out + ".meta.json", "w"))
        print("uncgame plies:", meta["plies"])
    elif args.arm in ("unc", "clearhash", "hashresend"):
        ids = set(json.load(open(args.sample))["games"])
        games = [g for g in corpus if g["id"] in ids]
        print(args.arm, "games:", len(games), "plies:", sum(len(g["moves"]) for g in games))
        print(do_reset_arm(games, args.out, args.arm))
    elif args.arm == "bailcheck":
        by_id = {g["id"]: g for g in corpus}
        sess = load_jsonl(args.bails)
        bails = [r for r in sess.values() if r["bail"]]
        print("bail plies found:", len(bails))
        out = []
        for r in sorted(bails, key=lambda x: (x["game"], x["ply"])):
            g = by_id[r["game"]]
            e1 = Engine(ENG); e1.uci(); e1.sync()
            fr = run_search(e1, pos_cmd(g, r["ply"]))
            head = perft_head(e1, pos_cmd(g, r["ply"]))
            e1.quit()
            out.append({"game": r["game"], "ply": r["ply"], "session_bm": r["bm"],
                        "fresh_bm": fr["bm"], "fresh_bail": fr["bail"],
                        "fresh_nodes": fr["nodes"], "gen_head": head,
                        "session_is_head": r["bm"] == head,
                        "same_move": r["bm"] == fr["bm"],
                        "same_bail": r["bail"] == fr["bail"]})
            print(out[-1])
        json.dump(out, open(args.out, "w"), indent=0)


if __name__ == "__main__":
    main()
