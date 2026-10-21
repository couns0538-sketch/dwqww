#include "forge/search.hpp"
#include <cstdint>
#include <iostream>
#include <stdexcept>
using namespace forge;
int main(){int checks=0;auto require=[&](bool c,const char* n){++checks;if(!c)throw std::runtime_error(n);};
 TranspositionTable t(1);auto put=[&](std::uint64_t key,int depth,int score){auto p=t.probe(key);t.store(p,key,score,0,Move::none(),depth,BoundUpper,false,0);};
 // Actual GCC multiply-high implementation: small distinct keys all select cluster0.
 put(1,12,101);t.new_search();put(2,8,102);put(3,8,103);put(4,8,104);
 auto before=t.probe(1);require(before.hit,"old A hit");require(before.entry.generation()!=t.generation(),"A remains old after hit");require(before.entry.depth==12,"A deep bound intact");
 auto hit_again=t.probe(1);require(hit_again.entry.generation()==before.entry.generation(),"repeated hit does not refresh generation");
 const int full_before=t.hashfull();auto victim=t.probe(5);require(!victim.hit,"fifth key misses");require(victim.entry.key32==1,"old recently-hit A selected on age-adjusted tie");
 std::cout<<"TT_FIXTURE old_hit_generation="<<int(before.entry.generation())<<" current="<<int(t.generation())<<" victim_tag="<<victim.entry.key32<<" hashfull_before="<<full_before<<'\n';
 auto a=t.probe(1);t.store(a,1,202,0,Move::none(),1,BoundUpper,false,0);auto after=t.probe(1);
 require(after.entry.depth==1&&after.entry.score==202,"age alone admits shallow same-key overwrite");require(after.entry.generation()==t.generation(),"store refreshes generation");
 require(t.hashfull()>full_before,"store generation refresh changes hashfull");
 std::cout<<"TT_COUPLING shallow_depth="<<int(after.entry.depth)<<" hashfull_after="<<t.hashfull()<<'\n';
 std::cout<<"TT fixture: checks "<<checks<<" failures 0\n";
}
