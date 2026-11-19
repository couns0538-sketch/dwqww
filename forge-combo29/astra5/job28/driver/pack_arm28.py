"""Freeze a match arm as sorted flat text, including partial games separately."""
import csv
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

from game28 import GAME_COLS, SEARCH_COLS


def sha(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()


def save_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix="."+path.name+".",suffix=".tmp")
    with os.fdopen(fd,"w") as f:
        json.dump(obj,f,indent=2); f.write("\n");f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def split(path):
    if path.stat().st_size<=20_000_000: return
    expected=sha(path); combined=hashlib.sha256()
    with path.open("rb") as f,(path.parent/(path.name+".parts.tsv")).open("x") as mf:
        print("kind\tfilename\tbytes\tsha256",file=mf)
        index=0; block=bytearray()
        def flush():
            nonlocal index
            index+=1
            part=path.with_name(f"{path.stem}.part{index:04}{path.suffix}")
            part.write_bytes(block);combined.update(part.read_bytes())
            print("part",part.name,len(block),sha(part),sep="\t",file=mf);block.clear()
        for line in f:
            if block and len(line)+len(block)>15_000_000: flush()
            block.extend(line)
        if block: flush()
        print("whole",path.name,path.stat().st_size,expected,sep="\t",file=mf)
    if combined.hexdigest()!=expected: raise ValueError(f"{path.name}: split hash mismatch")
    path.unlink()


def sample_wire(wire,dest,game):
    """Store the actual first search, last search and first hold-bearing search of the sample game."""
    group=[];first=None;last=None;hold=None;search_no=0
    with wire.open(errors="replace") as f:
        for ln,text in enumerate(f,1):
            if " > position fen " in text:
                group=[(ln,text)]
            elif group:
                group.append((ln,text))
                if " < bestmove " in text:
                    search_no+=1
                    record=(search_no,group)
                    if first is None: first=record
                    last=record
                    if hold is None and any(" < info string TmFinishIteration hold" in s for _,s in group):
                        hold=record
                    group=[]
    used=set()
    for kind,item in (("first search",first),("first hold",hold),("last search",last)):
        if item is None or item[0] in used: continue
        used.add(item[0]);print(f"game {game} ply {item[0]} ({kind})",file=dest)
        for line,text in item[1]: dest.write(f"g{game:04}/wire.txt:{line} {text}")
        dest.write("\n")


def pack_arm(live,out,block,stage,lo,hi,hard,reason):
    """Read write-closed game files within the named opening range; publish via one atomic rename."""
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(dir=out.parent,prefix="."+out.name+"."))
    done=[];started=[];incomplete=[];searches=plies=pending=0; options={};parents=set()
    with ExitStack() as stack:
        def table(name,columns):
            f=stack.enter_context((temp/name).open("x",newline=""))
            w=csv.writer(f,delimiter="\t",lineterminator="\n")
            w.writerow(columns)
            return w
        games=table("games.tsv",GAME_COLS); records=table("searches.tsv",SEARCH_COLS)
        other=table("unfinished-searches.tsv",SEARCH_COLS)
        openings=table("openings.tsv",["opening","fen"])
        engines=table("engines.tsv",["game","color","role","pid","start_ticks","started_utc","option_profile"])
        wirehash=table("wire-sha256.tsv",["game","bytes","sha256"])
        samples=stack.enter_context((temp/"wire-samples.txt").open("x"))
        faults=stack.enter_context((temp/"interruptions.txt").open("x"))
        saved_openings={}
        for gid in range(2*lo-1,2*hi+1):
            g=live/f"g{gid:04d}"
            if not g.is_dir():continue
            started.append(gid)
            if (g/"opening.txt").exists():
                k,fen=(g/"opening.txt").read_text().strip().split("\t",1)
                if int(k)!=(gid+1)//2: raise ValueError("wrong opening ID")
                if saved_openings.setdefault(k,fen)!=fen: raise ValueError("color pair opening mismatch")
            if (g/"engines.json").exists():
                pids=json.loads((g/"engines.json").read_text())
                for color,e in pids.items():
                    profile=e["role"]
                    if (e["pid"],e["start_ticks"]) in parents: raise ValueError("reused process identity")
                    parents.add((e["pid"],e["start_ticks"]))
                    if options.setdefault(profile,e["options"])!=e["options"]: raise ValueError("options differ by game")
                    engines.writerow([gid,color,profile,e["pid"],e["start_ticks"],e["started_utc"],profile])
            receipt=g/"result.tsv"
            result=None
            if receipt.exists():
                with receipt.open() as f: result=next(csv.DictReader(f,delimiter="\t"))
                if datetime.fromisoformat(result["ended_utc"]).timestamp()>hard: result=None
            if result:
                if int(result["game"])!=gid: raise ValueError("bad game result ID")
                games.writerow([result[c] for c in GAME_COLS]);done.append(gid);plies+=int(result["plies"])
            else: incomplete.append(gid)
            n=0
            sf=g/"searches.tsv"
            if sf.is_file():
                with sf.open() as f:
                    r=csv.DictReader(f,delimiter="\t")
                    if r.fieldnames!=SEARCH_COLS: raise ValueError(f"{sf}: unexpected header")
                    for n,row in enumerate(r,1):
                        if int(row["game"])!=gid or int(row["ply"])!=n: raise ValueError(f"{sf}: nonsequential records")
                        (records if result else other).writerow([row[c] for c in SEARCH_COLS])
            if result:
                if n!=int(result["plies"])+(result["ending"]=="time"):raise ValueError(f"{sf}: search count")
                searches+=n
            else:pending+=n
            wf=g/"wire.txt"
            if wf.is_file():
                wirehash.writerow([gid,wf.stat().st_size,sha(wf)])
                if gid==2*lo-1 or (result and result["ending"]=="time"):sample_wire(wf,samples,gid)
            fault=g/"interruption.txt"
            if fault.exists():
                faults.write(f"game {gid}\n"+fault.read_text()+"\n")
        for k,fen in saved_openings.items():openings.writerow([k,fen])
    (temp/"option-profiles.json").write_text(json.dumps(options,indent=2)+"\n")
    for path in list(temp.iterdir()): split(path)
    manifest={}
    for p in sorted(temp.iterdir()): manifest[p.name]={"bytes":p.stat().st_size,"sha256":sha(p)}
    expected=list(range(2*lo-1,2*hi+1))
    receipt={"block":block,"stage":stage,"opening_first":lo,"opening_last":hi,"reason":reason,
             "complete":done==expected,"started_games":len(started),"finished_games":len(done),
             "finished_game_ids":done,"unfinished_game_ids":incomplete,"not_started_game_ids":[i for i in expected if i not in started],
             "finished_pairs":sum(2*i-1 in done and 2*i in done for i in range(lo,hi+1)),
             "plies":plies,"searches":searches,"unfinished_searches":pending,"files":manifest,
             "frozen_utc":datetime.now(timezone.utc).isoformat(timespec="milliseconds")}
    save_json(temp/"receipt.json",receipt)
    os.rename(temp,out)
    return receipt
