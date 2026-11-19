"""Common formats and independent UCI decision, scoring, and board rules for Job 29."""
import csv,io,json,hashlib,math,re
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
import chess

BOOK_SHA="271cea0cd131935998b72aeee5e6bda336f8bea8f48bcf060088895f1765b21c"
NC_SHA="9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3"
OPTIONS = (
    'Threads 1|Hash 16|OwnBook false|MateAlphaGuard true|LmrQuietBase 93|'
    'LmrQuietDivisor 205|LmrNoisyBase 13|LmrNoisyDivisor 333|LmrHistoryDivisor 5643|'
    'NullMoveBase 5|LmpBase 8|HistoryPruneMultiplier 2220|HistoryBonusQuadratic 24|'
    'HistoryBonusLinear 54|HistoryBonusMax 2212|SingularDepth 6|IirDepth 2|'
    'NonPawnCorrection true|CuckooRep true|HistRework 2|TtPruneV2 true|CorrHistV2 true'
).split('|')
GO={"D1":("softnodes 4000","softnodes 2000"),"D2":("softnodes 2000","softnodes 1000"),"E":("nodes 4000","softnodes 2000"),
    "D3":("softnodes 8000","softnodes 4000"),"D4":("softnodes 1000","softnodes 500"),"C29":("softnodes 2000","softnodes 2000")}
THRESHOLDS=(300,500,800,1200,2000)
ARMS={"main":("D1","D2","E"),"optional":("D3","D4")}
def check(value,detail):
    if not value: raise ValueError(str(detail))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def utc(text):return datetime.fromisoformat(text.replace("Z","+00:00"))
def compact(path):
    if path.is_file():return path.read_bytes()
    receipt=table(path.with_name(path.name+".parts.tsv"));parts=[]
    for d in receipt:
        if d["kind"]=="part":
            raw=(path.parent/d["filename"]).read_bytes()
            check((len(raw),sha(raw))==(int(d["bytes"]),d["sha256"]),path);parts.append(raw)
    raw=b"".join(parts);whole=next(x for x in receipt if x["kind"]=="whole")
    check((len(raw),sha(raw))==(int(whole["bytes"]),whole["sha256"]),path);return raw
def table(path):return list(csv.DictReader(io.StringIO(compact(path).decode()),delimiter="	"))
def write_table(path,header,rows):
    with path.open("w",newline="") as f:
        w=csv.writer(f,delimiter="	",lineterminator="\n");w.writerow(header);w.writerows(rows)
def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(".tmp");tmp.write_text(json.dumps(data,indent=2)+"\n");tmp.replace(path)
def rule(board,moves):
    if board.is_checkmate():return "checkmate","0-1" if board.turn else "1-0"
    if board.is_stalemate():return "stalemate","1/2-1/2"
    if board.is_insufficient_material():return "insufficient","1/2-1/2"
    if board.can_claim_threefold_repetition():return "threefold","1/2-1/2"
    if board.can_claim_fifty_moves():return "fifty","1/2-1/2"
    if moves==600:return "cap","1/2-1/2"
    return None,None
def command(arm,opening,side):
    key=("D1" if opening==1 else "D2") if arm=="K29" else arm
    return "go "+GO[key][0 if side=="A" else 1]
def data_info(line):
    f=line.split()
    if f[:1]!=["info"] or "string" in f:return {}
    obs={}
    for k in ("depth","nodes"):
        if k in f:obs[k]=int(f[f.index(k)+1])
    if "score" in f:
        j=f.index("score");k=f[j+1];v=int(f[j+2]);check(k in ("cp","mate"),line);obs["score"]=f"{k} {v}"
    return obs
def scored(outcome,white):
    if outcome=="1/2-1/2":return 1
    return 2*int((white=="A")==(outcome=="1-0"))
def proc_options(x):return [" ".join(v) for v in x]
