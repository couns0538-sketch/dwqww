"""record_incomplete.py - record cold runs that were stopped before their end (owner's instruction, 2026-11-10 16:56).

For every out\\id\\<NAME>\\cold_*_all*.tsv.part: count the complete rows written so far, compare them with the
lock's rows of the same indices, rename the partial file to *.incomplete.tsv, and append one line to the
item's QUALIFY.log:

  QUAL <NAME> <stage>: INCOMPLETE <n> of 12000 rows written when the run was stopped; <k> of them equal the
  lock's rows, <d> differ; partial rows <file> sha256 <...> [<time> Vienna]

An INCOMPLETE line is not a PASS: the rows that were not searched are not covered. Where two partial files
exist for one stage (a run was started twice into different files), the longer one is recorded and the other
is named. Nothing is run here.

usage: record_incomplete.py OUT_DIR "<why and when stopped>"
"""
import hashlib
import os
import sys
import time

STAGE = {"cold_on": "cold net on", "cold_off": "cold net off", "cold_v2_on": "engine, verify build, cold net on"}
LOCK = {"cold_on": "cold_on_all.tsv", "cold_off": "cold_off_all.tsv", "cold_v2_on": "cold_on_all.tsv"}


def now_vienna():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 3600)) + " Vienna"


def complete_rows(path):
    with open(path, "rb") as f:
        data = f.read()
    end = data.rfind(b"\n")
    return [x.rstrip("\r") for x in data[:end + 1].decode("utf-8", "replace").split("\n")[:-1]] if end >= 0 else []


def main():
    out, why = sys.argv[1], sys.argv[2]
    idd = os.path.join(out, "id")
    for name in sorted(os.listdir(idd)):
        d = os.path.join(idd, name)
        if not os.path.isdir(d) or name == "lock":
            continue
        found = {}
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".tsv.part"):
                continue
            key = fn.split("_all")[0]                      # cold_on, cold_off, cold_v2_on
            if key in STAGE:
                found.setdefault(key, []).append(fn)
        for key, files in found.items():
            lock_rows = complete_rows(os.path.join(idd, "lock", LOCK[key]))
            best = None
            for fn in files:
                rows = complete_rows(os.path.join(d, fn))
                if best is None or len(rows) > len(best[1]):
                    best = (fn, rows)
            fn, rows = best
            same = sum(1 for a, b in zip(rows, lock_rows) if a == b)
            diff = len(rows) - same
            new_names = []
            for old in files:
                new = old[:-len(".tsv.part")] + ".incomplete.tsv"
                os.replace(os.path.join(d, old), os.path.join(d, new))
                new_names.append(new)
            kept = fn[:-len(".tsv.part")] + ".incomplete.tsv"
            with open(os.path.join(d, kept), "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            other = [x for x in new_names if x != kept]
            line = (f"QUAL {name} {STAGE[key]}: INCOMPLETE {len(rows)} of {len(lock_rows)} rows written when the run was "
                    f"stopped ({why}); {same} of them equal the lock's rows, {diff} differ; partial rows {kept} sha256 {sha}"
                    + (f"; a second partial file of the same stage: {', '.join(other)}" if other else "")
                    + f" [{now_vienna()}]")
            with open(os.path.join(d, "QUALIFY.log"), "a", encoding="ascii", errors="replace", newline="\r\n") as f:
                f.write(line + "\n")
            print(line[:200], flush=True)


if __name__ == "__main__":
    main()
