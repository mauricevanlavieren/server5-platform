// Exactly one logical task label carries status; unrelated steps remain neutral.
export function applyTaskColors(root, textOf = node => node.content) {
  const entries = [];
  const walk = (node, project = null, depth = 0) => {
    const text = textOf(node);
    const match = depth === 1 && text.match(/\[PROJECT:([A-Z0-9-]+)\]/u);
    if (match) project = match[1];
    entries.push([node, text, project]);
    (node.children || []).forEach(child => walk(child, project, depth + 1));
  };
  walk(root);
  const tasks = new Map();
  for (const [node, text] of entries) {
    node.payload ||= {};
    delete node.payload.taskColor;
    delete node.payload.taskId;
    const match = text.match(/^\[TASK:([A-Za-z0-9_-]{1,80})\] (queued|running|succeeded|failed|blocked|cancelled|interrupted)(?:;|$)/u);
    if (!match) continue;
    if (tasks.has(match[1])) throw Error('Ambiguous task color binding');
    const timestamp = text.match(/;\s*(\d{4}-\d\d-\d\dT[^; ]+)/u);
    const parsed = timestamp ? Date.parse(timestamp[1]) : NaN;
    tasks.set(match[1], {id: match[1], status: match[2], node, time: Number.isFinite(parsed) ? parsed : -Infinity});
  }
  for (const selected of tasks.values()) {
  let accepted = false;
  if (selected.status === 'succeeded') {
    accepted = entries.some(([, text]) => {
      if (!/\[ACCEPTED:[A-Za-z0-9_-]+\]/u.test(text)) return false;
      if (text.startsWith(`[TASK:${selected.id}] `)) return true;
      const links = [...text.matchAll(/\[LINK-TASK:([A-Za-z0-9_-]{1,80})\]/gu)];
      return /^\[STEP:[A-Z0-9-]+\] /u.test(text) && links.length === 1 && links[0][1] === selected.id;
    });
  }
  const target = selected.node;
  const color = accepted ? 'accepted' : {queued:null, running:'running', succeeded:'review', failed:'failed', blocked:'failed', cancelled:'failed', interrupted:'failed'}[selected.status];
  if (color) {
    target.payload.taskColor = color;
    target.payload.taskId = selected.id;
  }
}
}
