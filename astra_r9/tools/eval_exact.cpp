// Diagnostic executable only; never used for timing or QA handover.
#include "forge/nnue.hpp"
#include "forge/eval.hpp"
#include "forge/search.hpp"
#include <algorithm>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static std::uint64_t digest = 1469598103934665603ULL;
static std::uint64_t positions = 0, moves = 0, nulls = 0;
static void mix(std::uint32_t v) { digest ^= v; digest *= 1099511628211ULL; }
static void inspect(const forge::Board& b, const forge::nnue::Accumulator& acc) {
    forge::nnue::Accumulator fresh;
    forge::nnue::refresh(b, fresh);
    for (int c=0;c<2;++c) for (int h=0;h<forge::nnue::HiddenSize;++h) {
        const auto x=std::bit_cast<std::uint32_t>(acc.values[c][h]);
        if (x != std::bit_cast<std::uint32_t>(fresh.values[c][h]))
            throw std::runtime_error("incremental/refresh mismatch: " + b.fen());
        mix(x);
    }
    const int value=forge::nnue::evaluate(b,acc);
#ifdef FORGE_NNUE_DIAGNOSTICS
    const auto lanes=forge::nnue::diagnostic_lanes;
    const auto output=std::bit_cast<std::uint32_t>(forge::nnue::diagnostic_output);
#endif
#ifdef R9_TEST_WIDE
    forge::nnue::wide_output = false;
    const int baseline=forge::nnue::evaluate(b,acc);
    forge::nnue::wide_output = true;
    if (value != baseline) throw std::runtime_error("OFF/ON mismatch: " + b.fen());
#ifdef FORGE_NNUE_DIAGNOSTICS
    for(int j=0;j<16;++j)
        if(std::bit_cast<std::uint32_t>(lanes[j]) != std::bit_cast<std::uint32_t>(forge::nnue::diagnostic_lanes[j]))
            throw std::runtime_error("lane float bits mismatch: " + b.fen());
    if(output != std::bit_cast<std::uint32_t>(forge::nnue::diagnostic_output))
        throw std::runtime_error("pre-conversion float bits mismatch: " + b.fen());
#endif
#endif
    mix(static_cast<std::uint32_t>(value));
    const int hce=forge::Evaluator::evaluate_uncached(b);
    mix(static_cast<std::uint32_t>(hce));
    const int combined=forge::nnue::residual() ? std::clamp(hce+value,-forge::MateInMaxPly+1,forge::MateInMaxPly-1) : value;
    mix(static_cast<std::uint32_t>(combined));
    ++positions;
}
int main(int argc, char** argv) {
    try {
        if (argc != 2) throw std::runtime_error("usage: eval_exact FENS");
        std::ifstream in(argv[1]); if(!in) throw std::runtime_error("missing corpus");
#ifdef R9_TEST_WIDE
        forge::nnue::wide_output = true;
#endif
        std::string fen; std::uint64_t count=0; std::vector<std::string> seeds;
        while(std::getline(in,fen)) {
            forge::Board b; if(!b.set_fen(fen)) throw std::runtime_error("bad FEN");
            forge::nnue::Accumulator acc; forge::nnue::refresh(b,acc); inspect(b,acc);
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
            if(count % 187 == 0 && seeds.size()<64) seeds.push_back(fen);
        }
        if(count<10000) throw std::runtime_error("corpus too small");
        std::uint64_t rng=0xA9D1FF;
        for(const auto& seed:seeds) {
            forge::Board b; if(!b.set_fen(seed)) throw std::runtime_error("bad seed");
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
            if(b.fen()!=seed) throw std::runtime_error("playout unmake state mismatch");
        }
#ifdef FORGE_NNUE_DIAGNOSTICS
        if(forge::nnue::wide_output_calls == 0) throw std::runtime_error("ON path not exercised");
        std::cerr << "wide_output_calls=" << forge::nnue::wide_output_calls << '\n';
#endif
        std::cout << "PASS fens=" << count << " positions=" << positions << " moves=" << moves
                  << " nulls=" << nulls << " digest=" << std::hex << digest << '\n';
    } catch(const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
