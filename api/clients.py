"""
API Clients module for multi-provider LLM access
"""

from pathlib import Path
import json
from core.config import (GEMINI_AVAILABLE, ANTHROPIC_AVAILABLE, OPENAI_AVAILABLE, 
                        OLLAMA_AVAILABLE, genai, anthropic, openai, OllamaClient, 
                        QSettings, logger)


class APIClient:
    """Base class for API clients"""
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.name = "Base"
        self.models = []
    
    def get_models(self):
        """Get available models"""
        return self.models
    
    def generate_response(self, prompt, model, stream=False):
        """Generate response from the API"""
        raise NotImplementedError


class GeminiClient(APIClient):
    """Google Gemini API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Gemini"
        self.models = ["gemini-pro", "gemini-pro-vision"]
        self.client = None
        if api_key and GEMINI_AVAILABLE and genai:
            try:
                try:
                    genai.configure(api_key=api_key)  # type: ignore
                except AttributeError:
                    pass
                self.client = genai.GenerativeModel('gemini-pro')  # type: ignore
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
    
    def generate_response(self, prompt, model, stream=False):
        """Generate response from Gemini"""
        if not self.client:
            raise Exception("Gemini client not initialized. Check API key.")
        
        try:
            if stream:
                response = self.client.generate_content(prompt, stream=True)
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            else:
                response = self.client.generate_content(prompt)
                if hasattr(response, 'text') and response.text:
                    yield response.text
                else:
                    yield str(response)
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")


class ClaudeClient(APIClient):
    """Anthropic Claude API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Claude"
        self.models = ["claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-opus-20240229"]
        self.client = None
        if api_key and ANTHROPIC_AVAILABLE and anthropic:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
                self.client = None
    
    def generate_response(self, prompt, model, stream=False):
        """Generate response from Claude"""
        if not self.client:
            raise Exception("Claude client not initialized. Check API key.")
        
        try:
            if stream:
                with self.client.messages.stream(
                    model=model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        yield text
            else:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                if hasattr(response, 'content') and response.content:
                    # Claude response content is a list of content blocks
                    for content_block in response.content:
                        if hasattr(content_block, 'text'):
                            yield content_block.text  # type: ignore
                        else:
                            yield str(content_block)
                else:
                    yield str(response)
        except Exception as e:
            raise Exception(f"Claude API error: {e}")


class DeepSeekClient(APIClient):
    """DeepSeek API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "DeepSeek"
        self.models = ["deepseek-chat", "deepseek-coder"]
        self.base_url = "https://api.deepseek.com/v1"
        self.client = None
        if api_key and OPENAI_AVAILABLE and openai:
            try:
                self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)
            except Exception as e:
                logger.error(f"Failed to initialize DeepSeek client: {e}")
                self.client = None
    
    def generate_response(self, prompt, model, stream=False):
        """Generate response from DeepSeek"""
        if not self.client:
            raise Exception("DeepSeek client not initialized. Check API key.")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    if hasattr(chunk, 'choices') and chunk.choices:  # type: ignore
                        choice = chunk.choices[0]  # type: ignore
                        if hasattr(choice, 'delta') and choice.delta and hasattr(choice.delta, 'content') and choice.delta.content:
                            yield choice.delta.content
            else:
                if hasattr(response, 'choices') and response.choices:  # type: ignore
                    choice = response.choices[0]  # type: ignore
                    if hasattr(choice, 'message') and choice.message and hasattr(choice.message, 'content') and choice.message.content:
                        yield choice.message.content
                    else:
                        yield str(choice)
                else:
                    yield str(response)
        except Exception as e:
            raise Exception(f"DeepSeek API error: {e}")


class QwenClient(APIClient):
    """Qwen API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Qwen"
        self.models = ["qwen-plus", "qwen-turbo", "qwen-max", "qwen2.5-72b-instruct", "qwen-max-0919", "qwen-plus-0919"]
        self.base_url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        self.client = None
        if api_key and OPENAI_AVAILABLE and openai:
            try:
                self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)
            except Exception as e:
                logger.error(f"Failed to initialize Qwen client: {e}")
                self.client = None
    
    def generate_response(self, prompt, model, stream=False):
        """Generate response from Qwen"""
        if not self.client:
            raise Exception("Qwen client not initialized. Check API key.")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    if hasattr(chunk, 'choices') and chunk.choices:  # type: ignore
                        choice = chunk.choices[0]  # type: ignore
                        if hasattr(choice, 'delta') and choice.delta and hasattr(choice.delta, 'content') and choice.delta.content:
                            yield choice.delta.content
            else:
                if hasattr(response, 'choices') and response.choices:  # type: ignore
                    choice = response.choices[0]  # type: ignore
                    if hasattr(choice, 'message') and choice.message and hasattr(choice.message, 'content') and choice.message.content:
                        yield choice.message.content
                    else:
                        yield str(choice)
                else:
                    yield str(response)
        except Exception as e:
            raise Exception(f"Qwen API error: {e}")


