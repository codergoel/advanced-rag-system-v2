import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// PDF Processing APIs
export const pdfAPI = {
  uploadPDF: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/pdf/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  downloadPDF: (url) => {
    return api.post('/api/pdf/download', { url });
  },
};

// RAG APIs
export const ragAPI = {
  query: (question, searchType = 'hybrid') => {
    return api.post('/api/rag/query', { question, search_type: searchType });
  },
  
  stepbackQuery: (question) => {
    return api.post('/api/rag/stepback', { question });
  },
};

// Text2Cypher APIs
export const text2cypherAPI = {
  query: (question, terminology = '', examples = '') => {
    return api.post('/api/text2cypher/query', { question, terminology, examples });
  },
  
  getSchema: () => {
    return api.get('/api/text2cypher/schema');
  },
  
  loadMoviesDataset: () => {
    return api.post('/api/text2cypher/load-movies');
  },
};

export const agenticRAGAPI = {
  query: (question) => {
    return api.post('/api/agentic-rag/query', { question });
  },
  
  getTools: () => {
    return api.get('/api/agentic-rag/tools');
  },
};

// Entity Extraction APIs
export const entityAPI = {
  extract: (text, entityTypes = ['PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT']) => {
    return api.post('/api/entities/extract', { text, entity_types: entityTypes });
  },
  
  getGraph: () => {
    return api.get('/api/entities/graph');
  },
};

// Contract Extraction APIs
export const contractAPI = {
  extract: (contractText) => {
    return api.post('/api/contracts/extract', { contract_text: contractText });
  },
  
  list: () => {
    return api.get('/api/contracts/list');
  },
};

// Graph RAG APIs
export const graphRAGAPI = {
  globalQuery: (question) => {
    return api.post('/api/graph-rag/global', { question });
  },
  
  localQuery: (question) => {
    return api.post('/api/graph-rag/local', { question });
  },
  
  calculateCommunities: () => {
    return api.post('/api/graph-rag/communities');
  },
};

// Statistics APIs
export const statsAPI = {
  getStats: () => {
    return api.get('/api/stats');
  },
  
  getHealth: () => {
    return api.get('/health');
  },
};

// Knowledge Graph Construction APIs
export const knowledgeGraphAPI = {
  extract: (document) => {
    return api.post('/api/knowledge-graph/extract', { document });
  },
  
  import: (document) => {
    return api.post('/api/knowledge-graph/import', { document });
  },
  
  getSampleContract: () => {
    return api.get('/api/knowledge-graph/sample-contract');
  },
  
  getGraphData: () => {
    return api.get('/api/knowledge-graph/data');
  },
  
  query: (question) => {
    return api.post('/api/knowledge-graph/query', { question });
  },
  
  createConstraints: () => {
    return api.post('/api/knowledge-graph/constraints');
  },
  
  getStatistics: () => {
    return api.get('/api/knowledge-graph/statistics');
  },
  
  clear: () => {
    return api.post('/api/knowledge-graph/clear');
  },
};

// Database Management APIs
export const databaseAPI = {
  reset: () => {
    return api.post('/api/database/reset');
  },
};

export default api;
