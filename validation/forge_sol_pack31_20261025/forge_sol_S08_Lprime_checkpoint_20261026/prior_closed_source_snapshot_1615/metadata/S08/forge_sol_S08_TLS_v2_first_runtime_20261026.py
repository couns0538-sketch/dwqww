#!/usr/bin/env python3
"""One first-ever bare-d11 invocation per frozen v2 engine; no speed claim."""
import datetime, hashlib, json, os, pathlib, re, signal, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "forge_sol_S08_TLS_v2_FIRST_native_20261026"
TARGETS = [
    ("Release", ROOT / "forge_sol_S08_v2_Release_ON_window1_20261026/build/forge", "9208252eba0bc2aee5aa383806f854dff506c1ecd11c151d647c2567c64a3de2"),
    ("ASAN", ROOT / "forge_sol_S08_ASAN_v2_window1_20261026/build/forge", "4f6b1b5e919b43e691a45f8effbe7c5a419581e9a27d1ecaa39788f0df7475c5"),
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    rows = []
    for label, binary, expected in TARGETS:
        assert sha(binary) == expected, label
        stdin = b"bench 11\nquit\n"
        (OUT / f"{label}.stdin").write_bytes(stdin)
        env = dict(os.environ)
        env.update(ASAN_OPTIONS="detect_leaks=1:halt_on_error=1", UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        start = time.monotonic()
        p = subprocess.Popen(["taskset", "-c", "4", "nice", "-n", "19", str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, start_new_session=True)
        timeout = False
        try:
            stdout, stderr = p.communicate(stdin, timeout=180)
        except subprocess.TimeoutExpired:
            timeout = True
            os.killpg(p.pid, signal.SIGTERM)
            try:
                stdout, stderr = p.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                stdout, stderr = p.communicate()
        (OUT / f"{label}.stdout").write_bytes(stdout)
        (OUT / f"{label}.stderr").write_bytes(stderr)
        counts = re.findall(rb"(?m)^info string bench depth 11 nodes (\d+) time \d+ nps \d+\r?$", stdout)
        row = dict(label=label, argv=[str(binary)], affinity=[4], nice=19, binary_sha256_before=expected, binary_sha256_after=sha(binary), started_utc=started, elapsed_seconds=time.monotonic()-start, returncode=p.returncode, timeout=timeout, stdin_sha256=hashlib.sha256(stdin).hexdigest(), stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest(), bench_counts=[int(v) for v in counts], first_runtime_bare_bench=True, no_uci_before_bench=True, no_speed_claim=True)
        row["pass"] = p.returncode == 0 and not timeout and counts == [b"308972"] and not stderr and row["binary_sha256_after"] == expected
        rows.append(row)
        (OUT / "forge_sol_S08_TLS_v2_first_runtime_result_20261026.json").write_text(json.dumps(dict(results=rows, status="PASS" if all(r["pass"] for r in rows) else "FAIL"), indent=2)+"\n")
        print(json.dumps(row), flush=True)
    return 0 if all(r["pass"] for r in rows) else 1

if __name__ == "__main__":
    raise SystemExit(main())
