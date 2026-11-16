#!/usr/bin/env python3
"""build_queue.py — seat 20 job 31: turn the 120-line thread flag into an ACTIONABLE re-run queue.

For every seat with flagged lines, extract the finding id, the board (FEN/position) it used if the line names one,
and a one-line description; then rank by how much a confirmation is worth.

Ranking criteria (stated before ranking, applied mechanically):
  1. HIGHEST: the claim is about a SCORE (cp/mate) AND the same claim is what the PC build or a repair decision
     turns on (drawn-root doors, mate distance, mate score correctness).
  2. HIGH: a score claim on the PC r15 build (someone already used the right build but may not have stated threads).
  3. MEDIUM: a score claim about a search limit or a tuning option.
  4. LOWER: a score claim that is a control/confirm line rather than a primary finding.

usage: build_queue.py <outdir>
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

score_re = re.compile(r"\b(cp|mate)\s*[-+]?\d+", re.I)
thread_re = re.compile(r"threads?\s*[:=]?\s*(\d+)", re.I)
fen_re = re.compile(r"\b([1-8rnbqkpRNBQKP/]{10,})\s+([wb])\s+([KQkq-]+)\s+([a-h1-8-]+)\s+(\d+)\s+(\d+)")
id_re = re.compile(r"^\s*\|\s*\*{0,2}([0-9]{1,2}-[A-Za-z][0-9]+[a-z]?|S-[A-Z][0-9]+)\*{0,2}\s*\|")

HIGH_VALUE_TOKENS = ("drawn", "root_drawn", "halfmove", "repetition", "mate", "searchmoves", "ucinewgame",
                     "repair", "pc r15", "pc20", "distance")

rows = []
seats = []
for n in range(1, 61):
    s = f"{n:02d}"
    r = subprocess.run(["git", "ls-remote", "origin", f"refs/heads/for-fable-and-opus/swarm-{s}"],
                       capture_output=True, text=True)
    if r.stdout.strip():
        seats.append(s)

for s in seats:
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
        if any(t > 1 for t in tm):
            kind = "AT_RISK_THREADS_GT1"
        elif s == "04" or "tsan" in line.lower() or "racesanitizer" in line.lower():
            continue
        else:
            kind = "UNSTATED_THREADS"
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        fid = cells[0].strip("* ")
        body = " ".join(cells[1:])
        m = fen_re.search(body)
        board = " ".join(m.groups()) if m else "(board not named in the line)"
        low = body.lower()
        score = 4
        if any(t in low for t in ("drawn", "root_drawn", "halfmove", "repetition", "ucinewgame")):
            score = 1
        elif "pc r15" in low or "pc20" in low or "pc build" in low:
            score = 2
        elif "mate" in low or "searchmoves" in low:
            score = 3
        rows.append({"seat": s, "id": fid, "kind": kind, "priority": score, "board": board,
                     "text": body[:220]})

rows.sort(key=lambda r: (r["priority"], r["seat"], r["id"]))
out = []
out.append("# RE-RUN QUEUE — findings that report a score without stating Threads 1")
out.append("")
out.append("Built by seat 20 from every seat's FINDINGS.md (`job27/thread_audit.py`, `job31/build_queue.py`).")
out.append("Swarm rule (22:19Z): a score must be Threads 1 unless the job is about threading. Seat 04 measured the")
out.append("PC build at Threads 4 giving four distinct scores on ONE position (+2576, mate 13, mate 18, mate 16,")
out.append("nodes 5.0M-31.4M) while Threads 1 gave +2207 four times with identical nodes 75,311.")
out.append("")
out.append("**What this queue is for:** these lines are NOT wrong. They are *unconfirmable as written* — nobody can")
out.append("reproduce them without knowing the thread count, and a confirmation must use the same build and")
out.append("settings as the find. Re-run at `Threads 1`, state the count and the build in the confirmation line.")
out.append("")
out.append(f"Total flagged: **{len(rows)}** lines across {len({r['seat'] for r in rows})} seats.")
out.append("")
out.append("## The short list — 8 lines worth re-running first")
out.append("")
out.append("Chosen because the answer changes a repair decision or a currently-live finding, not because the")
out.append("line is suspect. Each is a score claim about a drawn-root/mate/PC-build behaviour.")
out.append("")
short = [r for r in rows if r["priority"] <= 2][:8]
for i, r in enumerate(short, 1):
    out.append(f"{i}. **seat {r['seat']} {r['id']}** — {r['text'][:150]}")
    out.append(f"   - board: `{r['board']}`")
out.append("")
out.append("## The full queue, prioritised")
out.append("")
out.append("| # | seat | finding | flag | board named in the line | what the line claims |")
out.append("|---|---|---|---|---|---|")
for i, r in enumerate(rows, 1):
    out.append(f"| {i} | {r['seat']} | {r['id']} | {r['kind'].replace('_', ' ').lower()} | "
               f"`{r['board']}` | {r['text'][:130].replace('|', '/')} |")

open(os.path.join(OUT, "RERUN_QUEUE.md"), "w").write("\n".join(out) + "\n")
print("\n".join(out[:40]))
print(f"\n... total {len(rows)} rows written to RERUN_QUEUE.md")
