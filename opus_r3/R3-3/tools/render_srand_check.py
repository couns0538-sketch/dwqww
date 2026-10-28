"""Render SRAND_CHECK.md for R3-3 (read-only on its inputs).

Usage: python -I -B render_srand_check.py <workdir> <outdir>
Inputs: scan/fs_scan.json, scan/git_scan.json, scan/summary_all.json, scan/srands.json, scan/cands_map.json,
        scan/refs.txt, pc_copies/forge_gates.json, pc_copies/forge_queue_state.json, pc_copies/FORGE_RESULTS.csv
"""
import csv
import json
import os
import re
import sys

W, OUT = sys.argv[1], sys.argv[2]


def j(p):
    return json.load(open(os.path.join(W, p), encoding='utf-8'))


fs = j('scan/fs_scan.json')
gs = j('scan/git_scan.json')
summ = j('scan/summary_all.json')
ch = j('scan/srands.json')
cmap = j('scan/cands_map.json')
refs = [r.strip() for r in open(os.path.join(W, 'scan/refs.txt')) if r.strip()]
raw = open(os.path.join(W, 'pc_copies/forge_gates.json'), 'rb').read()
man = json.loads(raw[3:] if raw.startswith(b'\xef\xbb\xbf') else raw)
man_srands = sorted({int(g['srand']) for g in man['gates'] if g.get('srand') is not None})
state = json.loads(open(os.path.join(W, 'pc_copies/forge_queue_state.json'), 'rb').read().decode('utf-8-sig'))
csv_srands = sorted({int(r['srand']) for r in csv.DictReader(open(os.path.join(W, 'pc_copies/FORGE_RESULTS.csv'), encoding='utf-8-sig')) if (r.get('srand') or '').isdigit()})
qlog = open(os.path.join(W, 'pc_copies/forge_queue.log'), 'rb').read().decode('latin-1')
qlog_srands = sorted({int(x) for x in re.findall(r'srand (\d+)', qlog)})
TEST_PLAN = [1254856699, 869014820, 958591904, 507544535, 1065932896, 881917307, 885637590, 2115600525, 1162618901,
             1894620847, 1325124880, 739447198, 1352390606, 2139766817, 1319449387, 610323748, 113016036, 817455375]
used_all = set(summ['srand_context_values']) | set(summ['seed_only_values'])
for v in TEST_PLAN + man_srands + csv_srands + qlog_srands:
    assert v in used_all, v
chosen = ch['chosen_srand']


def wrap(vals, per=10):
    out = []
    for i in range(0, len(vals), per):
        out.append(', '.join(str(v) for v in vals[i:i + per]))
    return out


L = []
P = L.append
P('# R3-3 srand check')
P('')
P('Every srand in GATE_PROPOSALS.md is new: it is not among the srands or seeds used or reserved in the searched paths '
  '(section 2: every PC gate, queue and planning location, all agents\' scratch, every git branch and Sol\'s commit), '
  'and its decimal string does not occur anywhere in the scanned text (a stricter test than "not a known srand"). '
  'Everything was read-only; PC files were read in place or through copies in scratch.')
P('')
P('## 1. How the values were chosen')
P('')
P('- Candidates: `value(id, k) = 300000000 + uint32(SHA-256("forge-r3-gates/2026-10-27/<id>/<k>")[0:4]) mod 1700000000`, '
  'k = 0..3 per entry (`tools/make_cands.py`). This is the PC\'s own fresh-srand range '
  '(`common_autonomy.ps1` Fresh-Srand: 300000000 + uint32 mod 1700000000), so the values look like every recent gate\'s.')
P('- Rule (`tools/choose_srands.py`): take the first candidate that (a) occurs in no scanned file or git blob as a '
  'digit-bounded 9-10 digit token, (b) is not in the set of used values below, (c) is not a srand or openings start in '
  'the live manifest copy. %s' % (
      ('All %d chosen values are the k = 0 candidates: no candidate was rejected.' % len(chosen)) if not ch['rejected']
      else ('%d values chosen; rejected candidates: %s' % (len(chosen), json.dumps(ch['rejected'])))))
