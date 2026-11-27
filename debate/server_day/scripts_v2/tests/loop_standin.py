"""Fable 26 Nov 2026: ONE stand-in for every program the home loop (home/loop.py, v17) starts: a test of the loop with
no network, no engine and no data. A copy of this file stands under each program's name in a stand-in package tree:
<tree>/home/{clock,fetch,custody,content,credit,publish,deliver,state,drain}.py and <tree>/tools/{budget,make_control}.py.
Each call (1) appends ONE line to <tree>/STANDIN/calls.jsonl: the program key, its arguments, its interpreter,
whether it runs isolated (-I) and without bytecode (-B), the steady clock at its start; (2) does what
<tree>/STANDIN/plan.json says for the n-th call of this program; (3) prints the planted lines and exits with the
planted code.

plan.json: {"<key>": [<spec of the 1st call>, <of the 2nd>, ...]}; the last spec repeats; a key that is missing takes
exit 0 and DEFAULT_LAST (the REAL program's real last line of a quiet pass, copied from my dry run b2 of 26 Nov or from
the program's own source). key = the file's name, plus the first argument for clock ("clock measure") and deliver
("deliver probe", "deliver send", "deliver observe").
spec: {"exit": int, "last": text, "stdout": text printed before the last line, "sleep": seconds before anything else,
       "crash": true (an exception: exit 1 with a Traceback), "do": [action, ...]}
action: {"op": "write", "at": A, "path": rel, "text": .. | "size": n | "from": absolute file, "create_only": bool}
        {"op": "remove", "at": A, "path": rel}
        {"op": "copytree", "at": A, "path": rel, "from_at": A, "from": rel}     (deliver send: made/ into sent/)
A: "home" = the --home argument, "out" = --out, "made" = --made, "tree" = the stand-in tree.
In "text" the marks @@K@@ (this program's call number, from 1) and @@HOME@@ are filled in; in "path" @@K@@ too.

AS A MODULE (the loop may import home/clock.py for its reading, as drain.py and deliver.py do): reading(home,
fingerprint, mono=None, wall=None) gives (server_now, lag_s, the line) as Decimals from plan key "clock.reading"
({"server_now": text, "lag_s": text, "n": int} or {"refused": text}), logging the call; ClockRefused, server_now() and
lag_s() beside it. It never reads a clock of its own.
"""
import json
import os
import shutil
import sys
import time
from decimal import Decimal
from pathlib import Path

ME = Path(__file__).resolve()
TREE = ME.parent.parent
BOX = TREE / "STANDIN"
DEFAULT_LAST = {
    "clock measure": "clock: ok n 2, the server's time 2026-11-30T06:16:45Z (utc_ms 1796019405200), offset -25178.0 s "
                     "(the server's minus the PC's; a note for people)",
    "fetch": "fetch: listing 642 bytes; control 0 files 0 bytes; offers 0 files 0 bytes; members 0 files 0 bytes; sent "
             "again 0 bytes; partial 0; confirmations 0; forks 0; refused 0; incomplete 0; ignored 0; budget binds no",
    "custody": "custody: RECEIVED 0 pieces 0 rows; C1 0 pieces 0 rows; new receipts 0; not received 0; waits 0; "
               "conflicts 0; forks 0",
    "content": "content: judged 0 pieces (0 refused); accepted 0 games 0 rows; noselfgame 0; set_aside 0; waits 0; "
               "conflicts 0",
    "credit": "credit: decided 0 rounds (0 complete, 0 partial) this pass; credited 0 games 0 rows; waits: none; holds 0",
    "publish": "publish: published 0 rounds (0 complete, 0 partial) this pass; kept rows 0; waits: none; failed: none",
    "deliver observe": "deliver: observe: all 0 sent control(s) seen",
    "deliver probe": "deliver: probe passed (`rename -l` refuses an existing name and moves to a free one; the probe "
                     "names are removed)",
    "deliver send": "deliver: CONTROL.1.json 0123456789ab (pilot_decision SELF_PLAY) sent: stand-in",
    "state": "state: STOP (9): no clock line of this run: run clock.py measure first",
    "budget": "{\"error\": \"stand-in: no report planted\"}",
    "make_control": "make_control: REFUSED (nothing written): stand-in: no control planted",
    "drain": "drain: REFUSED (4): the lease ends at 2026-12-01T06:00:00Z; the server's clock reads "
             "2026-11-30T06:16:45Z (UTC); nothing written",
}
DEFAULT_EXIT = {"state": 9, "budget": 2, "make_control": 4, "drain": 4}


