// FEN-only derivative of our own native NNUE oracle, not another engine.
// Dependency sha256 ea4593539d4d23744b0cc7fb5cf1c21eb9a8385fb6b7cf534f8d55c5e7e6f93e.
// Starts/Seed/LCG and actual legal-API walk order are retained exactly.
#include "forge/board.hpp"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_set>

namespace {
constexpr std::uint64_t Seed = 0x243f6a8885a308d3ULL;
constexpr std::array<const char*, 10> Starts{
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
    "4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
    "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
    "4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
};
std::uint64_t random_state = Seed;
std::uint64_t random_word() {
    random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return random_state;
}

void require(bool yes,const char* message) { if (!yes) throw std::runtime_error(message); }
std::uint64_t parse(const char* word) {
    std::size_t used=0;const auto value=std::stoull(word,&used);
    require(used==std::string_view(word).size(),"invalid integer");return value;
}
struct Writer {
    std::unordered_set<std::string> seen;
    std::uint64_t wanted,maximum,attempts=0,games=0;
    Writer(std::uint64_t count,std::uint64_t limit):wanted(count),maximum(limit) {seen.reserve(static_cast<std::size_t>(count));}
    bool done() const {return seen.size()==wanted;}
    void emit(const forge::Board& board) {
        require(attempts<maximum,"finite attempt limit reached before unique target");++attempts;
        const std::string fen=board.fen();std::size_t end=0;
        for (int field=0;field<4;++field) {end=fen.find(' ',end);require(end!=std::string::npos,"board API returned incomplete FEN");if (field<3)++end;}
        if (seen.insert(fen.substr(0,end)).second) std::cout<<fen<<'\n';
    }
    void start(forge::Board& board,const char* fen) {require(board.set_fen(fen),"invalid original fixture");++games;emit(board);}
};
}
int main(int argc,char** argv) {
    try {
        require(argc==5 && std::string_view(argv[1])=="--positions" && std::string_view(argv[3])=="--max-attempts","usage: FEN_generator --positions COUNT --max-attempts COUNT");
        const auto count=parse(argv[2]),limit=parse(argv[4]);
        require(count>=1024U && count<=1000000U && limit>=count && limit<=100000000U,"counts outside bounded protocol");
        std::ios::sync_with_stdio(false);Writer output(count,limit);forge::Board board;
        // Identical first-move enumeration; only NNUE observations are omitted.
        for (const char* fen:Starts) {
            output.start(board,fen);
            for (auto move:board.legal_moves()) {
                forge::Undo undo;require(board.make_move(move,undo),"legal first move rejected");
                output.emit(board);board.unmake_move(move,undo);
            }
        }
        require(!output.done(),"fixtures exhaust target");
        while (!output.done()) {
            const auto fixture=static_cast<std::size_t>(random_word()%Starts.size());
            output.start(board,Starts[fixture]);
            for (std::uint32_t ply=1U;ply<=192U && !output.done();++ply) {
                const auto moves=board.legal_moves();if(moves.empty())break;
                const auto move=moves[static_cast<std::size_t>(random_word()%moves.size())];
                forge::Undo undo;require(board.make_move(move,undo),"legal walk move rejected");output.emit(board);
            }
        }
        std::cout.flush();require(static_cast<bool>(std::cout),"FEN output write failed");
        std::cerr<<"unique="<<output.seen.size()<<" attempts="<<output.attempts<<" duplicates="<<(output.attempts-output.seen.size())<<" games="<<output.games<<" seed="<<Seed<<" walk_plies=192\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<"FEN_generator: "<<e.what()<<'\n';return 1;}
}
