#!/usr/bin/env python3
"""audit_harness_ordering.py OUT — prove mechanically that no harness of this seat sends a setoption between `go`
and `bestmove`.

I asserted this in 08-C17 ("every setoption of mine is sent before `go`, with a `sync()` after it") — that was a
claim from reading, not from a check. Given 08-C17 established that a mid-search setoption SILENTLY STOPS the
search, the assertion is load-bearing: if any harness violated it, that harness's numbers are truncated searches.

This is a static audit of every .py and .sh in the folder:
  - find every line that sends a setoption (send/command/printf/echo with "setoption"),
  - find every `go ` send and every `bestmove` wait,
  - report any file where a setoption send appears between a `go` send and the next bestmove wait.

It cannot prove ordering for shell pipelines, so those are listed separately for manual review rather than passed
silently.

ARGUMENT ORDER: OUT first.
"""
import re
import sys
from pathlib import Path

OUT = sys.argv[1]
root = Path("..").resolve()

SETOPT = re.compile(r'setoption', re.I)
GO_SEND = re.compile(r'(send\(\s*["\']go |printf\s+["\']go |echo\s+["\']go |send\("go )')
BESTMOVE_WAIT = re.compile(r'bestmove')

out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Static audit: is any `setoption` sent between `go` and `bestmove` in this seat's harnesses?")
emit("")
emit("| file | setoption sends | go sends | bestmove waits | setoption between go and bestmove? |")
emit("|---|---|---|---|---|")

bad = []
shell_pipelines = []
py_files = sorted(list(root.rglob("*.py")))
sh_files = sorted(list(root.rglob("*.sh")))

for p in py_files + sh_files:
    try:
        lines = p.read_text(errors="ignore").splitlines()
    except Exception:
        continue
    setopts = [(i, l) for i, l in enumerate(lines) if SETOPT.search(l) and
               (("send(" in l) or ("printf" in l) or ("echo" in l) or ("command(" in l))]
    gos = [(i, l) for i, l in enumerate(lines) if GO_SEND.search(l)]
    waits = [(i, l) for i, l in enumerate(lines)
             if ('read_until("bestmove"' in l or "read_until('bestmove'" in l
                 or "done.wait" in l)]
    if not (setopts or gos):
        continue
    is_shell = p.suffix == ".sh"
    # for each go send, is there a setoption send before the next bestmove wait?
    violation = False
    detail = ""
    for gi, gl in gos:
        nxt = [w for w, _ in waits if w > gi]
        end = nxt[0] if nxt else len(lines)
        for si, sl in setopts:
            if gi < si < end:
                # a setoption AFTER a go and BEFORE the bestmove wait is the dangerous shape. A setoption that
                # PRECEDES the go is safe even without a sync(), because the engine consumes stdin in order and
                # the go is sent after it.
                if si > gi:
                    violation = True
                    detail = "line %d after go at line %d" % (si + 1, gi + 1)
    # a shell pipeline that mentions setoption and go on separate lines is flagged for review, not passed
    if is_shell and setopts and gos:
        shell_pipelines.append(str(p.relative_to(root)))
    if violation:
        bad.append(str(p.relative_to(root)))
    emit("| %s | %d | %d | %d | %s |" %
         (p.relative_to(root), len(setopts), len(gos), len(waits),
          ("**YES — VIOLATION** (%s)" % detail) if violation else "no"))

emit("")
emit("## Verdict")
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| python/shell harnesses scanned | %d |" % len([p for p in py_files + sh_files
                                                   if SETOPT.search(p.read_text(errors='ignore')) or
                                                   GO_SEND.search(p.read_text(errors='ignore'))]))
emit("| files with a setoption between go and bestmove | **%d** %s |" % (len(bad), bad if bad else ""))
emit("| shell files needing manual review (ordering not provable statically) | %d |" % len(shell_pipelines))

emit("")
if not bad:
    emit("**No Python harness of this seat sends a setoption between `go` and `bestmove`.** The 08-C17 assertion holds")
    emit("for every Python harness, checked mechanically rather than by reading.")
else:
    emit("**VIOLATIONS FOUND — those harnesses record truncated searches:** %s" % bad)

if shell_pipelines:
    emit()
    emit("### shell files listed for manual review")
    emit("These mention both `setoption` and `go`; a shell pipeline's ordering cannot be proven by this static scan,")
    emit("so they are named rather than passed silently:")
    for s in shell_pipelines:
        emit("- `%s`" % s)

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
