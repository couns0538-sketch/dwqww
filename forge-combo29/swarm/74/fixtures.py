"""Special-move edge fixtures, each with an independent python-chess count.

A fixture is only worth its green if the edge it claims to test is actually
reachable in that FEN. So every fixture carries semantic assertions in both
directions: moves that MUST be generated and moves that MUST NOT be. Those are
checked against python-chess first (proving the fixture exercises the edge), and
then the engine's depth-1 move set is compared to python-chess move-for-move,
which is stricter than comparing node counts.

Counting only would let two compensating errors cancel; the move-set equality
plus the required-present / required-absent assertions make that impossible.

Usage: python3 fixtures.py <engine-binary> [--json out.json]
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field

import chess

from uci_perft import Engine, EngineError, FenRejected, py_perft, validate_fen


@dataclass
class Fixture:
    key: str
    title: str
    fen: str
    must_have: tuple[str, ...] = ()
    must_lack: tuple[str, ...] = ()
    depths: tuple[int, ...] = (1, 2, 3)
    note: str = ""


FIXTURES: list[Fixture] = [
    Fixture(
        key="ep-discovers-check",
        title="en passant that discovers check",
        fen="4k3/8/8/3pP3/8/8/8/4R1K1 w - d6 0 1",
        # exd6 e.p. vacates e5, opening the e-file from Re1 to Ke8.
        must_have=("e5d6",),
        note="the ep capture itself delivers discovered check along the e-file",
    ),
    Fixture(
        key="ep-exposes-king",
        title="en passant that would expose the king (illegal)",
        fen="8/8/8/8/k2pP2R/8/8/4K3 b - e3 0 1",
        # dxe3 e.p. vacates d4 and opens rank 4 from Rh4 to Ka4: illegal.
        must_lack=("d4e3",),
        note="both the captured pawn (d4) and the capturer leave rank 4",
    ),
    Fixture(
        key="castle-through-attack",
        title="castling through an attacked square",
        fen="r4rk1/8/8/8/8/8/8/R3K2R w KQ - 0 1",
        # Rf8 attacks f1, so the king crosses an attacked square.
        must_lack=("e1g1",),
        must_have=("e1c1",),
        note="O-O illegal because f1 is attacked; O-O-O unaffected",
    ),
    Fixture(
        key="castle-out-of-check",
        title="castling out of check",
        # White is in check from Bb4 (b4-c3-d2-e1). Both castles are barred.
        fen="4k3/8/8/8/1b6/8/8/R3K2R w KQ - 0 1",
        must_lack=("e1g1", "e1c1"),
        note="both castles illegal while the king stands in check",
    ),
    Fixture(
        key="castle-rook-attacked",
        title="castling when the rook is attacked (legal)",
        fen="r3k3/8/8/8/8/8/8/R3K2R w KQq - 0 1",
        # Ra8 attacks a1, but the king never crosses an attacked square.
        must_have=("e1c1", "e1g1"),
        note="an attacked rook does not bar castling; only king squares matter",
    ),
    Fixture(
        key="castle-rights-lost-rook-capture",
        title="castling rights lost by rook capture",
        fen="r3k2r/8/8/8/8/8/8/R3K3 w Qkq - 0 1",
        must_lack=("e1g1",),
        must_have=("e1c1",),
        note="h1 rook is gone, so the kingside right is gone; queenside survives",
    ),
    Fixture(
        key="promotion-with-capture",
        title="promotion with capture",
        # Na8 blocks the quiet push; Nb8 is the only capture target, so every
        # promotion in this position is a capture promotion.
        fen="nn6/P7/8/8/8/8/8/k6K w - - 0 1",
        must_have=("a7b8q", "a7b8r", "a7b8b", "a7b8n"),
        must_lack=("a7a8q", "a7a8r", "a7a8b", "a7a8n"),
        note="all four promotions by capture; the quiet push is blocked by Na8",
    ),
    Fixture(
        key="underpromotion-knight-check",
        title="underpromotion to knight giving check",
        fen="8/1P1k4/8/8/8/8/8/7K w - - 0 1",
        # Nb8+ is the only promotion that gives check: Q/R/B on b8 miss d7.
        must_have=("b7b8n", "b7b8q", "b7b8r", "b7b8b"),
        note="b8=N+ checks Kd7; b8=Q/R/B do not, so the knight is the only checker",
    ),
    Fixture(
        key="double-push-beside-pawn",
        title="double pawn push landing beside an enemy pawn",
        fen="4k3/8/8/8/3p4/8/4P3/4K3 w - - 0 1",
        must_have=("e2e4",),
        note="e2e4 sets an ep square next to the black d4 pawn; black may answer dxe3",
    ),
    Fixture(
        key="pinned-piece-along-line",
        title="pinned piece that can still move along the pin line",
        fen="4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1",
        # Re2 is pinned on the e-file but may still slide on it.
        must_have=("e2e3", "e2e4", "e2e8"),
        must_lack=("e2a2", "e2h2", "e2d2"),
        note="the pinned rook keeps every move along the pin line and no others",
    ),
    Fixture(
        key="pin-bishop-illegal",
        title="pinned bishop that may not leave the pin line",
        fen="4r1k1/8/8/8/8/8/4B3/4K3 w - - 0 1",
        # Be2 has no legal move at all along the e-file except e2-c4-style
        # diagonals, which all break the pin.
        must_lack=("e2c4", "e2d3", "e2f3", "e2g4"),
        note="control for the previous fixture: same pin, a piece that cannot use it",
    ),
]


def run(binary: str) -> tuple[list[dict], int]:
    engine = Engine(binary)
    rows: list[dict] = []
    failures = 0
    try:
        for fx in FIXTURES:
            board = validate_fen(fx.fen)
            engine.set_position(fx.fen)  # raises if the engine refused this FEN

            legal = {m.uci() for m in board.legal_moves}
            identity = engine.perft(1)
            engine_moves = set(identity.children)

            row: dict = {
                "key": fx.key,
                "title": fx.title,
                "fen": fx.fen,
                "note": fx.note,
                "must_have": list(fx.must_have),
                "must_lack": list(fx.must_lack),
                "problems": [],
                "cells": {},
            }
            problems: list[str] = row["problems"]

            # A. Prove the fixture exercises the edge at all (python-chess).
            for move in fx.must_have:
                if move not in legal:
                    problems.append(f"FIXTURE DEAD: {move} is not legal in this FEN")
            for move in fx.must_lack:
                if move in legal:
                    problems.append(f"FIXTURE DEAD: {move} IS legal in this FEN")

            # B. Board identity, then the move set itself.
            if identity.nodes != len(legal):
                problems.append(
                    f"identity: engine perft 1 {identity.nodes} vs python-chess {len(legal)}"
                )
            if engine_moves != legal:
                only_engine = sorted(engine_moves - legal)
                only_python = sorted(legal - engine_moves)
                problems.append(
                    f"move set differs: engine-only {only_engine}, python-only {only_python}"
                )

            # C. Counts at each requested depth.
            for depth in fx.depths:
                want = py_perft(board, depth)
                got = identity.nodes if depth == 1 else engine.perft(depth).nodes
                row["cells"][str(depth)] = {"engine": got, "python": want, "ok": got == want}
                if got != want:
                    problems.append(f"d{depth}: engine {got} vs python-chess {want}")

            if problems:
                failures += 1
            rows.append(row)

            status = "ok" if not problems else "PROBLEM"
            print(f"\n[{fx.key}] {fx.title}  -- {status}")
            print(f"  fen: {fx.fen}")
            print(
                f"  legal moves: {len(legal)}  required: {list(fx.must_have)}  "
                f"forbidden: {list(fx.must_lack)}"
            )
            cells = ", ".join(
                f"d{d}={c['engine']}" + ("" if c["ok"] else f"(want {c['python']})")
                for d, c in row["cells"].items()
            )
            print(f"  {cells}")
            for problem in problems:
                print(f"  !! {problem}")
    finally:
        engine.close()
    return rows, failures


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "build-swarm74/forge"
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]

    if "--self-test" in sys.argv:
        # Prove this script can fail. Plant a bad expectation and a dead fixture
        # and require both to be reported as problems.
        global FIXTURES
        planted = Fixture(
            key="planted-bad-count",
            title="self-test: expectation off by one",
            fen="4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
            must_have=("e2e4",),
            depths=(1, 2),
        )
        dead = Fixture(
            key="planted-dead-fixture",
            title="self-test: forbidden move is actually legal",
            fen="4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
            must_lack=("e2e4",),  # e2e4 IS legal, so the fixture is dead
            depths=(1,),
        )
        FIXTURES = [planted, dead]
        rows, failures = run(binary)
        # Also drive the count comparison itself to red.
        rows[0]["cells"]["1"]["engine"] += 1
        rows[0]["cells"]["1"]["ok"] = (
            rows[0]["cells"]["1"]["engine"] == rows[0]["cells"]["1"]["python"]
        )
        assert not rows[0]["cells"]["1"]["ok"], "planted off-by-one did not go red"
        assert any("FIXTURE DEAD" in p for p in rows[1]["problems"]), (
            "dead fixture was not detected"
        )
        print(
            "\nSELF-TEST PASSED: a planted off-by-one count and a dead fixture "
            "both go red"
        )
        return 0

    rows, failures = run(binary)
    total_cells = sum(len(r["cells"]) for r in rows)
    print(
        f"\nfixtures: {len(rows)} | cells: {total_cells} | "
        f"fixtures with problems: {failures}"
    )
    if out_json:
        with open(out_json, "w") as handle:
            json.dump(rows, handle, indent=2)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
