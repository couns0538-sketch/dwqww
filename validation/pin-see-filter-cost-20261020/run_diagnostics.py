#!/usr/bin/env python3
"""Pure diagnostic instrumentation after the uninstrumented API parity gate."""
from pathlib import Path
import datetime, difflib, hashlib, json, os, shutil, subprocess, tarfile, time

OUT = Path(__file__).resolve().parent
REPO = OUT.parent.parent
WORK = Path('/workspace/pin-see-filter-cost-20261020')
ATTEMPT = OUT/'diagnostics-attempt1'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
SEMANTIC = json.loads((OUT/'semantic-record.json').read_text())
assert SEMANTIC['status']=='PASS_BYTE_IDENTICAL_API_PARITY'
ATTEMPT.mkdir(exist_ok=False)
RECORD = {'source_commit':SEMANTIC['source_commit'], 'phases':[], 'status':'RUNNING',
          'engine_execution_budget_seconds':120, 'engine_elapsed_seconds':SEMANTIC['engine_elapsed_seconds'],
          'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope':'single-thread diagnostic counts; no timing/NPS comparison or strength claim',
          'performance_claim':None, 'flags':SEMANTIC['flags']}
FLAGS=SEMANTIC['flags']

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(): (ATTEMPT/'record.json').write_text(json.dumps(RECORD,indent=2)+'\n')
def run(label,args,timeout=60,engine=False,verify=False):
    if engine and RECORD['engine_elapsed_seconds']+timeout>120: raise RuntimeError('Engine budget exhausted')
    env=ENV.copy()
    if verify: env['FORGE_SEE_VERIFY_MASKS']='1'
    start=time.monotonic()
    try:
        p=subprocess.run([str(x) for x in args],cwd=WORK,env=env,capture_output=True,timeout=timeout)
        rc,stdout,stderr=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as exc:
        rc,stdout,stderr=124,exc.stdout or b'',exc.stderr or b''
    elapsed=time.monotonic()-start
    for ext,data in [('stdout',stdout),('stderr',stderr)]: (ATTEMPT/(label+'.'+ext)).write_bytes(data)
    RECORD['phases'].append({'label':label,'command':[str(x) for x in args],'cwd':str(WORK),
                            'timeout_seconds':timeout,'exit_code':rc,'engine_execution':engine,
                            'verify_complete_masks':verify,'elapsed_seconds_operational_only':elapsed,
                            'stdout_sha256':sha(ATTEMPT/(label+'.stdout')),
                            'stderr_sha256':sha(ATTEMPT/(label+'.stderr'))})
    if engine: RECORD['engine_elapsed_seconds']+=elapsed
    save(); print(label,rc,flush=True)
    if rc: raise RuntimeError(label+' exit '+str(rc))
    return stdout

FIELDS=['see_calls','exchange_plies','active_plies','candidate_origins','surviving_origins',
        'primary_full_query_calls','occupied_bishop_queries','occupied_rook_queries',
        'empty_bishop_queries','empty_rook_queries','between_classifications',
        'pawn_tests','knight_tests','king_tests','aligned_sliders','max_candidates',
        'mask_states_verified','verification_shadow_queries','mask_mismatches']

