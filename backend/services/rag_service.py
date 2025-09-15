from typing import List, Dict, Any
from .embedding_service import EmbeddingService
from .neo4j_service import Neo4jService
from .gemini_service import GeminiService

class RAGService:
    def __init__(self, embedding_service: EmbeddingService, 
                 neo4j_service: Neo4jService, gemini_service: GeminiService):
        """
        Initialize RAG service
        
        Args:
            embedding_service: Service for generating embeddings
            neo4j_service: Service for Neo4j operations
            gemini_service: Service for LLM operations
        """
        self.embedding_service = embedding_service
        self.neo4j_service = neo4j_service
        self.gemini_service = gemini_service
    
    def vector_search(self, question: str, k: int = 4) -> List[Dict]:
        """
        Perform vector similarity search
        
        Args:
            question: User question
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            if not question or not question.strip():
                return []
            
            # Generate embedding for the question
            question_embedding = self.embedding_service.embed_single_text(question)
            
            if not question_embedding:
                print("Error: Failed to generate embedding for question")
                return []
            
            # Perform vector search using correct index name
            results = self.neo4j_service.vector_search(question_embedding, "chunk_embeddings", k)
            
            return results
            
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []
    
    def keyword_search(self, question: str, k: int = 4) -> List[Dict]:
        """
        Perform keyword search
        
        Args:
            question: User question
            k: Number of results to return
            
        Returns:
            List of matching documents
        """
        try:
            if not question or not question.strip():
                return []
            
            # Perform keyword search using correct index name
            results = self.neo4j_service.keyword_search(question, "chunk_fulltext", k)
            return results
            
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []
    
    def hybrid_search(self, question: str, k: int = 4) -> List[Dict]:
        """
        Perform hybrid search combining vector and keyword search
        
        Args:
            question: User question
            k: Number of results to return
            
        Returns:
            List of documents with combined scores
        """
        try:
            if not question or not question.strip():
                return []
            
            # Generate embedding for the question
            question_embedding = self.embedding_service.embed_single_text(question)
            
            if not question_embedding:
                print("Error: Failed to generate embedding for hybrid search")
                return []
            
            # Perform hybrid search
            results = self.neo4j_service.hybrid_search(question_embedding, question, k)
            
            return results
            
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            return []
    
    def generate_answer(self, question: str, documents: List[Dict]) -> str:
        """
        Generate answer using retrieved documents
        
        Args:
            question: User question
            documents: Retrieved documents
            
        Returns:
            Generated answer
        """
        try:
            if not documents:
                return "I don't have enough information to answer this question."
            
            # Prepare context from documents
            context_texts = [doc.get("text", "") for doc in documents if doc.get("text")]
            
            system_message = """You are an expert assistant that can only use the provided documents to respond to questions. 
            Be accurate and cite the information from the documents. If the documents don't contain enough information 
            to answer the question, say so clearly."""
            
            user_message = f"""
            Use the following documents to answer the question that will follow:
            {context_texts}
            
            ---
            
            The question to answer using information only from the above documents: {question}
            """
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
            
            answer = self.gemini_service.chat(messages)
            return answer
            
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def generate_stepback(self, question: str) -> str:
        """
        Generate a step-back question for better retrieval
        
        Args:
            question: Original question
            
        Returns:
            Step-back question
        """
        try:
            stepback_system_message = """
            You are an expert at world knowledge. Your task is to step back
            and paraphrase a question to a more generic step-back question, which
            is easier to answer. Here are a few examples:

            "input": "Could the members of The Police perform lawful arrests?"
            "output": "what can the members of The Police do?"

            "input": "Jan Sindel's was born in what country?"
            "output": "what is Jan Sindel's personal history?"
            
            "input": "What specific algorithm does company X use for recommendation?"
            "output": "How do recommendation systems work?"
            """
            
            messages = [
                {"role": "system", "content": stepback_system_message},
                {"role": "user", "content": question}
            ]
            
            step_back_question = self.gemini_service.chat(messages)
            return step_back_question.strip()
            
        except Exception as e:
            print(f"Error generating stepback question: {e}")
            return question  # Fallback to original question
    
    def parent_retrieval(self, question: str, k: int = 4) -> List[Dict]:
        """
        Perform parent retrieval using child embeddings
        
        Args:
            question: User question
            k: Number of results to return
            
        Returns:
            List of parent documents
        """
        try:
            if not question or not question.strip():
                return []
            
            # Generate embedding for the question
            question_embedding = self.embedding_service.embed_single_text(question)
            
            if not question_embedding:
                print("Error: Failed to generate embedding for parent retrieval")
                return []
            
            # Perform parent retrieval using correct index name
            results = self.neo4j_service.parent_retrieval(question_embedding, k, "child_chunks")
            
            return results
            
        except Exception as e:
            print(f"Error in parent retrieval: {e}")
            return []
    
    def stepback_rag_pipeline(self, question: str) -> Dict[str, Any]:
        """
        Perform complete step-back RAG pipeline
        
        Args:
            question: User question
            
        Returns:
            Dictionary with question, stepback question, documents, and answer
        """
        try:
            # Generate step-back question
            stepback_question = self.generate_stepback(question)
            
            # Retrieve documents using step-back question
            documents = self.parent_retrieval(stepback_question)
            
            # Generate answer using original question and retrieved documents
            answer = self.generate_answer(question, documents)
            
            return {
                "original_question": question,
                "stepback_question": stepback_question,
                "retrieved_documents": documents,
                "answer": answer,
                "search_type": "stepback_rag"
            }
            
        except Exception as e:
            return {
                "original_question": question,
                "error": f"Error in stepback RAG pipeline: {str(e)}"
            }
    
    def multi_query_rag(self, question: str, k: int = 4) -> Dict[str, Any]:
        """
        Perform multi-query RAG by generating multiple related questions
        
        Args:
            question: User question
            k: Number of results per query
            
        Returns:
            Dictionary with results from multiple queries
        """
        try:
            # Generate multiple related questions
            multi_query_prompt = f"""
            Generate 3 different versions of the following question that would help retrieve 
            relevant information from a document database. Make them more specific and focused:
            
            Original question: {question}
            
            Return only the 3 questions, one per line.
            """
            
            messages = [{"role": "user", "content": multi_query_prompt}]
            response = self.gemini_service.chat(messages)
            
            # Parse the generated questions
            generated_questions = [q.strip() for q in response.split('\n') if q.strip()]
            all_questions = [question] + generated_questions[:3]  # Include original + up to 3 generated
            
            # Retrieve documents for each question
            all_documents = []
            seen_texts = set()
            
            for q in all_questions:
                docs = self.hybrid_search(q, k)
                for doc in docs:
                    text = doc.get("text", "")
                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        all_documents.append(doc)
            
            # Generate answer using all retrieved documents
            answer = self.generate_answer(question, all_documents)
            
            return {
                "original_question": question,
                "generated_questions": generated_questions,
                "retrieved_documents": all_documents,
                "answer": answer,
                "search_type": "multi_query_rag"
            }
            
        except Exception as e:
            return {
                "original_question": question,
                "error": f"Error in multi-query RAG: {str(e)}"
            }
    
    def contextual_compression_rag(self, question: str, k: int = 8) -> Dict[str, Any]:
        """
        Perform RAG with contextual compression to filter relevant parts
        
        Args:
            question: User question
            k: Number of initial results to retrieve
            
        Returns:
            Dictionary with compressed context and answer
        """
        try:
            # Retrieve more documents initially
            documents = self.hybrid_search(question, k)
            
            if not documents:
                return {
                    "original_question": question,
                    "answer": "No relevant documents found.",
                    "search_type": "contextual_compression_rag"
                }
            
            # Compress each document to extract relevant parts
            compressed_docs = []
            
            for doc in documents:
                text = doc.get("text", "")
                if not text:
                    continue
                
                compression_prompt = f"""
                Given the following question and document, extract only the parts of the document 
                that are directly relevant to answering the question. If no part is relevant, return "NOT_RELEVANT".
                
                Question: {question}
                
                Document: {text}
                
                Relevant parts:
                """
                
                messages = [{"role": "user", "content": compression_prompt}]
                compressed_text = self.gemini_service.chat(messages)
                
                if compressed_text.strip() != "NOT_RELEVANT":
                    compressed_docs.append({
                        **doc,
                        "compressed_text": compressed_text.strip(),
                        "original_text": text
                    })
            
            # Generate answer using compressed documents
            if compressed_docs:
                context_texts = [doc.get("compressed_text", "") for doc in compressed_docs]
                
                system_message = """You are an expert assistant. Use the provided relevant document excerpts 
                to answer the question accurately and concisely."""
                
                user_message = f"""
                Relevant document excerpts:
                {context_texts}
                
                Question: {question}
                """
                
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
                
                answer = self.gemini_service.chat(messages)
            else:
                answer = "No relevant information found in the documents."
            
            return {
                "original_question": question,
                "compressed_documents": compressed_docs,
                "answer": answer,
                "search_type": "contextual_compression_rag"
            }
            
        except Exception as e:
            return {
                "original_question": question,
                "error": f"Error in contextual compression RAG: {str(e)}"
            }
    
    def test_rag_functionality(self, test_question: str = "What is the main topic of the documents?") -> Dict[str, Any]:
        """
        Comprehensive test of RAG functionality
        
        Args:
            test_question: Test question to use
            
        Returns:
            Dictionary with test results for all RAG methods
        """
        test_results = {
            "test_question": test_question,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "results": {}
        }
        
        try:
            # Test 1: Vector Search
            print("Testing vector search...")
            vector_results = self.vector_search(test_question, k=3)
            test_results["results"]["vector_search"] = {
                "success": True,
                "result_count": len(vector_results),
                "results": vector_results[:2] if vector_results else []  # Show first 2 results
            }
            
            # Test 2: Keyword Search
            print("Testing keyword search...")
            keyword_results = self.keyword_search(test_question, k=3)
            test_results["results"]["keyword_search"] = {
                "success": True,
                "result_count": len(keyword_results),
                "results": keyword_results[:2] if keyword_results else []
            }
            
            # Test 3: Hybrid Search
            print("Testing hybrid search...")
            hybrid_results = self.hybrid_search(test_question, k=3)
            test_results["results"]["hybrid_search"] = {
                "success": True,
                "result_count": len(hybrid_results),
                "results": hybrid_results[:2] if hybrid_results else []
            }
            
            # Test 4: Parent Retrieval
            print("Testing parent retrieval...")
            parent_results = self.parent_retrieval(test_question, k=3)
            test_results["results"]["parent_retrieval"] = {
                "success": True,
                "result_count": len(parent_results),
                "results": parent_results[:2] if parent_results else []
            }
            
            # Test 5: Step-back Generation
            print("Testing step-back generation...")
            stepback_question = self.generate_stepback(test_question)
            test_results["results"]["stepback_generation"] = {
                "success": True,
                "original_question": test_question,
                "stepback_question": stepback_question
            }
            
            # Test 6: Answer Generation (using hybrid search results)
            print("Testing answer generation...")
            if hybrid_results:
                answer = self.generate_answer(test_question, hybrid_results)
                test_results["results"]["answer_generation"] = {
                    "success": True,
                    "answer": answer[:200] + "..." if len(answer) > 200 else answer
                }
            else:
                test_results["results"]["answer_generation"] = {
                    "success": False,
                    "error": "No documents available for answer generation"
                }
            
            # Test 7: Step-back RAG Pipeline
            print("Testing step-back RAG pipeline...")
            stepback_pipeline = self.stepback_rag_pipeline(test_question)
            test_results["results"]["stepback_pipeline"] = {
                "success": "error" not in stepback_pipeline,
                "pipeline_result": stepback_pipeline
            }
            
            # Overall test status
            test_results["overall_success"] = all(
                result.get("success", False) 
                for result in test_results["results"].values()
            )
            
            print(f"RAG functionality test completed. Overall success: {test_results['overall_success']}")
            
        except Exception as e:
            test_results["overall_success"] = False
            test_results["error"] = f"Test failed with error: {str(e)}"
            print(f"RAG test failed: {e}")
        
        return test_results
    
    def get_available_documents_count(self) -> Dict[str, int]:
        """
        Get count of available documents in the database
        
        Returns:
            Dictionary with document counts
        """
        try:
            # Get chunk count
            chunk_query = "MATCH (c:Chunk) RETURN count(c) as chunk_count"
            chunk_result = self.neo4j_service.execute_query(chunk_query)
            chunk_count = chunk_result[0]["chunk_count"] if chunk_result else 0
            
            # Get document count
            doc_query = "MATCH (d:Document) RETURN count(d) as doc_count"
            doc_result = self.neo4j_service.execute_query(doc_query)
            doc_count = doc_result[0]["doc_count"] if doc_result else 0
            
            # Get parent count
            parent_query = "MATCH (p:Parent) RETURN count(p) as parent_count"
            parent_result = self.neo4j_service.execute_query(parent_query)
            parent_count = parent_result[0]["parent_count"] if parent_result else 0
            
            # Get child count
            child_query = "MATCH (c:__Child__) RETURN count(c) as child_count"
            child_result = self.neo4j_service.execute_query(child_query)
            child_count = child_result[0]["child_count"] if child_result else 0
            
            return {
                "documents": doc_count,
                "chunks": chunk_count,
                "parents": parent_count,
                "children": child_count,
                "total_chunks": chunk_count + child_count
            }
            
        except Exception as e:
            print(f"Error getting document counts: {e}")
            return {
                "documents": 0,
                "chunks": 0,
                "parents": 0,
                "children": 0,
                "total_chunks": 0,
                "error": str(e)
            }
