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
import { ProjectSource } from '../App';
import './DependencyGraph.css';

interface DependencyGraphProps {
  report: ImpactReport | null;
  onNodeClick: (nodeId: string) => void;
  selectedNodeId: string | null;
  projectSources: ProjectSource[];
}

const DependencyGraph: React.FC<DependencyGraphProps> = ({
  report,
  onNodeClick,
  selectedNodeId,
  projectSources,
}) => {
  const { nodes, edges } = useMemo(() => {
    const investigationNodes = report ? report.nodes : [];
    const allNodes = [...investigationNodes];

    // Add project source nodes as disconnected nodes
    projectSources.forEach((source, index) => {
      // Check if this source already exists in investigation nodes
      const existingNode = investigationNodes.find(node =>
        node.name === source.original_filename || node.id === `source-${source.id}`
      );

      if (!existingNode) {
        allNodes.push({
          id: `source-${source.id}`,
          name: source.original_filename,
          type: 'file',
          path: source.original_filename,
          source_type: 'uploaded_file',
          confidence: 1.0, // Uploaded files have 100% confidence
          last_updated: source.created_at,
        });
      }
    });

    if (allNodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    const nodes: Node[] = allNodes.map((node, index) => {
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

      const position = getPosition(index, allNodes.length);
      
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

    const edges: Edge[] = report ? report.edges.map((edge) => ({
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
    })) : [];

    return { nodes, edges };
  }, [report, selectedNodeId, projectSources]);

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

  if (!report && projectSources.length === 0) {
    return (
      <div className="empty-graph">
        <div className="empty-state">
          <h3>No Investigation Data</h3>
          <p>Enter a change request to see the dependency graph</p>
        </div>
      </div>
    );
  }

  // Don't return empty state for sources - let them render as disconnected nodes in the graph

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
    uploaded_file: '📎', // Different icon for uploaded files
  };
  return icons[type] || '📦';
}

function getNodeColor(type: string, confidence: number): string {
  const baseColors: Record<string, string> = {
    db_table: '#e74c3c',
    repo: '#3498db',
    file: '#f39c12',
    api_endpoint: '#9b59b6',
    uploaded_file: '#27ae60', // Green color for uploaded files
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