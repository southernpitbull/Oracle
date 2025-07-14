"""
Multi-provider client manager for various LLM providers
"""
from core.config import OLLAMA_AVAILABLE, QSettings, logger
from .clients import (GeminiClient, ClaudeClient, DeepSeekClient, QwenClient, 
                     LMStudioClient, LlamaCppClient, NebiusClient, OpenRouterClient, 
                     HuggingFacePlaygroundClient, GoogleAIStudioClient, VLLMClient, PerplexityClient,
                     OllamaClient)

# Local model support
try:
    from .local_model_manager import LocalModelManager, LocalModelProvider
    LOCAL_MODELS_AVAILABLE = True
except ImportError:
    LOCAL_MODELS_AVAILABLE = False

# Local model server support
try:
    from .local_model_server import LocalModelServerManager, LlamaCppServer, ServerConfig, ModelConfig
    LOCAL_SERVER_AVAILABLE = True
except ImportError:
    LOCAL_SERVER_AVAILABLE = False


class MultiProviderClient:
    """Multi-provider API client manager with organized categories"""
    def __init__(self):
        # Flat structure for easier access, but organized conceptually
        self.providers = {}
        
        # Initialize all provider placeholders
        self._init_provider_structure()
        
        # Initialize local servers first
        self._init_local_servers()
        
        # Initialize local models
        self._init_local_models()
        
        # Initialize local model servers
        self._init_local_servers()
        
        # Set defaults
        self.current_provider = "Ollama"
        self.current_model = None
        
        # Load API keys and initialize commercial providers
        self.load_settings()
    
    def _init_provider_structure(self):
        """Initialize the provider structure"""
        # Local Servers
        self.providers.update({
            "Ollama": {"client": None, "models": [], "category": "Local Servers"},
            "LM Studio": {"client": None, "models": [], "category": "Local Servers"},
            "llama.cpp": {"client": None, "models": [], "category": "Local Servers"},
            "vLLM": {"client": None, "models": [], "category": "Local Servers"}
        })
        
        # Local Models (llama.cpp with multiple backends)
        if LOCAL_MODELS_AVAILABLE:
            self.providers.update({
                "Local Models": {"client": None, "models": [], "category": "Local Models"}
            })
        
        # AI Studios
        self.providers.update({
            "Nebius AI Studio": {"client": None, "models": [], "category": "AI Studios"},
            "OpenRouter.ai": {"client": None, "models": [], "category": "AI Studios"},
            "Hugging Face Playground": {"client": None, "models": [], "category": "AI Studios"},
            "Google AI Studio": {"client": None, "models": [], "category": "AI Studios"}
        })
        
        # Commercial APIs
        self.providers.update({
            "OpenAI": {"client": None, "models": [], "category": "Commercial APIs"},
            "Anthropic": {"client": None, "models": [], "category": "Commercial APIs"},
            "Google Gemini": {"client": None, "models": [], "category": "Commercial APIs"},
            "DeepSeek": {"client": None, "models": [], "category": "Commercial APIs"},
            "Qwen": {"client": None, "models": [], "category": "Commercial APIs"},
            "Groq": {"client": None, "models": [], "category": "Commercial APIs"},
            "Perplexity": {"client": None, "models": [], "category": "Commercial APIs"}
        })
    
    def _init_local_servers(self):
        """Initialize local server clients"""
        # Initialize Ollama client if available
        if OLLAMA_AVAILABLE:
            try:
                self.providers["Ollama"]["client"] = OllamaClient()
                models = self.providers["Ollama"]["client"].get_models()
                if models:
                    self.providers["Ollama"]["models"] = models
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
        
        # Initialize LM Studio client
        try:
            self.providers["LM Studio"]["client"] = LMStudioClient()
            models = self.providers["LM Studio"]["client"].get_models()
            if models:
                self.providers["LM Studio"]["models"] = models
        except Exception as e:
            logger.warning(f"Failed to initialize LM Studio client: {e}")
        
        # Initialize llama.cpp client
        try:
            self.providers["llama.cpp"]["client"] = LlamaCppClient()
            models = self.providers["llama.cpp"]["client"].get_models()
            if models:
                self.providers["llama.cpp"]["models"] = models
        except Exception as e:
            logger.warning(f"Failed to initialize llama.cpp client: {e}")
        
        # Initialize vLLM client
        try:
            self.providers["vLLM"]["client"] = VLLMClient()
            models = self.providers["vLLM"]["client"].get_models()
            if models:
                self.providers["vLLM"]["models"] = models
        except Exception as e:
            logger.warning(f"Failed to initialize vLLM client: {e}")
    
    def _init_local_models(self):
        """Initialize local model manager and provider"""
        if LOCAL_MODELS_AVAILABLE:
            try:
                # Initialize local model manager
                self.local_model_manager = LocalModelManager()
                
                # Initialize local model provider
                local_provider = LocalModelProvider(self.local_model_manager)
                self.providers["Local Models"]["client"] = local_provider
                self.providers["Local Models"]["models"] = local_provider.get_models()
                
                logger.info("Local model manager initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize local model manager: {e}")
    
    def _init_local_servers(self):
        """Initialize local model server manager"""
        if LOCAL_SERVER_AVAILABLE:
            try:
                # Initialize local model server manager
                self.local_server_manager = LocalModelServerManager()
                
                # Add local server provider
                self.providers["Local Server"] = {
                    "client": self.local_server_manager,
                    "models": [],
                    "category": "Local Servers"
                }
                
                logger.info("Local model server manager initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize local model server manager: {e}")

    def load_settings(self):
        """Load API keys and settings from QSettings"""
        settings = QSettings("TheOracle", "TheOracle")
        
        # Load API keys
        api_keys = {
            "openai_api_key": settings.value("openai_api_key", ""),
            "anthropic_api_key": settings.value("anthropic_api_key", ""),
            "google_api_key": settings.value("google_api_key", ""),
            "deepseek_api_key": settings.value("deepseek_api_key", ""),
            "qwen_api_key": settings.value("qwen_api_key", ""),
            "groq_api_key": settings.value("groq_api_key", ""),
            "nebius_api_key": settings.value("nebius_api_key", ""),
            "openrouter_api_key": settings.value("openrouter_api_key", ""),
            "huggingface_api_key": settings.value("huggingface_api_key", ""),
            "google_ai_studio_key": settings.value("google_ai_studio_key", ""),
            "perplexity_api_key": settings.value("perplexity_api_key", "")
        }
        
        # Load custom endpoints
        endpoints = {
            "lm_studio_host": settings.value("lm_studio_host", "http://127.0.0.1:1234"),
            "llama_cpp_host": settings.value("llama_cpp_host", "http://127.0.0.1:8080"),
            "ollama_host": settings.value("ollama_host", "http://127.0.0.1:11434"),
            "vllm_host": settings.value("vllm_host", "http://127.0.0.1:8000")
        }
        
        # Initialize commercial API clients
        self._init_commercial_apis(api_keys)
        
        # Initialize AI Studios
        self._init_ai_studios(api_keys)
        
        # Update local server endpoints
        self._update_local_endpoints(endpoints)
    
    def _init_commercial_apis(self, api_keys):
        """Initialize commercial API clients"""
        if api_keys["openai_api_key"]:
            from .clients import OpenAIClient
            self.providers["OpenAI"]["client"] = OpenAIClient(api_keys["openai_api_key"])
            self.providers["OpenAI"]["models"] = self.providers["OpenAI"]["client"].get_models()
        
        if api_keys["anthropic_api_key"]:
            self.providers["Anthropic"]["client"] = ClaudeClient(api_keys["anthropic_api_key"])
            self.providers["Anthropic"]["models"] = self.providers["Anthropic"]["client"].get_models()
        
        if api_keys["google_api_key"]:
            self.providers["Google Gemini"]["client"] = GeminiClient(api_keys["google_api_key"])
            self.providers["Google Gemini"]["models"] = self.providers["Google Gemini"]["client"].get_models()
        
        if api_keys["deepseek_api_key"]:
            self.providers["DeepSeek"]["client"] = DeepSeekClient(api_keys["deepseek_api_key"])
            self.providers["DeepSeek"]["models"] = self.providers["DeepSeek"]["client"].get_models()
        
        if api_keys["qwen_api_key"]:
            self.providers["Qwen"]["client"] = QwenClient(api_keys["qwen_api_key"])
            self.providers["Qwen"]["models"] = self.providers["Qwen"]["client"].get_models()
        
        if api_keys["groq_api_key"]:
            try:
                from .clients import GroqClient
                self.providers["Groq"]["client"] = GroqClient(api_keys["groq_api_key"])
                self.providers["Groq"]["models"] = self.providers["Groq"]["client"].get_models()
            except ImportError:
                logger.warning("Groq library not available")
        
        if api_keys["perplexity_api_key"]:
            try:
                from .clients import PerplexityClient
                self.providers["Perplexity"]["client"] = PerplexityClient(api_keys["perplexity_api_key"])
                self.providers["Perplexity"]["models"] = self.providers["Perplexity"]["client"].get_models()
            except Exception as e:
                logger.warning(f"Failed to initialize Perplexity client: {e}")
    
    def _init_ai_studios(self, api_keys):
        """Initialize AI Studio clients"""
        if api_keys["nebius_api_key"]:
            self.providers["Nebius AI Studio"]["client"] = NebiusClient(api_keys["nebius_api_key"])
            self.providers["Nebius AI Studio"]["models"] = self.providers["Nebius AI Studio"]["client"].get_models()
        
        if api_keys["openrouter_api_key"]:
            self.providers["OpenRouter.ai"]["client"] = OpenRouterClient(api_keys["openrouter_api_key"])
            self.providers["OpenRouter.ai"]["models"] = self.providers["OpenRouter.ai"]["client"].get_models()
        
        if api_keys["huggingface_api_key"]:
            self.providers["Hugging Face Playground"]["client"] = HuggingFacePlaygroundClient(api_keys["huggingface_api_key"])
            self.providers["Hugging Face Playground"]["models"] = self.providers["Hugging Face Playground"]["client"].get_models()
        
        if api_keys["google_ai_studio_key"]:
            self.providers["Google AI Studio"]["client"] = GoogleAIStudioClient(api_keys["google_ai_studio_key"])
            self.providers["Google AI Studio"]["models"] = self.providers["Google AI Studio"]["client"].get_models()
    
    def _update_local_endpoints(self, endpoints):
        """Update local server endpoints"""
        if self.providers["LM Studio"]["client"]:
            self.providers["LM Studio"]["client"].base_url = endpoints["lm_studio_host"]
        
        if self.providers["llama.cpp"]["client"]:
            self.providers["llama.cpp"]["client"].base_url = endpoints["llama_cpp_host"]
        
        if self.providers["vLLM"]["client"]:
            self.providers["vLLM"]["client"].base_url = endpoints["vllm_host"]
        
        # Reinitialize Ollama with new host if needed
        if endpoints["ollama_host"] != "http://127.0.0.1:11434" and OLLAMA_AVAILABLE:
            try:
                self.providers["Ollama"]["client"] = OllamaClient(host=endpoints["ollama_host"])
            except Exception as e:
                logger.warning(f"Failed to reinitialize Ollama with new host: {e}")

    def get_providers_by_category(self):
        """Get providers organized by category"""
        categories = {}
        for provider_name, provider_data in self.providers.items():
            category = provider_data["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(provider_name)
        return categories

    def get_models(self, provider_name):
        """Get models for a specific provider"""
        if provider_name in self.providers:
            return self.providers[provider_name]["models"]
        return []

    def get_client(self, provider_name):
        """Get client for a specific provider"""
        if provider_name in self.providers:
            return self.providers[provider_name]["client"]
        return None

    def refresh_models(self, provider_name):
        """Refresh models for a specific provider"""
        if provider_name in self.providers and self.providers[provider_name]["client"]:
            try:
                client = self.providers[provider_name]["client"]
                if hasattr(client, 'refresh_models'):
                    models = client.refresh_models()
                else:
                    models = client.get_models()
                self.providers[provider_name]["models"] = models
                return models
            except Exception as e:
                logger.error(f"Failed to refresh models for {provider_name}: {e}")
        return []

    def generate_response(self, prompt, provider_name=None, model_name=None, system_message=None, stream=False, model_params=None):
        """Generate response using specified provider and model"""
        provider_name = provider_name or self.current_provider
        model_name = model_name or self.current_model
        model_params = model_params or {}
        
        if provider_name not in self.providers:
            raise Exception(f"Provider {provider_name} not found")
        
        client = self.providers[provider_name]["client"]
        if not client:
            raise Exception(f"Provider {provider_name} not initialized")
        
        # Ensure model_name is provided
        if not model_name:
            available_models = self.providers[provider_name].get("models", [])
            if available_models:
                model_name = available_models[0]
            else:
                raise Exception(f"No model specified and no models available for {provider_name}")
        
        # Handle Ollama separately as it has a different interface
        if provider_name == "Ollama":
            # Use the OllamaClient's generate_response method directly
            return client.generate_response(prompt, model_name, stream, system_message, model_params)
        else:
            return client.generate_response(prompt, model_name, stream, system_message, model_params)
    
    def _generate_ollama_response(self, client, prompt, model_name, system_message, stream, model_params=None):
        """Generate response using Ollama client"""
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare options for Ollama
            options = {}
            if model_params:
                param_mapping = {
                    'temperature': 'temperature',
                    'top_p': 'top_p',
                    'top_k': 'top_k',
                    'max_tokens': 'num_predict',
                    'repetition_penalty': 'repeat_penalty',
                    'seed': 'seed',
                    'num_ctx': 'num_ctx',
                    'num_predict': 'num_predict'
                }
                
                for param, ollama_param in param_mapping.items():
                    if param in model_params and model_params[param] is not None:
                        options[ollama_param] = model_params[param]
                
                if 'stop' in model_params:
                    options['stop'] = model_params['stop']
            
            if stream:
                response = client.chat(
                    model=model_name, 
                    messages=messages, 
                    stream=True,
                    options=options if options else None
                )
                for chunk in response:
                    if 'message' in chunk and 'content' in chunk['message']:
                        yield chunk['message']['content']
            else:
                response = client.chat(
                    model=model_name, 
                    messages=messages,
                    options=options if options else None
                )
                if 'message' in response and 'content' in response['message']:
                    yield response['message']['content']
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Ollama API error: {e}")

    def get_available_providers(self):
        """Get list of providers that have initialized clients"""
        available = []
        for provider_name, provider_data in self.providers.items():
            if provider_data["client"] is not None:
                available.append(provider_name)
        return available

    def refresh_ollama_models(self):
        """Refresh Ollama models specifically"""
        if "Ollama" in self.providers and self.providers["Ollama"]["client"]:
            try:
                client = self.providers["Ollama"]["client"]
                models = client.refresh_models()
                self.providers["Ollama"]["models"] = models
                return models
            except Exception as e:
                logger.error(f"Failed to refresh Ollama models: {e}")
        return []

    def pull_ollama_model(self, model_name):
        """Pull a model using Ollama"""
        if "Ollama" in self.providers and self.providers["Ollama"]["client"]:
            try:
                client = self.providers["Ollama"]["client"]
                for progress in client.pull_model(model_name):
                    yield progress
            except Exception as e:
                logger.error(f"Failed to pull Ollama model: {e}")
                raise e
        else:
            raise Exception("Ollama client not available")

    def is_ollama_available(self):
        """Check if Ollama is available and running"""
        if "Ollama" in self.providers and self.providers["Ollama"]["client"]:
            return self.providers["Ollama"]["client"].is_available()
        return False

    def set_provider(self, provider_name):
        """
        Set the current provider by name.
        :param provider_name: str, the name of the provider to switch to
        :raises ValueError: if provider_name is not in self.providers
        """
        if provider_name not in self.providers:
            logger.error(f"Provider '{provider_name}' not found in available providers: {list(self.providers.keys())}")
            raise ValueError(f"Provider '{provider_name}' not found.")
        self.current_provider = provider_name
        logger.info(f"Switched to provider: {provider_name}")

    def get_models_for_provider(self, provider_name: str):
        """
        Return the list of models for the specified provider.
        :param provider_name: str, the name of the provider
        :return: list of model names, or an empty list if not found
        """
        provider = self.providers.get(provider_name)
        if provider and "models" in provider:
            return provider["models"]
        return []
