import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import Queue from '../src/pages/Queue';
import * as apiModule from '../src/services/api';

// Mock the API
vi.mock('../src/services/api', () => ({
  api: {
    getClients: vi.fn(),
    getQueue: vi.fn(),
    getVideos: vi.fn(),
    addToQueue: vi.fn(),
    removeFromQueue: vi.fn(),
    clearQueue: vi.fn()
  }
}));

describe('Queue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state initially', () => {
    vi.mocked(apiModule.api.getClients).mockReturnValue(new Promise(() => {}));

    render(<Queue />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should fetch and display clients', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { client_id: 'client2', friendly_name: 'Bedroom', daily_limit: 5, created_at: '2024-01-02', updated_at: '2024-01-02' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
      expect(screen.getByText('Bedroom')).toBeInTheDocument();
    });
  });

  it('should have a Queue Management heading', async () => {
    vi.mocked(apiModule.api.getClients).mockResolvedValue([]);

    render(<Queue />);

    expect(screen.getByRole('heading', { name: /queue management/i })).toBeInTheDocument();
  });

  it('should display error message when API call fails', async () => {
    vi.mocked(apiModule.api.getClients).mockRejectedValue(
      new Error('Failed to fetch clients')
    );

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('should load queue when client is selected', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockQueue = [
      {
        id: 1,
        video_id: 1,
        position: 1,
        created_at: '2024-01-01',
        video: { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false }
      },
      {
        id: 2,
        video_id: 2,
        position: 2,
        created_at: '2024-01-02',
        video: { id: 2, title: 'Video 2', path: 'video2.mp4', is_placeholder: false }
      }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue(mockQueue);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(apiModule.api.getQueue).toHaveBeenCalledWith('client1');
      expect(screen.getByText('Video 1')).toBeInTheDocument();
      expect(screen.getByText('Video 2')).toBeInTheDocument();
    });
  });

  it('should display Add Videos button when client is selected', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue([]);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add videos/i })).toBeInTheDocument();
    });
  });

  it('should display Clear Queue button when queue has items', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockQueue = [
      {
        id: 1,
        video_id: 1,
        position: 1,
        created_at: '2024-01-01',
        video: { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false }
      }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue(mockQueue);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /clear queue/i })).toBeInTheDocument();
    });
  });

  it('should show remove button for each queue item', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockQueue = [
      {
        id: 1,
        video_id: 1,
        position: 1,
        created_at: '2024-01-01',
        video: { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false }
      },
      {
        id: 2,
        video_id: 2,
        position: 2,
        created_at: '2024-01-02',
        video: { id: 2, title: 'Video 2', path: 'video2.mp4', is_placeholder: false }
      }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue(mockQueue);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      expect(removeButtons.length).toBe(2);
    });
  });

  it('should call removeFromQueue when remove button is clicked', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockQueue = [
      {
        id: 1,
        video_id: 1,
        position: 1,
        created_at: '2024-01-01',
        video: { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false }
      }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue(mockQueue);
    vi.mocked(apiModule.api.removeFromQueue).mockResolvedValue();

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByText('Video 1')).toBeInTheDocument();
    });

    const removeButton = screen.getByRole('button', { name: /remove/i });
    fireEvent.click(removeButton);

    await waitFor(() => {
      expect(apiModule.api.removeFromQueue).toHaveBeenCalledWith('client1', 1);
    });
  });

  it('should call clearQueue when Clear Queue button is clicked', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockQueue = [
      {
        id: 1,
        video_id: 1,
        position: 1,
        created_at: '2024-01-01',
        video: { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false }
      }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue(mockQueue);
    vi.mocked(apiModule.api.clearQueue).mockResolvedValue({ removed: 1 });

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /clear queue/i })).toBeInTheDocument();
    });

    const clearButton = screen.getByRole('button', { name: /clear queue/i });
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(apiModule.api.clearQueue).toHaveBeenCalledWith('client1');
    });
  });

  it('should show empty state when queue is empty', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue([]);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByText(/queue is empty/i)).toBeInTheDocument();
    });
  });

  it('should display queue size', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockQueue = [
      {
        id: 1,
        video_id: 1,
        position: 1,
        created_at: '2024-01-01',
        video: { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false }
      },
      {
        id: 2,
        video_id: 2,
        position: 2,
        created_at: '2024-01-02',
        video: { id: 2, title: 'Video 2', path: 'video2.mp4', is_placeholder: false }
      }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue(mockQueue);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByText(/2 videos in queue/i)).toBeInTheDocument();
    });
  });

  it('should open video selection modal when Add Videos button is clicked', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockVideos = [
      { id: 1, title: 'Big Buck Bunny', path: 'BigBuckBunny.mp4', is_placeholder: false, created_at: '2024-01-01' },
      { id: 2, title: 'Elephant Dream', path: 'ElephantsDream.mp4', is_placeholder: false, created_at: '2024-01-02' }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue).mockResolvedValue([]);
    vi.mocked(apiModule.api.getVideos).mockResolvedValue(mockVideos);

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add videos/i })).toBeInTheDocument();
    });

    const addVideosButton = screen.getByRole('button', { name: /add videos/i });
    fireEvent.click(addVideosButton);

    await waitFor(() => {
      expect(apiModule.api.getVideos).toHaveBeenCalled();
      expect(screen.getByText('Big Buck Bunny')).toBeInTheDocument();
      expect(screen.getByText('Elephant Dream')).toBeInTheDocument();
    });
  });

  it('should add selected videos to queue when confirmed', async () => {
    const mockClients = [
      { client_id: 'client1', friendly_name: 'Living Room', daily_limit: 3, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ];
    const mockVideos = [
      { id: 1, title: 'Big Buck Bunny', path: 'BigBuckBunny.mp4', is_placeholder: false, created_at: '2024-01-01' }
    ];
    const mockQueue = [
      {
        id: 1,
        video_id: 1,
        position: 1,
        created_at: '2024-01-01',
        video: { id: 1, title: 'Big Buck Bunny', path: 'BigBuckBunny.mp4', is_placeholder: false }
      }
    ];

    vi.mocked(apiModule.api.getClients).mockResolvedValue(mockClients);
    vi.mocked(apiModule.api.getQueue)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(mockQueue);
    vi.mocked(apiModule.api.getVideos).mockResolvedValue(mockVideos);
    vi.mocked(apiModule.api.addToQueue).mockResolvedValue({ added: 1, total_in_queue: 1 });

    render(<Queue />);

    await waitFor(() => {
      expect(screen.getByText('Living Room')).toBeInTheDocument();
    });

    const clientButton = screen.getByText('Living Room');
    fireEvent.click(clientButton);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add videos/i })).toBeInTheDocument();
    });

    const addVideosButton = screen.getByRole('button', { name: /add videos/i });
    fireEvent.click(addVideosButton);

    await waitFor(() => {
      expect(screen.getByText('Big Buck Bunny')).toBeInTheDocument();
    });

    // Select the video (assuming checkbox interface)
    const videoCheckbox = screen.getByRole('checkbox', { name: /big buck bunny/i });
    fireEvent.click(videoCheckbox);

    // Click the Add button in the modal
    const modalAddButton = screen.getByRole('button', { name: /^add$/i });
    fireEvent.click(modalAddButton);

    await waitFor(() => {
      expect(apiModule.api.addToQueue).toHaveBeenCalledWith('client1', [1]);
      expect(apiModule.api.getQueue).toHaveBeenCalledTimes(2); // Once on client select, once after adding
    });
  });
});
