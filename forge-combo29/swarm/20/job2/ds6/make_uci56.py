#!/usr/bin/env python3
"""make_uci56.py -- 2,000 random UCI command sequences of 5 to 30 lines (seed 56) from the
grammar file 15 names; each sequence ends with isready + quit."""
import random

random.seed(56)
OPTIONS = ["Hash", "Threads", "OwnBook", "MultiPV", "LmpBase", "RfpMargin", "QsSeeMargin",
           "SingularMargin", "IirDepth", "HistoryBonusMax", "AspirationDelta", "NonPawnCorrection",
           "IirAtRoot", "NoRfpAtCut", "BogusOption"]
VALUES = ["0", "1", "2", "16", "64", "256", "-5", "999999", "banana", "true", "false", ""]
MOVE_CHARS = "abcdefgh12345678"

def random_move():
    a = random.choice("abcdefgh") + random.choice("12345678")
    b = random.choice("abcdefgh") + random.choice("12345678")
    promos = ["", "", "", "q", "n", "b", "r"]
    return a + b + random.choice(promos)

def gen_seq():
    n = random.randint(5, 30)
    seq = ["uci"]
    body = []
    pos_state = None
    for _ in range(n - 2):
        t = random.random()
        if t < 0.12:
            body.append("isready")
        elif t < 0.20:
            body.append("ucinewgame")
        elif t < 0.38:
            opt = random.choice(OPTIONS)
            if random.random() < 0.15:
                body.append(f"setoption name {opt}")
            else:
                body.append(f"setoption name {opt} value {random.choice(VALUES)}")
        elif t < 0.58:
            if random.random() < 0.5:
                body.append("position startpos")
            else:
                body.append(f"position fen {random.choice(FENS)}")
            k = random.randint(0, 40)
            mv = " ".join(random_move() for _ in range(k))
            body.append(("position startpos moves " + mv) if random.random() < 0.5 else
                        ("position startpos moves e2e4 " + mv))
        elif t < 0.78:
            kind = random.choice(["depth", "nodes", "movetime", "infinite", "ponder", "depth"])
            if kind == "depth":
                body.append(f"go depth {random.randint(1, 6)}")
            elif kind == "nodes":
                body.append(f"go nodes {random.randint(1, 5000)}")
            elif kind == "movetime":
                body.append(f"go movetime {random.randint(1, 50)}")
            elif kind == "infinite":
                body.append("go infinite")
            else:
                body.append("go ponder")
        elif t < 0.88:
            body.append(random.choice(["stop", "ponderhit"]))
        else:
            body.append(random.choice(["garbage line", "go banana", "position", "setoption name",
                                       "go depth -3", "###"]))
    seq.extend(body)
    seq.append("isready")
    seq.append("quit")
    return seq

FENS = [l.strip() for l in open("/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd",
                                encoding="utf-8", errors="replace") if l.strip()][:50]
with open("/tmp/uci56_seqs.txt", "w") as f:
    for i in range(2000):
        f.write(f"### seq {i}\n")
        for l in gen_seq():
            f.write(l + "\n")
print("wrote /tmp/uci56_seqs.txt (2,000 sequences)")
