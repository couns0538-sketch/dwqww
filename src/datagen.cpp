#include "forge/datagen.hpp"

#include "forge/eval.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <charconv>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <system_error>

#if defined(_WIN32)
#include <io.h>
#else
#include <unistd.h>
#endif

namespace forge::datagen {

PackedBoard pack_board(const Board& board) {
    PackedBoard packed{};
    for (int square = 0; square < 64; ++square) {
        const auto code = static_cast<unsigned>(board.piece_at(square));
        auto& byte = packed[static_cast<std::size_t>(square >> 1)];
        byte = static_cast<std::uint8_t>(byte | ((square & 1) != 0 ? code << 4U : code));
    }
    return packed;
}

const char* termination_name(Termination termination) {
    switch (termination) {
        case Termination::Checkmate: return "checkmate";
        case Termination::Stalemate: return "stalemate";
        case Termination::Insufficient: return "insufficient";
        case Termination::Repetition: return "repetition";
        case Termination::FiftyMoves: return "fifty";
        case Termination::MaxPly: return "max_ply";
        case Termination::AdjudicatedWin: return "adj_win";
        case Termination::AdjudicatedDraw: return "adj_draw";
    }
    return "unknown";
}

std::uint64_t Rng::next() {
    std::uint64_t z = (state_ += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27U)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31U);
}

std::uint64_t game_seed(std::uint64_t run_seed, std::uint64_t index) {
    Rng mix(run_seed ^ (index * 0xD1B54A32D192ED03ULL));
    return mix.next();
}

int game_ply(const Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == Black ? 1 : 0);
}

std::optional<std::pair<int, Termination>> terminal(const Board& board, int max_ply) {
    // Same order and outcome as forge_selfplay.py terminal_result(): checkmate first, then the draws.
    const bool any_legal = board.has_legal_move();
    if (!any_legal && board.in_check()) return std::pair{board.side_to_move() == White ? 0 : 2, Termination::Checkmate};
    if (!any_legal) return std::pair{1, Termination::Stalemate};
    if (board.is_insufficient_material()) return std::pair{1, Termination::Insufficient};
    if (board.is_repetition()) return std::pair{1, Termination::Repetition};
    if (board.halfmove_clock() >= 100) return std::pair{1, Termination::FiftyMoves};
    if (game_ply(board) >= max_ply) return std::pair{1, Termination::MaxPly};
    return std::nullopt;
}

std::optional<Game> play_game(Searcher& searcher, const Config& config, const Board& start, Rng& rng) {
    Board board = start;
    Game game;
    for (int ply = 0; ply < config.random_plies; ++ply) {
        if (terminal(board, config.max_ply)) return std::nullopt;
        const MoveList moves = board.legal_moves();
        const Move move = moves[static_cast<std::size_t>(rng.below(moves.size()))];
        Undo undo;
        if (!board.make_move(move, undo)) throw std::runtime_error("random opening move rejected");
        game.opening.push_back(move);
    }
    if (terminal(board, config.max_ply)) return std::nullopt;

    SearchLimits limits;
    if (config.depth > 0) {
        limits.depth = config.depth;
    } else {
        limits.nodes = config.nodes;
        limits.nodes_specified = true;
    }
    // As "ucinewgame": empty table (generation 0), histories and evaluation caches.
    searcher.clear();

    auto finish = [&game](int white_result_x2, Termination why) {
        game.white_result_x2 = white_result_x2;
        game.termination = why;
        for (Record& record : game.records) {
            record.meta = static_cast<std::uint8_t>((record.meta & 1U) | (static_cast<unsigned>(white_result_x2) << 1U));
        }
    };
    std::optional<Color> winner;
    int win_streak = 0;
    int draw_streak = 0;
    while (true) {
        if (const auto end = terminal(board, config.max_ply)) {
            finish(end->first, end->second);
            return game;
        }
        const SearchInfo info = searcher.search(board, limits, false, Searcher::TTAccess::Exclusive);
        const Move move = info.best_move;
        const MoveList legal = board.legal_moves();
        if (move.is_none() || std::find(legal.begin(), legal.end(), move) == legal.end()) {
            throw std::runtime_error("search returned no legal best move in " + board.fen());
        }
        const int score = info.score;
        const Color side = board.side_to_move();
        const bool mate = is_mate_score(score);
        // forge_selfplay.py eligible_score(): quiet best move, not in check, no mate score, |cp| <= max.
        if (!board.in_check() && !move.is_capture() && !move.is_promotion() && !mate &&
            std::abs(score) <= config.max_score) {
            Record record;
            record.board = pack_board(board);
            record.score = static_cast<std::int16_t>(score);
            record.hce = static_cast<std::int16_t>(std::clamp(Evaluator::evaluate_uncached(board), -32767, 32767));
            record.meta = pack_meta(side, 0);
            if (config.text) record.fen = board.fen();
            game.records.push_back(std::move(record));
        }
        // forge_selfplay.py decisive_side() + streak: the same side ahead by win_cp, White's view.
        const int white_view = side == White ? score : -score;
        std::optional<Color> ahead;
        if (white_view >= config.win_cp) ahead = White;
        else if (white_view <= -config.win_cp) ahead = Black;
        win_streak = ahead.has_value() ? (ahead == winner ? win_streak + 1 : 1) : 0;
        winner = ahead;
        draw_streak = !mate && std::abs(score) <= config.draw_cp ? draw_streak + 1 : 0;

        Undo undo;
        if (!board.make_move(move, undo)) throw std::runtime_error("best move rejected by make_move");
        game.moves.push_back(move);
        if (const auto end = terminal(board, config.max_ply)) {
            finish(end->first, end->second);
            return game;
        }
        if (config.win_plies > 0 && win_streak >= config.win_plies) {
            finish(winner == White ? 2 : 0, Termination::AdjudicatedWin);
            return game;
        }
        if (config.draw_plies > 0 && draw_streak >= config.draw_plies && game_ply(board) >= config.draw_min_ply) {
            finish(1, Termination::AdjudicatedDraw);
            return game;
        }
    }
}

