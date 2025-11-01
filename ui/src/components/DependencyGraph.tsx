import React, { useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ImpactReport } from '../types/types';
import './DependencyGraph.css';

interface DependencyGraphProps {
  report: ImpactReport | null;
  onNodeClick: (nodeId: string) => void;
  selectedNodeId: string | null;
}

const DependencyGraph: React.FC<DependencyGraphProps> = ({
  report,
  onNodeClick,
  selectedNodeId,
}) => {
  const { nodes, edges } = useMemo(() => {
    if (!report) {
      return { nodes: [], edges: [] };
    }

    const nodes: Node[] = report.nodes.map((node, index) => {
      const getPosition = (index: number, total: number) => {
        const angle = (index / total) * 2 * Math.PI;
        const radius = 200;
        const centerX = 400;
        const centerY = 300;
        return {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        };
      };

      const position = getPosition(index, report.nodes.length);
      
      return {
        id: node.id,
        type: 'default',
        position,
        data: {
          label: (
            <div className="node-label">
              <div className="node-icon">{getNodeIcon(node.type)}</div>
              <div className="node-name">{node.name}</div>
              <div className="node-confidence">{Math.round(node.confidence * 100)}%</div>
            </div>
          ),
        },
        style: {
          background: getNodeColor(node.type, node.confidence),
          border: selectedNodeId === node.id ? '3px solid #3498db' : '2px solid #2c3e50',
          borderRadius: '8px',
          width: 160,
          height: 80,
          fontSize: '12px',
        },
      };
    });

    const edges: Edge[] = report.edges.map((edge) => ({
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: edge.confidence > 0.8,
      style: {
        strokeWidth: Math.max(1, edge.confidence * 4),
        stroke: getEdgeColor(edge.relationship_type, edge.confidence),
        strokeDasharray: edge.relationship_type === 'potential' ? '5,5' : 'none',
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: getEdgeColor(edge.relationship_type, edge.confidence),
      },
    }));

    return { nodes, edges };
  }, [report, selectedNodeId]);

  const [flowNodes, setNodes, onNodesChange] = useNodesState(nodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(edges);

  React.useEffect(() => {
    setNodes(nodes);
  }, [nodes, setNodes]);

  React.useEffect(() => {
    setEdges(edges);
  }, [edges, setEdges]);

  const onNodeClickHandler = (event: React.MouseEvent, node: Node) => {
    onNodeClick(node.id);
  };

  if (!report) {
    return (
      <div className="empty-graph">
        <div className="empty-state">
          <h3>No Investigation Data</h3>
          <p>Enter a change request to see the dependency graph</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dependency-graph" data-testid="react-flow">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickHandler}
        connectionMode={ConnectionMode.Loose}
        fitView
      >
        <Background color="#f0f0f0" gap={16} />
        <Controls />
        <MiniMap 
          nodeColor={(node) => '#2c3e50'}
          nodeStrokeWidth={3}
          nodeBorderRadius={2}
        />
      </ReactFlow>
    </div>
  );
};

function getNodeIcon(type: string): string {
  const icons: Record<string, string> = {
    db_table: '🗄️',
    repo: '📁',
    file: '📄',
    api_endpoint: '🔌',
  };
  return icons[type] || '📦';
}

function getNodeColor(type: string, confidence: number): string {
  const baseColors: Record<string, string> = {
    db_table: '#e74c3c',
    repo: '#3498db',
    file: '#f39c12',
    api_endpoint: '#9b59b6',
  };
  
  const opacity = 0.3 + (confidence * 0.7);
  const baseColor = baseColors[type] || '#95a5a6';
  
  // Convert hex to rgba with opacity
  const hex = baseColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

function getEdgeColor(type: string, confidence: number): string {
  if (type === 'literal') return '#e74c3c';
  if (type === 'semantic') return '#f39c12';
  if (type === 'potential') return '#95a5a6';
  return '#7f8c8d';
}

export default DependencyGraph;