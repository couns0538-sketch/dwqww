#include "forge/search.hpp"
#include "krk_oracle.hpp"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Acceptance and measurement driver only. No engine code is changed.
// Oracle is the retained exact KRK retrograde implementation; it shares Forge
// move/attack primitives and does not model repetition or the fifty-move rule.
struct Counts {
    int searches=0, positive_mates=0, missing_mates=0, illegal=0, lost_wins=0;
    int shorter_than_root=0, shorter_than_move=0, exact_hits=0, incomplete=0;
    long long nodes=0, excess_plies=0, excess_uci_moves=0;
};

void configure(const std::string& mode, bool nnue) {
    forge::nnue::enabled=nnue;
    forge::tune::SoundMatePruning=false;
    forge::tune::MateAlphaGuard=mode=="A";
    forge::tune::SoundArmPv=forge::tune::SoundPruneArm::ForceOff;
    forge::tune::SoundArmInCheck=forge::tune::SoundPruneArm::ForceOff;
    forge::tune::SoundArmMateAlpha=mode=="B" ? forge::tune::SoundPruneArm::ForceOn : forge::tune::SoundPruneArm::ForceOff;
    forge::tune::SoundPruneTrace=false;
}

void print_summary(const std::string& key, const Counts& c) {
    std::cout << "SUMMARY {\"group\":" << std::quoted(key)
              << ",\"searches\":" << c.searches << ",\"positive_mates\":" << c.positive_mates
              << ",\"missing_mates\":" << c.missing_mates << ",\"illegal\":" << c.illegal
              << ",\"lost_wins\":" << c.lost_wins << ",\"shorter_than_root\":" << c.shorter_than_root
              << ",\"shorter_than_move\":" << c.shorter_than_move << ",\"exact_hits\":" << c.exact_hits
              << ",\"incomplete\":" << c.incomplete << ",\"nodes\":" << c.nodes
              << ",\"excess_plies_sum\":" << c.excess_plies
              << ",\"excess_uci_moves_sum\":" << c.excess_uci_moves
              << ",\"mean_reported_minus_exact_plies\":";
    if(c.positive_mates) std::cout << double(c.excess_plies)/c.positive_mates;
    else std::cout << "null";
    std::cout << ",\"mean_reported_minus_exact_uci_moves\":";
    if(c.positive_mates) std::cout << double(c.excess_uci_moves)/c.positive_mates;
    else std::cout << "null";
    std::cout << "}" << std::endl;
}

int main(int argc,char** argv) {
  try {
    if(argc!=3) throw std::runtime_error("usage: krk_guard_validation roots.txt soundness|measurements|fixture");
    const std::string batch=argv[2];
    if(batch!="soundness"&&batch!="measurements"&&batch!="fixture") throw std::runtime_error("unknown batch");
    std::ifstream in(argv[1]);
    if(!in) throw std::runtime_error("roots not readable");
    std::vector<std::string> roots; std::string line;
    while(std::getline(in,line)) if(!line.empty()&&line.front()!='#') roots.push_back(line);
    if(roots.size()!=40) throw std::runtime_error("expected exactly 40 frozen roots");
    if(batch=="fixture") roots={"8/8/8/8/8/1R6/2k5/5K2 w - - 0 1"};
    const soak::KrkOracle oracle;
    for(const auto& fen:roots) {
        forge::Board b;
        if(!b.set_fen(fen)) throw std::runtime_error("bad input FEN");
        const auto root=oracle.assess_root(b);
        if(!root.supported||!root.legal||root.dtm_plies<=0) throw std::runtime_error("root not supported winning KRK");
    }
    std::map<std::string,Counts> groups;
    const std::vector<int> thread_counts=batch=="soundness"?std::vector<int>{1,2,4}:std::vector<int>{1};
    const std::vector<bool> nnue_modes=batch=="soundness"?std::vector<bool>{true}:std::vector<bool>{true,false};
    const std::vector<std::string> modes=batch=="soundness"?std::vector<std::string>{"A"}:std::vector<std::string>{"off","A","B"};
    const int depth=batch=="soundness"?14:13;
    for(bool nnue:nnue_modes) for(int threads:thread_counts) for(const auto& mode:modes) {
        configure(mode,nnue); // Never mutate global controls with workers searching.
        forge::Searcher searcher(16,threads);
        const std::string key=batch+"-"+mode+"-nnue"+(nnue?"true":"false")+"-t"+std::to_string(threads);
        auto& c=groups[key];
        for(std::size_t i=0;i<roots.size();++i) {
            forge::Board board;
            if(!board.set_fen(roots[i])) throw std::runtime_error("FEN rejected after validation");
            searcher.clear();
            forge::SearchLimits limits; limits.depth=depth;
            std::cout << "BEGIN {\"group\":" << std::quoted(key) << ",\"index\":" << i
                      << ",\"fen\":" << std::quoted(roots[i]) << ",\"depth\":" << depth
                      << ",\"threads\":" << threads << ",\"Hash\":16,\"OwnBook\":false,\"fresh_state\":true}" << std::endl;
            const auto result=searcher.search(board,limits,true,forge::Searcher::TTAccess::Exclusive);
            const auto a=oracle.assess_move(board,result.best_move);
            const bool legal=!result.best_move.is_none()&&board.is_legal(result.best_move);
            const bool mate=forge::is_mate_score(result.score)&&result.score>0;
            const int plies=mate?forge::MateValue-result.score:-1;
            const bool shorter_root=mate&&plies<a.root_dtm_plies;
            const bool shorter_move=mate&&(a.move_dtm_plies<0||plies<a.move_dtm_plies);
            ++c.searches; c.nodes+=result.nodes; c.positive_mates+=mate; c.missing_mates+=!mate;
            c.illegal+=!legal; c.lost_wins+=a.loses_forced_mate;
            c.shorter_than_root+=shorter_root; c.shorter_than_move+=shorter_move;
            c.exact_hits+=mate&&plies==a.root_dtm_plies;
            c.incomplete+=result.depth<depth;
            if(mate) { c.excess_plies+=plies-a.root_dtm_plies; c.excess_uci_moves+=(plies+1)/2-(a.root_dtm_plies+1)/2; }
            std::cout << "ROW {\"group\":" << std::quoted(key) << ",\"index\":" << i
                      << ",\"fen\":" << std::quoted(roots[i]) << ",\"bestmove\":" << std::quoted(forge::Board::move_to_uci(result.best_move))
                      << ",\"score\":" << result.score << ",\"depth\":" << result.depth
                      << ",\"nodes\":" << result.nodes << ",\"positive_mate\":" << (mate?"true":"false")
                      << ",\"reported_mate_plies\":" << plies << ",\"exact_root_dtm_plies\":" << a.root_dtm_plies
                      << ",\"chosen_move_dtm_plies\":" << a.move_dtm_plies
                      << ",\"legal\":" << (legal?"true":"false")
                      << ",\"loses_win\":" << (a.loses_forced_mate?"true":"false")
                      << ",\"shorter_than_root\":" << (shorter_root?"true":"false")
                      << ",\"shorter_than_move\":" << (shorter_move?"true":"false") << "}" << std::endl;
        }
        print_summary(key,c);
    }
    int failures=0;
    for(const auto& [key,c]:groups) failures+=c.illegal+c.lost_wins+c.shorter_than_root+c.shorter_than_move+c.incomplete;
    std::cout << "COMPLETE batch=" << batch << " groups=" << groups.size() << " failures=" << failures << std::endl;
    return failures?1:0;
  } catch(const std::exception& e) { std::cerr << "SETUP_ERROR " << e.what() << std::endl; return 2; }
}
