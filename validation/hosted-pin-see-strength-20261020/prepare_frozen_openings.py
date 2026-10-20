#!/usr/bin/env python3
"""Reserve once from official book; no engine, network, outcomes or Git mutations."""
from collections import Counter
import hashlib, io, json, zipfile
from pathlib import Path
import chess, chess.pgn
REPO=Path(__file__).resolve().parents[2]
PACKAGE=REPO/'.github/hosted-pin-see-strength'
SEED='20261020-pin-see-v1'
RUNTIME_SEED=20261023
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 assert not (PACKAGE/'provenance/reservation-frozen.json').exists(),'Already frozen'
 original=json.loads((REPO/'.github/hosted-tt-strength/provenance/openings-selection.json').read_text())
 excluded=set(); sources={}
 def add(fen):
  fen=' '.join(fen.split()[:4]); b=chess.Board(fen+' 0 1');excluded.add(fen);excluded.add(' '.join(b.fen(en_passant='legal').split()[:4]))
 paths={Path(row['path']) for row in original['registries']}
 paths|={p for p in REPO.rglob('*.epd') if PACKAGE not in p.parents and '.git' not in p.parts}
 for path in sorted(paths,key=lambda p:p.as_posix()):
  raw=path.read_bytes(); key=path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else path.as_posix();sources[key]=sha(raw)
  for line in raw.decode().splitlines():
   if line.strip() and not line.lstrip().startswith('#'):add(line)
 cohorts={}
 for name in ('hosted-confirmation','hosted-nnue-strength','hosted-tt-strength'):
  path=REPO/'.github'/name/'provenance/openings-selection.json';raw=path.read_bytes();report=json.loads(raw);fens=set()
  if 'prospective_selection' in report:fens|={r['fen'] for r in report['prospective_selection']['selections']}
  for rows in report.get('selections',{}).values():fens|={r['fen'] for r in rows}
  fens|=set(report.get('exclusions',{}).get('canonical_positions',[]))
  for fen in fens:add(fen)
  sources[path.relative_to(REPO).as_posix()]=sha(raw);cohorts[name]={'reserved_positions':len(fens),'canonical_positions':sorted(fens)}
 frozen={'historical_sources_sha256':sources,'excluded_canonical_positions':sorted(excluded),'reserved_cohorts':cohorts,'original_registry_count':len(original['registries'])}
 (PACKAGE/'provenance/historical-exclusions.json').write_text(json.dumps(frozen,indent=2)+'\n')
 source=original['source'];archive=(PACKAGE/'provenance/8moves_v3.pgn.zip').read_bytes();assert sha(archive)==source['archive_sha256']
 with zipfile.ZipFile(io.BytesIO(archive)) as z:pgn=z.read(source['zip_member'])
 assert sha(pgn)==source['pgn_sha256'];stream=io.StringIO(pgn.decode('utf-8-sig'));stats=Counter();eligible={};seen=set()
 while (game:=chess.pgn.read_game(stream)) is not None:
  stats['games']+=1;assert not game.errors and not game.headers.get('FEN');assert game.headers.get('Variant','Standard')=='Standard';b=game.board();plies=0
  for move in game.mainline_moves():assert b.is_legal(move);b.push(move);plies+=1
  assert plies==16 and b.is_valid() and b.legal_moves.count()>0
  fen=' '.join(b.fen(en_passant='fen').split()[:4]);assert fen not in seen;seen.add(fen)
  if b.ep_square is not None:stats['actual_ep_excluded']+=1;continue
  stats['strict_ep_none']+=1
  if fen in excluded:stats['historical_reserved_excluded']+=1;continue
  eligible[fen]=stats['games']
 assert stats['games']==34700 and stats['strict_ep_none']==31603 and stats['actual_ep_excluded']==3097
 selected=sorted(eligible,key=lambda f:hashlib.sha256((SEED+'\n'+f).encode()).digest())[:132];assert len(set(selected))==132 and not set(selected)&excluded
 runtime={};outputs={}
 for phase,fens in [('aa',selected[:4]),('sprt',selected[4:])]:
  raw=('\n'.join(fens)+'\n').encode('ascii');path=PACKAGE/'openings'/(phase+'.epd');path.write_bytes(raw);outputs[phase]={'path':path.relative_to(REPO).as_posix(),'sha256':sha(raw),'positions':len(fens)}
  ordered=sorted(fens,key=lambda f:hashlib.sha256((str(RUNTIME_SEED)+'\n'+f).encode()).digest());raw=('\n'.join(ordered)+'\n').encode('ascii');(PACKAGE/'provenance'/('runtime-'+phase+'.epd')).write_bytes(raw);runtime[phase]={'seed':RUNTIME_SEED,'ordered_fens':ordered,'selected_epd_sha256':sha(raw),'positions':len(fens)}
 report={'source':source,'statistics':dict(stats),'eligible_unique':len(eligible),'historical_exclusions_sha256':sha((PACKAGE/'provenance/historical-exclusions.json').read_bytes()),'prospective_selection':{'seed':SEED,'outputs':outputs,'selections':[{'fen':f,'source_game_1based':eligible[f]} for f in selected]}}
 (PACKAGE/'provenance/openings-selection.json').write_text(json.dumps(report,indent=2)+'\n');(PACKAGE/'provenance/runtime-order.json').write_text(json.dumps(runtime,indent=2)+'\n')
 marker={'status':'RESERVED_ONCE_NO_LAUNCH','selector_seed':SEED,'runtime_seed':RUNTIME_SEED,'selection_sha256':sha((PACKAGE/'provenance/openings-selection.json').read_bytes()),'engine_executions':0,'statistics':dict(stats)}
 (PACKAGE/'provenance/reservation-frozen.json').write_text(json.dumps(marker,indent=2)+'\n');print(json.dumps(marker))
if __name__=='__main__':main()
