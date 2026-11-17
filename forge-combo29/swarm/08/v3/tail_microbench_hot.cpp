
#include <immintrin.h>
#include <chrono>
#include <cstdio>
#include <cstdint>
#include <cstdlib>

__attribute__((noinline)) std::int64_t tail_scalar(__m512i s0, __m512i s1) {
    alignas(64) std::int32_t lanes[32];
    _mm512_store_si512(reinterpret_cast<__m512i*>(lanes), s0);
    _mm512_store_si512(reinterpret_cast<__m512i*>(lanes + 16), s1);
    std::int64_t sum = 0;
    for (const std::int32_t lane : lanes) sum += lane;
    return sum;
}
__attribute__((noinline)) std::int64_t tail_fold(__m512i s0, __m512i s1) {
    const __m512i t = _mm512_add_epi32(s0, s1);
    __m256i v = _mm256_add_epi32(_mm512_castsi512_si256(t), _mm512_extracti64x4_epi64(t, 1));
    v = _mm256_add_epi32(v, _mm256_permute2x128_si256(v, v, 0x01));
    v = _mm256_add_epi32(v, _mm256_shuffle_epi32(v, _MM_SHUFFLE(1,0,3,2)));
    v = _mm256_add_epi32(v, _mm256_shuffle_epi32(v, _MM_SHUFFLE(2,3,0,1)));
    return static_cast<std::int64_t>(_mm256_cvtsi256_si32(v));
}
// HOT: 16-vector working set (1 KB), like a reused accumulator slot
static const int HOT = 16;
int main(){
    const int N=2566881;
    __m512i* hot=(__m512i*)aligned_alloc(64,HOT*64);
    for(int i=0;i<HOT;i++) hot[i]=_mm512_set1_epi32(i);
    __m512i b=_mm512_set1_epi32(5);
    std::int64_t sink=0;
    hot[0]=_mm512_add_epi32(hot[0],b); tail_scalar(hot[0],b); tail_fold(hot[0],b);
    for(int rep=0;rep<3;rep++){
        auto t0=std::chrono::steady_clock::now();
        std::int64_t a=0;
        for(int i=0;i<N;i++) a+=tail_scalar(hot[i&(HOT-1)],b);
        auto t1=std::chrono::steady_clock::now();
        std::int64_t a2=0;
        for(int i=0;i<N;i++) a2+=tail_fold(hot[i&(HOT-1)],b);
        auto t2=std::chrono::steady_clock::now();
        sink+=a+a2;
        if(a!=a2){printf("MISMATCH\n");return 1;}
        double s=std::chrono::duration<double,std::milli>(t1-t0).count();
        double f=std::chrono::duration<double,std::milli>(t2-t1).count();
        printf("rep %d HOT: scalar %.2f ms fold %.2f ms save %+.2f ms = %+.3f%% of 2130  identical=yes\n",
               rep,s,f,s-f,100*(s-f)/2130.0);
    }
    printf("sink %ld\n",(long)sink);
    return 0;
}
