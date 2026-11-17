"""Move-identity walk: compare legal MOVE SETS at every node, not just counts.

Every other script here scores node counts. Perft counts are blind to a bug that
substitutes one legal move for another while preserving the total, so a green
count is not proof the generator is emitting the right moves -- only the right
number of them. This script closes that gap by walking the tree and comparing the
engine's move set against python-chess's at each node.

The engine only prints a divide at the root of a `go perft` call, so the walk
sets the position to each child and asks `go perft 1`. That makes the comparison
per-node rather than per-root:
  depth 1 -> root only            (~1 engine call per position)
  depth 2 -> root + every child   (~30 calls per position)
  depth 3 -> root + 2 full levels (~900 calls per position, use a small count)

Child FENs are serialized with fen_with_ep(), because python-chess's board.fen()
drops an en-passant square whose capture would be illegal -- the ep-exposes-king
case. Using fen() here would silently compare a weaker position at every such
node.

Usage: python3 identity.py <engine-binary> [--count N] [--seed S] [--depth D]
"""

from __future__ import annotations

import json
import random
import sys
import time

import chess

from fuzz import fen_with_ep, random_position, targeted_position, TARGETS
from uci_perft import Engine, EngineError, FenRejected, validate_fen


def walk(
    engine: Engine,
    board: chess.Board,
    depth: int,
    path: tuple[str, ...],
    out: dict,
) -> None:
    """Compare engine vs python move sets at `board`, then recurse to `depth`."""
    out["nodes"] += 1
    fen = fen_with_ep(board)
    try:
        engine.set_position(fen)
        divide = engine.perft(1)
    except (FenRejected, EngineError) as exc:
        out["problems"].append(
            {"fen": fen, "path": list(path), "reason": f"harness refused: {exc}"}
        )
        return

    engine_moves = set(divide.children)
    python_moves = {m.uci() for m in board.legal_moves}

    if divide.nodes != len(python_moves):
        out["problems"].append(
            {
                "fen": fen,
                "path": list(path),
                "reason": f"count differs: engine {divide.nodes} python {len(python_moves)}",
                "engine_moves": sorted(engine_moves),
                "python_moves": sorted(python_moves),
            }
        )
    elif engine_moves != python_moves:
        # Same count, different set: the exact bug a count-only perft cannot see.
        out["problems"].append(
            {
                "fen": fen,
                "path": list(path),
                "reason": "move set differs at equal count",
                "engine_only": sorted(engine_moves - python_moves),
                "python_only": sorted(python_moves - engine_moves),
            }
        )
    else:
        out["sets_equal"] += 1

    if depth <= 1:
        return
    for move in board.legal_moves:
        board.push(move)
        walk(engine, board, depth - 1, path + (move.uci(),), out)
        board.pop()


def run(binary: str, count: int, seed: int, depth: int, mix_targets: bool) -> dict:
    rng = random.Random(seed)
    engine = Engine(binary)
    out = {"nodes": 0, "sets_equal": 0, "problems": [], "positions": 0}
    started = time.time()
    try:
        for i in range(count):
            if mix_targets:
                # Rotate through the four targeted edge families so the identity
                # walk also covers the nodes those edges produce.
                target = list(TARGETS)[i % len(TARGETS)]
                fen, _ = targeted_position(rng, target)
            else:
                fen, _ = random_position(rng)
            board = validate_fen(fen)
            out["positions"] += 1
            walk(engine, board, depth, (), out)
            if (i + 1) % 25 == 0:
                print(
                    f"  ... {i + 1}/{count} positions, {out['nodes']} nodes, "
                    f"{out['sets_equal']} sets equal, {len(out['problems'])} problems, "
                    f"{time.time() - started:.1f}s"
                )
            if out["problems"]:
                break  # one real disagreement is enough to report
    finally:
        engine.close()
    out["seconds"] = round(time.time() - started, 1)
    out["seed"] = seed
    out["depth"] = depth
    return out


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "build-swarm74/forge"
    count = 200
    seed = 99
    depth = 2
    out_json = None
    if "--count" in sys.argv:
        count = int(sys.argv[sys.argv.index("--count") + 1])
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    if "--depth" in sys.argv:
        depth = int(sys.argv[sys.argv.index("--depth") + 1])
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    if "--self-test" in sys.argv:
        # Prove the walk can fail on the bug counts cannot see: take a real
        # position, delete one engine move and add a fake one, keeping the count
        # identical, and require the equal-count branch to fire.
        engine = Engine(binary)
        original = engine.perft
        calls = {"n": 0}

        def corrupted(depth_arg: int):
            divide = original(depth_arg)
            calls["n"] += 1
            if depth_arg == 1 and divide.children and calls["n"] == 1:
                # Swap one move out for another, preserving the count exactly so
                # only the SET differs -- invisible to any count comparison.
                victim = next(iter(divide.children))
                divide.children.pop(victim)
                divide.children["a1a8"] = 1
                divide.nodes = len(divide.children)
            return divide

        engine.perft = corrupted  # type: ignore[method-assign]
        board = chess.Board()
        out = {"nodes": 0, "sets_equal": 0, "problems": []}
        walk(engine, board, 1, (), out)
        engine.close()
        assert out["problems"], "equal-count move substitution was NOT detected"
        reason = out["problems"][0]["reason"]
        assert "move set differs at equal count" in reason, f"wrong failure path: {reason}"
        print(f"[self-test] equal-count substitution caught: {reason}")
        print(f"[self-test] engine-only {out['problems'][0]['engine_only']}, "
              f"python-only {out['problems'][0]['python_only']}")
        print("SELF-TEST PASSED: a same-count move substitution is caught by the set comparison")
        return 0

    result = run(binary, count, seed, depth, mix_targets=True)
    print(
        f"\npositions: {result['positions']} | nodes compared: {result['nodes']} | "
        f"move sets equal: {result['sets_equal']} | problems: {len(result['problems'])} | "
        f"{result['seconds']}s | seed {seed} | depth {depth}"
    )
    for problem in result["problems"][:5]:
        print(f"  !! {problem}")
    if out_json:
        with open(out_json, "w") as handle:
            json.dump(result, handle, indent=2)
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
