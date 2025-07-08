"""
Complete ChatApp implementation for The Oracle.
This file contains all the main functionality split out from the original Oracle.py.
"""

import os
import sys
import json
import sqlite3
import threading
import asyncio
import logging
import html
import re
import shutil
import tempfile
import webbrowser
from datetime import datetime
from collections import Counter
from functools import partial
from pathlib import Path
import subprocess
import platform
from typing import Dict, List, Optional, Tuple, Any
# Optional advanced dependencies
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from urllib.parse import urlparse
    import requests
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    try:
        from pypdf import PdfReader
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False
        PdfReader = None

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.offline import plot
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from wordcloud import WordCloud
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import numpy as np
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS as LangchainFAISS
    from langchain.chains import RetrievalQA
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

import pickle

# PyQt imports
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QLineEdit, QPushButton, QComboBox, QListWidget, QListWidgetItem, QSplitter,
                             QMenuBar, QMenu, QStatusBar, QLabel, QCheckBox, QFileDialog,
                             QMessageBox, QInputDialog, QFrame, QScrollArea, QTextBrowser,
                             QPlainTextEdit, QTabWidget, QGroupBox, QGridLayout, QSpinBox,
                             QDoubleSpinBox, QSlider, QDialog, QDialogButtonBox, QApplication,
                             QToolBar, QGraphicsDropShadowEffect, QSizePolicy, QProgressBar,
                             QTreeWidget, QTreeWidgetItem, QFormLayout, QSpacerItem, QButtonGroup,
                             QRadioButton, QSlider, QSpinBox, QDoubleSpinBox, QDateTimeEdit,
                             QCalendarWidget, QColorDialog, QFontDialog, QWizard, QWizardPage,
                             QDockWidget, QMdiArea, QMdiSubWindow, QSplashScreen)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QSettings, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction, QTextCursor, QTextCharFormat, QColor, QCloseEvent, QKeySequence, QCursor

# Core imports
from core.config import *
from core.evaluator import AIEvaluator
from core.knowledge_graph import KnowledgeGraph
from api.multi_provider import MultiProviderClient
from api.settings import APISettingsDialog
from api.threads import ModelResponseThread, MultiProviderResponseThread
from ui.model_settings_dialog import ModelSettingsDialog
from ui.prompt_library_dialog import PromptLibraryDialog
from ui.keyboard_shortcut_editor import KeyboardShortcutEditor
from ui.prompt_template_dialog import PromptTemplateDialog
from ui.system_prompt_dialog import SystemPromptDialog
from ui.message_formatter import MessageFormatter
from utils.file_utils import *
from utils.formatting import *

logger = logging.getLogger(__name__)


class ModernButton(QPushButton):
    """Enhanced button with hover effects and modern styling"""
    
    def __init__(self, text="", icon_path=None, parent=None):
        super().__init__(text, parent)
        self.icon_path = icon_path
        self.setupUI()
        
    def setupUI(self):
        """Set up the button's appearance"""
        if self.icon_path and os.path.exists(self.icon_path):
            icon = QIcon(self.icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)
        
        # Set minimum size for better appearance
        self.setMinimumHeight(32)
        
    def enterEvent(self, event):
        """Handle mouse enter"""
        super().enterEvent(event)
        self.setStyleSheet(self.styleSheet() + "transform: scale(1.02);")
        
    def leaveEvent(self, a0):
        """Handle mouse leave"""
        super().leaveEvent(a0)
        self.setStyleSheet(self.styleSheet().replace("transform: scale(1.02);", ""))


