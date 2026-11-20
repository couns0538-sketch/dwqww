"""o_runs.py (Opus, 20 November 2026), for the Grok swarm 3. Python 3 standard library only.
  python3 o_runs.py <exe> <first200.fens> <out_rows.txt> [Name=value ...]
Starts <exe>, sends Threads 1, Hash 16, the 14 settings S14, then the Name=value options given, each followed by
isready (every line up to readyok is read; it STOPS on a refusal line). Per position: ucinewgame, isready,
position fen, isready, go depth 12; row = number, nodes of the LAST info line before bestmove, bestmove.
Writes <out_rows.txt> and <out_rows.txt>.meta (exe path, sha256, id name, every option line sent) and prints
the node sum, the first three and the number of rows."""
import hashlib
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"),
       ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"),
       ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true")]
REFUSALS = ("unknown option", "invalid value", "invalid fen", "illegal move", "no such option")


def main():
    exe, fens, out = sys.argv[1], sys.argv[2], sys.argv[3]
    extra = [tuple(a.split("=", 1)) for a in sys.argv[4:]]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)

    def send(cmd):
        p.stdin.write(cmd + "\n")
        p.stdin.flush()

    def until(word):
        got = []
        while True:
            line = p.stdout.readline()
            if not line:
                sys.exit(f"STOP: the engine ended while waiting for {word}")
            line = line.strip()
            got.append(line)
            if any(r in line.lower() for r in REFUSALS):
                sys.exit(f"STOP: refusal line: {line}")
            if line.split(" ")[0] == word:
                return got

    send("uci")
    id_name = [x for x in until("uciok") if x.startswith("id name")]
    sent = []
    for name, value in [("Threads", "1"), ("Hash", "16")] + S14 + extra:
        sent.append(f"setoption name {name} value {value}")
        send(sent[-1])
        send("isready")
        until("readyok")
    rows = []
    for i, fen in enumerate([x.strip() for x in open(fens, encoding="utf-8") if x.strip()], 1):
        send("ucinewgame")
        send("isready")
        until("readyok")
        send(f"position fen {fen}")
        send("isready")
        until("readyok")
        send("go depth 12")
        got = until("bestmove")
        nodes = None
        for line in got:
            t = line.split()
            if t[:1] == ["info"] and "nodes" in t:
                nodes = int(t[t.index("nodes") + 1])
        if nodes is None:
            sys.exit(f"STOP: position {i}: no info line with nodes")
        rows.append((i, nodes, got[-1].split()[1]))
    send("quit")
    p.wait(timeout=30)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for i, nodes, best in rows:
            f.write(f"{i}\t{nodes}\t{best}\n")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    with open(out + ".meta", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"exe {exe}\nsha256 {sha}\n{id_name[0] if id_name else 'id name ?'}\n" + "\n".join(sent) + "\n")
    print(f"rows {len(rows)} sum {sum(r[1] for r in rows):,} first three "
          f"{rows[0][1]:,} / {rows[1][1]:,} / {rows[2][1]:,}")


if __name__ == "__main__":
    main()
