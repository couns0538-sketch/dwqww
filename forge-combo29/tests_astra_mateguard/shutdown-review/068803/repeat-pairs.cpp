#include "uci_process.hpp"
#include <fstream>
#include <iostream>
#include <memory>
std::string quoted(const std::string& s) {std::string out="\"";for(unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=c;}else if(c=='\n')out+="\\n";else if(c=='\r')out+="\\r";else if(c=='\t')out+="\\t";else if(c<32)out+='?';else out+=c;}return out+'"';}
int main(int argc,char**argv){
 if(argc!=4)return 2;const std::string directory=argv[1],fen="8/8/8/3pkp2/4p2p/b2P4/2Q2K2/1N4r1 w - - 2 69";
 for(int repetition=1;repetition<=10;repetition++)for(int engine=0;engine<2;engine++){
  const std::string side=engine==0?"candidate":"reference",name="pair-"+std::to_string(repetition)+"-"+side;
  std::unique_ptr<UciProcess> process;std::string error;UciResult result;UciShutdownResult shutdown;bool searched=false;
  try {process=std::make_unique<UciProcess>(argv[engine+2],1,10000);result=process->search(fen,9,10000,true);searched=true;shutdown=process->finish(250);}
  catch(const std::exception& e){error=e.what();if(process)shutdown=process->finish(250);}
  std::ofstream trace(directory+"/"+name+".transcript.txt");if(process)trace<<process->transcript();else trace<<error;trace.close();
  std::cout<<"{\"repetition\":"<<repetition<<",\"engine\":"<<quoted(side)<<",\"binary\":"<<quoted(argv[engine+2])<<",\"fen\":"<<quoted(fen)<<",\"searched\":"<<(searched?"true":"false")<<",\"error\":"<<quoted(error)<<",\"depth\":"<<result.depth<<",\"bestmove\":"<<quoted(result.move)<<",\"score_kind\":"<<quoted(result.score_kind)<<",\"score\":"<<result.score<<",\"bound\":"<<quoted(result.score_bound)<<",\"nodes\":"<<result.nodes<<",\"shutdown\":{\"reaped\":"<<(shutdown.reaped?"true":"false")<<",\"exit_code\":"<<shutdown.exit_code<<",\"signal\":"<<shutdown.signal<<",\"timed_out\":"<<(shutdown.timed_out?"true":"false")<<",\"driver_sigterm\":"<<(shutdown.driver_sigterm?"true":"false")<<",\"driver_sigkill\":"<<(shutdown.driver_sigkill?"true":"false")<<",\"error\":"<<quoted(shutdown.error)<<"},\"transcript\":"<<quoted(directory+"/"+name+".transcript.txt")<<"}"<<std::endl;
 }
}
