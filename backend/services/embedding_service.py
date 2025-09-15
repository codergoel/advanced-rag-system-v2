from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import os

class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L12-v2"):
        """
        Initialize the embedding service with sentence-transformers model
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []
            
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # Convert to list of lists for JSON serialization
            return embeddings.tolist()
            
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []
    
    def embed_single_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector as list
        """
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)
            return embedding[0].tolist()
        except Exception as e:
            print(f"Error generating single embedding: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dimension
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[tuple]:
        """
        Find the most similar embeddings to a query embedding
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top similar embeddings to return
            
        Returns:
            List of tuples (index, similarity_score)
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate)
                similarities.append((i, similarity))
            
            # Sort by similarity score in descending order
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            print(f"Error finding similar embeddings: {e}")
            return []
    
    def batch_embed_with_metadata(self, texts_with_metadata: List[dict]) -> List[dict]:
        """
        Generate embeddings for texts with associated metadata
        
        Args:
            texts_with_metadata: List of dicts with 'text' and other metadata fields
            
        Returns:
            List of dicts with embeddings added
        """
        try:
            texts = [item['text'] for item in texts_with_metadata]
            embeddings = self.embed_texts(texts)
            
            result = []
            for i, item in enumerate(texts_with_metadata):
                item_with_embedding = item.copy()
                item_with_embedding['embedding'] = embeddings[i] if i < len(embeddings) else []
                result.append(item_with_embedding)
            
            return result
            
        except Exception as e:
            print(f"Error in batch embedding with metadata: {e}")
            return texts_with_metadata
    
    def normalize_embeddings(self, embeddings: List[List[float]]) -> List[List[float]]:
        """
        Normalize embeddings to unit length
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            List of normalized embedding vectors
        """
        try:
            normalized = []
            
            for embedding in embeddings:
                vec = np.array(embedding)
                norm = np.linalg.norm(vec)
                
                if norm > 0:
                    normalized_vec = vec / norm
                    normalized.append(normalized_vec.tolist())
                else:
                    normalized.append(embedding)
            
            return normalized
            
        except Exception as e:
            print(f"Error normalizing embeddings: {e}")
            return embeddings
    
    def get_model_info(self) -> dict:
        """
        Get information about the current embedding model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dimension,
            "max_sequence_length": getattr(self.model, 'max_seq_length', 'Unknown')
        }