P('- 6 spare values (R3-SPARE-01..06) were checked the same way for later sub-gates or re-runs by hand; the runner draws its own '
  'random srand for automatic retries and confirm gates.')
P('')
P('| entry | srand | openings start |')
P('|---|---:|---:|')
for eid, v in chosen.items():
    P('| %s | %d | %s |' % (eid, v, ch['openings_start'].get(eid, '-')))
P('')
P('## 2. Paths searched')
P('')
P('**File system** (`tools/srand_scan.py fs`; text files up to 8 MiB; `.git`, `.venv`, `__pycache__`, `selfplay_out` and '
  'engine_io logs skipped): %d files, %.0f MB.' % (fs['files_scanned'], fs['bytes_scanned'] / 1e6))
P('')
P('| root | files | MB | what is there |')
P('|---|---:|---:|---|')
WHAT = {
    'C:/Users/Administrator/grok-pc': 'queue runner + manifest + every backup/staged copy (`forge_push\\autorestart\\forge_gates.json*`, `forge_queue*.ps1`), `forge_queue_state.json`, `forge_queue.log`, `FORGE_RESULTS.csv/.md`, `chain_gates*.ps1/.log`, autonomy scripts, older run logs and archives',
    'D:/grok-pc-data': 'gate folders `forge_push\\gate*\\` (RUN_INFO.json, RESULT.md, config.json, partial_* subfolders), `FORGE_RESULTS*`, `dwqww\\*.md` (OPUS_TEST_PLAN.md, SOL_LEFTOVERS_FOR_CLAUDE.md, OPUS_PROMPT.md), `.claude\\skills` (forge-gate-stats etc.), `.claude\\worktrees` (incl. the AL1 lock package 6_gate/7_history)',
    'F:/forge_push': 'gate folders created since 2026-10-27 (gate39-gate47: RUN_INFO.json, RESULT.md, config.json)',
    'F:/opus_scratch': 'all agents\' scratch and worktrees (job REPORTs, Sol inventory/status copies, R3 jobs in progress); excluded: this job\'s own scratch `r3\\R3-3`, build export `build\\r3_R3-3`, job folder `worktrees\\opus_r3_gates\\opus_r3\\R3-3`',
    'C:/Users/Administrator/.claude/projects/D--grok-pc-data-dwqww/memory': 'session memory notes',
    'C:/Users/Administrator/Downloads': 'depth 1 only: the user\'s downloaded briefs (TEST_PLAN_ALL_IDEAS_20261026.md = OPUS_TEST_PLAN.md byte for byte, CR notes, job prompts)',
}
for r, (n, b) in fs['per_root'].items():
    P('| `%s` | %d | %.0f | %s |' % (r, n, b / 1e6, WHAT.get(r, '')))
P('')
P('%d text files over 8 MiB were not read: self-play data dumps, sensor CSVs, engine I/O logs and disassembly/MSan logs '
  '(no gate srand is written to such files; fastchess does not send its seed to engines).' % fs['skipped_over_max_bytes'])
P('')
P('**Git** (`tools/srand_scan.py git`): every branch of the repository, %d local and origin refs (the other R3 agents\' '
  'branches fetched again on 2026-10-27 before the scan), plus Sol\'s commit `17aa0cae` (branch forge/sol-pack31-20261025; '
  'its ref was left out of the batch list so that its own blobs are read only with `git show 17aa0cae:<path>`, the PC rule '
  'for Sol\'s branch). Blobs were de-duplicated: %d unique text blobs read with `git cat-file --batch`, %d blobs that exist '
  'only in Sol\'s tree read with `git show`; %.0f MB in total.' % (
      len(refs) - 1, gs['n_blobs_cat_file'], gs['n_blobs_git_show'], gs['bytes_scanned'] / 1e6))
