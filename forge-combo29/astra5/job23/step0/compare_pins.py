"""Compare Job 23 inputs and stdout with Job 22, excluding path, NPS, and elapsed time."""
from pathlib import Path
import argparse
import re
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("repo", type=Path)
p.add_argument("out", type=Path)
args=p.parse_args()
base="040834d:forge-combo29/astra5/job22/step0"

def normalized(text):
    body=text.split("\nINPUT\n",1)[1]
    body=re.sub(r'(?:/[^ \n]+/)+net768\.nnue', '<net768>', body)
    return re.sub(r' time \d+ nps \d+(?=\n)', ' time <time> nps <nps>', body)

for tag in ("r15d","kF"):
    pins=sorted(q for q in (args.out/tag).glob("*.txt") if q.name!="checks.txt")
    if len(pins)!=5:
        raise SystemExit(f"Expected five completed pins for {tag}, found {len(pins)}")
    for path in pins:
        source=subprocess.check_output(["git","-C",str(args.repo),"show",f"{base}/{tag}/{path.name}"],text=True)
        if normalized(source)!=normalized(path.read_text()):
            raise SystemExit(f"FAIL {tag}/{path.name}: normalized UCI input/stdout/stderr differs")
        print(f"{tag}/{path.name} matches Job 22 UCI input, stdout and stderr after normalization")
