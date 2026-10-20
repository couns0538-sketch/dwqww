#!/usr/bin/env python3
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time

REPO=Path("/workspace/dwqww")
HERE=Path(__file__).resolve().parent
REV="47f0560221d986e41a309853e1295c557fcf5bf6"
SOURCE=Path("/workspace/.cloud-setup/forge-promotion-source")
CMAKE="/workspace/.cloud-setup/venv/bin/cmake"
CTEST="/workspace/.cloud-setup/venv/bin/ctest"
FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto"
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def files(root): return {str(p.relative_to(root)):digest(p) for p in sorted(root.rglob("*")) if p.is_file()}
def write(path,data): path.write_text(json.dumps(data,indent=2)+"\n")
parser=argparse.ArgumentParser()
parser.add_argument("profile",choices=["release","asan","tsan"])
args=parser.parse_args()
profile=args.profile
OUT=HERE/("frozen-"+profile+"-attempt1")
OUT.mkdir(exist_ok=False)
BUILD=Path("/workspace/.cloud-setup/forge-promotion-"+profile)
if BUILD.exists(): raise SystemExit("Refusing existing build directory: "+str(BUILD))
archive=subprocess.check_output(["git","archive",REV,"CMakeLists.txt","LICENSE","src","include","tests","bench","tools"],cwd=REPO)
expected_tar=HERE/"frozen-source-47f0560.tar"
if not expected_tar.exists(): expected_tar.write_bytes(archive)
assert expected_tar.read_bytes()==archive
if not SOURCE.exists():
    SOURCE.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar: tar.extractall(SOURCE,filter="data")
before=files(SOURCE)
archive_members={}
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    for member in tar.getmembers():
        if member.isfile(): archive_members[member.name]=hashlib.sha256(tar.extractfile(member).read()).hexdigest()
assert before==archive_members
write(HERE/"frozen-source-47f0560-files.json",before)
ENV=os.environ.copy()
ENV["PYTHONDONTWRITEBYTECODE"]="1"
if profile=="asan":
    ENV["ASAN_OPTIONS"]="detect_leaks=1:halt_on_error=1"
    ENV["UBSAN_OPTIONS"]="halt_on_error=1:print_stacktrace=1"
elif profile=="tsan": ENV["TSAN_OPTIONS"]="halt_on_error=1:exitcode=66"
config=[CMAKE,"-S",str(SOURCE),"-B",str(BUILD),"-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
if profile=="release": config += ["-DCMAKE_BUILD_TYPE=Release","-DFORGE_ENABLE_SANITIZERS=OFF","-DCMAKE_CXX_FLAGS="+FLAGS]
elif profile=="asan": config += ["-DCMAKE_BUILD_TYPE=RelWithDebInfo","-DFORGE_ENABLE_SANITIZERS=ON","-DCMAKE_CXX_FLAGS="+FLAGS+" -fno-pie","-DCMAKE_EXE_LINKER_FLAGS=-no-pie"]
else: config += ["-DCMAKE_BUILD_TYPE=RelWithDebInfo","-DFORGE_ENABLE_SANITIZERS=OFF","-DCMAKE_CXX_FLAGS="+FLAGS+" -fsanitize=thread -fno-omit-frame-pointer -fno-pie","-DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread -no-pie"]
summary={"source_commit":REV,"source_export":str(SOURCE),"source_archive_sha256":hashlib.sha256(archive).hexdigest(),
         "profile":profile,"started_utc":datetime.now(timezone.utc).isoformat(),"steps":[],
         "environment_overrides":{name:ENV[name] for name in ["PYTHONDONTWRITEBYTECODE","ASAN_OPTIONS","UBSAN_OPTIONS","TSAN_OPTIONS"] if name in ENV},
         "tsan_deadlock_detector":"default enabled; no disabling options", "status":"RUNNING"}
write(OUT/"summary.json",summary)
def run(label,command,timeout=1200):
    print("START "+profile+" "+label,flush=True)
    start=time.monotonic()
    with (OUT/(label+".stdout")).open("xb") as stdout, (OUT/(label+".stderr")).open("xb") as stderr:
        done=subprocess.run(command,cwd=REPO,env=ENV,stdout=stdout,stderr=stderr,timeout=timeout)
    step={"label":label,"command":command,"cwd":str(REPO),"timeout_seconds":timeout,
          "exit_code":done.returncode,"elapsed_seconds":time.monotonic()-start,
          "stdout_sha256":digest(OUT/(label+".stdout")),"stderr_sha256":digest(OUT/(label+".stderr"))}
    summary["steps"].append(step)
    write(OUT/"summary.json",summary)
    print(json.dumps(step),flush=True)
    if done.returncode: raise RuntimeError(label+" failed with exit "+str(done.returncode))
try:
    run("configure",config)
    run("build",[CMAKE,"--build",str(BUILD),"--parallel","2"])
    binary_before={name:digest(BUILD/name) for name in ["forge","forge_tests","forge_tt_tests","forge_rule50_tests","forge_legal_witness_tests","libforge_core.a"]}
    summary["binary_sha256_before"] = binary_before
    write(OUT/"summary.json",summary)
    run("ctest",[CTEST,"--test-dir",str(BUILD),"--output-on-failure","-j","1"])
    assert "100% tests passed, 0 tests failed out of 9" in (OUT/"ctest.stdout").read_text()
    binary_after={name:digest(BUILD/name) for name in binary_before}
    after=files(SOURCE)
    assert before==after
    assert binary_before==binary_after
    summary.update({"binary_sha256_before":binary_before,"binary_sha256_after":binary_after,
                    "source_files_unchanged":True,"status":"PASS","completed_utc":datetime.now(timezone.utc).isoformat()})
    write(OUT/"summary.json",summary)
    print("PASS "+profile+" full CTest 9/9; source and binary hashes unchanged",flush=True)
except Exception as exc:
    summary["binary_sha256_after_failure"] = {name:digest(BUILD/name) for name in ["forge","forge_tests","forge_tt_tests","forge_rule50_tests","forge_legal_witness_tests","libforge_core.a"] if (BUILD/name).is_file()}
    summary["source_files_unchanged_after_failure"] = before == files(SOURCE)
    summary.update({"status":"FAILED","error":repr(exc),"completed_utc":datetime.now(timezone.utc).isoformat()})
    write(OUT/"summary.json",summary)
    raise
finally:
    for name in ["ownbook-regression.json", "Testing/Temporary/LastTest.log", "uci-regression.log"]:
        original = BUILD/name
        if original.is_file():
            (OUT/("original-"+original.name)).write_bytes(original.read_bytes())
