import React, { useState } from 'react';
import { VideoOff, RefreshCw } from 'lucide-react';

const CameraFeed = ({ camera }) => {
  const [error, setError] = useState(false);
  const [key, setKey] = useState(0);

  const token = localStorage.getItem('access_token');
  const streamUrl = `http://localhost:8000/api/v1/cameras/${camera.id}/stream?token=${token}&_=${key}`;

  const handleRetry = () => {
    setError(false);
    setKey(prev => prev + 1);
  };

  return (
    <div className="relative w-full h-full bg-black flex items-center justify-center overflow-hidden">
      {!error ? (
        <>
          <img
            key={key}
            src={streamUrl}
            alt="Camera Feed"
            className="w-full h-full object-contain"
            onError={() => {
              console.error(`Stream failed for camera ${camera.id}`);
              setError(true);
            }}
            onLoad={() => console.log(`Stream loaded for camera ${camera.id}`)}
          />
          
          <div className="absolute top-3 right-3 flex items-center gap-2 bg-black/60 px-3 py-1 rounded-full">
            <span className="flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
            </span>
            <span className="text-xs font-bold text-white tracking-wider">LIVE</span>
          </div>
        </>
      ) : (
        <div className="text-center text-gray-400 p-4">
          <VideoOff className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p className="text-sm mb-3">Stream unavailable</p>
          <p className="text-xs mb-3 text-red-400">Check backend logs</p>
          <button 
            onClick={handleRetry}
            className="px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded-full text-xs flex items-center gap-2 mx-auto"
          >
            <RefreshCw size={12} /> Retry
          </button>
        </div>
      )}
    </div>
  );
};

export default CameraFeed;