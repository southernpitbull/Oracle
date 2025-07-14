"""
API Clients module for multi-provider LLM access
"""

import json
import requests
from core.config import (GEMINI_AVAILABLE, ANTHROPIC_AVAILABLE, OPENAI_AVAILABLE, 
                        OLLAMA_AVAILABLE, genai, anthropic, openai, 
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
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from the API"""
        raise NotImplementedError

class GeminiClient(APIClient):
    """Google Gemini API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Gemini"
        self.models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]
        self.client = None
        if api_key and GEMINI_AVAILABLE and genai:
            try:
                # Use the new google-genai library
                self.client = genai.Client(api_key=api_key)  # type: ignore
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Gemini"""
        if not self.client:
            raise Exception("Gemini client not initialized. Check API key.")
        
        # Prepare the content with system message if provided
        full_prompt = prompt
        if system_message:
            full_prompt = f"System: {system_message}\n\nUser: {prompt}"
        
        try:
            if stream:
                response = self.client.models.generate_content(
                    model=model, 
                    contents=full_prompt, 
                    stream=True
                )
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            else:
                response = self.client.models.generate_content(
                    model=model, 
                    contents=full_prompt
                )
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
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Claude"""
        if not self.client:
            raise Exception("Claude client not initialized. Check API key.")
        
        # Prepare API parameters
        api_params = {
            "model": model,
            "max_tokens": 4000,  # Default max tokens
            "messages": [{"role": "user", "content": prompt}]
        }
        
        # Add system message if provided
        if system_message:
            api_params["system"] = system_message
        
        # Apply model parameters if provided
        if model_params:
            # Map common parameters to Anthropic API parameters
            param_mapping = {
                'temperature': 'temperature',
                'max_tokens': 'max_tokens',
                'top_p': 'top_p',
                'top_k': 'top_k'
            }
            
            for param, api_param in param_mapping.items():
                if param in model_params and model_params[param] is not None:
                    if param == 'max_tokens' and model_params[param] == -1:
                        continue  # Skip -1 (unlimited)
                    api_params[api_param] = model_params[param]
            
            # Handle stop sequences
            if 'stop' in model_params and model_params['stop']:
                api_params['stop_sequences'] = model_params['stop']
        
        try:
            if stream:
                with self.client.messages.stream(**api_params) as stream:
                    for text in stream.text_stream:
                        yield text
            else:
                response = self.client.messages.create(**api_params)
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
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
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
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
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

class OpenAIClient(APIClient):
    """OpenAI API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "OpenAI"
        self.models = [
            "gpt-4", "gpt-4-turbo", "gpt-4-turbo-preview", 
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ]
        self.client = None
        if api_key and OPENAI_AVAILABLE and openai:
            try:
                self.client = openai.OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from OpenAI"""
        if not self.client:
            raise Exception("OpenAI client not initialized. Check API key.")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare API parameters
        api_params = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        # Apply model parameters if provided
        if model_params:
            # Map common parameters to OpenAI API parameters
            param_mapping = {
                'temperature': 'temperature',
                'max_tokens': 'max_tokens',
                'top_p': 'top_p',
                'frequency_penalty': 'frequency_penalty',
                'presence_penalty': 'presence_penalty',
                'seed': 'seed'
            }
            
            for param, api_param in param_mapping.items():
                if param in model_params and model_params[param] is not None:
                    # Handle special cases
                    if param == 'max_tokens' and model_params[param] == -1:
                        continue  # Skip -1 (unlimited)
                    if param == 'seed' and model_params[param] == -1:
                        continue  # Skip -1 (random seed)
                    api_params[api_param] = model_params[param]
            
            # Handle stop sequences
            if 'stop' in model_params and model_params['stop']:
                api_params['stop'] = model_params['stop']
        
        try:
            response = self.client.chat.completions.create(**api_params)
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {e}")

