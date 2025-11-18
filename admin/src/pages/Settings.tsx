import { useEffect, useState } from 'react';
import { api, Client } from '../services/api';

function Settings() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [friendlyName, setFriendlyName] = useState('');
  const [dailyLimit, setDailyLimit] = useState(3);

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

  useEffect(() => {
    fetchClients();
  }, []);

  const handleSelectClient = (client: Client) => {
    setSelectedClientId(client.client_id);
    setFriendlyName(client.friendly_name);
    setDailyLimit(client.daily_limit);
    setSuccessMessage(null);
    setError(null);
  };

  const handleSave = async () => {
    if (!selectedClientId) return;

    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      await api.updateClient(selectedClientId, {
        friendly_name: friendlyName,
        daily_limit: dailyLimit
      });

      // Reload clients to get updated data
      await fetchClients();
      setSuccessMessage('Settings saved successfully!');
    } catch (err) {
      console.error('Failed to update client:', err);
      setError('Error: Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Client Settings</h2>
        <div className="text-gray-600">Loading clients...</div>
      </div>
    );
  }

  if (error && clients.length === 0) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Client Settings</h2>
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  const selectedClient = clients.find(c => c.client_id === selectedClientId);

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Client Settings</h2>

      {/* Client Selection */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Select a client:</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {clients.map((client) => (
            <button
              key={client.client_id}
              onClick={() => handleSelectClient(client)}
              className={`px-4 py-3 text-left border rounded-md ${
                selectedClientId === client.client_id
                  ? 'bg-blue-50 border-blue-500 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <div className="font-medium">{client.friendly_name}</div>
              <div className="text-sm text-gray-500">
                Limit: {client.daily_limit} videos/day
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Settings Form */}
      {selectedClient && (
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
              Client Configuration
            </h3>

            {/* Success Message */}
            {successMessage && (
              <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4">
                <p className="text-sm text-green-800">{successMessage}</p>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Client ID (Read-only) */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Client ID
              </label>
              <input
                type="text"
                value={selectedClient.client_id}
                disabled
                className="block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              <p className="mt-1 text-sm text-gray-500">
                This identifier cannot be changed
              </p>
            </div>

            {/* Friendly Name */}
            <div className="mb-4">
              <label htmlFor="friendly-name" className="block text-sm font-medium text-gray-700 mb-1">
                Friendly Name
              </label>
              <input
                id="friendly-name"
                type="text"
                value={friendlyName}
                onChange={(e) => setFriendlyName(e.target.value)}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                placeholder="e.g., Living Room, Bedroom"
              />
              <p className="mt-1 text-sm text-gray-500">
                A human-readable name for this client
              </p>
            </div>

            {/* Daily Limit */}
            <div className="mb-6">
              <label htmlFor="daily-limit" className="block text-sm font-medium text-gray-700 mb-1">
                Daily Limit
              </label>
              <input
                id="daily-limit"
                type="number"
                min="1"
                max="100"
                value={dailyLimit}
                onChange={(e) => setDailyLimit(parseInt(e.target.value, 10))}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              <p className="mt-1 text-sm text-gray-500">
                Maximum number of non-placeholder videos per day
              </p>
            </div>

            {/* Save Button */}
            <div>
              <button
                onClick={handleSave}
                disabled={saving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Settings;
