import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Database, 
  Play, 
  RefreshCw, 
  Download, 
  Code, 
  FileText, 
  AlertCircle,
  CheckCircle,
  Loader,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import { text2cypherAPI, databaseAPI } from '../services/api';
import toast from 'react-hot-toast';

const Text2Cypher = () => {
  const [question, setQuestion] = useState('');
  const [terminology, setTerminology] = useState('');
  const [examples, setExamples] = useState('');
  const [cypherQuery, setCypherQuery] = useState('');
  const [queryResults, setQueryResults] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  const queryClient = useQueryClient();

  // Get schema data
  const { data: schemaData, isLoading: schemaLoading, refetch: refetchSchema } = useQuery(
    'text2cypher-schema',
    () => text2cypherAPI.getSchema(),
    {
      retry: false,
      onError: (error) => {
        console.error('Schema fetch error:', error);
      }
    }
  );

  // Load movies dataset mutation
  const loadMoviesMutation = useMutation(
    () => text2cypherAPI.loadMoviesDataset(),
    {
      onSuccess: (data) => {
        toast.success('Movies dataset loaded successfully!');
        refetchSchema(); // Refresh schema after loading
        queryClient.invalidateQueries('stats'); // Refresh stats
      },
      onError: (error) => {
        toast.error('Failed to load movies dataset: ' + (error.response?.data?.detail || error.message));
      }
    }
  );

  // Reset database mutation
  const resetDatabaseMutation = useMutation(
    () => databaseAPI.reset(),
    {
      onSuccess: () => {
        toast.success('Database reset successfully!');
        refetchSchema(); // Refresh schema after reset
        queryClient.invalidateQueries('stats'); // Refresh stats
        setCypherQuery('');
        setQueryResults(null);
      },
      onError: (error) => {
        toast.error('Failed to reset database: ' + (error.response?.data?.detail || error.message));
      }
    }
  );

  const handleGenerateCypher = async () => {
    if (!question.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await text2cypherAPI.query(question, terminology, examples);
      setCypherQuery(response.data.cypher_query);
      setQueryResults(response.data.results);
      toast.success('Cypher query generated successfully!');
    } catch (error) {
      toast.error('Failed to generate Cypher query: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExecuteQuery = async () => {
    if (!cypherQuery.trim()) {
      toast.error('Please generate a Cypher query first');
      return;
    }

    setIsExecuting(true);
    try {
      const response = await text2cypherAPI.query(question, terminology, examples);
      setQueryResults(response.data.results);
      toast.success('Query executed successfully!');
    } catch (error) {
      toast.error('Failed to execute query: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsExecuting(false);
    }
  };

  const handleLoadMoviesDataset = () => {
    if (window.confirm('This will load the movies dataset into your database. Continue?')) {
      loadMoviesMutation.mutate();
    }
  };

  const handleResetDatabase = () => {
    if (window.confirm('⚠️ WARNING: This will permanently delete ALL data in the database!\n\nThis includes:\n• All documents and chunks\n• All entities and relationships\n• All contracts and extracted data\n• All movies dataset data\n\nAre you sure you want to continue?')) {
      resetDatabaseMutation.mutate();
    }
  };

  const defaultTerminology = `Persons: When a user asks about a person by trade like actor, writer, director, producer, or reviewer, they are referring to a node with the label 'Person'.
Movies: When a user asks about a film or movie, they are referring to a node with the label Movie.
Genres: When a user asks about a genre or category, they are referring to a node with the label Genre.`;

  const defaultExamples = `Question: Who are the two people who have acted in the most movies together?
Cypher: MATCH (p1:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(p2:Person) WHERE p1 <> p2 RETURN p1.name, p2.name, COUNT(m) AS movieCount ORDER BY movieCount DESC LIMIT 1

Question: What movies did Tom Cruise act in?
Cypher: MATCH (p:Person {name: 'Tom Cruise'})-[:ACTED_IN]->(m:Movie) RETURN m.title, m.released ORDER BY m.released`;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Text2Cypher Playground</h1>
          <p className="text-gray-600">Convert natural language questions to Cypher queries using Gemini AI</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetchSchema()}
            className="btn btn-outline flex items-center space-x-2"
            disabled={schemaLoading}
          >
            <RefreshCw className={`h-4 w-4 ${schemaLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Schema</span>
          </button>
          <button
            onClick={handleLoadMoviesDataset}
            className="btn btn-primary flex items-center space-x-2"
            disabled={loadMoviesMutation.isLoading}
          >
            <Download className="h-4 w-4" />
            <span>Load Movies Dataset</span>
          </button>
          <button
            onClick={handleResetDatabase}
            className="btn btn-outline border-red-200 text-red-700 hover:bg-red-50 flex items-center space-x-2"
            disabled={resetDatabaseMutation.isLoading}
          >
            <Trash2 className="h-4 w-4" />
            <span>Reset DB</span>
            <AlertTriangle className="h-3 w-3" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          {/* Natural Language Question */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <FileText className="h-5 w-5 text-blue-500 mr-2" />
              Natural Language Question
            </h3>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., Who directed the most movies? What movies did Tom Cruise act in? List all action movies released after 2000."
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Terminology Mapping */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Database className="h-5 w-5 text-green-500 mr-2" />
              Terminology Mapping (Optional)
            </h3>
            <textarea
              value={terminology}
              onChange={(e) => setTerminology(e.target.value)}
              placeholder={defaultTerminology}
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
            />
            <p className="text-sm text-gray-500 mt-2">
              Help the AI understand how to map your question terminology to the database schema.
            </p>
          </div>

          {/* Examples */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Code className="h-5 w-5 text-purple-500 mr-2" />
              Examples (Optional)
            </h3>
            <textarea
              value={examples}
              onChange={(e) => setExamples(e.target.value)}
              placeholder={defaultExamples}
              className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
            <p className="text-sm text-gray-500 mt-2">
              Provide few-shot examples to improve query generation accuracy.
            </p>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerateCypher}
            disabled={isGenerating || !question.trim()}
            className="btn btn-primary w-full flex items-center justify-center space-x-2"
          >
            {isGenerating ? (
              <Loader className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            <span>{isGenerating ? 'Generating...' : 'Generate Cypher Query'}</span>
          </button>
        </div>

        {/* Output Section */}
        <div className="space-y-6">
          {/* Generated Cypher Query */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Code className="h-5 w-5 text-orange-500 mr-2" />
              Generated Cypher Query
            </h3>
            {cypherQuery ? (
              <div className="space-y-3">
                <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
                  <code>{cypherQuery}</code>
                </pre>
                <button
                  onClick={handleExecuteQuery}
                  disabled={isExecuting}
                  className="btn btn-outline flex items-center space-x-2"
                >
                  {isExecuting ? (
                    <Loader className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  <span>{isExecuting ? 'Executing...' : 'Execute Query'}</span>
                </button>
              </div>
            ) : (
              <div className="text-gray-500 text-center py-8">
                <Code className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>Generated Cypher query will appear here</p>
              </div>
            )}
          </div>

          {/* Query Results */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Database className="h-5 w-5 text-blue-500 mr-2" />
              Query Results
            </h3>
            {queryResults ? (
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">Query executed successfully</span>
                </div>
                <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto max-h-64">
                  <code>{JSON.stringify(queryResults, null, 2)}</code>
                </pre>
              </div>
            ) : (
              <div className="text-gray-500 text-center py-8">
                <Database className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>Query results will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Database Schema */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Database className="h-5 w-5 text-indigo-500 mr-2" />
          Database Schema (APOC Generated)
        </h3>
        {schemaLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader className="h-6 w-6 animate-spin text-indigo-500 mr-2" />
            <span>Loading schema...</span>
          </div>
        ) : schemaData?.data?.schema_string ? (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Schema loaded successfully</span>
            </div>
            <pre className="bg-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
              <code>{schemaData.data.schema_string}</code>
            </pre>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-yellow-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">No schema data available</span>
            </div>
            <p className="text-gray-600">
              Load the movies dataset or add some data to see the schema. The schema is automatically inferred using APOC procedures.
            </p>
          </div>
        )}
      </div>

      {/* Sample Questions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Sample Questions to Try</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            "Who directed the most movies?",
            "What movies did Tom Cruise act in?",
            "List all action movies released after 2000",
            "Who are the actors in The Matrix?",
            "What genres does Keanu Reeves appear in?",
            "Find movies with more than 3 actors",
            "Who wrote the most movies?",
            "What is the oldest movie in the database?"
          ].map((sampleQuestion, index) => (
            <button
              key={index}
              onClick={() => setQuestion(sampleQuestion)}
              className="text-left p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <span className="text-sm text-gray-700">{sampleQuestion}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Text2Cypher;