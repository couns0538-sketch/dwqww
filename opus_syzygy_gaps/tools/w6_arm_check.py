#!/usr/bin/env python3
"""w6_arm_check.py <gaps patch> <tree> [<tree> ...] : where the job's switches land next to the trial_w6 speed switches.

A hunk that applies cleanly can still land in one arm of a speed conditional, so that the other arm (the one the
trial_w6 build compiles) never gets it. This tool reads the conditional stack of each source file in the tree:
  1. every changed line of the gaps patch must be found in the tree, and none may sit inside a speed conditional;
  2. every speed conditional is printed when it contains code the gaps patch changes in the other arm's text
     (same statement with another spelling is not found by line 1, so the arms near a hunk are listed for reading).
Exit 0 = no changed line inside a speed conditional and all changed lines found; 1 = otherwise. Standard library only.
"""
import os
import re
import sys

SPEED = re.compile(r"FORGE_(SPD_|SEARCH_SPEED2)")
OPEN = re.compile(r"^\s*#\s*(if|ifdef|ifndef)\b(.*)$")
ELSE = re.compile(r"^\s*#\s*(else|elif)\b(.*)$")
END = re.compile(r"^\s*#\s*endif\b")
NEAR = 12


def changed_lines(patch):
    """Added lines of the patch by file, in order; removed lines are returned apart."""
    added, removed, cur = {}, {}, None
    with open(patch, encoding="utf-8", newline="") as f:
        for raw in f:
            s = raw.rstrip("\r\n")
            if s.startswith("+++ "):
                cur = s[4:].split("\t")[0]
                cur = cur[2:] if cur.startswith("b/") else cur
                added.setdefault(cur, [])
                removed.setdefault(cur, [])
            elif s.startswith("--- "):
                continue
            elif cur and s.startswith("+"):
                added[cur].append(s[1:])
            elif cur and s.startswith("-"):
                removed[cur].append(s[1:])
    return added, removed


def speed_stack_per_line(lines):
    """For each line, the list of speed conditionals open at it, as (line number of the #if, text, arm)."""
    out, stack = [], []
    for i, s in enumerate(lines, 1):
        m = OPEN.match(s)
        if m:
            stack.append([i, s.strip(), 0])
            out.append([])
            continue
        if ELSE.match(s) and stack:
            stack[-1][2] += 1
            out.append([])
            continue
        if END.match(s) and stack:
            stack.pop()
            out.append([])
            continue
        out.append([tuple(c) for c in stack if SPEED.search(c[1])])
    return out


def check_tree(tree, added):
    bad = 0
    for rel, want in sorted(added.items()):
        path = os.path.join(tree, rel)
        with open(path, encoding="utf-8", newline="") as f:
            lines = [x.rstrip("\r\n") for x in f]
        stacks = speed_stack_per_line(lines)
        pos = 0
        arms_near = {}
        placed = 0
        missing = 0
        for w in want:
            at = None
            for k in range(pos, len(lines)):
                if lines[k] == w:
                    at = k
                    break
            if at is None:
                print(f"  MISSING {rel}: {w[:110]}")
                missing += 1
                continue
            pos = at + 1
            placed += 1
            if stacks[at] and not OPEN.match(w) and not ELSE.match(w) and not END.match(w):
                print(f"  INSIDE SPEED ARM {rel}:{at + 1}: {stacks[at][-1][1]} arm {stacks[at][-1][2]}: {w[:90]}")
                bad += 1
            lo, hi = max(0, at - NEAR), min(len(lines), at + NEAR + 1)
            for k in range(lo, hi):
                for c in stacks[k]:
                    arms_near[c[0]] = c[1]
        bad += missing
        print(f"  {rel}: changed lines placed {placed} of {len(want)}, missing {missing}, speed conditionals within {NEAR} lines: {len(arms_near)}")
        for n in sorted(arms_near):
            print(f"    near: line {n}: {arms_near[n]}")
    return bad


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    added, _removed = changed_lines(sys.argv[1])
    total = 0
    for tree in sys.argv[2:]:
        print(f"tree {tree}")
        total += check_tree(tree, added)
    print(f"w6_arm_check: {'CLEAN' if total == 0 else 'BAD ' + str(total)}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
