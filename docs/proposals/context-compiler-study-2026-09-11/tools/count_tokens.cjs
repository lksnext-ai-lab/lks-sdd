// Reference token counts, not host input/output billing or hidden system context.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const o=require(path.join(root,'.vendor/gpt-tokenizer/cjs/encoding/o200k_base.js'));
const c=require(path.join(root,'.vendor/gpt-tokenizer/cjs/encoding/cl100k_base.js'));
const read=fs.readFileSync(0,'utf8');
const inputs=JSON.parse(read);
const count=(text)=>({characters:text.length,utf8_bytes:Buffer.byteLength(text),o200k_base:o.encode(text).length,cl100k_base:c.encode(text).length});
const outputs=inputs.map(item=>{
 const text=item.path?fs.readFileSync(path.resolve(root,item.path),'utf8'):item.text;
 return {id:item.id,...count(text),sha256:crypto.createHash('sha256').update(text).digest('hex')};
});
process.stdout.write(JSON.stringify(outputs,null,2));
