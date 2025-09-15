import React from 'react';
import { useQuery } from 'react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, Database, FileText, Network, Zap, RefreshCw, Trash2, AlertTriangle } from 'lucide-react';
import { statsAPI, databaseAPI } from '../services/api';
import toast from 'react-hot-toast';

const Statistics = () => {
  const { data: stats, isLoading, refetch } = useQuery(
    'detailed-stats',
    () => statsAPI.getStats(),
    {
      refetchInterval: 30000,
    }
  );

  const handleResetDatabase = async () => {
    if (window.confirm('⚠️ WARNING: This will permanently delete ALL data in the database!\n\nThis includes:\n• All documents and chunks\n• All entities and relationships\n• All contracts and extracted data\n\nAre you sure you want to continue?')) {
      try {
        await databaseAPI.reset();
        toast.success('Database reset successfully!');
        refetch(); // Refresh stats to show empty database
      } catch (error) {
        toast.error('Failed to reset database: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  // Prepare data for charts
  const nodeData = stats?.data?.node_counts ? 
    Object.entries(stats.data.node_counts).map(([key, value]) => ({
      name: key.replace('__', ''),
      value: value
    })) : [];

  const relationshipData = stats?.data?.relationship_counts ?
    Object.entries(stats.data.relationship_counts).map(([key, value]) => ({
      name: key,
      value: value
    })) : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Loading statistics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Statistics</h1>
          <p className="text-gray-600">Overview of your RAG system performance and data</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            className="btn btn-outline flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
          <button
            onClick={handleResetDatabase}
            className="btn btn-outline border-red-200 text-red-700 hover:bg-red-50 flex items-center space-x-2"
          >
            <Trash2 className="h-4 w-4" />
            <span>Reset DB</span>
            <AlertTriangle className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
              <Database className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Nodes</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.data?.total_nodes || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-green-100 text-green-600">
              <Network className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Relationships</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.data?.total_relationships || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-yellow-100 text-yellow-600">
              <FileText className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Documents</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.data?.node_counts?.Document || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-2 rounded-lg bg-purple-100 text-purple-600">
              <Zap className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Entities</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.data?.node_counts?.__Entity__ || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Node Types Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Node Types Distribution</h3>
          {nodeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={nodeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>

        {/* Relationship Types Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Relationship Types</h3>
          {relationshipData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={relationshipData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {relationshipData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No data available
            </div>
          )}
        </div>
      </div>

      {/* Detailed Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Node Counts Table */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Node Counts by Type</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Node Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Count
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {nodeData.map((item, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.value.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Relationship Counts Table */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Relationship Counts by Type</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Relationship Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Count
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {relationshipData.map((item, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.value.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Database Connection</p>
              <p className="text-xs text-gray-600">Connected to Neo4j</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Embedding Service</p>
              <p className="text-xs text-gray-600">Sentence Transformers Ready</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-gray-900">Gemini API</p>
              <p className="text-xs text-gray-600">LLM Service Active</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Statistics;
