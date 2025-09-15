# Advanced RAG System with Knowledge Graph Construction

A comprehensive Retrieval-Augmented Generation (RAG) system with multiple AI capabilities including vector search, hybrid search, step-back prompting, knowledge graph construction, and contract extraction.

## 🚀 Features

### Core RAG Capabilities
- **Vector Similarity Search** - Semantic search using sentence transformers
- **Full-Text Keyword Search** - Traditional keyword-based search
- **Hybrid Search** - Combines vector and keyword search for optimal results
- **Step-Back Prompting** - Generates broader questions for better retrieval
- **Parent-Child Chunking** - Hierarchical document structure for better context

### Advanced Features
- **Knowledge Graph Construction** - Extract structured information from legal documents
- **Contract Analysis** - Parse and analyze contract terms, parties, and relationships
- **Text2Cypher** - Convert natural language to Neo4j Cypher queries
- **Entity Extraction** - Extract entities and relationships from text
- **Graph RAG** - Global and local graph-based retrieval
- **Agentic RAG** - Multi-tool agent-based retrieval system

### Frontend Playground
- Interactive web interface for all features
- Real-time testing and visualization
- Knowledge graph visualization
- Contract extraction playground

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Neo4j** - Graph database for knowledge storage
- **Sentence Transformers** - Embedding generation
- **Google Gemini** - Large Language Model
- **PDF Processing** - Document parsing and chunking

### Frontend
- **React** - Modern JavaScript framework
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.9+**
- **Node.js 16+** and npm
- **Neo4j Database** (local or cloud instance)
- **Git**

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd advanced-rag-system
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the backend directory:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# Optional: OpenAI API (if using OpenAI embeddings)
OPENAI_API_KEY=your_openai_api_key
```

#### Start Neo4j Database
Make sure Neo4j is running on your system:
- **Local**: Start Neo4j Desktop or Docker container
- **Cloud**: Use Neo4j AuraDB or other cloud providers

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Start the Application

#### Start Backend Server
```bash
cd backend
source venv/bin/activate
python main.py
```
The backend will be available at `http://localhost:8000`

#### Start Frontend Development Server
```bash
cd frontend
npm start
```
The frontend will be available at `http://localhost:3000`

## 🎯 Usage

### 1. Knowledge Graph Construction Playground

Navigate to `/knowledge-graph-construction` to:
- Extract structured information from legal documents
- Import contracts into the knowledge graph
- Query the graph with natural language
- Visualize relationships and statistics

### 2. RAG Chat Interface

Use `/rag-chat` to:
- Upload PDF documents
- Ask questions about your documents
- Use different search strategies (vector, keyword, hybrid)
- Test step-back prompting

### 3. Text2Cypher

Visit `/text2cypher` to:
- Convert natural language to Cypher queries
- Load sample datasets
- Test query generation

### 4. Entity Extraction

Use `/entity-extraction` to:
- Extract entities from text
- Build knowledge graphs
- Visualize entity relationships

## 📊 API Endpoints

### RAG Endpoints
- `POST /api/rag/query` - Perform RAG query
- `POST /api/rag/stepback` - Step-back RAG pipeline
- `POST /api/rag/test` - Test all RAG functionality
- `GET /api/rag/documents/count` - Get document statistics

### Knowledge Graph Endpoints
- `POST /api/knowledge-graph/extract` - Extract contract information
- `POST /api/knowledge-graph/import` - Import to knowledge graph
- `GET /api/knowledge-graph/data` - Get graph data
- `POST /api/knowledge-graph/query` - Query the graph

### Text2Cypher Endpoints
- `POST /api/text2cypher/query` - Generate Cypher from natural language
- `GET /api/text2cypher/schema` - Get database schema
- `POST /api/text2cypher/load-movies` - Load sample dataset

## 🧪 Testing

### Test RAG Functionality
```bash
curl -X POST http://localhost:8000/api/rag/test \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the documents?"}'
```

### Test Knowledge Graph Construction
```bash
curl -X POST http://localhost:8000/api/knowledge-graph/extract \
  -H "Content-Type: application/json" \
  -d '{"document": "Your contract text here..."}'
```

## 📁 Project Structure

```
advanced-rag-system/
├── backend/
│   ├── services/
│   │   ├── rag_service.py              # Core RAG functionality
│   │   ├── knowledge_graph_construction_service.py
│   │   ├── text2cypher_service.py
│   │   ├── entity_extraction_service.py
│   │   ├── neo4j_service.py           # Database operations
│   │   ├── embedding_service.py       # Vector embeddings
│   │   ├── gemini_service.py          # LLM integration
│   │   └── pdf_service.py             # Document processing
│   ├── main.py                        # FastAPI application
│   ├── config.py                      # Configuration
│   └── requirements.txt               # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/                     # React components
│   │   ├── services/                  # API services
│   │   └── components/                # Reusable components
│   ├── package.json                   # Node dependencies
│   └── tailwind.config.js            # Styling configuration
├── README.md                          # This file
└── requirements.txt                   # Python dependencies
```

## 🔍 Key Algorithms Implemented

### 1. Vector Search
- Uses sentence-transformers for embedding generation
- Cosine similarity for document ranking
- Configurable result limits

### 2. Hybrid Search
- Combines vector and keyword search results
- Score normalization for fair comparison
- Deduplication of results

### 3. Step-Back Prompting
- Generates broader questions for better retrieval
- Uses LLM to create step-back questions
- Improves answer quality through better context

### 4. Parent-Child Chunking
- Hierarchical document structure
- Child chunks for detailed retrieval
- Parent chunks for broader context

## 🚨 Troubleshooting

### Common Issues

1. **Neo4j Connection Error**
   - Ensure Neo4j is running
   - Check connection credentials in `.env`
   - Verify network connectivity

2. **Embedding Generation Fails**
   - Check internet connection (for model download)
   - Verify sentence-transformers installation
   - Check available memory

3. **Frontend Build Errors**
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility
   - Verify all dependencies are installed

4. **API Endpoints Not Found**
   - Ensure backend server is running
   - Check for any startup errors
   - Verify port 8000 is available

### Performance Optimization

1. **Neo4j Indexes**
   - Vector indexes are created automatically
   - Full-text indexes for keyword search
   - Monitor query performance

2. **Embedding Caching**
   - Consider caching embeddings for repeated queries
   - Use batch processing for large documents

3. **Memory Management**
   - Monitor memory usage during large document processing
   - Consider chunking large documents

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Neo4j** for graph database capabilities
- **Google Gemini** for LLM integration
- **Sentence Transformers** for embedding generation
- **FastAPI** for the robust backend framework
- **React** for the modern frontend interface

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the API documentation at `http://localhost:8000/docs`

---

**Happy RAG-ing! 🚀**