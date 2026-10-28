// Unit tests of the FB2-J2 datagen v2 module. Usage: forge_datagen2_tests <scratch dir>
#include "forge/datagen2.hpp"
#include "forge/eval.hpp"
#include "forge/search.hpp"

#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using namespace forge;
using namespace forge::datagen2;

namespace {

int failures = 0;
int checks = 0;

void check(bool ok, const std::string& what) {
    ++checks;
    if (!ok) {
        ++failures;
        std::cout << "FAIL: " << what << '\n';
    }
}

std::string read_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    return std::string((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
}

Config test_config(const std::string& out) {
    Config c;
    c.out = out;
    c.nodes = 400;
    c.hash_mb = 1;
    c.random_plies = 6;
    c.random_plies_jitter = 2;
    c.temp_plies = 2;
    c.temperature = 120.0;
    c.temp_depth = 2;
    c.opening_eval_cap = 400;
    c.max_ply = 160;
    c.win_cp = 1200;
    c.win_plies = 3;
    c.draw_cp = 10;
    c.draw_plies = 8;
    c.draw_min_ply = 80;
    c.min_ply = 12;
    c.skip_prob = 0.1;
    c.quiet = true;
    return c;
}

const char* kStart = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

} // namespace

int main(int argc, char** argv) {
    const std::string scratch = argc > 1 ? argv[1] : "fable_datagen2_tests";
    std::filesystem::create_directories(scratch);

    // 1. move encoding: every legal move of positions with castling, promotions, en passant and checks
    {
        const char* fens[] = {
            kStart,
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            "rnbqkbnr/pp1p1ppp/8/2pPp3/8/8/PPP1PPPP/RNBQKBNR w KQkq e6 0 3",
            "4k3/1P6/8/8/8/8/8/4K3 w - - 0 1",
            "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        };
        int total = 0;
        for (const char* fen : fens) {
            Board board;
            check(board.set_fen(fen), std::string("set_fen ") + fen);
            for (const Move& move : board.legal_moves()) {
                const Move back = decode_move(board, encode_move(move));
                check(back.from == move.from && back.to == move.to && back.flags == move.flags && back.promotion == move.promotion,
                      "move round trip " + Board::move_to_uci(move) + " in " + fen);
                ++total;
            }
            check(decode_move(board, static_cast<std::uint16_t>(0)).is_none() || board.legal_moves().size() > 0, "decode of a bogus code");
        }
        std::cout << "move encoding: " << total << " legal moves round-tripped\n";
    }

    // 2. serialisation round trip of synthetic games and corruption detection
    {
        std::vector<Game> games;
        for (int g = 0; g < 5; ++g) {
            Game game;
            game.start_fen = kStart;
            game.white_result_x2 = static_cast<std::uint8_t>(g % 3);
            game.termination = static_cast<Termination>(g % 8);
            Board board;
            (void)board.set_fen(kStart);
            std::uint64_t seed = 77 + static_cast<std::uint64_t>(g);
            for (int ply = 0; ply < 30 + g; ++ply) {
                const MoveList moves = board.legal_moves();
                if (moves.empty()) break;
                seed = seed * 6364136223846793005ULL + 1442695040888963407ULL;
                const Move move = moves[static_cast<std::size_t>((seed >> 33U) % moves.size())];
                Ply p;
                p.move = move;
                p.score = ply < 4 ? ScoreNone : static_cast<std::int16_t>((ply * 37) % 2000 - 1000);
                p.flags = static_cast<std::uint8_t>(ply < 4 ? 0 : ((ply % 3 == 0) ? RecordKept : RecordNoisyPv));
                game.plies.push_back(p);
                Undo undo;
                (void)board.make_move(move, undo);
            }
            game.opening_plies = 4;
            games.push_back(game);
        }
        const std::string bytes = file_bytes(games, 12345);
        std::vector<Game> back;
        std::uint64_t seed = 0;
        std::string error;
        check(read_games(bytes, back, seed, &error), "read_games: " + error);
        check(seed == 12345, "seed round trip");
        check(back.size() == games.size(), "game count round trip");
        for (std::size_t g = 0; g < games.size() && g < back.size(); ++g) {
            check(back[g].start_fen == games[g].start_fen && back[g].white_result_x2 == games[g].white_result_x2
                  && back[g].termination == games[g].termination && back[g].opening_plies == games[g].opening_plies
                  && back[g].plies.size() == games[g].plies.size(), "game header round trip " + std::to_string(g));
            for (std::size_t i = 0; i < games[g].plies.size() && i < back[g].plies.size(); ++i) {
                check(encode_move(back[g].plies[i].move) == encode_move(games[g].plies[i].move)
                      && back[g].plies[i].score == games[g].plies[i].score && back[g].plies[i].flags == games[g].plies[i].flags,
                      "ply round trip");
            }
        }
        std::string broken = bytes;
        broken[60] = static_cast<char>(broken[60] ^ 1);
        check(!read_games(broken, back, seed, &error) && error == "checksum mismatch", "flipped byte detected: " + error);
        broken = bytes.substr(0, bytes.size() - 3);
        check(!read_games(broken, back, seed, &error), "truncated file detected");
        broken = bytes;
        broken[8] = static_cast<char>(broken[8] + 1);   // game count
        check(!read_games(broken, back, seed, &error), "bad header count detected: " + error);
        // records_of of the synthetic games: kept plies == rows, boards match a direct replay
        std::string rows, scores, metas, hces, text;
        std::uint64_t count = 0;
        check(records_of(games[0], rows, scores, metas, hces, &text, count, &error), "records_of: " + error);
        std::uint64_t expected = 0;
        for (const Ply& p : games[0].plies) expected += (p.flags & RecordKept) != 0 ? 1 : 0;
        check(count == expected && rows.size() == 32 * count && scores.size() == 2 * count && metas.size() == count && hces.size() == 2 * count,
              "records_of sizes");
        std::cout << "serialisation: " << games.size() << " synthetic games, " << count << " records of game 0\n";
    }

    // 3. played games: direct records == converter records; flags consistent with the rules; determinism
    {
        Config config = test_config(scratch + "/t3");
        Searcher searcher(1, 1);
        Stats stats;
        std::string error;
        std::vector<Game> games;
        int attempts = 0;
        while (games.size() < 4 && attempts < 20) {
            Game game;
            if (play_game(searcher, config, kStart, game_seed(9, static_cast<std::uint64_t>(attempts)), game, stats, &error)) games.push_back(game);
            else check(error.empty(), "play_game error: " + error);
            ++attempts;
        }
        check(games.size() == 4, "played 4 games");
        std::uint64_t kept = 0, searched = 0;
        for (const Game& game : games) {
            Board board;
            check(board.set_fen(game.start_fen), "start fen");
            for (std::size_t i = 0; i < game.plies.size(); ++i) {
                const Ply& p = game.plies[i];
                const Move move = decode_move(board, encode_move(p.move));
                check(!move.is_none(), "replayed move legal");
                if (i < game.opening_plies) {
                    check(p.score == ScoreNone && p.flags == 0, "opening ply has no score and no flags");
                } else {
                    ++searched;
                    check(p.score != ScoreNone, "searched ply has a score");
                    const bool in_check = board.in_check();
                    check(((p.flags & RecordInCheck) != 0) == in_check, "in-check flag matches the board");
                    if ((p.flags & RecordKept) != 0) {
                        ++kept;
                        check(!in_check && !move.is_capture() && !move.is_promotion() && std::abs(p.score) <= config.max_score
                              && !is_mate_score(p.score) && (p.flags & (RecordNoisyPv | RecordEarly | RecordSubsampled)) == 0,
                              "kept record obeys the filters");
                        const int game_ply = 2 * (board.fullmove_number() - 1) + (board.side_to_move() == Black ? 1 : 0);
                        check(game_ply >= config.min_ply, "kept record not before min_ply");
                    }
                    if ((p.flags & RecordGivesCheck) != 0) check(board.gives_check(move), "gives-check flag");
                }
                Undo undo;
                check(board.make_move(move, undo), "make replayed move");
            }
            int wr = 1;
            if (game.termination == Termination::Checkmate) {
                check(!board.has_legal_move() && board.in_check(), "checkmate termination is a checkmate");
                wr = board.side_to_move() == White ? 0 : 2;
                check(game.white_result_x2 == wr, "checkmate result");
            }
            if (game.termination == Termination::Stalemate) check(!board.has_legal_move() && !board.in_check() && game.white_result_x2 == 1, "stalemate");
            if (game.termination == Termination::AdjudicatedWin) check(game.white_result_x2 != 1, "adjudicated win is decisive");
            if (game.termination == Termination::AdjudicatedDraw || game.termination == Termination::MaxPly) check(game.white_result_x2 == 1, "draw result");
        }
        std::cout << "played: " << games.size() << " games, " << searched << " searched plies, " << kept << " kept records, "
                  << stats.opening_redraws << " opening redraws\n";
        check(kept > 0, "some records were kept");
        // determinism: a fresh searcher and the same seed give byte-identical games
        {
            Searcher other(1, 1);
            Stats s2;
            std::vector<Game> again;
            attempts = 0;
            while (again.size() < 4 && attempts < 20) {
                Game game;
                if (play_game(other, config, kStart, game_seed(9, static_cast<std::uint64_t>(attempts)), game, s2, &error)) again.push_back(game);
                ++attempts;
            }
            check(file_bytes(again, 9) == file_bytes(games, 9), "same seed -> byte-identical games");
        }
        // converter output == direct records
        std::string rows, scores, metas, hces, text;
        std::uint64_t count = 0;
        for (const Game& game : games) check(records_of(game, rows, scores, metas, hces, &text, count, &error), "records_of played: " + error);
        check(count == kept, "converter record count == kept flags");
        // direct replay with pack_board / evaluate_uncached must give the same bytes
        std::string rows2, hces2;
        for (const Game& game : games) {
            Board board;
            (void)board.set_fen(game.start_fen);
            for (const Ply& p : game.plies) {
                if ((p.flags & RecordKept) != 0) {
                    const auto packed = pack_board(board);
                    rows2.append(reinterpret_cast<const char*>(packed.data()), packed.size());
                    const int h = Evaluator::evaluate_uncached(board);
                    hces2.push_back(static_cast<char>(h & 0xFF));
                    hces2.push_back(static_cast<char>((h >> 8) & 0xFF));
                }
                Undo undo;
                (void)board.make_move(decode_move(board, encode_move(p.move)), undo);
            }
        }
        check(rows == rows2 && hces == hces2, "converter rows and HCE == direct replay");
    }

    // 4. end-to-end: run_generate with --pos, then run_convert; files byte-identical; info written
    {
        Config config = test_config(scratch + "/t4");
        config.games = 3;
        config.write_pos = true;
        config.write_text = true;
        check(run_generate(config) == 0, "run_generate");
        std::string error;
        check(run_convert(scratch + "/t4.fgb", scratch + "/t4conv", true, &error) == 0, "run_convert: " + error);
        const std::string pos_a = read_file(scratch + "/t4.pos"), pos_b = read_file(scratch + "/t4conv.pos");
        const std::string hce_a = read_file(scratch + "/t4.hce"), hce_b = read_file(scratch + "/t4conv.hce");
        const std::string txt_a = read_file(scratch + "/t4.txt"), txt_b = read_file(scratch + "/t4conv.txt");
        check(!pos_a.empty() && pos_a == pos_b, "direct .pos == converted .pos (" + std::to_string(pos_a.size()) + " bytes)");
        check(!hce_a.empty() && hce_a == hce_b, "direct .hce == converted .hce");
        check(!txt_a.empty() && txt_a == txt_b, "direct .txt == converted .txt");
        check(!read_file(scratch + "/t4.info.json").empty(), "info.json written");
        // the file reads back with the header counts of the written games
        std::vector<Game> games;
        std::uint64_t seed = 0;
        check(read_games(read_file(scratch + "/t4.fgb"), games, seed, &error) && games.size() == 3 && seed == 1, "fgb reads back: " + error);
        // same seed again -> byte-identical .fgb and .pos
        Config again = test_config(scratch + "/t4b");
        again.games = 3;
        again.write_pos = true;
        check(run_generate(again) == 0, "run_generate again");
        const std::string fgb_a = read_file(scratch + "/t4.fgb"), fgb_b = read_file(scratch + "/t4b.fgb");
        check(fgb_a == fgb_b, "same seed -> byte-identical .fgb (" + std::to_string(fgb_a.size()) + " bytes)");
        check(read_file(scratch + "/t4b.pos") == pos_a, "same seed -> byte-identical .pos");
        // a different seed differs
        Config other = test_config(scratch + "/t4c");
        other.games = 3;
        other.seed = 2;
        check(run_generate(other) == 0 && read_file(scratch + "/t4c.fgb") != fgb_a, "different seed -> different games");
        std::cout << "end-to-end: fgb " << fgb_a.size() << " bytes, pos " << pos_a.size() << " bytes for 3 games\n";
    }

    // 5. argument parsing
    {
        std::string error;
        Config c;
        check(parse_args({"--out", "x", "--games", "5", "--nodes", "123", "--skip-prob", "0.25", "--keep-in-check", "--pos"}, c, &error)
              && c.games == 5 && c.nodes == 123 && c.skip_prob == 0.25 && !c.filter_in_check && c.write_pos, "parse_args ok: " + error);
        Config c2;
        check(!parse_args({"--games", "5"}, c2, &error), "parse_args needs --out");
        Config c3;
        check(!parse_args({"--out", "x", "--games"}, c3, &error), "parse_args missing value");
        Config c4;
        check(!parse_args({"--out", "x", "--games", "5", "--bogus"}, c4, &error), "parse_args unknown argument");
        Config c5;
        check(!parse_args({"--out", "x"}, c5, &error), "parse_args needs a limit");
    }

    std::cout << checks << " checks, " << failures << " failures\n";
    return failures == 0 ? 0 : 1;
}
