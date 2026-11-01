// Positive controls: both invocations must fail with the expected sanitizer.
#include <climits>
#include <cstdlib>
int main(int argc,char**) {
    if(argc==1) {
        volatile int n=INT_MAX; return n+1;
    }
    int* p=new int[1]; volatile int i=2; p[i]=123; int r=p[i]; delete[] p; return r;
}
