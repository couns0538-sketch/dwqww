// Original Forge data transport adapter, 2026-10-30.
// IDEA_SOURCE: user-requested full-FEN roundtrip; MIT binpack format API at
// official-stockfish/nnue-pytorch ec2ead9feeb5677b828536fc53000d1379a1d207.
// No engine search/evaluation code is changed. Dependencies remain external.
#include "binpack.h"
#include <filesystem>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <fcntl.h>
#include <bit>
#include <sys/stat.h>
#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif

namespace fs=std::filesystem;
static std::string trim(const std::string& s) {
    const auto a=s.find_first_not_of(" \t\r\n");
    if(a==std::string::npos) return {};
    return s.substr(a,s.find_last_not_of(" \t\r\n")-a+1);
}
static std::vector<std::string> fields(const std::string& s) {
    std::vector<std::string> v; size_t start=0;
    for(;;) { auto end=s.find('|',start);v.push_back(trim(s.substr(start,end-start))); if(end==std::string::npos) break;start=end+1; }
    return v;
}
static long integer(const std::string& s, long lo, long hi) {
    size_t n=0; long x=std::stol(s,&n);
    if(n!=s.size()||x<lo||x>hi) throw std::runtime_error("integer outside declared range");
    return x;
}
static void reserve(const std::string& p) {
#ifdef _WIN32
    int fd=_open(p.c_str(),_O_WRONLY|_O_CREAT|_O_EXCL|_O_BINARY,_S_IREAD|_S_IWRITE);
    if(fd<0) throw std::runtime_error("output must be new: "+p);
    _close(fd);
#else
    int fd=open(p.c_str(),O_WRONLY|O_CREAT|O_EXCL,0644);
    if(fd<0) throw std::runtime_error("output must be new: "+p);
    close(fd);
#endif
}
static std::string normalized_fen(const std::string& f) {
    std::istringstream is(f);std::vector<std::string> v;std::string x;
    while(is>>x)v.push_back(x);
    if(v.size()!=6)throw std::runtime_error("need all six FEN fields");
    integer(v[4],0,255);long full=integer(v[5],1,8192);
    if(2*full-(v[1]=="w")>16383)throw std::runtime_error("binpack ply exceeds14bits");
    std::ostringstream os;for(size_t i=0;i<v.size();++i)os<<(i?" ":"")<<v[i];return os.str();
}
static binpack::TrainingDataEntry parse(const std::string& line,bool allow,bool& fallback) {
    auto p=fields(line);if(p.size()!=3&&p.size()!=4)throw std::runtime_error("need FEN|STM score|White result[|legal UCI move]");
    const auto fen=normalized_fen(p[0]);
    auto opt=chess::Position::tryFromFen(fen);if(!opt)throw std::runtime_error("invalid FEN");
    auto pos=*opt;
    std::istringstream fs(fen);std::string board,stm,rights,ep;fs>>board>>stm>>rights>>ep;
    auto epsq=chess::parser_bits::tryParseEpSquare(ep);
    if(!epsq)throw std::runtime_error("invalid EP field");
    pos.setEpSquareUnchecked(*epsq); // preserve even an inert original target
    if(pos.fen()!=fen)throw std::runtime_error("FEN normalisation would lose fields");
    int white;
    if(p[2]=="1"||p[2]=="1.0")white=1;
    else if(p[2]=="0.5")white=0;
    else if(p[2]=="0"||p[2]=="0.0")white=-1;
    else throw std::runtime_error("White result must be0/0.5/1");
    chess::Move mv{};
    fallback=p.size()==3;
    if(fallback) {
        if(!allow)throw std::runtime_error("missing legal move; --allow-transport-move is explicitly required");
        bool found=false;
        chess::movegen::forEachLegalMove(pos,[&](chess::Move candidate){if(!found){mv=candidate;found=true;}});
        if(!found)throw std::runtime_error("terminal FEN cannot supply a legal transport move");
    } else {
        const auto& u=p[3];
        if((u.size()!=4&&u.size()!=5)||u[0]<'a'||u[0]>'h'||u[2]<'a'||u[2]>'h'||u[1]<'1'||u[1]>'8'||u[3]<'1'||u[3]>'8'||(u.size()==5&&std::string("nbrq").find(u[4])==std::string::npos))throw std::runtime_error("invalid UCI move");
        mv=chess::uci::uciToMove(pos,u);
        if(!pos.isMoveLegal(mv))throw std::runtime_error("illegal supplied move");
    }
    binpack::TrainingDataEntry e{pos,mv,static_cast<std::int16_t>(integer(p[1],-32767,32767)),pos.ply(),static_cast<std::int16_t>(stm=="b"?-white:white)};
    auto r=binpack::unpackEntry(binpack::packEntry(e));
    if(r.pos.fen()!=fen||r.score!=e.score||r.result!=e.result||r.move!=e.move)throw std::runtime_error("binpack representation does not roundtrip exactly");
    return e;
}
static void flush(std::ofstream& out,std::vector<unsigned char>& b) {
    if(b.empty())return;
    const uint32_t n=static_cast<uint32_t>(b.size());
    const unsigned char h[8]={'B','I','N','P',static_cast<unsigned char>(n),static_cast<unsigned char>(n>>8),static_cast<unsigned char>(n>>16),static_cast<unsigned char>(n>>24)};
    out.write(reinterpret_cast<const char*>(h),8);out.write(reinterpret_cast<const char*>(b.data()),b.size());out.flush();
    if(!out)throw std::runtime_error("output write failed; unsealed partial retained");
    b.clear();
}
static void preflight(const std::string& p) {
    std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("cannot open binpack");
    const uint64_t total=fs::file_size(p);uint64_t off=0;
    while(off<total){unsigned char h[8];f.read(reinterpret_cast<char*>(h),8);if(f.gcount()!=8||std::string(reinterpret_cast<char*>(h),4)!="BINP")throw std::runtime_error("bad chunk header");
      const uint32_t n=uint32_t(h[4])|(uint32_t(h[5])<<8)|(uint32_t(h[6])<<16)|(uint32_t(h[7])<<24);
      if(n==0||n>1048576||n%34||uint64_t(n)>total-off-8)throw std::runtime_error("invalid independent-record chunk");
      std::vector<unsigned char>b(n);f.read(reinterpret_cast<char*>(b.data()),n);if(!f)throw std::runtime_error("truncated chunk");
      for(size_t k=0;k<n;k+=34){
        const auto* r=b.data()+k;
        if(r[32]||r[33])throw std::runtime_error("adapter decoder accepts independent records only");
        uint64_t occ=0;for(int j=0;j<8;++j)occ=(occ<<8)|r[j];
        if(std::popcount(occ)<2||std::popcount(occ)>32)throw std::runtime_error("invalid occupied count");
        int wk=0,bk=0,eps=0,idx=0;
        while(occ){int sq=std::countr_zero(occ);occ&=occ-1;int pc=(r[8+idx/2]>>(4*(idx%2)))&15;++idx;
          wk+=(pc==10);bk+=(pc==11||pc==15);
          if(pc==12){++eps;if(sq/8!=3&&sq/8!=4)throw std::runtime_error("invalid EP pawn rank");}
          if(pc==13&&sq!=0&&sq!=7)throw std::runtime_error("invalid castling rook");
          if(pc==14&&sq!=56&&sq!=63)throw std::runtime_error("invalid castling rook");
        }
        if(wk!=1||bk!=1||eps>1)throw std::runtime_error("invalid king/EP count");
        unsigned pr=(unsigned(r[28])<<8)|r[29];
        if((pr>>14)>2||(pr&16383)==0||r[30])throw std::runtime_error("invalid result/ply/clock");
      }
      off+=8+n;
    }
}
int main(int argc,char**argv){
 try{
  if(argc<3)throw std::runtime_error("usage: adapter encode input.txt NEW.binpack [--allow-transport-move] | decode input.binpack");
  const std::string mode=argv[1];uint64_t count=0,fallbacks=0;
  if(mode=="encode"){
   if(argc<4||argc>5)throw std::runtime_error("encode arguments");
   bool allow=argc==5&&std::string(argv[4])=="--allow-transport-move";if(argc==5&&!allow)throw std::runtime_error("unknown argument");
   std::ifstream input;std::istream* in=&std::cin;if(std::string(argv[2])!="-"){input.open(argv[2]);if(!input)throw std::runtime_error("cannot open input");in=&input;}
   reserve(argv[3]);std::ofstream out(argv[3],std::ios::binary|std::ios::trunc);if(!out)throw std::runtime_error("cannot open reserved output");
   std::vector<unsigned char>b;b.reserve(1048576);std::string line;
   while(std::getline(*in,line)){try{bool fb=false;const auto e=parse(line,allow,fb);const auto p=binpack::packEntry(e);if(b.size()+34>1048576)flush(out,b);b.insert(b.end(),p.bytes,p.bytes+32);b.push_back(0);b.push_back(0);++count;fallbacks+=fb;}catch(const std::exception&ex){throw std::runtime_error("row "+std::to_string(count)+": "+ex.what());}}
   if(in->bad())throw std::runtime_error("input read error");
   flush(out,b);
  }else if(mode=="decode"){
   if(argc!=3)throw std::runtime_error("decode arguments");
   preflight(argv[2]);
   binpack::CompressedTrainingDataEntryReader in(argv[2],std::ios::binary);
   while(in.hasNext()){auto e=in.next();if(!e.isValid())throw std::runtime_error("decoded illegal move");int white=e.pos.sideToMove()==chess::Color::Black?-e.result:e.result;if(white<-1||white>1)throw std::runtime_error("bad decoded result");
    std::cout<<e.pos.fen()<<" | "<<e.score<<" | "<<(white==1?"1.0":white==0?"0.5":"0.0")<<'\n';++count;
   }if(!std::cout)throw std::runtime_error("decoded output write error");
  }else throw std::runtime_error("unknown mode");
  std::cerr<<"{\"rows\":"<<count<<",\"transport_move_fallbacks\":"<<fallbacks<<",\"status\":\"PASS\"}\n";return 0;
 }catch(const std::exception&ex){std::cerr<<"ERROR: "<<ex.what()<<'\n';return 1;}
}
