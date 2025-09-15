import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from 'react-query';
import { Send, Bot, User, Loader2, Search, Zap, GitBranch } from 'lucide-react';
import { ragAPI } from '../services/api';
import toast from 'react-hot-toast';

const RAGChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Hello! I\'m your RAG assistant. Ask me questions about your uploaded documents and I\'ll help you find answers using advanced retrieval techniques.',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [searchType, setSearchType] = useState('hybrid');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const queryMutation = useMutation(
    ({ question, type }) => {
      if (type === 'stepback') {
        return ragAPI.stepbackQuery(question);
      }
      return ragAPI.query(question, type);
    },
    {
      onSuccess: (response, variables) => {
        const botMessage = {
          id: Date.now(),
          type: 'bot',
          content: response.data.answer,
          searchType: variables.type,
          retrievedDocs: response.data.retrieved_documents || response.data.retrievedDocuments,
          metadata: {
            searchType: response.data.search_type,
            stepbackQuestion: response.data.stepback_question,
          },
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, botMessage]);
      },
      onError: (error) => {
        toast.error('Failed to get response');
        const errorMessage = {
          id: Date.now(),
          type: 'bot',
          content: 'Sorry, I encountered an error while processing your question. Please try again.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
      },
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || queryMutation.isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    queryMutation.mutate({ question: input, type: searchType });
    setInput('');
  };

  const searchTypeOptions = [
    { value: 'hybrid', label: 'Hybrid Search', icon: Search, description: 'Combines vector and keyword search' },
    { value: 'vector', label: 'Vector Search', icon: Zap, description: 'Semantic similarity search' },
    { value: 'keyword', label: 'Keyword Search', icon: Search, description: 'Traditional text search' },
    { value: 'stepback', label: 'Step-back RAG', icon: GitBranch, description: 'Advanced reasoning with step-back prompting' },
  ];

  const formatTimestamp = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">RAG Chat</h1>
            <p className="text-gray-600">Ask questions about your uploaded documents</p>
          </div>
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Search Type:</label>
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              className="select text-sm"
              disabled={queryMutation.isLoading}
            >
              {searchTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Search Type Description */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-2">
            {React.createElement(
              searchTypeOptions.find(opt => opt.value === searchType)?.icon || Search,
              { className: "h-4 w-4 text-primary-600" }
            )}
            <span className="text-sm font-medium text-gray-900">
              {searchTypeOptions.find(opt => opt.value === searchType)?.label}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            {searchTypeOptions.find(opt => opt.value === searchType)?.description}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 card overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`flex max-w-[80%] ${
                  message.type === 'user' ? 'flex-row-reverse' : 'flex-row'
                }`}
              >
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user'
                      ? 'bg-primary-600 text-white ml-3'
                      : 'bg-gray-200 text-gray-600 mr-3'
                  }`}
                >
                  {message.type === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </div>
                <div
                  className={`rounded-lg px-4 py-2 ${
                    message.type === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="text-sm">{message.content}</div>
                  <div className="flex items-center justify-between mt-2">
                    <div
                      className={`text-xs ${
                        message.type === 'user' ? 'text-primary-200' : 'text-gray-500'
                      }`}
                    >
                      {formatTimestamp(message.timestamp)}
                    </div>
                    {message.metadata?.searchType && (
                      <div
                        className={`text-xs px-2 py-1 rounded ${
                          message.type === 'user'
                            ? 'bg-primary-500 text-primary-100'
                            : 'bg-gray-200 text-gray-600'
                        }`}
                      >
                        {message.metadata.searchType}
                      </div>
                    )}
                  </div>
                  
                  {/* Retrieved Documents */}
                  {message.retrievedDocs && message.retrievedDocs.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300">
                      <div className="text-xs font-medium text-gray-600 mb-2">
                        Retrieved Documents ({message.retrievedDocs.length}):
                      </div>
                      <div className="space-y-2">
                        {message.retrievedDocs.slice(0, 3).map((doc, idx) => (
                          <div key={idx} className="text-xs bg-white p-2 rounded border">
                            <div className="font-medium text-gray-700 mb-1">
                              Score: {doc.score?.toFixed(3)}
                            </div>
                            <div className="text-gray-600 line-clamp-2">
                              {doc.text?.substring(0, 100)}...
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Step-back Question */}
                  {message.metadata?.stepbackQuestion && (
                    <div className="mt-3 pt-3 border-t border-gray-300">
                      <div className="text-xs font-medium text-gray-600 mb-1">
                        Step-back Question:
                      </div>
                      <div className="text-xs text-gray-700 italic">
                        "{message.metadata.stepbackQuestion}"
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {queryMutation.isLoading && (
            <div className="flex justify-start">
              <div className="flex flex-row">
                <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-200 text-gray-600 mr-3">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="border-t p-4">
          <form onSubmit={handleSubmit} className="flex space-x-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="flex-1 input"
              disabled={queryMutation.isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || queryMutation.isLoading}
              className="btn btn-primary flex items-center space-x-2"
            >
              {queryMutation.isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RAGChat;
