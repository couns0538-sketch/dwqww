#!/usr/bin/env python3
"""S02 AREA 2 job 3 — build the report's table from the committed records only.

usage: summarise.py <outdir>
Refuses to print if the record set or the option list is missing/empty, and refuses if a case is missing a
field it needs — a partial set must not read as "0 faults" (the failure mode seat 19 warned about).
"""
import collections
import json
import os
import sys

out = sys.argv[1] if len(sys.argv) > 1 else "out"
rpath = os.path.join(out, "results.jsonl")
opath = os.path.join(out, "options.json")
for p in (rpath, opath):
    if not os.path.exists(p):
        sys.exit("FAIL: %s missing; refusing to print a table" % p)
rs = [json.loads(l) for l in open(rpath)]
opts = json.load(open(opath))
if not rs:
    sys.exit("FAIL: no cases recorded; an empty set would read as 0 faults")
if not opts:
    sys.exit("FAIL: no options parsed from the engine's uci answer")
for r in rs:
    for k in ("option", "type", "label", "value", "during", "answered", "legal", "crash",
              "answer_lines", "invalid_line", "san"):
        if k not in r:
            sys.exit("FAIL: case %r has no %r" % (r.get("option"), k))

print("cases %d over %d options (spin %d, check %d, string %d, button %d)" % (
    len(rs), len(opts),
    sum(1 for o in opts if o["type"] == "spin"), sum(1 for o in opts if o["type"] == "check"),
    sum(1 for o in opts if o["type"] == "string"), sum(1 for o in opts if o["type"] == "button")))
print()
print("| quantity | value |")
print("|---|---|")
print("| cases run | %d |" % len(rs))
print("| cases between searches | %d |" % sum(1 for r in rs if not r["during"]))
print("| cases during a search | %d |" % sum(1 for r in rs if r["during"]))
print("| crashes | %d |" % sum(r["crash"] for r in rs))
print("| sanitizer lines | %d |" % sum(1 for r in rs if r["san"]))
print("| cases where the next search printed no bestmove | %d |" % sum(1 for r in rs if not r["answered"]))
print("| cases where the next search's bestmove was illegal | %d |"
      % sum(1 for r in rs if r["legal"] is False))
print("| spin out-of-range (min-1 / max+1) cases | %d |"
      % sum(1 for r in rs if r["type"] == "spin" and r["label"] in ("min-1", "max+1") and not r["during"]))
print("| ... of those WITHOUT the `invalid value` line | %d |"
      % sum(1 for r in rs if r["type"] == "spin" and r["label"] in ("min-1", "max+1")
            and not r["during"] and r["invalid_line"] is None))
print("| spin given the word `banana` | %d |"
      % sum(1 for r in rs if r["type"] == "spin" and r["value"] == "banana" and not r["during"]))
print("| ... of those silently accepted | %d |"
      % sum(1 for r in rs if r["type"] == "spin" and r["value"] == "banana" and not r["during"]
            and r["invalid_line"] is None))
print("| check given the word `banana` | %d |"
      % sum(1 for r in rs if r["type"] == "check" and r["value"] == "banana" and not r["during"]))
print("| ... of those silently accepted | %d |"
      % sum(1 for r in rs if r["type"] == "check" and r["value"] == "banana" and not r["during"]
            and r["invalid_line"] is None))
print("| option sent with NO value | %d |" % sum(1 for r in rs if r["label"] == "none" and not r["during"]))
print("| ... of those WITHOUT an `invalid value` line | %d |"
      % sum(1 for r in rs if r["label"] == "none" and not r["during"] and r["invalid_line"] is None))
print()
print("### the no-value cases that printed nothing at all (by type)")
for r in rs:
    if r["label"] == "none" and not r["during"] and r["invalid_line"] is None:
        print("- %s (%s) answered %r" % (r["option"], r["type"], r["answer_lines"]))
print()
print("### the button option, every value sent")
for r in rs:
    if r["type"] == "button":
        print("- value %-8r during=%-5s answered=%s invalid_line=%r answer=%r"
              % (r["value"], r["during"], r["answered"], r["invalid_line"], r["answer_lines"]))
print()
print("### string options, every value sent")
for r in rs:
    if r["type"] == "string" and not r["during"]:
        print("- %-12s %-6s value %-10r -> %r answered=%s"
              % (r["option"], r["label"], r["value"], r["answer_lines"], r["answered"]))
