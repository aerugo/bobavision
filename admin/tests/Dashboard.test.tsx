import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '../src/pages/Dashboard';
import * as apiModule from '../src/services/api';

// Mock the API
vi.mock('../src/services/api', () => ({
  api: {
    getSystemStats: vi.fn()
  }
}));

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state initially', () => {
    vi.mocked(apiModule.api.getSystemStats).mockReturnValue(new Promise(() => {}));

    render(<Dashboard />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should fetch and display system statistics', async () => {
    const mockStats = {
      total_videos: 10,
      regular_videos: 8,
      placeholder_videos: 2,
      total_clients: 3,
      total_plays: 50,
      plays_today: 5
    };

    vi.mocked(apiModule.api.getSystemStats).mockResolvedValue(mockStats);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument(); // total_videos
      expect(screen.getByText('8')).toBeInTheDocument(); // regular_videos
      expect(screen.getByText('2')).toBeInTheDocument(); // placeholder_videos
      expect(screen.getByText('3')).toBeInTheDocument(); // total_clients
      expect(screen.getByText('50')).toBeInTheDocument(); // total_plays
      expect(screen.getByText('5')).toBeInTheDocument(); // plays_today
    });
  });

  it('should display stat labels', async () => {
    const mockStats = {
      total_videos: 10,
      regular_videos: 8,
      placeholder_videos: 2,
      total_clients: 3,
      total_plays: 50,
      plays_today: 5
    };

    vi.mocked(apiModule.api.getSystemStats).mockResolvedValue(mockStats);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/total videos/i)).toBeInTheDocument();
      expect(screen.getByText(/regular videos/i)).toBeInTheDocument();
      expect(screen.getByText(/placeholder videos/i)).toBeInTheDocument();
      expect(screen.getByText(/total clients/i)).toBeInTheDocument();
      expect(screen.getByText(/total plays/i)).toBeInTheDocument();
      expect(screen.getByText(/plays today/i)).toBeInTheDocument();
    });
  });

  it('should display error message when API call fails', async () => {
    vi.mocked(apiModule.api.getSystemStats).mockRejectedValue(
      new Error('Failed to fetch stats')
    );

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('should have a Dashboard heading', async () => {
    const mockStats = {
      total_videos: 10,
      regular_videos: 8,
      placeholder_videos: 2,
      total_clients: 3,
      total_plays: 50,
      plays_today: 5
    };

    vi.mocked(apiModule.api.getSystemStats).mockResolvedValue(mockStats);

    render(<Dashboard />);

    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });

  it('should call getSystemStats on mount', async () => {
    const mockStats = {
      total_videos: 10,
      regular_videos: 8,
      placeholder_videos: 2,
      total_clients: 3,
      total_plays: 50,
      plays_today: 5
    };

    vi.mocked(apiModule.api.getSystemStats).mockResolvedValue(mockStats);

    render(<Dashboard />);

    await waitFor(() => {
      expect(apiModule.api.getSystemStats).toHaveBeenCalledTimes(1);
    });
  });
});
