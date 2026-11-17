// Independent classifier: naive 0x88-style move generation written from scratch,
// not sharing code with forge's movegen. Used ONLY to label fixtures.
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <iostream>
struct P { char sq[64]; }; // ' ' empty; P N B R Q K p n b r q k
static int fileOf(int s){return s%8;} static int rankOf(int s){return s/8;} // a1=0
static bool onb(int f,int r){return f>=0&&f<8&&r>=0&&r<8;}
static int idx(int f,int r){return r*8+f;}
static std::string uciOf(int from,int to,char promo=0){
  std::string s;
  s += static_cast<char>('a'+fileOf(from)); s += static_cast<char>('1'+rankOf(from));
  s += static_cast<char>('a'+fileOf(to));   s += static_cast<char>('1'+rankOf(to));
  if (promo) s += promo;
  return s;
}
static bool isWhite(char c){return c>='A'&&c<='Z';}
static bool isBlack(char c){return c>='a'&&c<='z';}
static bool attacks(const P&p,int from,int to,char piece){
  int df=fileOf(to)-fileOf(from), dr=rankOf(to)-rankOf(from);
  auto ad=[&](int a){return a<0?-a:a;};
  switch(tolower(piece)){
    case 'p': return ad(df)==1 && (isWhite(piece)? dr==1 : dr==-1);
    case 'n': return (ad(df)==1&&ad(dr)==2)||(ad(df)==2&&ad(dr)==1);
    case 'k': return ad(df)<=1&&ad(dr)<=1&&!(df==0&&dr==0);
    case 'b': if(ad(df)!=ad(dr)||df==0) return false; break;
    case 'r': if(!((df==0)!=(dr==0))) return false; break;
    case 'q': if(!(ad(df)==ad(dr)||((df==0)!=(dr==0)))) return false; break;
  }
  if(tolower(piece)=='n'||tolower(piece)=='p'||tolower(piece)=='k') return true;
  int sf=df==0?0:(df>0?1:-1), sr=dr==0?0:(dr>0?1:-1);
  int f=fileOf(from)+sf,r=rankOf(from)+sr;
  while(f!=fileOf(to)||r!=rankOf(to)){ if(p.sq[idx(f,r)]!=' ') return false; f+=sf;r+=sr; }
  return true;
}
static int kingSq(const P&p,char k){for(int i=0;i<64;i++) if(p.sq[i]==k) return i; return -1;}
static bool attacked(const P&p,int sq,bool byWhite){
  for(int i=0;i<64;i++){ char c=p.sq[i]; if(c==' ')continue;
    if(byWhite!=isWhite(c)) continue;
    if(tolower(c)=='k' && i==sq) continue;
    if(attacks(p,i,sq,c)) return true; }
  return false;
}
static std::vector<std::string> legalMoves(P p,bool white){
  std::vector<std::string> out;
  for(int i=0;i<64;i++){ char c=p.sq[i]; if(c==' ')continue; if(white!=isWhite(c))continue;
    int df,dr;
    for(df=-7;df<=7;df++)for(dr=-7;dr<=7;dr++){
      if(!df&&!dr)continue;
      int f=fileOf(i)+df,r=rankOf(i)+dr; if(!onb(f,r))continue; int t=idx(f,r);
      char tc=p.sq[t]; if(tc!=' ' && (white==isWhite(tc))) continue;
      char pc=tolower(c); bool ok=false;
      if(pc=='p'){ int dir=white?1:-1;
        if(df==0&&dr==dir&&tc==' '){ if(r==(white?7:0)){ for(char pr: std::string("qrbn")){P q=p;q.sq[i]=' ';q.sq[t]=white?toupper(pr):pr; out.push_back(uciOf(i,t,pr));} ok=false;} else {P q=p;q.sq[i]=' ';q.sq[t]=c; if(!attacked(q,kingSq(q,white?'K':'k'),!white)) out.push_back(uciOf(i,t));} }
        else if(df==0&&dr==2*dir&&tc==' '){
          int mid=idx(fileOf(i), rankOf(i)+dir);
          int startrank = white?1:6;
          if(rankOf(i)==startrank && p.sq[mid]==' '){
            P q=p; q.sq[i]=' '; q.sq[t]=c;
            if(!attacked(q,kingSq(q,white?'K':'k'),!white)) out.push_back(uciOf(i,t));
          }
        }
        else if((df==1||df==-1)&&dr==dir&&tc!=' '){ if(r==(white?7:0)){for(char pr: std::string("qrbn")){P q=p;q.sq[i]=' ';q.sq[t]=white?toupper(pr):pr; if(!attacked(q,kingSq(q,white?'K':'k'),!white)) out.push_back(uciOf(i,t,pr));}} else {P q=p;q.sq[i]=' ';q.sq[t]=c; if(!attacked(q,kingSq(q,white?'K':'k'),!white)) out.push_back(uciOf(i,t));}}
        continue; }
      if(!attacks(p,i,t,c)) continue;
      P q=p; q.sq[i]=' '; q.sq[t]=c;
      if(!attacked(q,kingSq(q,white?'K':'k'),!white)) out.push_back(uciOf(i,t));
    }
  }
  // Castling: king e1/e8 with rook on the corner, squares empty and not attacked.
  {
    int ksq = white ? 4 : 60;
    char k = white ? 'K' : 'k', rk = white ? 'R' : 'r';
    if(p.sq[ksq]==k){
      auto safe=[&](int sq){ return !attacked(p,sq,!white); };
      bool kingSafe = safe(ksq);
      // king side
      if(p.sq[ksq+3]==rk && p.sq[ksq+1]==' ' && p.sq[ksq+2]==' ' &&
         kingSafe && safe(ksq+1) && safe(ksq+2)){
        P q=p; q.sq[ksq]=' '; q.sq[ksq+1]=' '; q.sq[ksq+2]=k; q.sq[ksq+3]=' ';
        // recompute: put rook on f
        q.sq[ksq+1]=rk; q.sq[ksq+3]=' ';
        if(!attacked(q,kingSq(q,white?'K':'k'),!white)) out.push_back(uciOf(ksq,ksq+2));
      }
      // queen side
      if(p.sq[ksq-4]==rk && p.sq[ksq-1]==' ' && p.sq[ksq-2]==' ' && p.sq[ksq-3]==' ' &&
         kingSafe && safe(ksq-1) && safe(ksq-2)){
        P q=p; q.sq[ksq]=' '; q.sq[ksq-4]=' '; q.sq[ksq-2]=k; q.sq[ksq-1]=rk;
        if(!attacked(q,kingSq(q,white?'K':'k'),!white)) out.push_back(uciOf(ksq,ksq-2));
      }
    }
  }
  return out;
}
int main(int argc,char**argv){
  // parse FEN board field only
  std::string fen=argv[1]; P p; memset(p.sq,' ',64);
  int r=7,f=0; size_t k=0;
  for(;k<fen.size()&&fen[k]!=' ';k++){ char c=fen[k];
    if(c=='/'){r--;f=0;} else if(c>='1'&&c<='8'){f+=c-'0';} else {p.sq[idx(f,r)]=c;f++;} }
  bool white = fen.find(" w ")==std::string::npos ? false : true;
  // Structural validity: exactly one king each, no pawns on rank 1/8.
  {
    int wk=0,bk=0;
    for(int i=0;i<64;i++){ if(p.sq[i]=='K')wk++; if(p.sq[i]=='k')bk++; }
    bool pawnBad=false;
    for(int f=0;f<8;f++){ if(tolower(p.sq[idx(f,0)])=='p')pawnBad=true; if(tolower(p.sq[idx(f,7)])=='p')pawnBad=true; }
    if(wk!=1||bk!=1||pawnBad){
      printf("INVALID kings w=%d b=%d pawn_on_back_rank=%d\n",wk,bk,(int)pawnBad);
      return 0;
    }
  }
  auto mv=legalMoves(p,white);
  bool inCheck=attacked(p,kingSq(p,white?'K':'k'),!white);
  auto parse=[&](const std::string& m,int& f,int& t,char& promo){
    f = (m[0]-'a') + 8*(m[1]-'1');
    t = (m[2]-'a') + 8*(m[3]-'1');
    promo = m.size()>4 ? m[4] : 0; };
  int caps=0; for(auto&m:mv){ int f,t; char pr; parse(m,f,t,pr); if(p.sq[t]!=' '||m.size()>4) {} if(p.sq[t]!=' ')caps++; }
  printf("%s legal=%zu in_check=%d captures=%d noncaps=%zu\n", mv.empty()? (inCheck?"CHECKMATE":"STALEMATE") : "MOVES", mv.size(), inCheck, caps, mv.size()-caps);
  for(auto&m:mv){ printf("   %s\n", m.c_str()); }
  return 0;
}
