"""
Complete ChatApp implementation for The Oracle.
This file contains all the main functionality split out from the original Oracle.py.
"""

import os
import json
import threading
import logging
import re
import tempfile
from datetime import datetime
from collections import Counter

# Optional advanced dependencies
try:
    import numpy
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import requests
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import matplotlib
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import seaborn
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

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

try:
    import networkx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import pandas
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

import pickle
import time

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
                             QDockWidget, QMdiArea, QMdiSubWindow, QSplashScreen, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer, QSize, QSettings
from PyQt6.QtGui import QFont, QIcon, QAction, QTextCursor, QTextCharFormat, QColor, QCloseEvent, QKeySequence, QShortcut

# Core imports
from core.evaluator import AIEvaluator
from core.knowledge_graph import KnowledgeGraph
from api.multi_provider import MultiProviderClient
from api.settings import APISettingsDialog
from api.threads import MultiProviderResponseThread
from utils.formatting import format_chat_message

# UI imports
from ui.tag_editor_dialog import TagEditorDialog

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
            self.setIconSize(QSize(20, 20))
        
        # Set minimum size for better appearance
        self.setMinimumHeight(40)
        self.setMinimumWidth(80)
        
        # Set object name for specific styling
        self.setObjectName("modern_button")
        
    def enterEvent(self, event):
        """Handle mouse enter with simple effects"""
        super().enterEvent(event)
        # Simple hover effect - just change background color
        self.setStyleSheet(self.styleSheet() + "background-color: #5a67d8;")
        event.accept()
        
    def leaveEvent(self, event):
        """Handle mouse leave"""
        super().leaveEvent(event)
        # Restore original background
        self.setStyleSheet(self.styleSheet().replace("background-color: #5a67d8;", ""))
        event.accept()


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


class TaggedConversationItem(QListWidgetItem):
    """Custom list item for conversations with tags"""
    
    def __init__(self, text, conversation_id, tags=None):
        super().__init__(text)
        self.conversation_id = conversation_id
        self.tags = set(tags or [])
        self.update_display()
        
    def update_display(self):
        """Update the display text with tags"""
        base_text = self.text().split(" [")[0]  # Remove existing tag display
        if self.tags:
            tag_text = ", ".join(sorted(self.tags))
            self.setText(f"{base_text} [{tag_text}]")
        else:
            self.setText(base_text)
            
    def add_tag(self, tag):
        """Add a tag to this conversation"""
        self.tags.add(tag)
        self.update_display()
        
    def remove_tag(self, tag):
        """Remove a tag from this conversation"""
        self.tags.discard(tag)
        self.update_display()
        
    def get_tags(self):
        """Get all tags for this conversation"""
        return list(self.tags)


class ChatApp(QMainWindow):
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
        self.conversation_analytics = {}  # Analytics data for conversations
        self.plugin_manager = None
        self.achievements = set()
        
        # Threaded replies functionality
        self.message_replies = {}  # message_id -> list of reply message_ids
        self.message_parents = {}  # message_id -> parent_message_id
        self.message_threads = {}  # thread_id -> list of message_ids
        self.current_thread_id = None
        self.reply_to_message_id = None
        
        # Setup UI and load data
        self.setup_ui()
        self.setup_styles()
        self.detect_and_load_local_models()  # <-- NEW: Detect/load local models on startup
        self.load_providers_and_models()
        self.load_conversations()
        self.setup_auto_save()
        self.setup_model_refresh_timer()  # Set up automatic model refresh
        self.load_chat_on_startup()

        # Initialize additional features
        self.setup_token_counter()
        self.setup_pinned_messages_display()
        
        # Setup menu
        self.setup_menu()

        # --- Add to __init__ ---
        self.conversation_tags = {}  # conversation_id -> set of tags
        self.command_palette = None
        self.model_parameters = {
            'temperature': 0.7,
            'top_p': 1.0,
            'max_tokens': 4096,
            'frequency_penalty': 0.0
        }

        # In __init__, add:
        self.slash_commands = {
            # Chat Management
            '/new': ('Start a new conversation', self.new_conversation),
            '/clear': ('Clear the current chat', self.clear_chat),
            '/save': ('Save current conversation', self.save_chat),
            '/load': ('Load a conversation', self.load_chat),
            '/export': ('Export conversation to file', lambda: self.export_chat("markdown")),
            '/summarize': ('Summarize the current conversation', self.summarize_chat),
            
            # Content Analysis
            '/explain': ('Explain the last message or code', self.explain_last_message),
            '/translate': ('Translate text to another language', self.translate_text),
            '/improve': ('Improve or rewrite text', self.improve_text),
            '/fix': ('Fix grammar and spelling', self.fix_text),
            '/tone': ('Change the tone of text', self.change_tone),
            
            # Data Processing
            '/table': ('Convert CSV/Excel to Markdown Table', self.csv_to_markdown_table),
            '/json': ('Format or validate JSON', self.format_json),
            '/csv': ('Process CSV data', self.process_csv),
            '/regex': ('Explain a regex pattern', self.explain_regex),
            '/extract': ('Extract information from text', self.extract_info),
            
            # Code & Development
            '/code': ('Generate or explain code', self.code_assistant),
            '/debug': ('Debug code or error messages', self.debug_code),
            '/test': ('Generate test cases', self.generate_tests),
            '/doc': ('Generate documentation', self.generate_docs),
            '/refactor': ('Refactor code', self.refactor_code),
            
            # Model & Settings
            '/model': ('Switch to a different model', self.switch_model),
            '/temp': ('Set model temperature', self.set_temperature),
            '/tokens': ('Set max tokens', self.set_max_tokens),
            '/rag': ('Toggle RAG (Retrieval-Augmented Generation)', self.toggle_rag_for_prompt),
            '/kb': ('Manage knowledge base', self.show_knowledge_base_dialog),
            
            # System & Tools
            '/search': ('Search chat history', lambda: self.search_entry.setFocus()),
            '/tags': ('Edit conversation tags', self.open_tag_editor),
            '/theme': ('Toggle dark/light theme', self.toggle_theme),
            '/settings': ('Open API settings', self.open_api_settings),
            '/help': ('Show slash command help', self.show_slash_help),
        }
        self.slash_command_dropdown = None
        
        # Quick-switch model functionality
        self.recent_models = []  # List of recently used models
        self.max_recent_models = 10  # Maximum number of recent models to remember
        self.load_recent_models()  # Load recent models from settings
        
        # Initialize missing features
        self.setup_pinned_conversations()
        self.setup_prompt_library()
        self.setup_rag_chunking_strategy()
        self.setup_compact_spacious_ui()
        self.setup_lazy_loading()
        self.setup_virtual_scrolling()
        self.setup_system_quick_capture()
        self.setup_browser_extension()
        self.setup_rag_for_codebases()
        self.setup_file_system_automation()
        self.setup_ai_shell_companion()
        self.setup_smart_clipboard_daemon()
        
        # Initialize default provider and model
        self.default_provider = self.settings.value("default_provider", "openai", type=str)
        self.default_model = self.settings.value("default_model", "gpt-3.5-turbo", type=str)
        
        # Initialize comprehensive tagging system
        self.setup_conversation_tagging_system()
