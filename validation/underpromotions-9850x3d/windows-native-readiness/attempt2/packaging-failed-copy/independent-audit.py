from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import re
import subprocess
import zipfile

ROOT = Path('/workspace/.cloud-setup/windows-validation-bundle with spaces')
RUN = Path('/workspace/.cloud-setup/windows-native-readiness-attempt2')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
validator=load_module(ROOT/'windows_validate.py','validator_audit')
manifest,frozen=validator.load_bundle(ROOT)
assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==set(manifest['files'])|{'manifest.json'}
protocol=json.loads((RUN/'protocol.json').read_text())
result=json.loads((RUN/'result.json').read_text())
phase=json.loads((RUN/'aa/result.json').read_text())
assert result['status']==phase['status']=='aa_passed'
assert phase['exit_code']==0 and result['equal_clock_gain_established'] is False
assert result['final_input_sha256']==protocol['input_sha256']==frozen
assert set(result['phases'])=={'aa'}
assert protocol['host']['wine_detected'] is True
assert protocol['fastchess_version'].endswith(validator.PIN)
assert phase==result['phases']['aa']
for name,digest in phase['outputs_sha256'].items():assert sha(RUN/'aa'/name)==digest

# Independent parser from the archived quality-result auditor, not pgn_stats.
independent=load_module(Path('/workspace/dwqww/validation/clock-safety-9850x3d/tests/audit-quality-result.py'),'independent_parser')
games=independent.parse_pgn((RUN/'aa/games.pgn').read_text())
assert len(games)==8
grouped=collections.defaultdict(list)
for game in games:grouped[game['tags']['Round']].append(game)
schedule=(ROOT/'openings/aa.epd').read_text().splitlines()
assert set(grouped)=={'1','2','3','4'}
wdl=[0,0,0]
for number,expected in enumerate(schedule,1):
    pair=grouped[str(number)];assert len(pair)==2
    one,two=pair
    assert one['moves']==two['moves'] and one['tags']['Result']==two['tags']['Result']
    assert one['tags']['White']==two['tags']['Black'] and one['tags']['Black']==two['tags']['White']
    for game in pair:
        tags=game['tags'];assert set((tags['White'],tags['Black']))=={'Candidate','Baseline'}
        assert tags['Termination']=='normal' and ' '.join(tags['FEN'].split()[:4])==expected
        score=independent.OUTCOMES[tags['Result']]
        if tags['Black']=='Candidate':score=2-score
        wdl[2-score]+=1
assert wdl==[3,2,3]
console=(RUN/'aa/console.txt').read_text()
assert sorted(map(int,re.findall(r'^Finished game (\d+) ',console,re.M)))==list(range(1,9))
assert sorted(map(int,re.findall(r'^Started game (\d+) ',console,re.M)))==list(range(1,9))
assert console.count('Finished match')==1 and 'Ptnml(0-2): [0, 0, 4, 0, 0]' in console
assert not re.search(r'^\[(WARN|ERR|FATAL)\s*\]',(RUN/'aa/fastchess.log').read_text(),re.M)

selection=json.loads((ROOT/'provenance/openings-selection.json').read_text())
corpus=(ROOT/'sources/candidate-6.4.2/tools/openings/forge-10000.epd')
assert sha(corpus)==selection['corpus_sha256']
excluded=set((ROOT/'provenance/prior-selected.epd').read_text().splitlines())
assert len(excluded)==selection['excluded_unique_positions']==961
for name,record in selection['prior_registries'].items():assert sha(Path(name))==record['sha256']
eligible={' '.join(line.split()[:4]) for line in corpus.read_text().splitlines() if line.split()[3]=='-'}-excluded
chosen=sorted(eligible,key=lambda value:hashlib.sha256(f'{selection["seed"]}\n{value}'.encode()).digest())[:5012]
assert (ROOT/'openings/selected.epd').read_text().splitlines()==chosen
for phase_name in ('aa','pilot','sprt'):
    record=selection['phase_selections'][phase_name];path=ROOT/'openings'/(phase_name+'.epd')
    assert sha(path)==record['sha256']
    assert path.read_text().splitlines()==chosen[record['start']:record['start']+record['pairs']]

candidate=manifest['provenance']['candidate']
for name,digest in candidate['source_files_sha256'].items():
    data=subprocess.check_output(['git','-C','/workspace/dwqww','show',candidate['engine_source_commit']+':'+name])
    assert hashlib.sha256(data).hexdigest()==digest==sha(ROOT/'sources/candidate-6.4.2'/name)
archive=Path('/workspace/dwqww/chess-engine-forge-6.4.0.zip')
original=manifest['provenance']['original'];assert sha(archive)==original['archive_sha256']
with zipfile.ZipFile(archive) as z:
    assert hashlib.sha256(z.read(original['member'])).hexdigest()==sha(ROOT/'engine/original-6.4.exe')
    for path in (ROOT/'sources/original-6.4.0').rglob('*'):
        if path.is_file():
            assert path.read_bytes()==z.read('chess-engine-forge-6.4.0/'+path.relative_to(ROOT/'sources/original-6.4.0').as_posix())

results_zip=RUN.with_name(RUN.name+'.zip')
with zipfile.ZipFile(results_zip) as z:
    assert z.testzip() is None
    assert set(z.namelist())=={p.relative_to(RUN).as_posix() for p in RUN.rglob('*') if p.is_file()}
    for name in z.namelist():assert z.read(name)==(RUN/name).read_bytes()
report={'audit_status':'passed','scope':'Wine readiness only; no native Windows, physical Ryzen or Elo result',
        'bundle':str(ROOT),'run_directory':str(RUN),'manifest_sha256':sha(ROOT/'manifest.json'),
        'bundle_files':len(manifest['files']),'frozen_inputs':len(frozen),
        'statistics':phase['statistics'],'independent_wdl':wdl,'independent_pairs':len(grouped),
        'all_input_hashes_unchanged':True,'independent_pgn_and_opening_audit_passed':True,
        'source_candidate_commit':candidate['engine_source_commit'],
        'original_source_and_release_pe_match_user_zip':True,
        'final_result_sha256':sha(RUN/'result.json'),'results_zip':str(results_zip),
        'results_zip_sha256':sha(results_zip),'results_zip_bytes':results_zip.stat().st_size,
        'script_sha256':sha(Path(__file__))}
output=RUN.parent/'windows-native-readiness-audit-attempt2.json'
output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
