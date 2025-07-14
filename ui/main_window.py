#!/usr/bin/env python3
"""
Main Window for The Oracle AI Chat Application
File: ui/main_window.py

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
    QProgressBar, QTabWidget, QCheckBox, QSpinBox, QDialog, QFormLayout,
    QSpacerItem, QSizePolicy, QToolButton
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QColor, QPixmap, QAction, QShortcut
from PyQt6.QtWidgets import QApplication

# Import comprehensive error handling
from utils.error_handler import (
    error_handler, error_context, safe_execute, log_function_call,
    ErrorSeverity, ErrorCategory, RetryConfig, handle_error, 
    create_error_context, validate_input
)

# Import other components
from utils.markdown_formatter import markdown_formatter
from utils.avatar_manager import avatar_manager

# Import conversation tagging system
from ui.conversation_tagging import TagManager, ConversationTagWidget, TagManagerWidget

# Import command palette system
from ui.command_palette import CommandPaletteManager, CommandPaletteDialog

# Import quick switch model menu
from core.quick_switch import QuickSwitchModelMenu
from ui.quick_switch_widget import QuickSwitchWidget

# Import last read marker system
from core.last_read_marker import LastReadMarker
from ui.last_read_marker_widget import LastReadMarkerDialog

# Use the logger from dependencies
from utils.dependencies import log as logger

# Import API settings dialog
from ui.api_settings_dialog import APISettingsDialog
from ui.prompt_library_dialog import PromptLibraryDialog
from ui.prompt_template_dialog import PromptTemplateDialog
from ui.keyboard_shortcut_editor import KeyboardShortcutEditor
from ui.system_prompt_dialog import SystemPromptDialog
from ui.model_settings_dialog import ModelSettingsDialog


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
        self.content_widget = None  # Store reference to content widget
        
        # Set up the panel
        # self.setFixedWidth(self.full_width)  # Remove this line to allow animation
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
            self.toggle_btn.setText("▲")  # Up arrow when expanded (can contract upward)
        else:
            self.toggle_btn.setText("▼")  # Down arrow when contracted (can expand downward)
    
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
        
        # Hide content widget but keep chat header visible
        if self.content_widget:
            self.content_widget.hide()
        
        # Ensure chat header is visible
        if self.chat_header_widget:
            self.chat_header_widget.show()
        
        # Set to collapsed height
        self.setFixedHeight(self.collapsed_height)
        
        self.update_button_position()
        # Emit signal to notify parent of panel state change
        self.panel_toggled.emit(self.is_open)
    
    def expand_panel(self):
        """Expand the panel."""
        if self.is_open:
            return
        
        self.is_open = True
        
        # Show content widget
        if self.content_widget:
            self.content_widget.show()
        
        # Ensure chat header is visible
        if self.chat_header_widget:
            self.chat_header_widget.show()
        
        # Set to full height
        self.setFixedHeight(self.full_height)
        
        self.update_button_position()
        # Emit signal to notify parent of panel state change
        self.panel_toggled.emit(self.is_open)


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
        
        # Conversation tags widget
        self.conversation_tags_widget = None  # Will be initialized when a conversation is selected
        self.tags_container = QWidget()
        self.tags_layout = QVBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(5)
        
        # Tags header
        tags_header = QLabel("🏷️ Conversation Tags")
        tags_header.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px; margin-top: 10px;")
        self.tags_layout.addWidget(tags_header)
        
        # Tags placeholder
        self.tags_placeholder = QLabel("Select a conversation to manage tags")
        self.tags_placeholder.setStyleSheet("color: #888888; font-style: italic; font-size: 11px; padding: 10px;")
        self.tags_layout.addWidget(self.tags_placeholder)
        
        self.tags_layout.addStretch()
        layout.addWidget(self.tags_container)
        
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
            item = QListWidgetItem("📝 {}\n⏰ {}".format(conv['title'], conv['timestamp']))
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
        self.update_conversation_tags(conv_id)
    
    def update_conversation_tags(self, conversation_id: str):
        """Update the conversation tags widget for the selected conversation."""
        # Remove existing tags widget
        if self.conversation_tags_widget:
            self.conversation_tags_widget.deleteLater()
            self.conversation_tags_widget = None
        
        # Hide placeholder
        self.tags_placeholder.hide()
        
        # Create new tags widget
        from conversation_tagging import ConversationTagWidget
        self.conversation_tags_widget = ConversationTagWidget(
            self.parent().parent().tag_manager,  # Access tag manager from MainWindow
            conversation_id
        )
        self.tags_layout.insertWidget(1, self.conversation_tags_widget)
    
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
        # Set a fun, legible font for the entire app
        fun_font = QFont("Comic Sans MS", 10)
        QApplication.instance().setFont(fun_font)
        self.model_selector.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 3px 8px;
                color: white;
                font-family: 'Comic Sans MS', 'Segoe Print', 'Baloo', cursive;
                font-size: 12px;
                min-width: 300px;
                min-height: 23px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
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
        # Set background styling for the center frame
        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
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
            formatted_message = """
<div style="margin: 10px 0; padding: 10px; background: #3a3a3a; border-radius: 8px; border-left: 4px solid #0078d4;">
    <div style="font-weight: bold; color: #0078d4; margin-bottom: 5px;">👤 {}</div>
    <div style="color: white; line-height: 1.4;">{}</div>
    <div style="font-size: 10px; color: #888; margin-top: 5px;">{}</div>
</div>
""".format(sender, message, timestamp)
        elif message_type == "assistant":
            model_info = " ({})".format(model_name) if model_name else ""
            formatted_message = """
