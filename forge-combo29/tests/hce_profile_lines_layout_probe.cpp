#include "forge/eval.hpp"
#include <iostream>
#include <cstddef>
struct ReorderedProbe {
 std::uint64_t key=0;
 forge::Score score=0;
 bool valid=false;
 std::array<forge::Bitboard,2> passed{};
};
int main() {
 using P=forge::Evaluator::PawnEntry;
 std::cout << "locked size=" << sizeof(P) << " align=" << alignof(P) << " key=" << offsetof(P,key) << " score=" << offsetof(P,score) << " passed=" << offsetof(P,passed) << " valid=" << offsetof(P,valid) << '\n';
 std::cout << "hypothesis size=" << sizeof(ReorderedProbe) << " align=" << alignof(ReorderedProbe) << " key=" << offsetof(ReorderedProbe,key) << " score=" << offsetof(ReorderedProbe,score) << " passed=" << offsetof(ReorderedProbe,passed) << " valid=" << offsetof(ReorderedProbe,valid) << '\n';
}
