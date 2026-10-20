from pathlib import Path
import gzip
import hashlib
import json
import shutil
import subprocess
import zipfile

REPO=Path('/workspace/dwqww')
SOURCE=Path('/workspace/.cloud-setup/forge-windows-tt-coherent-source')
BUILD=Path('/workspace/.cloud-setup/forge-windows-tt-coherent')
BUILD_EVIDENCE=Path('/workspace/.cloud-setup/forge-windows-tt-coherent-evidence')
CHECKS=BUILD_EVIDENCE/'runtime-attempt1'
EVIDENCE=REPO/'validation/tt-coherence-20261019/windows'
FOLDER=REPO/'releases/forge-6.4.3-candidate-windows-zen5'
ARCHIVE=REPO/'releases/forge-6.4.3-candidate-windows-zen5.zip'
TOOLCHAIN=Path('/workspace/.cloud-setup/toolchains/llvm-mingw-20261006-ucrt-ubuntu-22.04-x86_64')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
load=lambda path:json.loads(path.read_text())
assert not EVIDENCE.exists() and not FOLDER.exists() and not ARCHIVE.exists()
runtime=load(CHECKS/'result.json');build=load(BUILD_EVIDENCE/'result.json')
assert runtime['status']=='passed' and build['status']=='build_passed'
assert all(record['exit_code']==0 for record in runtime['checks'])
for name,record in build['binaries'].items():assert sha(BUILD/name)==record['sha256']
for name,digest in load(BUILD_EVIDENCE/'production-hashes.json').items():
    committed=subprocess.check_output(['git','-C',str(REPO),'show',build['production_commit']+':'+name])
    assert hashlib.sha256(committed).hexdigest()==digest==sha(SOURCE/name)
EVIDENCE.mkdir(parents=True);FOLDER.mkdir()
for path in BUILD_EVIDENCE.rglob('*'):
    if not path.is_file():continue
    destination=EVIDENCE/path.relative_to(BUILD_EVIDENCE)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if path.name=='disassembly.log':
        destination.with_suffix('.log.gz').write_bytes(gzip.compress(path.read_bytes(),mtime=0))
    else:shutil.copyfile(path,destination)
shutil.copyfile('/workspace/.cloud-setup/build-windows-tt-coherent.py',EVIDENCE/'build-driver.py')
shutil.copyfile('/workspace/.cloud-setup/validate-windows-tt-coherent.py',EVIDENCE/'validation-driver.py')
shutil.copyfile('/workspace/.cloud-setup/forge-tt-coherent-wine',EVIDENCE/'forge-tt-coherent-wine')
readobj=TOOLCHAIN/'bin/llvm-readobj'
command=[str(readobj),'--file-headers','--coff-imports',str(BUILD/'forge.exe')]
(EVIDENCE/'pe-headers-imports.txt').write_text(subprocess.check_output(command,text=True))
(EVIDENCE/'static-inspection-commands.json').write_text(json.dumps({
 'pe_command':command,'simd_command':[str(TOOLCHAIN/'bin/llvm-objdump'),'-d','--no-show-raw-insn',str(BUILD/'forge.exe')],
 'tool_hashes_observed_after_checks':{'llvm-readobj':sha(readobj),'llvm-objdump':sha(TOOLCHAIN/'bin/llvm-objdump')},
 'scope':'Static PE/AVX2 inspection only'},indent=2)+'\n')
shutil.copyfile(BUILD/'forge.exe',FOLDER/'forge-6.4.3-ryzen-9850x3d.exe')
shutil.copyfile(BUILD/'forge_tests.exe',FOLDER/'forge_tests.exe')
shutil.copyfile(BUILD/'forge_tt_tests.exe',FOLDER/'forge_tt_tests.exe')
shutil.copyfile(SOURCE/'LICENSE',FOLDER/'LICENSE')
shutil.copyfile(BUILD_EVIDENCE/'production-hashes.json',FOLDER/'source-hashes.json')
fixture_commit=runtime['fixture_commit']
provenance={'engine_version':'6.4.3 candidate','production_source_commit':build['production_commit'],
 'production_source_url':'https://github.com/couns0538-sketch/dwqww/tree/'+build['production_commit'],
 'production_source_sha256':load(BUILD_EVIDENCE/'production-hashes.json'),
 'fixture_commit':fixture_commit,'fixture_file':'tests/tt_coherence_tests.cpp',
 'fixture_sha256':sha(SOURCE/'tests/tt_coherence_tests.cpp'),
 'fixture_source_url':'https://github.com/couns0538-sketch/dwqww/blob/'+fixture_commit+'/tests/tt_coherence_tests.cpp',
 'compiler':build['compiler'],'flags':'Release -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static',
 'target':'Windows x64 Ryzen 7 9850X3D / Zen5','build_jobs':1,
 'binaries':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in FOLDER.glob('*.exe')},
 'windows_checks':'Core, coherent-TT, frozen-source UCI and ponder under Wine10; all exit0',
 'simd':runtime['simd'],'binary_and_tool_hashes_unchanged_during_checks':True,
 'validation_scope':'TT correctness candidate; no accepted speed or Elo gain',
 'speed_evidence':'Shared-VM A/A throughput was too noisy; performance is inconclusive',
 'native_windows_tested':False,'physical_ryzen_tested':False,'accepted_elo_gain':None,
 'stockfish_superiority_proven':False,'evidence_directory':'validation/tt-coherence-20261019/windows/',
 'windows_compile_flags_record':(BUILD/'CMakeFiles/forge_core.dir/flags.make').read_text(),
 'windows_link_record':(BUILD/'CMakeFiles/forge.dir/link.txt').read_text()}
