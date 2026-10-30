"""R11 package stage: one gate-ready folder per net that PASSED the check stage (hand-off to QA; never queued).

<root>/gate_ready/<net stem>_<net sha256[:8]>/
  <net>.nnue            the net (copied, sha256 verified against check.json)
  forge_<commit>_<march>.exe   the checked engine build (copied, sha256 verified)
  SHA256SUMS            every file of the folder
  bench.txt             ON bench d11..d22 (EvalFileHalfKA=<net>, Threads 1, Hash 16) and the OFF identity lines
  parity.log            fens_12k parity (Forge HalfKA kernels vs nnue-pytorch float64)
  wac.txt               WAC 300 at 200 ms, ON and OFF
  check.json            the full check record (build flags, FMA/zmm counts, numbers)
  provenance.json       where the net came from (checkpoint, training run, data manifest) when known
  README.md             what it is, how it was checked, the UCI option, the hand-off note
  PACKAGE_DONE          written last; a folder without it is incomplete and is never overwritten
Usage: r11_package.py --config <cfg.json> --check <check dir> [--provenance <json>]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r11_common as C  # noqa: E402


def _copy_verified(src: str, dst: str, sha: str) -> None:
    if os.path.exists(dst):
        if C.sha256_file(dst) != sha:
            raise C.StageFailed(f"{dst} exists with other content; not overwriting")
        return
    tmp = dst + ".part"
    if os.path.exists(tmp):
        raise C.StageFailed(f"leftover {tmp}; not overwriting")
    shutil.copyfile(src, tmp)
    if C.sha256_file(tmp) != sha:
        raise C.StageFailed(f"copy of {src} does not match sha256 {sha}")
    os.replace(tmp, dst)


def package(cfg: dict, check_dir: str, log: C.Log, provenance: dict | None = None) -> dict:
    chk = C.read_json(os.path.join(check_dir, "check.json"))
    if not chk:
        raise C.StageFailed(f"no check.json in {check_dir}")
    net = chk["net"]
    stem = os.path.splitext(os.path.basename(net))[0]
    if not chk.get("pass"):
        log.fail(f"package {stem}: the check did not pass; no gate-ready folder")
        return {"packaged": False, "reason": "check failed"}
    out = os.path.join(cfg["root"], "gate_ready", f"{stem}_{chk['net_sha256'][:8]}")
    C.assert_writable_path(out)
    if os.path.isfile(os.path.join(out, "PACKAGE_DONE")):
        log.info(f"package {stem}: already done ({out})")
        return {"packaged": True, "dir": C.winpath(out), "existing": True}
    os.makedirs(out, exist_ok=True)
    b = chk["build"]
    net_dst = os.path.join(out, os.path.basename(net))
    exe_dst = os.path.join(out, os.path.basename(b["exe"]))
    if C.sha256_file(net) != chk["net_sha256"]:
        raise C.StageFailed(f"{net} changed since the check (sha256 differs); re-run the check")
    _copy_verified(net, net_dst, chk["net_sha256"])
    _copy_verified(b["exe"], exe_dst, b["exe_sha256"])
    shutil.copyfile(os.path.join(check_dir, "parity.log"), os.path.join(out, "parity.log"))
    shutil.copyfile(os.path.join(check_dir, "check.json"), os.path.join(out, "check.json"))
    on = chk["on"]
    off = chk["off"]
    bench = [f"engine {os.path.basename(b['exe'])} sha256 {b['exe_sha256']} (commit {b['commit_full']}, -march={b['march']}, "
             f"FMA {b['fma_count_exe']}, zmm {b['zmm_count_exe']})",
             f"net {os.path.basename(net)} sha256 {chk['net_sha256']}", "",
             "ON  (setoption Threads 1, Hash 16, OwnBook false, EvalFileHalfKA <net>):"]
    bench += [f"  {on['lines'][str(d)]}" for d in on["depths"]]
    bench += [f"  d11 repeat {on.get('d11_repeat')}, after a reload {on.get('d11_reload')}, after <empty> (OFF) "
              f"{on.get('off_after')}", "", "OFF (lock identity, uci_check.py --full):"]
    bench += ["  " + ln for ln in off.get("output_tail", "").splitlines() if ln.startswith(("bench", "perft", "ALL"))]
    C.write_text(os.path.join(out, "bench.txt"), "\n".join(bench) + "\n")
    wac = [f"WAC 300 at {chk['wac_on']['movetime_ms']} ms, Threads 1, Hash 16, fresh ucinewgame + Clear Hash per position",
           f"ON  (EvalFileHalfKA=<net>): {chk['wac_on']['solved']} / {chk['wac_on']['positions']}",
           f"OFF (lock eval, same exe):  {chk['wac_off']['solved']} / {chk['wac_off']['positions']}",
           "A tactics sanity check, not a strength measurement."]
    C.write_text(os.path.join(out, "wac.txt"), "\n".join(wac) + "\n")
    prov = provenance or {}
    C.write_json(os.path.join(out, "provenance.json"), prov)
    p = chk["parity"]
    readme = f"""# Gate-ready package: {os.path.basename(net)}

