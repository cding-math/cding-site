#!/usr/bin/env node
// Maintainer-only generation. Cloudflare still builds with Hugo alone.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
const renderer=path.join(root,'static/vendor/katex/0.19.1/katex.min.js');
const katex=require(renderer);
if(katex.version!=='0.19.1')throw new Error('Unexpected KaTeX renderer version');
const expressions=JSON.parse(fs.readFileSync(path.join(root,'data/math_expressions.json'),'utf8'));
if(!Array.isArray(expressions)||expressions.some(value=>typeof value!=='string'||!value.trim())){
  throw new Error('Math expressions must be a nonempty-string array');
}
const output={
  version:katex.version,
  source_sha256:createHash('sha256').update(fs.readFileSync(renderer)).digest('hex'),
  inline:{},
  display:{},
};
for(const expression of [...new Set(expressions.map(value=>value.trim()))].sort()){
  for(const mode of ['inline','display']){
    output[mode][expression]=katex.renderToString(expression,{
      output:'htmlAndMathml',displayMode:mode==='display',trust:false,
      maxExpand:1000,maxSize:20,throwOnError:true,strict:'error',
    });
  }
}
const target=path.join(root,'data/math_rendered.json');
const text=JSON.stringify(output,null,2)+'\n';
if(process.argv.includes('--check')){
  if(!fs.existsSync(target)||fs.readFileSync(target,'utf8')!==text){
    throw new Error('Math cache is missing or stale. Run node scripts/render_math.mjs.');
  }
  console.log('Math cache matches the approved KaTeX 0.19.1 renderer.');
}else{
  fs.writeFileSync(target,text);
  console.log(`Rendered ${Object.keys(output.inline).length} expressions in inline and display modes.`);
}