// ---------------------------------------------------------------------------------------------
// Output

namespace {

void append_le(std::string& out, std::uint64_t value, int bytes) {
    for (int i = 0; i < bytes; ++i) out.push_back(static_cast<char>((value >> (8 * i)) & 0xFFU));
}

const char* result_text(int white_result_x2) {
    return white_result_x2 == 2 ? "1.0" : (white_result_x2 == 1 ? "0.5" : "0.0");
}

const char* result_pgn(int white_result_x2) {
    return white_result_x2 == 2 ? "1-0" : (white_result_x2 == 1 ? "1/2-1/2" : "0-1");
}

std::string text_bytes(const std::vector<Record>& records) {
    std::string out;
    for (const Record& record : records) {
        out += record.fen;
        out += " | ";
        out += std::to_string(record.score);
        out += " | ";
        out += result_text(record.meta >> 1U);
        out += '\n';
    }
    return out;
}

void sync_and_close(std::FILE* file, const std::string& name) {
    bool ok = std::fflush(file) == 0;
#if defined(_WIN32)
    ok = ok && _commit(_fileno(file)) == 0;
#else
    ok = ok && fsync(fileno(file)) == 0;
#endif
    ok = std::fclose(file) == 0 && ok;
    if (!ok) throw std::runtime_error("cannot flush " + name);
}

// Publishes <part> as <path> without ever replacing an existing <path>.
void publish(const std::string& part, const std::string& path) {
#if defined(_WIN32)
    if (std::rename(part.c_str(), path.c_str()) != 0) {  // Windows rename fails if <path> exists
        throw std::runtime_error("cannot publish " + path + " (exists?)");
    }
#else
    if (::link(part.c_str(), path.c_str()) != 0) {  // link never replaces <path>
        throw std::runtime_error("cannot publish " + path + " (exists?)");
    }
    (void)::unlink(part.c_str());
#endif
}

std::FILE* create_new(const std::string& part) {
    std::FILE* file = std::fopen(part.c_str(), "wbx");  // exclusive create (C11 "x")
    if (file == nullptr) throw std::runtime_error("cannot create " + part + " (exists or not writable)");
    return file;
}

// The run log (<out>.games or <out>.convert). Its exclusive .part is the prefix claim: a second
// process with the same prefix fails here, before writing any data.
class RunLog {
public:
    explicit RunLog(std::string path) : path_(std::move(path)) {
        if (std::filesystem::exists(path_)) throw std::runtime_error("refusing to reuse prefix: " + path_ + " exists");
        const std::filesystem::path parent = std::filesystem::path(path_).parent_path();
        if (!parent.empty()) std::filesystem::create_directories(parent);
        file_ = create_new(path_ + ".part");
    }
    ~RunLog() {
        if (file_ != nullptr) std::fclose(file_);  // unpublished: the .part marks an unfinished run
    }
    RunLog(const RunLog&) = delete;
    RunLog& operator=(const RunLog&) = delete;
    void write(const std::string& text) {
        if (std::fwrite(text.data(), 1, text.size(), file_) != text.size()) throw std::runtime_error("cannot write " + path_);
    }
    void publish_log() {
        std::FILE* file = file_;
        file_ = nullptr;
        sync_and_close(file, path_);
        publish(path_ + ".part", path_);
    }
private:
    std::string path_;
    std::FILE* file_ = nullptr;
};

} // namespace

