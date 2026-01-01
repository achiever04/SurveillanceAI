import React, { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';
import { Video, Users, AlertTriangle, CheckCircle } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';

const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await analyticsAPI.getDashboardStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  const statCards = [
    {
      title: 'Active Cameras',
      value: `${stats?.active_cameras || 0} / ${stats?.total_cameras || 0}`,
      icon: Video,
      color: 'blue'
    },
    {
      title: 'Detections (24h)',
      value: stats?.detections_24h || 0,
      icon: AlertTriangle,
      color: 'yellow'
    },
    {
      title: 'Watchlist Persons',
      value: stats?.watchlist_persons || 0,
      icon: Users,
      color: 'purple'
    },
    {
      title: 'Verified Detections',
      value: stats?.total_detections - stats?.unverified_detections || 0,
      icon: CheckCircle,
      color: 'green'
    }
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, index) => {
          const Icon = card.icon;
          const colorClasses = {
            blue: 'bg-blue-100 text-blue-600',
            yellow: 'bg-yellow-100 text-yellow-600',
            purple: 'bg-purple-100 text-purple-600',
            green: 'bg-green-100 text-green-600'
          };

          return (
            <div key={index} className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-gray-500 text-sm font-medium">{card.title}</h3>
                <div className={`p-2 rounded-lg ${colorClasses[card.color]}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <p className="text-2xl font-bold text-gray-800">{card.value}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Recent Detections</h2>
          <div className="text-center py-8 text-gray-500">No recent detections</div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">System Health</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600">Database</span>
              <span className="text-green-600 font-medium text-sm flex items-center">
                <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                Healthy
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600">Blockchain</span>
              <span className="text-green-600 font-medium text-sm flex items-center">
                <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-gray-600">IPFS</span>
              <span className="text-green-600 font-medium text-sm flex items-center">
                <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                Online
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;