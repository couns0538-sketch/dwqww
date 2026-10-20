#!/usr/bin/env python3
"""Preserve the completed outside-production prototype; never executes engines."""
from pathlib import Path
import csv, datetime, hashlib, json, tarfile, zipfile

ROOT=Path(__file__).resolve().parent
RESEARCH=ROOT.parent
WORK=Path('/workspace/see-recapture-promotion-prototype-20261020')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
freeze=json.loads((ROOT/'SOURCE-FREEZE.json').read_text())
run=json.loads((ROOT/'attempt1/record.json').read_text())
result=json.loads((ROOT/'attempt1/comparison.json').read_text())
assert run['status']=='PASS_BOUNDED_API_GATE'
assert result['status']=='PASS_BOUNDED_ORACLE_AND_ORDINARY_PARITY'
assert not result['candidate_oracle_mismatches'] and not result['failures']
assert all(p['exit_code']==0 for p in run['phases'])
assert all(sha(ROOT/'inputs'/n)==h for n,h in freeze['input_sha256'].items())
assert all(sha(ROOT/n)==h for n,h in freeze['source_only_file_sha256'].items())
old=json.loads((RESEARCH/'archive-manifest.json').read_text())['files']
assert all(sha(RESEARCH/n)==h for n,h in old.items())
assert sha(RESEARCH/'complete-evidence.zip')=='9f2b0d81d053c433bd3640ad5f6cefb8cbd04e1f3bdf7f02ead244525e7963f3'
assert sha('/workspace/.cloud-setup/forge-pin-mask-release/libforge_core.a')==run['original_core_sha256_before']
for label in ['reference','candidate']:
    source=WORK/('source-'+label)
    assert all(sha(source/n)==h for n,h in freeze['header_sha256'].items())
    with tarfile.open(ROOT/('source-'+label+'.tar'),'w') as tar:
        for p in sorted(source.rglob('*')):
            if p.is_file():tar.add(p,arcname=str(p.relative_to(source)))
assert sha(WORK/'source-candidate/src/board.cpp')==freeze['candidate_board_sha256']

summary={
    'status':'PASS_ISOLATED_PROMOTION_RECAPTURE_API_PROTOTYPE',
    'production_applied':False,'git_modified':False,'board_header_changed':False,
    'source16_commit':freeze['source16_commit'],
    'source16_board_sha256':freeze['source16_board_sha256'],
    'candidate_board_sha256':freeze['candidate_board_sha256'],
    'patch_sha256':freeze['patch_sha256'],
    'candidate_core_sha256':sha(ROOT/'attempt1/candidate-libforge_core.a'),
    'actual_candidate_api_sha256':sha(ROOT/'attempt1/api-candidate'),
    'cases':326,'legal_cases':324,'initial_illegal_oracle_exclusions':2,
    'fixed_grid_answers_checked_for_legal_cases':324*20,'new_adjacent_answers':30,
    'ordinary_rows_byte_identical':314,'guard_rows':12,
    'reference_exchange_mismatch_rows':len(result['reference_oracle_mismatches']),
    'candidate_exchange_mismatch_rows':0,
    'corrected_threshold_zero_false_negative_cases':2,
    'corrected_threshold_zero_false_positive_cases':2,
    'old_inherited_promotion_limitations_now_correct':2,
    'original_research_core_headers_inputs_unchanged':True,
    'only_changed_core_member':'board.cpp.o',
    'attempts':1,'failed_build_or_api_attempts':0,'board_compiles':1,'driver_compiles':1,
    'actual_api_invocations':2,'engine_budget_seconds':run['engine_budget_seconds'],
    'engine_seconds_budget_accounting_only':run['engine_seconds'],
    'performance_claim':None,'strength_claim':None,
    'limitations':[
        'Retains LVA/lsb selection and optional stopping; not universal exact chess minimax.',
        'No full engine, sanitizer, Windows, bench, or strength gate was run for this prototype.',
        'Ordinary-path source and observed rows are preserved, but the rare dispatch has unmeasured runtime cost.'
    ]}