def instrument(text,kind):
    text=text.replace('#include <cstdlib>','#include <cstdlib>\n#include <cstdio>',1)
    declaration='\n// Diagnostic-only counters: these binaries are restricted to one search thread.\nstruct SeeFilterDiagnostics {\n'
    declaration+=''.join('    std::uint64_t '+f+' = 0;\n' for f in FIELDS)
    declaration+='    bool verify_masks = std::getenv("FORGE_SEE_VERIFY_MASKS") != nullptr;\n'
    fmt='SEE_FILTER_COUNTERS {'+','.join('"'+f+'":%llu' for f in FIELDS)+'}\n'
    declaration+='    ~SeeFilterDiagnostics() {\n        std::fprintf(stderr, '+json.dumps(fmt)+',\n'
    declaration+=',\n'.join('            static_cast<unsigned long long>('+f+')' for f in FIELDS)+');\n    }\n};\n'
    declaration+='SeeFilterDiagnostics see_filter_diagnostics;\nthread_local bool see_filter_query_active = false;\n'
    needle='constexpr std::array<int, 7> SeeValue{0, 100, 300, 300, 500, 900, 0};\n'
    assert text.count(needle)==1; text=text.replace(needle,needle+declaration)
    helper_start=text.index('bool Board::square_attacked_with_occupancy(')
    helper_end=text.index('\nbool Board::square_attacked(',helper_start)
    helper=text[helper_start:helper_end]
    helper=helper.replace('    const Bitboard available = ~removed;','    if (see_filter_query_active) ++see_filter_diagnostics.primary_full_query_calls;\n    const Bitboard available = ~removed;\n    if (see_filter_query_active) ++see_filter_diagnostics.pawn_tests;',1)
    helper=helper.replace('    if ((attacks::knight(square)', '    if (see_filter_query_active) ++see_filter_diagnostics.knight_tests;\n    if ((attacks::knight(square)',1)
    helper=helper.replace('    if ((attacks::king(square)', '    if (see_filter_query_active) ++see_filter_diagnostics.king_tests;\n    if ((attacks::king(square)',1)
    helper=helper.replace('    if ((attacks::bishop(square, occupancy)', '    if (see_filter_query_active) ++see_filter_diagnostics.occupied_bishop_queries;\n    if ((attacks::bishop(square, occupancy)',1)
    helper=helper.replace('    return (attacks::rook(square, occupancy)', '    if (see_filter_query_active) ++see_filter_diagnostics.occupied_rook_queries;\n    return (attacks::rook(square, occupancy)',1)
    text=text[:helper_start]+helper+text[helper_end:]
    text=text.replace('bool Board::see_ge(const Move& move, int threshold) const {','bool Board::see_ge(const Move& move, int threshold) const {\n    ++see_filter_diagnostics.see_calls;',1)
    needle='        Bitboard stm_attackers = attackers & occupied(stm);\n'
    prefix='''        const Bitboard filter_input = stm_attackers;
        const auto diagnostic_candidates = static_cast<std::uint64_t>(popcount(stm_attackers & ~pieces(stm, King)));
        ++see_filter_diagnostics.exchange_plies;
        see_filter_diagnostics.active_plies += diagnostic_candidates != 0;
        see_filter_diagnostics.candidate_origins += diagnostic_candidates;
        see_filter_diagnostics.max_candidates = std::max(see_filter_diagnostics.max_candidates, diagnostic_candidates);
'''
    assert text.count(needle)==1; text=text.replace(needle,needle+prefix)
    if kind=='reference':
        text=text.replace('        while (candidates != 0) {\n','        see_filter_query_active = true;\n        while (candidates != 0) {\n',1)
        needle='''        }
        if (stm_attackers == 0) break;
'''
        assert text.count(needle)==1
        text=text.replace(needle,'''        }
        see_filter_query_active = false;
        see_filter_diagnostics.surviving_origins += static_cast<std::uint64_t>(popcount(stm_attackers & ~pieces(stm, King)));
        (void)filter_input;
        if (stm_attackers == 0) break;
''',1)
    else:
        text=text.replace('(attacks::pawn(stm, king) & pieces(enemy, Pawn) & live) != 0 ||','(++see_filter_diagnostics.pawn_tests, (attacks::pawn(stm, king) & pieces(enemy, Pawn) & live) != 0) ||',1)
        text=text.replace('(attacks::knight(king) & pieces(enemy, Knight) & live) != 0 ||','(++see_filter_diagnostics.knight_tests, (attacks::knight(king) & pieces(enemy, Knight) & live) != 0) ||',1)
        text=text.replace('(attacks::king(king) & pieces(enemy, King) & live) != 0;','(++see_filter_diagnostics.king_tests, (attacks::king(king) & pieces(enemy, King) & live) != 0);',1)
        text=text.replace('            Bitboard pinners =\n','            ++see_filter_diagnostics.empty_bishop_queries;\n            ++see_filter_diagnostics.empty_rook_queries;\n            Bitboard pinners =\n',1)
        text=text.replace('            Bitboard forbidden = 0;\n','            see_filter_diagnostics.aligned_sliders += static_cast<std::uint64_t>(popcount(pinners));\n            Bitboard forbidden = 0;\n',1)
        text=text.replace('                const int pinner = pop_lsb(pinners);\n','                ++see_filter_diagnostics.between_classifications;\n                const int pinner = pop_lsb(pinners);\n',1)
        needle='''        }
        if (stm_attackers == 0) break;
'''
        verification='''        }
        see_filter_diagnostics.surviving_origins += static_cast<std::uint64_t>(popcount(stm_attackers & ~pieces(stm, King)));
        if (see_filter_diagnostics.verify_masks) {
            Bitboard reference_attackers = filter_input;
            Bitboard reference_candidates = reference_attackers & ~pieces(stm, King);
            const Bitboard reference_removed = ~occupancy | square_bb(to);
            while (reference_candidates != 0) {
                const int origin = pop_lsb(reference_candidates);
                ++see_filter_diagnostics.verification_shadow_queries;
                if (square_attacked_with_occupancy(king_square(stm), opposite(stm),
                                                  occupancy ^ square_bb(origin), reference_removed)) {
                    reference_attackers &= ~square_bb(origin);
                }
            }
            ++see_filter_diagnostics.mask_states_verified;
            if (reference_attackers != stm_attackers) {
                ++see_filter_diagnostics.mask_mismatches;
                std::fprintf(stderr, "SEE_FILTER_MASK_MISMATCH target=%d side=%d\\n", to, static_cast<int>(stm));
                std::abort();
            }
        }
        if (stm_attackers == 0) break;
'''
        assert text.count(needle)==1; text=text.replace(needle,verification,1)
    return text

