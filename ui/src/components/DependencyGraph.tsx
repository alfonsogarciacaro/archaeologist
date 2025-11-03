import React, { useMemo, useState, useCallback } from 'react';
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
  NodeMouseHandler,
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
  onNodeDelete?: (nodeId: string) => void;
  onNodeMetadataUpdate?: (nodeId: string, metadata: any) => void;
}

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  nodeId: string | null;
}

interface MetadataDialogState {
  visible: boolean;
  nodeId: string | null;
  nodeData: any;
}

interface DeleteConfirmState {
  visible: boolean;
  nodeId: string | null;
  nodeName: string;
}

const DependencyGraph: React.FC<DependencyGraphProps> = ({
  report,
  onNodeClick,
  selectedNodeId,
  projectSources,
  onNodeDelete,
  onNodeMetadataUpdate,
}) => {
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    nodeId: null,
  });

  const [metadataDialog, setMetadataDialog] = useState<MetadataDialogState>({
    visible: false,
    nodeId: null,
    nodeData: null,
  });

  const [deleteConfirm, setDeleteConfirm] = useState<DeleteConfirmState>({
    visible: false,
    nodeId: null,
    nodeName: '',
  });

  const [editingMetadata, setEditingMetadata] = useState<string>('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState<boolean>(false);

  // Load saved positions from localStorage
  const loadSavedPositions = useCallback(() => {
    try {
      const saved = localStorage.getItem('nodePositions');
      const positions = saved ? JSON.parse(saved) : {};
      console.log('Loading saved positions:', positions);
      return positions;
    } catch {
      console.log('Failed to load saved positions, using empty object');
      return {};
    }
  }, []);

  // Save positions to localStorage
  const savePositions = useCallback((positions: Record<string, { x: number; y: number }>) => {
    try {
      console.log('Saving positions to localStorage:', positions);
      localStorage.setItem('nodePositions', JSON.stringify(positions));
      console.log('Positions saved successfully');
    } catch (error) {
      console.warn('Failed to save node positions:', error);
    }
  }, []);

  const { nodes, edges } = useMemo(() => {
    const investigationNodes = report ? report.nodes : [];
    const sourceNodes = projectSources.map(source => ({
      id: `source-${source.id}`,
      name: source.original_filename,
      type: 'file',
      path: source.original_filename,
      source_type: 'uploaded_file',
      confidence: 1.0,
      last_updated: source.created_at,
      metadata: source.metadata || {},
    }));

    // Add project source nodes as disconnected nodes, avoiding duplicates
    const allNodes = [...investigationNodes];
    sourceNodes.forEach((sourceNode) => {
      const existingNode = investigationNodes.find(node =>
        node.name === sourceNode.name || node.id === sourceNode.id
      );
      if (!existingNode) {
        allNodes.push(sourceNode);
      }
    });

    const savedPositions = loadSavedPositions();

    if (allNodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    const nodes: Node[] = allNodes.map((node) => {
      // Use saved position if available, otherwise calculate default position
      const savedPosition = savedPositions[node.id];
      let position;
      
      if (savedPosition) {
        // Use saved position
        position = savedPosition;
        console.log(`Using saved position for ${node.id}:`, position);
      } else {
        // Calculate default position for new nodes
        const index = allNodes.indexOf(node);
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
        position = getPosition(index, allNodes.length);
        console.log(`Using default position for ${node.id}:`, position);
      }

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
  }, [report, selectedNodeId, projectSources, loadSavedPositions]);

  const [flowNodes, setNodes, onNodesChange] = useNodesState(nodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(edges);

  // Custom nodes change handler to save positions
  const handleNodesChange = useCallback((changes: any) => {
    console.log('Nodes changed - raw changes:', changes);
    console.log('Changes type:', typeof changes);
    console.log('Is array?', Array.isArray(changes));
    
    // Handle different formats of changes
    let nodeChanges = [];
    
    if (Array.isArray(changes)) {
      nodeChanges = changes;
    } else if (changes && changes.nodes) {
      // Newer ReactFlow versions might use different format
      nodeChanges = changes.nodes;
    } else if (changes && typeof changes === 'object') {
      // Single change object
      nodeChanges = [changes];
    }
    
    console.log('Processed node changes:', nodeChanges);
    
    // Look for position changes
    const movedNodes = nodeChanges.filter((change, index) => {
      console.log(`Change ${index}:`, change);
      console.log(`  - type: ${change?.type}`);
      console.log(`  - dragging: ${change?.dragging}`);
      console.log(`  - position: ${change?.position}`);
      
      return change?.type === 'position' && change?.dragging === false;
    });
    
    if (movedNodes.length > 0) {
      console.log('Nodes moved:', movedNodes);
      
      // Save new positions
      const currentPositions = loadSavedPositions();
      const newPositions = { ...currentPositions };
      
      movedNodes.forEach(change => {
        // Check if position exists and has x, y coordinates
        if (change.position && typeof change.position.x === 'number' && typeof change.position.y === 'number') {
          newPositions[change.id] = {
            x: change.position.x,
            y: change.position.y
          };
          console.log(`Saving position for ${change.id}:`, change.position);
        } else {
          console.warn(`Invalid position for node ${change.id}:`, change.position);
        }
      });
      
      savePositions(newPositions);
    }
    
    // Pass changes to ReactFlow
    onNodesChange(changes);
  }, [loadSavedPositions, savePositions, onNodesChange]);

  React.useEffect(() => {
    console.log('Updating flow nodes, current nodes:', nodes);
    setNodes(nodes);
  }, [nodes, setNodes]);

  React.useEffect(() => {
    setEdges(edges);
  }, [edges, setEdges]);

  // Helper function to get all node data
  const getAllNodeData = useCallback(() => {
    const investigationNodes = report ? report.nodes : [];
    const sourceNodes = projectSources.map(source => ({
      id: `source-${source.id}`,
      name: source.original_filename,
      type: 'file',
      path: source.original_filename,
      source_type: 'uploaded_file',
      confidence: 1.0,
      last_updated: source.created_at,
      metadata: source.metadata || {},
    }));
    return [...investigationNodes, ...sourceNodes];
  }, [report, projectSources]);

  // Close all menus when clicking elsewhere
  const closeAllMenus = useCallback(() => {
    setContextMenu(prev => ({ ...prev, visible: false }));
    setMetadataDialog(prev => ({ ...prev, visible: false }));
    setDeleteConfirm(prev => ({ ...prev, visible: false }));
  }, []);

  // Handle node right-click for context menu
  const onNodeContextMenu: NodeMouseHandler = useCallback((event, node) => {
    event.preventDefault();

    setContextMenu({
      visible: true,
      x: event.clientX,
      y: event.clientY,
      nodeId: node.id,
    });
  }, []);

  // Handle node click
  const onNodeClickHandler = useCallback((event: React.MouseEvent, node: Node) => {
    if (event.button === 0) { // Left click
      closeAllMenus();
      onNodeClick(node.id);
    }
  }, [onNodeClick, closeAllMenus]);

  // Handle node drag start
  const onNodeDragStart = useCallback((event: any, node: Node) => {
    console.log('Node drag started:', node.id);
  }, []);

  // Handle node drag end to save positions
  const onNodeDragEnd = useCallback((event: any, node: Node) => {
    console.log('Node drag ended:', node.id, 'to position:', node.position);
    
    // Save to localStorage
    const positions: Record<string, { x: number; y: number }> = {
      ...loadSavedPositions(),
      [node.id]: { x: node.position.x, y: node.position.y },
    };
    savePositions(positions);
    
    // Also update the node in ReactFlow state to ensure consistency
    setNodes((currentNodes) => 
      currentNodes.map((n) => 
        n.id === node.id 
          ? { ...n, position: node.position }
          : n
      )
    );
  }, [loadSavedPositions, savePositions, setNodes]);

  // Handle delete node
  const handleDeleteNode = useCallback((nodeId: string) => {
    console.log('Delete node clicked:', nodeId); // Keep this for now to verify click works
    const allNodeData = getAllNodeData();
    const nodeData = allNodeData.find(n => n.id === nodeId);

    console.log('Setting delete confirm to visible:', true);
    // Close context menu first, then show dialog
    setContextMenu(prev => ({ ...prev, visible: false }));
    setTimeout(() => {
      setDeleteConfirm({
        visible: true,
        nodeId,
        nodeName: nodeData?.name || 'Unknown Node',
      });
    }, 10);
  }, [getAllNodeData]);

  // Handle view/edit metadata
  const handleViewMetadata = useCallback((nodeId: string) => {
    console.log('View metadata clicked:', nodeId);
    const allNodeData = getAllNodeData();
    const nodeData = allNodeData.find(n => n.id === nodeId);

    console.log('Setting metadata dialog to visible:', true, 'nodeData:', nodeData);
    
    // Extract existing metadata comments
    const existingComments = nodeData?.metadata?.comments || '';
    setEditingMetadata(existingComments);
    setHasUnsavedChanges(false);
    
    // Close context menu first, then show dialog
    setContextMenu(prev => ({ ...prev, visible: false }));
    setTimeout(() => {
      setMetadataDialog({
        visible: true,
        nodeId,
        nodeData,
      });
    }, 10);
  }, [getAllNodeData]);

  // Confirm delete
  const confirmDelete = useCallback(() => {
    if (deleteConfirm.nodeId && onNodeDelete) {
      onNodeDelete(deleteConfirm.nodeId);
    }
    setDeleteConfirm(prev => ({ ...prev, visible: false, nodeId: null, nodeName: '' }));
  }, [deleteConfirm.nodeId, onNodeDelete]);

  // Update metadata
  const updateMetadata = useCallback((nodeId: string) => {
    const metadata = { comments: editingMetadata };
    console.log('Updating metadata for node:', nodeId, 'with:', metadata);
    
    if (onNodeMetadataUpdate) {
      onNodeMetadataUpdate(nodeId, metadata);
    }
    setMetadataDialog(prev => ({ ...prev, visible: false, nodeId: null, nodeData: null }));
    setEditingMetadata('');
    setHasUnsavedChanges(false);
  }, [onNodeMetadataUpdate, editingMetadata]);


  // Close context menu when clicking outside
  React.useEffect(() => {
    const handleMouseDown = (event: MouseEvent) => {
      // Don't close if clicking inside context menu
      const target = event.target as HTMLElement;
      const contextMenuElement = document.querySelector('.context-menu');
      if (contextMenuElement && contextMenuElement.contains(target)) {
        return;
      }
      setContextMenu(prev => ({ ...prev, visible: false }));
    };

    if (contextMenu.visible) {
      document.addEventListener('mousedown', handleMouseDown);
      return () => document.removeEventListener('mousedown', handleMouseDown);
    }
  }, [contextMenu.visible]);

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

  return (
    <>
      <div className="dependency-graph" data-testid="react-flow">
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          onNodesChange={handleNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClickHandler}
          onNodeContextMenu={onNodeContextMenu}
          onNodeDrag={onNodeDragStart}
          onNodeDragStop={onNodeDragEnd}
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

      {/* Context Menu */}
      {contextMenu.visible && (
        <div
          className="context-menu"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <div
            className="context-menu-item"
            onMouseDown={() => {
              console.log('Metadata item mouseDown');
              handleViewMetadata(contextMenu.nodeId!);
            }}
          >
            📝 View/Edit Metadata
          </div>
          <div
            className="context-menu-item delete"
            onMouseDown={() => {
              console.log('Delete item mouseDown');
              handleDeleteNode(contextMenu.nodeId!);
            }}
          >
            🗑️ Delete Node
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm.visible && (
        <>
          {console.log('Rendering delete confirm dialog for:', deleteConfirm.nodeId)}
          <div className="modal-backdrop" onClick={(e) => {
            if (e.target === e.currentTarget) {
              setDeleteConfirm(prev => ({ ...prev, visible: false }));
            }
          }}>
            <div className="modal-content">
              <div className="modal-header">
                <h3>Confirm Delete</h3>
                <button className="close-btn" onClick={() => setDeleteConfirm(prev => ({ ...prev, visible: false }))}>
                  ×
                </button>
              </div>
              <div className="project-form">
                <p>
                  Are you sure you want to delete "<strong>{deleteConfirm.nodeName}</strong>"? This action cannot be undone.
                </p>
                <div className="form-actions">
                  <button
                    className="cancel-btn"
                    onClick={() => setDeleteConfirm(prev => ({ ...prev, visible: false }))}
                  >
                    Cancel
                  </button>
                  <button
                    className="submit-btn"
                    onClick={confirmDelete}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Metadata Dialog */}
      {metadataDialog.visible && metadataDialog.nodeData && (
        <>
          {console.log('Rendering metadata dialog for:', metadataDialog.nodeId)}
          <div className="modal-backdrop" onClick={(e) => {
            if (e.target === e.currentTarget) {
              setMetadataDialog(prev => ({ ...prev, visible: false }));
            }
          }}>
            <div className="modal-content">
              <div className="modal-header">
                <h3>Node Metadata: {metadataDialog.nodeData.name}</h3>
                <button className="close-btn" onClick={() => setMetadataDialog(prev => ({ ...prev, visible: false }))}>
                  ×
                </button>
              </div>
                <div className="project-form">
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ margin: '0 0 12px 0', color: '#555', fontSize: '14px' }}>Current Information</h4>
                    <div style={{ backgroundColor: '#f8f9fa', padding: '16px', borderRadius: '4px', fontSize: '13px' }}>
                      <div><strong>ID:</strong> {metadataDialog.nodeData.id}</div>
                      <div><strong>Name:</strong> {metadataDialog.nodeData.name}</div>
                      <div><strong>Type:</strong> {metadataDialog.nodeData.type}</div>
                      <div><strong>Path:</strong> {metadataDialog.nodeData.path}</div>
                      <div><strong>Source Type:</strong> {metadataDialog.nodeData.source_type}</div>
                      <div><strong>Confidence:</strong> {Math.round((metadataDialog.nodeData.confidence || 0) * 100)}%</div>
                      {metadataDialog.nodeData.last_updated && (
                        <div><strong>Last Updated:</strong> {new Date(metadataDialog.nodeData.last_updated).toLocaleString()}</div>
                      )}
                    </div>
                  </div>
                  
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ margin: '0 0 12px 0', color: '#555', fontSize: '14px' }}>Comments</h4>
                    <textarea
                      value={editingMetadata}
                      onChange={(e) => {
                        setEditingMetadata(e.target.value);
                        setHasUnsavedChanges(true);
                      }}
                      placeholder="Add comments about this node..."
                      style={{
                        width: '100%',
                        minHeight: '100px',
                        padding: '12px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '14px',
                        fontFamily: 'monospace',
                        resize: 'vertical'
                      }}
                    />
                  </div>
                  
                  <div className="form-actions">
                    <button
                      className="cancel-btn"
                      onClick={() => {
                        setMetadataDialog(prev => ({ ...prev, visible: false }));
                        setEditingMetadata('');
                        setHasUnsavedChanges(false);
                      }}
                    >
                      Close
                    </button>
                    <button
                      className="submit-btn"
                      disabled={!hasUnsavedChanges}
                      onClick={() => {
                        updateMetadata(metadataDialog.nodeId);
                      }}
                      style={{
                        opacity: hasUnsavedChanges ? 1 : 0.6,
                        cursor: hasUnsavedChanges ? 'pointer' : 'not-allowed'
                      }}
                    >
                      Save
                    </button>
                  </div>
                </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}

function getNodeIcon(type: string): string {
  const icons: Record<string, string> = {
    db_table: '🗄️',
    repo: '📁',
    file: '📄',
    api_endpoint: '🔌',
    uploaded_file: '📎',
  };
  return icons[type] || '📦';
}

function getNodeColor(type: string, confidence: number): string {
  const baseColors: Record<string, string> = {
    db_table: '#e74c3c',
    repo: '#3498db',
    file: '#f39c12',
    api_endpoint: '#9b59b6',
    uploaded_file: '#27ae60',
  };

  const opacity = 0.3 + (confidence * 0.7);
  const baseColor = baseColors[type] || '#95a5a6';

  // Convert hex to rgba with opacity
  const hex = baseColor.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

function getEdgeColor(type: string, confidence: number): string {
  if (type === 'literal') return '#e74c3c';
  if (type === 'semantic') return '#f39c12';
  if (type === 'potential') return '#95a5a6';
  return '#7f8c8d';
}

export default DependencyGraph;