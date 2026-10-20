#!/usr/bin/env python3
"""Independent legality proof of the authored mechanisms, no engine calls."""
from pathlib import Path
import csv, hashlib, json
import chess
ROOT=Path(__file__).resolve().parent
cases={c['id']:c for c in json.loads((ROOT/'oracle-corpus.json').read_text())}
checks={}
def board(name): return chess.Board(cases[name]['fen'])
def move_info(b,uci):
    m=chess.Move.from_uci(uci)
    return {'move':uci,'pseudo_legal':b.is_pseudo_legal(m),'legal':b.is_legal(m)}
b=board('ep_opens_two_square_rank_pin_white')
checks['ep_opened_ray']={'knight_initially_pinned':b.is_pinned(chess.BLACK,chess.F5)}
assert not b.is_pinned(chess.BLACK,chess.F5)
b.push_uci('e5d6')
checks['ep_opened_ray'].update({'knight_after_ep_pinned':b.is_pinned(chess.BLACK,chess.F5),'recapture':move_info(b,'f5d6'),'origin_e5_empty':b.piece_at(chess.E5) is None,'captured_d5_empty':b.piece_at(chess.D5) is None})
assert b.is_pinned(chess.BLACK,chess.F5) and not b.is_legal(chess.Move.from_uci('f5d6'))
b=board('three_recaptures_pin_released_white')
assert b.is_pinned(chess.BLACK,chess.E3)
b.push_uci('d4d1')
checks['three_recapture_pin_release']={'initial_reply':move_info(b,'e3d1'),'sequence':[]}
assert b.is_pseudo_legal(chess.Move.from_uci('e3d1')) and not b.is_legal(chess.Move.from_uci('e3d1'))
for uci in ['d8d1','e1d1','e3d1']:
    info=move_info(b,uci); assert info['legal']; checks['three_recapture_pin_release']['sequence'].append(info)
    b.push_uci(uci)
checks['three_recapture_pin_release']['target_victims_in_order']='bishop,white queen,black queen,white rook'
b=board('all_nonking_rejected_then_legal_king'); b.push_uci('g1g5')
checks['king_fallback_legal']={'pinned_knight':move_info(b,'e6g5'),'king':move_info(b,'f6g5')}
assert not b.is_legal(chess.Move.from_uci('e6g5')) and b.is_legal(chess.Move.from_uci('f6g5'))
b=board('all_nonking_rejected_king_blocked_by_pinned_defender'); b.push_uci('g1g5')
checks['king_fallback_pinned_geometric_defender']={'defender_h3_pinned':b.is_pinned(chess.WHITE,chess.H3),'h3_attacks_g5':chess.H3 in b.attackers(chess.WHITE,chess.G5),'pinned_knight':move_info(b,'e6g5'),'king':move_info(b,'f6g5')}
assert b.is_pinned(chess.WHITE,chess.H3) and chess.H3 in b.attackers(chess.WHITE,chess.G5)
assert not b.is_legal(chess.Move.from_uci('e6g5')) and not b.is_legal(chess.Move.from_uci('f6g5'))
b=board('initial_check_evasion_capture_pinned_recapturer')
assert b.is_check(); checks['initial_in_check']={'in_check':True,'initial':move_info(b,'f3g3')}
b.push_uci('f3g3'); assert not b.is_check()
checks['initial_in_check']['reply']=move_info(b,'e4g3')
assert b.is_pseudo_legal(chess.Move.from_uci('e4g3')) and not b.is_legal(chess.Move.from_uci('e4g3'))
b=board('initial_discovered_check_invalidates_unrelated_recapture')
assert not b.is_check(); b.push_uci('f3d4')
checks['discovered_check']={'black_in_check':b.is_check(),'checker_squares':[chess.square_name(s) for s in b.checkers()],'unrelated_reply':move_info(b,'f5d4')}
assert b.is_check() and list(b.checkers())==[chess.G2]
assert b.is_pseudo_legal(chess.Move.from_uci('f5d4')) and not b.is_legal(chess.Move.from_uci('f5d4'))
(ROOT/'mechanism-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
outputs={}
for kind in ['baseline','candidate']:
    with (ROOT/(kind+'.stdout')).open() as f: outputs[kind]={r['id']:r for r in csv.DictReader(f,delimiter='\t')}
limitations=[]
for name in ['inherited_recapture_promotion_white','inherited_recapture_promotion_black']:
    c=cases[name]
    assert c['oracle_exchange']==-1200
    for kind in outputs:
        row=outputs[kind][name]
        assert int(row['static_exchange'])==-400 and row['ge-500']=='1'
    limitations.append({'id':name,'fen':c['fen'],'initial':c['move'],'oracle_exchange':-1200,'baseline_exchange':-400,'candidate_exchange':-400,'actual_see_ge_minus500':True,'oracle_see_ge_minus500':False,'legal_promoting_recaptures':c['legal_recaptures'],'classification':'Inherited exact-promotion-aware SEE mismatch reproduced; not a green correctness assertion.'})
(ROOT/'known-limitation.json').write_text(json.dumps(limitations,indent=2)+'\n')
print('PASS independent mechanism checks; inherited promotion mismatch reproduced separately for both builds/colors')
