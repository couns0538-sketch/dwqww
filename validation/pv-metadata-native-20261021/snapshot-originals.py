#!/usr/bin/env python3
"""Hash complete frozen originals after finite gates; no engines/builds/Git."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,stat
HERE=Path(__file__).resolve().parent
BASE=Path('/workspace/.cloud-setup')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def item(path):return {'sha256':sha(path),'bytes':path.stat().st_size,'mode':stat.S_IMODE(path.stat().st_mode)}
clear=load(HERE/'ROOT-CLEARANCE.json')
assert clear.get('authorized') is True and len(clear['source_commit'])==40, 'Root clearance required'
for profile in ['release','asan','tsan']:
    receipt=load(HERE/('frozen-'+profile+'-attempt1/summary.json'))
    assert receipt['status']=='PASS' and receipt['source_commit']==clear['source_commit'] and len(receipt['ctest_names'])==14
assert load(HERE/'release-signature-wrapper-attempt1/summary.json')['status']=='PASS'
assert load(HERE/'active-uci-wrapper-attempt1/COMMAND.json')['status']=='PASS'
output=HERE/'ORIGINALS-FINAL-SHA256.json'
assert not output.exists(), 'Refusing previous snapshot'
roots={'source':BASE/'pv-metadata-native-source',**{p:BASE/('pv-metadata-native-'+p) for p in ['release','asan','tsan']}}
trees={}
for label,root in roots.items():
    paths=sorted(root.rglob('*'))
    assert not any(p.is_symlink() for p in paths), 'Symlink not permitted in original inventory'
    files={str(p.relative_to(root)):item(p) for p in paths if p.is_file()}
    assert len(files)==77 if label=='source' else len(files)>0
    trees[label]={'root':str(root),'files':files,'directory_modes':{'.':stat.S_IMODE(root.stat().st_mode),**{str(p.relative_to(root)):stat.S_IMODE(p.stat().st_mode) for p in paths if p.is_dir()}}}
protocol=load(HERE/'RELEASE-SIGNATURE-PROTOCOL.json')
singles={'baseline_engine':Path(protocol['baseline_engine']),'baseline_core':Path(protocol['baseline_core']),
 'baseline_nnue_object':BASE/'nearest-pawn-native-release/CMakeFiles/forge_core.dir/src/nnue.cpp.o',
 'baseline_source_manifest':HERE.parent/'nearest-pawn-native-20261020/frozen-source-2e151d0-files.json',
 'baseline_release_receipt':HERE.parent/'nearest-pawn-native-20261020/frozen-release-attempt1/summary.json'}
for name in protocol['protected_nonsearch_source_sha256']:singles['baseline_nonsearch/'+name]=Path(protocol['baseline_source_root'])/name
compiler=Path('/usr/bin/g++-14')
record={'recorded_utc':datetime.now(timezone.utc).isoformat(),'source_commit':clear['source_commit'],'engines_or_builds_executed_for_snapshot':False,
 'trees':trees,'single_files':{label:{'path':str(p),**item(p)} for label,p in singles.items()},
 'compiler':{'path':str(compiler),'resolved_path':str(compiler.resolve()),'sha256':sha(compiler)},
 'scope':'Complete native source and three builds, actual consumed parent21 originals; no speed or Elo inference.'}
with output.open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps({'status':'SNAPSHOT_SAVED','file_counts':{k:len(v['files']) for k,v in trees.items()},'sha256':sha(output),'engines_or_builds_executed_for_snapshot':False}))
