"""Play one 6000+60 node-time game, with a fresh process for each color."""
import asyncio
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

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
SEARCH_COLS = "game ply side engine N used clock_before clock_after bestmove holds wtime btime soft_line move_line".split()
GAME_COLS = "game opening white black result ending plies wclock bclock started_utc ended_utc".split()
REFUSAL=re.compile("unknown option|invalid value|ERROR",re.IGNORECASE)
NODE_LINE=re.compile(r"info string softnodes nodes (\d+)$")
HOLD="info string TmFinishIteration hold"


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Engine:
    def __init__(self, exe, side, label, stage, wire, dest):
        self.exe=exe; self.side=side; self.label=label; self.wire=wire; self.dest=dest
        self.options=[*BASE,("NodeClock","2000" if stage=="C26" and label=="A" else "1000"),
                      ("TmFinishIteration","true" if label=="A" else "false")]
        self.proc=None; self.active_reply=[]; self.pid_identity={}

    def note(self, event, line):
        self.wire.write(f"{self.side} {event} {line}\n")

    async def send(self, cmd):
        self.note(">",cmd)
        self.proc.stdin.write((cmd+"\n").encode("ascii"))
        await self.proc.stdin.drain()

    async def line(self, full=False):
        raw=await self.proc.stdout.readline()
        if not raw: raise RuntimeError(f"{self.side} engine closed its UCI pipe")
        line=raw.decode("utf-8",errors="replace").rstrip("\r\n")
        self.active_reply.append(line)
        if full or line.startswith(("bestmove ",HOLD,"info string softnodes nodes ")) or REFUSAL.search(line):
            self.note("<",line)
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
            line=await self.line(full=True)
            if line=="uciok": break
            if line.startswith("id "): ids.append(line)
            m=re.match(r"option name (.+?) type ",line)
            if m: names.add(m[1])
        for name,value in self.options:
            if name not in names: raise RuntimeError(self.side+" missing option "+name)
            await self.send(f"setoption name {name} value {value}")
        await self.send("ucinewgame")
        await self.send("isready")
        while await self.line(full=True)!="readyok": pass
        st=Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()[19]
        self.pid_identity=dict(pid=pid,start_ticks=st,started_utc=started,exe=str(self.exe),
                               id=ids,role=self.label,options=self.options)
        self.active_reply=[]

    async def search(self, position, go):
        self.active_reply=[]
        await self.send(position)
        await self.send(go)
        stopped=[];holds=0
        while True:
            line=await self.line()
            if m:=NODE_LINE.fullmatch(line): stopped.append((int(m[1]),line))
            holds+=line.startswith(HOLD)
            if line.startswith("bestmove "):
                if len(stopped)!=1: raise ValueError(f"{self.side} expected one final N, got {len(stopped)}")
                return stopped[0][0],stopped[0][1],line.split()[1],line,holds

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
    started=utc(); board=chess.Board(fen0); moves=[]; clocks=[6000,6000]; ply=0
    (dest/"opening.txt").write_text(f"{opening}\t{fen0}\n")
    with (dest/"wire.txt").open("x",encoding="ascii",errors="backslashreplace",buffering=1) as wire, (dest/"searches.tsv").open(
        "x",encoding="utf-8",newline="",buffering=1
    ) as out:
        engines=[Engine(exe,s,l,stage,wire,dest) for s,l in (("W",white),("B",black))]
        wr=csv.writer(out,delimiter="\t",lineterminator="\n"); wr.writerow(SEARCH_COLS)
        success=False
        try:
            # Sequential start avoids orphaning an in-flight second fork on an initialization failure.
            for proc in engines: await asyncio.wait_for(proc.start(),timeout=30)
            (dest/"engines.json").write_text(json.dumps({e.side:e.pid_identity for e in engines},indent=2)+"\n")
            final=end(board)
            while not final:
                ply=len(moves)+1; i=0 if board.turn else 1;proc=engines[i]
                position="position fen "+fen0+" moves"+(" "+" ".join(moves) if moves else "")
                go=f"go wtime {clocks[0]} btime {clocks[1]} winc 60 binc 60"
                n,sof,move,ml,holds=await asyncio.wait_for(proc.search(position,go),timeout=120)
                try: chosen=chess.Move.from_uci(move)
                except ValueError: raise ValueError(f"{proc.side} malformed bestmove {move!r}")
                if chosen not in board.legal_moves: raise ValueError(f"{proc.side} illegal bestmove {move} on {board.fen()}")
                used=n//1000; before=clocks[i]; loss=used>before
                after=before if loss else before-used+60
                wr.writerow([game,ply,proc.side,proc.label,n,used,before,after,move,holds,*clocks,sof,ml])
                if loss:
                    final=("0-1" if i==0 else "1-0","time")
                else:
                    clocks[i]=after; board.push(chosen); moves.append(move);final=end(board)
            result,ending=final
            answer=[game,opening,white,black,result,ending,len(moves),*clocks,started,utc()]
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
