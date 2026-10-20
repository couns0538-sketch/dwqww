#!/usr/bin/env python3
import json,os,signal,subprocess,sys,threading,time
from pathlib import Path
root=Path('/workspace/.cloud-setup/clock-audit')
root.mkdir(exist_ok=True)
log=(root/f'uci-{os.getpid()}.jsonl').open('x',buffering=1)
child=subprocess.Popen(sys.argv[1:] or ['/workspace/.cloud-setup/forge-avx2-build/forge'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
lock=threading.Lock()
def record(direction,line):
    now=time.monotonic_ns()
    try:
        fields=Path(f'/proc/{child.pid}/stat').read_text().split()
        cpu=int(fields[13])+int(fields[14])
    except (FileNotFoundError,IndexError,ValueError):cpu=None
    with lock:log.write(json.dumps({'t_ns':now,'direction':direction,'line':line.rstrip(),'child_cpu_ticks':cpu})+'\n')
def output():
    for line in child.stdout:
        record('out',line)
        sys.stdout.write(line);sys.stdout.flush()
def stop(signum,frame):
    child.terminate()
    raise SystemExit(128+signum)
for signum in (signal.SIGTERM,signal.SIGINT):signal.signal(signum,stop)
thread=threading.Thread(target=output,daemon=True);thread.start()
record('meta',json.dumps({'pid':child.pid,'affinity':sorted(os.sched_getaffinity(0)),'clock_ticks':os.sysconf('SC_CLK_TCK')}))
try:
    for line in sys.stdin:
        record('in',line)
        child.stdin.write(line);child.stdin.flush()
        if line.strip()=='quit':break
    child.stdin.close()
    rc=child.wait(timeout=15)
    thread.join(timeout=2)
    raise SystemExit(rc)
finally:
    if child.poll() is None:child.kill();child.wait()
