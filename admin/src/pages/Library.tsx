import { useEffect, useState } from 'react';
import { api, Video, ScanResult } from '../services/api';

function Library() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);

  const fetchVideos = async () => {
    try {
      setLoading(true);
      const data = await api.getVideos();
      setVideos(data);
      setError(null);
    } catch (err) {
      setError('Error: Failed to load videos');
      console.error('Failed to fetch videos:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleScan = async () => {
    try {
      setScanning(true);
      setScanResult(null);
      const result = await api.scanVideos();
      setScanResult(result);
      // Reload videos after scan
      await fetchVideos();
    } catch (err) {
      console.error('Failed to scan videos:', err);
      setError('Error: Failed to scan videos');
    } finally {
      setScanning(false);
    }
  };

  if (loading && videos.length === 0) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Video Library</h2>
        <div className="text-gray-600">Loading videos...</div>
      </div>
    );
  }

  if (error && videos.length === 0) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Video Library</h2>
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Video Library</h2>
          <p className="text-sm text-gray-600 mt-1">{videos.length} videos</p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {scanning ? 'Scanning...' : 'Scan for New Videos'}
        </button>
      </div>

      {/* Scan Result */}
      {scanResult && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <p className="text-sm text-green-800">
            Scan complete: {scanResult.added} videos added, {scanResult.skipped} skipped, {scanResult.total} total
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Video List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {videos.length === 0 ? (
            <li className="px-6 py-4">
              <p className="text-gray-500 text-center">No videos found. Click "Scan for New Videos" to add videos to the library.</p>
            </li>
          ) : (
            videos.map((video) => (
              <li key={video.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {video.title}
                      </p>
                      {video.is_placeholder && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Placeholder
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{video.path}</p>
                  </div>
                  <div className="text-sm text-gray-500">
                    ID: {video.id}
                  </div>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}

export default Library;
