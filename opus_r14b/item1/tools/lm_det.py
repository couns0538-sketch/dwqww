"""lm_det.py - Opus R14-B: run the trainer's train.py with torch's deterministic algorithms switched on (CPU loss
match). Used as the script that opus_tools/guard_exec.py runs: `guard_exec.py <this file> <train.py args...>`, with
the working directory = the trainer copy. Ops without a deterministic implementation raise instead of varying."""

import os
import runpy
import sys

import torch

torch.use_deterministic_algorithms(True)
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
sys.argv = ["train.py"] + sys.argv[1:]
runpy.run_path(os.path.join(os.getcwd(), "train.py"), run_name="__main__")
