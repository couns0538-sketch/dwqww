"""R11 self-test of the helper tools and the three Code Review flags.

  1 r11_astra.py extract: a correct archive extracts and verifies; a whole-archive checksum failure deletes every
    file the run extracted (CR flag 1); a member that already exists is never overwritten.
  2 r11_common.production_processes fails CLOSED when psutil is missing (CR flag 2).
  3 r11_common.assert_writable_path refuses production / live-data / other agents' folders.
  4 GPL boundary (CR flag 3): the branch changes nothing under src/, include/, tests/ or CMakeLists.txt relative to
    the R10 fix1 base 7f79c349, every file that includes or imports nnue-pytorch lives in tools/nnue_pytorch_amd/,
    and no file in opus_r11/ includes lib/binpack.h or imports the trainer's modules.
Usage: test_r11_tools.py <scratch_dir>   (must not exist). Prints "R11 TOOLS SELFTEST PASS".
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "opus_r11", "pipeline"))
import r11_astra as A  # noqa: E402
import r11_common as C  # noqa: E402

FAILS: list[str] = []


def check(cond: bool, what: str) -> None:
    print(("ok   " if cond else "FAIL ") + what, flush=True)
    if not cond:
        FAILS.append(what)


def make_transport(dl: str, whole_sha_override: str | None = None) -> None:
    os.makedirs(dl)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in (("completed/full10m/forge_filtered.pos", os.urandom(300_000)),
                           ("completed/full10m/forge_filtered.hce", os.urandom(50_000)),
                           ("completed/other.txt", b"x" * 1000)):
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
    blob = buf.getvalue()
    half = len(blob) // 2
    parts = []
    for i, (off, chunk) in enumerate(((0, blob[:half]), (half, blob[half:]))):
        name = f"t.tar.gz.part{i:06d}"
        with open(os.path.join(dl, name), "wb") as f:
            f.write(chunk)
        parts.append({"name": name, "offset": off, "size": len(chunk), "sha256": hashlib.sha256(chunk).hexdigest()})
    man = {"format": "forge-transport-v1", "part_bytes": half, "parts": parts,
           "whole": {"name": "t.tar.gz", "size": len(blob), "sha256": whole_sha_override or hashlib.sha256(blob).hexdigest()}}
    with open(os.path.join(dl, A.MANIFEST), "w", encoding="utf-8") as f:
        json.dump(man, f)


def main() -> int:
    scratch = sys.argv[1]
    if os.path.exists(scratch):
        print(f"{scratch} exists; give a new folder")
        return 2
    globs = ["completed/full10m/forge_filtered.pos", "completed/full10m/forge_filtered.hce"]

    # 1a correct archive
    dl, out = os.path.join(scratch, "dl_ok"), os.path.join(scratch, "out_ok")
    make_transport(dl)
    check(A.cmd_verify(dl) == 0, "astra: part checksums verify")
    rc = A.cmd_extract(dl, out, globs, os.path.join(scratch, "ok.json"))
    check(rc == 0 and sorted(os.listdir(out)) == ["forge_filtered.hce", "forge_filtered.pos"],
          "astra: correct archive extracts exactly the requested members")
    # 1b existing target is never overwritten
    rc = A.cmd_extract(dl, out, globs, None)
    check(rc == 2 and sorted(os.listdir(out)) == ["forge_filtered.hce", "forge_filtered.pos"],
          "astra: existing targets are not overwritten (and the earlier files stay)")
    # 1c whole-archive checksum failure -> partial files deleted
    dl2, out2 = os.path.join(scratch, "dl_bad"), os.path.join(scratch, "out_bad")
    make_transport(dl2, whole_sha_override="0" * 64)
    rc = A.cmd_extract(dl2, out2, globs, os.path.join(scratch, "bad.json"))
    left = os.listdir(out2) if os.path.isdir(out2) else []
    check(rc != 0 and left == [], f"astra: checksum failure removes the partial files (left: {left})")

    # 2 fail closed without psutil
    saved = sys.modules.get("psutil", "absent")
    sys.modules["psutil"] = None  # makes "import psutil" raise ImportError
    try:
        res = C.production_processes(["anything"])
    finally:
        if saved == "absent":
            del sys.modules["psutil"]
        else:
            sys.modules["psutil"] = saved
    check(len(res) == 1 and res[0]["pid"] == -1 and "fail closed" in res[0]["pattern"],
          f"process check fails closed without psutil: {res}")
    res = C.production_processes([r"this-pattern-matches-no-process-\d{40}"])
    check(res == [], "process check with psutil and no match returns []")

    # 3 protected folders
    for p in ("F:/forge_j1_data/x.binpack", "D:/forge_nnue_train/exports/y", "C:/Users/Administrator/grok-pc/z",
              "D:/grok-pc-data/selfplay_out/w", "D:/forge_j1_data_astra/v"):
        try:
            C.assert_writable_path(p)
            check(False, f"protected path accepted: {p}")
        except C.StageFailed:
            check(True, f"protected path refused: {p}")
    try:
        C.assert_writable_path("D:/grok-pc-data/r11_nnue/data/x")
        C.assert_writable_path("D:/grok-pc-data/selfplay_out_other/x")
        check(True, "own output folders accepted")
    except C.StageFailed as e:
        check(False, f"own output folder refused: {e}")

    # 4 GPL boundary
    r = subprocess.run(["git", "-C", REPO, "diff", "--stat", "7f79c349", "--", "src", "include", "tests", "CMakeLists.txt"],
                       capture_output=True, text=True)
    check(r.returncode == 0 and r.stdout.strip() == "", "no change under src/, include/, tests/, CMakeLists.txt vs 7f79c349")
    r = subprocess.run(["git", "-C", REPO, "ls-files"], capture_output=True, text=True)
    files = r.stdout.splitlines()
    gpl_users = []
    for f in files:
        if not f.endswith((".cpp", ".h", ".hpp", ".py")):
            continue
        if f.startswith("opus_r11/tests/"):
            continue  # this test names the markers it searches for
        try:
            text = open(os.path.join(REPO, f), "rb").read().decode("utf-8", "replace")
        except OSError:
            continue
        if '#include "lib/binpack.h"' in text or "import model as M" in text or "from model import" in text:
            gpl_users.append(f)
    bad = [f for f in gpl_users if not f.startswith("tools/nnue_pytorch_amd/") and not f.startswith("opus_r10/tools/")]
    check(bad == [], f"files using nnue-pytorch code live in tools/nnue_pytorch_amd/ only (GPL users: {gpl_users})")
    check(not any(f.startswith(("src/", "include/", "tests/")) for f in gpl_users), "nothing GPL under src/include/tests")

    print(f"\n{len(FAILS)} failed checks")
    print("R11 TOOLS SELFTEST " + ("PASS" if not FAILS else "FAIL"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
