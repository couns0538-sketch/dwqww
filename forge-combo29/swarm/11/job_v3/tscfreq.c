#include <stdio.h>
#include <time.h>
#include <stdint.h>
static inline uint64_t rdtsc(void){unsigned lo,hi;__asm__ __volatile__("rdtsc":"=a"(lo),"=d"(hi));return ((uint64_t)hi<<32)|lo;}
int main(void){
  struct timespec a,b; clock_gettime(CLOCK_MONOTONIC,&a);
  uint64_t t0=rdtsc();
  struct timespec s={0, 200*1000*1000}; nanosleep(&s,0);
  uint64_t t1=rdtsc(); clock_gettime(CLOCK_MONOTONIC,&b);
  double sec=(b.tv_sec-a.tv_sec)+(b.tv_nsec-a.tv_nsec)/1e9;
  printf("TSC %.6f GHz over %.3f s (%llu cycles)\n",(double)(t1-t0)/sec/1e9,sec,(unsigned long long)(t1-t0));
  return 0;
}
