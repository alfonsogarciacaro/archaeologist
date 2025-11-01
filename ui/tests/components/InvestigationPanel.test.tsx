import { describe, expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import InvestigationPanel from '../../src/components/InvestigationPanel';
import { DependencyNode } from '../../src/types/types';

const mockNode: DependencyNode = {
  id: "1",
  name: "schema.sql",
  type: "db_table",
  path: "/mock_enterprise/data_lake/db_schemas/schema.sql",
  source_type: "snapshot",
  confidence: 1.0,
  last_updated: "2023-10-27"
};

describe('InvestigationPanel Component', () => {
  test('renders_investigation_panel', () => {
    render(<InvestigationPanel node={mockNode} />);
    
    expect(screen.getByText('Investigation Details')).toBeInTheDocument();
    expect(screen.getByText('schema.sql')).toBeInTheDocument();
    expect(screen.getByText('Database Table')).toBeInTheDocument();
  });

  test('displays_node_information_correctly', () => {
    render(<InvestigationPanel node={mockNode} />);
    
    expect(screen.getByText('schema.sql')).toBeInTheDocument();
    expect(screen.getByText('/mock_enterprise/data_lake/db_schemas/schema.sql')).toBeInTheDocument();
    expect(screen.getByText('Snapshot')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('2023-10-27')).toBeInTheDocument();
  });

  test('displays_confidence_level', () => {
    render(<InvestigationPanel node={mockNode} />);
    
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  test('shows_code_evidence', () => {
    render(<InvestigationPanel node={mockNode} />);
    
    expect(screen.getByText('Evidence Found')).toBeInTheDocument();
    expect(screen.getByText(/Found db_table "schema.sql"/)).toBeInTheDocument();
  });

  test('shows_impact_assessment', () => {
    render(<InvestigationPanel node={mockNode} />);
    
    expect(screen.getByText('Impact Assessment')).toBeInTheDocument();
    expect(screen.getByText(/This db_table contains references/)).toBeInTheDocument();
  });

  test('shows_snapshot_warning_for_snapshot_sources', () => {
    render(<InvestigationPanel node={mockNode} />);
    
    expect(screen.getByText('Note:')).toBeInTheDocument();
    expect(screen.getByText(/This is a snapshot source/)).toBeInTheDocument();
  });

  test('hides_snapshot_warning_for_live_repos', () => {
    const liveRepoNode: DependencyNode = {
      ...mockNode,
      source_type: "live_repo",
      type: "repo"
    };
    
    render(<InvestigationPanel node={liveRepoNode} />);
    
    expect(screen.queryByText(/This is a snapshot source/)).not.toBeInTheDocument();
  });
});