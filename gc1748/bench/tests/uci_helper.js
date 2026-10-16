// minimal UCI driver: node child process, promise-based
const {spawn}=require('child_process');
class Uci{
  constructor(dist){this.p=spawn('node',[dist+'/uci/main.js']);this.buf='';this.lines=[];this.w=[];this.err='';
    this.p.stdout.on('data',d=>{this.buf+=d;let i;while((i=this.buf.indexOf('\n'))>=0){const l=this.buf.slice(0,i).trim();this.buf=this.buf.slice(i+1);this.lines.push(l);this.w.slice().forEach(f=>f(l));}});
    this.p.stderr.on('data',d=>this.err+=d);}
  send(s){this.p.stdin.write(s+'\n');}
  wait(re,ms=15000){return new Promise((res,rej)=>{const t=setTimeout(()=>{this.w=this.w.filter(x=>x!==f);rej(new Error('timeout '+re))},ms);const f=l=>{if(re.test(l)){clearTimeout(t);this.w=this.w.filter(x=>x!==f);res(l);}};this.w.push(f);});}
  async init(){this.send('uci');await this.wait(/^uciok/);this.send('isready');await this.wait(/^readyok/);}
  // returns {best, score:{type,val}, depth, info:[...]}
  async go(pos,cmd='go depth 6',ms=20000){this.send('ucinewgame');this.send(pos);this.send('isready');await this.wait(/^readyok/);
    const info=[];const off=this.w.push(l=>{if(l.startsWith('info depth'))info.push(l)});
    this.send(cmd);const bm=await this.wait(/^bestmove/,ms);this.w.splice(off-1,1);
    const last=info[info.length-1]||'';const m=last.match(/score (cp|mate) (-?\d+)/);
    return {best:bm.split(/\s+/)[1],score:m?{type:m[1],val:+m[2]}:null,depth:(last.match(/depth (\d+)/)||[])[1],last};}
  quit(){try{this.send('quit')}catch(e){} setTimeout(()=>{try{this.p.kill('SIGKILL')}catch(e){}},500);}
}
module.exports={Uci};

