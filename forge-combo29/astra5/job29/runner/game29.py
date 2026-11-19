"""Play one fixed-limit Forge game and retain an auditable UCI transcript."""
import asyncio
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

try:
    import chess
except ImportError:
    sys.path.insert(0,"/workspace/work/tactic3/deps")
    import chess

BASE = [
    ("Threads","1"),("Hash","16"),("OwnBook","false"),("MateAlphaGuard","true"),
    ("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
    ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
    ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
    ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
    ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
]
SEARCH_COLS = "match game ply side color n depth score bestmove go soft_n info_nodes info_line soft_line move_line".split()
GAME_COLS = "match game opening white black result ending plies started_utc ended_utc".split()
REFUSAL = re.compile("unknown option|invalid value|ERROR", re.IGNORECASE)
NODE_LINE = re.compile(r"info string softnodes nodes (\d+)")
DEPTH = re.compile(r"\bdepth (\d+)\b")
SCORE = re.compile(r"\bscore ((?:cp|mate) -?\d+)\b")
NODES = re.compile(r"\bnodes (\d+)\b")
PROFILES = {
    "D1": ("go softnodes 4000", "go softnodes 2000"),
    "D2": ("go softnodes 2000", "go softnodes 1000"),
    "E": ("go nodes 4000", "go softnodes 2000"),
    "D3": ("go softnodes 8000", "go softnodes 4000"),
    "D4": ("go softnodes 1000", "go softnodes 500"),
    "C29": ("go softnodes 2000", "go softnodes 2000"),
    "F1": ("go softnodes 2800", "go softnodes 2000"),
    "F2": ("go softnodes 2000", "go softnodes 1400"),
}


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Engine:
    def __init__(self, exe, side, label, go, wire):
        self.exe = exe
        self.side = side
        self.label = label
        self.go = go
        self.wire = wire
        self.options = BASE
        self.proc=None; self.active_reply=[]; self.pid_identity={}

    def note(self, event, line):
        self.wire.write(f"{self.side} {event} {line}\n")

    async def send(self, cmd):
        self.note(">",cmd)
        self.proc.stdin.write((cmd+"\n").encode("ascii"))
        await self.proc.stdin.drain()

    async def line(self):
        raw=await self.proc.stdout.readline()
        if not raw: raise RuntimeError(f"{self.side} engine closed its UCI pipe")
        line=raw.decode("utf-8",errors="replace").rstrip("\r\n")
        self.active_reply.append(line)
        self.note("<", line)
        if REFUSAL.search(line): raise RuntimeError(f"{self.side} engine diagnostic: {line}")
        return line

    async def start(self):
        creating=asyncio.create_task(asyncio.create_subprocess_exec(str(self.exe),cwd=self.exe.parent,
            stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT))
        try:
            self.proc=await asyncio.shield(creating)
        except asyncio.CancelledError:
            # Retain ownership if cancellation overlaps fork/exec; play() then kills this child.
            self.proc=await creating
            raise
        pid=self.proc.pid
        started=utc()
        await self.send("uci")
        names=set(); ids=[]
        while True:
            line=await self.line()
            if line=="uciok": break
            if line.startswith("id "): ids.append(line)
            m=re.match(r"option name (.+?) type ",line)
            if m: names.add(m[1])
        for name,value in self.options:
            if name not in names: raise RuntimeError(self.side+" missing option "+name)
            await self.send(f"setoption name {name} value {value}")
        await self.send("ucinewgame")
        await self.send("isready")
        while await self.line()!="readyok": pass
        st=Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()[19]
        self.pid_identity=dict(pid=pid,start_ticks=st,started_utc=started,exe=str(self.exe),
                               id=ids,role=self.label,options=self.options,go=self.go)
        self.active_reply=[]

    async def search(self, position):
        self.active_reply = []
        await self.send(position)
        await self.send(self.go)
        soft_n = soft_line = info_nodes = depth = score = info_line = "NA"
        while True:
            line = await self.line()
            if matched := NODE_LINE.fullmatch(line):
                if soft_n != "NA":
                    raise ValueError(f"{self.side} duplicated final node count")
                soft_n, soft_line = int(matched[1]), line
            elif line.startswith("info ") and not line.startswith("info string "):
                deep = DEPTH.search(line)
                if deep:
                    if nodes := NODES.search(line):
                        info_nodes = int(nodes[1])
                    if scoring := SCORE.search(line):
                        depth, score, info_line = int(deep[1]), scoring[1], line
            elif line.startswith("bestmove "):
                if self.go.startswith("go softnodes") and soft_n == "NA":
                    raise ValueError(f"{self.side} missing final node count")
                n = soft_n if self.go.startswith("go softnodes") else info_nodes
                return (n, depth, score, line.split()[1], self.go, soft_n, info_nodes,
                        info_line, soft_line, line)

    async def close(self,graceful):
        if self.proc is None: return
        try:
            if self.proc.returncode is None:
                if graceful:
                    await self.send("quit")
                    await asyncio.wait_for(self.proc.wait(),timeout=3)
                else:
                    self.proc.kill()
        finally:
            if self.proc.returncode is None:
                try: self.proc.kill()
                except ProcessLookupError: pass
            await self.proc.wait()


def end(board):
    if board.is_checkmate(): return ("0-1" if board.turn else "1-0","checkmate")
    if board.is_stalemate(): return "1/2-1/2","stalemate"
    if board.is_insufficient_material(): return "1/2-1/2","insufficient"
    if board.can_claim_threefold_repetition(): return "1/2-1/2","threefold"
    if board.can_claim_fifty_moves(): return "1/2-1/2","fifty"
    if len(board.move_stack)>=600: return "1/2-1/2","cap"
    return None


async def play(exe,stage,directory,game,opening,fen0):
    dest=directory/f"g{game:04d}"
    dest.mkdir()
    white,black=("A","B") if game%2 else ("B","A")
    fen0 = " ".join(fen0.split()[:4]) + " 0 1"
    started=utc(); board=chess.Board(fen0); moves=[]; ply=0
    (dest/"opening.txt").write_text(f"{opening}\t{fen0}\n")
    with (dest/"wire.txt").open("x",encoding="ascii",errors="backslashreplace",buffering=1) as wire, (dest/"searches.tsv").open(
        "x",encoding="utf-8",newline="",buffering=1
    ) as out:
        profile = {1:"D1", 2:"D2"}[opening] if stage=="K29" else stage
        go_a, go_b = PROFILES[profile]
        engines = [Engine(exe, color, label, go_a if label=="A" else go_b, wire)
                   for color,label in (("W",white), ("B",black))]
        wr=csv.writer(out,delimiter="\t",lineterminator="\n"); wr.writerow(SEARCH_COLS)
        success=False
        try:
            # Sequential start avoids orphaning an in-flight second fork on an initialization failure.
            for proc in engines: await asyncio.wait_for(proc.start(),timeout=30)
            (dest/"engines.json").write_text(json.dumps({e.side:e.pid_identity for e in engines},indent=2)+"\n")
            final=end(board)
            while not final:
                ply=len(moves)+1; i=0 if board.turn else 1;proc=engines[i]
                position="position fen "+fen0+(" moves "+" ".join(moves) if moves else "")
                reply = await asyncio.wait_for(proc.search(position), timeout=120)
                move = reply[3]
                try: chosen=chess.Move.from_uci(move)
                except ValueError: raise ValueError(f"{proc.side} malformed bestmove {move!r}")
                if chosen not in board.legal_moves: raise ValueError(f"{proc.side} illegal bestmove {move} on {board.fen()}")
                wr.writerow([stage, game, ply, proc.label, proc.side, *reply])
                board.push(chosen)
                moves.append(move)
                final=end(board)
            result,ending=final
            answer=[stage,game,opening,white,black,result,ending,len(moves),started,utc()]
            with (dest/"result.tsv").open("x",newline="") as f:
                wr=csv.writer(f,delimiter="\t",lineterminator="\n")
                wr.writerow(GAME_COLS);wr.writerow(answer)
            success=True
            return answer
        except BaseException as error:
            with (dest/"interruption.txt").open("w",encoding="utf-8") as failure:
                print(utc(),stage,game,ply,repr(error),file=failure)
                for engine in engines:
                    print(engine.side,engine.label,"actual reply lines seen on last command",file=failure)
                    for line in engine.active_reply: print(line,file=failure)
            raise
        finally:
            await asyncio.gather(*(engine.close(success) for engine in engines))
