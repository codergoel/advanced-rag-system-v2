from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

from services.pdf_service import PDFService
from services.embedding_service import EmbeddingService
from services.neo4j_service import Neo4jService
from services.gemini_service import GeminiService
from services.rag_service import RAGService
from services.text2cypher_service import Text2CypherService
from services.entity_extraction_service import EntityExtractionService
from services.contract_extraction_service import ContractExtractionService
from services.graph_rag_service import GraphRAGService
from services.agentic_rag_service import AgenticRAGService
from services.knowledge_graph_construction_service import KnowledgeGraphConstructionService

load_dotenv()

app = FastAPI(title="Advanced RAG System", description="A comprehensive RAG system with multiple AI capabilities")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_service = PDFService()
embedding_service = EmbeddingService()
neo4j_service = Neo4jService()
gemini_service = GeminiService()
rag_service = RAGService(embedding_service, neo4j_service, gemini_service)
text2cypher_service = Text2CypherService(neo4j_service, gemini_service)
entity_extraction_service = EntityExtractionService(neo4j_service, gemini_service)
contract_extraction_service = ContractExtractionService(neo4j_service, gemini_service)
graph_rag_service = GraphRAGService(neo4j_service, gemini_service, embedding_service)
agentic_rag_service = AgenticRAGService(neo4j_service, gemini_service)
knowledge_graph_construction_service = KnowledgeGraphConstructionService(neo4j_service, gemini_service)

# Pydantic models
class URLRequest(BaseModel):
    url: str

class QuestionRequest(BaseModel):
    question: str
    search_type: Optional[str] = "hybrid"  # vector, keyword, hybrid

class Text2CypherRequest(BaseModel):
    question: str
    terminology: Optional[str] = ""
    examples: Optional[str] = ""

class EntityExtractionRequest(BaseModel):
    text: str
    entity_types: List[str] = ["PERSON", "ORGANIZATION", "LOCATION", "EVENT"]

class ContractRequest(BaseModel):
    contract_text: str

class KnowledgeGraphRequest(BaseModel):
    document: str