Made by the R11 NNUE pipeline (branch opus-r11-nnue-pipeline) on {time.strftime('%Y-%m-%d %H:%M')} PC clock.
**Hand-off to QA. Not queued: no queue.txt / queue_state.json / forge_gates.json / lock / baseline was touched.**
QA runs Code Review and queues it against the current lock.

| item | value |
|---|---|
| net | `{os.path.basename(net)}`, {chk['net_bytes']:,} bytes, sha256 `{chk['net_sha256']}` |
| architecture | nnue-pytorch b2614500 K32H3^ (HalfKAv2_hm family), L1 {chk['l1']} |
| engine | `{os.path.basename(b['exe'])}`, sha256 `{b['exe_sha256']}`, built from `{b['commit_full']}` (qa-r10v2-fix1) with the box recipe + `-march={b['march']}` (AVX2, FMA {b['fma_count_exe']}, zmm {b['zmm_count_exe']}) |
| UCI | `setoption name EvalFileHalfKA value <absolute Windows path of the .nnue>` (empty = off = lock eval) |
| parity (fens_12k) | **{p['exact']} / {p['fens_count']} exact** vs nnue-pytorch float64, max raw diff {p['max_raw_diff']}, SIMD ({p['simd']}) vs scalar mismatches {p['simd_vs_scalar_mismatches']} |
| OFF identity | {'ALL OK' if off['ok'] else 'FAILED'} (bench d11 {off.get('bench_d11')}) |
| ON bench | {', '.join(f"d{d} {on['nodes'][str(d)]:,}" for d in on['depths'])} (d11 stable over a repeat and a reload) |
| WAC 300 (200 ms) | ON {chk['wac_on']['solved']} / 300, OFF {chk['wac_off']['solved']} / 300 |

Files: see `SHA256SUMS`. Details: `bench.txt`, `parity.log`, `wac.txt`, `check.json`, `provenance.json`.
No Elo claim: strength is decided by QA's gate.
"""
    C.write_text(os.path.join(out, "README.md"), readme)
    sums = []
    for fn in sorted(os.listdir(out)):
        fp = os.path.join(out, fn)
        if os.path.isfile(fp) and fn not in ("SHA256SUMS", "PACKAGE_DONE") and not fn.endswith(".part"):
            sums.append(f"{C.sha256_file(fp)}  {fn}")
    C.write_text(os.path.join(out, "SHA256SUMS"), "\n".join(sums) + "\n")
    C.write_text(os.path.join(out, "PACKAGE_DONE"), time.strftime("%Y-%m-%dT%H:%M:%S") + "\n")
    log.ok(f"package {stem}: gate-ready folder {C.winpath(out)} ({len(sums)} files)")
    return {"packaged": True, "dir": C.winpath(out)}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--check", required=True)
    ap.add_argument("--provenance")
    a = ap.parse_args(argv)
    cfg = C.read_json(a.config)
    log = C.Log(os.path.join(cfg["root"], "logs", "pipeline.log"), "package")
    try:
        res = package(cfg, a.check, log, C.read_json(a.provenance) if a.provenance else None)
        return 0 if res.get("packaged") else 1
    except C.StageFailed as e:
        log.fail(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
