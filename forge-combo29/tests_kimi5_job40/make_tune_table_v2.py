#!/usr/bin/env python3
"""kimi5 job 40 step 4: build tune_table_v2.tsv from job 37's tune_list.tsv and the
capped runs of Steps 2 and 3. Recomputes the exploded counts from the raw rows/caps
files and prints how many rows files it read. Run from forge-combo29.
Rule (file 40): for the options of Step 3, min and max = the farthest value run on
each side with 0 exploded positions on O AND G, or the spec's bound where that is
nearer to the default; source = "measured" or "spec". A side whose only run exploded
falls back to the default (no 0-exploded value exists on that side); the exploding
values are listed below the table. The CheckExtPlies note line of tune_list.tsv
becomes its measured data row here (its G cell at 2 is job 40's Step 2).
"""
import os

J = "tests_kimi5_job40"
STEP3_OPTIONS = ["DoubleExtLimit", "DoubleExtPlies", "SingularExtPlies", "SingularTtCutExt",
                 "SingularCutNodeExt", "CheckExtPlies", "DoubleExtMargin"]

def read_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                p = line.split()
                rows.append((int(p[0]), int(p[1]), int(p[2]), p[3]))
    return rows

def read_caps(path):
    caps = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                n, c = line.split()
                caps[int(n)] = int(c)
    return caps

def exploded_count(tag, set_, folder):
    run = read_rows(os.path.join(J, folder, f"{tag}.rows"))
    caps = read_caps(os.path.join(J, folder, f"{tag}.caps"))
    return sum(1 for n, d, nodes, bm in run if d < 12 or nodes >= caps[n]), 2

files_read = 0
# exploded[(option, value)][set] = count
exploded = {}
with open(os.path.join(J, "runlist.tsv")) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        name, value, set_ = line.split("\t")
        tag = f"s3_{name}_{value.replace('-', 'm')}_{set_}"
        cnt, nread = exploded_count(tag, set_, "s3")
        exploded.setdefault((name, value), {})[set_] = cnt
        files_read += nread
# Step 2's cell: CheckExtPlies 2 on G lives in s2/
cnt, nread = exploded_count("s2_CheckExtPlies_2_G", "G", "s2")
exploded.setdefault(("CheckExtPlies", "2"), {})["G"] = cnt
files_read += nread
# spec/tune_list defaults and bounds for the 7 options
specs = {}
with open("kimi5/job37/tune_list.tsv") as f:
    header = f.readline()
    tune_rows = []
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        tune_rows.append(line)
        p = line.split("\t")
        if len(p) == 5 and p[0] in STEP3_OPTIONS:
            specs[p[0]] = (p[1], p[2], p[3], p[4])  # default, min, max, step
files_read += 2  # tune_list.tsv + runlist.tsv
# CheckExtPlies has no data row in tune_list.tsv (only the note line about the
# unfinished cell); its bounds come from options_spec_v2.tsv (default 1, min 0, max 2, step 1).
if "CheckExtPlies" not in specs:
    specs["CheckExtPlies"] = ("1", "0", "2", "1")

def zero_both(name, value):
    d = exploded.get((name, value), {})
    return d.get("O", None) == 0 and d.get("G", None) == 0

# values run per option, below/above default (from the exploded map; O-only cells count for O,
# but a bound needs 0 on O AND G, so an O-only run cannot set a bound alone)
ran = {}
for (name, value) in exploded:
    ran.setdefault(name, []).append(int(value))

out = ["name\tdefault\tmin\tmax\tstep\tsource"]
below_table = []
for line in tune_rows:
    p = line.split("\t")
    name = p[0]
    if len(p) == 5 and name in STEP3_OPTIONS:
        default, smin, smax, step = specs[name]
        d = int(default)
        below = sorted(v for v in ran.get(name, []) if v < d)   # ascending: farthest from default FIRST
        above = sorted(v for v in ran.get(name, []) if v > d)
        cand_min = next((v for v in below if zero_both(name, str(v))), None)
        cand_max = next((v for v in reversed(above) if zero_both(name, str(v))), None)
        # rule: the farthest value run on the side with 0 exploded on O AND G; the spec's
        # bound where that is nearer to the default; a side with no run takes the spec
        # bound; a side whose runs all exploded falls back to the default itself.
        if cand_min is not None:
            new_min = int(smin) if abs(int(smin) - d) < abs(cand_min - d) else cand_min
        else:
            new_min = int(smin) if not below else d
        if cand_max is not None:
            new_max = int(smax) if abs(int(smax) - d) < abs(cand_max - d) else cand_max
        else:
            new_max = int(smax) if not above else d
        out.append(f"{name}\t{default}\t{new_min}\t{new_max}\t{step}\tmeasured")
    elif len(p) == 5:
        out.append(f"{line}\tspec")
    elif p[0] in STEP3_OPTIONS:
        # the CheckExtPlies note line: emit its measured data row in its place
        default, smin, smax, step = specs[p[0]]
        d = int(default)
        below = sorted(v for v in ran.get(p[0], []) if v < d)
        above = sorted(v for v in ran.get(p[0], []) if v > d)
        cand_min = next((v for v in below if zero_both(p[0], str(v))), None)
        cand_max = next((v for v in reversed(above) if zero_both(p[0], str(v))), None)
        if cand_min is not None:
            new_min = int(smin) if abs(int(smin) - d) < abs(cand_min - d) else cand_min
        else:
            new_min = int(smin) if not below else d
        if cand_max is not None:
            new_max = int(smax) if abs(int(smax) - d) < abs(cand_max - d) else cand_max
        else:
            new_max = int(smax) if not above else d
        out.append(f"{p[0]}\t{default}\t{new_min}\t{new_max}\t{step}\tmeasured")
out.append("")
out.append("# values of Step 3 that exploded at least one position (count on O, count on G):")
for (name, value) in sorted(exploded, key=lambda kv: (kv[0], int(kv[1]))):
    d = exploded[(name, value)]
    o, g = d.get("O", 0), d.get("G", 0)
    if o or g:
        out.append(f"# {name} {value}: O {o}, G {g}")
        below_table.append((name, value, o, g))

with open(os.path.join(J, "tune_table_v2.tsv"), "w") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
print(f"rows_files_read: {files_read}")
