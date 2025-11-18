import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Settings from '../src/pages/Settings';
import * as apiModule from '../src/services/api';

// Mock the API
vi.mock('../src/services/api', () => ({
  api: {
    getClients: vi.fn(),
    getClient: vi.fn(),
    updateClient: vi.fn()
  }
}));

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state initially', () => {
    vi.mocked(apiModule.api.getClients).mockReturnValue(new Promise(() => {}));

    render(<Settings />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should fetch and display clients', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { client_id: 'client2', friendly_name: 'Bedroom', daily_limit: 5, created_at: '2024-01-02', updated_at: '2024-01-02' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
      expect(screen.getByText('Bedroom')).toBeInTheDocument();
    });
  });

  it('should have a Client Settings heading', async () => {
    vi.mocked(apiModule.api.getClients).mockResolvedValue([]);

    render(<Settings />);

    expect(screen.getByRole('heading', { name: /client settings/i })).toBeInTheDocument();
  });

  it('should display error message when API call fails', async () => {
    vi.mocked(apiModule.api.getClients).mockRejectedValue(
      new Error('Failed to fetch clients')
    );

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('should show client details when client is selected', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByText(/client id/i)).toBeInTheDocument();
      expect(screen.getByDisplayValue('Living Room')).toBeInTheDocument();
      expect(screen.getByDisplayValue('3')).toBeInTheDocument();
    });
  });

  it('should display Save button when client is selected', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });
  });

  it('should allow editing friendly name', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      const input = screen.getByDisplayValue('Living Room');
      expect(input).toBeInTheDocument();
    });

    const input = screen.getByDisplayValue('Living Room') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'New Name' } });

    expect(input.value).toBe('New Name');
  });

  it('should allow editing daily limit', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      const input = screen.getByDisplayValue('3');
      expect(input).toBeInTheDocument();
    });

    const input = screen.getByDisplayValue('3') as HTMLInputElement;
    fireEvent.change(input, { target: { value: '5' } });

    expect(input.value).toBe('5');
  });

  it('should call updateClient when Save button is clicked', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const updatedClient = {
      client_id: 'client1',
      friendly_name: 'New Name',
      daily_limit: 5,
      created_at: '2024-01-01',
      updated_at: '2024-01-02'
    };

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.updateClient).mockResolvedValue(updatedClient);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Living Room')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Living Room');
    fireEvent.change(nameInput, { target: { value: 'New Name' } });

    const limitInput = screen.getByDisplayValue('3');
    fireEvent.change(limitInput, { target: { value: '5' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(apiModule.api.updateClient).toHaveBeenCalledWith('client1', {
        friendly_name: 'New Name',
        daily_limit: 5
      });
    });
  });

  it('should show success message after saving', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const updatedClient = {
      client_id: 'client1',
      friendly_name: 'New Name',
      daily_limit: 5,
      created_at: '2024-01-01',
      updated_at: '2024-01-02'
    };

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.updateClient).mockResolvedValue(updatedClient);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Living Room')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Living Room');
    fireEvent.change(nameInput, { target: { value: 'New Name' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/saved successfully/i)).toBeInTheDocument();
    });
  });

  it('should disable save button while saving', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const updatedClient = {
      client_id: 'client1',
      friendly_name: 'New Name',
      daily_limit: 5,
      created_at: '2024-01-01',
      updated_at: '2024-01-02'
    };

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.updateClient).mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve(updatedClient), 100))
    );

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Living Room')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Living Room');
    fireEvent.change(nameInput, { target: { value: 'New Name' } });

    const saveButton = screen.getByRole('button', { name: /save/i });
    fireEvent.click(saveButton);

    // Button should be disabled during save
    expect(saveButton).toBeDisabled();
  });

  it('should display daily limit label', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);

    render(<Settings />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByText(/daily limit/i)).toBeInTheDocument();
    });
  });
});
