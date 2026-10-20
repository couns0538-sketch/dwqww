#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, io, json, subprocess, tarfile, zipfile

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
record=json.loads((ROOT/'record.json').read_text())
freeze=json.loads((ROOT/'PRE-RUN-FREEZE.json').read_text())
cases=json.loads((ROOT/'oracle-corpus.json').read_text())
comparisons=json.loads((ROOT/'comparisons.json').read_text())
assert record['status']=='COMPLETE_BOUNDED_PROMOTION_RECAPTURE_RESEARCH'
assert all(sha(ROOT/n)==h for n,h in freeze['files_sha256'].items())
assert all(sha(p)==h for p,h in record['original_inputs_sha256_before'].items())
assert all(p['exit_code']==0 for p in record['phases'])
assert record['board_compiles']==record['driver_compiles']==0
assert len(record['false_negative_cases_at_zero'])==2
assert len(record['false_positive_cases_at_zero'])==2
rows={r['id']:r for r in csv.DictReader((ROOT/'source16-api.stdout').read_text().splitlines(),delimiter='\t')}
assert len(rows)==10
for case in cases:
    row=rows[case['id']]
    assert row['initial_legal']=='1'
    actual_recaptures=sorted(row['legal_recaptures'].split(',')) if row['legal_recaptures'] else []
    assert actual_recaptures==case['legal_recaptures']

source_archive=subprocess.check_output(['git','archive',record['source_commit'],
    'CMakeLists.txt','LICENSE','src','include','tests','tools','bench'],cwd=REPO)
(ROOT/'frozen-source16.tar').write_bytes(source_archive)
with tarfile.open(fileobj=io.BytesIO(source_archive)) as tar:
    assert tar.extractfile('src/board.cpp').read()==(ROOT/'source16-board.cpp').read_bytes()
members=subprocess.check_output(['ar','t',ROOT/'source16-libforge_core.a']).decode().splitlines()
write(ROOT/'core-member-sha256.json',{m:hashlib.sha256(subprocess.check_output(
    ['ar','p',ROOT/'source16-libforge_core.a',m])).hexdigest() for m in members})
