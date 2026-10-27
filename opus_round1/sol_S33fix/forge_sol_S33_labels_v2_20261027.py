"""S33-1 (v2): label every S33 advice table "approx model" and quote only fastchess-printed gate figures.

usage:
  python -I -B forge_sol_S33_labels_v2_20261027.py render --csv SOL_TABLE.csv --md OUT.md --csv-out OUT.csv
  python -I -B forge_sol_S33_labels_v2_20261027.py check  --gates GATES_DIR DOC.md [DOC.md ...]

render: rebuilds Sol's full plan table (his CSV, numbers unchanged) as markdown with the label in the title, in a
caption directly above the table and in the probability headers; the CSV gets a model_label column.
check: every markdown table must carry 'approx model' in its header row or in the caption line(s) directly above
it, unless the caption says 'fastchess-printed' (a table of real gate figures); every real-gate LLR or
'Elo x +/- y' quoted next to a gate name (G95, G100r, G119, ...) must equal the fastchess-printed RESULT.md value
string. Exit 1 with a problem list otherwise. Standard library only.
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

LABEL = 'approx model'
CAPTION = ('**approx model** — Sol\'s S33 planner: Gaussian online-LLR approximation of the SPRT, modeled trials '
           '(20,000 per cell), not fastchess\'s exact GSPRT and not played games. True Elo is logistic; bounds are nElo.')
GATE_TAGS = {'G95': 'gate95_e12f_vs_h256e12', 'G100r': 'gate100r_e32f003_vs_h256e12', 'G104': 'gate104_e48f006_vs_h256e12',
             'G104c': 'gate104_e48f006_vs_h256e12_confirm', 'G119': 'gate119_e32f003rec_s197_vs_h256e12',
             'G120': 'gate120_e32f003rec_s198_vs_h256e12', 'G120c': 'gate120_e32f003rec_s198_vs_h256e12_confirm'}


# ----------------------------------------------------------------------------------------------- render
def render(csv_path, md_path, csv_out):
    rows = list(csv.DictReader(open(csv_path, encoding='utf-8', newline='')))
    if len(rows) != 630:
        raise ValueError('expected Sol\'s 630-cell table, got %d rows' % len(rows))
    md = ['# S33 full advisory plan table (approx model) — v2 of 2026-10-26, relabelled 2026-10-27', '',
          'Same numbers as Sol\'s `forge_sol_S33_sprt_plan_table_20261026.md` (rendered from his CSV, sha256 in the '
          'job FILES.txt); only the labels are new (QA fix-up S33-1). Modeled trials only, not played games. No observed '
          'gates or concurrency groups pooled.', '', CAPTION, '',
          '|Profile|Conc|True Elo|Protocol|P(H1) approx model|P(H0) approx model|P(cap) approx model|'
          'Mean games approx model|Median games approx model|',
          '|---|---|---:|---|---:|---:|---:|---:|---:|']
    for r in rows:
        md.append('|{p}|{c}|{e:g}|{pr}|{h1:.5f}|{h0:.5f}|{cap:.5f}|{mean:.2f}|{med:.0f}|'.format(
            p=r['profile'], c=r['concurrency'] or 'model', e=float(r['true_logistic_elo']), pr=r['protocol'],
            h1=float(r['mc_H1']), h0=float(r['mc_H0']), cap=float(r['mc_cap']), mean=float(r['mc_mean_games']),
            med=float(r['mc_median_games'])))
    Path(md_path).write_text('\n'.join(md) + '\n', encoding='utf-8', newline='\n')
    fields = ['model_label'] + list(rows[0].keys())
    with open(csv_out, 'w', encoding='utf-8', newline='') as h:
        w = csv.DictWriter(h, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow(dict(r, model_label=LABEL))
    return len(rows)


# ----------------------------------------------------------------------------------------------- check
def tables(text):
    """[(header_line_index, caption_lines)] for every markdown table (header row followed by a |---| row)."""
    lines = text.splitlines()
    out = []
    for i in range(len(lines) - 1):
        if lines[i].lstrip().startswith('|') and re.match(r'^\s*\|\s*:?-{3,}', lines[i + 1]):
            if i > 0 and lines[i - 1].lstrip().startswith('|'):
                continue  # not a header row
            cap, j = [], i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            while j >= 0 and lines[j].strip() and not lines[j].lstrip().startswith('|') and len(cap) < 3:
                cap.insert(0, lines[j])
                j -= 1
            out.append((i, lines[i], cap))
    return out


def fastchess_figures(gates_dir):
    """Printed figures (as strings, exactly as fastchess/RESULT.md prints them) for the known gates."""
    figs = {}
    for gate, tag in GATE_TAGS.items():
        p = Path(gates_dir) / tag / 'RESULT.md'
        if not p.is_file():
            continue
        t = p.read_text(encoding='utf-8-sig')
        e = re.search(r'Elo: (-?[0-9.]+) \+/- ([0-9.]+)\s+nElo: (-?[0-9.]+) \+/- ([0-9.]+)', t)
        figs[gate] = {'llr': re.search(r'LLR: (-?[0-9.]+)\s+bounds', t).group(1), 'elo': e.group(1), 'elo_err': e.group(2),
                      'nelo': e.group(3), 'nelo_err': e.group(4)}
    return figs


GATE_RE = re.compile(r'\b(G(?:95|100r|104c|104|119|120c|120))(?![\w-])')
LLR_RE = re.compile(r'\bLLR\s*(?:=|:)?\s*(-?\d+(?:\.\d+)?)')
ELO_RE = re.compile(r'(?<![nN])\bElo\s*(?:=|:)?\s*([+-]?\d+(?:\.\d+)?)\s*(?:\+/-|±)\s*(\d+(?:\.\d+)?)')


def check_text(text, figs, name='doc'):
    problems = []
    for i, header, cap in tables(text):
        caption = ' '.join(cap).lower()
        if LABEL in header.lower() or LABEL in caption or 'fastchess-printed' in caption:
            continue
        problems.append('%s:%d table without "%s" label: %s' % (name, i + 1, LABEL, header.strip()[:80]))
    for n, line in enumerate(text.splitlines(), 1):
        # a gate quote runs from the gate name to the next gate name on the same line
        marks = list(GATE_RE.finditer(line))
        for k, m in enumerate(marks):
            seg = line[m.end(): marks[k + 1].start() if k + 1 < len(marks) else len(line)]
            gate = m.group(1)
            if gate not in figs:
                continue
            for v in LLR_RE.finditer(seg):
                if v.group(1) != figs[gate]['llr']:
                    problems.append('%s:%d %s LLR %s is not the fastchess-printed %s' % (name, n, gate, v.group(1), figs[gate]['llr']))
            for v in ELO_RE.finditer(seg):
                if (v.group(1).lstrip('+'), v.group(2)) != (figs[gate]['elo'], figs[gate]['elo_err']):
                    problems.append('%s:%d %s Elo %s +/- %s is not the fastchess-printed %s +/- %s' % (
                        name, n, gate, v.group(1), v.group(2), figs[gate]['elo'], figs[gate]['elo_err']))
    return problems


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('render')
    r.add_argument('--csv', required=True)
    r.add_argument('--md', required=True)
    r.add_argument('--csv-out', required=True)
    c = sub.add_parser('check')
    c.add_argument('--gates', required=True)
    c.add_argument('docs', nargs='+')
    a = p.parse_args(argv)
    if a.cmd == 'render':
        print('rendered', render(a.csv, a.md, a.csv_out), 'rows')
        return 0
    figs = fastchess_figures(a.gates)
    problems = []
    for d in a.docs:
        problems += check_text(Path(d).read_text(encoding='utf-8'), figs, Path(d).name)
    print(json.dumps({'status': 'PASS' if not problems else 'FAIL', 'docs': len(a.docs), 'gates_known': sorted(figs),
                      'problems': problems}, indent=1))
    return 0 if not problems else 1


if __name__ == '__main__':
    raise SystemExit(main())
