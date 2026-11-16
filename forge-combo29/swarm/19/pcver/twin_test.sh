#!/usr/bin/env bash
# twin_test.sh EXE : the two root-drawn tests, using the known-good driver style
# (send, then read to the answering token / bestmove; never pipe quit behind a go — 19-F12).
set -u
EXE="$1"
drv() {
  printf '%s\n' "$@" | awk 'BEGIN{print "uci"} {print} END{print "quit"}' > /dev/null
  python3 - "$EXE" "$@" <<'PY'
import subprocess, sys, re
exe=sys.argv[1]; lines=sys.argv[2:]
p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
def send(l): p.stdin.write(l+"\n"); p.stdin.flush()
def readto(tok):
    got=[]
    while True:
        l=p.stdout.readline()
        if not l: return got
        got.append(l.rstrip("\n"))
        if l.startswith(tok): return got
send("uci"); readto("uciok")
i=0
while i < len(lines):
    l=lines[i]
    if l.startswith("go "):
        send(l)
        for g in readto("bestmove"):
            pass
        # collect the search block properly
    elif l=="isready":
        send(l); readto("readyok")
    else:
        send(l)
    i+=1
send("quit")
try: p.communicate(timeout=60)
except subprocess.TimeoutExpired: p.kill()
PY
}
echo "placeholder"
