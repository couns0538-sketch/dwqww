// Independent fifty-move claim model v3.
// Node value at clock>=100 for the side to move = max(0, best continuation), because
// FIDE 9.3 makes the claim OPTIONAL and a mating move ends the game at once.
// Mate/stalemate are decided BEFORE the claim option. Depth always decrements.
#include "forge/board.hpp"
#include "forge/bitboard.hpp"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <algorithm>
using namespace forge;
static long long g_nodes=0, g_cap=20000000; static bool g_cap_hit=false;
static int material(Board& b){
  auto cnt=[&](Color c,PieceType t){ return popcount(b.pieces(c,t)); };
  int s=0;
  s += 100*(cnt(White,Pawn)-cnt(Black,Pawn));
  s += 320*(cnt(White,Knight)-cnt(Black,Knight));
  s += 330*(cnt(White,Bishop)-cnt(Black,Bishop));
  s += 500*(cnt(White,Rook)-cnt(Black,Rook));
  s += 900*(cnt(White,Queen)-cnt(Black,Queen));
  return s;
}
static int g_ply=0;
static constexpr int kMaxPly=40;
static int solve(Board& b,int depth,int alpha,int beta){
  if(++g_nodes>g_cap){ g_cap_hit=true; return 0; }
  if(g_ply>kMaxPly) return b.side_to_move()==White? material(b): -material(b);
  const MoveList mv=b.legal_moves(false);
  if(mv.size()==0) return b.in_check()? -30000+(128-depth) : 0;   // mate/stalemate first
  const bool claimable = b.halfmove_clock()>=100;
  if(depth<=0) return b.side_to_move()==White? material(b) : -material(b);
  int best = claimable ? 0 : -99999;    // the claiming side may take the draw
  for(const Move m: mv){
    Undo u; (void)b.make_move(m,u); ++g_ply;
    int s=-solve(b,depth-1,-beta,-alpha);
    --g_ply; b.unmake_move(m,u);
    if(s>best) best=s;
    if(best>alpha) alpha=best;
    if(alpha>=beta) break;
  }
  return best;
}
int main(int argc,char**argv){
  Board b; std::string e;
  if(!b.set_fen(argv[1],&e)){ printf("REFUSED %s\n",e.c_str()); return 3; }
  int d=atoi(argv[2]); if(argc>3) g_cap=atoll(argv[3]);
  int s=solve(b,d,-99999,99999);
  if(g_cap_hit) printf("CAPPED\n"); else printf("score %d nodes %lld\n",s,g_nodes);
  return 0;
}
