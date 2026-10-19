#include "forge/board.hpp"
#include "forge/search.hpp"
#include <iostream>
#include <string>
namespace forge { struct SearcherTestProbe { static int alpha_beta(Searcher& s, Board& b, int d, int a, int beta, int ply=0){ return s.alpha_beta(b,d,ply,a,beta); } }; }
int main(int argc,char**argv){ if(argc!=6){std::cerr<<"usage: probe FEN depth alpha beta hash\n";return 2;} forge::Board b; if(!b.set_fen(argv[1])) return 3; forge::Searcher s((std::size_t)std::stoul(argv[5])); int v=forge::SearcherTestProbe::alpha_beta(s,b,std::stoi(argv[2]),std::stoi(argv[3]),std::stoi(argv[4])); std::cout<<v<<"\n"; }
