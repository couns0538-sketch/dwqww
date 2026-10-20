#!/usr/bin/env python3
"""Reproduce accepted timed-only origin contract on unchanged frozen886 engine."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ACCEPTED = "356e863dbd86d2ce24b8ee9486d7406f1d525480"
FROZEN = "8865666cc0ab4961cd507bae40ff6ce44e9319df"
BINARY = Path("/workspace/.cloud-setup/forge-tt-single-worker-gated-release/forge")
SOURCE_EXPORT = Path("/workspace/.cloud-setup/forge-tt-single-worker-gated-source")
PREFIX = "validation/hourly/2026-10-20-go-origin-native/"
OUT = HERE / "red-attempt1"
OUT.mkdir(exist_ok=False)
TEMP = Path(tempfile.mkdtemp(prefix="forge-clock-red-", dir="/tmp"))
ENV = os.environ.copy()
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
steps = []
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def blob(path):
    return subprocess.check_output(["git", "show", ACCEPTED + ":" + PREFIX + path], cwd=REPO)
def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")
def logged(label, command, expected=0):
    start = time.monotonic()
    with (OUT / (label + ".stdout")).open("xb") as stdout, (OUT / (label + ".stderr")).open("xb") as stderr:
        done = subprocess.run(command, cwd=REPO, env=ENV, stdout=stdout, stderr=stderr, timeout=40)
    item = {"label":label, "command":command, "cwd":str(REPO), "exit_code":done.returncode,
            "expected_exit_code":expected, "elapsed_seconds":time.monotonic()-start,
            "stdout_sha256":sha(OUT/(label+".stdout")), "stderr_sha256":sha(OUT/(label+".stderr"))}
    steps.append(item)
    save_json(OUT / "commands.json", steps)
    print(json.dumps(item), flush=True)
    if done.returncode != expected:
        raise RuntimeError(f"{label}: exit {done.returncode}, expected {expected}")
    return done

identity = {"started_utc":datetime.now(timezone.utc).isoformat(), "accepted_source":ACCEPTED,
            "frozen_engine_source":FROZEN, "binary":str(BINARY), "temp_directory":str(TEMP),
            "kind":"timing origin regression only; no benchmark/match/strength inference"}
save_json(OUT/"identity.json",identity)
try:
    prior=json.loads((REPO/"validation/single-thread-tt-20261020/parity-gated-attempt1/inputs.json").read_text())
    expected=prior["engines"]["candidate"]["sha256"]
    identity["binary_sha256_before"]=sha(BINARY)
    identity["binary_sha256_expected"]=expected
    assert identity["binary_sha256_before"] == expected
    checks={}
    for path in ["include/forge/search.hpp","src/search.cpp","src/uci.cpp","CMakeLists.txt"]:
        committed=subprocess.check_output(["git","show",FROZEN+":"+path],cwd=REPO)
        frozen_sha=hashlib.sha256(committed).hexdigest()
        export=SOURCE_EXPORT/path
        checks[path]={"commit_sha256":frozen_sha,"export_sha256":sha(export)}
        assert checks[path]["commit_sha256"] == checks[path]["export_sha256"]
    identity["frozen_source_checks"]=checks
    identity["build_metadata_checks"]={}
    for path,expected_hash in prior["frozen_sha256"].items():
        if path.startswith(str(BINARY.parent)+"/"):
            identity["build_metadata_checks"][path]={"sha256":sha(path),"expected":expected_hash}
            assert sha(path)==expected_hash
    identity["accepted_files"]={}
    for name in ["native_clock_probe.py","delayed_pthread_create.c","native_probe_fixture.cpp"]:
        data=blob(name)
        (TEMP/name).write_bytes(data)
        (OUT/name).write_bytes(data)
        identity["accepted_files"][name]=hashlib.sha256(data).hexdigest()
    save_json(OUT/"identity.json",identity)
    logged("shim-build",["cc","-std=gnu11","-O2","-fPIC","-shared","-Wall","-Wextra","-Werror",
                         "-o",str(TEMP/"libdelay.so"),str(TEMP/"delayed_pthread_create.c"),"-ldl"])
    fixtures={}
    for label,define in [("baseline",None),("scoped","FIX_GO_ORIGIN"),("unscoped","BAD_GO_ORIGIN_ALL")]:
        binary=TEMP/("fixture-"+label)
        command=["g++","-std=c++20","-O2","-pthread"]
        if define: command.append("-D"+define)
        command += [str(TEMP/"native_probe_fixture.cpp"),"-o",str(binary)]
        logged("fixture-build-"+label,command)
        fixtures[label]=binary
    for label,expected_exit in [("scoped",0),("unscoped",1)]:
        command=[sys.executable,str(TEMP/"native_clock_probe.py"),"--baseline",str(fixtures["baseline"]),
                 "--candidate",str(fixtures[label]),"--shim",str(TEMP/"libdelay.so"),"--out",str(OUT/("fixture-"+label)),"--delay-ms","440"]
        logged("fixture-probe-"+label,command,expected_exit)
    candidate = OUT / "candidate-origin-probe.py"
    candidate.write_text("""import hashlib, json, pathlib, runpy, sys
binary, shim, probe, out = map(pathlib.Path, sys.argv[1:])
out.mkdir(exist_ok=False)
ns = runpy.run_path(str(probe), run_name='accepted_clock_probe')
results = [ns['run_trial'](binary, shim, 'candidate_timed', 'go movetime 1200', out, 440),
           ns['run_trial'](binary, shim, 'candidate_depth', 'go depth 1', out, 440)]
checks = {'timed_origin': results[0]['first_info_time_ms'] >= 380,
          'analysis_origin': results[1]['first_info_time_ms'] < 220}
summary = {'status': 'PASS' if all(checks.values()) else 'INCONCLUSIVE_OR_FAIL',
           'scope': 'candidate-side origin checks from unchanged accepted probe; not full baseline comparison',
           'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
           'checks': checks, 'results': results}
(out/'result.json').write_text(json.dumps(summary, indent=2)+'\\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
""")
    logged("frozen886-candidate-probe",[sys.executable,str(candidate),str(BINARY),str(TEMP/"libdelay.so"),
                                        str(TEMP/"native_clock_probe.py"),str(OUT/"frozen886")],1)
    result=json.loads((OUT/"frozen886/result.json").read_text())
    assert result["checks"] == {"timed_origin":True,"analysis_origin":False}
    identity["binary_sha256_after"]=sha(BINARY)
    assert identity["binary_sha256_after"]==identity["binary_sha256_before"]
    identity["completed_utc"]=datetime.now(timezone.utc).isoformat()
    identity["shim_sha256"]=sha(TEMP/"libdelay.so")
    identity["fixture_binaries_sha256"]={name:sha(path) for name,path in fixtures.items()}
    identity["status"]="EXPECTED_RED_CONFIRMED"
    identity["result"]=result
    save_json(OUT/"identity.json",identity)
    print(json.dumps({"status":identity["status"],"evidence":str(OUT),"result":result},indent=2))
except Exception as exc:
    identity["status"]="DRIVER_FAILED"
    identity["error"]=repr(exc)
    save_json(OUT/"identity.json",identity)
    raise
