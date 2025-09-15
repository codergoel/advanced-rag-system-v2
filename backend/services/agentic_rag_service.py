"""
Agentic RAG Service

Implements an agentic RAG system with:
- Retriever agents (specialized and generic)
- Retriever router (LLM-based tool selection)
- Answer critic (validates answer completeness)
"""

import json
from typing import Dict, List, Any, Optional
from services.neo4j_service import Neo4jService
from services.gemini_service import GeminiService
from services.groq_service import GroqService
from services.text2cypher_service import Text2CypherService


class AgenticRAGService:
    def __init__(self, neo4j_service: Neo4jService, gemini_service: GeminiService):
        self.neo4j_service = neo4j_service
        self.gemini_service = gemini_service
        self.groq_service = GroqService()  # Add Groq service
        self.text2cypher_service = Text2CypherService(neo4j_service, gemini_service)
        
        # Initialize retriever tools
        self.tools = self._initialize_tools()
        
        # Prompts for different components
        self.tool_picker_prompt = """
Your job is to choose the right tool needed to respond to the user question.
The available tools are provided to you in the request.
Make sure to pass the right and complete arguments to the chosen tool.
"""
        
        self.query_update_prompt = """
You are an expert at updating questions to make them more atomic, specific, and easier to find the answer to.
You do this by filling in missing information in the question, with the extra information provided to you in previous answers.
You respond with the updated question that has all information in it.
Only edit the question if needed. If the original question already is atomic, specific, and easy to answer, you keep the original.
Do not ask for more information than the original question. Only rephrase the question to make it more complete.
JSON template to use:
{
"question": "question1"
}
"""
        
        self.answer_critique_prompt = """
You are an expert at identifying if questions have been fully answered or if there is an opportunity to enrich the answer.
The user will provide a question, and you will scan through the provided information to see if the question is answered.
If anything is missing from the answer, you will provide a set of new questions that can be asked to gather the missing information.
All new questions must be complete, atomic, and specific.
However, if the provided information is enough to answer the original question, you will respond with an empty list.
JSON template to use for finding missing information:
{
"questions": ["question1", "question2"]
}
"""
        
        self.main_prompt = """
Your job is to help the user with their questions.
You will receive user questions and information needed to answer the questions.
If the information is missing to answer part of or the whole question, you will say that the information is missing. 
You will only use the information provided to you in the prompt to answer the questions.
You are not allowed to make anything up or use external information.
"""

    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize the available retriever tools"""
        return {
            "movie_info_by_title": {
                "description": {
                    "type": "function",
                    "function": {
                        "name": "movie_info_by_title",
                        "description": "Get information about a movie by providing the title",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The movie title"
                                }
                            },
                            "required": ["title"]
                        }
                    }
                },
                "function": self.movie_info_by_title
            },
            "movies_info_by_actor": {
                "description": {
                    "type": "function",
                    "function": {
                        "name": "movies_info_by_actor",
                        "description": "Get information about movies by providing an actor name",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "actor": {
                                    "type": "string",
                                    "description": "The actor name"
                                }
                            },
                            "required": ["actor"]
                        }
                    }
                },
                "function": self.movies_info_by_actor
            },
            "text2cypher": {
                "description": {
                    "type": "function",
                    "function": {
                        "name": "text2cypher",
                        "description": "Query the database with a user question. When other tools don't fit, fallback to use this one.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "The user question to find the answer for"
                                }
                            },
                            "required": ["question"]
                        }
                    }
                },
                "function": self.text2cypher
            },
            "answer_given": {
                "description": {
                    "type": "function",
                    "function": {
                        "name": "answer_given",
                        "description": "If a complete answer to the question is already provided in the conversation, use this tool to extract it.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "answer": {
                                    "type": "string",
                                    "description": "The answer to the question"
                                }
                            },
                            "required": ["answer"]
                        }
                    }
                },
                "function": self.answer_given
            }
        }

    # Retriever Agent Functions
    def movie_info_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Return movie information by title."""
        query = """
        MATCH (m:Movie)
        WHERE toLower(m.title) CONTAINS $title
        OPTIONAL MATCH (m)<-[:ACTED_IN]-(a:Person)
        OPTIONAL MATCH (m)<-[:DIRECTED]-(d:Person)
        RETURN m AS movie, collect(a.name) AS cast, collect(d.name) AS directors
        """
        try:
            results = self.neo4j_service.execute_query(query, {"title": title.lower()})
            return results
        except Exception as e:
            return [{"error": f"Error querying movie by title: {str(e)}"}]

    def movies_info_by_actor(self, actor: str) -> List[Dict[str, Any]]:
        """Return movie information by actor."""
        query = """
        MATCH (a:Person)-[:ACTED_IN]->(m:Movie)
        OPTIONAL MATCH (m)<-[:ACTED_IN]-(a2:Person)
        OPTIONAL MATCH (m)<-[:DIRECTED]-(d:Person)
        WHERE toLower(a.name) CONTAINS $actor
        RETURN m AS movie, collect(a2.name) AS cast, collect(d.name) AS directors
        """
        try:
            results = self.neo4j_service.execute_query(query, {"actor": actor.lower()})
            return results
        except Exception as e:
            return [{"error": f"Error querying movies by actor: {str(e)}"}]

    def text2cypher(self, question: str) -> List[Dict[str, Any]]:
        """Query the database with a user question using text2cypher."""
        try:
            cypher_query = self.text2cypher_service.generate_cypher(question)
            results = self.neo4j_service.execute_query(cypher_query)
            return results
        except Exception as e:
            return [{"error": f"Error with text2cypher: {str(e)}"}]

    def answer_given(self, answer: str) -> str:
        """Extract the answer from a given text."""
        return answer

    # Tool Call Handling
    def handle_tool_calls(self, llm_tool_calls: List[Any]) -> List[Any]:
        """Handle tool calls from the LLM (following document specification)"""
        output = []
        if llm_tool_calls:
            for tool_call in llm_tool_calls:
                try:
                    # Handle both dict format and object format
                    if isinstance(tool_call, dict):
                        function_name = tool_call["function"]["name"]
                        function_args = json.loads(tool_call["function"]["arguments"])
                    else:
                        # Handle object format from Groq response
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name in self.tools:
                        function_to_call = self.tools[function_name]["function"]
                        res = function_to_call(**function_args)
                        output.extend(res if isinstance(res, list) else [res])
                    else:
                        output.append({"error": f"Unknown function: {function_name}"})
                except Exception as e:
                    output.append({"error": f"Error calling function: {str(e)}"})
        return output

    # Query Updating
    def query_update(self, input_question: str, answers: List[Dict[str, str]]) -> str:
        """Update questions with new information from previous answers"""
        try:
            messages = [
                {"role": "system", "content": self.query_update_prompt},
                *answers,
                {"role": "user", "content": f"The user question to rewrite: '{input_question}'"}
            ]
            
            response = self.groq_service.chat(messages)
            if response and response.strip():
                try:
                    result = json.loads(response)
                    return result.get("question", input_question)
                except json.JSONDecodeError:
                    # If response is not valid JSON, return original question
                    return input_question
            else:
                return input_question
        except Exception as e:
            print(f"Error updating query: {str(e)}")
            return input_question

    # Retriever Router
    def route_question(self, question: str, answers: List[Dict[str, str]]) -> List[Any]:
        """Route a question to the appropriate retriever using LLM-based tool selection"""
        try:
            # Prepare messages for LLM tool selection
            messages = [
                {"role": "system", "content": self.tool_picker_prompt},
                *answers,
                {"role": "user", "content": f"The user question to find a tool to answer: '{question}'"}
            ]
            
            # Get tool descriptions for the LLM
            tool_descriptions = [tool_info["description"] for tool_info in self.tools.values()]
            
            # Call LLM with tool selection capability
            response = self.groq_service.chat_with_tools(messages, tool_descriptions)
            
            # Handle tool calls from LLM response
            if response and hasattr(response, 'tool_calls') and response.tool_calls:
                return self.handle_tool_calls(response.tool_calls)
            else:
                # Fallback to text2cypher if no tool calls
                return self.text2cypher(question)
                
        except Exception as e:
            print(f"Error routing question: {str(e)}")
            # Fallback to text2cypher
            return self.text2cypher(question)


    def handle_user_input(self, input_question: str, answers: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Handle user input through the agentic RAG system"""
        if answers is None:
            answers = []
            
        # Update the question with context from previous answers
        updated_question = self.query_update(input_question, answers)
        
        # Route the question to appropriate retriever
        response = self.route_question(updated_question, answers)
        
        # Add the response to answers
        answers.append({
            "role": "assistant", 
            "content": f"For the question: '{updated_question}', we have the answer: '{json.dumps(response)}'"
        })
        
        return answers

    # Answer Critic
    def critique_answers(self, question: str, answers: List[Dict[str, str]]) -> List[str]:
        """Critique answers to check if the original question is fully answered"""
        try:
            messages = [
                {"role": "system", "content": self.answer_critique_prompt},
                *answers,
                {"role": "user", "content": f"The original user question to answer: {question}"}
            ]
            
            response = self.groq_service.chat(messages)
            if response and response.strip():
                try:
                    result = json.loads(response)
                    return result.get("questions", [])
                except json.JSONDecodeError:
                    # If response is not valid JSON, return empty list
                    return []
            else:
                return []
        except Exception as e:
            print(f"Error critiquing answers: {str(e)}")
            return []

    # Main Agentic RAG Function (following the document specification)
    def main(self, input_question: str) -> str:
        """
        Main function to process a question through the agentic RAG system
        Following the exact specification from the document
        """
        try:
            # Step 1: Handle user input and get initial answers
            answers = self.handle_user_input(input_question)
            
            # Step 2: Critique the answers to check completeness
            critique = self.critique_answers(input_question, answers)
            
            # Step 3: If critique suggests missing information, get additional data
            if critique:
                additional_answers = self.handle_user_input(" ".join(critique), answers)
                answers.extend(additional_answers)
            
            # Step 4: Generate final response using all gathered information
            final_response = self._generate_final_response(input_question, answers)
            
            return final_response
            
        except Exception as e:
            return f"Error processing question: {str(e)}"

    def process_question(self, input_question: str) -> Dict[str, Any]:
        """Wrapper function for API compatibility"""
        try:
            # Use the main function as specified in the document
            answer = self.main(input_question)
            
            return {
                "question": input_question,
                "answer": answer,
                "retrieval_steps": 1,
                "critique_questions": [],
                "status": "success"
            }
            
        except Exception as e:
            return {
                "question": input_question,
                "answer": f"Error processing question: {str(e)}",
                "retrieval_steps": 0,
                "critique_questions": [],
                "status": "error"
            }

    def _generate_final_response(self, question: str, answers: List[Dict[str, str]]) -> str:
        """Generate final response using all gathered information"""
        try:
            messages = [
                {"role": "system", "content": self.main_prompt},
                *answers,
                {"role": "user", "content": f"The user question to answer: {question}"}
            ]
            
            response = self.groq_service.chat(messages)
            return response if response else "Unable to generate a response."
            
        except Exception as e:
            return f"Error generating final response: {str(e)}"
    
    def _format_response(self, data: List[Dict], question: str) -> str:
        """Format the response data into a readable answer"""
        if not data:
            return "No data found for this question."
        
        # Handle different types of data
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            
            if isinstance(first_item, str):
                return f"Found {len(data)} results:\n" + "\n".join([str(item) for item in data])
            
            if "error" in first_item:
                return f"Error: {first_item['error']}"
            
            # Format movie data
            if isinstance(first_item, dict) and "movie" in first_item:
                movies = []
                seen_titles = set()  # Track seen titles to avoid duplicates
                
                for item in data:
                    if isinstance(item, dict) and "movie" in item:
                        movie = item["movie"]
                        title = movie.get("title", "Unknown") if isinstance(movie, dict) else str(movie)
                        year = movie.get("released", "Unknown year") if isinstance(movie, dict) else "Unknown year"
                        cast = item.get("cast", [])
                        directors = item.get("directors", [])
                        
                        # Skip duplicates
                        if title in seen_titles:
                            continue
                        seen_titles.add(title)
                        
                        movie_info = f"**{title}** ({year})"
                        if directors:
                            movie_info += f"\n- Directed by: {', '.join(directors)}"
                        if cast:
                            movie_info += f"\n- Cast: {', '.join(cast[:5])}"  # Show first 5 cast members
                        movies.append(movie_info)
                
                if movies:
                    return "\n\n".join(movies)
            
            # Format general data
            return f"Found {len(data)} results:\n" + "\n".join([str(item) for item in data[:5]])
        
        return str(data)

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools for the frontend"""
        return [
            {
                "name": tool_name,
                "description": tool_info["description"]["function"]["description"],
                "parameters": tool_info["description"]["function"]["parameters"]
            }
            for tool_name, tool_info in self.tools.items()
        ]
