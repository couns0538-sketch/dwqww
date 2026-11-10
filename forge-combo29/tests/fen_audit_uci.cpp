// Exercise the actual production apply_position function, not a copied parser.
#define main forge_uci_entry_for_audit
#include "../src/uci.cpp"
#undef main
#include <cstdlib>
static void require(bool ok,const char* text){if(!ok){std::cerr<<"FAIL "<<text<<'\n';std::exit(1);}}
static bool same(const forge::Board&a,const forge::Board&b){return a.fen()==b.fen()&&a.key()==b.key()&&a.pawn_key()==b.pawn_key()&&a.checkers()==b.checkers()&&a.key_history()==b.key_history();}
static void apply_case(forge::Board&b,const std::string&command){std::istringstream in(command);apply_position(b,in);}
int main(){
    forge::Board baseline;apply_case(baseline,"startpos moves d2d4 d7d5");require(baseline.history_size()==3,"seed history");
    const std::vector<std::string> rejected={
        "", "unknown", "startpos garbage", "startpos moves e2e4 e7e5 invalid",
        "startpos moves e2e4 e7e5 e1e8", "startpos moves e2e4 e2e3", "startpos moves g1f3q",
        "startpos moves e2e4 moves e7e5", "startpos moves e2e4junk",
        "fen", "fen 8/8/8/8/8/8/8/8 w - - 0 1", "fen 4k3/8/8/8/8/8/8/4K3 w - - 0",
        "fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1 trailing",
        "fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1 moves e1e2 e8e7 bad",
        "fen 4k3/8/8/8/8/8/8/K3R3 w - - 0 1",
        "fen 4k3/8/8/8/8/8/8/4K3 w - - 0 9223372036854775808",
        "startpos moves "+std::string(10000,'x')};
    std::ostringstream messages;auto* old=std::cout.rdbuf(messages.rdbuf());
    for(const auto&command:rejected){auto b=baseline;apply_case(b,command);require(same(b,baseline),"rejected position partially committed");}
    forge::Board b=baseline;apply_case(b,"startpos moves e2e4 e7e5");
    forge::Board expected;for(auto text:{"e2e4","e7e5"}){auto m=expected.parse_uci(text);require(m.has_value(),"expected legal");forge::Undo u;(void)expected.make_move(*m,u);}
    require(same(b,expected),"valid startpos moves commit");
    apply_case(b,"startpos moves");forge::Board initial;require(same(b,initial),"empty move list commit");
    const std::string fen="4k3/8/8/8/8/8/8/4K3 w - - 0 1";
    apply_case(b,"fen "+fen+" moves e1e2 e8e7");require(expected.set_fen(fen),"seed FEN");
    for(auto text:{"e1e2","e8e7"}){auto m=expected.parse_uci(text);require(m.has_value(),"expected king move");forge::Undo u;(void)expected.make_move(*m,u);}
    require(same(b,expected),"valid fen moves commit");
    std::cout.rdbuf(old);
    require(messages.str().find("illegal move")!=std::string::npos && messages.str().find("invalid FEN")!=std::string::npos,"missing error diagnostics");
    std::cout<<"PASS actual_UCI_position_handler rejected_atomic="<<rejected.size()<<" valid_commits=3\n";
}
