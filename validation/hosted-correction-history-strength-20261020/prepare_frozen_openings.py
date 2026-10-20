#!/usr/bin/env python3
"""Reserve once from verified corpus cache; never replay the full book again."""
import hashlib,json,subprocess
from pathlib import Path
import chess
REPO=Path(__file__).resolve().parents[2];PACKAGE=REPO/'.github/hosted-correction-history-strength';SEED='20261020-correction-history-v1';RUNTIME_SEED=20261026
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def main():
 assert not (PACKAGE/'provenance/reservation-frozen.json').exists(),'Already frozen'
 originpath=REPO/'.github/hosted-promotion-see-strength/provenance/openings-selection.json';originraw=originpath.read_bytes();previous=json.loads(originraw);source=previous['source'];cacheorigin=previous['book_legal_cache'];cachepath=PACKAGE/'provenance'/Path(cacheorigin['path']).name;raw=cachepath.read_bytes();assert sha(raw)==cacheorigin['sha256']=='42735af2eb7ef9a43695de69b256e519075e3a30ef6a565febcabf0abd2bdcff';assert raw==(REPO/cacheorigin['path']).read_bytes();cache=json.loads(raw)
 assert cache['source']==source and cache['cache_key_archive_sha256']==source['archive_sha256'] and cache['status']=='FULL_LEGAL_REPLAY_COMPLETE';assert cache['statistics']=={'games':34700,'strict_ep_none':31603,'actual_ep_excluded':3097};assert len(cache['positions'])==31603
 generator=REPO/'validation/hosted-pin-mask-strength-20261020/prepare_frozen_openings.py';assert sha(generator.read_bytes())==cache['generator_sha256'];proofpath=REPO/'validation/hosted-pin-mask-strength-20261020/opening-check.json';proofraw=proofpath.read_bytes();proof=json.loads(proofraw);assert proof['status']=='passed' and proof['book_cache_full_legal_replay']==34700 and proof['book_cache_sha256']==cacheorigin['sha256'];assert sha((PACKAGE/'provenance/8moves_v3.pgn.zip').read_bytes())==source['archive_sha256']
 oldexpath=REPO/'.github/hosted-promotion-see-strength/provenance/historical-exclusions.json';oldexraw=oldexpath.read_bytes();assert sha(oldexraw)==previous['historical_exclusions_sha256'];oldex=json.loads(oldexraw);excluded=set(oldex['excluded_canonical_positions']);sources=dict(oldex['historical_sources_sha256'])
 for path,digest in sources.items():assert sha((REPO/path).read_bytes())==digest,path
 original=json.loads((REPO/'.github/hosted-tt-strength/provenance/openings-selection.json').read_text());assert len(original['registries'])==42
 for row in original['registries']:assert sha(Path(row['path']).read_bytes())==row['sha256']
 def add(fen):
  fen=' '.join(fen.split()[:4]);board=chess.Board(fen+' 0 1');excluded.add(fen);excluded.add(' '.join(board.fen(en_passant='legal').split()[:4]))
 found=subprocess.check_output(['rg','--files','--hidden','--no-ignore','-g','*.epd','-g','!.git/**'],cwd=REPO,text=True).splitlines()
 for relative in sorted(found):
  path=REPO/relative
  if PACKAGE in path.parents:continue
  raw=path.read_bytes();digest=sha(raw)
  if relative in sources:assert digest==sources[relative];continue
  sources[relative]=digest
  for line in raw.decode().splitlines():
   if line.strip() and not line.lstrip().startswith('#'):add(line)
 cohorts={}
 for name in ('hosted-confirmation','hosted-nnue-strength','hosted-tt-strength','hosted-pin-see-strength','hosted-pin-mask-strength','hosted-promotion-see-strength'):
  path=REPO/'.github'/name/'provenance/openings-selection.json';raw=path.read_bytes();report=json.loads(raw);fens=set()
  if 'prospective_selection' in report:fens|={row['fen'] for row in report['prospective_selection']['selections']}
  for rows in report.get('selections',{}).values():fens|={row['fen'] for row in rows}
  fens|=set(report.get('exclusions',{}).get('canonical_positions',[]))
  for fen in fens:add(fen)
  sources[path.relative_to(REPO).as_posix()]=sha(raw);cohorts[name]={'reserved_positions':len(fens),'canonical_positions':sorted(fens)}
 assert all(cohorts[name]['reserved_positions']==132 for name in ('hosted-pin-see-strength','hosted-pin-mask-strength','hosted-promotion-see-strength'))
 snapshot={'historical_sources_sha256':sources,'excluded_canonical_positions':sorted(excluded),'reserved_cohorts':cohorts,'original_registry_count':42,'reused_verified_snapshot_path':oldexpath.relative_to(REPO).as_posix(),'reused_verified_snapshot_sha256':sha(oldexraw)};expath=PACKAGE/'provenance/historical-exclusions.json';expath.write_text(json.dumps(snapshot,indent=2)+'\n')
 eligible={fen:index for fen,index in cache['positions'].items() if fen not in excluded};selected=sorted(eligible,key=lambda fen:hashlib.sha256((SEED+'\n'+fen).encode()).digest())[:260];assert len(set(selected))==260 and not set(selected)&excluded;runtime={};outputs={}
 for phase,fens in [('aa',selected[:4]),('sprt',selected[4:])]:
  raw=('\n'.join(fens)+'\n').encode('ascii');path=PACKAGE/'openings'/(phase+'.epd');path.write_bytes(raw);outputs[phase]={'path':path.relative_to(REPO).as_posix(),'sha256':sha(raw),'positions':len(fens)}
  ordered=sorted(fens,key=lambda fen:hashlib.sha256((str(RUNTIME_SEED)+'\n'+fen).encode()).digest());raw=('\n'.join(ordered)+'\n').encode('ascii');(PACKAGE/'provenance'/('runtime-'+phase+'.epd')).write_bytes(raw);runtime[phase]={'seed':RUNTIME_SEED,'ordered_fens':ordered,'selected_epd_sha256':sha(raw),'positions':len(fens)}
 cacheinfo={'path':cachepath.relative_to(REPO).as_posix(),'sha256':sha(cachepath.read_bytes()),'key':source['archive_sha256'],'origin_path':cacheorigin['path'],'origin_generator_path':generator.relative_to(REPO).as_posix(),'origin_generator_sha256':cache['generator_sha256'],'origin_full_replay_proof_path':proofpath.relative_to(REPO).as_posix(),'origin_full_replay_proof_sha256':sha(proofraw),'origin_selection_path':originpath.relative_to(REPO).as_posix(),'origin_selection_sha256':sha(originraw),'full_corpus_replays_this_preparation':0}
 report={'source':source,'book_legal_cache':cacheinfo,'statistics':dict(cache['statistics'],historical_reserved_excluded=len(cache['positions'])-len(eligible)),'eligible_unique':len(eligible),'historical_exclusions_sha256':sha(expath.read_bytes()),'prospective_selection':{'seed':SEED,'outputs':outputs,'selections':[{'fen':fen,'source_game_1based':eligible[fen]} for fen in selected]}}
 (PACKAGE/'provenance/openings-selection.json').write_text(json.dumps(report,indent=2)+'\n');(PACKAGE/'provenance/runtime-order.json').write_text(json.dumps(runtime,indent=2)+'\n');marker={'status':'RESERVED_ONCE_NO_LAUNCH','selector_seed':SEED,'runtime_seed':RUNTIME_SEED,'selection_sha256':sha((PACKAGE/'provenance/openings-selection.json').read_bytes()),'book_cache_sha256':cacheinfo['sha256'],'full_corpus_replays_this_preparation':0,'statistics':report['statistics'],'engine_executions':0};(PACKAGE/'provenance/reservation-frozen.json').write_text(json.dumps(marker,indent=2)+'\n');print(json.dumps(marker))
if __name__=='__main__':main()
