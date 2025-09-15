import React, { useState, useEffect } from 'react';
import { knowledgeGraphAPI } from '../services/api';

const KnowledgeGraphConstruction = () => {
  const [contractText, setContractText] = useState('');
  const [extractedData, setExtractedData] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('extract');

  // Load sample contract on component mount
  useEffect(() => {
    loadSampleContract();
    loadStatistics();
  }, []);

  const loadSampleContract = async () => {
    try {
      const response = await knowledgeGraphAPI.getSampleContract();
      setContractText(response.data.sample_contract);
    } catch (err) {
      console.error('Error loading sample contract:', err);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await knowledgeGraphAPI.getStatistics();
      setStatistics(response.data);
    } catch (err) {
      console.error('Error loading statistics:', err);
    }
  };

  const extractContractInfo = async () => {
    if (!contractText.trim()) {
      setError('Please enter contract text');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await knowledgeGraphAPI.extract(contractText);
      setExtractedData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error extracting contract information');
    } finally {
      setLoading(false);
    }
  };

  const importToGraph = async () => {
    if (!contractText.trim()) {
      setError('Please enter contract text');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await knowledgeGraphAPI.import(contractText);
      setExtractedData(response.data.extraction_result);
      setError(null);
      // Reload statistics and graph data
      await loadStatistics();
      await loadGraphData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error importing contract to graph');
    } finally {
      setLoading(false);
    }
  };

  const loadGraphData = async () => {
    try {
      const response = await knowledgeGraphAPI.getGraphData();
      setGraphData(response.data);
    } catch (err) {
      console.error('Error loading graph data:', err);
    }
  };

  const createConstraints = async () => {
    setLoading(true);
    try {
      await knowledgeGraphAPI.createConstraints();
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error creating constraints');
    } finally {
      setLoading(false);
    }
  };

  const clearData = async () => {
    if (!window.confirm('Are you sure you want to clear all contract data?')) {
      return;
    }

    setLoading(true);
    try {
      await knowledgeGraphAPI.clear();
      setExtractedData(null);
      setGraphData(null);
      await loadStatistics();
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error clearing data');
    } finally {
      setLoading(false);
    }
  };

  const queryContracts = async () => {
    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await knowledgeGraphAPI.query(query);
      setQueryResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error querying contracts');
    } finally {
      setLoading(false);
    }
  };

  const renderExtractedData = (data) => {
    if (!data || data.error) {
      return <div className="text-red-600">Error: {data?.error || 'No data available'}</div>;
    }

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Contract Type</h4>
            <p className="text-gray-900">{data.contract_type}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Effective Date</h4>
            <p className="text-gray-900">{data.effective_date}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Term</h4>
            <p className="text-gray-900">{data.term}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Total Amount</h4>
            <p className="text-gray-900">{data.total_amount || 'Not specified'}</p>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-700 mb-2">Contract Scope</h4>
          <p className="text-gray-900 text-sm">{data.contract_scope}</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-700 mb-2">Parties</h4>
          <div className="space-y-3">
            {data.parties?.map((party, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4">
                <p className="font-medium">{party.name}</p>
                <p className="text-sm text-gray-600">Role: {party.role}</p>
                <p className="text-sm text-gray-600">
                  Location: {party.location?.city}, {party.location?.state}, {party.location?.country}
                </p>
              </div>
            ))}
          </div>
        </div>

        {data.governing_law && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Governing Law</h4>
            <p className="text-gray-900">
              {data.governing_law.state}, {data.governing_law.country}
            </p>
          </div>
        )}
      </div>
    );
  };

  const renderGraphData = (data) => {
    if (!data || data.error) {
      return <div className="text-red-600">Error: {data?.error || 'No graph data available'}</div>;
    }

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-700 mb-2">Contracts</h4>
            <p className="text-2xl font-bold text-blue-900">{data.total_contracts}</p>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-semibold text-green-700 mb-2">Organizations</h4>
            <p className="text-2xl font-bold text-green-900">{data.total_organizations}</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-semibold text-purple-700 mb-2">Locations</h4>
            <p className="text-2xl font-bold text-purple-900">{data.total_locations}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border rounded-lg p-4">
            <h4 className="font-semibold text-gray-700 mb-3">Contracts</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {data.contracts?.map((contract, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-3 py-2">
                  <p className="font-medium text-sm">{contract.type}</p>
                  <p className="text-xs text-gray-600">Effective: {contract.effective_date}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <h4 className="font-semibold text-gray-700 mb-3">Organizations</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {data.organizations?.map((org, index) => (
                <div key={index} className="border-l-4 border-green-500 pl-3 py-2">
                  <p className="font-medium text-sm">{org.name}</p>
                  <p className="text-xs text-gray-600">Role: {org.role}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white border rounded-lg p-4">
          <h4 className="font-semibold text-gray-700 mb-3">Party Relationships</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.party_relationships?.map((rel, index) => (
              <div key={index} className="border-l-4 border-yellow-500 pl-3 py-2">
                <p className="text-sm">
                  <span className="font-medium">{rel.organization}</span> 
                  <span className="text-gray-600"> → </span>
                  <span className="font-medium">Contract</span>
                  <span className="text-gray-600"> ({rel.role})</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderQueryResult = (result) => {
    if (!result || result.error) {
      return <div className="text-red-600">Error: {result?.error || 'No query result available'}</div>;
    }

    return (
      <div className="space-y-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-700 mb-2">Generated Cypher Query</h4>
          <pre className="text-sm bg-white p-3 rounded border overflow-x-auto">
            {result.cypher_query}
          </pre>
        </div>

        <div className="bg-green-50 p-4 rounded-lg">
          <h4 className="font-semibold text-green-700 mb-2">Answer</h4>
          <p className="text-gray-900">{result.answer}</p>
        </div>

        {result.results && result.results.length > 0 && (
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-700 mb-2">Query Results</h4>
            <div className="max-h-64 overflow-y-auto">
              <pre className="text-sm bg-white p-3 rounded border">
                {JSON.stringify(result.results, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Knowledge Graph Construction Playground
          </h1>
          <p className="text-gray-600">
            Extract structured information from legal documents and build knowledge graphs using LLMs
          </p>
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="mb-8 bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Graph Statistics</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{statistics.contracts || 0}</div>
                <div className="text-sm text-gray-600">Contracts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{statistics.organizations || 0}</div>
                <div className="text-sm text-gray-600">Organizations</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{statistics.locations || 0}</div>
                <div className="text-sm text-gray-600">Locations</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{statistics.party_relationships || 0}</div>
                <div className="text-sm text-gray-600">Party Relations</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{statistics.location_relationships || 0}</div>
                <div className="text-sm text-gray-600">Location Relations</div>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'extract', label: 'Extract & Import' },
                { id: 'graph', label: 'Graph Data' },
                { id: 'query', label: 'Query Graph' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Extract & Import Tab */}
        {activeTab === 'extract' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Contract Text Input</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Contract Document
                  </label>
                  <textarea
                    value={contractText}
                    onChange={(e) => setContractText(e.target.value)}
                    rows={12}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Paste your contract text here..."
                  />
                </div>
                <div className="flex space-x-4">
                  <button
                    onClick={loadSampleContract}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  >
                    Load Sample Contract
                  </button>
                  <button
                    onClick={extractContractInfo}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {loading ? 'Extracting...' : 'Extract Information'}
                  </button>
                  <button
                    onClick={importToGraph}
                    disabled={loading}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
                  >
                    {loading ? 'Importing...' : 'Extract & Import to Graph'}
                  </button>
                </div>
              </div>
            </div>

            {extractedData && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Extracted Contract Information</h2>
                {renderExtractedData(extractedData)}
              </div>
            )}

            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Graph Management</h2>
              <div className="flex space-x-4">
                <button
                  onClick={createConstraints}
                  disabled={loading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                >
                  Create Constraints
                </button>
                <button
                  onClick={loadGraphData}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  Load Graph Data
                </button>
                <button
                  onClick={clearData}
                  disabled={loading}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
                >
                  Clear All Data
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Graph Data Tab */}
        {activeTab === 'graph' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Knowledge Graph Data</h2>
              <button
                onClick={loadGraphData}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Refresh Data
              </button>
            </div>
            {graphData ? renderGraphData(graphData) : (
              <div className="text-gray-500 text-center py-8">
                No graph data available. Import some contracts first.
              </div>
            )}
          </div>
        )}

        {/* Query Tab */}
        {activeTab === 'query' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Query the Knowledge Graph</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Natural Language Question
                  </label>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="e.g., How many contracts do we have with ACME Inc.?"
                  />
                </div>
                <div className="flex space-x-4">
                  <button
                    onClick={queryContracts}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  >
                    {loading ? 'Querying...' : 'Query Graph'}
                  </button>
                </div>
              </div>
            </div>

            {queryResult && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Query Result</h2>
                {renderQueryResult(queryResult)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraphConstruction;
