"""
Quick Switch Model Menu - Rapid model switching functionality.

This module provides a quick-switch interface for rapidly changing between
different AI models without navigating through settings menus.
"""

import json
import os
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QCompleter, QLineEdit
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from utils.error_handler import (
    ErrorHandler, ErrorSeverity, ErrorCategory,
    error_handler, safe_execute, retry_on_failure
)


@dataclass
class ModelInfo:
    """Information about an AI model."""
    provider: str
    model_name: str
    display_name: str
    is_available: bool = True
    api_key_required: bool = True
    has_valid_key: bool = False
    cost_per_1k_tokens: Optional[float] = None
    max_tokens: Optional[int] = None
    supports_vision: bool = False
    supports_audio: bool = False
    supports_function_calling: bool = False
    context_window: Optional[int] = None
    last_used: Optional[str] = None
    usage_count: int = 0


class QuickSwitchModelMenu(QObject):
    """
    Quick-switch model menu for rapid model selection.
    
    Provides a searchable interface to quickly switch between available
    AI models with filtering, sorting, and recent usage tracking.
    """
    
    # Signals
    model_selected = pyqtSignal(str, str)  # provider, model_name
    model_switched = pyqtSignal(str, str)  # provider, model_name
    models_updated = pyqtSignal(list)  # List[ModelInfo]
    error_occurred = pyqtSignal(str)  # error_message
    
    def __init__(self, settings_manager=None, api_manager=None):
        super().__init__()
        
        # Initialize error handler
        self.error_handler = ErrorHandler()
        
        # Dependencies
        self.settings_manager = settings_manager
        self.api_manager = api_manager
        
        # Model data
        self.models: Dict[str, ModelInfo] = {}
        self.recent_models: List[str] = []
        self.favorite_models: List[str] = []
        
        # UI components (will be set by the main window)
        self.completer: Optional[QCompleter] = None
        self.search_input: Optional[QLineEdit] = None
        
        # Configuration
        self.max_recent_models = 10
        self.max_favorite_models = 20
        self.auto_refresh_interval = 30000  # 30 seconds
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_models)
        
        # Initialize
        self._load_configuration()
        self._initialize_models()
        self._start_auto_refresh()
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to load quick switch configuration")
    def _load_configuration(self):
        """Load configuration from settings."""
        try:
            config_path = Path.home() / ".oracle" / "quick_switch_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                self.recent_models = config.get('recent_models', [])
                self.favorite_models = config.get('favorite_models', [])
                self.max_recent_models = config.get('max_recent_models', 10)
                self.max_favorite_models = config.get('max_favorite_models', 20)
                
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to load quick switch configuration: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.CONFIGURATION
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to save quick switch configuration")
    def _save_configuration(self):
        """Save configuration to settings."""
        try:
            config_dir = Path.home() / ".oracle"
            config_dir.mkdir(exist_ok=True)
            
            config_path = config_dir / "quick_switch_config.json"
            config = {
                'recent_models': self.recent_models,
                'favorite_models': self.favorite_models,
                'max_recent_models': self.max_recent_models,
                'max_favorite_models': self.max_favorite_models
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to save quick switch configuration: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.CONFIGURATION
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to initialize models")
    def _initialize_models(self):
        """Initialize the model list with available models."""
        try:
            # Define available models by provider
            model_definitions = {
                'OpenAI': [
                    ModelInfo('OpenAI', 'gpt-4o', 'GPT-4o', cost_per_1k_tokens=5.0, max_tokens=128000, supports_vision=True, supports_function_calling=True, context_window=128000),
                    ModelInfo('OpenAI', 'gpt-4o-mini', 'GPT-4o Mini', cost_per_1k_tokens=0.15, max_tokens=128000, supports_vision=True, supports_function_calling=True, context_window=128000),
                    ModelInfo('OpenAI', 'gpt-4-turbo', 'GPT-4 Turbo', cost_per_1k_tokens=10.0, max_tokens=128000, supports_vision=True, supports_function_calling=True, context_window=128000),
                    ModelInfo('OpenAI', 'gpt-3.5-turbo', 'GPT-3.5 Turbo', cost_per_1k_tokens=0.5, max_tokens=16385, supports_function_calling=True, context_window=16385),
                ],
                'Anthropic': [
                    ModelInfo('Anthropic', 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', cost_per_1k_tokens=3.0, max_tokens=200000, supports_vision=True, supports_function_calling=True, context_window=200000),
                    ModelInfo('Anthropic', 'claude-3-5-haiku-20241022', 'Claude 3.5 Haiku', cost_per_1k_tokens=0.25, max_tokens=200000, supports_vision=True, supports_function_calling=True, context_window=200000),
                    ModelInfo('Anthropic', 'claude-3-opus-20240229', 'Claude 3 Opus', cost_per_1k_tokens=15.0, max_tokens=200000, supports_vision=True, supports_function_calling=True, context_window=200000),
                ],
                'Google': [
                    ModelInfo('Google', 'gemini-1.5-pro', 'Gemini 1.5 Pro', cost_per_1k_tokens=3.5, max_tokens=1000000, supports_vision=True, supports_function_calling=True, context_window=1000000),
                    ModelInfo('Google', 'gemini-1.5-flash', 'Gemini 1.5 Flash', cost_per_1k_tokens=0.075, max_tokens=1000000, supports_vision=True, supports_function_calling=True, context_window=1000000),
                ],
                'Ollama': [
                    ModelInfo('Ollama', 'llama3.2', 'Llama 3.2', api_key_required=False, cost_per_1k_tokens=0.0, max_tokens=8192, context_window=8192),
                    ModelInfo('Ollama', 'llama3.2:3b', 'Llama 3.2 3B', api_key_required=False, cost_per_1k_tokens=0.0, max_tokens=8192, context_window=8192),
                    ModelInfo('Ollama', 'llama3.2:8b', 'Llama 3.2 8B', api_key_required=False, cost_per_1k_tokens=0.0, max_tokens=8192, context_window=8192),
                    ModelInfo('Ollama', 'llama3.2:70b', 'Llama 3.2 70B', api_key_required=False, cost_per_1k_tokens=0.0, max_tokens=8192, context_window=8192),
                    ModelInfo('Ollama', 'codellama', 'Code Llama', api_key_required=False, cost_per_1k_tokens=0.0, max_tokens=8192, context_window=8192),
                    ModelInfo('Ollama', 'mistral', 'Mistral', api_key_required=False, cost_per_1k_tokens=0.0, max_tokens=8192, context_window=8192),
                    ModelInfo('Ollama', 'qwen2', 'Qwen2', api_key_required=False, cost_per_1k_tokens=0.0, max_tokens=8192, context_window=8192),
                ],
                'Deepseek': [
                    ModelInfo('Deepseek', 'deepseek-chat', 'Deepseek Chat', cost_per_1k_tokens=0.14, max_tokens=32768, supports_function_calling=True, context_window=32768),
                    ModelInfo('Deepseek', 'deepseek-coder', 'Deepseek Coder', cost_per_1k_tokens=0.14, max_tokens=32768, supports_function_calling=True, context_window=32768),
                ],
                'Mistral AI': [
                    ModelInfo('Mistral AI', 'mistral-large-latest', 'Mistral Large', cost_per_1k_tokens=6.0, max_tokens=32768, supports_function_calling=True, context_window=32768),
                    ModelInfo('Mistral AI', 'mistral-medium-latest', 'Mistral Medium', cost_per_1k_tokens=2.7, max_tokens=32768, supports_function_calling=True, context_window=32768),
                    ModelInfo('Mistral AI', 'mistral-small-latest', 'Mistral Small', cost_per_1k_tokens=0.14, max_tokens=32768, supports_function_calling=True, context_window=32768),
                ],
                'Groq': [
                    ModelInfo('Groq', 'llama3.2-70b-4096', 'Llama 3.2 70B (Groq)', cost_per_1k_tokens=0.05, max_tokens=4096, context_window=4096),
                    ModelInfo('Groq', 'llama3.2-8b-8192', 'Llama 3.2 8B (Groq)', cost_per_1k_tokens=0.05, max_tokens=8192, context_window=8192),
                    ModelInfo('Groq', 'mixtral-8x7b-32768', 'Mixtral 8x7B (Groq)', cost_per_1k_tokens=0.24, max_tokens=32768, context_window=32768),
                ],
                'OpenRouter': [
                    ModelInfo('OpenRouter', 'anthropic/claude-3-5-sonnet', 'Claude 3.5 Sonnet (OpenRouter)', cost_per_1k_tokens=3.0, max_tokens=200000, supports_vision=True, supports_function_calling=True, context_window=200000),
                    ModelInfo('OpenRouter', 'openai/gpt-4o', 'GPT-4o (OpenRouter)', cost_per_1k_tokens=5.0, max_tokens=128000, supports_vision=True, supports_function_calling=True, context_window=128000),
                    ModelInfo('OpenRouter', 'google/gemini-1.5-pro', 'Gemini 1.5 Pro (OpenRouter)', cost_per_1k_tokens=3.5, max_tokens=1000000, supports_vision=True, supports_function_calling=True, context_window=1000000),
                ]
            }
            
            # Add all models to the dictionary
            for provider, models in model_definitions.items():
                for model in models:
                    key = f"{provider}:{model.model_name}"
                    self.models[key] = model
            
            # Update model availability based on API keys
            self._update_model_availability()
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to initialize models: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to update model availability")
    def _update_model_availability(self):
        """Update model availability based on API keys and settings."""
        try:
            if not self.settings_manager:
                return
            
            # Get API keys from settings
            api_keys = self.settings_manager.get_api_keys()
            
            for model_key, model in self.models.items():
                provider = model.provider
                
                # Check if API key is required and available
                if model.api_key_required:
                    has_key = provider in api_keys and api_keys[provider].strip()
                    model.has_valid_key = bool(has_key)
                    model.is_available = model.has_valid_key
                else:
                    # Local models (like Ollama) don't require API keys
                    model.has_valid_key = True
                    model.is_available = True
                    
                    # For Ollama models, check if the model is actually available
                    if provider == 'Ollama' and self.api_manager:
                        # This would require checking with the Ollama server
                        # For now, we'll assume it's available
                        pass
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to update model availability: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to refresh models")
    def refresh_models(self):
        """Refresh the model list and update availability."""
        try:
            self._update_model_availability()
            self._update_completer()
            self.models_updated.emit(list(self.models.values()))
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to refresh models: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to start auto refresh")
    def _start_auto_refresh(self):
        """Start the auto-refresh timer."""
        try:
            self.refresh_timer.start(self.auto_refresh_interval)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to start auto refresh: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to stop auto refresh")
    def stop_auto_refresh(self):
        """Stop the auto-refresh timer."""
        try:
            self.refresh_timer.stop()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to stop auto refresh: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to get available models")
    def get_available_models(self, include_unavailable: bool = False) -> List[ModelInfo]:
        """Get list of available models."""
        try:
            models = list(self.models.values())
            if not include_unavailable:
                models = [m for m in models if m.is_available]
            return models
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to get available models: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.MODEL_MANAGEMENT
            )
            return []
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to get model by key")
    def get_model_by_key(self, model_key: str) -> Optional[ModelInfo]:
        """Get model information by key."""
        try:
            return self.models.get(model_key)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to get model by key {model_key}: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.MODEL_MANAGEMENT
            )
            return None
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to select model")
    def select_model(self, provider: str, model_name: str):
        """Select a model and emit the selection signal."""
        try:
            model_key = f"{provider}:{model_name}"
            model = self.get_model_by_key(model_key)
            
            if model and model.is_available:
                # Update usage tracking
                self._update_model_usage(model_key)
                
                # Emit signals
                self.model_selected.emit(provider, model_name)
                self.model_switched.emit(provider, model_name)
                
                self.error_handler.log_info(
                    f"Model selected: {provider}:{model_name}",
                    ErrorCategory.MODEL_MANAGEMENT
                )
            else:
                error_msg = f"Model not available: {provider}:{model_name}"
                self.error_occurred.emit(error_msg)
                self.error_handler.log_error(
                    error_msg,
                    ErrorSeverity.WARNING,
                    ErrorCategory.MODEL_MANAGEMENT
                )
                
        except Exception as e:
            error_msg = f"Failed to select model {provider}:{model_name}: {e}"
            self.error_occurred.emit(error_msg)
            self.error_handler.log_error(
                error_msg,
                ErrorSeverity.ERROR,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to update model usage")
    def _update_model_usage(self, model_key: str):
        """Update usage tracking for a model."""
        try:
            # Update usage count
            if model_key in self.models:
                self.models[model_key].usage_count += 1
            
            # Update recent models
            if model_key in self.recent_models:
                self.recent_models.remove(model_key)
            self.recent_models.insert(0, model_key)
            
            # Keep only the most recent models
            self.recent_models = self.recent_models[:self.max_recent_models]
            
            # Save configuration
            self._save_configuration()
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to update model usage for {model_key}: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to toggle favorite")
    def toggle_favorite(self, model_key: str):
        """Toggle a model's favorite status."""
        try:
            if model_key in self.favorite_models:
                self.favorite_models.remove(model_key)
            else:
                if len(self.favorite_models) < self.max_favorite_models:
                    self.favorite_models.append(model_key)
            
            self._save_configuration()
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to toggle favorite for {model_key}: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to get recent models")
    def get_recent_models(self) -> List[ModelInfo]:
        """Get list of recently used models."""
        try:
            recent_models = []
            for model_key in self.recent_models:
                model = self.get_model_by_key(model_key)
                if model:
                    recent_models.append(model)
            return recent_models
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to get recent models: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
            return []
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to get favorite models")
    def get_favorite_models(self) -> List[ModelInfo]:
        """Get list of favorite models."""
        try:
            favorite_models = []
            for model_key in self.favorite_models:
                model = self.get_model_by_key(model_key)
                if model:
                    favorite_models.append(model)
            return favorite_models
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to get favorite models: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
            return []
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to search models")
    def search_models(self, query: str) -> List[ModelInfo]:
        """Search models by name, provider, or capabilities."""
        try:
            if not query.strip():
                return self.get_available_models()
            
            query_lower = query.lower()
            results = []
            
            for model in self.get_available_models():
                # Search in display name, provider, and model name
                if (query_lower in model.display_name.lower() or
                    query_lower in model.provider.lower() or
                    query_lower in model.model_name.lower()):
                    results.append(model)
            
            return results
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to search models with query '{query}': {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
            return []
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to setup UI components")
    def setup_ui_components(self, search_input: QLineEdit, completer: QCompleter):
        """Setup UI components for the quick switch interface."""
        try:
            self.search_input = search_input
            self.completer = completer
            
            # Connect signals
            if self.search_input:
                self.search_input.textChanged.connect(self._on_search_text_changed)
                self.search_input.returnPressed.connect(self._on_search_return_pressed)
            
            # Setup completer
            self._update_completer()
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to setup UI components: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to update completer")
    def _update_completer(self):
        """Update the completer with current model list."""
        try:
            if not self.completer:
                return
            
            # Create model for completer
            model = QStandardItemModel()
            
            # Add recent models first
            recent_models = self.get_recent_models()
            if recent_models:
                recent_item = QStandardItem("--- Recent Models ---")
                recent_item.setEnabled(False)
                model.appendRow(recent_item)
                
                for model_info in recent_models:
                    item = QStandardItem(f"{model_info.display_name} ({model_info.provider})")
                    item.setData(f"{model_info.provider}:{model_info.model_name}")
                    model.appendRow(item)
            
            # Add favorite models
            favorite_models = self.get_favorite_models()
            if favorite_models:
                favorite_item = QStandardItem("--- Favorite Models ---")
                favorite_item.setEnabled(False)
                model.appendRow(favorite_item)
                
                for model_info in favorite_models:
                    item = QStandardItem(f"{model_info.display_name} ({model_info.provider})")
                    item.setData(f"{model_info.provider}:{model_info.model_name}")
                    model.appendRow(item)
            
            # Add all available models
            all_models_item = QStandardItem("--- All Models ---")
            all_models_item.setEnabled(False)
            model.appendRow(all_models_item)
            
            available_models = self.get_available_models()
            for model_info in available_models:
                item = QStandardItem(f"{model_info.display_name} ({model_info.provider})")
                item.setData(f"{model_info.provider}:{model_info.model_name}")
                model.appendRow(item)
            
            self.completer.setModel(model)
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to update completer: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to handle search text change")
    def _on_search_text_changed(self, text: str):
        """Handle search text changes."""
        try:
            if not text.strip():
                self._update_completer()
                return
            
            # Filter completer based on search text
            results = self.search_models(text)
            
            # Update completer with filtered results
            model = QStandardItemModel()
            for model_info in results:
                item = QStandardItem(f"{model_info.display_name} ({model_info.provider})")
                item.setData(f"{model_info.provider}:{model_info.model_name}")
                model.appendRow(item)
            
            if self.completer:
                self.completer.setModel(model)
                
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle search text change: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to handle search return pressed")
    def _on_search_return_pressed(self):
        """Handle return key press in search input."""
        try:
            if not self.search_input:
                return
            
            text = self.search_input.text().strip()
            if not text:
                return
            
            # Try to find exact match first
            results = self.search_models(text)
            if results:
                # Select the first result
                model_info = results[0]
                self.select_model(model_info.provider, model_info.model_name)
                
                # Clear search input
                self.search_input.clear()
                
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle search return pressed: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    @error_handler(ErrorCategory.MODEL_MANAGEMENT, "Failed to handle completer activation")
    def on_completer_activated(self, text: str):
        """Handle completer item selection."""
        try:
            # Extract model key from completer item
            if self.completer:
                index = self.completer.completionModel().index(0, 0)
                model_key = self.completer.completionModel().data(index, Qt.UserRole)
                
                if model_key:
                    provider, model_name = model_key.split(':', 1)
                    self.select_model(provider, model_name)
                    
                    # Clear search input
                    if self.search_input:
                        self.search_input.clear()
                        
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle completer activation: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            )
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            self.stop_auto_refresh()
            self._save_configuration()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to cleanup quick switch menu: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.MODEL_MANAGEMENT
            ) 
