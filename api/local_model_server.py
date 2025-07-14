# -*- coding: utf-8 -*-
"""
Local Model Server for The Oracle AI Chat Application
File: api/local_model_server.py
Author: The Oracle Development Team
Date: 2024-12-19

Comprehensive local model server using llama.cpp with support for:
- Multiple backends: CPU, CUDA, Vulkan, ROCm, Metal, OpenCL
- All known model architectures (Llama, Mistral, Phi, Gemma, etc.)
- Advanced features: streaming, batching, quantization, context management
- Performance optimization and resource management
"""

import os
import sys
import json
import time
import signal
import socket
import threading
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Generator
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer, QMutex, QWaitCondition
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Supported backend types for local model inference."""
    CPU = "cpu"
    CUDA = "cuda"
    VULKAN = "vulkan"
    ROCM = "rocm"
    METAL = "metal"  # Apple Silicon
    OPENCL = "opencl"  # OpenCL acceleration
    SYCL = "sycl"  # Intel oneAPI


class ModelArchitecture(Enum):
    """Comprehensive list of supported model architectures."""
    # Llama family
    LLAMA = "llama"
    LLAMA2 = "llama2"
    LLAMA3 = "llama3"
    CODELLAMA = "codellama"
    
    # Mistral family
    MISTRAL = "mistral"
    MISTRAL2 = "mistral2"
    MIXTRAL = "mixtral"
    
    # Microsoft Phi family
    PHI = "phi"
    PHI2 = "phi2"
    PHI3 = "phi3"
    
    # Google models
    GEMMA = "gemma"
    GEMMA2 = "gemma2"
    
    # Alibaba models
    QWEN = "qwen"
    QWEN2 = "qwen2"
    TONGYI = "tongyi"
    
    # Other major models
    FALCON = "falcon"
    MPT = "mpt"
    BLOOM = "bloom"
    GPT2 = "gpt2"
    GPTJ = "gptj"
    GPTNEOX = "gptneox"
    CODEGEN = "codegen"
    STARCODER = "starcoder"
    WIZARDLM = "wizardlm"
    VICUNA = "vicuna"
    ALPACA = "alpaca"
    ORCA = "orca"
    DOLPHIN = "dolphin"
    NEURAL_CHAT = "neural_chat"
    OPENHERMES = "openhermes"
    TIGERBOT = "tigerbot"
    CHATGLM = "chatglm"
    BAICHUAN = "baichuan"
    INTERNLM = "internlm"
    YI = "yi"
    DEEPSEEK = "deepseek"
    MAGICODER = "magicoder"
    WIZARDCODER = "wizardcoder"
    UNKNOWN = "unknown"


class QuantizationType(Enum):
    """Supported quantization types."""
    F16 = "f16"
    Q2_K = "q2_k"
    Q3_K_S = "q3_k_s"
    Q3_K_M = "q3_k_m"
    Q3_K_L = "q3_k_l"
    Q4_0 = "q4_0"
    Q4_1 = "q4_1"
    Q4_K_S = "q4_k_s"
    Q4_K_M = "q4_k_m"
    Q5_0 = "q5_0"
    Q5_1 = "q5_1"
    Q5_K_S = "q5_k_s"
    Q5_K_M = "q5_k_m"
    Q6_K = "q6_k"
    Q8_0 = "q8_0"


@dataclass
class ServerConfig:
    """Configuration for the local model server."""
    host: str = "127.0.0.1"
    port: int = 8080
    max_connections: int = 10
    timeout: int = 30
    enable_cors: bool = True
    log_level: str = "INFO"
    enable_metrics: bool = True
    enable_health_check: bool = True
    enable_model_management: bool = True
    enable_batch_processing: bool = True
    max_batch_size: int = 4
    enable_streaming: bool = True
    enable_websocket: bool = True
    websocket_port: int = 8081
    enable_ssl: bool = False
    ssl_cert: str = ""
    ssl_key: str = ""


@dataclass
class ModelConfig:
    """Configuration for model loading and inference."""
    model_path: str
    backend: BackendType = BackendType.CPU
    quantization: QuantizationType = QuantizationType.Q4_K_M
    context_length: int = 4096
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 40
    repeat_penalty: float = 1.1
    seed: int = -1
    threads: int = -1
    gpu_layers: int = 0
    batch_size: int = 512
    rope_freq_base: float = 10000.0
    rope_freq_scale: float = 1.0
    mul_mat_q: bool = True
    f16_kv: bool = True
    logits_all: bool = False
    vocab_only: bool = False
    use_mmap: bool = True
    use_mlock: bool = False
    numa: bool = False
    n_ctx: int = 4096
    n_batch: int = 512
    n_ubatch: int = 512
    n_parallel: int = 1
    n_keep: int = 0
    n_draft: int = 8
    n_chunks: int = -1
    n_gpu_layers: int = 0
    n_gqa: int = 8
    rms_norm_eps: float = 1e-5
    rope_freq_base: float = 10000.0
    rope_freq_scale: float = 1.0
    mul_mat_q: bool = True
    f16_kv: bool = True
    logits_all: bool = False
    vocab_only: bool = False
    use_mmap: bool = True
    use_mlock: bool = False
    numa: bool = False
    embedding: bool = False
    offload_kqv: bool = True
    flash_attn: bool = True
    color: bool = False
    ctx_size: int = 4096
    batch_size: int = 512
    ubatch_size: int = 512
    parallel: int = 1
    keep: int = 0
    draft: int = 8
    chunks: int = -1
    gpu_layers: int = 0
    gqa: int = 8
    rms_norm_eps: float = 1e-5


@dataclass
class InferenceRequest:
    """Request for model inference."""
    prompt: str
    system_message: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    repeat_penalty: Optional[float] = None
    seed: Optional[int] = None
    stop: Optional[List[str]] = None
    stream: bool = False
    model: Optional[str] = None


@dataclass
class InferenceResponse:
    """Response from model inference."""
    text: str
    tokens_used: int
    time_taken: float
    model: str
    finish_reason: str = "stop"
    usage: Optional[Dict[str, Any]] = None


class LlamaCppServer(QObject):
    """Local model server using llama.cpp with multiple backends."""
    
    # Signals
    server_started = pyqtSignal(str)  # server_url
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)  # error_message
    model_loaded = pyqtSignal(str)  # model_name
    model_unloaded = pyqtSignal(str)  # model_name
    inference_started = pyqtSignal(str)  # model_name
    inference_complete = pyqtSignal(str, str)  # model_name, response
    inference_error = pyqtSignal(str, str)  # model_name, error
    inference_chunk = pyqtSignal(str, str)  # model_name, chunk
    
    def __init__(self, config: ServerConfig = None):
        super().__init__()
        self.config = config or ServerConfig()
        self.server_process = None
        self.server_url = f"http://{self.config.host}:{self.config.port}"
        self.websocket_url = f"ws://{self.config.host}:{self.config.websocket_port}"
        self.is_running = False
        self.loaded_models = {}
        self.model_configs = {}
        self.request_queue = []
        self.response_queue = []
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_connections)
        
        # Initialize llama.cpp paths
        self.llama_cpp_path = self._find_llama_cpp()
        self._validate_backends()
        
        # Health check timer
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self._health_check)
        self.health_timer.start(30000)  # Check every 30 seconds
    
    def _find_llama_cpp(self) -> Optional[str]:
        """Find llama.cpp installation."""
        possible_paths = [
            "llama-cpp-python",
            "llama_cpp_python",
            "llama.cpp",
            "llama-cpp",
            "llama_cpp"
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--help"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"Found llama.cpp at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        # Try to find in Python packages
        try:
            import llama_cpp
            logger.info("Found llama.cpp Python package")
            return "python -m llama_cpp.server"
        except ImportError:
            pass
        
        logger.warning("llama.cpp not found. Please install llama-cpp-python")
        return None
    
    def _validate_backends(self):
        """Validate available backends."""
        if not self.llama_cpp_path:
            return
        
        available_backends = []
        
        # Check CUDA
        try:
            result = subprocess.run([self.llama_cpp_path, "--help"], 
                                  capture_output=True, text=True, timeout=5)
            if "cuda" in result.stdout.lower():
                available_backends.append(BackendType.CUDA)
        except Exception:
            pass
        
        # Check Vulkan
        try:
            result = subprocess.run([self.llama_cpp_path, "--help"], 
                                  capture_output=True, text=True, timeout=5)
            if "vulkan" in result.stdout.lower():
                available_backends.append(BackendType.VULKAN)
        except Exception:
            pass
        
        # Check ROCm
        try:
            result = subprocess.run([self.llama_cpp_path, "--help"], 
                                  capture_output=True, text=True, timeout=5)
            if "rocm" in result.stdout.lower():
                available_backends.append(BackendType.ROCM)
        except Exception:
            pass
        
        # Check Metal (macOS)
        if sys.platform == "darwin":
            try:
                result = subprocess.run([self.llama_cpp_path, "--help"], 
                                      capture_output=True, text=True, timeout=5)
                if "metal" in result.stdout.lower():
                    available_backends.append(BackendType.METAL)
            except Exception:
                pass
        
        # CPU is always available
        available_backends.append(BackendType.CPU)
        
        logger.info(f"Available backends: {[b.value for b in available_backends]}")
        self.available_backends = available_backends
    
    def start_server(self) -> bool:
        """Start the llama.cpp server."""
        if self.is_running:
            logger.warning("Server is already running")
            return True
        
        if not self.llama_cpp_path:
            logger.error("llama.cpp not found")
            return False
        
        try:
            # Build server command
            cmd = [
                self.llama_cpp_path,
                "--server",
                "--host", self.config.host,
                "--port", str(self.config.port),
                "--n-ctx", str(self.config.max_connections * 4096),
                "--n-batch", str(self.config.max_batch_size),
                "--n-parallel", str(self.config.max_connections)
            ]
            
            if self.config.enable_websocket:
                cmd.extend(["--websocket", "--websocket-port", str(self.config.websocket_port)])
            
            if self.config.enable_ssl and self.config.ssl_cert and self.config.ssl_key:
                cmd.extend(["--ssl", "--ssl-cert", self.config.ssl_cert, "--ssl-key", self.config.ssl_key])
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait for server to start
            time.sleep(2)
            
            if self.server_process.poll() is None:
                self.is_running = True
                logger.info(f"Server started at {self.server_url}")
                self.server_started.emit(self.server_url)
                
                # Start monitoring thread
                self.monitor_thread = threading.Thread(target=self._monitor_server, daemon=True)
                self.monitor_thread.start()
                
                return True
            else:
                stdout, stderr = self.server_process.communicate()
                logger.error(f"Server failed to start: {stderr}")
                self.server_error.emit(f"Server failed to start: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            self.server_error.emit(str(e))
            return False
    
    def stop_server(self):
        """Stop the llama.cpp server."""
        if not self.is_running:
            return
        
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
            
            self.is_running = False
            logger.info("Server stopped")
            self.server_stopped.emit()
            
        except subprocess.TimeoutExpired:
            if self.server_process:
                self.server_process.kill()
            logger.warning("Server forcefully stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
    
    def _monitor_server(self):
        """Monitor server process."""
        while self.is_running and self.server_process:
            if self.server_process.poll() is not None:
                logger.error("Server process terminated unexpectedly")
                self.server_error.emit("Server process terminated unexpectedly")
                self.is_running = False
                break
            time.sleep(1)
    
    def _health_check(self):
        """Perform health check on the server."""
        if not self.is_running:
            return
        
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code != 200:
                logger.warning("Server health check failed")
        except Exception as e:
            logger.warning(f"Server health check failed: {e}")
    
    def load_model(self, model_path: str, config: ModelConfig = None) -> bool:
        """Load a model into the server."""
        if not self.is_running:
            logger.error("Server is not running")
            return False
        
        try:
            model_name = Path(model_path).stem
            
            # Prepare model configuration
            model_config = config or ModelConfig(model_path=model_path)
            
            # Build load command
            cmd = {
                "model": model_path,
                "backend": model_config.backend.value,
                "n_ctx": model_config.context_length,
                "n_batch": model_config.batch_size,
                "n_gpu_layers": model_config.gpu_layers,
                "rope_freq_base": model_config.rope_freq_base,
                "rope_freq_scale": model_config.rope_freq_scale,
                "mul_mat_q": model_config.mul_mat_q,
                "f16_kv": model_config.f16_kv,
                "logits_all": model_config.logits_all,
                "vocab_only": model_config.vocab_only,
                "use_mmap": model_config.use_mmap,
                "use_mlock": model_config.use_mlock,
                "numa": model_config.numa,
                "embedding": model_config.embedding,
                "offload_kqv": model_config.offload_kqv,
                "flash_attn": model_config.flash_attn
            }
            
            # Send load request
            response = requests.post(
                f"{self.server_url}/v1/models",
                json=cmd,
                timeout=60
            )
            
            if response.status_code == 200:
                self.loaded_models[model_name] = model_path
                self.model_configs[model_name] = model_config
                logger.info(f"Model {model_name} loaded successfully")
                self.model_loaded.emit(model_name)
                return True
            else:
                logger.error(f"Failed to load model {model_name}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error loading model {model_path}: {e}")
            return False
    
    def unload_model(self, model_name: str) -> bool:
        """Unload a model from the server."""
        if not self.is_running:
            return False
        
        try:
            response = requests.delete(
                f"{self.server_url}/v1/models/{model_name}",
                timeout=30
            )
            
            if response.status_code == 200:
                if model_name in self.loaded_models:
                    del self.loaded_models[model_name]
                if model_name in self.model_configs:
                    del self.model_configs[model_name]
                logger.info(f"Model {model_name} unloaded successfully")
                self.model_unloaded.emit(model_name)
                return True
            else:
                logger.error(f"Failed to unload model {model_name}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {e}")
            return False
    
    def generate_response(self, request: InferenceRequest) -> Union[str, Generator[str, None, None]]:
        """Generate response from the model."""
        if not self.is_running:
            raise Exception("Server is not running")
        
        if not request.model or request.model not in self.loaded_models:
            raise Exception(f"Model {request.model} not loaded")
        
        try:
            # Prepare request payload
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": request.stream,
                "temperature": request.temperature or self.model_configs[request.model].temperature,
                "top_p": request.top_p or self.model_configs[request.model].top_p,
                "top_k": request.top_k or self.model_configs[request.model].top_k,
                "max_tokens": request.max_tokens or self.model_configs[request.model].max_tokens,
                "repeat_penalty": request.repeat_penalty or self.model_configs[request.model].repeat_penalty,
                "seed": request.seed or self.model_configs[request.model].seed
            }
            
            if request.system_message:
                payload["system"] = request.system_message
            
            if request.stop:
                payload["stop"] = request.stop
            
            self.inference_started.emit(request.model)
            
            if request.stream:
                return self._generate_streaming_response(request.model, payload)
            else:
                return self._generate_single_response(request.model, payload)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            self.inference_error.emit(request.model, str(e))
            raise
    
    def _generate_single_response(self, model_name: str, payload: Dict[str, Any]) -> str:
        """Generate a single response."""
        start_time = time.time()
        
        response = requests.post(
            f"{self.server_url}/v1/completions",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            text = data["choices"][0]["text"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            time_taken = time.time() - start_time
            
            logger.info(f"Generated response in {time_taken:.2f}s, {tokens_used} tokens")
            self.inference_complete.emit(model_name, text)
            return text
        else:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            self.inference_error.emit(model_name, error_msg)
            raise Exception(error_msg)
    
    def _generate_streaming_response(self, model_name: str, payload: Dict[str, Any]) -> Generator[str, None, None]:
        """Generate a streaming response."""
        start_time = time.time()
        
        response = requests.post(
            f"{self.server_url}/v1/completions",
            json=payload,
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            full_text = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data.strip() == '[DONE]':
                            break
                        try:
                            chunk_data = json.loads(data)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_text += content
                                    self.inference_chunk.emit(model_name, content)
                                    yield content
                        except json.JSONDecodeError:
                            continue
            
            time_taken = time.time() - start_time
            logger.info(f"Generated streaming response in {time_taken:.2f}s")
            self.inference_complete.emit(model_name, full_text)
        else:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            self.inference_error.emit(model_name, error_msg)
            raise Exception(error_msg)
    
    def get_loaded_models(self) -> Dict[str, str]:
        """Get list of loaded models."""
        return self.loaded_models.copy()
    
    def get_model_info(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a loaded model."""
        return self.model_configs.get(model_name)
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get server status information."""
        if not self.is_running:
            return {"status": "stopped"}
        
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "running",
                    "url": self.server_url,
                    "websocket_url": self.websocket_url if self.config.enable_websocket else None,
                    "loaded_models": list(self.loaded_models.keys()),
                    "available_backends": [b.value for b in self.available_backends]
                }
            else:
                return {"status": "error", "error": f"Health check failed: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_server()
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        if hasattr(self, 'health_timer'):
            self.health_timer.stop()


class LocalModelServerManager(QObject):
    """Manager for multiple local model servers."""
    
    server_status_changed = pyqtSignal(str, str)  # server_name, status
    model_status_changed = pyqtSignal(str, str, str)  # server_name, model_name, status
    
    def __init__(self):
        super().__init__()
        self.servers = {}
        self.server_configs = {}
        self.model_registry = {}
        
        # Load server configurations
        self._load_server_configs()
    
    def _load_server_configs(self):
        """Load server configurations from file."""
        config_file = Path("config/local_servers.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    configs = json.load(f)
                    for name, config in configs.items():
                        self.server_configs[name] = ServerConfig(**config)
            except Exception as e:
                logger.error(f"Failed to load server configs: {e}")
    
    def create_server(self, name: str, config: ServerConfig = None) -> bool:
        """Create and start a new server."""
        if name in self.servers:
            logger.warning(f"Server {name} already exists")
            return False
        
        server_config = config or self.server_configs.get(name) or ServerConfig()
        server = LlamaCppServer(server_config)
        
        if server.start_server():
            self.servers[name] = server
            self.server_configs[name] = server_config
            logger.info(f"Server {name} created and started")
            self.server_status_changed.emit(name, "running")
            return True
        else:
            logger.error(f"Failed to create server {name}")
            return False
    
    def stop_server(self, name: str) -> bool:
        """Stop a server."""
        if name not in self.servers:
            return False
        
        server = self.servers[name]
        server.stop_server()
        del self.servers[name]
        logger.info(f"Server {name} stopped")
        self.server_status_changed.emit(name, "stopped")
        return True
    
    def load_model(self, server_name: str, model_path: str, config: ModelConfig = None) -> bool:
        """Load a model on a specific server."""
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found")
            return False
        
        server = self.servers[server_name]
        model_name = Path(model_path).stem
        
        if server.load_model(model_path, config):
            self.model_registry[f"{server_name}:{model_name}"] = {
                "server": server_name,
                "model": model_name,
                "path": model_path,
                "config": config
            }
            self.model_status_changed.emit(server_name, model_name, "loaded")
            return True
        else:
            return False
    
    def unload_model(self, server_name: str, model_name: str) -> bool:
        """Unload a model from a specific server."""
        if server_name not in self.servers:
            return False
        
        server = self.servers[server_name]
        if server.unload_model(model_name):
            registry_key = f"{server_name}:{model_name}"
            if registry_key in self.model_registry:
                del self.model_registry[registry_key]
            self.model_status_changed.emit(server_name, model_name, "unloaded")
            return True
        else:
            return False
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all available models across all servers."""
        models = {}
        for registry_key, info in self.model_registry.items():
            models[registry_key] = info.copy()
        return models
    
    def get_server_status(self, name: str) -> Dict[str, Any]:
        """Get status of a specific server."""
        if name not in self.servers:
            return {"status": "not_found"}
        
        return self.servers[name].get_server_status()
    
    def get_all_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers."""
        status = {}
        for name, server in self.servers.items():
            status[name] = server.get_server_status()
        return status
    
    def cleanup(self):
        """Clean up all servers."""
        for name, server in self.servers.items():
            server.cleanup()
        self.servers.clear()
        logger.info("All servers cleaned up")


# Global server manager instance
server_manager = LocalModelServerManager() 
