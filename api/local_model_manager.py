"""
Local Model Manager for The Oracle AI Chat Application.
Supports llama.cpp with multiple backends: CPU, CUDA, Vulkan, ROCm.
"""

import os
import json
import subprocess
import threading
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import QProgressDialog, QMessageBox

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Supported backend types for local model inference."""
    CPU = "cpu"
    CUDA = "cuda"
    VULKAN = "vulkan"
    ROCM = "rocm"
    METAL = "metal"  # Apple Silicon
    OPENCL = "opencl"  # OpenCL acceleration


class ModelArchitecture(Enum):
    """Supported model architectures."""
    LLAMA = "llama"
    MISTRAL = "mistral"
    PHI = "phi"
    GEMMA = "gemma"
    QWEN = "qwen"
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
    QWEN2 = "qwen2"
    YI = "yi"
    DEEPSEEK = "deepseek"
    CODELLAMA = "codellama"
    MAGICODER = "magicoder"
    WIZARDCODER = "wizardcoder"
    PHI2 = "phi2"
    PHI3 = "phi3"
    GEMMA2 = "gemma2"
    MIXTRAL = "mixtral"
    LLAMA3 = "llama3"
    MISTRAL2 = "mistral2"
    UNKNOWN = "unknown"


@dataclass
class ModelInfo:
    """Information about a local model."""
    name: str
    filename: str
    size: int
    url: str
    description: str
    tags: List[str]
    backend: BackendType
    architecture: ModelArchitecture = ModelArchitecture.UNKNOWN
    context_length: int = 4096
    parameters: int = 0
    quantization: str = "Q4_K_M"  # Default quantization
    license: str = "Unknown"
    creator: str = "Unknown"
    training_data: str = "Unknown"
    capabilities: List[str] = None  # e.g., ["chat", "code", "reasoning"]
    benchmarks: Dict[str, float] = None  # Performance benchmarks
    requirements: Dict[str, str] = None  # System requirements


@dataclass
class InferenceConfig:
    """Configuration for model inference."""
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 40
    repeat_penalty: float = 1.1
    max_tokens: int = 2048
    context_length: int = 4096
    seed: int = -1
    threads: int = -1
    gpu_layers: int = 0
    batch_size: int = 512


class LocalModelManager(QObject):
    """Manager for local models using llama.cpp with multiple backends."""
    
    # Signals
    model_download_progress = pyqtSignal(str, int)  # model_name, progress_percentage
    model_download_complete = pyqtSignal(str, str)  # model_name, model_path
    model_download_error = pyqtSignal(str, str)  # model_name, error_message
    inference_started = pyqtSignal(str)  # model_name
    inference_complete = pyqtSignal(str, str)  # model_name, response
    inference_error = pyqtSignal(str, str)  # model_name, error_message
    inference_chunk = pyqtSignal(str, str)  # model_name, chunk
    
    def __init__(self):
        super().__init__()
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        self.available_models = self._load_available_models()
        self.downloaded_models = self._scan_downloaded_models()
        self.active_models = {}  # model_name -> subprocess
        self.backend_configs = self._get_backend_configs()
        
        # Initialize llama.cpp paths
        self.llama_cpp_path = self._find_llama_cpp()
        self._validate_backends()
    
    def _load_available_models(self) -> Dict[str, ModelInfo]:
        """Load available models from configuration."""
        models = {}
        
        # Llama 2 Models
        models.update({
            "llama-2-7b": ModelInfo(
                name="llama-2-7b",
                filename="llama-2-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf",
                description="Llama 2 7B parameter model, good balance of performance and resource usage",
                tags=["llama2", "7b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.LLAMA,
                context_length=4096,
                parameters=7_000_000_000,
                license="Meta License",
                creator="Meta",
                capabilities=["chat", "general"],
                requirements={"ram": "8GB", "vram": "4GB"}
            ),
            "llama-2-13b": ModelInfo(
                name="llama-2-13b",
                filename="llama-2-13b.gguf",
                size=8_000_000_000,
                url="https://huggingface.co/TheBloke/Llama-2-13B-GGUF/resolve/main/llama-2-13b.Q4_K_M.gguf",
                description="Llama 2 13B parameter model, better performance than 7B",
                tags=["llama2", "13b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.LLAMA,
                context_length=4096,
                parameters=13_000_000_000,
                license="Meta License",
                creator="Meta",
                capabilities=["chat", "general", "reasoning"]
            ),
            "llama-2-70b": ModelInfo(
                name="llama-2-70b",
                filename="llama-2-70b.gguf",
                size=40_000_000_000,
                url="https://huggingface.co/TheBloke/Llama-2-70B-GGUF/resolve/main/llama-2-70b.Q4_K_M.gguf",
                description="Llama 2 70B parameter model, highest quality but requires significant resources",
                tags=["llama2", "70b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.LLAMA,
                context_length=4096,
                parameters=70_000_000_000,
                license="Meta License",
                creator="Meta",
                capabilities=["chat", "general", "reasoning", "analysis"]
            )
        })
        
        # Llama 3 Models
        models.update({
            "llama-3-8b": ModelInfo(
                name="llama-3-8b",
                filename="llama-3-8b.gguf",
                size=5_000_000_000,
                url="https://huggingface.co/TheBloke/Llama-3-8B-GGUF/resolve/main/llama-3-8b.Q4_K_M.gguf",
                description="Llama 3 8B model, improved over Llama 2",
                tags=["llama3", "8b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.LLAMA3,
                context_length=8192,
                parameters=8_000_000_000,
                license="Meta License",
                creator="Meta",
                capabilities=["chat", "general", "reasoning"]
            ),
            "llama-3-70b": ModelInfo(
                name="llama-3-70b",
                filename="llama-3-70b.gguf",
                size=40_000_000_000,
                url="https://huggingface.co/TheBloke/Llama-3-70B-GGUF/resolve/main/llama-3-70b.Q4_K_M.gguf",
                description="Llama 3 70B model, state-of-the-art performance",
                tags=["llama3", "70b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.LLAMA3,
                context_length=8192,
                parameters=70_000_000_000,
                license="Meta License",
                creator="Meta",
                capabilities=["chat", "general", "reasoning", "analysis", "coding"]
            )
        })
        
        # Mistral Models
        models.update({
            "mistral-7b": ModelInfo(
                name="mistral-7b",
                filename="mistral-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF/resolve/main/mistral-7b-v0.1.Q4_K_M.gguf",
                description="Mistral 7B model, excellent performance for its size",
                tags=["mistral", "7b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.MISTRAL,
                context_length=8192,
                parameters=7_000_000_000,
                license="Apache 2.0",
                creator="Mistral AI",
                capabilities=["chat", "general", "reasoning"]
            ),
            "mistral-2-7b": ModelInfo(
                name="mistral-2-7b",
                filename="mistral-2-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/Mistral-2-7B-GGUF/resolve/main/mistral-2-7b.Q4_K_M.gguf",
                description="Mistral 2 7B model, improved over original Mistral",
                tags=["mistral2", "7b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.MISTRAL2,
                context_length=32768,
                parameters=7_000_000_000,
                license="Apache 2.0",
                creator="Mistral AI",
                capabilities=["chat", "general", "reasoning", "coding"]
            )
        })
        
        # Mixtral Models
        models.update({
            "mixtral-8x7b": ModelInfo(
                name="mixtral-8x7b",
                filename="mixtral-8x7b.gguf",
                size=26_000_000_000,
                url="https://huggingface.co/TheBloke/Mixtral-8x7B-v0.1-GGUF/resolve/main/mixtral-8x7b-v0.1.Q4_K_M.gguf",
                description="Mixtral 8x7B MoE model, excellent performance",
                tags=["mixtral", "8x7b", "moe", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.MIXTRAL,
                context_length=32768,
                parameters=47_000_000_000,
                license="Apache 2.0",
                creator="Mistral AI",
                capabilities=["chat", "general", "reasoning", "coding"]
            )
        })
        
        # Phi Models
        models.update({
            "phi-2": ModelInfo(
                name="phi-2",
                filename="phi-2.gguf",
                size=2_000_000_000,
                url="https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
                description="Microsoft Phi-2 model, small but capable",
                tags=["phi", "2.7b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.PHI,
                context_length=2048,
                parameters=2_700_000_000,
                license="MIT",
                creator="Microsoft",
                capabilities=["chat", "general", "coding"]
            ),
            "phi-3-mini": ModelInfo(
                name="phi-3-mini",
                filename="phi-3-mini.gguf",
                size=2_000_000_000,
                url="https://huggingface.co/TheBloke/Phi-3-mini-4K-instruct-GGUF/resolve/main/phi-3-mini-4k-instruct.Q4_K_M.gguf",
                description="Microsoft Phi-3 Mini model, improved reasoning",
                tags=["phi3", "3.8b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.PHI3,
                context_length=4096,
                parameters=3_800_000_000,
                license="MIT",
                creator="Microsoft",
                capabilities=["chat", "general", "reasoning", "coding"]
            )
        })
        
        # Gemma Models
        models.update({
            "gemma-2b": ModelInfo(
                name="gemma-2b",
                filename="gemma-2b.gguf",
                size=1_500_000_000,
                url="https://huggingface.co/TheBloke/Gemma-2B-GGUF/resolve/main/gemma-2b.Q4_K_M.gguf",
                description="Google Gemma 2B model, lightweight and fast",
                tags=["gemma", "2b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.GEMMA,
                context_length=8192,
                parameters=2_000_000_000,
                license="Gemma License",
                creator="Google",
                capabilities=["chat", "general"]
            ),
            "gemma-7b": ModelInfo(
                name="gemma-7b",
                filename="gemma-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/Gemma-7B-GGUF/resolve/main/gemma-7b.Q4_K_M.gguf",
                description="Google Gemma 7B model, good performance",
                tags=["gemma", "7b", "general"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.GEMMA,
                context_length=8192,
                parameters=7_000_000_000,
                license="Gemma License",
                creator="Google",
                capabilities=["chat", "general", "reasoning"]
            )
        })
        
        # Code Models
        models.update({
            "codellama-7b": ModelInfo(
                name="codellama-7b",
                filename="codellama-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf",
                description="Code Llama 7B model, specialized for code generation",
                tags=["codellama", "7b", "code"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.CODELLAMA,
                context_length=4096,
                parameters=7_000_000_000,
                license="Meta License",
                creator="Meta",
                capabilities=["code", "chat"]
            ),
            "wizardcoder-7b": ModelInfo(
                name="wizardcoder-7b",
                filename="wizardcoder-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/WizardCoder-7B-V1.0-GGUF/resolve/main/wizardcoder-7b-v1.0.Q4_K_M.gguf",
                description="WizardCoder 7B model, excellent for programming",
                tags=["wizardcoder", "7b", "code"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.WIZARDCODER,
                context_length=8192,
                parameters=7_000_000_000,
                license="Apache 2.0",
                creator="WizardLM",
                capabilities=["code", "chat", "debugging"]
            ),
            "starcoder-7b": ModelInfo(
                name="starcoder-7b",
                filename="starcoder-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/starcoder-GGUF/resolve/main/starcoder.Q4_K_M.gguf",
                description="StarCoder 7B model, trained on code",
                tags=["starcoder", "7b", "code"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.STARCODER,
                context_length=8192,
                parameters=7_000_000_000,
                license="BigCode OpenRAIL-M",
                creator="BigCode",
                capabilities=["code", "chat"]
            )
        })
        
        # Qwen Models
        models.update({
            "qwen-7b": ModelInfo(
                name="qwen-7b",
                filename="qwen-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/Qwen-7B-GGUF/resolve/main/qwen-7b.Q4_K_M.gguf",
                description="Qwen 7B model, good Chinese and English support",
                tags=["qwen", "7b", "multilingual"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.QWEN,
                context_length=8192,
                parameters=7_000_000_000,
                license="Qwen License",
                creator="Alibaba",
                capabilities=["chat", "general", "multilingual"]
            ),
            "qwen2-7b": ModelInfo(
                name="qwen2-7b",
                filename="qwen2-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/Qwen2-7B-GGUF/resolve/main/qwen2-7b.Q4_K_M.gguf",
                description="Qwen2 7B model, improved over Qwen",
                tags=["qwen2", "7b", "multilingual"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.QWEN2,
                context_length=32768,
                parameters=7_000_000_000,
                license="Qwen License",
                creator="Alibaba",
                capabilities=["chat", "general", "multilingual", "reasoning"]
            )
        })
        
        # Chinese Models
        models.update({
            "chatglm3-6b": ModelInfo(
                name="chatglm3-6b",
                filename="chatglm3-6b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/ChatGLM3-6B-GGUF/resolve/main/chatglm3-6b.Q4_K_M.gguf",
                description="ChatGLM3 6B model, excellent Chinese support",
                tags=["chatglm", "6b", "chinese"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.CHATGLM,
                context_length=8192,
                parameters=6_000_000_000,
                license="ChatGLM License",
                creator="THUDM",
                capabilities=["chat", "general", "chinese"]
            ),
            "baichuan2-7b": ModelInfo(
                name="baichuan2-7b",
                filename="baichuan2-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/Baichuan2-7B-GGUF/resolve/main/baichuan2-7b.Q4_K_M.gguf",
                description="Baichuan2 7B model, good Chinese performance",
                tags=["baichuan", "7b", "chinese"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.BAICHUAN,
                context_length=4096,
                parameters=7_000_000_000,
                license="Baichuan License",
                creator="Baichuan Inc",
                capabilities=["chat", "general", "chinese"]
            )
        })
        
        # Specialized Models
        models.update({
            "wizardlm-7b": ModelInfo(
                name="wizardlm-7b",
                filename="wizardlm-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/WizardLM-7B-V1.0-GGUF/resolve/main/wizardlm-7b-v1.0.Q4_K_M.gguf",
                description="WizardLM 7B model, instruction-tuned",
                tags=["wizardlm", "7b", "instruction"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.WIZARDLM,
                context_length=2048,
                parameters=7_000_000_000,
                license="Apache 2.0",
                creator="WizardLM",
                capabilities=["chat", "instruction", "reasoning"]
            ),
            "vicuna-7b": ModelInfo(
                name="vicuna-7b",
                filename="vicuna-7b.gguf",
                size=4_000_000_000,
                url="https://huggingface.co/TheBloke/vicuna-7B-v1.5-GGUF/resolve/main/vicuna-7b-v1.5.Q4_K_M.gguf",
                description="Vicuna 7B model, chat-optimized",
                tags=["vicuna", "7b", "chat"],
                backend=BackendType.CPU,
                architecture=ModelArchitecture.VICUNA,
                context_length=2048,
                parameters=7_000_000_000,
                license="Apache 2.0",
                creator="LMSYS",
                capabilities=["chat", "general"]
            )
        })
        
        return models
    
    def _scan_downloaded_models(self) -> Dict[str, str]:
        """Scan for already downloaded models."""
        downloaded = {}
        for model_file in self.models_dir.glob("*.gguf"):
            model_name = model_file.stem
            downloaded[model_name] = str(model_file)
        return downloaded
    
    def _get_backend_configs(self) -> Dict[BackendType, Dict[str, Any]]:
        """Get configuration for each backend."""
        return {
            BackendType.CPU: {
                "executable": "llama.cpp",
                "args": ["--n-gpu-layers", "0"],
                "env": {}
            },
            BackendType.CUDA: {
                "executable": "llama.cpp",
                "args": ["--n-gpu-layers", "35"],
                "env": {"CUDA_VISIBLE_DEVICES": "0"}
            },
            BackendType.VULKAN: {
                "executable": "llama.cpp",
                "args": ["--n-gpu-layers", "35", "--vulkan"],
                "env": {}
            },
            BackendType.ROCM: {
                "executable": "llama.cpp",
                "args": ["--n-gpu-layers", "35", "--rocm"],
                "env": {"HIP_VISIBLE_DEVICES": "0"}
            }
        }
    
    def _find_llama_cpp(self) -> Optional[str]:
        """Find llama.cpp executable."""
        possible_paths = [
            "llama.cpp",
            "./llama.cpp",
            "llama-cpp-python",
            "./llama-cpp-python",
            "build/bin/main",
            "./build/bin/main"
        ]
        
        for path in possible_paths:
            if shutil.which(path):
                return path
        
        # Check if llama-cpp-python is installed via pip
        try:
            import llama_cpp
            return "python -m llama_cpp.server"
        except ImportError:
            pass
        
        return None
    
    def _validate_backends(self):
        """Validate that required backends are available."""
        if not self.llama_cpp_path:
            logger.warning("llama.cpp not found. Local models will not be available.")
            return
        
        # Test each backend
        for backend_type, config in self.backend_configs.items():
            try:
                result = subprocess.run(
                    [self.llama_cpp_path, "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Backend {backend_type.value} is available")
                else:
                    logger.warning(f"Backend {backend_type.value} may not be working properly")
            except Exception as e:
                logger.warning(f"Backend {backend_type.value} not available: {e}")
    
    def get_available_models(self) -> Dict[str, ModelInfo]:
        """Get all available models."""
        return self.available_models
    
    def get_downloaded_models(self) -> Dict[str, str]:
        """Get list of downloaded models."""
        return self.downloaded_models
    
    def is_model_downloaded(self, model_name: str) -> bool:
        """Check if a model is downloaded."""
        return model_name in self.downloaded_models
    
    def download_model(self, model_name: str, progress_callback=None) -> bool:
        """Download a model."""
        if model_name not in self.available_models:
            self.model_download_error.emit(model_name, "Model not found")
            return False
        
        model_info = self.available_models[model_name]
        model_path = self.models_dir / model_info.filename
        
        if model_path.exists():
            self.model_download_complete.emit(model_name, str(model_path))
            return True
        
        try:
            # Create download thread
            download_thread = ModelDownloadThread(model_info, model_path, progress_callback)
            download_thread.download_progress.connect(self.model_download_progress.emit)
            download_thread.download_complete.connect(self.model_download_complete.emit)
            download_thread.download_error.connect(self.model_download_error.emit)
            download_thread.start()
            return True
        except Exception as e:
            error_msg = f"Failed to start download: {e}"
            self.model_download_error.emit(model_name, error_msg)
            return False
    
    def load_model(self, model_name: str, backend: BackendType = BackendType.CPU) -> bool:
        """Load a model for inference."""
        if not self.is_model_downloaded(model_name):
            logger.error(f"Model {model_name} not downloaded")
            return False
        
        if not self.llama_cpp_path:
            logger.error("llama.cpp not available")
            return False
        
        model_path = self.downloaded_models[model_name]
        
        try:
            # Start llama.cpp server process
            config = self.backend_configs[backend]
            cmd = [self.llama_cpp_path, "--model", model_path] + config["args"]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=config["env"]
            )
            
            self.active_models[model_name] = process
            logger.info(f"Loaded model {model_name} with backend {backend.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    def unload_model(self, model_name: str):
        """Unload a model."""
        if model_name in self.active_models:
            process = self.active_models[model_name]
            process.terminate()
            del self.active_models[model_name]
            logger.info(f"Unloaded model {model_name}")
    
    def generate_response(self, model_name: str, prompt: str, config: InferenceConfig = None) -> str:
        """Generate a response using a local model."""
        if model_name not in self.active_models:
            if not self.load_model(model_name):
                raise RuntimeError(f"Failed to load model {model_name}")
        
        if config is None:
            config = InferenceConfig()
        
        try:
            # Use llama-cpp-python for inference
            import llama_cpp
            
            model_path = self.downloaded_models[model_name]
            llm = llama_cpp.Llama(
                model_path=model_path,
                n_ctx=config.context_length,
                n_threads=config.threads,
                n_gpu_layers=config.gpu_layers,
                temperature=config.temperature,
                top_p=config.top_p,
                top_k=config.top_k,
                repeat_penalty=config.repeat_penalty,
                max_tokens=config.max_tokens,
                seed=config.seed
            )
            
            response = llm(prompt, max_tokens=config.max_tokens, temperature=config.temperature)
            return response["choices"][0]["text"]
            
        except ImportError:
            # Fallback to subprocess if llama-cpp-python not available
            return self._generate_response_subprocess(model_name, prompt, config)
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    def _generate_response_subprocess(self, model_name: str, prompt: str, config: InferenceConfig) -> str:
        """Generate response using subprocess (fallback method)."""
        if model_name not in self.active_models:
            raise RuntimeError(f"Model {model_name} not loaded")
        
        process = self.active_models[model_name]
        
        # Send prompt to process
        try:
            process.stdin.write(prompt + "\n")
            process.stdin.flush()
            
            response = ""
            while True:
                line = process.stdout.readline()
                if not line or line.strip() == "":
                    break
                response += line
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Subprocess generation failed: {e}")
            raise
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        return self.available_models.get(model_name)
    
    def get_supported_backends(self) -> List[BackendType]:
        """Get list of supported backends."""
        return list(self.backend_configs.keys())
    
    def get_models_by_architecture(self, architecture: ModelArchitecture) -> Dict[str, ModelInfo]:
        """Get all models of a specific architecture."""
        return {
            name: model for name, model in self.available_models.items()
            if model.architecture == architecture
        }
    
    def get_models_by_capability(self, capability: str) -> Dict[str, ModelInfo]:
        """Get all models that support a specific capability."""
        return {
            name: model for name, model in self.available_models.items()
            if model.capabilities and capability in model.capabilities
        }
    
    def get_models_by_size(self, max_size_gb: float) -> Dict[str, ModelInfo]:
        """Get all models smaller than or equal to the specified size in GB."""
        max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        return {
            name: model for name, model in self.available_models.items()
            if model.size <= max_size_bytes
        }
    
    def get_models_by_license(self, license_type: str) -> Dict[str, ModelInfo]:
        """Get all models with a specific license type."""
        return {
            name: model for name, model in self.available_models.items()
            if license_type.lower() in model.license.lower()
        }
    
    def get_model_architectures(self) -> List[ModelArchitecture]:
        """Get list of all available model architectures."""
        architectures = set()
        for model in self.available_models.values():
            architectures.add(model.architecture)
        return list(architectures)
    
    def get_model_capabilities(self) -> List[str]:
        """Get list of all available model capabilities."""
        capabilities = set()
        for model in self.available_models.values():
            if model.capabilities:
                capabilities.update(model.capabilities)
        return list(capabilities)
    
    def get_architecture_info(self, architecture: ModelArchitecture) -> Dict[str, Any]:
        """Get information about a specific architecture."""
        arch_info = {
            "name": architecture.value,
            "description": self._get_architecture_description(architecture),
            "models": self.get_models_by_architecture(architecture),
            "capabilities": self._get_architecture_capabilities(architecture),
            "requirements": self._get_architecture_requirements(architecture)
        }
        return arch_info
    
    def _get_architecture_description(self, architecture: ModelArchitecture) -> str:
        """Get description for a model architecture."""
        descriptions = {
            ModelArchitecture.LLAMA: "Meta's Llama architecture, excellent for general tasks",
            ModelArchitecture.LLAMA3: "Meta's latest Llama 3 architecture with improved performance",
            ModelArchitecture.MISTRAL: "Mistral AI's efficient architecture with good reasoning",
            ModelArchitecture.MISTRAL2: "Mistral AI's improved architecture with longer context",
            ModelArchitecture.MIXTRAL: "Mistral AI's Mixture of Experts architecture",
            ModelArchitecture.PHI: "Microsoft's Phi architecture, good for coding",
            ModelArchitecture.PHI3: "Microsoft's latest Phi 3 architecture",
            ModelArchitecture.GEMMA: "Google's Gemma architecture, lightweight and fast",
            ModelArchitecture.QWEN: "Alibaba's Qwen architecture with multilingual support",
            ModelArchitecture.QWEN2: "Alibaba's improved Qwen 2 architecture",
            ModelArchitecture.CODELLAMA: "Meta's Code Llama, specialized for programming",
            ModelArchitecture.WIZARDCODER: "WizardLM's coding-specialized architecture",
            ModelArchitecture.STARCODER: "BigCode's StarCoder architecture for code generation",
            ModelArchitecture.CHATGLM: "THUDM's ChatGLM architecture with Chinese support",
            ModelArchitecture.BAICHUAN: "Baichuan's architecture with Chinese optimization",
            ModelArchitecture.WIZARDLM: "WizardLM's instruction-tuned architecture",
            ModelArchitecture.VICUNA: "LMSYS's Vicuna architecture for chat optimization"
        }
        return descriptions.get(architecture, "Unknown architecture")
    
    def _get_architecture_capabilities(self, architecture: ModelArchitecture) -> List[str]:
        """Get typical capabilities for a model architecture."""
        capabilities = {
            ModelArchitecture.LLAMA: ["chat", "general", "reasoning"],
            ModelArchitecture.LLAMA3: ["chat", "general", "reasoning", "coding"],
            ModelArchitecture.MISTRAL: ["chat", "general", "reasoning"],
            ModelArchitecture.MISTRAL2: ["chat", "general", "reasoning", "coding"],
            ModelArchitecture.MIXTRAL: ["chat", "general", "reasoning", "coding"],
            ModelArchitecture.PHI: ["chat", "general", "coding"],
            ModelArchitecture.PHI3: ["chat", "general", "reasoning", "coding"],
            ModelArchitecture.GEMMA: ["chat", "general"],
            ModelArchitecture.QWEN: ["chat", "general", "multilingual"],
            ModelArchitecture.QWEN2: ["chat", "general", "multilingual", "reasoning"],
            ModelArchitecture.CODELLAMA: ["code", "chat"],
            ModelArchitecture.WIZARDCODER: ["code", "chat", "debugging"],
            ModelArchitecture.STARCODER: ["code", "chat"],
            ModelArchitecture.CHATGLM: ["chat", "general", "chinese"],
            ModelArchitecture.BAICHUAN: ["chat", "general", "chinese"],
            ModelArchitecture.WIZARDLM: ["chat", "instruction", "reasoning"],
            ModelArchitecture.VICUNA: ["chat", "general"]
        }
        return capabilities.get(architecture, [])
    
    def _get_architecture_requirements(self, architecture: ModelArchitecture) -> Dict[str, str]:
        """Get typical system requirements for a model architecture."""
        requirements = {
            ModelArchitecture.LLAMA: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.LLAMA3: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.MISTRAL: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.MISTRAL2: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.MIXTRAL: {"ram": "32GB", "vram": "16GB"},
            ModelArchitecture.PHI: {"ram": "4GB", "vram": "2GB"},
            ModelArchitecture.PHI3: {"ram": "6GB", "vram": "3GB"},
            ModelArchitecture.GEMMA: {"ram": "4GB", "vram": "2GB"},
            ModelArchitecture.QWEN: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.QWEN2: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.CODELLAMA: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.WIZARDCODER: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.STARCODER: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.CHATGLM: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.BAICHUAN: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.WIZARDLM: {"ram": "8GB", "vram": "4GB"},
            ModelArchitecture.VICUNA: {"ram": "8GB", "vram": "4GB"}
        }
        return requirements.get(architecture, {})
    
    def cleanup(self):
        """Cleanup resources."""
        for model_name in list(self.active_models.keys()):
            self.unload_model(model_name)


class ModelDownloadThread(QThread):
    """Thread for downloading models."""
    
    download_progress = pyqtSignal(str, int)  # model_name, progress
    download_complete = pyqtSignal(str, str)  # model_name, model_path
    download_error = pyqtSignal(str, str)  # model_name, error
    
    def __init__(self, model_info: ModelInfo, model_path: Path, progress_callback=None):
        super().__init__()
        self.model_info = model_info
        self.model_path = model_path
        self.progress_callback = progress_callback
    
    def run(self):
        """Download the model."""
        try:
            response = requests.get(self.model_info.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.download_progress.emit(self.model_info.name, progress)
            
            self.download_complete.emit(self.model_info.name, str(self.model_path))
            
        except Exception as e:
            self.download_error.emit(self.model_info.name, str(e))
            # Clean up partial download
            if self.model_path.exists():
                self.model_path.unlink()


class LocalModelProvider:
    """Provider interface for local models."""
    
    def __init__(self, manager: LocalModelManager):
        self.manager = manager
        self.name = "Local Models"
        self.models = {}
        self._update_models()
    
    def _update_models(self):
        """Update available models."""
        self.models = {}
        for model_name, model_info in self.manager.get_available_models().items():
            if self.manager.is_model_downloaded(model_name):
                self.models[model_name] = {
                    "name": model_name,
                    "description": model_info.description,
                    "backend": model_info.backend.value,
                    "context_length": model_info.context_length,
                    "parameters": model_info.parameters
                }
    
    def get_models(self) -> Dict[str, Dict]:
        """Get available models."""
        self._update_models()
        return self.models
    
    def generate_response(self, model_name: str, prompt: str, **kwargs) -> str:
        """Generate a response."""
        config = InferenceConfig(**kwargs)
        return self.manager.generate_response(model_name, prompt, config)
    
    def is_available(self) -> bool:
        """Check if local models are available."""
        return self.manager.llama_cpp_path is not None and len(self.manager.get_downloaded_models()) > 0 
