// Depth-8 identity against a recorded base run.
// Each expected line is: bestmove, score ("cp N" or "mate N"), nodes, fen, tab-separated.
// Threads 1, Hash 16, OwnBook false, ucinewgame before every position, go depth 8.
//
//   g++ -O2 -std=c++20 tests_r3fu_20/depth8_compare.cpp -o depth8_compare
//   ./depth8_compare --emit <base-engine> <fens> > tests_r3fu_20/depth8_expected.txt
//   ./depth8_compare <engine> tests_r3fu_20/depth8_expected.txt

#include <iostream>
#include <string>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

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

void prepare(Engine& engine) {
    send(engine, "uci");
    until_prefix(engine, "uciok");
    send(engine, "setoption name Threads value 1");
    send(engine, "setoption name Hash value 16");
    send(engine, "setoption name OwnBook value false");
    send(engine, "isready");
    until_prefix(engine, "readyok");
}

struct Result {
    std::string best;
    std::string score;
    std::string nodes;
};

std::string field_after(const std::string& line, const std::string& key) {
    const std::string token = key + " ";
    const std::size_t at = line.find(token);
    if (at == std::string::npos) return {};
    const std::size_t start = at + token.size();
    const std::size_t end = line.find(' ', start);
    return line.substr(start, end == std::string::npos ? std::string::npos : end - start);
}

Result search_depth8(Engine& engine, const std::string& fen) {
    send(engine, "ucinewgame");
    send(engine, "isready");
    until_prefix(engine, "readyok");
    send(engine, "position fen " + fen);
    send(engine, "go depth 8");
    std::string score;
    std::string nodes;
    for (;;) {
        const std::string line = read_line(engine);
        if (line.empty() && feof(engine.from_engine)) break;
        if (line.compare(0, 10, "info depth") == 0) {
            const std::string kind = field_after(line, "score");
            const std::size_t score_at = line.find("score ");
            std::string second;
            if (score_at != std::string::npos) {
                const std::size_t first = score_at + 6;
                const std::size_t gap = line.find(' ', first);
                if (gap != std::string::npos) {
                    const std::size_t second_at = gap + 1;
                    const std::size_t second_end = line.find(' ', second_at);
                    second = line.substr(second_at, second_end == std::string::npos ? std::string::npos : second_end - second_at);
                }
            }
            if (!kind.empty() && !second.empty()) score = kind + " " + second;
            nodes = field_after(line, "nodes");
        } else if (line.compare(0, 9, "bestmove ") == 0) {
            Result result;
            result.best = line.substr(9);
            const std::size_t space = result.best.find(' ');
            if (space != std::string::npos) result.best.resize(space);
            result.score = score;
            result.nodes = nodes;
            return result;
        }
    }
    return {};
}

std::vector<std::string> split_tabs(const std::string& line) {
    std::vector<std::string> fields;
    std::size_t start = 0;
    for (;;) {
        const std::size_t tab = line.find('\t', start);
        if (tab == std::string::npos) {
            fields.push_back(line.substr(start));
            break;
        }
        fields.push_back(line.substr(start, tab - start));
        start = tab + 1;
    }
    return fields;
}

}  // namespace

int main(int argc, char** argv) {
    const bool emit = argc == 4 && std::string(argv[1]) == "--emit";
    if (!emit && argc != 3) {
        std::cerr << "usage: depth8_compare <engine> <expected>\n"
                     "       depth8_compare --emit <engine> <fens>\n";
        return 2;
    }
    Engine engine;
    const char* binary = emit ? argv[2] : argv[1];
    if (!start_engine(engine, binary)) {
        std::cerr << "could not start engine\n";
        return 2;
    }
    prepare(engine);
    if (emit) {
        FILE* fens = fopen(argv[3], "r");
        if (fens == nullptr) return 2;
        char buffer[4096];
        int count = 0;
        while (fgets(buffer, sizeof buffer, fens) != nullptr) {
            std::string fen(buffer);
            while (!fen.empty() && (fen.back() == '\n' || fen.back() == '\r')) fen.pop_back();
            if (fen.empty()) continue;
            const Result result = search_depth8(engine, fen);
            std::cout << result.best << '\t' << result.score << '\t' << result.nodes << '\t' << fen << '\n';
            ++count;
        }
        fclose(fens);
        send(engine, "quit");
        waitpid(engine.pid, nullptr, 0);
        std::cerr << "emitted " << count << "\n";
        return 0;
    }

    FILE* expected = fopen(argv[2], "r");
    if (expected == nullptr) return 2;
    char buffer[8192];
    int count = 0;
    int failures = 0;
    while (fgets(buffer, sizeof buffer, expected) != nullptr) {
        std::string line(buffer);
        while (!line.empty() && (line.back() == '\n' || line.back() == '\r')) line.pop_back();
        if (line.empty()) continue;
        const std::vector<std::string> fields = split_tabs(line);
        if (fields.size() != 4) {
            std::cerr << "bad record " << count << "\n";
            return 2;
        }
        const Result got = search_depth8(engine, fields[3]);
        if (got.best != fields[0] || got.score != fields[1] || got.nodes != fields[2]) {
            if (failures < 8) {
                std::cerr << "mismatch " << count << "\n expected " << fields[0] << " " << fields[1] << " " << fields[2]
                          << "\n got      " << got.best << " " << got.score << " " << got.nodes << "\n";
            }
            ++failures;
        }
        ++count;
    }
    fclose(expected);
    send(engine, "quit");
    waitpid(engine.pid, nullptr, 0);
    if (failures != 0) {
        std::cerr << "depth8 failures " << failures << " of " << count << "\n";
        return 1;
    }
    std::cout << "depth8 " << count << "/" << count << "\n";
    return 0;
}
