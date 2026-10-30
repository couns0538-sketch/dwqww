// R8 v5 test engine: a minimal UCI engine (Forge Board; plays a legal move with a small fake score, no search) that
// hangs or exits on purpose, to test forge_selfplay_fast's engine deadline, restart and give-up paths.
// Mode from the environment variable FORGE_FAKE_ENGINE:
//   hang:K[:FLAG]  stop answering at the K-th `go` (sleeps forever); with FLAG only while the file FLAG does not exist:
//                  the first engine creates FLAG and hangs, a restarted engine behaves
//   exit:K[:FLAG]  exit (code 3) at the K-th `go`, same FLAG rule
//   dead           exit at once (every start fails)
//   unset/empty    always answer
#include "forge/board.hpp"

#include <windows.h>

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>

using namespace forge;

int main() {
    const char* env = std::getenv("FORGE_FAKE_ENGINE");
    std::string mode = env ? env : "", kind, flag;
    int k = 0;
    {
        std::istringstream in(mode);
        std::getline(in, kind, ':');
        std::string n;
        std::getline(in, n, ':');
        k = n.empty() ? 0 : std::atoi(n.c_str());
        std::getline(in, flag);
    }
    if (kind == "dead") return 3;
    bool armed = kind == "hang" || kind == "exit";
    if (armed && !flag.empty()) {
        if (GetFileAttributesA(flag.c_str()) != INVALID_FILE_ATTRIBUTES) {
            armed = false;
        } else {
            HANDLE h = CreateFileA(flag.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
            if (h != INVALID_HANDLE_VALUE) CloseHandle(h);
        }
    }
    Board b;
    (void)b.set_fen(Board::StandardStartFen);
    int gos = 0;
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line == "uci") {
            std::cout << "id name fake_engine\nuciok" << std::endl;
        } else if (line == "isready") {
            std::cout << "readyok" << std::endl;
        } else if (line == "quit") {
            return 0;
        } else if (line.rfind("position startpos", 0) == 0) {
            (void)b.set_fen(Board::StandardStartFen);
            std::istringstream in(line.substr(17));
            std::string word;
            while (in >> word) {
                if (word == "moves") continue;
                const auto m = b.parse_uci(word);
                if (!m) break;
                Undo u;
                (void)b.make_move(*m, u);
            }
        } else if (line.rfind("go", 0) == 0) {
            ++gos;
            if (armed && gos == k) {
                if (kind == "hang")
                    for (;;) Sleep(1000);
                return 3;
            }
            const MoveList legal = b.legal_moves();
            if (legal.size() == 0) {
                std::cout << "bestmove 0000" << std::endl;
                continue;
            }
            const Move mv = legal[static_cast<std::size_t>((b.key() >> 7) % legal.size())];
            std::cout << "info depth 1 score cp " << static_cast<int>(b.key() % 61) - 30 << " nodes 1\nbestmove "
                      << Board::move_to_uci(mv) << std::endl;
        }
    }
    return 0;
}
