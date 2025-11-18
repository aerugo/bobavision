/**
 * API Client for communicating with BobaVision backend
 */

// Type definitions
export interface SystemStats {
  total_videos: number;
  regular_videos: number;
  placeholder_videos: number;
  total_clients: number;
  total_plays: number;
  plays_today: number;
}

export interface RecentPlay {
  video_id: number;
  video_title: string;
  played_at: string;
  is_placeholder: boolean;
}

export interface ClientStats {
  client_id: string;
  friendly_name: string;
  daily_limit: number;
  plays_today: number;
  plays_remaining: number;
  total_plays: number;
  queue_size: number;
  recent_plays: RecentPlay[];
}

export interface Video {
  id: number;
  path: string;
  title: string;
  tags?: string | null;
  is_placeholder: boolean;
  duration_seconds?: number | null;
  created_at: string;
}

export interface Client {
  client_id: string;
  friendly_name: string;
  daily_limit: number;
  tag_filters?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface QueueItem {
  id: number;
  video_id: number;
  position: number;
  created_at: string;
  video: {
    id: number;
    title: string;
    path: string;
    is_placeholder: boolean;
  };
}

export interface ScanResult {
  added: number;
  skipped: number;
  total: number;
}

export interface AddToQueueResponse {
  added: number;
  total_in_queue: number;
}

export interface ClearQueueResponse {
  removed: number;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, options);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Statistics endpoints
  async getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>('/api/stats');
  }

  async getClientStats(clientId: string): Promise<ClientStats> {
    return this.request<ClientStats>(`/api/stats/client/${clientId}`);
  }

  // Video endpoints
  async getVideos(filters?: { is_placeholder?: boolean; tags?: string }): Promise<Video[]> {
    const queryParams = new URLSearchParams();
    if (filters?.is_placeholder !== undefined) {
      queryParams.append('is_placeholder', String(filters.is_placeholder));
    }
    if (filters?.tags) {
      queryParams.append('tags', filters.tags);
    }

    const query = queryParams.toString();
    const endpoint = query ? `/api/videos?${query}` : '/api/videos';

    return this.request<Video[]>(endpoint);
  }

  async scanVideos(): Promise<ScanResult> {
    return this.request<ScanResult>('/api/videos/scan', {
      method: 'POST'
    });
  }

  // Client endpoints
  async getClients(): Promise<Client[]> {
    return this.request<Client[]>('/api/clients');
  }

  async getClient(clientId: string): Promise<Client> {
    return this.request<Client>(`/api/clients/${clientId}`);
  }

  async createClient(data: {
    client_id: string;
    friendly_name: string;
    daily_limit: number;
    tag_filters?: string;
  }): Promise<Client> {
    return this.request<Client>('/api/clients', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  }

  async updateClient(
    clientId: string,
    data: {
      friendly_name?: string;
      daily_limit?: number;
      tag_filters?: string;
    }
  ): Promise<Client> {
    return this.request<Client>(`/api/clients/${clientId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  }

  // Queue endpoints
  async getQueue(clientId: string): Promise<QueueItem[]> {
    return this.request<QueueItem[]>(`/api/queue/${clientId}`);
  }

  async addToQueue(clientId: string, videoIds: number[]): Promise<AddToQueueResponse> {
    return this.request<AddToQueueResponse>(`/api/queue/${clientId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ video_ids: videoIds })
    });
  }

  async removeFromQueue(clientId: string, queueId: number): Promise<void> {
    await this.request(`/api/queue/${clientId}/${queueId}`, {
      method: 'DELETE'
    });
  }

  async clearQueue(clientId: string): Promise<ClearQueueResponse> {
    return this.request<ClearQueueResponse>(`/api/queue/${clientId}/clear`, {
      method: 'POST'
    });
  }

  async reorderQueue(clientId: string, queueIds: number[]): Promise<void> {
    await this.request(`/api/queue/${clientId}/reorder`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ queue_ids: queueIds })
    });
  }
}

// Export a default instance
export const api = new ApiClient();
