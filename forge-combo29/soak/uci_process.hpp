#pragma once
// POSIX subprocess transport used only by soak tools. No engine source edits.
#include <chrono>
#include <csignal>
#include <poll.h>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

struct UciResult {
    std::string move,score_kind,transcript;
    int score=0,depth=0;
    unsigned long long nodes=0;
    bool same(const UciResult& o)const{return move==o.move&&score_kind==o.score_kind&&score==o.score&&nodes==o.nodes;}
    bool positive_mate()const{return score_kind=="mate"&&score>0;}
};
class UciProcess {
    pid_t child_=-1;int input_=-1,output_=-1;std::string pending_,trace_;
public:
    explicit UciProcess(const std::string& path){
        int a[2],b[2];if(pipe(a)||pipe(b))throw std::runtime_error("pipe failed");child_=fork();
        if(child_<0)throw std::runtime_error("fork failed");
        if(child_==0){dup2(a[0],0);dup2(b[1],1);dup2(b[1],2);close(a[0]);close(a[1]);close(b[0]);close(b[1]);execl(path.c_str(),path.c_str(),static_cast<char*>(nullptr));_exit(127);}
        close(a[0]);close(b[1]);input_=a[1];output_=b[0];
        send("uci");until("uciok");send("setoption name Threads value 1");send("setoption name Hash value 16");send("setoption name OwnBook value false");ready();
    }
    ~UciProcess(){if(child_<0)return;try{send("quit");}catch(...){}close(input_);int status=0;
        for(int i=0;i<50;++i){if(waitpid(child_,&status,WNOHANG)==child_){close(output_);return;}usleep(10000);}
        kill(child_,SIGKILL);waitpid(child_,&status,0);close(output_);
    }
    UciProcess(const UciProcess&)=delete;UciProcess& operator=(const UciProcess&)=delete;
    void send(const std::string& text){trace_+="> "+text+"\n";const auto data=text+"\n";std::size_t done=0;while(done<data.size()){const auto n=write(input_,data.data()+done,data.size()-done);if(n<=0)throw std::runtime_error("engine stdin closed");done+=static_cast<std::size_t>(n);}}
    std::string line(int timeout_ms=30000){
        const auto end=std::chrono::steady_clock::now()+std::chrono::milliseconds(timeout_ms);
        for(;;){const auto pos=pending_.find('\n');if(pos!=std::string::npos){auto result=pending_.substr(0,pos);pending_.erase(0,pos+1);if(!result.empty()&&result.back()=='\r')result.pop_back();trace_+="< "+result+"\n";return result;}
            const auto left=std::chrono::duration_cast<std::chrono::milliseconds>(end-std::chrono::steady_clock::now()).count();if(left<=0)throw std::runtime_error("engine response timeout\n"+trace_);
            pollfd p{output_,POLLIN,0};const auto ok=poll(&p,1,static_cast<int>(left));if(ok<=0)throw std::runtime_error("engine poll timeout\n"+trace_);
            char buf[8192];const auto n=read(output_,buf,sizeof(buf));if(n<=0)throw std::runtime_error("engine disconnected\n"+trace_);pending_.append(buf,static_cast<std::size_t>(n));
        }
    }
    void until(const std::string& word){while(line()!=word){}}
    void ready(){send("isready");until("readyok");}
    void threads(int n){send("setoption name Threads value "+std::to_string(n));ready();}
    UciResult search(const std::string& fen,int depth){
        trace_.clear();send("ucinewgame");ready();send("position fen "+fen);send("go depth "+std::to_string(depth));UciResult r;
        for(;;){const auto text=line();std::istringstream in(text);std::string token;in>>token;
            if(token=="bestmove"){in>>r.move;r.transcript=trace_;if(r.score_kind.empty())throw std::runtime_error("no score info\n"+trace_);return r;}
            if(token!="info")continue;
            while(in>>token){if(token=="depth")in>>r.depth;else if(token=="score")in>>r.score_kind>>r.score;else if(token=="nodes")in>>r.nodes;}
        }
    }
};
