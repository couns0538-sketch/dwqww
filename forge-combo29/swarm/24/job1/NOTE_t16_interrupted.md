## t16 was killed by my own command — this is the record

At 2026-11-16T21:52:21Z I ran `pkill -f "build-tsan/forge"` to stop my repro_pos90.py experiment, and that pattern
also matched the engine process of the in-flight Threads-16 run of job 1. The t16 run had completed 61 of 100
positions. Its files are kept as t16.interrupted.* (results/raw/meta/summary/run.log) and the run is RE-STARTED
from position 0 into clean t16.* files. Nothing from the interrupted run is used in the report; its 61 rows are
kept only so the interruption is visible rather than hidden.

This is my error, not an engine fault and not a sanitizer finding.