class MultiProviderClient:
    """Multi-provider API client manager"""
    def __init__(self):
        self.providers = {
            "Ollama": {"client": None, "models": []},
            "Gemini": {"client": None, "models": []},
            "Claude": {"client": None, "models": []},
            "DeepSeek": {"client": None, "models": []},
            "Qwen": {"client": None, "models": []}
        }
        
        # Initialize Ollama client if available
        if OLLAMA_AVAILABLE:
            try:
                from ollama import Client as OllamaClient
                self.providers["Ollama"]["client"] = OllamaClient(host="http://127.0.0.1:11434")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
        
        self.current_provider = "Ollama"  # Default provider
        self.current_model = None
        self.load_settings()
    
    def load_settings(self):
        """Load API keys from settings"""
        settings = QSettings("TheOracle", "TheOracle")
        
        # Load API keys
        gemini_key = settings.value("gemini_api_key", "")
        claude_key = settings.value("claude_api_key", "")
        deepseek_key = settings.value("deepseek_api_key", "")
        qwen_key = settings.value("qwen_api_key", "")
        
        # Initialize clients
        if gemini_key:
            self.providers["Gemini"]["client"] = GeminiClient(gemini_key)
            self.providers["Gemini"]["models"] = self.providers["Gemini"]["client"].get_models()
        
        if claude_key:
            self.providers["Claude"]["client"] = ClaudeClient(claude_key)
            self.providers["Claude"]["models"] = self.providers["Claude"]["client"].get_models()
        
        if deepseek_key:
            self.providers["DeepSeek"]["client"] = DeepSeekClient(deepseek_key)
            self.providers["DeepSeek"]["models"] = self.providers["DeepSeek"]["client"].get_models()
        
        if qwen_key:
            self.providers["Qwen"]["client"] = QwenClient(qwen_key)
            self.providers["Qwen"]["models"] = self.providers["Qwen"]["client"].get_models()
    
    def save_settings(self):
        """Save API keys to settings"""
        settings = QSettings("TheOracle", "TheOracle")
        # Settings are saved when user enters keys in the UI
    
    def get_available_providers(self):
        """Get list of available providers"""
        return [name for name, info in self.providers.items() 
                if info["client"] is not None]
    
    def get_models_for_provider(self, provider):
        """Get models for a specific provider"""
        if provider == "Ollama":
            try:
                # Always fetch fresh models for Ollama
                response = self.providers["Ollama"]["client"].list()
                models = [m['model'] for m in response['models']]
                # Cache the models
                self.providers["Ollama"]["models"] = models
                return models
            except Exception as e:
                logger.error(f"Failed to get Ollama models: {e}")
                return self.providers["Ollama"]["models"]  # Return cached models if available
        else:
            return self.providers.get(provider, {}).get("models", [])
    
    def refresh_ollama_models(self):
        """Refresh Ollama models"""
        if "Ollama" in self.providers:
            try:
                response = self.providers["Ollama"]["client"].list()
                models = [m['model'] for m in response['models']]
                self.providers["Ollama"]["models"] = models
                logger.info(f"Refreshed Ollama models: {len(models)} models found")
                return models
            except Exception as e:
                logger.error(f"Failed to refresh Ollama models: {e}")
                return []
        return []
    
    def set_provider(self, provider, model=None):
        """Set current provider and model"""
        self.current_provider = provider
        if model:
            self.current_model = model
        elif provider in self.providers:
            models = self.get_models_for_provider(provider)
            if models:
                self.current_model = models[0]
    
    def generate_response(self, prompt, system_message=None, stream=True):
        """Generate response using current provider and model"""
        if self.current_provider not in self.providers:
            raise Exception(f"Provider {self.current_provider} not available")
        
        client = self.providers[self.current_provider]["client"]
        if not client:
            raise Exception(f"Client for {self.current_provider} not initialized")
        
        if self.current_provider == "Ollama":
            # Special handling for Ollama
            response = client.generate(
                model=self.current_model, 
                prompt=prompt, 
                system=system_message, 
                stream=stream
            )
            if stream:
                for chunk in response:
                    token = chunk.get('response') or chunk.get('message') or chunk.get('content') or ''
                    if token:
                        yield token
            else:
                yield response.get('response', '')
        else:
            # Handle other providers
            for chunk in client.generate_response(prompt, self.current_model, stream=stream):
                yield chunk
