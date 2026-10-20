#!/usr/bin/env python3
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SOURCE=Path("/workspace/.cloud-setup/forge-clock-contract-source")
FLAGS=["-std=c++20","-O2","-DNDEBUG","-march=x86-64-v3","-mtune=znver5","-fno-fast-math","-ffp-contract=off","-fno-lto","-Wall","-Wextra","-Wpedantic","-Wconversion","-Wshadow"]
parser=argparse.ArgumentParser()
parser.add_argument("profile",choices=["release","asan","tsan"])
parser.add_argument("--attempt",type=int,default=1)
a=parser.parse_args()
assert a.attempt >= 1
profile=a.profile
BUILD=Path("/workspace/.cloud-setup/forge-clock-contract-"+profile)
OUT=HERE/("witnesses-"+profile+"-attempt"+str(a.attempt))
OUT.mkdir(exist_ok=False)
BIN=Path("/workspace/.cloud-setup/forge-clock-contract-diagnostics")/(profile if a.attempt == 1 else profile+"-attempt"+str(a.attempt))
BIN.mkdir(parents=True,exist_ok=False)
full=json.loads((HERE/("frozen-"+profile+"-attempt1")/"summary.json").read_text())
assert full["status"]=="PASS"
ENV=os.environ.copy()
ENV["PYTHONDONTWRITEBYTECODE"]="1"
if profile=="asan":
    ENV["ASAN_OPTIONS"]="detect_leaks=1:halt_on_error=1"
    ENV["UBSAN_OPTIONS"]="halt_on_error=1:print_stacktrace=1"
if profile=="tsan": ENV["TSAN_OPTIONS"]="halt_on_error=1:exitcode=66"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+"\n")
inputs=[HERE/"automatic-origin-api.cpp",HERE/"run-actual-api.py",HERE/"actual-api-concurrency.cpp",SOURCE/"include/forge/search.hpp",SOURCE/"src/search.cpp",BUILD/"libforge_core.a",BUILD/"forge"]
if profile=="release":inputs += [Path("/workspace/.cloud-setup/forge-tt-single-worker-gated-source/include/forge/search.hpp"),Path("/workspace/.cloud-setup/forge-tt-single-worker-gated-release/libforge_core.a")]
summary={"profile":profile,"source_commit":full["source_commit"],"started_utc":datetime.now(timezone.utc).isoformat(),"steps":[],"sha256_before":{str(p):sha(p) for p in inputs},"environment_overrides":{name:ENV[name] for name in ["PYTHONDONTWRITEBYTECODE","ASAN_OPTIONS","UBSAN_OPTIONS","TSAN_OPTIONS"] if name in ENV},"status":"RUNNING"}
save(OUT/"summary.json",summary)
def run(label,command,expected=0,timeout=180):
    print("START "+profile+" "+label,flush=True)
    start=time.monotonic()
    with (OUT/(label+".stdout")).open("xb") as stdout,(OUT/(label+".stderr")).open("xb") as stderr:
        r=subprocess.run(command,cwd=REPO,env=ENV,stdout=stdout,stderr=stderr,timeout=timeout)
    item={"label":label,"command":command,"cwd":str(REPO),"expected_exit":expected,"exit_code":r.returncode,"timeout_seconds":timeout,"elapsed_seconds":time.monotonic()-start,"stdout_sha256":sha(OUT/(label+".stdout")),"stderr_sha256":sha(OUT/(label+".stderr"))}
    summary["steps"].append(item)
    save(OUT/"summary.json",summary)
    print(json.dumps(item),flush=True)
    assert r.returncode==expected,(label,r.returncode,expected)
    return (OUT/(label+".stdout")).read_text(),(OUT/(label+".stderr")).read_text()
try:
    if profile=="release":
        old_include="/workspace/.cloud-setup/forge-tt-single-worker-gated-source/include"
        old_core="/workspace/.cloud-setup/forge-tt-single-worker-gated-release/libforge_core.a"
        old_binary=BIN/"automatic-origin-red"
        run("old-origin-compile",["g++",*FLAGS,"-I"+old_include,str(HERE/"automatic-origin-api.cpp"),old_core,"-pthread","-Wl,--export-dynamic-symbol=pthread_create","-ldl","-o",str(old_binary)])
        stdout,stderr=run("old-origin-red",[str(old_binary)],1)
        assert stdout.count("FAIL ")==5 and stdout.count("PASS ")==2 and "origin contract failures=5" in stdout and not stderr
    flags=list(FLAGS)
    if profile in ["asan","tsan"]:flags += ["-fno-pie","-no-pie","-g","-fno-omit-frame-pointer"]
    if profile=="asan":flags += ["-fsanitize=address,undefined"]
    if profile=="tsan":flags += ["-fsanitize=thread"]
    new_binary=BIN/"automatic-origin-green"
    run("origin-compile",["g++",*flags,"-I"+str(SOURCE/"include"),str(HERE/"automatic-origin-api.cpp"),str(BUILD/"libforge_core.a"),"-pthread","-Wl,--export-dynamic-symbol=pthread_create","-ldl","-o",str(new_binary)])
    stdout,stderr=run("origin-green",[str(new_binary)])
    assert stdout.count("PASS ")==7 and "origin contract failures=0" in stdout and not stderr
    actual=[sys.executable,str(HERE/"run-actual-api.py"),"--build",str(BUILD),"--label","clock-"+profile,"--source-root",str(SOURCE),"--output-dir",str(OUT/"actual-api"),"--binary-dir",str(BIN),"--optimization","O2" if profile!="release" else "O3","--sanitizer",{"release":"none","asan":"address","tsan":"thread"}[profile]]
    if profile!="release":actual += ["--non-pie"]
    run("actual-api",actual)
    api=json.loads((OUT/"actual-api"/("clock-"+profile+"-actual-api.json")).read_text())
    assert api["status"]=="passed" and len(api["completed_groups"])==7 and api["source_unchanged_during_driver"]
    if profile=="release":
        red=json.loads((HERE/"red-attempt1/identity.json").read_text())
        shim=Path(red["temp_directory"])/"libdelay.so"
        probe=HERE/"red-attempt1/native_clock_probe.py"
        candidate=HERE/"red-attempt1/candidate-origin-probe.py"
        assert sha(shim)==red["shim_sha256"]
        assert sha(probe)==red["accepted_files"]["native_clock_probe.py"]
        run("uci-origin-green",[sys.executable,str(candidate),str(BUILD/"forge"),str(shim),str(probe),str(OUT/"uci-origin")])
        uci=json.loads((OUT/"uci-origin/result.json").read_text())
        assert uci["status"]=="PASS" and all(uci["checks"].values())
        summary["uci_result"]=uci
    after={str(p):sha(p) for p in inputs}
    assert summary["sha256_before"]==after
    summary.update({"sha256_after":after,"inputs_unchanged":True,"status":"PASS","completed_utc":datetime.now(timezone.utc).isoformat()})
    save(OUT/"summary.json",summary)
    print("PASS "+profile+" automatic origin/API witnesses",flush=True)
except Exception as exc:
    summary.update({"status":"FAILED","error":repr(exc),"completed_utc":datetime.now(timezone.utc).isoformat()})
    save(OUT/"summary.json",summary)
    raise
