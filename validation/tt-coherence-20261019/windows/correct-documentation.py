from pathlib import Path
import hashlib
import json
import shutil
import zipfile

REPO=Path('/workspace/dwqww')
FOLDER=REPO/'releases/forge-6.4.3-candidate-windows-zen5'
ZIP=FOLDER.with_name(FOLDER.name+'.zip')
EVIDENCE=REPO/'validation/tt-coherence-20261019/windows'
OLD=EVIDENCE/'documentation-correction'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='6a33a3ec64af0f46a5fc5c5191e040cebcd2aba002022384b820aedea8f3bd91'
assert sha(ZIP)==EXPECTED and not OLD.exists()
OLD.mkdir()
for source in (FOLDER/'README.txt',FOLDER/'SHA256SUMS',EVIDENCE/'artifact.json',EVIDENCE/'package-driver.py'):
    shutil.copyfile(source,OLD/source.name)
original=Path('/workspace/.cloud-setup/forge-6.4.3-documentation-attempt1.zip')
assert not original.exists();shutil.copyfile(ZIP,original)
old_phrase='''Readers now consume a coherent atomic entry snapshot, and generation values
are captured for each search worker.'''
new_phrase='''Readers now consume complete entry copies protected by striped locks.
The table no longer exposes mutable entries to search workers. Generation
changes occur after search workers are joined.'''
readme=(FOLDER/'README.txt').read_text();assert old_phrase in readme
(FOLDER/'README.txt').write_text(readme.replace(old_phrase,new_phrase))
for helper in (Path('/workspace/.cloud-setup/package-windows-6.4.3.py'),EVIDENCE/'package-driver.py'):
    text=helper.read_text();assert old_phrase in text
    helper.write_text(text.replace(old_phrase,new_phrase))
(FOLDER/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(FOLDER.iterdir())
                                      if p.is_file() and p.name!='SHA256SUMS'))
# Retain original packaging bytes, then atomically replace only this unpublished
# candidate ZIP after inspecting the replacement.
temporary=ZIP.with_suffix('.corrected.tmp')
with zipfile.ZipFile(temporary,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for path in sorted(FOLDER.iterdir()):z.write(path,FOLDER.name+'/'+path.name)
with zipfile.ZipFile(temporary) as z:
    assert z.testzip() is None
    assert set(z.namelist())=={FOLDER.name+'/'+p.name for p in FOLDER.iterdir() if p.is_file()}
    for p in FOLDER.iterdir():assert z.read(FOLDER.name+'/'+p.name)==p.read_bytes()
    for line in (FOLDER/'SHA256SUMS').read_text().splitlines():
        expected,name=line.split('  ',1);assert hashlib.sha256(z.read(FOLDER.name+'/'+name)).hexdigest()==expected
    assert hashlib.sha256(z.read(FOLDER.name+'/forge-6.4.3-ryzen-9850x3d.exe')).hexdigest()=='142cbd41fceafabfef59cc405517bb4b14c4f9a3b3f15a908a43ec52926c1cee'
temporary.replace(ZIP)
record={'status':'documentation_corrected_before_publication','old_zip_sha256':EXPECTED,
        'old_zip_bytes':original.stat().st_size,'old_zip_preserved_external':str(original),
        'old_readme_preserved':'documentation-correction/README.txt',
        'cause':'README incorrectly described atomic snapshots and per-worker generation; df5 uses striped mutex-protected copies and quiescent generation changes',
        'new_zip_sha256':sha(ZIP),'new_zip_bytes':ZIP.stat().st_size,
        'engine_test_and_source_bytes_unchanged':True,'changes':'README wording and its SHA256SUMS digest only'}
(OLD/'diagnosis.json').write_text(json.dumps(record,indent=2)+'\n')
artifact=json.loads((EVIDENCE/'artifact.json').read_text());artifact.update(sha256=sha(ZIP),bytes=ZIP.stat().st_size,
 previous_unpublished_sha256=EXPECTED,documentation_correction_record='documentation-correction/diagnosis.json')
(EVIDENCE/'artifact.json').write_text(json.dumps(artifact,indent=2)+'\n')
shutil.copyfile(Path(__file__),EVIDENCE/'correct-documentation.py')
print(json.dumps(artifact,indent=2))
