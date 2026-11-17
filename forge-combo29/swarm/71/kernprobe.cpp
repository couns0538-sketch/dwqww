#include "forge/nnue_v3.hpp"
#include <cstdio>
#include <fstream>
#include <string>
using namespace forge::nnue::v3;
int main(int argc,char**argv){
    std::string err; if(!load(argv[1],&err)){std::printf("load fail %s\n",err.c_str());return 1;}
    const Net& net=*loaded();
    std::ifstream in(argv[2]); std::string line; forge::Board b; int n=0,bad=0;
    while(std::getline(in,line)){ if(line.empty())continue; if(!b.set_fen(line))continue;
        auto acc=std::make_unique<Accumulator>(); refresh(net,b,*acc);
        const auto us=b.side_to_move(); const int bucket=output_bucket(net,b);
        const std::int16_t* o=acc->values[(size_t)us].data(); const std::int16_t* t=acc->values[(size_t)forge::opposite(us)].data();
        const long long s=output_sum_with(Kernel::Scalar,net,o,t,bucket);
        long long a2=s, a5=s;
        if(kernel_available(Kernel::Avx2)) a2=output_sum_with(Kernel::Avx2,net,o,t,bucket);
        if(kernel_available(Kernel::Avx512)) a5=output_sum_with(Kernel::Avx512,net,o,t,bucket);
        ++n; if(s!=a2||s!=a5){++bad; std::printf("KDIFF %s scalar %lld avx2 %lld avx512 %lld\n",line.c_str(),s,a2,a5);} }
    std::printf("KERNEL compared %d differing %d best %s\n",n,bad,kernel_name());
    return bad?3:0;
}