class ClockRefused(Exception):
    """The stand-in helper's refusal (the real one's name)."""


def _plan():
    return json.loads((BOX / "plan.json").read_text(encoding="utf-8"))


def _calls():
    try:
        return [json.loads(x) for x in (BOX / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    except FileNotFoundError:
        return []


def _log(key, argv):
    """Append this call's line (one write of whole bytes) and give its spec and its number among this key's calls."""
    nth = sum(1 for x in _calls() if x["prog"] == key)
    rec = {"prog": key, "k": nth + 1, "argv": list(argv), "exe": sys.executable, "isolated": bool(sys.flags.isolated),
           "no_bytecode": bool(sys.dont_write_bytecode), "mono": time.monotonic(), "cwd": os.getcwd(),
           "stdin_closed": sys.stdin is None or sys.stdin.closed}
    with open(BOX / "calls.jsonl", "ab") as f:
        f.write((json.dumps(rec, sort_keys=True) + "\n").encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())
    specs = _plan().get(key) or [{}]
    return specs[min(nth, len(specs) - 1)], nth + 1


def reading(home, fingerprint, mono=None, wall=None):
    spec, _k = _log("clock.reading", [str(home), fingerprint])
    if "refused" in spec or "server_now" not in spec:
        raise ClockRefused(spec.get("refused", "no clock line of this run: run clock.py measure first"))
    return Decimal(spec["server_now"]), Decimal(spec["lag_s"]), {"n": spec.get("n", 2), "ok": True}


def server_now(home, fingerprint, mono=None, wall=None):
    return float(reading(home, fingerprint)[0])


def lag_s(home, fingerprint, mono=None, wall=None):
    return reading(home, fingerprint)[1]


def _opt(args, flag):
    return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else None


def main(argv):
    name, args = ME.stem, argv[1:]
    sub = args[0] if name in ("clock", "deliver") and args and not args[0].startswith("-") else ""
    key = f"{name} {sub}".strip()
    spec, k = _log(key, args)
    time.sleep(spec.get("sleep", 0))
    if spec.get("crash"):
        raise RuntimeError("stand-in: a planted crash")
    base = {"home": _opt(args, "--home"), "out": _opt(args, "--out"), "made": _opt(args, "--made"), "tree": str(TREE)}

    def place(at, rel):
        if base.get(at) is None:
            raise SystemExit(f"stand-in {key}: the plan names '{at}' but the call has no such argument")
        return Path(base[at]) / rel

    for a in spec.get("do", []):
        dst = place(a["at"], a["path"].replace("@@K@@", str(k)))
        if a["op"] == "remove":
            if dst.is_dir():
                shutil.rmtree(dst)
            elif dst.exists():
                dst.unlink()
        elif a["op"] == "copytree":
            shutil.copytree(place(a["from_at"], a["from"]), dst, dirs_exist_ok=True)
        elif a["op"] == "write":
            if a.get("create_only") and dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if "from" in a:
                shutil.copyfile(a["from"], dst)
            elif "size" in a:
                dst.write_bytes(b"x" * a["size"])
            else:
                text = a.get("text", "").replace("@@K@@", str(k)).replace("@@HOME@@", str(base.get("home")))
                dst.write_bytes(text.encode("utf-8"))
        else:
            raise SystemExit(f"stand-in {key}: an action the stand-in does not know: {a['op']}")
    if "stdout" in spec:
        print(spec["stdout"].replace("@@K@@", str(k)))
    print(spec.get("last", DEFAULT_LAST.get(key, f"{name}: stand-in")).replace("@@K@@", str(k)), flush=True)
    return spec.get("exit", DEFAULT_EXIT.get(key, 0))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
