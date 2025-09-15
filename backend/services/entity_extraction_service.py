from typing import List, Dict, Any, Tuple
import json
import re
from .neo4j_service import Neo4jService
from .gemini_service import GeminiService

class EntityExtractionService:
    def __init__(self, neo4j_service: Neo4jService, gemini_service: GeminiService):
        """
        Initialize Entity Extraction service
        
        Args:
            neo4j_service: Service for Neo4j operations
            gemini_service: Service for LLM operations
        """
        self.neo4j_service = neo4j_service
        self.gemini_service = gemini_service
        
        # Default entity types
        self.default_entity_types = [
            "PERSON",
            "ORGANIZATION", 
            "LOCATION",
            "EVENT",
            "PRODUCT",
            "CONCEPT"
        ]
    
    def extract_entities(self, text: str, entity_types: List[str] = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract entities and relationships from text
        
        Args:
            text: Text to extract entities from
            entity_types: List of entity types to extract
            
        Returns:
            Tuple of (entities, relationships)
        """
        try:
            if not entity_types:
                entity_types = self.default_entity_types
            
            # Create extraction prompt
            extraction_prompt = self._create_extraction_prompt(entity_types, text)
            
            # Generate extraction using Gemini
            messages = [{"role": "user", "content": extraction_prompt}]
            output = self.gemini_service.chat(messages, model="gemini-1.5-pro")
            
            # Parse the output
            entities, relationships = self._parse_extraction_output(output)
            
            return entities, relationships
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return [], []
    
    def _create_extraction_prompt(self, entity_types: List[str], text: str) -> str:
        """
        Create the entity extraction prompt
        
        Args:
            entity_types: List of entity types
            text: Input text
            
        Returns:
            Formatted prompt
        """
        entity_types_str = ", ".join(entity_types)
        
        prompt = f"""
-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types_str}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"|<entity_name>|<entity_type>|<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity (1-10)
Format each relationship as ("relationship"|<source_entity>|<target_entity>|<relationship_description>|<relationship_strength>)

3. Return output in English as a single list of all the entities and relationships identified in steps 1 and 2. Use **|** as the list delimiter.

4. When finished, output <|COMPLETE|>

