#!/usr/bin/env python3
"""Read-only freshness/ranking audit and independent selected-game legal replay.

The retained corpus cache was produced by one full legal official-book replay.
This verifier replays each of the132 selected source games, skips other games,
and independently checks the complete cached ranking against frozen exclusions.
"""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
import chess,chess.pgn
REPO=Path(__file__).resolve().parents[2];PACKAGE=REPO/'.github/hosted-promotion-see-strength';sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();selection=json.loads((PACKAGE/'provenance/openings-selection.json').read_text());source=selection['source'];cacheinfo=selection['book_legal_cache'];cachepath=REPO/cacheinfo['path'];raw=cachepath.read_bytes();assert sha(raw)==cacheinfo['sha256'];cache=json.loads(raw);assert cache['source']==source and cache['cache_key_archive_sha256']==source['archive_sha256']==cacheinfo['key'];assert source['archive_sha256'] in cachepath.name;assert cache['status']=='FULL_LEGAL_REPLAY_COMPLETE';assert cache['statistics']=={'games':34700,'strict_ep_none':31603,'actual_ep_excluded':3097};assert len(cache['positions'])==31603;assert cache['generator_sha256']==cacheinfo['origin_generator_sha256']==sha((REPO/cacheinfo['origin_generator_path']).read_bytes());assert (REPO/cacheinfo['origin_path']).read_bytes()==raw;assert sha((REPO/cacheinfo['origin_full_replay_proof_path']).read_bytes())==cacheinfo['origin_full_replay_proof_sha256'];originproof=json.loads((REPO/cacheinfo['origin_full_replay_proof_path']).read_text());assert originproof['status']=='passed' and originproof['book_cache_full_legal_replay']==34700 and originproof['book_cache_sha256']==cacheinfo['sha256'];assert sha((REPO/cacheinfo['origin_selection_path']).read_bytes())==cacheinfo['origin_selection_sha256'];assert cacheinfo['full_corpus_replays_this_preparation']==0;assert cache['engine_executions']==0;assert len(set(cache['positions'].values()))==31603;assert all(type(i) is int and 1<=i<=34700 for i in cache['positions'].values());assert all(fen.split()[3]=='-' for fen in cache['positions'])
 exraw=(PACKAGE/'provenance/historical-exclusions.json').read_bytes();assert sha(exraw)==selection['historical_exclusions_sha256'];ex=json.loads(exraw);excluded=set(ex['excluded_canonical_positions'])
 for path,digest in ex['historical_sources_sha256'].items():assert sha((REPO/path).read_bytes())==digest,path
 original=json.loads((REPO/'.github/hosted-tt-strength/provenance/openings-selection.json').read_text());assert len(original['registries'])==42
 for row in original['registries']:assert sha(Path(row['path']).read_bytes())==row['sha256']
 registry_paths={Path(row['path']) for row in original['registries']}|{REPO/path for path in ex['historical_sources_sha256'] if path.endswith('.epd')}
 historical_keys=set()
 for path in registry_paths:
  for line in path.read_text().splitlines():
   if not line.strip() or line.lstrip().startswith('#'):continue
   fen=' '.join(line.split()[:4]);historical_keys.add(fen);historical_keys.add(' '.join(chess.Board(fen+' 0 1').fen(en_passant='legal').split()[:4]))
 assert historical_keys<=excluded
 for cohort in ex['reserved_cohorts'].values():assert set(cohort['canonical_positions'])<=excluded
 for name,count in [('hosted-nnue-strength',1028),('hosted-tt-strength',1028),('hosted-pin-see-strength',132),('hosted-pin-mask-strength',132)]:assert ex['reserved_cohorts'][name]['reserved_positions']==count
 eligible={fen:index for fen,index in cache['positions'].items() if fen not in excluded};assert len(eligible)==selection['eligible_unique'];seed='20261020-promotion-see-v1';ranked=sorted(eligible,key=lambda fen:hashlib.sha256((seed+'\n'+fen).encode()).digest())[:132];chosen=selection['prospective_selection'];assert chosen['seed']==seed;assert [r['fen'] for r in chosen['selections']]==ranked;assert len(set(ranked))==132 and not set(ranked)&excluded;assert all(eligible[row['fen']]==row['source_game_1based'] for row in chosen['selections'])
 runtime=json.loads((PACKAGE/'provenance/runtime-order.json').read_text())
 for phase,fens in [('aa',ranked[:4]),('sprt',ranked[4:])]:
  raw=('\n'.join(fens)+'\n').encode('ascii');assert raw==(PACKAGE/'openings'/(phase+'.epd')).read_bytes();assert sha(raw)==chosen['outputs'][phase]['sha256'];ordered=sorted(fens,key=lambda fen:hashlib.sha256(('20261025\n'+fen).encode()).digest());raw=('\n'.join(ordered)+'\n').encode('ascii');assert runtime[phase]['seed']==20261025 and runtime[phase]['ordered_fens']==ordered;assert sha(raw)==runtime[phase]['selected_epd_sha256'];assert raw==(PACKAGE/'provenance'/('runtime-'+phase+'.epd')).read_bytes()
 raw=(PACKAGE/'provenance/8moves_v3.pgn.zip').read_bytes();assert sha(raw)==source['archive_sha256']
 with zipfile.ZipFile(io.BytesIO(raw)) as zipped:raw=zipped.read(source['zip_member'])
 assert sha(raw)==source['pgn_sha256'];stream=io.StringIO(raw.decode('utf-8-sig'));wanted={row['source_game_1based']:row['fen'] for row in chosen['selections']};visited=0;replayed=0
 while True:
  index=visited+1
  if index in wanted:
   board=chess.pgn.read_game(stream,Visitor=chess.pgn.BoardBuilder)
   if board is None:break
   assert board.ply()==16 and board.is_valid() and board.legal_moves.count()>0 and board.ep_square is None;assert ' '.join(board.fen(en_passant='fen').split()[:4])==wanted[index];replayed+=1
  elif not chess.pgn.skip_game(stream):break
  visited+=1
 assert visited==34700 and replayed==132
 result={'status':'passed','book_cache_sha256':cacheinfo['sha256'],'book_cache_full_legal_replay':34700,'full_corpus_replays_this_preparation':0,'verified_book_cache_reused_byte_exact':True,'independent_selected_source_games_legally_replayed':replayed,'official_source_games_visited':visited,'strict_ep_none_cache':31603,'fresh_eligible_after_exclusions':len(eligible),'historical_reserved_source_positions_excluded':31603-len(eligible),'historical_source_hashes_verified':len(ex['historical_sources_sha256']),'historical_canonical_keys_reconstructed':len(historical_keys),'all_historical_keys_and_reserved_cohorts_in_exclusion_snapshot':True,'old42registry_hashes_verified':True,'full_reserved_cohorts_excluded':{'nnue':1028,'tt':1028,'unused_candidate15':132,'unused_candidate16':132},'fresh_unique_positions':132,'frozen_aa_pairs':4,'frozen_sprt_pairs':128,'selector_seed':seed,'runtime_seed':20261025,'engine_executions':0,'frozen_inputs_rewritten':False};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
