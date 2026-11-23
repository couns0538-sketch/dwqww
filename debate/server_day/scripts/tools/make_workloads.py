"""Fable 2026-11-23, W5 (a) and (b) of FINAL_PLAN_2311.md: the UCI texts every server-day build is profiled and
checked with, made from the LIVE config, so that no option or game setting is typed a second time.

    make_workloads.py <pipeline folder> <config.toml> <net.fnn3> <books.epd> <games> <new out folder>

Runs on the PC (it imports the loop's own code for the option list and the self-play line). Writes:
  options.uci          the options the loop sends for this net, in the loop's order; the net's path is @@NET@@
  profile.uci          the profile run of a profile-guided build: options, net check, bench 11 / 13 / 16, then
                       <games> self-play games, each as the loop plays it (new game, position, ONE selfgame line)
  verify.uci           built-in pins (bench 11, bench 13, 12 perft counts), then the net with the loop's options
                       (eval, bench 11, bench 13)
  startup.uci          the start-up check: options, `eval` on two positions (which evaluator answers: N17), then
                       the live searcher: new game, start position, go depth 18
  startup_hash32.uci   the same with Hash 32 on purpose: its numbers differ, and a start script must refuse
  n12_batch.uci        the plan's N12 batch: six fixed openings in ONE process, a new game before each
  n12_no_newgame.uci   planted: the new-game command left out before game 2 (must give other rows)
  n12_writeminply9.uci planted: one changed game setting (must give other rows)
  selfgame_line.txt, MANIFEST.json (hashes of config, net and books; the option list; the counts)
The texts hold commands only. tools/drive.py does the waiting (readyok, bestmove, sgend).
"""
import hashlib
import json
import sys
from pathlib import Path

import chess

PERFT = [  # the six standard positions, 12 published counts (pipeline/tools/perft_suite.py)
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", {5: 4865609, 6: 119060324}),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", {4: 4085603, 5: 193690690}),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", {5: 674624, 6: 11030083}),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", {4: 422333, 5: 15833292}),
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", {4: 2103487, 5: 89941194}),
    ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", {4: 3894594, 5: 164075551}),
]
# N12's batch (the plan's W5 (i); Astra 20261123T053252Z; the same six as tmp/fable_scratch/debate/n12_sixgames.py,
# which gave on the PC's Windows program: rows / end / searches / nodes = 86 drawadj 86 302461; 101 drawadj 101
# 383484; 0 rule 0 0; 127 evallimit 128 530258; 81 drawadj 81 307107; 67 rule 67 227258).
# Each is eight opening moves from the start position; the engine is given "position startpos moves ...".
N12 = [
    "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6",       # N12 first
    "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7",       # N12 second (the two plants act on this game only)
    "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",       # A7 threefold: 0 rows, ends by rule
    "g1f3 g8f6 b1c3 b8c6 c3b1 c6b8 f3g1 f6g8",       # A7 same FEN, no draw
    "b1c3 g8f6 c3d5 b8a6 g1h3 a6b8 h3g1 f6e4",       # A7 other history 1
    "b1c3 g8f6 c3e4 f6g8 e4c3 g8f6 c3d5 f6e4",       # A7 other history 2
]


# N17 of the plan: the start position, and a position a queen up whose value must be far from zero
STARTUP_PROBES = ["position startpos",
                  "position fen rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"]
