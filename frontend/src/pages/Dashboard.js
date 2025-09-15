import React from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import { 
  FileText, 
  MessageSquare, 
  Database, 
  Network, 
  GitBranch,
  BarChart3,
  ChevronRight,
  Activity,
  Users,
  Files,
  Zap,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import { statsAPI, databaseAPI } from '../services/api';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery(
    'stats',
    () => statsAPI.getStats(),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const { data: health } = useQuery(
    'health',
    () => statsAPI.getHealth(),
    {
      refetchInterval: 10000, // Refetch every 10 seconds
    }
  );

  const handleResetDatabase = async () => {
    if (window.confirm('⚠️ WARNING: This will permanently delete ALL data in the database!\n\nThis includes:\n• All documents and chunks\n• All entities and relationships\n• All contracts and extracted data\n\nAre you sure you want to continue?')) {
      try {
        await databaseAPI.reset();
        toast.success('Database reset successfully!');
        refetchStats(); // Refresh stats to show empty database
      } catch (error) {
        toast.error('Failed to reset database: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const features = [
    {
      name: 'PDF Processor',
      description: 'Upload and process PDF documents with advanced text extraction and chunking.',
      icon: FileText,
      href: '/pdf-processor',
      color: 'bg-blue-500',
    },
    {
      name: 'RAG Chat',
      description: 'Interactive chat with your documents using hybrid search and advanced retrieval.',
      icon: MessageSquare,
      href: '/rag-chat',
      color: 'bg-green-500',
    },
    {
      name: 'Text2Cypher',
      description: 'Convert natural language questions to Cypher queries for graph databases.',
      icon: Database,
      href: '/text2cypher',
      color: 'bg-purple-500',
    },
    {
      name: 'Entity Extraction',
      description: 'Extract entities and relationships from text to build knowledge graphs.',
      icon: Network,
      href: '/entity-extraction',
      color: 'bg-orange-500',
    },
    {
      name: 'Contract Extraction',
      description: 'Extract structured information from legal contracts and agreements.',
      icon: FileText,
      href: '/contract-extraction',
      color: 'bg-red-500',
    },
    {
      name: 'Graph RAG',
      description: 'Advanced RAG using graph communities and entity relationships.',
      icon: GitBranch,
      href: '/graph-rag',
      color: 'bg-indigo-500',
    },
  ];

  const quickStats = [
    {
      name: 'Total Documents',
      value: stats?.data?.node_counts?.Document || 0,
      icon: Files,
      color: 'text-blue-600',
    },
    {
      name: 'Entities',
      value: stats?.data?.node_counts?.__Entity__ || 0,
      icon: Users,
      color: 'text-green-600',
    },
    {
      name: 'Relationships',
      value: stats?.data?.total_relationships || 0,
      icon: Activity,
      color: 'text-purple-600',
    },
    {
      name: 'System Status',
      value: health?.data?.status === 'healthy' ? 'Online' : 'Offline',
      icon: Zap,
      color: health?.data?.status === 'healthy' ? 'text-green-600' : 'text-red-600',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gradient mb-4">
          Advanced RAG System
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          A comprehensive platform for document processing, knowledge extraction, 
          and intelligent question answering using state-of-the-art AI technologies.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickStats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className={`p-2 rounded-lg bg-gray-100 ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">
                  {statsLoading ? '...' : stat.value}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Link
              key={feature.name}
              to={feature.href}
              className="card hover:shadow-lg transition-all duration-200 group"
            >
              <div className="flex items-center mb-4">
                <div className={`p-3 rounded-lg ${feature.color} text-white`}>
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="ml-4 text-lg font-semibold text-gray-900">
                  {feature.name}
                </h3>
              </div>
              <p className="text-gray-600 mb-4">{feature.description}</p>
              <div className="flex items-center text-primary-600 group-hover:text-primary-700">
                <span className="text-sm font-medium">Get Started</span>
                <ChevronRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">System Overview</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* System Health */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">API Status</span>
                <span className={`badge ${health?.data?.status === 'healthy' ? 'badge-success' : 'badge-error'}`}>
                  {health?.data?.status || 'Unknown'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Database</span>
                <span className="badge badge-success">Connected</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Embedding Service</span>
                <span className="badge badge-success">Ready</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Gemini API</span>
                <span className="badge badge-success">Active</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Link
                to="/pdf-processor"
                className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <FileText className="h-5 w-5 text-blue-500 mr-3" />
                <span className="text-gray-900">Upload a new document</span>
              </Link>
              <Link
                to="/rag-chat"
                className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <MessageSquare className="h-5 w-5 text-green-500 mr-3" />
                <span className="text-gray-900">Start a RAG conversation</span>
              </Link>
              <Link
                to="/entity-extraction"
                className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <Network className="h-5 w-5 text-orange-500 mr-3" />
                <span className="text-gray-900">Extract entities from text</span>
              </Link>
              <Link
                to="/statistics"
                className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <BarChart3 className="h-5 w-5 text-purple-500 mr-3" />
                <span className="text-gray-900">View detailed statistics</span>
              </Link>
              
              {/* Database Reset Button */}
              <div className="border-t border-gray-200 pt-3 mt-3">
                <button
                  onClick={handleResetDatabase}
                  className="flex items-center w-full p-3 rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 transition-colors text-red-700"
                >
                  <Trash2 className="h-5 w-5 text-red-500 mr-3" />
                  <span className="font-medium">Reset Database</span>
                  <AlertTriangle className="h-4 w-4 text-red-500 ml-auto" />
                </button>
                <p className="text-xs text-red-600 mt-1 ml-8">
                  ⚠️ This will permanently delete all data
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started */}
      <div className="card bg-gradient-to-r from-primary-50 to-purple-50 border-primary-200">
        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-900 mb-2">Getting Started</h3>
          <p className="text-gray-600 mb-6">
            New to the system? Start by uploading a document and exploring the RAG capabilities.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/pdf-processor" className="btn btn-primary">
              Upload Document
            </Link>
            <Link to="/rag-chat" className="btn btn-outline">
              Try RAG Chat
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
