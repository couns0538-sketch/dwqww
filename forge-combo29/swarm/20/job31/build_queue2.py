#!/usr/bin/env python3
"""build_queue2.py — seat 20 job 31b: the ACTIONABLE re-run queue, with a curated short list.

The first version (build_queue.py) ranked mechanically and its short list came out dominated by one seat's
patch-regression lines, which are not what anyone needs first. This version:
  * keeps the mechanical full table (so nothing is hidden),
  * but writes the short list BY HAND, each entry with the reason it is on the list and the exact command shape
    a re-runner needs (build, settings, board, thread count).

usage: build_queue2.py <outdir>
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
score_re = re.compile(r"\b(cp|mate)\s*[-+]?\d+", re.I)
thread_re = re.compile(r"threads?\s*[:=]?\s*(\d+)", re.I)
fen_re = re.compile(r"\b([1-8rnbqkpRNBQKP/]{10,}\s+[wb]\s+[KQkq-]+\s+[a-h1-8-]+\s+\d+\s+\d+)")

rows = []
for n in range(1, 61):
    s = f"{n:02d}"
    if subprocess.run(["git", "ls-remote", "origin", f"refs/heads/for-fable-and-opus/swarm-{s}"],
                      capture_output=True, text=True).stdout.strip() == "":
        continue
    if subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin",
                       f"for-fable-and-opus/swarm-{s}"], capture_output=True).returncode != 0:
        continue
    show = subprocess.run(["git", "show", f"FETCH_HEAD:forge-combo29/swarm/{s}/FINDINGS.md"],
                          capture_output=True, text=True)
    if show.returncode != 0:
        continue
    for line in show.stdout.split("\n"):
        if not line.strip().startswith("|") or not score_re.search(line):
            continue
        tm = [int(x) for x in thread_re.findall(line)]
        if 1 in tm or "threads 1" in line.lower():
            continue
        if s == "04" or "tsan" in line.lower():
            continue
        kind = "AT_RISK (states Threads >1)" if any(t > 1 for t in tm) else "UNSTATED (no thread count)"
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        fid = cells[0].strip("* ")
        body = " | ".join(cells[1:])
        m = fen_re.search(body)
        rows.append({"seat": s, "id": fid, "kind": kind,
                     "board": m.group(1) if m else "(not named in the line)",
                     "text": body[:230]})

SHORT = [
    ("30", "30-F19",
     "The only line in the queue already measured on the PC r15 build. If its score holds at Threads 1 it is the "
     "first third-party confirmation of PC-build behaviour; if it does not, every 'on the PC build' claim needs a "
     "thread count before it is quoted.",
     "PC r15 exe, PC20, Threads 1 explicit, the line's `quiet_hm100` board, `go depth 10`, 5 fresh runs"),
    ("25", "S-F1 / S-F2",
     "The mate-distance claim that first exposed this whole area, and the one my own S-F22 independently proved "
     "(true distance 8 plies). A Threads-1 re-run on their board either reproduces `mate -12` (making it a solid "
     "independent confirmation of the depth-limited miss) or does not.",
     "base exe, S14, Threads 1 explicit, `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`, `go depth 12`, 5 fresh runs"),
    ("28", "S-F4",
     "The repetition door — the one door seat 01's patch leaves open on the base tree. I confirmed it (S-C4) at "
     "Threads 1, but a second confirmation from a seat that states Threads 1 would close it properly.",
     "base exe, S14 or none (state it), Threads 1 explicit, their third-occurrence board, `go depth 6`"),
    ("21", "21-F9",
     "The halfmove >= 100 sweep (100, 150, 9999, 65536, up to 2147483648). The sweep is the kind of claim whose "
     "SCORES are the whole content, so a thread count decides whether it is evidence or noise.",
     "base exe, their settings, Threads 1 explicit, the counters they list, `go depth 5`"),
    ("21", "21-F11",
     "`mate 0` on a checkmated root. A one-position claim with a decisive answer — cheap to re-run, and if it holds "
     "at Threads 1 nobody needs to look at it again.",
     "base exe, Threads 1 explicit, `4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60`, `go depth 1`, 3 fresh runs"),
    ("27", "S-F8 / S-F8a / S-F8b / S-F8c",
     "A four-part chain about `searchmoves` changing the SCORE, with a bounded-but-unsolved conclusion. Four score "
     "claims in a chain: if any of them was measured above Threads 1 the chain needs rebuilding, and the chain is "
     "what seat 10's and seat 12's findings are being separated with.",
     "base exe, their builds (build-release / build-sm / build-sm2 named in their files), Threads 1 explicit, "
     "startpos and their 20 positions, `go depth 12` and the depths they name"),
    ("01", "S-F19 / S-F22 / S-F23",
     "The seat that produced the patch everyone else is testing has a three-line correction chain about a "
     "halfmove-100 board whose mate is 3 plies away, and whether it is discriminating. Threads 1 must be stated "
     "before any patch recommendation rests on it.",
     "unpatched base exe, S14, Threads 1 explicit, `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1` and "
     "`8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1`, `go depth 5`"),
    ("28", "S-F21 / S-F19",
     "One of THREE competing drawn-root fixes exists in this seat's folder (they say only one may be applied). The "
     "regression numbers that justify choosing between them are scores; a thread count decides if they mean "
     "anything.",
     "base exe patched and unpatched, S14, Threads 1 explicit, the boards their lines name, `go depth 5..6`"),
]

out = []
out.append("# RE-RUN QUEUE — findings that report a score without stating Threads 1")
out.append("")
out.append("Owner-requested, built by seat 20 (`job27/thread_audit.py`, `job31/build_queue.py`, `job31/build_queue2.py`).")
out.append("")
out.append("**Swarm rule (22:19Z):** a score must be from Threads 1 unless the job is about threading. Seat 04")
out.append("measured the PC build at Threads 4 on one position and got four distinct scores (+2576, mate 13,")
out.append("mate 18, mate 16; nodes 5.0M–31.4M), while Threads 1 gave +2207 four times with identical nodes 75,311.")
out.append("")
out.append("**These lines are not wrong.** They are *unconfirmable as written*: nobody can reproduce a score without")
out.append("knowing the thread count, and a confirmation must use the same build AND the same settings as the find.")
out.append("A re-runner should send `setoption name Threads value 1`, state it in the confirmation line, and name the")
out.append("build (`base 6b98f217` or `PC r15`) and the settings (`none`, `S14`, `PC20`).")
out.append("")
out.append(f"**Total flagged: {len(rows)} lines across {len({r['seat'] for r in rows})} seats.**")
out.append("")
out.append("## The short list — 8 lines worth re-running first, with the reason")
out.append("")
out.append("Hand-picked, because nobody can re-run 120. Each is a score claim whose answer changes either a repair")
out.append("decision or a currently-**live** finding. Chosen on consequence, not on suspicion.")
out.append("")
for i, (seat, fid, why, how) in enumerate(SHORT, 1):
    out.append(f"### {i}. seat {seat} — {fid}")
    out.append("")
    out.append(f"**Why:** {why}")
    out.append("")
    out.append(f"**How to re-run:** {how}")
    out.append("")
out.append("## The full queue, grouped by seat")
out.append("")
from collections import defaultdict
by_seat = defaultdict(list)
for r in rows:
    by_seat[r["seat"]].append(r)
for seat in sorted(by_seat, key=lambda s: (-len(by_seat[s]), s)):
    rs = by_seat[seat]
    out.append(f"### seat {seat} — {len(rs)} lines")
    out.append("")
    out.append("| finding | flag | board named in the line | what the line claims |")
    out.append("|---|---|---|---|")
    for r in rs:
        out.append(f"| {r['id']} | {r['kind']} | `{r['board']}` | {r['text'][:150].replace('|', '/')} |")
    out.append("")

open(os.path.join(OUT, "RERUN_QUEUE.md"), "w").write("\n".join(out) + "\n")
print(f"wrote RERUN_QUEUE.md: {len(rows)} lines, {len(by_seat)} seats, {len(SHORT)} short-list entries")
for seat in sorted(by_seat, key=lambda s: -len(by_seat[s])):
    print(f"  seat {seat}: {len(by_seat[seat])} flagged")
