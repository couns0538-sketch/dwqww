#!/usr/bin/env python3
"""verify_job.py JOB [--convert OUT_DIR] [--bin DIR] - Opus R14-B item 2: read-only check of a FINISHED relabel2.py
job before its labels are used (RELABEL_HANDOFF.md "Checks before using the output" in one command). Nothing in JOB
is written. Checks:
  1 final/MANIFEST.json: bytes, md5 and sha256 of train.txt / val.txt / labels.tsv; its prepare_json_sha256 =
    prepare.json; game_overlap 0
  2 counts: rows / train_rows / val_rows of MANIFEST = prepare.json = the lines of the three files
  3 labels.tsv: its header, every row id once and in order, splits train / val only; train.txt and val.txt are
    exactly the labels rows of their split as "FEN | new score | result", in order; no game id in both splits
  4 the published shards: their labels.tsv sha256 = MANIFEST's shard_labels_sha256 in order (re-hashed), and the
    settings a shard records (node limit, hash, probe sha256; shards of versions before e01caaf1 record none) =
    run_config.json
  5 with --convert OUT_DIR (must not exist): Forge's fen2bin and hce_dump (--bin, default the converters earlier jobs
    used) on train.txt and val.txt: records = lines, bad 0 / bad_fen 0 / clamped 0; the .pos / .hce files stay there
Exit 0 = every check passed, 4 = a mismatch (each one named), 2 = not a finished job / bad arguments.
Runs at BelowNormal (psutil if present). Standard library otherwise; reads every output byte once (50M rows: ~13 GB
with the shards, minutes).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from relabel2 import LABELS_HEADER, SHARD_SETTINGS  # noqa: E402  (the frozen tool's own constants)

NAMES = ("train.txt", "val.txt", "labels.tsv")


def digests(path):
    md5, sha, n = hashlib.md5(), hashlib.sha256(), 0
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            md5.update(block)
            sha.update(block)
            n += len(block)
    return n, md5.hexdigest(), sha.hexdigest()


def info_file(path):
    """key=value lines of a converter's .info file (it writes CRLF)."""
    out = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("job")
    ap.add_argument("--convert", metavar="OUT_DIR")
    ap.add_argument("--bin", default=r"F:\opus_scratch\rescore_d8\bin", help="folder with fen2bin.exe and hce_dump.exe")
    a = ap.parse_args()
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)
    except ImportError:
        pass
    job, final = Path(a.job), Path(a.job) / "final"
    for f in (job / "prepare.json", job / "run_config.json", final / "MANIFEST.json", *(final / n for n in NAMES)):
        if not f.is_file():
            print(f"NOT A FINISHED JOB: {f} missing", file=sys.stderr)
            return 2
    if a.convert and os.path.exists(a.convert):
        print(f"--convert {a.convert} exists (use a new folder)", file=sys.stderr)
        return 2
    bad = []

    def check(ok, what):
        print(f"{'PASS' if ok else 'FAIL'} {what}")
        if not ok:
            bad.append(what)

    prep = json.loads((job / "prepare.json").read_text(encoding="utf-8"))
    cfg = json.loads((job / "run_config.json").read_text(encoding="utf-8"))
    man = json.loads((final / "MANIFEST.json").read_text(encoding="utf-8"))
    # 1 manifest
    for n in NAMES:
        size, md5, sha = digests(final / n)
        want = man["files"][n]
        check((size, md5, sha) == (want["bytes"], want["md5"], want["sha256"]), f"{n}: bytes / md5 / sha256 = MANIFEST ({md5})")
    check(digests(job / "prepare.json")[2] == man["prepare_json_sha256"], "MANIFEST prepare_json_sha256 = prepare.json")
    check(man.get("game_overlap") == 0, "MANIFEST game_overlap 0")
    # 2 + 3 one pass over labels.tsv, train.txt and val.txt
    games = {"train": set(), "val": set()}
    counts = {"train": 0, "val": 0}
    expect, mismatch = 0, None
    with open(final / "labels.tsv", encoding="utf-8", newline="\n") as lf, \
            open(final / "train.txt", encoding="utf-8", newline="\n") as tf, \
            open(final / "val.txt", encoding="utf-8", newline="\n") as vf:
        check(lf.readline() == LABELS_HEADER, "labels.tsv header")
        out = {"train": tf, "val": vf}
        for line in lf:
            f = line.rstrip("\n").split("\t")
            if mismatch is None:
                if len(f) != 9 or f[0] != str(expect) or f[2] not in out:
                    mismatch = f"labels.tsv data line {expect + 1}: row id / split / fields: {line[:80]!r}"
                elif out[f[2]].readline() != f"{f[3]} | {f[4]} | {f[6]}\n":
                    mismatch = f"{f[2]}.txt line {counts[f[2]] + 1} is not labels row {f[0]} as 'FEN | score | result'"
            if mismatch is None:
                games[f[2]].add(f[1])
                counts[f[2]] += 1
            expect += 1
        leftover = [n for n, fh in out.items() if mismatch is None and fh.readline() != ""]
    check(mismatch is None, f"labels.tsv row ids 0..{expect - 1} in order; train.txt / val.txt = its rows"
                            + (f" - {mismatch}" if mismatch else ""))
    check(not leftover, f"no extra lines in train.txt / val.txt{' - extra in ' + str(leftover) if leftover else ''}")
    check(not games["train"] & games["val"], f"no game id in both splits ({len(games['train'])} train, {len(games['val'])} val games)")
    check(expect == prep["rows"] == man["rows"], f"rows: labels {expect}, prepare.json {prep['rows']}, MANIFEST {man['rows']}")
    check((counts["train"], counts["val"]) == (prep["train_rows"], prep["val_rows"]) == (man["train_rows"], man["val_rows"]),
          f"split rows: train {counts['train']} / val {counts['val']} = prepare.json = MANIFEST")
    # 4 shards
    shard_hashes = man.get("shard_labels_sha256", [])
    found, settings_ok, recorded = [], True, 0
    for k in range(len(shard_hashes)):
        d = job / "shards" / f"shard_{k:05d}"
        if not (d / "labels.tsv").is_file():
            found.append(None)
            continue
        found.append(digests(d / "labels.tsv")[2])
        try:
            summ = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            summ = {}
        for sk, ck in SHARD_SETTINGS:
            if sk in summ:
                recorded += 1
                settings_ok &= summ[sk] == cfg.get(ck)
    if None in found:
        print(f"note: {found.count(None)} of {len(found)} shards are no longer there; checked the rest")
    check(all(h is None or h == w for h, w in zip(found, shard_hashes)) and shard_hashes,
          f"{len(found) - found.count(None)} shards re-hashed = MANIFEST shard_labels_sha256")
    check(settings_ok, f"shard settings = run_config.json ({recorded} recorded values; none before e01caaf1)")
    # 5 Forge's converters
    if a.convert:
        os.makedirs(a.convert)
        for n in ("train", "val"):
            lines = counts[n]
            for tool, ext, keys in (("fen2bin", "pos", ("bad",)), ("hce_dump", "hce", ("bad_fen", "clamped"))):
                target = os.path.join(a.convert, f"{n}.{ext}")
                flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
                p = subprocess.run([os.path.join(a.bin, f"{tool}.exe"), str(final / f"{n}.txt"), target],
                                   capture_output=True, creationflags=flags)
                inf = info_file(target + ".info") if os.path.exists(target + ".info") else {}
                ok = p.returncode == 0 and inf.get("records") == str(lines) and all(inf.get(k) == "0" for k in keys)
                check(ok, f"{tool} {n}.txt: exit {p.returncode}, records {inf.get('records')} of {lines} lines, "
                          + ", ".join(f"{k} {inf.get(k)}" for k in keys))
    print(f"verify_job: {'all PASS' if not bad else f'{len(bad)} FAIL'} ({job})")
    return 4 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
