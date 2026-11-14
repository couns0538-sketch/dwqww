// Phase D: exact incremental/full and built-in/file NNUE comparisons.
#include "forge/nnue.hpp"
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

struct Counts { std::uint64_t positions=0,incremental=0,loaded=0,nulls=0,castles=0,ep=0,promotions=0,captures=0,damaged=0,faults=0; };
static Counts total;
static std::uint64_t batch_seed=1,chunk_id=0;
static int full_value(const forge::Board& b){forge::nnue::Accumulator a;forge::nnue::refresh(b,a);return forge::nnue::evaluate(b,a);}
static void fail(const std::string& kind,const forge::Board& b,const std::string& start,const std::string& moves,std::uint64_t index,int want,int got){
    ++total.faults;
    std::cout<<"FAULT {\"kind\":\""<<kind<<"\",\"seed\":"<<batch_seed<<",\"chunk\":"<<chunk_id
        <<",\"index\":"<<index<<",\"start\":\""<<start<<"\",\"moves\":\""<<moves
        <<"\",\"fen\":\""<<b.fen()<<"\",\"expected\":"<<want<<",\"actual\":"<<got<<"}"<<std::endl;
    throw std::runtime_error(kind);
}
static void walk(std::uint64_t seed,std::size_t count,std::vector<int>& expected,bool loaded,std::vector<std::string>& samples,std::ostream* corpus){
    std::mt19937_64 rng(seed);
    std::size_t index=0;
    auto check=[&](const forge::Board& b,const forge::nnue::Accumulator& a,const std::string& start,const std::string& moves){
        if(index>=count)return;
        const int incremental=forge::nnue::evaluate(b,a), full=full_value(b);
        ++total.incremental;
        if(incremental!=full)fail("incremental_full",b,start,moves,index,full,incremental);
        if(loaded){++total.loaded;if(expected[index]!=full)fail("builtin_file",b,start,moves,index,expected[index],full);}
        else {expected.push_back(full);++total.positions;if(samples.size()<128 && index%997==0)samples.push_back(b.fen());if(corpus && index%257==0)*corpus<<b.fen()<<'\n';}
        ++index;
    };
    const std::vector<std::string> special={
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1","4k3/8/8/8/3Pp3/8/8/4K3 b - d3 0 1",
        "1r2k3/P7/8/8/8/8/7p/4K3 w - - 0 1","4k3/7P/8/8/8/8/p7/1R2K3 b - - 0 1"};
    auto moved=[&](forge::Board& b,forge::nnue::Accumulator& a,forge::Move m,const std::string& start,std::string& history){
        const auto dirty=forge::nnue::dirty_pieces(b,m);forge::nnue::Accumulator next;
        forge::nnue::update(a,next,dirty);forge::Undo undo;
        if(!b.make_move(m,undo))throw std::runtime_error("legal move rejected");
        history+=" "+forge::Board::move_to_uci(m);a=next;
        if(!loaded){if(m.is_castle())++total.castles;if(m.flags&forge::EnPassant)++total.ep;if(m.is_promotion())++total.promotions;if(m.is_capture())++total.captures;}
        check(b,a,start,history);
    };
    for(const auto& fen:special){forge::Board root;if(!root.set_fen(fen))throw std::runtime_error("fixture FEN rejected");const auto legal=root.legal_moves();
        for(const auto m:legal){if(index>=count)break;forge::Board b=root;forge::nnue::Accumulator a;forge::nnue::refresh(b,a);std::string history;moved(b,a,m,fen,history);}}
    while(index<count){
        forge::Board b;const std::string start(forge::Board::StandardStartFen);if(!b.set_fen(start))throw std::runtime_error("startpos rejected");
        forge::nnue::Accumulator a;forge::nnue::refresh(b,a);std::string history;
        for(int ply=0;ply<300 && index<count;++ply){
            const auto legal=b.legal_moves();if(legal.empty()||b.is_repetition()||b.halfmove_clock()>=100)break;
            if(ply%17==0 && !b.in_check()){
                forge::NullUndo undo;b.make_null_move(undo);
                if(!loaded)++total.nulls;check(b,a,start,history+" null");b.unmake_null_move(undo);
                if(index>=count)break;
            }
            moved(b,a,legal[static_cast<std::size_t>(rng()%legal.size())],start,history);
        }
    }
}
static std::vector<unsigned char> read(const std::string& path){std::ifstream in(path,std::ios::binary);if(!in)throw std::runtime_error("cannot open net");return {std::istreambuf_iterator<char>(in),std::istreambuf_iterator<char>()};}
static void damaged(const std::string& net,const std::vector<std::string>& samples){
    const auto original=read(net);if(original.size()<20)throw std::runtime_error("short valid net");
    std::vector<int> before;for(const auto& fen:samples){forge::Board b;if(!b.set_fen(fen))throw std::runtime_error("sample FEN");before.push_back(full_value(b));}
    for(int kind=0;kind<4;++kind){auto bytes=original;
        if(kind==0)bytes[0]^=1;if(kind==1)bytes[8]=2;if(kind==2){bytes[12]=128;bytes[13]=0;}if(kind==3)bytes.pop_back();
        const std::string path=net+".soak-bad-"+std::to_string(kind);{std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<const char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));}
        std::string error;const bool accepted=forge::nnue::load_file(path,error);++total.damaged;
        if(accepted){forge::Board b;fail("damaged_accepted",b,"startpos","",kind,0,1);}
        for(std::size_t i=0;i<samples.size();++i){forge::Board b;if(!b.set_fen(samples[i]))throw std::runtime_error("sample FEN");const int got=full_value(b);if(got!=before[i])fail("damaged_changed_old_net",b,samples[i],"",kind,before[i],got);}
    }
}
int main(int argc,char** argv){
    std::string net,corpus_path;std::size_t count=100000;int seconds=240;std::uint64_t chunks=1000000,first=0;
    for(int i=1;i<argc;++i){if(i+1>=argc)return 2;const std::string a=argv[i],v=argv[++i];
        if(a=="--seed")batch_seed=std::stoull(v);else if(a=="--chunk")count=std::stoull(v);else if(a=="--seconds")seconds=std::stoi(v);
        else if(a=="--net")net=v;else if(a=="--chunks")chunks=std::stoull(v);else if(a=="--first-chunk")first=std::stoull(v);else if(a=="--corpus")corpus_path=v;else return 2;}
    if(net.empty())return 2;std::ofstream corpus;if(!corpus_path.empty())corpus.open(corpus_path,std::ios::app);
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(seconds);std::uint64_t completed=0;
    try {for(chunk_id=first;chunk_id<first+chunks && std::chrono::steady_clock::now()<deadline;++chunk_id){
        std::vector<int> expected;expected.reserve(count);std::vector<std::string> samples;std::string error;
        if(!forge::nnue::load_file("",error))throw std::runtime_error(error);
        walk(batch_seed+chunk_id*0x9e3779b97f4a7c15ULL,count,expected,false,samples,corpus?&corpus:nullptr);
        if(!forge::nnue::load_file(net,error))throw std::runtime_error(error);
        walk(batch_seed+chunk_id*0x9e3779b97f4a7c15ULL,count,expected,true,samples,nullptr);
        damaged(net,samples);++completed;
        std::cout<<"PROGRESS chunks="<<completed<<" positions="<<total.positions<<" faults="<<total.faults<<std::endl;
    }}catch(const std::exception& e){std::cout<<"EXCEPTION "<<e.what()<<std::endl;if(!total.faults)++total.faults;}
    std::cout<<"SUMMARY {\"seed\":"<<batch_seed<<",\"positions\":"<<total.positions<<",\"incremental_checks\":"<<total.incremental
        <<",\"loaded_checks\":"<<total.loaded<<",\"nulls\":"<<total.nulls<<",\"castles\":"<<total.castles<<",\"en_passant\":"<<total.ep
        <<",\"promotions\":"<<total.promotions<<",\"captures\":"<<total.captures<<",\"damaged_file_checks\":"<<total.damaged
        <<",\"chunks\":"<<completed<<",\"faults\":"<<total.faults<<"}"<<std::endl;
    return total.faults?1:0;
}