<div style="margin: 10px 0; padding: 10px; background: #2b2b2b; border-radius: 8px; border-left: 4px solid #00b894;">
    <div style="font-weight: bold; color: #00b894; margin-bottom: 5px;">🤖 Assistant{}</div>
    <div style="color: white; line-height: 1.4;">{}</div>
    <div style="font-size: 10px; color: #888; margin-top: 5px;">{}</div>
</div>
""".format(model_info, message, timestamp)
        else:
            formatted_message = """
<div style="margin: 10px 0; padding: 10px; background: #2b2b2b; border-radius: 8px; border-left: 4px solid #f39c12;">
    <div style="font-weight: bold; color: #f39c12; margin-bottom: 5px;">ℹ️ {}</div>
    <div style="color: white; line-height: 1.4;">{}</div>
    <div style="font-size: 10px; color: #888; margin-top: 5px;">{}</div>
</div>
""".format(sender, message, timestamp)
        
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


class TopPanel(QFrame):
    """Top panel that slides vertically (down/up) with chat header when contracted."""
    
    panel_toggled = pyqtSignal(bool)  # is_open
    
    def __init__(self, parent=None, height=200):
        super().__init__(parent)
        self.full_height = 330  # Increased by another 10% to show all 3 tabs and content
        self.collapsed_height = 60  # Reduced collapsed height to fit chat header with minimal margins
        self.is_open = False  # Start contracted
        self.button_width = 32
        self.button_height = 24
        self.content_widget = None
        self.chat_header_widget = None
        
        # Set up the panel
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2b2b2b, stop:1 #3a3a3a);
                border: 1px solid #555555;
                border-radius: 8px;
            }
        """)
        
        # Create toggle button
        self.toggle_btn = QPushButton("▼")  # Down arrow to expand
        self.toggle_btn.setFixedSize(self.button_width, self.button_height)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 12px;
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
        self.main_layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        self.main_layout.setSpacing(2)  # Minimal spacing
        
        # Update button position
        self.update_button_position()
        
        # Set initial collapsed height
        self.setFixedHeight(self.collapsed_height)
    
    def add_chat_header(self):
        """Add chat header widget to the panel."""
        self.chat_header_widget = QWidget()
        header_layout = QHBoxLayout(self.chat_header_widget)
        header_layout.setContentsMargins(8, 5, 8, 5)  # Minimal margins for chat header
        header_layout.setSpacing(8)  # Minimal spacing for chat header
        
        # Chat title (left side)
        title = QLabel("💬 Chat")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))  # Reduced font size
        title.setStyleSheet("color: #ffffff; padding: 2px;")  # Minimal padding
        header_layout.addWidget(title)
        
        # Add toggle button to the center of the header
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        header_layout.addStretch()
        
        # Model selector (right side)
        model_label = QLabel("Model:")
        model_label.setStyleSheet("color: #ffffff; font-size: 10px;")  # Reduced font size
        header_layout.addWidget(model_label)
        
        self.model_selector = QComboBox()
        self.model_selector.addItems(["GPT-4", "GPT-3.5-turbo", "Claude-3", "Gemini-Pro"])
        self.model_selector.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 3px 8px;  /* Minimal padding */
                color: white;
                font-size: 10px;  /* Reduced font size */
                min-width: 300px;  /* Increased width 3x */
                min-height: 23px;  /* Increased height by 15% */
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
        """)
        header_layout.addWidget(self.model_selector)
        
        # Add chat header at the top of the layout
        self.main_layout.insertWidget(0, self.chat_header_widget)
        
        # Ensure chat header is visible initially
        self.chat_header_widget.show()
    
    def update_button_position(self):
        """Update button position based on panel state."""
        if self.is_open:
            self.toggle_btn.setText("▲")  # Up arrow when expanded (can contract upward)
        else:
            self.toggle_btn.setText("▼")  # Down arrow when contracted (can expand downward)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.update_button_position()
    
    def enterEvent(self, event):
        """Handle mouse enter events."""
        super().enterEvent(event)
        if not self.is_open:
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
        """Collapse the panel upward."""
        if not self.is_open:
            return
        
        self.is_open = False
        
        # Hide content widget but keep chat header visible
        if self.content_widget:
            self.content_widget.hide()
        
        # Ensure chat header is visible
        if self.chat_header_widget:
            self.chat_header_widget.show()
        
        # Move toggle button back to chat header when collapsed
        if hasattr(self.content_widget, 'toggle_btn_placeholder'):
            # Replace toggle button with placeholder in tools widget
            placeholder = self.content_widget.toggle_btn_placeholder
            if placeholder and placeholder.parent():
                parent_layout = placeholder.parent().layout()
                if parent_layout:
                    parent_layout.replaceWidget(self.toggle_btn, placeholder)
                    placeholder.show()
        
        # Ensure toggle button is properly added back to chat header
        if self.chat_header_widget and self.chat_header_widget.layout():
            header_layout = self.chat_header_widget.layout()
            # Check if toggle button is already in the layout
            button_found = False
            for i in range(header_layout.count()):
                if header_layout.itemAt(i).widget() == self.toggle_btn:
                    button_found = True
                    break
            
            # If toggle button is not in the header layout, add it back
            if not button_found:
                # Find the position after the chat title (index 1) and before the right stretch
                header_layout.insertWidget(2, self.toggle_btn)
        
        # Ensure toggle button is visible in chat header
        self.toggle_btn.show()
        
        # Set to collapsed height
        self.setFixedHeight(self.collapsed_height)
        
        self.update_button_position()
        # Emit signal to notify parent of panel state change
        self.panel_toggled.emit(self.is_open)
    
    def expand_panel(self):
        """Expand the panel downward."""
        if self.is_open:
            return
        
        self.is_open = True
        
        # Show content widget
        if self.content_widget:
            self.content_widget.show()
        
        # Ensure chat header is visible
        if self.chat_header_widget:
            self.chat_header_widget.show()
        
        # Move toggle button to tools widget when expanded
        if hasattr(self.content_widget, 'toggle_btn_placeholder'):
            # Replace placeholder with actual toggle button
            placeholder = self.content_widget.toggle_btn_placeholder
            if placeholder and placeholder.parent():
                parent_layout = placeholder.parent().layout()
                if parent_layout:
                    parent_layout.replaceWidget(placeholder, self.toggle_btn)
                    placeholder.hide()
                    self.toggle_btn.show()
        
        # Set to full height
        self.setFixedHeight(self.full_height)
        
        self.update_button_position()
        # Emit signal to notify parent of panel state change
        self.panel_toggled.emit(self.is_open)


class BottomPanel(QFrame):
    """Bottom panel that slides vertically (up/down)."""
    
    def __init__(self, parent=None, height=200):
        super().__init__(parent)
        self.full_height = height
        self.collapsed_height = 40  # Further reduced collapsed height to fit toggle button with minimal margins
        self.is_open = True
        self.button_width = 32
        self.button_height = 24
        self.content_widget = None
        
        # Set up the panel
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2b2b2b, stop:1 #3a3a3a);
                border: 1px solid #555555;
                border-radius: 8px;
            }
        """)
        
        # Create toggle button
        self.toggle_btn = QPushButton("▲")
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
        self.main_layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        self.main_layout.setSpacing(2)  # Minimal spacing
        
        # Add toggle button at the top center
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.toggle_btn)
        button_layout.addStretch()
        
        self.main_layout.addLayout(button_layout)
        
        # Update button position
        self.update_button_position()
        
    def update_button_position(self):
        """Update button position based on panel state."""
        if self.is_open:
            self.toggle_btn.setText("▲")  # Up arrow when expanded (can contract upward)
        else:
            self.toggle_btn.setText("▼")  # Down arrow when contracted (can expand downward)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        self.update_button_position()
    
    def enterEvent(self, event):
        """Handle mouse enter events."""
        super().enterEvent(event)
        if not self.is_open:
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
        """Collapse the panel upward."""
        if not self.is_open:
            return
        
        self.is_open = False
        
        # Hide content widget
        if self.content_widget:
            self.content_widget.hide()
        
        # Animate to collapsed height
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        start_rect = self.geometry()
        # Move bottom edge up (contract upward)
        end_rect = QRect(start_rect.x(), start_rect.y() + (self.full_height - self.collapsed_height), 
                        start_rect.width(), self.collapsed_height)
        
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass  # No connection to disconnect
        self.animation.finished.connect(self._finalize_height)
        self.animation.start()
        
        self.update_button_position()
    
    def expand_panel(self):
        """Expand the panel downward."""
        if self.is_open:
            return
        
        self.is_open = True
        
        # Show content widget
        if self.content_widget:
            self.content_widget.show()
        
        # Animate to full height
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        start_rect = self.geometry()
        # Move bottom edge down (expand downward)
        end_rect = QRect(start_rect.x(), start_rect.y() - (self.full_height - self.collapsed_height), 
                        start_rect.width(), self.full_height)
        
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass  # No connection to disconnect
        self.animation.finished.connect(self._finalize_height)
        self.animation.start()
        
        self.update_button_position()

    def _finalize_height(self):
        """Set the final height after animation completes."""
        if self.is_open:
            self.setMinimumHeight(self.full_height)
        else:
            self.setMinimumHeight(self.collapsed_height)


