"""Prove the driver and the refusal detector can both FAIL before trusting them.

Four checks:
  1. a valid FEN is accepted and searched with a node count near the budget
  2. an invalid FEN emits `info string invalid FEN` in the POSITION reply
  3. the same invalid FEN emits it in the GO output when isready is skipped
  4. the detector returns False on a valid position (so it is not always-true)
"""

from __future__ import annotations

import sys

import ucidrv

ENGINE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-base/forge"

VALID = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4"
INVALID = "zzzz/pppp/8/8/8/8/PPPP/ZZZZ w - - 0 1"


def refusals(lines: list[str]) -> list[str]:
    return [l for l in lines if "invalid FEN" in l]


def main() -> int:
    failures: list[str] = []

    # 1. valid FEN accepted, node count close to budget
    with ucidrv.Engine(ENGINE) as e:
        e.handshake()
        e.set_option("OwnBook", "false")
        e.set_option("Threads", "1")
        e.set_option("Hash", "64")
        e.set_option("MultiPV", "1")
        e.sync()
        pos = e.set_position(VALID)
        if refusals(pos):
            failures.append(f"valid FEN was refused: {refusals(pos)}")
        go, ms = e.go_nodes(200000, timeout=180)
        if refusals(go):
            failures.append(f"valid FEN refused in go: {refusals(go)}")
        infos = [x for x in (ucidrv.parse_info(l) for l in go) if x]
        if not infos:
            failures.append("valid FEN produced no info depth line")
            nodes = -1
        else:
            nodes = infos[-1].get("nodes", -1)
            if not (200000 <= nodes <= 210000):
                failures.append(f"node count {nodes} not in [200000,210000]")
        print(f"CHECK1 valid FEN: refusals={len(refusals(pos))} nodes={nodes} ms={ms:.1f}")

    # 2. invalid FEN diagnostic in the POSITION reply
    with ucidrv.Engine(ENGINE) as e:
        e.handshake()
        pos = e.set_position(INVALID)
        r = refusals(pos)
        print(f"CHECK2 invalid FEN in position reply: {r}")
        if not r:
            failures.append("invalid FEN gave no diagnostic in the position reply")
        # the detector must NOT read the diagnostic out of a stream that lacks it
        if refusals([l for l in pos if l.startswith("info depth")]):
            failures.append("diagnostic appeared inside info depth lines (unexpected)")

    # 3. same diagnostic in the GO output when isready is skipped
    with ucidrv.Engine(ENGINE) as e:
        e.handshake()
        e.set_option("OwnBook", "false")
        e.send(f"position fen {INVALID}")
        go, _ = e.go_nodes(200000, timeout=180)
        r = refusals(go)
        print(f"CHECK3 invalid FEN in go output: {r}")
        if not r:
            failures.append("invalid FEN gave no diagnostic in the go output")

    # 4. detector is not always-true: a known-good position has no refusal
    with ucidrv.Engine(ENGINE) as e:
        e.handshake()
        e.set_option("OwnBook", "false")
        e.sync()
        pos = e.set_position(None)  # startpos
        if refusals(pos):
            failures.append("startpos reported a refusal")
        print(f"CHECK4 startpos refusals: {len(refusals(pos))}")

    if failures:
        print("\nFAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS all four checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
