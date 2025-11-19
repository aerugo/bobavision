import { useEffect, useState } from 'react';
import { api, Client, ClientStats } from '../services/api';

function Settings() {
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [clientStats, setClientStats] = useState<ClientStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingStats, setLoadingStats] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [friendlyName, setFriendlyName] = useState('');
  const [dailyLimit, setDailyLimit] = useState(3);

  // Bonus plays state
  const [bonusPlaysCount, setBonusPlaysCount] = useState(1);
  const [addingBonus, setAddingBonus] = useState(false);

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

  const fetchClientStats = async (clientId: string) => {
    try {
      setLoadingStats(true);
      const stats = await api.getClientStats(clientId);
      setClientStats(stats);
    } catch (err) {
      console.error('Failed to fetch client stats:', err);
      setClientStats(null);
    } finally {
      setLoadingStats(false);
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
    fetchClientStats(client.client_id);
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

      // Reload clients and stats to get updated data
      await fetchClients();
      await fetchClientStats(selectedClientId);
      setSuccessMessage('Settings saved successfully!');
    } catch (err) {
      console.error('Failed to update client:', err);
      setError('Error: Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleAddBonusPlays = async () => {
    if (!selectedClientId || bonusPlaysCount < 1) return;

    try {
      setAddingBonus(true);
      setError(null);
      setSuccessMessage(null);

      await api.addBonusPlays(selectedClientId, bonusPlaysCount);

      // Reload stats to show updated bonus plays
      await fetchClientStats(selectedClientId);
      setSuccessMessage(`Added ${bonusPlaysCount} bonus video${bonusPlaysCount > 1 ? 's' : ''} for today!`);
      setBonusPlaysCount(1); // Reset to default
    } catch (err) {
      console.error('Failed to add bonus plays:', err);
      setError('Error: Failed to add bonus plays');
    } finally {
      setAddingBonus(false);
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

      {/* Stats Display */}
      {selectedClient && clientStats && (
        <div className="mb-6 bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
              Today's Usage
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-sm font-medium text-blue-700">Videos Watched Today</div>
                <div className="mt-1 text-3xl font-bold text-blue-900">{clientStats.plays_today}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-sm font-medium text-green-700">Videos Remaining</div>
                <div className="mt-1 text-3xl font-bold text-green-900">{clientStats.plays_remaining}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm font-medium text-gray-700">Daily Limit</div>
                <div className="mt-1 text-3xl font-bold text-gray-900">{clientStats.daily_limit}</div>
              </div>
            </div>

            {/* Bonus Plays Section */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Add Bonus Videos for Today</h4>
              <p className="text-sm text-gray-600 mb-4">
                Grant extra videos for today only, without changing the daily limit for future days.
              </p>
              <div className="flex items-end gap-3">
                <div className="flex-1 max-w-xs">
                  <label htmlFor="bonus-count" className="block text-sm font-medium text-gray-700 mb-1">
                    Number of bonus videos
                  </label>
                  <input
                    id="bonus-count"
                    type="number"
                    min="1"
                    max="100"
                    value={bonusPlaysCount}
                    onChange={(e) => setBonusPlaysCount(parseInt(e.target.value, 10))}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
                <button
                  onClick={handleAddBonusPlays}
                  disabled={addingBonus || bonusPlaysCount < 1}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {addingBonus ? 'Adding...' : 'Add Bonus Videos'}
                </button>
              </div>
            </div>

            {loadingStats && (
              <div className="mt-2 text-sm text-gray-500">Updating...</div>
            )}
          </div>
        </div>
      )}

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
