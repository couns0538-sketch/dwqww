// usage: node bench.js <distdir> [depth=9]  -> per-position nodes + total nodes + nps via the dist's UCI (single thread, fresh ucinewgame each)
const path=require('path');const D=path.resolve(process.argv[2]);const DEPTH=+process.argv[3]||9;
const {Uci}=require('./tests/uci_helper');
const P=[['startpos','startpos'],
['kiwipete','fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'],
['qgd-middle','fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8'],
['rook-endgame','fen 8/5pk1/6p1/8/3R4/6P1/r4PK1/8 w - - 0 1'],
['pos3-endgame','fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1'],
['tactical-pos4','fen r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1']];
(async()=>{const u=new Uci(D);await u.init();let tn=0,tt=0;const rows=[];
 for(const [n,p] of P){u.send('ucinewgame');u.send('position '+p);u.send('isready');await u.wait(/^readyok/);
  const info=[];const f=l=>{if(l.startsWith('info depth'))info.push(l)};u.w.push(f);const t0=Date.now();u.send('go depth '+DEPTH);const bm=await u.wait(/^bestmove/,300000);const ms=Date.now()-t0;u.w=u.w.filter(x=>x!==f);
  const nodes=+(info[info.length-1].match(/nodes (\d+)/)[1]);tn+=nodes;tt+=ms;rows.push(`${n.padEnd(14)} depth ${DEPTH} nodes ${String(nodes).padStart(9)} ${String(ms).padStart(6)}ms best ${bm.split(' ')[1]}`);}
 u.quit();console.log(rows.join('\n'));console.log(`BENCH ${path.basename(D)} depth=${DEPTH} nodes=${tn} time=${tt}ms nps=${Math.round(tn*1000/tt)}`);})().catch(e=>{console.log('ERROR',e.message);process.exit(2)});

