"""Run the four authorized S28 cases serially and retain untouched subprocess bytes."""
from pathlib import Path
import argparse, base64, datetime, hashlib, json, os, subprocess, sys

def seal(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "encoding": "base64", "data": base64.b64encode(data).decode("ascii")}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tool", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    tool = args.tool.resolve(strict=True)
    home = Path("/workspace/forge-pack24-20261025")
    pack = home / "forge_sol_jobpack_24jobs_20261025/files"
    cmroot = Path("/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin")
    bases = {"L": pack / "01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src",
             "B": pack / "01b_base_h256_e12_buffix/forge_h256_e12_buffix_src"}
    nets = {"lock": bases["L"] / "src/nnue_weights.inc",
            "f006": pack / "03_nets/resid_h256_e48_f006_b06_ep48.inc"}
    queue = home / "S28/forge_sol_S28_native_queue_20261025.json"
    helper = home / "S01/forge_sol_S01_delivery_v2_20261025/forge_sol_S01_rerecord_pins_20261025.py"
    args.out.mkdir(parents=False, exist_ok=False)
    report = {"status": "INCOMPLETE", "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "tool": str(tool), "tool_sha256": hashlib.sha256(tool.read_bytes()).hexdigest(),
              "queue_sha256": hashlib.sha256(queue.read_bytes()).hexdigest(), "runs": []}
    result = args.out / "forge_sol_S28_native_controller_result_20261025.json"
    def checkpoint():
        result.write_text(json.dumps(report, indent=2) + "\n")
    checkpoint()
    try:
        for netname in ("lock", "f006"):
            for basename, tree in bases.items():
                tag = basename + "_" + netname
                prefix = [sys.executable, "-B", str(tool)] if tool.suffix == ".py" else ["bash", str(tool)]
                command = prefix + ["--tree", str(tree), "--net", str(nets[netname]),
                           "--out", str(args.out / ("forge_sol_S28_" + tag + "_20261025")),
                           "--execute", "--pin-helper", str(helper), "--cmake", str(cmroot / "cmake"),
                           "--ctest", str(cmroot / "ctest"), "--fma-checker",
                           str(pack / "04_refs/check_nnue_simd_v2_fma_checker.py"), "--jobs", "2"]
                if netname == "f006": command += ["--queue", str(queue)]
                row = {"case": tag, "argv": command, "status": "RUNNING",
                       "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
                report["runs"].append(row)
                checkpoint()
                print("START", tag, flush=True)
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
                proc = subprocess.run(command, cwd=args.out, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                row.update(status="PASS" if proc.returncode == 0 else "FAIL", exit=proc.returncode,
                           ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           stdout=seal(proc.stdout), stderr=seal(proc.stderr))
                checkpoint()
                print(row["status"], tag, "exit", proc.returncode, flush=True)
                if proc.returncode: raise RuntimeError(tag + " failed; later cases not run")
        report["status"] = "PASS"
    except Exception as error:
        report["error"] = str(error)
        report["status"] = "FAIL"
    finally:
        report["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        checkpoint()
    return 0 if report["status"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