class BottomToolsWidget(QWidget):
    """Widget containing tools and features for the bottom panel."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the bottom tools UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Title with toggle button
        title_widget = QWidget()
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)
        
        title = QLabel("🛠️ Tools & Features")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; padding: 5px;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # Add toggle button to the center of the title
        # This will be set by the TopPanel when it's expanded
        self.toggle_btn = None
        self.toggle_btn_placeholder = QWidget()  # Placeholder for toggle button
        title_layout.addWidget(self.toggle_btn_placeholder)
        title_layout.addStretch()
        layout.addWidget(title_widget)
        
        # Create tabs for different tool categories
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background: #2b2b2b;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #3a3a3a;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #0078d4;
            }
            QTabBar::tab:hover {
                background: #4a4a4a;
            }
        """)
        
        # Quick Actions Tab
        self.quick_actions_tab = self.create_quick_actions_tab()
        self.tab_widget.addTab(self.quick_actions_tab, "⚡ Quick Actions")
        
        # File Management Tab
        self.file_management_tab = self.create_file_management_tab()
        self.tab_widget.addTab(self.file_management_tab, "📁 Files")
        
        # Settings Tab
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")
        
        layout.addWidget(self.tab_widget)
        
    def create_quick_actions_tab(self):
        """Create the quick actions tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Quick action buttons
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
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
        
        actions_layout = QGridLayout(actions_group)
        
        # Action buttons
        actions = [
            ("🆕 New Chat", "Start a new conversation"),
            ("💾 Save Chat", "Save current conversation"),
            ("📤 Export", "Export conversation"),
            ("🔍 Search", "Search chat history"),
            ("🏷️ Tags", "Manage conversation tags"),
            ("📊 Analytics", "View chat analytics"),
            ("🎨 Theme", "Change theme"),
            ("⚙️ Settings", "Open settings")
        ]
        
        for i, (text, tooltip) in enumerate(actions):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 6px;
                    padding: 8px;
                    color: white;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #4a4a4a;
                    border: 1px solid #0078d4;
                }
            """)
            actions_layout.addWidget(btn, i // 4, i % 4)
        
        layout.addWidget(actions_group)
        layout.addStretch()
        return tab
    
    def create_file_management_tab(self):
        """Create the file management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Recent files
        recent_group = QGroupBox("Recent Files")
        recent_group.setStyleSheet("""
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
        
        recent_layout = QVBoxLayout(recent_group)
        
        # Recent files list
        self.recent_files_list = QListWidget()
        self.recent_files_list.setMaximumHeight(100)
        self.recent_files_list.setStyleSheet("""
            QListWidget {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 4px;
                color: white;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:hover {
                background: #3a3a3a;
            }
        """)
        
        # Add sample recent files
        sample_files = ["conversation_1.json", "export_chat.md", "settings_backup.json"]
        for file in sample_files:
            self.recent_files_list.addItem(f"📄 {file}")
        
        recent_layout.addWidget(self.recent_files_list)
        layout.addWidget(recent_group)
        
        # File actions
        file_actions_layout = QHBoxLayout()
        
        open_btn = QPushButton("📂 Open File")
        open_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                border: 1px solid #0078d4;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        
        save_btn = QPushButton("💾 Save As")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #00b894;
                border: 1px solid #00b894;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #00a085;
            }
        """)
        
        file_actions_layout.addWidget(open_btn)
        file_actions_layout.addWidget(save_btn)
        file_actions_layout.addStretch()
        
        layout.addLayout(file_actions_layout)
        layout.addStretch()
        return tab
    
    def create_settings_tab(self):
        """Create the settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_group.setStyleSheet("""
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
        
        general_layout = QFormLayout(general_group)
        
        # Auto-save setting
        self.auto_save_checkbox = QCheckBox("Enable auto-save")
        self.auto_save_checkbox.setStyleSheet("color: white; font-size: 11px;")
        general_layout.addRow("Auto-save:", self.auto_save_checkbox)
        
        # Theme setting
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: white;
                font-size: 11px;
            }
        """)
        general_layout.addRow("Theme:", self.theme_combo)
        
        # Font size setting
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setStyleSheet("""
            QSpinBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                color: white;
                font-size: 11px;
            }
        """)
        general_layout.addRow("Font Size:", self.font_size_spin)
        
        layout.addWidget(general_group)
        layout.addStretch()
        return tab


