import { useEffect, useState } from 'react';
import { api, Client, QueueItem } from '../services/api';

function Queue() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [queueLoading, setQueueLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const data = await api.getClients();
      setClients(data);
      setError(null);
    } catch (err) {
      setError('Error: Failed to load clients');
      console.error('Failed to fetch clients:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchQueue = async (clientId: string) => {
    try {
      setQueueLoading(true);
      const data = await api.getQueue(clientId);
      setQueue(data);
      setError(null);
    } catch (err) {
      setError('Error: Failed to load queue');
      console.error('Failed to fetch queue:', err);
    } finally {
      setQueueLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  const handleSelectClient = (clientId: string) => {
    setSelectedClientId(clientId);
    fetchQueue(clientId);
  };

  const handleRemoveFromQueue = async (queueId: number) => {
    if (!selectedClientId) return;

    try {
      await api.removeFromQueue(selectedClientId, queueId);
      // Reload queue
      await fetchQueue(selectedClientId);
    } catch (err) {
      console.error('Failed to remove from queue:', err);
      setError('Error: Failed to remove video from queue');
    }
  };

  const handleClearQueue = async () => {
    if (!selectedClientId) return;

    try {
      await api.clearQueue(selectedClientId);
      // Reload queue
      await fetchQueue(selectedClientId);
    } catch (err) {
      console.error('Failed to clear queue:', err);
      setError('Error: Failed to clear queue');
    }
  };

  if (loading) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Queue Management</h2>
        <div className="text-gray-600">Loading clients...</div>
      </div>
    );
  }

  if (error && clients.length === 0) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Queue Management</h2>
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  const selectedClient = clients.find(c => c.client_id === selectedClientId);

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Queue Management</h2>

      {/* Client Selection */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Select a client:</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {clients.map((client) => (
            <button
              key={client.client_id}
              onClick={() => handleSelectClient(client.client_id)}
              className={`px-4 py-3 text-left border rounded-md ${
                selectedClientId === client.client_id
                  ? 'bg-blue-50 border-blue-500 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <div className="font-medium">{client.friendly_name}</div>
              <div className="text-sm text-gray-500">{client.client_id}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Queue Display */}
      {selectedClient && (
        <div>
          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Queue Header */}
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                Queue for {selectedClient.friendly_name}
              </h3>
              <p className="text-sm text-gray-600 mt-1">{queue.length} videos in queue</p>
            </div>
            <div className="space-x-2">
              <button
                onClick={() => {/* TODO: Implement add videos */}}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Add Videos
              </button>
              {queue.length > 0 && (
                <button
                  onClick={handleClearQueue}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Clear Queue
                </button>
              )}
            </div>
          </div>

          {/* Queue List */}
          {queueLoading ? (
            <div className="text-gray-600">Loading queue...</div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              {queue.length === 0 ? (
                <div className="px-6 py-12 text-center">
                  <p className="text-gray-500">Queue is empty. Add videos to get started.</p>
                </div>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {queue.map((item, index) => (
                    <li key={item.id} className="px-6 py-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center flex-1 min-w-0">
                          <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                            <span className="text-sm font-medium text-gray-600">{index + 1}</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {item.video.title}
                            </p>
                            <p className="text-sm text-gray-500">{item.video.path}</p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemoveFromQueue(item.id)}
                          className="ml-4 inline-flex items-center px-3 py-1 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                          Remove
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Queue;
