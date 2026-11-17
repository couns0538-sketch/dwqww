#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>
static std::uint64_t fnv(const std::uint8_t* d, std::size_t n) {
    std::uint64_t h = 14695981039346656037ULL;
    for (std::size_t i = 0; i < n; ++i) { h ^= d[i]; h *= 1099511628211ULL; }
    return h;
}
static void put_u32(std::vector<std::uint8_t>& o, std::uint32_t v){for(int i=0;i<4;++i)o.push_back((std::uint8_t)((v>>(8*i))&0xFFU));}
static void put_i16(std::vector<std::uint8_t>& o, std::int16_t v){auto u=(std::uint16_t)v;o.push_back((std::uint8_t)(u&0xFFU));o.push_back((std::uint8_t)((u>>8U)&0xFFU));}
int main(int argc,char**argv){
    unsigned lo = argc>1?(unsigned)std::atoi(argv[1]):0;
    unsigned hi = argc>2?(unsigned)std::atoi(argv[2]):2000;
    const int hidden=512,kb=8,ob=8; const std::size_t h=hidden;
    for (unsigned seed=lo; seed<=hi; ++seed) {
        std::vector<std::uint8_t> o; o.reserve(6400000);
        const char m[8]={'F','O','R','G','E','N','N','3'}; o.insert(o.end(),m,m+8);
        put_u32(o,3); put_u32(o,192); put_u32(o,768); put_u32(o,hidden); put_u32(o,kb); put_u32(o,ob);
        put_u32(o,0); put_u32(o,255); put_u32(o,64); put_u32(o,400);
        for(int sq=0;sq<64;++sq) o.push_back((std::uint8_t)((sq>>3)*kb/8));
        for(int p=0;p<=32;++p) o.push_back((std::uint8_t)std::min(ob-1,std::max(p-2,0)*ob/32));
        while(o.size()<192) o.push_back(0);
        std::mt19937 rng(seed);
        std::uniform_int_distribution<int> dw1(-40,40),db1(-200,200),dw2(-127,127),db2(-5000,5000);
        for(std::size_t i=0;i<(std::size_t)kb*768*h;++i) put_i16(o,(std::int16_t)dw1(rng));
        for(std::size_t i=0;i<h;++i) put_i16(o,(std::int16_t)db1(rng));
        for(std::size_t i=0;i<(std::size_t)ob*2*h;++i) put_i16(o,(std::int16_t)dw2(rng));
        for(int i=0;i<ob;++i) put_u32(o,(std::uint32_t)db2(rng));
        std::uint64_t payload=fnv(o.data(),o.size());
        for(int i=0;i<8;++i) o.push_back((std::uint8_t)((payload>>(8*i))&0xFFU));
        std::uint64_t whole=fnv(o.data(),o.size());
        char p[32],w[32]; std::snprintf(p,32,"%016llx",(unsigned long long)payload); std::snprintf(w,32,"%016llx",(unsigned long long)whole);
        if (std::strcmp(p,"fdff70de72e4ca82")==0) { std::printf("MATCH payload seed %u\n",seed); return 0; }
        if (std::strcmp(w,"fdff70de72e4ca82")==0) { std::printf("MATCH whole-file seed %u\n",seed); return 0; }
    }
    std::printf("NO MATCH payload-or-whole in [%u,%u]\n",lo,hi);
    return 1;
}
