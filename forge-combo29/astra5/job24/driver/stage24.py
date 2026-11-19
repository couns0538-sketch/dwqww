"""Replay a job 24 stage with one fresh fastchess invocation per pair set."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
LAB = Path(os.getenv("JOB24_WORK", "/workspace/work/run23/job24work"))
RUN23 = LAB.parent
FC = Path(os.getenv("JOB24_FASTCHESS", LAB/"fastchess/fastchess-linux-x86-64/fastchess"))
PAIRSETS = Path(os.getenv("JOB24_PAIRS", LAB/"pairs/pairsets.tsv"))
BOOK = Path(os.getenv("JOB24_BOOK", LAB/"book/astra5-general-openings24.epd"))
PC20 = Path(os.getenv("JOB24_PC20", LAB/"step0/pc20.txt"))
NET = Path(os.getenv("JOB24_NET", RUN23/"net/net768.nnue"))
RESULTS = Path(os.getenv("JOB24_RESULTS", ROOT/"results"))
DEADLINE = datetime.fromisoformat(os.environ.get("JOB24_DEADLINE","2026-11-19T18:11:17+00:00")).timestamp()
BUILDS = {
    "r15d":(Path(os.getenv("JOB24_R15D",RUN23/"builds/r15d-znver4/forge")),
            "9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671"),
    "kF":(Path(os.getenv("JOB24_KF",RUN23/"builds/kF-znver4/forge")),
          "c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb"),
}
SCORE = re.compile(r'Games:\s*(\d+),\s*Wins:\s*(\d+),\s*Losses:\s*(\d+),\s*Draws:\s*(\d+)')
HEADERS = ["j","status","games","wins","losses","draws","returncode","start_utc","end_utc","pgn_sha256","log_sha256"]


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()


def read_options():
    fixed=[]
    for line in PC20.read_text().splitlines():
        m=re.fullmatch(r'setoption name (\S+) value (\S+)',line)
        if not m: raise ValueError(f"invalid PC20: {line}")
        fixed.append(f"option.{m[1]}={m[2]}")
    if len(fixed)!=22 or fixed[:2]!=["option.Threads=1","option.Hash=16"]:
        raise ValueError("unexpected PC20 settings")
    fixed=fixed[2:] + ["option.NNUEArchFile="+str(NET),"option.NNUEArch=true"]
    with PAIRSETS.open() as f:
        reader=csv.DictReader(f,delimiter="\t")
        header=reader.fieldnames
        if len(header)!=81 or header[0]!="j": raise ValueError("invalid pair-vector header")
        names=[s.removeprefix("plus_") for s in header[1:41]]
        if header[1:41]!=["plus_"+n for n in names] or header[41:]!=["minus_"+n for n in names]:
            raise ValueError("pair-vector names differ")
        rows=list(reader)
    if [int(r["j"]) for r in rows]!=list(range(1,81)): raise ValueError("incorrect pair IDs")
    return fixed,names,rows


def command(exe,stage,row,names,fixed,pgn):
    j=int(row["j"])
    args=[str(FC)]
    for color in ("plus","minus"):
        args.extend(["-engine","cmd="+str(exe),"name="+color,*fixed])
        args.extend(f"option.{name}={int(row[color+'_'+name])}" for name in names)
        if stage=="C24" and color=="plus": args.append("option.LmrQuietBase=60")
    return args+["-each","proto=uci","nodes=20000","option.Threads=1","option.Hash=16",
                 "option.OwnBook=false","-openings","file="+str(BOOK),"format=epd","order=random",
                 "-srand",str(2400000+j),"-rounds","8","-games","2","-repeat","-concurrency","8",
                 "-force-concurrency","-recover","-pgnout","file="+str(pgn)]


def freeze_inputs(exe,expected,dest):
    inputs={"fastchess":FC,"engine":exe,"net":NET,"book":BOOK,"pairsets":PAIRSETS,"fixed":PC20}
    hashes={name:sha(path) for name,path in inputs.items()}
    if hashes["engine"]!=expected or hashes["net"]!="c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7":
        raise ValueError("engine/net digest mismatch")
    if hashes["fastchess"]!="091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f":
        raise ValueError("fastchess digest mismatch")
    with (dest/"inputs.tsv").open("x") as out:
        print("name\tsha256\tpath",file=out)
        for name,path in inputs.items(): print(name,hashes[name],str(path),sep="\t",file=out)


def run(stage,preview):
    build="kF" if stage=="K1" else "r15d"
    exe,expected=BUILDS[build]
    fixed,names,rows=read_options()
    dest=(RESULTS/stage).resolve()
    if preview:
        print(json.dumps(command(exe,stage,rows[0],names,fixed,dest/"j001.pgn"),indent=2))
        return
    dest.mkdir(parents=True,exist_ok=False)
    freeze_inputs(exe,expected,dest)
    if stage=="C24": rows=rows[:1]
    with (dest/"stage.tsv").open("x",buffering=1) as overview:
        summary=csv.writer(overview,delimiter="\t",lineterminator="\n")
        summary.writerow(HEADERS)
        for row in rows:
            remaining=DEADLINE-time.time()
            if remaining<=2: break
            j=int(row["j"])
            base=dest/f"j{j:03d}"
            pgn=base.with_suffix(".pgn")
            log=base.with_suffix(".log")
            commandline=command(exe,stage,row,names,fixed,pgn)
            base.with_suffix(".command.json").write_text(json.dumps(commandline,indent=2)+"\n")
            start=utc()
            deadline_hit=False
            with tempfile.TemporaryDirectory(prefix="fc-") as cwd, log.open("xb") as output:
                with subprocess.Popen(commandline,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,
                                      start_new_session=True) as process:
                    try:
                        rc=process.wait(timeout=max(.05,DEADLINE-time.time()-2))
                    except subprocess.TimeoutExpired:
                        deadline_hit=True
                        process.send_signal(signal.SIGINT)
                        try:
                            rc=process.wait(timeout=max(.05,DEADLINE-time.time()))
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid,signal.SIGKILL)
                            rc=process.wait()
            end=utc()
            lines=log.read_text(errors="replace").splitlines()
            scores=[match.groups() for line in lines if (match:=SCORE.search(line))]
            n,w,l,d=map(int,scores[-1]) if scores else (0,0,0,0)
            games=sum(1 for line in pgn.open(errors="replace") if line.startswith("[Result ")) if pgn.exists() else 0
            complete=rc==0 and n==games==16 and w+l+d==16
            status="complete" if complete else ("deadline" if deadline_hit else "failed")
            receipt=[j,status,games,w,l,d,rc,start,end,sha(pgn) if pgn.exists() else "absent",sha(log)]
            with base.with_suffix(".receipt.txt").open("x") as f:
                print("field\tvalue",file=f)
                for name,value in zip(HEADERS,receipt): print(name,value,sep="\t",file=f)
                print("printed_wld_games",n,sep="\t",file=f)
            summary.writerow(receipt)
            print(stage,j,status,"games",games,"score",w,l,d,"end",end,flush=True)
            if not complete:
                if deadline_hit: break
                raise RuntimeError(f"fastchess set {j} failed; see {log}")
    with (dest/"end.txt").open("x") as f:
        print("written_utc",utc(),file=f)
        print("deadline_utc",datetime.fromtimestamp(DEADLINE,timezone.utc).isoformat(),file=f)
        print("requested_sets",len(rows),file=f)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("R1","R2","C24","K1"))
    parser.add_argument("--preview",action="store_true",help="Print pair-set 1 arguments; no match is started")
    args=parser.parse_args()
    run(args.stage,args.preview)