(FOLDER/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
(FOLDER/'README.txt').write_text('''Forge 6.4.3 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.3-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5; it is not a universal x86 build.

This candidate fixes a demonstrated shared transposition-table data race.
Readers now consume complete entry copies protected by striped locks.
The table no longer exposes mutable entries to search workers. Generation
changes occur after search workers are joined. Previous promotion, stalemate, clock,
TT-tag and AVX2 changes remain. Evaluation weights are unchanged.

Windows core, coherent-TT, UCI and ponder regression checks passed under
Wine10 using the frozen 6.4.3 source tools. Emitted 256-bit clamp/multiply/add
instructions were checked, with no fused arithmetic found. Optional test
executables contain the core and coherent-TT checks. Source/build identity
and exact test-fixture hashes are recorded in provenance.json.

This is a TT correctness candidate. The shared-VM speed calibration was
too noisy to establish a performance result. No accepted Elo gain exists.
Native Windows and physical Ryzen validation remain pending. Full-strength
Stockfish superiority is unproven. Wine correctness is not native Elo.

The separate 6.4.2 portable match-validation bundle remains a frozen 6.4.2
experiment; it does not test this 6.4.3 executable automatically. This package
does not alter that bundle, older releases, or their evidence.

Source: production df5d839a6a03f705310bb958601375fa9411e810;
TT regression fixture 77ee53bdae40fbffee42be406b73f245f4434993.
See source-hashes.json, provenance.json and SHA256SUMS.
''')
(FOLDER/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(FOLDER.iterdir()) if p.is_file()))
with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for path in sorted(FOLDER.iterdir()):z.write(path,FOLDER.name+'/'+path.name)
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    assert set(z.namelist())=={FOLDER.name+'/'+p.name for p in FOLDER.iterdir() if p.is_file()}
    for path in FOLDER.iterdir():assert z.read(FOLDER.name+'/'+path.name)==path.read_bytes()
    for line in (FOLDER/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);assert hashlib.sha256(z.read(FOLDER.name+'/'+name)).hexdigest()==expected
    assert hashlib.sha256(z.read(FOLDER.name+'/forge-6.4.3-ryzen-9850x3d.exe')).hexdigest()==runtime['input_sha256_after']['forge.exe']
report={'status':'packaged_and_verified','artifact':str(ARCHIVE.relative_to(REPO)),
 'sha256':sha(ARCHIVE),'bytes':ARCHIVE.stat().st_size,'source_commit':build['production_commit'],
 'fixture_commit':fixture_commit,'engine_sha256':sha(FOLDER/'forge-6.4.3-ryzen-9850x3d.exe'),
 'scope':'Wine correctness only; speed inconclusive; native hardware/Elo unproven'}
(EVIDENCE/'artifact.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(Path(__file__),EVIDENCE/'package-driver.py')
(EVIDENCE/'README.md').write_text('Windows 6.4.3 candidate checks passed under Wine only: core, coherent-TT, frozen-source UCI and ponder. SIMD inspection found 256-bit clamp/multiply/add and no fused arithmetic. Source, binaries and test-tool hashes stayed unchanged. Exact commands, all logs, fixture delta, compiler/link flags and a gzip of the full disassembly are preserved here. Production is df5d839; the fixture matches 77ee53b.\n\nThis is TT correctness evidence. Speed calibration was inconclusive; native Windows, physical Ryzen, Elo advancement and Stockfish superiority remain unproven. No timed games or Wine A/A repeats were run.\n')
print(json.dumps(report,indent=2))
