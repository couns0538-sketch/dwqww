// IDEA_SOURCE: Owner A2; independent review of Forge's production comparator.
#include "forge/search.hpp"
#include "forge/syzygy.hpp"
#include <iostream>
#include <string>
using namespace forge;
int main(int argc,char**argv) {
 bool on=argc>1 && std::string(argv[1])=="on";
#ifdef CANDIDATE
 options::smp_protect_proven_score=on;
#else
 if(on) return 2;
#endif
 const int scores[]={-32000,-31872,-31871,-31743,-31742,-100,0,100,31742,31743,31867,31871,31872,31999,32000};
 const int depths[]={1,5,12,32};
 int tested=0, mate_violations=0,protected_violations=0;
 for(bool tables:{false,true}) {
  syzygy::tb_scores=tables;
  for(int best_score:scores)for(int candidate_score:scores)for(int best_depth:depths)for(int candidate_depth:depths){
   SearchInfo b,c;b.score=best_score;b.depth=best_depth;c.score=candidate_score;c.depth=candidate_depth;
   bool better=better_thread_result(c,b);
   std::cout << int(better); ++tested;
   if(best_score>=MateInMaxPly && candidate_score<best_score && better) ++mate_violations;
   if(on && tables && best_score>=syzygy::TbWinInMaxPly && candidate_score<best_score && better) ++protected_violations;
  }
 }
 std::cout<<"\ncases="<<tested<<" mate_protection_violations="<<mate_violations<<" tb_protection_violations="<<protected_violations<<"\n";
 return mate_violations||protected_violations;
}
