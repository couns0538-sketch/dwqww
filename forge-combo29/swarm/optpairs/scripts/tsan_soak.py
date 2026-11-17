"""ThreadSanitizer soak, driven the only way that works.

The first version of this was a shell script that piped a whole command block
including `quit` into the engine. That is the brief's trap 1: the engine aborts
and fabricates a `bestmove` with ZERO `info depth` lines, so nothing was searched
and the clean TSan output meant nothing. Demonstrated before rewriting:
`printf '... go depth 12\\nquit\\n' | ./forge` printed `bestmove a2a3` and no info
lines.

So each search here gets a fresh process, is read to `bestmove`, and only then
gets `quit`. stderr and stdout are merged, because ThreadSanitizer writes to
stderr and the engine's own chatter is on stdout.

Proved live first: scripts/tsan_planted_race.sh must report a race, otherwise a
clean run is "no report" rather than "no race".
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "evidence")

BIN = "/tmp/build-tsan/forge"

P = "r2q1rk1/pp2ppbp/2n2np1/2pp4/3P1B2/2PBPN2/PP1N1PPP/R2Q1RK1 w - - 0 9"
Q = "4rrk1/pp1n1ppp/2pb4/8/2B1P3/2N2N2/PP3PPP/R2R2K1 w - - 1 15"
R = "rnbq1rk1/pp2bppp/2p1pn2/3p4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 7"

CASES = [
    ("T4 depth 11, nnue on", [("Threads", "4"), ("Hash", "32")], P, "go depth 11"),
    ("T4 depth 11, nnue off", [("Threads", "4"), ("UseNNUE", "false"), ("Hash", "32")], P, "go depth 11"),
    ("T4 depth 11, Hash 1 (max collisions)", [("Threads", "4"), ("Hash", "1")], P, "go depth 11"),
    ("T4 depth 11, position Q", [("Threads", "4"), ("Hash", "32")], Q, "go depth 11"),
    ("T4 depth 11, position R", [("Threads", "4"), ("Hash", "32")], R, "go depth 11"),
    ("T4 movetime 2s", [("Threads", "4"), ("Hash", "32")], P, "go movetime 2000"),
    ("T8 depth 10 (oversubscribed)", [("Threads", "8"), ("Hash", "32")], P, "go depth 10"),
    ("T4 MultiPV 3 (helpers idle)", [("Threads", "4"), ("MultiPV", "3"), ("Hash", "32")], P, "go depth 10"),
    ("T4 drawn-root bail", [("Threads", "4"), ("OwnBook", "false")],
     "8/8/8/8/8/1R6/8/k1K5 w - - 100 1", "go depth 8"),
]


def one(label, options, fen, go, resize_after=None):
    """Run one search to bestmove, optionally resizing Hash mid-process and
    searching again, then quit. Returns the raw transcript."""
    proc = subprocess.Popen([BIN], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    transcript = []

    def send(t):
        proc.stdin.write(t + "\n")
        proc.stdin.flush()

    def read_until_ready():
        while True:
            line = proc.stdout.readline()
            if not line:
                return False
            transcript.append(line.rstrip("\n"))
            if line.strip() == "readyok":
                return True

    def read_until_bestmove():
        infos = 0
        while True:
            line = proc.stdout.readline()
            if not line:
                return infos
            transcript.append(line.rstrip("\n"))
            if line.startswith("info depth"):
                infos += 1
            if line.startswith("bestmove"):
                return infos

    send("uci")
    for line in proc.stdout:
        transcript.append(line.rstrip("\n"))
        if line.strip() == "uciok":
            break
    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until_ready()
    send(f"position fen {fen}")
    send("isready")
    read_until_ready()
    send(go)
    infos = read_until_bestmove()
    if resize_after:
        send(f"setoption name Hash value {resize_after}")
        send("isready")
        read_until_ready()
        send("position fen " + fen)
        send("isready")
        read_until_ready()
        send(go)
        infos += read_until_bestmove()
    send("quit")
    # ThreadSanitizer writes its report AT EXIT, after `bestmove`. A harness that
    # stops reading at bestmove sees a clean run for a racy binary -- which is
    # what the first version of this script did, and the planted-fault build is
    # what caught it. Drain everything still in the pipe.
    try:
        rest, _ = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        rest, _ = proc.communicate()
    if rest:
        transcript.extend(rest.splitlines())
    tsan = [l for l in transcript if "ThreadSanitizer" in l]
    return {"label": label, "options": options, "fen": fen, "go": go,
            "info_lines": infos, "searched": infos > 0, "exit": proc.returncode,
            "tsan_reports": len(tsan), "tsan_lines": tsan[:40],
            "bestmove": next((l for l in transcript if l.startswith("bestmove")), None)}


def main():
    results = []
    for label, options, fen, go in CASES:
        results.append(one(label, options, fen, go))
    results.append({**one("T4 resize Hash 32->64 mid-process", [("Threads", "4"), ("Hash", "32")], P,
                          "go depth 10", resize_after="64"), "label": "T4 resize Hash 32->64 mid-process"})
    bad = [r for r in results if not r["searched"]]
    out = {"binary": BIN, "cases": results,
           "unsearched_cases": [r["label"] for r in bad],
           "total_tsan_reports": sum(r["tsan_reports"] for r in results)}
    with open(os.path.join(OUT, "tsan.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    with open(os.path.join(OUT, "tsan.txt"), "w") as fh:
        for r in results:
            fh.write(f"### {r['label']}  exit={r['exit']}  info_lines={r['info_lines']}"
                     f"  tsan={r['tsan_reports']}  {r['bestmove']}\n")
            for l in r["tsan_lines"]:
                fh.write("    " + l + "\n")
    print(f"TSan soak, {len(results)} cases, binary {BIN}")
    for r in results:
        flag = "" if r["searched"] else "   <-- NOT SEARCHED"
        print(f"  {r['label']:42s} info={r['info_lines']:3d} tsan={r['tsan_reports']}{flag}")
    print("total TSan reports:", out["total_tsan_reports"])
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
