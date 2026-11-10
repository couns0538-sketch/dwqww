"""make_files_md.py - write FILES.md: every file of the pack with size, md5 and sha256, and the D:-only artefacts.

usage: make_files_md.py REPO_DIR OUT_DIR
FILES.md cannot list itself; STATUS.md is listed with the hashes it has when this tool runs (the final reply of the
job quotes the md5 of STATUS.md again after the last edit).
"""
import hashlib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402


def digests(path):
    m, s = hashlib.md5(), hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            m.update(chunk)
            s.update(chunk)
    return m.hexdigest(), s.hexdigest()


def rows(root, rel_base, skip=()):
    out = []
    for d, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            p = os.path.join(d, name)
            rel = os.path.relpath(p, rel_base).replace("\\", "/")
            if rel in skip:
                continue
            m, s = digests(p)
            out.append(f"| `{rel}` | {os.path.getsize(p)} | `{m}` | `{s}` |")
    return out


def main():
    repo, out = sys.argv[1], sys.argv[2]
    print(pinguard.ensure(), flush=True)
    pack = os.path.join(repo, "fable_speed_lane")
    stamp = time.strftime("%Y-%m-%d %H:%M", time.gmtime(time.time() + 3600)) + " Vienna"
    lines = ["# FILES: manifest with md5 and sha256", "",
             f"Written {stamp} by `tools/make_files_md.py`. This file does not list itself. `STATUS.md` may be edited "
             "after this manifest; its final md5 is in the job's closing line.", "",
             "## 1. On the branch", "", "| File | Bytes | md5 | sha256 |", "|---|---|---|---|"]
    lines += rows(pack, repo, skip=("fable_speed_lane/FILES.md",))
    lines += rows(os.path.join(repo, "skills", "forge-bitexact-speed-lane"), repo)
    lines += ["", "## 2. On the PC only (`D:\\forge_jobs_20261109\\fable2\\out`), not committed", "",
              "Engine source, the embedded net and executables stay on D:.", "",
              "| File | Bytes | md5 | sha256 |", "|---|---|---|---|"]
    base = os.path.join(out, "base")
    for name in ("combo29_lock_E1284F7F.exe", "fens_12k_v2.txt", "frozen_train_cmds.txt"):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            m, s = digests(p)
            lines.append(f"| `out/base/{name}` | {os.path.getsize(p)} | `{m}` | `{s}` |")
    ctl = os.path.join(out, "build", "c29ctl", "m2use", "forge_m2use.exe")
    if os.path.isfile(ctl):
        m, s = digests(ctl)
        lines.append(f"| `out/build/c29ctl/m2use/forge_m2use.exe` (control rebuild of the lock source) | {os.path.getsize(ctl)} | `{m}` | `{s}` |")
    packs = os.path.join(out, "packs")
    if os.path.isdir(packs):
        lines += rows(packs, out)
    builds = os.path.join(out, "build")
    extra = []
    for tag in sorted(os.listdir(builds)) if os.path.isdir(builds) else []:
        if tag.endswith("_v2"):
            p = os.path.join(builds, tag, "m2use", "forge_m2use.exe")
            if os.path.isfile(p):
                m, s = digests(p)
                extra.append(f"| `out/build/{tag}/m2use/forge_m2use.exe` (verify build, test only) | {os.path.getsize(p)} | `{m}` | `{s}` |")
    lines += extra
    with open(os.path.join(pack, "FILES.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"FILES.md written, {sum(1 for x in lines if x.startswith('| `'))} files listed", flush=True)


if __name__ == "__main__":
    main()
