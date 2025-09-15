import React, { useState } from 'react';
import { useMutation, useQuery } from 'react-query';
import { FileText, Play, Eye } from 'lucide-react';
import { contractAPI } from '../services/api';
import toast from 'react-hot-toast';

const ContractExtraction = () => {
  const [contractText, setContractText] = useState('');
  const [result, setResult] = useState(null);

  const { data: contracts, refetch: refetchContracts } = useQuery(
    'contracts',
    contractAPI.list
  );

  const extractMutation = useMutation(contractAPI.extract, {
    onSuccess: (response) => {
      setResult(response.data);
      toast.success('Contract information extracted successfully!');
      refetchContracts();
    },
    onError: (error) => {
      toast.error('Failed to extract contract information');
      console.error('Extraction error:', error);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!contractText.trim()) return;
    extractMutation.mutate({ contractText });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Contract Extraction</h1>
        <p className="text-gray-600">
          Extract structured information from legal contracts and agreements.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          <form onSubmit={handleSubmit} className="card space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Extract Contract Info</h2>
            
            <div>
              <label className="label">Contract Text</label>
              <textarea
                value={contractText}
                onChange={(e) => setContractText(e.target.value)}
                placeholder="Paste your contract text here..."
                className="textarea h-40"
                required
              />
            </div>

            <button
              type="submit"
              disabled={!contractText.trim() || extractMutation.isLoading}
              className="btn btn-primary w-full"
            >
              {extractMutation.isLoading ? (
                <>
                  <FileText className="h-4 w-4 animate-spin mr-2" />
                  Extracting...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Extract Contract Info
                </>
              )}
            </button>
          </form>

          {/* Sample Contract */}
          <div className="card bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Sample Contract</h3>
            <button
              onClick={() => setContractText("SERVICE AGREEMENT\n\nThis Service Agreement is entered into on January 15, 2024, between TechCorp Inc., a corporation organized under the laws of California, with its principal place of business at 123 Tech Street, San Francisco, CA 94105 (\"Provider\"), and BusinessCo LLC, a limited liability company organized under the laws of New York, with its principal place of business at 456 Business Ave, New York, NY 10001 (\"Client\").\n\nThe Provider agrees to provide software development services to the Client for a period of 12 months, commencing on February 1, 2024, and ending on January 31, 2025. The total contract value is $120,000.\n\nThis agreement shall be governed by the laws of California.")}
              className="w-full text-left p-3 bg-white rounded-lg border hover:bg-gray-50 transition-colors"
            >
              <div className="font-medium text-gray-900">Service Agreement Sample</div>
              <div className="text-sm text-gray-600 mt-1">
                Click to use a sample service agreement for testing.
              </div>
            </button>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {result ? (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Extracted Information</h3>
              
              {result.error ? (
                <div className="text-red-600">{result.error}</div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Contract Type</label>
                    <p className="text-gray-900">{result.contract_type || 'Not specified'}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">Effective Date</label>
                    <p className="text-gray-900">{result.effective_date || 'Not specified'}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">End Date</label>
                    <p className="text-gray-900">{result.end_date || 'Not specified'}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">Total Amount</label>
                    <p className="text-gray-900">
                      {result.total_amount ? `$${result.total_amount.toLocaleString()}` : 'Not specified'}
                    </p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">Contract Scope</label>
                    <p className="text-gray-900">{result.contract_scope || 'Not specified'}</p>
                  </div>
                  
                  {result.parties && result.parties.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-700">Parties</label>
                      <div className="space-y-2 mt-1">
                        {result.parties.map((party, index) => (
                          <div key={index} className="border border-gray-200 rounded p-3">
                            <div className="font-medium">{party.name}</div>
                            <div className="text-sm text-gray-600">Role: {party.role}</div>
                            {party.location && (
                              <div className="text-sm text-gray-600">
                                Location: {[party.location.city, party.location.state, party.location.country].filter(Boolean).join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="card">
              <div className="text-center py-12">
                <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Contract Analyzed</h3>
                <p className="text-gray-600">
                  Paste contract text and click "Extract Contract Info" to analyze the document.
                </p>
              </div>
            </div>
          )}

          {/* Stored Contracts */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Stored Contracts</h3>
              <button
                onClick={() => refetchContracts()}
                className="btn btn-outline btn-sm"
              >
                <Eye className="h-4 w-4 mr-1" />
                Refresh
              </button>
            </div>
            
            {contracts?.data?.contracts?.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {contracts.data.contracts.slice(0, 5).map((contract, index) => (
                  <div key={index} className="border border-gray-200 rounded p-3">
                    <div className="font-medium text-gray-900">{contract.contract_type}</div>
                    <div className="text-sm text-gray-600">
                      {contract.effective_date} - {contract.end_date || 'Ongoing'}
                    </div>
                    {contract.total_amount && (
                      <div className="text-sm text-green-600">
                        ${contract.total_amount.toLocaleString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">No contracts stored yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContractExtraction;
