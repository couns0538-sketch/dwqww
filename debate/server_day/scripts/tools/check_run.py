"""Fable 2026-11-23, W5 of FINAL_PLAN_2311.md: read a transcript of tools/drive.py and compare what the engine
answered with known answers. Standard library only: the same file runs on the PC and on Linux.

    check_run.py <transcript> show                     print the summary (json)
    check_run.py <transcript> write <new known.json>   keep the summary as known answers; refused unless the run
                                                       ended cleanly and holds no refusal line
    check_run.py <transcript> known <known.json>       exit 0 only if EVERY compared field equals the known answers
                                                       and the run is clean; every difference is printed

What is read (in the engine's own order):
  bench      [depth, nodes] of every `info string bench` line
  perft      [position command, depth, nodes] of every `go perft`
  eval       [hce, nnue, total] of every `info string eval` line
  net        of every `info string NNUE v3 active:` line: hidden, king_buckets, checksum (the path and the kernel
             name are machine and build facts: kept in the summary as `net_kernel`, never compared)
  search     of every `go` that is not a perft: [depth, nodes, hashfull of the last info line that has all three,
             bestmove]
  games      of every `selfgame`: [rows, the whole sgend line, digest]; digest = sha256 over every complete `sg`
             row, one space, the result integer of the end line, LF (the field digest of the plan's N12 fixture)
  totals     rows, searches, nodes over all games; sha256 over all `sg` and `sgend` lines as written
  refusals   every line with `unknown option`, `invalid value`, `No such option`, `ERROR`, `invalid FEN`,
             `illegal move`, or that starts with `sgerror`: a clean run has none
  drive      the driver's own last line: its exit code and the engine's must be 0
"""
import hashlib
import json
import re
import sys
from pathlib import Path

REFUSAL = re.compile(r"unknown option|invalid value|No such option|ERROR|invalid FEN|illegal move|^sgerror ")
COMPARED = ("bench", "perft", "eval", "net", "search", "games", "totals", "refusals", "drive")


def summary(path: Path) -> dict:
    segs, tail = [], ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(">>> "):
            segs.append((line[4:], []))
        elif line.startswith("### drive.py:"):
            tail = line
        elif segs:
            segs[-1][1].append(line)
    s = {"bench": [], "perft": [], "eval": [], "net": [], "net_kernel": [], "search": [], "games": [],
         "refusals": [], "commands": len(segs)}
    all_sg = hashlib.sha256()
    rows = searches = nodes = 0
    position = ""
    for cmd, lines in segs:
        if cmd.startswith("position "):
            position = cmd
        for ln in lines:
            if REFUSAL.search(ln):
                s["refusals"].append(ln[:200])
            m = re.match(r"info string bench depth (\d+) nodes (\d+)", ln)
            if m:
                s["bench"].append([int(m[1]), int(m[2])])
            m = re.match(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)", ln)
            if m:
                s["eval"].append([int(m[1]), int(m[2]), int(m[3])])
            if ln.startswith("info string NNUE v3 active:"):
                m = re.search(r" hidden (\d+) king_buckets (\d+).* checksum ([0-9a-f]+) ", ln)
                k = re.search(r" kernel (\S+)", ln)
                s["net"].append([int(m[1]), int(m[2]), m[3]] if m else ["unreadable", ln[:120]])
                s["net_kernel"].append(k[1] if k else "")
        if cmd.startswith("go perft "):
            got = [int(ln.split()[1]) for ln in lines if re.fullmatch(r"nodes \d+", ln)]
            s["perft"].append([position, int(cmd.split()[2]), got[-1] if got else None])
        elif cmd.split()[0] == "go":
            last, best = None, None
            for ln in lines:
                if ln.startswith("info ") and " depth " in ln and " nodes " in ln and " hashfull " in ln:
                    t = ln.split()
                    last = [int(t[t.index("depth") + 1]), int(t[t.index("nodes") + 1]), int(t[t.index("hashfull") + 1])]
                if ln.startswith("bestmove"):
                    best = ln.split()[1] if len(ln.split()) > 1 else ""
            s["search"].append([*(last or [None, None, None]), best])
        elif cmd.split()[0] == "selfgame":
            sg = [ln for ln in lines if ln.startswith("sg ")]
            end = [ln for ln in lines if ln.startswith("sgend ")]
            for ln in sg + end:
                all_sg.update((ln + "\n").encode("utf-8"))
            if len(end) != 1:
                s["games"].append([len(sg), "NO sgend LINE" if not end else "MORE THAN ONE sgend LINE", ""])
                continue
            t = end[0].split()
            h = hashlib.sha256()
            for ln in sg:
                h.update((ln + " " + t[t.index("result") + 1] + "\n").encode("ascii"))
            s["games"].append([len(sg), end[0], h.hexdigest()])
            rows += len(sg)
            searches += int(t[t.index("searches") + 1])
            nodes += int(t[t.index("nodes") + 1])
    s["totals"] = {"games": len(s["games"]), "rows": rows, "searches": searches, "nodes": nodes,
                   "sg_sha256": all_sg.hexdigest() if s["games"] else ""}
    m = re.match(r"### drive\.py: exit (\d+).*; engine exit code (\S+);", tail)
    s["drive"] = [int(m[1]), m[2]] if m else ["NO LAST LINE OF drive.py", ""]
    return s


