"""
Multi-provider client manager for various LLM providers
"""
from core.config import OLLAMA_AVAILABLE, QSettings, logger
from .clients import GeminiClient, ClaudeClient, DeepSeekClient, QwenClient


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
            for chunk in client.generate_response(prompt, self.current_model, system_message=system_message, stream=stream):
                yield chunk