void write_new_file(const std::string& path, const std::string& bytes) {
    if (std::filesystem::exists(path)) throw std::runtime_error("refusing to overwrite " + path);
    const std::string part = path + ".part";
    std::FILE* file = create_new(part);
    if (std::fwrite(bytes.data(), 1, bytes.size(), file) != bytes.size()) {
        std::fclose(file);
        throw std::runtime_error("cannot write " + part);
    }
    sync_and_close(file, part);
    publish(part, path);
}

std::string shard_name(const std::string& prefix, std::uint64_t index) {
    std::ostringstream name;
    name << prefix << '_' << std::setw(3) << std::setfill('0') << index;
    return name.str();
}

std::string pos_bytes(const std::vector<Record>& records) {
    const std::uint64_t n = records.size();
    std::string out;
    out.reserve(static_cast<std::size_t>(16 + 35 * n));
    out.append("FPOS", 4);
    append_le(out, 1, 4);
    append_le(out, n, 8);
    for (const Record& record : records) out.append(reinterpret_cast<const char*>(record.board.data()), record.board.size());
    for (const Record& record : records) append_le(out, static_cast<std::uint16_t>(record.score), 2);
    for (const Record& record : records) out.push_back(static_cast<char>(record.meta));
    return out;
}

std::string hce_bytes(const std::vector<Record>& records) {
    const std::uint64_t n = records.size();
    std::string out;
    out.reserve(static_cast<std::size_t>(16 + 2 * n));
    out.append("FHCE", 4);
    append_le(out, 1, 4);
    append_le(out, n, 8);
    for (const Record& record : records) append_le(out, static_cast<std::uint16_t>(record.hce), 2);
    return out;
}

ShardWriter::ShardWriter(std::string prefix, std::uint64_t positions_per_file, bool text, std::string info)
    : prefix_(std::move(prefix)), positions_per_file_(std::max<std::uint64_t>(1, positions_per_file)), text_(text),
      info_(std::move(info)) {}

void ShardWriter::add(Record record) { records_.push_back(std::move(record)); }

void ShardWriter::maybe_close() {
    if (records_.size() >= positions_per_file_) close();
}

void ShardWriter::close() {
    if (records_.empty()) return;
    const std::string base = shard_name(prefix_, shard_index_);
    write_new_file(base + ".hce", hce_bytes(records_));
    if (text_) write_new_file(base + ".txt", text_bytes(records_));
    write_new_file(base + ".info", info_ + "records=" + std::to_string(records_.size()) + "\n");
    write_new_file(base + ".pos", pos_bytes(records_));  // last: a .pos means a complete shard
    written_ += records_.size();
    ++shard_index_;
    records_.clear();
}

