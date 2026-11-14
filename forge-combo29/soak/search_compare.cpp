#include "uci_process.hpp"
#include "forge/board.hpp"
#include <algorithm>
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <vector>

static std::string compact(const UciResult& r){return r.move+" "+r.score_kind+" "+std::to_string(r.score)+" nodes "+std::to_string(r.nodes)+" depth "+std::to_string(r.depth);}
static std::vector<std::string> read_fens(const std::string& path){std::ifstream in(path);if(!in)throw std::runtime_error("cannot read positions");std::vector<std::string> fens;std::string line;
    while(std::getline(in,line)){if(line.empty()||line[0]=='#')continue;std::istringstream row(line);std::string board,side,castle,ep,half="0",full="1";if(!(row>>board>>side>>castle>>ep))continue;std::string h,f;if(row>>h>>f){if(h.find_first_not_of("0123456789")==std::string::npos&&f.find_first_not_of("0123456789")==std::string::npos){half=h;full=f;}}const std::string fen=board+" "+side+" "+castle+" "+ep+" "+half+" "+full;forge::Board b;if(!b.set_fen(fen))throw std::runtime_error("invalid corpus FEN "+line);if(!b.legal_moves().empty()&&!b.is_insufficient_material())fens.push_back(fen);}
    return fens;
}
static std::string krk_fen(int wk,int wr,int bk){std::array<char,64> sq{};sq[wk]='K';sq[wr]='R';sq[bk]='k';std::string fen;
    for(int rank=7;rank>=0;--rank){int empty=0;for(int file=0;file<8;++file){const char p=sq[rank*8+file];if(!p){++empty;continue;}if(empty){fen+=char('0'+empty);empty=0;}fen+=p;}if(empty)fen+=char('0'+empty);if(rank)fen+='/';}return fen+" w - - 0 1";}
