#!/usr/bin/env python3
"""check_07f1.py OUTDIR -- seat 10's OWN harness for seat 07's 07-F1.
Claim: position startpos + `go depth N searchmoves <no legal root move>` answers a fabricated report
(one `info depth D ... score cp 0 nodes 0` per depth, then `bestmove 0000`) on BASE and on PC r15/PC20.
Threads 1, Hash 16, OwnBook false. One fresh process per case; read to bestmove (EOF-safe)."""
import json, os, subprocess, sys
import chess
BASE=os.path.expanduser("~/builds/release/forge"); PC=os.path.expanduser("~/builds/pc/forge")
OUT=os.path.abspath(sys.argv[1]); os.makedirs(OUT,exist_ok=True)
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
     ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
     ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
     ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
          ("MateAlphaGuard","true"),("OwnBook","false")]
def one(exe,regime,cmd):
    lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
    lines+=["setoption name %s value %s"%kv for kv in (S14 if regime=="s14" else PC20)]
    lines+=["isready","ucinewgame","isready","position startpos","isready",cmd]
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    for l in lines: p.stdin.write(l+"\n"); p.stdin.flush()
    out=[]
    while True:
        line=p.stdout.readline()
        if not line: break
        out.append(line.rstrip())
        if line.startswith("bestmove"): break
    p.stdin.write("quit\n")
    try: p.stdin.flush()
    except Exception: pass
    try: p.wait(timeout=60)
    except Exception: p.kill()
    info=[l for l in out if l.startswith("info depth")]
    depthlines=[]
    for l in info:
        try: depthlines.append(int(l.split("depth ")[1].split()[0]))
        except Exception: pass
    nodes=[]
    for l in info:
        if " nodes " in l:
            try: nodes.append(int(l.split(" nodes ")[1].split()[0]))
            except Exception: pass
    scores=[l for l in info if " score cp 0 " in l]
    istr=[l for l in out if "info string" in l]
    bm=[l.split()[1] for l in out if l.startswith("bestmove")]
    return {"cmd":cmd,"info_depth_lines":len(info),"depths":depthlines,
            "all_nodes_zero":(all(n==0 for n in nodes) if nodes else None),
            "lines_scoring_cp0":len(scores),"info_strings":istr,
            "bestmove":bm[0] if bm else None}
cases={"searchmoves_illegal_move":"go depth 8 searchmoves a1a1",
       "searchmoves_no_move":"go depth 8 searchmoves",
       "searchmoves_legal_CONTROL":"go depth 8 searchmoves e2e4"}
res={}
for bname,exe,reg in (("base_s14",BASE,"s14"),("pc20",PC,"pc20")):
    res[bname]={c:one(exe,reg,cmd) for c,cmd in cases.items()}
    for c,v in res[bname].items():
        print(bname,c,"->",{k:v[k] for k in ("info_depth_lines","all_nodes_zero","lines_scoring_cp0","bestmove")},flush=True)
res["startpos_legal_moves_python"]=chess.Board().legal_moves.count()
json.dump(res,open(os.path.join(OUT,"check_07f1.json"),"w"),indent=2)