std::optional<Record> parse_text_record(const std::string& raw) {
    // fen2bin.cpp: "FEN | score | result", score int in [-32767, 32767], result 0 / 0.5 / 1 (White).
    // hce_dump.cpp: FEN = text before the first '|', trailing blanks removed, Board::set_fen.
    std::string line = raw;
    if (!line.empty() && line.back() == '\r') line.pop_back();
    const std::size_t first = line.find('|');
    if (first == std::string::npos) return std::nullopt;
    const std::size_t second = line.find('|', first + 1);
    if (second == std::string::npos) return std::nullopt;
    std::string fen = line.substr(0, first);
    while (!fen.empty() && (fen.back() == ' ' || fen.back() == '\t')) fen.pop_back();
    Board board;
    if (!board.set_fen(fen)) return std::nullopt;
    const std::string score_text = line.substr(first + 1, second - first - 1);
    char* end = nullptr;
    const long score = std::strtol(score_text.c_str(), &end, 10);
    if (end == score_text.c_str() || score < -32767 || score > 32767) return std::nullopt;
    const std::string result_field = line.substr(second + 1);
    const double result = std::strtod(result_field.c_str(), &end);
    if (end == result_field.c_str()) return std::nullopt;
    int white_result_x2 = 0;
    if (result == 0.0) white_result_x2 = 0;
    else if (result == 0.5) white_result_x2 = 1;
    else if (result == 1.0) white_result_x2 = 2;
    else return std::nullopt;
    Record record;
    record.board = pack_board(board);
    record.score = static_cast<std::int16_t>(score);
    record.hce = static_cast<std::int16_t>(std::clamp(Evaluator::evaluate_uncached(board), -32767, 32767));
    record.meta = pack_meta(board.side_to_move(), white_result_x2);
    record.fen = fen;
    return record;
}

// ---------------------------------------------------------------------------------------------
// Command line

namespace {

struct UsageError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

constexpr const char* Usage =
    "usage: forge datagen --out PREFIX (--games N | --positions N) [options]\n"
    "       forge datagen --out PREFIX --convert TEXT_FILE [--positions-per-file N]\n"
    "  --nodes N (5000) | --depth D        fixed search budget per move\n"
    "  --seed S (1)  --hash MB (16)  --random-plies N (8)  --max-ply N (300)  --max-score CP (3000)\n"
    "  --win-cp CP (2000) --win-plies N (4, 0 = off)   win adjudication (same side, consecutive plies)\n"
    "  --draw-cp CP (0) --draw-plies N (0 = off) --draw-min-ply N (0)   draw adjudication\n"
    "  --openings FILE   EPD/FEN start positions (default: the start position)\n"
    "  --positions-per-file N (1000000)  --text (also write FEN | score | result lines)\n"
    "Writes <PREFIX>_NNN.pos/.hce (FPOS/FHCE v1), <PREFIX>_NNN.info and <PREFIX>.games; never overwrites.";

template <typename T>
T parse_number(std::string_view name, std::string_view text, T minimum) {
    T parsed{};
    const auto [ptr, ec] = std::from_chars(text.data(), text.data() + text.size(), parsed);
    if (ec != std::errc{} || ptr != text.data() + text.size() || parsed < minimum) {
        throw UsageError("invalid value for " + std::string(name) + ": " + std::string(text));
    }
    return parsed;
}

std::vector<Board> load_starts(const std::string& path) {
    std::vector<Board> starts;
    if (path.empty()) {
        Board board;
        (void)board.set_fen(Board::StandardStartFen);
        starts.push_back(board);
        return starts;
    }
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open openings file " + path);
    std::string line;
    std::size_t number = 0;
    while (std::getline(in, line)) {
        ++number;
        std::istringstream fields(line);
        std::vector<std::string> tokens;
        std::string token;
        while (tokens.size() < 6 && fields >> token) tokens.push_back(token);
        if (tokens.empty() || tokens[0].front() == '#') continue;
        if (tokens.size() < 4) throw std::runtime_error(path + ":" + std::to_string(number) + ": not a FEN/EPD line");
        std::string fen = tokens[0] + ' ' + tokens[1] + ' ' + tokens[2] + ' ' + tokens[3];
        const bool counters = tokens.size() == 6 &&
            std::all_of(tokens[4].begin(), tokens[4].end(), [](char c) { return c >= '0' && c <= '9'; }) &&
            std::all_of(tokens[5].begin(), tokens[5].end(), [](char c) { return c >= '0' && c <= '9'; });
        fen += counters ? ' ' + tokens[4] + ' ' + tokens[5] : std::string(" 0 1");
        Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) throw std::runtime_error(path + ":" + std::to_string(number) + ": " + error);
        starts.push_back(board);
    }
    if (starts.empty()) throw std::runtime_error("no positions in openings file " + path);
    return starts;
}

