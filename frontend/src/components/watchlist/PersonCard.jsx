import React from 'react';
import { User, AlertTriangle, Eye, Edit, Trash2 } from 'lucide-react';

const PersonCard = ({ person, onUpdate, onDelete }) => {
  const getRiskColor = (level) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return colors[person.risk_level] || colors.low;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-gray-400" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{person.name}</h3>
              <p className="text-sm text-gray-500">{person.person_id}</p>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Category</span>
            <span className="text-sm font-medium capitalize">
              {person.category.replace('_', ' ')}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Risk Level</span>
            <span className={`px-2 py-1 text-xs rounded-full ${getRiskColor()}`}>
              {person.risk_level.toUpperCase()}
            </span>
          </div>

          {person.age && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Age</span>
              <span className="text-sm font-medium">{person.age}</span>
            </div>
          )}

          {person.last_seen_at && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Last Seen</span>
              <span className="text-sm font-medium">
                {new Date(person.last_seen_at).toLocaleDateString()}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Detections</span>
            <span className="text-sm font-medium">{person.total_detections}</span>
          </div>
        </div>
      </div>

      <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-t border-gray-200">
        <button
          onClick={() => onUpdate(person)}
          className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700"
        >
          <Edit className="w-4 h-4" />
          <span>Edit</span>
        </button>
        
        <button
          onClick={() => onDelete(person)}
          className="flex items-center space-x-1 text-sm text-red-600 hover:text-red-700"
        >
          <Trash2 className="w-4 h-4" />
          <span>Delete</span>
        </button>
      </div>
    </div>
  );
};

export default PersonCard;