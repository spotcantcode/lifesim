import { ReactFlow, Background, Controls, type Node, type Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { Scenario } from '../types';
export default function TimelineTree({ scenarios, select }: { scenarios: Scenario[]; select: (id: string) => void }) {
  const depth = (scenario: Scenario, seen = new Set<string>()): number => {
    if (!scenario.parent_id || seen.has(scenario.id)) return 0;
    seen.add(scenario.id);
    const parent = scenarios.find(item => item.id === scenario.parent_id);
    return parent ? depth(parent, seen) + 1 : 0;
  };
  const nodes: Node[] = scenarios.map((scenario, index) => ({ id: scenario.id, position: { x: depth(scenario)*320, y: index*125 }, data: { label: <><strong>{scenario.name}</strong><span>Month {scenario.state.month} · {scenario.state.work_hours}h / week</span><small>{scenario.parent_id ? `Branched at month ${scenario.fork_month}` : 'Original timeline'}</small></> }, sourcePosition: 'right' as Node['sourcePosition'], targetPosition: 'left' as Node['targetPosition'], style: { width: 260 } }));
  const edges: Edge[] = scenarios.filter(item => item.parent_id).map(item => ({ id: item.id, source: item.parent_id!, target: item.id, type: 'smoothstep', style: { stroke: '#8eac7c' } }));
  return <div className="tree"><ReactFlow nodes={nodes} edges={edges} fitView colorMode="dark" nodesDraggable={false} nodesConnectable={false} onNodeClick={(_, node) => select(node.id)}><Background color="#3b473f" gap={24}/><Controls showInteractive={false}/></ReactFlow></div>;
}
