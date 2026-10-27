#!/usr/bin/env python3
"""A7: dry-parse queue lines with the UNCHANGED v3b argument parser, without running the trainer.

The parser is taken from a byte-identical renamed copy of train_resid_v3b.py (md5 checked): the module-level constants
and the statements of main() before `a = ap.parse_args()` are extracted with ast and executed (they are only
`ap = argparse.ArgumentParser(...)` and `ap.add_argument(...)` calls; anything else aborts). No torch import, no data,
no file writes outside --out.

Positive control: the argv of a finished PC run (first line of its settings_*.txt, written by the trainer itself) must
parse to exactly the JSON the trainer dumped below it. The A7 lines are then built the way the supervisor builds a
command (standard prefix of that run + queue args without --script + --run-dir) and parsed. Negative controls: an
unknown argument and a bad type must be rejected.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

RATE_SPEC = 1.22e6       # positions/s given by the A7 spec
SUPERVISOR_ONLY = {"--script"}


def load_parser(copy: Path, expect_md5: str) -> tuple[argparse.ArgumentParser, int]:
    src = copy.read_bytes()
    md5 = hashlib.md5(src).hexdigest()
    if md5 != expect_md5:
        raise SystemExit(f"trainer copy md5 {md5} != expected {expect_md5}")
    tree = ast.parse(src.decode("utf-8"), filename=str(copy))
    doc = ast.get_docstring(tree)
    consts = [n for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
              and all(isinstance(t, ast.Name) for t in n.targets)]
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    stmts = []
    for st in main.body:
        if (isinstance(st, ast.Assign) and isinstance(st.value, ast.Call)
                and isinstance(st.value.func, ast.Attribute) and st.value.func.attr == "parse_args"):
            break
        stmts.append(st)
    first, rest = stmts[0], stmts[1:]
    ok_first = (isinstance(first, ast.Assign) and isinstance(first.value, ast.Call)
                and ast.unparse(first.value.func) == "argparse.ArgumentParser")
    ok_rest = all(isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
                  and ast.unparse(s.value.func) == "ap.add_argument" for s in rest)
    if not (ok_first and ok_rest):
        raise SystemExit("main() does not start with ArgumentParser + add_argument calls only; refusing")
    mod = ast.Module(body=consts + stmts, type_ignores=[])
    ns: dict = {"argparse": argparse, "__doc__": doc}
    exec(compile(mod, str(copy), "exec"), ns)  # only constants, ArgumentParser and add_argument calls
    return ns["ap"], len(rest)


def schedule(ns: dict, n_available: int, rate_measured: float) -> dict:
    """v3b's own step maths (main(): spe = N // batch, capped by --steps-per-epoch; total = spe * epochs), with
    N = the --max-train prefix when it is set and the data has that many positions."""
    n_train = min(ns["max_train"] or n_available, n_available)
    spe = n_train // ns["batch_size"]
    if ns["steps_per_epoch"]:
        spe = min(spe, ns["steps_per_epoch"])
    total = spe * ns["epochs"]
    positions = total * ns["batch_size"]
    return {"train_positions": n_train, "steps_per_epoch": spe, "total_steps": total,
            "positions_processed": positions,
            "gpu_hours_at_1.22M": positions / RATE_SPEC / 3600,
            "gpu_hours_at_measured": positions / rate_measured / 3600,
            "warmup_frac": ns["warmup_steps"] / total,
            "lr_floor": ns["lr"] * ns["min_lr_frac"]}


def parse(ap: argparse.ArgumentParser, argv: list[str]) -> tuple[dict | None, str]:
    try:
        return vars(ap.parse_args(argv)), ""
    except SystemExit as e:  # argparse error -> exit 2 (message on stderr)
        return None, f"argparse exit {e.code}"


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--trainer-copy", type=Path, required=True)
    p.add_argument("--expect-md5", required=True)
    p.add_argument("--settings", type=Path, required=True, help="settings_*.txt of a finished run (read-only)")
    p.add_argument("--ref-queue-args", required=True, help="that run's queue args (from queue.txt), one string")
    p.add_argument("--lines", type=Path, required=True, help="A7 queue lines: '<name> <args>' per line, # = comment")
    p.add_argument("--rate-measured", type=float, required=True, help="measured v3b positions/s (whole run)")
    p.add_argument("--max-train-available", type=int, required=True, help="training positions available now")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=False)

    ap, n_args = load_parser(a.trainer_copy, a.expect_md5)
    print(f"parser: {n_args} add_argument calls from {a.trainer_copy.name} (md5 {a.expect_md5})")

    text = a.settings.read_text(encoding="utf-8")
    first, _, js = text.partition("\n")
    dumped = json.loads(js)
    toks = first.split()
    assert toks[0].endswith(".py"), toks[0]
    ref_argv = toks[1:]
    got, err = parse(ap, ref_argv)
    pos_ok = got == dumped
    print(f"positive control ({a.settings.parent.name}): parsed == trainer's own settings dump: {pos_ok} {err}")
    if not pos_ok:
        diff = {k: (got or {}).get(k, "<missing>") for k in dumped if (got or {}).get(k, "<missing>") != dumped[k]}
        print("  differences:", diff)
        return 1

    # split the reference argv: supervisor prefix (up to --log-every N) + queue args + --run-dir DIR
    i = ref_argv.index("--log-every") + 2
    prefix, tail = ref_argv[:i], ref_argv[i:]
    assert tail[-2] == "--run-dir", tail[-2:]
    ref_q = a.ref_queue_args.split()
    ref_q_trainer = [t for j, t in enumerate(ref_q) if t not in SUPERVISOR_ONLY and (j == 0 or ref_q[j - 1] not in SUPERVISOR_ONLY)]
    split_ok = tail[:-2] == ref_q_trainer
    print(f"supervisor split: prefix {len(prefix)} tokens (train files {prefix.count('--train')} flag), queue args match queue.txt: {split_ok}")
    if not split_ok:
        return 1
    run_root = str(Path(tail[-1]).parent)

    results = []
    for line in a.lines.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, *qargs = line.split()
        script = None
        targs = []
        it = iter(range(len(qargs)))
        for j in it:
            if qargs[j] in SUPERVISOR_ONLY:
                script = qargs[j + 1]
                next(it, None)
            else:
                targs.append(qargs[j])
        argv_full = prefix + targs + ["--run-dir", run_root + "\\" + name]
        ns, err = parse(ap, argv_full)
        row = {"name": name, "script": script, "queue_args": " ".join(qargs), "parsed_ok": ns is not None, "error": err}
        if ns is not None:
            keys = ["shape", "residual", "epochs", "batch_size", "lr", "min_lr_frac", "warmup_steps", "blend_start",
                    "blend_end", "seed", "val_positions", "max_train", "final_full_val", "init_check", "dev_scalars",
                    "order_buffers", "mmap_data", "adam_impl", "steps_per_epoch"]
            row["parsed"] = {k: ns[k] for k in keys}
            row["schedule"] = schedule(ns, a.max_train_available, a.rate_measured)
        results.append(row)
        s = row.get("schedule", {})
        print(f"{'OK  ' if row['parsed_ok'] else 'FAIL'} {name} script={script} {err}"
              + (f" | epochs {row['parsed']['epochs']} lr {row['parsed']['lr']} floor {s['lr_floor']:.2e} "
                 f"max_train {row['parsed']['max_train']:,} -> spe {s['steps_per_epoch']:,} total {s['total_steps']:,} "
                 f"positions {s['positions_processed']:,} = {s['gpu_hours_at_1.22M']:.2f} GPU-h at 1.22M/s "
                 f"({s['gpu_hours_at_measured']:.2f} h at {a.rate_measured:,.0f}/s)" if row["parsed_ok"] else ""))
    (a.out / "dryparse.json").write_text(json.dumps({"parser_add_argument_calls": n_args, "positive_control": pos_ok,
                                                      "supervisor_split_ok": split_ok, "lines": results},
                                                     indent=1), encoding="utf-8")
    expected_fail = [r for r in results if r["name"].startswith("NEGATIVE_")]
    real = [r for r in results if not r["name"].startswith("NEGATIVE_")]
    ok = all(r["parsed_ok"] for r in real) and all(not r["parsed_ok"] for r in expected_fail)
    print(f"RESULT {'PASS' if ok else 'FAIL'}: {sum(r['parsed_ok'] for r in real)}/{len(real)} queue lines parse; "
          f"{sum(not r['parsed_ok'] for r in expected_fail)}/{len(expected_fail)} negative controls rejected")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
