#include "uci_process.hpp"
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
#include <iomanip>

using Steady = std::chrono::steady_clock;
std::string json(const std::string& s) { std::string out="\""; for(unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=c;}else if(c=='\n')out+="\\n";else if(c=='\r')out+="\\r";else if(c=='\t')out+="\\t";else if(c<32){char b[7];snprintf(b,sizeof(b),"\\u%04x",c);out+=b;}else out+=c;}return out+'"'; }
double milliseconds(Steady::time_point from){return std::chrono::duration<double,std::milli>(Steady::now()-from).count();}
int main(int argc,char**argv){
 if(argc!=5){std::cerr<<"usage: clock-manual BINARY COMMAND_FILE OUTPUT_DIR MODE\n";return 2;}
 const std::string binary=argv[1],input=argv[2],dir=argv[3],mode=argv[4];const auto epoch=Steady::now();
 std::ofstream stdoutBytes(dir+"/engine.stdout.txt",std::ios::binary),stderrBytes(dir+"/engine.stderr.txt",std::ios::binary),stdinBytes(dir+"/engine.stdin.txt",std::ios::binary),events(dir+"/events.jsonl.txt",std::ios::binary);
 if(!stdoutBytes||!stderrBytes||!stdinBytes||!events)return 2;
 auto observer=[&](const std::string& stream,const std::string& bytes){auto& out=stream=="stdout"?stdoutBytes:stream=="stderr"?stderrBytes:stdinBytes;out.write(bytes.data(),static_cast<std::streamsize>(bytes.size()));out.flush();events<<"{\"monotonic_ms\":"<<std::fixed<<std::setprecision(6)<<milliseconds(epoch)<<",\"stream\":"<<json(stream)<<",\"bytes\":"<<json(bytes)<<"}\n";events.flush();};
 std::unique_ptr<UciProcess> engine;UciShutdownResult shutdown;std::string error;int cases=0,hugeCases=0,earlyHuge=0;bool protocolFailure=false;
 try{
  engine=std::make_unique<UciProcess>(binary,1,10000,observer);
  engine->send("setoption name Move Overhead value 10",2000);engine->ready(2000);
  std::ifstream file(input);if(!file)throw std::runtime_error("command file unavailable");std::string command;
  while(std::getline(file,command)){
   if(!command.empty()&&command.back()=='\r')command.pop_back();
   if(command.empty()||command[0]=='#')continue;
   if(command.rfind("position ",0)==0){engine->send(command,2000);continue;}
   if(command.rfind("go ",0)!=0)throw std::runtime_error("unexpected manual command: "+command);
   const bool huge=command.find("3000000000")!=std::string::npos;const auto before=Steady::now();engine->send(command,2000);const auto sent=Steady::now();
   std::string best;double bestMs=-1,stopMs=-1;bool bestBeforeStop=false;int reportedTime=-1,depth=-1;unsigned long long nodes=0;
   auto consume=[&](const std::string& line){std::istringstream in(line);std::string token;in>>token;if(token=="bestmove"){if(!best.empty())throw std::runtime_error("multiple bestmoves for one go");if(!(in>>best))throw std::runtime_error("bestmove missing move");bestMs=milliseconds(sent);return;}if(token=="info"){while(in>>token){if(token=="string"||token=="pv")break;if(token=="time")in>>reportedTime;else if(token=="depth")in>>depth;else if(token=="nodes")in>>nodes;}}};
   if(huge){
    ++hugeCases;const auto checkpoint=sent+std::chrono::milliseconds(150);
    while(Steady::now()<checkpoint){const auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(checkpoint-Steady::now()).count();const int left=static_cast<int>(std::max<long long>(1,(ns+999999)/1000000));auto line=engine->observe_line_for(left);if(line)consume(*line);}
    bestBeforeStop=!best.empty();if(bestBeforeStop)++earlyHuge;stopMs=milliseconds(sent);engine->send("stop",2000);
   }
   const auto responseDeadline=Steady::now()+std::chrono::seconds(5);
   while(best.empty()&&Steady::now()<responseDeadline){const auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(responseDeadline-Steady::now()).count();auto line=engine->observe_line_for(static_cast<int>(std::max<long long>(1,(ns+999999)/1000000)));if(line)consume(*line);}
   if(best.empty())throw std::runtime_error("No bestmove within the operational response bound: "+command);
   ++cases;
   std::cout<<"CASE {\"index\":"<<cases<<",\"mode\":"<<json(mode)<<",\"go\":"<<json(command)<<",\"goWriteDurationMs\":"<<std::chrono::duration<double,std::milli>(sent-before).count()<<",\"hugeClock\":"<<(huge?"true":"false")<<",\"stopElapsedMs\":"<<stopMs<<",\"bestmoveBeforeStop\":"<<(bestBeforeStop?"true":"false")<<",\"noBestmoveObservedAt150ms\":"<<(huge?(!bestBeforeStop?"true":"false"):"null")<<",\"bestmove\":"<<json(best)<<",\"bestmoveElapsedMs\":"<<bestMs<<",\"lastReportedTimeMs\":"<<reportedTime<<",\"lastReportedDepth\":"<<depth<<",\"lastReportedNodes\":"<<nodes<<",\"timingToleranceAssertion\":false}"<<std::endl;
   engine->ready(2000);
  }
  if(cases!=7||hugeCases!=2)throw std::runtime_error("manual case count mismatch");
  shutdown=engine->finish(3000);
 }catch(const UciStartupError& e){error=e.what();shutdown=e.shutdown;protocolFailure=true;}
 catch(const std::exception& e){error=e.what();protocolFailure=true;if(engine)shutdown=engine->finish(3000);}
 std::ofstream trace(dir+"/transport.transcript.txt",std::ios::binary);trace<<(engine?engine->transcript():error);trace.close();
 const bool operational=shutdown.reaped&&shutdown.exit_code==0&&shutdown.signal==0&&!shutdown.timed_out&&!shutdown.driver_sigterm&&!shutdown.driver_sigkill&&shutdown.error.empty()&&!protocolFailure;
 std::cout<<"SUMMARY {\"mode\":"<<json(mode)<<",\"completedCases\":"<<cases<<",\"requestedCases\":7,\"hugeClockCases\":"<<hugeCases<<",\"hugeClockEarlyBestmoves\":"<<earlyHuge<<",\"operationalComplete\":"<<(operational?"true":"false")<<",\"error\":"<<json(error)<<",\"shutdown\":{\"reaped\":"<<(shutdown.reaped?"true":"false")<<",\"exit_code\":"<<shutdown.exit_code<<",\"signal\":"<<shutdown.signal<<",\"timed_out\":"<<(shutdown.timed_out?"true":"false")<<",\"driver_sigterm\":"<<(shutdown.driver_sigterm?"true":"false")<<",\"driver_sigkill\":"<<(shutdown.driver_sigkill?"true":"false")<<",\"error\":"<<json(shutdown.error)<<"}}"<<std::endl;
 return !operational?2:earlyHuge?1:0;
}