def clean(s: dict) -> list[str]:
    bad = []
    if s["drive"] != [0, "0"]:
        bad.append(f"the run did not end cleanly: drive {s['drive']}")
    if s["refusals"]:
        bad.append(f"{len(s['refusals'])} refusal line(s), the first: {s['refusals'][0]}")
    if any(g[1].startswith(("NO ", "MORE ")) for g in s["games"]):
        bad.append("a selfgame without exactly one sgend line")
    if any(p[2] is None for p in s["perft"]):
        bad.append("a perft without its nodes line")
    if any(x[0] == "unreadable" for x in s["net"]):
        bad.append("a net line that cannot be read")
    return bad


def main() -> int:
    if len(sys.argv) not in (3, 4) or sys.argv[2] not in ("show", "write", "known") or \
            (sys.argv[2] == "show") != (len(sys.argv) == 3):
        print(__doc__)
        return 2
    s = summary(Path(sys.argv[1]))
    mode = sys.argv[2]
    if mode == "show":
        print(json.dumps(s, indent=1))
        return 0
    bad = clean(s)
    if mode == "write":
        out = Path(sys.argv[3])
        if out.exists():
            print(f"STOP: {out} exists (known answers are never written over)")
            return 2
        if bad:
            print("REFUSED, nothing written: " + "; ".join(bad))
            return 1
        out.write_bytes((json.dumps(s, indent=1) + "\n").encode("ascii"))
        print(f"known answers written: {out.name}: {s['commands']} commands, bench {s['bench']}, "
              f"{len(s['perft'])} perft, {len(s['search'])} searches, totals {s['totals']}")
        return 0
    known = json.loads(Path(sys.argv[3]).read_text(encoding="ascii"))
    diffs = list(bad)
    for k in COMPARED:
        if s[k] == known[k]:
            continue
        a, b = s[k], known[k]
        if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    diffs.append(f"{k}[{i}]: got {str(x)[:150]}  known {str(y)[:150]}")
        else:
            diffs.append(f"{k}: got {str(a)[:200]}  known {str(b)[:200]}")
    if diffs:
        print(f"DIFFERENT from {Path(sys.argv[3]).name} ({len(diffs)}):")
        for d in diffs[:12]:
            print("  " + d)
        return 1
    print(f"EQUAL to {Path(sys.argv[3]).name}: bench {s['bench']}, {len(s['perft'])} perft, eval {s['eval']}, "
          f"net {s['net']}, search {s['search']}, totals {s['totals']}; kernel {sorted(set(s['net_kernel']))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
