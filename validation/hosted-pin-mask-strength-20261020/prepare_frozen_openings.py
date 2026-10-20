#!/usr/bin/env python3
"""One fresh reservation, retaining a reusable legal corpus cache keyed by book SHA."""
from collections import Counter
import hashlib,io,json,zipfile
from pathlib import Path
import chess,chess.pgn
REPO=Path(__file__).resolve().parents[2];PACKAGE=REPO/'.github/hosted-pin-mask-strength'
SEED='20261020-pin-mask-v1';RUNTIME_SEED=20261024
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def main():
 assert not (PACKAGE/'provenance/reservation-frozen.json').exists(),'Already frozen'
 previous=json.loads((REPO/'.github/hosted-pin-see-strength/provenance/openings-selection.json').read_text());source=previous['source'];archive=(PACKAGE/'provenance/8moves_v3.pgn.zip').read_bytes();assert sha(archive)==source['archive_sha256']
 cachepath=PACKAGE/'provenance'/('book-legal-cache-'+source['archive_sha256']+'.json')
 if cachepath.exists():
  cache=json.loads(cachepath.read_text());assert cache['source']==source and cache['status']=='FULL_LEGAL_REPLAY_COMPLETE';assert cache['statistics']=={'games':34700,'strict_ep_none':31603,'actual_ep_excluded':3097}
 else:
  with zipfile.ZipFile(io.BytesIO(archive)) as z:raw=z.read(source['zip_member'])
  assert sha(raw)==source['pgn_sha256'];stream=io.StringIO(raw.decode('utf-8-sig'));stats=Counter();positions={};seen=set()
  while (board:=chess.pgn.read_game(stream,Visitor=chess.pgn.BoardBuilder)) is not None:
   stats['games']+=1;assert board.ply()==16 and board.is_valid() and board.legal_moves.count()>0;fen=' '.join(board.fen(en_passant='fen').split()[:4]);assert fen not in seen;seen.add(fen)
   if board.ep_square is not None:stats['actual_ep_excluded']+=1;continue
   stats['strict_ep_none']+=1;assert fen.split()[3]=='-';positions[fen]=stats['games']
  assert dict(stats)=={'games':34700,'strict_ep_none':31603,'actual_ep_excluded':3097}
  cache={'status':'FULL_LEGAL_REPLAY_COMPLETE','cache_key_archive_sha256':source['archive_sha256'],'source':source,'statistics':dict(stats),'python_chess_version':chess.__version__,'generator_sha256':sha(Path(__file__).read_bytes()),'positions':{fen:positions[fen] for fen in sorted(positions)},'engine_executions':0}
  cachepath.write_text(json.dumps(cache,indent=2)+'\n')
 excluded=set();sources={}
 def add(fen):
  fen=' '.join(fen.split()[:4]);board=chess.Board(fen+' 0 1');excluded.add(fen);excluded.add(' '.join(board.fen(en_passant='legal').split()[:4]))
 original=json.loads((REPO/'.github/hosted-tt-strength/provenance/openings-selection.json').read_text())
 paths={Path(row['path']) for row in original['registries']}
 for row in original['registries']:assert sha(Path(row['path']).read_bytes())==row['sha256']
 paths|={p for p in REPO.rglob('*.epd') if PACKAGE not in p.parents and '.git' not in p.parts}
 for path in sorted(paths,key=lambda p:p.as_posix()):
  raw=path.read_bytes();key=path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.as_posix();sources[key]=sha(raw)
  for line in raw.decode().splitlines():
   if line.strip() and not line.lstrip().startswith('#'):add(line)
 cohorts={}
 for name in ('hosted-confirmation','hosted-nnue-strength','hosted-tt-strength','hosted-pin-see-strength'):
  path=REPO/'.github'/name/'provenance/openings-selection.json';raw=path.read_bytes();report=json.loads(raw);fens=set()
  if 'prospective_selection' in report:fens|={row['fen'] for row in report['prospective_selection']['selections']}
  for rows in report.get('selections',{}).values():fens|={row['fen'] for row in rows}
  fens|=set(report.get('exclusions',{}).get('canonical_positions',[]))
  for fen in fens:add(fen)
  sources[path.relative_to(REPO).as_posix()]=sha(raw);cohorts[name]={'reserved_positions':len(fens),'canonical_positions':sorted(fens)}
 assert cohorts['hosted-pin-see-strength']['reserved_positions']==132
 snapshot={'historical_sources_sha256':sources,'excluded_canonical_positions':sorted(excluded),'reserved_cohorts':cohorts,'original_registry_count':len(original['registries'])};expath=PACKAGE/'provenance/historical-exclusions.json';expath.write_text(json.dumps(snapshot,indent=2)+'\n')
 eligible={fen:index for fen,index in cache['positions'].items() if fen not in excluded};selected=sorted(eligible,key=lambda fen:hashlib.sha256((SEED+'\n'+fen).encode()).digest())[:132];assert len(set(selected))==132 and not set(selected)&excluded;runtime={};outputs={}
 for phase,fens in [('aa',selected[:4]),('sprt',selected[4:])]:
  raw=('\n'.join(fens)+'\n').encode('ascii');path=PACKAGE/'openings'/(phase+'.epd');path.write_bytes(raw);outputs[phase]={'path':path.relative_to(REPO).as_posix(),'sha256':sha(raw),'positions':len(fens)}
  ordered=sorted(fens,key=lambda fen:hashlib.sha256((str(RUNTIME_SEED)+'\n'+fen).encode()).digest());raw=('\n'.join(ordered)+'\n').encode('ascii');(PACKAGE/'provenance'/('runtime-'+phase+'.epd')).write_bytes(raw);runtime[phase]={'seed':RUNTIME_SEED,'ordered_fens':ordered,'selected_epd_sha256':sha(raw),'positions':len(fens)}
 report={'source':source,'book_legal_cache':{'path':cachepath.relative_to(REPO).as_posix(),'sha256':sha(cachepath.read_bytes()),'key':source['archive_sha256']},'statistics':dict(cache['statistics'],historical_reserved_excluded=len(cache['positions'])-len(eligible)),'eligible_unique':len(eligible),'historical_exclusions_sha256':sha(expath.read_bytes()),'prospective_selection':{'seed':SEED,'outputs':outputs,'selections':[{'fen':fen,'source_game_1based':eligible[fen]} for fen in selected]}}
 (PACKAGE/'provenance/openings-selection.json').write_text(json.dumps(report,indent=2)+'\n');(PACKAGE/'provenance/runtime-order.json').write_text(json.dumps(runtime,indent=2)+'\n');marker={'status':'RESERVED_ONCE_NO_LAUNCH','selector_seed':SEED,'runtime_seed':RUNTIME_SEED,'selection_sha256':sha((PACKAGE/'provenance/openings-selection.json').read_bytes()),'book_cache_sha256':sha(cachepath.read_bytes()),'statistics':report['statistics'],'engine_executions':0};(PACKAGE/'provenance/reservation-frozen.json').write_text(json.dumps(marker,indent=2)+'\n');print(json.dumps(marker))
if __name__=='__main__':main()
