import { useEffect, useState } from 'react';
import { api, SystemStats } from '../services/api';

interface StatCardProps {
  label: string;
  value: number;
}

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <dt className="text-sm font-medium text-gray-500 truncate">{label}</dt>
        <dd className="mt-1 text-3xl font-semibold text-gray-900">{value}</dd>
      </div>
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true);
        const data = await api.getSystemStats();
        setStats(data);
        setError(null);
      } catch (err) {
        setError('Error: Failed to load statistics');
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>
        <div className="text-gray-600">Loading statistics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      {/* System Overview */}
      <div className="mb-8">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Overview</h3>
        <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard label="Total Videos" value={stats.total_videos} />
          <StatCard label="Regular Videos" value={stats.regular_videos} />
          <StatCard label="Placeholder Videos" value={stats.placeholder_videos} />
        </dl>
      </div>

      {/* Clients & Usage */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Clients & Usage</h3>
        <dl className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard label="Total Clients" value={stats.total_clients} />
          <StatCard label="Total Plays" value={stats.total_plays} />
          <StatCard label="Plays Today" value={stats.plays_today} />
        </dl>
      </div>
    </div>
  );
}

export default Dashboard;