class LMStudioClient(APIClient):
    """LM Studio API client (OpenAI-compatible)"""
    def __init__(self, base_url="http://127.0.0.1:1234"):
        super().__init__()
        self.name = "LM Studio"
        self.base_url = base_url
        self.models = []
        self.refresh_models()
    
    def refresh_models(self):
        """Refresh available models from LM Studio"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.models = [model["id"] for model in data.get("data", [])]
                logger.info(f"LM Studio models refreshed: {len(self.models)} models")
            else:
                logger.warning(f"Failed to get LM Studio models: {response.status_code}")
        except Exception as e:
            logger.warning(f"LM Studio not available: {e}")
            self.models = []
    
    def get_models(self):
        """Get available models"""
        self.refresh_models()
        return self.models
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from LM Studio"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=stream,
                timeout=30
            )
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]
                            if line.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(line)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
            else:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    yield data['choices'][0]['message']['content']
                    
        except Exception as e:
            logger.error(f"LM Studio API error: {e}")
            raise Exception(f"LM Studio API error: {e}")

class LlamaCppClient(APIClient):
    """llama.cpp server API client"""
    def __init__(self, base_url="http://127.0.0.1:8080"):
        super().__init__()
        self.name = "llama.cpp"
        self.base_url = base_url
        self.models = []
        self.refresh_models()
    
    def refresh_models(self):
        """Refresh available models from llama.cpp server"""
        try:
            # llama.cpp server doesn't have a models endpoint, so we'll check if it's running
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                # If server is running, we assume there's at least one model loaded
                self.models = ["llama.cpp-model"]
                logger.info("llama.cpp server is running")
            else:
                logger.warning(f"llama.cpp server health check failed: {response.status_code}")
        except Exception as e:
            logger.warning(f"llama.cpp server not available: {e}")
            self.models = []
    
    def get_models(self):
        """Get available models"""
        self.refresh_models()
        return self.models
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from llama.cpp server"""
        # Combine system message and prompt
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\nUser: {prompt}\nAssistant:"
        
        payload = {
            "prompt": full_prompt,
            "stream": stream,
            "temperature": 0.7,
            "top_p": 0.9,
            "n_predict": 512
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/completion",
                json=payload,
                stream=stream,
                timeout=30
            )
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]
                            try:
                                data = json.loads(line)
                                content = data.get('content', '')
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
            else:
                data = response.json()
                yield data.get('content', '')
                    
        except Exception as e:
            logger.error(f"llama.cpp API error: {e}")
            raise Exception(f"llama.cpp API error: {e}")

class GroqClient(APIClient):
    """Groq API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Groq"
        self.models = [
            "llama2-70b-4096", "mixtral-8x7b-32768", 
            "gemma-7b-it", "llama3-8b-8192", "llama3-70b-8192"
        ]
        self.client = None
        if api_key:
            try:
                import groq
                self.client = groq.Groq(api_key=api_key)
            except ImportError:
                logger.warning("Groq library not available")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
    
    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Groq"""
        if not self.client:
            raise Exception("Groq client not initialized. Check API key or install groq library.")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Groq API error: {e}")

class NebiusClient(APIClient):
    """Nebius AI Studio API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Nebius AI Studio"
        self.base_url = "https://api.studio.nebius.ai/v1"
        self.models = []
        if api_key and OPENAI_AVAILABLE and openai:
            try:
                self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)
                self.refresh_models()
            except Exception as e:
                logger.error(f"Failed to initialize Nebius client: {e}")
                self.client = None
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI library not available for Nebius client")
            elif not openai:
                logger.warning("OpenAI module not properly imported for Nebius client")
            self.client = None

    def refresh_models(self):
        """Refresh available models from Nebius"""
        if not self.client:
            logger.warning("Nebius client not initialized, cannot refresh models")
            return []
        try:
            response = self.client.models.list()
            self.models = [model.id for model in response.data]
            return self.models
        except Exception as e:
            logger.error(f"Failed to get Nebius models: {e}")
            return []

    def get_models(self):
        """Get available models"""
        if not self.models:
            self.refresh_models()
        return self.models

    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Nebius AI Studio"""
        if not self.client:
            raise Exception("Nebius client not initialized. Check API key.")

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Nebius API error: {e}")
            raise Exception(f"Nebius API error: {e}")