class MainWindow(QMainWindow):
    """Main application window with sliding panels and chat interface."""
    
    def __init__(self):
        """Initialize MainWindow with comprehensive error handling."""
        try:
            super().__init__()
            self.setWindowTitle("The Oracle - AI Chat Application")
            self.setMinimumSize(1400, 900)
            self.resize(1800, 1200)
            
            # Initialize tag manager
            self.tag_manager = TagManager()
            
            # Initialize command palette manager
            self.command_palette_manager = CommandPaletteManager()
            
            # Initialize quick switch model menu
            self.quick_switch_menu = QuickSwitchModelMenu()
            self.quick_switch_widget = None  # Will be created when needed
            
            # Initialize last read marker system
            self.last_read_marker = LastReadMarker()
            self.last_read_marker_dialog = None  # Will be created when needed
            
            # Initialize components with error handling
            self.setup_ui()
            self.setup_menu()
            self.setup_status_bar()
            self.setup_connections()
            
            # Load initial data
            self.load_models()
            
            # Load conversation tags with error handling
            self.load_conversation_tags()
            
            if hasattr(logger, 'info'):
                logger.info("Main window initialized successfully")
            
        except Exception as exc:
            if hasattr(logger, 'critical'):
                logger.critical("Failed to initialize MainWindow: {}".format(exc))
            else:
                print("Critical error: Failed to initialize MainWindow: {}".format(exc))
            raise

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
            
            # Top panel (tools) - now at the top with chat header when contracted
            self.top_panel = TopPanel(height=330)
            self.bottom_tools_widget = BottomToolsWidget()
            self.top_panel.content_widget = self.bottom_tools_widget
            self.top_panel.main_layout.insertWidget(0, self.bottom_tools_widget)
            
            # Hide content widget initially since panel starts contracted
            self.bottom_tools_widget.hide()
            
            # Add chat header to top panel
            self.top_panel.add_chat_header()
            
            # Connect toggle button to tools widget
            self.bottom_tools_widget.toggle_btn = self.top_panel.toggle_btn
            
            main_layout.addWidget(self.top_panel)
            
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
            self.left_panel = SlidingPanel(side='left', width=320)
            self.conversation_list = ConversationList()
            self.left_panel.content_widget = self.conversation_list # Assign content widget
            self.left_panel.main_layout.insertWidget(0, self.conversation_list)
            self.content_splitter.addWidget(self.left_panel)
            
            # Center chat area - takes most space (60% of width)
            self.chat_widget = ChatWidget()
            self.chat_widget.content_widget = self.chat_widget # Assign content widget
            self.content_splitter.addWidget(self.chat_widget)
            
            # Right sliding panel (settings) - 20% of width
            self.right_panel = SlidingPanel(side='right', width=320)
            self.model_settings = ModelSettings()
            self.right_panel.content_widget = self.model_settings # Assign content widget
            self.right_panel.main_layout.insertWidget(0, self.model_settings)
            self.content_splitter.addWidget(self.right_panel)
            
            # Set splitter proportions: 20% left, 60% center, 20% right
            left_width = int(1800 * 0.20)
            center_width = int(1800 * 0.60)
            right_width = int(1800 * 0.20)
            self.content_splitter.setSizes([left_width, center_width, right_width])
            
            main_layout.addWidget(self.content_splitter)
            
            # Set stretch factors: top_panel (0), content_splitter (1)
            main_layout.setStretch(0, 0)
            main_layout.setStretch(1, 1)
            
            # Connect resize event to maintain proportions
            self.resizeEvent = self.on_resize_event
            
            if hasattr(logger, 'info'):
                logger.info("UI setup completed successfully")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to setup UI: {}".format(exc))
            else:
                print("Error: Failed to setup UI: {}".format(exc))
            raise

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

            # --- FILE MENU ---
            file_menu = menubar.addMenu(self.tr("📁 File"))
            new_action = QAction(self.tr("🆕 New Conversation"), self)
            new_action.setShortcut(QKeySequence.StandardKey.New)
            new_action.setToolTip(self.tr("Start a new conversation"))
            new_action.triggered.connect(self.new_conversation)
            file_menu.addAction(new_action)
            # Add more file actions as completed features become available
            exit_action = QAction(self.tr("🚪 Exit"), self)
            exit_action.setShortcut(QKeySequence.StandardKey.Quit)
            exit_action.setToolTip(self.tr("Exit The Oracle"))
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            # --- EDIT MENU ---
            edit_menu = menubar.addMenu(self.tr("✏️ Edit"))
            # Example: Undo/Redo if implemented
            # undo_action = QAction(self.tr("Undo"), self)
            # undo_action.setShortcut(QKeySequence.StandardKey.Undo)
            # edit_menu.addAction(undo_action)
            # ... (add more as completed)

            # --- VIEW MENU ---
            view_menu = menubar.addMenu(self.tr("👁️ View"))
            # Example: Toggle Theme
            toggle_theme_action = QAction(self.tr("Toggle Theme"), self)
            toggle_theme_action.setShortcut(self.tr("Ctrl+Shift+T"))
            toggle_theme_action.setToolTip(self.tr("Toggle between light and dark themes"))
            toggle_theme_action.triggered.connect(self.toggle_theme)
            view_menu.addAction(toggle_theme_action)
            # ... (add more as completed)

            # --- CONVERSATION MENU ---
            conversation_menu = menubar.addMenu(self.tr("💬 Conversation"))
            # Example: New Conversation
            conv_new_action = QAction(self.tr("New Conversation"), self)
            conv_new_action.setShortcut(self.tr("Ctrl+N"))
            conv_new_action.setToolTip(self.tr("Start a new conversation"))
            conv_new_action.triggered.connect(self.new_conversation)
            conversation_menu.addAction(conv_new_action)
            # ... (add more as completed)

            # --- MODELS MENU ---
            models_menu = menubar.addMenu(self.tr("🤖 Models"))
            # Example: Quick Switch Model
            quick_switch_action = QAction(self.tr("Quick Switch Model"), self)
            quick_switch_action.setShortcut(self.tr("Ctrl+M"))
            quick_switch_action.setToolTip(self.tr("Quickly switch between models"))
            quick_switch_action.triggered.connect(self.show_quick_switch)
            models_menu.addAction(quick_switch_action)
            # ... (add more as completed)

            # --- TOOLS MENU ---
            tools_menu = menubar.addMenu(self.tr("🔧 Tools"))
            tag_manager_action = QAction(self.tr("Tag Manager"), self)
            tag_manager_action.setShortcut(self.tr("Ctrl+T"))
            tag_manager_action.setToolTip(self.tr("Manage conversation tags"))
            tag_manager_action.triggered.connect(self.show_tag_manager)
            tools_menu.addAction(tag_manager_action)
            last_read_action = QAction(self.tr("Last Read Markers"), self)
            last_read_action.setShortcut(self.tr("Ctrl+L"))
            last_read_action.setToolTip(self.tr("Show last read markers"))
            last_read_action.triggered.connect(self.show_last_read_markers)
            tools_menu.addAction(last_read_action)
            command_palette_action = QAction(self.tr("Command Palette"), self)
            command_palette_action.setShortcut(self.tr("Ctrl+Shift+P"))
            command_palette_action.setToolTip(self.tr("Open the command palette for quick actions"))
            command_palette_action.triggered.connect(self.show_command_palette)
            tools_menu.addAction(command_palette_action)
            # Quick Switch Model is in Models menu

            # --- SETTINGS MENU ---
            settings_menu = menubar.addMenu(self.tr("⚙️ Settings"))
            api_settings_action = QAction(self.tr("API Settings"), self)
            api_settings_action.setToolTip(self.tr("Configure API keys and providers"))
            api_settings_action.triggered.connect(self.show_api_settings)
            settings_menu.addAction(api_settings_action)
            shortcut_editor_action = QAction(self.tr("Keyboard Shortcuts"), self)
            shortcut_editor_action.setToolTip(self.tr("Edit keyboard shortcuts"))
            shortcut_editor_action.triggered.connect(self.show_keyboard_shortcut_editor)
            settings_menu.addAction(shortcut_editor_action)
            model_settings_action = QAction(self.tr("Model Settings"), self)
            model_settings_action.setToolTip(self.tr("Configure model parameters"))
            model_settings_action.triggered.connect(self.show_model_settings)
            settings_menu.addAction(model_settings_action)
            prompt_library_action = QAction(self.tr("Prompt Library"), self)
            prompt_library_action.setToolTip(self.tr("Manage your prompt library"))
            prompt_library_action.triggered.connect(self.show_prompt_library)
            settings_menu.addAction(prompt_library_action)
            prompt_template_action = QAction(self.tr("Prompt Template Builder"), self)
            prompt_template_action.setToolTip(self.tr("Build and manage prompt templates"))
            prompt_template_action.triggered.connect(self.show_prompt_template)
            settings_menu.addAction(prompt_template_action)
            system_prompt_action = QAction(self.tr("System Prompt Editor"), self)
            system_prompt_action.setToolTip(self.tr("Edit the system prompt for conversations"))
            system_prompt_action.triggered.connect(self.show_system_prompt_editor)
            settings_menu.addAction(system_prompt_action)
            # ... (add more as completed)

            # --- HELP MENU ---
            help_menu = menubar.addMenu(self.tr("❓ Help"))
            # Example: About
            about_action = QAction(self.tr("About"), self)
            about_action.setToolTip(self.tr("About The Oracle"))
            about_action.triggered.connect(lambda: QMessageBox.about(self, self.tr("About The Oracle"), self.tr("The Oracle - AI Chat Application\nVersion 2.0.0")))
            help_menu.addAction(about_action)
            # ... (add more as completed)

            # --- EXPERIMENTAL MENU ---
            experimental_menu = menubar.addMenu(self.tr("🧪 Experimental"))
            # Add experimental features here as they are completed

            if hasattr(logger, 'info'):
                logger.info("Menu setup completed successfully")

        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to setup menu: {}".format(exc))
            else:
                print("Error: Failed to setup menu: {}".format(exc))

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
            
            if hasattr(logger, 'info'):
                logger.info("Status bar setup completed successfully")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to setup status bar: {}".format(exc))
            else:
                print("Error: Failed to setup status bar: {}".format(exc))

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
            
            # Model selection (now from top panel)
            self.top_panel.model_selector.currentTextChanged.connect(self.on_model_changed)
            
            # Top panel expand/contract
            self.top_panel.panel_toggled.connect(self.on_top_panel_toggled)
            
            if hasattr(logger, 'info'):
                logger.info("Signal connections setup completed successfully")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to setup connections: {}".format(exc))
            else:
                print("Error: Failed to setup connections: {}".format(exc))

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
            if hasattr(logger, 'error'):
                logger.error("Failed to handle resize event: {}".format(exc))
            else:
                print("Error: Failed to handle resize event: {}".format(exc))

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
                
                if hasattr(logger, 'info'):
                    logger.info("Models loaded successfully: {} providers, {} total models".format(
                        len(models), sum(len(model_list) for model_list in models.values())))
            else:
                if hasattr(logger, 'warning'):
                    logger.warning("Chat widget or model selector not available")
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to load models: {}".format(exc))
            else:
                print("Error: Failed to load models: {}".format(exc))
            
            # Fallback: load basic models
            try:
                if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'model_selector'):
                    self.chat_widget.model_selector.addItem("OpenAI: GPT-3.5-turbo", "OpenAI:GPT-3.5-turbo")
                    if hasattr(logger, 'info'):
                        logger.info("Fallback models loaded")
            except Exception as fallback_error:
                if hasattr(logger, 'error'):
                    logger.error("Failed to load fallback models: {}".format(fallback_error))
                else:
                    print("Error: Failed to load fallback models: {}".format(fallback_error))

    def handle_message(self, message: str):
        """Handle incoming messages with error handling."""
        try:
            if hasattr(logger, 'info'):
                logger.info("Handling message: {}".format(message[:100] + "..." if len(message) > 100 else message))
            
            # Add message to chat history
            if hasattr(self, 'chat_widget'):
                self.chat_widget.add_message("User", message, "user")
                
                # TODO: Process message with AI
                # For now, just echo back
                response = "Echo: {}".format(message)
                self.chat_widget.add_message("Assistant", response, "assistant")
                
                if hasattr(logger, 'debug'):
                    logger.debug("Message handled successfully")
            else:
                if hasattr(logger, 'warning'):
                    logger.warning("Chat widget not available for message handling")
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle message: {}".format(exc))
            else:
                print("Error: Failed to handle message: {}".format(exc))

    def handle_file_attachment(self, file_path: str):
        """Handle file attachments with error handling."""
        try:
            if hasattr(logger, 'info'):
                logger.info("Handling file attachment: {}".format(file_path))
            
            # TODO: Process file attachment
            if hasattr(self, 'chat_widget'):
                self.chat_widget.add_message("System", "File attached: {}".format(file_path), "system")
                
            if hasattr(logger, 'debug'):
                logger.debug("File attachment handled successfully")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle file attachment: {}".format(exc))
            else:
                print("Error: Failed to handle file attachment: {}".format(exc))

    def handle_settings_change(self, settings: Dict[str, Any]):
        """Handle model settings changes with error handling."""
        try:
            if hasattr(logger, 'info'):
                logger.info("Settings changed: {}".format(settings))
            # TODO: Apply new settings
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle settings change: {}".format(exc))
            else:
                print("Error: Failed to handle settings change: {}".format(exc))

    def load_conversation(self, conversation_id: str):
        """Load a conversation with error handling."""
        try:
            if hasattr(logger, 'info'):
                logger.info("Loading conversation: {}".format(conversation_id))
            # TODO: Load conversation from storage
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to load conversation: {}".format(exc))
            else:
                print("Error: Failed to load conversation: {}".format(exc))

    def on_model_changed(self, model: str):
        """Handle model selection change with error handling."""
        try:
            if hasattr(logger, 'info'):
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
                        if hasattr(logger, 'info'):
                            logger.info("Selected: {} - {}".format(provider, model_name))
                    else:
                        if hasattr(self, 'status_label'):
                            self.status_label.setText("Model: {}".format(model))
                else:
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("Model: {}".format(model))
            else:
                if hasattr(logger, 'warning'):
                    logger.warning("Chat widget or model selector not available")
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle model change: {}".format(exc))
            else:
                print("Error: Failed to handle model change: {}".format(exc))

    def on_provider_changed(self, provider: str):
        """Handle provider selection change with error handling."""
        try:
            if hasattr(logger, 'info'):
                logger.info("Provider changed to: {}".format(provider))
            if hasattr(self, 'status_label'):
                self.status_label.setText("Provider: {}".format(provider))
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle provider change: {}".format(exc))
            else:
                print("Error: Failed to handle provider change: {}".format(exc))

    def new_conversation(self):
        """Create a new conversation with error handling."""
        try:
            # TODO: Implement new conversation creation
            if hasattr(logger, 'info'):
                logger.info("New conversation created")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to create new conversation: {}".format(exc))
            else:
                print("Error: Failed to create new conversation: {}".format(exc))
    
    def show_tag_manager(self):
        """Show the tag manager dialog."""
        try:
            from conversation_tagging import TagManagerWidget
            
            # Create tag manager dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("🏷️ Tag Manager")
            dialog.setModal(True)
            dialog.setMinimumSize(600, 500)
            
            # Create layout
            layout = QVBoxLayout(dialog)
            
            # Create tag manager widget
            tag_manager_widget = TagManagerWidget(self.tag_manager)
            layout.addWidget(tag_manager_widget)
            
            # Add close button
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            # Show dialog
            dialog.exec()
            
            if hasattr(logger, 'info'):
                logger.info("Tag manager dialog shown")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to show tag manager: {}".format(exc))
            else:
                print("Error: Failed to show tag manager: {}".format(exc))
    
    def show_command_palette(self):
        """Show the command palette dialog."""
        try:
            dialog = CommandPaletteDialog(self.command_palette_manager, self)
            dialog.command_executed.connect(self.on_command_executed)
            dialog.exec()
            
            if hasattr(logger, 'info'):
                logger.info("Command palette dialog shown")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to show command palette: {}".format(exc))
            else:
                print("Error: Failed to show command palette: {}".format(exc))
    
    def show_quick_switch(self):
        """Show the quick switch model menu dialog."""
        try:
            # Create quick switch widget if it doesn't exist
            if self.quick_switch_widget is None:
                self.quick_switch_widget = QuickSwitchWidget(self.quick_switch_menu, self)
                self.quick_switch_widget.model_selected.connect(self.on_quick_switch_model_selected)
                self.quick_switch_widget.widget_closed.connect(self.on_quick_switch_closed)
            
            # Show the widget
            self.quick_switch_widget.show()
            self.quick_switch_widget.raise_()
            self.quick_switch_widget.activateWindow()
            
            if hasattr(logger, 'info'):
                logger.info("Quick switch model menu shown")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to show quick switch menu: {}".format(exc))
            else:
                print("Error: Failed to show quick switch menu: {}".format(exc))
    
    def on_quick_switch_model_selected(self, provider: str, model_name: str):
        """Handle model selection from quick switch menu."""
        try:
            # Update the model selector in the chat widget
            if hasattr(self, 'chat_widget') and hasattr(self.chat_widget, 'model_selector'):
                # Find the model in the selector
                for i in range(self.chat_widget.model_selector.count()):
                    item_data = self.chat_widget.model_selector.itemData(i, Qt.ItemDataRole.UserRole)
                    if item_data and ":" in str(item_data):
                        item_provider, item_model = str(item_data).split(":", 1)
                        if item_provider == provider and item_model == model_name:
                            self.chat_widget.model_selector.setCurrentIndex(i)
                            break
            
            # Update status
            if hasattr(self, 'status_label'):
                self.status_label.setText("Model switched to: {} - {}".format(provider, model_name))
            
            if hasattr(logger, 'info'):
                logger.info("Model switched via quick switch: {} - {}".format(provider, model_name))
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle quick switch model selection: {}".format(exc))
            else:
                print("Error: Failed to handle quick switch model selection: {}".format(exc))
    
    def on_quick_switch_closed(self):
        """Handle quick switch widget closure."""
        try:
            # Hide the widget
            if self.quick_switch_widget:
                self.quick_switch_widget.hide()
            
            if hasattr(logger, 'info'):
                logger.info("Quick switch model menu closed")
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle quick switch closure: {}".format(exc))
            else:
                print("Error: Failed to handle quick switch closure: {}".format(exc))
    
    def on_command_executed(self, command_id: str):
        """Handle command execution from palette."""
        try:
            # Map command IDs to actual actions
            command_actions = {
                'new_conversation': self.new_conversation,
                'tag_manager': self.show_tag_manager,
                'command_palette': self.show_command_palette,
                'quick_switch': self.show_quick_switch,
                # Add more command mappings as needed
            }
            
            if command_id in command_actions:
                command_actions[command_id]()
            
            if hasattr(logger, 'info'):
                logger.info("Executed command from palette: {}".format(command_id))
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to execute command {}: {}".format(command_id, exc))
            else:
                print("Error: Failed to execute command {}: {}".format(command_id, exc))
    
    def closeEvent(self, event):
        """Handle application close event with error handling."""
        try:
            if hasattr(logger, 'info'):
                logger.info("Application closing...")
            
            # Save any pending data
            # TODO: Implement data saving
            
            # Clean up resources
            # TODO: Implement cleanup
            
            # Clean up quick switch widget
            if hasattr(self, 'quick_switch_widget') and self.quick_switch_widget:
                self.quick_switch_widget.cleanup()
            
            # Clean up quick switch menu
            if hasattr(self, 'quick_switch_menu') and self.quick_switch_menu:
                self.quick_switch_menu.cleanup()
            
            if hasattr(logger, 'info'):
                logger.info("Application closed successfully")
            event.accept()
            
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Error during application close: {}".format(exc))
            else:
                print("Error: Error during application close: {}".format(exc))
            event.accept()  # Still close the application

    def load_conversation_tags(self):
        """Load conversation tags with error handling."""
        try:
            # TODO: Load conversation tags from storage
            pass
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to load conversation tags: {}".format(exc))
            else:
                print("Error: Failed to load conversation tags: {}".format(exc)) 

    def show_last_read_markers(self):
        """Show the last read markers dialog with error handling."""
        try:
            if self.last_read_marker_dialog is None:
                # Create dialog with current conversation data
                conversation_data = self.get_conversation_data()
                self.last_read_marker_dialog = LastReadMarkerDialog(
                    self.last_read_marker, conversation_data, self
                )
                
                # Connect signals
                self.last_read_marker_dialog.marker_widget.conversation_selected.connect(
                    self.on_last_read_conversation_selected
                )
                self.last_read_marker_dialog.marker_widget.marker_updated.connect(
                    self.on_last_read_marker_updated
                )
            
            self.last_read_marker_dialog.show()
            self.last_read_marker_dialog.raise_()
            self.last_read_marker_dialog.activateWindow()
            
            if hasattr(logger, 'info'):
                logger.info("Last read markers dialog shown successfully")
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to show last read markers dialog: {}".format(exc))
            else:
                print("Error: Failed to show last read markers dialog: {}".format(exc))
    
    def on_last_read_conversation_selected(self, conversation_id: str):
        """Handle conversation selection from last read markers dialog."""
        try:
            # Load the selected conversation
            self.load_conversation(conversation_id)
            
            # Close the dialog
            if self.last_read_marker_dialog:
                self.last_read_marker_dialog.close()
                
            if hasattr(logger, 'info'):
                logger.info("Conversation selected from last read markers: {}".format(conversation_id))
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle last read conversation selection: {}".format(exc))
            else:
                print("Error: Failed to handle last read conversation selection: {}".format(exc))
    
    def on_last_read_marker_updated(self, conversation_id: str, message_id: str):
        """Handle marker updates from last read markers dialog."""
        try:
            # Update conversation list to reflect changes
            self.conversation_list.load_conversations()
            
            if hasattr(logger, 'debug'):
                logger.debug("Last read marker updated: {} -> {}".format(conversation_id, message_id))
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to handle last read marker update: {}".format(exc))
            else:
                print("Error: Failed to handle last read marker update: {}".format(exc))
    
    def get_conversation_data(self) -> Dict:
        """Get current conversation data for last read markers."""
        try:
            # TODO: Implement actual conversation data retrieval
            # For now, return sample data
            return {
                "conv_1": {
                    "title": "Sample Conversation 1",
                    "messages": [
                        {"id": "msg_001", "content": "First message"},
                        {"id": "msg_002", "content": "Second message"}
                    ]
                },
                "conv_2": {
                    "title": "Sample Conversation 2", 
                    "messages": [
                        {"id": "msg_003", "content": "Third message"}
                    ]
                }
            }
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to get conversation data: {}".format(exc))
            else:
                print("Error: Failed to get conversation data: {}".format(exc))
            return {}
    
    def mark_message_as_read(self, conversation_id: str, message_id: str):
        """Mark a message as read in the current conversation."""
        try:
            self.last_read_marker.mark_as_read(conversation_id, message_id)
            
            if hasattr(logger, 'debug'):
                logger.debug("Message marked as read: {} -> {}".format(conversation_id, message_id))
                
        except Exception as exc:
            if hasattr(logger, 'error'):
                logger.error("Failed to mark message as read: {}".format(exc))
            else:
                print("Error: Failed to mark message as read: {}".format(exc)) 

    def on_top_panel_toggled(self, is_open):
        """Update splitter geometry when top panel expands/contracts."""
        self.content_splitter.updateGeometry()
        self.content_splitter.repaint()
        self.centralWidget().updateGeometry()
        self.centralWidget().repaint()

    def show_api_settings(self):
        if self.api_settings_dialog is None:
            self.api_settings_dialog = APISettingsDialog(self, dark_theme=True)
        self.api_settings_dialog.show()
        self.api_settings_dialog.raise_()
        self.api_settings_dialog.activateWindow()

    def show_prompt_library(self):
        if self.prompt_library_dialog is None:
            self.prompt_library_dialog = PromptLibraryDialog(self, dark_theme=True)
        self.prompt_library_dialog.show()
        self.prompt_library_dialog.raise_()
        self.prompt_library_dialog.activateWindow()

    def show_prompt_template(self):
        if self.prompt_template_dialog is None:
            self.prompt_template_dialog = PromptTemplateDialog(self, dark_theme=True)
        self.prompt_template_dialog.show()
        self.prompt_template_dialog.raise_()
        self.prompt_template_dialog.activateWindow()

    def show_keyboard_shortcut_editor(self):
        if self.keyboard_shortcut_editor is None:
            self.keyboard_shortcut_editor = KeyboardShortcutEditor(self, dark_theme=True)
        self.keyboard_shortcut_editor.show()
        self.keyboard_shortcut_editor.raise_()
        self.keyboard_shortcut_editor.activateWindow()

    def show_system_prompt_editor(self):
        if self.system_prompt_dialog is None:
            self.system_prompt_dialog = SystemPromptDialog(parent=self, dark_theme=True)
        self.system_prompt_dialog.show()
        self.system_prompt_dialog.raise_()
        self.system_prompt_dialog.activateWindow()

    def show_model_settings(self):
        if self.model_settings_dialog is None:
            self.model_settings_dialog = ModelSettingsDialog(self, dark_theme=True)
        self.model_settings_dialog.show()
        self.model_settings_dialog.raise_()
        self.model_settings_dialog.activateWindow()
