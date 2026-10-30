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
import re
import subprocess
import sys
import tarfile
import time

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


def make_transport(dl: str, whole_sha_override: str | None = None) -> tuple[tuple[str, int], dict]:
    """A synthetic transport set; returns (pins of the real blob, member sha256s)."""
    os.makedirs(dl)
    buf = io.BytesIO()
    members = {}
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in (("completed/full10m/forge_filtered.pos", os.urandom(300_000)),
                           ("completed/full10m/forge_filtered.hce", os.urandom(50_000)),
                           ("completed/other.txt", b"x" * 1000)):
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
            members[name] = hashlib.sha256(data).hexdigest()
    blob = buf.getvalue()
    pins = (hashlib.sha256(blob).hexdigest(), len(blob))
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
    return pins, members


def no_staging(out: str) -> bool:
    return not os.path.isdir(out) or not any(x.startswith(".staging_") for x in os.listdir(out))


def main() -> int:
    scratch = sys.argv[1]
    if os.path.exists(scratch):
        print(f"{scratch} exists; give a new folder")
        return 2
    globs = ["completed/full10m/forge_filtered.pos", "completed/full10m/forge_filtered.hce"]

    # 1a correct archive (pins of the synthetic blob; the CLI uses the real pins)
    dl, out = os.path.join(scratch, "dl_ok"), os.path.join(scratch, "out_ok")
    pins, mem = make_transport(dl)
    check(A.cmd_verify(dl, pins) == 0, "astra: part checksums verify")
    rc = A.cmd_extract(dl, out, globs, os.path.join(scratch, "ok.json"), pins, mem)
    check(rc == 0 and sorted(os.listdir(out)) == ["forge_filtered.hce", "forge_filtered.pos"] and no_staging(out),
          "astra: correct archive -> staged, checked, renamed: exactly the requested members, no staging left")
    # 1b existing target is never overwritten
    rc = A.cmd_extract(dl, out, globs, None, pins, mem)
    check(rc == 2 and sorted(os.listdir(out)) == ["forge_filtered.hce", "forge_filtered.pos"] and no_staging(out),
          "astra: existing targets are not overwritten (earlier files stay, staging cleaned)")
    # 1c whole-archive checksum failure (manifest consistent with itself, data different) -> nothing in place
    dl2, out2 = os.path.join(scratch, "dl_bad"), os.path.join(scratch, "out_bad")
    pins2, mem2 = make_transport(dl2, whole_sha_override="0" * 64)
    rc = A.cmd_extract(dl2, out2, globs, os.path.join(scratch, "bad.json"), ("0" * 64, pins2[1]), mem2)
    left = os.listdir(out2) if os.path.isdir(out2) else []
    check(rc != 0 and left == [], f"astra: checksum failure leaves nothing (staged files deleted; left: {left})")
    # 1d CR fix 3: a manifest that does not match the pins is refused before anything is written
    out3 = os.path.join(scratch, "out_pin")
    rc = A.cmd_extract(dl, out3, globs, None, ("f" * 64, pins[1]), mem)
    check(rc != 0 and (not os.path.isdir(out3) or os.listdir(out3) == []),
          "astra: manifest whole sha256 != pinned value -> refused, nothing written")
    rc = A.cmd_extract(dl, out3, globs, None, (pins[0], pins[1] + 1), mem)
    check(rc != 0 and (not os.path.isdir(out3) or os.listdir(out3) == []),
          "astra: manifest whole size != pinned size -> refused, nothing written")
    # 1e a pinned member with another sha256 -> staged files deleted, nothing renamed
    out4 = os.path.join(scratch, "out_member")
    bad_mem = dict(mem)
    bad_mem["completed/full10m/forge_filtered.pos"] = "e" * 64
    rc = A.cmd_extract(dl, out4, globs, None, pins, bad_mem)
    check(rc != 0 and os.listdir(out4) == [], f"astra: member pin mismatch -> nothing in place ({os.listdir(out4)})")
    # 1f the CLI pins are the release's values, and the real download's manifest matches them
    check(A.PINNED_WHOLE_SHA256 == "148803c5a45a5e291c18f667b918100ec1fa1a8e08d5a74dfe430651b3f1418f"
          and A.PINNED_WHOLE_SIZE == 2_329_781_152, "astra: pinned whole sha256 148803c5... and size 2,329,781,152")
    real = "D:/grok-pc-data/r11_nnue/astra_dl/transport_manifest.json"
    if os.path.isfile(real):
        rm = json.load(open(real, encoding="utf-8"))
        check(rm["whole"]["sha256"] == A.PINNED_WHOLE_SHA256 and rm["whole"]["size"] == A.PINNED_WHOLE_SIZE,
              "astra: the downloaded transport manifest matches the pins")

    # 1g CR fix 8: free disk space is checked before writing, downloading and extracting
    drive = C.winpath(scratch)[:2]
    try:
        C.require_disk(scratch, 1 << 20, "tiny write")
        check(True, "a small write passes the 1 GB small-write floor")
    except C.StageFailed as e:
        check(False, f"a small write was refused: {e}")
    saved_floors = dict(C._FLOORS)
    C._FLOORS[drive] = 1e6
    try:
        C.require_disk(scratch, 100 << 20, "bulk write")
        check(False, "a bulk write must be refused below the drive floor")
    except C.StageFailed as e:
        check("floor" in str(e), f"a bulk write below the drive floor is refused: {str(e)[:90]}")
    dl_refused = os.path.join(scratch, "dl_refused")
    rc = A.cmd_download(dl_refused)
    check(rc == 2 and not os.path.exists(dl_refused), "Astra download refused before anything is written (floor)")
    C._FLOORS.clear()
    C._FLOORS.update(saved_floors)
    saved_small = C.SMALL_WRITE_FLOOR_GB
    C.SMALL_WRITE_FLOOR_GB = 1e6
    out5 = os.path.join(scratch, "out_nospace")
    rc = A.cmd_extract(dl, out5, globs, None, pins, mem)
    C.SMALL_WRITE_FLOOR_GB = saved_small
    check(rc != 0 and os.listdir(out5) == [], "Astra extract refused for lack of space leaves nothing behind")

    # 0 the shipped config loads (a comment key in limits once broke every stage after the fix-8 commit)
    real_cfg = C.read_json(os.path.join(REPO, "opus_r11", "pipeline", "r11_config.json"))
    try:
        lim = C.limits_from(real_cfg)
        check(lim.min_disk_free_gb == 40.0 and lim.disk_floor_gb.get("D:") == 40.0,
              "the shipped r11_config.json loads (limits_from) with the 40 GB D: floor")
    except Exception as e:  # noqa: BLE001
        check(False, f"the shipped r11_config.json does not load: {e}")
    for section in ("data", "engine", "trainer", "check", "train"):
        check(section in real_cfg, f"config section {section!r} present")
    # CR R2 H1: yield is the only GPU policy - no share / duty cycle anywhere
    profs = real_cfg["train"]["profiles"]
    check(all(p.get("gpu_policy") == "yield" and "share_duty" not in p for p in profs.values()),
          f"every training profile yields to production, none shares ({ {k: p.get('gpu_policy') for k, p in profs.items()} })")
    import importlib.util
    spec = importlib.util.spec_from_file_location("r11_train_entry", os.path.join(REPO, "tools", "nnue_pytorch_amd", "r11",
                                                                                   "r11_train_entry.py"))
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)  # defines functions only; nothing of the trainer is imported
    for bad in (["--r11-policy", "share"], ["--r11-share-duty", "0.5"]):
        try:
            entry.parse_own_args(bad + ["--r11-clone", "x", "--r11-run-dir", "y", "--"])
            check(False, f"the entry must refuse {bad[0]}")
        except SystemExit as e:
            check("unknown option" in str(e), f"the entry refuses {bad[0]} (no share policy left)")
    # CR R2 M1: the entry checks for production BEFORE importing torch: with a dummy clone (no train.py, no trainer
    # modules) and a running "production" marker process it must exit 76, never reach an import
    marker = f"R11M1MARKER{os.getpid()}"
    pfile = os.path.join(scratch, "patterns.json")
    with open(pfile, "w", encoding="utf-8") as f:
        json.dump([marker], f)  # from a FILE: on the command line the entry's own launcher would match
    fake_clone = os.path.join(scratch, "fake_clone")
    os.makedirs(fake_clone)

    def run_entry(run_dir: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", "-B", spec.origin, "--r11-clone", fake_clone, "--r11-run-dir", run_dir,
                               "--r11-patterns-file", pfile, "--r11-affinity", "0x700", "--", "dummy.binpack"],
                              capture_output=True, text=True, timeout=300)

    dummy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(12)", marker])
    try:
        time.sleep(1.0)
        run_m1 = os.path.join(scratch, "run_m1")
        r = run_entry(run_m1)
    finally:
        dummy.wait(timeout=60)
    ev = open(os.path.join(run_m1, "r11_events.jsonl"), encoding="utf-8").read() if os.path.isfile(
        os.path.join(run_m1, "r11_events.jsonl")) else ""
    check(r.returncode == 76 and "yield_before_import" in ev and "No module named" not in r.stderr,
          f"production check before import torch: exit {r.returncode}, event yield_before_import "
          f"{'present' if 'yield_before_import' in ev else 'missing'}")
    # negative: no production marker -> the entry gets past the check (it must not match its own launcher) and only
    # then imports the trainer, which fails on the dummy clone
    r2 = run_entry(os.path.join(scratch, "run_m1_neg"))
    check(r2.returncode not in (0, 76) and "No module named 'train'" in r2.stderr,
          f"no production -> the entry does not yield to itself and reaches the trainer import (exit {r2.returncode})")
    # M1 hardened (found live 2026-10-30: production started while the entry was importing torch): a stub clone whose
    # train module starts the "production" marker during the imports (mode import) or inside main() before fit start
    # (mode fit); the entry must yield after the imports / at fit start without a checkpoint, and run through with no
    # marker (mode none)
    stub = os.path.join(scratch, "stub_clone")
    os.makedirs(os.path.join(stub, "trainer"))
    for rel, text in {
        "trainer/__init__.py": "",
        "trainer/callbacks.py": "class Callback:\n    pass\n",
        "trainer/engine.py": "class SimpleTrainer:\n    def load_checkpoint(self, path):\n        return {}\n\n"
                             "    def fit(self, train_loader, val_loader=None):\n        return None\n",
        "train.py": "import os, subprocess, sys, time, zipfile\n"
                    "MODE = os.environ['R11_STUB_MODE']\n\n\n"
                    "def production_starts():\n"
                    "    subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(6)', os.environ['R11_STUB_MARKER']])\n"
                    "    time.sleep(1.5)\n\n\n"
                    "if MODE == 'import':\n    production_starts()\n\n\n"
                    "class CheckpointManager:\n    pass\n\n\n"
                    "class FakeTrainer:\n"
                    "    check_val_every_n_epoch, current_epoch, global_step, max_epochs = 1, 0, 0, 1\n"
                    "    callback_metrics, _r11_val_loader = {}, None\n\n"
                    "    def save_checkpoint(self, path):\n"
                    "        with zipfile.ZipFile(path, 'w') as z:\n"
                    "            z.writestr('archive/data.pkl', b'stub')\n\n"
                    "    def flush_checkpoints(self):\n"
                    "        pass\n\n\n"
                    "def main():\n"
                    "    if MODE == 'rotate':  # the entry's real _save + rotation on six epochs\n"
                    "        cm, t = CheckpointManager(), FakeTrainer()\n"
                    "        for e, v in enumerate([0.9, 0.5, 0.7, 0.6, 0.8, 0.95]):\n"
                    "            t.current_epoch, t.global_step = e, 10 * (e + 1)\n"
                    "            cm._save(t, e + 1, True, v)\n"
                    "        print('STUB ROTATE END', flush=True)\n"
                    "        return\n"
                    "    if MODE == 'epochs':  # the entry's real epoch-end / validation-end saves: 6 epochs, validation every 3\n"
                    "        cm, t = CheckpointManager(), FakeTrainer()\n"
                    "        t.max_epochs, t.check_val_every_n_epoch, t._r11_val_loader = 6, 3, object()\n"
                    "        for e in range(6):\n"
                    "            t.current_epoch, t.global_step = e, 10 * (e + 1)\n"
                    "            cm.on_train_epoch_end(t)\n"
                    "            if (e + 1) % 3 == 0:\n"
                    "                t.callback_metrics = {'val_loss_epoch': 1.0 - 0.1 * e}\n"
                    "                cm.on_validation_end(t)\n"
                    "        print('STUB EPOCHS END', flush=True)\n"
                    "        return\n"
                    "    if MODE == 'fit':\n        production_starts()\n"
                    "    CheckpointManager().on_fit_start(FakeTrainer())\n"
                    "    print('STUB MAIN END', flush=True)\n",
    }.items():
        with open(os.path.join(stub, rel), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def marker_gone() -> bool:
        import psutil
        for _ in range(60):
            if not any(marker in " ".join(p.info["cmdline"] or []) for p in psutil.process_iter(["cmdline"])):
                return True
            time.sleep(0.5)
        return False

    stub_res = {}
    for mode in ("import", "fit", "none"):
        check(marker_gone(), f"no marker process left before stub mode {mode}")
        rd = os.path.join(scratch, f"run_m1_stub_{mode}")
        env = dict(os.environ, R11_STUB_MODE=mode, R11_STUB_MARKER=marker)
        rr = subprocess.run([sys.executable, "-I", "-B", spec.origin, "--r11-clone", stub, "--r11-run-dir", rd,
                             "--r11-patterns-file", pfile, "--r11-affinity", "0x700", "--", "dummy.binpack"],
                            capture_output=True, text=True, timeout=600, env=env)
        evs = [json.loads(x)["event"] for x in open(os.path.join(rd, "r11_events.jsonl"), encoding="utf-8")] \
            if os.path.isfile(os.path.join(rd, "r11_events.jsonl")) else []
        ck = [x for x in os.listdir(os.path.join(rd, "checkpoints")) if x.endswith(".ckpt")] \
            if os.path.isdir(os.path.join(rd, "checkpoints")) else []
        stub_res[mode] = (rr.returncode, evs, ck, rr.stderr[-300:])
    rc, evs, ck, err = stub_res["import"]
    check(rc == 76 and evs == ["yield_after_import"] and not ck,
          f"production starts during the imports -> exit 76 after the imports, trainer main never called: {stub_res['import']}")
    rc, evs, ck, err = stub_res["fit"]
    check(rc == 76 and evs == ["start", "fit_start", "stopped"] and not ck,
          f"production starts before fit -> exit 76 at fit start, no checkpoint: {stub_res['fit']}")
    rc, evs, ck, err = stub_res["none"]
    check(rc == 0 and evs == ["start", "fit_start", "finished"],
          f"no production -> the entry runs the trainer to its end (exit 0): {stub_res['none']}")
    check(marker_gone(), "the stub's marker processes ended by themselves")
    # CR R3 fail-closed: a CPU mask the PC does not have (one bit, so it passes the 1..3-CPU check) makes
    # SetProcessAffinityMask fail for real -> the entry exits 78 before importing anything, the build script builds
    # nothing, set_idle_background raises
    bad_mask = hex(1 << 40)
    rd = os.path.join(scratch, "run_r3_fail_closed")
    rr = subprocess.run([sys.executable, "-I", "-B", spec.origin, "--r11-clone", stub, "--r11-run-dir", rd,
                         "--r11-patterns-file", pfile, "--r11-affinity", bad_mask, "--", "dummy.binpack"],
                        capture_output=True, text=True, timeout=300, env=dict(os.environ, R11_STUB_MODE="none",
                                                                              R11_STUB_MARKER=marker))
    evs = [json.loads(x) for x in open(os.path.join(rd, "r11_events.jsonl"), encoding="utf-8")] \
        if os.path.isfile(os.path.join(rd, "r11_events.jsonl")) else []
    check(rr.returncode == 78 and [e["event"] for e in evs] == ["priority_failed"] and
          evs[0].get("failed") == [f"affinity {bad_mask} (error 87)"],  # CR R4: ERROR_INVALID_PARAMETER logged
          f"entry: a failed affinity call -> exit 78, event priority_failed, nothing imported: rc {rr.returncode} {evs}")
    build = os.path.join(REPO, "tools", "nnue_pytorch_amd", "r11", "build_r11_tools.py")
    rb = subprocess.run([sys.executable, "-I", "-B", build, "--affinity", bad_mask, "--out-dir",
                         os.path.join(scratch, "build_must_not_exist")], capture_output=True, text=True, timeout=300)
    check(rb.returncode == 2 and f"affinity {bad_mask} (error 87)" in rb.stdout and
          not os.path.exists(os.path.join(scratch, "build_must_not_exist")),
          f"build_r11_tools: a failed affinity call -> FAIL, nothing built: rc {rb.returncode} {rb.stdout.strip()[-160:]}")
    try:
        C.set_idle_background(1 << 40)
        check(False, "set_idle_background must fail closed on a failed affinity call")
    except C.StageFailed as e:
        check("affinity" in str(e) and "False" in str(e), f"set_idle_background fails closed: {e}")
    import r11_train as TR
    cfg_share = json.loads(json.dumps(real_cfg))
    cfg_share["train"]["profiles"]["smoke"]["gpu_policy"] = "share"
    try:
        TR.run_train(cfg_share, "smoke", C.Log(None, "train"), None)
        check(False, "a share profile must be refused")
    except C.StageFailed as e:
        check("yield is the only GPU policy" in str(e), "the train stage refuses a share profile")
    # CR R3-3: checkpoint rotation must not delete - the shipped profiles keep >= 1,000,000, the entry and the driver
    # refuse less, and the entry's real save/rotate code keeps all six checkpoints of a stub run and tracks the best
    profs = real_cfg["train"]["profiles"]
    check(all(int(p.get("keep_last", 0)) >= 1_000_000 for p in profs.values()),
          f"the shipped profiles keep every checkpoint: {[(k, p.get('keep_last')) for k, p in profs.items()]}")
    try:
        entry.parse_own_args(["--r11-clone", "x", "--r11-run-dir", "y", "--r11-keep-last", "2", "--"])
        check(False, "the entry must refuse --r11-keep-last 2")
    except SystemExit as e:
        check("CR R3" in str(e), "the entry refuses --r11-keep-last 2 (it could delete checkpoints)")
    check(entry.parse_own_args(["--r11-clone", "x", "--r11-run-dir", "y", "--"])[0]["keep_last"] == 1_000_000,
          "the entry's default keep_last is 1,000,000")
    # CR R4: no deletion code left in the rotation - the entry's only os.remove is a failed write's own .tmp
    esrc = open(spec.origin, encoding="utf-8").read()
    removes = re.findall(r"os\.remove\(([^)]*)\)", esrc)
    check(removes == ["tmp"] and "rotation.jsonl" not in esrc,
          f"the entry deletes nothing but a failed checkpoint's own .tmp (os.remove calls: {removes})")
    cfg_k = json.loads(json.dumps(real_cfg))
    cfg_k["train"]["profiles"]["smoke"]["keep_last"] = 2
    try:
        TR.run_train(cfg_k, "smoke", C.Log(None, "train"), None)
        check(False, "the train driver must refuse keep_last 2")
    except C.StageFailed as e:
        check("could delete checkpoints" in str(e), "the train driver refuses a profile with keep_last 2")
    rd = os.path.join(scratch, "run_r3_rotate")
    rr = subprocess.run([sys.executable, "-I", "-B", spec.origin, "--r11-clone", stub, "--r11-run-dir", rd,
                         "--r11-patterns-file", pfile, "--r11-affinity", "0x700", "--r11-disk-floor-gb", "1", "--",
                         "dummy.binpack"], capture_output=True, text=True, timeout=600,
                        env=dict(os.environ, R11_STUB_MODE="rotate", R11_STUB_MARKER=marker))
    cdir = os.path.join(rd, "checkpoints")
    ck = sorted(x for x in os.listdir(cdir) if x.endswith(".ckpt")) if os.path.isdir(cdir) else []
    ixp = os.path.join(cdir, "r11_ckpt_index.json")
    ix = json.load(open(ixp, encoding="utf-8")) if os.path.isfile(ixp) else {}
    best = os.path.basename((ix.get("best") or {}).get("path") or "")
    check(rr.returncode == 0 and len(ck) == 6 and not os.path.exists(os.path.join(cdir, "rotation.jsonl")) and
          not ix.get("removed") and best == "epoch=1-step=20.ckpt",
          f"the entry's save/rotate code keeps all 6 checkpoints and tracks the best (val 0.5): rc {rr.returncode}, "
          f"{len(ck)} files, best {best}, removed {ix.get('removed')} {rr.stderr[-200:]}")
    # save interval (nothing is deleted, so the interval keeps a run inside the disk floor): the entry's real
    # epoch-end / validation-end logic saves every N epochs and at the last; the first checkpoint's floor reserve
    # follows L1 (a fixed 512 MiB let an L1 1024 checkpoint, 1.44 GiB, cross the floor)
    gib = 2**30
    check(1.5 * gib <= entry.first_ckpt_need(["--l1", "1024"]) <= 1.7 * gib and
          entry.first_ckpt_need(["--l1", "64"]) == 512 << 20,
          "first-checkpoint floor reserve: L1 1024 -> 1.6 GiB (actual 1.44), L1 64 -> 512 MiB")
    try:
        entry.parse_own_args(["--r11-clone", "x", "--r11-run-dir", "y", "--r11-save-every", "0", "--"])
        check(False, "the entry must refuse --r11-save-every 0")
    except SystemExit:
        check(True, "the entry refuses --r11-save-every 0")
    saved = {}
    for label, extra in (("every3", ["--r11-save-every", "3"]), ("default", [])):
        rd = os.path.join(scratch, f"run_save_{label}")
        rr = subprocess.run([sys.executable, "-I", "-B", spec.origin, "--r11-clone", stub, "--r11-run-dir", rd,
                             "--r11-patterns-file", pfile, "--r11-affinity", "0x700", "--r11-disk-floor-gb", "1"] + extra
                            + ["--", "dummy.binpack"], capture_output=True, text=True, timeout=600,
                            env=dict(os.environ, R11_STUB_MODE="epochs", R11_STUB_MARKER=marker))
        cdir = os.path.join(rd, "checkpoints")
        saved[label] = (rr.returncode, sorted(x for x in os.listdir(cdir) if x.endswith(".ckpt")) if os.path.isdir(cdir) else [])
    check(saved["every3"] == (0, ["epoch=2-step=30.ckpt", "epoch=5-step=60.ckpt"]),
          f"--r11-save-every 3: checkpoints only at the validated epochs 3 and 6: {saved['every3']}")
    check(saved["default"][0] == 0 and len(saved["default"][1]) == 6,
          f"default (every epoch): 6 checkpoints: {saved['default']}")
    try:
        TR.save_every({"save_every_epochs": 7, "max_epochs": 20})
        check(False, "the driver must refuse a save interval that does not divide max_epochs")
    except C.StageFailed:
        check(all(TR.save_every(p) >= 1 for p in profs.values()),
              "the driver refuses save_every_epochs 7 for 20 epochs; the shipped profiles divide their max_epochs")

    # 1h CR fix 10: sealed inputs are identified by their full sha256; a change in the middle of a big file (which a
    # first/last-MiB fingerprint misses) is detected
    big = os.path.join(scratch, "sealed_big.bin")
    with open(big, "wb") as f:
        f.write(os.urandom(3 << 20))
    sealed = C.SealedInputs()
    registered = sealed.sha256(big)

    def edges(path: str) -> str:  # the pre-fix-10 fingerprint, only to show what it missed
        hh = hashlib.sha256()
        with open(path, "rb") as fh:
            hh.update(fh.read(1 << 20))
            fh.seek(os.path.getsize(path) - (1 << 20))
            hh.update(fh.read(1 << 20))
        return hh.hexdigest()

    before_edges = edges(big)
    with open(big, "r+b") as f:
        f.seek((3 << 20) // 2)
        b = f.read(1)
        f.seek((3 << 20) // 2)
        f.write(bytes([b[0] ^ 1]))
    check(edges(big) == before_edges, "the old first/last-MiB fingerprint does NOT see a change in the middle")
    try:
        C.SealedInputs().verify(big, registered, "test input")
        check(False, "a changed sealed input must be refused")
    except C.StageFailed as e:
        check("input changed since registration" in str(e), "the full sha256 detects the change in the middle")

    # 1d CR fix 1: no STOP/PAUSE control files anywhere in the pipeline; the hold is the named event
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.windll.kernel32
    k32.CreateEventW.restype = wintypes.HANDLE
    k32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    k32.ResetEvent.argtypes = [wintypes.HANDLE]
    k32.SetEvent.argtypes = [wintypes.HANDLE]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    check(not C.hold_requested(), "no hold before the event exists")
    h = k32.CreateEventW(None, True, True, C.HOLD_EVENT)
    check(bool(h) and C.hold_requested(), f"hold active while {C.HOLD_EVENT} is signalled")
    k32.ResetEvent(h)
    check(not C.hold_requested(), "no hold while the event is reset")
    k32.SetEvent(h)
    k32.CloseHandle(h)
    check(not C.hold_requested(), "no hold after the last handle is closed")
    offenders = []
    for d in ("opus_r11/pipeline", "tools/nnue_pytorch_amd/r11"):
        for fn in os.listdir(os.path.join(REPO, d)):
            if fn.endswith(".py"):
                text = open(os.path.join(REPO, d, fn), encoding="utf-8").read()
                for marker in ('"STOP"', '"PAUSE"', "stop_requested", "control/STOP", "control/PAUSE", '"control"'):
                    if marker in text:
                        offenders.append(f"{d}/{fn}: {marker}")
    check(offenders == [], f"no STOP/PAUSE control files in the pipeline code: {offenders}")

    # 1e CR fix 2 (amended): Idle priority + I/O priority very low + memory priority low on <= 3 cores, inherited by a
    # child process, and NO working-set cap (background mode capped it at 32 MB: 300 MB touched stayed at 32 MB)
    probe = os.path.join(scratch, "prio_probe.py")
    with open(probe, "w", encoding="utf-8", newline="\n") as f:
        f.write("import ctypes, json, subprocess, sys\n"
                "from ctypes import wintypes\n"
                "import numpy as np, psutil\n"
                f"sys.path.insert(0, {os.path.join(REPO, 'opus_r11', 'pipeline')!r})\n"
                "import r11_common as C\n"
                "def state():\n"
                "    k32 = ctypes.windll.kernel32\n"
                "    k32.GetCurrentProcess.restype = wintypes.HANDLE\n"
                "    k32.GetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]\n"
                "    v = wintypes.ULONG(99)\n"
                "    ok = k32.GetProcessInformation(k32.GetCurrentProcess(), 0, ctypes.byref(v), 4)\n"
                "    p = psutil.Process()\n"
                "    return {'nice': int(p.nice()), 'io': int(p.ionice()), 'mem': int(v.value) if ok else -1,\n"
                "            'aff': p.cpu_affinity()}\n"
                "if sys.argv[1:] == ['child']:\n"
                "    print(json.dumps(state()))\n"
                "    sys.exit(0)\n"
                "info = C.set_idle_background(0x700)\n"
                "a = np.ones(300 * 2**20 // 8)\n"
                "wset_mb = psutil.Process().memory_info().wset / 2**20\n"
                "child = subprocess.run([sys.executable, '-I', '-B', __file__, 'child'], capture_output=True, text=True)\n"
                "print(json.dumps({'info': info, **state(), 'wset_mb': round(wset_mb), "
                "'child': json.loads(child.stdout.strip().splitlines()[-1])}))\n")
    r = subprocess.run([sys.executable, "-I", "-B", probe], capture_output=True, text=True)
    try:
        pr = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        pr = {"error": r.stdout[-300:] + r.stderr[-300:]}
    want = {"nice": 0x40, "io": 0, "mem": 2, "aff": [8, 9, 10]}
    check(all(pr.get(k) == v for k, v in want.items()),
          f"set_idle_background: Idle (0x40), I/O priority very low (0), memory priority low (2), CPUs 8-10: {pr}")
    check(all((pr.get("child") or {}).get(k) == v for k, v in want.items()),
          f"a child inherits Idle, I/O very low, memory low and the 3-core mask: {pr.get('child')}")
    check((pr.get("wset_mb") or 0) >= 200,
          f"no working-set cap: 300 MB touched -> working set {pr.get('wset_mb')} MB (background mode kept it at 32 MB)")
    bg = re.compile(r"SetPriorityClass\([^)]*(0x00100000|PROCESS_MODE_BACKGROUND_BEGIN)")
    bg_users = []
    for d in ("opus_r11/pipeline", "tools/nnue_pytorch_amd/r11"):
        for fn in os.listdir(os.path.join(REPO, d)):
            if fn.endswith((".py", ".cpp")) and bg.search(open(os.path.join(REPO, d, fn), encoding="utf-8").read()):
                bg_users.append(f"{d}/{fn}")
    check(bg_users == [], f"no process enters background mode (PROCESS_MODE_BACKGROUND_BEGIN): {bg_users}")
    try:
        C.set_idle_background(0xF)
        check(False, "a 4-CPU mask must be refused")
    except C.StageFailed:
        check(True, "a 4-CPU mask is refused")

    # 1f CR R3: the cap lifter for processes started before the fix 2 amendment (logs/cr2_amendment/
    # lift_wscap_watch.py) - identity (a root must be running and carry the expected text; PIDs are never re-opened
    # blindly) and fail-closed; a probe enters background mode like the old code and prints its working-set flags
    watcher = os.path.join(REPO, "opus_r11", "logs", "cr2_amendment", "lift_wscap_watch.py")
    lmark = f"R11LIFTPROBE{os.getpid()}"
    lrel = os.path.join("opus_r11", "r11_lift_probe.py")  # CR R4: --expect must name an R11 script
    lprobe = os.path.join(scratch, lrel)
    os.makedirs(os.path.dirname(lprobe), exist_ok=True)
    with open(lprobe, "w", encoding="utf-8", newline="\n") as f:
        f.write("import ctypes, sys, time\n"
                "from ctypes import wintypes\n"
                "import numpy as np\n"
                "k32 = ctypes.windll.kernel32\n"
                "k32.GetCurrentProcess.restype = wintypes.HANDLE\n"
                "k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]\n"
                "k32.GetProcessWorkingSetSizeEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t),\n"
                "                                           ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(wintypes.DWORD)]\n"
                "h = k32.GetCurrentProcess()\n"
                "k32.SetPriorityClass(h, 0x00100000)  # background mode, as the code before the amendment did\n"
                "k32.SetPriorityClass(h, 0x40)\n"
                "a = np.ones(64 * 2**20 // 8)\n"
                "for i in range(40):\n"
                "    mn, mx, fl = ctypes.c_size_t(), ctypes.c_size_t(), wintypes.DWORD()\n"
                "    k32.GetProcessWorkingSetSizeEx(h, ctypes.byref(mn), ctypes.byref(mx), ctypes.byref(fl))\n"
                "    print(hex(fl.value), flush=True)\n"
                "    a += 1.0\n"
                "    time.sleep(0.5)\n")

    def run_watcher(args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", "-B", watcher] + args, capture_output=True, text=True, timeout=120)

    wl = os.path.join(scratch, "lift_wscap.log")
    lp = subprocess.Popen([sys.executable, "-I", "-B", lprobe, lmark], stdout=subprocess.PIPE, text=True)
    time.sleep(3.0)
    r_generic = run_watcher([wl, "--expect", lmark, "--once", str(lp.pid)])  # in the command line, but no R11 script
    r_expect = run_watcher([wl, "--expect", os.path.join("opus_r11", "r11_other.py"), "--once", str(lp.pid)])
    gone = subprocess.Popen([sys.executable, "-c", "pass"])
    gone.wait()
    r_dead = run_watcher([wl, "--expect", lrel, "--once", str(gone.pid)])
    r_mask = run_watcher([wl, "--expect", lrel, "--affinity", hex(1 << 40), "--once", str(lp.pid)])
    before = open(wl, encoding="utf-8").read() if os.path.isfile(wl) else ""
    rcs = (r_generic.returncode, r_expect.returncode, r_dead.returncode, r_mask.returncode)
    check(rcs == (2, 2, 2, 2) and "soft defaults" not in before and before.count("FAIL") == 4 and
          "must name an R11 script" in before,
          f"lifter refuses (exit 2, nothing changed): --expect that names no R11 script, a root without the expected "
          f"R11 script, a dead root, a mask it cannot set: {rcs}")
    r_ok = run_watcher([wl, "--expect", lrel, "--once", str(lp.pid)])
    out, _ = lp.communicate(timeout=120)  # the probe ends by itself (20 s); nothing is killed
    flags = out.split()
    lifted = [ln for ln in open(wl, encoding="utf-8").read().splitlines() if "soft defaults" in ln]
    check(r_ok.returncode == 0 and len(lifted) == 1 and flags[:1] == ["0x6"] and flags[-1:] == ["0xa"],
          f"lifter un-caps exactly the capped probe (the venv launcher's child): exit {r_ok.returncode}, "
          f"{len(lifted)} change(s), probe flags {flags[0] if flags else '?'} -> {flags[-1] if flags else '?'}")

    # 2 CR fix 4: the process check FAILS without psutil; an unreadable python command line counts as production
    saved = sys.modules.get("psutil", "absent")
    sys.modules["psutil"] = None  # makes "import psutil" raise ImportError
    try:
        C.production_processes(["anything"])
        failed = False
    except C.StageFailed:
        failed = True
    finally:
        if saved == "absent":
            del sys.modules["psutil"]
        else:
            sys.modules["psutil"] = saved
    check(failed, "process check fails (StageFailed) when psutil is missing")
    res = C.production_processes([r"this-pattern-matches-no-process-\d{40}"])
    check(res == [], "process check with psutil and no match returns []")
    import psutil

    class FakeProc:
        def __init__(self, pid, name, cmdline, ppid=1000):
            self.info = {"pid": pid, "ppid": ppid, "name": name, "cmdline": cmdline}

    real_iter = psutil.process_iter
    psutil.process_iter = lambda attrs=None: iter([FakeProc(999001, "python.exe", None),
                                                   FakeProc(999002, "System", None),
                                                   FakeProc(999003, "notepad.exe", ["notepad.exe", "x.txt"]),
                                                   FakeProc(999004, None, None, ppid=4),
                                                   FakeProc(999005, None, None, ppid=1234)])
    try:
        res = C.production_processes([r"no-such-pattern-\d{30}"])
    finally:
        psutil.process_iter = real_iter
    check([r["pid"] for r in res] == [999001, 999005] and all(r["pattern"] == C.UNREADABLE for r in res),
          "unreadable command line: python and unnamed non-kernel processes count as production (wait); "
          f"System and kernel children (ppid 4) do not: {res}")

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
