#!/usr/bin/env python3
"""Independent read-only full official-book replay and frozen selection check."""
from collections import Counter
import argparse,hashlib,io,json,zipfile
from pathlib import Path
import chess,chess.pgn
REPO=Path(__file__).resolve().parents[2];PACKAGE=REPO/'.github/hosted-pin-see-strength';sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();report=json.loads((PACKAGE/'provenance/openings-selection.json').read_text());exraw=(PACKAGE/'provenance/historical-exclusions.json').read_bytes();assert sha(exraw)==report['historical_exclusions_sha256'];ex=json.loads(exraw);excluded=set(ex['excluded_canonical_positions'])
 for path,digest in ex['historical_sources_sha256'].items():assert sha((REPO/path).read_bytes())==digest,path
 for name in ('hosted-nnue-strength','hosted-tt-strength'):assert ex['reserved_cohorts'][name]['reserved_positions']==1028
 for r in json.loads((REPO/'.github/hosted-tt-strength/provenance/openings-selection.json').read_text())['registries']:assert sha(Path(r['path']).read_bytes())==r['sha256']
 source=report['source'];raw=(PACKAGE/'provenance/8moves_v3.pgn.zip').read_bytes();assert sha(raw)==source['archive_sha256']
 with zipfile.ZipFile(io.BytesIO(raw)) as z:raw=z.read(source['zip_member'])
 assert sha(raw)==source['pgn_sha256'];stream=io.StringIO(raw.decode('utf-8-sig'));stats=Counter();eligible={};seen=set()
 while (b:=chess.pgn.read_game(stream,Visitor=chess.pgn.BoardBuilder)) is not None:
  stats['games']+=1;assert b.ply()==16 and b.is_valid() and b.legal_moves.count()>0
  fen=' '.join(b.fen(en_passant='fen').split()[:4]);assert fen not in seen;seen.add(fen)
  if b.ep_square is not None:stats['actual_ep_excluded']+=1;continue
  stats['strict_ep_none']+=1
  if fen in excluded:stats['historical_reserved_excluded']+=1;continue
  eligible[fen]=stats['games']
 seed='20261020-pin-see-v1';ranked=sorted(eligible,key=lambda f:hashlib.sha256((seed+'\n'+f).encode()).digest())[:132];selected=report['prospective_selection'];assert selected['seed']==seed;assert [r['fen'] for r in selected['selections']]==ranked;assert all(eligible[r['fen']]==r['source_game_1based'] for r in selected['selections']);assert dict(stats)==report['statistics'];assert len(eligible)==report['eligible_unique']
 for phase,fens in [('aa',ranked[:4]),('sprt',ranked[4:])]:assert (PACKAGE/'openings'/(phase+'.epd')).read_text()=='\n'.join(fens)+'\n'
 result={'status':'passed','full_legal_replay':dict(stats),'unique_positions':len(seen),'eligible':len(eligible),'fresh_unique_positions':132,'historical_sources_verified':len(ex['historical_sources_sha256']),'old42registry_hashes_verified':True,'full1028nnue_and1028tt_reserved_cohorts_excluded':True,'engine_executions':0,'frozen_inputs_rewritten':False};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