std::string config_text(const Config& config) {
    std::ostringstream text;
    text << "format=FPOS v1 (.pos) + FHCE v1 (.hce, Evaluator::evaluate_uncached), forge datagen v2 (S32)\n";
    if (!config.convert.empty()) {
        text << "mode=convert\n";
        return text.str();
    }
    text << "mode=selfplay\nseed=" << config.seed << "\nbudget=" << (config.depth > 0 ? "depth " : "nodes ")
         << (config.depth > 0 ? static_cast<std::uint64_t>(config.depth) : config.nodes) << "\nhash_mb=" << config.hash_mb
         << "\nrandom_plies=" << config.random_plies << "\nmax_ply=" << config.max_ply << "\nwin_cp=" << config.win_cp
         << "\nwin_plies=" << config.win_plies << "\ndraw_cp=" << config.draw_cp << "\ndraw_plies=" << config.draw_plies
         << "\ndraw_min_ply=" << config.draw_min_ply << "\nmax_score=" << config.max_score
         << "\nopenings=" << (config.openings.empty() ? std::string("startpos") : std::filesystem::path(config.openings).filename().string())
         << '\n';
    return text.str();
}

double seconds_since(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
}

int generate(const Config& config) {
    const std::vector<Board> starts = load_starts(config.openings);
    const auto started = std::chrono::steady_clock::now();
    RunLog log(config.out + ".games");
    const std::string info = config_text(config);
    std::istringstream header(info);
    for (std::string line; std::getline(header, line);) log.write("# " + line + '\n');
    log.write("# game\tattempt\tstart\tresult\ttermination\trecords\topening\tmoves\n");
    ShardWriter writer(config.out, config.positions_per_file, config.text, info);
    Searcher searcher(config.hash_mb, 1);
    std::uint64_t attempts = 0;
    std::uint64_t games = 0;
    std::uint64_t plies = 0;
    std::array<std::uint64_t, 3> results{};
    std::array<std::uint64_t, 8> terminations{};
    while ((config.games == 0 || games < config.games) &&
           (config.positions == 0 || writer.written() + writer.pending() < config.positions)) {
        if (attempts - games > 100000) throw std::runtime_error("no game survives the random opening");
        const std::uint64_t index = attempts++;
        Rng rng(game_seed(config.seed, index));
        const std::size_t start = starts.size() == 1 ? 0 : static_cast<std::size_t>(rng.below(starts.size()));
        std::optional<Game> game = play_game(searcher, config, starts[start], rng);
        if (!game.has_value()) continue;
        ++games;
        plies += game->moves.size();
        ++results[static_cast<std::size_t>(game->white_result_x2)];
        ++terminations[static_cast<std::size_t>(game->termination)];
        std::string line = std::to_string(games - 1) + '\t' + std::to_string(index) + '\t' + std::to_string(start) + '\t' +
                           result_pgn(game->white_result_x2) + '\t' + termination_name(game->termination) + '\t' +
                           std::to_string(game->records.size()) + '\t';
        for (std::size_t i = 0; i < game->opening.size(); ++i) line += (i ? " " : "") + Board::move_to_uci(game->opening[i]);
        line += '\t';
        for (std::size_t i = 0; i < game->moves.size(); ++i) line += (i ? " " : "") + Board::move_to_uci(game->moves[i]);
        log.write(line + '\n');
        for (Record& record : game->records) writer.add(std::move(record));
        writer.maybe_close();
    }
    writer.close();
    log.publish_log();
    const double elapsed = seconds_since(started);
    std::cout << "{\"mode\":\"selfplay\",\"games\":" << games << ",\"attempts\":" << attempts << ",\"positions\":"
              << writer.written() << ",\"shards\":" << writer.shards() << ",\"searched_plies\":" << plies
              << ",\"results\":{\"1-0\":" << results[2] << ",\"1/2-1/2\":" << results[1] << ",\"0-1\":" << results[0] << "},\"terminations\":{";
    for (std::size_t i = 0; i < terminations.size(); ++i) {
        std::cout << (i ? "," : "") << '"' << termination_name(static_cast<Termination>(i)) << "\":" << terminations[i];
    }
    std::cout << "},\"elapsed_s\":" << elapsed << ",\"positions_per_s\":"
              << (elapsed > 0 ? static_cast<double>(writer.written()) / elapsed : 0.0) << "}" << std::endl;
    return 0;
}

