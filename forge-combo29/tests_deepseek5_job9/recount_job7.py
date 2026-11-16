# The recount of NOTES_deepseek5's corrected lines: counts depth/bestmove columns of
# /tmp/glmflash/ds5_job7_b/clock_raw.txt against OFF per position. See job 9 Part 0.
import json, collections
rows = []
for l in open("/tmp/glmflash/ds5_job7_b/clock_raw.txt"):
    p = l.rstrip("\n").split("|")
    if len(p) < 11: continue
    rows.append(dict(setting=p[0], line=p[1], pos=p[2], best=p[3],
                     depth=int(p[4]) if p[4] not in ("None","") else -1, wall=float(p[6])))
out = {}
for line in ("L1","L2","L3"):
    sub = {s: [r for r in rows if r["setting"]==s and r["line"]==line] for s in ("OFF","OFF2","FI","NS")}
    out[line] = {s: {"lower_depth": sum(1 for a,b in zip(sub["OFF"],sub[s]) if b["depth"] < a["depth"]),
                     "bestmove_diff": sum(1 for a,b in zip(sub["OFF"],sub[s]) if a["best"] != b["best"])} for s in ("FI","NS","OFF2")}
print(json.dumps(out, indent=1))
