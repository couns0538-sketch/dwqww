// Exercise the actual private Worker path; the public evaluator remains the oracle.
#include "forge/search.hpp"
#include "forge/eval_params.hpp"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static SearchStack* root(Worker& w) { return &w.stack_[4]; }
    static int eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void move(Worker& w, SearchStack* ss, const Board& b, Move m) { w.record_move(ss,b,m); (ss+1)->ply=ss->ply+1; }
    template<class W=Worker> static void null(W& w, SearchStack* ss) {
        if constexpr (requires { w.record_null_move(ss); }) w.record_null_move(ss);
        else { (ss+1)->dirty.count=0; (ss+1)->accumulator.valid=false; }
        (ss+1)->ply=ss->ply+1;
    }
    template<class S=SearchStack> static bool valid(const S* ss) {
        if constexpr (requires { ss->runtime_psqt.valid; }) return ss->runtime_psqt.valid;
        else return false;
    }
    template<class S=SearchStack> static Score score(const S* ss) {
        if constexpr (requires { ss->runtime_psqt.score; }) return ss->runtime_psqt.score;
        else return 0;
    }
    template<class S=SearchStack> static int phase(const S* ss) {
        if constexpr (requires { ss->runtime_psqt.phase; }) return ss->runtime_psqt.phase;
        else return -1;
    }
    template<class S=SearchStack> static void invalidate(S* ss) {
        if constexpr (requires { ss->runtime_psqt.valid; }) ss->runtime_psqt.valid=false;
    }
    template<class S=SearchStack> static void poison(S* ss) {
        if constexpr (requires { ss->runtime_psqt.valid; }) {
            ss->runtime_psqt.score=123; ss->runtime_psqt.phase=-7; ss->runtime_psqt.valid=true;
        }
    }
};
}
using namespace forge;
using Probe=SearcherTestProbe;
namespace {
int checks=0,failures=0;
void check(bool okay,const std::string& label) { ++checks; if(!okay) ++failures; std::cout<<(okay?"PASS ":"FAIL ")<<label<<'\n'; }
Board position(const std::string& fen) { Board b; std::string error; if(!b.set_fen(fen,&error)) throw std::runtime_error(fen+": "+error); return b; }
Move move(Board& b,const std::string& text) { const auto m=b.parse_uci(text); if(!m) throw std::runtime_error("illegal fixture "+text+" in "+b.fen()); return *m; }
std::pair<Score,int> oracle(const Board& b) {
    Score score=0; int phase=0;
    for(int square=0;square<64;++square) {
        const Piece p=b.piece_at(square); if(p==Empty) continue;
        const int type=piece_type(p); phase+=PhaseValue[static_cast<std::size_t>(type)];
        const Score term=params::table[static_cast<std::size_t>(params::Psqt+(type-1)*64+(color_of(p)==White?square:flip_square(square)))];
        score+=color_of(p)==White?term:-term;
    }
    return {score,phase};
}
void verify(Worker& w,const Board& b,SearchStack* ss,const std::string& label) {
    const int actual=Probe::eval(w,b,ss);
    const int hce=Evaluator::evaluate_uncached(b);
    const int expected=nnue::enabled && nnue::available()
        ? std::clamp(hce+nnue::evaluate(b,ss->accumulator),-MateInMaxPly+1,MateInMaxPly-1):hce;
    check(actual==expected,label+" actual Worker evaluation equals full oracle with same NNUE accumulator");
    if(nnue::enabled && nnue::available() && nnue::residual()) {
        const auto [score,phase]=oracle(b);
        check(Probe::valid(ss),label+" private runtime cache valid");
        check(Probe::score(ss)==score,label+" exact packed PSQT");
        check(Probe::phase(ss)==phase,label+" exact unclamped phase");
    }
}
SearchStack* begin(Worker& w,const Board& b) {
    w.clear(); SearchLimits limits; limits.depth=1;
    const std::vector<Worker*> all{&w}; (void)w.search(b,limits,false,all);
    return Probe::root(w);
}
void edge(Worker& w,Board b,const std::string& text,const std::string& label) {
    SearchStack* ss=begin(w,b); verify(w,b,ss,label+" root");
    const Move m=move(b,text); Probe::move(w,ss,b,m); check(!Probe::valid(ss+1),label+" child invalidated");
    Undo undo; (void)b.make_move(m,undo); verify(w,b,ss+1,label+" child");
    verify(w,b,ss+1,label+" same-ply reuse"); b.unmake_move(m,undo); verify(w,b,ss,label+" unmade parent");
}
}
int main() {
    check(nnue::available() && nnue::residual(),"fixture uses current compiled residual network");
    SharedSearchState shared(1); auto owned=std::make_unique<Worker>(shared,0); Worker& w=*owned;
    edge(w,position(std::string(Board::StandardStartFen)),"g1f3","quiet");
    edge(w,position("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1"),"e4d5","capture");
    edge(w,position("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"),"e5d6","en passant");
    for(const auto& [side,from,to]:std::vector<std::tuple<std::string,std::string,std::string>>{{"w","e1","g1"},{"w","e1","c1"},{"b","e8","g8"},{"b","e8","c8"}})
        edge(w,position("r3k2r/8/8/8/8/8/8/R3K2R "+side+" KQkq - 0 1"),from+to,"castle "+from+to);
    for(char promotion:std::string("qrbn")) {
        edge(w,position("4k3/P7/8/8/8/8/8/4K3 w - - 0 1"),"a7a8"+std::string(1,promotion),"white promotion "+std::string(1,promotion));
        edge(w,position("4k3/8/8/8/8/8/p7/4K3 b - - 0 1"),"a2a1"+std::string(1,promotion),"black promotion "+std::string(1,promotion));
    }
    edge(w,position("1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1"),"a7b8q","capture promotion");
    edge(w,position("r1bqkbnr/pppppppp/8/8/3n4/1N6/1PPPPPPP/RNBQKBNR w KQkq - 0 1"),"b3d4","raw phase25 to24 capture");

    Board chain=position(std::string(Board::StandardStartFen)); SearchStack* root=begin(w,chain); SearchStack* ss=root;
    std::vector<std::pair<Move,Undo>> history;
    for(const std::string text:{"e2e4","d7d5","e4d5","g8f6"}) {
        const Move m=move(chain,text); Probe::move(w,ss,chain,m); Undo undo; (void)chain.make_move(m,undo); history.emplace_back(m,undo); ++ss;
    }
    verify(w,chain,ss,"four unevaluated ancestor edges");
    Probe::invalidate(ss); verify(w,chain,ss,"NNUE valid PSQT invalid fallback");
    Probe::invalidate(ss-1); ss->accumulator.valid=false; Probe::poison(ss);
    verify(w,chain,ss,"NNUE replay with invalid PSQT ancestor fallback");
    while(!history.empty()) { chain.unmake_move(history.back().first,history.back().second); history.pop_back(); --ss; }
    verify(w,chain,root,"full chain unmake");
    for(const std::string text:{"b1c3","g1f3","d2d4"}) {
        const Move m=move(chain,text); Probe::move(w,root,chain,m); Undo undo; (void)chain.make_move(m,undo); verify(w,chain,root+1,"sibling "+text); chain.unmake_move(m,undo);
    }
    Probe::null(w,root); check(!Probe::valid(root+1),"null invalidates stale sibling"); NullUndo null; chain.make_null_move(null);
    verify(w,chain,root+1,"zero-dirty null child");
    const Move after_null=move(chain,"g8f6"); Probe::move(w,root+1,chain,after_null); Undo after; (void)chain.make_move(after_null,after);
    verify(w,chain,root+2,"real child after null"); chain.unmake_move(after_null,after); chain.unmake_null_move(null);
    verify(w,chain,root,"null unmake parent");

    Board before=position("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1"); const params::Table original=params::table;
    struct Restore { params::Table saved; ~Restore(){params::table=saved;nnue::enabled=true;} } restore{original};
    Evaluator evaluator; EvalTrace old_trace; (void)evaluate_traced(before,old_trace);
    const int old_eval=evaluator.evaluate(before);
    const int index=params::Psqt+28; // White pawn e4: this Board predates the table mutation.
    params::table[static_cast<std::size_t>(index)]+=S(17,23);
    EvalTrace trace; const int direct=Evaluator::evaluate_uncached(before);
    check(direct==old_eval+17,"PSQT mutation changes the actual occupied-square evaluation");
    check(evaluator.evaluate(before)==direct,"public evaluate sees mutation after FEN");
    check(evaluate_traced(before,trace)==direct,"public trace sees current PSQT after FEN");
    check(trace.coefficients[static_cast<std::size_t>(index)]==1,"public trace retains occupied-square PSQT coefficient");
    check(trace.coefficients==old_trace.coefficients && trace.phase==old_trace.phase && trace.scale==old_trace.scale,
          "table mutation preserves all public trace coefficients phase and scale");
    root=begin(w,before); verify(w,before,root,"new search current mutated params");
    params::table=original; check(evaluator.evaluate(before)==old_eval,"same public Evaluator sees restored params");
    check(params::table==params::defaults(),"default parameter table restored");
    SearchLimits limits; limits.depth=1; const std::vector<Worker*> all{&w}; (void)w.search(before,limits,false,all);
    verify(w,before,Probe::root(w),"reused Worker new search after params restored");
    nnue::enabled=false; verify(w,before,Probe::root(w),"NNUE-disabled original public HCE path"); nnue::enabled=true;
    std::cout<<"SUMMARY checks="<<checks<<" failures="<<failures<<'\n'; return failures==0?0:1;
}