static std::string lost_krk(const std::string& fen,const std::string& move){
    forge::Board b;if(!b.set_fen(fen))return "invalid_fen";const auto m=b.parse_uci(move);if(!m)return "illegal_move";const auto legal=b.legal_moves();if(std::find(legal.begin(),legal.end(),*m)==legal.end())return "illegal_move";
    forge::Undo undo;if(!b.make_move(*m,undo))return "illegal_move";const auto replies=b.legal_moves();if(replies.empty())return b.in_check()?"":"stalemate";
    for(const auto reply:replies)if(b.captured_piece(reply)==forge::WR)return "rook_can_be_captured";
    return "";
}
int main(int argc,char** argv){
    std::signal(SIGPIPE,SIG_IGN);
    std::string mode="compare",input,output,fault_dir,lock,intg;std::uint64_t seed=1,offset=0,limit=1000000;int seconds=240;
    for(int i=1;i<argc;++i){if(i+1>=argc)return 2;const std::string a=argv[i],v=argv[++i];
        if(a=="--mode")mode=v;else if(a=="--input")input=v;else if(a=="--output")output=v;else if(a=="--fault-dir")fault_dir=v;else if(a=="--lock")lock=v;else if(a=="--integration")intg=v;
        else if(a=="--seed")seed=std::stoull(v);else if(a=="--offset")offset=std::stoull(v);else if(a=="--limit")limit=std::stoull(v);else if(a=="--seconds")seconds=std::stoi(v);else return 2;}
    if(lock.empty()||intg.empty()||fault_dir.empty())return 2;std::filesystem::create_directories(fault_dir);
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(seconds);
    std::uint64_t positions=0,differences=0,attempts=0,selected=0,lock_runs=0,int_runs=0,lock_misses=0,int_misses=0,lock_lost=0,int_lost=0,lock_failures=0,int_failures=0,faults=0;
    try{
        UciProcess reference(lock),integration(intg);
        if(mode=="compare"){
            const auto fens=read_fens(input);if(fens.empty())throw std::runtime_error("empty corpus");
            for(std::uint64_t i=offset;i<fens.size() && positions<limit && std::chrono::steady_clock::now()<deadline;++i){
                const auto& fen=fens[i];std::cout<<"CASE seed="<<seed<<" index="<<i<<" fen="<<fen<<std::endl;
                const auto a=reference.search(fen,9),b=integration.search(fen,9);++positions;
                std::cout<<"RESULT index="<<i<<" lock="<<compact(a)<<" integration="<<compact(b)<<std::endl;
                if(a.same(b))continue;
                ++differences;++faults;std::ofstream file(fault_dir+"/E-"+std::to_string(seed)+"-"+std::to_string(i)+".txt");
                file<<"E depth-9 comparison difference\nSeed "<<seed<<" corpus index "<<i<<"\nFEN "<<fen<<"\nThreads 1 Hash 16 OwnBook false; fresh ucinewgame before every search.\nOriginal lock output:\n"<<a.transcript<<"Original integration output:\n"<<b.transcript;
                int repeated=0;for(int trial=1;trial<=10;++trial){const auto x=reference.search(fen,9),y=integration.search(fen,9);if(!x.same(y))++repeated;file<<"\nTry "<<trial<<"\nLOCK\n"<<x.transcript<<"INTEGRATION\n"<<y.transcript;}
                file<<"\nRepeated "<<repeated<<" / 10 tries.\n";file.flush();
                std::cout<<"FAULT E seed="<<seed<<" index="<<i<<" repeats="<<repeated<<"/10"<<std::endl;
                if(faults>=10)break;
            }
        }else if(mode=="select-krk"){
            std::mt19937_64 rng(seed);std::set<std::string> seen;std::ofstream selected_file(output);
            while(selected<limit && std::chrono::steady_clock::now()<deadline){
                const int bk=static_cast<int>(rng()%64),wk=static_cast<int>(rng()%64),wr=static_cast<int>(rng()%64);
                if(bk==wk||wr==bk||wr==wk)continue;const int df=std::abs((bk%8)-(wk%8)),dr=std::abs((bk/8)-(wk/8));
                if(std::max(df,dr)<2||std::max(df,dr)>3)continue;if(bk%8!=0&&bk%8!=7&&bk/8!=0&&bk/8!=7)continue;
                const auto fen=krk_fen(wk,wr,bk);if(!seen.insert(fen).second)continue;forge::Board board;if(!board.set_fen(fen)||board.in_check(forge::Black))continue;
                std::cout<<"SELECT_CASE seed="<<seed<<" fen="<<fen<<std::endl;++attempts;
                const auto a=reference.search(fen,14);if(!a.positive_mate())continue;const auto b=integration.search(fen,14);if(!b.positive_mate())continue;
                ++selected;selected_file<<fen<<'\n';selected_file.flush();std::cout<<"SELECTED "<<selected<<" fen="<<fen<<" lock="<<compact(a)<<" integration="<<compact(b)<<std::endl;
            }
        }else if(mode=="krk"){
            const auto fens=read_fens(input);reference.threads(2);integration.threads(2);
            for(std::uint64_t i=offset;i<fens.size() && positions<limit && std::chrono::steady_clock::now()<deadline;++i){
                const auto& fen=fens[i];++positions;
                for(int build=0;build<2;++build){auto& engine=build?integration:reference;const std::string name=build?"integration":"lock";std::string transcript;int misses=0,lost=0,failures=0;
                    for(int trial=1;trial<=10;++trial){std::cout<<"KRK_CASE seed="<<seed<<" index="<<i<<" build="<<name<<" try="<<trial<<" fen="<<fen<<std::endl;
                        const auto r=engine.search(fen,14);const auto loss=lost_krk(fen,r.move);if(!r.positive_mate())++misses;if(!loss.empty())++lost;if(!r.positive_mate()||!loss.empty())++failures;
                        transcript+="\nTry "+std::to_string(trial)+"\n"+r.transcript+"mate_missing="+std::to_string(!r.positive_mate())+" lost_mate_reason="+loss+"\n";
                        std::cout<<"KRK_RESULT "<<name<<" "<<compact(r)<<" missing="<<!r.positive_mate()<<" lost="<<(loss.empty()?"none":loss)<<std::endl;
                    }
                    if(build){int_runs+=10;int_misses+=misses;int_lost+=lost;int_failures+=failures;}else{lock_runs+=10;lock_misses+=misses;lock_lost+=lost;lock_failures+=failures;}
                    if(misses||lost){++faults;std::ofstream file(fault_dir+"/G-"+std::to_string(seed)+"-"+std::to_string(i)+"-"+name+".txt");file<<"G two-thread KRK mate failure: "<<name<<"\nSeed "<<seed<<" index "<<i<<"\nFEN "<<fen<<"\nThreads 2 Hash 16 OwnBook false, go depth 14, fresh ucinewgame each try.\n"<<transcript<<"\nMate score missing "<<misses<<" / 10 tries; mate-losing move "<<lost<<" / 10 tries.\n";}
                }
            }
        }else throw std::runtime_error("unknown mode");
    }catch(const std::exception& e){++faults;std::cout<<"FAULT_EXCEPTION "<<e.what()<<std::endl;}
    std::cout<<"SUMMARY {\"seed\":"<<seed<<",\"positions\":"<<positions<<",\"differences\":"<<differences<<",\"selection_attempts\":"<<attempts<<",\"selected\":"<<selected
        <<",\"lock_runs\":"<<lock_runs<<",\"integration_runs\":"<<int_runs<<",\"lock_misses\":"<<lock_misses<<",\"integration_misses\":"<<int_misses
        <<",\"lock_lost_mates\":"<<lock_lost<<",\"integration_lost_mates\":"<<int_lost<<",\"lock_failures\":"<<lock_failures<<",\"integration_failures\":"<<int_failures<<",\"faults\":"<<faults<<"}"<<std::endl;
    return faults?1:0;
}
