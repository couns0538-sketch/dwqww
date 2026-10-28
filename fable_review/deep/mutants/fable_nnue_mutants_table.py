"""Summarise every mutant re-run log under F:/opus_scratch/fable_review/mutants/<job>/run.log as a markdown table row."""
import os, re, sys
BASE = 'F:/opus_scratch/fable_review/mutants'
CAUGHT = re.compile(r'(-> caught|\bCAUGHT\b|\bKILLED\b|FAIL \(as expected\)|-> OK\b|: caught\b)', re.I)
NOT = re.compile(r'(NOT caught|NOT CAUGHT|\bsurvived\b|\bSURVIVED\b|NOT killed|-> MISSED)', re.I)
BROKEN = re.compile(r'(build failed|pattern not found|configure failed|Traceback|GENERATION FAILED|BUILD FAILED)', re.I)
rows = []
for job in sorted(os.listdir(BASE)):
    log = os.path.join(BASE, job, 'run.log')
    if not os.path.isfile(log):
        continue
    text = open(log, encoding='utf-8', errors='replace').read()
    lines = text.splitlines()
    exit_line = next((l for l in reversed(lines) if l.startswith('exit ')), 'exit ?')
    caught = sum(1 for l in lines if CAUGHT.search(l) and not NOT.search(l))
    notc = sum(1 for l in lines if NOT.search(l))
    broken = sum(1 for l in lines if BROKEN.search(l))
    summary = next((l.strip() for l in reversed(lines) if re.search(r'(\d+\s*/\s*\d+|status=|CHECK: ?PASS|CHECK PASS|killed \d+|caught \d+|all caught|summary:)', l, re.I)), '')
    rows.append((job, exit_line, caught, notc, broken, summary[:110]))
print('| job | exit | caught lines | not-caught lines | broken | last summary line |')
print('|---|---|---:|---:|---:|---|')
for r in rows:
    print('| ' + ' | '.join(str(x) for x in r) + ' |')
