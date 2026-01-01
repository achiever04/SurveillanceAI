import React, { useState, useEffect } from 'react';
import { blockchainAPI } from '../services/api';
import { Shield, Search, CheckCircle, Clock, FileText, Link as LinkIcon } from 'lucide-react';
import LoadingSpinner from '../components/common/LoadingSpinner';

const AuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const loadAuditLogs = async () => {
    try {
      // Fetching transactions/logs from blockchain service
      const response = await blockchainAPI.getTransactions({ limit: 50 });
      setLogs(response.data);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => 
    log.tx_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Audit Trail</h1>
          <p className="text-sm text-gray-500 mt-1">Immutable record of all system actions secured by Hyperledger Fabric</p>
        </div>
        <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-2">
          <Shield size={14} />
          BLOCKCHAIN ACTIVE
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Toolbar */}
        <div className="p-4 border-b border-gray-100 bg-gray-50 flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search Transaction ID or Type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Timeline List */}
        <div className="divide-y divide-gray-100">
          {filteredLogs.length > 0 ? (
            filteredLogs.map((log) => (
              <div key={log.tx_id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-start gap-4">
                  {/* Icon Column */}
                  <div className="mt-1">
                    <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                      <FileText size={16} />
                    </div>
                  </div>

                  {/* Content Column */}
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                        {log.type}
                      </h3>
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock size={12} className="mr-1" />
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-600 mt-1">
                      Action performed on entity: <span className="font-mono text-xs bg-gray-100 px-1 rounded">{log.asset_id}</span>
                    </p>
                    
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-xs font-mono text-gray-400 flex items-center bg-gray-50 px-2 py-1 rounded border border-gray-100">
                        <LinkIcon size={10} className="mr-1" />
                        TX: {log.tx_id.substring(0, 20)}...
                      </span>
                      <span className="text-xs text-green-600 flex items-center font-medium">
                        <CheckCircle size={12} className="mr-1" />
                        Committed
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-12 text-center text-gray-500">
              <Shield className="h-12 w-12 mx-auto text-gray-300 mb-3" />
              <p>No audit logs found matching your criteria</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuditPage;