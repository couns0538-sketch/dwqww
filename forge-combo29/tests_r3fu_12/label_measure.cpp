#include "forge/board.hpp"

#include <charconv>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <cerrno>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <unordered_set>
#include <utility>
#include <vector>

#include <poll.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

// Fixed-seed self-play walk, then three searches per position:
// go nodes 5000, go softnodes 5000, and go depth 16 as the reference.
// A contract miss or a summary that does not match the log exits non-zero.

namespace {

constexpr int kPositions = 10000;
constexpr int kWalkDepth = 4;
constexpr int kReferenceDepth = 16;
constexpr std::uint64_t kBudget = 5000;
constexpr std::uint64_t kSeed = 0x5212f00d5eedULL;
constexpr const char* kDir = "forge-combo29/tests_r3fu_12";

class Engine {
public:
    explicit Engine(const std::string& path) {
        int to_child[2];
        int from_child[2];
        if (pipe(to_child) != 0 || pipe(from_child) != 0) fail("pipe");
        pid_ = fork();
        if (pid_ < 0) fail("fork");
        if (pid_ == 0) {
            dup2(to_child[0], STDIN_FILENO);
            dup2(from_child[1], STDOUT_FILENO);
            close(to_child[0]);
            close(to_child[1]);
            close(from_child[0]);
            close(from_child[1]);
            execl(path.c_str(), path.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        close(to_child[0]);
        close(from_child[1]);
        write_fd_ = to_child[1];
        read_fd_ = from_child[0];
    }

    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    ~Engine() {
        if (pid_ > 0) (void)finish();
    }

    int finish() {
        if (pid_ <= 0) return 0;
        send("quit\n");
        close(write_fd_);
        close(read_fd_);
        write_fd_ = -1;
        read_fd_ = -1;
        int status = 0;
        waitpid(pid_, &status, 0);
        pid_ = -1;
        return status;
    }

    void send(const std::string& text) {
        const char* data = text.data();
        std::size_t left = text.size();
        while (left > 0) {
            const ssize_t wrote = ::write(write_fd_, data, left);
            if (wrote < 0) {
                if (errno == EINTR) continue;
                fail("write");
            }
            data += wrote;
            left -= static_cast<std::size_t>(wrote);
        }
    }

    bool read_line(std::string& line, std::chrono::steady_clock::time_point deadline) {
        for (;;) {
            const auto split = pending_.find('\n');
            if (split != std::string::npos) {
                line = pending_.substr(0, split);
                if (!line.empty() && line.back() == '\r') line.pop_back();
                pending_.erase(0, split + 1);
                return true;
            }
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                deadline - std::chrono::steady_clock::now());
            if (left.count() <= 0) return false;
            pollfd pfd{};
            pfd.fd = read_fd_;
            pfd.events = POLLIN;
            const int polled = ::poll(&pfd, 1, static_cast<int>(left.count()));
            if (polled < 0) {
                if (errno == EINTR) continue;
                return false;
            }
            if (polled == 0) return false;
            char buffer[4096];
            const ssize_t got = ::read(read_fd_, buffer, sizeof buffer);
            if (got < 0) {
                if (errno == EINTR) continue;
                return false;
            }
            if (got == 0) return false;
            pending_.append(buffer, buffer + got);
        }
    }

    bool wait_ready(int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        std::string line;
        while (read_line(line, deadline)) {
            if (line == "readyok") return true;
        }
        return false;
    }

private:
    [[noreturn]] void fail(const char* what) {
        std::cerr << "engine io " << what << std::endl;
        std::exit(2);
    }

    pid_t pid_ = -1;
    int write_fd_ = -1;
    int read_fd_ = -1;
    std::string pending_;
};

struct Search {
    bool ok = false;
    bool saw_soft = false;
    int depth = -1;
    std::uint64_t info_nodes = 0;
    std::uint64_t soft_nodes = 0;
    std::string best;
    std::string score;
};

struct Row {
    int index = -1;
    std::string fen;
    std::string nodes_move;
    std::string nodes_score;
    int nodes_depth = -1;
    std::uint64_t nodes_info = 0;
    std::uint64_t nodes_used = 0;
    std::string soft_move;
    std::string soft_score;
    int soft_depth = -1;
    std::uint64_t soft_used = 0;
    std::string ref_move;
    std::string ref_score;
    std::uint64_t ref_nodes = 0;
};

struct Totals {
    int positions = 0;
    long long nodes_mae_sum = 0;
    long long nodes_mae_n = 0;
    long long nodes_agree = 0;
    long long nodes_node_sum = 0;
    long long soft_mae_sum = 0;
    long long soft_mae_n = 0;
    long long soft_agree = 0;
    long long soft_node_sum = 0;
};

std::string positions_path() { return std::string(kDir) + "/positions.txt"; }
std::string shard_path(int shard) { return std::string(kDir) + "/shard_" + std::to_string(shard) + ".txt"; }
std::string summary_path() { return std::string(kDir) + "/summary.txt"; }

[[noreturn]] void die(const std::string& why) {
    std::cerr << "FAIL " << why << std::endl;
    std::exit(1);
}

std::uint64_t mix(std::uint64_t& state) {
    state = state * 6364136223846793005ULL + 1ULL;
    return state;
}

bool quiet_position(const forge::Board& board) {
    return board.legal_moves().empty() || board.is_repetition() || board.halfmove_clock() >= 100 ||
           board.is_insufficient_material();
}

bool move_is_legal(const std::string& fen, const std::string& uci) {
    forge::Board board;
    if (!board.set_fen(fen)) return false;
    const std::optional<forge::Move> parsed = board.parse_uci(uci);
    if (!parsed.has_value() || parsed->is_none()) return false;
    const forge::MoveList moves = board.legal_moves();
    for (std::size_t i = 0; i < moves.size(); ++i) {
        if (moves[i] == *parsed) return true;
    }
    return false;
}

void prepare(Engine& engine) {
    engine.send("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
                "setoption name OwnBook value false\nisready\n");
    if (!engine.wait_ready(10000)) die("engine did not answer readyok");
}

bool place(Engine& engine, const std::string& fen) {
    engine.send("ucinewgame\nposition fen " + fen + "\nisready\n");
    return engine.wait_ready(10000);
}

Search wait_bestmove(Engine& engine, int timeout_ms) {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
    Search result;
    std::string line;
    while (engine.read_line(line, deadline)) {
        if (line.compare(0, 9, "bestmove ") == 0) {
            std::istringstream input(line);
            std::string tag;
            input >> tag >> result.best;
            result.ok = !result.best.empty();
            return result;
        }
        constexpr std::string_view kSoft = "info string softnodes nodes ";
        if (line.compare(0, kSoft.size(), kSoft) == 0) {
            result.soft_nodes = std::strtoull(line.c_str() + kSoft.size(), nullptr, 10);
            result.saw_soft = true;
            continue;
        }
        if (line.compare(0, 5, "info ") != 0 || line.compare(0, 11, "info string") == 0) continue;
        std::istringstream input(line);
        std::string token;
        input >> token;
        while (input >> token) {
            if (token == "depth") {
                input >> result.depth;
            } else if (token == "score") {
                std::string kind;
                std::string value;
                input >> kind >> value;
                if ((kind == "cp" || kind == "mate") && !value.empty()) result.score = kind + ":" + value;
            } else if (token == "nodes") {
                input >> result.info_nodes;
            } else if (token == "pv") {
                break;
            }
        }
    }
    return result;
}

Search go_fen(Engine& engine, const std::string& fen, const std::string& command, int timeout_ms) {
    if (!place(engine, fen)) die("ready failed before " + command);
    engine.send(command + "\n");
    Search result = wait_bestmove(engine, timeout_ms);
    if (!result.ok) die(command + " produced no bestmove for " + fen);
    return result;
}

bool mate_score(const std::string& score) { return score.rfind("mate:", 0) == 0; }

bool cp_score(const std::string& score, long long& value) {
    if (score.rfind("cp:", 0) != 0) return false;
    const std::string text = score.substr(3);
    const auto parsed = std::from_chars(text.data(), text.data() + text.size(), value);
    return parsed.ec == std::errc{} && parsed.ptr == text.data() + text.size();
}

std::uint64_t hard_nodes_used(const Search& search) {
    if (search.info_nodes > kBudget) die("go nodes finished an iteration above 5000");
    if (search.depth >= 64 && search.info_nodes < kBudget) return search.info_nodes;
    return kBudget;
}

void check_search_contract(const Row& row) {
    if (!move_is_legal(row.fen, row.nodes_move) || !move_is_legal(row.fen, row.soft_move) ||
        !move_is_legal(row.fen, row.ref_move)) {
        die("illegal move at " + std::to_string(row.index) + " " + row.fen);
    }
    if (row.nodes_score.empty() || row.soft_score.empty() || row.ref_score.empty()) {
        die("missing score at " + std::to_string(row.index));
    }
    if (row.nodes_depth < 1 || row.soft_depth < 1 || row.ref_move.empty()) {
        die("unfinished search at " + std::to_string(row.index));
    }
    if (row.nodes_info > kBudget) die("go nodes info above budget at " + std::to_string(row.index));
    const std::uint64_t expect_used =
        (row.nodes_depth >= 64 && row.nodes_info < kBudget) ? row.nodes_info : kBudget;
    if (row.nodes_used != expect_used) die("go nodes used mismatch at " + std::to_string(row.index));
    if (row.soft_used > kBudget * 4) die("softnodes above 4N at " + std::to_string(row.index));
    if (row.soft_used < kBudget && row.soft_depth < 64) {
        die("softnodes stopped under N before depth 64 at " + std::to_string(row.index));
    }
    if (row.ref_nodes == 0) die("reference reported no nodes at " + std::to_string(row.index));
}

std::string row_line(const Row& row) {
    std::ostringstream out;
    out << row.index << '|' << row.nodes_move << '|' << row.nodes_score << '|' << row.nodes_depth << '|'
        << row.nodes_info << '|' << row.nodes_used << '|' << row.soft_move << '|' << row.soft_score << '|'
        << row.soft_depth << '|' << row.soft_used << '|' << row.ref_move << '|' << row.ref_score << '|'
        << row.ref_nodes << '|' << row.fen;
    return out.str();
}

std::vector<std::string> split_fields(const std::string& line) {
    std::vector<std::string> fields;
    std::string cur;
    for (const char ch : line) {
        if (ch == '|') {
            fields.push_back(cur);
            cur.clear();
        } else {
            cur.push_back(ch);
        }
    }
    fields.push_back(cur);
    return fields;
}

bool parse_row(const std::string& line, Row& row) {
    const std::vector<std::string> fields = split_fields(line);
    if (fields.size() != 14) return false;
    const auto index = std::from_chars(fields[0].data(), fields[0].data() + fields[0].size(), row.index);
    const auto nd = std::from_chars(fields[3].data(), fields[3].data() + fields[3].size(), row.nodes_depth);
    const auto ni = std::from_chars(fields[4].data(), fields[4].data() + fields[4].size(), row.nodes_info);
    const auto nu = std::from_chars(fields[5].data(), fields[5].data() + fields[5].size(), row.nodes_used);
    const auto sd = std::from_chars(fields[8].data(), fields[8].data() + fields[8].size(), row.soft_depth);
    const auto su = std::from_chars(fields[9].data(), fields[9].data() + fields[9].size(), row.soft_used);
    const auto rn = std::from_chars(fields[12].data(), fields[12].data() + fields[12].size(), row.ref_nodes);
    if (index.ec != std::errc{} || nd.ec != std::errc{} || ni.ec != std::errc{} || nu.ec != std::errc{} ||
        sd.ec != std::errc{} || su.ec != std::errc{} || rn.ec != std::errc{}) {
        return false;
    }
    row.nodes_move = fields[1];
    row.nodes_score = fields[2];
    row.soft_move = fields[6];
    row.soft_score = fields[7];
    row.ref_move = fields[10];
    row.ref_score = fields[11];
    row.fen = fields[13];
    return !row.fen.empty();
}

void add_pair(long long& mae_sum, long long& mae_n, long long& agree, const std::string& score,
              const std::string& move, const std::string& ref_score, const std::string& ref_move) {
    if (move == ref_move) ++agree;
    if (mate_score(score) || mate_score(ref_score)) return;
    long long value = 0;
    long long reference = 0;
    if (!cp_score(score, value) || !cp_score(ref_score, reference)) die("score is neither cp nor mate");
    const long long gap = value > reference ? value - reference : reference - value;
    mae_sum += gap;
    ++mae_n;
}

std::string summary_line(const Totals& totals) {
    std::ostringstream out;
    out << "SUMMARY positions " << totals.positions << " nodes_mae_sum " << totals.nodes_mae_sum
        << " nodes_mae_n " << totals.nodes_mae_n << " nodes_agree " << totals.nodes_agree
        << " nodes_node_sum " << totals.nodes_node_sum << " soft_mae_sum " << totals.soft_mae_sum
        << " soft_mae_n " << totals.soft_mae_n << " soft_agree " << totals.soft_agree
        << " soft_node_sum " << totals.soft_node_sum;
    return out.str();
}

void repair_tail(const std::string& path) {
    std::fstream file(path, std::ios::in | std::ios::out | std::ios::binary);
    if (!file) return;
    file.seekg(0, std::ios::end);
    const auto size = file.tellg();
    if (size <= 0) return;
    file.seekg(-1, std::ios::end);
    char last = 0;
    file.get(last);
    if (last == '\n') return;
    std::string body;
    file.seekg(0);
    std::getline(file, body, '\0');
    const auto cut = body.rfind('\n');
    file.close();
    std::ofstream out(path, std::ios::trunc);
    if (cut != std::string::npos) out << body.substr(0, cut + 1);
}

std::unordered_set<int> done_indices(const std::string& path) {
    repair_tail(path);
    std::unordered_set<int> done;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        Row row;
        if (!parse_row(line, row)) die("corrupt shard line in " + path);
        if (!done.insert(row.index).second) die("duplicate index in " + path);
    }
    return done;
}

void generate(const std::string& engine_path) {
    Engine engine(engine_path);
    prepare(engine);
    std::uint64_t state = kSeed;
    std::vector<std::string> positions;
    positions.reserve(kPositions);
    std::unordered_set<std::string> seen;
    int games = 0;
    while (static_cast<int>(positions.size()) < kPositions) {
        if (++games > 8000) die("self-play walk did not reach 10000 positions");
        forge::Board board;
        if (!board.set_fen(forge::Board::StandardStartFen)) die("start fen rejected");
        const int opening = 8 + static_cast<int>(mix(state) % 5ULL);
        bool opened = true;
        for (int ply = 0; ply < opening; ++ply) {
            const forge::MoveList moves = board.legal_moves();
            if (moves.empty() || quiet_position(board)) {
                opened = false;
                break;
            }
            const forge::Move chosen = moves[static_cast<std::size_t>(mix(state) % moves.size())];
            forge::Undo undo;
            if (!board.make_move(chosen, undo)) {
                opened = false;
                break;
            }
        }
        if (!opened || quiet_position(board)) continue;
        for (int ply = 0; ply < 70 && static_cast<int>(positions.size()) < kPositions; ++ply) {
            if (quiet_position(board)) break;
            const std::string fen = board.fen();
            if (seen.insert(fen).second) positions.push_back(fen);
            const Search played = go_fen(engine, fen, "go depth " + std::to_string(kWalkDepth), 60000);
            if (!move_is_legal(fen, played.best)) die("self-play move illegal " + played.best + " " + fen);
            forge::Board next = board;
            const std::optional<forge::Move> parsed = next.parse_uci(played.best);
            forge::Undo undo;
            if (!parsed.has_value() || !next.make_move(*parsed, undo)) die("self-play move rejected");
            board = std::move(next);
        }
        if (games % 25 == 0) {
            std::cerr << "walk games " << games << " positions " << positions.size() << std::endl;
        }
    }
    const int status = engine.finish();
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) die("engine exit during walk");
    std::ofstream out(positions_path(), std::ios::trunc);
    out << "# seed " << kSeed << " walk-depth " << kWalkDepth << " opening-plies 8-12\n";
    for (const std::string& fen : positions) out << fen << '\n';
    out.flush();
    if (!out) die("could not write positions");
    std::cout << "GEN " << positions.size() << " seed " << kSeed << std::endl;
}

std::vector<std::string> load_positions() {
    std::ifstream in(positions_path());
    if (!in) die("missing positions");
    std::vector<std::string> positions;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        positions.push_back(line);
    }
    if (static_cast<int>(positions.size()) != kPositions) {
        die("positions count " + std::to_string(positions.size()));
    }
    return positions;
}

void run_shard(const std::string& engine_path, int shard, int shards) {
    if (shard < 0 || shards < 1 || shard >= shards) die("bad shard");
    const std::vector<std::string> positions = load_positions();
    const std::unordered_set<int> done = done_indices(shard_path(shard));
    Engine engine(engine_path);
    prepare(engine);
    std::ofstream out(shard_path(shard), std::ios::app);
    if (!out) die("could not open shard");
    int finished = static_cast<int>(done.size());
    for (int index = shard; index < kPositions; index += shards) {
        if (done.count(index) != 0) continue;
        const std::string& fen = positions[static_cast<std::size_t>(index)];
        const Search nodes = go_fen(engine, fen, "go nodes " + std::to_string(kBudget), 180000);
        const Search soft = go_fen(engine, fen, "go softnodes " + std::to_string(kBudget), 180000);
        const Search ref = go_fen(engine, fen, "go depth " + std::to_string(kReferenceDepth), 300000);
        if (nodes.saw_soft) die("go nodes printed softnodes at " + std::to_string(index));
        if (!soft.saw_soft) die("softnodes missing node count at " + std::to_string(index));
        if (ref.depth < kReferenceDepth) die("reference depth short at " + std::to_string(index));
        Row row;
        row.index = index;
        row.fen = fen;
        row.nodes_move = nodes.best;
        row.nodes_score = nodes.score;
        row.nodes_depth = nodes.depth;
        row.nodes_info = nodes.info_nodes;
        row.nodes_used = hard_nodes_used(nodes);
        row.soft_move = soft.best;
        row.soft_score = soft.score;
        row.soft_depth = soft.depth;
        row.soft_used = soft.soft_nodes;
        row.ref_move = ref.best;
        row.ref_score = ref.score;
        row.ref_nodes = ref.info_nodes;
        check_search_contract(row);
        out << row_line(row) << '\n';
        out.flush();
        ++finished;
        if (finished % 50 == 0) {
            std::cerr << "shard " << shard << " done " << finished << std::endl;
        }
    }
    const int status = engine.finish();
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) die("engine exit on shard " + std::to_string(shard));
    std::cout << "SHARD " << shard << " complete " << finished << std::endl;
}

Totals accumulate(const std::vector<Row>& rows) {
    Totals totals;
    std::vector<char> seen(static_cast<std::size_t>(kPositions), 0);
    for (const Row& row : rows) {
        if (row.index < 0 || row.index >= kPositions || seen[static_cast<std::size_t>(row.index)]) {
            die("row index mismatch");
        }
        seen[static_cast<std::size_t>(row.index)] = 1;
        check_search_contract(row);
        add_pair(totals.nodes_mae_sum, totals.nodes_mae_n, totals.nodes_agree, row.nodes_score, row.nodes_move,
                 row.ref_score, row.ref_move);
        add_pair(totals.soft_mae_sum, totals.soft_mae_n, totals.soft_agree, row.soft_score, row.soft_move,
                 row.ref_score, row.ref_move);
        totals.nodes_node_sum += static_cast<long long>(row.nodes_used);
        totals.soft_node_sum += static_cast<long long>(row.soft_used);
        ++totals.positions;
    }
    for (const char bit : seen) {
        if (bit == 0) die("missing position in log");
    }
    if (totals.positions != kPositions || totals.nodes_mae_n <= 0 || totals.soft_mae_n <= 0) {
        die("summary counts mismatch");
    }
    return totals;
}

std::vector<Row> load_rows(int shards) {
    const std::vector<std::string> positions = load_positions();
    std::vector<Row> rows;
    rows.reserve(kPositions);
    for (int shard = 0; shard < shards; ++shard) {
        std::ifstream in(shard_path(shard));
        if (!in) die("missing " + shard_path(shard));
        std::string line;
        while (std::getline(in, line)) {
            if (line.empty()) continue;
            Row row;
            if (!parse_row(line, row)) die("corrupt row");
            if (row.fen != positions[static_cast<std::size_t>(row.index)]) die("fen mismatch at row");
            rows.push_back(std::move(row));
        }
    }
    return rows;
}

void check_logs(int shards) {
    const Totals totals = accumulate(load_rows(shards));
    const std::string fresh = summary_line(totals);
    std::ifstream existing(summary_path());
    if (existing) {
        std::string stored;
        std::getline(existing, stored);
        if (stored != fresh) die("summary mismatch\nstored " + stored + "\nfresh " + fresh);
        std::cout << "CHECK_PASS " << fresh << std::endl;
        return;
    }
    std::ofstream out(summary_path(), std::ios::trunc);
    out << fresh << '\n';
    if (!out) die("could not write summary");
    std::cout << "CHECK_WROTE " << fresh << std::endl;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: label_measure <engine> gen|run|check ..." << std::endl;
        return 2;
    }
    const std::string path = argv[1];
    const std::string mode = argv[2];
    if (mode == "gen") {
        generate(path);
        return 0;
    }
    if (mode == "run") {
        if (argc != 5) die("run <engine> run <shard> <shards>");
        run_shard(path, std::atoi(argv[3]), std::atoi(argv[4]));
        return 0;
    }
    if (mode == "check") {
        const int shards = argc == 4 ? std::atoi(argv[3]) : 4;
        check_logs(shards);
        return 0;
    }
    std::cerr << "unknown mode " << mode << std::endl;
    return 2;
}
