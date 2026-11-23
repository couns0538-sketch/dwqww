"""Opus 2026-11-20: the self-play part of a PGO profile run for an exe WITH the game loop inside the engine (carbon2's
`selfgame`, tmp/opus_scratch/selfgame_pc), the counterpart of forge/tools/pgo_selfplay.py with the same arguments, so
that build_forge_clang_pgo.sh can call it through PGOSP_DRIVER. A profile is taken with the work the exe will do: the
loop's client sends ONE `selfgame` line a game, never `go`. Plays <games> games with ONE exe: the loop's options for
<net>, the net checked active, then for each opening `ucinewgame`, `position fen <opening>`, the `selfgame` line with
the loop's [datagen] values; then quits it, so that an instrumented exe writes its profile (LLVM_PROFILE_FILE comes
from the caller's environment).
    pgo_selfgame.py <config> <net> <epd> <games> <exe>
"""
import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, "C:/nnue-lab/pipeline")
from nnloop.common import load_config  # noqa: E402
from nnloop.engine import EngineSpec, UciEngine, check_options, engine_for_net  # noqa: E402


def main():
    cfg = load_config(sys.argv[1])
    net, epd, games, exe = str(Path(sys.argv[2]).resolve()), Path(sys.argv[3]), int(sys.argv[4]), str(Path(sys.argv[5]).resolve())
    books = []
    for ln in epd.read_text(encoding="utf-8").splitlines():
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
    g = cfg["datagen"]
    sg = (f"selfgame softnodes {int(g['soft_nodes'])} evallimit {int(g['eval_limit'])} maxply {int(g['max_ply'])} "
          f"writeminply {int(g['write_min_ply'])} drawply {int(g['draw_adj_ply'])} drawscore {int(g['draw_adj_score'])} "
          f"drawcount {int(g['draw_adj_count'])}")
    # engine_for_net BUILDS the config's own exe when it is missing; inside a build of that very exe that would start
    # the same build again and again. Same path rule as nnloop/engine.py engine_for_net.
    e = cfg["engine"]
    own = Path(cfg["paths"]["runs"]) / "engines" / ("v3-" + str(e.get("v3_build_tag", "r7clang") or "r7clang")) / \
        e.get("built_exe_name", "engine.exe")
    if not own.exists():
        raise SystemExit(f"STOP: the config's own exe {own} is missing; build this exe by hand with PGOSP_CFG naming a "
                         f"config whose exe exists (the loop must never build it on first use)")
    full = engine_for_net(cfg, net)
    spec = EngineSpec(exe, dict(full.options), full.cwd)
    check_options(spec)
    eng = UciEngine(spec)
    eng.send("position startpos")
    eng.send("eval")
    lines = eng.ready()
    if not any("hce 0 nnue" in ln for ln in lines):
        raise SystemExit("STOP: the net is not active: " + " | ".join(lines)[:300])
    t0 = time.time()
    searches = nodes = records = errors = 0
    for f in books:
        eng.new_game()
        eng.send(f"position fen {f}")
        eng.send(sg)
        deadline = time.time() + 600
        while True:
            line = eng._get(deadline)
            if line.startswith("sg "):
                records += 1
            elif line.startswith("sgerror "):
                errors += 1
                break
            elif line.startswith("sgend "):
                t = line.split()
                searches += int(t[t.index("searches") + 1])
                nodes += int(t[t.index("nodes") + 1])
                break
            elif "unknown" in line.lower() or "ERROR" in line:
                raise SystemExit("STOP: the engine said: " + line)
    eng.quit()
    print(f"profile selfgame: {games} games, {searches} searches, {nodes} nodes, {records} records, "
          f"{errors} thrown, wall {time.time() - t0:.1f} s", flush=True)
    if searches < games * 20:
        raise SystemExit("STOP: far fewer searches than the games should give")


if __name__ == "__main__":
    main()