class OpenRouterClient(APIClient):
    """OpenRouter.ai API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "OpenRouter.ai"
        self.base_url = "https://openrouter.ai/api/v1"
        self.models = []
        if api_key and OPENAI_AVAILABLE and openai:
            try:
                self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)
                self.refresh_models()
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter client: {e}")
                self.client = None
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI library not available for OpenRouter client")
            elif not openai:
                logger.warning("OpenAI module not properly imported for OpenRouter client")
            self.client = None

    def refresh_models(self):
        """Refresh available models from OpenRouter"""
        if not self.client:
            logger.warning("OpenRouter client not initialized, cannot refresh models")
            return []
        try:
            response = self.client.models.list()
            self.models = [model.id for model in response.data]
            return self.models
        except Exception as e:
            logger.error(f"Failed to get OpenRouter models: {e}")
            return []

    def get_models(self):
        """Get available models"""
        if not self.models:
            self.refresh_models()
        return self.models

    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from OpenRouter"""
        if not self.client:
            raise Exception("OpenRouter client not initialized. Check API key.")

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise Exception(f"OpenRouter API error: {e}")

class HuggingFacePlaygroundClient(APIClient):
    """Hugging Face Playground API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Hugging Face Playground"
        self.base_url = "https://api-inference.huggingface.co"
        self.models = [
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-large",
            "facebook/blenderbot-400M-distill",
            "facebook/blenderbot-1B-distill",
            "gpt2",
            "gpt2-medium",
            "gpt2-large"
        ]
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def get_models(self):
        """Get available models"""
        return self.models

    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Hugging Face Playground"""
        if not self.api_key:
            raise Exception("Hugging Face API key not provided.")

        # Combine system message and prompt
        full_prompt = prompt
        if system_message:
            full_prompt = f"{system_message}\n\nUser: {prompt}\nAssistant:"

        try:
            response = requests.post(
                f"{self.base_url}/models/{model}",
                headers=self.headers,
                json={"inputs": full_prompt}
            )
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                yield result[0].get("generated_text", "")
            else:
                yield result.get("generated_text", "")
                
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            raise Exception(f"Hugging Face API error: {e}")

class GoogleAIStudioClient(APIClient):
    """Google AI Studio API client (alternative to Gemini)"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Google AI Studio"
        self.models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
        self.client = None
        if api_key and GEMINI_AVAILABLE and genai:
            try:
                self.client = genai.Client(api_key=api_key)  # type: ignore
            except Exception as e:
                logger.error(f"Failed to initialize Google AI Studio client: {e}")
                self.client = None

    def get_models(self):
        """Get available models"""
        return self.models

    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Google AI Studio"""
        if not self.client:
            raise Exception("Google AI Studio client not initialized. Check API key.")

        # Handle system message by prepending to prompt
        full_prompt = prompt
        if system_message:
            full_prompt = f"System: {system_message}\n\nUser: {prompt}"

        try:
            if stream:
                response = self.client.models.generate_content(
                    model=model, 
                    contents=full_prompt, 
                    stream=True
                )
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        yield chunk.text
            else:
                response = self.client.models.generate_content(
                    model=model, 
                    contents=full_prompt
                )
                if hasattr(response, 'text') and response.text:
                    yield response.text
                else:
                    yield "I apologize, but I couldn't generate a response."
                    
        except Exception as e:
            logger.error(f"Google AI Studio API error: {e}")
            raise Exception(f"Google AI Studio API error: {e}")

class VLLMClient(APIClient):
    """vLLM API client"""
    def __init__(self, base_url="http://127.0.0.1:8000"):
        super().__init__()
        self.name = "vLLM"
        self.base_url = base_url
        self.models = []
        self.refresh_models()

    def refresh_models(self):
        """Refresh available models from vLLM server"""
        try:
            response = requests.get(f"{self.base_url}/v1/models")
            response.raise_for_status()
            data = response.json()
            self.models = [model["id"] for model in data.get("data", [])]
            return self.models
        except Exception as e:
            logger.warning(f"Failed to get vLLM models: {e}")
            return []

    def get_models(self):
        """Get available models"""
        if not self.models:
            self.refresh_models()
        return self.models

    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from vLLM server"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
            "max_tokens": 2048
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data != '[DONE]':
                                try:
                                    chunk = json.loads(data)
                                    content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                    if content:
                                        yield content
                                except json.JSONDecodeError:
                                    continue
            else:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                yield content
                
        except Exception as e:
            logger.error(f"vLLM API error: {e}")
            raise Exception(f"vLLM API error: {e}")

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
    
    def generate_response(self, prompt, system_message=None, stream=True, model_params=None):
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

