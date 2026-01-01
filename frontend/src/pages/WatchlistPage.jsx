import React, { useState, useEffect } from 'react';
import { watchlistAPI } from '../services/api';
import { UserPlus, Search, AlertCircle, Trash2, Eye } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Alert from '../components/common/Alert';
import EnrollmentForm from '../components/watchlist/EnrollmentForm'; // Import the form

const WatchlistPage = () => {
  const [persons, setPersons] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showEnrollModal, setShowEnrollModal] = useState(false); // State for modal

  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = async () => {
    try {
      const response = await watchlistAPI.getAll();
      setPersons(response.data);
    } catch (error) {
      setError('Failed to load watchlist');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnrollPerson = async (formData) => {
    try {
      await watchlistAPI.create(formData);
      loadWatchlist();
      setShowEnrollModal(false);
    } catch (err) {
      setError('Failed to enroll person. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this person from watchlist?")) return;
    try {
      await watchlistAPI.delete(id);
      loadWatchlist();
    } catch (err) {
      setError("Failed to delete person");
    }
  };

  const filteredPersons = persons.filter(person => 
    person.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.person_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRiskColor = (level) => {
    const map = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return map[level] || map.low;
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Watchlist Management</h1>
        <button 
          onClick={() => setShowEnrollModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors shadow-sm"
        >
          <UserPlus size={20} />
          Add Person
        </button>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError('')} />}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Search Bar */}
        <div className="p-4 border-b border-gray-100">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Search by name or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">Person</th>
                <th className="px-6 py-3">Category</th>
                <th className="px-6 py-3">Risk Level</th>
                <th className="px-6 py-3">Last Seen</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredPersons.map((person) => (
                <tr key={person.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 flex-shrink-0 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                        {person.name.charAt(0)}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{person.name}</div>
                        <div className="text-xs text-gray-500">ID: {person.person_id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 capitalize">
                      {person.category.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskColor(person.risk_level)} uppercase`}>
                      {person.risk_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {person.last_seen_at ? new Date(person.last_seen_at).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-gray-400 hover:text-blue-600 mr-3">
                      <Eye size={18} />
                    </button>
                    <button 
                      onClick={() => handleDelete(person.id)}
                      className="text-gray-400 hover:text-red-600"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filteredPersons.length === 0 && (
            <div className="text-center py-12">
              <AlertCircle className="h-10 w-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No persons found matching your search</p>
            </div>
          )}
        </div>
      </div>

      {/* Render Modal */}
      {showEnrollModal && (
        <EnrollmentForm
          onClose={() => setShowEnrollModal(false)}
          onSubmit={handleEnrollPerson}
        />
      )}
    </div>
  );
};

export default WatchlistPage;