"""Fable 2026-11-23, W5 of FINAL_PLAN_2311.md: give ONE engine process a UCI text (serverday/workloads/*.uci) and
keep everything it says. Standard library only: the same file runs on the PC and on Linux.

    drive.py <engine exe> <workload.uci> <net file, or - for none> <new transcript file> [seconds a step = 1800]

- `@@NET@@` in the text becomes the absolute path of the net file (forward slashes).
- It WAITS, so that no command interrupts a search: after `isready` for `readyok`; after `go ...` (not `go perft`)
  for `bestmove`; after `selfgame ...` for `sgend` or `sgerror`; after every other command it sends an `isready`
  of its own and waits for the answer (bench, perft and eval are finished when that answer comes).
- The transcript holds each command as `>>> <command>` (with @@NET@@ unfilled, so that transcripts from two
  machines can be compared) and every line the engine wrote, stderr included. The `isready` this tool adds and
  its answer are left out.
- Exit code 0 = every command was answered and the engine ended with exit code 0. 3 = a step ran into its time
  limit (the engine is ended). 4 = the engine ended early or with another exit code. 2 = wrong call.
"""
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path


def main() -> int:
    if len(sys.argv) not in (5, 6):
        print(__doc__)
        return 2
    exe, work, net, out = sys.argv[1:5]
    limit = float(sys.argv[5]) if len(sys.argv) == 6 else 1800.0
    out = Path(out)
    if out.exists():
        print(f"STOP: {out} exists (a transcript is never written over)")
        return 2
    netpath = "" if net == "-" else str(Path(net).resolve()).replace("\\", "/")
    cmds = [ln.strip() for ln in Path(work).read_text(encoding="ascii").splitlines() if ln.strip()]
    if any("@@NET@@" in c for c in cmds) and not netpath:
        print("STOP: the text needs a net file and none was given")
        return 2
    if not cmds or cmds[-1] != "quit":
        print("STOP: the text does not end with quit")
        return 2

    p = subprocess.Popen([str(Path(exe).resolve())], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1,
                         cwd=str(Path(exe).resolve().parent))
    q: "queue.Queue[str | None]" = queue.Queue()

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\r\n"))
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    log: list[str] = []
    state = {"ended": False}

    def send(c: str) -> None:
        p.stdin.write(c.replace("@@NET@@", netpath) + "\n")
        p.stdin.flush()

    def wait_for(done, keep=True, secs=None) -> str:
        """Read lines until done(line); returns 'ok', 'timeout' or 'ended'."""
        end = time.time() + (limit if secs is None else secs)
        while True:
            try:
                line = q.get(timeout=max(0.05, end - time.time()))
            except queue.Empty:
                return "timeout"
            if line is None:
                state["ended"] = True
                return "ended"
            hit = done(line)
            if keep or not hit:
                log.append(line)
            if hit:
                return "ok"

    rc, why = 0, ""
    t0 = time.time()
    try:
        for c in cmds:
            log.append(">>> " + c)
            try:
                send(c)
            except OSError:
                rc, why = 4, f"the engine was gone when `{c}` was sent"
                break
            if c == "quit":
                break
            head = c.split()[0]
            if c == "isready":
                r = wait_for(lambda s: s == "readyok")
            elif head == "go" and not c.startswith("go perft"):
                r = wait_for(lambda s: s.startswith("bestmove"))
            elif head == "selfgame":
                r = wait_for(lambda s: s.startswith("sgend ") or s.startswith("sgerror "))
            else:
                r = "ok"
            if r == "ok" and c != "isready":
                try:
                    send("isready")
                except OSError:
                    rc, why = 4, f"the engine was gone after `{c}`"
                    break
                r = wait_for(lambda s: s == "readyok", keep=False)
            if r == "timeout":
                rc, why = 3, f"no answer to `{c}` within {limit:.0f} s"
                break
            if r == "ended":
                rc, why = 4, f"the engine ended at `{c}`"
                break
        if rc == 0:
            try:
                p.stdin.close()
            except OSError:
                pass
            while not state["ended"]:          # whatever it still writes after quit
                if wait_for(lambda s: False, secs=60) == "timeout":
                    rc, why = 3, "the engine did not end after quit"
                    break
            if rc == 0:
                try:
                    code = p.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    rc, why, code = 3, "the engine did not end after quit", None
                if rc == 0 and code != 0:
                    rc, why = 4, f"the engine's exit code was {code}"
    finally:
        if p.poll() is None:
            p.kill()
            p.wait()
    log.append(f"### drive.py: exit {rc}{' (' + why + ')' if why else ''}; engine exit code {p.returncode}; "
               f"{len(cmds)} commands; {time.time() - t0:.1f} s")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(("\n".join(log) + "\n").encode("utf-8"))
    print(log[-1])
    return rc


if __name__ == "__main__":
    sys.exit(main())
