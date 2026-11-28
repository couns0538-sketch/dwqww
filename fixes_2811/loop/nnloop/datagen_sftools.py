"""Data generation with the official Stockfish `tools` branch (generate_training_data).

Runs one generator process per chunk. A chunk is written under a temporary name and renamed when
the process exits cleanly, so a crash loses at most one chunk.
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from .common import child_env, log, run_logged, stop_requested, tail_text
from .datagen_uci import StopRequested

_COUNT_RE = re.compile(r"_n(\d+)\.binpack$")


def count_done(out_dir: Path) -> int:
    total = 0
    for p in out_dir.glob("chunk_*_n*.binpack"):
        m = _COUNT_RE.search(p.name)
        if m:
            total += int(m.group(1))
    return total


def generate(cfg: dict, round_no: int, out_dir: Path, target: int, tag: str = "chunk") -> dict:
    g = cfg["datagen"]
    t = cfg["sf_tools"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("tmp_*"):
        stale.unlink(missing_ok=True)
    chunk = int(g.get("chunk_positions", 250000))
    have = count_done(out_dir)
    t0 = time.time()
    made = 0
    k = len(list(out_dir.glob("chunk_*_n*.binpack")))
    while have < target:
        if stop_requested(cfg):
            raise StopRequested("STOP file found during sf_tools generation")
        n = min(chunk, target - have)
        tmp_base = f"tmp_{tag}_{k:04d}"
        seed = f"{g.get('seed', 1)}-{tag}-{round_no}-{k}-{time.time_ns()}"
        cmds = [
            "uci",
            "setoption name PruneAtShallowDepth value false",
            f"setoption name Threads value {int(g['workers'])}",
            f"setoption name Hash value {int(t.get('hash_mb', 1024))}",
            f"setoption name EvalFile value {t['net']}",
            "isready",
            ("generate_training_data"
             f" depth {int(t.get('depth', 20))} nodes {int(g['nodes'])} count {n}"
             f" random_move_count {int(g['random_move_count'])}"
             f" random_move_min_ply {max(1, int(g['random_move_min_ply']))}"
             f" random_move_max_ply {int(g['random_move_max_ply'])}"
             f" write_min_ply {int(g['write_min_ply'])} write_max_ply {int(g['max_ply'])}"
             + (f" random_multi_pv {int(g['random_multi_pv'])} random_multi_pv_diff {int(g.get('random_multi_pv_diff', 100))}"
                if int(g.get("random_multi_pv", 0)) > 1 else "") +
             f" eval_limit {int(g['eval_limit'])} keep_draws 1"
             f" output_file_name {tmp_base} seed {seed}"),
            "quit",
        ]
        lp = out_dir / "sf_tools.log"
        tc = time.time()
        rc = run_logged([t["cmd"]], lp, cwd=str(out_dir), env=child_env(cfg), stdin_text="\n".join(cmds) + "\n")
        tmp = out_dir / (tmp_base + ".binpack")
        if rc != 0 or not tmp.exists() or tmp.stat().st_size == 0:
            raise RuntimeError(f"sf_tools generator failed (exit {rc}); log tail:\n{tail_text(lp, 1500)}")
        # the generator reports the real count ("N sfens, ..."); take the last such line
        got = n
        for m in re.finditer(r"^(\d+) sfens,", tail_text(lp, 4000), re.M):
            got = int(m.group(1))
        final = out_dir / f"chunk_{k:04d}_n{got}.binpack"
        os.replace(tmp, final)
        have += got
        made += got
        k += 1
        log(f"sf_tools: chunk {final.name} done in {time.time() - tc:.0f} s "
            f"({got / max(1e-9, time.time() - tc):.0f} pos/s); total {have}/{target}")
    el = time.time() - t0
    return {"positions": have, "new_positions": made, "seconds": round(el, 1),
            "pos_per_s": round(made / el, 1) if el > 0 and made else 0, "backend": "sf_tools",
            "workers": int(g["workers"]), "nodes": int(g["nodes"]), "net": t["net"]}
