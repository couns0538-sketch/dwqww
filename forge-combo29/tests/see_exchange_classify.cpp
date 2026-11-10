// Portable copy of the preserved original; only the include path below differs.
#define main audit_main
#include "see_exchange_audit.cpp"
#undef main
Move least(Board& b,int target){Move best=Move::none();int order=10000;for(auto m:b.legal_moves(true)){if(m.to!=target||!m.is_capture())continue;int key=piece_type(b.piece_at(m.from))*64+m.from;if(key<order){order=key;best=m;}}return best;}
int greedy(Board& b,int target){auto m=least(b,target);if(m.is_none())return 0;int imm=gain(b,m);Undo u;(void)b.make_move(m,u);int v=imm-greedy(b,target);b.unmake_move(m,u);return std::max(0,v);}
void trace(Board& b,int target,int depth=0){if(depth>12)return;Move lva=least(b,target);if(lva.is_none())return;std::cout<<std::string(depth*2,' ')<<"LVA "<<Board::move_to_uci(lva)<<" choices:";for(auto m:b.legal_moves(true)){if(m.to!=target||!m.is_capture())continue;int imm=gain(b,m);Undo u;(void)b.make_move(m,u);int v=imm-best_reply(b,target),g=imm-greedy(b,target);b.unmake_move(m,u);std::cout<<" "<<Board::move_to_uci(m)<<"(exact="<<v<<",greedy="<<g<<")";}std::cout<<"\n";Undo u;(void)b.make_move(lva,u);trace(b,target,depth+1);b.unmake_move(lva,u);}
int main(int argc,char**argv){Board b;if(!b.set_fen(argv[1]))return 1;auto m=b.parse_uci(argv[2]);if(!m)return 2;int s=b.static_exchange(*m),ex=oracle(b,*m),imm=gain(b,*m);Undo u;(void)b.make_move(*m,u);int gr=imm-greedy(b,m->to);std::cout<<"SEE="<<s<<" exact="<<ex<<" legal_LVA="<<gr<<"\n";trace(b,m->to);}
