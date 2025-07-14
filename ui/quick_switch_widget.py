"""
Quick Switch Model Menu Widget - GUI components for rapid model switching.

This module provides the GUI components for the quick switch model menu,
including a searchable dropdown, model list, and selection interface.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QCompleter,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QFrame,
    QScrollArea, QSizePolicy, QSpacerItem, QMenu,
    QToolButton, QSplitter, QTextEdit, QCheckBox
)
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QColor, QPalette,
    QStandardItemModel, QStandardItem, QKeySequence, QAction
)

from core.quick_switch import QuickSwitchModelMenu, ModelInfo
from utils.error_handler import (
    ErrorHandler, ErrorSeverity, ErrorCategory,
    error_handler, safe_execute
)


@dataclass
class ModelDisplayInfo:
    """Display information for a model in the UI."""
    model_info: ModelInfo
    is_favorite: bool = False
    is_recent: bool = False
    usage_count: int = 0


class ModelListItem(QWidget):
    """Custom list item widget for displaying model information."""
    
    model_selected = pyqtSignal(str, str)  # provider, model_name
    favorite_toggled = pyqtSignal(str)  # model_key
    
    def __init__(self, model_info: ModelInfo, is_favorite: bool = False, is_recent: bool = False):
        super().__init__()
        
        # Initialize error handler
        self.error_handler = ErrorHandler()
        
        self.model_info = model_info
        self.model_key = f"{model_info.provider}:{model_info.model_name}"
        self.is_favorite = is_favorite
        
        self._setup_ui()
        self._apply_styling()
    
    @error_handler(ErrorCategory.UI, "Failed to setup model list item UI")
    def _setup_ui(self):
        """Setup the UI components for the model list item."""
        try:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(8, 6, 8, 6)
            layout.setSpacing(8)
            
            # Favorite button
            self.favorite_btn = QToolButton()
            self.favorite_btn.setIcon(self._get_favorite_icon())
            self.favorite_btn.setToolTip("Toggle favorite")
            self.favorite_btn.clicked.connect(self._toggle_favorite)
            self.favorite_btn.setFixedSize(20, 20)
            layout.addWidget(self.favorite_btn)
            
            # Model info container
            info_container = QWidget()
            info_layout = QVBoxLayout(info_container)
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(2)
            
            # Model name and provider
            name_layout = QHBoxLayout()
            name_layout.setSpacing(8)
            
            self.name_label = QLabel(self.model_info.display_name)
            self.name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            name_layout.addWidget(self.name_label)
            
            self.provider_label = QLabel(f"({self.model_info.provider})")
            self.provider_label.setFont(QFont("Segoe UI", 8))
            self.provider_label.setStyleSheet("color: #666;")
            name_layout.addWidget(self.provider_label)
            
            # Add spacer to push provider to the right
            name_layout.addStretch()
            
            # Usage indicator for recent models
            if self.model_info.usage_count > 0:
                usage_label = QLabel(f"Used {self.model_info.usage_count} times")
                usage_label.setFont(QFont("Segoe UI", 7))
                usage_label.setStyleSheet("color: #888;")
                name_layout.addWidget(usage_label)
            
            info_layout.addLayout(name_layout)
            
            # Model details
            details_layout = QHBoxLayout()
            details_layout.setSpacing(12)
            
            # Cost information
            if self.model_info.cost_per_1k_tokens is not None:
                cost_text = f"${self.model_info.cost_per_1k_tokens}/1K tokens"
                cost_label = QLabel(cost_text)
                cost_label.setFont(QFont("Segoe UI", 7))
                cost_label.setStyleSheet("color: #666; background: #f0f0f0; padding: 2px 4px; border-radius: 2px;")
                details_layout.addWidget(cost_label)
            
            # Context window
            if self.model_info.context_window:
                context_text = f"{self.model_info.context_window:,} tokens"
                context_label = QLabel(context_text)
                context_label.setFont(QFont("Segoe UI", 7))
                context_label.setStyleSheet("color: #666; background: #f0f0f0; padding: 2px 4px; border-radius: 2px;")
                details_layout.addWidget(context_label)
            
            # Capabilities icons
            capabilities_layout = QHBoxLayout()
            capabilities_layout.setSpacing(4)
            
            if self.model_info.supports_vision:
                vision_icon = QLabel("👁")
                vision_icon.setToolTip("Supports vision")
                vision_icon.setStyleSheet("font-size: 10px;")
                capabilities_layout.addWidget(vision_icon)
            
            if self.model_info.supports_audio:
                audio_icon = QLabel("🎵")
                audio_icon.setToolTip("Supports audio")
                audio_icon.setStyleSheet("font-size: 10px;")
                capabilities_layout.addWidget(audio_icon)
            
            if self.model_info.supports_function_calling:
                func_icon = QLabel("⚙")
                func_icon.setToolTip("Supports function calling")
                func_icon.setStyleSheet("font-size: 10px;")
                capabilities_layout.addWidget(func_icon)
            
            if self.model_info.api_key_required and not self.model_info.has_valid_key:
                key_icon = QLabel("🔑")
                key_icon.setToolTip("API key required")
                key_icon.setStyleSheet("font-size: 10px; color: #ff6b6b;")
                capabilities_layout.addWidget(key_icon)
            
            capabilities_layout.addStretch()
            details_layout.addLayout(capabilities_layout)
            
            info_layout.addLayout(details_layout)
            layout.addWidget(info_container)
            
            # Select button
            self.select_btn = QPushButton("Select")
            self.select_btn.setFixedSize(60, 24)
            self.select_btn.clicked.connect(self._select_model)
            layout.addWidget(self.select_btn)
            
            # Set up mouse events for selection
            self.setMouseTracking(True)
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to setup model list item UI: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to apply styling to model list item")
    def _apply_styling(self):
        """Apply styling to the model list item."""
        try:
            # Set background and border
            self.setStyleSheet("""
                ModelListItem {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    margin: 2px 0px;
                }
                ModelListItem:hover {
                    background-color: #f8f9fa;
                    border-color: #007acc;
                }
                ModelListItem:selected {
                    background-color: #e3f2fd;
                    border-color: #2196f3;
                }
            """)
            
            # Update favorite button styling
            self._update_favorite_button()
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to apply styling to model list item: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to get favorite icon")
    def _get_favorite_icon(self) -> QIcon:
        """Get the appropriate favorite icon."""
        try:
            if self.is_favorite:
                return QIcon("icons/star_filled.png")  # You'll need to add this icon
            else:
                return QIcon("icons/star_empty.png")   # You'll need to add this icon
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to get favorite icon: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
            # Fallback to text
            return QIcon()
    
    @error_handler(ErrorCategory.UI, "Failed to update favorite button")
    def _update_favorite_button(self):
        """Update the favorite button appearance."""
        try:
            self.favorite_btn.setIcon(self._get_favorite_icon())
            if self.is_favorite:
                self.favorite_btn.setStyleSheet("color: #ffd700;")
            else:
                self.favorite_btn.setStyleSheet("color: #ccc;")
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to update favorite button: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to toggle favorite")
    def _toggle_favorite(self):
        """Toggle the favorite status of this model."""
        try:
            self.is_favorite = not self.is_favorite
            self._update_favorite_button()
            self.favorite_toggled.emit(self.model_key)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to toggle favorite: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to select model")
    def _select_model(self):
        """Select this model."""
        try:
            self.model_selected.emit(self.model_info.provider, self.model_info.model_name)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to select model: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self._select_model()
            super().mousePressEvent(event)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle mouse press event: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )


class QuickSwitchWidget(QWidget):
    """
    Main widget for the quick switch model menu.
    
    Provides a searchable interface with recent models, favorites,
    and all available models in a user-friendly layout.
    """
    
    # Signals
    model_selected = pyqtSignal(str, str)  # provider, model_name
    widget_closed = pyqtSignal()
    
    def __init__(self, quick_switch_menu: QuickSwitchModelMenu, parent=None):
        super().__init__(parent)
        
        # Initialize error handler
        self.error_handler = ErrorHandler()
        
        # Core components
        self.quick_switch_menu = quick_switch_menu
        
        # UI components
        self.search_input: Optional[QLineEdit] = None
        self.model_list: Optional[QListWidget] = None
        self.recent_section: Optional[QWidget] = None
        self.favorites_section: Optional[QWidget] = None
        self.all_models_section: Optional[QWidget] = None
        
        # State
        self.current_filter = ""
        self.show_unavailable = False
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        self._refresh_model_list()
    
    @error_handler(ErrorCategory.UI, "Failed to setup quick switch widget UI")
    def _setup_ui(self):
        """Setup the main UI components."""
        try:
            # Main layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)
            
            # Header
            header_layout = QHBoxLayout()
            
            title_label = QLabel("Quick Switch Model")
            title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            header_layout.addWidget(title_label)
            
            header_layout.addStretch()
            
            # Close button
            close_btn = QPushButton("×")
            close_btn.setFixedSize(24, 24)
            close_btn.setStyleSheet("""
                QPushButton {
                    background: #ff6b6b;
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #ff5252;
                }
            """)
            close_btn.clicked.connect(self._close_widget)
            header_layout.addWidget(close_btn)
            
            layout.addLayout(header_layout)
            
            # Search section
            search_layout = QHBoxLayout()
            
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search models...")
            self.search_input.setFont(QFont("Segoe UI", 10))
            self.search_input.setStyleSheet("""
                QLineEdit {
                    padding: 8px 12px;
                    border: 2px solid #e0e0e0;
                    border-radius: 6px;
                    background: white;
                }
                QLineEdit:focus {
                    border-color: #007acc;
                }
            """)
            search_layout.addWidget(self.search_input)
            
            # Show unavailable checkbox
            self.show_unavailable_cb = QCheckBox("Show unavailable")
            self.show_unavailable_cb.setFont(QFont("Segoe UI", 9))
            self.show_unavailable_cb.toggled.connect(self._on_show_unavailable_toggled)
            search_layout.addWidget(self.show_unavailable_cb)
            
            layout.addLayout(search_layout)
            
            # Model list
            self.model_list = QListWidget()
            self.model_list.setStyleSheet("""
                QListWidget {
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    background: white;
                    padding: 4px;
                }
                QListWidget::item {
                    padding: 0px;
                    margin: 2px 0px;
                }
                QListWidget::item:selected {
                    background: transparent;
                }
            """)
            layout.addWidget(self.model_list)
            
            # Status bar
            self.status_label = QLabel("Ready")
            self.status_label.setFont(QFont("Segoe UI", 8))
            self.status_label.setStyleSheet("color: #666;")
            layout.addWidget(self.status_label)
            
            # Apply main widget styling
            self.setStyleSheet("""
                QuickSwitchWidget {
                    background: #f8f9fa;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
            """)
            
            # Set size policy
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.setMinimumSize(500, 400)
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to setup quick switch widget UI: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to connect signals")
    def _connect_signals(self):
        """Connect all signals and slots."""
        try:
            # Search input
            if self.search_input:
                self.search_input.textChanged.connect(self._on_search_text_changed)
                self.search_input.returnPressed.connect(self._on_search_return_pressed)
            
            # Quick switch menu signals
            self.quick_switch_menu.model_selected.connect(self._on_model_selected)
            self.quick_switch_menu.error_occurred.connect(self._on_error_occurred)
            self.quick_switch_menu.models_updated.connect(self._on_models_updated)
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to connect signals: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to refresh model list")
    def _refresh_model_list(self):
        """Refresh the model list display."""
        try:
            if not self.model_list:
                return
            
            # Clear current list
            self.model_list.clear()
            
            # Get models based on current filter and settings
            if self.current_filter:
                models = self.quick_switch_menu.search_models(self.current_filter)
            else:
                models = self.quick_switch_menu.get_available_models(include_unavailable=self.show_unavailable)
            
            # Get recent and favorite models
            recent_models = self.quick_switch_menu.get_recent_models()
            favorite_models = self.quick_switch_menu.get_favorite_models()
            
            recent_keys = {f"{m.provider}:{m.model_name}" for m in recent_models}
            favorite_keys = {f"{m.provider}:{m.model_name}" for m in favorite_models}
            
            # Add section headers and models
            if not self.current_filter:
                # Add recent models section
                if recent_models:
                    self._add_section_header("Recent Models")
                    for model in recent_models:
                        self._add_model_item(model, is_recent=True, is_favorite=f"{model.provider}:{model.model_name}" in favorite_keys)
                
                # Add favorite models section
                if favorite_models:
                    self._add_section_header("Favorite Models")
                    for model in favorite_models:
                        if f"{model.provider}:{model.model_name}" not in recent_keys:  # Don't duplicate
                            self._add_model_item(model, is_favorite=True)
                
                # Add all models section
                if models:
                    self._add_section_header("All Available Models")
                    for model in models:
                        model_key = f"{model.provider}:{model.model_name}"
                        if model_key not in recent_keys and model_key not in favorite_keys:
                            self._add_model_item(model)
            else:
                # Filtered view - just show matching models
                for model in models:
                    model_key = f"{model.provider}:{model.model_name}"
                    is_recent = model_key in recent_keys
                    is_favorite = model_key in favorite_keys
                    self._add_model_item(model, is_recent=is_recent, is_favorite=is_favorite)
            
            # Update status
            self._update_status(f"Showing {len(models)} models")
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to refresh model list: {e}",
                ErrorSeverity.ERROR,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to add section header")
    def _add_section_header(self, title: str):
        """Add a section header to the model list."""
        try:
            header_widget = QWidget()
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(8, 8, 8, 4)
            
            header_label = QLabel(title)
            header_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            header_label.setStyleSheet("color: #007acc; background: #e3f2fd; padding: 4px 8px; border-radius: 4px;")
            header_layout.addWidget(header_label)
            header_layout.addStretch()
            
            header_item = QListWidgetItem(self.model_list)
            header_item.setSizeHint(header_widget.sizeHint())
            self.model_list.setItemWidget(header_item, header_widget)
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to add section header '{title}': {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to add model item")
    def _add_model_item(self, model: ModelInfo, is_recent: bool = False, is_favorite: bool = False):
        """Add a model item to the list."""
        try:
            # Create custom widget
            item_widget = ModelListItem(model, is_favorite=is_favorite, is_recent=is_recent)
            
            # Connect signals
            item_widget.model_selected.connect(self._on_model_item_selected)
            item_widget.favorite_toggled.connect(self._on_favorite_toggled)
            
            # Add to list
            list_item = QListWidgetItem(self.model_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.model_list.setItemWidget(list_item, item_widget)
            
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to add model item for {model.display_name}: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle search text change")
    def _on_search_text_changed(self, text: str):
        """Handle search text changes."""
        try:
            self.current_filter = text
            self._refresh_model_list()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle search text change: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle search return pressed")
    def _on_search_return_pressed(self):
        """Handle return key press in search input."""
        try:
            if not self.search_input:
                return
            
            text = self.search_input.text().strip()
            if not text:
                return
            
            # Try to select the first available model
            results = self.quick_switch_menu.search_models(text)
            if results:
                model = results[0]
                self._select_model(model.provider, model.model_name)
                
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle search return pressed: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle show unavailable toggle")
    def _on_show_unavailable_toggled(self, checked: bool):
        """Handle show unavailable checkbox toggle."""
        try:
            self.show_unavailable = checked
            self._refresh_model_list()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle show unavailable toggle: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle model item selection")
    def _on_model_item_selected(self, provider: str, model_name: str):
        """Handle model item selection."""
        try:
            self._select_model(provider, model_name)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle model item selection: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle favorite toggle")
    def _on_favorite_toggled(self, model_key: str):
        """Handle favorite toggle from model item."""
        try:
            self.quick_switch_menu.toggle_favorite(model_key)
            # Refresh the list to update favorite status
            self._refresh_model_list()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle favorite toggle: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle model selection")
    def _on_model_selected(self, provider: str, model_name: str):
        """Handle model selection from quick switch menu."""
        try:
            self.model_selected.emit(provider, model_name)
            self._update_status(f"Selected: {provider} - {model_name}")
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle model selection: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle error occurrence")
    def _on_error_occurred(self, error_message: str):
        """Handle error from quick switch menu."""
        try:
            self._update_status(f"Error: {error_message}")
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle error occurrence: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to handle models updated")
    def _on_models_updated(self, models: List[ModelInfo]):
        """Handle models updated signal."""
        try:
            self._refresh_model_list()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle models updated: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to select model")
    def _select_model(self, provider: str, model_name: str):
        """Select a model and close the widget."""
        try:
            self.quick_switch_menu.select_model(provider, model_name)
            self._close_widget()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to select model: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to update status")
    def _update_status(self, message: str):
        """Update the status label."""
        try:
            if self.status_label:
                self.status_label.setText(message)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to update status: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    @error_handler(ErrorCategory.UI, "Failed to close widget")
    def _close_widget(self):
        """Close the widget."""
        try:
            self.widget_closed.emit()
            self.hide()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to close widget: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        try:
            if event.key() == Qt.Key.Key_Escape:
                self._close_widget()
            else:
                super().keyPressEvent(event)
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle key press event: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    def showEvent(self, event):
        """Handle show event."""
        try:
            super().showEvent(event)
            if self.search_input:
                self.search_input.setFocus()
                self.search_input.selectAll()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to handle show event: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            )
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.quick_switch_menu:
                self.quick_switch_menu.cleanup()
        except Exception as e:
            self.error_handler.log_error(
                f"Failed to cleanup quick switch widget: {e}",
                ErrorSeverity.WARNING,
                ErrorCategory.UI
            ) 
