"""Shared helpers for the opus3_spsa tests (no engine, no games): pinned dummy files, configs, CLI runner."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE.parent
TUNER = PACK / "spsa" / "opus3_spsa.py"
PY = sys.executable


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_env(root, n_openings=64, tag="t"):
    """Pinned dummy inputs: an 'engine', a 'fastchess' and an openings PGN (train) plus a screen partition."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    exe = root / "dummy_engine.exe"
    exe.write_bytes(b"not an engine: identity-pinning fixture " + tag.encode())
    fc = root / "dummy_fastchess.exe"
    fc.write_bytes(b"not fastchess: identity-pinning fixture")
    def book(name, n, off):
        lines = []
        for i in range(n):
            lines.append(f'[Event "fixture {name} {i + off}"]\n[White "?"]\n[Black "?"]\n[Result "*"]\n\n'
                         f'1. e4 e5 2. Nf3 Nc6 {i + off} *\n')
        p = root / f"{name}.pgn"
        p.write_text("\n".join(lines), encoding="ascii", newline="\n")
        return p
    train = book("train", n_openings, 0)
    screen = book("screen", 16, 100000)
    return {"root": root, "exe": exe, "fastchess": fc, "train": train, "screen": screen}


def joint_params():
    """The joint razoring + qsearch-pruning parameter set of configs/joint_razor_qs.json (PLAN.md section 2)."""
    return [
        {"name": "RazorBase", "family": "F1", "kind": "int", "start": 150, "lock": 150, "min": 0, "max": 600,
         "c_end": 15, "r_end": 0.002},
        {"name": "RazorMultiplier", "family": "F1", "kind": "int", "start": 350, "lock": 350, "min": 100, "max": 800,
         "c_end": 35, "r_end": 0.002},
        {"name": "QsFutilityMargin", "family": "F2", "kind": "int", "start": 160, "lock": 160, "min": 40, "max": 400,
         "c_end": 16, "r_end": 0.002},
        {"name": "RazorDepth", "family": "F1", "kind": "level", "levels": [1, 2, 3], "start_level": 1, "lock": 2,
         "c_end": 1, "r_end": 0.002, "enabled": False},
        {"name": "QsSeeMargin", "family": "F2", "kind": "level", "levels": [40, 140, 240], "start_level": 0,
         "lock": 40, "c_end": 1, "r_end": 0.002, "enabled": False},
    ]


def joint_constraints():
    return [
        {"id": "C1", "coef": {"QsFutilityMargin": 1, "RazorBase": -1, "RazorMultiplier": -1}, "le": 0},
        {"id": "C2", "coef": {"QsSeeMargin": 1, "QsFutilityMargin": -1}, "le": 0, "enabled": False},
        {"id": "C3", "coef": {"RazorBase": 1, "RazorMultiplier": 2}, "le": 2000},
    ]


def make_config(env, **over):
    cfg = {
        "schema": "opus3-spsa-config/1", "name": "test", "run_nonce": over.pop("run_nonce", "0"),
        "seed": 20261110, "pairs_planned": 400, "pairs_per_batch": 4, "alpha": 0.602, "gamma": 0.101,
        "A_ratio": 0.1, "bounds_mode": "inner",
        "params": joint_params(), "constraints": joint_constraints(),
        "identity": {
            "engine_exe": {"path": str(env["exe"]), "sha256": sha(env["exe"])},
            "fastchess": {"path": str(env["fastchess"]), "sha256": sha(env["fastchess"])},
            "openings": {"path": str(env["train"]), "sha256": sha(env["train"])},
        },
        "engine": {"profile": "lock", "fixed_options": {"Threads": 1, "Hash": 16, "OwnBook": False},
                   "switch_options": {}},
        "match": {"tc": "8+0.08", "concurrency": 1, "timemargin": 1000},
        "openings": {"role": "train", "format": "pgn", "forbidden_sha256": [sha(env["screen"])]},
        "live": {"enabled": False},
        "synthetic": {"kind": "quadratic", "K": 400.0, "draw": 0.3, "seed": 7,
                      "opt": {"RazorBase": 250.0, "RazorMultiplier": 300.0, "QsFutilityMargin": 120.0},
                      "scale": {"RazorBase": 100.0, "RazorMultiplier": 150.0, "QsFutilityMargin": 60.0}},
    }
    for k, v in over.items():
        cfg[k] = v
    return cfg


def write_config(path, cfg):
    Path(path).write_text(json.dumps(cfg, indent=1), encoding="ascii")
    return Path(path)


def cli(*args, crash=None, timeout=900):
    env = dict(os.environ)
    env.pop("OPUS3_CRASH_AT", None)
    if crash:
        env["OPUS3_CRASH_AT"] = crash
    p = subprocess.run([PY, "-I", "-B", str(TUNER)] + [str(a) for a in args], capture_output=True, text=True,
                       env=env, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def run_files(run_dir):
    """Byte contents that must match between interrupted and uninterrupted runs."""
    d = Path(run_dir)
    out = {"ledger.jsonl": (d / "ledger.jsonl").read_bytes(), "HEAD.json": (d / "HEAD.json").read_bytes(),
           "RUN.json": (d / "RUN.json").read_bytes()}
    for p in sorted((d / "ckpt").glob("ckpt_*.json")):
        out["ckpt/" + p.name] = p.read_bytes()
    return out


def rmtree(path):
    if Path(path).exists():
        shutil.rmtree(path)
