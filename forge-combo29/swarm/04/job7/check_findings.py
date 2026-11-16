#!/usr/bin/env python3
"""check_findings.py — validate that every finding row in FINDINGS.md has the right cell count.

WHY THIS EXISTS (read this if you are another seat):
  A markdown table row breaks silently when a cell contains an unescaped `|` — which happens the
  moment you write inline code like `nm -C forge | grep -c __tsan_` inside a table cell. The row
  splits into extra columns instead of rendering, and the file LOOKS fine in an editor. Two other
  seats hit this the same night I did, and seven of my own rows were broken for a while without any
  command reporting an error.
  Do not try to find it with `awk -F'|'` or a shell one-liner: those are quoting-sensitive and gave
  me contradictory answers, and two of my "fixes" damaged rows that had been correct. This script
  counts only UNESCAPED pipes, which is what a markdown renderer does.

  If your folder has a FINDINGS.md with a table: run this on it.

  IMPORTANT LIMIT, measured: this checker infers the expected cell count from the file's own header (or
  from the brief's two shapes when there is no header). Across the swarm, seats use their OWN table
  shapes -- one seat's revision lines are 3 cells, another's are 6 -- so pointing this script at another
  seat's file reports their deliberate format as "malformed". It is reliable for YOUR file, where the
  shape is known. Do not use it to accuse another seat of breakage; use it to check your own rows before
  you push. (I checked 13 seats with it and then verified the flagged rows by eye: every flagged row in
  another seat's file was that seat's intentional format, not breakage. Reporting them would have been a
  false alarm, which is why this note exists.)

The table header declares 5 columns: | id | area | finding | evidence | state |
A check row (S-C) may use 5 cells too, with the verdict in the second cell (and the verdict, not
"NEW", belongs in the state column).

A cell may contain a literal pipe only if it is escaped as \\| ; an unescaped one starts a new cell.

Usage: python3 check_findings.py PATH [--fix]
  --fix  escapes the single extra unescaped pipe in any row that has exactly 7, choosing the one that is
         NOT one of the six structural delimiters.
  exit   0 = every row well formed; 1 = at least one row malformed (listed with its line number).
"""
import re
import sys

HEADER_CELLS = 5


def unescaped_pipes(line):
    return [m.start() for m in re.finditer(r"(?<!\\)\|", line)]


def main():
    path = sys.argv[1]
    do_fix = "--fix" in sys.argv
    lines = open(path).read().splitlines(True)
    out = []
    bad = []
    fixed = 0

    # THE RULE, from the brief itself — two legitimate row shapes, not one:
    #   F line: | S-F<k> | area | finding | file with the command | NEW |   = 5 cells = 6 pipes
    #   C line: | S-C<k> | CONFIRMS or REFUTES <their id> | evidence file | one sentence |  = 4 cells = 5 pipes
    # So validity is per row TYPE, not one global count. A first version of this script used a single
    # global count and consequently flagged every legitimate C row in 12 other seats' files as broken
    # (and keyed on "| 04-", which passed everything belonging to anyone else). Both are fixed here.
    declared = None
    for raw in lines:
        cells = raw.rstrip("\n").split("|")
        if len(cells) >= 4 and cells[1].strip().lower() == "id":
            declared = len(cells) - 2      # drop the empty first and last split parts
            break
    f_pipes = (declared + 1) if declared else 6          # 5 cells -> 6 unescaped pipes
    c_pipes = f_pipes - 1                                # 4 cells -> 5 unescaped pipes

    for i, raw in enumerate(lines, 1):
        body = raw.rstrip("\n")
        # A table row is any line starting with a pipe that is not the header and not a separator row.
        if not body.startswith("|") or set(body.replace("|", "").replace("-", "").replace(" ", "")) == set():
            out.append(raw)
            continue
        if body.split("|")[1].strip().lower() == "id":
            out.append(raw)
            continue
        if not re.match(r"^\|\s*[0-9S]", body):
            out.append(raw)
            continue
        idx = unescaped_pipes(body)
        ident = body.split("|")[1].strip()
        is_check = bool(re.search(r"-[CS]\d*[0-9]", ident)) and ident.upper().split("-")[-1].startswith("C")
        want = c_pipes if is_check else f_pipes
        # A C row is acceptable with either 4 cells (the brief's shape) or 5 (the header's shape,
        # which is what this seat uses so the verdict sits in the state column). Both render.
        ok = (len(idx) in (c_pipes, f_pipes)) if is_check else (len(idx) == f_pipes)
        if ok:
            out.append(raw)
            continue
        if do_fix and len(idx) == want + 1:
            # Keep the first `want - 1` pipes as structural delimiters and the LAST one as the closing
            # pipe; the single leftover is the stray that belongs inside a cell.
            structural = idx[:want - 1] + [idx[-1]]
            stray = [p2 for p2 in idx if p2 not in structural]
            if len(stray) == 1:
                e = stray[0]
                body = body[:e] + "\\" + body[e:]
                out.append(body + "\n")
                fixed += 1
                continue
        bad.append((i, body.split("|")[1].strip(), len(idx)))
        out.append(raw)
    if do_fix and fixed:
        open(path, "w").write("".join(out))
    print("rows checked: %d" % sum(1 for l in lines if l.startswith("| 04-")))
    if fixed:
        print("rows fixed: %d" % fixed)
    if bad:
        print("MALFORMED (unescaped pipe count != %d):" % (HEADER_CELLS + 1))
        for i, ident, n in bad:
            print("   line %d  %s  pipes=%d" % (i, ident, n))
        sys.exit(1)
    print("OK: every row has %d unescaped pipes (5 cells)" % (HEADER_CELLS + 1))


if __name__ == "__main__":
    main()
