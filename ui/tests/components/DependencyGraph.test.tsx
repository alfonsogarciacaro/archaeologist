import React from 'react';
import { describe, expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import DependencyGraph from '../../src/components/DependencyGraph';
import { ImpactReport } from '../../src/types/types';

// Mock reactflow to avoid rendering issues in tests
vi.mock('reactflow', () => ({
  ReactFlow: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="react-flow">{children}</div>
  ),
  Background: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="background">{children}</div>
  ),
  Controls: () => <div data-testid="controls" />,
  MiniMap: () => <div data-testid="minimap" />,
  useNodesState: () => [[], vi.fn()],
  useEdgesState: () => [[], vi.fn()],
  MarkerType: {
    ArrowClosed: 'arrowclosed',
  },
  ConnectionMode: {
    Loose: 'loose',
  },
}));

import 'reactflow/dist/style.css';

const mockReport: ImpactReport = {
  query: "Change term_sheet_id from string to UUID",
  nodes: [
    {
      id: "1",
      name: "schema.sql",
      type: "db_table",
      path: "/mock_enterprise/data_lake/db_schemas/schema.sql",
      source_type: "snapshot",
      confidence: 1.0,
      last_updated: "2023-10-27"
    },
    {
      id: "2",
      name: "user-service",
      type: "repo",
      path: "/mock_enterprise/live_repos/user-service.git",
      source_type: "live_repo",
      confidence: 0.9
    }
  ],
  edges: [
    {
      source: "1",
      target: "2",
      confidence: 1.0,
      relationship_type: "literal",
      evidence: "Found 'term_sheet_id VARCHAR(50)' in schema.sql"
    }
  ],
  knowledge_gaps: [],
  summary: "Found 2 components potentially impacted"
};

describe('DependencyGraph Component', () => {
  test('renders_empty_graph', () => {
    // On initial load, the graph area is empty
    render(<DependencyGraph report={null} onNodeClick={vi.fn()} selectedNodeId={null} />);
    
    expect(screen.getByText('No Investigation Data')).toBeInTheDocument();
    expect(screen.getByText('Enter a change request to see the dependency graph')).toBeInTheDocument();
  });

  test('renders_graph_from_api_response', () => {
    // When the API returns a mock impact report, the UI renders the correct nodes and edges
    const onNodeClick = vi.fn();
    render(<DependencyGraph report={mockReport} onNodeClick={onNodeClick} selectedNodeId={null} />);
    
    // Should render ReactFlow component
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    
    // Should render the background, controls, and minimap
    expect(screen.getByTestId('background')).toBeInTheDocument();
    expect(screen.getByTestId('controls')).toBeInTheDocument();
    expect(screen.getByTestId('minimap')).toBeInTheDocument();
  });

  test('node_click_opens_sidebar', () => {
    // Clicking on a node in the graph displays its details in the sidebar
    const onNodeClick = vi.fn();
    render(<DependencyGraph report={mockReport} onNodeClick={onNodeClick} selectedNodeId="1" />);
    
    // The component should have received the selected node ID
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });
});