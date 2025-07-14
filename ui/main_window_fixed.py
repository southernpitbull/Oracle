#!/usr/bin/env python3
"""
Main Window for The Oracle AI Chat Application
File: ui/main_window_fixed.py

This module provides the main application window with comprehensive error handling,
sliding panels, chat interface, and all UI components.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QPushButton, QTextEdit, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QScrollArea, QGroupBox, QGridLayout,
    QFileDialog, QMessageBox, QStatusBar, QMenuBar,
    QProgressBar, QTabWidget, QCheckBox, QSpinBox, QDialog
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QColor, QPixmap, QAction, QShortcut

# Import comprehensive error handling
from utils.error_handler import (
    error_handler, error_context, safe_execute, log_function_call,
    ErrorSeverity, ErrorCategory, RetryConfig, handle_error, 
    create_error_context, validate_input
)

# Import other components
from utils.markdown_formatter import markdown_formatter
from utils.avatar_manager import avatar_manager

# Use the logger from dependencies
from utils.dependencies import log as logger


class SlidingPanel(QFrame):
    """Sliding panel with expand/collapse functionality."""
    
    def __init__(self, parent=None, side='left', width=300):
        super().__init__(parent)
        self.side = side
        self.full_width = width
        self.collapsed_width = 50
        self.is_open = True
        self.button_width = 40
        self.button_height = 30
        
        # Set up the panel
        self.setFixedWidth(self.full_width)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2b2b2b, stop:1 #3a3a3a);
                border: 1px solid #555555;
                border-radius: 8px;
            }
        """)
        
        # Create toggle button
        self.toggle_btn = QPushButton("◀" if side == 'left' else "▶")
        self.toggle_btn.setFixedSize(self.button_width, self.button_height)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #106ebe;
            }
            QPushButton:pressed {
                background: #005a9e;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_panel)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Add toggle button at the bottom
        button_layout = QHBoxLayout()
        if side == 'left':
            button_layout.addStretch()
            button_layout.addWidget(self.toggle_btn)
        else:
            button_layout.addWidget(self.toggle_btn)
            button_layout.addStretch()
        
        self.main_layout.addLayout(button_layout)
        
        # Update button position
        self.update_button_position()
        
    def update_button_position(self):
        """Update button position based on panel state."""
        if self.is_open:
            self.toggle_btn.setText("◀" if self.side == 'left' else "▶")
        else:
            self.toggle_btn.setText("▶" if self.side == 'left' else "◀")
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.update_button_position()
    
    def enterEvent(self, event):
        """Handle mouse enter events."""
        super().enterEvent(event)
        if not self.is_open:
            # Show a hint that the panel can be expanded
            self.setToolTip("Click to expand panel")
    
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        super().leaveEvent(event)
        self.setToolTip("")
    
    def toggle_panel(self):
        """Toggle panel open/closed state."""
        if self.is_open:
            self.collapse_panel()
        else:
            self.expand_panel()
    
    def collapse_panel(self):
        """Collapse the panel."""
        if not self.is_open:
            return
        
        self.is_open = False
        
        # Animate to collapsed width
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        start_rect = self.geometry()
        end_rect = QRect(start_rect.x(), start_rect.y(), self.collapsed_width, start_rect.height())
        
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        
        self.update_button_position()
    
    def expand_panel(self):
        """Expand the panel."""
        if self.is_open:
            return
        
        self.is_open = True
        
        # Animate to full width
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        start_rect = self.geometry()
        end_rect = QRect(start_rect.x(), start_rect.y(), self.full_width, start_rect.height())
        
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        
        self.update_button_position()


class ConversationList(QWidget):
    """Left panel for conversation history and management."""
    
    conversation_selected = pyqtSignal(str)  # conversation_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the conversation list UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("💬 Conversations")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; padding: 5px;")
        header_layout.addWidget(title)
        
        # New conversation button
        new_btn = QPushButton("🆕")
        new_btn.setFixedSize(30, 30)
        new_btn.setToolTip("New Conversation")
        new_btn.setStyleSheet("""
            QPushButton {
                background: #00b894;
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #00a085;
            }
        """)
        new_btn.clicked.connect(self.new_conversation)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search conversations...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 15px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.search_box.textChanged.connect(self.filter_conversations)
        layout.addWidget(self.search_box)
        
        # Conversation list
        self.conversation_list = QListWidget()
        self.conversation_list.setStyleSheet("""
            QListWidget {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
                color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background: #3a3a3a;
            }
        """)
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        layout.addWidget(self.conversation_list)
        
        # Load sample conversations
        self.load_conversations()
        
    def load_conversations(self):
        """Load conversation list."""
        # Sample conversations for demonstration
        conversations = [
            {"id": "conv1", "title": "Python Code Review", "timestamp": "2024-01-15 14:30", "tags": ["python", "code"]},
            {"id": "conv2", "title": "AI Model Discussion", "timestamp": "2024-01-14 16:45", "tags": ["ai", "models"]},
            {"id": "conv3", "title": "Web Development Help", "timestamp": "2024-01-13 09:20", "tags": ["web", "development"]},
        ]
        
        for conv in conversations:
            item = QListWidgetItem(f"📝 {conv['title']}\n⏰ {conv['timestamp']}")
            item.setData(Qt.ItemDataRole.UserRole, conv['id'])
            self.conversation_list.addItem(item)
    
    def filter_conversations(self, text: str):
        """Filter conversations based on search text."""
        # TODO: Implement conversation filtering
        pass
    
    def on_conversation_selected(self, item: QListWidgetItem):
        """Handle conversation selection."""
        conv_id = item.data(Qt.ItemDataRole.UserRole)
        self.conversation_selected.emit(conv_id)
    
    def new_conversation(self):
        """Create a new conversation."""
        # TODO: Implement new conversation creation
        pass


class ModelSettings(QWidget):
    """Right panel for model settings and system instructions."""
    
    settings_changed = pyqtSignal(dict)  # settings_dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the model settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("⚙️ Model Settings")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; padding: 5px;")
        layout.addWidget(title)
        
        # Model selection
        model_group = QGroupBox("🧠 Model Configuration")
        model_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        model_layout = QVBoxLayout(model_group)
        
        # Model selector
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        model_layout.addWidget(model_label)
        
        self.model_selector = QComboBox()
        self.model_selector.addItems(["GPT-4", "GPT-3.5-turbo", "Claude-3", "Gemini-Pro"])
        self.model_selector.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 11px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
        """)
        model_layout.addWidget(self.model_selector)
        
        layout.addWidget(model_group)
        
        # Parameters
        params_group = QGroupBox("🎯 Parameters")
        params_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        params_layout = QGridLayout(params_group)
        params_layout.setSpacing(10)
        
        # Temperature
        temp_label = QLabel("Temperature:")
        temp_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        params_layout.addWidget(temp_label, 0, 0)
        
        self.temperature_slider = QSpinBox()
        self.temperature_slider.setRange(0, 20)
        self.temperature_slider.setValue(7)
        self.temperature_slider.setSuffix(" (0.7)")
        self.temperature_slider.setStyleSheet("""
            QSpinBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: white;
                font-size: 11px;
            }
        """)
        params_layout.addWidget(self.temperature_slider, 0, 1)
        
        # Max tokens
        tokens_label = QLabel("Max Tokens:")
        tokens_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        params_layout.addWidget(tokens_label, 1, 0)
        
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 8000)
        self.max_tokens.setValue(2000)
        self.max_tokens.setStyleSheet("""
            QSpinBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: white;
                font-size: 11px;
            }
        """)
        params_layout.addWidget(self.max_tokens, 1, 1)
        
        layout.addWidget(params_group)
        
        # System instructions
        system_group = QGroupBox("📝 System Instructions")
        system_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        system_layout = QVBoxLayout(system_group)
        
        self.system_instructions = QTextEdit()
        self.system_instructions.setPlaceholderText("Enter system instructions for the AI...")
        self.system_instructions.setMaximumHeight(150)
        self.system_instructions.setStyleSheet("""
            QTextEdit {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 11px;
            }
            QTextEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        system_layout.addWidget(self.system_instructions)
        
        layout.addWidget(system_group)
        
        # Apply button
        apply_btn = QPushButton("✅ Apply Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background: #00b894;
                border: 1px solid #00b894;
                border-radius: 6px;
                padding: 10px;
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #00a085;
                border: 1px solid #00a085;
            }
        """)
        apply_btn.clicked.connect(self.apply_settings)
        layout.addWidget(apply_btn)
        
        layout.addStretch()

    def apply_settings(self):
        """Gather current settings from UI controls, emit signal, and show confirmation."""
        settings = {
            'model': self.model_selector.currentText(),
            'temperature': self.temperature_slider.value() / 10.0,  # Assuming slider is 0-20 for 0.0-2.0
            'max_tokens': self.max_tokens.value(),
            'system_instructions': self.system_instructions.toPlainText(),
        }
        self.settings_changed.emit(settings)
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Settings Applied", "Model settings have been applied successfully.")


class ChatWidget(QWidget):
    """Center chat area with message history and input."""
    
    message_sent = pyqtSignal(str)  # message_text
    file_attached = pyqtSignal(str)  # file_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the chat widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with model selector
        header_layout = QHBoxLayout()
        
        title = QLabel("💬 Chat")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; padding: 5px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Model selector
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #ffffff; font-size: 11px;")
        header_layout.addWidget(model_label)
        
        self.model_selector = QComboBox()
        self.model_selector.addItems(["GPT-4", "GPT-3.5-turbo", "Claude-3", "Gemini-Pro"])
        self.model_selector.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 10px;
                color: white;
                font-size: 11px;
                min-width: 120px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
        """)
        header_layout.addWidget(self.model_selector)
        
        layout.addLayout(header_layout)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
                color: white;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.chat_history)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # File attachment button
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setToolTip("Attach File")
        attach_btn.setStyleSheet("""
            QPushButton {
                background: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 20px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #5a5a5a;
                border: 1px solid #0078d4;
            }
        """)
        attach_btn.clicked.connect(self.attach_file)
        input_layout.addWidget(attach_btn)
        
        # Message input
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("Type your message here... (Ctrl+Enter to send)")
        self.message_input.setStyleSheet("""
            QTextEdit {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 10px;
                color: white;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.message_input.textChanged.connect(self.on_text_changed)
        input_layout.addWidget(self.message_input)
        
        # Send button
        send_btn = QPushButton("🚀")
        send_btn.setFixedSize(40, 40)
        send_btn.setToolTip("Send Message (Ctrl+Enter)")
        send_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 20px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #106ebe;
                border: 1px solid #106ebe;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Set up keyboard shortcuts
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.send_message)
        
    def on_text_changed(self):
        """Handle text input changes."""
        # TODO: Implement auto-save or other text change handling
        pass
    
    def send_message(self):
        """Send the current message."""
        message = self.message_input.toPlainText().strip()
        if message:
            self.message_sent.emit(message)
            self.message_input.clear()
    
    def add_message(self, sender: str, message: str, message_type: str = "user", model_name: str = None):
        """Add a message to the chat history."""
        timestamp = self._get_current_time()
        
        # Format the message based on type
        if message_type == "user":
            formatted_message = f"""
<div style="margin: 10px 0; padding: 10px; background: #3a3a3a; border-radius: 8px; border-left: 4px solid #0078d4;">
    <div style="font-weight: bold; color: #0078d4; margin-bottom: 5px;">👤 {sender}</div>
    <div style="color: white; line-height: 1.4;">{message}</div>
    <div style="font-size: 10px; color: #888; margin-top: 5px;">{timestamp}</div>
</div>
"""
        elif message_type == "assistant":
            model_info = f" ({model_name})" if model_name else ""
            formatted_message = f"""
<div style="margin: 10px 0; padding: 10px; background: #2b2b2b; border-radius: 8px; border-left: 4px solid #00b894;">
    <div style="font-weight: bold; color: #00b894; margin-bottom: 5px;">🤖 Assistant{model_info}</div>
    <div style="color: white; line-height: 1.4;">{message}</div>
    <div style="font-size: 10px; color: #888; margin-top: 5px;">{timestamp}</div>
</div>
"""
        else:
            formatted_message = f"""
<div style="margin: 10px 0; padding: 10px; background: #2b2b2b; border-radius: 8px; border-left: 4px solid #f39c12;">
    <div style="font-weight: bold; color: #f39c12; margin-bottom: 5px;">ℹ️ {sender}</div>
    <div style="color: white; line-height: 1.4;">{message}</div>
    <div style="font-size: 10px; color: #888; margin-top: 5px;">{timestamp}</div>
</div>
"""
        
        # Add to chat history
        current_html = self.chat_history.toHtml()
        self.chat_history.setHtml(current_html + formatted_message)
        
        # Scroll to bottom
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _get_current_time(self) -> str:
        """Get current time formatted for display."""
        return datetime.now().strftime("%H:%M:%S")
    
    def attach_file(self):
        """Attach a file to the conversation."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", "", "All Files (*)"
        )
        if file_path:
            self.file_attached.emit(file_path)


