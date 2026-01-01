import React, { useState, useEffect } from 'react';
import { detectionAPI } from '../services/api';
import { FileText, Download, Eye, Shield, Calendar } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';

const EvidencePage = () => {
  const [detections, setDetections] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadEvidence();
  }, []);

  const loadEvidence = async () => {
    try {
      const response = await detectionAPI.getAll({ limit: 50 });
      setDetections(response.data);
    } catch (error) {
      console.error('Failed to load evidence:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Evidence Management</h1>
          <p className="text-sm text-gray-500">Secure storage and retrieval of surveillance evidence</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
          <h2 className="font-semibold text-gray-800 flex items-center gap-2">
            <FileText size={18} />
            Evidence Logs
          </h2>
          <button className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 transition-colors text-gray-700">
            <Download size={16} />
            Export Report
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-4">Event ID</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Source</th>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Verification</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {detections.length > 0 ? (
                detections.map((detection) => (
                  <tr key={detection.id} className="hover:bg-blue-50/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-xs text-blue-600 font-medium">
                      {detection.event_id || `EVT-${detection.id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize border border-blue-200">
                        {detection.detection_type?.replace('_', ' ') || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      Camera {detection.camera_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 flex items-center gap-2">
                      <Calendar size={14} className="text-gray-400" />
                      {new Date(detection.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {detection.blockchain_tx_id ? (
                        <div className="flex items-center gap-1.5 bg-green-50 text-green-700 px-2 py-1 rounded-lg w-fit border border-green-100">
                          <Shield size={14} />
                          <span className="text-xs font-bold">Verified on Chain</span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400 italic">Processing...</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors" title="View Details">
                          <Eye size={18} />
                        </button>
                        <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" title="Download Evidence">
                          <Download size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                    No evidence records found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default EvidencePage;