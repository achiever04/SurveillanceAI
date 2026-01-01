import React, { useState } from 'react';
import { VideoOff, RefreshCw } from 'lucide-react';
import { cameraAPI } from '../../services/api';

const CameraFeed = ({ camera }) => {
  const [error, setError] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Use the backend stream URL (MJPEG)
  // Add a timestamp to prevent browser caching when retrying
  const streamUrl = `${cameraAPI.getStream(camera.id)}?t=${Date.now()}`;

  const handleRetry = () => {
    setError(false);
    setRetryCount(prev => prev + 1);
  };

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center overflow-hidden">
      {!error ? (
        <img
          src={streamUrl}
          alt={`Feed from ${camera.name}`}
          className="w-full h-full object-contain"
          onError={() => setError(true)}
        />
      ) : (
        <div className="text-center text-gray-400 p-4">
          <VideoOff className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm mb-3">Stream unavailable</p>
          <button 
            onClick={handleRetry}
            className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-full text-xs flex items-center gap-2 mx-auto transition-colors"
          >
            <RefreshCw size={12} /> Retry Connection
          </button>
        </div>
      )}

      {/* Live Indicator */}
      {!error && (
        <div className="absolute top-3 right-3 flex items-center gap-2">
          <span className="flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
          </span>
          <span className="text-xs font-bold text-white drop-shadow-md tracking-wider">LIVE AI</span>
        </div>
      )}
    </div>
  );
};

export default CameraFeed;