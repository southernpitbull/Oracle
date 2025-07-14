#!/usr/bin/env python3
"""
Command Palette System
File: ui/command_palette.py

This module provides a comprehensive command palette system that allows users
to quickly access all application features through a searchable, categorized
interface with keyboard shortcuts and smart suggestions.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QDialog, QDialogButtonBox,
    QFormLayout, QMessageBox, QFrame, QGridLayout, QScrollArea,
    QFrame, QMessageBox, QMenu, QApplication, QMainWindow,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QTabWidget,
    QTextEdit, QSplitter, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon, QAction, QKeySequence

from utils.error_handler import error_handler, ErrorSeverity, ErrorCategory
from utils.dependencies import log as logger


class CommandCategory(Enum):
    """Categories for organizing commands."""
    FILE = "📁 File"
    EDIT = "✏️ Edit"
    VIEW = "👁️ View"
    TOOLS = "🔧 Tools"
    SETTINGS = "⚙️ Settings"
    HELP = "❓ Help"
    NAVIGATION = "🧭 Navigation"
    AI = "🤖 AI"
    CONVERSATION = "💬 Conversation"
    SEARCH = "🔍 Search"
    EXPORT = "📤 Export"
    IMPORT = "📥 Import"
    CUSTOM = "🎨 Custom"


@dataclass
class Command:
    """Represents a command in the palette."""
    id: str
    name: str
    description: str
    category: CommandCategory
    shortcut: Optional[str] = None
    icon: Optional[str] = None
    action: Optional[Callable] = None
    enabled: bool = True
    visible: bool = True
    usage_count: int = 0
    last_used: Optional[datetime] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        """Convert command to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'shortcut': self.shortcut,
            'icon': self.icon,
            'enabled': self.enabled,
            'visible': self.visible,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Command':
        """Create command from dictionary."""
        data['category'] = CommandCategory(data['category'])
        if data['last_used']:
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        return cls(**data)


