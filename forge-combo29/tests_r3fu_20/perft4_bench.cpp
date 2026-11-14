// Perft 4 of the eight bench positions. The expected node totals are the base
// engine's answers. Build this file alone and pass the engine binary:
//   g++ -O2 -std=c++20 tests_r3fu_20/perft4_bench.cpp -o perft4_bench
//   ./perft4_bench ./forge

#include <array>
#include <iostream>
#include <string>
#include <sys/wait.h>
#include <unistd.h>

namespace {

struct Engine {
    pid_t pid = -1;
    FILE* to_engine = nullptr;
    FILE* from_engine = nullptr;
};

bool start_engine(Engine& engine, const char* path) {
    int to_child[2];
    int from_child[2];
    if (pipe(to_child) != 0 || pipe(from_child) != 0) return false;
    const pid_t pid = fork();
    if (pid < 0) return false;
    if (pid == 0) {
        dup2(to_child[0], STDIN_FILENO);
        dup2(from_child[1], STDOUT_FILENO);
        close(to_child[0]);
        close(to_child[1]);
        close(from_child[0]);
        close(from_child[1]);
        execl(path, path, static_cast<char*>(nullptr));
        _exit(127);
    }
    close(to_child[0]);
    close(from_child[1]);
    engine.pid = pid;
    engine.to_engine = fdopen(to_child[1], "w");
    engine.from_engine = fdopen(from_child[0], "r");
    return engine.to_engine != nullptr && engine.from_engine != nullptr;
}

void send(Engine& engine, const std::string& line) {
    fputs(line.c_str(), engine.to_engine);
    fputc('\n', engine.to_engine);
    fflush(engine.to_engine);
}

std::string read_line(Engine& engine) {
    char buffer[65536];
    if (fgets(buffer, sizeof buffer, engine.from_engine) == nullptr) return {};
    std::string line(buffer);
    while (!line.empty() && (line.back() == '\n' || line.back() == '\r')) line.pop_back();
    return line;
}

std::string until_prefix(Engine& engine, const std::string& prefix) {
    for (;;) {
        const std::string line = read_line(engine);
        if (line.empty() && feof(engine.from_engine)) return {};
        if (line.compare(0, prefix.size(), prefix) == 0) return line;
    }
}

struct Case {
    const char* fen;
    const char* nodes;
};

constexpr std::array<Case, 8> kCases{{
    {"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "197281"},
    {"r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "4085603"},
    {"r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10", "3269539"},
    {"8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "43238"},
    {"r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8", "1635300"},
    {"2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", "3813973"},
    {"6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1", "24244"},
    {"r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9", "2433324"},
}};

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: perft4_bench <engine>\n";
        return 2;
    }
    Engine engine;
    if (!start_engine(engine, argv[1])) {
        std::cerr << "could not start engine\n";
        return 2;
    }
    send(engine, "uci");
    if (until_prefix(engine, "uciok").empty()) return 2;
    int failures = 0;
    for (const Case& item : kCases) {
        send(engine, std::string("position fen ") + item.fen);
        send(engine, "go perft 4");
        const std::string line = until_prefix(engine, "nodes ");
        const std::string got = line.size() > 6 ? line.substr(6) : std::string{};
        if (got != item.nodes) {
            std::cerr << "perft mismatch " << item.fen << " expected " << item.nodes << " got " << got << "\n";
            ++failures;
        }
    }
    send(engine, "quit");
    int status = 0;
    waitpid(engine.pid, &status, 0);
    if (failures != 0) {
        std::cerr << "perft4 failures " << failures << "\n";
        return 1;
    }
    std::cout << "perft4 bench positions 8/8\n";
    return 0;
}
