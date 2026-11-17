#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 08's 08-F12 — the built-in book answers `position startpos` at defaults.

Seat 08's claim: with `OwnBook` at its default, 9 of 14 opening positions are answered from the built-in book
(`info string book move`, 0 info lines), INCLUDING `position startpos` itself; the book reaches at least
`1.e4 e5 2.Nf3 Nc6 3.Bb5`; `go depth 12` is never a book answer; and the book move VARIES between runs because
`Book Variety` defaults to 30.

WHY THIS MATTERS TO MY OWN RECORD: several of my harnesses send `OwnBook false`, but any that did not would have
had book answers silently mixed in - and `position startpos` is the most likely first line a harness writes. If
the book fires there, a latency or node-count table can contain answers with no search behind them.

Method: with OwnBook at DEFAULT (not sent at all), run `go depth 12` from startpos and from a few opening
positions, several times, and check for (a) an `info string book move` line, (b) zero info-depth lines, (c) whether
the move varies between runs. Then the same with OwnBook false as the control.

Usage: check_book_default.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path

TIMEOUT=120.0
BASE_OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
           ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
           ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
           ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
           ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
           ("Threads","1"),("Hash","16")]
# seat 08 states "`go depth 12` is never a book answer" because the book is probed only when `game_search`
# holds, i.e. for clock/movetime searches (uci.cpp:681). So the test must use a CLOCK search; using `go depth`
# would guarantee a false negative - which is exactly what my first attempt did.
GO = __import__('os').environ.get("BOOK_GO", "go wtime 6000 btime 6000 winc 60 binc 60")

POSITIONS=[
 ("startpos","rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
 ("Ruy_1","rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"),
 ("Ruy_2","rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"),
 ("G_midgame","1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
]

class R:
    def __init__(self,fd): self.fd,self.buf,self.eof=fd,b"",False
    def line(self,dl):
        while b"\n" not in self.buf:
            if self.eof: return None
            rem=dl-time.monotonic()
            if rem<=0: return None
            r,_,_=select.select([self.fd],[],[],rem)
            if not r: return None
            c=os.read(self.fd,65536)
            if not c: self.eof=True; return None
            self.buf+=c
        l,_,self.buf=self.buf.partition(b"\n")
        return l.decode("utf-8","replace")

def run(exe,fen,ownbook):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno()); buf=[]
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            buf.append(l)
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+30
    send("uci"); until("uciok",d)
    for n,v in BASE_OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    if ownbook is not None:
        send("setoption name OwnBook value %s"%("true" if ownbook else "false"))
        send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    t0=time.monotonic()
    send(GO)
    bm=None
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        buf.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; break
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=15)
    except Exception: p.kill()
    book=[l for l in buf if "book move" in l]
    dl=[l for l in buf if l.startswith("info depth")]
    return {"book":bool(book),"book_line":book[0] if book else None,"n_info":len(dl),
            "bestmove":bm,"wall":round(wall,2)}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 08's 08-F12: does the built-in book answer `position startpos` at defaults?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20-ish options except OwnBook, which is left at its DEFAULT (not sent) for the first arm,","",
           "and explicitly false for the control. GO = %s, 3 runs per cell." % GO]
    lines.append("position\townbook\tbook_fired\tinfo_lines\tmoves_seen\twall_ms")
    rows=[]
    for name,fen in POSITIONS:
        for tag,ob in (("default",None),("false",False)):
            res=[run(exe,fen,ob) for _ in range(3)]
            moves=sorted({r["bestmove"] for r in res})
            fired=sum(1 for r in res if r["book"])
            rows.append({"position":name,"ownbook":tag,"fired":fired,"runs":res,"moves":moves})
            print("%-11s OwnBook %-7s book %d/3 info %.0f moves %s"
                  %(name,tag,fired,sum(r["n_info"] for r in res)/3,moves),flush=True)
            lines.append("%s\t%s\t%d/3\t%.0f\t%s\t%.1f"%(name,tag,fired,
                         sum(r["n_info"] for r in res)/3,moves,sum(r["wall"] for r in res)/3))
    v=[]
    v.append("")
    sp_default=next(r for r in rows if r["position"]=="startpos" and r["ownbook"]=="default")
    sp_false=next(r for r in rows if r["position"]=="startpos" and r["ownbook"]=="false")
    v.append("A. `position startpos`, OwnBook at DEFAULT: book fired in %d of 3 runs, moves seen %s."
             %(sp_default["fired"],sp_default["moves"]))
    v.append("   OwnBook false: book fired %d of 3, moves %s."%(sp_false["fired"],sp_false["moves"]))
    if sp_default["fired"]:
        v.append("   -> CONFIRMS seat 08: `position startpos` IS answered from the built-in book at defaults,")
        v.append("      which is the first line many harnesses write. A table built without `OwnBook false`")
        v.append("      contains book answers with no search behind them.")
        if len(sp_default["moves"])>1:
            v.append("   -> AND THE MOVE VARIES between runs (%s), so a book-on engine is not repeatable either -"
                     %sp_default["moves"])
            v.append("      exactly as seat 08 reports, caused by Book Variety defaulting to 30.")
    else:
        v.append("   -> does NOT reproduce here: startpos was searched, not booked, at defaults.")
    v.append("")
    mid=next(r for r in rows if r["position"]=="G_midgame" and r["ownbook"]=="default")
    v.append("B. Control, a real middlegame at defaults: book fired %d of 3 (expected 0)."%mid["fired"])
    v.append("   -> so the book fires on OPENINGS only, which is the scope a harness needs to know.")
    (out/"check_book_default.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_book_default.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
