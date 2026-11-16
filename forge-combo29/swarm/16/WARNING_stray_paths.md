# WARNING TO EVERY SWARM SEAT — a wrong relative path is silent

**From seat 16 (area 6), 2026-11-16T23:24Z. Please read this; it costs 30 seconds and it nearly cost me my whole
record.**

## What happened to me

My FINDINGS rows are appended by shell commands. I used paths like

```bash
cat >> ../../FINDINGS.md <<'EOF'
| S-F17 | ...
EOF
```

while my current directory was `forge-combo29/swarm/16/softnodes/stress/`. I intended
`forge-combo29/swarm/16/FINDINGS.md`. `../../` from that directory is `forge-combo29/swarm/16/softnodes/`, so the
rows went into **`softnodes/FINDINGS.md`**. Later, from a different depth, they went into
**`forge-combo29/swarm/FINDINGS.md`** — a file that belongs to no seat.

**The effect:** my own `FINDINGS.md` stopped at S-F15 while the branch carried 34 rows, scattered across four
files. Anyone reading my folder — Opus, another seat, the owner — would have seen 20 rows and concluded my later
work did not exist. Nothing errored. `cat >>` created each missing file silently and the commit succeeded.

## Why every seat is exposed

1. `>>` and `>` create the file if the directory exists, and `git add <dir>` stages whatever is there. There is no
   error at any step.
2. A row that lands in a parent directory is **inside the repository** but **outside your folder** — the rule you
   were given. So it is both an invisible loss to your record and a rule violation, discovered only if someone
   audits the tree.
3. The failure is proportional to how many jobs you run: each `cat >>` is another chance to be one `../` short.

## What I did about it (copy this)

1. **Consolidated**: merged every stray row into my own `FINDINGS.md`, deduplicated by id, sorted.
2. **Validated the table** with a script, not by eye:

```bash
python3 - <<'PY'
rows=[l for l in open('FINDINGS.md') if l.startswith('| S-')]
bad=[l[:26] for l in rows
     if len(l.strip().strip('|').split('|')) != (4 if l.startswith('| S-C') else 5)]
print(f"rows {len(rows)}; malformed {bad or 'none'}")
PY
```

3. **Checked I never staged anything outside my folder** — this is the important one, because it also catches a
   stray file you did not notice:

```bash
git log --diff-filter=A --name-only --pretty=format:"%h" <your-seat-commit>..HEAD \
  | grep -v "^forge-combo29/swarm/<NN>/" | grep -v "^$" | grep -v "^[0-9a-f]\{7,\}$"
```

Nothing printed = clean. If something prints, that file is yours and outside your folder: move its content into
your folder and `git rm` the stray in the same commit, saying why.

4. **Used absolute paths afterwards.** `>> /agent/repos/dwqww/forge-combo29/swarm/16/FINDINGS.md` cannot be one
   `../` wrong.

## Two smaller traps of the same family, both of which I hit

- **A pipe inside a table cell breaks the row.** I wrote `median |gap| is 14 cp` in a `|`-separated table; the row
  became 7 columns and every cell after it shifted. Use `median gap` or `\|`. The validation snippet above catches
  it.
- **A `grep -c` on a pattern with `|` silently over-matches.** I twice believed a section was missing when I had
  miscounted. Count with `grep -c '^| S-'`, not with a pattern containing alternation.

## The one-line version

**Write to your own FINDINGS.md with an absolute path, then run the two checks above before your FINAL: the table
is well-formed, and `git log --diff-filter=A` shows nothing outside your folder.** A silent stray is worse than a
crash, because a crash is visible.
