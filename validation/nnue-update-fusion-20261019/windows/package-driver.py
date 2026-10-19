from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

REPO=Path('/workspace/dwqww')
COMMIT='36f5b2f6e1ff519e82a4b52edc85caceaf15aed0'
SOURCE=Path('/workspace/.cloud-setup/forge-windows-nnue-update-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-nnue-update')
BASE=Path('/workspace/.cloud-setup/forge-windows-nnue-update-evidence')
OUT=REPO/'validation/nnue-update-fusion-20261019/windows'
PACKAGE=REPO/'releases/forge-6.4.10-candidate-windows-zen5'
ARCHIVE=PACKAGE.with_name(PACKAGE.name+'.zip')
TOOLS=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
preserved_before=json.loads(Path('/workspace/.cloud-setup/forge-windows-nnue-update-parent-preservation.json').read_text())
preserved_files=[Path(name) for name in preserved_before]
assert {str(p):sha(p) for p in preserved_files}==preserved_before
load=lambda p:json.loads(p.read_text())
assert not any(p.exists() for p in (OUT,PACKAGE,ARCHIVE))
runtime=load(BASE/'runtime-attempt1/result.json');build=load(BASE/'result.json')
assert runtime['status']==build['status'].replace('build_','')=='passed'
assert runtime['source_and_tests_commit']==build['source_and_tests_commit']==COMMIT
assert len(runtime['checks'])==8 and all(c['exit_code']==0 for c in runtime['checks'])
assert len(runtime['ownbook_transitions'])==5 and all(t['PASS'] for t in runtime['ownbook_transitions'])
assert runtime['legal_witness_comparisons']==18947 and runtime['bench11_nodes']==351063
assert runtime['input_sha256_before']==runtime['input_sha256_after']
differential=load(BASE/'differential-attempt1/result.json')
assert differential['status']=='passed' and differential['floating_point_controls_identical'] and differential['native_all_identical']
assert differential['input_sha256_before']==differential['input_sha256_after']
assert [c['bytes'] for c in differential['windows_parent_candidate_comparisons']]==[4097860,21192328]
fastpath=load(BASE/'nnue-update-fastpath-independent-audit.json')
assert fastpath['status']=='passed' and fastpath['fused_arithmetic_count']==0

source_hashes=load(BASE/'source-hashes.json')
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_hashes
for name,digest in source_hashes.items():
    data=subprocess.check_output(['git','-C',str(REPO),'show',COMMIT+':'+name])
    assert hashlib.sha256(data).hexdigest()==digest