class MainWindow(QMainWindow):
    """Main application window with sliding panels and chat interface."""
    
    @error_handler(severity=ErrorSeverity.CRITICAL, category=ErrorCategory.UI)
    def __init__(self):
        """Initialize MainWindow with comprehensive error handling."""
        try:
            super().__init__()
            self.setWindowTitle("The Oracle - AI Chat Application")
            self.setMinimumSize(1200, 700)
            self.resize(1600, 1000)
            
            # Initialize components with error handling
            safe_execute(self.setup_ui)
            safe_execute(self.setup_menu)
            safe_execute(self.setup_status_bar)
            safe_execute(self.setup_connections)
            
            # Load initial data with retry mechanism
            retry_config = RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                exponential_backoff=True,
                retry_on_exceptions=[ImportError, RuntimeError]
            )
            
            with error_context("load_models", ErrorSeverity.ERROR):
                self.load_models()
            
            # Load conversation tags with error handling
            with error_context("load_conversation_tags", ErrorSeverity.WARNING):
                self.load_conversation_tags()
            
            logger.info("Main window initialized with P1 features")
            
        except Exception as exc:
            logger.critical("Failed to initialize MainWindow: {}".format(exc))
            handle_error(exc, create_error_context("MainWindow.__init__"))
            raise

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_ui(self):
        """Set up the main user interface with comprehensive error handling."""
        try:
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Main content area with splitter for better proportions
            self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.content_splitter.setChildrenCollapsible(False)
            self.content_splitter.setStyleSheet("""
                QSplitter::handle {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #555555, stop:1 #666666);
                    width: 3px;
                    border-radius: 1px;
                }
                QSplitter::handle:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #0078d4, stop:1 #0098f4);
                    width: 4px;
                }
            """)
            
            # Left sliding panel (conversations) - 20% of width
            with error_context("create_left_panel", ErrorSeverity.ERROR):
                self.left_panel = SlidingPanel(side='left', width=320)
                self.conversation_list = ConversationList()
                left_layout = QVBoxLayout(self.left_panel)
                left_layout.setContentsMargins(15, 15, 10, 40)
                left_layout.addWidget(self.conversation_list)
                self.content_splitter.addWidget(self.left_panel)
            
            # Center chat area - takes most space (60% of width)
            with error_context("create_chat_widget", ErrorSeverity.ERROR):
                self.chat_widget = ChatWidget()
                self.content_splitter.addWidget(self.chat_widget)
            
            # Right sliding panel (settings) - 20% of width
            with error_context("create_right_panel", ErrorSeverity.ERROR):
                self.right_panel = SlidingPanel(side='right', width=320)
                self.model_settings = ModelSettings()
                right_layout = QVBoxLayout(self.right_panel)
                right_layout.setContentsMargins(10, 15, 15, 40)
                right_layout.addWidget(self.model_settings)
                self.content_splitter.addWidget(self.right_panel)
            
            # Set splitter proportions: 20% left, 60% center, 20% right
            left_width = int(1600 * 0.20)
            center_width = int(1600 * 0.60)
            right_width = int(1600 * 0.20)
            self.content_splitter.setSizes([left_width, center_width, right_width])
            
            main_layout.addWidget(self.content_splitter)
            
            # Connect resize event to maintain proportions
            self.resizeEvent = self.on_resize_event
            
            logger.info("UI setup completed successfully")
            
        except Exception as exc:
            logger.error("Failed to setup UI: {}".format(exc))
            handle_error(exc, create_error_context("setup_ui"))
            raise

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_menu(self):
        """Set up the menu bar with error handling."""
        try:
            menubar = self.menuBar()
            menubar.setStyleSheet("""
                QMenuBar {
                    background: #2b2b2b;
                    color: white;
                    border-bottom: 1px solid #555555;
                }
                QMenuBar::item {
                    background: transparent;
                    padding: 8px 12px;
                }
                QMenuBar::item:selected {
                    background: #3a3a3a;
                }
                QMenu {
                    background: #2b2b2b;
                    border: 1px solid #555555;
                    color: white;
                }
                QMenu::item {
                    padding: 8px 20px;
                }
                QMenu::item:selected {
                    background: #0078d4;
                }
            """)
            
            # File menu
            file_menu = menubar.addMenu("📁 File")
            
            new_action = QAction("🆕 New Conversation", self)
            new_action.setShortcut(QKeySequence.StandardKey.New)
            new_action.triggered.connect(self.new_conversation)
            file_menu.addAction(new_action)
            
            exit_action = QAction("🚪 Exit", self)
            exit_action.setShortcut(QKeySequence.StandardKey.Quit)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            logger.info("Menu setup completed successfully")
            
        except Exception as exc:
            logger.error("Failed to setup menu: {}".format(exc))
            handle_error(exc, create_error_context("setup_menu"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_status_bar(self):
        """Set up the status bar with error handling."""
        try:
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            self.status_bar.setStyleSheet("""
                QStatusBar {
                    background: #2b2b2b;
                    color: white;
                    border-top: 1px solid #555555;
                }
            """)
            
            # Create status label
            self.status_label = QLabel("Ready")
            self.status_label.setStyleSheet("color: #00b894; font-weight: bold; font-size: 12px;")
            self.status_bar.addWidget(self.status_label)
            
            self.status_bar.showMessage("Ready")
            
            logger.info("Status bar setup completed successfully")
            
        except Exception as exc:
            logger.error("Failed to setup status bar: {}".format(exc))
            handle_error(exc, create_error_context("setup_status_bar"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_connections(self):
        """Set up signal connections with error handling."""
        try:
            # Chat connections
            self.chat_widget.message_sent.connect(self.handle_message)
            self.chat_widget.file_attached.connect(self.handle_file_attachment)
            
            # Settings connections
            self.model_settings.settings_changed.connect(self.handle_settings_change)
            
            # Conversation connections
            self.conversation_list.conversation_selected.connect(self.load_conversation)
            
            # Model selection
            self.chat_widget.model_selector.currentTextChanged.connect(self.on_model_changed)
            
            logger.info("Signal connections setup completed successfully")
            
        except Exception as exc:
            logger.error("Failed to setup connections: {}".format(exc))
            handle_error(exc, create_error_context("setup_connections"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def on_resize_event(self, event):
        """Handle window resize to maintain proportional frame sizes with error handling."""
        try:
            super().resizeEvent(event)
            
            # Get current window width
            window_width = self.width()
            
            # Calculate proportional sizes: 20% left, 60% center, 20% right
            left_width = int(window_width * 0.20)
            center_width = int(window_width * 0.60)
            right_width = int(window_width * 0.20)
            
            # Ensure minimum sizes
            left_width = max(240, left_width)
            right_width = max(240, right_width)
            center_width = max(480, center_width)
            
            # Update splitter sizes
            if hasattr(self, 'content_splitter'):
                self.content_splitter.setSizes([left_width, center_width, right_width])
                
                # Update status bar with current proportions
                if hasattr(self, 'status_bar'):
                    total_width = left_width + center_width + right_width
                    left_pct = int((left_width / total_width) * 100)
                    center_pct = int((center_width / total_width) * 100)
                    right_pct = int((right_width / total_width) * 100)
                    
                    self.status_bar.showMessage("Layout: {}% | {}% | {}%".format(left_pct, center_pct, right_pct))
            
        except Exception as exc:
            logger.error("Failed to handle resize event: {}".format(exc))
            handle_error(exc, create_error_context("on_resize_event"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.CONFIGURATION)
    def load_models(self):
        """Load available models with error handling and retry mechanism."""
        try:
            # TODO: Load from API providers
            models = {
                "OpenAI": ["GPT-4", "GPT-3.5-turbo", "GPT-4-turbo"],
                "Anthropic": ["Claude-3-opus", "Claude-3-sonnet", "Claude-3-haiku"],
                "Google": ["Gemini-Pro", "Gemini-Pro-Vision", "Gemini 2.5 Pro", "Gemma 3"],
                "Ollama": ["llama2", "mistral", "codellama", "Qwen 3", "Custom Model"],
                "Local": ["Local-GPT", "Custom-Model"]
            }
            
            # Populate the floating combo box with hierarchical format
            if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'model_selector'):
                self.chat_widget.model_selector.clear()
                
                for provider, model_list in models.items():
                    for model in model_list:
                        display_text = "{}: {}".format(provider, model)
                        self.chat_widget.model_selector.addItem(display_text, "{}:{}".format(provider, model))
                
                logger.info("Models loaded successfully: {} providers, {} total models".format(
                    len(models), sum(len(model_list) for model_list in models.values())))
            else:
                logger.warning("Chat widget or model selector not available")
                
        except Exception as exc:
            logger.error("Failed to load models: {}".format(exc))
            handle_error(exc, create_error_context("load_models"))
            
            # Fallback: load basic models
            try:
                if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'model_selector'):
                    self.chat_widget.model_selector.addItem("OpenAI: GPT-3.5-turbo", "OpenAI:GPT-3.5-turbo")
                    logger.info("Fallback models loaded")
            except Exception as fallback_error:
                logger.error("Failed to load fallback models: {}".format(fallback_error))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def handle_message(self, message: str):
        """Handle incoming messages with error handling."""
        try:
            logger.info("Handling message: {}".format(message[:100] + "..." if len(message) > 100 else message))
            
            # Add message to chat history
            if hasattr(self, 'chat_widget'):
                self.chat_widget.add_message("User", message, "user")
                
                # TODO: Process message with AI
                # For now, just echo back
                response = "Echo: {}".format(message)
                self.chat_widget.add_message("Assistant", response, "assistant")
                
                logger.debug("Message handled successfully")
            else:
                logger.warning("Chat widget not available for message handling")
                
        except Exception as exc:
            logger.error("Failed to handle message: {}".format(exc))
            handle_error(exc, create_error_context("handle_message"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.FILE_SYSTEM)
    def handle_file_attachment(self, file_path: str):
        """Handle file attachments with error handling."""
        try:
            logger.info("Handling file attachment: {}".format(file_path))
            
            # TODO: Process file attachment
            if hasattr(self, 'chat_widget'):
                self.chat_widget.add_message("System", "File attached: {}".format(file_path), "system")
                
            logger.debug("File attachment handled successfully")
            
        except Exception as exc:
            logger.error("Failed to handle file attachment: {}".format(exc))
            handle_error(exc, create_error_context("handle_file_attachment"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.CONFIGURATION)
    def handle_settings_change(self, settings: Dict[str, Any]):
        """Handle model settings changes with error handling."""
        try:
            logger.info("Settings changed: {}".format(settings))
            # TODO: Apply new settings
            
        except Exception as exc:
            logger.error("Failed to handle settings change: {}".format(exc))
            handle_error(exc, create_error_context("handle_settings_change"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.DATABASE)
    def load_conversation(self, conversation_id: str):
        """Load a conversation with error handling."""
        try:
            logger.info("Loading conversation: {}".format(conversation_id))
            # TODO: Load conversation from storage
            
        except Exception as exc:
            logger.error("Failed to load conversation: {}".format(exc))
            handle_error(exc, create_error_context("load_conversation"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.CONFIGURATION)
    def on_model_changed(self, model: str):
        """Handle model selection change with error handling."""
        try:
            logger.info("Model changed to: {}".format(model))
            
            # Get the current item data to extract provider and model
            if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'model_selector'):
                current_index = self.chat_widget.model_selector.currentIndex()
                if current_index >= 0:
                    item_data = self.chat_widget.model_selector.itemData(current_index, Qt.ItemDataRole.UserRole)
                    if item_data and ":" in str(item_data):
                        provider, model_name = str(item_data).split(":", 1)
                        if hasattr(self, 'status_label'):
                            self.status_label.setText("{}: {}".format(provider, model_name))
                        logger.info("Selected: {} - {}".format(provider, model_name))
                    else:
                        if hasattr(self, 'status_label'):
                            self.status_label.setText("Model: {}".format(model))
                else:
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("Model: {}".format(model))
            else:
                logger.warning("Chat widget or model selector not available")
                
        except Exception as exc:
            logger.error("Failed to handle model change: {}".format(exc))
            handle_error(exc, create_error_context("on_model_changed"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.CONFIGURATION)
    def on_provider_changed(self, provider: str):
        """Handle provider selection change with error handling."""
        try:
            logger.info("Provider changed to: {}".format(provider))
            if hasattr(self, 'status_label'):
                self.status_label.setText("Provider: {}".format(provider))
                
        except Exception as exc:
            logger.error("Failed to handle provider change: {}".format(exc))
            handle_error(exc, create_error_context("on_provider_changed"))

    # Add error handling to all menu action handlers
    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def new_conversation(self):
        """Create a new conversation with error handling."""
        try:
            if hasattr(self, 'conversation_list'):
                self.conversation_list.new_conversation()
            if hasattr(self, 'chat_widget'):
                self.chat_widget.chat_history.clear()
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage("New conversation created")
                
            logger.info("New conversation created successfully")
            
        except Exception as exc:
            logger.error("Failed to create new conversation: {}".format(exc))
            handle_error(exc, create_error_context("new_conversation"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def closeEvent(self, event):
        """Handle application close event with error handling."""
        try:
            logger.info("Application closing...")
            
            # Save any pending data
            # TODO: Implement data saving
            
            # Clean up resources
            # TODO: Implement cleanup
            
            logger.info("Application closed successfully")
            event.accept()
            
        except Exception as exc:
            logger.error("Error during application close: {}".format(exc))
            handle_error(exc, create_error_context("closeEvent"))
            event.accept()  # Still close the application

    def load_conversation_tags(self):
        """Load conversation tags with error handling."""
        try:
            # TODO: Load conversation tags from storage
            pass
        except Exception as exc:
            logger.error("Failed to load conversation tags: {}".format(exc))
            handle_error(exc, create_error_context("load_conversation_tags")) 
