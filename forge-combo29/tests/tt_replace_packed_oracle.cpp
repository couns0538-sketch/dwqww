#include <algorithm>
#include <iostream>
int main(){unsigned count=0;for(int i=0;i<4;++i)for(int j=i+1;j<4;++j)for(int a=-124;a<=255;++a)for(int b=-124;b<=255;++b){int p=std::min(a*4+i,b*4+j);unsigned got=unsigned(p)&3U;unsigned want=b<a?j:i;if(got!=want)return 1;++count;}std::cout<<"PASS exhaustive "<<count<<" ordered slot/score pairs; min associativity extends to all four slots\n";}
