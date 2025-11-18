import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ApiClient } from '../src/services/api';

// Mock fetch globally
global.fetch = vi.fn();

describe('ApiClient', () => {
  let api: ApiClient;
  const mockFetch = global.fetch as ReturnType<typeof vi.fn>;

  beforeEach(() => {
    api = new ApiClient('http://localhost:8000');
    mockFetch.mockClear();
  });

  describe('getSystemStats', () => {
    it('should fetch system statistics', async () => {
      const mockStats = {
        total_videos: 10,
        regular_videos: 8,
        placeholder_videos: 2,
        total_clients: 3,
        total_plays: 50,
        plays_today: 5
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      } as Response);

      const result = await api.getSystemStats();

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/stats', undefined);
      expect(result).toEqual(mockStats);
    });

    it('should throw error on fetch failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      } as Response);

      await expect(api.getSystemStats()).rejects.toThrow('HTTP error! status: 500');
    });
  });

  describe('getClientStats', () => {
    it('should fetch client statistics', async () => {
      const mockClientStats = {
        client_id: 'client1',
        friendly_name: 'Client 1',
        daily_limit: 3,
        plays_today: 2,
        plays_remaining: 1,
        total_plays: 20,
        queue_size: 3,
        recent_plays: []
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockClientStats
      } as Response);

      const result = await api.getClientStats('client1');

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/stats/client/client1', undefined);
      expect(result).toEqual(mockClientStats);
    });

    it('should throw 404 error for non-existent client', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      } as Response);

      await expect(api.getClientStats('nonexistent')).rejects.toThrow('HTTP error! status: 404');
    });
  });

  describe('getVideos', () => {
    it('should fetch all videos', async () => {
      const mockVideos = [
        { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false },
        { id: 2, title: 'Video 2', path: 'video2.mp4', is_placeholder: false }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockVideos
      } as Response);

      const result = await api.getVideos();

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/videos', undefined);
      expect(result).toEqual(mockVideos);
    });

    it('should fetch videos with filter', async () => {
      const mockVideos = [
        { id: 1, title: 'Video 1', path: 'video1.mp4', is_placeholder: false }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockVideos
      } as Response);

      const result = await api.getVideos({ is_placeholder: false });

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/videos?is_placeholder=false', undefined);
      expect(result).toEqual(mockVideos);
    });
  });

  describe('scanVideos', () => {
    it('should trigger video scan', async () => {
      const mockScanResult = {
        added: 5,
        skipped: 2,
        total: 7
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockScanResult
      } as Response);

      const result = await api.scanVideos();

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/videos/scan', {
        method: 'POST'
      });
      expect(result).toEqual(mockScanResult);
    });
  });

  describe('getClients', () => {
    it('should fetch all clients', async () => {
      const mockClients = [
        { client_id: 'client1', friendly_name: 'Client 1', daily_limit: 3 },
        { client_id: 'client2', friendly_name: 'Client 2', daily_limit: 5 }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockClients
      } as Response);

      const result = await api.getClients();

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/clients', undefined);
      expect(result).toEqual(mockClients);
    });
  });

  describe('getClient', () => {
    it('should fetch a specific client', async () => {
      const mockClient = {
        client_id: 'client1',
        friendly_name: 'Client 1',
        daily_limit: 3,
        tag_filters: null
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockClient
      } as Response);

      const result = await api.getClient('client1');

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/clients/client1', undefined);
      expect(result).toEqual(mockClient);
    });
  });

  describe('createClient', () => {
    it('should create a new client', async () => {
      const newClient = {
        client_id: 'new_client',
        friendly_name: 'New Client',
        daily_limit: 3
      };

      const mockResponse = { ...newClient, tag_filters: null };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response);

      const result = await api.createClient(newClient);

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newClient)
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('updateClient', () => {
    it('should update an existing client', async () => {
      const updates = {
        friendly_name: 'Updated Name',
        daily_limit: 5
      };

      const mockResponse = {
        client_id: 'client1',
        friendly_name: 'Updated Name',
        daily_limit: 5,
        tag_filters: null
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response);

      const result = await api.updateClient('client1', updates);

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/clients/client1', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getQueue', () => {
    it('should fetch client queue', async () => {
      const mockQueue = [
        { id: 1, video_id: 1, position: 1, video: { title: 'Video 1' } },
        { id: 2, video_id: 2, position: 2, video: { title: 'Video 2' } }
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockQueue
      } as Response);

      const result = await api.getQueue('client1');

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/queue/client1', undefined);
      expect(result).toEqual(mockQueue);
    });
  });

  describe('addToQueue', () => {
    it('should add videos to queue', async () => {
      const videoIds = [1, 2, 3];
      const mockResponse = {
        added: 3,
        total_in_queue: 3
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response);

      const result = await api.addToQueue('client1', videoIds);

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/queue/client1', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_ids: videoIds })
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('removeFromQueue', () => {
    it('should remove item from queue', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Queue item removed' })
      } as Response);

      await api.removeFromQueue('client1', 1);

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/queue/client1/1', expect.objectContaining({
        method: 'DELETE'
      }));
    });
  });

  describe('clearQueue', () => {
    it('should clear entire queue', async () => {
      const mockResponse = { removed: 3 };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response);

      const result = await api.clearQueue('client1');

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/queue/client1/clear', {
        method: 'POST'
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe('reorderQueue', () => {
    it('should reorder queue items', async () => {
      const queueIds = [3, 1, 2];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Queue reordered' })
      } as Response);

      await api.reorderQueue('client1', queueIds);

      expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/queue/client1/reorder', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ queue_ids: queueIds })
      });
    });
  });
});
