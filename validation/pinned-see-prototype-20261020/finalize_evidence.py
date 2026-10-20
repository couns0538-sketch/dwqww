#!/usr/bin/env python3
from pathlib import Path
import datetime, hashlib, json, shutil, subprocess, tarfile, zipfile

ROOT=Path(__file__).resolve().parent
WORK=Path('/workspace/pinned-see-prototype-20261020')
BUILD=Path('/workspace/.cloud-setup/forge-extension-path-release')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((ROOT/'build-record.json').read_text())
matrix=json.loads((ROOT/'matrix-record.json').read_text())
supplement=json.loads((ROOT/'supplement-record.json').read_text())
assert matrix['status']=='PASS_bounded_prototype_correctness' and supplement['status']=='PASS'
assert sha(BUILD/'libforge_core.a')==build['original_core_sha256_before']
assert sha(WORK/'source/src/board.cpp')==build['candidate_board_sha256']
frozen=json.loads((ROOT/'frozen-source-sha256.json').read_text())
assert all(sha(WORK/'source'/p)==h for p,h in frozen.items() if p!='src/board.cpp')
shutil.copy2(WORK/'board.cpp.o',ROOT/'candidate-board.cpp.o')
with tarfile.open(ROOT/'candidate-build-source.tar','w') as tar:
    tar.add(WORK/'source',arcname='source')
phase=subprocess.run(['python3',str(ROOT/'assert_authored.py')],capture_output=True,timeout=5)
(ROOT/'assert-authored.stdout').write_bytes(phase.stdout)
(ROOT/'assert-authored.stderr').write_bytes(phase.stderr)
assert phase.returncode==0
executions=[x for x in matrix['phases'] if x['label'].startswith('run-')]+supplement['phases']
summary={
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'PASS_bounded_prototype_correctness_only',
 'production_and_git_changed':False,
 'baseline_source_commit':build['source_commit'],
 'applied_outside_patch':'pinned-see.patch; exported /workspace/pinned-see-prototype-20261020/source/src/board.cpp only',
 'source_exports':'Complete source required to build every existing target: CMakeLists, LICENSE, include, src, tests, tools, bench; excludes unrelated historical release/evidence trees.',
 'frozen_build_source_files':len(frozen),
 'changed_archive_members':build['only_changed_member'],
 'original_release_core_unchanged':True,
 'actual_api_cases':matrix['cases']+len(supplement['comparisons']),
 'authored_cases':48,'authored_legal_cases':46,'initial_illegal_precondition_cases':2,
 'seeded_sparse_legal_captures':256,'thresholds_per_case':len(matrix['thresholds']),
 'baseline_exact_oracle_mismatches':len(matrix['oracle_mismatches']['baseline'])+sum(x['baseline']!=x['oracle'] for x in supplement['comparisons']),
 'candidate_exact_oracle_mismatches':len(matrix['oracle_mismatches']['candidate'])+len(supplement['failures']),
 'initial_legality_or_recapture_set_mismatches':len(matrix['api_oracle_failures']),
 'engine_execution_seconds_budget_accounting_only':sum(x['elapsed_seconds'] for x in executions),
 'assert_authored_command':['python3',str(ROOT/'assert_authored.py')],
 'assert_authored_return_code':phase.returncode,
 'preserved_failure':'supplement-attempt1 invalid authored FEN rejected by independent oracle before engine execution; corrected nonparticipating black king square a7->h7 only.',
 'highest_remaining_risks':['Every non-king geometric recapturer now performs full own-king attack lookup; cost and playing-strength effect unmeasured.','Only bounded public Board API oracle validation performed; full candidate Release/ASan/TSan/CTest/search gates remain required.','Generic SEE retains original least-valuable-attacker approximation and recapture-promotion handling; 302 legal cases do not establish universal exchange minimax.'],
 'acceptance':'Prototype ready for separate isolated candidate review. No production integration, speed, NPS or Elo claim.'}
(ROOT/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
files=[p for p in ROOT.iterdir() if p.is_file() and p.name not in ['complete-evidence.zip','archive-manifest.json']]
manifest={p.name:sha(p) for p in sorted(files)}
(ROOT/'archive-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(ROOT/'complete-evidence.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p in files+[ROOT/'archive-manifest.json']: archive.write(p,p.name)
with zipfile.ZipFile(ROOT/'complete-evidence.zip') as archive:
    assert archive.testzip() is None
    for name,h in manifest.items(): assert hashlib.sha256(archive.read(name)).hexdigest()==h
print(json.dumps({'status':summary['status'],'files':len(manifest),'archive_bytes':(ROOT/'complete-evidence.zip').stat().st_size,'archive_sha256':sha(ROOT/'complete-evidence.zip'),'cases':summary['actual_api_cases'],'baseline_mismatches':summary['baseline_exact_oracle_mismatches'],'candidate_mismatches':summary['candidate_exact_oracle_mismatches']},indent=2))