######################
-Real Data-
######################
Entity_types: {entity_types_str}
Text: {text}
######################
Output:"""
        
        return prompt
    
    def _parse_extraction_output(self, output_str: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse the extraction output into entities and relationships
        
        Args:
            output_str: Raw output from LLM
            
        Returns:
            Tuple of (entities, relationships)
        """
        try:
            entities = []
            relationships = []
            
            # Remove completion marker
            if "<|COMPLETE|>" in output_str:
                output_str = output_str.replace("<|COMPLETE|>", "")
            
            # Split by delimiter
            records = [r.strip() for r in output_str.split("|") if r.strip()]
            
            current_record = []
            for item in records:
                if item.startswith('("entity"') or item.startswith('("relationship"'):
                    if current_record:
                        self._process_record(current_record, entities, relationships)
                    current_record = [item]
                else:
                    if current_record:
                        current_record.append(item)
            
            # Process the last record
            if current_record:
                self._process_record(current_record, entities, relationships)
            
            return entities, relationships
            
        except Exception as e:
            print(f"Error parsing extraction output: {e}")
            return [], []
    
    def _process_record(self, record_parts: List[str], entities: List[Dict], relationships: List[Dict]):
        """
        Process a single record (entity or relationship)
        
        Args:
            record_parts: Parts of the record
            entities: List to append entities to
            relationships: List to append relationships to
        """
        try:
            if not record_parts:
                return
            
            first_part = record_parts[0].strip()
            
            if '"entity"' in first_part:
                # Parse entity
                if len(record_parts) >= 4:
                    entity_name = record_parts[1].strip(' "')
                    entity_type = record_parts[2].strip(' "')
                    entity_description = record_parts[3].strip(' ")')
                    
                    entities.append({
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "entity_description": entity_description
                    })
            
            elif '"relationship"' in first_part:
                # Parse relationship
                if len(record_parts) >= 5:
                    source_entity = record_parts[1].strip(' "')
                    target_entity = record_parts[2].strip(' "')
                    relationship_description = record_parts[3].strip(' "')
                    
                    # Parse strength
                    try:
                        strength_str = record_parts[4].strip(' ")')
                        relationship_strength = float(strength_str)
                    except (ValueError, IndexError):
                        relationship_strength = 5.0  # Default strength
                    
                    relationships.append({
                        "source_entity": source_entity,
                        "target_entity": target_entity,
                        "relationship_description": relationship_description,
                        "relationship_strength": relationship_strength
                    })
                    
        except Exception as e:
            print(f"Error processing record: {e}")
    
    def store_entities_and_relationships(self, entities: List[Dict], relationships: List[Dict], 
                                       chunk_id: str = None, book_id: str = None):
        """
        Store entities and relationships in Neo4j
        
        Args:
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries
            chunk_id: Optional chunk identifier
            book_id: Optional book identifier
        """
        try:
            # Store entities with chunk relationship if provided
            if entities:
                if chunk_id is not None:
                    # Store with chunk relationship
                    entity_query = """
                    MERGE (c:__Chunk__ {id: $chunk_id})
                    WITH c
                    UNWIND $entities AS entity
                    MERGE (e:__Entity__ {name: entity.entity_name})
                    SET e += {
                        type: entity.entity_type,
                        description: coalesce(e.description, []) + [entity.entity_description]
                    }
                    MERGE (e)<-[:HAS_ENTITY]-(c)
                    """
                    self.neo4j_service.execute_query(entity_query, {
                        "entities": entities,
                        "chunk_id": chunk_id
                    })
                else:
                    # Store without chunk relationship
                    entity_query = """
                    UNWIND $entities AS entity
                    MERGE (e:__Entity__ {name: entity.entity_name})
                    SET e += {
                        type: entity.entity_type,
                        description: coalesce(e.description, []) + [entity.entity_description]
                    }
                    """
                    self.neo4j_service.execute_query(entity_query, {"entities": entities})
            
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
                self.neo4j_service.execute_query(rel_query, {"relationships": relationships})
                
        except Exception as e:
            print(f"Error storing entities and relationships: {e}")
    
    def get_graph_data(self) -> Dict[str, Any]:
        """
        Get graph data for visualization
        
        Returns:
            Dictionary with nodes and edges for graph visualization
        """
        try:
            # Get entities (nodes)
            entity_query = """
            MATCH (e:__Entity__)
            RETURN e.name AS name, e.type AS type, e.description AS description,
                   size((e)-[:RELATIONSHIP]-()) AS degree
            ORDER BY degree DESC
            LIMIT 100
            """
            entities = self.neo4j_service.execute_query(entity_query)
            
            # Get relationships (edges)
            relationship_query = """
            MATCH (s:__Entity__)-[r:RELATIONSHIP]->(t:__Entity__)
            RETURN s.name AS source, t.name AS target, 
                   r.description AS description, r.strength AS strength
            LIMIT 200
            """
            relationships = self.neo4j_service.execute_query(relationship_query)
            
            # Format for visualization
            nodes = []
            for entity in entities:
                nodes.append({
                    "id": entity["name"],
                    "label": entity["name"],
                    "type": entity.get("type", "UNKNOWN"),
                    "description": entity.get("description", [""])[0] if entity.get("description") else "",
                    "degree": entity.get("degree", 0)
                })
            
            edges = []
            for rel in relationships:
                edges.append({
                    "source": rel["source"],
                    "target": rel["target"],
                    "description": rel.get("description", ""),
                    "strength": rel.get("strength", 1)
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges)
                }
            }
            
        except Exception as e:
            return {"error": f"Error getting graph data: {str(e)}"}
    
    def summarize_entities(self) -> Dict[str, Any]:
        """
        Summarize entities that have multiple descriptions
        
        Returns:
            Summary results
        """
        try:
            # Find entities with multiple descriptions
            candidates_query = """
            MATCH (e:__Entity__) 
            WHERE size(e.description) > 1 
            RETURN e.name AS entity_name, e.description AS description_list
            """
            candidates = self.neo4j_service.execute_query(candidates_query)
            
            summaries = []
            for candidate in candidates:
                entity_name = candidate["entity_name"]
                description_list = candidate["description_list"]
                
                # Generate summary
                summary_prompt = f"""
                You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
                Given an entity and a list of descriptions, all related to the same entity.
                Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
                If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
                Make sure it is written in third person, and include the entity name so we have the full context.

                Entity: {entity_name}
                Description List: {description_list}
                
                Summary:
                """
                
                messages = [{"role": "user", "content": summary_prompt}]
                summary = self.gemini_service.chat(messages)
                
                summaries.append({
                    "entity": entity_name,
                    "summary": summary.strip()
                })
            
            # Update entities with summaries
            if summaries:
                update_query = """
                UNWIND $summaries AS item
                MATCH (e:__Entity__ {name: item.entity})
                SET e.summary = item.summary
                """
                self.neo4j_service.execute_query(update_query, {"summaries": summaries})
            
            return {
                "summarized_entities": len(summaries),
                "summaries": summaries
            }
            
        except Exception as e:
            return {"error": f"Error summarizing entities: {str(e)}"}
    
    def get_entity_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extracted entities
        
        Returns:
            Dictionary with entity statistics
        """
        try:
            stats = {}
            
            # Count entities by type
            type_query = """
            MATCH (e:__Entity__)
            RETURN e.type AS type, count(e) AS count
            ORDER BY count DESC
            """
            type_counts = self.neo4j_service.execute_query(type_query)
            stats["entity_types"] = {item["type"]: item["count"] for item in type_counts}
            
            # Count relationships
            rel_query = """
            MATCH ()-[r:RELATIONSHIP]->()
            RETURN count(r) AS total_relationships
            """
            rel_count = self.neo4j_service.execute_query(rel_query)
            stats["total_relationships"] = rel_count[0]["total_relationships"] if rel_count else 0
            
            # Top connected entities
            connected_query = """
            MATCH (e:__Entity__)
            RETURN e.name AS name, e.type AS type, 
                   size((e)-[:RELATIONSHIP]-()) AS connections
            ORDER BY connections DESC
            LIMIT 10
            """
            top_connected = self.neo4j_service.execute_query(connected_query)
            stats["top_connected_entities"] = top_connected
            
            return stats
            
        except Exception as e:
            return {"error": f"Error getting entity statistics: {str(e)}"}
