'use strict';
// Counts explicit indexed JS work, including reusable sorted moves and keys.
// Native typed-sort internals, geometry and history reads are NOT counted.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),{createStore}=require(root+'/tools/durable-records');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),input=path.join(root,'diagnostics/quiet-sort11/evidence/phases.ndjson'),bytes=fs.readFileSync(input);
assert.equal(sha(bytes),'70be6fca5a3946fa4d3cac80cb34e96284838d5623e6adf0239a9cda39d91571');
const rows=bytes.toString().trimEnd().split('\n').map(JSON.parse),out=path.join(__dirname,'evidence'),store=createStore(out,{expectedRecords:2,purpose:'exact corpus indexed-work diagnosis only; not NPS',corpusSha256:sha(bytes)});
const fields=m=>[m.from,m.to,m.piece,m.captured,m.promo,m.flags];
const empty=()=>({moveReads:0,moveWrites:0,scoreReads:0,scoreWrites:0,keyReads:0,keyWrites:0,nativeSortCalls:0,nativeSortItems:0});
for(const iteration of [15,16]){
 const target=path.join(root,'staged/iteration-'+iteration+'/candidate'),{Board}=require(target+'/board/board'),{Search}=require(target+'/search/search'),{StagedMovePicker}=require(target+'/search/movepicker'),gen=require(target+'/move/movegen');
 const s=new Search(new Board()),p=new StagedMovePicker(s,0),original=gen.generateQuietMoves,totals=empty();let counting=false,stats,items=0;
 function proxy(t,label,typed=false){return new Proxy(t,{get(t,k){
  if(counting&&/^\d+$/.test(String(k)))stats[label+'Reads']++;
  if(typed&&k==='subarray')return(...args)=>proxy(t.subarray(...args),label,true);
  if(typed&&k==='sort')return(...args)=>{if(counting){stats.nativeSortCalls++;stats.nativeSortItems+=t.length;}return t.sort(...args);};
  const v=t[k];return typed&&typeof v==='function'?v.bind(t):v;
 },set(t,k,v){if(counting&&/^\d+$/.test(String(k)))stats[label+'Writes']++;t[k]=v;return true;}});}
 p.quietScores=proxy(p.quietScores,'score');p.sortedQuiets=proxy(p.sortedQuiets,'move');p.quietSortKeys=proxy(new Int32Array(1024),'key',true);
 const stream=path.join(out,'source'+iteration+'.ndjson'),fd=fs.openSync(stream,'wx');
 function write(record){const b=Buffer.from(JSON.stringify(record)+'\n');for(let offset=0;offset<b.length;){const n=fs.writeSync(fd,b,offset,b.length-offset);assert(n>0);offset+=n;}}
 try{
  for(const row of rows){
   s.board.setFen(row.fen);const moves=row.source.map(([from,to,piece,captured,promo,flags])=>({from,to,piece,captured,promo,flags}));
   moves.forEach((m,i)=>s.history[m.piece][m.to]=row.scores[i]);gen.generateQuietMoves=()=>proxy(moves.slice(),'move');p.init(null,5);stats=empty();counting=true;
   try{p.generateQuiets();}finally{counting=false;}
   assert.deepEqual(p.quiets.map(fields),row.sortedIndices.map(i=>row.source[i]));assert.deepEqual(p.quietScores.slice(0,moves.length),row.sortedIndices.map(i=>row.scores[i]));assert.equal(s.quietSnapshots.active.length,0);
   for(const k of Object.keys(totals))totals[k]+=stats[k];items+=moves.length;write({id:row.id,items:moves.length,...stats});
  }
  fs.fsyncSync(fd);
 }finally{fs.closeSync(fd);gen.generateQuietMoves=original;}
 assert.equal(rows.length,16336);assert.equal(items,462831);
 const record={iteration,phases:rows.length,items,totals,streamSha256:sha(fs.readFileSync(stream)),sourceSha256:sha(fs.readFileSync(target+'/search/movepicker.js')),scope:'Explicit indexed operations including all move/score/key buffers; native typed sort internals excluded; no NPS inference'};store.append(record);console.log(JSON.stringify(record));
}
store.finish();
