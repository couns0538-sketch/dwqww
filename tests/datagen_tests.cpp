// S32 datagen v2 unit tests: record encoding, game rules (forge_selfplay.py semantics), sign
// conventions, determinism, the no-overwrite shard writer and the text converter.
// usage: forge_datagen_tests [scratch_dir]   (files are written below scratch_dir and left in place)
#include "forge/datagen.hpp"
#include "forge/eval.hpp"
#include "forge/search.hpp"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using namespace forge;
using namespace forge::datagen;

int failures = 0;

void check(bool condition, const std::string& message) {
    std::cout << (condition ? "PASS " : "FAIL ") << message << '\n';
    if (!condition) ++failures;
}

Board from_fen(const std::string& fen) {
    Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) throw std::runtime_error("invalid test FEN " + fen + ": " + error);
    return board;
}

Board play(Board board, const std::vector<std::string>& moves) {
    for (const std::string& text : moves) {
        const auto move = board.parse_uci(text);
        if (!move.has_value()) throw std::runtime_error("illegal test move " + text);
        Undo undo;
        (void)board.make_move(*move, undo);
    }
    return board;
}

std::string read_file(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    return std::string(std::istreambuf_iterator<char>(in), std::istreambuf_iterator<char>());
}

bool same_terminal(const std::optional<std::pair<int, Termination>>& got, int result, Termination why) {
    return got.has_value() && got->first == result && got->second == why;
}

void test_encoding() {
    const Board start = from_fen(std::string(Board::StandardStartFen));
    const PackedBoard expected{0x24, 0x53, 0x36, 0x42, 0x11, 0x11, 0x11, 0x11, 0, 0, 0, 0, 0, 0, 0, 0,
                               0, 0, 0, 0, 0, 0, 0, 0, 0x77, 0x77, 0x77, 0x77, 0x8A, 0xB9, 0x9C, 0xA8};
    check(pack_board(start) == expected, "pack_board(startpos) == fen2bin nibble layout");
    const Board e4 = play(start, {"e2e4"});
    const PackedBoard packed = pack_board(e4);
    check(packed[6] == 0x10 && packed[14] == 0x01, "pack_board after e2e4: e2 (low nibble of byte 6) empty, e4 white pawn");
    check(pack_meta(White, 2) == 4 && pack_meta(Black, 2) == 5 && pack_meta(Black, 0) == 1 && pack_meta(White, 1) == 2,
          "pack_meta: bit0 black to move, bits1-2 White result * 2");
    Rng zero(0);
    check(zero.next() == 0xE220A8397B1DCDAFULL, "SplitMix64(0) first output matches the reference value");
    check(game_seed(1, 0) == game_seed(1, 0) && game_seed(1, 0) != game_seed(1, 1) && game_seed(1, 0) != game_seed(2, 0),
          "game_seed is a function of (run seed, attempt index)");
}

