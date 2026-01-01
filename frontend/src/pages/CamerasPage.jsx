import React, { useState, useEffect } from 'react';
import { cameraAPI } from '../services/api';
import { Video, VideoOff, Play, Pause, Plus, Trash2 } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Alert from '../components/common/Alert';
import CameraForm from '../components/camera/CameraForm'; // Import the form

const CamerasPage = () => {
  const [cameras, setCameras] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      const response = await cameraAPI.getAll();
      setCameras(response.data);
    } catch (error) {
      setError('Failed to load cameras');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCamera = async (cameraData) => {
    try {
      await cameraAPI.create(cameraData);
      loadCameras(); // Refresh list
      setShowAddModal(false);
    } catch (err) {
      setError('Failed to add camera. Check if RTSP URL is valid.');
    }
  };

  const handleStartCamera = async (cameraId) => {
    try {
      await cameraAPI.update(cameraId, { is_active: true });
      loadCameras();
    } catch (error) {
      setError('Failed to start camera');
    }
  };

  const handleStopCamera = async (cameraId) => {
    try {
      await cameraAPI.update(cameraId, { is_active: false });
      loadCameras();
    } catch (error) {
      setError('Failed to stop camera');
    }
  };

  const handleDeleteCamera = async (cameraId) => {
    if(!window.confirm("Are you sure you want to delete this camera?")) return;
    try {
      await cameraAPI.delete(cameraId);
      loadCameras();
    } catch (error) {
      setError('Failed to delete camera');
    }
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Cameras</h1>
        <button 
          onClick={() => setShowAddModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors shadow-sm"
        >
          <Plus size={20} />
          Add Camera
        </button>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError('')} />}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cameras.map((camera) => (
          <div key={camera.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
            <div className="aspect-video bg-gray-900 relative flex items-center justify-center group">
              {camera.is_active ? (
                <Video className="h-12 w-12 text-green-500 animate-pulse" />
              ) : (
                <VideoOff className="h-12 w-12 text-gray-700" />
              )}
              
              <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs text-white font-medium ${camera.is_active ? 'bg-green-500' : 'bg-gray-600'}`}>
                {camera.is_active ? 'Streaming' : 'Offline'}
              </div>
            </div>

            <div className="p-4">
              <div className="mb-4">
                <h3 className="font-bold text-gray-800 text-lg">{camera.name}</h3>
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  {camera.location || 'No location set'}
                </p>
              </div>

              <div className="flex gap-2 pt-2 border-t border-gray-100">
                {camera.is_active ? (
                  <button
                    onClick={() => handleStopCamera(camera.id)}
                    className="flex-1 flex items-center justify-center space-x-2 bg-amber-50 text-amber-600 px-3 py-2 rounded hover:bg-amber-100 transition-colors"
                  >
                    <Pause size={16} />
                    <span className="font-medium">Stop</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleStartCamera(camera.id)}
                    className="flex-1 flex items-center justify-center space-x-2 bg-green-50 text-green-600 px-3 py-2 rounded hover:bg-green-100 transition-colors"
                  >
                    <Play size={16} />
                    <span className="font-medium">Start</span>
                  </button>
                )}

                <button 
                  onClick={() => handleDeleteCamera(camera.id)}
                  className="p-2 text-red-500 hover:bg-red-50 rounded transition-colors"
                  title="Delete Camera"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {cameras.length === 0 && (
        <div className="text-center py-16 bg-white rounded-xl border border-dashed border-gray-300">
          <VideoOff className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No cameras added</h3>
          <p className="text-gray-500 mb-6">Add your first camera to start surveillance monitoring</p>
          <button 
            onClick={() => setShowAddModal(true)}
            className="text-blue-600 font-medium hover:text-blue-700 underline"
          >
            Add Camera Now
          </button>
        </div>
      )}

      {/* Render Modal */}
      {showAddModal && (
        <CameraForm 
          onClose={() => setShowAddModal(false)} 
          onSubmit={handleAddCamera} 
        />
      )}
    </div>
  );
};

export default CamerasPage;