def counters(label):
    text=(ATTEMPT/(label+'.stderr')).read_text()
    line=next(line for line in text.splitlines() if line.startswith('SEE_FILTER_COUNTERS '))
    return json.loads(line.removeprefix('SEE_FILTER_COUNTERS ').removesuffix('\\n'))

try:
    members=list(SEMANTIC['reference_core_members'])
    diag_cores={}
    for kind in ['reference','mask']:
        source=WORK/('source-diagnostics-attempt1-'+kind)
        shutil.copytree(WORK/('source-'+kind),source)
        before=(source/'src/board.cpp').read_text(); after=instrument(before,kind)
        (source/'src/board.cpp').write_text(after)
        (ATTEMPT/(kind+'-board.cpp')).write_text(after)
        (ATTEMPT/(kind+'-instrumentation.patch')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/board.cpp',tofile='b/src/board.cpp')))
        with tarfile.open(ATTEMPT/('source-'+kind+'.tar'),'w') as tar:
            for relative in SEMANTIC['reference_source_sha256']: tar.add(source/relative,arcname=relative)
        obj=ATTEMPT/(kind+'-board.cpp.o')
        run('compile-board-'+kind,['/usr/bin/c++',*FLAGS,'-I'+str(source/'include'),'-c',source/'src/board.cpp','-o',obj],90)
        core=ATTEMPT/(kind+'-libforge_core.a'); shutil.copy2(OUT/'reference-libforge_core.a',core)
        board_member=WORK/'board.cpp.o'; shutil.copy2(obj,board_member)
        run('replace-board-'+kind,['ar','r',core,board_member]); run('ranlib-'+kind,['ranlib',core])
        hashes={m:hashlib.sha256(subprocess.check_output(['ar','p',core,m])).hexdigest() for m in members}
        changed=[m for m in members if hashes[m]!=SEMANTIC['reference_core_members'][m]]
        assert changed==['board.cpp.o']
        RECORD[kind+'_core']={'sha256':sha(core),'member_sha256':hashes,'changed_members':changed}
        diag_cores[kind]=core
        exe=ATTEMPT/('see-'+kind)
        run('link-api-'+kind,['/usr/bin/c++',*FLAGS,OUT/'see_diagnostic.o',core,'-pthread','-o',exe],60)
        run('api-'+kind,[exe,OUT/'inputs/all316.tsv'],15,engine=True,verify=kind=='mask')
    assert (ATTEMPT/'api-reference.stdout').read_bytes()==(OUT/'api-reference.stdout').read_bytes()
    assert (ATTEMPT/'api-mask.stdout').read_bytes()==(OUT/'api-reference.stdout').read_bytes()
    RECORD['diagnostic_api_stdout_matches_uninstrumented_reference']=True
    RECORD['api_counters']={kind:counters('api-'+kind) for kind in diag_cores}
    assert RECORD['api_counters']['mask']['mask_mismatches']==0
    assert RECORD['api_counters']['mask']['mask_states_verified']>0
    for name in ['see_calls','exchange_plies','active_plies','candidate_origins','surviving_origins','max_candidates']:
        assert RECORD['api_counters']['reference'][name]==RECORD['api_counters']['mask'][name],name
    save()
    bench_source=r'''#include "forge/board.hpp"
#include "forge/search.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string_view>
int main() {
    constexpr std::array<std::string_view, 8> fens{
        forge::Board::StandardStartFen,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    };
    forge::Searcher searcher(16);
    searcher.set_threads(1);
    std::uint64_t total = 0;
    std::cout << "case\tdepth\tnodes\tscore\tbestmove\tpv\n";
    for (std::size_t i = 0; i < fens.size(); ++i) {
        forge::Board board;
        if (!board.set_fen(fens[i])) throw std::runtime_error("bad bench FEN");
        forge::SearchLimits limits;
        limits.depth = 11;
        searcher.clear();
        const auto result = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        total += result.nodes;
        std::cout << i << '\t' << result.depth << '\t' << result.nodes << '\t' << result.score
                  << '\t' << forge::Board::move_to_uci(result.best_move) << '\t';
        bool first = true;
        for (const auto move : result.pv) {
            if (!board.is_pseudo_legal(move) || !board.is_legal(move)) throw std::runtime_error("illegal PV");
            if (!first) std::cout << ',';
            first = false;
            std::cout << forge::Board::move_to_uci(move);
            forge::Undo undo;
            if (!board.make_move(move, undo)) throw std::runtime_error("PV make failed");
        }
        std::cout << '\n';
    }
    std::cout << "total_nodes\t" << total << '\n';
}
'''
    # Literal C++ text above uses normal quotes, not shell quoting.
    bench_source=bench_source.replace('\\"','"')
    (ATTEMPT/'bench11.cpp').write_text(bench_source)
    run('compile-bench-driver',['/usr/bin/c++',*FLAGS,'-I'+str(WORK/'source-reference/include'),'-c',ATTEMPT/'bench11.cpp','-o',ATTEMPT/'bench11.o'],60)
    for kind,core in diag_cores.items():
        exe=ATTEMPT/('bench11-'+kind)
        run('link-bench-'+kind,['/usr/bin/c++',*FLAGS,ATTEMPT/'bench11.o',core,'-pthread','-o',exe],60)
        run('bench11-'+kind,[exe],10,engine=True)
    ref=(ATTEMPT/'bench11-reference.stdout').read_bytes(); mask=(ATTEMPT/'bench11-mask.stdout').read_bytes()
    assert ref==mask
    assert ref.decode().splitlines()[-1]=='total_nodes\t385792'
    assert len(ref.decode().splitlines())==10
    RECORD['byte_identical_bench_nodes_scores_bestmoves_pvs']=True
    RECORD['bench_depth']=11; RECORD['bench_positions']=8; RECORD['bench_nodes']=385792
    RECORD['bench_counters']={kind:counters('bench11-'+kind) for kind in diag_cores}
    for name in ['see_calls','exchange_plies','active_plies','candidate_origins','surviving_origins','max_candidates']:
        assert RECORD['bench_counters']['reference'][name]==RECORD['bench_counters']['mask'][name],name
    assert RECORD['bench_counters']['mask']['verification_shadow_queries']==0
    assert RECORD['bench_counters']['mask']['mask_states_verified']==0
    assert sha(SEMANTIC['original_core_path'])==SEMANTIC['original_core_sha256_before']
    assert all(sha(Path('/workspace/.cloud-setup/forge-pin-see-source')/p)==h for p,h in SEMANTIC['reference_source_sha256'].items())
    assert all(sha(p)==h for p,h in SEMANTIC['immutable_input_sha256_before'].items())
    RECORD['original_source_core_and_inputs_unchanged']=True
    RECORD['status']='PASS_EXACT_PARITY_WITH_OPERATION_COUNTS'
    RECORD['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
    print(json.dumps({k:RECORD[k] for k in ['status','bench_nodes','api_counters','bench_counters','engine_elapsed_seconds']}))
except BaseException as exc:
    RECORD['status']='FAILED_PRESERVE_ATTEMPT'; RECORD['error']=repr(exc); save(); raise
