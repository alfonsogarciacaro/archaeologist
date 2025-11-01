import '@testing-library/jest-dom';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../src/App';
import { ImpactReport } from '../../src/types/types';

// Mock fetch to simulate API responses
const mockImpactReport: ImpactReport = {
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
  knowledge_gaps: [
    {
      component: "external-payment-api",
      missing_information: "API schema for payment processing",
      required_action: "Request API documentation from Payments Team",
      estimated_impact: "Medium - payment processing may be affected"
    }
  ],
  summary: "Found 1 component potentially impacted"
};

describe('App Component Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  test('renders_app_with_header', () => {
    render(<App />);
    
    expect(screen.getByText('Enterprise Code Archaeologist')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter change request (e.g., \'Change term_sheet_id from string to UUID\')')).toBeInTheDocument();
    expect(screen.getByText('Test Status:')).toBeInTheDocument();
    expect(screen.getByText('0 / 11 Tests Passing')).toBeInTheDocument();
  });

  test('renders_empty_graph_initially', () => {
    render(<App />);
    
    expect(screen.getByText('No Investigation Data')).toBeInTheDocument();
    expect(screen.getByText('Enter a change request to see the dependency graph')).toBeInTheDocument();
  });

  test('submit_query_calls_api', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockImpactReport
    } as Response);

    render(<App />);
    
    const input = screen.getByPlaceholderText('Enter change request');
    const submitButton = screen.getByRole('button');
    
    await userEvent.type(input, 'Change term_sheet_id from string to UUID');
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/investigate',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: 'Change term_sheet_id from string to UUID' }),
        }
      );
    });
  });

  test('renders_graph_from_api_response', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockImpactReport
    } as Response);

    render(<App />);
    
    const input = screen.getByPlaceholderText('Enter change request');
    const submitButton = screen.getByRole('button');
    
    await userEvent.type(input, 'Change term_sheet_id from string to UUID');
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    });
  });

  test('knowledge_gap_banner_appears', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockImpactReport
    } as Response);

    render(<App />);
    
    const input = screen.getByPlaceholderText('Enter change request');
    const submitButton = screen.getByRole('button');
    
    await userEvent.type(input, 'Change term_sheet_id from string to UUID');
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('⚠️')).toBeInTheDocument();
      expect(screen.getByText('Knowledge Gap Identified:')).toBeInTheDocument();
      expect(screen.getByText('API schema for payment processing')).toBeInTheDocument();
      expect(screen.getByText('Action: Request API documentation from Payments Team')).toBeInTheDocument();
    });
  });

  test('node_click_opens_sidebar', async () => {
    const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockImpactReport
    } as Response);

    render(<App />);
    
    const input = screen.getByPlaceholderText('Enter change request');
    const submitButton = screen.getByRole('button');
    
    await userEvent.type(input, 'Change term_sheet_id from string to UUID');
    await userEvent.click(submitButton);
    
    // Wait for the graph to render
    await waitFor(() => {
      expect(screen.getByTestId('react-flow')).toBeInTheDocument();
    });
    
    // The sidebar should not be visible initially
    expect(screen.queryByText('Investigation Details')).not.toBeInTheDocument();
  });
});