OUT.mkdir(parents=True);PACKAGE.mkdir()
for p in BASE.rglob('*'):
    if not p.is_file():continue
    target=OUT/p.relative_to(BASE);target.parent.mkdir(parents=True,exist_ok=True)
    if p.name=='disassembly.log':target.with_suffix('.log.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    else:shutil.copyfile(p,target)
for source,name in [(Path('/workspace/.cloud-setup/build-windows-nnue-update.py'),'build-driver.py'),
                    (Path('/workspace/.cloud-setup/validate-windows-nnue-update.py'),'validation-driver.py'),
                    (Path('/workspace/.cloud-setup/forge-nnue-update-wine'),'forge-nnue-update-wine'),
                    (Path('/workspace/.cloud-setup/windows-nnue-update-differential.py'),'differential-driver.py')]:
    shutil.copyfile(source,OUT/name)
pe_command=[str(TOOLS/'llvm-readobj'),'--file-headers','--coff-imports',str(BUILD/'forge.exe')]
pe_output=subprocess.check_output(pe_command,text=True)
(OUT/'pe-headers-imports.txt').write_text(pe_output)
pe_records={}
for binary in sorted(BUILD.glob('*.exe')):
    command=[str(TOOLS/'llvm-readobj'),'--file-headers','--coff-imports',str(binary)]
    output=subprocess.check_output(command,text=True)
    imports=re.findall(r'^  Name: (.+)$',output,re.M)
    assert 'Machine: IMAGE_FILE_MACHINE_AMD64' in output and 'AddressSize: 64bit' in output
    assert imports and all(name.lower()=='kernel32.dll' or name.lower().startswith('api-ms-win-crt-') for name in imports), imports
    pe_records[binary.name]={'command':command,'sha256':sha(binary),'architecture':'AMD64','imports':imports,'system_or_ucrt_imports_only':True}
    (OUT/(binary.name+'-pe-headers-imports.txt')).write_text(output)
(OUT/'pe-validation.json').write_text(json.dumps(pe_records,indent=2)+'\n')

(OUT/'pe-command.json').write_text(json.dumps(pe_command,indent=2)+'\n')
members={'forge.exe':'forge-6.4.10-ryzen-9850x3d.exe','forge_tests.exe':'forge_tests.exe',
         'forge_tt_tests.exe':'forge_tt_tests.exe','forge_rule50_tests.exe':'forge_rule50_tests.exe',
         'forge_legal_witness_tests.exe':'forge_legal_witness_tests.exe'}
for source,name in members.items():
    assert sha(BUILD/source)==runtime['input_sha256_after'][source]
    shutil.copyfile(BUILD/source,PACKAGE/name)
for source,name in [(SOURCE/'LICENSE','LICENSE'),(BASE/'production-hashes.json','source-hashes.json'),
                    (BASE/'test-hashes.json','test-hashes.json'),
                    (SOURCE/'tests/legal_witness_fixtures.tsv','legal_witness_fixtures.tsv'),
                    (SOURCE/'tools/openings/forge-10000.epd','forge-10000.epd')]:
    shutil.copyfile(source,PACKAGE/name)
provenance={'engine_version':'6.4.10 candidate','source_and_tests_commit':COMMIT,
 'source_url':'https://github.com/couns0538-sketch/dwqww/tree/'+COMMIT,
 'production_source_sha256':load(BASE/'production-hashes.json'),'test_source_sha256':load(BASE/'test-hashes.json'),
 'static_libraries':build['libraries'],
 'compiler':build['compiler'],'flags':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
 'target':'Windows x64 Ryzen 7 9850X3D / Zen5','parallel_build_jobs':2,
 'nnue_update_change':'Count2 remove-then-add updates use one pass per perspective, keeping each lane subtraction then addition; other dirty patterns retain original copy/change-loop fallback; exact in-place updates retained',
 'nnue_differential':differential,
 'nnue_update_emitted_fastpath':fastpath,
 'nnue_api_weights_network_unchanged':all(differential['unchanged_api_and_network_guards'].values()),
 'ownbook_change':'Honor OwnBook false for loaded external Polyglot books, keeping external data loaded and Book File independent of the boolean; true/false/true/false+reload/true tested against actual Windows executable',
 'ownbook_transitions':runtime['ownbook_transitions'],
 'ownbook_evidence':'runtime-attempt1/ownbook-transcript.json; evidence-only adapter translates temporary Linux book filename to Wine Z: path; production tool unchanged',
 'root_effort_change':'Attribute root node effort and best-move lookup by stable full Move identity across iterative-deepening reorder and aspiration retries; time-manager constants unchanged; actual timed-stop and Elo impact unproven',
 'inherited_move_picker_change':'Initialize direct-check masks only when quiet or evasion scoring consumes them, preserving the existing mask formulas and scoring',
 'inherited_qsearch_query_change':'Compute gives_check only inside the existing qsearch pruning block where consumed, after legality and move counting; no evaluator/search rule change intended',
 'inherited_legal_witness_change':'Try one nonpromotion quiet pawn push, validate king safety with is_legal, otherwise retain complete original generation fallback',
 'legal_witness_oracles':'Old complete generator and independent make/unmake king-safety oracle over fixtures, 10000-position corpus and deterministic walks',
 'wine_legal_witness_comparisons':18947,'wine_checks':runtime['checks'],
 'core_reference_perft_passed':True,'tt_groups':8,'rule50_targeted_failures':0,
 'bench11_nodes':351063,'bench_scope':'Hash16MiB/Threads1 node signature only; matches Windows6.4.9 parent; no time/NPS comparison',
 'simd':runtime['simd'],'source_binary_and_tool_hashes_unchanged':True,
 'inherited_tt_coherence':'Striped mutex-protected by-value copies and opaque probe-time destinations; lifecycle-quiescent generation changes',
 'inherited_halfmove_policy':'Score eligible when both capped clocks<90 or exact capped-clock match (cap100); existing main<90 cutoff retained; raw static eval/hash moves reusable',
 'history_limit':'Below90 grouping remains heuristic; not a universal repetition or rule50/history solution',
 'entry_bytes':16,'cluster_bytes':64,
 'binaries':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in PACKAGE.glob('*.exe')},
 'evidence_directory':'validation/nnue-update-fusion-20261019/windows/',
 'performance_claim':'No Windows throughput/timed match measurement performed; helper-kernel results, if recorded separately, do not establish engine Elo',
 'wine_version':'wine-10.0 (Debian 10.0~repack-6)',
 'accepted_elo_gain':None,'native_windows_tested':False,'physical_ryzen_tested':False,
 'stockfish_superiority_proven':False,
 'compile_flags_record':(BUILD/'CMakeFiles/forge_core.dir/flags.make').read_text(),
 'link_record':(BUILD/'CMakeFiles/forge.dir/link.txt').read_text()}
