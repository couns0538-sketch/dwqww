#!/usr/bin/env python3
"""tee-both wrapper: forwards UCI both ways; INPUT prefixed '>' and OUTPUT verbatim to DS5LOG."""
import os, subprocess, sys, threading
ENGINE = os.environ.get("DS5ENGINE", "/tmp/ds13_base/build/forge")
log = os.environ.get("DS5LOG", "/tmp/glmflash/teeboth_default") + "." + str(os.getpid()) + ".log"
p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
lf = open(log, "a")
def pump_in():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        lf.write("> " + line); lf.flush()
        p.stdin.write(line); p.stdin.flush()
threading.Thread(target=pump_in, daemon=True).start()
while True:
    line = p.stdout.readline()
    if not line:
        break
    lf.write(line); lf.flush()
    sys.stdout.write(line); sys.stdout.flush()