# Health check
@app.get("/")
async def root():
    return {"message": "Advanced RAG System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# PDF Processing endpoints
@app.post("/api/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    try:
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text and process
        text = pdf_service.extract_text(file_path)
        chunks = pdf_service.chunk_text(text)
        
        # Generate embeddings
        embeddings = embedding_service.embed_texts(chunks)
        
        # Store in Neo4j
        doc_id = file.filename.replace(".pdf", "")
        neo4j_service.store_document_chunks(doc_id, chunks, embeddings)
        
        return {
            "message": "PDF processed successfully",
            "document_id": doc_id,
            "chunks_count": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf/download")
async def download_pdf(request: URLRequest):
    """Download and process a PDF from URL"""
    try:
        # Download PDF
        file_path = pdf_service.download_pdf(request.url)
        
        # Extract text and process
        text = pdf_service.extract_text(file_path)
        chunks = pdf_service.chunk_text(text)
        
        # Generate embeddings
        embeddings = embedding_service.embed_texts(chunks)
        
        # Store in Neo4j
        doc_id = os.path.basename(file_path).replace(".pdf", "")
        neo4j_service.store_document_chunks(doc_id, chunks, embeddings)
        
        return {
            "message": "PDF downloaded and processed successfully",
            "document_id": doc_id,
            "chunks_count": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# RAG endpoints
@app.post("/api/rag/query")
async def rag_query(request: QuestionRequest):
    """Perform RAG query with different search types"""
    try:
        if request.search_type == "vector":
            results = rag_service.vector_search(request.question)
        elif request.search_type == "keyword":
            results = rag_service.keyword_search(request.question)
        elif request.search_type == "hybrid":
            results = rag_service.hybrid_search(request.question)
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
        
        # Generate answer using retrieved documents
        answer = rag_service.generate_answer(request.question, results)
        
        return {
            "question": request.question,
            "answer": answer,
            "retrieved_documents": results,
            "search_type": request.search_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/stepback")
async def stepback_rag_query(request: QuestionRequest):
    """Perform step-back RAG with parent-child chunking"""
    try:
        result = rag_service.stepback_rag_pipeline(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/test")
async def test_rag_functionality(request: QuestionRequest):
    """Test all RAG functionality comprehensively"""
    try:
        result = rag_service.test_rag_functionality(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/documents/count")
async def get_document_counts():
    """Get count of available documents in the database"""
    try:
        counts = rag_service.get_available_documents_count()
        return counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Text2Cypher endpoints
@app.post("/api/text2cypher/query")
async def text2cypher_query(request: Text2CypherRequest):
    """Convert natural language to Cypher query"""
    try:
        cypher_query = text2cypher_service.generate_cypher(
            request.question,
            request.terminology,
            request.examples
        )
        
        # Execute the query
        results = neo4j_service.execute_query(cypher_query)
        
        return {
            "question": request.question,
            "cypher_query": cypher_query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/text2cypher/schema")
async def get_database_schema():
    """Get the Neo4j database schema using APOC"""
    try:
        structured_schema = text2cypher_service.get_structured_schema()
        schema_string = text2cypher_service.get_schema_string(structured_schema)
        return {
            "structured_schema": structured_schema,
            "schema_string": schema_string
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text2cypher/load-movies")
async def load_movies_dataset():
    """Load the movies dataset into Neo4j"""
    try:
        result = text2cypher_service.load_movies_dataset()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Entity Extraction endpoints
@app.post("/api/entities/extract")
async def extract_entities(request: EntityExtractionRequest):
    """Extract entities from text and create knowledge graph"""
    try:
        entities, relationships = entity_extraction_service.extract_entities(
            request.text,
            request.entity_types
        )
        
        # Store in Neo4j
        entity_extraction_service.store_entities_and_relationships(entities, relationships)
        
        return {
            "entities": entities,
            "relationships": relationships,
            "entities_count": len(entities),
            "relationships_count": len(relationships)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities/graph")
async def get_entity_graph():
    """Get the entity graph visualization data"""
    try:
        graph_data = entity_extraction_service.get_graph_data()
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Contract Extraction endpoints
@app.post("/api/contracts/extract")
async def extract_contract_info(request: ContractRequest):
    """Extract structured information from contract text"""
    try:
        contract_info = contract_extraction_service.extract_contract_info(request.contract_text)
        
        # Store in Neo4j
        contract_extraction_service.store_contract_info(contract_info)
        
        return contract_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contracts/list")
async def list_contracts():
    """List all stored contracts"""
    try:
        contracts = contract_extraction_service.get_all_contracts()
        return {"contracts": contracts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Graph RAG endpoints
@app.post("/api/graph-rag/global")
async def global_graph_rag(request: QuestionRequest):
    """Perform global graph RAG using community summaries"""
    try:
        result = graph_rag_service.global_retriever(request.question)
        return {
            "question": request.question,
            "answer": result,
            "search_type": "global_graph_rag"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/graph-rag/local")
async def local_graph_rag(request: QuestionRequest):
    """Perform local graph RAG using entity embeddings"""
    try:
        result = graph_rag_service.local_search(request.question)
        return {
            "question": request.question,
            "answer": result,
            "search_type": "local_graph_rag"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/graph-rag/communities")
async def calculate_communities():
    """Calculate and store graph communities"""
    try:
        result = graph_rag_service.calculate_communities()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoints
@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        stats = neo4j_service.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Agentic RAG endpoints
@app.post("/api/agentic-rag/query")
async def agentic_rag_query(request: QuestionRequest):
    """Process a question through the agentic RAG system"""
    try:
        result = agentic_rag_service.process_question(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agentic-rag/tools")
async def get_agentic_rag_tools():
    """Get available retriever tools"""
    try:
        tools = agentic_rag_service.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge Graph Construction endpoints
@app.post("/api/knowledge-graph/extract")
async def extract_contract_info(request: KnowledgeGraphRequest):
    """Extract structured information from contract document"""
    try:
        result = knowledge_graph_construction_service.extract_contract_info(request.document)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge-graph/import")
async def import_contract_to_graph(request: KnowledgeGraphRequest):
    """Extract and import contract information into knowledge graph"""
    try:
        # First extract the contract information
        contract_data = knowledge_graph_construction_service.extract_contract_info(request.document)
        
        if "error" in contract_data:
            return contract_data
        
        # Then import it into the graph
        import_result = knowledge_graph_construction_service.import_contract_to_graph(contract_data)
        
        return {
            "extraction_result": contract_data,
            "import_result": import_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge-graph/sample-contract")
async def get_sample_contract():
    """Get sample contract text for demonstration"""
    try:
        sample_contract = knowledge_graph_construction_service.get_sample_contract()
        return {"sample_contract": sample_contract}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge-graph/data")
async def get_contract_graph_data():
    """Get contract graph data for visualization"""
    try:
        graph_data = knowledge_graph_construction_service.get_contract_graph_data()
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge-graph/query")
async def query_contracts(request: QuestionRequest):
    """Query the contract knowledge graph using natural language"""
    try:
        result = knowledge_graph_construction_service.query_contracts(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge-graph/constraints")
async def create_graph_constraints():
    """Create unique constraints and indexes for the knowledge graph"""
    try:
        result = knowledge_graph_construction_service.create_graph_constraints()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge-graph/statistics")
async def get_contract_statistics():
    """Get statistics about the contract knowledge graph"""
    try:
        stats = knowledge_graph_construction_service.get_contract_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge-graph/clear")
async def clear_contract_data():
    """Clear all contract-related data from the graph"""
    try:
        result = knowledge_graph_construction_service.clear_contract_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Database management endpoints
@app.post("/api/database/reset")
async def reset_database():
    """Reset the Neo4j database (clear all data)"""
    try:
        # Clear all nodes and relationships
        neo4j_service.execute_query("MATCH (n) DETACH DELETE n")
        
        # Recreate indexes
        neo4j_service._create_indexes()
        
        return {
            "message": "Database reset successfully",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
