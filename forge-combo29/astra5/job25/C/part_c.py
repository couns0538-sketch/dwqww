"""Launch one Job 25 fastchess tournament with its frozen opening seed and thread count."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
RUN = Path(os.environ.get("JOB25_RUN23", "/workspace/work/run23"))
BOOK = RUN / "job24work/book/astra5-general-openings24.epd"
FC = RUN / "job24work/fastchess/fastchess-linux-x86-64/fastchess"
NET = RUN / "net/net768.nnue"
PC20 = RUN / "job25work/step0/pc20.txt"
ENGINES = {name: RUN / f"builds/{name}-znver4/forge" for name in ("kF","r15d")}
DEADLINE = datetime.fromisoformat(os.environ.get("JOB25_CUTOFF", "2026-11-19T19:03:40+00:00")).timestamp()
FILES = {
    FC:"091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f",
    BOOK:"889e8db12ee327cae68b29ada3458a2fb957cf8f5563d29a7fd13d850ff3f638",
    NET:"c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7",
    ENGINES["kF"]:"c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb",
    ENGINES["r15d"]:"9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671",
}


def sha(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def command(plan, dest):
    opts=[]
    for line in PC20.read_text().splitlines():
        name,value=line.removeprefix("setoption name ").split(" value ")
        if name=="Threads": value=plan["threads"]
        opts.append(f"option.{name}={value}")
    if len(opts)!=22 or opts[1]!="option.Hash=16":
        raise ValueError("unexpected PC20")
    opts.extend([f"option.NNUEArchFile={NET}","option.NNUEArch=true"])
    args=[str(FC)]
    for name,exe in ENGINES.items():
        args.extend(["-engine",f"cmd={exe}",f"name={name}",*opts])
    return args+["-each","proto=uci","nodes=50000","-openings",f"file={BOOK}","format=epd","order=random",
                 "-srand",plan["seed"],"-rounds",plan["rounds"],"-games","2","-repeat",
                 "-concurrency",plan["concurrency"],"-recover","-pgnout","file="+str(dest/"games.pgn")]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part",choices=("C1","C2","C4"))
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args()
    with (HERE/"run-plan.tsv").open() as f:
        plan=next(row for row in csv.DictReader(f,delimiter="\t") if row["part"]==args.part)
    dest=HERE/args.part
    cmd=command(plan,dest)
    if args.preview:
        print(json.dumps(cmd,indent=2)); return
    digests={str(p):sha(p) for p in FILES}
    if not all(digests[str(path)]==expected for path,expected in FILES.items()):
        raise ValueError(f"file pin failed: {digests}")
    if time.time()>=DEADLINE-2: raise TimeoutError("past job deadline")
    dest.mkdir(exist_ok=False)
    (dest/"argv.json").write_text(json.dumps(cmd,indent=2)+"\n")
    (dest/"inputs.json").write_text(json.dumps(digests|{str(PC20):sha(PC20)},indent=2)+"\n")
    start=utc(); begin=time.monotonic(); before=resource.getrusage(resource.RUSAGE_CHILDREN); interrupted=False
    with tempfile.TemporaryDirectory() as cwd, (dest/"fastchess.log").open("xb") as log:
        with subprocess.Popen(cmd,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True) as proc:
            try:
                code=proc.wait(timeout=max(.05,DEADLINE-time.time()-2))
            except subprocess.TimeoutExpired:
                interrupted=True; proc.send_signal(signal.SIGINT)
                try: code=proc.wait(timeout=max(.05,DEADLINE-time.time()))
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    receipt=dict(part=args.part,start_utc=start,end_utc=utc(),elapsed_seconds=time.monotonic()-begin,
                 waited_child_user_seconds=after.ru_utime-before.ru_utime,
                 waited_child_system_seconds=after.ru_stime-before.ru_stime,
                 fastchess_pid=proc.pid,fastchess_returncode=code,cutoff_interruption=interrupted,
                 logfile_sha256=sha(dest/"fastchess.log"),pgn_sha256=sha(dest/"games.pgn") if (dest/"games.pgn").exists() else None)
    (dest/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt),flush=True)
    if code and not interrupted: raise RuntimeError("fastchess process failed")


if __name__=="__main__":
    main()
