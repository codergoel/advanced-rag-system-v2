import React, { useState } from 'react';
import { useMutation } from 'react-query';
import { GitBranch, Globe, MapPin, Play, Settings } from 'lucide-react';
import { graphRAGAPI } from '../services/api';
import toast from 'react-hot-toast';

const GraphRAG = () => {
  const [question, setQuestion] = useState('');
  const [searchType, setSearchType] = useState('global');
  const [result, setResult] = useState(null);

  const globalMutation = useMutation(graphRAGAPI.globalQuery, {
    onSuccess: (response) => {
      setResult(response.data);
      toast.success('Global graph RAG completed!');
    },
    onError: (error) => {
      toast.error('Failed to perform global graph RAG');
      console.error('Global RAG error:', error);
    },
  });

  const localMutation = useMutation(graphRAGAPI.localQuery, {
    onSuccess: (response) => {
      setResult(response.data);
      toast.success('Local graph RAG completed!');
    },
    onError: (error) => {
      toast.error('Failed to perform local graph RAG');
      console.error('Local RAG error:', error);
    },
  });

  const communitiesMutation = useMutation(graphRAGAPI.calculateCommunities, {
    onSuccess: (response) => {
      toast.success('Communities calculated successfully!');
      console.log('Communities result:', response.data);
    },
    onError: (error) => {
      toast.error('Failed to calculate communities');
      console.error('Communities error:', error);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    if (searchType === 'global') {
      globalMutation.mutate({ question });
    } else {
      localMutation.mutate({ question });
    }
  };

  const isLoading = globalMutation.isLoading || localMutation.isLoading;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Graph RAG</h1>
        <p className="text-gray-600">
          Advanced RAG using graph communities and entity relationships for comprehensive answers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          <form onSubmit={handleSubmit} className="card space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Graph RAG Query</h2>
            
            <div>
              <label className="label">Search Type</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setSearchType('global')}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    searchType === 'global'
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <Globe className="h-4 w-4" />
                    <span className="font-medium">Global RAG</span>
                  </div>
                  <p className="text-xs text-gray-600">
                    Uses community summaries for broad insights
                  </p>
                </button>
                
                <button
                  type="button"
                  onClick={() => setSearchType('local')}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    searchType === 'local'
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <MapPin className="h-4 w-4" />
                    <span className="font-medium">Local RAG</span>
                  </div>
                  <p className="text-xs text-gray-600">
                    Uses entity embeddings for specific details
                  </p>
                </button>
              </div>
            </div>

            <div>
              <label className="label">Question</label>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a complex question that requires understanding of relationships and context..."
                className="textarea h-24"
                required
              />
            </div>

            <button
              type="submit"
              disabled={!question.trim() || isLoading}
              className="btn btn-primary w-full"
            >
              {isLoading ? (
                <>
                  <GitBranch className="h-4 w-4 animate-spin mr-2" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run Graph RAG
                </>
              )}
            </button>
          </form>

          {/* Community Management */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Graph Management</h3>
            <div className="space-y-3">
              <button
                onClick={() => communitiesMutation.mutate()}
                disabled={communitiesMutation.isLoading}
                className="btn btn-outline w-full"
              >
                {communitiesMutation.isLoading ? (
                  <>
                    <Settings className="h-4 w-4 animate-spin mr-2" />
                    Calculating...
                  </>
                ) : (
                  <>
                    <Settings className="h-4 w-4 mr-2" />
                    Calculate Communities
                  </>
                )}
              </button>
              <p className="text-sm text-gray-600">
                Run community detection to group related entities for better global RAG performance.
              </p>
            </div>
          </div>

          {/* Sample Questions */}
          <div className="card bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Sample Questions</h3>
            <div className="space-y-2">
              <button
                onClick={() => setQuestion("What is the overall story about and who are the main characters?")}
                className="w-full text-left p-3 bg-white rounded-lg border hover:bg-gray-50 transition-colors"
              >
                <div className="font-medium text-gray-900">Story Overview</div>
                <div className="text-sm text-gray-600">Global question about main themes and characters</div>
              </button>
              
              <button
                onClick={() => setQuestion("How are the main characters related to each other?")}
                className="w-full text-left p-3 bg-white rounded-lg border hover:bg-gray-50 transition-colors"
              >
                <div className="font-medium text-gray-900">Character Relationships</div>
                <div className="text-sm text-gray-600">Local question about specific relationships</div>
              </button>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {result ? (
            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                {searchType === 'global' ? (
                  <Globe className="h-5 w-5 text-blue-600" />
                ) : (
                  <MapPin className="h-5 w-5 text-green-600" />
                )}
                <h3 className="text-lg font-semibold text-gray-900">
                  {searchType === 'global' ? 'Global' : 'Local'} Graph RAG Result
                </h3>
              </div>
              
              <div className="prose max-w-none">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-900 whitespace-pre-wrap">{result.answer}</p>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>Search Type: {result.search_type}</span>
                  <span>Question: {result.question}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="text-center py-12">
                <GitBranch className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Query Executed</h3>
                <p className="text-gray-600">
                  Enter a question and select a search type to perform Graph RAG analysis.
                </p>
              </div>
            </div>
          )}

          {/* Information Cards */}
          <div className="space-y-4">
            <div className="card bg-blue-50 border-blue-200">
              <div className="flex items-start space-x-3">
                <Globe className="h-5 w-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-blue-900">Global RAG</h4>
                  <p className="text-blue-800 text-sm mt-1">
                    Uses community detection to identify clusters of related entities, 
                    then generates summaries for each community. Best for broad, 
                    thematic questions about overall patterns and relationships.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="card bg-green-50 border-green-200">
              <div className="flex items-start space-x-3">
                <MapPin className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-green-900">Local RAG</h4>
                  <p className="text-green-800 text-sm mt-1">
                    Uses entity embeddings to find the most relevant entities, 
                    then retrieves their local context including relationships 
                    and community information. Best for specific, detailed questions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphRAG;
