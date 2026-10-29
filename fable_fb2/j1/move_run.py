"""Continue the J1 training in a new run directory and mark the old one as stopped (FB2-J1 operational fix).
usage: move_run.py <old run dir> <new run dir>
Copies ckpt.pt (with a cleared stop_reason), status.json and best.fnn3 to the new directory; writes a stop_reason
into the old directory's ckpt.pt and status.json so that any driver still pointing at it exits by itself
(the trainer prints "nothing to do" and the driver sees the stop reason)."""
import json
import os
import shutil
import sys

import torch

old, new = sys.argv[1], sys.argv[2]
os.makedirs(new, exist_ok=True)
ck = torch.load(os.path.join(old, "ckpt.pt"), map_location="cpu", weights_only=False)
reason = f"moved: the run continues in {new} (an old driver kept relaunching this directory)"
ck["train_state"]["stop_reason"] = None
torch.save(ck, os.path.join(new, "ckpt.pt.tmp"))
os.replace(os.path.join(new, "ckpt.pt.tmp"), os.path.join(new, "ckpt.pt"))
ck["train_state"]["stop_reason"] = reason
torch.save(ck, os.path.join(old, "ckpt.pt.tmp"))
os.replace(os.path.join(old, "ckpt.pt.tmp"), os.path.join(old, "ckpt.pt"))
status = json.load(open(os.path.join(old, "status.json")))
status_new = dict(status)
status_new["stop_reason"] = None
status_new["out"] = new
with open(os.path.join(new, "status.json"), "w", newline="\n") as f:
    json.dump(status_new, f, indent=1, sort_keys=True)
status["stop_reason"] = reason
with open(os.path.join(old, "status.json.tmp"), "w", newline="\n") as f:
    json.dump(status, f, indent=1, sort_keys=True)
os.replace(os.path.join(old, "status.json.tmp"), os.path.join(old, "status.json"))
if os.path.exists(os.path.join(old, "best.fnn3")):
    shutil.copyfile(os.path.join(old, "best.fnn3"), os.path.join(new, "best.fnn3"))
print(f"moved: step {ck['train_state']['step']} seen {ck['train_state']['seen']} checkpoints {len(ck['train_state']['checkpoints'])} -> {new}; old dir marked stopped")
