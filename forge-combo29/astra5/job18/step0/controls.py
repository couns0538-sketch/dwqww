"""Run one fresh unguarded Forge process per job 18 Step 0 control and capture both sides of UCI."""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("engine",type=Path)
    p.add_argument("label",choices=("r15d","kF"))
    p.add_argument("out",type=Path)
    p.add_argument("settings",type=Path)
    p.add_argument("net",type=Path)
    args=p.parse_args()
    exe=args.engine.resolve(strict=True)
    net=args.net.resolve(strict=True)
    out=args.out/args.label
    out.mkdir(exist_ok=True)
    presets=args.settings.read_text().splitlines()
    assert len(presets)==22 and len(set(presets))==22
    assert presets[:2]==["setoption name Threads value 1","setoption name Hash value 16"]
    assert not any("NullMateGuard" in line or "NNUEArch" in line for line in presets)
    net_opts=[f"setoption name NNUEArchFile value {net}","setoption name NNUEArch value true"]
    net_sha=digest(net)
    assert net_sha=="c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7"
    engine_sha=digest(exe)
    specs=[
        ("defaults","bench 11",312866),("defaults","bench 13",862329),("defaults","go perft 5",4865609),
        ("PC20-net768","bench 11",882074),("PC20-net768","bench 13",4275906),
    ]
    with (out/"checks.txt").open("x") as f:
        print(f"engine {exe}\nengine_sha256 {engine_sha}\nnet {net}\nnet_sha256 {net_sha}",file=f,flush=True)
        for preset, command, expected in specs:
            options = [] if preset=="defaults" else list(presets)
            is_net=preset=="PC20-net768"
            if is_net:
                options.extend(net_opts)
            body="\n".join(options+["isready",command,"quit"])+"\n"
            start=subprocess.check_output(["date","-u","+%Y-%m-%dT%H:%M:%SZ"],text=True).strip()
            proc=subprocess.run([exe],cwd=exe.parent,input=body,text=True,capture_output=True,timeout=60)
            end=subprocess.check_output(["date","-u","+%Y-%m-%dT%H:%M:%SZ"],text=True).strip()
            path=out/(preset+"-"+command.replace(" ","-")+".txt")
            path.write_text(f"started {start}\nfinished {end}\nengine {exe}\nengine_sha256 {engine_sha}\n"
                            f"returncode {proc.returncode}\nINPUT\n{body}STDOUT\n{proc.stdout}STDERR\n{proc.stderr}")
            lines=proc.stdout.splitlines()
            nodes=re.findall(r"\bnodes (\d+)\b",proc.stdout)
            valid=(proc.returncode==0 and not proc.stderr and lines.count("readyok")==1
                   and nodes==[str(expected)] and
                   not re.search(r"unknown option|invalid value|\bERROR\b",proc.stdout,re.IGNORECASE))
            markers=[line for line in lines if line.startswith("info string NNUE v3")]
            if is_net:
                valid=valid and len(markers)==2 and markers[0].startswith("info string NNUE v3 loaded:") and markers[1].startswith("info string NNUE v3 active:")
                valid=valid and all(" checksum 30ab43b4ba5db5f3 " in line for line in markers)
                if markers:
                    print("\n".join(markers),file=f)
            else:
                valid=valid and not markers
            record=f"{args.label} {preset} {command} | expected {expected} | observed {nodes} | {'PASS' if valid else 'FAIL'}"
            print(record,file=f,flush=True)
            print(record,flush=True)
            if not valid:
                raise SystemExit(1)


if __name__=="__main__":
    main()
