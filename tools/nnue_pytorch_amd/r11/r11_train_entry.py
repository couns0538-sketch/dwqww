"""R11 train entry: runs nnue-pytorch's own train.main() (the R6 clone, unchanged) with three additions.

GPL-3.0 (imports the trainer's modules at run time from --r11-clone; nothing is copied). Tool tree only.

1. R11CheckpointManager replaces the trainer's CheckpointManager:
   - after every validation (the epoch's scheduler step is done and val_loss_epoch is known) it writes
     <run>/checkpoints/epoch=E-step=S.ckpt atomically (temp name + rename) with "r11_next_epoch" = E + 1;
     without a validation loader it saves at the epoch end with "r11_next_epoch" = E (the trainer's own redo rule);
   - it keeps the newest --r11-keep-last periodic checkpoints plus the best by val_loss_epoch and removes older
     ones it wrote itself (listed in <run>/checkpoints/r11_ckpt_index.json; every removal is logged to
     rotation.jsonl). The index survives restarts, so rotation works across auto-resumes (the trainer's own
     save_top_k only knows the checkpoints of the current process);
   - one fixed directory for all restarts (the trainer's default changes with every TensorBoard version).
2. Exact resume: SimpleTrainer.load_checkpoint continues at "r11_next_epoch" (the trainer restarts at the saved
   epoch, which trains the last finished epoch twice).
3. Control and governor, checked every --r11-check-seconds during training:
   - hold: sleep while the named event Local\\Forge_R11_Hold is signalled (no STOP/PAUSE files: R11 is stopped by
     its own PID and resumes from the newest checkpoint);
   - free RAM below --r11-min-free-ram-gb: save and exit 75 (the driver resumes when RAM is back); a watchdog thread
     exits 97 at once below --r11-hard-ram-gb (no save: the live trainer comes first);
   - YIELD is the only GPU policy (CR R2 H1: no sharing, no duty cycle): the production-trainer check runs before
     torch is imported (CR R2 M1: exit 76 at once, nothing loaded) and again during training; when a production
     trainer appears (command-line regex list; psutil missing = fail, an unreadable python command line = running)
     the entry saves and exits 76, the driver waits for it to end and resumes.
Usage: <trainer venv python> -B r11_train_entry.py --r11-clone <clone> --r11-run-dir <dir> [--r11-keep-last 2]
       [--r11-min-free-ram-gb 8] [--r11-hard-ram-gb 7] --r11-patterns-file <json list of regexes>
       [--r11-check-seconds 20]
       (the production regexes come from a FILE: on a command line they would match the entry's own launcher)
       [--r11-affinity 0x700] [--r11-disk-floor-gb 40] -- <train.py arguments>
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import sys
import threading
import time
from ctypes import wintypes

EXIT_RESOURCE, EXIT_YIELD, EXIT_HARD = 75, 76, 97


class R11Stop(Exception):
    def __init__(self, code: int, reason: str):
        super().__init__(reason)
        self.code = code
        self.reason = reason


def parse_own_args(argv: list[str]) -> tuple[dict, list[str]]:
    if "--" not in argv:
        raise SystemExit("usage: r11_train_entry.py --r11-... -- <train.py args>")
    i = argv.index("--")
    own, rest = argv[:i], argv[i + 1:]
    opts = {"clone": None, "run_dir": None, "keep_last": 2,
            "min_free_ram_gb": 8.0, "hard_ram_gb": 7.0, "patterns_file": None,
            "check_seconds": 20.0, "affinity": "0x700", "disk_floor_gb": 40.0}
    k = 0
    while k < len(own):
        key = own[k]
        if not key.startswith("--r11-") or k + 1 >= len(own):
            raise SystemExit(f"bad option {key}")
        name = key[len("--r11-"):].replace("-", "_")
        if name not in opts:
            raise SystemExit(f"unknown option {key}")
        val = own[k + 1]
        opts[name] = type(opts[name])(val) if opts[name] is not None else val
        k += 2
    if not opts["clone"] or not opts["run_dir"]:
        raise SystemExit("--r11-clone and --r11-run-dir are required")
    return opts, rest


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def free_gb() -> tuple[float, float]:
    if sys.platform != "win32":
        return 64.0, 64.0
    ms = _MEMORYSTATUSEX()
    ms.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
    return ms.ullAvailPhys / 2**30, ms.ullAvailPageFile / 2**30


HOLD_EVENT = "Local\\Forge_R11_Hold"


def hold_requested() -> bool:
    """True while the named event Local\\Forge_R11_Hold exists and is signalled."""
    if sys.platform != "win32":
        return False
    k32 = ctypes.windll.kernel32
    k32.OpenEventW.restype = wintypes.HANDLE
    k32.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k32.OpenEventW(0x00100000, False, HOLD_EVENT)  # SYNCHRONIZE
    if not h:
        return False
    try:
        return k32.WaitForSingleObject(h, 0) == 0
    finally:
        k32.CloseHandle(h)


def production_running(patterns: list[str]) -> str | None:
    """Matched pattern or None. CR fix 4: psutil missing / no process list -> SystemExit (the run fails); a python
    process whose command line cannot be read (AccessDenied) counts as running (yield), never as "no match"."""
    try:
        import psutil
    except ImportError:
        raise SystemExit("[r11] psutil is missing: cannot check for production trainers (fail)")
    regs = [re.compile(p, re.I) for p in patterns if p]
    me = os.getpid()
    try:  # this process and its own launcher chain are never "production" (the venv launcher is a parent process)
        own = {me} | {a.pid for a in psutil.Process(me).parents()}
    except Exception:  # noqa: BLE001
        own = {me}
    try:
        procs = list(psutil.process_iter(["pid", "ppid", "name", "cmdline"]))
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"[r11] process list unavailable ({type(e).__name__}): cannot check for production trainers")
    for p in procs:
        info = p.info
        if info.get("pid") in own:
            continue
        name = info.get("name") or ""
        cmdline = info.get("cmdline")
        if cmdline is None:
            kernel = not name and info.get("ppid") in (0, 4)  # Registry, Memory Compression, Secure System
            if not kernel and (not name or name.lower().startswith("python")):
                return "command line unreadable (AccessDenied): treated as a production trainer"
            continue
        cmd = " ".join(cmdline)
        for r in regs:
            if r.search(cmd):
                return r.pattern
    return None


def log_event(run_dir: str, kind: str, **kw) -> None:
    rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": kind}
    rec.update(kw)
    with open(os.path.join(run_dir, "r11_events.jsonl"), "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[r11] {kind} {json.dumps(kw)}", flush=True)


def main() -> int:
    opts, train_args = parse_own_args(sys.argv[1:])
    run_dir = os.path.abspath(opts["run_dir"])
    ckpt_dir = os.path.join(run_dir, "checkpoints")
    os.makedirs(ckpt_dir, exist_ok=True)
    clone = os.path.abspath(opts["clone"])
    sys.path.insert(0, clone)
    os.chdir(clone)
    if sys.platform == "win32":
        # CR fix 2 (amended): Idle (0x40) + I/O priority very low + memory priority low on at most 3 cores (the
        # trainer's loader threads inherit the mask). NOT background mode: it caps the working set at 32 MB (measured:
        # this entry ran at 90 % kernel time, 445k page faults/s)
        mask = int(opts["affinity"], 0)
        if bin(mask).count("1") > 3:
            raise SystemExit("--r11-affinity must select at most 3 CPUs")
        import psutil
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        k32.SetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        h = k32.GetCurrentProcess()
        k32.SetPriorityClass(h, 0x00000040)
        psutil.Process().ionice(psutil.IOPRIO_VERYLOW)
        low = wintypes.ULONG(2)  # MEMORY_PRIORITY_LOW
        k32.SetProcessInformation(h, 0, ctypes.byref(low), 4)  # ProcessMemoryPriority
        k32.SetProcessAffinityMask(h, mask)
    if not opts["patterns_file"]:
        raise SystemExit("--r11-patterns-file is required (the production-trainer regexes)")
    with open(opts["patterns_file"], "r", encoding="utf-8") as f:
        patterns = [p for p in json.load(f) if p]
    if not patterns:
        raise SystemExit("the production-trainer pattern list is empty")

    # CR R2 M1: the production-trainer check runs BEFORE torch or any trainer module is imported - when production is
    # running the entry exits 76 at once: no GPU context, no RAM taken, nothing loaded
    hit = production_running(patterns)
    if hit:
        log_event(run_dir, "yield_before_import", pattern=hit)
        sys.stdout.flush()
        os._exit(EXIT_YIELD)

    # hard RAM watchdog: exit at once (no save) - the live trainer must never be pushed into the commit limit
    def watchdog() -> None:
        while True:
            ram, commit = free_gb()
            if ram < opts["hard_ram_gb"] or commit < opts["hard_ram_gb"]:
                print(f"[r11] HARD RAM FLOOR: free {ram:.2f} GB commit {commit:.2f} GB < {opts['hard_ram_gb']} GB, exit 97",
                      flush=True)
                os._exit(EXIT_HARD)
            time.sleep(1.0)

    threading.Thread(target=watchdog, daemon=True).start()

    import torch  # noqa: F401  (after the watchdog: importing torch already costs memory)
    import train as T
    from trainer import callbacks as CB
    from trainer import engine as E

    index_path = os.path.join(ckpt_dir, "r11_ckpt_index.json")

    def load_index() -> dict:
        if os.path.isfile(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"entries": [], "best": None, "removed": []}

    def save_index(ix: dict) -> None:
        tmp = index_path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(ix, f, indent=1)
        os.replace(tmp, index_path)

    class R11CheckpointManager(CB.Callback):
        def __init__(self, save_last=True, every_n_epochs=20, save_top_k=-1, dirpath=None):  # trainer's signature
            super().__init__()
            self.keep_last = int(opts["keep_last"])
            self.last_check = 0.0
            self.has_val = False

        # ---- saving and rotation
        def _save(self, trainer, next_epoch: int, complete: bool, val_loss, tag: str = "") -> str:
            name = f"{tag}epoch={trainer.current_epoch}-step={trainer.global_step}.ckpt"
            path = os.path.join(ckpt_dir, name)
            tmp = path + ".tmp"
            # CR fix 8: a checkpoint the size of the newest one must fit above the run drive's floor, else exit 75
            # without writing (the driver waits and resumes from the newest checkpoint)
            import shutil
            sizes = [x.get("bytes", 0) for x in load_index().get("entries", [])]
            need = max(sizes) if sizes else 512 << 20
            free = shutil.disk_usage(ckpt_dir).free
            if (free - need) / 2**30 < opts["disk_floor_gb"]:
                raise R11Stop(EXIT_RESOURCE, f"disk: {free / 2**30:.1f} GB free, a {need / 2**30:.2f} GB checkpoint "
                                             f"would cross the {opts['disk_floor_gb']} GB floor; not saved")
            self._pending_meta = {"r11_next_epoch": int(next_epoch), "r11_epoch_complete": bool(complete),
                                  "r11_val_loss": val_loss}
            trainer.save_checkpoint(tmp)
            trainer.flush_checkpoints()
            # CR fix 7: verify before the rename - torch.save writes a zip whose central directory is written last,
            # so a complete, readable directory with the state dict proves the file was finished
            import zipfile
            try:
                with zipfile.ZipFile(tmp) as z:
                    names = z.namelist()
                if not any(n.endswith("data.pkl") for n in names):
                    raise ValueError("no data.pkl in the checkpoint archive")
            except Exception as ex:  # noqa: BLE001
                os.remove(tmp)
                raise R11Stop(EXIT_RESOURCE, f"checkpoint {tmp} failed its check ({ex}); removed, will retry")
            os.replace(tmp, path)
            ix = load_index()
            ix["entries"] = [x for x in ix["entries"] if x["path"] != path]
            ix["entries"].append({"path": path, "epoch": trainer.current_epoch, "next_epoch": int(next_epoch),
                                  "step": trainer.global_step, "val_loss": val_loss, "complete": bool(complete),
                                  "saved": time.strftime("%Y-%m-%dT%H:%M:%S"), "bytes": os.path.getsize(path)})
            self._rotate(ix)
            save_index(ix)
            log_event(run_dir, "checkpoint", path=path, next_epoch=next_epoch, val_loss=val_loss,
                      best=(ix["best"] or {}).get("path"))
            return path

        def _rotate(self, ix: dict) -> None:
            live = [x for x in ix["entries"] if os.path.isfile(x["path"])]
            scored = [x for x in live if isinstance(x.get("val_loss"), (int, float)) and x["val_loss"] == x["val_loss"]]
            best = min(scored, key=lambda x: (x["val_loss"], -x["step"])) if scored else None
            ix["best"] = best
            newest = sorted(live, key=lambda x: (x["next_epoch"], x["step"], x["saved"]))[-self.keep_last:]
            keep = {x["path"] for x in newest} | ({best["path"]} if best else set())
            for x in live:
                p = x["path"]
                inside = os.path.dirname(os.path.abspath(p)) == os.path.abspath(ckpt_dir)
                if p not in keep and inside and os.path.basename(p).endswith(".ckpt"):
                    os.remove(p)  # R11 rule: newest N + best; only files this manager wrote (listed in its index)
                    ix["removed"].append({"path": p, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
                    with open(os.path.join(ckpt_dir, "rotation.jsonl"), "a", encoding="utf-8", newline="\n") as f:
                        f.write(json.dumps({"removed": p, "epoch": x["epoch"], "val_loss": x.get("val_loss"),
                                            "kept": sorted(keep)}) + "\n")
            ix["entries"] = [x for x in ix["entries"] if os.path.isfile(x["path"])]

        def on_save_checkpoint(self, trainer, checkpoint):
            meta = getattr(self, "_pending_meta", None)
            if meta:
                checkpoint.update(meta)

        def on_fit_start(self, trainer):
            self.has_val = trainer.check_val_every_n_epoch is not None
            log_event(run_dir, "fit_start", epoch=trainer.current_epoch, step=trainer.global_step,
                      max_epochs=trainer.max_epochs)

        def on_validation_end(self, trainer):
            self.has_val = True
            val = trainer.callback_metrics.get("val_loss_epoch")
            val = float(val) if val is not None else None
            self._save(trainer, trainer.current_epoch + 1, True, val)

        def on_train_epoch_end(self, trainer):
            # with validation the save happens after it; without, save here (the trainer's own redo rule)
            will_validate = getattr(trainer, "_r11_val_loader", None) is not None and \
                (trainer.current_epoch + 1) % max(1, trainer.check_val_every_n_epoch) == 0
            if not will_validate:
                self._save(trainer, trainer.current_epoch, False, None)

        def on_train_end(self, trainer):
            trainer.flush_checkpoints()
            log_event(run_dir, "train_end", epoch=trainer.current_epoch, step=trainer.global_step)

        # ---- control and governor (yield is the only GPU policy: CR R2 H1, no duty-cycle sharing)
        def on_train_batch_end(self, trainer, batch, batch_idx, outputs):
            now = time.time()
            if now - self.last_check < opts["check_seconds"]:
                return
            self.last_check = now
            held = False
            while hold_requested():
                if not held:
                    log_event(run_dir, "hold", event=HOLD_EVENT)
                    held = True
                time.sleep(10)
            if held:
                log_event(run_dir, "hold_released")
            reason, code = None, 0
            ram, commit = free_gb()
            if ram < opts["min_free_ram_gb"] or commit < opts["min_free_ram_gb"]:
                reason, code = f"free RAM {ram:.2f} GB / commit {commit:.2f} GB < {opts['min_free_ram_gb']} GB", EXIT_RESOURCE
            else:
                hit = production_running(patterns)
                if hit:
                    reason, code = f"production trainer running ({hit})", EXIT_YIELD
            if reason:
                path = self._save(trainer, trainer.current_epoch, False, None, tag="stop-")
                raise R11Stop(code, f"{reason}; saved {path}")

    T.CheckpointManager = R11CheckpointManager
    orig_load = E.SimpleTrainer.load_checkpoint
    orig_fit = E.SimpleTrainer.fit

    def load_checkpoint(self, path):
        ck = orig_load(self, path)
        if "r11_next_epoch" in ck:
            self.current_epoch = int(ck["r11_next_epoch"])
        log_event(run_dir, "resumed", path=path, epoch=self.current_epoch, step=self.global_step)
        return ck

    def fit(self, train_loader, val_loader=None):
        self._r11_val_loader = val_loader
        return orig_fit(self, train_loader, val_loader)

    E.SimpleTrainer.load_checkpoint = load_checkpoint
    E.SimpleTrainer.fit = fit
    sys.argv = [os.path.join(clone, "train.py")] + train_args
    log_event(run_dir, "start", argv=train_args, policy="yield", keep_last=opts["keep_last"])
    try:
        T.main()
    except R11Stop as s:
        log_event(run_dir, "stopped", code=s.code, reason=s.reason)
        sys.stdout.flush()
        os._exit(s.code)
    log_event(run_dir, "finished")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
