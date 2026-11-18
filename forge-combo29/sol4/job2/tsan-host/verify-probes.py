import json
import os
from pathlib import Path
import subprocess


def run(argv, extra_environment=None):
    environment = os.environ.copy()
    environment.update(extra_environment or {})
    result = subprocess.run(argv, env=environment, capture_output=True, text=True, timeout=30)
    return {"argv": argv, "environment_overrides": extra_environment or {}, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def record(log, stage, configuration, probe, result, **metadata):
    print(json.dumps({"stage": stage, "configuration": configuration, "probe": probe,
                      **metadata, **result}), file=log, flush=True)


os.chdir(Path(__file__).resolve().parent)
configurations = {"default_pie": [], "non_pie": ["-fno-pie", "-no-pie"],
                  "non_pie_static_libtsan": ["-fno-pie", "-no-pie", "-static-libtsan"]}
options = {"TSAN_OPTIONS": "halt_on_error=1:exitcode=66"}
flags = ["-std=c++20", "-O1", "-g", "-fno-omit-frame-pointer", "-fsanitize=thread", "-pthread"]
summary = {}
with open("attempts.jsonl", "w") as log:
    for configuration, layout_flags in configurations.items():
        summary[configuration] = {}
        for probe, probe_flags in {"clean": [], "race": ["-DPLANTED_RACE"]}.items():
            binary = f"{configuration}-{probe}"
            build = run(["g++", *flags, *layout_flags, *probe_flags, "tsan-probe.cpp", "-o", binary])
            record(log, "compile", configuration, probe, build)
            build_ok = build["exit_code"] == 0
            counts = {"build_succeeded": build_ok, "pass": 0, "startup_rejected": 0, "other_failure": 0}
            summary[configuration][probe] = counts
            if not build_ok:
                continue
            record(log, "linkage", configuration, probe, run(["ldd", f"./{binary}"]))
            record(log, "elf", configuration, probe, run(["readelf", "-h", f"./{binary}"]))
            for attempt in range(1, 31):
                observed = run([f"./{binary}"], options)
                entered_main = "tsan probe reached main" in observed["stdout"]
                completed = "tsan probe completed, value=2" in observed["stdout"]
                warning = "WARNING: ThreadSanitizer: data race" in observed["stderr"]
                if probe == "clean" and entered_main and completed and observed["exit_code"] == 0 and not observed["stderr"]:
                    classification = "pass"
                elif probe == "race" and entered_main and warning and observed["exit_code"] == 66:
                    classification = "pass"
                elif not entered_main and "FATAL: ThreadSanitizer: unexpected memory mapping" in observed["stderr"]:
                    classification = "startup_rejected"
                else:
                    classification = "other_failure"
                counts[classification] += 1
                record(log, "run", configuration, probe, observed, attempt=attempt, classification=classification,
                       entered_main=entered_main, completed=completed, race_warning=warning)
Path("summary.json").write_text(json.dumps(summary, indent=2) + "\n")
