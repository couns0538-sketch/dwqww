"""R11: fetch, verify and unpack Astra A1's filtered set (release astra-a1-data-results-20261030).

The release ships one .tar.gz split into numbered byte chunks plus transport_manifest.json
(format forge-transport-v1: parts with offset/size/sha256 and the whole-file sha256). This tool
checks every part, streams the parts in order straight into tarfile (no reassembled copy on disk),
checks the whole-archive sha256 while streaming, and extracts only the requested members (regular files, by
base name) into a staging folder; they are renamed into place only after the whole archive matched the PINNED
sha256 148803c5... and size 2,329,781,152 and each pinned member its sha256 (CR fix 3).

Usage (run with python -I; paths are arguments, never the current directory):
  r11_astra.py download <dl_dir>                 # gh release download into an EMPTY folder
  r11_astra.py verify <dl_dir>                   # part sizes + sha256 vs transport_manifest.json
  r11_astra.py list <dl_dir> [--out list.txt]    # member names, sizes (streams the whole archive)
  r11_astra.py extract <dl_dir> <out_dir> <member_glob> [<member_glob> ...] [--json result.json]
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r11_common as C  # noqa: E402

RELEASE = "astra-a1-data-results-20261030"
REPO = "couns0538-sketch/dwqww"
MANIFEST = "transport_manifest.json"
# CR fix 3: the whole archive is pinned (release notes + Astra's report), not taken from the downloaded manifest
PINNED_WHOLE_SHA256 = "148803c5a45a5e291c18f667b918100ec1fa1a8e08d5a74dfe430651b3f1418f"
PINNED_WHOLE_SIZE = 2_329_781_152
PINNED_MEMBERS = {  # docs/ASTRA_A1_DATA.md on astra-a1-data, "Output | SHA256"
    "completed/full10m/forge_filtered.pos": "2019bf8e560e4821b8c50286a257ba7f4d4435521e90b2324e0e35dfcc324802",
    "completed/full10m/forge_filtered.hce": "9c5f4e6db58b59fc40465ff00c38cb71c8b05161bfb9aacc5d0e309b312b8e87",
}


def load_manifest(dl_dir: str, pins: tuple[str, int] | None = (PINNED_WHOLE_SHA256, PINNED_WHOLE_SIZE)) -> dict:
    with open(os.path.join(dl_dir, MANIFEST), "r", encoding="utf-8") as f:
        man = json.load(f)
    if man.get("format") != "forge-transport-v1":
        raise SystemExit(f"FAIL unknown transport format {man.get('format')!r}")
    if pins is not None and (man["whole"]["sha256"] != pins[0] or man["whole"]["size"] != pins[1]):
        raise SystemExit(f"FAIL manifest whole sha256/size {man['whole']['sha256']} / {man['whole']['size']} != pinned "
                         f"{pins[0]} / {pins[1]}")
    parts = sorted(man["parts"], key=lambda p: p["offset"])
    off = 0
    for p in parts:
        if p["offset"] != off:
            raise SystemExit(f"FAIL part {p['name']} offset {p['offset']} != expected {off}")
        if os.path.basename(p["name"]) != p["name"]:
            raise SystemExit(f"FAIL part name with a path: {p['name']!r}")
        off += p["size"]
    if off != man["whole"]["size"]:
        raise SystemExit(f"FAIL parts add up to {off}, whole is {man['whole']['size']}")
    man["parts"] = parts
    return man


def sha256_file(path: str, bufsize: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def cmd_download(dl_dir: str) -> int:
    try:  # CR fix 8: the pinned archive size must fit above the drive's floor before anything is downloaded
        C.require_disk(dl_dir, PINNED_WHOLE_SIZE + (1 << 20), "Astra release download")
    except C.StageFailed as e:
        print(f"FAIL {e}")
        return 2
    os.makedirs(dl_dir, exist_ok=True)
    if os.listdir(dl_dir):
        print(f"FAIL download folder {dl_dir} is not empty (untrusted downloads go into a new empty folder)")
        return 2
    cmd = ["gh", "release", "download", RELEASE, "-R", REPO, "-D", dl_dir,
           "-p", "forge_astra_a1_data_results_20261030.tar.gz.part*", "-p", MANIFEST]
    print("running:", " ".join(cmd), flush=True)
    return subprocess.call(cmd)


def cmd_verify(dl_dir: str, pins: tuple[str, int] | None = (PINNED_WHOLE_SHA256, PINNED_WHOLE_SIZE)) -> int:
    man = load_manifest(dl_dir, pins)
    ok = True
    for p in man["parts"]:
        path = os.path.join(dl_dir, p["name"])
        if not os.path.isfile(path):
            print(f"FAIL missing part {p['name']}")
            ok = False
            continue
        size = os.path.getsize(path)
        digest = sha256_file(path)
        good = size == p["size"] and digest == p["sha256"]
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {p['name']} size {size} sha256 {digest}")
    print("VERIFY PARTS " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


class ConcatReader:
    """Read the parts in order as one stream; hash everything that passes through."""

    def __init__(self, dl_dir: str, man: dict):
        self.paths = [os.path.join(dl_dir, p["name"]) for p in man["parts"]]
        self.idx = 0
        self.f = open(self.paths[0], "rb")
        self.h = hashlib.sha256()
        self.total = 0

    def read(self, n: int = -1) -> bytes:
        out = bytearray()
        want = n if n is not None and n >= 0 else 1 << 62
        while want > 0 and self.f is not None:
            b = self.f.read(min(want, 1 << 22))
            if b:
                out += b
                want -= len(b)
                continue
            self.f.close()
            self.idx += 1
            self.f = open(self.paths[self.idx], "rb") if self.idx < len(self.paths) else None
        data = bytes(out)
        self.h.update(data)
        self.total += len(data)
        return data

    def drain(self) -> None:
        while self.read(1 << 22):
            pass


def _stream(dl_dir: str, pins: tuple[str, int] | None):
    man = load_manifest(dl_dir, pins)
    reader = ConcatReader(dl_dir, man)
    tf = tarfile.open(fileobj=reader, mode="r|gz")
    return man, reader, tf


def cmd_list(dl_dir: str, out: str | None, pins: tuple[str, int] | None = (PINNED_WHOLE_SHA256, PINNED_WHOLE_SIZE)) -> int:
    man, reader, tf = _stream(dl_dir, pins)
    lines = []
    for m in tf:
        lines.append(f"{m.size}\t{m.type.decode() if isinstance(m.type, bytes) else m.type}\t{m.name}")
    tf.close()
    reader.drain()
    whole_ok = reader.h.hexdigest() == man["whole"]["sha256"] and reader.total == man["whole"]["size"]
    text = "\n".join(lines) + "\n"
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    print(f"members {len(lines)}; whole sha256 {reader.h.hexdigest()} size {reader.total} -> "
          + ("WHOLE PASS" if whole_ok else "WHOLE FAIL"))
    return 0 if whole_ok else 1


def _remove_partial(paths: list[str]) -> None:
    """Code Review flag (R11): files extracted by THIS run are deleted when the archive fails its checksum or the
    extraction stops with an error, so no unverified data stays behind. Only files this run created are touched."""
    for p in paths:
        if os.path.exists(p):
            os.remove(p)
            print(f"removed unverified partial file {p}")


def cmd_extract(dl_dir: str, out_dir: str, globs: list[str], json_out: str | None,
                pins: tuple[str, int] | None = (PINNED_WHOLE_SHA256, PINNED_WHOLE_SIZE),
                member_pins: dict[str, str] | None = None) -> int:
    """CR fix 3: members are written into <out_dir>/.staging_<pid>_<time>/ and renamed into <out_dir> only after the
    whole archive matched the pinned sha256 + size and every pinned member its sha256; on any failure the staged
    files are deleted (CR flag: no unverified partial data stays behind)."""
    member_pins = PINNED_MEMBERS if member_pins is None else member_pins
    os.makedirs(out_dir, exist_ok=True)
    try:
        man, reader, tf = _stream(dl_dir, pins)
    except SystemExit as e:
        print(str(e))
        return 1
    staging = os.path.join(out_dir, f".staging_{os.getpid()}_{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(staging)
    got = []
    created: list[str] = []  # every path this run created inside the staging folder
    t0 = time.time()

    def abort(code: int) -> int:
        _remove_partial(created)
        if os.path.isdir(staging) and not os.listdir(staging):
            os.rmdir(staging)  # the empty staging folder this run made
        return code

    try:
        for m in tf:
            if not m.isfile():
                continue
            if not any(fnmatch.fnmatch(m.name, g) for g in globs):
                continue
            final = os.path.join(out_dir, os.path.basename(m.name))
            if os.path.exists(final):
                print(f"FAIL target exists, not overwriting: {final}")
                return abort(2)
            staged = os.path.join(staging, os.path.basename(m.name))
            C.require_disk(staging, m.size, f"extract of {m.name}")  # CR fix 8 (raises -> staged files removed)
            src = tf.extractfile(m)
            h = hashlib.sha256()
            with open(staged, "xb") as f:
                created.append(staged)
                while True:
                    b = src.read(1 << 22)
                    if not b:
                        break
                    h.update(b)
                    f.write(b)
            if os.path.getsize(staged) != m.size:
                raise OSError(f"member {m.name}: wrote {os.path.getsize(staged)} bytes, expected {m.size}")
            got.append({"member": m.name, "staged": staged, "path": final, "size": m.size, "sha256": h.hexdigest()})
            print(f"staged {m.name} ({m.size} bytes, sha256 {h.hexdigest()})", flush=True)
        tf.close()
        reader.drain()
    except Exception as e:  # noqa: BLE001 - any extraction error leaves no partial files behind
        print(f"FAIL extraction error: {type(e).__name__}: {e}")
        return abort(1)
    whole_ok = reader.h.hexdigest() == man["whole"]["sha256"] and reader.total == man["whole"]["size"]
    if pins is not None:
        whole_ok &= reader.h.hexdigest() == pins[0] and reader.total == pins[1]
    bad_members = [g["member"] for g in got if g["member"] in member_pins and member_pins[g["member"]] != g["sha256"]]
    if not whole_ok or bad_members:
        print(f"FAIL whole-archive checksum {reader.h.hexdigest()} size {reader.total} (manifest "
              f"{man['whole']['sha256']} size {man['whole']['size']}, pinned {pins}); pinned members that differ: "
              f"{bad_members}")
        return abort(1)
    for g in got:  # every check passed: move the staged files into place
        if os.path.exists(g["path"]):
            print(f"FAIL target appeared meanwhile, not overwriting: {g['path']}")
            return abort(2)
        os.replace(g.pop("staged"), g["path"])
    os.rmdir(staging)
    res = {"release": RELEASE, "whole_sha256": reader.h.hexdigest(), "whole_size": reader.total,
           "whole_ok": whole_ok, "members": got, "seconds": round(time.time() - t0, 1)}
    if json_out:
        with open(json_out + ".part", "w", encoding="utf-8", newline="\n") as f:
            json.dump(res, f, indent=1)
        os.replace(json_out + ".part", json_out)
    print("EXTRACT " + ("PASS" if whole_ok and got else "FAIL") + f" ({len(got)} members)")
    return 0 if whole_ok and got else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("download"); s.add_argument("dl_dir")
    s = sub.add_parser("verify"); s.add_argument("dl_dir")
    s = sub.add_parser("list"); s.add_argument("dl_dir"); s.add_argument("--out")
    s = sub.add_parser("extract"); s.add_argument("dl_dir"); s.add_argument("out_dir"); s.add_argument("globs", nargs="+")
    s.add_argument("--json")
    a = ap.parse_args(argv)
    C.set_idle_background()  # CR fix 2: Idle + background mode on 3 cores
    if a.cmd == "download":
        return cmd_download(a.dl_dir)
    if a.cmd == "verify":
        return cmd_verify(a.dl_dir)
    if a.cmd == "list":
        return cmd_list(a.dl_dir, a.out)
    return cmd_extract(a.dl_dir, a.out_dir, a.globs, a.json)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
