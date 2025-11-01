import { beforeEach, describe, expect, test, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Header from '../../src/components/Header';

// Mock fetch for API calls
global.fetch = vi.fn();

describe('Header Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders_header', () => {
    // The header with the search bar is rendered
    render(<Header onInvestigate={vi.fn()} isLoading={false} />);
    
    expect(screen.getByText('Enterprise Code Archaeologist')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter change request (e.g., \'Change term_sheet_id from string to UUID\')')).toBeInTheDocument();
  });

  test('submit_query_calls_api', async () => {
    // Submitting a query triggers a fetch call to the /investigate endpoint
    const mockOnInvestigate = vi.fn();
    render(<Header onInvestigate={mockOnInvestigate} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Enter change request');
    const submitButton = screen.getByRole('button');
    
    await userEvent.type(input, 'Change term_sheet_id from string to UUID');
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnInvestigate).toHaveBeenCalledWith('Change term_sheet_id from string to UUID');
    });
  });

  test('disables input and button when loading', () => {
    render(<Header onInvestigate={vi.fn()} isLoading={true} />);
    
    const input = screen.getByPlaceholderText('Enter change request');
    const submitButton = screen.getByRole('button');
    
    expect(input).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  test('shows loading spinner when loading', () => {
    render(<Header onInvestigate={vi.fn()} isLoading={true} />);
    
    // Check for loading spinner (should be present when loading)
    const loadingIcon = document.querySelector('.loading-icon');
    expect(loadingIcon).toBeInTheDocument();
  });
});