class CommandPaletteManager:
    """Manages the command palette and command registry."""
    
    def __init__(self, storage_path: str = "data/command_palette.json"):
        self.storage_path = storage_path
        self.commands: Dict[str, Command] = {}
        self.categories: Dict[CommandCategory, List[str]] = {}
        self.search_history: List[str] = []
        self.load_commands()
        self.initialize_default_commands()
    
    def initialize_default_commands(self):
        """Initialize default commands if none exist."""
        if not self.commands:
            default_commands = [
                # File Commands
                Command(
                    id="new_conversation",
                    name="New Conversation",
                    description="Create a new conversation",
                    category=CommandCategory.FILE,
                    shortcut="Ctrl+N",
                    icon="🆕",
                    tags=["conversation", "new", "create"]
                ),
                Command(
                    id="open_conversation",
                    name="Open Conversation",
                    description="Open an existing conversation",
                    category=CommandCategory.FILE,
                    shortcut="Ctrl+O",
                    icon="📂",
                    tags=["conversation", "open", "load"]
                ),
                Command(
                    id="save_conversation",
                    name="Save Conversation",
                    description="Save current conversation",
                    category=CommandCategory.FILE,
                    shortcut="Ctrl+S",
                    icon="💾",
                    tags=["conversation", "save", "store"]
                ),
                Command(
                    id="export_conversation",
                    name="Export Conversation",
                    description="Export conversation to various formats",
                    category=CommandCategory.EXPORT,
                    shortcut="Ctrl+E",
                    icon="📤",
                    tags=["conversation", "export", "share"]
                ),
                
                # Edit Commands
                Command(
                    id="copy_text",
                    name="Copy Text",
                    description="Copy selected text to clipboard",
                    category=CommandCategory.EDIT,
                    shortcut="Ctrl+C",
                    icon="📋",
                    tags=["text", "copy", "clipboard"]
                ),
                Command(
                    id="paste_text",
                    name="Paste Text",
                    description="Paste text from clipboard",
                    category=CommandCategory.EDIT,
                    shortcut="Ctrl+V",
                    icon="📋",
                    tags=["text", "paste", "clipboard"]
                ),
                Command(
                    id="clear_chat",
                    name="Clear Chat",
                    description="Clear current conversation",
                    category=CommandCategory.EDIT,
                    shortcut="Ctrl+Shift+C",
                    icon="🗑️",
                    tags=["conversation", "clear", "reset"]
                ),
                
                # View Commands
                Command(
                    id="toggle_theme",
                    name="Toggle Theme",
                    description="Switch between light and dark themes",
                    category=CommandCategory.VIEW,
                    shortcut="Ctrl+T",
                    icon="🎨",
                    tags=["theme", "appearance", "dark", "light"]
                ),
                Command(
                    id="show_welcome_screen",
                    name="Show Welcome Screen",
                    description="Display the welcome screen",
                    category=CommandCategory.VIEW,
                    shortcut="Ctrl+W",
                    icon="🏠",
                    tags=["welcome", "home", "start"]
                ),
                
                # Tools Commands
                Command(
                    id="search_chat",
                    name="Search Chat",
                    description="Search within current conversation",
                    category=CommandCategory.SEARCH,
                    shortcut="Ctrl+F",
                    icon="🔍",
                    tags=["search", "find", "conversation"]
                ),
                Command(
                    id="attach_file",
                    name="Attach File",
                    description="Attach a file to the conversation",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+A",
                    icon="📎",
                    tags=["file", "attach", "upload"]
                ),
                Command(
                    id="tag_manager",
                    name="Tag Manager",
                    description="Manage conversation tags",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+T",
                    icon="🏷️",
                    tags=["tags", "organize", "categorize"]
                ),
                Command(
                    id="rag_toggle",
                    name="Toggle RAG",
                    description="Enable/disable RAG for prompts",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+R",
                    icon="🧠",
                    tags=["rag", "knowledge", "context"]
                ),
                Command(
                    id="knowledge_base",
                    name="Knowledge Base",
                    description="Manage document knowledge base",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+K",
                    icon="📚",
                    tags=["knowledge", "documents", "base"]
                ),
                Command(
                    id="summarize_chat",
                    name="Summarize Chat",
                    description="Generate conversation summary",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+S",
                    icon="📝",
                    tags=["summary", "conversation", "ai"]
                ),
                Command(
                    id="explain_regex",
                    name="Explain Regex Pattern",
                    description="Analyze and explain regex patterns",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+R",
                    icon="🔍",
                    tags=["regex", "pattern", "explain"]
                ),
                Command(
                    id="csv_to_markdown",
                    name="CSV to Markdown Table",
                    description="Convert CSV data to markdown table",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+M",
                    icon="📊",
                    tags=["csv", "markdown", "table", "convert"]
                ),
                Command(
                    id="prompt_history",
                    name="Prompt History",
                    description="Access recent prompts",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Up",
                    icon="📜",
                    tags=["prompt", "history", "recent"]
                ),
                Command(
                    id="quick_switch_model",
                    name="Quick Switch Model",
                    description="Rapidly switch between AI models",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+M",
                    icon="🔄",
                    tags=["model", "switch", "ai", "quick"]
                ),
                Command(
                    id="local_model_server",
                    name="Local Model Server",
                    description="Manage local AI models",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+L",
                    icon="🖥️",
                    tags=["local", "model", "server", "ollama"]
                ),
                Command(
                    id="auto_optimization",
                    name="Auto Optimization",
                    description="Optimize model performance",
                    category=CommandCategory.TOOLS,
                    shortcut="Ctrl+Shift+O",
                    icon="⚡",
                    tags=["optimization", "performance", "auto"]
                ),
                
                # Settings Commands
                Command(
                    id="api_settings",
                    name="API Settings",
                    description="Configure AI provider API keys",
                    category=CommandCategory.SETTINGS,
                    shortcut="Ctrl+,",
                    icon="🔑",
                    tags=["api", "settings", "keys", "configure"]
                ),
                Command(
                    id="keyboard_shortcuts",
                    name="Keyboard Shortcuts",
                    description="Customize hotkeys",
                    category=CommandCategory.SETTINGS,
                    shortcut="Ctrl+Shift+K",
                    icon="⌨️",
                    tags=["shortcuts", "keyboard", "hotkeys"]
                ),
                
                # Help Commands
                Command(
                    id="about",
                    name="About The Oracle",
                    description="Application information",
                    category=CommandCategory.HELP,
                    shortcut="F1",
                    icon="ℹ️",
                    tags=["about", "info", "help"]
                ),
                
                # Navigation Commands
                Command(
                    id="focus_chat",
                    name="Focus Chat Input",
                    description="Focus on the chat input area",
                    category=CommandCategory.NAVIGATION,
                    shortcut="Ctrl+L",
                    icon="💬",
                    tags=["focus", "chat", "input", "navigate"]
                ),
                Command(
                    id="next_conversation",
                    name="Next Conversation",
                    description="Switch to next conversation",
                    category=CommandCategory.NAVIGATION,
                    shortcut="Ctrl+Tab",
                    icon="➡️",
                    tags=["next", "conversation", "switch"]
                ),
                Command(
                    id="previous_conversation",
                    name="Previous Conversation",
                    description="Switch to previous conversation",
                    category=CommandCategory.NAVIGATION,
                    shortcut="Ctrl+Shift+Tab",
                    icon="⬅️",
                    tags=["previous", "conversation", "switch"]
                ),
                
                # AI Commands
                Command(
                    id="regenerate_response",
                    name="Regenerate Response",
                    description="Regenerate the last AI response",
                    category=CommandCategory.AI,
                    shortcut="Ctrl+Shift+R",
                    icon="🔄",
                    tags=["ai", "regenerate", "response"]
                ),
                Command(
                    id="stop_generation",
                    name="Stop Generation",
                    description="Stop current AI response generation",
                    category=CommandCategory.AI,
                    shortcut="Ctrl+.",
                    icon="⏹️",
                    tags=["ai", "stop", "generation"]
                ),
            ]
            
            for command in default_commands:
                self.register_command(command)
    
    def register_command(self, command: Command):
        """Register a new command."""
        self.commands[command.id] = command
        
        # Add to category
        if command.category not in self.categories:
            self.categories[command.category] = []
        self.categories[command.category].append(command.id)
        
        if hasattr(logger, 'debug'):
            logger.debug("Registered command: {} ({})".format(command.name, command.id))
    
    def unregister_command(self, command_id: str):
        """Unregister a command."""
        if command_id in self.commands:
            command = self.commands[command_id]
            
            # Remove from category
            if command.category in self.categories:
                self.categories[command.category].remove(command_id)
            
            del self.commands[command_id]
            
            if hasattr(logger, 'debug'):
                logger.debug("Unregistered command: {} ({})".format(command.name, command_id))
    
    def get_command(self, command_id: str) -> Optional[Command]:
        """Get a command by ID."""
        return self.commands.get(command_id)
    
    def search_commands(self, query: str) -> List[Command]:
        """Search commands by name, description, or tags."""
        if not query.strip():
            return list(self.commands.values())
        
        query = query.lower()
        results = []
        
        for command in self.commands.values():
            if not command.visible:
                continue
            
            # Search in name
            if query in command.name.lower():
                results.append(command)
                continue
            
            # Search in description
            if query in command.description.lower():
                results.append(command)
                continue
            
            # Search in tags
            if any(query in tag.lower() for tag in command.tags):
                results.append(command)
                continue
        
        # Sort by relevance (exact matches first, then usage count)
        results.sort(key=lambda cmd: (
            query not in cmd.name.lower(),  # Exact name matches first
            -cmd.usage_count,  # Higher usage count first
            cmd.name.lower()  # Alphabetical
        ))
        
        return results
    
    def get_commands_by_category(self, category: CommandCategory) -> List[Command]:
        """Get all commands in a category."""
        if category not in self.categories:
            return []
        
        return [self.commands[cmd_id] for cmd_id in self.categories[category] 
                if cmd_id in self.commands and self.commands[cmd_id].visible]
    
    def execute_command(self, command_id: str, *args, **kwargs) -> bool:
        """Execute a command."""
        command = self.get_command(command_id)
        if not command or not command.enabled:
            return False
        
        try:
            if command.action:
                command.action(*args, **kwargs)
            
            # Update usage statistics
            command.usage_count += 1
            command.last_used = datetime.now()
            
            # Add to search history
            if command.name not in self.search_history:
                self.search_history.append(command.name)
                if len(self.search_history) > 50:  # Keep last 50
                    self.search_history.pop(0)
            
            self.save_commands()
            
            if hasattr(logger, 'info'):
                logger.info("Executed command: {} ({})".format(command.name, command_id))
            
            return True
            
        except Exception as e:
            if hasattr(logger, 'error'):
                logger.error("Failed to execute command {}: {}".format(command_id, e))
            return False
    
    def get_recent_commands(self, limit: int = 10) -> List[Command]:
        """Get recently used commands."""
        commands = [cmd for cmd in self.commands.values() if cmd.last_used]
        commands.sort(key=lambda cmd: cmd.last_used, reverse=True)
        return commands[:limit]
    
    def get_popular_commands(self, limit: int = 10) -> List[Command]:
        """Get most frequently used commands."""
        commands = list(self.commands.values())
        commands.sort(key=lambda cmd: cmd.usage_count, reverse=True)
        return commands[:limit]
    
    def load_commands(self):
        """Load commands from storage."""
        try:
            if os.path.exists(self.storage_path):
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load commands
                for cmd_data in data.get('commands', []):
                    command = Command.from_dict(cmd_data)
                    self.commands[command.id] = command
                
                # Load categories
                for category_name, cmd_ids in data.get('categories', {}).items():
                    try:
                        category = CommandCategory(category_name)
                        self.categories[category] = cmd_ids
                    except ValueError:
                        continue
                
                # Load search history
                self.search_history = data.get('search_history', [])
                
                if hasattr(logger, 'info'):
                    logger.info("Loaded {} commands from storage".format(len(self.commands)))
            
        except Exception as e:
            if hasattr(logger, 'error'):
                logger.error("Failed to load commands: {}".format(e))
    
    def save_commands(self):
        """Save commands to storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            data = {
                'commands': [cmd.to_dict() for cmd in self.commands.values()],
                'categories': {
                    category.value: cmd_ids 
                    for category, cmd_ids in self.categories.items()
                },
                'search_history': self.search_history
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            if hasattr(logger, 'debug'):
                logger.debug("Saved {} commands to storage".format(len(self.commands)))
            
        except Exception as e:
            if hasattr(logger, 'error'):
                logger.error("Failed to save commands: {}".format(e))


class CommandItemWidget(QWidget):
    """Widget for displaying a command in the list."""
    
    command_clicked = pyqtSignal(str)  # command_id
    
    def __init__(self, command: Command, parent=None):
        super().__init__(parent)
        self.command = command
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the command item widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Icon
        if self.command.icon:
            icon_label = QLabel(self.command.icon)
            icon_label.setFixedSize(20, 20)
            icon_label.setStyleSheet("font-size: 16px;")
            layout.addWidget(icon_label)
        
        # Command info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Name
        name_label = QLabel(self.command.name)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(name_label)
        
        # Description
        desc_label = QLabel(self.command.description)
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setStyleSheet("color: #888888;")
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Shortcut
        if self.command.shortcut:
            shortcut_label = QLabel(self.command.shortcut)
            shortcut_label.setFont(QFont("Segoe UI", 8))
            shortcut_label.setStyleSheet("""
                color: #666666;
                background: #2a2a2a;
                padding: 2px 6px;
                border-radius: 4px;
                border: 1px solid #444444;
            """)
            layout.addWidget(shortcut_label)
        
        # Set widget style
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
        """)
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = self.on_click
    
    def on_click(self, event):
        """Handle widget click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.command_clicked.emit(self.command.id)


class CommandPaletteDialog(QDialog):
    """Main command palette dialog."""
    
    command_executed = pyqtSignal(str)  # command_id
    
    def __init__(self, command_manager: CommandPaletteManager, parent=None):
        super().__init__(parent)
        self.command_manager = command_manager
        self.setup_ui()
        self.setup_shortcuts()
        self.refresh_commands()
    
    def setup_ui(self):
        """Set up the command palette UI."""
        self.setWindowTitle("Command Palette")
        self.setModal(False)
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background: #2b2b2b;
                border: 2px solid #555555;
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🎯 Command Palette")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ff6b6b;
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #ff5252;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search commands... (Type to filter)")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #3a3a3a;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_commands)
        layout.addWidget(self.search_edit)
        
        # Category filter
        category_layout = QHBoxLayout()
        
        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        for category in CommandCategory:
            self.category_combo.addItem(category.value, category)
        self.category_combo.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.category_combo.currentTextChanged.connect(self.filter_commands)
        category_layout.addWidget(self.category_combo)
        
        category_layout.addStretch()
        layout.addLayout(category_layout)
        
        # Commands list
        self.commands_list = QListWidget()
        self.commands_list.setStyleSheet("""
            QListWidget {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
                color: white;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background: #0078d4;
            }
            QListWidget::item:hover {
                background: #3a3a3a;
            }
        """)
        self.commands_list.itemClicked.connect(self.on_command_selected)
        self.commands_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.commands_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.commands_list)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Focus on search box
        self.search_edit.setFocus()
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Escape to close
        escape_shortcut = QAction(self)
        escape_shortcut.setShortcut(QKeySequence("Escape"))
        escape_shortcut.triggered.connect(self.close)
        self.addAction(escape_shortcut)
        
        # Enter to execute selected command
        enter_shortcut = QAction(self)
        enter_shortcut.setShortcut(QKeySequence("Return"))
        enter_shortcut.triggered.connect(self.execute_selected_command)
        self.addAction(enter_shortcut)
        
        # Up/Down for navigation
        up_shortcut = QAction(self)
        up_shortcut.setShortcut(QKeySequence("Up"))
        up_shortcut.triggered.connect(self.navigate_up)
        self.addAction(up_shortcut)
        
        down_shortcut = QAction(self)
        down_shortcut.setShortcut(QKeySequence("Down"))
        down_shortcut.triggered.connect(self.navigate_down)
        self.addAction(down_shortcut)
    
    def refresh_commands(self):
        """Refresh the commands list."""
        self.commands_list.clear()
        
        # Get all visible commands
        commands = [cmd for cmd in self.commands_manager.commands.values() if cmd.visible]
        
        # Sort by usage count and name
        commands.sort(key=lambda cmd: (-cmd.usage_count, cmd.name.lower()))
        
        for command in commands:
            item = QListWidgetItem()
            
            # Create command widget
            command_widget = CommandItemWidget(command)
            command_widget.command_clicked.connect(self.execute_command)
            
            # Set item widget
            item.setSizeHint(command_widget.sizeHint())
            self.commands_list.addItem(item)
            self.commands_list.setItemWidget(item, command_widget)
        
        self.update_status()
    
    def filter_commands(self):
        """Filter commands based on search query and category."""
        query = self.search_edit.text().strip()
        selected_category = self.category_combo.currentData()
        
        # Hide all items first
        for i in range(self.commands_list.count()):
            item = self.commands_list.item(i)
            command_widget = self.commands_list.itemWidget(item)
            
            if not command_widget:
                continue
            
            command = command_widget.command
            
            # Check if command matches filters
            matches = True
            
            # Category filter
            if selected_category and command.category != selected_category:
                matches = False
            
            # Search filter
            if query:
                query_lower = query.lower()
                name_match = query_lower in command.name.lower()
                desc_match = query_lower in command.description.lower()
                tag_match = any(query_lower in tag.lower() for tag in command.tags)
                
                if not (name_match or desc_match or tag_match):
                    matches = False
            
            # Show/hide item
            item.setHidden(not matches)
        
        self.update_status()
    
    def update_status(self):
        """Update status bar with current information."""
        visible_count = 0
        for i in range(self.commands_list.count()):
            if not self.commands_list.item(i).isHidden():
                visible_count += 1
        
        total_count = len(self.commands_manager.commands)
        self.status_label.setText(f"Showing {visible_count} of {total_count} commands")
    
    def on_command_selected(self, item: QListWidgetItem):
        """Handle command selection."""
        command_widget = self.commands_list.itemWidget(item)
        if command_widget:
            self.execute_command(command_widget.command.id)
    
    def execute_selected_command(self):
        """Execute the currently selected command."""
        current_item = self.commands_list.currentItem()
        if current_item:
            command_widget = self.commands_list.itemWidget(current_item)
            if command_widget:
                self.execute_command(command_widget.command.id)
    
    def execute_command(self, command_id: str):
        """Execute a command."""
        success = self.commands_manager.execute_command(command_id)
        if success:
            self.command_executed.emit(command_id)
            self.close()
        else:
            # Show error in status
            self.status_label.setText(f"Failed to execute command: {command_id}")
            self.status_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
    
    def navigate_up(self):
        """Navigate to previous command."""
        current_row = self.commands_list.currentRow()
        if current_row > 0:
            self.commands_list.setCurrentRow(current_row - 1)
    
    def navigate_down(self):
        """Navigate to next command."""
        current_row = self.commands_list.currentRow()
        if current_row < self.commands_list.count() - 1:
            self.commands_list.setCurrentRow(current_row + 1)
    
    def show_context_menu(self, position):
        """Show context menu for commands."""
        item = self.commands_list.itemAt(position)
        if not item:
            return
        
        command_widget = self.commands_list.itemWidget(item)
        if not command_widget:
            return
        
        command = command_widget.command
        
        menu = QMenu(self)
        
        # Execute action
        execute_action = QAction("▶️ Execute", self)
        execute_action.triggered.connect(lambda: self.execute_command(command.id))
        menu.addAction(execute_action)
        
        # Show details action
        details_action = QAction("ℹ️ Show Details", self)
        details_action.triggered.connect(lambda: self.show_command_details(command))
        menu.addAction(details_action)
        
        menu.exec(self.commands_list.mapToGlobal(position))
    
    def show_command_details(self, command: Command):
        """Show detailed information about a command."""
        details_dialog = QDialog(self)
        details_dialog.setWindowTitle(f"Command Details: {command.name}")
        details_dialog.setModal(True)
        details_dialog.setFixedSize(400, 300)
        details_dialog.setStyleSheet("""
            QDialog {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(details_dialog)
        
        # Command info
        info_text = f"""
        <h3>{command.name}</h3>
        <p><b>Description:</b> {command.description}</p>
        <p><b>Category:</b> {command.category.value}</p>
        <p><b>Shortcut:</b> {command.shortcut or 'None'}</p>
        <p><b>Usage Count:</b> {command.usage_count}</p>
        <p><b>Last Used:</b> {command.last_used.strftime('%Y-%m-%d %H:%M:%S') if command.last_used else 'Never'}</p>
        <p><b>Tags:</b> {', '.join(command.tags) if command.tags else 'None'}</p>
        """
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: white; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(details_dialog.accept)
        layout.addWidget(close_btn)
        
        details_dialog.exec()


class CommandPaletteWidget(QWidget):
    """Widget for embedding command palette in other dialogs."""
    
    command_executed = pyqtSignal(str)  # command_id
    
    def __init__(self, command_manager: CommandPaletteManager, parent=None):
        super().__init__(parent)
        self.command_manager = command_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the embedded command palette UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search commands...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_commands)
        layout.addWidget(self.search_edit)
        
        # Commands list
        self.commands_list = QListWidget()
        self.commands_list.setStyleSheet("""
            QListWidget {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 6px;
                color: white;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background: #0078d4;
            }
            QListWidget::item:hover {
                background: #3a3a3a;
            }
        """)
        self.commands_list.itemClicked.connect(self.on_command_selected)
        layout.addWidget(self.commands_list)
        
        self.refresh_commands()
    
    def refresh_commands(self):
        """Refresh the commands list."""
        self.commands_list.clear()
        
        commands = [cmd for cmd in self.commands_manager.commands.values() if cmd.visible]
        commands.sort(key=lambda cmd: (-cmd.usage_count, cmd.name.lower()))
        
        for command in commands:
            item = QListWidgetItem()
            command_widget = CommandItemWidget(command)
            command_widget.command_clicked.connect(self.execute_command)
            item.setSizeHint(command_widget.sizeHint())
            self.commands_list.addItem(item)
            self.commands_list.setItemWidget(item, command_widget)
    
    def filter_commands(self):
        """Filter commands based on search query."""
        query = self.search_edit.text().strip()
        
        for i in range(self.commands_list.count()):
            item = self.commands_list.item(i)
            command_widget = self.commands_list.itemWidget(item)
            
            if not command_widget:
                continue
            
            command = command_widget.command
            
            if query:
                query_lower = query.lower()
                name_match = query_lower in command.name.lower()
                desc_match = query_lower in command.description.lower()
                tag_match = any(query_lower in tag.lower() for tag in command.tags)
                
                item.setHidden(not (name_match or desc_match or tag_match))
            else:
                item.setHidden(False)
    
    def on_command_selected(self, item: QListWidgetItem):
        """Handle command selection."""
        command_widget = self.commands_list.itemWidget(item)
        if command_widget:
            self.execute_command(command_widget.command.id)
    
    def execute_command(self, command_id: str):
        """Execute a command."""
        success = self.commands_manager.execute_command(command_id)
        if success:
            self.command_executed.emit(command_id) 
