from pathlib import Path
import gzip
import hashlib
import json
import shutil
import subprocess
import zipfile

REPO=Path('/workspace/dwqww')
COMMIT='816423b1ddac23a00244449deef59dba736055a9'
SOURCE=Path('/workspace/.cloud-setup/forge-windows-rule50-context-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-rule50-context')
BASE=Path('/workspace/.cloud-setup/forge-windows-rule50-context-evidence')
CHECKS=BASE/'runtime-attempt1'
OUT=REPO/'validation/rule50-context-20261019/windows'
PACKAGE=REPO/'releases/forge-6.4.4-candidate-windows-zen5'
ARCHIVE=PACKAGE.with_name(PACKAGE.name+'.zip')
TOOLS=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64/bin')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
assert not any(p.exists() for p in (OUT,PACKAGE,ARCHIVE))
runtime=load(CHECKS/'result.json');build=load(BASE/'result.json')
assert runtime['status']=='passed' and build['status']=='build_passed'
assert build['source_commit']==runtime['source_and_tests_commit']==COMMIT
assert len(runtime['checks'])==5 and all(c['exit_code']==0 for c in runtime['checks'])
assert runtime['tt_groups']==8 and runtime['rule50_targeted_failures']==0
assert runtime['input_sha256_before']==runtime['input_sha256_after']
for name,record in build['binaries'].items():assert sha(BUILD/name)==record['sha256']
source_hashes=load(BASE/'source-hashes.json')
assert {p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob('*') if p.is_file()}==source_hashes
for name,digest in source_hashes.items():
    committed=subprocess.check_output(['git','-C',str(REPO),'show',COMMIT+':'+name])
    assert hashlib.sha256(committed).hexdigest()==digest
OUT.mkdir(parents=True);PACKAGE.mkdir()
for path in BASE.rglob('*'):
    if not path.is_file():continue
    destination=OUT/path.relative_to(BASE);destination.parent.mkdir(parents=True,exist_ok=True)
    if path.name=='disassembly.log':destination.with_suffix('.log.gz').write_bytes(gzip.compress(path.read_bytes(),mtime=0))
    else:shutil.copyfile(path,destination)
for source,name in [(Path('/workspace/.cloud-setup/build-windows-rule50-context.py'),'build-driver.py'),
                    (Path('/workspace/.cloud-setup/validate-windows-rule50-context.py'),'validation-driver.py'),
                    (Path('/workspace/.cloud-setup/forge-rule50-context-wine'),'forge-rule50-context-wine')]:
    shutil.copyfile(source,OUT/name)
pe_command=[str(TOOLS/'llvm-readobj'),'--file-headers','--coff-imports',str(BUILD/'forge.exe')]
(OUT/'pe-headers-imports.txt').write_text(subprocess.check_output(pe_command,text=True))
(OUT/'pe-command.json').write_text(json.dumps(pe_command,indent=2)+'\n')
members={'forge.exe':'forge-6.4.4-ryzen-9850x3d.exe','forge_tests.exe':'forge_tests.exe',
         'forge_tt_tests.exe':'forge_tt_tests.exe','forge_rule50_tests.exe':'forge_rule50_tests.exe'}
for source,name in members.items():shutil.copyfile(BUILD/source,PACKAGE/name)
for source,name in [(SOURCE/'LICENSE','LICENSE'),(BASE/'production-hashes.json','source-hashes.json'),
                    (BASE/'test-hashes.json','test-hashes.json')]:shutil.copyfile(source,PACKAGE/name)
policy={'score_eligible_when':'Both stored/current capped halfmove clocks are below90 OR capped clocks match exactly',
        'clock_cap':100,'main_direct_cutoff_clock_guard':'Existing current-clock<90 guard retained',
        'raw_static_eval_and_tt_moves':'Remain reusable across score-clock mismatch',
        'limitations':'Below90 grouping is heuristic; equal clocks do not establish repetition/history equivalence; not a universal rule50/history solution',
        'entry_bytes':16,'cluster_bytes':64}
provenance={'engine_version':'6.4.4 candidate','source_and_tests_commit':COMMIT,
 'source_url':'https://github.com/couns0538-sketch/dwqww/tree/'+COMMIT,
 'production_source_sha256':load(BASE/'production-hashes.json'),'test_source_sha256':load(BASE/'test-hashes.json'),
 'compiler':build['compiler'],'flags':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
 'target':'Windows x64 Ryzen 7 9850X3D / Zen5','parallel_build_jobs':1,
 'tt_coherence':'Striped mutex-protected by-value entry copies with opaque probe-time destinations; generation changes under lifecycle quiescence',
 'halfmove_context_policy':policy,
 'binaries':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in PACKAGE.glob('*.exe')},
 'wine_checks':runtime['checks'],'tt_regression_groups':8,'rule50_targeted_failures':0,'simd':runtime['simd'],
 'source_binary_and_tool_hashes_unchanged':True,
 'evidence_directory':'validation/rule50-context-20261019/windows/',
 'validation_scope':'Targeted TT/rule50 correctness candidate only; no accepted strength or speed result',
 'speed_evidence':'Same-binary shared-VM A/A showed about fivefold execution-cost variation; conditional NPS gains are unmeasurable here',
 'accepted_elo_gain':None,'native_windows_tested':False,'physical_ryzen_tested':False,
 'stockfish_superiority_proven':False,
 'compile_flags_record':(BUILD/'CMakeFiles/forge_core.dir/flags.make').read_text(),
 'link_record':(BUILD/'CMakeFiles/forge.dir/link.txt').read_text()}
