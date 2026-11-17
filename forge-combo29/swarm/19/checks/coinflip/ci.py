import subprocess, os, re, math, statistics as st
# recompute per-position ratios is expensive; instead use the RESULT.txt summary we have plus a paired CI
# requires raw. Re-run cheaply? No - we stored only aggregates. Let's compute CI from stored quartiles is invalid.
# So: recompute with a short run storing per-position values.
print("need per-position data - rerunning with storage")
