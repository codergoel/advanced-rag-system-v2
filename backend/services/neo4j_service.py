from neo4j import GraphDatabase, basic_auth
from typing import List, Dict, Any, Optional, Tuple
import os
import json
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class Neo4jService:
    def __init__(self):
        """
        Initialize Neo4j service
        """
        # Neo4j connection parameters
        self.uri = NEO4J_URI
        self.username = NEO4J_USERNAME
        self.password = NEO4J_PASSWORD
        
        # Initialize driver
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=basic_auth(self.username, self.password),
            notifications_min_severity="OFF"
        )
        
        # Initialize indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes for the application"""
        try:
            # Vector indexes - using existing names from the database
            self.execute_query("""
                CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
                FOR (c:Chunk)
                ON c.embedding
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 384,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            
            self.execute_query("""
                CREATE VECTOR INDEX child_chunks IF NOT EXISTS
                FOR (c:__Child__)
                ON c.embedding
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 384,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            
            self.execute_query("""
                CREATE VECTOR INDEX entities IF NOT EXISTS
                FOR (n:__Entity__)
                ON n.embedding
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 384,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            
            # Fulltext indexes - using existing names from the database
            try:
                self.execute_query("CREATE FULLTEXT INDEX chunk_fulltext IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text]")
            except:
                pass  # Index might already exist
            
            try:
                self.execute_query("CREATE FULLTEXT INDEX ftParentChunk IF NOT EXISTS FOR (p:Parent) ON EACH [p.text]")
            except:
                pass
            
            # Constraints
            self.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Contract) REQUIRE c.id IS UNIQUE")
            self.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE")
            self.execute_query("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.fullAddress IS UNIQUE")
            
        except Exception as e:
            print(f"Error creating indexes: {e}")
    
    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a Cypher query
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        import time
        
        try:
            if parameters is None:
                parameters = {}
            
            records, summary, keys = self.driver.execute_query(query, parameters)
            return [record.data() for record in records]
            
        except Exception as e:
            error_msg = str(e)
            if "AuthenticationRateLimit" in error_msg:
                print(f"Authentication rate limit hit, waiting 5 seconds...")
                time.sleep(5)
                return []
            elif "Unauthorized" in error_msg:
                print(f"Authentication failed. Check Neo4j credentials.")
                return []
            else:
                print(f"Error executing query: {e}")
                return []
    
    def store_document_chunks(self, doc_id: str, chunks: List[str], embeddings: List[List[float]]):
        """
        Store document chunks with embeddings in Neo4j
        
        Args:
            doc_id: Document identifier
            chunks: List of text chunks
            embeddings: List of embedding vectors
        """
        try:
            # Create document node and chunks
            cypher_query = '''
            MERGE (doc:Document {id: $doc_id})
            WITH doc, $chunks as chunks, $embeddings as embeddings, range(0, size($chunks) - 1) AS indices
            UNWIND indices AS i
            MERGE (c:Chunk {id: $doc_id + '-' + toString(i)})
            SET c.text = chunks[i], 
                c.embedding = embeddings[i],
                c.index = i,
                c.doc_id = $doc_id
            MERGE (doc)-[:HAS_CHUNK]->(c)
            '''
            
            self.execute_query(cypher_query, {
                "doc_id": doc_id,
                "chunks": chunks,
                "embeddings": embeddings
            })
            
        except Exception as e:
            print(f"Error storing document chunks: {e}")
    
    def store_parent_child_chunks(self, doc_id: str, parent_child_pairs: List[Tuple[str, List[str]]], 
                                 child_embeddings: List[List[List[float]]]):
        """
        Store parent-child chunk structure
        
        Args:
            doc_id: Document identifier
            parent_child_pairs: List of (parent_text, [child_texts]) tuples
            child_embeddings: Embeddings for child chunks
        """
        try:
            # Clear existing data for this document
            self.execute_query("MATCH (doc:PDF {id: $doc_id})-[:HAS_PARENT]->(p:Parent)-[:HAS_CHILD]->(c:Child) DETACH DELETE p, c", {"doc_id": doc_id})
            
            cypher_import_query = """
            MERGE (pdf:PDF {id: $pdf_id})
            MERGE (p:Parent {id: $pdf_id + '-' + $parent_id})
            SET p.text = $parent_text
            MERGE (pdf)-[:HAS_PARENT]->(p)
            WITH p, $children AS children, $embeddings as embeddings
            UNWIND range(0, size(children) - 1) AS child_index
            MERGE (c:Child {id: $pdf_id + '-' + $parent_id + '-' + toString(child_index)})
            SET c.text = children[child_index], 
                c.embedding = embeddings[child_index],
                c.index = child_index
            MERGE (p)-[:HAS_CHILD]->(c)
            """
            
            for i, (parent_text, child_texts) in enumerate(parent_child_pairs):
                if i < len(child_embeddings):
                    self.execute_query(cypher_import_query, {
                        "pdf_id": doc_id,
                        "parent_id": str(i),
                        "parent_text": parent_text,
                        "children": child_texts,
                        "embeddings": child_embeddings[i]
                    })
                    
        except Exception as e:
            print(f"Error storing parent-child chunks: {e}")
    
    def vector_search(self, query_embedding: List[float], index_name: str = "chunk_embeddings", k: int = 4) -> List[Dict]:
        """
        Perform vector similarity search
        
        Args:
            query_embedding: Query embedding vector
            index_name: Name of the vector index
            k: Number of results to return
            
        Returns:
            List of similar documents with scores
        """
        try:
            query = '''
            CALL db.index.vector.queryNodes($index_name, $k, $query_embedding) 
            YIELD node AS hits, score
            RETURN hits.text AS text, score, hits.index AS index, hits.id AS id
            ORDER BY score DESC
            '''
            
            return self.execute_query(query, {
                "index_name": index_name,
                "k": k,
                "query_embedding": query_embedding
            })
            
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []
    
    def keyword_search(self, query: str, index_name: str = "chunk_fulltext", k: int = 4) -> List[Dict]:
        """
        Perform keyword search using fulltext index
        
        Args:
            query: Search query
            index_name: Name of the fulltext index
            k: Number of results to return
            
        Returns:
            List of matching documents with scores
        """
        try:
            cypher_query = '''
            CALL db.index.fulltext.queryNodes($index_name, $query, {limit: $k})
            YIELD node, score
            RETURN node.text AS text, score, node.index AS index, node.id AS id
            ORDER BY score DESC
            '''
            
            return self.execute_query(cypher_query, {
                "index_name": index_name,
                "query": query,
                "k": k
            })
            
        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []
    
    def hybrid_search(self, query_embedding: List[float], query: str, k: int = 4) -> List[Dict]:
        """
        Perform hybrid search combining vector and keyword search
        
        Args:
            query_embedding: Query embedding vector
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of documents with combined scores
        """
        try:
            hybrid_query = '''
            CALL {
                // vector index
                CALL db.index.vector.queryNodes('chunk_embeddings', $k, $query_embedding) 
                YIELD node, score
                WITH collect({node:node, score:score}) AS nodes, max(score) AS max
                UNWIND nodes AS n
                // We use 0 as min
                RETURN n.node AS node, (n.score / max) AS score
                UNION
                // keyword index
                CALL db.index.fulltext.queryNodes('chunk_fulltext', $query, {limit: $k})
                YIELD node, score
                WITH collect({node:node, score:score}) AS nodes, max(score) AS max
                UNWIND nodes AS n
                // We use 0 as min
                RETURN n.node AS node, (n.score / max) AS score
            }
            // dedup
            WITH node, max(score) AS score 
            ORDER BY score DESC 
            LIMIT $k
            RETURN node.text AS text, score, node.index AS index, node.id AS id
            '''
            
            return self.execute_query(hybrid_query, {
                "query_embedding": query_embedding,
                "query": query,
                "k": k
            })
            
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            return []
    
    def parent_retrieval(self, query_embedding: List[float], k: int = 4, index_name: str = "child_chunks") -> List[Dict]:
        """
        Perform parent retrieval using child embeddings
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            index_name: Name of the vector index for child chunks
            
        Returns:
            List of parent documents
        """
        try:
            retrieval_query = """
            CALL db.index.vector.queryNodes($index_name, $k_mult, $query_embedding)
            YIELD node, score
            MATCH (node)<-[:HAS_CHILD]-(parent)
            WITH parent, max(score) AS score
            RETURN parent.text AS text, score
            ORDER BY score DESC
            LIMIT toInteger($k)
            """
            
            return self.execute_query(retrieval_query, {
                "query_embedding": query_embedding,
                "k": k,
                "k_mult": k * 4,
                "index_name": "child_chunks"
            })
            
        except Exception as e:
            print(f"Error in parent retrieval: {e}")
            return []
    
    def store_entities_and_relationships(self, entities: List[Dict], relationships: List[Dict]):
        """
        Store extracted entities and relationships
        
        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries
        """
        try:
            # Store entities
            if entities:
                entity_query = """
                UNWIND $entities AS entity
                MERGE (e:__Entity__ {name: entity.entity_name})
                SET e += {
                    type: entity.entity_type,
                    description: entity.entity_description
                }
                """
                self.execute_query(entity_query, {"entities": entities})
            
            # Store relationships
            if relationships:
                rel_query = """
                UNWIND $relationships AS rel
                MERGE (s:__Entity__ {name: rel.source_entity})
                MERGE (t:__Entity__ {name: rel.target_entity})
                CREATE (s)-[r:RELATIONSHIP {
                    description: rel.relationship_description,
                    strength: rel.relationship_strength
                }]->(t)
                """
                self.execute_query(rel_query, {"relationships": relationships})
                
        except Exception as e:
            print(f"Error storing entities and relationships: {e}")
    
    def get_schema(self) -> str:
        """
        Get database schema information
        
        Returns:
            Schema string
        """
        try:
            # Get node labels and properties
            node_query = """
            CALL apoc.meta.data()
            YIELD label, other, elementType, type, property
            WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
            WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
            RETURN {labels: nodeLabels, properties: properties} AS output
            """
            
            # Get relationships
            rel_query = """
            CALL apoc.meta.data()
            YIELD label, other, elementType, type, property
            WHERE type = "RELATIONSHIP" AND elementType = "node"
            UNWIND other AS other_node
            RETURN {start: label, type: property, end: toString(other_node)} AS output
            """
            
            nodes = self.execute_query(node_query)
            relationships = self.execute_query(rel_query)
            
            schema_parts = ["Node properties:"]
            for node in nodes:
                output = node.get("output", {})
                label = output.get("labels", "")
                props = output.get("properties", [])
                prop_str = ", ".join([f"{p['property']}: {p['type']}" for p in props])
                schema_parts.append(f"{label} {{{prop_str}}}")
            
            schema_parts.append("\nThe relationships:")
            for rel in relationships:
                output = rel.get("output", {})
                schema_parts.append(f"(:{output.get('start', '')})-[:{output.get('type', '')}]->(:{output.get('end', '')})")
            
            return "\n".join(schema_parts)
            
        except Exception as e:
            return f"Error getting schema: {str(e)}"
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {}
            
            # Count nodes by label
            node_counts = self.execute_query("""
                MATCH (n)
                RETURN labels(n)[0] AS label, count(n) AS count
                ORDER BY count DESC
            """)
            stats["node_counts"] = {item["label"]: item["count"] for item in node_counts}
            
            # Count relationships by type
            rel_counts = self.execute_query("""
                MATCH ()-[r]->()
                RETURN type(r) AS type, count(r) AS count
                ORDER BY count DESC
            """)
            stats["relationship_counts"] = {item["type"]: item["count"] for item in rel_counts}
            
            # Total counts
            total_nodes = self.execute_query("MATCH (n) RETURN count(n) AS count")
            total_rels = self.execute_query("MATCH ()-[r]->() RETURN count(r) AS count")
            
            stats["total_nodes"] = total_nodes[0]["count"] if total_nodes else 0
            stats["total_relationships"] = total_rels[0]["count"] if total_rels else 0
            
            return stats
            
        except Exception as e:
            return {"error": f"Error getting statistics: {str(e)}"}
    
    def close(self):
        """Close the Neo4j driver"""
        if self.driver:
            self.driver.close()