STARTUP_DEPTH = 18


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    pipeline, cfg_path, net, epd, games, out = sys.argv[1:7]
    games, out = int(games), Path(out)
    sys.path.insert(0, pipeline)
    from nnloop.common import load_config
    from nnloop.engine import engine_for_net, uci_value

    cfg = load_config(cfg_path)
    e = cfg["engine"]
    own = Path(cfg["paths"]["runs"]) / "engines" / ("v3-" + str(e.get("v3_build_tag"))) / e.get("built_exe_name", "engine.exe")
    if not own.exists():        # engine_for_net would BUILD a missing exe: never from this tool
        raise SystemExit(f"STOP: the config's own exe {own} is missing")
    net = str(Path(net).resolve())
    spec = engine_for_net(cfg, net)
    names = list(spec.options)
    if "NNUEArchFile" not in names or "NNUEArch" not in names or names.index("NNUEArchFile") > names.index("NNUEArch"):
        raise SystemExit(f"STOP: the option list does not hold NNUEArchFile before NNUEArch: {names}")
    if Path(str(spec.options["NNUEArchFile"])).resolve() != Path(net):
        raise SystemExit(f"STOP: NNUEArchFile is {spec.options['NNUEArchFile']}, not the net given")
    opts = [f"setoption name {k} value {'@@NET@@' if k == 'NNUEArchFile' else uci_value(v)}" for k, v in spec.options.items()]

    books = []
    for ln in Path(epd).read_text(encoding="utf-8").splitlines():
        t = ln.split()
        if len(t) >= 6 and t[4].isdigit() and t[5].isdigit():
            books.append(" ".join(t[:6]))
        elif len(t) >= 4:
            books.append(" ".join(t[:4]) + " 0 1")
    if len(books) < games:
        raise SystemExit(f"STOP: {epd} holds {len(books)} positions, {games} asked")
    books = books[:games]
    for f in books:
        if not chess.Board(f).is_valid():
            raise SystemExit(f"STOP: book position not valid: {f}")
    for line in N12:                      # every N12 opening must be eight legal moves
        b = chess.Board()
        for m in line.split():
            b.push_uci(m)

    g = cfg["datagen"]

    def sg(write_min_ply=None):
        return (f"selfgame softnodes {int(g['soft_nodes'])} evallimit {int(g['eval_limit'])} maxply {int(g['max_ply'])} "
                f"writeminply {int(g['write_min_ply']) if write_min_ply is None else write_min_ply} "
                f"drawply {int(g['draw_adj_ply'])} drawscore {int(g['draw_adj_score'])} drawcount {int(g['draw_adj_count'])}")

    out.mkdir(parents=True, exist_ok=False)

    def put(name, lines):
        (out / name).write_bytes(("\n".join(lines) + "\n").encode("ascii"))

    put("options.uci", opts)
    put("selfgame_line.txt", [sg()])
    prof = ["uci", *opts, "isready", "position startpos", "eval", "bench 11", "bench 13", "bench 16"]
    for f in books:
        prof += ["ucinewgame", "isready", f"position fen {f}", sg()]
    put("profile.uci", prof + ["quit"])

    ver = ["uci", "bench 11", "bench 13"]
    for fen, want in PERFT:
        for d in want:
            ver += [f"position fen {fen}", f"go perft {d}"]
    ver += [*opts, "isready", "position startpos", "eval", "bench 11", "bench 13", "quit"]
    put("verify.uci", ver)

    start = ["uci", *opts, "isready"]
    for probe in STARTUP_PROBES:               # N17: WHICH evaluator answers, before the search is trusted
        start += [probe, "eval"]
    start += ["ucinewgame", "isready", "position startpos", f"go depth {STARTUP_DEPTH}", "quit"]
    put("startup.uci", start)
    h32 = [("setoption name Hash value 32" if x.startswith("setoption name Hash value ") else x) for x in start]
    if h32 == start or sum(x.startswith("setoption name Hash value ") for x in start) != 1:
        raise SystemExit("STOP: the option list holds no single Hash line to change for the planted case")
    put("startup_hash32.uci", h32)

    def n12(skip_newgame_before=None, wmp9_for=None):
        t = ["uci", *opts, "isready"]
        for i, mv in enumerate(N12, 1):
            if i != skip_newgame_before:
                t += ["ucinewgame", "isready"]
            t += ["position startpos moves " + mv, sg(9 if i == wmp9_for else None)]
        return t + ["quit"]

    put("n12_batch.uci", n12())
    put("n12_no_newgame.uci", n12(skip_newgame_before=2))     # planted: no new game before game 2
    put("n12_writeminply9.uci", n12(wmp9_for=2))              # planted: one changed game setting, game 2 only

    man = {"made_by": "serverday/tools/make_workloads.py", "config_sha256": sha(cfg_path), "net_file": Path(net).name,
           "net_sha256": sha(net), "net_bytes": Path(net).stat().st_size, "books_sha256": sha(epd),
           "profile_games": games, "options": opts, "selfgame_line": sg(),
           "startup_probes": STARTUP_PROBES, "startup_depth": STARTUP_DEPTH,
           "loop_exe": str(own).replace("\\", "/"), "loop_exe_sha256": sha(own),
           "perft": [[fen, {str(d): n for d, n in want.items()}] for fen, want in PERFT]}
    (out / "MANIFEST.json").write_bytes((json.dumps(man, indent=1) + "\n").encode("ascii"))
    print(f"wrote {len(list(out.iterdir()))} files to {out}: {len(opts)} options, {games} profile games; "
          f"net {man['net_sha256'][:16]} ({man['net_bytes']} bytes)")
    print("selfgame line:", sg())


if __name__ == "__main__":
    main()
