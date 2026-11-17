
#include <immintrin.h>
#include <chrono>
#include <cstdio>
#include <cstdint>
#include <vector>

__attribute__((noinline)) std::int64_t tail_scalar(__m512i sum0, __m512i sum1) {
    alignas(64) std::int32_t lanes[32];
    _mm512_store_si512(reinterpret_cast<__m512i*>(lanes), sum0);
    _mm512_store_si512(reinterpret_cast<__m512i*>(lanes + 16), sum1);
    std::int64_t sum = 0;
    for (const std::int32_t lane : lanes) sum += lane;
    return sum;
}
__attribute__((noinline)) std::int64_t tail_fold(__m512i sum0, __m512i sum1) {
    const __m512i total = _mm512_add_epi32(sum0, sum1);
    __m256i v = _mm256_add_epi32(_mm512_castsi512_si256(total), _mm512_extracti64x4_epi64(total, 1));
    v = _mm256_add_epi32(v, _mm256_permute2x128_si256(v, v, 0x01));
    v = _mm256_add_epi32(v, _mm256_shuffle_epi32(v, _MM_SHUFFLE(1,0,3,2)));
    v = _mm256_add_epi32(v, _mm256_shuffle_epi32(v, _MM_SHUFFLE(2,3,0,1)));
    return static_cast<std::int64_t>(_mm256_cvtsi256_si32(v));
}
int main() {
    const int N = 2566881;
    // Distinct inputs each iteration so nothing can be hoisted or CSE'd, and the
    // value feeds an observable sink.
    std::vector<__m512i> in(N);
    for (int i=0;i<N;i++) in[i]=_mm512_set1_epi32(i);
    __m512i b = _mm512_set1_epi32(5);
    std::int64_t sink=0;
    tail_scalar(in[0],b); tail_fold(in[0],b);
    for (int rep=0;rep<3;rep++){
        auto t0=std::chrono::steady_clock::now();
        std::int64_t acc=0;
        for (int i=0;i<N;i++) acc+=tail_scalar(in[i],b);
        auto t1=std::chrono::steady_clock::now();
        std::int64_t acc2=0;
        for (int i=0;i<N;i++) acc2+=tail_fold(in[i],b);
        auto t2=std::chrono::steady_clock::now();
        sink+=acc+acc2;
        if(acc!=acc2){printf("MISMATCH\n");return 1;}
        double s=std::chrono::duration<double,std::milli>(t1-t0).count();
        double f=std::chrono::duration<double,std::milli>(t2-t1).count();
        printf("rep %d: scalar %.2f ms  fold %.2f ms  save %+.2f ms = %+.3f%% of 2130 ms  identical=%s\n",
               rep,s,f,s-f,100*(s-f)/2130.0,"yes");
    }
    printf("sink %ld\n",(long)sink);
    return 0;
}