int convert(const Config& config) {
    std::ifstream in(config.convert, std::ios::binary);
    if (!in) throw std::runtime_error("cannot open " + config.convert);
    const auto started = std::chrono::steady_clock::now();
    RunLog log(config.out + ".convert");
    ShardWriter writer(config.out, config.positions_per_file, false, config_text(config));
    std::string line;
    std::uint64_t number = 0;
    while (std::getline(in, line)) {
        ++number;
        std::optional<Record> record = parse_text_record(line);
        if (!record.has_value()) throw std::runtime_error(config.convert + ":" + std::to_string(number) + ": invalid record");
        record->fen.clear();
        writer.add(std::move(*record));
        writer.maybe_close();
    }
    writer.close();
    log.write("source=" + std::filesystem::path(config.convert).filename().string() + "\nlines=" + std::to_string(number) +
              "\nrecords=" + std::to_string(writer.written()) + "\nshards=" + std::to_string(writer.shards()) + "\n");
    log.publish_log();
    std::cout << "{\"mode\":\"convert\",\"lines\":" << number << ",\"positions\":" << writer.written()
              << ",\"shards\":" << writer.shards() << ",\"elapsed_s\":" << seconds_since(started) << "}" << std::endl;
    return 0;
}

} // namespace

int run(int argc, const char* const* argv) {
    Config config;
    try {
        for (int i = 0; i < argc; ++i) {
            const std::string_view arg = argv[i];
            auto next = [&]() -> std::string_view {
                if (i + 1 >= argc) throw UsageError("missing value for " + std::string(arg));
                return argv[++i];
            };
            if (arg == "--out") config.out = std::string(next());
            else if (arg == "--convert") config.convert = std::string(next());
            else if (arg == "--openings") config.openings = std::string(next());
            else if (arg == "--nodes") config.nodes = parse_number<std::uint64_t>(arg, next(), 1);
            else if (arg == "--depth") config.depth = parse_number<int>(arg, next(), 1);
            else if (arg == "--games") config.games = parse_number<std::uint64_t>(arg, next(), 1);
            else if (arg == "--positions") config.positions = parse_number<std::uint64_t>(arg, next(), 1);
            else if (arg == "--positions-per-file") config.positions_per_file = parse_number<std::uint64_t>(arg, next(), 1);
            else if (arg == "--seed") config.seed = parse_number<std::uint64_t>(arg, next(), 0);
            else if (arg == "--hash") config.hash_mb = parse_number<std::size_t>(arg, next(), 1);
            else if (arg == "--random-plies") config.random_plies = parse_number<int>(arg, next(), 0);
            else if (arg == "--max-ply") config.max_ply = parse_number<int>(arg, next(), 1);
            else if (arg == "--max-score") config.max_score = parse_number<int>(arg, next(), 0);
            else if (arg == "--win-cp") config.win_cp = parse_number<int>(arg, next(), 1);
            else if (arg == "--win-plies") config.win_plies = parse_number<int>(arg, next(), 0);
            else if (arg == "--draw-cp") config.draw_cp = parse_number<int>(arg, next(), 0);
            else if (arg == "--draw-plies") config.draw_plies = parse_number<int>(arg, next(), 0);
            else if (arg == "--draw-min-ply") config.draw_min_ply = parse_number<int>(arg, next(), 0);
            else if (arg == "--text") config.text = true;
            else if (arg == "--help" || arg == "-h") {
                std::cout << Usage << std::endl;
                return 0;
            } else {
                throw UsageError("unknown option " + std::string(arg));
            }
        }
        if (config.out.empty()) throw UsageError("--out is required");
        if (config.convert.empty() && config.games == 0 && config.positions == 0) {
            throw UsageError("--games or --positions is required");
        }
        if (config.max_ply <= config.random_plies) throw UsageError("--max-ply must exceed --random-plies");
        if (config.hash_mb > 2048) throw UsageError("--hash must be at most 2048");
    } catch (const UsageError& error) {
        std::cerr << "datagen: " << error.what() << '\n' << Usage << std::endl;
        return 2;
    }
    try {
        return config.convert.empty() ? generate(config) : convert(config);
    } catch (const std::exception& error) {
        std::cerr << "datagen: " << error.what() << std::endl;
        return 1;
    }
}

} // namespace forge::datagen
