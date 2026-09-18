// Controlled serialization experiment. Round-trip is NOT model comprehension.
const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const S=path.resolve(__dirname,'..');
const encodings={o200k_base:require(path.join(S,'.vendor/gpt-tokenizer/cjs/encoding/o200k_base.js')),cl100k_base:require(path.join(S,'.vendor/gpt-tokenizer/cjs/encoding/cl100k_base.js'))};
const count=t=>Object.fromEntries(Object.entries(encodings).map(([k,v])=>[k,v.encode(t).length]));
const fixtures=[
 {id:'small-flat',data:[{id:'FR-001',state:'confirmed',unit:'api',limit:10},{id:'FR-002',state:'confirmed',unit:'web',limit:20}]},
 {id:'uniform-100',data:Array.from({length:100},(_,i)=>({id:`FR-${String(i+1).padStart(3,'0')}`,state:i%7===0?'pending':'confirmed',unit:['api','web','worker'][i%3],limit:(i+1)*5}))},
 {id:'nested-irregular',data:[{id:'A',rules:{allow:['reader','editor'],deny:{crossTenant:true}},max:null},{id:'B',states:[{on:'paid',unless:['chargeback','hold']},{on:'open'}],version:2},{id:'C',name:'Étiquette',enabled:false}]},
 {id:'unicode-and-escaping',data:[{id:'a|b',text:'No borrar; excepción: retención legal.\n行を削除しない。',value:'"quoted",comma'}, {id:'é',text:'e\u0301 != é; Ezin da ezabatu; لا تحذف',value:' \\t '}]},
 {id:'conditions',data:[{condition:'tenant distinto',result:'denegar',exception:'ninguna'},{condition:'sin permiso',result:'denegar',exception:'ninguna'},{condition:'0 registros',result:'CSV solo cabecera',exception:'ninguna'},{condition:'1..10000 registros',result:'CSV completo',exception:'retención legal exige omitir datos eliminados'},{condition:'>10000 registros',result:'rechazar',exception:'ninguna'}]},
];
const rows=[];const texts=[];
for(const f of fixtures){
 const variants={
  json_pretty:JSON.stringify(f.data,null,2),
  json_compact:JSON.stringify(f.data),
  markdown_records:f.data.map((r,i)=>`## Registro ${i+1}\n`+Object.entries(r).map(([k,v])=>`- ${k}: ${JSON.stringify(v)}`).join('\n')).join('\n\n'),
 };
 const keys=Object.keys(f.data[0]);
 const uniform=f.data.every(r=>JSON.stringify(Object.keys(r))===JSON.stringify(keys));
 if(uniform){
  // JSON cells keep exact types, unicode and embedded delimiters recoverable.
  variants.tabular_json_cells='Cada línea es un array JSON; columnas: '+JSON.stringify(keys)+'\n'+f.data.map(r=>JSON.stringify(keys.map(k=>r[k]))).join('\n');
  const reconstructed=variants.tabular_json_cells.split('\n').slice(1).map(l=>Object.fromEntries(JSON.parse(l).map((v,i)=>[keys[i],v])));
  if(JSON.stringify(reconstructed)!==JSON.stringify(f.data))throw Error('round trip');
 }
 for(const [format,text] of Object.entries(variants)){
  rows.push({fixture:f.id,format,utf8_bytes:Buffer.byteLength(text),...count(text),round_trip:format.startsWith('json')||format==='tabular_json_cells'?'verified':'not-applicable-text-view'});
  texts.push({fixture:f.id,format,text});
 }
 const original=variants.json_pretty;
 const packed=zlib.gzipSync(original).toString('base64');
 if(zlib.gunzipSync(Buffer.from(packed,'base64')).toString()!==original)throw Error('gzip roundtrip');
 rows.push({fixture:f.id,format:'gzip_base64_not_directly_usable',utf8_bytes:Buffer.byteLength(packed),...count(packed),decoded_tokens:count(original),round_trip:'verified-by-code-not-LLM'});
}
const known={hello_world:encodings.o200k_base.encode('hello world'),cl100k_hello_world:encodings.cl100k_base.encode('hello world')};
if(JSON.stringify(known.hello_world)!=='[24912,2375]'||JSON.stringify(known.cl100k_hello_world)!=='[15339,1917]')throw Error('known tokenizer vector');
const out=path.join(S,'evidence');
fs.writeFileSync(path.join(out,'format-results.json'),JSON.stringify({package:'gpt-tokenizer@3.4.0',scope:'reference text tokens; no host billing, visual tokens or comprehension measured',known_vectors:known,rows},null,2));
fs.writeFileSync(path.join(out,'format-corpus.json'),JSON.stringify(texts,null,2));
console.log(JSON.stringify(rows,null,2));