void test_terminal() {
    const Board start = from_fen(std::string(Board::StandardStartFen));
    check(!terminal(start, 300).has_value(), "startpos is not terminal");
    check(game_ply(start) == 0 && game_ply(play(start, {"e2e4"})) == 1, "game_ply from the move counters");
    check(same_terminal(terminal(from_fen("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"), 300), 0,
                        Termination::Checkmate), "White checkmated -> White result 0");
    check(same_terminal(terminal(from_fen("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1"), 300), 2, Termination::Checkmate),
          "Black checkmated -> White result 2");
    check(same_terminal(terminal(from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"), 300), 1, Termination::Stalemate), "stalemate -> draw");
    check(same_terminal(terminal(from_fen("8/8/4k3/8/8/3KB3/8/8 w - - 0 1"), 300), 1, Termination::Insufficient),
          "KB v K -> insufficient material draw");
    check(same_terminal(terminal(from_fen("7k/8/8/8/8/8/8/K5R1 b - - 100 80"), 300), 1, Termination::FiftyMoves),
          "halfmove clock 100 with a legal move -> fifty-move draw");
    check(same_terminal(terminal(from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 151"), 300), 1,
                        Termination::MaxPly) &&
              !terminal(from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 151"), 301).has_value(),
          "game ply 300 -> draw at max-ply 300, not at 301");
    const std::vector<std::string> shuffle{"g1f3", "g8f6", "f3g1", "f6g8"};
    const Board twice = play(start, shuffle);
    check(!terminal(twice, 300).has_value(), "second occurrence of a position is not terminal");
    std::vector<std::string> eight = shuffle;
    eight.insert(eight.end(), shuffle.begin(), shuffle.end());
    check(same_terminal(terminal(play(start, eight), 300), 1, Termination::Repetition), "third occurrence -> repetition draw");
}

Config small_config() {
    Config config;
    config.nodes = 1500;
    config.random_plies = 4;
    config.max_ply = 120;
    config.text = true;
    return config;
}

bool same_game(const Game& a, const Game& b) {
    if (a.opening != b.opening || a.moves != b.moves || a.white_result_x2 != b.white_result_x2 ||
        a.termination != b.termination || a.records.size() != b.records.size()) return false;
    for (std::size_t i = 0; i < a.records.size(); ++i) {
        const Record& x = a.records[i];
        const Record& y = b.records[i];
        if (x.board != y.board || x.score != y.score || x.hce != y.hce || x.meta != y.meta || x.fen != y.fen) return false;
    }
    return true;
}

void test_games(std::vector<Record>& sample) {
    const Config config = small_config();
    const Board start = from_fen(std::string(Board::StandardStartFen));
    Searcher first(4, 1);
    Searcher second(4, 1);
    std::optional<Game> a;
    std::optional<Game> b;
    std::uint64_t attempt = 0;
    while (!a.has_value()) {
        Rng rng_a(game_seed(7, attempt));
        Rng rng_b(game_seed(7, attempt));
        a = play_game(first, config, start, rng_a);
        b = play_game(second, config, start, rng_b);
        ++attempt;
    }
    check(b.has_value() && same_game(*a, *b), "same seed -> identical game (moves, records, result)");
    check(a->opening.size() == 4 && !a->moves.empty(), "4 random plies, then searched plies");
    // A searcher that already played a different game gives the same game after clear().
    Rng other(game_seed(99, 0));
    (void)play_game(first, config, start, other);
    Rng again(game_seed(7, attempt - 1));
    const std::optional<Game> c = play_game(first, config, start, again);
    check(c.has_value() && same_game(*a, *c), "game is independent of the searcher's history (clear per game)");

    // Records: replaying the game reaches each recorded position, in order, before a quiet move.
    Board board = start;
    for (const Move move : a->opening) {
        Undo undo;
        (void)board.make_move(move, undo);
    }
    std::size_t next = 0;
    bool meta_ok = true;
    bool fen_ok = true;
    for (const Move move : a->moves) {
        if (next < a->records.size() && a->records[next].board == pack_board(board)) {
            const Record& record = a->records[next];
            meta_ok = meta_ok && (record.meta & 1U) == (board.side_to_move() == Black ? 1U : 0U) &&
                      (record.meta >> 1U) == static_cast<unsigned>(a->white_result_x2);
            fen_ok = fen_ok && record.fen == board.fen() && !move.is_capture() && !move.is_promotion() && !board.in_check() &&
                     record.hce == Evaluator::evaluate_uncached(board);
            ++next;
        }
        Undo undo;
        (void)board.make_move(move, undo);
    }
    check(next == a->records.size(), "every record is a position of the game, in game order");
    check(meta_ok, "record meta: side to move + final White result");
    check(fen_ok, "record FEN/HCE match the position; best move quiet; not in check");
    sample = a->records;
}

void test_signs() {
    // White is a rook up: the search score and the HCE are positive with White to move and negative
    // with Black to move (side-to-move convention); the colour-mirrored start gives the mirrored signs.
    Config config = small_config();
    config.random_plies = 0;
    config.max_ply = 40;
    for (const bool mirrored : {false, true}) {
        const Board start = from_fen(mirrored ? "r3k3/pppp4/8/8/8/8/PPPP4/4K3 b q - 0 1" : "4k3/pppp4/8/8/8/8/PPPP4/R3K3 w Q - 0 1");
        const Color strong = mirrored ? Black : White;
        Searcher searcher(4, 1);
        Rng rng(1);
        const std::optional<Game> game = play_game(searcher, config, start, rng);
        if (!game.has_value()) throw std::runtime_error("sign test start position is terminal");
        int agree = 0;
        int hce_agree = 0;
        int total = 0;
        for (const Record& record : game->records) {
            const Color side = (record.meta & 1U) != 0 ? Black : White;
            const int sign = side == strong ? 1 : -1;
            agree += record.score * sign > 0 ? 1 : 0;
            hce_agree += record.hce * sign > 0 ? 1 : 0;
            ++total;
        }
        check(total >= 10 && agree * 10 >= total * 9 && hce_agree * 10 >= total * 9,
              std::string(mirrored ? "Black" : "White") + " a rook up: >= 90% of scores and HCE have the side-to-move sign (" +
                  std::to_string(agree) + "/" + std::to_string(hce_agree) + "/" + std::to_string(total) + ")");
        check(game->white_result_x2 != (mirrored ? 2 : 0), "the side a rook up does not lose");
    }
    // Mate in one for White / for Black: the game result labels.
    Config mate = small_config();
    mate.random_plies = 0;
    Searcher searcher(4, 1);
    Rng rng(1);
    const std::optional<Game> white = play_game(searcher, mate, from_fen("6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1"), rng);
    check(white.has_value() && white->white_result_x2 == 2 && white->termination == Termination::Checkmate,
          "White mates -> White result 1.0 (x2 = 2)");
    const std::optional<Game> black = play_game(searcher, mate, from_fen("3r2k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 1"), rng);
    check(black.has_value() && black->white_result_x2 == 0 && black->termination == Termination::Checkmate,
          "Black mates -> White result 0.0");
    // Win adjudication: a queen and rook up, the same side >= 600 cp (test threshold) for 4 plies.
    Config adjudicate = mate;
    adjudicate.win_cp = 600;
    const std::optional<Game> won = play_game(searcher, adjudicate, from_fen("4k3/8/8/8/8/8/8/QR2K3 w - - 0 1"), rng);
    check(won.has_value() && won->white_result_x2 == 2 &&
              (won->termination == Termination::AdjudicatedWin || won->termination == Termination::Checkmate),
          std::string("win adjudication/mate -> White result 1.0 (") + termination_name(won->termination) + ")");
    // Draw adjudication (off by default): K+R v K+R, |score| <= 150 cp for 6 consecutive plies.
    Config draw = mate;
    draw.draw_cp = 150;
    draw.draw_plies = 6;
    const std::optional<Game> drawn = play_game(searcher, draw, from_fen("4k3/8/8/r7/8/8/7R/4K3 w - - 0 1"), rng);
    check(drawn.has_value() && drawn->white_result_x2 == 1 && drawn->termination == Termination::AdjudicatedDraw &&
              drawn->moves.size() >= 6,
          "draw adjudication: 6 plies within 150 cp -> draw");
    Config no_draw = mate;
    no_draw.max_ply = 30;
    const std::optional<Game> played = play_game(searcher, no_draw, from_fen("4k3/8/8/r7/8/8/7R/4K3 w - - 0 1"), rng);
    check(played.has_value() && played->termination != Termination::AdjudicatedDraw, "draw adjudication is off by default");
}

void test_writer(const std::filesystem::path& dir, const std::vector<Record>& sample) {
    std::filesystem::create_directories(dir);
    const std::string prefix = (dir / "w").string();
    std::vector<Record> records = sample;
    while (records.size() < 7) records.insert(records.end(), sample.begin(), sample.end());
    records.resize(7);
    ShardWriter writer(prefix, 3, true, "test=1\n");
    for (const Record& record : records) {
        writer.add(record);
        writer.maybe_close();
    }
    writer.close();
    check(writer.written() == 7 && writer.shards() == 3, "7 records at 3 per file -> shards 3+3+1");
    const std::string pos0 = read_file(shard_name(prefix, 0) + ".pos");
    const std::string hce2 = read_file(shard_name(prefix, 2) + ".hce");
    check(pos0.size() == 16 + 35 * 3 && pos0.compare(0, 4, "FPOS") == 0 && pos0[4] == 1 && pos0[8] == 3,
          "shard 0 .pos: FPOS v1, n = 3, size 16 + 35n");
    check(hce2.size() == 16 + 2 && hce2.compare(0, 4, "FHCE") == 0 && hce2[8] == 1, "shard 2 .hce: FHCE v1, n = 1");
    const std::vector<Record> first(records.begin(), records.begin() + 3);
    check(pos0 == pos_bytes(first), "shard bytes == pos_bytes(records)");
    // Column layout: boards, then int16 scores, then meta bytes (fen2bin.cpp).
    const auto score0 = static_cast<std::int16_t>(static_cast<std::uint16_t>(static_cast<unsigned char>(pos0[16 + 96])) |
                                                  static_cast<std::uint16_t>(static_cast<unsigned char>(pos0[16 + 97]) << 8U));
    check(score0 == records[0].score && static_cast<unsigned char>(pos0[16 + 102]) == records[0].meta,
          "column layout: score at 16 + 32n, meta at 16 + 34n");
    check(!std::filesystem::exists(shard_name(prefix, 0) + ".pos.part") && std::filesystem::exists(shard_name(prefix, 0) + ".txt"),
          "published names only; text shard written");
    bool refused = false;
    try {
        write_new_file(shard_name(prefix, 0) + ".pos", "x");
    } catch (const std::runtime_error&) {
        refused = true;
    }
    check(refused && read_file(shard_name(prefix, 0) + ".pos") == pos0, "existing shard is never overwritten");
    { std::ofstream stale((dir / "stale.pos.part").string(), std::ios::binary); stale << "partial"; }
    bool stale_refused = false;
    try {
        write_new_file((dir / "stale.pos").string(), "x");
    } catch (const std::runtime_error&) {
        stale_refused = true;
    }
    check(stale_refused && !std::filesystem::exists(dir / "stale.pos"), "a leftover .part blocks its name (exclusive create)");
    // Text round trip: the .txt shard converts back to identical .pos/.hce bytes.
    std::ifstream text(shard_name(prefix, 0) + ".txt", std::ios::binary);
    std::vector<Record> parsed;
    for (std::string line; std::getline(text, line);) {
        const std::optional<Record> record = parse_text_record(line);
        if (record.has_value()) parsed.push_back(*record);
    }
    check(parsed.size() == 3 && pos_bytes(parsed) == pos0 && hce_bytes(parsed) == read_file(shard_name(prefix, 0) + ".hce"),
          "text shard -> parse_text_record -> identical .pos and .hce bytes");
}

void test_parse() {
    const std::optional<Record> ok = parse_text_record("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1 | -38 | 0.5\r");
    check(ok.has_value() && ok->score == -38 && ok->meta == pack_meta(Black, 1) &&
              ok->hce == Evaluator::evaluate_uncached(from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")),
          "parse_text_record: score, black to move, draw, HCE");
    check(!parse_text_record("no bars here").has_value() &&
              !parse_text_record("8/8/4k3/8/8/3K4/8/8 w - - 0 1 | 40000 | 1.0").has_value() &&
              !parse_text_record("8/8/4k3/8/8/3K4/8/8 w - - 0 1 | 5 | 0.3").has_value() &&
              !parse_text_record("8/8/8/8/8/3K4/8/8 w - - 0 1 | 5 | 1.0").has_value(),
          "parse_text_record rejects: no fields, score out of int16 range, bad result, invalid FEN");
}

void test_command_line(const std::filesystem::path& dir) {
    const char* none[] = {"--games", "1"};
    check(run(2, none) == 2, "missing --out -> usage error 2");
    const std::string out = (dir / "cli").string();
    const char* zero[] = {"--out", out.c_str(), "--games", "0"};
    check(run(4, zero) == 2, "--games 0 -> usage error 2");
    const char* unknown[] = {"--out", out.c_str(), "--games", "1", "--frobnicate"};
    check(run(5, unknown) == 2, "unknown option -> usage error 2");
    const char* game[] = {"--out", out.c_str(), "--games", "1", "--nodes", "800", "--max-ply", "60", "--seed", "3"};
    check(run(10, game) == 0 && std::filesystem::exists(out + ".games") && std::filesystem::exists(out + "_000.pos"),
          "one game -> exit 0, .games and _000.pos published");
    check(run(10, game) == 1, "reusing the prefix -> exit 1 (refused)");
}

} // namespace

int main(int argc, char** argv) {
    const std::filesystem::path base = argc > 1 ? std::filesystem::path(argv[1]) : std::filesystem::path("datagen_unit");
    const auto stamp = std::chrono::steady_clock::now().time_since_epoch().count();
    const std::filesystem::path dir = base / ("run_" + std::to_string(stamp));
    std::filesystem::create_directories(dir);
    try {
        test_encoding();
        test_terminal();
        std::vector<Record> sample;
        test_games(sample);
        test_signs();
        test_writer(dir / "writer", sample);
        test_parse();
        test_command_line(dir);
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        ++failures;
    }
    std::cout << (failures == 0 ? "ALL PASS" : "FAILURES: " + std::to_string(failures)) << std::endl;
    return failures == 0 ? 0 : 1;
}
