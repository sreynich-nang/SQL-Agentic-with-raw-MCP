"""Utilities for managing Gemini LLM model"""

import os
from typing import Optional, Dict, Any
import google.generativeai as genai

class ModelManager:
    """Manage Gemini LLM model and API"""
    
    def __init__(self, model_id: str, api_key: str):
        self.model_id = model_id
        self.api_key = api_key
        
        # Initialize Gemini client
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_id)
    
    async def generate_response(
        self, 
        messages: list, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response using Gemini model
        
        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response text
        """
        try:
            return await self._gemini_generate(messages, system_prompt, max_tokens, temperature)
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    async def _gemini_generate(self, messages, system_prompt, max_tokens, temperature) -> str:
        """Generate response using Google Gemini API"""
        # Format conversation history for Gemini
        conversation_history = []
        
        # Add system prompt if provided
        if system_prompt:
            conversation_history.append({
                "role": "user",
                "parts": [f"System: {system_prompt}"]
            })
            conversation_history.append({
                "role": "model", 
                "parts": ["I understand. I'll follow those instructions."]
            })
        
        # Convert messages to Gemini format
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            conversation_history.append({
                "role": role,
                "parts": [msg["content"]]
            })
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Start chat with history (excluding the last message)
        if len(conversation_history) > 1:
            chat = self.client.start_chat(history=conversation_history[:-1])
            # Send the last message
            response = chat.send_message(
                conversation_history[-1]["parts"][0],
                generation_config=generation_config
            )
        else:
            # Single message case
            response = self.client.generate_content(
                conversation_history[-1]["parts"][0],
                generation_config=generation_config
            )
        
        return response.text

def get_model() -> ModelManager:
    """Get Gemini model manager instance from environment configuration"""
    from utils.env_utils import get_model_config
    
    config = get_model_config()
    return ModelManager(config['MODEL_ID'], config['MODEL_API_KEY'])