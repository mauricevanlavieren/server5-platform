import { Transformer } from 'markmap-lib';
import { build } from 'esbuild';
import { readFileSync, writeFileSync, renameSync, readdirSync } from 'node:fs';
import { Parser } from 'htmlparser2';
import { applyTaskColors } from './task-colors.mjs';
import { validateCurrentSteps } from './current-step.mjs';
const maps = {};
for (const id of ['server5-commandcenter', 'current-projects']) {
  const source = readFileSync(id === 'current-projects' && process.env.CURRENT_PROJECTS_SOURCE || `../docs/mindmaps/import-${id}.md`, 'utf8');
  if (id === 'current-projects') validateCurrentSteps(source);
  const headings = source.split('\n').filter(line => line.trim());
  if (!headings.every(line => /^#{1,6} .+$/u.test(line))) throw Error(`Unexpected source structure: ${id}`);
  const { root } = new Transformer().transform(source);
  // These imports contain plain-text headings: fail rather than silently alter text.
  const plainText = html => {
    let text = '';
    const parser = new Parser({ ontext: chunk => { text += chunk; }, onopentag: () => { throw Error('Unexpected HTML in source heading'); } });
    parser.end(html);
    return text;
  };
  const walk = node => [node, ...(node.children || []).flatMap(walk)];
  const nodes = walk(root);
  if (nodes.length !== headings.length) throw Error(`Node count mismatch: ${id}`);
  const stack = [];
  headings.forEach((line, index) => {
    const [, hashes, text] = line.match(/^(#+) (.*)$/u);
    const level = hashes.length;
    if ((index === 0 && level !== 1) || (index > 0 && (level === 1 || level > stack.length + 1))) throw Error(`Invalid hierarchy: ${id}`);
    if (plainText(nodes[index].content) !== text) throw Error(`Text mismatch: ${id}, node ${index}`);
    stack.length = level - 1;
    if (level > 1 && !(stack[level - 2].children || []).includes(nodes[index])) throw Error(`Hierarchy mismatch: ${id}`);
    stack.push(nodes[index]);
  });
  if (id === 'current-projects') applyTaskColors(root, node => plainText(node.content));
  maps[id] = root;
  console.log(`${id}: ${nodes.length} nodes verified`);
}
// Broker receipts survive pruning; export metadata only, never worker text.
const latest = new Map();
for (const name of readdirSync('../docs/mindmaps/live-lifecycle').sort()) {
  if (!/^broker-\d+\.(?:pending\.)?json$/u.test(name)) continue;
  const { event } = JSON.parse(readFileSync(`../docs/mindmaps/live-lifecycle/${name}`, 'utf8'));
  if (!latest.has(event.task_id) || latest.get(event.task_id).seq < event.seq) latest.set(event.task_id, event);
}
const accepted = new Set();
const acceptanceWalk = node => {
  if (/\[ACCEPTED:[A-Za-z0-9_-]+\]/u.test(node.content)) {
    const task = node.content.match(/^\[TASK:([A-Za-z0-9_-]+)\]/u);
    const links = [...node.content.matchAll(/\[LINK-TASK:([A-Za-z0-9_-]+)\]/gu)];
    if (task) accepted.add(task[1]);
    else if (/^\[STEP:/u.test(node.content) && links.length === 1) accepted.add(links[0][1]);
  }
  (node.children || []).forEach(acceptanceWalk);
};
acceptanceWalk(maps['current-projects']);
maps.taskStatus = [...latest.values()].sort((a,b) => b.seq-a.seq).map(e => ({id:e.task_id, status:e.status, at:e.at, accepted:e.status === 'succeeded' && accepted.has(e.task_id)}));
if (!process.env.MAP_OUTPUT) {
  await build({entryPoints:['viewer.js'], bundle:true, minify:true, outfile:'public/.viewer.js.next'});
  renameSync('public/.viewer.js.next', 'public/viewer.js');
}
const output = process.env.MAP_OUTPUT || 'public/map.json';
writeFileSync(`${output}.next`, JSON.stringify(maps));
renameSync(`${output}.next`, output);
