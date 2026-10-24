import {readFileSync} from 'node:fs';
import {build} from 'esbuild';
let source=readFileSync('test-projects-viewer.js','utf8')
 .replace("import './public/test-projects-control.js';",'')
 .replace('./test-projects.json','./current-projects.json')
 .replace('if(JSON.stringify(s)!==previous){',`if(!s.root){
    if(map){map.destroy();map=null;} previous=undefined;
    document.querySelector('#status').textContent='Geen actieve opdracht';return;
  }
  if(JSON.stringify(s)!==previous){`);
await build({stdin:{contents:source,resolveDir:process.cwd(),sourcefile:'current-projects-viewer.js'},bundle:true,minify:true,outfile:'public/current-projects.js'});
