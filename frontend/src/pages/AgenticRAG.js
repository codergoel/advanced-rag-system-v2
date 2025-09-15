import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { agenticRAGAPI } from '../services/api';
import { 
  Bot, 
  Send, 
  Loader2, 
  Brain, 
  Zap, 
  CheckCircle, 
  AlertCircle,
  Info,
  Wrench,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

const AgenticRAG = () => {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [availableTools, setAvailableTools] = useState([]);

  // Fetch available tools
  const { data: toolsData, refetch: refetchTools, error: toolsError, isLoading: toolsLoading } = useQuery(
    'agentic-rag-tools',
    () => agenticRAGAPI.getTools(),
    {
      refetchOnWindowFocus: false,
      retry: 3
    }
  );

  // Update available tools when data changes
  React.useEffect(() => {
    if (toolsData?.tools && Array.isArray(toolsData.tools)) {
      setAvailableTools(toolsData.tools);
    } else if (toolsData) {
      // Try to extract tools from different possible structures
      if (toolsData.data?.tools) {
        setAvailableTools(toolsData.data.tools);
      } else if (Array.isArray(toolsData)) {
        setAvailableTools(toolsData);
      }
    }
  }, [toolsData, toolsLoading, toolsError]);

  // Handle tools error
  React.useEffect(() => {
    if (toolsError) {
      toast.error('Failed to load available tools: ' + (toolsError.response?.data?.detail || toolsError.message));
    }
  }, [toolsError]);

  // Agentic RAG query mutation
  const agenticRAGMutation = useMutation(
    (question) => agenticRAGAPI.query(question),
    {
      onSuccess: (data) => {
        console.log('Agentic RAG Success:', data);
        setResult(data.data || data);
        toast.success('Query processed successfully!');
      },
      onError: (error) => {
        console.error('Agentic RAG Error:', error);
        toast.error('Failed to process query: ' + (error.response?.data?.detail || error.message));
        setResult(null);
      },
      onSettled: () => {
        setIsLoading(false);
      }
    }
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      toast.error('Please enter a question');
      return;
    }

    console.log('Submitting question:', question);
    setIsLoading(true);
    setResult(null);
    agenticRAGMutation.mutate(question);
  };

  const handleExampleQuestion = (exampleQuestion) => {
    setQuestion(exampleQuestion);
  };

  const exampleQuestions = [
    "What movies did Tom Hanks act in?",
    "Who directed The Matrix?",
    "Show me all movies released in 1999",
    "What is the capital of France?",
    "Who are the actors in Apollo 13?",
    "Find movies with the word 'Matrix' in the title"
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Brain className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">Agentic RAG Playground</h1>
          </div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Experience intelligent question answering with multiple specialized retrieval agents. 
            The system automatically selects the best retriever for each question and validates the completeness of answers.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Query Interface */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center mb-6">
                <Bot className="h-6 w-6 text-blue-600 mr-2" />
                <h2 className="text-2xl font-semibold text-gray-900">Ask a Question</h2>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
                    Your Question
                  </label>
                  <textarea
                    id="question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask any question about movies, actors, directors, or general knowledge..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows={4}
                    disabled={isLoading}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !question.trim()}
                  className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-5 w-5" />
                      <span>Ask Question</span>
                    </>
                  )}
                </button>
              </form>

              {/* Example Questions */}
              <div className="mt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Example Questions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {exampleQuestions.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => handleExampleQuestion(example)}
                      className="text-left p-3 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors"
                      disabled={isLoading}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Results */}
            {result && (
              <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center mb-4">
                  <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
                  <h3 className="text-xl font-semibold text-gray-900">Answer</h3>
                </div>
                
                {/* Debug info */}
                <div className="mb-4 p-2 bg-gray-100 rounded text-xs">
                  <strong>Debug - Result object:</strong> {JSON.stringify(result, null, 2)}
                </div>

                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Question:</h4>
                    <p className="text-gray-700">{result.question}</p>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Answer:</h4>
                    <p className="text-gray-700 whitespace-pre-wrap">{result.answer}</p>
                  </div>

                  {result.critique_questions && result.critique_questions.length > 0 && (
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                        <AlertCircle className="h-5 w-5 text-yellow-600 mr-2" />
                        Additional Questions Asked:
                      </h4>
                      <ul className="list-disc list-inside text-gray-700 space-y-1">
                        {result.critique_questions.map((q, index) => (
                          <li key={index}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">Processing Details:</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Retrieval Steps:</span> {result.retrieval_steps}
                      </div>
                      <div>
                        <span className="font-medium">Status:</span> 
                        <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                          result.status === 'success' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {result.status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - Available Tools */}
          <div className="space-y-6">
            {/* Available Tools */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <Wrench className="h-6 w-6 text-green-600 mr-2" />
                  <h3 className="text-lg font-semibold text-gray-900">Available Tools</h3>
                </div>
                <button
                  onClick={() => refetchTools()}
                  className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Refresh tools"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>


              <div className="space-y-3">
                {availableTools.map((tool, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <Zap className="h-4 w-4 text-blue-600" />
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900">{tool.name}</h4>
                        <p className="text-xs text-gray-600 mt-1">{tool.description}</p>
                        {tool.parameters && tool.parameters.required && (
                          <div className="mt-2">
                            <p className="text-xs text-gray-500">
                              Required: {tool.parameters.required.join(', ')}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {toolsLoading && (
                <div className="text-center py-4">
                  <Loader2 className="h-8 w-8 text-blue-400 mx-auto mb-2 animate-spin" />
                  <p className="text-sm text-gray-500">Loading tools...</p>
                </div>
              )}
              
              {!toolsLoading && availableTools.length === 0 && !toolsError && (
                <div className="text-center py-4">
                  <Info className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No tools available</p>
                </div>
              )}
              
              {toolsError && (
                <div className="text-center py-4">
                  <AlertCircle className="h-8 w-8 text-red-400 mx-auto mb-2" />
                  <p className="text-sm text-red-500">Error loading tools</p>
                  <button 
                    onClick={() => refetchTools()}
                    className="text-xs text-blue-500 hover:text-blue-700 mt-1"
                  >
                    Retry
                  </button>
                </div>
              )}
            </div>

            {/* How It Works */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Brain className="h-6 w-6 text-purple-600 mr-2" />
                How Agentic RAG Works
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">1</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Question Analysis</h4>
                    <p className="text-xs text-gray-600">The system analyzes your question and updates it with context from previous answers.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">2</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Tool Selection</h4>
                    <p className="text-xs text-gray-600">An LLM selects the most appropriate retriever tool for your question.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">3</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Data Retrieval</h4>
                    <p className="text-xs text-gray-600">The selected tool retrieves relevant data from the knowledge base.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">4</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Answer Validation</h4>
                    <p className="text-xs text-gray-600">The system checks if the answer is complete and asks follow-up questions if needed.</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">5</span>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Final Response</h4>
                    <p className="text-xs text-gray-600">A comprehensive answer is generated using all retrieved information.</p>
                  </div>
                </div>
              </div>
            </div>

            {/* System Status */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
                System Status
              </h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Neo4j Database</span>
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Connected</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Gemini API</span>
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Active</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Retriever Tools</span>
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">{availableTools.length} Available</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgenticRAG;
