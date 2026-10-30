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
   - --r11-policy yield: when a production trainer appears (command-line regex list, fail closed when the process
     list is unavailable) save and exit 76, the driver waits for it to end and resumes; share: keep running, sleep
     so the GPU duty is at most --r11-share-duty; ignore: nothing.
Usage: <trainer venv python> -B r11_train_entry.py --r11-clone <clone> --r11-run-dir <dir> [--r11-keep-last 2]
       [--r11-policy yield|share|ignore] [--r11-share-duty 1.0] [--r11-min-free-ram-gb 8] [--r11-hard-ram-gb 7]
       [--r11-patterns 'regex1;regex2'] [--r11-check-seconds 20] -- <train.py arguments>
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
    opts = {"clone": None, "run_dir": None, "keep_last": 2, "policy": "share", "share_duty": 1.0,
            "min_free_ram_gb": 8.0, "hard_ram_gb": 7.0, "patterns": "guard.tag;forge_nnue_train[\\\\/]runs",
            "check_seconds": 20.0, "affinity": "0x700"}
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
    try:
        procs = list(psutil.process_iter(["pid", "ppid", "name", "cmdline"]))
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"[r11] process list unavailable ({type(e).__name__}): cannot check for production trainers")
    for p in procs:
        info = p.info
        if info.get("pid") == me:
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
        # CR fix 2: Idle (0x40) + background mode on at most 3 cores (the trainer's loader threads inherit the mask)
        mask = int(opts["affinity"], 0)
        if bin(mask).count("1") > 3:
            raise SystemExit("--r11-affinity must select at most 3 CPUs")
        k32 = ctypes.windll.kernel32
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        h = k32.GetCurrentProcess()
        k32.SetPriorityClass(h, 0x00100000)  # background mode first: it resets the class to Normal
        k32.SetPriorityClass(h, 0x00000040)  # then Idle (base priority 4, I/O priority stays very low)
        k32.SetProcessAffinityMask(h, mask)
    patterns = [p for p in opts["patterns"].split(";") if p]

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
            self.t_batch = None
            self.has_val = False

        # ---- saving and rotation
        def _save(self, trainer, next_epoch: int, complete: bool, val_loss, tag: str = "") -> str:
            name = f"{tag}epoch={trainer.current_epoch}-step={trainer.global_step}.ckpt"
            path = os.path.join(ckpt_dir, name)
            tmp = path + ".tmp"
            self._pending_meta = {"r11_next_epoch": int(next_epoch), "r11_epoch_complete": bool(complete),
                                  "r11_val_loss": val_loss}
            trainer.save_checkpoint(tmp)
            trainer.flush_checkpoints()
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

        # ---- control, governor, duty cycle
        def on_train_batch_start(self, trainer, batch, batch_idx):
            self.t_batch = time.perf_counter()

        def on_train_batch_end(self, trainer, batch, batch_idx, outputs):
            if opts["policy"] == "share" and opts["share_duty"] < 1.0 and self.t_batch is not None:
                dt = time.perf_counter() - self.t_batch
                time.sleep(dt * (1.0 / max(0.05, opts["share_duty"]) - 1.0))
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
            if True:
                ram, commit = free_gb()
                if ram < opts["min_free_ram_gb"] or commit < opts["min_free_ram_gb"]:
                    reason, code = f"free RAM {ram:.2f} GB / commit {commit:.2f} GB < {opts['min_free_ram_gb']} GB", EXIT_RESOURCE
                elif opts["policy"] == "yield":
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
    log_event(run_dir, "start", argv=train_args, policy=opts["policy"], keep_last=opts["keep_last"])
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
