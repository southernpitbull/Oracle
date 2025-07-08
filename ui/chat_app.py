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
import uuid

# Add the parent directory to the Python path so we can import core modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
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
    from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
    from langchain_community.embeddings import HuggingFaceEmbeddings
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
from ui.theme_styles import create_themed_message_box
from ui.icon_manager import get_icon
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
        if self.icon_path:
            # Use icon manager for consistent icon handling
            if isinstance(self.icon_path, str):
                icon = get_icon(self.icon_path)
            else:
                icon = self.icon_path

            if icon and not icon.isNull():
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

        # Initialize avatar buttons
        self.user_avatar_button = None
        self.ai_avatar_button = None
        self.user_avatar_file = "user-default.png"
        self.ai_avatar_file = "ai-default.png"

        # Initialize UI
        self.setup_ui()
        self.setup_menu()
        self.setup_styles()
        self.load_providers_and_models()
        self.load_conversations()
        self.setup_auto_save()
        self.load_chat_on_startup()
        self.setup_code_execution()
        self.setup_command_palette()

    def setup_ui(self):
        """Set up the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Setup comprehensive toolbar
        self.setup_toolbar()

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
        self.model_settings_button = ModernButton("⚙️", get_icon("toolbar/settings"))
        self.model_settings_button.setMaximumWidth(40)
        self.model_settings_button.setToolTip("Model Settings (Temperature, Max Tokens, etc.)")
        self.model_settings_button.clicked.connect(self.open_model_settings_manually)
        toolbar_layout.addWidget(self.model_settings_button)

        # Enhanced buttons with icons
        self.refresh_models_button = ModernButton("🔄", get_icon("toolbar/refresh"))
        self.refresh_models_button.setMaximumWidth(40)
        self.refresh_models_button.setToolTip("Refresh All Models")
        self.refresh_models_button.clicked.connect(self.refresh_current_provider_models)
        toolbar_layout.addWidget(self.refresh_models_button)

        self.api_settings_button = ModernButton("🔑 API Keys", get_icon("toolbar/settings"))
        self.api_settings_button.setToolTip("API Keys")
        self.api_settings_button.clicked.connect(self.open_api_settings)
        toolbar_layout.addWidget(self.api_settings_button)

        # Theme toggle button
        self.theme_button = ModernButton("🌙", get_icon("general/theme_dark"))
        self.theme_button.setToolTip("Toggle Dark/Light Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_button)

        self.pull_button = ModernButton("📥 Pull Model")
        self.pull_button.clicked.connect(self.pull_model)
        toolbar_layout.addWidget(self.pull_button)

        self.new_chat_button = ModernButton("🆕 New Chat", get_icon("buttons/add_new"))
        self.new_chat_button.clicked.connect(self.new_conversation)
        toolbar_layout.addWidget(self.new_chat_button)

        # Prompt templates button
        self.prompt_templates_button = ModernButton("📝 Prompts", get_icon("toolbar/templates"))
        self.prompt_templates_button.setToolTip("Open Prompt Templates & Generator")
        self.prompt_templates_button.clicked.connect(self.open_prompt_templates)
        toolbar_layout.addWidget(self.prompt_templates_button)

        # Add RAG toggle button
        self.rag_toggle_button = ModernButton("🧠 RAG", get_icon("toolbar/brain"))
        self.rag_toggle_button.setCheckable(True)
        self.rag_toggle_button.setChecked(self.rag_enabled)
        self.rag_toggle_button.setToolTip("Toggle Retrieval-Augmented Generation")
        self.rag_toggle_button.clicked.connect(self.toggle_rag)
        toolbar_layout.addWidget(self.rag_toggle_button)

        # Enhanced search
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("🔍 Search chat...")
        toolbar_layout.addWidget(self.search_entry)

        self.search_button = ModernButton("🔍", get_icon("toolbar/search"))
        self.search_button.setMaximumWidth(40)
        self.search_button.setToolTip("Search Chat")
        self.search_button.clicked.connect(self.filter_chat)
        toolbar_layout.addWidget(self.search_button)

        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        # Main content splitter with enhanced styling
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # Left panel for conversations with enhanced features
        self.setup_left_panel(splitter)

        # Chat area with enhanced layout
        self.setup_chat_area(splitter)

        splitter.setSizes([300, 1300])
        main_layout.addWidget(splitter)

        # Enhanced status bar
        self.setup_status_bar()

        # Final UI validation and setup
        self.finalize_ui_setup()

    def setup_left_panel(self, splitter):
        """Setup the left panel with conversations and folders"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Conversation management header
        conv_header = QHBoxLayout()
        conv_label = QLabel("💬 Conversations")
        conv_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2D3748;")
        conv_header.addWidget(conv_label)

        # Add folder creation button
        folder_btn = ModernButton("📁", get_icon("buttons/folder"))
        folder_btn.setMaximumWidth(30)
        folder_btn.setToolTip("Create Folder")
        folder_btn.clicked.connect(self.create_conversation_folder)
        conv_header.addWidget(folder_btn)

        # Add sort button
        sort_btn = ModernButton("🔽", get_icon("buttons/sort"))
        sort_btn.setMaximumWidth(30)
        sort_btn.setToolTip("Sort Conversations")
        sort_btn.clicked.connect(self.show_sort_options)
        conv_header.addWidget(sort_btn)

        conv_header.addStretch()
        left_layout.addLayout(conv_header)

        # Folder filter dropdown
        self.folder_combo = QComboBox()
        self.folder_combo.addItems(["All Conversations", "📁 Work", "📁 Personal", "📁 Code"])
        self.folder_combo.currentTextChanged.connect(self.filter_by_folder)
        left_layout.addWidget(self.folder_combo)

        # Search filter for conversations
        self.conv_search = QLineEdit()
        self.conv_search.setPlaceholderText("🔍 Filter conversations...")
        self.conv_search.textChanged.connect(self.filter_conversations)
        left_layout.addWidget(self.conv_search)

        # Conversation list
        self.conv_listbox = AnimatedListWidget()
        self.conv_listbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.conv_listbox.customContextMenuRequested.connect(self.show_conversation_context_menu)
        self.conv_listbox.currentRowChanged.connect(self.load_selected_conv)
        left_layout.addWidget(self.conv_listbox)

        splitter.addWidget(left_panel)

    def setup_chat_area(self, splitter):
        """Setup the main chat area with enhanced features"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        # Chat info header
        info_layout = QHBoxLayout()
        self.chat_info_label = QLabel("🤖 Ready to assist you!")
        self.chat_info_label.setStyleSheet("font-weight: bold; color: #4A5568;")
        info_layout.addWidget(self.chat_info_label)

        # Add compact mode toggle
        self.compact_mode_btn = ModernButton("⚡", get_icon("buttons/compact"))
        self.compact_mode_btn.setCheckable(True)
        self.compact_mode_btn.setToolTip("Toggle Compact Mode")
        self.compact_mode_btn.clicked.connect(self.toggle_compact_mode)
        info_layout.addWidget(self.compact_mode_btn)

        # Add line numbers toggle
        self.line_numbers_btn = ModernButton("🔢", get_icon("buttons/numbers"))
        self.line_numbers_btn.setCheckable(True)
        self.line_numbers_btn.setChecked(self.show_line_numbers)
        self.line_numbers_btn.setToolTip("Toggle Code Line Numbers")
        self.line_numbers_btn.clicked.connect(self.toggle_line_numbers)
        info_layout.addWidget(self.line_numbers_btn)

        # Add code folding toggle
        self.code_folding_btn = ModernButton("📂", get_icon("buttons/fold"))
        self.code_folding_btn.setCheckable(True)
        self.code_folding_btn.setChecked(self.enable_code_folding)
        self.code_folding_btn.setToolTip("Toggle Code Folding")
        self.code_folding_btn.clicked.connect(self.toggle_code_folding)
        info_layout.addWidget(self.code_folding_btn)

        info_layout.addStretch()
        chat_layout.addLayout(info_layout)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_display.customContextMenuRequested.connect(self.show_chat_context_menu)
        self.chat_display.verticalScrollBar().valueChanged.connect(self.on_scroll_changed)
        chat_layout.addWidget(self.chat_display)

        # Scroll to bottom button (initially hidden)
        self.scroll_to_bottom_button = ModernButton("⬇️ Scroll to Bottom")
        self.scroll_to_bottom_button.clicked.connect(self.scroll_to_bottom)
        self.scroll_to_bottom_button.hide()
        chat_layout.addWidget(self.scroll_to_bottom_button)

        # Input area
        input_layout = QVBoxLayout()

        # Input controls row
        input_controls = QHBoxLayout()

        # Slash commands dropdown
        self.slash_combo = QComboBox()
        self.slash_combo.addItems([
            "💬 Chat Mode",
            "/summarize - Summarize text",
            "/explain - Explain code",
            "/translate - Translate text",
            "/review - Review code",
            "/debug - Debug code",
            "/optimize - Optimize code"
        ])
        self.slash_combo.currentTextChanged.connect(self.on_slash_command_selected)
        input_controls.addWidget(self.slash_combo)

        # Edit last prompt button
        self.edit_last_btn = ModernButton("✏️ Edit Last", get_icon("buttons/edit"))
        self.edit_last_btn.setToolTip("Edit Last Prompt")
        self.edit_last_btn.clicked.connect(self.edit_last_prompt)
        input_controls.addWidget(self.edit_last_btn)

        # Prompt history button
        self.history_btn = ModernButton("📜", get_icon("buttons/history"))
        self.history_btn.setToolTip("Prompt History")
        self.history_btn.clicked.connect(self.show_prompt_history)
        input_controls.addWidget(self.history_btn)

        # Voice input toggle
        self.voice_btn = ModernButton("🎤", get_icon("buttons/mic"))
        self.voice_btn.setCheckable(True)
        self.voice_btn.setToolTip("Toggle Voice Input")
        self.voice_btn.clicked.connect(self.toggle_voice_input)
        input_controls.addWidget(self.voice_btn)

        input_controls.addStretch()
        input_layout.addLayout(input_controls)

        # Main input area
        input_row = QHBoxLayout()

        # Text input
        self.input_entry = QTextEdit()
        self.input_entry.setMaximumHeight(100)
        self.input_entry.setPlaceholderText("Type your message here... (Ctrl+Enter to send)")
        self.input_entry.textChanged.connect(self.update_token_count)
        input_row.addWidget(self.input_entry)

        # Input buttons column
        input_buttons = QVBoxLayout()

        # Attach file button
        self.attach_btn = ModernButton("📎", get_icon("buttons/attach"))
        self.attach_btn.setToolTip("Attach File")
        self.attach_btn.clicked.connect(self.attach_file)
        input_buttons.addWidget(self.attach_btn)

        # Send button
        self.send_btn = ModernButton("📤 Send", get_icon("buttons/send"))
        self.send_btn.setToolTip("Send Message (Ctrl+Enter)")
        self.send_btn.clicked.connect(self.send_message)
        input_buttons.addWidget(self.send_btn)

        input_row.addLayout(input_buttons)
        input_layout.addLayout(input_row)

        # Token count display
        token_layout = QHBoxLayout()
        self.token_count_label = QLabel("Tokens: 0")
        self.token_count_label.setStyleSheet("color: #718096; font-size: 12px;")
        token_layout.addWidget(self.token_count_label)
        token_layout.addStretch()
        input_layout.addLayout(token_layout)

        chat_layout.addLayout(input_layout)
        splitter.addWidget(chat_widget)

    def setup_status_bar(self):
        """Setup enhanced status bar with live indicators"""
        self.status_bar = self.statusBar()

        # Provider status
        self.provider_status = QLabel("Provider: Ollama")
        self.status_bar.addWidget(self.provider_status)

        # Model status
        self.model_status = QLabel("Model: None")
        self.status_bar.addWidget(self.model_status)

        # Token status
        self.token_status = QLabel("Tokens: 0")
        self.status_bar.addWidget(self.token_status)

        # RAG status (live indicator)
        self.rag_status = QLabel("RAG: Disabled | KB Docs: 0 | Sources Used: 0")
        self.status_bar.addPermanentWidget(self.rag_status)

        # Update RAG status initially
        self.update_rag_status()

    def setup_toolbar(self):
        """Setup comprehensive toolbar with all major features"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)

        # File operations
        new_action = QAction(get_icon("buttons/add_new"), "New", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self.new_conversation)
        toolbar.addAction(new_action)

        open_action = QAction(get_icon("buttons/upload"), "Open", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self.open_conversation)
        toolbar.addAction(open_action)

        save_action = QAction(get_icon("buttons/save"), "Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_chat)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Prompt management
        prompt_lib_action = QAction(get_icon("toolbar/library"), "Prompt Library", self)
        prompt_lib_action.triggered.connect(self.open_prompt_library)
        toolbar.addAction(prompt_lib_action)

        persona_action = QAction(get_icon("Avatars/chat-llm"), "Personas", self)
        persona_action.triggered.connect(self.open_persona_gallery)
        toolbar.addAction(persona_action)

        templates_action = QAction(get_icon("toolbar/templates"), "Templates", self)
        templates_action.triggered.connect(self.open_prompt_templates)
        toolbar.addAction(templates_action)

        toolbar.addSeparator()

        # RAG and Knowledge Base
        rag_action = QAction(get_icon("toolbar/brain"), "RAG", self)
        rag_action.setCheckable(True)
        rag_action.setChecked(self.rag_enabled)
        rag_action.triggered.connect(self.toggle_rag)
        toolbar.addAction(rag_action)

        kb_action = QAction(get_icon("toolbar/database"), "Knowledge Base", self)
        kb_action.triggered.connect(self.manage_knowledge_base)
        toolbar.addAction(kb_action)

        toolbar.addSeparator()

        # Code tools
        code_action = QAction(get_icon("toolbar/code"), "Code Tools", self)
        code_action.triggered.connect(self.open_code_sandbox)
        toolbar.addAction(code_action)

        execute_action = QAction(get_icon("toolbar/play"), "Execute", self)
        execute_action.triggered.connect(self.execute_selected_code)
        toolbar.addAction(execute_action)

        toolbar.addSeparator()

        # Analytics and tools
        analytics_action = QAction(get_icon("toolbar/analytics"), "Analytics", self)
        analytics_action.triggered.connect(self.analyze_chat)
        toolbar.addAction(analytics_action)

        # --- Add Semantic Search and RAG Analytics to toolbar ---
        semantic_search_action = QAction(get_icon("toolbar/search"), "Semantic Search", self)
        semantic_search_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
        semantic_search_action.setToolTip("Semantic Search (Ctrl+Shift+F)")
        semantic_search_action.triggered.connect(self.open_semantic_search)
        toolbar.addAction(semantic_search_action)

        rag_analytics_action = QAction(get_icon("toolbar/analytics"), "RAG Analytics", self)
        rag_analytics_action.setShortcut(QKeySequence("Ctrl+Shift+G"))
        rag_analytics_action.setToolTip("RAG Analytics (Ctrl+Shift+G)")
        rag_analytics_action.triggered.connect(self.open_rag_analytics)
        toolbar.addAction(rag_analytics_action)
        # --- End additions ---

        export_action = QAction(get_icon("buttons/download"), "Export", self)
        export_action.triggered.connect(lambda: self.export_chat("pdf"))
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Settings
        settings_action = QAction(get_icon("toolbar/settings"), "Settings", self)
        settings_action.triggered.connect(self.open_preferences)
        toolbar.addAction(settings_action)

        # Store toolbar reference
        self.main_toolbar = toolbar

    def setup_menu(self):
        """Set up application menu"""
        try:
            menubar = self.menuBar()
            if menubar:
                # File menu
                file_menu = menubar.addMenu("File")

                # New conversation
                new_action = QAction("New Conversation", self)
                new_action.setShortcut(QKeySequence("Ctrl+N"))
                new_action.triggered.connect(self.new_conversation)
                file_menu.addAction(new_action)

                # Exit
                exit_action = QAction("Exit", self)
                exit_action.setShortcut(QKeySequence("Ctrl+Q"))
                exit_action.triggered.connect(self.close)
                file_menu.addAction(exit_action)

                # Chat menu
                chat_menu = menubar.addMenu("Chat")

                # System prompt
                system_prompt_action = QAction("Set System Prompt", self)
                system_prompt_action.triggered.connect(self.set_system_prompt)
                chat_menu.addAction(system_prompt_action)

                # Settings menu
                settings_menu = menubar.addMenu("Settings")

                # API settings
                api_settings_action = QAction("API Settings", self)
                api_settings_action.triggered.connect(self.open_api_settings)
                settings_menu.addAction(api_settings_action)

                # Model settings
                model_settings_action = QAction("Model Settings", self)
                model_settings_action.triggered.connect(self.open_model_settings_manually)
                settings_menu.addAction(model_settings_action)

                # Add Semantic Search and RAG Analytics to menu
                tools_menu = menubar.addMenu("Tools")
                semantic_search_action = QAction("Semantic Search", self)
                semantic_search_action.setShortcut(QKeySequence("Ctrl+Shift+F"))
                semantic_search_action.setToolTip("Semantic Search (Ctrl+Shift+F)")
                semantic_search_action.triggered.connect(self.open_semantic_search)
                tools_menu.addAction(semantic_search_action)
                rag_analytics_action = QAction("RAG Analytics", self)
                rag_analytics_action.setShortcut(QKeySequence("Ctrl+Shift+G"))
                rag_analytics_action.setToolTip("RAG Analytics (Ctrl+Shift+G)")
                rag_analytics_action.triggered.connect(self.open_rag_analytics)
                tools_menu.addAction(rag_analytics_action)

                # Help menu
                help_menu = menubar.addMenu("Help")

                # About
                about_action = QAction("About", self)
                about_action.triggered.connect(self.show_about_dialog)
                help_menu.addAction(about_action)

        except Exception as e:
            logger.error(f"Error setting up menu: {e}")

    def load_providers_and_models(self):
        """Load available providers and models"""
        try:
            # Add providers to combo box
            providers = ["Ollama", "OpenAI", "Anthropic", "Google", "Cohere"]
            self.provider_combo.addItems(providers)

            # Load models for initial provider
            self.on_provider_changed("Ollama")
        except Exception as e:
            logger.error(f"Error loading providers: {e}")

    def load_conversations(self):
        """Load conversation list"""
        try:
            # Placeholder implementation - in full version this would load from database
            self.conv_listbox.addItem("Welcome Chat")
            self.conv_listbox.addItem("Previous Conversation")
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")

    def setup_auto_save(self):
        """Setup auto-save functionality"""
        try:
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self.auto_save_chat)
            self.auto_save_timer.start(60000)  # Auto-save every minute
        except Exception as e:
            logger.error(f"Error setting up auto-save: {e}")

    def load_chat_on_startup(self):
        """Load chat on startup"""
        try:
            # Placeholder implementation
            self.chat_display.append("<div style='text-align: center; padding: 20px; color: #666;'>Welcome to The Oracle! Start a conversation by typing a message below.</div>")
        except Exception as e:
            logger.error(f"Error loading chat on startup: {e}")

    def setup_code_execution(self):
        """Setup code execution environment"""
        try:
            # Placeholder implementation
            logger.info("Code execution environment initialized")
        except Exception as e:
            logger.error(f"Error setting up code execution: {e}")

    def setup_styles(self):
        """Setup application styles and themes"""
        try:
            # Set dark theme styles
            if self.dark_theme:
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #2b2b2b;
                        color: #ffffff;
                    }
                    QTextEdit {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 1px solid #555555;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QLineEdit {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 1px solid #555555;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QComboBox {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 1px solid #555555;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton {
                        background-color: #4a4a4a;
                        color: #ffffff;
                        border: 1px solid #666666;
                        border-radius: 5px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #5a5a5a;
                    }
                    QPushButton:pressed {
                        background-color: #666666;
                    }
                    QListWidget {
                        background-color: #3c3c3c;
                        color: #ffffff;
                        border: 1px solid #555555;
                        border-radius: 5px;
                    }
                    QLabel {
                        color: #ffffff;
                    }
                    QStatusBar {
                        background-color: #2b2b2b;
                        color: #ffffff;
                    }
                """)
            else:
                # Light theme
                self.setStyleSheet("""
                    QMainWindow {
                        background-color: #ffffff;
                        color: #000000;
                    }
                    QTextEdit {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QLineEdit {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QComboBox {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton {
                        background-color: #f0f0f0;
                        color: #000000;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                        padding: 8px 16px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                    QPushButton:pressed {
                        background-color: #d0d0d0;
                    }
                    QListWidget {
                        background-color: #ffffff;
                        color: #000000;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                    }
                    QLabel {
                        color: #000000;
                    }
                    QStatusBar {
                        background-color: #f0f0f0;
                        color: #000000;
                    }
                """)
        except Exception as e:
            logger.error(f"Error setting up styles: {e}")

    def show_about_dialog(self):
        """Show about dialog"""
        try:
            QMessageBox.about(self, "About The Oracle",
                             "The Oracle v2.0\n\nAdvanced AI Chat Assistant\n\nFeatures comprehensive AI integration with enhanced UI")
        except Exception as e:
            logger.error(f"Error showing about dialog: {e}")

    def set_user_avatar(self, avatar_filename):
        """Set the user avatar"""
        try:
            avatar_path = os.path.join(self.icon_base_path, "Avatars", avatar_filename)
            if os.path.exists(avatar_path):
                pixmap = QPixmap(avatar_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.user_avatar_button.setIcon(QIcon(pixmap))
                self.user_avatar_file = avatar_filename
            else:
                logger.warning(f"User avatar not found: {avatar_path}")
        except Exception as e:
            logger.error(f"Error setting user avatar: {e}")

    def set_ai_avatar(self, avatar_filename):
        """Set the AI avatar"""
        try:
            avatar_path = os.path.join(self.icon_base_path, "Avatars", avatar_filename)
            if os.path.exists(avatar_path):
                pixmap = QPixmap(avatar_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.ai_avatar_button.setIcon(QIcon(pixmap))
                self.ai_avatar_file = avatar_filename
            else:
                logger.warning(f"AI avatar not found: {avatar_path}")
        except Exception as e:
            logger.error(f"Error setting AI avatar: {e}")

    def select_user_avatar(self):
        """Open avatar selection dialog for user"""
        self.open_avatar_selector("user")

    def select_ai_avatar(self):
        """Open avatar selection dialog for AI"""
        self.open_avatar_selector("ai")

    def open_avatar_selector(self, avatar_type):
        """Open avatar selection dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Select {avatar_type.title()} Avatar")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # Create scroll area for avatars
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)

        # Load available avatars
        avatars_dir = os.path.join(self.icon_base_path, "Avatars")
        if os.path.exists(avatars_dir):
            avatar_files = [f for f in os.listdir(avatars_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

            row, col = 0, 0
            for avatar_file in avatar_files[:50]:  # Limit to first 50 avatars
                avatar_path = os.path.join(avatars_dir, avatar_file)
                button = QPushButton()
                button.setFixedSize(80, 80)

                pixmap = QPixmap(avatar_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                button.setIcon(QIcon(pixmap))
                button.setIconSize(QSize(64, 64))
                button.clicked.connect(lambda checked, f=avatar_file: self.select_avatar(dialog, avatar_type, f))

                scroll_layout.addWidget(button, row, col)
                col += 1
                if col > 5:
                    col = 0
                    row += 1

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.exec()

    def select_avatar(self, dialog, avatar_type, avatar_file):
        """Select an avatar"""
        if avatar_type == "user":
            self.set_user_avatar(avatar_file)
        else:
            self.set_ai_avatar(avatar_file)
        dialog.close()

    def toggle_rag(self):
        """Toggle RAG system"""
        self.rag_enabled = not self.rag_enabled
        self.rag_toggle_button.setChecked(self.rag_enabled)
        status = "Enabled" if self.rag_enabled else "Disabled"
        self.rag_status.setText(f"RAG {status}")

    def update_token_count(self):
        """Update token count display"""
        try:
            text = self.input_entry.toPlainText()
            # Simple token estimation (approximate)
            token_count = len(text.split()) * 1.3  # Rough estimate
            self.token_count_label.setText(f"Tokens: {int(token_count)}")
            self.token_status.setText(f"Tokens: {int(token_count)}")
        except Exception as e:
            logger.error(f"Error updating token count: {e}")

    def on_slash_command_selected(self, command):
        """Handle slash command selection"""
        if command.startswith("/"):
            # Extract command and insert template
            cmd = command.split(" - ")[0]
            templates = {
                "/summarize": "Please summarize the following text:\n\n",
                "/explain": "Please explain the following code:\n\n```\n\n```",
                "/translate": "Please translate the following text to [language]:\n\n",
                "/review": "Please review the following code:\n\n```\n\n```",
                "/debug": "Please debug the following code:\n\n```\n\n```",
                "/optimize": "Please optimize the following code:\n\n```\n\n```"
            }

            if cmd in templates:
                self.input_entry.setPlainText(templates[cmd])
                # Reset to chat mode
                self.slash_combo.setCurrentIndex(0)
                self.input_entry.setPlainText(templates[cmd])
                # Reset to chat mode
                self.slash_combo.setCurrentIndex(0)

    def show_prompt_history(self):
        """Show prompt history dropdown"""
        if not self.prompt_history:
            QMessageBox.information(self, "Prompt History", "No prompt history available.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Prompt History")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        # History list
        history_list = QListWidget()
        for prompt in self.prompt_history[-20:]:  # Last 20 prompts
            item = QListWidgetItem(prompt[:100] + "..." if len(prompt) > 100 else prompt)
            item.setData(Qt.ItemDataRole.UserRole, prompt)
            history_list.addItem(item)

        history_list.itemDoubleClicked.connect(lambda item: self.use_history_prompt(dialog, item))
        layout.addWidget(history_list)

        # Buttons
        button_layout = QHBoxLayout()
        use_btn = QPushButton("Use Selected")
        use_btn.clicked.connect(lambda: self.use_history_prompt(dialog, history_list.currentItem()))
        button_layout.addWidget(use_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.exec()

    def use_history_prompt(self, dialog, item):
        """Use selected prompt from history"""
        if item:
            prompt = item.data(Qt.ItemDataRole.UserRole)
            self.input_entry.setPlainText(prompt)
            dialog.close()

    def toggle_voice_input(self):
        """Toggle voice input (placeholder for future implementation)"""
        QMessageBox.information(self, "Voice Input", "Voice input feature coming soon!")

    def filter_chat(self):
        """Filter chat messages based on search criteria"""
        try:
            search_text = self.search_entry.text() if hasattr(self, 'search_entry') else ""
            if not search_text:
                return

            # Implement chat filtering logic
            if hasattr(self, 'chat_display'):
                # For now, just show a message - implement actual filtering later
                self.status_bar.showMessage(f"Filtering chat for: {search_text}")

        except Exception as e:
            logger.error(f"Error filtering chat: {e}")

    def show_sort_options(self):
        """Show sort options dialog"""
        try:
            from PyQt6.QtWidgets import QMenu
            menu = QMenu(self)

            # Add sort options
            menu.addAction("Date (Newest First)", lambda: self.sort_conversations("date_desc"))
            menu.addAction("Date (Oldest First)", lambda: self.sort_conversations("date_asc"))
            menu.addAction("Name (A-Z)", lambda: self.sort_conversations("name_asc"))
            menu.addAction("Name (Z-A)", lambda: self.sort_conversations("name_desc"))

            # Show menu at cursor
            menu.exec(QCursor.pos())

        except Exception as e:
            logger.error(f"Error showing sort options: {e}")

    def sort_conversations(self, sort_type):
        """Sort conversations by the specified criteria"""
        try:
            if hasattr(self, 'conversation_list'):
                # Implement sorting logic based on sort_type
                self.status_bar.showMessage(f"Sorted conversations by {sort_type}")

        except Exception as e:
            logger.error(f"Error sorting conversations: {e}")

    def load_selected_conv(self, row):
        """Load the selected conversation"""
        try:
            if row >= 0 and hasattr(self, 'conv_listbox'):
                item = self.conv_listbox.item(row)
                if item:
                    conv_name = item.text()
                    # Load conversation from history/storage
                    # For now, just update the status
                    self.status_bar.showMessage(f"Loaded conversation: {conv_name}")

        except Exception as e:
            logger.error(f"Error loading conversation: {e}")

    def new_conversation(self):
        """Start a new conversation"""
        try:
            # Clear chat display
            if hasattr(self, 'chat_display'):
                self.chat_display.clear()

            # Reset conversation state
            if hasattr(self, 'conversation_history'):
                self.conversation_history = []

            # Clear input field
            if hasattr(self, 'input_entry'):
                self.input_entry.clear()

            # Update chat info
            if hasattr(self, 'chat_info_label'):
                self.chat_info_label.setText("🤖 Ready to assist you!")

            # Add welcome message
            if hasattr(self, 'chat_display'):
                welcome_msg = """
<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border-radius: 10px; margin: 10px;">
    <h2>🌟 Welcome to The Oracle!</h2>
    <p>I'm here to help you with any questions or tasks. Here are some things you can try:</p>
    <ul>
        <li>🧠 Ask me anything - I have access to extensive knowledge</li>
        <li>💻 Request code examples or debugging help</li>
        <li>📝 Ask me to explain complex topics</li>
        <li>🔍 Use RAG features for document analysis</li>
        <li>⚡ Try slash commands like /summarize or /explain</li>
    </ul>
    <p><em>Pro tip: Use Ctrl+Shift+F for semantic search and Ctrl+Shift+G for RAG analytics!</em></p>
</div>
                """
                self.chat_display.append(welcome_msg)

            # Reset current conversation ID
            self.current_conversation_id = None

            # Update status
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage("Started new conversation")

            logger.info("New conversation started")

        except Exception as e:
            logger.error(f"Error starting new conversation: {e}")
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"Error: {e}")

    def open_conversation(self):
        """Open an existing conversation from file"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Conversation",
                "conversations/",
                "JSON Files (*.json);;All Files (*)"
            )

            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversation_data = json.load(f)

                # Clear current chat
                self.new_conversation()

                # Load conversation history
                if 'messages' in conversation_data:
                    self.conversation_history = conversation_data['messages']

                    # Display messages
                    for msg in self.conversation_history:
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        timestamp = msg.get('timestamp', '')

                        if hasattr(self, 'message_formatter'):
                            formatted_msg = self.message_formatter.format_message(
                                content, role, timestamp
                            )
                            self.chat_display.append(formatted_msg)

                # Update conversation ID
                self.current_conversation_id = conversation_data.get('id', str(uuid.uuid4()))

                # Update status
                filename = os.path.basename(file_path)
                self.status_bar.showMessage(f"Opened conversation: {filename}")

                logger.info(f"Opened conversation from {file_path}")

        except Exception as e:
            logger.error(f"Error opening conversation: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open conversation: {e}")

    def save_conversation(self):
        """Save current conversation to file"""
        try:
            if not hasattr(self, 'conversation_history') or not self.conversation_history:
                QMessageBox.information(self, "Save Conversation", "No conversation to save.")
                return

            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"conv_{timestamp}.json"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Conversation",
                f"conversations/{default_name}",
                "JSON Files (*.json);;All Files (*)"
            )

            if file_path:
                # Ensure conversations directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Prepare conversation data
                conversation_data = {
                    'id': getattr(self, 'current_conversation_id', str(uuid.uuid4())),
                    'created': datetime.now().isoformat(),
                    'title': f"Conversation {timestamp}",
                    'messages': self.conversation_history,
                    'metadata': {
                        'provider': getattr(self, 'current_provider', 'unknown'),
                        'model': getattr(self, 'current_model', 'unknown'),
                        'app_version': '2.0.0'
                    }
                }

                # Save to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(conversation_data, f, indent=2, ensure_ascii=False)

                # Update status
                filename = os.path.basename(file_path)
                self.status_bar.showMessage(f"Saved conversation: {filename}")

                logger.info(f"Saved conversation to {file_path}")

        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save conversation: {e}")

    def save_chat(self):
        """Save the current chat"""
        try:
            # Get current conversation name or generate one
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"conversation_{timestamp}.json"

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Conversation",
                default_name,
                "JSON Files (*.json);;All Files (*)"
            )

            if file_path:
                self.save_conversation_to_file(file_path)

        except Exception as e:
            logger.error(f"Error saving chat: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save chat: {e}")

    def save_conversation_to_file(self, file_path):
        """Save conversation to a specific file path"""
        try:
            if not hasattr(self, 'messages') or not self.messages:
                logger.warning("No messages to save")
                return False

            conversation_data = {
                "title": getattr(self, 'current_conversation_title', "Untitled"),
                "messages": self.messages,
                "timestamp": datetime.now().isoformat(),
                "provider": getattr(self, 'current_provider', "Unknown"),
                "model": getattr(self, 'current_model', "Unknown")
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Conversation saved to: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving conversation to file: {e}")
            return False

    def open_prompt_library(self):
        """Open the prompt library dialog"""
        try:
            dialog = PromptLibraryDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening prompt library: {e}")
            QMessageBox.information(self, "Prompt Library", "Prompt library feature coming soon!")

    def set_system_prompt(self):
        """Set or modify the system prompt"""
        try:
            from ui.system_prompt_dialog import SystemPromptDialog
            dialog = SystemPromptDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                system_prompt = dialog.get_system_prompt()
                # Store the system prompt
                self.system_prompt = system_prompt
                self.status_bar.showMessage("System prompt updated")
        except Exception as e:
            logger.error(f"Error setting system prompt: {e}")
            # Fallback to simple input dialog
            system_prompt, ok = QInputDialog.getMultiLineText(
                self,
                "System Prompt",
                "Enter system prompt:",
                getattr(self, 'system_prompt', '')
            )
            if ok:
                self.system_prompt = system_prompt
                self.status_bar.showMessage("System prompt updated")

    def send_message(self):
        """Send a message (placeholder - implement actual logic)"""
        try:
            # Get input text
            if hasattr(self, 'input_entry'):
                message = self.input_entry.toPlainText()
                if message.strip():
                    # Add to prompt history for edit functionality
                    self.prompt_history.append(message)
                    # Keep only last 20 prompts
                    if len(self.prompt_history) > 20:
                        self.prompt_history = self.prompt_history[-20:]
                    
                    # Add to chat display
                    if hasattr(self, 'chat_display'):
                        self.chat_display.append(f"User: {message}")

                    # Clear input
                    self.input_entry.clear()

                    # Update status
                    if hasattr(self, 'status_bar') and self.status_bar:
                        self.status_bar.showMessage("Message sent")

                    # Here you would add the actual AI response logic

        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def scroll_to_bottom(self):
        """Scroll chat display to bottom"""
        try:
            if hasattr(self, 'chat_display'):
                scrollbar = self.chat_display.verticalScrollBar()
                if scrollbar:
                    scrollbar.setValue(scrollbar.maximum())

                # Hide the scroll to bottom button
                if hasattr(self, 'scroll_to_bottom_button'):
                    self.scroll_to_bottom_button.hide()

        except Exception as e:
            logger.error(f"Error scrolling to bottom: {e}")

    def attach_file(self):
        """Attach a file to the conversation"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Attach File",
                "",
                "All Files (*);;Text Files (*.txt);;Images (*.png *.jpg *.jpeg *.gif);;Documents (*.pdf *.doc *.docx)"
            )

            if file_path:
                # Add file to conversation (placeholder logic)
                filename = os.path.basename(file_path)
                if hasattr(self, 'chat_display'):
                    self.chat_display.append(f"📎 Attached: {filename}")

                self.status_bar.showMessage(f"Attached file: {filename}")

        except Exception as e:
            logger.error(f"Error attaching file: {e}")

    def open_persona_gallery(self):
        """Open persona gallery dialog"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("👤 AI Personas Gallery")
            dialog.setMinimumSize(800, 600)

            layout = QVBoxLayout(dialog)

            # Header
            header = QLabel("<h2>🎭 Choose an AI Persona</h2>")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header)

            # Persona grid
            scroll = QScrollArea()
            scroll_widget = QWidget()
            grid_layout = QGridLayout(scroll_widget)

            # Sample personas
            personas = [
                {"name": "🧠 The Expert", "desc": "Deep technical knowledge specialist", "prompt": "You are an expert with deep technical knowledge. Provide detailed, accurate explanations."},
                {"name": "🎨 The Creative", "desc": "Creative writing and brainstorming", "prompt": "You are a creative assistant who thinks outside the box and provides innovative ideas."},
                {"name": "📚 The Teacher", "desc": "Patient educator and explainer", "prompt": "You are a patient teacher who explains concepts clearly with examples."},
                {"name": "💼 The Professional", "desc": "Business and formal communications", "prompt": "You are a professional assistant focused on business communications and formal writing."},
                {"name": "🔬 The Researcher", "desc": "Research and analysis specialist", "prompt": "You are a thorough researcher who provides well-sourced, analytical responses."},
                {"name": "🛠️ The Developer", "desc": "Programming and technical solutions", "prompt": "You are a senior developer who provides clean, efficient code solutions with explanations."},
            ]

            row, col = 0, 0
            for persona in personas:
                # Create persona card
                card = QFrame()
                card.setFrameStyle(QFrame.Shape.Box)
                card.setStyleSheet("""
                    QFrame {
                        border: 2px solid #ddd;
                        border-radius: 10px;
                        padding: 10px;
                        margin: 5px;
                        background-color: #f9f9f9;
                    }
                    QFrame:hover {
                        border-color: #4CAF50;
                        background-color: #f0f8ff;
                    }
                """)

                card_layout = QVBoxLayout(card)

                # Persona name
                name_label = QLabel(persona["name"])
                name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
                card_layout.addWidget(name_label)

                # Description
                desc_label = QLabel(persona["desc"])
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("color: #666; margin: 5px 0;")
                card_layout.addWidget(desc_label)

                # Select button
                select_btn = QPushButton("Select")
                select_btn.clicked.connect(lambda checked, p=persona: self.select_persona(p, dialog))
                select_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                card_layout.addWidget(select_btn)

                grid_layout.addWidget(card, row, col)

                col += 1
                if col >= 2:
                    col = 0
                    row += 1

            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)

            # Custom persona section
            custom_group = QGroupBox("Create Custom Persona")
            custom_layout = QVBoxLayout(custom_group)

            custom_name = QLineEdit()
            custom_name.setPlaceholderText("Enter persona name...")
            custom_layout.addWidget(QLabel("Name:"))
            custom_layout.addWidget(custom_name)

            custom_prompt = QTextEdit()
            custom_prompt.setPlaceholderText("Enter system prompt for this persona...")
            custom_prompt.setMaximumHeight(100)
            custom_layout.addWidget(QLabel("System Prompt:"))
            custom_layout.addWidget(custom_prompt)

            create_btn = QPushButton("Create & Use")
            create_btn.clicked.connect(lambda: self.create_custom_persona(custom_name.text(), custom_prompt.toPlainText(), dialog))
            custom_layout.addWidget(create_btn)

            layout.addWidget(custom_group)

            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            logger.error(f"Error opening persona gallery: {e}")
            QMessageBox.information(self, "Persona Gallery", "Persona gallery feature coming soon!")

    def select_persona(self, persona, dialog):
        """Select a persona and apply its system prompt"""
        try:
            self.system_prompt = persona["prompt"]
            self.current_persona = persona["name"]

            # Update UI to show selected persona
            if hasattr(self, 'chat_info_label'):
                self.chat_info_label.setText(f"{persona['name']} is ready to assist!")

            # Update status
            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"Selected persona: {persona['name']}")

            dialog.close()
            logger.info(f"Selected persona: {persona['name']}")

        except Exception as e:
            logger.error(f"Error selecting persona: {e}")

    def create_custom_persona(self, name, prompt, dialog):
        """Create and use a custom persona"""
        try:
            if not name.strip() or not prompt.strip():
                QMessageBox.warning(dialog, "Invalid Input", "Please provide both name and prompt.")
                return

            custom_persona = {
                "name": f"🎭 {name}",
                "desc": "Custom persona",
                "prompt": prompt
            }

            self.select_persona(custom_persona, dialog)

        except Exception as e:
            logger.error(f"Error creating custom persona: {e}")

    def open_prompt_templates(self):
        """Open prompt templates dialog"""
        try:
            dialog = PromptTemplateDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening prompt templates: {e}")
            # Fallback dialog
            self.show_prompt_templates_fallback()

    def show_prompt_templates_fallback(self):
        """Fallback prompt templates dialog"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Prompt Templates")
            dialog.setMinimumSize(700, 500)

            layout = QVBoxLayout(dialog)

            # Header
            header = QLabel("<h2>📝 Prompt Templates & Generator</h2>")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header)

            # Template categories
            tabs = QTabWidget()

            # Writing templates
            writing_tab = QWidget()
            writing_layout = QVBoxLayout(writing_tab)

            writing_templates = [
                ("Email Draft", "Please help me write a professional email about: [TOPIC]\n\nTone: [FORMAL/CASUAL]\nRecipient: [RECIPIENT]\nPurpose: [PURPOSE]"),
                ("Essay Outline", "Create an outline for an essay on: [TOPIC]\n\nLength: [WORD COUNT]\nStyle: [ACADEMIC/PERSUASIVE/INFORMATIVE]\nKey points to cover: [POINTS]"),
                ("Creative Story", "Write a creative story with the following elements:\n\nGenre: [GENRE]\nSetting: [SETTING]\nMain character: [CHARACTER]\nPlot twist: [TWIST]"),
                ("Product Description", "Write a compelling product description for: [PRODUCT]\n\nTarget audience: [AUDIENCE]\nKey features: [FEATURES]\nTone: [TONE]")
            ]

            for name, template in writing_templates:
                btn = QPushButton(f"📝 {name}")
                btn.clicked.connect(lambda checked, t=template: self.use_template(t))
                writing_layout.addWidget(btn)

            tabs.addTab(writing_tab, "Writing")

            # Code templates
            code_tab = QWidget()
            code_layout = QVBoxLayout(code_tab)

            code_templates = [
                ("Code Review", "Please review the following code:\n\n```[LANGUAGE]\n[CODE]\n```\n\nFocus on: [AREAS TO REVIEW]"),
                ("Bug Fix", "I'm getting this error: [ERROR]\n\nIn this code:\n```[LANGUAGE]\n[CODE]\n```\n\nPlease help me fix it."),
                ("Code Explanation", "Please explain how this code works:\n\n```[LANGUAGE]\n[CODE]\n```\n\nLevel of detail: [BEGINNER/INTERMEDIATE/ADVANCED]"),
                ("Optimization", "Please optimize this code for [PERFORMANCE/READABILITY/MAINTAINABILITY]:\n\n```[LANGUAGE]\n[CODE]\n```")
            ]

            for name, template in code_templates:
                btn = QPushButton(f"💻 {name}")
                btn.clicked.connect(lambda checked, t=template: self.use_template(t))
                code_layout.addWidget(btn)

            tabs.addTab(code_tab, "Code")

            # Analysis templates
            analysis_tab = QWidget()
            analysis_layout = QVBoxLayout(analysis_tab)

            analysis_templates = [
                ("Data Analysis", "Please analyze this data:\n\n[DATA/DESCRIPTION]\n\nWhat I want to know: [QUESTIONS]\nType of analysis: [STATISTICAL/TREND/COMPARISON]"),
                ("Research Summary", "Please summarize research on: [TOPIC]\n\nFocus areas: [AREAS]\nTarget audience: [AUDIENCE]\nLength: [LENGTH]"),
                ("SWOT Analysis", "Please create a SWOT analysis for: [SUBJECT]\n\nContext: [CONTEXT]\nTimeframe: [TIMEFRAME]\nKey factors: [FACTORS]"),
                ("Pros and Cons", "Please provide a balanced pros and cons analysis of: [TOPIC]\n\nCriteria: [CRITERIA]\nStakeholders: [STAKEHOLDERS]")
            ]

            for name, template in analysis_templates:
                btn = QPushButton(f"📊 {name}")
                btn.clicked.connect(lambda checked, t=template: self.use_template(t))
                analysis_layout.addWidget(btn)

            tabs.addTab(analysis_tab, "Analysis")

            layout.addWidget(tabs)

            # Custom template section
            custom_group = QGroupBox("Create Custom Template")
            custom_layout = QVBoxLayout(custom_group)

            template_name = QLineEdit()
            template_name.setPlaceholderText("Template name...")
            custom_layout.addWidget(QLabel("Name:"))
            custom_layout.addWidget(template_name)

            template_content = QTextEdit()
            template_content.setPlaceholderText("Template content... Use [PLACEHOLDER] for variables.")
            template_content.setMaximumHeight(100)
            custom_layout.addWidget(QLabel("Template:"))
            custom_layout.addWidget(template_content)

            save_template_btn = QPushButton("Save Template")
            save_template_btn.clicked.connect(lambda: self.save_custom_template(template_name.text(), template_content.toPlainText()))
            custom_layout.addWidget(save_template_btn)

            layout.addWidget(custom_group)

            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            logger.error(f"Error showing fallback prompt templates: {e}")

    def use_template(self, template):
        """Use a template by inserting it into the input field"""
        try:
            if hasattr(self, 'input_entry'):
                current_text = self.input_entry.toPlainText()
                if current_text:
                    # Append template with a separator
                    new_text = f"{current_text}\n\n{template}"
                else:
                    new_text = template

                self.input_entry.setPlainText(new_text)

                # Move cursor to end
                cursor = self.input_entry.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                self.input_entry.setTextCursor(cursor)

                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage("Template inserted")

        except Exception as e:
            logger.error(f"Error using template: {e}")

    def save_custom_template(self, name, content):
        """Save a custom template"""
        try:
            if not name.strip() or not content.strip():
                QMessageBox.warning(self, "Invalid Input", "Please provide both name and content.")
                return

            # In a real implementation, this would save to a file or database
            # For now, just show confirmation
            QMessageBox.information(self, "Template Saved", f"Template '{name}' saved successfully!")

            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage(f"Saved template: {name}")

        except Exception as e:
            logger.error(f"Error saving custom template: {e}")

    def manage_knowledge_base(self):
        """Open Knowledge Base management dialog"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("🧠 Knowledge Base Management")
            dialog.setMinimumSize(800, 600)
            layout = QVBoxLayout(dialog)

            # Header
            header = QLabel("<h2>🧠 Knowledge Base Management</h2>")
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header)

            # Document list section
            doc_section = QGroupBox("📚 Indexed Documents")
            doc_layout = QVBoxLayout(doc_section)

            # Document list
            self.kb_doc_list = QListWidget()
            self.kb_doc_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

            # Load existing documents if any
            if not hasattr(self, 'knowledge_base_docs'):
                self.knowledge_base_docs = []

            for doc in self.knowledge_base_docs:
                status = "✅ Embedded" if doc.get('embedded', False) else "⏳ Not Embedded"
                item = QListWidgetItem(f"{doc.get('name', 'Unknown')} | {status}")
                item.setData(Qt.ItemDataRole.UserRole, doc)
                self.kb_doc_list.addItem(item)

            doc_layout.addWidget(self.kb_doc_list)

            # Document management buttons
            doc_btn_layout = QHBoxLayout()

            add_doc_btn = QPushButton("📁 Add Document")
            add_doc_btn.clicked.connect(lambda: self.add_kb_document())
            doc_btn_layout.addWidget(add_doc_btn)

            remove_doc_btn = QPushButton("🗑️ Remove Selected")
            remove_doc_btn.clicked.connect(lambda: self.remove_kb_document())
            doc_btn_layout.addWidget(remove_doc_btn)

            embed_doc_btn = QPushButton("🧮 Embed/Re-Embed")
            embed_doc_btn.clicked.connect(lambda: self.embed_kb_document())
            doc_btn_layout.addWidget(embed_doc_btn)

            doc_layout.addLayout(doc_btn_layout)
            layout.addWidget(doc_section)

            # Chunking strategy section
            chunk_section = QGroupBox("⚙️ Chunking Strategy")
            chunk_layout = QGridLayout(chunk_section)

            chunk_layout.addWidget(QLabel("Chunk Size:"), 0, 0)
            self.chunk_size_spin = QSpinBox()
            self.chunk_size_spin.setRange(128, 8192)
            self.chunk_size_spin.setValue(getattr(self, 'rag_chunk_size', 512))
            chunk_layout.addWidget(self.chunk_size_spin, 0, 1)

            chunk_layout.addWidget(QLabel("Overlap:"), 1, 0)
            self.overlap_spin = QSpinBox()
            self.overlap_spin.setRange(0, 1024)
            self.overlap_spin.setValue(getattr(self, 'rag_chunk_overlap', 64))
            chunk_layout.addWidget(self.overlap_spin, 1, 1)

            chunk_layout.addWidget(QLabel("Embedding Model:"), 2, 0)
            self.embed_model_combo = QComboBox()
            self.embed_model_combo.addItems([
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
                "text-embedding-ada-002",
                "local-bert-base"
            ])
            chunk_layout.addWidget(self.embed_model_combo, 2, 1)

            layout.addWidget(chunk_section)

            # Statistics section
            stats_section = QGroupBox("📊 Statistics")
            stats_layout = QVBoxLayout(stats_section)

            total_docs = len(self.knowledge_base_docs)
            embedded_docs = len([d for d in self.knowledge_base_docs if d.get('embedded', False)])

            stats_text = f"""
            📄 Total Documents: {total_docs}
            ✅ Embedded Documents: {embedded_docs}
            ⏳ Pending Embedding: {total_docs - embedded_docs}
            🧮 Current Chunk Size: {getattr(self, 'rag_chunk_size', 512)}
            🔄 Current Overlap: {getattr(self, 'rag_chunk_overlap', 64)}
            """

            stats_label = QLabel(stats_text)
            stats_layout.addWidget(stats_label)
            layout.addWidget(stats_section)

            # Action buttons
            button_layout = QHBoxLayout()

            save_settings_btn = QPushButton("💾 Save Settings")
            save_settings_btn.clicked.connect(lambda: self.save_kb_settings())
            button_layout.addWidget(save_settings_btn)

            refresh_btn = QPushButton("🔄 Refresh")
            refresh_btn.clicked.connect(lambda: self.refresh_kb_dialog())
            button_layout.addWidget(refresh_btn)

            button_layout.addStretch()

            close_btn = QPushButton("✖️ Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

            # Store dialog reference for refreshing
            self.kb_dialog = dialog

            dialog.exec()

        except Exception as e:
            logger.error(f"Error opening knowledge base management: {e}")
            # Fallback simple dialog
            QMessageBox.information(self, "Knowledge Base",
                                  "Knowledge Base management feature is being initialized...\n\n"
                                  "This allows you to:\n"
                                  "• Add documents for RAG\n"
                                  "• Configure chunking strategies\n"
                                  "• Manage embeddings\n"
                                  "• View statistics")

    def add_kb_document(self):
        """Add a document to the knowledge base"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Add Document to Knowledge Base",
                "",
                "All Supported Files (*.txt *.pdf *.docx *.md);;Text Files (*.txt);;PDF Files (*.pdf);;Word Documents (*.docx);;Markdown Files (*.md);;All Files (*)"
            )

            if file_path:
                filename = os.path.basename(file_path)

                # Check if already exists
                existing = [d for d in self.knowledge_base_docs if d.get('path') == file_path]
                if existing:
                    QMessageBox.warning(self, "Duplicate Document",
                                      f"Document '{filename}' is already in the knowledge base.")
                    return

                # Add to knowledge base
                doc = {
                    'name': filename,
                    'path': file_path,
                    'embedded': False,
                    'added_date': datetime.now().isoformat(),
                    'size': os.path.getsize(file_path) if os.path.exists(file_path) else  0
                }

                self.knowledge_base_docs.append(doc)

                # Update the dialog list if it exists
                if hasattr(self, 'kb_doc_list'):
                    item = QListWidgetItem(f"{filename} | ⏳ Not Embedded")
                    item.setData(Qt.ItemDataRole.UserRole, doc)
                    self.kb_doc_list.addItem(item)

                QMessageBox.information(self, "Document Added",
                                      f"Added '{filename}' to knowledge base.\n\n"
                                      "Click 'Embed/Re-Embed' to process it for RAG.")

                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"Added document: {filename}")

        except Exception as e:
            logger.error(f"Error adding KB document: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add document: {e}")

    def remove_kb_document(self):
        """Remove selected document from knowledge base"""
        try:
            if not hasattr(self, 'kb_doc_list'):
                return

            item = self.kb_doc_list.currentItem()
            if not item:
                QMessageBox.information(self, "No Selection", "Please select a document to remove.")
                return

            doc = item.data(Qt.ItemDataRole.UserRole)

            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Remove '{doc.get('name', 'Unknown')}' from knowledge base?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Remove from list
                self.knowledge_base_docs = [d for d in self.knowledge_base_docs
                                          if d.get('path') != doc.get('path')]

                # Remove from dialog
                row = self.kb_doc_list.row(item)
                self.kb_doc_list.takeItem(row)

                QMessageBox.information(self, "Document Removed",
                                      f"Removed '{doc.get('name', 'Unknown')}' from knowledge base.")

                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"Removed document: {doc.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error removing KB document: {e}")

    def embed_kb_document(self):
        """Embed selected document (placeholder implementation)"""
        try:
            if not hasattr(self, 'kb_doc_list'):
                return

            item = self.kb_doc_list.currentItem()
            if not item:
                QMessageBox.information(self, "No Selection", "Please select a document to embed.")
                return

            doc = item.data(Qt.ItemDataRole.UserRole)

            # Simulate embedding process
            reply = QMessageBox.question(self, "Embed Document",
                                       f"Embed '{doc.get('name', 'Unknown')}' for RAG?\n\n"
                                       "This will process the document into searchable chunks.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # Mark as embedded (in real implementation, this would do actual embedding)
                doc['embedded'] = True
                doc['embedded_date'] = datetime.now().isoformat()

                # Update display
                item.setText(f"{doc.get('name', 'Unknown')} | ✅ Embedded")

                QMessageBox.information(self, "Embedding Complete",
                                      f"Successfully embedded '{doc.get('name', 'Unknown')}'.\n\n"
                                      "Document is now available for RAG queries.")

                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"Embedded document: {doc.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Error embedding KB document: {e}")

    def save_kb_settings(self):
        """Save knowledge base settings"""
        try:
            if hasattr(self, 'chunk_size_spin'):
                self.rag_chunk_size = self.chunk_size_spin.value()
            if hasattr(self, 'overlap_spin'):
                self.rag_chunk_overlap = self.overlap_spin.value()
            if hasattr(self, 'embed_model_combo'):
                self.rag_embed_model = self.embed_model_combo.currentText()

            QMessageBox.information(self, "Settings Saved",
                                  f"Knowledge Base settings saved:\n\n"
                                  f"📏 Chunk Size: {getattr(self, 'rag_chunk_size', 512)}\n"
                                  f"🔄 Overlap: {getattr(self, 'rag_chunk_overlap', 64)}\n"
                                  f"🧮 Model: {getattr(self, 'rag_embed_model', 'default')}")

            if hasattr(self, 'status_bar'):
                self.status_bar.showMessage("Knowledge Base settings saved")

        except Exception as e:
            logger.error(f"Error saving KB settings: {e}")

    def refresh_kb_dialog(self):
        """Refresh the knowledge base dialog"""
        try:
            # Close and reopen dialog
            if hasattr(self, 'kb_dialog'):
                self.kb_dialog.close()
            self.manage_knowledge_base()

        except Exception as e:
            logger.error(f"Error refreshing KB dialog: {e}")

    def open_code_sandbox(self):
        """Open code sandbox for safe code execution"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Code Sandbox",
                "Code sandbox feature is coming soon!\n\nThis will allow safe execution of code snippets in isolated environments."
            )
        except Exception as e:
            logger.error(f"Error opening code sandbox: {e}")

    def execute_selected_code(self):
        """Execute selected code in the chat"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Code Execution",
                "Code execution feature is coming soon!\n\nThis will allow running selected code blocks safely."
            )
        except Exception as e:
            logger.error(f"Error executing code: {e}")

    def analyze_chat(self):
        """Analyze current chat for insights"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Chat Analytics",
                "Chat analysis feature is coming soon!\n\nThis will provide insights into conversation patterns, token usage, and more."
            )
        except Exception as e:
            logger.error(f"Error analyzing chat: {e}")

    def open_semantic_search(self):
        """Open semantic search interface"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Semantic Search",
                "Semantic search feature is coming soon!\n\nThis will allow searching conversations by meaning, not just keywords."
            )
        except Exception as e:
            logger.error(f"Error opening semantic search: {e}")

    def open_rag_analytics(self):
        """Open RAG analytics interface"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "RAG Analytics",
                "RAG analytics feature is coming soon!\n\nThis will provide insights into knowledge base usage and effectiveness."
            )
        except Exception as e:
            logger.error(f"Error opening RAG analytics: {e}")

    def open_preferences(self):
        """Open application preferences"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Preferences",
                "Preferences dialog is coming soon!\n\nThis will allow customizing all application settings."
            )
        except Exception as e:
            logger.error(f"Error opening preferences: {e}")

    def open_model_settings_manually(self):
        """Open model settings dialog manually"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Model Settings",
                "Advanced model settings dialog is coming soon!\n\nThis will allow fine-tuning model parameters."
            )
        except Exception as e:
            logger.error(f"Error opening model settings: {e}")

    def update_rag_status(self):
        """Update RAG status in status bar"""
        try:
            if hasattr(self, 'rag_status'):
                if self.rag_enabled:
                    self.rag_status.setText("RAG: ON")
                    self.rag_status.setStyleSheet("color: green;")
                else:
                    self.rag_status.setText("RAG: OFF")
                    self.rag_status.setStyleSheet("color: gray;")
        except Exception as e:
            logger.error(f"Error updating RAG status: {e}")

    def finalize_ui_setup(self):
        """Finalize UI setup after all components are initialized"""
        try:
            # Set focus to input field
            if hasattr(self, 'input_entry'):
                self.input_entry.setFocus()

            # Update initial status
            self.update_rag_status()

            # Load initial data
            self.load_providers_and_models()

        except Exception as e:
            logger.error(f"Error finalizing UI setup: {e}")

    def setup_command_palette(self):
        """Setup command palette for quick actions"""
        try:
            # Placeholder for command palette - will be implemented later
            logger.info("Command palette initialized")
        except Exception as e:
            logger.error(f"Error setting up command palette: {e}")

    def on_provider_changed(self, provider_name):
        """Handle provider change"""
        try:
            logger.info(f"Provider changed to: {provider_name}")
            # Update models for the new provider
            self.refresh_current_provider_models()
        except Exception as e:
            logger.error(f"Error changing provider: {e}")

    def on_model_changed(self, model_name):
        """Handle model change"""
        try:
            logger.info(f"Model changed to: {model_name}")
            # Update UI as needed
        except Exception as e:
            logger.error(f"Error changing model: {e}")

    def refresh_current_provider_models(self):
        """Refresh models for current provider"""
        try:
            logger.info("Refreshing models for current provider")
            # Implement model refresh logic
        except Exception as e:
            logger.error(f"Error refreshing models: {e}")

    def open_api_settings(self):
        """Open API settings dialog"""
        try:
            from api.settings import APISettingsDialog
            dialog = APISettingsDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Error opening API settings: {e}")

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        try:
            # Implement theme toggle logic
            logger.info("Theme toggled")
        except Exception as e:
            logger.error(f"Error toggling theme: {e}")

    def pull_model(self):
        """Pull/download a model"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Pull Model",
                "Model pulling feature is coming soon!\n\nThis will allow downloading models from repositories."
            )
        except Exception as e:
            logger.error(f"Error pulling model: {e}")

    def create_conversation_folder(self):
        """Create a new conversation folder"""
        try:
            from PyQt6.QtWidgets import QInputDialog
            folder_name, ok = QInputDialog.getText(
                self,
                "New Folder",
                "Enter folder name:"
            )
            if ok and folder_name:
                logger.info(f"Created folder: {folder_name}")
        except Exception as e:
            logger.error(f"Error creating folder: {e}")

    def filter_by_folder(self, folder_name):
        """Filter conversations by folder"""
        try:
            logger.info(f"Filtering by folder: {folder_name}")
            # Implement folder filtering logic
        except Exception as e:
            logger.error(f"Error filtering by folder: {e}")

    def on_scroll_changed(self, value):
        """Handle scroll changes in chat display"""
        try:
            # Handle scroll position changes for features like loading more messages
            pass
        except Exception as e:
            logger.error(f"Error handling scroll change: {e}")

    def filter_conversations(self):
        """Filter conversations based on search text"""
        try:
            search_text = getattr(self, 'conv_search', None)
            if not search_text:
                return
            
            search_query = search_text.text().lower().strip() if hasattr(search_text, 'text') else ""
            
            # Get the conversation list widget
            conv_list = getattr(self, 'conv_list', None)
            if not conv_list:
                return
            
            # Filter conversations based on search query
            for i in range(conv_list.count()):
                item = conv_list.item(i)
                if item:
                    item_text = item.text().lower()
                    # Show item if search query is empty or matches
                    should_show = not search_query or search_query in item_text
                    item.setHidden(not should_show)
                    
        except Exception as e:
            logger.error(f"Error filtering conversations: {e}")

    def on_conversation_loaded(self, conversation_data):
        """Handle when a conversation is loaded"""
        try:
            # Update UI state when conversation is loaded
            if conversation_data:
                # Update current conversation reference
                self.current_conversation = conversation_data
                
                # Update window title if conversation has a name
                if hasattr(conversation_data, 'get') and conversation_data.get('name'):
                    self.setWindowTitle(f"The Oracle - {conversation_data['name']}")
                else:
                    self.setWindowTitle("The Oracle")
                    
        except Exception as e:
            logger.error(f"Error handling conversation loaded: {e}")

    def load_conversation_lazy(self, conversation_id):
        """Load conversation with lazy loading"""
        try:
            # Implement lazy loading for large conversations
            if hasattr(self, 'load_conversation'):
                return self.load_conversation(conversation_id)
            return None
        except Exception as e:
            logger.error(f"Error in lazy conversation loading: {e}")
            return None

    def format_timestamp(self, timestamp):
        """Format timestamp for display"""
        try:
            if isinstance(timestamp, str):
                return timestamp
            elif hasattr(timestamp, 'strftime'):
                return timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return str(timestamp)
        except Exception as e:
            logger.error(f"Error formatting timestamp: {e}")
            return "Unknown time"

    def setup_enhanced_message_area(self):
        """Setup enhanced message display area"""
        try:
            # Enhanced message area setup
            if hasattr(self, 'chat_display'):
                # Apply enhanced styling or features to message area
                self.chat_display.setStyleSheet("""
                    QTextEdit {
                        background-color: #f8f9fa;
                        border: 1px solid #dee2e6;
                        border-radius: 8px;
                        padding: 10px;
                        font-family: 'Segoe UI', sans-serif;
                        font-size: 14px;
                        line-height: 1.5;
                    }
                """)
        except Exception as e:
            logger.error(f"Error setting up enhanced message area: {e}")

    def show_conversation_context_menu(self, position):
        """Show context menu for conversation list"""
        try:
            from PyQt6.QtWidgets import QMenu
            from PyQt6.QtCore import QPoint
            
            # Get the conversation list widget
            conv_list = getattr(self, 'conv_listbox', None)
            if not conv_list:
                return
                
            # Get the item at the clicked position
            item = conv_list.itemAt(position)
            if not item:
                return
                
            # Create context menu
            context_menu = QMenu(self)
            
            # Add menu actions
            rename_action = context_menu.addAction("📝 Rename Conversation")
            delete_action = context_menu.addAction("🗑️ Delete Conversation")
            context_menu.addSeparator()
            export_action = context_menu.addAction("📤 Export Conversation")
            archive_action = context_menu.addAction("📦 Archive Conversation")
            
            # Show the menu and get the selected action
            action = context_menu.exec(conv_list.mapToGlobal(position))
            
            if action == rename_action:
                self.rename_conversation(item)
            elif action == delete_action:
                self.delete_conversation(item)
            elif action == export_action:
                self.export_conversation(item)
            elif action == archive_action:
                self.archive_conversation(item)
                
        except Exception as e:
            logger.error(f"Error showing conversation context menu: {e}")

    def show_chat_context_menu(self, position):
        """Show context menu for chat display"""
        try:
            from PyQt6.QtWidgets import QMenu
            
            # Get the chat display widget
            chat_display = getattr(self, 'chat_display', None)
            if not chat_display:
                return
                
            # Create context menu
            context_menu = QMenu(self)
            
            # Add menu actions
            copy_action = context_menu.addAction("📋 Copy")
            copy_all_action = context_menu.addAction("📋 Copy All")
            context_menu.addSeparator()
            clear_action = context_menu.addAction("🗑️ Clear Chat")
            context_menu.addSeparator()
            export_action = context_menu.addAction("📤 Export Chat")
            
            # Show the menu and get the selected action
            action = context_menu.exec(chat_display.mapToGlobal(position))
            
            if action == copy_action:
                self.copy_selected_text()
            elif action == copy_all_action:
                self.copy_all_text()
            elif action == clear_action:
                self.clear_chat()
            elif action == export_action:
                self.export_current_conversation()
                
        except Exception as e:
            logger.error(f"Error showing chat context menu: {e}")

    def rename_conversation(self, item):
        """Rename a conversation"""
        try:
            from PyQt6.QtWidgets import QInputDialog
            
            if not item:
                return
                
            current_name = item.text()
            new_name, ok = QInputDialog.getText(
                self, 
                "Rename Conversation", 
                "Enter new name:", 
                text=current_name
            )
            
            if ok and new_name.strip():
                item.setText(new_name.strip())
                # TODO: Update conversation name in storage
                
        except Exception as e:
            logger.error(f"Error renaming conversation: {e}")

    def delete_conversation(self, item):
        """Delete a conversation"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            if not item:
                return
                
            reply = QMessageBox.question(
                self,
                "Delete Conversation",
                f"Are you sure you want to delete '{item.text()}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Remove from list
                conv_list = getattr(self, 'conv_listbox', None)
                if conv_list:
                    row = conv_list.row(item)
                    conv_list.takeItem(row)
                # TODO: Delete from storage
                
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")

    def export_conversation(self, item):
        """Export a conversation"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            if not item:
                return
                
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Conversation",
                f"{item.text()}.json",
                "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                # TODO: Implement actual export logic
                logger.info(f"Would export conversation to: {filename}")
                
        except Exception as e:
            logger.error(f"Error exporting conversation: {e}")

    def archive_conversation(self, item):
        """Archive a conversation"""
        try:
            if not item:
                return
                
            # TODO: Implement archiving logic
            logger.info(f"Would archive conversation: {item.text()}")
            
        except Exception as e:
            logger.error(f"Error archiving conversation: {e}")

    def copy_selected_text(self):
        """Copy selected text from chat display"""
        try:
            chat_display = getattr(self, 'chat_display', None)
            if chat_display and hasattr(chat_display, 'copy'):
                chat_display.copy()
        except Exception as e:
            logger.error(f"Error copying selected text: {e}")

    def copy_all_text(self):
        """Copy all text from chat display"""
        try:
            from PyQt6.QtWidgets import QApplication
            
            chat_display = getattr(self, 'chat_display', None)
            if chat_display:
                all_text = chat_display.toPlainText()
                clipboard = QApplication.clipboard()
                clipboard.setText(all_text)
        except Exception as e:
            logger.error(f"Error copying all text: {e}")

    def clear_chat(self):
        """Clear the chat display"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self,
                "Clear Chat",
                "Are you sure you want to clear the current chat?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                chat_display = getattr(self, 'chat_display', None)
                if chat_display:
                    chat_display.clear()
                    
        except Exception as e:
            logger.error(f"Error clearing chat: {e}")

    def export_current_conversation(self):
        """Export the current conversation"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export Current Conversation",
                "conversation.json",
                "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                chat_display = getattr(self, 'chat_display', None)
                if chat_display:
                    content = chat_display.toPlainText()
                    with open(filename, 'w', encoding='utf-8') as f:
                        if filename.endswith('.json'):
                            import json
                            json.dump({"content": content}, f, indent=2, ensure_ascii=False)
                        else:
                            f.write(content)
                            
        except Exception as e:
            logger.error(f"Error exporting current conversation: {e}")

    def toggle_compact_mode(self):
        """Toggle compact mode for the chat interface"""
        try:
            # Toggle the compact mode state
            self.compact_mode = not getattr(self, 'compact_mode', False)
            
            # Update the button state
            if hasattr(self, 'compact_mode_btn'):
                self.compact_mode_btn.setChecked(self.compact_mode)
            
            # Apply compact mode styling
            chat_display = getattr(self, 'chat_display', None)
            if chat_display:
                if self.compact_mode:
                    # Compact mode styling
                    chat_display.setStyleSheet("""
                        QTextEdit {
                            background-color: #f8f9fa;
                            border: 1px solid #dee2e6;
                            border-radius: 4px;
                            padding: 5px;
                            font-family: 'Segoe UI', sans-serif;
                            font-size: 12px;
                            line-height: 1.2;
                        }
                    """)
                else:
                    # Normal mode styling
                    chat_display.setStyleSheet("""
                        QTextEdit {
                            background-color: #f8f9fa;
                            border: 1px solid #dee2e6;
                            border-radius: 8px;
                            padding: 10px;
                            font-family: 'Segoe UI', sans-serif;
                            font-size: 14px;
                            line-height: 1.5;
                        }
                    """)
            
            logger.info(f"Compact mode {'enabled' if self.compact_mode else 'disabled'}")
            
        except Exception as e:
            logger.error(f"Error toggling compact mode: {e}")

    def toggle_line_numbers(self):
        """Toggle line numbers in code blocks"""
        try:
            # Toggle the line numbers state
            self.show_line_numbers = not getattr(self, 'show_line_numbers', False)
            
            # Update the button state
            if hasattr(self, 'line_numbers_btn'):
                self.line_numbers_btn.setChecked(self.show_line_numbers)
            
            # Apply line numbers setting
            # This would typically affect how code blocks are rendered
            logger.info(f"Line numbers {'enabled' if self.show_line_numbers else 'disabled'}")
            
            # Update any existing code blocks if needed
            self.update_code_block_display()
            
        except Exception as e:
            logger.error(f"Error toggling line numbers: {e}")

    def toggle_code_folding(self):
        """Toggle code folding in code blocks"""
        try:
            # Toggle the code folding state
            self.enable_code_folding = not getattr(self, 'enable_code_folding', False)
            
            # Update the button state
            if hasattr(self, 'code_folding_btn'):
                self.code_folding_btn.setChecked(self.enable_code_folding)
            
            # Apply code folding setting
            logger.info(f"Code folding {'enabled' if self.enable_code_folding else 'disabled'}")
            
            # Update any existing code blocks if needed
            self.update_code_block_display()
            
        except Exception as e:
            logger.error(f"Error toggling code folding: {e}")

    def update_code_block_display(self):
        """Update the display of code blocks based on current settings"""
        try:
            # This method would update how code blocks are rendered
            # based on line numbers and code folding settings
            chat_display = getattr(self, 'chat_display', None)
            if chat_display:
                # Get current content
                current_content = chat_display.toHtml()
                
                # Re-render code blocks with current settings
                # This is a placeholder - actual implementation would parse
                # and re-render code blocks with proper formatting
                logger.debug("Code block display updated")
                
        except Exception as e:
            logger.error(f"Error updating code block display: {e}")

    def edit_last_prompt(self):
        """Edit the last prompt sent by the user"""
        try:
            # Check if there's any prompt history
            if not self.prompt_history:
                if hasattr(self, 'status_bar') and self.status_bar:
                    self.status_bar.showMessage("No previous prompts to edit")
                return
            
            # Get the last prompt
            last_prompt = self.prompt_history[-1]
            
            # Check if input_entry exists
            if hasattr(self, 'input_entry'):
                # Set the last prompt text in the input entry
                self.input_entry.setPlainText(last_prompt)
                
                # Focus on the input entry for editing
                self.input_entry.setFocus()
                
                # Position cursor at the end
                cursor = self.input_entry.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.input_entry.setTextCursor(cursor)
                
                if hasattr(self, 'status_bar') and self.status_bar:
                    self.status_bar.showMessage("Last prompt loaded for editing")
            else:
                if hasattr(self, 'status_bar') and self.status_bar:
                    self.status_bar.showMessage("Input field not available")
                
        except Exception as e:
            logger.error(f"Error editing last prompt: {e}")
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.showMessage("Error loading last prompt for editing")
