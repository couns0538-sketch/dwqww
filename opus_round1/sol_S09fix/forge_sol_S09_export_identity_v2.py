#!/usr/bin/env python3
"""S09-1: confirm that the S09 v2 trainer's `--buckets 1` export is byte-identical to the current v3b trainer.

Mode `roundtrip`: for every given net (.inc), build the model of BOTH trainers from the net's int16 weights
(value / 4096, exact in float32), export with each trainer's own export_forge(), and compare
  current .inc == v2 .inc == the original .inc file, and current .bin == v2 .bin.
For an 8-head net only the v2 trainer can export; its int16 arrays must equal the input's (the header comment and
the head macro spelling of another exporter may differ and are reported, not hidden).
Mode `compare-runs`: compare two training run folders file by file (every epoch .pt/.inc/.bin/.json byte for byte)
and their settings files (parsed args; the v2-only key `buckets` must be 1 and is then ignored; argv/time differ).
The trainers are imported from renamed copies (opus_nnue_smoke_*.py); nothing is trained by this tool.
usage:
  forge_sol_S09_export_identity_v2.py roundtrip --current C.py --v2 V.py --out DIR --net NAME=PATH [--net ...]
  forge_sol_S09_export_identity_v2.py compare-runs A_DIR B_DIR [--json out.json]
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, sys
from pathlib import Path

import numpy as np

ARR = re.compile(r"static const std::int16_t (NnueW1|NnueB1|NnueW2|NnueB2)(?:\[(\d+)\])? = ")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def parse_inc(path):
    text = Path(path).read_text(encoding="ascii")
    arrays, header = {}, []
    for chunk in re.split(r"(?=static const std::int16_t )", text):
        m = ARR.match(chunk)
        if not m:
            header.append(chunk)
            continue
        body = chunk[m.end():].split(";")[0]
        nums = [int(x) for x in re.findall(r"-?\d+", body)]
        if m[2] is not None and len(nums) != int(m[2]):
            raise ValueError(f"{m[1]}: {len(nums)} values, declared {m[2]}")
        arrays[m[1]] = np.asarray(nums, dtype=np.int16)
    head = "".join(header)
    hidden = arrays["NnueB1"].size
    heads = arrays["NnueB2"].size
    if arrays["NnueW1"].size != 768 * hidden or arrays["NnueW2"].size != heads * 2 * hidden:
        raise ValueError("inconsistent array sizes")
    residual = "#define FORGE_NNUE_RESIDUAL 1" in head
    macro = re.findall(r"#define (FORGE_NNUE_OUTPUT_\w+) (\d+)", head)
    return {"arrays": arrays, "hidden": hidden, "heads": heads, "residual": residual, "head_macro": macro,
            "first_line": head.splitlines()[0] if head else ""}


def load_trainer(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def model_from_net(mod, net, buckets=None):
    import torch
    kw = {} if buckets is None else {"buckets": buckets}
    m = mod.NNUE(net["hidden"], qat=True, residual=net["residual"], **kw)
    a, h, n = net["arrays"], net["hidden"], net["heads"]
    with torch.no_grad():
        m.ft.weight.copy_(torch.from_numpy(a["NnueW1"].astype(np.float32).reshape(768, h).T / 4096.0))
        m.ft.bias.copy_(torch.from_numpy(a["NnueB1"].astype(np.float32) / 4096.0))
        m.out.weight.copy_(torch.from_numpy(a["NnueW2"].astype(np.float32).reshape(n, 2 * h) / 4096.0))
        m.out.bias.copy_(torch.from_numpy(a["NnueB2"].astype(np.float32) / 4096.0))
    return m


def roundtrip(a):
    cur = load_trainer(a.current, "s09_current_trainer")
    v2 = load_trainer(a.v2, "s09_v2_trainer")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    rows, ok = [], True
    for spec in a.net:
        name, _, path = spec.partition("=")
        net = parse_inc(path)
        row = {"net": name, "path": path, "sha256": sha(path), "hidden": net["hidden"], "heads": net["heads"],
               "residual": net["residual"], "head_macro": net["head_macro"]}
        if net["heads"] == 1:
            cur.export_forge(model_from_net(cur, net), out / f"{name}_current", 2.25, net["residual"])
            v2.export_forge(model_from_net(v2, net, buckets=1), out / f"{name}_v2", 2.25, net["residual"])
            for ext in ("inc", "bin"):
                row[f"current_{ext}_sha256"] = sha(out / f"{name}_current.{ext}")
                row[f"v2_{ext}_sha256"] = sha(out / f"{name}_v2.{ext}")
            row["v2_inc_eq_current_inc"] = row["v2_inc_sha256"] == row["current_inc_sha256"]
            row["v2_bin_eq_current_bin"] = row["v2_bin_sha256"] == row["current_bin_sha256"]
            row["v2_inc_eq_original"] = row["v2_inc_sha256"] == row["sha256"]
            row["status"] = "PASS" if (row["v2_inc_eq_current_inc"] and row["v2_bin_eq_current_bin"]
                                       and row["v2_inc_eq_original"]) else "FAIL"
        else:
            v2.export_forge(model_from_net(v2, net, buckets=net["heads"]), out / f"{name}_v2", 2.25, net["residual"])
            back = parse_inc(out / f"{name}_v2.inc")
            same = all(np.array_equal(back["arrays"][k], net["arrays"][k]) for k in net["arrays"])
            row.update(v2_inc_sha256=sha(out / f"{name}_v2.inc"), v2_arrays_eq_original=same,
                       v2_head_macro=back["head_macro"], original_first_line=net["first_line"],
                       v2_first_line=back["first_line"], v2_inc_eq_original=sha(out / f"{name}_v2.inc") == row["sha256"],
                       status="PASS_ARRAYS" if same else "FAIL")
        ok &= row["status"].startswith("PASS")
        rows.append(row)
        print(json.dumps({k: row[k] for k in row if k not in ("path",)}))
    (out / "roundtrip_result.json").write_text(json.dumps({"current": str(a.current), "current_sha256": sha(a.current),
                                                           "v2": str(a.v2), "v2_sha256": sha(a.v2), "rows": rows},
                                                          indent=1) + "\n", encoding="utf-8", newline="\n")
    print("ALL PASS" if ok else "FAIL")
    return 0 if ok else 1


def settings(run):
    files = sorted(Path(run).glob("settings_*.txt"))
    if len(files) != 1:
        raise ValueError(f"{run}: expected one settings file, found {len(files)}")
    text = files[0].read_text(encoding="utf-8")
    argv, _, js = text.partition("\n")
    return argv, json.loads(js)


def compare_runs(a):
    A, B = Path(a.a), Path(a.b)
    names_a = sorted(p.name for p in A.iterdir() if p.is_file() and not p.name.startswith("settings_"))
    names_b = sorted(p.name for p in B.iterdir() if p.is_file() and not p.name.startswith("settings_"))
    rows = []
    for n in sorted(set(names_a) | set(names_b)):
        pa, pb = A / n, B / n
        if not (pa.exists() and pb.exists()):
            rows.append({"file": n, "status": "MISSING_IN_" + ("B" if pa.exists() else "A")})
            continue
        rows.append({"file": n, "bytes": pa.stat().st_size, "sha256_a": sha(pa), "sha256_b": sha(pb),
                     "status": "IDENTICAL" if pa.read_bytes() == pb.read_bytes() else "DIFFERENT"})
    _, sa = settings(A)
    _, sb = settings(B)
    extra = {k: (sa.get(k), sb.get(k)) for k in set(sa) ^ set(sb)}
    bucket_ok = all(v in (None, 1) for pair in extra.values() for v in pair) and set(extra) <= {"buckets"}
    diff = {k: (sa[k], sb[k]) for k in set(sa) & set(sb) if sa[k] != sb[k] and k != "run_dir"}
    ok = rows and all(r["status"] == "IDENTICAL" for r in rows) and bucket_ok and not diff
    res = {"a": str(A), "b": str(B), "files": rows, "settings_only_in_one": extra, "settings_differ": diff,
           "status": "PASS" if ok else "FAIL"}
    for r in rows:
        print(f"{r['status']:10} {r['file']}")
    print(f"settings: only-in-one {extra}; differing (excl. run_dir) {diff}")
    print(res["status"])
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("roundtrip")
    r.add_argument("--current", required=True)
    r.add_argument("--v2", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--net", action="append", required=True)
    c = sub.add_parser("compare-runs")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--json")
    a = ap.parse_args(argv)
    return roundtrip(a) if a.mode == "roundtrip" else compare_runs(a)


if __name__ == "__main__":
    sys.exit(main())
