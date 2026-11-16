#!/usr/bin/env python3
"""gprof_run.py OUTDIR [REPS] -- independent profile of the BASE build with gprof (perf is unavailable:
this kernel 6.12.113+ has no linux-tools package in this image). Four bench-16 runs in one process give
~4.5 s of samples, which is enough for a flat profile.

Build: cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-pg -fno-omit-frame-pointer" -DCMAKE_EXE_LINKER_FLAGS=-pg
Run:   this script, then `gprof -b <exe> gmon.out`
"""
import os, subprocess, sys, json
EXE=os.path.expanduser("~/builds/gprof/forge")
OUT=os.path.abspath(sys.argv[1]); REPS=int(sys.argv[2]) if len(sys.argv)>2 else 4
os.makedirs(OUT,exist_ok=True)
lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16","isready","ucinewgame","isready"]
lines+= ["bench 16"]*REPS
p=subprocess.run([EXE], input="\n".join(lines)+"\n", capture_output=True, text=True, timeout=1800, cwd=OUT)
open(os.path.join(OUT,"run.log"),"w").write(p.stdout+"\n=== stderr\n"+p.stderr)
gm=os.path.join(OUT,"gmon.out")
g=subprocess.run(["gprof","-b",EXE,gm], capture_output=True, text=True, timeout=300)
open(os.path.join(OUT,"gprof_flat.txt"),"w").write(g.stdout)
print(p.stdout[-400:])
print(g.stdout[:1200])