(PACKAGE/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(PACKAGE/'README.txt').write_text('''Forge 6.4.4 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.4-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

6.4.4 addresses tested forward and reverse reuse of TT search scores across
different halfmove-clock contexts near the fifty-move boundary. A score is
eligible when BOTH stored/current clocks are below90, OR their capped clocks
match exactly. Clocks are capped at100. The old main-search current-clock<90
direct-cutoff guard remains. Raw static evaluation and hash moves remain
reusable when a search score is ineligible. The below90 grouping is heuristic;
equal clocks do not establish repetition/history equivalence. This is not a
universal solution to rule50, repetition or search-history context.

The preceding TT coherence fix uses striped mutexes to protect complete
by-value entry copies and opaque probe-time destination handles. Generation
changes occur under lifecycle quiescence after workers are joined. Entry and
cluster layouts remain16 and64 bytes. Previous promotion, stalemate, clock,
TT-tag and AVX2 changes remain; evaluation weights are unchanged.

Under Wine10, core tests, all8 TT regression groups, targeted rule50 tests,
and frozen-source UCI/ponder checks passed. Both reverse-context regressions
passed and targeted_regression_failures=0. Emitted256-bit clamp/multiply/add
and absence of fused arithmetic were checked. All source, test, binary and
tool hashes stayed unchanged. Optional test executables reproduce these
regression checks. Source and tests are pinned together to commit816423b.

This is a targeted correctness candidate. No accepted Elo gain exists.
Same-binary A/A execution cost varied about fivefold on the shared VM, so
conditional NPS gains are unmeasurable here. Native Windows and physical
Ryzen validation remain pending; Stockfish superiority is unproven.

The separate portable6.4.2 match-validation bundle stays pinned to6.4.2;
it does not test this6.4.4 binary automatically. Older artifacts and evidence
are retained. This package performs no uploads or background reporting.

Source:816423b1ddac23a00244449deef59dba736055a9.
See source-hashes.json, test-hashes.json, provenance.json and SHA256SUMS.
''')
(PACKAGE/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(PACKAGE.iterdir()) if p.is_file()))
with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for path in sorted(PACKAGE.iterdir()):archive.write(path,PACKAGE.name+'/'+path.name)
with zipfile.ZipFile(ARCHIVE) as archive:
    assert archive.testzip() is None
    assert set(archive.namelist())=={PACKAGE.name+'/'+p.name for p in PACKAGE.iterdir() if p.is_file()}
    for path in PACKAGE.iterdir():assert archive.read(PACKAGE.name+'/'+path.name)==path.read_bytes()
    for line in (PACKAGE/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);assert hashlib.sha256(archive.read(PACKAGE.name+'/'+name)).hexdigest()==expected
    for source,name in members.items():
        assert hashlib.sha256(archive.read(PACKAGE.name+'/'+name)).hexdigest()==runtime['input_sha256_after'][source]
report={'status':'packaged_and_verified','artifact':str(ARCHIVE.relative_to(REPO)),
 'sha256':sha(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'source_and_tests_commit':COMMIT,
 'engine_sha256':sha(PACKAGE/'forge-6.4.4-ryzen-9850x3d.exe'),
 'runtime_checks':len(runtime['checks']),'tt_groups':8,'rule50_targeted_failures':0,
 'scope':'Wine correctness only; native hardware, speed/Elo/Stockfish claims unproven'}
(OUT/'artifact.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(Path(__file__),OUT/'package-driver.py')
(OUT/'README.md').write_text('Frozen 6.4.4 Windows build and tests use production/test commit `'+COMMIT+'`. Wine core, all8 TT groups, targeted rule50 regressions, UCI and ponder passed; source, binaries and tools stayed unchanged. SIMD inspection found YMM clamp/multiply/add with no fused operations. Exact commands, all logs, source/test hashes, compiler/link records and full compressed disassembly are preserved here.\n\nThe score-context policy permits both capped clocks below90 or exact capped-clock equality (cap100), retains the main current-clock<90 cutoff guard, and leaves raw static eval/hash moves reusable. Below90 compatibility is heuristic and does not solve every repetition/history issue. TT entry/cluster layout remains16/64 bytes.\n\nThis is targeted correctness evidence only. Shared-VM same-binary A/A was too variable to resolve conditional NPS gains; no accepted Elo, native Windows/Ryzen or Stockfish result exists. No timed games or Wine A/A repeats were run. The existing portable6.4.2 validator bundle is unchanged and remains pinned to6.4.2.\n')
print(json.dumps(report,indent=2))
