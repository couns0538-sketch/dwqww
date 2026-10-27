#pragma once
#include <array>
#include <string_view>
#include <utility>
namespace forge_s14_fixture {
inline constexpr std::array<std::pair<std::string_view,std::string_view>,20> Workload{{
    {"white-start","rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"},
    {"black-start","rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"},
    {"black-stalemate","7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"},
    {"black-checkmate","7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"},
    {"white-diagonal-pin","7k/8/8/8/8/2b5/3P4/4K3 w - - 0 1"},
    {"black-diagonal-pin","4k3/3p4/2B5/8/8/8/8/7K b - - 0 1"},
    {"white-file-pin-legal-push","4r2k/8/8/8/8/8/4P3/4K3 w - - 0 1"},
    {"black-file-pin-legal-push","4k3/4p3/8/8/8/8/8/4R2K b - - 0 1"},
    {"pawn-blocks-check","7k/8/8/8/1b6/8/2P5/4K3 w - - 0 1"},
    {"double-check-pawn-does-not-evade","4r2k/8/8/8/1b6/8/2P5/4K3 w - - 0 1"},
    {"white-pinned-pawn-stalemate","8/8/8/8/4q3/8/5kP1/5n1K w - - 0 1"},
    {"black-pinned-pawn-stalemate","5N1k/5Kp1/8/4Q3/8/8/8/8 b - - 0 1"},
    {"white-quiet-promotion","4k3/P7/8/8/8/8/8/4K3 w - - 0 1"},
    {"black-quiet-promotion","4k3/8/8/8/8/8/7p/4K3 b - - 0 1"},
    {"white-capture-promotion","1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1"},
    {"black-capture-promotion","4k3/8/8/8/8/8/7p/4K1R1 b - - 0 1"},
    {"white-ep-forward-blocked","4k3/8/4p3/3pP3/8/8/8/4K3 w - d6 0 1"},
    {"black-ep-forward-blocked","4k3/8/8/8/3Pp3/4P3/8/4K3 b - d3 0 1"},
    {"illegal-ep-rank-pin","4k3/8/8/r4pPK/8/8/8/8 w - f6 0 1"},
    {"castles-no-pawn-witness","r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"},
}};
}
