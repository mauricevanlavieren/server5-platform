// Project positions are explicit editorial state, never inferred from broker IDs.
export function validateCurrentSteps(source) {
  let project;
  const finish = () => {
    if (project && (project.status === 'ACTIEF' ? (project.count > 1 || (project.count === 0 && !project.parked)) : project.count !== 0))
      throw Error(`Current-step count invalid: ${project.id}`);
  };
  const ids = new Set();
  for (const line of source.split('\n')) {
    if (line.startsWith('## ')) {
      finish();
      project = undefined;
      const match = line.match(/\[PROJECT:([A-Z0-9-]+)\] \[(ACTIEF|WACHTEND|GEBLOKKEERD|VOLTOOID)\]/u);
      if (match) {
        if (ids.has(match[1])) throw Error('Duplicate project ID');
        ids.add(match[1]);
        project = {id: match[1], status: match[2], count: 0, parked: false};
      } else if (/^## \d+\. \d+\./u.test(line)) {
        throw Error('Project needs explicit ID and status');
      }
    } else if (project && /^### \[STEP:[A-Z0-9-]+\] (?:GEPLAND|BEOORDELING OPEN|RCCAP) .+\[LINK-TASK:[A-Za-z0-9_-]{16,80}\]$/u.test(line)) {
      project.parked = true;
    } else if (line.includes('🔄 HUIDIGE STAP')) {
      if (!project) {
        // Workflow may describe the rule, but task records cannot claim a position.
        if (/\[(?:TASK|TEMP)[^\]]*\]/u.test(line)) throw Error('Broker/history record claims project position');
      } else {
        project.count++;
        if (!/^### .*\[STEP:[A-Z0-9-]+\]/u.test(line) || /pending|geblokkeerd|failed|succeeded|wacht op|afgerond/iu.test(line))
          throw Error(`Invalid current step: ${project.id}`);
      }
    }
  }
  finish();
}
