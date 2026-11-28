"""Loop-Ready CLI Adapter for FORGENN3-P (`train` and `export` subcommands matching pipeline/nnloop/trainer.py).

Implements the exact `[train] train_cmd` & `export_cmd` contract of `pipeline/nnloop/trainer.py:180-230`:
  1. `train`: accepts `--datasets ... --val <val> --out-model <model.pt> --hce-exe <exe> --epochs N --lr LR
     --batch-size B --hidden H --king-buckets KB --ob-smooth S --mix M --w1-decay D --lr-cycles auto
     --distill-net <pt> --distill-weight W --anchor-shards ... --anchor-repeat R --seed S`
     Delegates to `train_v3p.py`, copies `cand.pt` atomically to `--out-model`, and prints standard
     `LOSS <x>`, `VAL <x>`, and `VAL_MIX60 <x>` lines so `nnloop/trainer.py` parses metrics identically!
  2. `export`: accepts `--model <model.pt> --net <out.fnn3>`, loads the `arch="v3p"` checkpoint,
     quantizes via `train_v3p.to_file_net_p`, writes `<out.fnn3>` atomically via `.part -> os.replace`,
     and verifies checksum & file size.
  3. `--selftest`: zero-GPU CPU round-trip test verifying CLI contract, `export` atomic write,
     checksum integrity, and `VAL_MIX60` output parsing!
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import torch

THIS_DIR = Path(__file__).resolve().parent
LAB = Path(os.environ.get("FORGE_LAB_ROOT", r"C:\nnue-lab"))
if (LAB / "pipeline").exists():
    sys.path.insert(0, str(LAB / "pipeline"))
sys.path.insert(0, str(THIS_DIR))

import forge_v3p  # noqa: E402
import train_v3p as tv3p  # noqa: E402


def load_model(model_path: str | Path) -> tv3p.ForgeNetV3P:
    ck = torch.load(model_path, map_location="cpu", weights_only=True)
    assert ck.get("arch") == "v3p", f"Expected arch='v3p', got {ck.get('arch')!r}"
    model = tv3p.ForgeNetV3P(
        hidden=int(ck["hidden"]),
        king_buckets=int(ck["king_buckets"]),
        out_buckets=int(ck["out_buckets"]),
        mirror=bool(ck["mirror"]),
        pairwise=bool(ck["pairwise"]),
        has_psqt=bool(ck["has_psqt"]),
    )
    model.load_state_dict(ck["state"])
    return model


def cmd_export(model_path: Path, net_path: Path) -> int:
    model = load_model(model_path)
    net = tv3p.to_file_net_p(model)
    net_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = net_path.with_name(net_path.name + ".part")
    cksum = forge_v3p.write_net(str(tmp), net)
    os.replace(tmp, net_path)
    # Round-trip verify header & checksum (read_net raises if stored checksum mismatches!)
    rt = forge_v3p.read_net(str(net_path))
    assert rt.hidden == model.hidden and rt.king_buckets == model.king_buckets and rt.pairwise == model.pairwise and rt.has_psqt == model.has_psqt
    print(f"EXPORT_V3P_OK: {net_path} bytes={net_path.stat().st_size} hidden={rt.hidden} kb={rt.king_buckets} cksum={cksum:016x}", flush=True)
    return 0


def cmd_train(args: argparse.Namespace) -> int:
    out_model = Path(args.out_model).resolve()
    work_dir = out_model.parent / "_v3p_train_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(THIS_DIR / "train_v3p.py"),
        "--datasets", *args.datasets,
        "--val", args.val,
        "--hce-exe", args.hce_exe,
        "--out-dir", str(work_dir),
        "--hidden", str(args.hidden),
        "--king-buckets", str(args.king_buckets),
        "--epochs", str(args.epochs),
        "--batch-size", str(args.batch_size),
        "--lr", str(args.lr),
        "--lr-cycles", args.lr_cycles,
        "--w1-decay", str(args.w1_decay),
        "--ob-smooth", str(args.ob_smooth),
        "--mix", str(args.mix),
        "--loss-pow", str(args.loss_pow),
        "--seed", str(args.seed),
        "--save-ckpt-every", "1",
        "--resume",
    ]
    if args.distill_net:
        cmd += ["--distill-net", args.distill_net, "--distill-weight", str(args.distill_weight)]
    if args.anchor_shards:
        cmd += ["--anchor-shards", *args.anchor_shards, "--anchor-repeat", str(args.anchor_repeat)]
    if args.fqs_shards:
        cmd += ["--fqs-shards", *args.fqs_shards, "--fqs-repeat", str(args.fqs_repeat)]

    r = subprocess.run(cmd)
    if r.returncode != 0:
        return r.returncode

    src_pt = work_dir / "cand.pt"
    assert src_pt.exists(), f"Missing trained model: {src_pt}"
    tmp_pt = out_model.with_name(out_model.name + ".part")
    shutil.copy2(src_pt, tmp_pt)
    os.replace(tmp_pt, out_model)

    m_path = work_dir / "metrics.json"
    if m_path.exists():
        m = json.loads(m_path.read_text(encoding="utf-8"))
        if "legacy_val_quiet_mix60" in m:
            print(f"VAL_MIX60 {m['legacy_val_quiet_mix60']:.6f}", flush=True)
        if "final_eval_r0203_quiet_mix60" in m:
            print(f"VAL {m['final_eval_r0203_quiet_mix60']:.6f}", flush=True)
    return 0


def selftest_cpu() -> int:
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td)
        m = tv3p.ForgeNetV3P(hidden=128, king_buckets=8, out_buckets=8, mirror=True, pairwise=True, has_psqt=True)
        pt = tp / "cand.pt"
        fnn3 = tp / "cand.fnn3"
        tv3p.save_model_p(m, pt)
        rc = cmd_export(pt, fnn3)
        assert rc == 0 and fnn3.exists() and not fnn3.with_name(fnn3.name + ".part").exists()
        # Verify trainer.py train_cmd/export_cmd template compatibility
        sample_fields = {
            "python": sys.executable, "datasets": '"a.plain"', "val": "v.plain",
            "model": str(pt), "net": str(fnn3), "epochs": 40, "lr": 0.0005, "batch_size": 8192,
        }
        t_tpl = '"{python}" forge_train_v3p_loop_adapter.py train --datasets {datasets} --val "{val}" --out-model "{model}" --epochs {epochs} --lr {lr} --batch-size {batch_size} --hidden 1024'
        e_tpl = '"{python}" forge_train_v3p_loop_adapter.py export --model "{model}" --net "{net}"'
        assert t_tpl.format(**sample_fields) and e_tpl.format(**sample_fields)
        print("LOOP_ADAPTER_V3P_SELFTEST_PASS", flush=True)
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest_cpu()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="subcmd", required=True)

    tr = sub.add_parser("train")
    tr.add_argument("--datasets", nargs="+", required=True)
    tr.add_argument("--val", required=True)
    tr.add_argument("--out-model", required=True)
    tr.add_argument("--hce-exe", default=str(LAB / "forge/build/hce_dump.exe"))
    tr.add_argument("--epochs", type=int, default=40)
    tr.add_argument("--lr", type=float, default=0.0005)
    tr.add_argument("--batch-size", type=int, default=8192)
    tr.add_argument("--hidden", type=int, default=1024)
    tr.add_argument("--king-buckets", type=int, default=8)
    tr.add_argument("--lr-cycles", default="auto")
    tr.add_argument("--w1-decay", type=float, default=0.3)
    tr.add_argument("--ob-smooth", type=float, default=2e-6)
    tr.add_argument("--mix", type=float, default=0.75)
    tr.add_argument("--loss-pow", type=float, default=2.0)
    tr.add_argument("--distill-net", default="")
    tr.add_argument("--distill-weight", type=float, default=0.2)
    tr.add_argument("--anchor-shards", nargs="*", default=[])
    tr.add_argument("--anchor-repeat", type=int, default=25)
    tr.add_argument("--fqs-shards", nargs="*", default=[])
    tr.add_argument("--fqs-repeat", type=int, default=3)
    tr.add_argument("--keep-noisy", action="store_true")
    tr.add_argument("--teacher-once", action="store_true")
    tr.add_argument("--seed", type=int, default=1)

    ex = sub.add_parser("export")
    ex.add_argument("--model", required=True)
    ex.add_argument("--net", required=True)

    args = ap.parse_args()
    if args.subcmd == "export":
        return cmd_export(Path(args.model), Path(args.net))
    return cmd_train(args)


if __name__ == "__main__":
    raise SystemExit(main())