write(ROOT/'SUMMARY.json',summary)
(ROOT/'README.md').write_text("""# Outside-production promotion-recapture prototype

The narrowly guarded fallback passes the bounded API gate. Production source16,
Git, the Board header/class definition, original core, and previous research
artifacts remain untouched. This is a prototype result, not a source17 switch.

The patch inserts one anonymous-namespace helper using public Board getters and
one dispatch before the ordinary threshold bounds. The source16 swap loop and
threshold logic remain byte-for-byte unchanged outside that insertion. No class
definition or header changed, so replacing only Board.cpp in a copied core does
not mix inconsistent Board definitions across translation units.

The guard requires a last-rank target and a live original pawn of the promoting
color geometrically attacking it after excluding the initial origin/captured
square. Initial king/castle handling is preserved. The rare helper retains the
source16 pin mask, LVA/lsb choices, ray updates, and terminal king-defense test,
adds promotion material plus the resulting queen victim value, and folds a
bounded 64-entry full gain stack without the old rare-path threshold shortcuts.

The immutable 316-case baseline and ten new research cases were frozen before
the only build/run attempt. Two original initial-illegal moves are excluded from
oracle claims and retained in the ordinary-path parity check.

- All 324 legal cases match frozen oracle values and 6,480 fixed-grid answers.
- All 30 adjacent-bracket answers on the ten new cases pass.
- All 314 non-guard full output rows are byte-identical to source16.
- Twelve rows enter the fallback; eight source16 exchange mismatches are fixed.
- Both mirrored threshold-zero false negatives now return +500, matching oracle.
- Both mirrored false positives now return -600, matching oracle.
- The old inherited -400 versus -1200 controls now correctly return -1200.
- Pinned-pawn +500 and promotion/king-recapture +300 controls stay correct.

The new driver prints the existing twenty thresholds, actual guard
classification, and adjacent brackets. Its source16 twenty-threshold prefix
matches the previously frozen actual output. The independent source audit found
no issue in stack arithmetic, pin/LVA behavior, the guard, king termination,
array bounds, or header/ODR consistency.

Only one Board object and one diagnostic driver object were compiled,
sequentially. Only Board.cpp.o differs in copied core members. The two finite
API invocations used {:.6f} seconds of a 30-second operational budget, with a
10-second cap each. Every phase exited zero; no retry, bench, match, or
additional engine invocation was run.

SOURCE-FREEZE.json, inputs/, attempt1/record.json, attempt1/comparison.json,
raw outputs, patch, exact Board sources, source/header TARs, objects, copied
cores, executable diagnostics, and drivers preserve the result. The previous
research capsule remains unchanged at SHA-256
9f2b0d81d053c433bd3640ad5f6cefb8cbd04e1f3bdf7f02ead244525e7963f3.

No runtime/NPS/Elo gain is claimed. LVA/lsb and optional-stop approximations
remain. Full engine/sanitizer/Windows gates and any integration decision belong
to a separately frozen candidate. The capsule manifest hashes every payload;
the archive verification receipt is outside the ZIP to avoid self-reference.
""".format(run['engine_seconds']))

excluded={'complete-evidence.zip','archive-manifest.json','archive-verification.json'}
payloads={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*'))
          if p.is_file() and p.name not in excluded}
write(ROOT/'archive-manifest.json',{'files':payloads,'files_count':len(payloads)})
archive=ROOT/'complete-evidence.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    for n in payloads:z.write(ROOT/n,n)
    z.write(ROOT/'archive-manifest.json','archive-manifest.json')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert set(z.namelist())==set(payloads)|{'archive-manifest.json'}
    assert all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in payloads.items())
assert all(sha(ROOT/n)==h for n,h in payloads.items())
assert all(sha(RESEARCH/n)==h for n,h in old.items())
write(ROOT/'archive-verification.json',{'status':'PASS_ALL_MEMBERS_BYTE_VERIFIED',
    'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,
    'payloads':len(payloads),'all_previous_research_files_unchanged':True})
print(json.dumps({'status':summary['status'],'archive_sha256':sha(archive),
    'payloads':len(payloads),'candidate_board_sha256':summary['candidate_board_sha256']}))
