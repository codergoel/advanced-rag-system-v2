import React, { useState } from 'react';
import { useMutation, useQuery } from 'react-query';
import { Network, Play, Eye } from 'lucide-react';
import { entityAPI } from '../services/api';
import toast from 'react-hot-toast';

const EntityExtraction = () => {
  const [text, setText] = useState('');
  const [entityTypes, setEntityTypes] = useState(['PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT']);
  const [result, setResult] = useState(null);

  const { data: graphData, refetch: refetchGraph } = useQuery(
    'entity-graph',
    entityAPI.getGraph,
    { enabled: false }
  );

  const extractMutation = useMutation(entityAPI.extract, {
    onSuccess: (response) => {
      setResult(response.data);
      toast.success('Entities extracted successfully!');
      refetchGraph();
    },
    onError: (error) => {
      toast.error('Failed to extract entities');
      console.error('Extraction error:', error);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    extractMutation.mutate({ text, entityTypes });
  };

  const availableEntityTypes = [
    'PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT', 'PRODUCT', 'CONCEPT'
  ];

  const handleEntityTypeChange = (type) => {
    setEntityTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Entity Extraction</h1>
        <p className="text-gray-600">
          Extract entities and relationships from text to build knowledge graphs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          <form onSubmit={handleSubmit} className="card space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Extract Entities</h2>
            
            <div>
              <label className="label">Text to Analyze</label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter text to extract entities from..."
                className="textarea h-32"
                required
              />
            </div>

            <div>
              <label className="label">Entity Types to Extract</label>
              <div className="grid grid-cols-2 gap-2">
                {availableEntityTypes.map((type) => (
                  <label key={type} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={entityTypes.includes(type)}
                      onChange={() => handleEntityTypeChange(type)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700">{type}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={!text.trim() || extractMutation.isLoading}
              className="btn btn-primary w-full"
            >
              {extractMutation.isLoading ? (
                <>
                  <Network className="h-4 w-4 animate-spin mr-2" />
                  Extracting...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Extract Entities
                </>
              )}
            </button>
          </form>

          {/* Sample Text */}
          <div className="card bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Sample Text</h3>
            <button
              onClick={() => setText("Apple Inc. is an American multinational technology company headquartered in Cupertino, California. Tim Cook is the CEO of Apple. The company was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976. Apple is known for products like the iPhone, iPad, and Mac computers.")}
              className="w-full text-left p-3 bg-white rounded-lg border hover:bg-gray-50 transition-colors"
            >
              <div className="font-medium text-gray-900">Apple Inc. Sample</div>
              <div className="text-sm text-gray-600 mt-1">
                Click to use sample text about Apple Inc. and its leadership.
              </div>
            </button>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {result ? (
            <>
              {/* Summary */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Extraction Summary</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {result.entities_count}
                    </div>
                    <div className="text-sm text-blue-800">Entities Found</div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {result.relationships_count}
                    </div>
                    <div className="text-sm text-green-800">Relationships Found</div>
                  </div>
                </div>
              </div>

              {/* Entities */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Extracted Entities</h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {result.entities.map((entity, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-900">{entity.entity_name}</span>
                        <span className="badge badge-primary">{entity.entity_type}</span>
                      </div>
                      <p className="text-sm text-gray-600">{entity.entity_description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Relationships */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Extracted Relationships</h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {result.relationships.map((rel, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="font-medium text-gray-900">{rel.source_entity}</span>
                        <span className="text-gray-500">→</span>
                        <span className="font-medium text-gray-900">{rel.target_entity}</span>
                        <span className="badge badge-secondary">
                          {rel.relationship_strength}/10
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{rel.relationship_description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="card">
              <div className="text-center py-12">
                <Network className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Entities Extracted</h3>
                <p className="text-gray-600">
                  Enter text and click "Extract Entities" to analyze and build a knowledge graph.
                </p>
              </div>
            </div>
          )}

          {/* Graph Visualization Button */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Knowledge Graph</h3>
            <button
              onClick={() => refetchGraph()}
              className="btn btn-outline w-full"
              disabled={!graphData?.data}
            >
              <Eye className="h-4 w-4 mr-2" />
              View Graph Visualization
            </button>
            {graphData?.data && (
              <div className="mt-3 text-sm text-gray-600">
                Graph contains {graphData.data.stats?.total_nodes} nodes and {graphData.data.stats?.total_edges} edges
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EntityExtraction;