P('')
P('Not searched: conversation transcripts of other sessions (`~\\.claude\\projects\\*.jsonl`; they also contain this job\'s '
  'own candidate list) and binary files.')
P('')
P('## 3. Used values')
P('')
P('Extraction (`srand_scan.py`): JSON `"srand"`/`"seed"` fields, fastchess `-srand N`, `srand=N` / `srand: N`, prose '
  '("srand 1556281522", "srand from the test plan (G-B3: 1162618901)"), PowerShell `$srand…=N`, `--seed N`, and every '
  'integer in a Markdown, pipe or CSV table column whose header names srand or seed. Loose matches (training seeds, '
  'counts near the word "seed") are kept: a larger exclusion set only makes the check stricter.')
P('')
P('| source category | distinct values |')
P('|---|---:|')
for c, n in sorted(summ['per_category_counts'].items(), key=lambda kv: -kv[1]):
    P('| %s | %d |' % (c, n))
P('')
P('Cross-checks (each value below is inside the used set):')
P('- live manifest `forge_gates.json` (copy): %d gates, %d distinct srands, openings starts up to %d;' % (len(man['gates']), len(man_srands), max(int(g['openings_start']) for g in man['gates'] if g.get('openings_start'))))
P('- queue state: current gate `%s`, srand %s;' % (state['current']['tag'] if state.get('current') else '-', state['current']['srand'] if state.get('current') else '-'))
P('- `FORGE_RESULTS.csv` (copy): %d srands; `forge_queue.log` (copy): %d "srand N" values (incl. random retry srands);' % (len(csv_srands), len(qlog_srands)))
P('- OPUS_TEST_PLAN.md / TEST_PLAN_ALL_IDEAS_20261026.md: the 18 reserved srands %s;' % ', '.join(str(v) for v in TEST_PLAN))
P('- job REPORTs: the test-plan srands quoted by O5 (1162618901), O8 (113016036), C5 (817455375), S-A2 (869014820) and S-A4 (507544535) are in the set; SOL_LEFTOVERS_FOR_CLAUDE.md names no further value; the forge-gate-stats skill names none. (O1\'s self-play seeds 9901-9905 have 4 digits, below the 6-digit minimum of the extraction and far from the 9-10 digit values chosen here.)')
P('')
P('**srand-context values (%d):**' % len(summ['srand_context_values']))
P('')
P('```')
for ln in wrap(summ['srand_context_values']):
    P(ln)
P('```')
P('')
P('**seed-context values (%d; training/tool seeds, excluded as well):**' % len(summ['seed_only_values']))
P('')
P('```')
for ln in wrap(summ['seed_only_values']):
    P(ln)
P('```')
P('')
P('## 4. Result')
P('')
P('- Literal hits of the %d candidates: file system %d, git %d.' % (sum(len(v) for v in cmap.values()), len(fs['candidate_hits']), len(gs['candidate_hits'])))
P('- Every chosen srand is unique within the proposals, absent from the used set, absent from the manifest srands and '
  'openings starts, and occurs nowhere in the scanned text.')
P('- Finding: `common_autonomy.ps1` Used-Srands (the QA helper that picks fresh srands) reads RUN_INFO files only under '
  '`D:\\grok-pc-data\\forge_push`; since 2026-10-27 new gate folders are on `F:\\forge_push`, so srands recorded only '
  'there (e.g. random retry srands) are outside its set. Its manifest + FORGE_RESULTS.csv + queue-state sources still '
  'cover first-attempt srands.')
P('- To protect the chosen values, install the entries (or at least their srands) into the manifest before other '
  'proposals pick srands; the runner\'s confirm generator excludes manifest srands only.')
md = '\n'.join(L) + '\n'
with open(os.path.join(OUT, 'SRAND_CHECK.md'), 'w', newline='\n', encoding='utf-8') as fh:
    fh.write(md)
print('SRAND_CHECK.md lines', len(L))
