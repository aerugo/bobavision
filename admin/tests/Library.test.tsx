import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Library from '../src/pages/Library';
import * as apiModule from '../src/services/api';

// Mock the API
vi.mock('../src/services/api', () => ({
  api: {
    getVideos: vi.fn(),
    scanVideos: vi.fn()
  }
}));

describe('Library', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state initially', () => {
    vi.mocked(apiModule.api.getVideos).mockReturnValue(new Promise(() => {}));

    render(<Library />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should fetch and display videos', async () => {
    const mockVideos = [
      { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false, created_at: '2024-01-01' },
      { id: 2, title: 'Video 2', path: 'video2.mp4', is_placeholder: false, created_at: '2024-01-02' },
      { id: 3, title: 'All Done Video', path: 'placeholder.mp4', is_placeholder: true, created_at: '2024-01-03' }
    ];

    vi.mocked(apiModule.api.getVideos).mockResolvedValue(mockVideos);

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByText('Video 1')).toBeInTheDocument();
      expect(screen.getByText('Video 2')).toBeInTheDocument();
      expect(screen.getByText('All Done Video')).toBeInTheDocument();
    });
  });

  it('should have a Library heading', async () => {
    vi.mocked(apiModule.api.getVideos).mockResolvedValue([]);

    render(<Library />);

    expect(screen.getByRole('heading', { name: /video library/i })).toBeInTheDocument();
  });

  it('should display error message when API call fails', async () => {
    vi.mocked(apiModule.api.getVideos).mockRejectedValue(
      new Error('Failed to fetch videos')
    );

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('should show Scan button', async () => {
    vi.mocked(apiModule.api.getVideos).mockResolvedValue([]);

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /scan/i })).toBeInTheDocument();
    });
  });

  it('should trigger scan when Scan button is clicked', async () => {
    const mockScanResult = { added: 5, skipped: 2, total: 7 };

    vi.mocked(apiModule.api.getVideos).mockResolvedValue([]);
    vi.mocked(apiModule.api.scanVideos).mockResolvedValue(mockScanResult);

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /scan/i })).toBeInTheDocument();
    });

    const scanButton = screen.getByRole('button', { name: /scan/i });
    fireEvent.click(scanButton);

    await waitFor(() => {
      expect(apiModule.api.scanVideos).toHaveBeenCalledTimes(1);
    });
  });

  it('should show scan results after scanning', async () => {
    const mockScanResult = { added: 5, skipped: 2, total: 7 };
    const mockVideos = [
      { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false, created_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getVideos).mockResolvedValue(mockVideos);
    vi.mocked(apiModule.api.scanVideos).mockResolvedValue(mockScanResult);

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /scan/i })).toBeInTheDocument();
    });

    const scanButton = screen.getByRole('button', { name: /scan/i });
    fireEvent.click(scanButton);

    await waitFor(() => {
      expect(screen.getByText(/5 videos added/i)).toBeInTheDocument();
    });
  });

  it('should show placeholder badge for placeholder videos', async () => {
    const mockVideos = [
      { id: 1, title: 'Regular Video', path: 'video.mp4', is_placeholder: false, created_at: '2024-01-01' },
      { id: 2, title: 'Placeholder', path: 'placeholder.mp4', is_placeholder: true, created_at: '2024-01-02' }
    ];

    vi.mocked(apiModule.api.getVideos).mockResolvedValue(mockVideos);

    render(<Library />);

    await waitFor(() => {
      const placeholderBadges = screen.getAllByText(/placeholder/i);
      // Should have at least 2: the title "Placeholder" and a badge
      expect(placeholderBadges.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('should display video count', async () => {
    const mockVideos = [
      { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false, created_at: '2024-01-01' },
      { id: 2, title: 'Video 2', path: 'video2.mp4', is_placeholder: false, created_at: '2024-01-02' }
    ];

    vi.mocked(apiModule.api.getVideos).mockResolvedValue(mockVideos);

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByText(/2 videos/i)).toBeInTheDocument();
    });
  });

  it('should disable scan button while scanning', async () => {
    const mockScanResult = { added: 5, skipped: 2, total: 7 };

    vi.mocked(apiModule.api.getVideos).mockResolvedValue([]);
    vi.mocked(apiModule.api.scanVideos).mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve(mockScanResult), 100))
    );

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /scan/i })).toBeInTheDocument();
    });

    const scanButton = screen.getByRole('button', { name: /scan/i });
    fireEvent.click(scanButton);

    // Button should be disabled during scan
    expect(scanButton).toBeDisabled();
  });

  it('should reload videos after successful scan', async () => {
    const mockScanResult = { added: 2, skipped: 0, total: 2 };
    const initialVideos = [
      { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false, created_at: '2024-01-01' }
    ];
    const updatedVideos = [
      { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false, created_at: '2024-01-01' },
      { id: 2, title: 'Video 2', path: 'video2.mp4', is_placeholder: false, created_at: '2024-01-02' }
    ];

    vi.mocked(apiModule.api.getVideos)
      .mockResolvedValueOnce(initialVideos)
      .mockResolvedValueOnce(updatedVideos);
    vi.mocked(apiModule.api.scanVideos).mockResolvedValue(mockScanResult);

    render(<Library />);

    await waitFor(() => {
      expect(screen.getByText('Video 1')).toBeInTheDocument();
    });

    const scanButton = screen.getByRole('button', { name: /scan/i });
    fireEvent.click(scanButton);

    await waitFor(() => {
      expect(apiModule.api.getVideos).toHaveBeenCalledTimes(2);
      expect(screen.getByText('Video 2')).toBeInTheDocument();
    });
  });
});
