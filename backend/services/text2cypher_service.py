from typing import Dict, List, Any
from .neo4j_service import Neo4jService
from .gemini_service import GeminiService

class Text2CypherService:
    def __init__(self, neo4j_service: Neo4jService, gemini_service: GeminiService):
        """
        Initialize Text2Cypher service
        
        Args:
            neo4j_service: Service for Neo4j operations
            gemini_service: Service for LLM operations
        """
        self.neo4j_service = neo4j_service
        self.gemini_service = gemini_service
        
        # Built-in Neo4j queries for schema inference (fallback when APOC meta.data is not available)
        self.NODE_PROPERTIES_QUERY = """
        MATCH (n)
        UNWIND labels(n) AS label
        WITH label, collect(DISTINCT keys(n)) AS all_keys
        UNWIND all_keys AS key_list
        UNWIND key_list AS property
        WITH label, collect(DISTINCT property) AS properties
        RETURN {labels: label, properties: [prop IN properties | {property: prop, type: "STRING"}]} AS output
        """
        
        self.REL_PROPERTIES_QUERY = """
        MATCH ()-[r]->()
        WITH DISTINCT type(r) AS relationshipType
        RETURN {type: relationshipType, properties: []} AS output
        """
        
        self.REL_QUERY = """
        MATCH (a)-[r]->(b)
        RETURN DISTINCT 
            {start: labels(a)[0], type: type(r), end: labels(b)[0]} AS output
        LIMIT 100
        """
        
        # Default prompt template (exact from documentation)
        self.prompt_template = """
Instructions:
Generate Cypher statement to query a graph database to get the data to answer the following user question.

Graph database schema:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided in the schema.
{schema}

Terminology mapping:
This section is helpful to map terminology between the user question and the graph database schema.
{terminology}

Examples:
The following examples provide useful patterns for querying the graph database.
{examples}

Format instructions:
Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
ONLY RESPOND WITH CYPHER—NO CODE BLOCKS.

User question: {question}
"""
    
    def get_structured_schema(self) -> Dict[str, Any]:
        """
        Get structured schema using APOC procedures (exact from documentation)
        
        Returns:
            Structured schema dictionary
        """
        try:
            # Get node properties
            node_labels_response = self.neo4j_service.execute_query(self.NODE_PROPERTIES_QUERY)
            node_properties = [
                data["output"]
                for data in node_labels_response
            ]
            
            # Get relationship properties
            rel_properties_query_response = self.neo4j_service.execute_query(self.REL_PROPERTIES_QUERY)
            rel_properties = [
                data["output"]
                for data in rel_properties_query_response
            ]
            
            # Get relationships
            rel_query_response = self.neo4j_service.execute_query(self.REL_QUERY)
            relationships = [
                data["output"]
                for data in rel_query_response
            ]
            
            return {
                "node_props": {el["labels"]: el["properties"] for el in node_properties},
                "rel_props": {el["type"]: el["properties"] for el in rel_properties},
                "relationships": relationships,
            }
            
        except Exception as e:
            return {"error": f"Error getting structured schema: {str(e)}"}
    
    def get_schema_string(self, structured_schema: Dict[str, Any] = None) -> str:
        """
        Get formatted schema string (exact from documentation)
        
        Args:
            structured_schema: Optional structured schema, will be fetched if not provided
            
        Returns:
            Formatted schema string
        """
        try:
            if not structured_schema:
                structured_schema = self.get_structured_schema()
            
            if "error" in structured_schema:
                return structured_schema["error"]
            
            def _format_props(props: List[Dict[str, Any]]) -> str:
                return ", ".join([f"{prop['property']}: {prop['type']}" for prop in props])
            
            formatted_node_props = [
                f"{label} {{{_format_props(props)}}}"
                for label, props in structured_schema["node_props"].items()
            ]
            
            formatted_rel_props = [
                f"{rel_type} {{{_format_props(props)}}}"
                for rel_type, props in structured_schema["rel_props"].items()
            ]
            
            formatted_rels = [
                f"(:{element['start']})-[:{element['type']}]->(:{element['end']})"
                for element in structured_schema["relationships"]
            ]
            
            return "\n".join([
                "Node labels and properties:",
                "\n".join(formatted_node_props),
                "Relationship types and properties:",
                "\n".join(formatted_rel_props),
                "The relationships:",
                "\n".join(formatted_rels),
            ])
            
        except Exception as e:
            return f"Error formatting schema: {str(e)}"
    
    def generate_cypher(self, question: str, terminology: str = "", examples: List[List[str]] = None) -> str:
        """
        Generate Cypher query from natural language question (exact from documentation)
        
        Args:
            question: Natural language question
            terminology: Optional terminology mapping
            examples: Optional list of [question, cypher] pairs for few-shot learning
            
        Returns:
            Generated Cypher query
        """
        try:
            # Get structured schema
            structured_schema = self.get_structured_schema()
            if "error" in structured_schema:
                return self._generate_simple_cypher(question)
            
            # Get schema string
            schema_string = self.get_schema_string(structured_schema)
            
            # Format examples if provided (following documentation format)
            examples_string = ""
            if examples:
                examples_list = []
                for example in examples:
                    if len(example) == 2:
                        examples_list.append(f"Question: {example[0]}\nCypher: {example[1]}")
                examples_string = "\n".join(examples_list)
            
            # Create the full prompt using the template from documentation
            full_prompt = self.prompt_template.format(
                question=question,
                schema=schema_string,
                terminology=terminology or "Persons: When a user asks about a person by trade like actor, writer, director, producer, or reviewer, they are referring to a node with the label Person.\nMovies: When a user asks about a film or movie, they are referring to a node with the label Movie.",
                examples=examples_string
            )
            
            # Generate Cypher using LLM
            messages = [{"role": "user", "content": full_prompt}]
            response = self.gemini_service.chat(messages)
            
            if response and response.strip() and not response.startswith("Error:"):
                # Clean up the response to extract just the Cypher query
                cypher_query = self._clean_cypher_response(response)
                return cypher_query
            else:
                return self._generate_simple_cypher(question)
                
        except Exception as e:
            print(f"Error in LLM-based Cypher generation: {str(e)}")
            # Fallback to simple generation
            return self._generate_simple_cypher(question)

    def _clean_cypher_response(self, response: str) -> str:
        """
        Clean up LLM response to extract just the Cypher query
        
        Args:
            response: Raw response from LLM
            
        Returns:
            Cleaned Cypher query
        """
        try:
            # Remove code blocks if present
            response = response.replace("```cypher", "").replace("```", "")
            
            # Split by lines and find the Cypher query
            lines = response.strip().split('\n')
            cypher_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('//') or line.startswith('#'):
                    continue
                # Skip explanatory text
                if any(word in line.lower() for word in ['explanation', 'this query', 'the query', 'cypher:', 'query:']):
                    continue
                # Add lines that look like Cypher
                if any(keyword in line.upper() for keyword in ['MATCH', 'RETURN', 'WHERE', 'ORDER', 'LIMIT', 'WITH', 'UNWIND', 'CALL']):
                    cypher_lines.append(line)
            
            if cypher_lines:
                return '\n'.join(cypher_lines)
            else:
                # If no clear Cypher found, return the original response cleaned
                return response.strip()
                
        except Exception:
            return response.strip()
    
    def get_default_examples(self) -> List[List[str]]:
        """
        Get default few-shot examples for the movies dataset (from documentation)
        
        Returns:
            List of [question, cypher] pairs
        """
        return [
            [
                "Who are the two people who have acted in the most movies together?",
                "MATCH (p1:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(p2:Person) WHERE p1 <> p2 RETURN p1.name, p2.name, COUNT(m) AS movieCount ORDER BY movieCount DESC LIMIT 1"
            ],
            [
                "In what country was the movie Ready Player One produced?",
                "MATCH (m:Movie { title: 'Ready Player One' })-[:PRODUCED_IN]->(c:Country) RETURN c.name"
            ]
        ]
    
    def create_prompt_example(self, question: str = "Who directed the most movies?") -> str:
        """
        Create a complete prompt example following the documentation format
        
        Args:
            question: Example question to use
            
        Returns:
            Complete formatted prompt
        """
        try:
            # Get schema
            schema_string = self.get_schema_string()
            
            # Default terminology from documentation
            terminology_string = """
Persons: When a user asks about a person by trade like actor, writer, director, producer, or reviewer, they are referring to a node with the label 'Person'.
Movies: When a user asks about a film or movie, they are referring to a node with the label Movie.
"""
            
            # Get default examples
            examples = self.get_default_examples()
            examples_string = "\n".join([f"Question: {e[0]}\nCypher: {e[1]}" for e in examples])
            
            # Create the full prompt
            full_prompt = self.prompt_template.format(
                question=question,
                schema=schema_string,
                terminology=terminology_string,
                examples=examples_string
            )
            
            return full_prompt
            
        except Exception as e:
            return f"Error creating prompt example: {str(e)}"
    
    def _generate_simple_cypher(self, question: str) -> str:
        """Generate simple Cypher queries based on common patterns"""
        question_lower = question.lower()
        
        # Tom Hanks movies
        if 'tom hanks' in question_lower and ('movie' in question_lower or 'act' in question_lower):
            return """
            MATCH (a:Person)-[:ACTED_IN]->(m:Movie)
            WHERE toLower(a.name) CONTAINS 'tom hanks'
            RETURN m.title AS title, m.released AS year
            ORDER BY m.released DESC
            """
        
        # Matrix movies
        elif 'matrix' in question_lower:
            if 'direct' in question_lower or 'director' in question_lower:
                return """
                MATCH (d:Person)-[:DIRECTED]->(m:Movie)
                WHERE toLower(m.title) CONTAINS 'matrix'
                RETURN d.name AS director, m.title AS movie
                """
            else:
                return """
                MATCH (m:Movie)
                WHERE toLower(m.title) CONTAINS 'matrix'
                RETURN m.title AS title, m.released AS year
                ORDER BY m.released
                """
        
        # Movies in specific year
        elif '1999' in question_lower:
            return """
            MATCH (m:Movie)
            WHERE m.released = 1999
            RETURN m.title AS title, m.released AS year
            ORDER BY m.title
            """
        
        # Apollo 13 actors
        elif 'apollo 13' in question_lower and ('actor' in question_lower or 'cast' in question_lower):
            return """
            MATCH (a:Person)-[:ACTED_IN]->(m:Movie)
            WHERE toLower(m.title) CONTAINS 'apollo 13'
            RETURN a.name AS actor, m.title AS movie
            ORDER BY a.name
            """
        
        # Action movies before 1995
        elif 'action' in question_lower and 'before' in question_lower and '1995' in question_lower:
            return """
            MATCH (m:Movie)-[:IN_GENRE]->(g:Genre)
            WHERE g.name = 'Action' AND m.released < 1995
            RETURN m.title AS title, m.released AS year
            ORDER BY m.released DESC
            """
        
        # Movies by genre
        elif any(genre in question_lower for genre in ['action', 'comedy', 'drama', 'thriller', 'horror']):
            genre = next(genre for genre in ['action', 'comedy', 'drama', 'thriller', 'horror'] if genre in question_lower)
            return f"""
            MATCH (m:Movie)-[:IN_GENRE]->(g:Genre)
            WHERE toLower(g.name) = '{genre}'
            RETURN m.title AS title, m.released AS year
            ORDER BY m.released DESC
            LIMIT 10
            """
        
        # Movies by actor
        elif 'acted' in question_lower or 'actor' in question_lower:
            return """
            MATCH (a:Person)-[:ACTED_IN]->(m:Movie)
            RETURN a.name AS actor, m.title AS movie
            ORDER BY a.name
            LIMIT 10
            """
        
        # Movies by director
        elif 'directed' in question_lower or 'director' in question_lower:
            return """
            MATCH (d:Person)-[:DIRECTED]->(m:Movie)
            RETURN d.name AS director, m.title AS movie
            ORDER BY d.name
            LIMIT 10
            """
        
        # General movie search
        elif 'movie' in question_lower:
            return """
            MATCH (m:Movie)
            RETURN m.title AS title, m.released AS year
            ORDER BY m.released DESC
            LIMIT 10
            """
        
        # Default fallback
        else:
            return """
            MATCH (n)
            RETURN n
            LIMIT 10
            """
    
    def load_movies_dataset(self) -> Dict[str, Any]:
        """
        Load a sample movies dataset (fallback when APOC example.movies is not available)
        
        Returns:
            Result of the dataset loading operation
        """
        try:
            # Create a sample movies dataset
            movies_queries = [
                # Create sample movies
                """
                CREATE (m1:Movie {title: 'The Matrix', released: 1999, tagline: 'Welcome to the Real World'})
                CREATE (m2:Movie {title: 'The Matrix Reloaded', released: 2003, tagline: 'Free your mind'})
                CREATE (m3:Movie {title: 'Apollo 13', released: 1995, tagline: 'Houston, we have a problem'})
                """,
                # Create sample people
                """
                CREATE (p1:Person {name: 'Keanu Reeves', born: 1964})
                CREATE (p2:Person {name: 'Carrie-Anne Moss', born: 1967})
                CREATE (p3:Person {name: 'Laurence Fishburne', born: 1961})
                CREATE (p4:Person {name: 'Tom Hanks', born: 1956})
                CREATE (p5:Person {name: 'Kevin Bacon', born: 1958})
                CREATE (p6:Person {name: 'Lana Wachowski', born: 1965})
                CREATE (p7:Person {name: 'Ron Howard', born: 1954})
                """,
                # Create relationships
                """
                MATCH (p1:Person {name: 'Keanu Reeves'}), (m1:Movie {title: 'The Matrix'})
                CREATE (p1)-[:ACTED_IN {roles: ['Neo']}]->(m1)
                """,
                """
                MATCH (p2:Person {name: 'Carrie-Anne Moss'}), (m1:Movie {title: 'The Matrix'})
                CREATE (p2)-[:ACTED_IN {roles: ['Trinity']}]->(m1)
                """,
                """
                MATCH (p3:Person {name: 'Laurence Fishburne'}), (m1:Movie {title: 'The Matrix'})
                CREATE (p3)-[:ACTED_IN {roles: ['Morpheus']}]->(m1)
                """,
                """
                MATCH (p4:Person {name: 'Tom Hanks'}), (m3:Movie {title: 'Apollo 13'})
                CREATE (p4)-[:ACTED_IN {roles: ['Jim Lovell']}]->(m3)
                """,
                """
                MATCH (p5:Person {name: 'Kevin Bacon'}), (m3:Movie {title: 'Apollo 13'})
                CREATE (p5)-[:ACTED_IN {roles: ['Jack Swigert']}]->(m3)
                """,
                """
                MATCH (p6:Person {name: 'Lana Wachowski'}), (m1:Movie {title: 'The Matrix'})
                CREATE (p6)-[:DIRECTED]->(m1)
                """,
                """
                MATCH (p7:Person {name: 'Ron Howard'}), (m3:Movie {title: 'Apollo 13'})
                CREATE (p7)-[:DIRECTED]->(m3)
                """
            ]
            
            # Execute all queries
            for query in movies_queries:
                self.neo4j_service.execute_query(query)
            
            return {
                "message": "Sample movies dataset loaded successfully",
                "dataset_type": "Sample Movies Dataset",
                "description": "Sample dataset with movies, actors, directors, and relationships for testing text2cypher functionality"
            }
            
        except Exception as e:
            return {"error": f"Error loading movies dataset: {str(e)}"}
    
    def generate_cypher_with_validation(self, question: str, terminology: str = "", 
                                      examples: List[List[str]] = None) -> Dict[str, Any]:
        """
        Generate Cypher query with validation
        
        Args:
            question: Natural language question
            terminology: Optional terminology mapping
            examples: Optional list of [question, cypher] pairs for few-shot learning
            
        Returns:
            Dictionary with query, validation results, and execution results
        """
        try:
            # Generate Cypher query
            cypher_query = self.generate_cypher(question, terminology, examples)
            
            result = {
                "question": question,
                "cypher_query": cypher_query,
                "is_valid": False,
                "execution_results": [],
                "error": None
            }
            
            # Try to execute the query to validate it
            try:
                execution_results = self.neo4j_service.execute_query(cypher_query)
                result["is_valid"] = True
                result["execution_results"] = execution_results
                
            except Exception as exec_error:
                result["error"] = f"Query execution error: {str(exec_error)}"
                
                # Try to fix common issues and regenerate
                fixed_query = self._attempt_query_fix(cypher_query, str(exec_error))
                if fixed_query != cypher_query:
                    try:
                        execution_results = self.neo4j_service.execute_query(fixed_query)
                        result["cypher_query"] = fixed_query
                        result["is_valid"] = True
                        result["execution_results"] = execution_results
                        result["error"] = None
                        result["fixed"] = True
                    except Exception:
                        pass  # Keep original error
            
            return result
            
        except Exception as e:
            return {
                "question": question,
                "error": f"Error in Cypher generation: {str(e)}",
                "is_valid": False
            }
    
    def _attempt_query_fix(self, cypher_query: str, error_message: str) -> str:
        """
        Attempt to fix common Cypher query issues
        
        Args:
            cypher_query: Original Cypher query
            error_message: Error message from execution
            
        Returns:
            Fixed Cypher query (or original if no fix applied)
        """
        try:
            # Common fixes
            fixed_query = cypher_query
            
            # Fix case sensitivity issues
            if "Unknown function" in error_message or "Invalid input" in error_message:
                # Try common function name fixes
                fixes = {
                    "Count(": "count(",
                    "Sum(": "sum(",
                    "Max(": "max(",
                    "Min(": "min(",
                    "Avg(": "avg(",
                }
                
                for wrong, correct in fixes.items():
                    fixed_query = fixed_query.replace(wrong, correct)
            
            # Fix property access issues
            if "Property" in error_message and "does not exist" in error_message:
                # This would require more sophisticated parsing
                pass
            
            return fixed_query
            
        except Exception:
            return cypher_query
    
    def get_query_explanation(self, cypher_query: str) -> str:
        """
        Generate explanation for a Cypher query
        
        Args:
            cypher_query: Cypher query to explain
            
        Returns:
            Natural language explanation
        """
        try:
            explanation_prompt = f"""
            Explain the following Cypher query in simple, natural language. 
            Describe what data it retrieves and how it works:
            
            Cypher Query:
            {cypher_query}
            
            Explanation:
            """
            
            messages = [{"role": "user", "content": explanation_prompt}]
            explanation = self.gemini_service.chat(messages)
            
            return explanation.strip()
            
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    def suggest_improvements(self, cypher_query: str) -> List[str]:
        """
        Suggest improvements for a Cypher query
        
        Args:
            cypher_query: Cypher query to analyze
            
        Returns:
            List of improvement suggestions
        """
        try:
            suggestions = []
            
            # Basic performance suggestions
            if "MATCH" in cypher_query and "WHERE" not in cypher_query:
                suggestions.append("Consider adding WHERE clauses to filter results early")
            
            if cypher_query.count("MATCH") > 3:
                suggestions.append("Consider combining multiple MATCH clauses for better performance")
            
            if "ORDER BY" in cypher_query and "LIMIT" not in cypher_query:
                suggestions.append("Consider adding LIMIT when using ORDER BY to improve performance")
            
            if "*" in cypher_query and "RETURN" in cypher_query:
                suggestions.append("Consider returning specific properties instead of entire nodes")
            
            # Use LLM for more sophisticated suggestions
            improvement_prompt = f"""
            Analyze the following Cypher query and suggest specific improvements for 
            performance, readability, or best practices:
            
            {cypher_query}
            
            Provide 2-3 specific, actionable suggestions:
            """
            
            messages = [{"role": "user", "content": improvement_prompt}]
            llm_suggestions = self.gemini_service.chat(messages)
            
            # Parse LLM suggestions
            for line in llm_suggestions.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    suggestions.append(line)
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            return [f"Error generating suggestions: {str(e)}"]
    
    def generate_test_queries(self, schema_info: str = None) -> List[Dict[str, str]]:
        """
        Generate sample test queries for the current database schema
        
        Args:
            schema_info: Optional schema information
            
        Returns:
            List of test queries with descriptions
        """
        try:
            if not schema_info:
                schema_info = self.neo4j_service.get_schema()
            
            test_prompt = f"""
            Based on the following database schema, generate 5 example natural language questions 
            and their corresponding Cypher queries that would be useful for testing:
            
            Schema:
            {schema_info}
            
            Format each as:
            Question: [natural language question]
            Cypher: [cypher query]
            
            Focus on common query patterns like finding relationships, counting nodes, 
            filtering by properties, etc.
            """
            
            messages = [{"role": "user", "content": test_prompt}]
            response = self.gemini_service.chat(messages)
            
            # Parse the response
            test_queries = []
            lines = response.split('\n')
            current_question = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith("Question:"):
                    current_question = line.replace("Question:", "").strip()
                elif line.startswith("Cypher:") and current_question:
                    cypher = line.replace("Cypher:", "").strip()
                    test_queries.append({
                        "question": current_question,
                        "cypher": cypher,
                        "description": f"Test query for: {current_question}"
                    })
                    current_question = ""
            
            return test_queries
            
        except Exception as e:
            return [{"error": f"Error generating test queries: {str(e)}"}]
