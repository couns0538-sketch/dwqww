// R10 diagnostic only. Derived from Forge's own R9 eval_exact.cpp.
// Never a timing/QA production executable. No embedded weight is modified here.
#include "forge/nnue.hpp"
#include "forge/eval.hpp"
#include "forge/search.hpp"
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#ifndef FORGE_NNUE_DIAGNOSTICS
#error FORGE_NNUE_DIAGNOSTICS is required
#endif
#ifndef __AVX512F__
#error AVX512F is required to exercise NNUEWideOutput
#endif

using Bits = std::array<std::uint32_t,20>;
static std::uint64_t digest=1469598103934665603ULL, positions=0, moves=0, nulls=0;
static void mix(std::uint32_t v) { digest^=v; digest*=1099511628211ULL; }
struct Sample { Bits bits; std::uint64_t active; };

static Sample evaluate(const forge::Board& b,const forge::nnue::Accumulator& acc,bool wide) {
    forge::nnue::wide_output=wide;
    const auto before=forge::nnue::wide_output_calls;
    const int nnue=forge::nnue::evaluate(b,acc);
    Sample s{};
    s.active=forge::nnue::wide_output_calls-before;
    if(s.active!=(wide ? 1U : 0U)) throw std::runtime_error("wrong OFF/ON activation");
    for(int j=0;j<16;++j) s.bits[j]=std::bit_cast<std::uint32_t>(forge::nnue::diagnostic_lanes[j]);
    s.bits[16]=std::bit_cast<std::uint32_t>(forge::nnue::diagnostic_output);
    const int hce=forge::Evaluator::evaluate_uncached(b);
    const int combined=forge::nnue::residual() ? std::clamp(hce+nnue,-forge::MateInMaxPly+1,forge::MateInMaxPly-1) : nnue;
    s.bits[17]=static_cast<std::uint32_t>(nnue);
    s.bits[18]=static_cast<std::uint32_t>(hce);
    s.bits[19]=static_cast<std::uint32_t>(combined);
    return s;
}

static std::array<Sample,2> inspect(const forge::Board& b,const forge::nnue::Accumulator& acc) {
    forge::nnue::Accumulator fresh; forge::nnue::refresh(b,fresh);
    for(int c=0;c<2;++c) for(int h=0;h<forge::nnue::HiddenSize;++h) {
        const auto x=std::bit_cast<std::uint32_t>(acc.values[c][h]);
        if(x!=std::bit_cast<std::uint32_t>(fresh.values[c][h])) throw std::runtime_error("incremental/refresh mismatch: "+b.fen());
        mix(x);
    }
    const auto off=evaluate(b,acc,false), on=evaluate(b,acc,true);
    if(off.bits!=on.bits) throw std::runtime_error("OFF/ON component mismatch: "+b.fen());
    for(auto bits:off.bits) mix(bits);
    ++positions;
    return {off,on};
}

static void emit(std::ostream& out,std::uint64_t row,const std::string& fen,const Sample& s) {
    out << std::dec << row << '\t' << fen << '\t' << s.active;
    for(auto bits:s.bits) out << '\t' << std::hex << std::setfill('0') << std::setw(8) << bits;
    out << '\n';
    if(!out) throw std::runtime_error("trace write failed");
}

int main(int argc,char** argv) {
    try {
        if(argc!=5) throw std::runtime_error("usage: eval_components FENS OFF_TSV ON_TSV SEED");
        std::size_t used=0;
        const std::uint64_t seed=std::stoull(argv[4],&used,10);
        if(used!=std::string(argv[4]).size() || seed==0 || seed==0xA9D1FF) throw std::runtime_error("fresh nonzero decimal seed required");
        std::ifstream in(argv[1]); if(!in) throw std::runtime_error("missing corpus");
        for(int i=2;i<4;++i) if(std::filesystem::exists(argv[i])) throw std::runtime_error("trace already exists");
        std::ofstream off(argv[2]), on(argv[3]);
        if(!off || !on) throw std::runtime_error("cannot open new traces");
        off << "R10_COMPONENT_TRACE\t1\t" << seed << "\tOFF\n";
        on << "R10_COMPONENT_TRACE\t1\t" << seed << "\tON\n";
        std::string fen; std::uint64_t count=0; std::vector<std::string> seeds;
        while(std::getline(in,fen)) {
            if(!fen.empty() && fen.back()=='\r') fen.pop_back();
            if(fen.find('\t')!=std::string::npos) throw std::runtime_error("tab in corpus FEN");
            forge::Board b; if(!b.set_fen(fen)) throw std::runtime_error("bad FEN");
            forge::nnue::Accumulator acc; forge::nnue::refresh(b,acc);
            const auto pair=inspect(b,acc); emit(off,count,fen,pair[0]); emit(on,count,fen,pair[1]);
            for(const auto& m:b.legal_moves()) {
                const auto dirty=forge::nnue::dirty_pieces(b,m);
                forge::Undo undo; if(!b.make_move(m,undo)) throw std::runtime_error("illegal move");
                forge::nnue::Accumulator child; forge::nnue::update(acc,child,dirty);
                inspect(b,child); ++moves; b.unmake_move(m,undo); inspect(b,acc);
            }
            if(!b.in_check()) {
                forge::NullUndo undo; b.make_null_move(undo); inspect(b,acc); ++nulls;
                b.unmake_null_move(undo); inspect(b,acc);
            }
            ++count;
            if(count%187==0 && seeds.size()<64) seeds.push_back(fen);
        }
        if(count!=12000) throw std::runtime_error("corpus must contain exactly 12000 FENs");
        std::uint64_t rng=seed;
        for(const auto& start:seeds) {
            forge::Board b; if(!b.set_fen(start)) throw std::runtime_error("bad seed FEN");
            std::vector<forge::nnue::Accumulator> accumulators(129);
            std::vector<forge::Move> played; std::vector<forge::Undo> undos;
            forge::nnue::refresh(b,accumulators[0]);
            for(int ply=0;ply<128;++ply) {
                const auto legal=b.legal_moves(); if(legal.empty()) break;
                rng^=rng<<13; rng^=rng>>7; rng^=rng<<17;
                const auto m=legal[rng%legal.size()]; const auto dirty=forge::nnue::dirty_pieces(b,m);
                forge::Undo undo; if(!b.make_move(m,undo)) throw std::runtime_error("playout move");
                forge::nnue::update(accumulators[ply],accumulators[ply+1],dirty);
                played.push_back(m); undos.push_back(undo); inspect(b,accumulators[ply+1]); ++moves;
            }
            while(!played.empty()) {
                b.unmake_move(played.back(),undos.back()); played.pop_back(); undos.pop_back();
                inspect(b,accumulators[played.size()]);
            }
            if(b.fen()!=start) throw std::runtime_error("playout unmake state mismatch");
        }
        off.flush(); on.flush(); if(!off || !on) throw std::runtime_error("trace flush failed");
        if(forge::nnue::wide_output_calls!=positions) throw std::runtime_error("ON global count mismatch");
        std::cout << "PASS fens=" << count << " positions=" << positions << " moves=" << moves << " nulls=" << nulls
                  << " wide_output_calls=" << forge::nnue::wide_output_calls << " seed=" << seed << " digest=" << std::hex << digest << '\n';
    } catch(const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