summary={
    'status':'REPRODUCED_THRESHOLD_ZERO_FALSE_NEGATIVES_AND_FALSE_POSITIVES',
    'source_commit':record['source_commit'],
    'source16_board_sha256':record['source16_board_sha256'],
    'source16_core_sha256':record['core_sha256'],
    'actual_api_executable_sha256':record['executable_sha256'],
    'source_archive_sha256':sha(ROOT/'frozen-source16.tar'),
    'pre_run_freeze_sha256':sha(ROOT/'PRE-RUN-FREEZE.json'),
    'cases':10,'new_mirrored_cases':8,'known_controls':2,
    'exchange_value_disagreements':6,'wrong_threshold_answers':44,'threshold_answers':200,
    'threshold_zero_false_negatives':record['false_negative_cases_at_zero'],
    'threshold_zero_false_positives':record['false_positive_cases_at_zero'],
    'api_legality_or_recapture_failures':[],
    'invalid_fixtures':0,'failed_build_or_api_runs':0,
    'board_compiles':0,'driver_compiles':0,'serial_links':1,'actual_api_runs':1,
    'engine_execution_seconds_budget_accounting_only':record['engine_elapsed_seconds_budget_accounting_only'],
    'engine_budget_seconds':30,'all_previous_files_unchanged':True,
    'source17_implemented':False,
    'recommendation':'Implement one narrowly guarded last-rank promotion-aware LVA gain-stack helper before old threshold bounds; preserve ordinary source16 SEE.',
    'performance_claim':None,'strength_claim':None
}
write(ROOT/'SUMMARY.json',summary)
lines=[
    '# Promotion-recapture SEE research',
    '',
    'Confirmed a source16 SEE false negative at threshold zero for both colors.',
    'No source17 fix has been implemented. DESIGN.md recommends one rare guarded',
    'promotion-aware LVA gain-stack helper, leaving ordinary SEE unchanged.',
    '',
    '| Mirrored control pair | Oracle | Actual source16 | Threshold zero |',
    '| --- | ---: | ---: | --- |',
    '| Own later promotion saves capture | +500 | -100 | False negative |',
    '| Enemy first promotion poisons capture | -600 | +200 | False positive |',
    '| Promoting pawn is pinned | +500 | +500 | Agrees |',
    '| Promotion then king recapture | +300 | +300 | Agrees |',
    '| Original inherited limitation | -1200 | -400 | Both reject |',
    '',
    'All ten fixtures are valid/legal. The eight new cases are four mirrored',
    'pairs; the original two limitations remain controls. Complete python-chess',
    'legal same-target capture minimax trees and 20 thresholds were frozen before',
    'the link and only actual API run. Cases, trees, and expectations were not',
    'filtered or changed after observing source16 results.',
    '',
    'The proposed second hypothesis did not return +500: its actual source16 SEE',
    'is +200 against oracle -600. The false-positive conclusion still holds.',
    'The first hypothesis is a confirmed +500 versus -100 false negative, so the',
    'opportunity affects zero-threshold capture classification, not just ordering.',
    '',
    'There are six exchange-value disagreements and 44 wrong answers among 200',
    'fixed-threshold queries. All actual initial legality and complete first',
    'recapture sets agree with the independent oracle. Source16 outputs are red',
    'research evidence; the four already-correct pin/king cases are controls.',
    '',
    'Only the existing diagnostic object was linked to a copied frozen Release16',
    'core. No Board or driver source was compiled. The one actual API run used',
    f"{record['engine_elapsed_seconds_budget_accounting_only']:.6f} seconds of a 30-second operational budget.",
    'No matches, timing/NPS comparison, source edits, Git actions, or strength',
    'claim occurred. All previous inputs and the original source16 core remained',
    'unchanged. There were no invalid fixture or link/API failures.',
    '',
    'PRE-RUN-FREEZE.json, oracle-corpus.json, cases.tsv, thresholds.json,',
    'source16-api.stdout, comparisons.json, and record.json preserve the exact',
    'inputs, complete trees, outputs, command, exit statuses, hashes, and scope.',
    'The copied core, driver source/object, actual executable, source16 Board,',
    'complete source TAR, design, and independent source-only design review are',
    'included in complete-evidence.zip.',
    '',
    'The archive manifest covers every payload. Its byte-verification receipt',
    'is kept outside the ZIP to avoid self-referential hashing. This bounded',
    'research is not an implementation or candidate-acceptance result.',
    ''
]
(ROOT/'README.md').write_text('\n'.join(lines))
excluded={'complete-evidence.zip','archive-manifest.json','archive-verification.json'}
payloads={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*'))
          if p.is_file() and p.name not in excluded}
write(ROOT/'archive-manifest.json',{'files':payloads,'files_count':len(payloads)})
archive=ROOT/'complete-evidence.zip'
assert not archive.exists()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    for name in payloads:z.write(ROOT/name,name)
    z.write(ROOT/'archive-manifest.json','archive-manifest.json')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set(payloads)|{'archive-manifest.json'}
    assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in payloads.items())
assert all(sha(ROOT/n)==h for n,h in payloads.items())
write(ROOT/'archive-verification.json',{
    'status':'PASS_ALL_MEMBERS_BYTE_VERIFIED','archive_sha256':sha(archive),
    'archive_bytes':archive.stat().st_size,'payloads':len(payloads),
    'original_inputs_unchanged':all(sha(p)==h for p,h in record['original_inputs_sha256_before'].items())})
print(json.dumps({'status':summary['status'],'archive_sha256':sha(archive),
    'payloads':len(payloads),'false_negatives_at_zero':2,'false_positives_at_zero':2,
    'source17_implemented':False}))