(PACKAGE/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(PACKAGE/'README.txt').write_text('''Forge 6.4.10 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.10-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

This candidate adds a one-pass NNUE accumulator update for count2 changes
that remove one feature and then add another. Each lane still subtracts the
removed weight before adding the new weight. Other dirty patterns retain
the original fallback, and exact in-place updates remain supported.

The actual frozen6.4.9 and6.4.10 Windows cores produced byte-identical
4,097,860-byte update streams and21,192,328-byte original snapshot streams.
The update driver covers1,644 distinct/in-place API checks,31 dirty masks,
and both-color special moves; the original driver includes100,000 synthetic
output evaluations. All four Windows streams also exactly match the frozen
Linux streams, with matching recorded round-to-nearest/FTZ/DAZ controls.
Headers, weights and network are unchanged. Separate emitted-code inspection
verified the count2/remove/add guard, subtraction before addition and one
store per lane on vector/scalar routes, with no fused arithmetic. The
compiler uses Zen5 ZMM vectors in this update path. These correctness and
static-inspection results provide no performance or Elo measurement.

The inherited OwnBook repair makes OwnBook=false suppress an external Polyglot book after
it has been loaded. Book File now controls loading independently of OwnBook.
The actual Windows executable passed all five true/false/true/false+reload/true
transitions using a one-entry external book whose path includes a space.
Only an evidence adapter translated that temporary path to Wine Z: syntax;
the frozen production regression test is unchanged.

The inherited root effort repair addresses attribution when root move
ordering changes. Node effort and best-move lookup now use stable full Move
identity across iterative deepening and aspiration retries. Time-manager
constants and evaluation weights are unchanged. Actual timed-stop behavior,
clock reliability and Elo impact have not been established.

The inherited MovePicker change delays direct-check mask initialization until
quiet or evasion generation consumes those masks, retaining their formulas
and move scoring.

The inherited qsearch change computes gives_check inside the existing pruning
block where the read-only result is consumed.

The inherited legal-move query tries one quiet nonpromotion pawn push with
the normal king-safety check, then uses the complete original generator
fallback whenever that witness fails, including promotions.

Under Wine10, all 18,947 comparisons against the old full generator and an
independent make/unmake legality oracle passed. Fixtures, the frozen 10,000-
position corpus and deterministic walks were checked. Core tests including
six reference perft cases, all eight TT groups, rule50 regressions, and frozen
UCI/ponder tests plus the actual OwnBook regression passed. The stdin bench11 signature is 351,063 nodes with
Hash16MiB/Threads1, matching the Windows6.4.9 parent. Time/NPS is not compared.
YMM clamp/multiply/add and absence of fused arithmetic were checked. All
source, fixture, corpus, binary and tool hashes remained unchanged.

Inherited TT safety uses striped mutex-protected entry copies and opaque
probe-time destinations. Score context permits both capped clocks below90
or an exact capped-clock match (cap100), while preserving the main-search
current-clock<90 cutoff guard, raw static eval and hash-move reuse. Entry and
cluster layouts remain16/64 bytes. The below90 grouping is heuristic and does
not solve every repetition or rule50/history issue.

This is a candidate with correctness evidence. No accepted Elo gain exists.
No Windows throughput or timed match was run; any separate helper-kernel
measurement does not establish engine Elo. Native Windows, physical Ryzen
and Stockfish superiority remain unproven. The separate portable6.4.8 validator remains unchanged and does not test this
executable automatically. No new offline validation bundle was built.

Optional tests are included. From this directory, the witness oracle runs as:
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

Source and tests:36f5b2f6e1ff519e82a4b52edc85caceaf15aed0.
See source-hashes.json, test-hashes.json, provenance.json and SHA256SUMS.
''')
(PACKAGE/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(PACKAGE.iterdir()) if p.is_file()))
with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(PACKAGE.iterdir()):z.write(p,PACKAGE.name+'/'+p.name)
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))==len(list(PACKAGE.iterdir()))
    assert set(z.namelist())=={PACKAGE.name+'/'+p.name for p in PACKAGE.iterdir()}
    for p in PACKAGE.iterdir():assert z.read(PACKAGE.name+'/'+p.name)==p.read_bytes()
    for line in (PACKAGE/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);assert hashlib.sha256(z.read(PACKAGE.name+'/'+name)).hexdigest()==expected
    for source,name in members.items():assert hashlib.sha256(z.read(PACKAGE.name+'/'+name)).hexdigest()==runtime['input_sha256_after'][source]
