"""Group 1 driver: ONE engine process plays both sides of each book line, in order.
Protocol per the brief: ucinewgame+isready per opening; per move
'position fen <FEN> moves <uci...>' (no 'moves' when none); the go command; read to
bestmove; record '<book line> <ply> <bestmove> <nodes>'; push on a python-chess board;
game over when board.is_game_over(claim_draw=True) or after 300 plies."""
import subprocess, re, sys, json, chess

BAD = ("unknown option","invalid value","ERROR","No such option")
S14 = [("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
       ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
       ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
       ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),
              ("MateAlphaGuard","true"),("OwnBook","false")]

class Eng:
    def __init__(self, path, extra_opts=(), net=None):
        self.p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.path = path
        self.option_lines = ["uci"]
        self.send("uci")
        self.idline = None
        while True:
            l = self.p.stdout.readline()
            if not l: raise RuntimeError("died during uci")
            l = l.rstrip("\n")
            if l.startswith("id name "): self.idline = l
            if l.strip() == "uciok": break
        for n, v in [("Threads",1),("Hash",16)] + list(extra_opts):
            s = f"setoption name {n} value {v}"
            self.send(s); self.option_lines.append(s)
        if net:
            s = f"setoption name NNUEArchFile value {net}"
            self.send(s); self.option_lines.append(s)
            s = "setoption name NNUEArch value true"
            self.send(s); self.option_lines.append(s)
        self.send("isready"); self.option_lines.append("isready")
        hs = []
        while True:
            l = self.p.stdout.readline()
            if not l: raise RuntimeError("died before readyok")
            l = l.rstrip("\n"); hs.append(l)
            if l.strip() == "readyok": break
        self.handshake = hs
        for l in hs:
            for b in BAD:
                if b.lower() in l.lower():
                    raise RuntimeError(f"VOID handshake: {l!r}")
        if net:
            txt = "\n".join(hs)
            if "checksum 30ab43b4ba5db5f3" not in txt:
                raise RuntimeError("VOID: no 'checksum 30ab43b4ba5db5f3' line")
            if "info string NNUE v3 active" not in txt:
                raise RuntimeError("VOID: no 'info string NNUE v3 active' line")
    def send(self, s):
        self.p.stdin.write(s + "\n"); self.p.stdin.flush()
    def read_bestmove(self):
        out = []
        while True:
            l = self.p.stdout.readline()
            if not l: raise RuntimeError("engine died before bestmove")
            l = l.rstrip("\n"); out.append(l)
            if l.startswith("bestmove"): return out
    def newgame(self):
        self.send("ucinewgame"); self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l: raise RuntimeError("died before readyok (newgame)")
            if l.strip() == "readyok": return
    def close(self):
        try: self.send("quit"); self.p.wait(timeout=10)
        except Exception: self.p.kill()

def parse_out(out):
    nodes = None
    for l in out:
        if l.startswith("info") and " nodes " in l:
            m = re.search(r" nodes (\d+)", l)
            if m: nodes = int(m.group(1))
    bm = out[-1].split()[1] if out and out[-1].startswith("bestmove") else None
    return bm, nodes

def play_game(e, line_no, fen, go_cmd, max_plies=300):
    board = chess.Board(fen)
    if board.is_game_over(claim_draw=True):
        return [(line_no, 0, "START_GAME_OVER", "")]
    moves, recs = [], []
    while not board.is_game_over(claim_draw=True) and len(moves) < max_plies:
        pos = f"position fen {fen}" + ((" moves " + " ".join(moves)) if moves else "")
        e.send(pos); e.send(go_cmd)
        out = e.read_bestmove()
        bm, nodes = parse_out(out)
        if bm is None:
            recs.append((line_no, len(moves)+1, "NO_BESTMOVE", nodes if nodes is not None else ""))
            break
        recs.append((line_no, len(moves)+1, bm, nodes if nodes is not None else ""))
        try:
            m = chess.Move.from_uci(bm)
        except ValueError:
            recs.append((line_no, len(moves)+1, f"UNPARSEABLE:{bm}", ""))
            break
        if m not in board.legal_moves:
            recs.append((line_no, len(moves)+1, f"ILLEGAL:{bm}", ""))
            break
        board.push(m); moves.append(bm)
    return recs

def run(path, lines, go_cmd, out_path, meta_path, extra_opts=(), net=None):
    e = Eng(path, extra_opts=extra_opts, net=net)
    all_recs = []
    try:
        for line_no, fen in lines:
            all_recs.extend(play_game(e, line_no, fen, go_cmd))
    finally:
        idline = e.idline
        optlines = list(e.option_lines)
        e.close()
    with open(out_path, "w") as fh:
        for r in all_recs:
            fh.write(f"{r[0]} {r[1]} {r[2]} {r[3]}\n")
    import hashlib
    sha = hashlib.sha256(open(path,'rb').read()).hexdigest()
    with open(meta_path, "w") as fh:
        fh.write(f"program: {path}\nsha256: {sha}\n{idline}\n")
        for l in optlines: fh.write(l + "\n")
    return all_recs

def load_lines(path, lo, hi):
    out = []
    with open(path) as fh:
        for i, l in enumerate(fh, 1):
            if lo <= i <= hi:
                out.append((i, l.strip()))
            if i > hi: break
    return out

if __name__ == "__main__":
    print("module ok; PC20 options:", len(PC20))
