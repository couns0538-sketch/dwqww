// what does a king-square "null" move (from == to) become after binpack's CompressedMove round trip?
#include "lib/binpack.h"
#include <cstdio>
int main() {
    auto pos = chess::Position::fromFen("4k3/8/8/8/8/8/8/4K3 w - - 0 1");
    const chess::Square ksq = pos.kingSquare(pos.sideToMove());
    binpack::TrainingDataEntry e;
    e.pos = pos; e.move = chess::Move{ksq, ksq}; e.score = 12; e.ply = 40; e.result = 0;
    const auto packed = binpack::packEntry(e);
    const auto back = binpack::unpackEntry(packed);
    std::printf("ksq %d -> from %d to %d type %d (orig type %d)\n", (int)chess::ordinal(ksq), (int)chess::ordinal(back.move.from),
                (int)chess::ordinal(back.move.to), (int)chess::ordinal(back.move.type), (int)chess::ordinal(e.move.type));
    std::printf("moves equal: %d\n", (int)(back.move == e.move));
    return 0;
}
