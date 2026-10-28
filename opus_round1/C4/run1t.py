"""Runs a trainer script with torch limited to one thread (smoke runs on the shared PC).
usage: python run1t.py <trainer.py> [trainer args...]"""
import runpy, sys
import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
script = sys.argv[1]
sys.argv = [script] + sys.argv[2:]
runpy.run_path(script, run_name="__main__")
