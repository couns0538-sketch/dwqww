from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path('/workspace/.cloud-setup/windows-validation-bundle with spaces')
REPO=Path('/workspace/dwqww')
OUT=REPO/'releases/forge-6.4.2-windows-validation-bundle.zip'
BASE=REPO/'validation/underpromotions-9850x3d/windows-native-readiness'
EVIDENCE=BASE/'attempt2'
RUN=Path('/workspace/.cloud-setup/windows-native-readiness-attempt2')
PREFIX='forge-6.4.2-windows-validation-bundle/'
EXPECTED_MANIFEST='576cf088dda67c060934f1f533fa8a69a5d5c4642a36bb2af6b01103c45296e8'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(ROOT/'manifest.json')==EXPECTED_MANIFEST
manifest=json.loads((ROOT/'manifest.json').read_text())
paths={p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file()}
assert set(paths)==set(manifest['files'])|{'manifest.json'}
for name,digest in manifest['files'].items():assert sha(paths[name])==digest
assert not OUT.exists() and not EVIDENCE.exists()
with zipfile.ZipFile(OUT,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for name,path in sorted(paths.items()):
        entry=zipfile.ZipInfo(PREFIX+name,date_time=(2026,10,19,0,0,0))
        entry.compress_type=zipfile.ZIP_DEFLATED
        entry.external_attr=(0o100755 if name.endswith(('.exe','.cmd')) else 0o100644)<<16
        archive.writestr(entry,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

# Inspect packaged bytes rather than trusting the write input manifest.
with zipfile.ZipFile(OUT) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist())==len(set(archive.namelist()))==2346
    assert set(archive.namelist())=={PREFIX+name for name in paths}
    packed_manifest=archive.read(PREFIX+'manifest.json')
    assert hashlib.sha256(packed_manifest).hexdigest()==EXPECTED_MANIFEST
    for name,path in paths.items():
        data=archive.read(PREFIX+name)
        assert data==path.read_bytes()
        if name!='manifest.json':assert hashlib.sha256(data).hexdigest()==manifest['files'][name]
    candidate=manifest['provenance']['candidate']
    for name,digest in candidate['source_files_sha256'].items():
        assert hashlib.sha256(archive.read(PREFIX+'sources/candidate-6.4.2/'+name)).hexdigest()==digest
    critical={name:hashlib.sha256(archive.read(PREFIX+name)).hexdigest()
              for name in ('engine/candidate.exe','engine/original-6.4.exe','fastchess/fastchess.exe',
                           'runtime/python.exe','windows_validate.py','pgn_stats.py')}

EVIDENCE.mkdir(parents=True)
for source,name in [
    (RUN.with_name(RUN.name+'.zip'),'original-results.zip'),
    (RUN.parent/'windows-native-readiness-audit-attempt1.json','independent-audit.json'),
    (RUN.parent/'audit-native-readiness-attempt2.py','independent-audit.py'),
    (RUN.parent/'windows-native-readiness-launch-attempt1.json','launch.json'),
    (RUN.parent/'windows-validation-bundle-freeze-attempt2.json','bundle-freeze.json'),
    (RUN/'result.json','result.json'),(RUN/'protocol.json','protocol.json'),
    (RUN/'aa/result.json','aa-result.json'),(RUN/'aa/command.json','command.json'),
    (RUN/'aa/console.txt','console.txt'),(RUN/'aa/games.pgn','games.pgn'),
    (RUN/'aa/state.json','state.json')]:
    shutil.copyfile(source,EVIDENCE/name)
report={'status':'passed','artifact':str(OUT.relative_to(REPO)),
        'artifact_bytes':OUT.stat().st_size,'artifact_sha256':sha(OUT),
        'manifest_sha256':EXPECTED_MANIFEST,'archive_prefix':PREFIX,
        'manifest_listed_files':len(manifest['files']),'archive_regular_files':len(paths),
        'all_crc_and_membership_checks_passed':True,'every_packaged_byte_matches_frozen_stage':True,
        'every_manifest_checksum_verified':True,'candidate_production_source_hashes_verified':True,
        'source_commit':candidate['engine_source_commit'],'critical_sha256':critical,
        'readiness_results_zip_sha256':sha(EVIDENCE/'original-results.zip'),
        'readiness_scope':'Wine readiness only; no native Windows, physical Ryzen or Elo result',
        'script_sha256':sha(Path(__file__))}
(BASE/'bundle-verification.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(Path(__file__),BASE/'package-and-verify.py')
readiness=json.loads((EVIDENCE/'result.json').read_text())
assert readiness['status']=='aa_passed' and readiness['equal_clock_gain_established'] is False
readme=f'''The [offline Windows validation bundle](../../../releases/{OUT.name}) is packaged and checked. Extract it into an ASCII-only directory, then run `run-readiness.cmd` for readiness or `run-validation.cmd` for the native timed experiment. Spaces in the parent directory were tested. No installation or credentials are required.

The corrected bundle contains **{len(paths):,} regular files**: {len(manifest['files']):,} entries in its manifest plus the root manifest itself. Every ZIP CRC, member name, frozen file hash, and candidate production-source hash passed inspection. Candidate executable SHA256 is `{critical['engine/candidate.exe']}`; its source commit is `{candidate['engine_source_commit']}`.

| Artifact | SHA256 |
| --- | --- |
| Bundle ZIP ({OUT.stat().st_size:,} bytes) | `{sha(OUT)}` |
| Root manifest | `{EXPECTED_MANIFEST}` |
| Attempt 2 results ZIP ({(EVIDENCE/'original-results.zip').stat().st_size:,} bytes) | `{sha(EVIDENCE/'original-results.zip')}` |

Attempt 2 passed under **Wine only**: 8 normal games, 4 unique deterministic color-swapped pairs, W/D/L 3/2/3 and native pentanomial counts `[0, 0, 4, 0, 0]`. All {len(paths):,} frozen inputs were unchanged. Independent PGN, schedule, source/archive, manifest and results-ZIP audits passed. This establishes readiness, with no native Windows, physical Ryzen, Elo or Stockfish result. See [attempt 2 audit](attempt2/independent-audit.json), [protocol](attempt2/protocol.json), [results](attempt2/result.json) and [packaged-byte verification](bundle-verification.json). The original results ZIP retains the complete UCI trace; readable command, PGN, console and native state are also included here.

The second fixed-node readiness run overlapped an authorized `-j2` TSan compilation after four games had completed. This is recorded in its launch evidence. There is no speed or timing-stability claim.

An assembly defect was found before release: the first manifest omitted two unchanged, source-only nested `tools/openings/manifest.json` files because the freeze helper filtered that basename everywhere. The earlier whole-bundle completeness claim was invalid; its normal A/A result and declared-input checks remain valid. [Attempt 1](attempt1/) preserves the exact original manifest, original results ZIP, report, protocol, audit and faulty helper. [The discrepancy](manifest-discrepancy.json) and [repair](manifest-repair.json) record the correction. Only the root manifest metadata changed; engine, runtime, runner and opening bytes did not. A fresh readiness attempt was then required and passed. No games are pooled.

The native experiment gates four fixed-node A/A pairs, then eight timed pilot pairs, then serial paired logistic SPRT H0=0/H1=5 Elo, alpha=beta=.05, capped at 5,000 pairs. It uses 10+0.1 clocks, Threads=1, Hash=32 MiB, OwnBook/Ponder=false, Move Overhead=100 ms, restart per game, strict handling and no adjudication. Any fault invalidates the attempt. H1 requires an explicit native decision and an independent paired likelihood crossing; it does not establish gain >=5 Elo. A cap without a boundary is inconclusive. The complete run can take several days and retain multiple gigabytes of traces. No native timed run has been performed here.

The opponent is the unmodified **original znver4 Windows release PE** from the user's exact Forge 6.4.0 ZIP; the candidate is the new Zen5 build. This compares complete releases, including compiler and architecture-flag differences. It does not isolate one source change. The original release's source-to-binary build provenance was not independently authenticated, although its PE and bundled original source match the archive. Both sources, compiler/build records, portable Python, Fastchess source/licences and the 4/8/5,000 fresh disjoint opening schedule are inside the bundle. Native Elo advancement remains pending.
'''
(BASE/'README.md').write_text(readme)
print(json.dumps(report,indent=2))
