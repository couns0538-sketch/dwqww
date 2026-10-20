from pathlib import Path
import gzip
import hashlib
import json
import shutil
import subprocess
import zipfile

REPO=Path('/workspace/dwqww')
COMMIT='82cd2c24062d07cbacbe5b722b6ec0b718981abd'
SOURCE=Path('/workspace/.cloud-setup/forge-windows-legal-witness-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-legal-witness')
BASE=Path('/workspace/.cloud-setup/forge-windows-legal-witness-evidence')
OUT=REPO/'validation/legal-witness-20261019/windows'
PACKAGE=REPO/'releases/forge-6.4.5-candidate-windows-zen5'
ARCHIVE=PACKAGE.with_name(PACKAGE.name+'.zip')
TOOLS=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
assert not any(p.exists() for p in (OUT,PACKAGE,ARCHIVE))
runtime=load(BASE/'runtime-attempt1/result.json');build=load(BASE/'result.json')
assert runtime['status']==build['status'].replace('build_','')=='passed'
assert runtime['source_and_tests_commit']==build['source_and_tests_commit']==COMMIT
assert len(runtime['checks'])==7 and all(c['exit_code']==0 for c in runtime['checks'])
assert runtime['legal_witness_comparisons']==18947 and runtime['bench11_nodes']==351063
assert runtime['input_sha256_before']==runtime['input_sha256_after']
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
for source,name in [(Path('/workspace/.cloud-setup/build-windows-legal-witness.py'),'build-driver.py'),
                    (Path('/workspace/.cloud-setup/validate-windows-legal-witness.py'),'validation-driver.py'),
                    (Path('/workspace/.cloud-setup/forge-legal-witness-wine'),'forge-legal-witness-wine')]:
    shutil.copyfile(source,OUT/name)
pe_command=[str(TOOLS/'llvm-readobj'),'--file-headers','--coff-imports',str(BUILD/'forge.exe')]
(OUT/'pe-headers-imports.txt').write_text(subprocess.check_output(pe_command,text=True))
(OUT/'pe-command.json').write_text(json.dumps(pe_command,indent=2)+'\n')
members={'forge.exe':'forge-6.4.5-ryzen-9850x3d.exe','forge_tests.exe':'forge_tests.exe',
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
provenance={'engine_version':'6.4.5 candidate','source_and_tests_commit':COMMIT,
 'source_url':'https://github.com/couns0538-sketch/dwqww/tree/'+COMMIT,
 'production_source_sha256':load(BASE/'production-hashes.json'),'test_source_sha256':load(BASE/'test-hashes.json'),
 'compiler':build['compiler'],'flags':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
 'target':'Windows x64 Ryzen 7 9850X3D / Zen5','parallel_build_jobs':2,
 'legal_witness_change':'Try one nonpromotion quiet pawn push, validate king safety with is_legal, otherwise retain complete original generation fallback',
 'legal_witness_oracles':'Old complete generator and independent make/unmake king-safety oracle over fixtures, 10000-position corpus and deterministic walks',
 'wine_legal_witness_comparisons':18947,'wine_checks':runtime['checks'],
 'core_reference_perft_passed':True,'tt_groups':8,'rule50_targeted_failures':0,
 'bench11_nodes':351063,'bench_scope':'Hash16MiB/Threads1 node signature only; matches Windows6.4.4 parent; no time/NPS comparison',
 'simd':runtime['simd'],'source_binary_and_tool_hashes_unchanged':True,
 'inherited_tt_coherence':'Striped mutex-protected by-value copies and opaque probe-time destinations; lifecycle-quiescent generation changes',
 'inherited_halfmove_policy':'Score eligible when both capped clocks<90 or exact capped-clock match (cap100); existing main<90 cutoff retained; raw static eval/hash moves reusable',
 'history_limit':'Below90 grouping remains heuristic; not a universal repetition or rule50/history solution',
 'entry_bytes':16,'cluster_bytes':64,
 'binaries':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in PACKAGE.glob('*.exe')},
 'evidence_directory':'validation/legal-witness-20261019/windows/',
 'performance_claim':'No Windows throughput/timed match measurement performed; helper-kernel results, if recorded separately, do not establish engine Elo',
 'accepted_elo_gain':None,'native_windows_tested':False,'physical_ryzen_tested':False,
 'stockfish_superiority_proven':False,
 'compile_flags_record':(BUILD/'CMakeFiles/forge_core.dir/flags.make').read_text(),
 'link_record':(BUILD/'CMakeFiles/forge.dir/link.txt').read_text()}
(PACKAGE/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(PACKAGE/'README.txt').write_text('''Forge 6.4.5 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.5-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

This candidate optimizes the Boolean legal-move query: it tries one quiet,
nonpromotion pawn push and applies the normal king-safety check. A successful
witness proves a legal move exists. Every failed witness uses the unchanged
complete generator fallback, including promotions. Evaluation weights and
intended search behavior are unchanged.

Under Wine10, all 18,947 comparisons against the old full generator and an
independent make/unmake legality oracle passed. Fixtures, the frozen 10,000-
position corpus and deterministic walks were checked. Core tests including
six reference perft cases, all eight TT groups, rule50 regressions, and frozen
UCI/ponder tests passed. The stdin bench11 signature is 351,063 nodes with
Hash16MiB/Threads1, matching the Windows6.4.4 parent. Time/NPS is not compared.
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
and Stockfish superiority remain unproven. The portable6.4.2 validator stays
pinned to6.4.2 and does not test this executable automatically.

Optional tests are included. From this directory, the witness oracle runs as:
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

Source and tests:82cd2c24062d07cbacbe5b722b6ec0b718981abd.
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
 'engine_sha256':sha(PACKAGE/'forge-6.4.5-ryzen-9850x3d.exe'),'runtime_checks':7,
 'legal_witness_comparisons':18947,'bench11_nodes':351063,
 'scope':'Wine correctness and bounded node signature; no speed, Elo or native hardware result'}
(OUT/'artifact.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(Path(__file__),OUT/'package-driver.py')
(OUT/'README.md').write_text('Frozen Windows6.4.5 uses exact source/test commit `'+COMMIT+'`. All seven functional/signature checks passed: core with six perft references, TT8, rule50, legal-witness oracle (18,947 comparisons), UCI, ponder and stdin bench11 (351,063 nodes; internal Hash16MiB/Threads1; same as Windows6.4.4 parent). YMM arithmetic/noFMA and all before/after hashes passed. Exact commands, stdout/stderr, source/test manifests, compiler/link records and compressed full disassembly are retained here.\n\nOnly correctness and bounded node signatures are established. No Windows throughput or timed match was run, and helper-kernel measurements do not establish engine Elo. Native Ryzen/Windows and Stockfish superiority remain unproven. The separate portable6.4.2 validator and all older artifacts are unchanged.\n')
print(json.dumps(report,indent=2))
