"""
Groq API Service

Provides an interface for interacting with the Groq API for LLM operations.
"""

import json
from typing import List, Dict, Any, Optional
from groq import Groq
from config import GROQ_API_KEY


class GroqService:
    def __init__(self):
        """Initialize Groq service"""
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"  # Current available model
    
    def chat(self, messages: List[Dict[str, str]], model: str = None, temperature: float = 0.1) -> str:
        """
        Chat with Groq API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (optional)
            temperature: Temperature for response generation
            
        Returns:
            Response text from the model
        """
        try:
            selected_model = model or self.model
            
            # Convert messages to Groq format
            groq_messages = []
            for msg in messages:
                groq_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=groq_messages,
                temperature=temperature,
                max_tokens=2048
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error in Groq chat: {e}")
            return f"Error: {str(e)}"
    
    def chat_with_tools(self, messages: List[Dict[str, str]], tools: List[Dict] = None, 
                       model: str = None) -> Any:
        """
        Chat with tools (function calling simulation)
        """
        try:
            # Create a prompt that includes tool descriptions and asks for tool selection
            tool_descriptions = self._format_tools_for_prompt(tools) if tools else ""
            
            # Enhanced prompt for tool selection
            system_prompt = f"""You are an expert at choosing the right tool to answer user questions.

Available tools:
{tool_descriptions}

Your job is to choose the right tool needed to respond to the user question.
Make sure to pass the right and complete arguments to the chosen tool.

Respond with a JSON object in this exact format:
{{
  "tool_calls": [
    {{
      "function": {{
        "name": "tool_name",
        "arguments": "{{\\"param1\\": \\"value1\\", \\"param2\\": \\"value2\\"}}"
      }}
    }}
  ]
}}

If no tool is needed or you can't determine the right tool, respond with:
{{"tool_calls": []}}"""

            # Add system prompt to messages
            enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
            
            # Get response from Groq
            response_text = self.chat(enhanced_messages, model)
            
            # Try to parse JSON tool calls from response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    response_json = json.loads(json_match.group())
                    if "tool_calls" in response_json and response_json["tool_calls"]:
                        # Create mock response object
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
                print(f"Failed to parse JSON from response: {response_text}")
                pass
            
            # Return empty tool calls if no valid JSON found
            return type('Response', (), {'tool_calls': []})()
            
        except Exception as e:
            print(f"Error in Groq tool chat: {e}")
            return type('Response', (), {'tool_calls': []})()
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string"""
        prompt = ""
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        return prompt.strip()
    
    def _format_tools_for_prompt(self, tools: List[Dict]) -> str:
        """Format tools for prompt"""
        tool_descriptions = []
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                name = func.get("name", "unknown")
                description = func.get("description", "No description")
                parameters = func.get("parameters", {})
                
                # Format parameters
                param_info = ""
                if parameters and "properties" in parameters:
                    props = parameters["properties"]
                    required = parameters.get("required", [])
                    param_list = []
                    for param_name, param_details in props.items():
                        param_type = param_details.get("type", "string")
                        param_desc = param_details.get("description", "")
                        required_mark = " (required)" if param_name in required else ""
                        param_list.append(f"  - {param_name} ({param_type}): {param_desc}{required_mark}")
                    if param_list:
                        param_info = "\n  Parameters:\n" + "\n".join(param_list)
                
                tool_descriptions.append(f"- {name}: {description}{param_info}")
        return "\n".join(tool_descriptions)
