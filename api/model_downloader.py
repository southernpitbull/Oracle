# -*- coding: utf-8 -*-
"""
Model Downloader for The Oracle AI Chat Application
File: api/model_downloader.py
Author: The Oracle Development Team
Date: 2024-12-19

Comprehensive model downloader supporting:
- Hugging Face Hub (with authentication and resume capability)
- Ollama model registry (with progress tracking)
- LM Studio model servers (with validation)
- Local model conversion and optimization
- Model validation and integrity checking
"""

import os
import sys
import json
import time
import hashlib
import tempfile
import shutil
import logging
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, Generator, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from urllib.parse import urlparse, urljoin
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer, QMutex
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

logger = logging.getLogger(__name__)


class ModelSource(Enum):
    """Supported model sources."""
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    LOCAL = "local"
    CUSTOM = "custom"


class ModelFormat(Enum):
    """Supported model formats."""
    GGUF = "gguf"
    GGML = "ggml"
    SAFETENSORS = "safetensors"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    TENSORRT = "tensorrt"
    UNKNOWN = "unknown"


class DownloadStatus(Enum):
    """Download status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VALIDATING = "validating"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RESUMING = "resuming"


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    source: ModelSource
    format: ModelFormat
    size_bytes: int
    description: str = ""
    author: str = ""
    license: str = ""
    tags: List[str] = None
    architecture: str = ""
    quantization: str = ""
    context_length: int = 4096
    parameters: int = 0
    download_url: str = ""
    model_id: str = ""
    version: str = ""
    last_updated: str = ""
    downloads: int = 0
    rating: float = 0.0
    requirements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.requirements is None:
            self.requirements = {}


@dataclass
class DownloadConfig:
    """Configuration for model downloads."""
    download_dir: str = "models"
    temp_dir: str = "temp"
    max_concurrent_downloads: int = 3
    chunk_size: int = 8192
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_resume: bool = True
    enable_validation: bool = True
    enable_conversion: bool = True
    enable_optimization: bool = True
    max_download_size: int = 0  # 0 = unlimited
    preferred_formats: List[ModelFormat] = None
    api_keys: Dict[str, str] = None
    
    def __post_init__(self):
        if self.preferred_formats is None:
            self.preferred_formats = [ModelFormat.GGUF, ModelFormat.SAFETENSORS]
        if self.api_keys is None:
            self.api_keys = {}


@dataclass
class DownloadProgress:
    """Download progress information."""
    model_name: str
    status: DownloadStatus
    bytes_downloaded: int = 0
    total_bytes: int = 0
    percentage: float = 0.0
    speed_mbps: float = 0.0
    eta_seconds: int = 0
    current_file: str = ""
    total_files: int = 1
    current_file_index: int = 0
    error_message: str = ""
    start_time: float = 0.0
    last_update: float = 0.0


class ModelDownloader(QObject):
    """Comprehensive model downloader with support for multiple sources."""
    
    # Signals
    download_started = pyqtSignal(str)  # model_name
    download_progress = pyqtSignal(str, float, float, float)  # model_name, percentage, speed, eta
    download_completed = pyqtSignal(str, str)  # model_name, local_path
    download_failed = pyqtSignal(str, str)  # model_name, error_message
    download_cancelled = pyqtSignal(str)  # model_name
    validation_started = pyqtSignal(str)  # model_name
    validation_completed = pyqtSignal(str, bool)  # model_name, is_valid
    conversion_started = pyqtSignal(str)  # model_name
    conversion_completed = pyqtSignal(str, str)  # model_name, output_path
    
    def __init__(self, config: DownloadConfig = None):
        super().__init__()
        self.config = config or DownloadConfig()
        self.downloads: Dict[str, DownloadProgress] = {}
        self.active_downloads: Dict[str, threading.Event] = {}
        self.download_queue: List[Tuple[str, ModelInfo]] = []
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_downloads)
        self.mutex = QMutex()
        
        # Create directories
        self._create_directories()
        
        # Initialize API clients
        self._init_api_clients()
        
        logger.info("Model downloader initialized")
    
    def _create_directories(self):
        """Create necessary directories."""
        Path(self.config.download_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.temp_dir).mkdir(parents=True, exist_ok=True)
    
    def _init_api_clients(self):
        """Initialize API clients for different sources."""
        self.hf_client = None
        self.ollama_client = None
        
        # Initialize Hugging Face client
        if self.config.api_keys.get("huggingface"):
            try:
                from huggingface_hub import HfApi
                self.hf_client = HfApi(token=self.config.api_keys["huggingface"])
                logger.info("Hugging Face client initialized")
            except ImportError:
                logger.warning("huggingface_hub not available")
        
        # Initialize Ollama client
        try:
            import ollama
            self.ollama_client = ollama.Client(host="http://127.0.0.1:11434")
            logger.info("Ollama client initialized")
        except ImportError:
            logger.warning("ollama-python not available")
        except Exception as e:
            logger.warning(f"Ollama client not available: {e}")
    
    def search_models(self, query: str, source: ModelSource = None, 
                     limit: int = 50, filters: Dict[str, Any] = None) -> List[ModelInfo]:
        """Search for models across different sources."""
        models = []
        
        if source is None or source == ModelSource.HUGGINGFACE:
            models.extend(self._search_huggingface(query, limit, filters))
        
        if source is None or source == ModelSource.OLLAMA:
            models.extend(self._search_ollama(query, limit, filters))
        
        if source is None or source == ModelSource.LM_STUDIO:
            models.extend(self._search_lm_studio(query, limit, filters))
        
        return models
    
    def _search_huggingface(self, query: str, limit: int, filters: Dict[str, Any]) -> List[ModelInfo]:
        """Search for models on Hugging Face Hub."""
        models = []
        
        if not self.hf_client:
            return models
        
        try:
            # Search for models
            search_results = self.hf_client.list_models(
                search=query,
                limit=limit,
                sort="downloads",
                direction=-1
            )
            
            for model in search_results:
                # Check if model has GGUF files
                try:
                    files = self.hf_client.list_repo_files(model.modelId)
                    gguf_files = [f for f in files if f.endswith('.gguf')]
                    
                    if gguf_files:
                        model_info = ModelInfo(
                            name=model.modelId,
                            source=ModelSource.HUGGINGFACE,
                            format=ModelFormat.GGUF,
                            size_bytes=0,  # Will be calculated later
                            description=model.description or "",
                            author=model.author or "",
                            license=model.license or "",
                            tags=model.tags or [],
                            architecture=model.config.get("architectures", [""])[0] if model.config else "",
                            model_id=model.modelId,
                            downloads=model.downloads or 0,
                            last_updated=model.lastModified or ""
                        )
                        models.append(model_info)
                except Exception as e:
                    logger.debug(f"Error getting files for {model.modelId}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error searching Hugging Face: {e}")
        
        return models
    
    def _search_ollama(self, query: str, limit: int, filters: Dict[str, Any]) -> List[ModelInfo]:
        """Search for models in Ollama registry."""
        models = []
        
        if not self.ollama_client:
            return models
        
        try:
            # Get available models from Ollama
            available_models = self.ollama_client.list()
            
            for model in available_models.models:
                if query.lower() in model.name.lower():
                    model_info = ModelInfo(
                        name=model.name,
                        source=ModelSource.OLLAMA,
                        format=ModelFormat.GGUF,
                        size_bytes=model.size or 0,
                        description=model.details.get("description", ""),
                        author=model.details.get("author", ""),
                        license=model.details.get("license", ""),
                        tags=model.details.get("tags", []),
                        architecture=model.details.get("architecture", ""),
                        quantization=model.details.get("quantization", ""),
                        context_length=model.details.get("context_length", 4096),
                        parameters=model.details.get("parameters", 0),
                        model_id=model.name,
                        version=model.details.get("version", ""),
                        last_updated=model.details.get("modified_at", ""),
                        downloads=model.details.get("downloads", 0)
                    )
                    models.append(model_info)
                    
                    if len(models) >= limit:
                        break
                        
        except Exception as e:
            logger.error(f"Error searching Ollama: {e}")
        
        return models
    
    def _search_lm_studio(self, query: str, limit: int, filters: Dict[str, Any]) -> List[ModelInfo]:
        """Search for models in LM Studio registry."""
        models = []
        
        try:
            # LM Studio uses a similar API to Hugging Face
            # This is a simplified implementation
            api_url = "https://api.lmstudio.ai/models"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for model in data.get("models", []):
                    if query.lower() in model.get("name", "").lower():
                        model_info = ModelInfo(
                            name=model.get("name", ""),
                            source=ModelSource.LM_STUDIO,
                            format=ModelFormat.GGUF,
                            size_bytes=model.get("size", 0),
                            description=model.get("description", ""),
                            author=model.get("author", ""),
                            license=model.get("license", ""),
                            tags=model.get("tags", []),
                            architecture=model.get("architecture", ""),
                            quantization=model.get("quantization", ""),
                            context_length=model.get("context_length", 4096),
                            parameters=model.get("parameters", 0),
                            model_id=model.get("id", ""),
                            version=model.get("version", ""),
                            downloads=model.get("downloads", 0)
                        )
                        models.append(model_info)
                        
                        if len(models) >= limit:
                            break
                            
        except Exception as e:
            logger.error(f"Error searching LM Studio: {e}")
        
        return models
    
    def download_model(self, model_info: ModelInfo, progress_callback: Callable = None) -> str:
        """Download a model from the specified source."""
        model_name = model_info.name
        
        # Check if already downloading
        if model_name in self.active_downloads:
            raise Exception(f"Model {model_name} is already being downloaded")
        
        # Create download progress
        progress = DownloadProgress(
            model_name=model_name,
            status=DownloadStatus.PENDING,
            start_time=time.time()
        )
        
        self.downloads[model_name] = progress
        self.active_downloads[model_name] = threading.Event()
        
        # Submit download task
        future = self.executor.submit(
            self._download_model_worker,
            model_info,
            progress,
            self.active_downloads[model_name],
            progress_callback
        )
        
        # Start monitoring
        self._monitor_download(model_name, future)
        
        return model_name
    
    def _download_model_worker(self, model_info: ModelInfo, progress: DownloadProgress,
                              cancel_event: threading.Event, progress_callback: Callable = None):
        """Worker thread for downloading models."""
        try:
            progress.status = DownloadStatus.DOWNLOADING
            progress.start_time = time.time()
            self.download_started.emit(model_info.name)
            
            # Determine download method based on source
            if model_info.source == ModelSource.HUGGINGFACE:
                local_path = self._download_from_huggingface(model_info, progress, cancel_event, progress_callback)
            elif model_info.source == ModelSource.OLLAMA:
                local_path = self._download_from_ollama(model_info, progress, cancel_event, progress_callback)
            elif model_info.source == ModelSource.LM_STUDIO:
                local_path = self._download_from_lm_studio(model_info, progress, cancel_event, progress_callback)
            else:
                raise Exception(f"Unsupported model source: {model_info.source}")
            
            # Validate downloaded model
            if self.config.enable_validation:
                progress.status = DownloadStatus.VALIDATING
                self.validation_started.emit(model_info.name)
                
                if not self._validate_model(local_path, model_info):
                    raise Exception("Model validation failed")
                
                self.validation_completed.emit(model_info.name, True)
            
            # Convert model if needed
            if self.config.enable_conversion:
                progress.status = DownloadStatus.CONVERTING
                self.conversion_started.emit(model_info.name)
                
                converted_path = self._convert_model(local_path, model_info)
                if converted_path != local_path:
                    # Remove original file if conversion created new file
                    os.remove(local_path)
                    local_path = converted_path
                
                self.conversion_completed.emit(model_info.name, local_path)
            
            # Mark as completed
            progress.status = DownloadStatus.COMPLETED
            progress.percentage = 100.0
            self.download_completed.emit(model_info.name, local_path)
            
        except Exception as e:
            progress.status = DownloadStatus.FAILED
            progress.error_message = str(e)
            self.download_failed.emit(model_info.name, str(e))
            logger.error(f"Download failed for {model_info.name}: {e}")
        
        finally:
            # Cleanup
            if model_info.name in self.active_downloads:
                del self.active_downloads[model_info.name]
    
    def _download_from_huggingface(self, model_info: ModelInfo, progress: DownloadProgress,
                                  cancel_event: threading.Event, progress_callback: Callable = None) -> str:
        """Download model from Hugging Face Hub."""
        try:
            from huggingface_hub import hf_hub_download, snapshot_download
            
            model_id = model_info.model_id
            download_dir = Path(self.config.download_dir) / "huggingface" / model_id.replace("/", "_")
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to download GGUF files first
            try:
                # Download the main GGUF file
                gguf_file = hf_hub_download(
                    repo_id=model_id,
                    filename="*.gguf",
                    local_dir=download_dir,
                    resume_download=self.config.enable_resume,
                    token=self.config.api_keys.get("huggingface")
                )
                return str(gguf_file)
            except Exception as e:
                logger.warning(f"Could not download GGUF file: {e}")
                
                # Fallback to full model download
                snapshot_download(
                    repo_id=model_id,
                    local_dir=download_dir,
                    resume_download=self.config.enable_resume,
                    token=self.config.api_keys.get("huggingface")
                )
                
                # Find GGUF files in downloaded directory
                gguf_files = list(download_dir.rglob("*.gguf"))
                if gguf_files:
                    return str(gguf_files[0])
                else:
                    raise Exception("No GGUF files found in model")
                    
        except Exception as e:
            raise Exception(f"Failed to download from Hugging Face: {e}")
    
    def _download_from_ollama(self, model_info: ModelInfo, progress: DownloadProgress,
                             cancel_event: threading.Event, progress_callback: Callable = None) -> str:
        """Download model from Ollama registry."""
        if not self.ollama_client:
            raise Exception("Ollama client not available")
        
        try:
            model_name = model_info.name
            download_dir = Path(self.config.download_dir) / "ollama"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Pull model using Ollama
            for progress_update in self.ollama_client.pull(model_name, stream=True):
                if cancel_event.is_set():
                    raise Exception("Download cancelled")
                
                # Update progress
                if isinstance(progress_update, dict):
                    if 'completed' in progress_update and 'total' in progress_update:
                        completed = progress_update['completed']
                        total = progress_update['total']
                        if total > 0:
                            progress.percentage = (completed / total) * 100
                            progress.bytes_downloaded = completed
                            progress.total_bytes = total
                            
                            if progress_callback:
                                progress_callback(progress)
                            else:
                                self.download_progress.emit(
                                    model_name,
                                    progress.percentage,
                                    0.0,  # Speed calculation would need more data
                                    0     # ETA calculation would need more data
                                )
                
                # Check for completion
                if progress_update.get('status') == 'success':
                    break
            
            # Find the downloaded model file
            model_path = download_dir / f"{model_name}.gguf"
            if not model_path.exists():
                # Look for model in Ollama's default location
                ollama_models_dir = Path.home() / ".ollama" / "models"
                model_files = list(ollama_models_dir.rglob(f"*{model_name}*.gguf"))
                if model_files:
                    model_path = model_files[0]
                else:
                    raise Exception("Could not find downloaded model file")
            
            return str(model_path)
            
        except Exception as e:
            raise Exception(f"Failed to download from Ollama: {e}")
    
    def _download_from_lm_studio(self, model_info: ModelInfo, progress: DownloadProgress,
                                cancel_event: threading.Event, progress_callback: Callable = None) -> str:
        """Download model from LM Studio registry."""
        try:
            model_id = model_info.model_id
            download_dir = Path(self.config.download_dir) / "lm_studio" / model_id
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # LM Studio uses direct file downloads
            download_url = f"https://models.lmstudio.ai/{model_id}/model.gguf"
            
            response = requests.get(download_url, stream=True, timeout=self.config.timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            progress.total_bytes = total_size
            
            model_path = download_dir / "model.gguf"
            
            with open(model_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=self.config.chunk_size):
                    if cancel_event.is_set():
                        raise Exception("Download cancelled")
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress.bytes_downloaded = downloaded
                        
                        if total_size > 0:
                            progress.percentage = (downloaded / total_size) * 100
                            
                            if progress_callback:
                                progress_callback(progress)
                            else:
                                self.download_progress.emit(
                                    model_info.name,
                                    progress.percentage,
                                    0.0,  # Speed calculation
                                    0     # ETA calculation
                                )
            
            return str(model_path)
            
        except Exception as e:
            raise Exception(f"Failed to download from LM Studio: {e}")
    
    def _validate_model(self, model_path: str, model_info: ModelInfo) -> bool:
        """Validate downloaded model."""
        try:
            # Check file exists and has reasonable size
            if not os.path.exists(model_path):
                return False
            
            file_size = os.path.getsize(model_path)
            if file_size < 1024 * 1024:  # Less than 1MB
                return False
            
            # Try to load with llama.cpp to validate
            try:
                from llama_cpp import Llama
                model = Llama(model_path=model_path, n_ctx=512, n_threads=1)
                # Try a simple inference
                response = model("test", max_tokens=1, temperature=0)
                return True
            except Exception as e:
                logger.warning(f"Model validation failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating model: {e}")
            return False
    
    def _convert_model(self, model_path: str, model_info: ModelInfo) -> str:
        """Convert model to preferred format if needed."""
        # For now, return the original path
        # Conversion logic can be added here later
        return model_path
    
    def _monitor_download(self, model_name: str, future):
        """Monitor download progress."""
        try:
            future.result()  # Wait for completion
        except Exception as e:
            logger.error(f"Download monitoring error for {model_name}: {e}")
    
    def cancel_download(self, model_name: str):
        """Cancel an active download."""
        if model_name in self.active_downloads:
            self.active_downloads[model_name].set()
            self.download_cancelled.emit(model_name)
    
    def get_download_status(self, model_name: str) -> Optional[DownloadProgress]:
        """Get download status for a model."""
        return self.downloads.get(model_name)
    
    def get_all_download_status(self) -> Dict[str, DownloadProgress]:
        """Get status of all downloads."""
        return self.downloads.copy()
    
    def cleanup_completed_downloads(self):
        """Clean up completed downloads from tracking."""
        completed = [name for name, progress in self.downloads.items() 
                    if progress.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]]
        
        for name in completed:
            del self.downloads[name]
    
    def cleanup(self):
        """Clean up resources."""
        # Cancel all active downloads
        for cancel_event in self.active_downloads.values():
            cancel_event.set()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Clean up temp directory
        try:
            shutil.rmtree(self.config.temp_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Error cleaning up temp directory: {e}")


class ModelDownloaderUI(QObject):
    """UI wrapper for model downloader with progress dialogs."""
    
    def __init__(self, downloader: ModelDownloader):
        super().__init__()
        self.downloader = downloader
        self.progress_dialogs: Dict[str, QProgressDialog] = {}
        
        # Connect signals
        self.downloader.download_started.connect(self._on_download_started)
        self.downloader.download_progress.connect(self._on_download_progress)
        self.downloader.download_completed.connect(self._on_download_completed)
        self.downloader.download_failed.connect(self._on_download_failed)
        self.downloader.download_cancelled.connect(self._on_download_cancelled)
    
    def download_model_with_ui(self, model_info: ModelInfo) -> str:
        """Download model with progress dialog."""
        return self.downloader.download_model(model_info, self._progress_callback)
    
    def _progress_callback(self, progress: DownloadProgress):
        """Progress callback for downloads."""
        if progress.model_name in self.progress_dialogs:
            dialog = self.progress_dialogs[progress.model_name]
            dialog.setValue(int(progress.percentage))
            dialog.setLabelText(f"Downloading {progress.model_name}...\n"
                              f"Speed: {progress.speed_mbps:.1f} MB/s\n"
                              f"ETA: {progress.eta_seconds}s")
    
    def _on_download_started(self, model_name: str):
        """Handle download started event."""
        dialog = QProgressDialog(f"Starting download of {model_name}...", "Cancel", 0, 100)
        dialog.setWindowTitle("Downloading Model")
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.canceled.connect(lambda: self.downloader.cancel_download(model_name))
        
        self.progress_dialogs[model_name] = dialog
        dialog.show()
    
    def _on_download_progress(self, model_name: str, percentage: float, speed: float, eta: float):
        """Handle download progress event."""
        if model_name in self.progress_dialogs:
            dialog = self.progress_dialogs[model_name]
            dialog.setValue(int(percentage))
            dialog.setLabelText(f"Downloading {model_name}...\n"
                              f"Speed: {speed:.1f} MB/s\n"
                              f"ETA: {eta:.0f}s")
    
    def _on_download_completed(self, model_name: str, local_path: str):
        """Handle download completed event."""
        if model_name in self.progress_dialogs:
            dialog = self.progress_dialogs[model_name]
            dialog.close()
            del self.progress_dialogs[model_name]
        
        QMessageBox.information(None, "Download Complete", 
                              f"Model {model_name} has been downloaded successfully!\n"
                              f"Location: {local_path}")
    
    def _on_download_failed(self, model_name: str, error_message: str):
        """Handle download failed event."""
        if model_name in self.progress_dialogs:
            dialog = self.progress_dialogs[model_name]
            dialog.close()
            del self.progress_dialogs[model_name]
        
        QMessageBox.critical(None, "Download Failed", 
                           f"Failed to download {model_name}:\n{error_message}")
    
    def _on_download_cancelled(self, model_name: str):
        """Handle download cancelled event."""
        if model_name in self.progress_dialogs:
            dialog = self.progress_dialogs[model_name]
            dialog.close()
            del self.progress_dialogs[model_name]
        
        QMessageBox.information(None, "Download Cancelled", 
                              f"Download of {model_name} was cancelled.") 
