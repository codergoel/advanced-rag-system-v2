import React, { useState } from 'react';
import { useMutation } from 'react-query';
import { Upload, Link as LinkIcon, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { pdfAPI } from '../services/api';
import toast from 'react-hot-toast';

const PDFProcessor = () => {
  const [dragActive, setDragActive] = useState(false);
  const [url, setUrl] = useState('');
  const [processingResults, setProcessingResults] = useState(null);

  const uploadMutation = useMutation(pdfAPI.uploadPDF, {
    onSuccess: (response) => {
      toast.success('PDF uploaded and processed successfully!');
      setProcessingResults(response.data);
    },
    onError: (error) => {
      toast.error('Failed to upload PDF');
      console.error('Upload error:', error);
    },
  });

  const downloadMutation = useMutation(pdfAPI.downloadPDF, {
    onSuccess: (response) => {
      toast.success('PDF downloaded and processed successfully!');
      setProcessingResults(response.data);
      setUrl('');
    },
    onError: (error) => {
      toast.error('Failed to download PDF');
      console.error('Download error:', error);
    },
  });

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        uploadMutation.mutate(file);
      } else {
        toast.error('Please upload a PDF file');
      }
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf') {
        uploadMutation.mutate(file);
      } else {
        toast.error('Please upload a PDF file');
      }
    }
  };

  const handleUrlSubmit = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    
    if (!url.toLowerCase().endsWith('.pdf')) {
      toast.error('Please provide a valid PDF URL');
      return;
    }
    
    downloadMutation.mutate(url);
  };

  const isLoading = uploadMutation.isLoading || downloadMutation.isLoading;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">PDF Processor</h1>
        <p className="text-gray-600">
          Upload PDF documents or provide URLs to extract text and create searchable chunks for RAG.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="space-y-6">
          {/* File Upload */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload PDF File</h2>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-gray-400'
              } ${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {isLoading ? (
                <div className="space-y-4">
                  <Loader2 className="h-12 w-12 text-primary-600 mx-auto animate-spin" />
                  <p className="text-gray-600">Processing PDF...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto" />
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      Drop your PDF file here, or{' '}
                      <label className="text-primary-600 hover:text-primary-700 cursor-pointer">
                        browse
                        <input
                          type="file"
                          accept=".pdf"
                          onChange={handleFileSelect}
                          className="hidden"
                        />
                      </label>
                    </p>
                    <p className="text-gray-500 mt-2">Supports PDF files up to 50MB</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* URL Download */}
          <div className="card">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Download from URL</h2>
            <form onSubmit={handleUrlSubmit} className="space-y-4">
              <div>
                <label className="label">PDF URL</label>
                <div className="relative">
                  <LinkIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com/document.pdf"
                    className="input pl-10"
                    disabled={isLoading}
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={!url.trim() || isLoading}
                className="btn btn-primary w-full"
              >
                {downloadMutation.isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Downloading...
                  </>
                ) : (
                  <>
                    <LinkIcon className="h-4 w-4 mr-2" />
                    Download & Process
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Sample URLs */}
          <div className="card bg-gray-50">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Sample PDFs</h3>
            <div className="space-y-2">
              <button
                onClick={() => setUrl('https://arxiv.org/pdf/1709.00666.pdf')}
                className="w-full text-left p-3 bg-white rounded-lg border hover:bg-gray-50 transition-colors"
                disabled={isLoading}
              >
                <div className="font-medium text-gray-900">Einstein Paper (arXiv)</div>
                <div className="text-sm text-gray-600">https://arxiv.org/pdf/1709.00666.pdf</div>
              </button>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {processingResults ? (
            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <CheckCircle className="h-6 w-6 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-900">Processing Complete</h2>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-primary-600">
                      {processingResults.chunks_count}
                    </div>
                    <div className="text-sm text-gray-600">Text Chunks Created</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {processingResults.document_id}
                    </div>
                    <div className="text-sm text-gray-600">Document ID</div>
                  </div>
                </div>
                
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-green-900">Ready for RAG</h4>
                      <p className="text-green-700 text-sm mt-1">
                        Your document has been processed and is ready for question answering. 
                        You can now use the RAG Chat feature to ask questions about this document.
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => window.location.href = '/rag-chat'}
                    className="btn btn-primary flex-1"
                  >
                    Start RAG Chat
                  </button>
                  <button
                    onClick={() => setProcessingResults(null)}
                    className="btn btn-outline"
                  >
                    Process Another
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="text-center py-12">
                <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Document Processed</h3>
                <p className="text-gray-600">
                  Upload a PDF file or provide a URL to get started with document processing.
                </p>
              </div>
            </div>
          )}

          {/* Processing Info */}
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-start space-x-3">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900">How it works</h4>
                <ul className="text-blue-800 text-sm mt-2 space-y-1">
                  <li>• Text is extracted from your PDF document</li>
                  <li>• Content is split into optimized chunks for retrieval</li>
                  <li>• Embeddings are generated using sentence-transformers</li>
                  <li>• Data is stored in Neo4j with vector indexes</li>
                  <li>• Ready for hybrid search and RAG queries</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFProcessor;
