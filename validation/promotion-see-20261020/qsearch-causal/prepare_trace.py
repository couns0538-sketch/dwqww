#!/usr/bin/env python3
"""Only freeze source/protocol and outside work copies. No compiler/engine/archive."""
from pathlib import Path
import datetime, difflib, hashlib, json, shutil
import chess

ROOT=Path(__file__).resolve().parent
WORK=Path('/workspace/promotion-see-qsearch-causal-20261020')
BUILDS={
    'source16':('/workspace/.cloud-setup/forge-pin-mask-source','/workspace/.cloud-setup/forge-pin-mask-release',
                '553caef144ae2e1b696ba35d7a0eb1a50a03fde9','a7718ec0555715e45b3aa96789754047e03db3104748a0fe8e03404e8695c267'),
    'source17':('/workspace/.cloud-setup/forge-promotion-source','/workspace/.cloud-setup/forge-promotion-release',
                '47f0560221d986e41a309853e1295c557fcf5bf6','d772f89980edb0e9f7fd5da99ef5c7bdb402aa8319082907b2bf31180359bd12')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
WORK.mkdir(exist_ok=False)
originals=ROOT/'originals';originals.mkdir()
sources={};headers={};frozen={};original_paths={}
for label,(source_name,build_name,revision,expected_core) in BUILDS.items():
    source=Path(source_name);build=Path(build_name);out=originals/label;out.mkdir()
    assert sha(build/'libforge_core.a')==expected_core
    shutil.copytree(source/'include',out/'include')
    for name in ['search.cpp','board.cpp','uci.cpp']:shutil.copy2(source/'src'/name,out/name)
    for src,dest in [(build/'libforge_core.a','libforge_core.a'),
                     (build/'CMakeFiles/forge.dir/src/uci.cpp.o','uci.cpp.o'),
                     (build/'CMakeFiles/forge_core.dir/flags.make','flags.make')]:
        shutil.copy2(src,out/dest);original_paths[str(src)]=sha(src)
    sources[label]=(out/'search.cpp').read_text()
    headers[label]={str(p.relative_to(out)):sha(p) for p in sorted((out/'include').rglob('*')) if p.is_file()}
    frozen[label]={'commit':revision,'core_sha256':expected_core,'search_sha256':sha(out/'search.cpp'),
                   'board_sha256':sha(out/'board.cpp'),'uci_object_sha256':sha(out/'uci.cpp.o'),
                   'header_sha256':headers[label]}
assert sources['source16']==sources['source17']
assert headers['source16']==headers['source17']
before=sources['source16']
after=before.replace('#include <cmath>','#include <cmath>\n#include <cstdio>',1)
start=after.index('int Worker::qsearch(');end=after.index('// Main alpha-beta search',start)
segment=after[start:end]
needle='        if (!board.is_legal(move)) continue;\n        ++move_count;\n'
replacement='''        if (!board.is_legal(move)) continue;
        const Bitboard trace_occupancy = square_bb(1) | square_bb(42) | square_bb(50) |
                                         square_bb(57) | square_bb(58) | square_bb(63);
        const bool trace_target = move.from == 1 && move.to == 57 &&
            board.side_to_move() == White && board.occupied() == trace_occupancy &&
            board.piece_at(1) == WQ && board.piece_at(50) == WP &&
            board.piece_at(57) == BB && board.piece_at(58) == BR &&
            board.king_square(White) == 42 && board.king_square(Black) == 63;
        if (trace_target) std::fprintf(stderr,
            "QSEARCH_TRACE stage=ENTER move=b1b8 ply=%d alpha=%d beta=%d in_check=%d static_eval=%d futility_base=%d fen=%s\\n",
            ply, alpha, beta, static_cast<int>(in_check), ss->static_eval, futility_base, board.fen().c_str());
        ++move_count;
'''
assert segment.count(needle)==1;segment=segment.replace(needle,replacement,1)
needle='''            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
                best_score = std::max(best_score, futility_base + capture_value(board, move));
'''
replacement='''            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
                if (trace_target) std::fprintf(stderr, "QSEARCH_TRACE stage=SKIP_FUTILITY move=b1b8\\n");
                best_score = std::max(best_score, futility_base + capture_value(board, move));
'''
assert segment.count(needle)==1;segment=segment.replace(needle,replacement,1)
needle='            if (!board.see_ge(move, -tune::QsSeeMargin)) continue;\n'
replacement='''            const bool see_pass = board.see_ge(move, -tune::QsSeeMargin);
            if (trace_target) std::fprintf(stderr,
                "QSEARCH_TRACE stage=SEE move=b1b8 threshold=%d passed=%d\\n",
                -tune::QsSeeMargin, static_cast<int>(see_pass));
            if (!see_pass) {
                if (trace_target) std::fprintf(stderr, "QSEARCH_TRACE stage=SKIP_SEE move=b1b8\\n");
                continue;
            }
'''
assert segment.count(needle)==1;segment=segment.replace(needle,replacement,1)
needle='''        (void)board.make_move(move, undo);
        shared_.tt.prefetch(board.key());
        const int score = -qsearch(board, ss + 1, -beta, -alpha);
        board.unmake_move(move, undo);
'''
replacement='''        (void)board.make_move(move, undo);
        if (trace_target) std::fprintf(stderr, "QSEARCH_TRACE stage=SEARCH_ENTER move=b1b8 fen=%s\\n", board.fen().c_str());
        shared_.tt.prefetch(board.key());
        const int score = -qsearch(board, ss + 1, -beta, -alpha);
        board.unmake_move(move, undo);
        if (trace_target) std::fprintf(stderr, "QSEARCH_TRACE stage=SEARCH_RETURN move=b1b8 score=%d\\n", score);
'''
assert segment.count(needle)==1;segment=segment.replace(needle,replacement,1)
after=after[:start]+segment+after[end:]
(ROOT/'search-trace.cpp').write_text(after)
(ROOT/'qsearch-trace.patch').write_text(''.join(difflib.unified_diff(
    before.splitlines(True),after.splitlines(True),fromfile='a/src/search.cpp',tofile='b/src/search.cpp')))
source_work=WORK/'source';(source_work/'src').mkdir(parents=True)
shutil.copytree(originals/'source16/include',source_work/'include')
shutil.copy2(ROOT/'search-trace.cpp',source_work/'src/search.cpp')

fen='1br3k1/2P5/2K5/8/8/8/8/1Q6 b - - 0 1'
board=chess.Board(fen);initial=chess.Move.from_uci('g8h8')
assert board.is_valid() and initial in board.legal_moves and not board.gives_check(initial)
board.push(initial);child=board.fen()
noisy=sorted(m.uci() for m in board.legal_moves if board.is_capture(m) or m.promotion)
assert not board.is_check() and noisy==['b1b8']
VALUES={None:0,1:100,2:300,3:300,4:500,5:900,6:0}
def exchange(b,target):
    best=0;tree=[]
    for m in sorted(b.legal_moves,key=lambda m:m.uci()):
        if m.to_square!=target or not b.is_capture(m):continue
        gain=VALUES[b.piece_type_at(m.to_square)]+(VALUES[m.promotion]-100 if m.promotion else 0)
        b.push(m);reply,children=exchange(b,target);b.pop()
        tree.append({'move':m.uci(),'gain':gain,'net':gain-reply,'children':children});best=max(best,gain-reply)
    return best,tree
target=chess.Move.from_uci('b1b8');gain=VALUES[board.piece_type_at(target.to_square)]
board.push(target);reply,tree=exchange(board,target.to_square);board.pop()
assert gain-reply==300
write(ROOT/'fixture-oracle.json',{'oracle':'python-chess '+chess.__version__,'parent':fen,
    'root_move':'g8h8','child':child,'child_legal_noisy_moves':noisy,
    'target_move':'b1b8','target_exchange':gain-reply,'target_reply_tree':tree})
protocol={'status':'PREPARED_NOT_BUILT_OR_RUN','required_clearance_exact':'17 QSEARCH TRACE CLEAR',
    'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'frozen_builds':frozen,'original_path_sha256':original_paths,
    'search_trace_sha256':sha(ROOT/'search-trace.cpp'),'fixture_oracle_sha256':sha(ROOT/'fixture-oracle.json'),
    'parent_fen':fen,'root_move':'g8h8','depth':1,'threads':1,'hash_mb':16,'own_book':False,
    'expected_threshold':-40,'expected_source16_see_pass':False,'expected_source17_see_pass':True,
    'per_process_total_response_deadline_seconds':10,'max_processes':2,'max_searches_per_process':1,
    'engine_budget_seconds':30,'retry':False,'performance_claim':None,'strength_claim':None,
    'original_file_sha256':{str(p.relative_to(originals)):sha(p) for p in sorted(originals.rglob('*')) if p.is_file()},
    'driver_sha256':{n:sha(ROOT/n) for n in ['PLAN.md','prepare_trace.py','run_trace.py']}}
write(ROOT/'PROTOCOL.json',protocol)
write(ROOT/'PREPARATION-RECEIPT.json',{'status':'PREPARED_NOT_BUILT_OR_RUN',
    'protocol_sha256':sha(ROOT/'PROTOCOL.json'),'search_trace_sha256':sha(ROOT/'search-trace.cpp'),
    'all_original_paths_unchanged':all(sha(p)==h for p,h in original_paths.items()),
    'compiler_invocations':0,'engine_invocations':0,'archive_invocations':0})
print(json.dumps({'status':protocol['status'],'search_trace_sha256':protocol['search_trace_sha256'],
                  'child':child,'only_legal_noisy':noisy,'target_oracle':300}))
