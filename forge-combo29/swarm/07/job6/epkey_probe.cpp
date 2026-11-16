// epkey_probe.cpp -- control for PROBE 2 of board_probes.cpp.
//
// board_probes.cpp showed that a double push with NO possible capturer leaves the key
// unchanged (the ep term is correctly absent). That result only means something if the ep
// term is really included when a LEGAL ep capture exists. This program shows both sides:
//   (A) ep capture legal  -> key WITH ep term must differ from the same board without it
//   (B) ep capture illegal (the capturing pawn is pinned) -> key must NOT differ
#include "forge/board.hpp"

#include <cstdio>

using namespace forge;

int main() {
    // (A) ep capture legal. Black pawn d4, White pawn just arrived on e4, Black to move,
    //     ep square e3. The only difference between the two FENs is the ep field, and the
    //     side to move is the SAME in both, so any key difference is the ep term alone.
    Board a; (void)a.set_fen("4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1");
    Board a_ref; (void)a_ref.set_fen("4k3/8/8/8/3pP3/8/8/4K3 b - - 0 1");
    std::printf("A with ep   fen=[%s] key=%llu\n", a.fen().c_str(), (unsigned long long)a.key());
    std::printf("A no   ep   fen=[%s] key=%llu\n", a_ref.fen().c_str(), (unsigned long long)a_ref.key());
    const bool a_differs = a.key() != a_ref.key();
    std::printf("A keys differ = %s (must be yes: the ep term has to enter the key when a legal "
                "ep capture exists, otherwise probe2a's equality proved nothing)\n",
                a_differs ? "yes" : "NO");

    // (A2) ep capture ILLEGAL because the capturing pawn is pinned: the black pawn on d4 is
    //      pinned to its king on d8 by a white rook on d1. Capturing e3 would open the file.
    Board pin; (void)pin.set_fen("3k4/8/8/8/3pP3/8/8/3RK3 b - e3 0 1");
    Board pin_ref; (void)pin_ref.set_fen("3k4/8/8/8/3pP3/8/8/3RK3 b - - 0 1");
    std::printf("A2 pinned ep fen=[%s] key=%llu\n", pin.fen().c_str(), (unsigned long long)pin.key());
    std::printf("A2 pinned ref fen=[%s] key=%llu\n", pin_ref.fen().c_str(), (unsigned long long)pin_ref.key());
    const bool pinned_differs = pin.key() != pin_ref.key();
    std::printf("A2 keys differ = %s (must be NO: no legal ep capture, so the ep term must be absent)\n",
                pinned_differs ? "YES" : "no");

    // (B) ep capture illegal: the black pawn on d4 is pinned by the white rook on h4 down
    // the fourth rank to the black king on a4... construct with the king on the same rank as
    // the capturing pawn's destination, which is what an ep capture would vacate.
    Board b; (void)b.set_fen("k7/8/8/8/K2pP2r/8/8/8 b - - 0 1");
    std::printf("B constructed fen=[%s]\n", b.fen().c_str());
    std::printf("B key=%llu\n", (unsigned long long)b.key());

    return a_differs ? 0 : 1;
}