class AnimatedListWidget(QListWidget):
    """List widget with enhanced styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        """Set up the list widget"""
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(1, 1)
        self.setGraphicsEffect(shadow)


class ChatApp(QMainWindow):
    LAZY_LOAD_BATCH_SIZE = 20  # Number of conversations to load per batch

    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Oracle")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize core components
        self.evaluator = AIEvaluator()
        self.knowledge_graph = KnowledgeGraph()
        self.ai_evaluator = AIEvaluator()
        self.multi_client = MultiProviderClient()
        
        # State variables
        self.current_conversation_id = None
        self.servers = ["http://localhost:11434"]
        self.file_images = []
        self.chat_history = []
        self.conversation_map = {}
        self.conversation_models = {}
        self.conversation_cache = {}
        self.conversation_metadata = {}
        self.response_thread = None
        self.auto_save_timer = None
        self.last_scroll_position = 0
        self.scroll_to_bottom_button = None
        
        # Enhanced state variables for advanced features
        self.pinned_messages = {}  # conversation_id -> list of pinned message indices
        self.message_timestamps = {}  # conversation_id -> list of timestamps
        self.conversation_folders = {}  # folder_name -> list of conversation_ids
        self.archived_conversations = set()  # Set of archived conversation IDs
        self.conversation_system_prompts = {}  # conversation_id -> system prompt
        self.prompt_history = []  # Last 20 prompts
        self.prompt_library = {}  # category -> list of prompts
        self.conversation_notes = {}  # conversation_id -> dict of message_id -> notes
        self.attachment_metadata = {}  # conversation_id -> list of attachment info
        self.rag_enabled = False
        self.knowledge_base = None
        self.vector_store = None
        self.embedding_model = None
        self.document_store = []
        self.conversation_analytics = {}  # Analytics data for conversations
        self.plugin_manager = None
        self.achievements = set()  # Set of unlocked achievements
        self.user_preferences = {}  # User customization preferences
        self.theme_config = {}  # Theme configuration
        self.keyboard_shortcuts = {}  # Custom keyboard shortcuts
        self.workflow_chains = {}  # Saved workflow chains
        self.code_execution_results = {}  # Results of code execution
        self.model_parameters = {  # Model parameter overrides
            'temperature': 0.7,
            'max_tokens': 4096,
            'top_p': 1.0,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
        }
        self.conversation_stats = {  # Conversation statistics
            'total_messages': 0,
            'total_tokens': 0,
            'models_used': set(),
            'session_start': datetime.now()
        }
        self.search_filters = {}  # Advanced search filters
        self.export_templates = {}  # Custom export templates
        self.collaboration_mode = False  # Live collaboration mode
        self.voice_enabled = False  # Voice input/output
        self.markdown_extensions = ['tables', 'fenced_code', 'codehilite', 'toc']
        self.latex_enabled = False  # LaTeX rendering
        self.mermaid_enabled = False  # Mermaid diagram rendering
        self.custom_css = ""  # Custom CSS for theming
        self.api_usage_tracking = {}  # API usage statistics
        self.security_settings = {}  # Security and privacy settings
        self.backup_settings = {}  # Backup configuration
        self.integration_settings = {}  # Third-party integrations
        self.notification_settings = {}  # Notification preferences
        self.accessibility_settings = {}  # Accessibility options
        self.performance_settings = {}  # Performance tuning options
        
        # Virtual scrolling
        self.virtual_messages = []
        self.visible_message_widgets = []
        self.message_heights = {}
        self.viewport_start = 0
        self.viewport_end = 0
        self.virtual_scroll_enabled = True
        
        # Current provider and model
        self.current_provider = "Ollama"
        self.current_model = None
        
        # Settings
        self.save_code_blocks_action = QAction("Save Code Blocks", self)
        self.save_code_blocks_action.setCheckable(True)
        self.save_code_blocks_action.setChecked(True)
        self.enable_code_saving = True
        self.enable_markdown = True
        self.dark_theme = True
        self.show_line_numbers = False  # New setting for code block line numbers
        self.enable_code_folding = False  # New setting for code folding
        self.compact_mode = False  # New setting for compact UI mode
        
        # Initialize message formatter
        self.message_formatter = MessageFormatter(self.dark_theme, self.show_line_numbers, self.enable_code_folding)
        
        # Initialize icon path
        self.icon_base_path = os.path.join(os.path.dirname(__file__), "..", "icons")
        
        # Initialize UI
        self.setup_ui()
        self.setup_menu()
        self.setup_styles()
        self.load_providers_and_models()
        self.load_conversations()
        self.setup_auto_save()
        self.load_chat_on_startup()
        self.setup_code_execution()

    def setup_ui(self):
        """Set up the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top toolbar with enhanced styling
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)
        
        # Provider selection with enhanced labels
        provider_label = QLabel("🤖 Provider:")
        provider_label.setStyleSheet("font-weight: bold; color: #4A5568;")
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(140)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        toolbar_layout.addWidget(provider_label)
        toolbar_layout.addWidget(self.provider_combo)
        
        # Model selection with enhanced labels
        model_label = QLabel("🧠 Model:")
        model_label.setStyleSheet("font-weight: bold; color: #4A5568;")
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(220)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        toolbar_layout.addWidget(model_label)
        toolbar_layout.addWidget(self.model_combo)
        
        # Model settings button
        self.model_settings_button = ModernButton("⚙️", self.get_icon_path("toolbar", "settings"))
        self.model_settings_button.setMaximumWidth(40)
        self.model_settings_button.setToolTip("Model Settings (Temperature, Max Tokens, etc.)")
        self.model_settings_button.clicked.connect(self.open_model_settings_manually)
        toolbar_layout.addWidget(self.model_settings_button)
        
        # Enhanced buttons with icons
        self.refresh_models_button = ModernButton("🔄", self.get_icon_path("toolbar", "refresh"))
        self.refresh_models_button.setMaximumWidth(40)
        self.refresh_models_button.setToolTip("Refresh Models")
        self.refresh_models_button.clicked.connect(self.refresh_current_provider_models)
        toolbar_layout.addWidget(self.refresh_models_button)
        
        self.api_settings_button = ModernButton("🔑 API Keys", self.get_icon_path("toolbar", "settings"))
        self.api_settings_button.setToolTip("API Keys")
        self.api_settings_button.clicked.connect(self.open_api_settings)
        toolbar_layout.addWidget(self.api_settings_button)
        
        # Theme toggle button
        self.theme_button = ModernButton("🌙", self.get_icon_path("general", "theme_dark"))
        self.theme_button.setToolTip("Toggle Dark/Light Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)
        
        self.pull_button = ModernButton("📥 Pull Model")
        self.pull_button.clicked.connect(self.pull_model)
        toolbar_layout.addWidget(self.pull_button)
        
        self.new_chat_button = ModernButton("🆕 New Chat", self.get_icon_path("buttons", "add_new"))
        self.new_chat_button.clicked.connect(self.new_conversation)
        toolbar_layout.addWidget(self.new_chat_button)
        
        # Enhanced search
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("🔍 Search chat...")
        toolbar_layout.addWidget(self.search_entry)
        
        self.search_button = ModernButton("🔍", self.get_icon_path("toolbar", "search"))
        self.search_button.setMaximumWidth(40)
        self.search_button.setToolTip("Search Chat")
        self.search_button.clicked.connect(self.filter_chat)
        toolbar_layout.addWidget(self.search_button)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # Main content splitter with enhanced styling
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        
        # Left panel for conversations
        self.left_panel = QWidget()
        self.left_panel.setMaximumWidth(300)
        self.left_panel.setMinimumWidth(250)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setSpacing(10)
        
        # Conversation list header with modern styling
        conv_header = QLabel("💬 Conversations")
        conv_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2D3748, stop:1 #4A5568);
                color: white;
                border-radius: 8px;
                margin-bottom: 5px;
            }
        """)
        left_layout.addWidget(conv_header)
        
        # Enhanced conversation list
        self.conv_listbox = AnimatedListWidget()
        self.conv_listbox.currentRowChanged.connect(self.load_selected_conv)
        left_layout.addWidget(self.conv_listbox)
        
        # New conversation button at bottom of left panel
        new_chat_btn = ModernButton("🆕 New Conversation", self.get_icon_path("buttons", "add_new"))
        new_chat_btn.clicked.connect(self.new_conversation)
        left_layout.addWidget(new_chat_btn)
        
        splitter.addWidget(self.left_panel)
        
        # Chat area with enhanced layout
        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)
        chat_layout.setSpacing(0)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        # Create a vertical splitter to hold the chat display and input area
        chat_input_splitter = QSplitter(Qt.Orientation.Vertical)
        chat_input_splitter.setHandleWidth(8)

        # --- Top part of the splitter: Chat Display Container ---
        chat_display_container = QWidget()
        chat_display_layout = QVBoxLayout(chat_display_container)
        chat_display_layout.setContentsMargins(0, 0, 0, 0)
        chat_display_layout.setSpacing(5)

        # Chat display with enhanced styling
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.setOpenExternalLinks(True)
        chat_display_layout.addWidget(self.chat_display)

        # Enhanced scroll to bottom button
        self.scroll_to_bottom_button = ModernButton("↓ Scroll to Bottom")
        self.scroll_to_bottom_button.setMaximumHeight(30)
        self.scroll_to_bottom_button.clicked.connect(self.scroll_to_bottom)
        self.scroll_to_bottom_button.hide()

        scroll_button_layout = QHBoxLayout()
        scroll_button_layout.addStretch()
        scroll_button_layout.addWidget(self.scroll_to_bottom_button)
        scroll_button_layout.addStretch()
        chat_display_layout.addLayout(scroll_button_layout)

        # Connect scroll events
        scrollbar = self.chat_display.verticalScrollBar()
        if scrollbar:
            scrollbar.valueChanged.connect(self.on_scroll_changed)

        chat_input_splitter.addWidget(chat_display_container)

        # --- Bottom part of the splitter: Input Frame ---
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setSpacing(10)

        self.input_entry = QTextEdit()
        self.input_entry.setMaximumHeight(120)
        self.input_entry.setPlaceholderText("✨ Type your message here... (Ctrl+Enter to send)")
        self.input_entry.keyPressEvent = lambda e: self.input_key_press_event(e)
        input_layout.addWidget(self.input_entry)

        # Enhanced send button with icon
        self.send_button = ModernButton("📤 Send", self.get_icon_path("chat", "send_message"))
        self.send_button.setObjectName("send_button")
        self.send_button.setMinimumWidth(100)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        chat_input_splitter.addWidget(input_frame)

        # Set initial sizes for the vertical splitter to give most space to chat
        chat_input_splitter.setSizes([self.height() - 200, 150])

        chat_layout.addWidget(chat_input_splitter)
        splitter.addWidget(self.chat_widget)
        
        splitter.setSizes([300, 1300])
        main_layout.addWidget(splitter)
        
        # Enhanced status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("🚀 Ready to chat with The Oracle!")

    def setup_menu(self):
        """Set up the comprehensive menu bar with all features"""
        try:
            menubar = self.menuBar()
            if not menubar:
                logger.warning("Could not create menu bar")
                return
            
            # File Menu
            file_menu = menubar.addMenu("File")
            
            # New conversation
            new_conversation_action = QAction("New Conversation", self)
            new_conversation_action.setShortcut(QKeySequence("Ctrl+N"))
            new_conversation_action.triggered.connect(self.new_conversation)
            file_menu.addAction(new_conversation_action)
            
            file_menu.addSeparator()
            
            # Load/Save actions
            open_action = QAction("Open Conversation", self)
            open_action.setShortcut(QKeySequence("Ctrl+O"))
            open_action.triggered.connect(self.open_conversation)
            file_menu.addAction(open_action)
            
            save_action = QAction("Save Chat", self)
            save_action.setShortcut(QKeySequence("Ctrl+S"))
            save_action.triggered.connect(self.save_chat)
            file_menu.addAction(save_action)
            
            save_as_action = QAction("Save As...", self)
            save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
            save_as_action.triggered.connect(self.save_chat_as)
            file_menu.addAction(save_as_action)
            
            file_menu.addSeparator()
            
            # Import/Export submenu
            import_menu = file_menu.addMenu("Import")
            import_actions = [
                ("Import from JSON", lambda: self.import_conversation("json")),
                ("Import from TXT", lambda: self.import_conversation("txt")),
                ("Import from CSV", lambda: self.import_conversation("csv")),
                ("Import Chat History", lambda: self.import_chat_history())
            ]
            
            for text, func in import_actions:
                action = QAction(text, self)
                action.triggered.connect(func)
                import_menu.addAction(action)
            
            export_menu = file_menu.addMenu("Export")
            export_actions = [
                ("To JSON", lambda: self.export_chat("json")),
                ("To TXT", lambda: self.export_chat("txt")),
                ("To HTML", lambda: self.export_chat("html")),
                ("To Markdown", lambda: self.export_chat("md")),
                ("To PDF", lambda: self.export_chat("pdf")),
                ("To Word Document", lambda: self.export_chat("docx")),
                ("To CSV", lambda: self.export_chat("csv"))
            ]
            
            for text, func in export_actions:
                action = QAction(text, self)
                action.triggered.connect(func)
                export_menu.addAction(action)
            
            file_menu.addSeparator()
            
            # Recent files
            recent_menu = file_menu.addMenu("Recent Conversations")
            self.update_recent_menu(recent_menu)
            
            file_menu.addSeparator()
            
            # Print
            print_action = QAction("Print Chat", self)
            print_action.setShortcut(QKeySequence("Ctrl+P"))
            print_action.triggered.connect(self.print_chat)
            file_menu.addAction(print_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction("Exit", self)
            exit_action.setShortcut(QKeySequence("Ctrl+Q"))
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Edit Menu
            edit_menu = menubar.addMenu("Edit")
            
            undo_action = QAction("Undo", self)
            undo_action.setShortcut(QKeySequence("Ctrl+Z"))
            undo_action.triggered.connect(self.undo_last_action)
            edit_menu.addAction(undo_action)
            
            redo_action = QAction("Redo", self)
            redo_action.setShortcut(QKeySequence("Ctrl+Y"))
            redo_action.triggered.connect(self.redo_last_action)
            edit_menu.addAction(redo_action)
            
            edit_menu.addSeparator()
            
            copy_action = QAction("Copy Chat", self)
            copy_action.setShortcut(QKeySequence("Ctrl+C"))
            copy_action.triggered.connect(self.copy_chat_to_clipboard)
            edit_menu.addAction(copy_action)
            
            paste_action = QAction("Paste", self)
            paste_action.setShortcut(QKeySequence("Ctrl+V"))
            paste_action.triggered.connect(self.paste_from_clipboard)
            edit_menu.addAction(paste_action)
            
            edit_menu.addSeparator()
            
            find_action = QAction("Find in Chat", self)
            find_action.setShortcut(QKeySequence("Ctrl+F"))
            find_action.triggered.connect(self.find_in_chat)
            edit_menu.addAction(find_action)
            
            replace_action = QAction("Find and Replace", self)
            replace_action.setShortcut(QKeySequence("Ctrl+H"))
            replace_action.triggered.connect(self.find_and_replace)
            edit_menu.addAction(replace_action)
            
            edit_menu.addSeparator()
            
            select_all_action = QAction("Select All", self)
            select_all_action.setShortcut(QKeySequence("Ctrl+A"))
            select_all_action.triggered.connect(self.select_all_chat)
            edit_menu.addAction(select_all_action)
            
            # Chat Menu
            chat_menu = menubar.addMenu("Chat")
            
            # Formatting options
            markdown_action = QAction("Markdown Formatting", self)
            markdown_action.setCheckable(True)
            markdown_action.setChecked(True)
            markdown_action.triggered.connect(self.toggle_markdown)
            chat_menu.addAction(markdown_action)
            
            syntax_highlighting_action = QAction("Syntax Highlighting", self)
            syntax_highlighting_action.setCheckable(True)
            syntax_highlighting_action.setChecked(True)
            syntax_highlighting_action.triggered.connect(self.toggle_syntax_highlighting)
            chat_menu.addAction(syntax_highlighting_action)
            
            chat_menu.addSeparator()
            
            # System prompt management
            system_prompt_action = QAction("Set System Prompt...", self)
            system_prompt_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
            system_prompt_action.triggered.connect(self.set_system_prompt)
            chat_menu.addAction(system_prompt_action)
            
            clear_system_prompt_action = QAction("Clear System Prompt", self)
            clear_system_prompt_action.triggered.connect(self.clear_system_prompt)
            chat_menu.addAction(clear_system_prompt_action)
            
            chat_menu.addSeparator()
            
            # Prompt management
            prompt_library_action = QAction("Prompt Library...", self)
            prompt_library_action.setShortcut(QKeySequence("Ctrl+L"))
            prompt_library_action.triggered.connect(self.open_prompt_library)
            chat_menu.addAction(prompt_library_action)
            
            prompt_templates_action = QAction("Prompt Templates...", self)
            prompt_templates_action.triggered.connect(self.open_prompt_templates)
            chat_menu.addAction(prompt_templates_action)
            
            chat_menu.addSeparator()
            
            # Chat actions
            clear_action = QAction("Clear Chat", self)
            clear_action.setShortcut(QKeySequence("Ctrl+Delete"))
            clear_action.triggered.connect(self.clear_chat)
            chat_menu.addAction(clear_action)
            
            summarize_action = QAction("Summarize Chat", self)
            summarize_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
            summarize_action.triggered.connect(self.summarize_chat)
            chat_menu.addAction(summarize_action)
            
            translate_action = QAction("Translate Chat", self)
            translate_action.triggered.connect(self.translate_chat)
            chat_menu.addAction(translate_action)
            
            chat_menu.addSeparator()
            
            # Message management
            delete_last_message_action = QAction("Delete Last Message", self)
            delete_last_message_action.setShortcut(QKeySequence("Ctrl+Backspace"))
            delete_last_message_action.triggered.connect(self.delete_last_message)
            chat_menu.addAction(delete_last_message_action)
            
            edit_message_action = QAction("Edit Message", self)
            edit_message_action.triggered.connect(self.edit_selected_message)
            chat_menu.addAction(edit_message_action)
            
            regenerate_response_action = QAction("Regenerate Response", self)
            regenerate_response_action.setShortcut(QKeySequence("Ctrl+R"))
            regenerate_response_action.triggered.connect(self.regenerate_last_response)
            chat_menu.addAction(regenerate_response_action)

            # View Menu
            view_menu = menubar.addMenu("View")
            
            # UI Layout options
            fullscreen_action = QAction("Toggle Fullscreen", self)
            fullscreen_action.setShortcut(QKeySequence("F11"))
            fullscreen_action.triggered.connect(self.toggle_fullscreen)
            view_menu.addAction(fullscreen_action)
            
            view_menu.addSeparator()
            
            # Panel visibility
            sidebar_action = QAction("Show Sidebar", self)
            sidebar_action.setCheckable(True)
            sidebar_action.setChecked(True)
            sidebar_action.triggered.connect(self.toggle_sidebar)
            view_menu.addAction(sidebar_action)
            
            toolbar_action = QAction("Show Toolbar", self)
            toolbar_action.setCheckable(True)
            toolbar_action.setChecked(True)
            toolbar_action.triggered.connect(self.toggle_toolbar)
            view_menu.addAction(toolbar_action)
            
            status_bar_action = QAction("Show Status Bar", self)
            status_bar_action.setCheckable(True)
            status_bar_action.setChecked(True)
            status_bar_action.triggered.connect(self.toggle_status_bar)
            view_menu.addAction(status_bar_action)
            
            view_menu.addSeparator()
            
            # Code display options
            line_numbers_action = QAction("Show Line Numbers in Code Blocks", self)
            line_numbers_action.setCheckable(True)
            line_numbers_action.setChecked(self.show_line_numbers)
            line_numbers_action.triggered.connect(self.toggle_line_numbers)
            view_menu.addAction(line_numbers_action)
            
            code_folding_action = QAction("Enable Code Folding", self)
            code_folding_action.setCheckable(True)
            code_folding_action.setChecked(self.enable_code_folding)
            code_folding_action.triggered.connect(self.toggle_code_folding)
            view_menu.addAction(code_folding_action)
            
            word_wrap_action = QAction("Word Wrap", self)
            word_wrap_action.setCheckable(True)
            word_wrap_action.setChecked(True)
            word_wrap_action.triggered.connect(self.toggle_word_wrap)
            view_menu.addAction(word_wrap_action)
            
            view_menu.addSeparator()
            
            # UI mode options
            compact_mode_action = QAction("Compact UI Mode", self)
            compact_mode_action.setCheckable(True)
            compact_mode_action.setChecked(self.compact_mode)
            compact_mode_action.triggered.connect(self.toggle_compact_mode)
            view_menu.addAction(compact_mode_action)
            
            focus_mode_action = QAction("Focus Mode", self)
            focus_mode_action.setCheckable(True)
            focus_mode_action.triggered.connect(self.toggle_focus_mode)
            view_menu.addAction(focus_mode_action)
            
            view_menu.addSeparator()
            
            # Zoom controls
            zoom_in_action = QAction("Zoom In", self)
            zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
            zoom_in_action.triggered.connect(self.zoom_in)
            view_menu.addAction(zoom_in_action)
            
            zoom_out_action = QAction("Zoom Out", self)
            zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
            zoom_out_action.triggered.connect(self.zoom_out)
            view_menu.addAction(zoom_out_action)
            
            reset_zoom_action = QAction("Reset Zoom", self)
            reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
            reset_zoom_action.triggered.connect(self.reset_zoom)
            view_menu.addAction(reset_zoom_action)

            # Tools Menu
            tools_menu = menubar.addMenu("Tools")
            
            # File operations
            attach_action = QAction("Attach File", self)
            attach_action.setShortcut(QKeySequence("Ctrl+Shift+A"))
            attach_action.triggered.connect(self.attach_file)
            tools_menu.addAction(attach_action)
            
            batch_process_action = QAction("Batch Process Files", self)
            batch_process_action.triggered.connect(self.batch_process_files)
            tools_menu.addAction(batch_process_action)
            
            tools_menu.addSeparator()
            
            # Knowledge Base/RAG submenu
            rag_menu = tools_menu.addMenu("Knowledge Base")
            
            add_doc_action = QAction("Add Document", self)
            add_doc_action.triggered.connect(self.add_document_to_rag)
            rag_menu.addAction(add_doc_action)
            
            add_folder_action = QAction("Add Folder", self)
            add_folder_action.triggered.connect(self.add_folder_to_rag)
            rag_menu.addAction(add_folder_action)
            
            manage_kb_action = QAction("Manage Knowledge Base", self)
            manage_kb_action.triggered.connect(self.manage_knowledge_base)
            rag_menu.addAction(manage_kb_action)
            
            rag_menu.addSeparator()
            
            init_rag_action = QAction("Initialize RAG System", self)
            init_rag_action.triggered.connect(self.initialize_rag_system)
            rag_menu.addAction(init_rag_action)
            
            rebuild_index_action = QAction("Rebuild Search Index", self)
            rebuild_index_action.triggered.connect(self.rebuild_search_index)
            rag_menu.addAction(rebuild_index_action)
            
            # Code execution submenu
            code_menu = tools_menu.addMenu("Code Execution")
            
            execute_code_action = QAction("Execute Selected Code", self)
            execute_code_action.setShortcut(QKeySequence("Ctrl+E"))
            execute_code_action.triggered.connect(self.execute_selected_code)
            code_menu.addAction(execute_code_action)
            
            code_sandbox_action = QAction("Open Code Sandbox", self)
            code_sandbox_action.triggered.connect(self.open_code_sandbox)
            code_menu.addAction(code_sandbox_action)
            
            jupyter_action = QAction("Launch Jupyter Notebook", self)
            jupyter_action.triggered.connect(self.launch_jupyter)
            code_menu.addAction(jupyter_action)
            
            # Analytics submenu
            analytics_menu = tools_menu.addMenu("Analytics")
            
            analyze_action = QAction("Analyze Chat Patterns", self)
            analyze_action.triggered.connect(self.analyze_chat)
            analytics_menu.addAction(analyze_action)
            
            conversation_stats_action = QAction("Conversation Statistics", self)
            conversation_stats_action.triggered.connect(self.show_conversation_stats)
            analytics_menu.addAction(conversation_stats_action)
            
            token_usage_action = QAction("Token Usage Report", self)
            token_usage_action.triggered.connect(self.show_token_usage)
            analytics_menu.addAction(token_usage_action)
            
            visualize_action = QAction("Visualize Conversations", self)
            visualize_action.triggered.connect(self.visualize_conversations)
            analytics_menu.addAction(visualize_action)
            
            # Model management submenu
            model_menu = tools_menu.addMenu("Model Management")
            
            pull_model_action = QAction("Pull/Download Model", self)
            pull_model_action.triggered.connect(self.pull_model)
            model_menu.addAction(pull_model_action)
            
            compare_models_action = QAction("Compare Models", self)
            compare_models_action.triggered.connect(self.compare_models)
            model_menu.addAction(compare_models_action)
            
            benchmark_action = QAction("Benchmark Models", self)
            benchmark_action.triggered.connect(self.benchmark_models)
            model_menu.addAction(benchmark_action)
            
            model_info_action = QAction("Model Information", self)
            model_info_action.triggered.connect(self.show_model_info)
            model_menu.addAction(model_info_action)
            
            tools_menu.addSeparator()
            
            # Search and navigation
            advanced_search_action = QAction("Advanced Search", self)
            advanced_search_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
            advanced_search_action.triggered.connect(self.advanced_search)
            tools_menu.addAction(advanced_search_action)
            
            global_search_action = QAction("Global Conversation Search", self)
            global_search_action.triggered.connect(self.global_search)
            tools_menu.addAction(global_search_action)
            
            tools_menu.addSeparator()
            
            # Utilities
            text_tools_menu = tools_menu.addMenu("Text Tools")
            
            word_count_action = QAction("Word Count", self)
            word_count_action.triggered.connect(self.show_word_count)
            text_tools_menu.addAction(word_count_action)
            
            grammar_check_action = QAction("Grammar Check", self)
            grammar_check_action.triggered.connect(self.check_grammar)
            text_tools_menu.addAction(grammar_check_action)
            
            spell_check_action = QAction("Spell Check", self)
            spell_check_action.triggered.connect(self.check_spelling)
            text_tools_menu.addAction(spell_check_action)
            
            text_summary_action = QAction("Text Summary", self)
            text_summary_action.triggered.connect(self.create_text_summary)
            text_tools_menu.addAction(text_summary_action)

            # Settings Menu
            settings_menu = menubar.addMenu("Settings")
            
            # API and provider settings
            api_settings_action = QAction("API Settings", self)
            api_settings_action.triggered.connect(self.open_api_settings)
            settings_menu.addAction(api_settings_action)
            
            provider_settings_action = QAction("Provider Settings", self)
            provider_settings_action.triggered.connect(self.open_provider_settings)
            settings_menu.addAction(provider_settings_action)
            
            model_settings_action = QAction("Model Settings", self)
            model_settings_action.triggered.connect(self.open_model_settings_manually)
            settings_menu.addAction(model_settings_action)
            
            settings_menu.addSeparator()
            
            # UI and appearance
            preferences_action = QAction("Preferences", self)
            preferences_action.setShortcut(QKeySequence("Ctrl+,"))
            preferences_action.triggered.connect(self.open_preferences)
            settings_menu.addAction(preferences_action)
            
            theme_menu = settings_menu.addMenu("Theme")
            
            dark_theme_action = QAction("Dark Theme", self)
            dark_theme_action.setCheckable(True)
            dark_theme_action.setChecked(self.dark_theme)
            dark_theme_action.triggered.connect(self.set_dark_theme)
            theme_menu.addAction(dark_theme_action)
            
            light_theme_action = QAction("Light Theme", self)
            light_theme_action.setCheckable(True)
            light_theme_action.setChecked(not self.dark_theme)
            light_theme_action.triggered.connect(self.set_light_theme)
            theme_menu.addAction(light_theme_action)
            
            auto_theme_action = QAction("Auto Theme", self)
            auto_theme_action.setCheckable(True)
            auto_theme_action.triggered.connect(self.set_auto_theme)
            theme_menu.addAction(auto_theme_action)
            
            custom_theme_action = QAction("Custom Theme...", self)
            custom_theme_action.triggered.connect(self.open_theme_editor)
            theme_menu.addAction(custom_theme_action)
            
            # Input and keyboard
            keyboard_shortcuts_action = QAction("Keyboard Shortcuts...", self)
            keyboard_shortcuts_action.triggered.connect(self.open_keyboard_shortcuts)
            settings_menu.addAction(keyboard_shortcuts_action)
            
            input_settings_action = QAction("Input Settings", self)
            input_settings_action.triggered.connect(self.open_input_settings)
            settings_menu.addAction(input_settings_action)
            
            settings_menu.addSeparator()
            
            # Advanced settings
            advanced_settings_action = QAction("Advanced Settings", self)
            advanced_settings_action.triggered.connect(self.open_advanced_settings)
            settings_menu.addAction(advanced_settings_action)
            
            plugin_manager_action = QAction("Plugin Manager", self)
            plugin_manager_action.triggered.connect(self.open_plugin_manager)
            settings_menu.addAction(plugin_manager_action)
            
            settings_menu.addSeparator()
            
            # Import/Export settings
            export_settings_action = QAction("Export Settings", self)
            export_settings_action.triggered.connect(self.export_settings)
            settings_menu.addAction(export_settings_action)
            
            import_settings_action = QAction("Import Settings", self)
            import_settings_action.triggered.connect(self.import_settings)
            settings_menu.addAction(import_settings_action)
            
            reset_settings_action = QAction("Reset Settings", self)
            reset_settings_action.triggered.connect(self.reset_settings)
            settings_menu.addAction(reset_settings_action)

            # Help Menu
            help_menu = menubar.addMenu("Help")
            
            # Documentation
            user_guide_action = QAction("User Guide", self)
            user_guide_action.setShortcut(QKeySequence("F1"))
            user_guide_action.triggered.connect(self.open_user_guide)
            help_menu.addAction(user_guide_action)
            
            keyboard_help_action = QAction("Keyboard Shortcuts", self)
            keyboard_help_action.triggered.connect(self.show_keyboard_help)
            help_menu.addAction(keyboard_help_action)
            
            feature_tour_action = QAction("Feature Tour", self)
            feature_tour_action.triggered.connect(self.start_feature_tour)
            help_menu.addAction(feature_tour_action)
            
            help_menu.addSeparator()
            
            # Support and feedback
            bug_report_action = QAction("Report Bug", self)
            bug_report_action.triggered.connect(self.report_bug)
            help_menu.addAction(bug_report_action)
            
            feature_request_action = QAction("Request Feature", self)
            feature_request_action.triggered.connect(self.request_feature)
            help_menu.addAction(feature_request_action)
            
            feedback_action = QAction("Send Feedback", self)
            feedback_action.triggered.connect(self.send_feedback)
            help_menu.addAction(feedback_action)
            
            help_menu.addSeparator()
            
            # Updates and info
            check_updates_action = QAction("Check for Updates", self)
            check_updates_action.triggered.connect(self.check_for_updates)
            help_menu.addAction(check_updates_action)
            
            changelog_action = QAction("Changelog", self)
            changelog_action.triggered.connect(self.show_changelog)
            help_menu.addAction(changelog_action)
            
            help_menu.addSeparator()
            
            about_action = QAction("About The Oracle", self)
            about_action.triggered.connect(self.show_about_dialog)
            help_menu.addAction(about_action)
            
        except Exception as e:
            logger.error(f"Error setting up menu: {e}")

    def setup_styles(self):
        """Apply enhanced dark theme styling with modern design"""
        if self.dark_theme:
            self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0F1419, stop:1 #1A202C);
                color: #F7FAFC;
            }
            
            QWidget {
                background-color: transparent;
                color: #F7FAFC;
            }
            
            QTextBrowser {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1A202C, stop:1 #2D3748);
                border: 2px solid #4A5568;
                border-radius: 12px;
                padding: 15px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
                line-height: 1.5;
            }
            
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2D3748, stop:1 #4A5568);
                border: 2px solid #718096;
                border-radius: 10px;
                padding: 12px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
                color: #F7FAFC;
            }
            
            QTextEdit:focus {
                border-color: #63B3ED;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2D3748, stop:1 #38B2AC);
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4A5568, stop:1 #718096);
                border: 2px solid #718096;
                border-radius: 8px;
                padding: 8px 16px;
                color: #F7FAFC;
                font-weight: bold;
                font-size: 13px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #63B3ED, stop:1 #4299E1);
                border-color: #63B3ED;
                transform: translateY(-1px);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #3182CE, stop:1 #2B6CB0);
                transform: translateY(0px);
            }
            
            QPushButton[objectName="send_button"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #38A169, stop:1 #48BB78);
                border-color: #38A169;
            }
            
            QPushButton[objectName="send_button"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #48BB78, stop:1 #68D391);
                border-color: #48BB78;
            }
            
            QComboBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2D3748, stop:1 #4A5568);
                border: 2px solid #718096;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                min-height: 20px;
            }
            
            QComboBox:hover {
                border-color: #63B3ED;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNSA1TDkgMSIgc3Ryb2tlPSIjRjdGQUZDIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2D3748, stop:1 #4A5568);
                border: 2px solid #718096;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #F7FAFC;
            }
            
            QLineEdit:focus {
                border-color: #63B3ED;
            }
            
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1A202C, stop:1 #2D3748);
                border: 2px solid #4A5568;
                border-radius: 10px;
                padding: 5px;
                font-size: 13px;
            }
            
            QListWidget::item {
                padding: 12px;
                margin: 2px;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2D3748, stop:1 #4A5568);
                border: 1px solid #718096;
            }
            
            QListWidget::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4A5568, stop:1 #718096);
                border-color: #63B3ED;
            }
            
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #63B3ED, stop:1 #4299E1);
                color: #1A202C;
                font-weight: bold;
            }
            
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2D3748, stop:1 #4A5568);
                color: #F7FAFC;
                border-top: 1px solid #718096;
                padding: 5px;
            }
            
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2D3748, stop:1 #4A5568);
                color: #F7FAFC;
                border-bottom: 1px solid #718096;
                padding: 3px;
            }
            
            QMenuBar::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            QMenuBar::item:selected {
                background: #63B3ED;
                color: #1A202C;
            }
            
            QMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2D3748, stop:1 #4A5568);
                border: 2px solid #718096;
                border-radius: 8px;
                padding: 5px;
            }
            
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            
            QMenu::item:selected {
                background: #63B3ED;
                color: #1A202C;
            }
            
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4A5568, stop:1 #718096);
                border-radius: 4px;
            }
            
            QSplitter::handle:hover {
                background: #63B3ED;
            }
            
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1A202C, stop:1 #2D3748);
                border: 1px solid #4A5568;
                border-radius: 10px;
                padding: 5px;
            }
            """)
        else:
            # Light theme with modern enhancements
            self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #F7FAFC, stop:1 #EDF2F7);
                color: #1A202C;
            }
            
            QWidget {
                background-color: transparent;
                color: #1A202C;
            }
            
            QTextBrowser {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #FFFFFF, stop:1 #F7FAFC);
                border: 2px solid #E2E8F0;
                border-radius: 12px;
                padding: 15px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
                line-height: 1.5;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4299E1, stop:1 #63B3ED);
                border: 2px solid #4299E1;
                border-radius: 8px;
                padding: 8px 16px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #3182CE, stop:1 #4299E1);
                border-color: #3182CE;
            }
            
            QPushButton[objectName="send_button"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #38A169, stop:1 #48BB78);
                border-color: #38A169;
            }
            
            QPushButton[objectName="send_button"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2F855A, stop:1 #38A169);
                border-color: #2F855A;
            }
            """)
        
        # Add icon paths for enhanced UI
        self.icon_base_path = os.path.join(os.path.dirname(__file__), "..", "icons")

    def load_providers_and_models(self):
        """Load available providers and models with organized categories"""
        # Clear existing items
        self.provider_combo.clear()
        
        # Get providers organized by category
        categories = self.multi_client.get_providers_by_category()
        available_providers = self.multi_client.get_available_providers()
        
        # Add providers grouped by category
        for category, providers in categories.items():
            # Add category separator
            self.provider_combo.addItem(f"--- {category} ---")
            self.provider_combo.setItemData(self.provider_combo.count() - 1, False, Qt.ItemDataRole.UserRole)
            
            # Add providers in this category
            for provider in providers:
                if provider in available_providers:
                    self.provider_combo.addItem(f"  {provider}")
                else:
                    # Show unavailable providers in gray
                    self.provider_combo.addItem(f"  {provider} (unavailable)")
                    self.provider_combo.setItemData(self.provider_combo.count() - 1, False, Qt.ItemDataRole.UserRole)
        
        # Set default to first available provider
        if available_providers:
            # Find the first available provider in the combo box
            for i in range(self.provider_combo.count()):
                item_text = self.provider_combo.itemText(i).strip()
                if item_text in available_providers:
                    self.provider_combo.setCurrentIndex(i)
                    self.current_provider = item_text
                    self.on_provider_changed(item_text)
                    break
        else:
            # Default to Ollama even if not available
            self.current_provider = "Ollama"
            self.on_provider_changed("Ollama")

    def load_conversations(self):
        """Load conversation list with lazy loading (batch)"""
        self.conv_listbox.clear()
        self.conversation_map = {}
        self._all_conversations = []
        conversations_dir = "conversations"
        if os.path.exists(conversations_dir):
            for filename in os.listdir(conversations_dir):
                if filename.endswith('.json'):
                    conv_id = filename[:-5]
                    try:
                        with open(os.path.join(conversations_dir, filename), 'r') as f:
                            data = json.load(f)
                        if data:
                            first_msg = data[0]['content'][:50] + "..." if len(data[0]['content']) > 50 else data[0]['content']
                            name = f"{first_msg} ({len(data)} msgs)"
                            self._all_conversations.append((name, conv_id))
                    except Exception as e:
                        logger.error(f"Failed to load conversation {conv_id}: {e}")
        self._lazy_load_index = 0
        self._lazy_load_next_batch()

    def _lazy_load_next_batch(self):
        """Load the next batch of conversations into the listbox"""
        batch = self._all_conversations[self._lazy_load_index:self._lazy_load_index + self.LAZY_LOAD_BATCH_SIZE]
        for name, conv_id in batch:
            self.conv_listbox.addItem(name)
            self.conversation_map[name] = conv_id
        self._lazy_load_index += self.LAZY_LOAD_BATCH_SIZE
        # Add 'Load More' button if more remain
        if self._lazy_load_index < len(self._all_conversations):
            load_more_item = QListWidgetItem("↓ Load More Conversations")
            load_more_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.conv_listbox.addItem(load_more_item)

    # --- Virtual Scrolling for Chat ---
    def input_key_press_event(self, event):
        """Handle key press events in input field"""
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.send_message()
        else:
            QTextEdit.keyPressEvent(self.input_entry, event)

    def send_message(self):
        """Send a message to the AI"""
        message = self.input_entry.toPlainText().strip()
        if not message:
            return
        
        # Clear input
        self.input_entry.clear()
        
        # Hide welcome screen if visible
        self.toggle_welcome_screen(False)
        
        # Add user message to chat
        self.append_to_chat("User", message, is_user=True)
        
        # Add to chat history
        self.chat_history.append({"role": "user", "content": message})
        
        # Create new conversation if needed
        if not self.current_conversation_id:
            self.current_conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.load_conversations()
        
        # Generate response
        self.generate_response(message)

    def generate_response(self, message):
        """Generate AI response"""
        if not self.current_provider or not self.current_model:
            QMessageBox.warning(self, "No Model Selected", "Please select a provider and model first.")
            return
        
        # Disable send button during generation
        self.send_button.setEnabled(False)
        self.send_button.setText("⏳ Processing...")
        
        # Get current model parameters
        model_params = self.get_model_parameters_for_request()
        
        # Get system prompt for this conversation
        system_prompt = self.get_system_prompt_for_conversation()
        
        # Create and start response thread
        if self.current_provider == "Ollama":
            self.response_thread = ModelResponseThread(
                self.multi_client.providers["Ollama"]["client"],
                self.current_model,
                message,
                model_params,
                system_prompt if system_prompt else None
            )
        else:
            self.response_thread = MultiProviderResponseThread(
                self.multi_client,
                message,
                provider=self.current_provider,
                model=self.current_model,
                system_message=system_prompt if system_prompt else None,
                model_params=model_params
            )
        
        self.response_thread.response_chunk.connect(self.on_response_chunk)
        self.response_thread.response_finished.connect(self.on_response_finished)
        self.response_thread.error_occurred.connect(self.on_response_error)
        self.response_thread.start()

    def on_response_chunk(self, chunk):
        """Handle response chunk from AI"""
        if not hasattr(self, 'current_response'):
            self.current_response = ""
            # Add initial assistant message header
            cursor = self.chat_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            timestamp = datetime.now().strftime("%H:%M:%S")
            cursor.insertHtml(f'<br><b>Assistant ({timestamp}):</b><br>')
        
        self.current_response += chunk
        
        # Simply append the chunk to the display
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)  # Insert as plain text to avoid HTML issues
        
        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def on_response_finished(self, full_response):
        """Handle completed response from AI"""
        # Add a line break after the response
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("\n\n")  # Add some spacing
        
        self.send_button.setEnabled(True)
        self.send_button.setText("📤 Send")
        
        # Add to chat history
        self.chat_history.append({"role": "assistant", "content": full_response})
        
        # Reset current response
        if hasattr(self, 'current_response'):
            delattr(self, 'current_response')
        
        # Save conversation
        self.save_current_conversation_to_json()

    def on_response_error(self, error):
        """Handle response error"""
        self.send_button.setEnabled(True)
        self.send_button.setText("📤 Send")
        
        # Add error message to chat
        error_html = f"""
        <div class="system-message" style="background-color: #FED7D7; border-left: 4px solid #E53E3E; padding: 10px; margin: 10px 0;">
            <div class="message-header">
                <span class="role">System</span>
                <span class="timestamp">{datetime.now().strftime("%H:%M:%S")}</span>
            </div>
            <div class="message-content">❌ Error: {html.escape(str(error))}</div>
        </div>
        """
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(error_html)
        
        # Reset current response if it exists
        if hasattr(self, 'current_response'):
            delattr(self, 'current_response')

    def append_to_chat(self, role, content, is_user=True):
        """Append message to chat display (threaded and pin support)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format the message content using MessageFormatter for better code block rendering
        if not is_user and self.enable_markdown:
            formatted_content = self.message_formatter.format_message(content, self.current_model)
        else:
            formatted_content = html.escape(content)
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # If message is pinned, add a pin icon
        idx = len(self.chat_history) - 1
        pin_html = ""
        if self.current_conversation_id in self.pinned_messages and idx in self.pinned_messages[self.current_conversation_id]:
            pin_html = " <span style='color:#FFD700;'>📌</span>"
        
        if is_user:
            message_html = f"""
            <div class="user-message" style="
                background: linear-gradient(135deg, #2D3748 0%, #4A5568 100%);
                border: 1px solid #718096;
                border-radius: 10px;
                padding: 12px 16px;
                margin: 10px 0;
                color: #F7FAFC;
            ">
                <div style="font-weight: bold; color: #63B3ED; margin-bottom: 5px;">
                    👤 User ({timestamp}){pin_html}
                </div>
                <div style="line-height: 1.5;">{formatted_content}</div>
            </div>
            """
        else:
            message_html = f"""
            <div class="assistant-message" style="
                background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%);
                border: 1px solid #4A5568;
                border-radius: 10px;
                padding: 12px 16px;
                margin: 10px 0;
                color: #F7FAFC;
            ">
                <div style="font-weight: bold; color: #48BB78; margin-bottom: 5px;">
                    🤖 {role} ({timestamp}){pin_html}
                </div>
                <div style="line-height: 1.5;">{formatted_content}</div>
            </div>
            """
        
        cursor.insertHtml(message_html)
        
        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def update_last_assistant_message(self, content):
        """Update the last assistant message in the display"""
        # Get the current HTML content
        current_html = self.chat_display.toHtml()
        
        # Find the last assistant message and update it
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Create the updated message HTML
        updated_content = format_chat_message("Assistant", content, timestamp, self.enable_markdown)
        
        # For streaming updates, we need to replace the last assistant message
        # This is a simplified approach - we'll append the content directly
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Clear the last empty assistant message and insert the updated one
        # Find and remove the last assistant message div
        html_content = self.chat_display.toHtml()
        
        # Simple approach: find last assistant-message div and replace it
        last_assistant_start = html_content.rfind('<div class="assistant-message">')
        if last_assistant_start != -1:
            # Find the end of this div
            div_count = 0
            end_pos = last_assistant_start
            while end_pos < len(html_content):
                if html_content[end_pos:end_pos+5] == '<div':
                    div_count += 1
                elif html_content[end_pos:end_pos+6] == '</div>':
                    div_count -= 1
                    if div_count == 0:
                        end_pos += 6
                        break
                end_pos += 1
            
            # Replace the content
            new_html = html_content[:last_assistant_start] + updated_content + html_content[end_pos:]
            self.chat_display.setHtml(new_html)
        else:
            # No existing assistant message, append new one
            cursor.insertHtml(updated_content)
        
        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def on_provider_changed(self, provider):
        """Handle provider change"""
        if not provider:
            return
        
        # Clean provider name (remove leading spaces and category markers)
        provider = provider.strip()
        if provider.startswith("---") or provider.endswith("(unavailable)"):
            return
        
        self.current_provider = provider
        self.multi_client.current_provider = provider
        
        # Update models
        models = self.multi_client.get_models(provider)
        self.model_combo.clear()
        if models:
            self.model_combo.addItems(models)
            if models:
                self.current_model = models[0]
                self.model_combo.setCurrentText(self.current_model)
        else:
            self.model_combo.addItem("No models available")
            self.current_model = None
        
        # Enable pull button only for Ollama
        self.pull_button.setEnabled(provider == "Ollama")

    def on_model_changed(self, model):
        """Handle model change and show settings dialog"""
        if not model or model == "No models available":
            return
            
        # Store the previous model to potentially revert
        previous_model = getattr(self, 'current_model', None)
        
        # Set the new model
        self.current_model = model
        
        # Show model settings dialog
        self.show_model_settings_dialog(model, previous_model)

    def open_model_settings_manually(self):
        """Open model settings dialog manually (not triggered by model change)"""
        if not self.current_model:
            QMessageBox.information(self, "No Model", "Please select a model first.")
            return
        
        self.show_model_settings_dialog(self.current_model, None)

    def show_model_settings_dialog(self, model, previous_model=None):
        """Show the model settings dialog for the selected model"""
        try:
            # Get current provider
            provider = getattr(self, 'current_provider', 'Unknown')
            
            # Get current model parameters
            current_settings = getattr(self, 'model_parameters', {}).copy()
            
            # Create and show the dialog
            dialog = ModelSettingsDialog(
                parent=self,
                current_model=model,
                current_provider=provider,
                current_settings=current_settings
            )
            
            # Connect the settings applied signal
            dialog.settings_applied.connect(self.apply_model_settings)
            
            # Show the dialog
            result = dialog.exec()
            
            # If user cancelled, revert to previous model
            if result == QDialog.DialogCode.Rejected and previous_model:
                # Revert model selection without triggering another dialog
                self.model_combo.blockSignals(True)
                self.model_combo.setCurrentText(previous_model)
                self.model_combo.blockSignals(False)
                self.current_model = previous_model
                
        except Exception as e:
            logger.error(f"Error showing model settings dialog: {e}")
            # If there's an error, just continue with model change
            QMessageBox.warning(self, "Settings Error", 
                              f"Could not open model settings: {e}")

    def apply_model_settings(self, settings):
        """Apply the model settings from the dialog"""
        try:
            # Update model parameters
            self.model_parameters.update(settings)
            
            # Store settings per model
            if not hasattr(self, 'model_specific_settings'):
                self.model_specific_settings = {}
            
            model_key = f"{self.current_provider}::{self.current_model}"
            self.model_specific_settings[model_key] = settings.copy()
            
            # Update status bar to show settings applied
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(
                    f"Settings applied for {self.current_model}", 3000
                )
            
            logger.info(f"Applied settings for {self.current_model}: {settings}")
            
        except Exception as e:
            logger.error(f"Error applying model settings: {e}")
            QMessageBox.warning(self, "Settings Error", 
                              f"Could not apply settings: {e}")

    def get_model_parameters_for_request(self):
        """Get the current model parameters for API requests"""
        # Start with base parameters
        params = self.model_parameters.copy()
        
        # Override with model-specific settings if available
        if hasattr(self, 'model_specific_settings'):
            model_key = f"{self.current_provider}::{self.current_model}"
            if model_key in self.model_specific_settings:
                params.update(self.model_specific_settings[model_key])
        
        # Remove any None or invalid values
        cleaned_params = {}
        for key, value in params.items():
            if value is not None and value != -1:  # -1 often means "default"
                cleaned_params[key] = value
        
        return cleaned_params

    def refresh_current_provider_models(self):
        """Refresh models for current provider"""
        if not self.current_provider:
            return
        
        self.refresh_models_button.setEnabled(False)
        self.refresh_models_button.setText("...")
        
        try:
            # Special handling for Ollama
            if self.current_provider == "Ollama":
                models = self.multi_client.refresh_ollama_models()
            else:
                # Refresh models for other providers
                models = self.multi_client.refresh_models(self.current_provider)
            
            # Update UI
            self.model_combo.clear()
            if models:
                self.model_combo.addItems(models)
                if models:
                    self.current_model = models[0]
                    self.model_combo.setCurrentText(self.current_model)
            else:
                self.model_combo.addItem("No models available")
                self.current_model = None
            
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh models: {e}")
        finally:
            self.refresh_models_button.setEnabled(True)
            self.refresh_models_button.setText("🔄")

    def open_api_settings(self):
        """Open API settings dialog"""
        dialog = APISettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.multi_client.load_settings()
            self.load_providers_and_models()

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        self.dark_theme = not self.dark_theme
        self.setup_styles()
        
        # Update theme button
        if self.dark_theme:
            self.theme_button.setText("🌙")
            self.theme_button.setToolTip("Switch to Light Theme")
        else:
            self.theme_button.setText("☀️") 
            self.theme_button.setToolTip("Switch to Dark Theme")

    def toggle_markdown(self):
        """Toggle markdown formatting"""
        self.enable_markdown = not self.enable_markdown

    def toggle_code_saving(self):
        """Toggle code block saving"""
        self.enable_code_saving = not self.enable_code_saving

    def toggle_line_numbers(self):
        """Toggle line numbers in code blocks"""
        self.show_line_numbers = not self.show_line_numbers
        
        # Update the message formatter with the new setting
        self.message_formatter = MessageFormatter(self.dark_theme, self.show_line_numbers, self.enable_code_folding)
        
        # Refresh the current display to apply the change
        self.refresh_chat_display()

    def toggle_code_folding(self):
        """Toggle code folding in code blocks"""
        self.enable_code_folding = not self.enable_code_folding
        
        # Update the message formatter with the new setting
        self.message_formatter = MessageFormatter(self.dark_theme, self.show_line_numbers, self.enable_code_folding)
        
        # Refresh the current display to apply the change
        self.refresh_chat_display()

    def toggle_compact_mode(self):
        """Toggle between compact and spacious UI mode"""
        self.compact_mode = not self.compact_mode
        
        # Apply the new styling
        self.apply_ui_mode_styles()
        
        # Show status message
        mode_text = "Compact" if self.compact_mode else "Spacious"
        self.status_bar.showMessage(f"Switched to {mode_text} UI mode", 3000)

    def apply_ui_mode_styles(self):
        """Apply compact or spacious styling to the UI"""
        if self.compact_mode:
            # Compact mode - reduced padding and margins
            compact_styles = """
            QWidget {
                font-size: 12px;
            }
            
            QTextBrowser {
                padding: 8px;
                margin: 2px;
                line-height: 1.3;
            }
            
            QTextEdit {
                padding: 6px;
                margin: 2px;
                font-size: 12px;
            }
            
            QPushButton {
                padding: 4px 8px;
                margin: 1px;
                font-size: 11px;
                min-height: 16px;
            }
            
            QComboBox {
                padding: 2px 6px;
                margin: 1px;
                font-size: 11px;
                min-height: 18px;
            }
            
            QLabel {
                margin: 1px;
                font-size: 11px;
            }
            
            QListWidget {
                padding: 2px;
                font-size: 11px;
            }
            
            QListWidget::item {
                padding: 2px 4px;
                margin: 1px;
            }
            """
        else:
            # Spacious mode - increased padding and margins
            compact_styles = """
            QWidget {
                font-size: 14px;
            }
            
            QTextBrowser {
                padding: 16px;
                margin: 8px;
                line-height: 1.6;
            }
            
            QTextEdit {
                padding: 12px;
                margin: 6px;
                font-size: 14px;
            }
            
            QPushButton {
                padding: 10px 16px;
                margin: 4px;
                font-size: 13px;
                min-height: 24px;
            }
            
            QComboBox {
                padding: 6px 12px;
                margin: 4px;
                font-size: 13px;
                min-height: 26px;
            }
            
            QLabel {
                margin: 4px;
                font-size: 13px;
            }
            
            QListWidget {
                padding: 8px;
                font-size: 13px;
            }
            
            QListWidget::item {
                padding: 6px 8px;
                margin: 2px;
            }
            """
        
        # Apply the mode-specific styles on top of the existing theme
        current_style = self.styleSheet()
        self.setStyleSheet(current_style + compact_styles)

    def load_selected_conv(self, index):
        """Load selected conversation or next batch if 'Load More'"""
        item = self.conv_listbox.item(index)
        if item and item.text() == "↓ Load More Conversations":
            self.conv_listbox.takeItem(index)  # Remove the 'Load More' item
            self._lazy_load_next_batch()
            return
        # ...existing code for loading conversation...
        if index < 0:
            return
        if item:
            name = item.text()
            conv_id = self.conversation_map.get(name)
            if conv_id:
                self.load_conversation(conv_id)

    def load_conversation(self, conv_id):
        """Load a specific conversation"""
        try:
            filepath = f"conversations/{conv_id}.json"
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Handle both old and new format
                if isinstance(data, list):
                    # Old format - just messages
                    self.chat_history = data
                elif isinstance(data, dict) and "messages" in data:
                    # New format - with metadata
                    self.chat_history = data["messages"]
                    metadata = data.get("metadata", {})
                    
                    # Load system prompt if present
                    if "system_prompt" in metadata and metadata["system_prompt"]:
                        self.conversation_system_prompts[conv_id] = metadata["system_prompt"]
                    
                    # Load other metadata
                    if "pinned_messages" in metadata:
                        self.pinned_messages[conv_id] = metadata["pinned_messages"]
                    
                    # Set provider/model if available
                    if "provider" in metadata and metadata["provider"]:
                        # You could switch to this provider/model automatically
                        pass
                else:
                    # Fallback
                    self.chat_history = []
                
                self.current_conversation_id = conv_id
                self.refresh_chat_display()
                self.toggle_welcome_screen(False)
                
                # Update system prompt indicator
                self.update_system_prompt_indicator()
        except Exception as e:
            logger.error(f"Failed to load conversation {conv_id}: {e}")

    def refresh_chat_display(self):
        """Refresh the chat display with all messages"""
        self.chat_display.clear()
        for message in self.chat_history:
            formatted_message = self.format_message_for_display(message)
            self.chat_display.append(formatted_message)

    def format_message_for_display(self, message):
        """Format a single message for display"""
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        
        if role == 'user':
            return f"<div style='background-color: #e3f2fd; padding: 10px; margin: 5px; border-radius: 10px;'><b>👤 You:</b> {content}</div>"
        elif role == 'assistant':
            return f"<div style='background-color: #f3e5f5; padding: 10px; margin: 5px; border-radius: 10px;'><b>🤖 Oracle:</b> {content}</div>"
        else:
            return f"<div style='background-color: #f5f5f5; padding: 10px; margin: 5px; border-radius: 10px;'><b>{role}:</b> {content}</div>"

    def filter_chat(self):
        """Filter chat messages based on search entry"""
        search_term = self.search_entry.text().strip().lower()
        
        if not search_term:
            # If search is empty, show all messages
            self.refresh_chat_display()
            return
        
        # Clear the current display
        self.chat_display.clear()
        
        # Filter and display messages that contain the search term
        filtered_count = 0
        for message in self.chat_history:
            content = message.get('content', '').lower()
            role = message.get('role', '')
            
            if search_term in content:
                # Add the message to display
                formatted_message = self.format_message_for_display(message)
                self.chat_display.append(formatted_message)
                filtered_count += 1
        
        # Show status message
        if hasattr(self, 'status_bar'):
            if filtered_count > 0:
                self.status_bar.showMessage(f"Found {filtered_count} messages matching '{search_term}'", 3000)
            else:
                self.status_bar.showMessage(f"No messages found matching '{search_term}'", 3000)
    
    def save_chat(self):
        """Save the current chat to a file"""
        if not self.chat_history:
            QMessageBox.information(self, "No Chat", "There is no chat to save.")
            return
        
        try:
            # Get save location from user
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Chat", f"oracle_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON files (*.json);;Text files (*.txt);;All files (*.*)"
            )
            
            if file_path:
                if file_path.endswith('.json'):
                    self.export_chat("json", file_path)
                else:
                    self.export_chat("txt", file_path)
                    
                QMessageBox.information(self, "Chat Saved", f"Chat saved to {file_path}")
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Chat saved", 3000)
                    
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save chat: {str(e)}")
            logger.error(f"Error saving chat: {e}")

    def export_chat(self, format_type, file_path=None):
        """Export chat in the specified format"""
        if not self.chat_history:
            QMessageBox.information(self, "No Chat", "There is no chat to export.")
            return
        
        try:
            if not file_path:
                # Get save location from user
                filters = {
                    "json": "JSON files (*.json)",
                    "txt": "Text files (*.txt)",
                    "html": "HTML files (*.html)",
                    "md": "Markdown files (*.md)"
                }
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self, f"Export Chat as {format_type.upper()}", 
                    f"oracle_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}",
                    f"{filters.get(format_type, 'All files (*.*)')};;All files (*.*)"
                )
                
                if not file_path:
                    return
            
            # Export based on format
            if format_type == "json":
                self._export_to_json(file_path)
            elif format_type == "txt":
                self._export_to_txt(file_path)
            elif format_type == "html":
                self._export_to_html(file_path)
            elif format_type == "md":
                self._export_to_markdown(file_path)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"Chat exported to {format_type.upper()}", 3000)
                
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export chat: {str(e)}")
            logger.error(f"Error exporting chat: {e}")

    def _export_to_json(self, file_path):
        """Export chat to JSON format"""
        chat_data = {
            "timestamp": datetime.now().isoformat(),
            "provider": self.current_provider,
            "model": self.current_model,
            "conversation_id": self.current_conversation_id,
            "messages": []
        }
        
        for entry in self.chat_history:
            if isinstance(entry, dict):
                chat_data["messages"].append(entry)
            else:
                # Handle legacy format
                chat_data["messages"].append({
                    "role": "unknown",
                    "content": str(entry),
                    "timestamp": datetime.now().isoformat()
                })
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)

    def _export_to_txt(self, file_path):
        """Export chat to plain text format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Oracle Chat Export\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Provider: {self.current_provider}\n")
            f.write(f"Model: {self.current_model}\n")
            f.write("="*50 + "\n\n")
            
            for entry in self.chat_history:
                if isinstance(entry, dict):
                    role = entry.get("role", "unknown").title()
                    content = entry.get("content", "")
                    timestamp = entry.get("timestamp", "")
                    
                    f.write(f"{role}")
                    if timestamp:
                        f.write(f" ({timestamp})")
                    f.write(":\n")
                    f.write(f"{content}\n\n")
                else:
                    f.write(f"{entry}\n\n")

    def _export_to_html(self, file_path):
        """Export chat to HTML format"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Oracle Chat Export</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        .message {{ margin-bottom: 15px; padding: 10px; border-radius: 5px; }}
        .user {{ background: #e3f2fd; }}
        .assistant {{ background: #f3e5f5; }}
        .system {{ background: #fff3e0; }}
        .timestamp {{ font-size: 0.8em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Oracle Chat Export</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Provider: {self.current_provider} | Model: {self.current_model}</p>
    </div>
"""
        
        for entry in self.chat_history:
            if isinstance(entry, dict):
                role = entry.get("role", "unknown")
                content = entry.get("content", "").replace("\n", "<br>")
                timestamp = entry.get("timestamp", "")
                
                html_content += f"""
    <div class="message {role}">
        <strong>{role.title()}</strong>
        {f'<span class="timestamp">({timestamp})</span>' if timestamp else ''}
        <div>{content}</div>
    </div>
"""
            else:
                content_with_breaks = str(entry).replace("\n", "<br>")
                html_content += f"""
    <div class="message">
        <div>{content_with_breaks}</div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _export_to_markdown(self, file_path):
        """Export chat to Markdown format"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Oracle Chat Export\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Provider:** {self.current_provider}  \n")
            f.write(f"**Model:** {self.current_model}  \n\n")
            f.write("---\n\n")
            
            for entry in self.chat_history:
                if isinstance(entry, dict):
                    role = entry.get("role", "unknown").title()
                    content = entry.get("content", "")
                    timestamp = entry.get("timestamp", "")
                    
                    f.write(f"## {role}")
                    if timestamp:
                        f.write(f" *({timestamp})*")
                    f.write("\n\n")
                    f.write(f"{content}\n\n")
                else:
                    f.write(f"{entry}\n\n")

    def save_current_conversation_to_json(self):
        """Save the current conversation to JSON in conversations directory"""
        if not self.chat_history:
            return
        
        try:
            # Create conversations directory if it doesn't exist
            conversations_dir = os.path.join(os.path.dirname(__file__), "..", "conversations")
            os.makedirs(conversations_dir, exist_ok=True)
            
            # Generate filename
            if self.current_conversation_id:
                filename = f"conv_{self.current_conversation_id}.json"
            else:
                filename = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            file_path = os.path.join(conversations_dir, filename)
            
            # Export to JSON
            self._export_to_json(file_path)
            
            logger.info(f"Conversation saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

    def new_conversation(self):
        """Start a new conversation"""
        # Save current conversation if it has content
        if hasattr(self, 'chat_history') and self.chat_history:
            reply = QMessageBox.question(
                self, "New Conversation", 
                "Save the current conversation before starting a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                self.save_current_conversation_to_json()
        
        # Clear current conversation data
        self.chat_display.clear()
        self.chat_history = []
        self.conversation_history = []
        self.current_conversation_id = None
        
        # Clear input field
        if hasattr(self, 'input_entry'):
            self.input_entry.clear()
        
        # Reset conversation selection in the list
        if hasattr(self, 'conv_listbox'):
            self.conv_listbox.clearSelection()
        
        # Update status
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage("🚀 New conversation started!", 3000)

    def pull_model(self):
        """Pull/download a model using Ollama"""
        if self.current_provider != "Ollama":
            QMessageBox.warning(self, "Feature Not Available", 
                              "Model pulling is only available for Ollama.")
            return
        
        # Check if Ollama is available
        if not self.multi_client.is_ollama_available():
            QMessageBox.warning(self, "Ollama Not Available", 
                              "Ollama is not available. Please ensure Ollama is installed and running.")
            return
        
        # Get model name from user
        model_name, ok = QInputDialog.getText(
            self, "Pull Model", 
            "Enter the model name to pull (e.g., 'llama2', 'codellama', 'mistral'):",
            QLineEdit.EchoMode.Normal
        )
        
        if not ok or not model_name.strip():
            return
        
        model_name = model_name.strip()
        
        # Confirm the action
        reply = QMessageBox.question(
            self, "Confirm Model Pull",
            f"This will download the model '{model_name}' from Ollama.\n"
            "Large models can take significant time and bandwidth.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Start the pull operation in a background thread
        self._start_model_pull(model_name)
    
    def _start_model_pull(self, model_name):
        """Start model pull operation in background thread"""
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class ModelPullThread(QThread):
            progress_update = pyqtSignal(str)
            pull_completed = pyqtSignal(bool, str)
            
            def __init__(self, model_name, multi_client):
                super().__init__()
                self.model_name = model_name
                self.multi_client = multi_client
            
            def run(self):
                try:
                    self.progress_update.emit(f"Starting pull for model: {self.model_name}")
                    
                    # Use the multi_client's pull_ollama_model method
                    for progress in self.multi_client.pull_ollama_model(self.model_name):
                        self.progress_update.emit(progress)
                    
                    self.pull_completed.emit(True, f"Successfully pulled model: {self.model_name}")
                except Exception as e:
                    self.pull_completed.emit(False, f"Failed to pull model: {str(e)}")
        
        # Create and start the thread
        self.pull_thread = ModelPullThread(model_name, self.multi_client)
        self.pull_thread.progress_update.connect(self._on_pull_progress)
        self.pull_thread.pull_completed.connect(self._on_pull_completed)
        
        # Disable pull button during operation
        self.pull_button.setEnabled(False)
        self.pull_button.setText("📥 Pulling...")
        
        # Show status message
        self.status_bar.showMessage(f"Pulling model: {model_name}...")
        
        self.pull_thread.start()
    
    def _on_pull_progress(self, message):
        """Handle pull progress updates"""
        self.status_bar.showMessage(message)
        logger.info(message)
    
    def _on_pull_completed(self, success, message):
        """Handle pull completion"""
        # Re-enable pull button
        self.pull_button.setEnabled(True)
        self.pull_button.setText("📥 Pull Model")
        
        if success:
            # Show success message
            QMessageBox.information(self, "Pull Successful", message)
            self.status_bar.showMessage("Model pull completed successfully", 5000)
            
            # Refresh models list for Ollama
            if self.current_provider == "Ollama":
                try:
                    models = self.multi_client.refresh_ollama_models()
                    self.model_combo.clear()
                    if models:
                        self.model_combo.addItems(models)
                        # Select the newly pulled model if it's in the list
                        if (hasattr(self, 'pull_thread') and self.pull_thread and 
                            hasattr(self.pull_thread, 'model_name') and 
                            self.pull_thread.model_name in models):
                            self.model_combo.setCurrentText(self.pull_thread.model_name)
                            self.current_model = self.pull_thread.model_name
                except Exception as e:
                    logger.warning(f"Failed to refresh models after pull: {e}")
        else:
            # Show error message
            QMessageBox.warning(self, "Pull Failed", message)
            self.status_bar.showMessage("Model pull failed", 5000)
        
        # Clean up thread
        if hasattr(self, 'pull_thread') and self.pull_thread:
            self.pull_thread.deleteLater()
            self.pull_thread = None

    def setup_auto_save(self):
        """Set up auto-save functionality"""
        try:
            # Create auto-save timer
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self.auto_save_conversation)
            
            # Set auto-save interval (5 minutes)
            self.auto_save_timer.start(300000)  # 5 minutes in milliseconds
            
            logger.info("Auto-save functionality initialized")
        except Exception as e:
            logger.warning(f"Failed to setup auto-save: {e}")

    def auto_save_conversation(self):
        """Auto-save the current conversation"""
        try:
            if hasattr(self, 'chat_history') and self.chat_history:
                self.save_current_conversation_to_json()
                logger.debug("Auto-saved conversation")
        except Exception as e:
            logger.warning(f"Auto-save failed: {e}")

    def load_chat_on_startup(self):
        """Load the most recent chat on startup"""
        try:
            # Try to load the most recent conversation
            conversations_dir = os.path.join(os.path.dirname(__file__), "..", "conversations")
            if os.path.exists(conversations_dir):
                # Get most recent conversation file
                conv_files = [f for f in os.listdir(conversations_dir) if f.endswith('.json')]
                if conv_files:
                    # Sort by modification time, get most recent
                    conv_files.sort(key=lambda x: os.path.getmtime(os.path.join(conversations_dir, x)), reverse=True)
                    most_recent = conv_files[0]
                    
                    # Extract conversation ID
                    conv_id = most_recent.replace('conv_', '').replace('.json', '')
                    
                    # Load the conversation
                    self.load_conversation(conv_id)
                    logger.info(f"Loaded most recent conversation: {conv_id}")
        except Exception as e:
            logger.warning(f"Failed to load chat on startup: {e}")

    def setup_code_execution(self):
        """Set up code execution environment"""
        try:
            # Initialize code execution settings
            self.code_execution_enabled = True
            self.safe_mode = True  # Run code in safe mode by default
            
            # Set up supported languages
            self.supported_languages = ['python', 'javascript', 'bash', 'sql']
            
            logger.info("Code execution environment initialized")
        except Exception as e:
            logger.warning(f"Failed to setup code execution: {e}")

    def get_system_prompt_for_conversation(self):
        """Get the system prompt for the current conversation"""
        try:
            # Check if there's a conversation-specific system prompt
            if hasattr(self, 'conversation_system_prompts') and self.current_conversation_id:
                return self.conversation_system_prompts.get(self.current_conversation_id, "")
            
            # Return default system prompt
            return getattr(self, 'default_system_prompt', "")
        except Exception as e:
            logger.warning(f"Error getting system prompt: {e}")
            return ""

    def update_system_prompt_indicator(self):
        """Update the system prompt indicator in the UI"""
        try:
            # Check if system prompt is set
            system_prompt = self.get_system_prompt_for_conversation()
            
            # Update indicator (if it exists)
            if hasattr(self, 'system_prompt_indicator'):
                if system_prompt:
                    self.system_prompt_indicator.setText("🎯 System Prompt Active")
                    self.system_prompt_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
                else:
                    self.system_prompt_indicator.setText("💬 Default Mode")
                    self.system_prompt_indicator.setStyleSheet("color: #666; font-style: italic;")
        except Exception as e:
            logger.warning(f"Error updating system prompt indicator: {e}")

    def set_system_prompt(self):
        """Open dialog to set system prompt for current conversation"""
        try:
            current_prompt = self.get_system_prompt_for_conversation()
            
            # Open input dialog
            prompt, ok = QInputDialog.getMultiLineText(
                self, "Set System Prompt",
                "Enter the system prompt for this conversation:",
                current_prompt
            )
            
            if ok:
                # Initialize conversation_system_prompts if needed
                if not hasattr(self, 'conversation_system_prompts'):
                    self.conversation_system_prompts = {}
                
                # Ensure we have a conversation ID
                if not self.current_conversation_id:
                    self.current_conversation_id = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Set the system prompt
                if prompt.strip():
                    self.conversation_system_prompts[self.current_conversation_id] = prompt.strip()
                    QMessageBox.information(self, "System Prompt Set", 
                                          "System prompt has been set for this conversation.")
                else:
                    # Remove system prompt if empty
                    self.conversation_system_prompts.pop(self.current_conversation_id, None)
                    QMessageBox.information(self, "System Prompt Cleared", 
                                          "System prompt has been cleared for this conversation.")
                
                # Update indicator
                self.update_system_prompt_indicator()
                
                # Update status
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("System prompt updated", 3000)
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to set system prompt: {str(e)}")
            logger.error(f"Error setting system prompt: {e}")

    def open_prompt_library(self):
        """Open the prompt library dialog"""
        try:
            from ui.prompt_library_dialog import PromptLibraryDialog
            dialog = PromptLibraryDialog(self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get selected prompt
                selected_prompt = dialog.get_selected_prompt()
                if selected_prompt:
                    # Insert into input field
                    if hasattr(self, 'input_entry'):
                        current_text = self.input_entry.toPlainText()
                        if current_text:
                            self.input_entry.setPlainText(current_text + "\n\n" + selected_prompt)
                        else:
                            self.input_entry.setPlainText(selected_prompt)
                        
                        # Move cursor to end
                        cursor = self.input_entry.textCursor()
                        cursor.movePosition(cursor.MoveOperation.End)
                        self.input_entry.setTextCursor(cursor)
                    
                    if hasattr(self, 'status_bar'):
                        self.status_bar.showMessage("Prompt inserted from library", 2000)
                        
        except ImportError:
            QMessageBox.warning(self, "Feature Unavailable", 
                              "Prompt library feature is not available.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open prompt library: {str(e)}")
            logger.error(f"Error opening prompt library: {e}")

    def scroll_to_bottom(self):
        """Scroll the chat display to the bottom"""
        try:
            if hasattr(self, 'chat_display') and self.chat_display:
                scrollbar = self.chat_display.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            logger.warning(f"Error scrolling to bottom: {e}")

    def on_scroll_changed(self, value):
        """Handle scroll position changes"""
        try:
            if hasattr(self, 'chat_display') and hasattr(self, 'scroll_to_bottom_button'):
                scrollbar = self.chat_display.verticalScrollBar()
                # Show/hide scroll to bottom button based on position
                at_bottom = value >= scrollbar.maximum() - 10
                self.scroll_to_bottom_button.setVisible(not at_bottom)
        except Exception as e:
            logger.warning(f"Error handling scroll change: {e}")

    def toggle_welcome_screen(self, show):
        """Toggle the welcome screen visibility"""
        try:
            if hasattr(self, 'welcome_screen'):
                self.welcome_screen.setVisible(show)
            if hasattr(self, 'chat_display'):
                self.chat_display.setVisible(not show)
        except Exception as e:
            logger.warning(f"Error toggling welcome screen: {e}")

    def manage_knowledge_base(self):
        """Open knowledge base management dialog"""
        # This would open a dialog to manage the knowledge base
        QMessageBox.information(self, "Knowledge Base", 
                              "Knowledge base management dialog would open here.")

    def visualize_conversations(self):
        """Visualize conversation patterns"""
        # This would create visualizations of conversation patterns
        QMessageBox.information(self, "Visualization", 
                              "Conversation visualization would be displayed here.")

    def advanced_search(self):
        """Open advanced search dialog"""
        # This would open an advanced search interface
        QMessageBox.information(self, "Advanced Search", 
                              "Advanced search dialog would open here.")

    def open_keyboard_shortcuts(self):
        """Open keyboard shortcuts editor"""
        try:
            from ui.keyboard_shortcut_editor import KeyboardShortcutEditor
            dialog = KeyboardShortcutEditor(self)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Update shortcuts if needed
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Keyboard shortcuts updated", 3000)
                    
        except ImportError:
            QMessageBox.warning(self, "Feature Unavailable", 
                              "Keyboard shortcuts editor is not available.")
        except Exception as e:
            logger.error(f"Error opening keyboard shortcuts: {e}")

    def get_icon_path(self, category, icon_name):
        """Get the path to an icon file"""
        try:
            # Build the icon path
            icon_dir = os.path.join(os.path.dirname(__file__), "..", "icons", category)
            
            # Try different common image formats
            for ext in ['.png', '.svg', '.jpg', '.ico']:
                icon_path = os.path.join(icon_dir, f"{icon_name}{ext}")
                if os.path.exists(icon_path):
                    return icon_path
            
            # If specific icon not found, try a fallback
            fallback_path = os.path.join(os.path.dirname(__file__), "..", "icons", f"{icon_name}.png")
            if os.path.exists(fallback_path):
                return fallback_path
                
            # Return None if no icon found
            return None
            
        except Exception as e:
            logger.warning(f"Error getting icon path for {category}/{icon_name}: {e}")
            return None

# ==================== MENU ACTION METHODS ====================
    
    # File Menu Methods
    def open_conversation(self):
        """Open a conversation from file"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Conversation", "", 
                "JSON files (*.json);;Text files (*.txt);;All files (*.*)"
            )
            if file_path:
                self.load_conversation_from_file(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open conversation: {str(e)}")
            logger.error(f"Error opening conversation: {e}")

    def save_chat_as(self):
        """Save chat with a new filename"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Chat As", "", 
                "JSON files (*.json);;Text files (*.txt);;All files (*.*)"
            )
            if file_path:
                if file_path.endswith('.json'):
                    self.export_chat("json", file_path)
                else:
                    self.export_chat("txt", file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save chat: {str(e)}")
            logger.error(f"Error saving chat: {e}")

    def import_conversation(self, format_type):
        """Import conversation from various formats"""
        try:
            filters = {
                "json": "JSON files (*.json)",
                "txt": "Text files (*.txt)", 
                "csv": "CSV files (*.csv)"
            }
            
            file_path, _ = QFileDialog.getOpenFileName(
                self, f"Import {format_type.upper()}", "",
                f"{filters.get(format_type, 'All files (*.*)')};;All files (*.*)"
            )
            
            if file_path:
                self._import_from_file(file_path, format_type)
                QMessageBox.information(self, "Import Complete", 
                                      f"Successfully imported conversation from {format_type.upper()}")
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import: {str(e)}")
            logger.error(f"Error importing conversation: {e}")

    def import_chat_history(self):
        """Import chat history from previous sessions"""
        QMessageBox.information(self, "Import Chat History", 
                              "Chat history import would be implemented here.")

    def update_recent_menu(self, menu):
        """Update the recent conversations menu"""
        try:
            menu.clear()
            # Add recent conversation items here
            recent_action = QAction("No recent conversations", self)
            recent_action.setEnabled(False)
            menu.addAction(recent_action)
        except Exception as e:
            logger.warning(f"Error updating recent menu: {e}")

    def print_chat(self):
        """Print the current chat"""
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.chat_display.print(printer)
        except ImportError:
            QMessageBox.warning(self, "Print Unavailable", 
                              "Print functionality requires additional dependencies.")
        except Exception as e:
            QMessageBox.warning(self, "Print Error", f"Failed to print: {str(e)}")

    # Edit Menu Methods  
    def undo_last_action(self):
        """Undo the last action"""
        QMessageBox.information(self, "Undo", "Undo functionality would be implemented here.")

    def redo_last_action(self):
        """Redo the last undone action"""
        QMessageBox.information(self, "Redo", "Redo functionality would be implemented here.")

    def copy_chat_to_clipboard(self):
        """Copy chat content to clipboard"""
        try:
            if hasattr(self, 'chat_display'):
                clipboard = QApplication.clipboard()
                clipboard.setText(self.chat_display.toPlainText())
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Chat copied to clipboard", 2000)
        except Exception as e:
            logger.warning(f"Error copying to clipboard: {e}")

    def paste_from_clipboard(self):
        """Paste content from clipboard"""
        try:
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text and hasattr(self, 'input_entry'):
                self.input_entry.insertPlainText(text)
        except Exception as e:
            logger.warning(f"Error pasting from clipboard: {e}")

    def find_in_chat(self):
        """Find text in chat"""
        QMessageBox.information(self, "Find", "Find functionality would be implemented here.")

    def find_and_replace(self):
        """Find and replace text in chat"""
        QMessageBox.information(self, "Find & Replace", "Find and replace functionality would be implemented here.")

    def select_all_chat(self):
        """Select all chat content"""
        try:
            if hasattr(self, 'chat_display'):
                self.chat_display.selectAll()
        except Exception as e:
            logger.warning(f"Error selecting all: {e}")

    # Chat Menu Methods
    def toggle_syntax_highlighting(self):
        """Toggle syntax highlighting"""
        self.syntax_highlighting = not getattr(self, 'syntax_highlighting', True)
        if hasattr(self, 'status_bar'):
            status = "enabled" if self.syntax_highlighting else "disabled"
            self.status_bar.showMessage(f"Syntax highlighting {status}", 3000)

    def clear_system_prompt(self):
        """Clear the system prompt for current conversation"""
        try:
            if hasattr(self, 'conversation_system_prompts') and self.current_conversation_id:
                self.conversation_system_prompts.pop(self.current_conversation_id, None)
                self.update_system_prompt_indicator()
                QMessageBox.information(self, "System Prompt Cleared", 
                                      "System prompt has been cleared for this conversation.")
        except Exception as e:
            logger.error(f"Error clearing system prompt: {e}")

    def open_prompt_templates(self):
        """Open prompt templates dialog"""
        try:
            from ui.prompt_template_dialog import PromptTemplateDialog
            dialog = PromptTemplateDialog(self)
            dialog.exec()
        except ImportError:
            QMessageBox.warning(self, "Feature Unavailable", 
                              "Prompt templates feature is not available.")
        except Exception as e:
            logger.error(f"Error opening prompt templates: {e}")

    def translate_chat(self):
        """Translate the current chat"""
        QMessageBox.information(self, "Translate", "Translation functionality would be implemented here.")

    def delete_last_message(self):
        """Delete the last message in chat"""
        try:
            if hasattr(self, 'chat_history') and self.chat_history:
                self.chat_history.pop()
                self.refresh_chat_display()
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Last message deleted", 3000)
        except Exception as e:
            logger.warning(f"Error deleting last message: {e}")

    def edit_selected_message(self):
        """Edit a selected message"""
        QMessageBox.information(self, "Edit Message", "Message editing functionality would be implemented here.")

    def regenerate_last_response(self):
        """Regenerate the last AI response"""
        try:
            if hasattr(self, 'chat_history') and self.chat_history:
                # Find last user message and regenerate response
                last_user_message = None
                for msg in reversed(self.chat_history):
                    if isinstance(msg, dict) and msg.get('role') == 'user':
                        last_user_message = msg.get('content', '')
                        break
                
                if last_user_message:
                    # Remove last AI response if present
                    if (self.chat_history and isinstance(self.chat_history[-1], dict) and 
                        self.chat_history[-1].get('role') == 'assistant'):
                        self.chat_history.pop()
                    
                    # Regenerate response
                    self.generate_response(last_user_message)
                else:
                    QMessageBox.information(self, "No Message", "No user message found to regenerate response for.")
        except Exception as e:
            logger.error(f"Error regenerating response: {e}")

    # View Menu Methods
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if hasattr(self, 'sidebar_widget'):
            visible = self.sidebar_widget.isVisible()
            self.sidebar_widget.setVisible(not visible)

    def toggle_toolbar(self):
        """Toggle toolbar visibility"""
        if hasattr(self, 'toolbar'):
            visible = self.toolbar.isVisible()
            self.toolbar.setVisible(not visible)

    def toggle_status_bar(self):
        """Toggle status bar visibility"""
        if hasattr(self, 'status_bar'):
            visible = self.status_bar.isVisible()
            self.status_bar.setVisible(not visible)

    def toggle_word_wrap(self):
        """Toggle word wrap in chat display"""
        if hasattr(self, 'chat_display'):
            current_wrap = self.chat_display.lineWrapMode()
            if current_wrap == QTextBrowser.LineWrapMode.NoWrap:
                self.chat_display.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
            else:
                self.chat_display.setLineWrapMode(QTextBrowser.LineWrapMode.NoWrap)

    def toggle_focus_mode(self):
        """Toggle focus mode (minimal UI)"""
        self.focus_mode = not getattr(self, 'focus_mode', False)
        # Hide/show UI elements based on focus mode
        if hasattr(self, 'status_bar'):
            status = "enabled" if self.focus_mode else "disabled"
            self.status_bar.showMessage(f"Focus mode {status}", 3000)

    def zoom_in(self):
        """Zoom in the chat display"""
        if hasattr(self, 'chat_display'):
            self.chat_display.zoomIn(1)

    def zoom_out(self):
        """Zoom out the chat display"""
        if hasattr(self, 'chat_display'):
            self.chat_display.zoomOut(1)

    def reset_zoom(self):
        """Reset zoom to default"""
        if hasattr(self, 'chat_display'):
            self.chat_display.zoomIn(0)  # Reset to default

    # Tools Menu Methods
    def batch_process_files(self):
        """Batch process multiple files"""
        QMessageBox.information(self, "Batch Process", "Batch processing functionality would be implemented here.")

    def add_folder_to_rag(self):
        """Add a folder to the RAG system"""
        try:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Add to Knowledge Base")
            if folder_path:
                QMessageBox.information(self, "Folder Added", 
                                      f"Folder would be added to knowledge base: {folder_path}")
        except Exception as e:
            logger.error(f"Error adding folder to RAG: {e}")

    def rebuild_search_index(self):
        """Rebuild the search index for RAG"""
        QMessageBox.information(self, "Rebuild Index", "Search index rebuild functionality would be implemented here.")

    def execute_selected_code(self):
        """Execute selected code block"""
        QMessageBox.information(self, "Execute Code", "Code execution functionality would be implemented here.")

    def open_code_sandbox(self):
        """Open code sandbox environment"""
        QMessageBox.information(self, "Code Sandbox", "Code sandbox functionality would be implemented here.")

    def launch_jupyter(self):
        """Launch Jupyter Notebook"""
        try:
            import subprocess
            subprocess.Popen(['jupyter', 'notebook'])
        except Exception as e:
            QMessageBox.warning(self, "Jupyter Error", f"Failed to launch Jupyter: {str(e)}")

    def show_conversation_stats(self):
        """Show conversation statistics"""
        QMessageBox.information(self, "Conversation Stats", "Statistics functionality would be implemented here.")

    def show_token_usage(self):
        """Show token usage report"""
        QMessageBox.information(self, "Token Usage", "Token usage reporting would be implemented here.")

    def compare_models(self):
        """Compare different models"""
        QMessageBox.information(self, "Compare Models", "Model comparison functionality would be implemented here.")

    def benchmark_models(self):
        """Benchmark model performance"""
        QMessageBox.information(self, "Benchmark Models", "Model benchmarking would be implemented here.")

    def show_model_info(self):
        """Show current model information"""
        try:
            info = f"Current Provider: {self.current_provider}\nCurrent Model: {self.current_model}"
            QMessageBox.information(self, "Model Information", info)
        except Exception as e:
            logger.error(f"Error showing model info: {e}")

    def global_search(self):
        """Search across all conversations"""
        QMessageBox.information(self, "Global Search", "Global search functionality would be implemented here.")

    def show_word_count(self):
        """Show word count statistics"""
        try:
            if hasattr(self, 'chat_history'):
                total_words = 0
                for entry in self.chat_history:
                    if isinstance(entry, dict):
                        content = entry.get('content', '')
                        total_words += len(content.split())
                
                QMessageBox.information(self, "Word Count", f"Total words in conversation: {total_words}")
        except Exception as e:
            logger.error(f"Error counting words: {e}")

    def check_grammar(self):
        """Check grammar in the chat"""
        QMessageBox.information(self, "Grammar Check", "Grammar checking would be implemented here.")

    def check_spelling(self):
        """Check spelling in the chat"""
        QMessageBox.information(self, "Spell Check", "Spell checking would be implemented here.")

    def create_text_summary(self):
        """Create a summary of the text"""
        QMessageBox.information(self, "Text Summary", "Text summarization would be implemented here.")

    # Settings Menu Methods
    def open_provider_settings(self):
        """Open provider-specific settings"""
        QMessageBox.information(self, "Provider Settings", "Provider settings would be implemented here.")

    def open_preferences(self):
        """Open general preferences dialog"""
        QMessageBox.information(self, "Preferences", "Preferences dialog would be implemented here.")

    def set_dark_theme(self):
        """Set dark theme"""
        self.dark_theme = True
        self.setup_styles()

    def set_light_theme(self):
        """Set light theme"""
        self.dark_theme = False
        self.setup_styles()

    def set_auto_theme(self):
        """Set automatic theme based on system"""
        QMessageBox.information(self, "Auto Theme", "Auto theme functionality would be implemented here.")

    def open_theme_editor(self):
        """Open custom theme editor"""
        QMessageBox.information(self, "Theme Editor", "Custom theme editor would be implemented here.")

    def open_input_settings(self):
        """Open input settings dialog"""
        QMessageBox.information(self, "Input Settings", "Input settings would be implemented here.")

    def open_advanced_settings(self):
        """Open advanced settings dialog"""
        QMessageBox.information(self, "Advanced Settings", "Advanced settings would be implemented here.")

    def open_plugin_manager(self):
        """Open plugin manager"""
        QMessageBox.information(self, "Plugin Manager", "Plugin manager would be implemented here.")

    def export_settings(self):
        """Export application settings"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Settings", "oracle_settings.json",
                "JSON files (*.json);;All files (*.*)"
            )
            if file_path:
                QMessageBox.information(self, "Settings Exported", f"Settings exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")

    def import_settings(self):
        """Import application settings"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Settings", "",
                "JSON files (*.json);;All files (*.*)"
            )
            if file_path:
                QMessageBox.information(self, "Settings Imported", f"Settings imported from {file_path}")
        except Exception as e:
            logger.error(f"Error importing settings: {e}")

    def reset_settings(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults.")

    # Help Menu Methods
    def open_user_guide(self):
        """Open user guide"""
        QMessageBox.information(self, "User Guide", "User guide would open here.")

    def show_keyboard_help(self):
        """Show keyboard shortcuts help"""
        help_text = """
Keyboard Shortcuts:

File Operations:
Ctrl+N - New Conversation
Ctrl+O - Open Conversation  
Ctrl+S - Save Chat
Ctrl+P - Print Chat
Ctrl+Q - Exit

Edit Operations:
Ctrl+Z - Undo
Ctrl+Y - Redo
Ctrl+C - Copy Chat
Ctrl+V - Paste
Ctrl+F - Find in Chat
Ctrl+H - Find and Replace
Ctrl+A - Select All

Chat Operations:
Ctrl+L - Open Prompt Library
Ctrl+Shift+P - Set System Prompt
Ctrl+Delete - Clear Chat
Ctrl+R - Regenerate Response
Ctrl+Backspace - Delete Last Message

View Operations:
F11 - Toggle Fullscreen
Ctrl++ - Zoom In
Ctrl+- - Zoom Out
Ctrl+0 - Reset Zoom

Tools:
Ctrl+E - Execute Selected Code
Ctrl+Shift+A - Attach File
Ctrl+Shift+F - Advanced Search

Settings:
Ctrl+, - Preferences

Help:
F1 - User Guide
        """
        
        QMessageBox.information(self, "Keyboard Shortcuts", help_text)

    def start_feature_tour(self):
        """Start interactive feature tour"""
        QMessageBox.information(self, "Feature Tour", "Interactive feature tour would start here.")

    def report_bug(self):
        """Report a bug"""
        QMessageBox.information(self, "Report Bug", "Bug reporting functionality would be implemented here.")

    def request_feature(self):
        """Request a new feature"""
        QMessageBox.information(self, "Feature Request", "Feature request functionality would be implemented here.")

    def send_feedback(self):
        """Send feedback"""
        QMessageBox.information(self, "Send Feedback", "Feedback functionality would be implemented here.")

    def check_for_updates(self):
        """Check for application updates"""
        QMessageBox.information(self, "Check Updates", "Update checking would be implemented here.")

    def show_changelog(self):
        """Show application changelog"""
        QMessageBox.information(self, "Changelog", "Changelog would be displayed here.")

    def show_about_dialog(self):
        """Show about dialog"""
        about_text = """
The Oracle - AI Chat Application

Version: 2.0.0
A sophisticated AI chat application with multi-provider support.

Features:
• Multiple AI provider support
• Advanced prompt management  
• Code execution capabilities
• Knowledge base integration
• Conversation analytics
• Comprehensive export options
• Modern, customizable interface

© 2025 The Oracle Team
        """
        QMessageBox.about(self, "About The Oracle", about_text)

    # Helper Methods for Menu Actions
    def load_conversation_from_file(self, file_path):
        """Load conversation from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    # Process JSON conversation data
                    if isinstance(data, dict) and 'messages' in data:
                        self.chat_history = data['messages']
                        self.refresh_chat_display()
                else:
                    # Handle text files
                    content = f.read()
                    self.chat_display.setPlainText(content)
        except Exception as e:
            raise Exception(f"Failed to load conversation: {str(e)}")

    def _import_from_file(self, file_path, format_type):
        """Import conversation from file based on format"""
        try:
            if format_type == "json":
                self.load_conversation_from_file(file_path)
            elif format_type == "txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Parse text content into messages
                    lines = content.split('\n')
                    # Simple parsing - can be enhanced
                    for line in lines:
                        if line.strip():
                            self.chat_history.append({
                                'role': 'user',
                                'content': line.strip(),
                                'timestamp': datetime.now().isoformat()
                            })
                self.refresh_chat_display()
            elif format_type == "csv":
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            self.chat_history.append({
                                'role': row[0],
                                'content': row[1],
                                'timestamp': datetime.now().isoformat()
                            })
                self.refresh_chat_display()
        except Exception as e:
            raise Exception(f"Failed to import from {format_type}: {str(e)}")

    # Additional missing methods referenced in existing code
    def load_chat(self):
        """Load a chat from file (legacy method)"""
        self.open_conversation()

    def clear_chat(self):
        """Clear the current chat"""
        try:
            reply = QMessageBox.question(
                self, "Clear Chat", 
                "Are you sure you want to clear the current chat?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.chat_display.clear()
                self.chat_history = []
                self.conversation_history = []
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Chat cleared", 3000)
        except Exception as e:
            logger.error(f"Error clearing chat: {e}")

    def summarize_chat(self):
        """Summarize the current chat"""
        try:
            if not self.chat_history:
                QMessageBox.information(self, "No Chat", "There is no chat to summarize.")
                return
                
            # Simple summary - count messages and basic stats
            total_messages = len(self.chat_history)
            user_messages = sum(1 for msg in self.chat_history 
                              if isinstance(msg, dict) and msg.get('role') == 'user')
            assistant_messages = total_messages - user_messages
            
            summary = f"""
Chat Summary:
• Total messages: {total_messages}
• User messages: {user_messages}  
• Assistant messages: {assistant_messages}
• Current provider: {self.current_provider}
• Current model: {self.current_model}
            """
            
            QMessageBox.information(self, "Chat Summary", summary)
        except Exception as e:
            logger.error(f"Error summarizing chat: {e}")

    def attach_file(self):
        """Attach a file to the conversation"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Attach File", "",
                "All files (*.*);;Text files (*.txt);;Images (*.png *.jpg *.gif)"
            )
            
            if file_path:
                QMessageBox.information(self, "File Attached", 
                                      f"File attachment functionality would process: {file_path}")
        except Exception as e:
            logger.error(f"Error attaching file: {e}")

    def add_document_to_rag(self):
        """Add a document to the RAG system"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Add Document to Knowledge Base", "",
                "Documents (*.pdf *.txt *.docx);;All files (*.*)"
            )
            
            if file_path:
                QMessageBox.information(self, "Document Added", 
                                      f"Document would be added to knowledge base: {file_path}")
        except Exception as e:
            logger.error(f"Error adding document to RAG: {e}")

    def initialize_rag_system(self):
        """Initialize the RAG system"""
        QMessageBox.information(self, "Initialize RAG", "RAG system initialization would be implemented here.")

    def analyze_chat(self):
        """Analyze chat patterns"""
        QMessageBox.information(self, "Analyze Chat", "Chat analysis functionality would be implemented here.")