class PerplexityClient(APIClient):
    """Perplexity AI API client"""
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.name = "Perplexity"
        self.base_url = "https://api.perplexity.ai"
        self.models = [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online",
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct",
            "mixtral-8x7b-instruct",
            "sonar-small-chat",
            "sonar-medium-chat"
        ]
        if api_key:
            try:
                self.client = openai.OpenAI(api_key=api_key, base_url=self.base_url)
            except Exception as e:
                logger.error(f"Failed to initialize Perplexity client: {e}")
                self.client = None

    def get_models(self):
        """Get available models"""
        return self.models

    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Perplexity"""
        if not self.client:
            raise Exception("Perplexity client not initialized. Check API key.")

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream
            )
            
            if stream:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            else:
                yield response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise Exception(f"Perplexity API error: {e}")

class OllamaClient(APIClient):
    """Ollama API client using ollama-python library"""
    def __init__(self, host="http://127.0.0.1:11434"):
        super().__init__(None)  # Ollama doesn't use API keys
        self.name = "Ollama"
        self.host = host
        self.models = []
        self.client = None
        
        try:
            import ollama
            self.client = ollama.Client(host=host)
            self.refresh_models()
        except ImportError:
            logger.error("ollama-python library not available. Please install with: pip install ollama")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.client = None

    def refresh_models(self):
        """Refresh available models from Ollama"""
        if not self.client:
            return []
        try:
            models_response = self.client.list()
            self.models = []
            if hasattr(models_response, 'models') and models_response.models:
                self.models = [model.model for model in models_response.models]
            elif isinstance(models_response, dict) and 'models' in models_response:
                self.models = [model.get('name', model.get('model', '')) for model in models_response['models']]
            return self.models
        except Exception as e:
            logger.error(f"Failed to get Ollama models: {e}")
            return []

    def get_models(self):
        """Get available models"""
        if not self.models:
            self.refresh_models()
        return self.models

    def generate_response(self, prompt, model, stream=False, system_message=None, model_params=None):
        """Generate response from Ollama"""
        if not self.client:
            raise Exception("Ollama client not initialized. Check if Ollama is running.")

        # Prepare messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # Prepare options
        options = {}
        if model_params:
            # Map common parameters to Ollama options
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

        try:
            if stream:
                response = self.client.chat(
                    model=model,
                    messages=messages,
                    stream=True,
                    options=options if options else None
                )
                for chunk in response:
                    if isinstance(chunk, dict) and 'message' in chunk:
                        content = chunk['message'].get('content', '')
                        if content:
                            yield content
                    elif hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                        if chunk.message.content:
                            yield chunk.message.content
            else:
                response = self.client.chat(
                    model=model,
                    messages=messages,
                    options=options if options else None
                )
                if isinstance(response, dict) and 'message' in response:
                    yield response['message'].get('content', '')
                elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                    yield response.message.content
                else:
                    yield str(response)
                    
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"Ollama API error: {e}")

    def pull_model(self, model_name):
        """Pull a model from Ollama registry"""
        if not self.client:
            raise Exception("Ollama client not initialized")
        
        try:
            # Pull the model
            for progress in self.client.pull(model_name, stream=True):
                # Yield progress updates
                if isinstance(progress, dict):
                    status = progress.get('status', '')
                    if 'completed' in progress and 'total' in progress:
                        completed = progress['completed']
                        total = progress['total']
                        percent = (completed / total) * 100 if total > 0 else 0
                        yield f"{status}: {percent:.1f}%"
                    else:
                        yield status
                else:
                    yield str(progress)
                    
            # Refresh models after successful pull
            self.refresh_models()
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            raise Exception(f"Failed to pull model {model_name}: {e}")

    def is_available(self):
        """Check if Ollama is available and running"""
        if not self.client:
            return False
        try:
            self.client.list()
            return True
        except Exception:
            return False
