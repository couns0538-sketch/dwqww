"""Opus 24 Nov: A3f's stand-in for sftp.exe, for tests only (home/fetch.py with "transport": "local"). The fetch
starts it as
    fake_transport.py list <root> <rel>            prints "<length> <name>" for each FILE in <root>/<rel>
    fake_transport.py get <root> <rel> <partial>   appends <root>/<rel>[length of partial:] to <partial>
A plan file <root>.plan.json (written by the test) changes calls one at a time: {"<op> <rel>": [call, ...]}; each
call is taken from the front of its list and the rest is written back. A call may hold:
    "say": text        printed to stderr first (what sftp would say)
    "exit": code       the exit code (a list call with an exit code lists nothing)
    "chunks": [[n, pause_s], ...]   send n bytes, flush, sleep pause_s (the process stays alive)
    "rest": true       after the chunks, send what is left
    "hang_s": x        stay alive x seconds after the last byte, sending nothing
Without a call, a get sends everything and exits 0. Writes only <partial> and the plan file.
"""
import json
import sys
import time
from pathlib import Path

op, root, rel = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
plan_file = root.with_name(root.name + ".plan.json")
call = {}
if plan_file.exists():
    plan = json.loads(plan_file.read_text(encoding="ascii"))
    if plan.get(f"{op} {rel}"):
        call = plan[f"{op} {rel}"].pop(0)
        plan_file.write_text(json.dumps(plan), encoding="ascii")
if "say" in call:
    print(call["say"], file=sys.stderr, flush=True)
if op == "list":
    d = root / rel if rel else root
    if "exit" not in call and d.is_dir():
        for p in sorted(d.iterdir()):
            if p.is_file():
                print(p.stat().st_size, p.name)
    sys.exit(call.get("exit", 0))
part = Path(sys.argv[4])
data = (root / rel).read_bytes()
pos = part.stat().st_size if part.exists() else 0
with open(part, "ab") as f:
    for n, pause in call.get("chunks", [] if call else [[len(data), 0]]):
        f.write(data[pos:pos + n])
        f.flush()
        pos = min(len(data), pos + n)
        time.sleep(pause)
    if call.get("rest"):
        f.write(data[pos:])
        f.flush()
time.sleep(call.get("hang_s", 0))
sys.exit(call.get("exit", 0))
