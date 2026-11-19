"""Independently compare literal records over a caller-specified range of complete games."""
import argparse
import csv
from hashlib import sha256
from itertools import zip_longest
from pathlib import Path
import re
import sys

RECORD = re.compile(rb"(\d+) (\d+) ([a-h][1-8][a-h][1-8][nbrq]?) (NA|\d+)\n")


def records_bytes(arm):
    manifest = arm / "records-manifest.tsv"
    if not manifest.exists():
        return (arm / "records.txt").read_bytes()
    with manifest.open(newline="") as f:
        parts = list(csv.DictReader(f, delimiter="\t"))
    payloads = []
    for i, item in enumerate(parts):
        whole = i == len(parts) - 1
        if item["kind"] != ("whole" if whole else "part"):
            raise ValueError(f"{manifest}: invalid manifest order")
        payload = b"".join(payloads) if whole else (arm / item["file"]).read_bytes()
        if (len(payload),payload.count(b'\n'),sha256(payload).hexdigest()) != (
            int(item["bytes"]),int(item["rows"]),item["sha256"]
        ):
            raise ValueError(f"{manifest}: manifest mismatch: {item['file']}")
        if whole:
            return payload
        payloads.append(payload)
    raise ValueError(f"{manifest}: empty manifest")


def read(arm, first, last, prefix):
    data = records_bytes(arm)
    groups = {}
    numbers = dict(games=0, records=0, na=0, nodes=0)
    pid = None
    end = 0
    with (arm / "games.tsv").open("rb") as fp:
        header = fp.readline().rstrip(b"\r\n").decode("ascii").split("\t")
        for gid in range(first, last+1):
            line = fp.readline()
            if not line.endswith(b"\n"):
                raise ValueError(f"{arm}: game {gid} has no complete receipt")
            fields = line[:-1].decode("ascii").rstrip("\r").split("\t")
            receipt = dict(zip(header,fields,strict=True))
            if int(receipt["book_line"]) != gid or not receipt["end_utc"]:
                raise ValueError(f"{arm}: missing or out-of-order game {gid}")
            if pid is None:
                pid = receipt["p1_pid"]
            if not pid or receipt["p1_pid"] != pid or receipt["p2_pid"] != pid:
                raise ValueError(f"{arm}: engine PID differs in game {gid}")
            n, offset = int(receipt["plies"]), int(receipt["record_bytes"])
            if not (0 <= n <= 292 and end <= offset <= len(data)):
                raise ValueError(f"{arm}: game {gid} has invalid length or offset")
            group = data[end:offset]
            rows = group.splitlines(keepends=True)
            if len(rows) != n:
                raise ValueError(f"{arm}: wrong number of records in game {gid}")
            missing = nodes = 0
            for ply, raw in enumerate(rows,8):
                m = RECORD.fullmatch(raw)
                if m is None or m[1] != str(gid).encode() or m[2] != str(ply).encode():
                    raise ValueError(f"{arm}: bad game/ply/format at {gid} {ply}: {raw!r}")
                if m[4] == b"NA":
                    missing += 1
                else:
                    nodes += int(m[4])
            if (missing,nodes) != (int(receipt["na"]),int(receipt["nodes"])):
                raise ValueError(f"{arm}: wrong NA total or node sum for game {gid}")
            groups[gid] = group
            numbers["games"] += 1
            numbers["records"] += n
            numbers["na"] += missing
            numbers["nodes"] += nodes
            end = offset
        if not prefix and (fp.read(1) or end != len(data)):
            raise ValueError(f"{arm}: data beyond requested end; use explicit --prefix for intentional slicing")
    numbers["bytes"] = end
    numbers["sha256"] = sha256(data[:end]).hexdigest()
    return groups, numbers


def main():
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("left", type=Path)
    arg.add_argument("right", type=Path)
    arg.add_argument("last", type=int, help="last fully receipted game number, included")
    arg.add_argument("--first", type=int, default=700001)
    arg.add_argument("--prefix", choices=("left","right","both"), help="permit trailing games only on these sides")
    a = arg.parse_args()
    if a.last < a.first:
        arg.error("last must be at least first")
    L,lstats = read(a.left,a.first,a.last,a.prefix in ("left","both"))
    R,rstats = read(a.right,a.first,a.last,a.prefix in ("right","both"))
    for name,stats in [("left",lstats),("right",rstats)]:
        print(name, *(f"{k}={v}" for k,v in stats.items()))
    differs = [g for g in L if L[g] != R[g]]
    print("games_differ",len(differs),"reading", "DIFFERS" if differs else "IDENTICAL")
    if differs:
        g = differs[0]
        for p,(x,y) in enumerate(zip_longest(L[g].splitlines(keepends=True),R[g].splitlines(keepends=True)),8):
            if x != y:
                print("first_game",g,"first_ply",p)
                print("left",x.decode("ascii").rstrip("\n") if x is not None else "[end of game]")
                print("right",y.decode("ascii").rstrip("\n") if y is not None else "[end of game]")
                break


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as e:
        sys.exit(str(e))
