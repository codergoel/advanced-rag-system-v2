from typing import List, Dict, Any, Optional
import json
from .neo4j_service import Neo4jService
from .gemini_service import GeminiService
from .embedding_service import EmbeddingService

class GraphRAGService:
    def __init__(self, neo4j_service: Neo4jService, gemini_service: GeminiService, 
                 embedding_service: EmbeddingService):
        """
        Initialize Graph RAG service
        
        Args:
            neo4j_service: Service for Neo4j operations
            gemini_service: Service for LLM operations
            embedding_service: Service for embeddings
        """
        self.neo4j_service = neo4j_service
        self.gemini_service = gemini_service
        self.embedding_service = embedding_service
    
    def calculate_communities(self) -> Dict[str, Any]:
        """
        Calculate graph communities using Louvain algorithm
        
        Returns:
            Community calculation results
        """
        try:
            # Drop existing graph projection if it exists
            try:
                self.neo4j_service.execute_query("CALL gds.graph.drop('entity')")
            except:
                pass  # Graph might not exist
            
            # Create graph projection
            projection_query = """
            MATCH (source:__Entity__)-[r:RELATIONSHIP]->(target:__Entity__)
            WITH gds.graph.project('entity', source, target, {}, {undirectedRelationshipTypes: ['*']}) AS g
            RETURN g.graphName AS graph, g.nodeCount AS nodes, g.relationshipCount AS rels
            """
            
            projection_result = self.neo4j_service.execute_query(projection_query)
            
            # Run Louvain community detection
            louvain_query = """
            CALL gds.louvain.write("entity", {writeProperty:"louvain"})
            YIELD communityCount, communityDistribution
            RETURN communityCount, communityDistribution
            """
            
            louvain_result = self.neo4j_service.execute_query(louvain_query)
            
            if louvain_result:
                result = louvain_result[0]
                return {
                    "communityCount": result.get("communityCount", 0),
                    "communityDistribution": result.get("communityDistribution", {}),
                    "projection": projection_result[0] if projection_result else {}
                }
            else:
                return {"error": "Failed to calculate communities"}
                
        except Exception as e:
            return {"error": f"Error calculating communities: {str(e)}"}
    
    def get_community_info(self) -> List[Dict[str, Any]]:
        """
        Get information about detected communities
        
        Returns:
            List of community information
        """
        try:
            community_query = """
            MATCH (e:__Entity__)
            WHERE e.louvain IS NOT NULL
            WITH e.louvain AS louvain, collect(e) AS nodes
            WHERE size(nodes) > 1
            CALL apoc.path.subgraphAll(nodes[0], {
                whitelistNodes: nodes
            })
            YIELD relationships
            RETURN louvain AS communityId,
                   [n in nodes | {
                       id: n.name, 
                       description: coalesce(n.summary, n.description[0], ''), 
                       type: coalesce(n.type, 'UNKNOWN')
                   }] AS nodes,
                   [r in relationships | {
                       start: startNode(r).name, 
                       type: type(r), 
                       end: endNode(r).name, 
                       description: coalesce(r.summary, r.description, '')
                   }] AS rels
            """
            
            return self.neo4j_service.execute_query(community_query)
            
        except Exception as e:
            print(f"Error getting community info: {e}")
            return []
    
    def summarize_communities(self) -> Dict[str, Any]:
        """
        Generate summaries for detected communities
        
        Returns:
            Community summarization results
        """
        try:
            community_info = self.get_community_info()
            
            communities = []
            for community in community_info:
                # Generate community summary
                summary = self._generate_community_summary(
                    community["nodes"], 
                    community["rels"]
                )
                
                if summary and "error" not in summary:
                    communities.append({
                        "community": summary,
                        "communityId": community["communityId"],
                        "nodes": [node["id"] for node in community["nodes"]]
                    })
            
            # Store community summaries
            if communities:
                self._store_community_summaries(communities)
            
            return {
                "summarized_communities": len(communities),
                "communities": communities
            }
            
        except Exception as e:
            return {"error": f"Error summarizing communities: {str(e)}"}
    
    def _generate_community_summary(self, nodes: List[Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """
        Generate summary for a single community
        
        Args:
            nodes: List of nodes in the community
            relationships: List of relationships in the community
            
        Returns:
            Community summary
        """
        try:
            # Format community data for prompt
            nodes_text = "\n".join([
                f"- {node['id']} ({node['type']}): {node['description']}"
                for node in nodes
            ])
            
            relationships_text = "\n".join([
                f"- {rel['start']} -> {rel['end']}: {rel['description']}"
                for rel in relationships
            ])
            
            input_text = f"""Entities:
{nodes_text}

Relationships:
{relationships_text}"""
            
            community_prompt = f"""
You are an AI assistant that helps analyze communities within a knowledge graph. 
Write a comprehensive report of a community, given a list of entities and their relationships.

The report should include the following sections:
- TITLE: community's name that represents its key entities - title should be short but specific
- SUMMARY: An executive summary of the community's overall structure and key information
- IMPACT SEVERITY RATING: a float score between 0-10 that represents the importance of this community
- RATING EXPLANATION: Give a single sentence explanation of the impact severity rating
- DETAILED FINDINGS: A list of 3-5 key insights about the community

Return output as a well-formed JSON with the following format:
{{
    "title": "<report_title>",
    "summary": "<executive_summary>",
    "rating": <impact_severity_rating>,
    "rating_explanation": "<rating_explanation>",
    "findings": [
        {{
            "summary": "<insight_1_summary>",
            "explanation": "<insight_1_explanation>"
        }},
        {{
            "summary": "<insight_2_summary>", 
            "explanation": "<insight_2_explanation>"
        }}
    ]
}}

Community Data:
{input_text}
"""
            
            messages = [{"role": "user", "content": community_prompt}]
            response = self.gemini_service.chat(messages, model="gemini-1.5-pro")
            
            # Parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"error": "Could not parse community summary"}
                    
        except Exception as e:
            return {"error": f"Error generating community summary: {str(e)}"}
    
    def _store_community_summaries(self, communities: List[Dict[str, Any]]):
        """
        Store community summaries in Neo4j
        
        Args:
            communities: List of community summaries
        """
        try:
            import_query = """
            UNWIND $communities AS row
            MERGE (c:__Community__ {communityId: row.communityId})
            SET c.title = row.community.title,
                c.summary = row.community.summary,
                c.rating = row.community.rating,
                c.rating_explanation = row.community.rating_explanation,
                c.findings = [f IN row.community.findings | f.summary + ': ' + f.explanation]
            WITH c, row
            UNWIND row.nodes AS node
            MERGE (n:__Entity__ {name: node})
            MERGE (n)-[:IN_COMMUNITY]->(c)
            """
            
            self.neo4j_service.execute_query(import_query, {"communities": communities})
            
        except Exception as e:
            print(f"Error storing community summaries: {e}")
    
    def global_retriever(self, query: str, rating_threshold: float = 5.0) -> str:
        """
        Perform global retrieval using community summaries
        
        Args:
            query: User query
            rating_threshold: Minimum community rating to include
            
        Returns:
            Generated answer
        """
        try:
            # Get high-rated community summaries
            community_query = """
            MATCH (c:__Community__)
            WHERE c.rating >= $rating
            RETURN c.summary AS summary, c.title AS title, c.rating AS rating
            ORDER BY c.rating DESC
            """
            
            communities = self.neo4j_service.execute_query(community_query, {"rating": rating_threshold})
            
            if not communities:
                return "No relevant community information found for this query."
            
            # Generate intermediate results for each community
            intermediate_results = []
            for community in communities:
                map_prompt = f"""
You are a helpful assistant responding to questions about data in the provided community summary.

Generate a response consisting of key points that respond to the user's question, 
summarizing all relevant information from the community data.

If you don't know the answer or if the community data doesn't contain sufficient information 
to provide an answer, just say so. Do not make anything up.

Community Summary:
Title: {community['title']}
Summary: {community['summary']}
Rating: {community['rating']}

User Question: {query}

Response:
"""
                
                messages = [{"role": "user", "content": map_prompt}]
                intermediate_response = self.gemini_service.chat(messages)
                intermediate_results.append({
                    "community": community['title'],
                    "response": intermediate_response,
                    "rating": community['rating']
                })
            
            # Combine intermediate results
            reduce_prompt = f"""
You are a helpful assistant responding to questions by synthesizing information from multiple community analyses.

Generate a comprehensive response that responds to the user's question by combining and 
summarizing all the relevant information from the community analyses below.

Remove any irrelevant information and merge the relevant information into a comprehensive answer.
If you don't know the answer or if the provided information doesn't contain sufficient information 
to provide an answer, just say so. Do not make anything up.

Community Analyses:
{chr(10).join([f"Community: {r['community']} (Rating: {r['rating']}){chr(10)}{r['response']}{chr(10)}" for r in intermediate_results])}

User Question: {query}

Comprehensive Response:
"""
            
            messages = [{"role": "user", "content": reduce_prompt}]
            final_answer = self.gemini_service.chat(messages)
            
            return final_answer
            
        except Exception as e:
            return f"Error in global retrieval: {str(e)}"
    
    def local_search(self, query: str, k_entities: int = 5, top_chunks: int = 3, 
                    top_communities: int = 3, top_relationships: int = 3) -> str:
        """
        Perform local search using entity embeddings
        
        Args:
            query: User query
            k_entities: Number of entities to retrieve
            top_chunks: Number of chunks to include
            top_communities: Number of communities to include
            top_relationships: Number of relationships to include
            
        Returns:
            Generated answer
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_single_text(query)
            
            # Local search query
            local_search_query = """
            CALL db.index.vector.queryNodes('entities', $k, $embedding)
            YIELD node, score
            WITH collect(node) as nodes
            WITH collect {
                UNWIND nodes as n
                MATCH (n)<-[:HAS_ENTITY]->(c:__Chunk__)
                WITH c, count(distinct n) as freq
                RETURN c.text AS chunkText
                ORDER BY freq DESC
                LIMIT $topChunks
            } AS text_mapping,
            collect {
                UNWIND nodes as n
                MATCH (n)-[:IN_COMMUNITY]->(c:__Community__)
                WITH c, c.rating as rating
                RETURN c.summary 
                ORDER BY rating DESC
                LIMIT $topCommunities
            } AS report_mapping,
            collect {
                UNWIND nodes as n
                MATCH (n)-[r:SUMMARIZED_RELATIONSHIP]-(m) 
                WHERE m IN nodes
                RETURN r.summary AS descriptionText
                ORDER BY r.strength DESC 
                LIMIT $topInsideRels
            } as insideRels,
            collect {
                UNWIND nodes as n
                RETURN coalesce(n.summary, n.description[0], '') AS descriptionText
            } as entities
            RETURN {
                Chunks: text_mapping, 
                Reports: report_mapping, 
                Relationships: insideRels, 
                Entities: entities
            } AS text
            """
            
            context_result = self.neo4j_service.execute_query(local_search_query, {
                "k": k_entities,
                "embedding": query_embedding,
                "topChunks": top_chunks,
                "topCommunities": top_communities,
                "topInsideRels": top_relationships
            })
            
            if not context_result:
                return "No relevant information found for this query."
            
            context_data = context_result[0]["text"]
            
            # Generate answer using retrieved context
            local_prompt = f"""
You are a helpful assistant responding to questions about data in the provided context.

Generate a comprehensive response that responds to the user's question, summarizing all 
relevant information from the context data and incorporating any relevant general knowledge.

If you don't know the answer, just say so. Do not make anything up.

Context Data:
Chunks: {context_data.get('Chunks', [])}
Community Reports: {context_data.get('Reports', [])}
Relationships: {context_data.get('Relationships', [])}
Entities: {context_data.get('Entities', [])}

User Question: {query}

Response:
"""
            
            messages = [{"role": "user", "content": local_prompt}]
            final_answer = self.gemini_service.chat(messages)
            
            return final_answer
            
        except Exception as e:
            return f"Error in local search: {str(e)}"
    
    def create_entity_embeddings(self) -> Dict[str, Any]:
        """
        Create embeddings for entities based on their summaries
        
        Returns:
            Results of embedding creation
        """
        try:
            # Get entities with summaries
            entities_query = """
            MATCH (e:__Entity__)
            WHERE e.summary IS NOT NULL
            RETURN e.name AS name, e.summary AS summary
            """
            
            entities = self.neo4j_service.execute_query(entities_query)
            
            if not entities:
                return {"error": "No entities with summaries found"}
            
            # Generate embeddings
            entity_data = []
            for entity in entities:
                embedding = self.embedding_service.embed_single_text(entity["summary"])
                entity_data.append({
                    "name": entity["name"],
                    "embedding": embedding
                })
            
            # Store embeddings
            update_query = """
            UNWIND $data AS row
            MATCH (e:__Entity__ {name: row.name})
            CALL db.create.setNodeVectorProperty(e, 'embedding', row.embedding)
            """
            
            self.neo4j_service.execute_query(update_query, {"data": entity_data})
            
            return {
                "entities_processed": len(entity_data),
                "message": "Entity embeddings created successfully"
            }
            
        except Exception as e:
            return {"error": f"Error creating entity embeddings: {str(e)}"}
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive graph statistics
        
        Returns:
            Dictionary with graph statistics
        """
        try:
            stats = {}
            
            # Basic counts
            basic_query = """
            MATCH (e:__Entity__)
            RETURN 'entities' AS type, count(e) AS count
            UNION
            MATCH ()-[:RELATIONSHIP]->()
            RETURN 'relationships' AS type, count(*) AS count
            UNION
            MATCH (c:__Community__)
            RETURN 'communities' AS type, count(c) AS count
            """
            
            basic_results = self.neo4j_service.execute_query(basic_query)
            for result in basic_results:
                stats[result["type"]] = result["count"]
            
            # Community distribution
            community_dist_query = """
            MATCH (c:__Community__)
            RETURN c.rating AS rating, count(c) AS count
            ORDER BY rating DESC
            """
            
            community_dist = self.neo4j_service.execute_query(community_dist_query)
            stats["community_rating_distribution"] = community_dist
            
            # Top entities by connections
            top_entities_query = """
            MATCH (e:__Entity__)
            RETURN e.name AS name, e.type AS type, 
                   size((e)-[:RELATIONSHIP]-()) AS connections
            ORDER BY connections DESC
            LIMIT 10
            """
            
            top_entities = self.neo4j_service.execute_query(top_entities_query)
            stats["top_connected_entities"] = top_entities
            
            return stats
            
        except Exception as e:
            return {"error": f"Error getting graph statistics: {str(e)}"}
