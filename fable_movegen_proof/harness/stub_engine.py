"""stub_engine.py - a fake UCI engine for the harness self-test (never an engine binary).

Modes:
  hang     answers uci and isready, then reads its input and never answers a go
  early    answers the first 50 go perft commands with a made-up block, then exits in the middle of a block
  garbage  answers every go perft with a block that contains a malformed line
"""
import sys
import time


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "hang"
    out = sys.stdout
    answered = 0
    for line in sys.stdin:
        cmd = line.strip()
        if cmd == "uci":
            out.write("id name stub\nuciok\n")
        elif cmd == "isready":
            out.write("readyok\n")
        elif cmd == "quit":
            break
        elif cmd.startswith("go"):
            if mode == "hang":
                out.flush()
                while True:
                    time.sleep(3600)
            answered += 1
            if mode == "early" and answered > 50:
                out.write("e2e4: 20\n")
                out.flush()
                return 0
            out.write("e2e4: 20\n")
            if mode == "garbage":
                out.write("@@ not a move line @@\n")
            out.write("nodes 20\n")
        out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