report={'status':'packaged_and_verified','artifact':str(ARCHIVE.relative_to(REPO)),
 'sha256':sha(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'source_and_tests_commit':COMMIT,
 'engine_sha256':sha(PACKAGE/'forge-6.4.10-ryzen-9850x3d.exe'),'runtime_checks':8,'ownbook_transitions':5,'nnue_update_stream_bytes':4097860,'nnue_original_snapshot_bytes':21192328,'nnue_windows_and_linux_streams_identical':True,
 'legal_witness_comparisons':18947,'bench11_nodes':351063,
 'scope':'Wine correctness and bounded node signature; no speed, Elo or native hardware result'}
preserved_after={str(p):sha(p) for p in preserved_files}
assert preserved_before==preserved_after
(OUT/'prior-artifact-preservation.json').write_text(json.dumps({'status':'unchanged','input_sha256_before':preserved_before,'input_sha256_after':preserved_after},indent=2)+'\n')
(OUT/'artifact.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(Path(__file__),OUT/'package-driver.py')
(OUT/'README.md').write_text('Frozen Windows6.4.10 uses exact source/test commit `'+COMMIT+'`. This candidate adds a count2 remove/add one-pass NNUE update preserving subtraction-then-addition, fallback and exact in-place behavior. Actual frozen6.4.9/6.4.10Windowscores produced byte-identical4,097,860-byte update and21,192,328-byte original streams; allfour matchLinux with identical recordedFPUcontrols. Separate emitted-update inspection verifies guard,order,singlepass andnoFMA; output-layerYMM checks remain separate. OwnBook behavior is inherited. The inherited root repair uses stable full-Move effort identity. Actual timed-stop behavior, clock reliability and Elo impact remain unproven. Inherited MovePicker/query/legal-witness changes remain. All eight functional/signature checks passed: core with six perft references, TT8, rule50, legal-witness oracle (18,947 comparisons), UCI, ponder, actual OwnBook (five transitions with external-book reload while false), and stdin bench11 (351,063 nodes; internal Hash16MiB/Threads1; same as Windows6.4.9 parent). YMM arithmetic/noFMA and all before/after hashes passed. Exact commands, stdout/stderr, source/test manifests, compiler/link records and compressed full disassembly are retained here.\n\nOnly correctness and bounded node signatures are established. No Windows throughput or timed match was run, and helper-kernel measurements do not establish engine Elo. Native Ryzen/Windows and Stockfish superiority remain unproven. The separate portable6.4.8 validator and all older artifacts are unchanged.\n')
print(json.dumps(report,indent=2))
