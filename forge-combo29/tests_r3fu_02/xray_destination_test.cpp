#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <string>

namespace {

int failures = 0;

void expect(const char* fen, char from_file, char from_rank, char to_file, char to_rank, int expected) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cerr << "FAIL fen " << fen << " " << error << '\n';
        ++failures;
        return;
    }
    forge::Move move{};
    move.from = static_cast<std::uint8_t>((from_file - 'a') + (from_rank - '1') * 8);
    move.to = static_cast<std::uint8_t>((to_file - 'a') + (to_rank - '1') * 8);
    const int index = forge::quiet_threat_index(board, move);
    if (index != expected) {
        std::cerr << "FAIL " << fen << ' ' << from_file << from_rank << to_file << to_rank << " index " << index
                  << " expected " << expected << '\n';
        ++failures;
    }
}

}  // namespace

int main() {
    // Black rook on e8, white queen on e4. e3 is on the far side of the queen,
    // so the rook attacks it only after the queen is removed from occupancy.
    expect("4r2k/8/8/8/4Q3/8/8/4K3 w - - 0 1", 'e', '4', 'e', '3', 3);
    // e5 sits between the rook and the queen, so it is attacked with the queen still on e4.
    expect("4r2k/8/8/8/4Q3/8/8/4K3 w - - 0 1", 'e', '4', 'e', '5', 3);
    // d4 is off the rook's file. The queen is threatened; the destination is not.
    expect("4r2k/8/8/8/4Q3/8/8/4K3 w - - 0 1", 'e', '4', 'd', '4', 2);
    if (failures != 0) {
        std::cerr << failures << " failure(s)\n";
        return 1;
    }
    std::cout << "xray destination tests passed\n";
    return 0;
}
