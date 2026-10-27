#!/usr/bin/env python3
"""S09-4: repackage Sol's delivered S09 packet (read-only, from git) into ONE files index + per-step archives.

Sol's packet `releases/forge_sol_pack31_20261025/S09/` on commit 17aa0cae has 902 loose files and several
overlapping indexes (MANIFEST .json/.txt, SHA256SUMS, three evidence maps). Here:
  * one archive per step: every `evidence/<step>/` and `provenance/<step>/` folder, plus `00_top_level` for the
    packet's top-level files (deterministic tar.gz: sorted members, fixed mtime/owner/mode, gzip mtime 0);
  * files that are already compressed (.gz/.xz) and larger than --big bytes are NOT re-packed (no second copy of
    ~37 MB in git): the index points to them on 17aa0cae (`git show 17aa0cae:<path>`);
  * ONE index (`FILES_sol_S09_v2.txt`): every original file (path, bytes, sha256, git blob, archive or
    NOT_REPACKED), every archive (bytes, sha256, members), and groups of byte-identical files.
Every archive is re-read after writing and each member's sha256 is checked against the git blob's bytes.
usage: opus_s09_package_sol_packet.py --repo R --commit 17aa0cae --out DIR [--big 1048576]
"""
from __future__ import annotations
import argparse, gzip, hashlib, io, subprocess, sys, tarfile
from pathlib import Path

PREFIX = "releases/forge_sol_pack31_20261025/S09/"


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True).stdout


def blobs(repo, ids):
    """Read blob contents with one `git cat-file --batch` process."""
    proc = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = {}
    for oid in ids:
        proc.stdin.write(oid.encode() + b"\n")
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        size = int(header[2])
        out[oid] = proc.stdout.read(size)
        proc.stdout.read(1)
    proc.stdin.close()
    proc.wait()
    return out


def step_of(rel):
    parts = rel.split("/")
    if len(parts) >= 3 and parts[0] in ("evidence", "provenance"):
        return parts[0] + "/" + parts[1]
    return "00_top_level"


def make_tgz(members, mtime):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name, data in sorted(members):
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode, info.uid, info.gid, info.uname, info.gname = len(data), mtime, 0o644, 0, 0, "", ""
            tar.addfile(info, io.BytesIO(data))
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", compresslevel=9, mtime=0) as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--commit", default="17aa0cae")
    ap.add_argument("--out", required=True)
    ap.add_argument("--big", type=int, default=1 << 20)
    a = ap.parse_args(argv)
    out = Path(a.out)
    (out / "archives").mkdir(parents=True, exist_ok=False)
    mtime = int(git(a.repo, "show", "-s", "--format=%ct", a.commit).strip())
    rows = []
    for line in git(a.repo, "ls-tree", "-r", "-l", a.commit, "--", PREFIX).decode().splitlines():
        meta, path = line.split("\t", 1)
        _, kind, oid, size = meta.split()
        if kind == "blob":
            rows.append({"path": path[len(PREFIX):], "oid": oid, "bytes": int(size)})
    data = blobs(a.repo, [r["oid"] for r in rows])
    steps = {}
    for r in rows:
        b = data[r["oid"]]
        assert len(b) == r["bytes"]
        r["sha256"] = hashlib.sha256(b).hexdigest()
        big = r["bytes"] > a.big and r["path"].endswith((".gz", ".xz"))
        r["step"] = step_of(r["path"])
        r["archive"] = "NOT_REPACKED" if big else None
        if not big:
            steps.setdefault(r["step"], []).append(r)
    archives = []
    for i, (step, members) in enumerate(sorted(steps.items())):
        name = f"S09_{i:02d}_{step.replace('/', '__')}.tar.gz"
        blob = make_tgz([(m["path"], data[m["oid"]]) for m in members], mtime)
        (out / "archives" / name).write_bytes(blob)
        with tarfile.open(out / "archives" / name, "r:gz") as tar:  # verify every member against git
            got = {m.name: hashlib.sha256(tar.extractfile(m).read()).hexdigest() for m in tar.getmembers()}
        want = {m["path"]: m["sha256"] for m in members}
        if got != want:
            raise SystemExit(f"{name}: member verification failed")
        for m in members:
            m["archive"] = name
        archives.append({"name": name, "step": step, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                         "members": len(members), "member_bytes": sum(m["bytes"] for m in members)})
    groups = {}
    for r in rows:
        groups.setdefault(r["sha256"], []).append(r["path"])
    dups = sorted((v for v in groups.values() if len(v) > 1), key=lambda v: v[0])
    lines = [f"# FILES_sol_S09_v2 — ONE index of Sol's S09 packet ({PREFIX} on {a.commit}), repackaged per step (S09-4)",
             f"# {len(rows)} original files, {sum(r['bytes'] for r in rows):,} bytes; {len(archives)} per-step archives "
             f"({sum(x['bytes'] for x in archives):,} bytes); {sum(1 for r in rows if r['archive'] == 'NOT_REPACKED')} big "
             f"compressed files NOT re-packed (read them with `git show {a.commit}:{PREFIX}<path>`).",
             "# Every archive member was re-read and its sha256 checked against the git blob.", "",
             "## Archives: name | bytes | sha256 | members | member bytes | step"]
    lines += [f"{x['name']} | {x['bytes']} | {x['sha256']} | {x['members']} | {x['member_bytes']} | {x['step']}" for x in archives]
    lines += ["", "## Files: path | bytes | sha256 | git blob | archive"]
    lines += [f"{r['path']} | {r['bytes']} | {r['sha256']} | {r['oid']} | {r['archive']}" for r in sorted(rows, key=lambda r: r["path"])]
    lines += ["", f"## Byte-identical groups ({len(dups)}): paths"]
    lines += [" == ".join(g) for g in dups]
    (out / "FILES_sol_S09_v2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(rows)} files; {len(archives)} archives, {sum(x['bytes'] for x in archives):,} bytes; "
          f"not re-packed: {[r['path'] for r in rows if r['archive'] == 'NOT_REPACKED']}; identical groups: {len(dups)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
