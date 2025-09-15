import google.generativeai as genai
import os
import json
from typing import List, Dict, Any, Optional
import tiktoken

class GeminiService:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDlFW2XcEnaF848zdj5td1xOL3mjDowkuc")
        genai.configure(api_key=api_key)
        
        # Initialize models
        self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        self.pro_model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Initialize tokenizer for token counting
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    def chat(self, messages: List[Dict[str, str]], model: str = "gemini-1.5-flash", 
             temperature: float = 0, config: Dict = None) -> str:
        """
        Chat with Gemini API using messages format similar to OpenAI
        """
        try:
            # Convert OpenAI-style messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Select model
            selected_model = self.pro_model if "pro" in model else self.text_model
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=4096,
            )
            
            if config:
                if config.get("response_format", {}).get("type") == "json_object":
                    prompt += "\n\nPlease respond with valid JSON only."
            
            # Generate response
            response = selected_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error in Gemini chat: {e}")
            return f"Error: {str(e)}"
    
    def chat_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict] = None, 
                       model: str = "gemini-1.5-flash") -> Any:
        """
        Chat with tools (function calling simulation)
        """
        try:
            # Convert messages and add tool descriptions
            prompt = self._convert_messages_to_prompt(messages)
            
            if tools:
                tool_descriptions = self._format_tools_for_prompt(tools)
                prompt += f"\n\nAvailable tools:\n{tool_descriptions}"
                prompt += "\n\nIf you need to use a tool, respond with JSON in this format:"
                prompt += '\n{"tool_calls": [{"function": {"name": "tool_name", "arguments": "{\\"param\\": \\"value\\"}"}}]}'
            
            # Select model
            selected_model = self.pro_model if "pro" in model else self.text_model
            
            # Generate response
            response = selected_model.generate_content(prompt)
            
            # Try to parse tool calls
            try:
                response_json = json.loads(response.text)
                if "tool_calls" in response_json:
                    # Create a mock response object with tool_calls attribute
                    mock_response = type('Response', (), {
                        'tool_calls': []
                    })()
                    
                    for call in response_json["tool_calls"]:
                        tool_call = type('ToolCall', (), {
                            'function': type('Function', (), {
                                'name': call["function"]["name"],
                                'arguments': call["function"]["arguments"]
                            })()
                        })()
                        mock_response.tool_calls.append(tool_call)
                    
                    return mock_response
            except json.JSONDecodeError:
                pass
            
            # Return empty response object if no tool calls
            return type('Response', (), {'tool_calls': []})()
            
        except Exception as e:
            print(f"Error in Gemini tool chat: {e}")
            return type('Response', (), {'tool_calls': []})()
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _format_tools_for_prompt(self, tools: List[Dict]) -> str:
        """Format tools for inclusion in prompt"""
        tool_descriptions = []
        
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                name = func.get("name", "")
                description = func.get("description", "")
                parameters = func.get("parameters", {})
                
                tool_desc = f"- {name}: {description}"
                if "properties" in parameters:
                    props = parameters["properties"]
                    params = []
                    for param_name, param_info in props.items():
                        param_type = param_info.get("type", "string")
                        param_desc = param_info.get("description", "")
                        params.append(f"{param_name} ({param_type}): {param_desc}")
                    
                    if params:
                        tool_desc += f"\n  Parameters: {', '.join(params)}"
                
                tool_descriptions.append(tool_desc)
        
        return "\n".join(tool_descriptions)
    
    def num_tokens_from_string(self, string: str, model: str = "gpt-4") -> int:
        """Returns the number of tokens in a text string."""
        try:
            num_tokens = len(self.encoding.encode(string))
            return num_tokens
        except Exception:
            # Fallback: approximate token count
            return len(string.split()) * 1.3
    
    def extract_structured_data(self, text: str, schema: Dict, model: str = "gemini-1.5-pro") -> Dict:
        """
        Extract structured data from text using a schema
        """
        try:
            prompt = f"""
            Extract structured information from the following text according to the provided schema.
            Return the result as valid JSON that matches the schema structure.
            
            Schema:
            {json.dumps(schema, indent=2)}
            
            Text:
            {text}
            
            Please respond with valid JSON only, no additional text.
            """
            
            selected_model = self.pro_model if "pro" in model else self.text_model
            
            response = selected_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=4096,
                )
            )
            
            # Try to parse JSON response
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"error": "Could not parse structured data", "raw_response": response.text}
                    
        except Exception as e:
            return {"error": f"Error extracting structured data: {str(e)}"}
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Gemini (fallback to sentence-transformers if not available)
        """
        # Note: Gemini doesn't have a direct embedding API like OpenAI
        # We'll use this as a placeholder and rely on sentence-transformers
        # In a real implementation, you might use Google's embedding models
        print("Warning: Using sentence-transformers for embeddings as Gemini doesn't provide embedding API")
        return []
    
    def stream_chat(self, messages: List[Dict[str, str]], model: str = "gemini-1.5-flash"):
        """
        Stream chat responses (generator)
        """
        try:
            prompt = self._convert_messages_to_prompt(messages)
            selected_model = self.pro_model if "pro" in model else self.text_model
            
            # Gemini doesn't support streaming in the same way as OpenAI
            # We'll simulate it by yielding the full response
            response = selected_model.generate_content(prompt)
            
            # Simulate streaming by yielding chunks
            text = response.text
            chunk_size = 50
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                yield {"choices": [{"delta": {"content": chunk}}]}
                
        except Exception as e:
            yield {"choices": [{"delta": {"content": f"Error: {str(e)}"}}]}
