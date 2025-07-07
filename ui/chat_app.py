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
    PDF_AVAILABLE = False

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

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import FAISS as LangchainFAISS
    from langchain.chains import RetrievalQA
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

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
        
    def leaveEvent(self, event):
        """Handle mouse leave"""
        super().leaveEvent(event)
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
        
        # Enhanced buttons with icons
        self.refresh_models_button = ModernButton("🔄", self.get_icon_path("toolbar", "refresh"))
        self.refresh_models_button.setMaximumWidth(40)
        self.refresh_models_button.setToolTip("Refresh Models")
        self.refresh_models_button.clicked.connect(self.refresh_current_provider_models)
        toolbar_layout.addWidget(self.refresh_models_button)
        
        self.api_settings_button = ModernButton("⚙️ Settings", self.get_icon_path("toolbar", "settings"))
        self.api_settings_button.setToolTip("API Settings")
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
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_panel)
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
        
        splitter.addWidget(left_panel)
        
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
        """Set up the application menu"""
        menubar = self.menuBar()
        if not menubar:
            return
            
        # File menu
        file_menu = menubar.addMenu("File")
        if file_menu:
            save_action = QAction("Save Chat", self)
            save_action.triggered.connect(self.save_chat)
            file_menu.addAction(save_action)
            
            load_action = QAction("Load Chat", self)
            load_action.triggered.connect(self.load_chat)
            file_menu.addAction(load_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
        
        # Chat menu
        chat_menu = menubar.addMenu("Chat")
        if chat_menu:
            markdown_action = QAction("Markdown Formatting", self)
            markdown_action.setCheckable(True)
            markdown_action.setChecked(True)
            markdown_action.triggered.connect(self.toggle_markdown)
            chat_menu.addAction(markdown_action)
            
            # Export submenu
            export_menu = chat_menu.addMenu("Export")
            if export_menu:
                export_actions = [
                    ("To JSON", lambda: self.export_chat("json")),
                    ("To TXT", lambda: self.export_chat("txt")),
                    ("To HTML", lambda: self.export_chat("html")),
                ]
                
                for text, func in export_actions:
                    action = QAction(text, self)
                    action.triggered.connect(func)
                    export_menu.addAction(action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        if tools_menu:
            attach_action = QAction("Attach File", self)
            attach_action.triggered.connect(self.attach_file)
            tools_menu.addAction(attach_action)
            
            summarize_action = QAction("Summarize Chat", self)
            summarize_action.triggered.connect(self.summarize_chat)
            tools_menu.addAction(summarize_action)

        # Help menu
        help_menu = menubar.addMenu("Help")
        if help_menu:
            about_action = QAction("About The Oracle", self)
            about_action.triggered.connect(self.show_about_dialog)
            help_menu.addAction(about_action)

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
        """Load available providers and models"""
        providers = ["Ollama"] + list(self.multi_client.providers.keys())[1:]
        self.provider_combo.clear()
        self.provider_combo.addItems(providers)
        self.provider_combo.setCurrentText("Ollama")
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
        
        # Create and start response thread
        if self.current_provider == "Ollama":
            self.response_thread = ModelResponseThread(
                self.multi_client.providers["Ollama"]["client"],
                self.current_model,
                message
            )
        else:
            self.response_thread = MultiProviderResponseThread(
                self.multi_client,
                message
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
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Simple text-based format for better compatibility
        if is_user:
            cursor.insertText(f"\nUser ({timestamp}): {content}\n")
        else:
            cursor.insertText(f"\n{role} ({timestamp}): {content}\n")
        
        # If message is pinned, add a pin icon
        idx = len(self.chat_history) - 1
        pin_html = ""
        if self.current_conversation_id in self.pinned_messages and idx in self.pinned_messages[self.current_conversation_id]:
            pin_html = " <span style='color:#FFD700;'>📌</span>"
        
        if is_user:
            self.chat_display.append(f"\nUser: {content}{pin_html}\n")
        else:
            self.chat_display.append(f"\n{role}: {content}{pin_html}\n")
        
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
        
        self.current_provider = provider
        self.multi_client.set_provider(provider)
        
        # Update models
        models = self.multi_client.get_models_for_provider(provider)
        self.model_combo.clear()
        self.model_combo.addItems(models)
        
        # Enable pull button only for Ollama
        self.pull_button.setEnabled(provider == "Ollama")

    def on_model_changed(self, model):
        """Handle model change"""
        self.current_model = model

    def refresh_current_provider_models(self):
        """Refresh models for current provider"""
        if not self.current_provider:
            return
        
        self.refresh_models_button.setEnabled(False)
        self.refresh_models_button.setText("...")
        
        try:
            if self.current_provider == "Ollama":
                self.multi_client.refresh_ollama_models()
            
            # Update UI
            models = self.multi_client.get_models_for_provider(self.current_provider)
            self.model_combo.clear()
            self.model_combo.addItems(models)
            
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

    def pull_model(self):
        """Pull a model (Ollama only)"""
        if self.current_provider != "Ollama":
            return
        
        model_name, ok = QInputDialog.getText(self, "Pull Model", "Enter model name:")
        if ok and model_name:
            self.status_bar.showMessage(f"Pulling model {model_name}...")
            
            def pull_thread():
                try:
                    ollama_client = self.multi_client.providers["Ollama"]["client"]
                    stream = ollama_client.pull(model=model_name, stream=True)
                    for progress in stream:
                        status = progress.get('status', '')
                        self.status_bar.showMessage(f"Pulling... {status}")
                    
                    self.status_bar.showMessage("Model pulled successfully")
                    self.refresh_current_provider_models()
                except Exception as e:
                    self.status_bar.showMessage(f"Pull failed: {e}")
            
            threading.Thread(target=pull_thread, daemon=True).start()

    def new_conversation(self):
        """Start a new conversation and show the welcome screen"""
        self.chat_history = []
        self.current_conversation_id = None
        self.chat_display.clear()
        self.show_welcome_screen()
        # Optionally reset input, model, etc.
        if hasattr(self, 'input_entry'):
            self.input_entry.clear()

    def show_welcome_screen(self):
        """Display a welcome screen with model info and quick-start buttons"""
        model = self.model_combo.currentText() if hasattr(self, 'model_combo') else 'Model'
        welcome_html = f'''
        <div style='text-align: center; padding: 40px; font-family: Arial, sans-serif;'>
            <h1 style='color: #63B3ED; font-size: 36px; margin-bottom: 20px;'>🌟 Welcome to The Oracle 🌟</h1>
            <p style='font-size: 18px; color: #718096; margin-bottom: 30px;'>
                Your Enhanced AI Assistant with Modern Interface<br>
                <b>Current Model:</b> <span style='color:#4299E1'>{model}</span>
            </p>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; margin: 20px auto; max-width: 600px;'>
                <h3 style='color: white; margin-bottom: 15px;'>✨ Quick Start:</h3>
                <button onclick="pycmd('explain_code')" style='margin: 8px; padding: 10px 18px; border-radius: 8px; background: #63B3ED; color: white; border: none; font-size: 16px;'>Explain Code</button>
                <button onclick="pycmd('write_email')" style='margin: 8px; padding: 10px 18px; border-radius: 8px; background: #48BB78; color: white; border: none; font-size: 16px;'>Write an Email</button>
                <button onclick="pycmd('summarize_text')" style='margin: 8px; padding: 10px 18px; border-radius: 8px; background: #4299E1; color: white; border: none; font-size: 16px;'>Summarize Text</button>
            </div>
            <p style='font-size: 16px; color: #4A5568; margin-top: 30px;'>🚀 Start chatting by selecting a model and typing your message below!</p>
        </div>
        '''
        self.chat_display.setHtml(welcome_html)

    def filter_chat(self):
        """Filter chat messages"""
        search_text = self.search_entry.text().strip()
        if not search_text:
            return
        
        # Simple search implementation
        # In a real app, you'd implement more sophisticated search
        QMessageBox.information(self, "Search", f"Searching for: {search_text}")

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
                    self.chat_history = json.load(f)
                
                self.current_conversation_id = conv_id
                self.refresh_chat_display()
                self.toggle_welcome_screen(False)
        except Exception as e:
            logger.error(f"Failed to load conversation {conv_id}: {e}")

    def refresh_chat_display(self):
        """Refresh the chat display with virtual scrolling"""
        self.chat_display.clear()
        self._virtual_scroll_message_count = len(self.chat_history)
        self._virtual_scroll_message_height = 60  # Approximate height per message (px)
        self._virtual_scroll_viewport_height = self.chat_display.viewport().height()
        self._virtual_scroll_visible_count = max(1, self._virtual_scroll_viewport_height // self._virtual_scroll_message_height)
        self._virtual_scroll_offset = 0
        self._virtual_scroll_render_messages()
        # Connect scroll event
        scrollbar = self.chat_display.verticalScrollBar()
        if scrollbar:
            scrollbar.valueChanged.connect(self._on_virtual_scroll)

    def _on_virtual_scroll(self, value):
        # Calculate which messages should be visible
        scrollbar = self.chat_display.verticalScrollBar()
        if not scrollbar:
            return
        max_scroll = scrollbar.maximum()
        if max_scroll == 0:
            self._virtual_scroll_offset = 0
        else:
            percent = value / max_scroll
            max_offset = max(0, self._virtual_scroll_message_count - self._virtual_scroll_visible_count)
            self._virtual_scroll_offset = int(percent * max_offset)
        self._virtual_scroll_render_messages()

    def _virtual_scroll_render_messages(self):
        # Only render visible messages
        start = self._virtual_scroll_offset
        end = min(start + self._virtual_scroll_visible_count + 2, self._virtual_scroll_message_count)
        self.chat_display.clear()
        for msg in self.chat_history[start:end]:
            self.append_to_chat(msg['role'], msg['content'], msg['role'] == 'user')

    def save_current_conversation_to_json(self):
        """Save current conversation to JSON"""
        if not self.current_conversation_id or not self.chat_history:
            return
        
        try:
            os.makedirs("conversations", exist_ok=True)
            filepath = f"conversations/{self.current_conversation_id}.json"
            with open(filepath, 'w') as f:
                json.dump(self.chat_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

    def save_chat(self):
        """Save chat to file"""
        self.save_current_conversation_to_json()
        self.status_bar.showMessage("Chat saved")

    def load_chat(self):
        """Load chat from file"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Chat", "", "JSON Files (*.json)")
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    self.chat_history = json.load(f)
                self.refresh_chat_display()
                self.toggle_welcome_screen(False)
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load chat: {e}")

    def export_chat(self, format_type):
        """Export chat to various formats"""
        if not self.chat_history:
            QMessageBox.warning(self, "No Chat", "No chat history to export")
            return
        
        if format_type == "json":
            filepath = export_to_json(self.chat_history)
        elif format_type == "txt":
            text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.chat_history])
            filepath = export_to_txt(text)
        elif format_type == "html":
            html = "<html><body>"
            for msg in self.chat_history:
                html += format_chat_message(msg['role'], msg['content'])
            html += "</body></html>"
            filepath = export_to_html(html)
        else:
            filepath = None
        
        if filepath:
            QMessageBox.information(self, "Export Complete", f"Chat exported to {filepath}")

    def attach_file(self):
        """Attach a file to the chat"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Attach File", "", "All Files (*)")
        if filepath:
            # Simple file attachment - in a real app, you'd process the file
            filename = os.path.basename(filepath)
            self.append_to_chat("System", f"File attached: {filename}", is_user=False)

    def summarize_chat(self):
        """Summarize the current chat"""
        if not self.chat_history:
            QMessageBox.warning(self, "No Chat", "No chat history to summarize")
            return
        
        # Simple summarization - in a real app, you'd use AI
        msg_count = len(self.chat_history)
        user_msgs = len([m for m in self.chat_history if m['role'] == 'user'])
        assistant_msgs = len([m for m in self.chat_history if m['role'] == 'assistant'])
        
        summary = f"Chat Summary:\n- Total messages: {msg_count}\n- User messages: {user_msgs}\n- Assistant messages: {assistant_msgs}"
        QMessageBox.information(self, "Chat Summary", summary)

    def create_welcome_screen(self):
        """Create welcome screen widget"""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        
        title = QLabel("Welcome to The Oracle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Select a model and start chatting!")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #8B949E; margin: 10px;")
        layout.addWidget(subtitle)
        
        layout.addStretch()
        return welcome_widget

    def toggle_welcome_screen(self, show_welcome):
        """Toggle welcome screen visibility"""
        if show_welcome:
            if not hasattr(self, 'welcome_screen'):
                self.welcome_screen = self.create_welcome_screen()
            layout = self.chat_widget.layout()
            if layout:
                layout.replaceWidget(self.chat_display, self.welcome_screen)
            self.chat_display.hide()
            self.welcome_screen.show()
        else:
            if hasattr(self, 'welcome_screen'):
                layout = self.chat_widget.layout()
                if layout:
                    layout.replaceWidget(self.welcome_screen, self.chat_display)
                self.welcome_screen.hide()
                self.chat_display.show()

    def get_icon_path(self, category, name):
        """Get the full path to an icon"""
        return os.path.join(self.icon_base_path, category, f"{name}.png")
    
    def add_welcome_message(self):
        """Add enhanced welcome message to chat"""
        welcome_html = """
        <div style='text-align: center; padding: 40px; font-family: Arial, sans-serif;'>
            <h1 style='color: #63B3ED; font-size: 36px; margin-bottom: 20px;'>
                🌟 Welcome to The Oracle 🌟
            </h1>
            <p style='font-size: 18px; color: #718096; margin-bottom: 30px;'>
                Your Enhanced AI Assistant with Modern Interface
            </p>
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 15px; margin: 20px auto; max-width: 600px;'>
                <h3 style='color: white; margin-bottom: 15px;'>✨ New Features:</h3>
                <ul style='text-align: left; color: white; font-size: 16px;'>
                    <li>🎨 Beautiful 3D icons throughout the interface</li>
                    <li>🌈 Smooth animations and modern gradients</li>
                    <li>🎯 Enhanced user experience with intuitive design</li>
                    <li>🔍 Improved search and navigation</li>
                    <li>📱 Responsive and accessible interface</li>
                </ul>
            </div>
            <p style='font-size: 16px; color: #4A5568; margin-top: 30px;'>
                🚀 Start chatting by selecting a model and typing your message below!
            </p>
        </div>
        """
        self.chat_display.setHtml(welcome_html)
    
    def on_scroll_changed(self, value):
        """Handle scroll position changes"""
        scrollbar = self.chat_display.verticalScrollBar()
        if not scrollbar:
            return
        
        max_value = scrollbar.maximum()
        
        # Show/hide scroll to bottom button
        if max_value > 0 and value < max_value - 10:
            if self.scroll_to_bottom_button:
                self.scroll_to_bottom_button.show()
        else:
            if self.scroll_to_bottom_button:
                self.scroll_to_bottom_button.hide()

    def scroll_to_bottom(self):
        """Scroll to bottom of chat"""
        scrollbar = self.chat_display.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
        if self.scroll_to_bottom_button:
            self.scroll_to_bottom_button.hide()

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        self.save_current_conversation_to_json()
        event.accept()

    def add_message_to_chat(self, sender, message):
        """Add a message to the chat display with enhanced styling and markdown table rendering"""
        timestamp = datetime.now().strftime("%H:%M")
        # Make links clickable
        message = self.make_links_clickable(message)
        # Render markdown tables
        message = self.render_markdown(message)
        # Add copy button for message
        copy_button_html = f"""
            <span style='float:right; cursor:pointer;' onclick=\"navigator.clipboard.writeText(`{html.escape(message)}`)\">
                <img src='data:image/svg+xml;utf8,<svg width=\'16\' height=\'16\' fill=\'none\' xmlns=\'http://www.w3.org/2000/svg\'><rect width=\'12\' height=\'14\' x=\'2\' y=\'1\' rx=\'2\' fill=\'%23fff\' stroke=\'%23667eea\' stroke-width=\'2\'/></svg>' style='vertical-align:middle;' title='Copy message'>
            </span>
        """
        # Detect code blocks and add copy code button
        def add_copy_code_buttons(text):
            code_pattern = re.compile(r'(<pre><code.*?>)([\s\S]*?)(</code></pre>)', re.MULTILINE)
            def repl(match):
                code = match.group(2)
                button = f"<span style='float:right; cursor:pointer;' onclick=\"navigator.clipboard.writeText(`{html.escape(code)}`)\"><img src='data:image/svg+xml;utf8,<svg width=\'16\' height=\'16\' fill=\'none\' xmlns=\'http://www.w3.org/2000/svg\'><rect width=\'12\' height=\'14\' x=\'2\' y=\'1\' rx=\'2\' fill=\'%23fff\' stroke=\'%23667eea\' stroke-width=\'2\'/></svg>' style='vertical-align:middle;' title='Copy code'></span>"
                return match.group(1) + button + code + match.group(3)
            return code_pattern.sub(repl, text)
        message_with_code_buttons = add_copy_code_buttons(message)
        if sender == "user" or sender == "User":
            msg_html = f"""
            <div style='text-align: right; margin: 15px 0;'>
                <div style='display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 12px 16px; border-radius: 18px 18px 4px 18px; 
                           max-width: 70%; box-shadow: 0 4px 12px rgba(0,0,0,0.15);'>
                    <div style='font-size: 14px; line-height: 1.4; word-wrap: break-word;'>{message_with_code_buttons}{copy_button_html}</div>
                    <div style='font-size: 10px; opacity: 0.8; margin-top: 4px; text-align: right;'>{timestamp}</div>
                </div>
            </div>
            """
        else:
            msg_html = f"""
            <div style='text-align: left; margin: 15px 0;'>
                <div style='display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           color: white; padding: 12px 16px; border-radius: 18px 18px 18px 4px; 
                           max-width: 70%; box-shadow: 0 4px 12px rgba(0,0,0,0.15);'>
                    <div style='font-size: 14px; line-height: 1.4; word-wrap: break-word;'>{message_with_code_buttons}{copy_button_html}</div>
                    <div style='font-size: 10px; opacity: 0.8; margin-top: 4px;'>🤖 {timestamp}</div>
                </div>
            </div>
            """
        self.chat_display.append(msg_html)
        self.scroll_to_bottom()

    def make_links_clickable(self, text):
        """Convert URLs in text to clickable HTML links"""
        url_pattern = re.compile(r'(https?://[\w\-._~:/?#\[\]@!$&\'()*+,;=%]+)')
        return url_pattern.sub(r'<a href="\1" style="color:#63B3ED;text-decoration:underline;" target="_blank">\1</a>', text)

    def render_markdown_tables(self, content):
        """Render markdown tables with proper formatting"""
        if not MARKDOWN_AVAILABLE:
            return content
        
        try:
            # Convert markdown tables to HTML
            html_content = markdown.markdown(content, extensions=['tables', 'fenced_code', 'codehilite'])
            
            # Add table styling
            html_content = html_content.replace('<table>', 
                '<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">')
            html_content = html_content.replace('<th>', 
                '<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2; text-align: left;">')
            html_content = html_content.replace('<td>', 
                '<td style="border: 1px solid #ddd; padding: 8px;">')
            
            return html_content
        except Exception as e:
            logger.warning(f"Failed to render markdown tables: {e}")
            return content

    def render_markdown(self, text):
        """Render markdown with table support and enhanced styling"""
        if MARKDOWN_AVAILABLE:
            # Use markdown with table extension
            import markdown
            html_content = markdown.markdown(text, extensions=['tables'])
            # Add custom CSS for tables
            table_css = '''<style>
                table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                th, td { border: 1px solid #63B3ED; padding: 8px; text-align: left; }
                th { background: #63B3ED; color: white; }
                tr:nth-child(even) { background: #F7FAFC; }
            </style>'''
            return table_css + html_content
        return text

    def add_message_timestamp(self, message_id, timestamp=None):
        """Add timestamp to message"""
        if timestamp is None:
            timestamp = datetime.now()
        
        if self.current_conversation_id not in self.message_timestamps:
            self.message_timestamps[self.current_conversation_id] = {}
        
        self.message_timestamps[self.current_conversation_id][message_id] = timestamp

    def get_message_timestamp_html(self, message_id, show_timestamps=True):
        """Get HTML for message timestamp"""
        if not show_timestamps:
            return ""
        
        timestamp = self.message_timestamps.get(self.current_conversation_id, {}).get(message_id)
        if timestamp:
            time_str = timestamp.strftime("%H:%M:%S")
            return f'<span class="timestamp" style="font-size: 10px; color: #999; margin-left: 5px;">{time_str}</span>'
        return ""

    def pin_message(self, message_index):
        """Pin a message to the top of the conversation"""
        if self.current_conversation_id not in self.pinned_messages:
            self.pinned_messages[self.current_conversation_id] = []
        
        if message_index not in self.pinned_messages[self.current_conversation_id]:
            self.pinned_messages[self.current_conversation_id].append(message_index)
            self.refresh_chat_display()
            self.status_bar.showMessage(f"📌 Message pinned", 2000)

    def unpin_message(self, message_index):
        """Unpin a message"""
        if (self.current_conversation_id in self.pinned_messages and 
            message_index in self.pinned_messages[self.current_conversation_id]):
            self.pinned_messages[self.current_conversation_id].remove(message_index)
            self.refresh_chat_display()
            self.status_bar.showMessage(f"📌 Message unpinned", 2000)

    def edit_last_prompt(self):
        """Allow editing of the last user prompt"""
        if not self.chat_history:
            return
        
        # Find the last user message
        last_user_msg_idx = None
        for i in range(len(self.chat_history) - 1, -1, -1):
            if self.chat_history[i].get('role') == 'user':
                last_user_msg_idx = i
                break
        
        if last_user_msg_idx is None:
            return
        
        last_prompt = self.chat_history[last_user_msg_idx]['content']
        new_prompt, ok = QInputDialog.getMultiLineText(
            self, "Edit Last Prompt", "Edit your last prompt:", last_prompt
        )
        
        if ok and new_prompt.strip():
            # Remove all messages after the last user message
            self.chat_history = self.chat_history[:last_user_msg_idx + 1]
            # Update the last user message
            self.chat_history[last_user_msg_idx]['content'] = new_prompt.strip()
            
            # Refresh display and regenerate response
            self.refresh_chat_display()
            self.generate_response(new_prompt.strip())

    def show_token_count(self):
        """Display token count for current context"""
        if not TIKTOKEN_AVAILABLE:
            self.status_bar.showMessage("Token counting not available", 3000)
            return
        
        try:
            # Get current context
            context = ""
            for msg in self.chat_history:
                context += f"{msg['role']}: {msg['content']}\n"
            
            # Add current input
            current_input = self.input_entry.toPlainText()
            if current_input:
                context += f"user: {current_input}\n"
            
            # Count tokens (using cl100k_base encoding as default)
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            token_count = len(encoding.encode(context))
            
            # Update status bar
            self.status_bar.showMessage(f"🔢 Token count: {token_count}", 5000)
            
        except Exception as e:
            self.status_bar.showMessage(f"❌ Token counting failed: {e}", 3000)

    def create_conversation_folder(self, folder_name):
        """Create a new folder for organizing conversations"""
        if folder_name not in self.conversation_folders:
            self.conversation_folders[folder_name] = []
            self.refresh_conversation_list()
            self.status_bar.showMessage(f"📁 Folder '{folder_name}' created", 2000)

    def move_conversation_to_folder(self, conversation_id, folder_name):
        """Move conversation to a specific folder"""
        # Remove from other folders
        for folder, convs in self.conversation_folders.items():
            if conversation_id in convs:
                convs.remove(conversation_id)
        
        # Add to new folder
        if folder_name not in self.conversation_folders:
            self.conversation_folders[folder_name] = []
        
        self.conversation_folders[folder_name].append(conversation_id)
        self.refresh_conversation_list()

    def archive_conversation(self, conversation_id):
        """Archive a conversation"""
        self.archived_conversations.add(conversation_id)
        self.refresh_conversation_list()
        self.status_bar.showMessage(f"📦 Conversation archived", 2000)

    def search_conversation_content(self, search_term):
        """Search within current conversation with highlighting"""
        if not self.chat_history:
            return
        
        matches = []
        for i, msg in enumerate(self.chat_history):
            if search_term.lower() in msg['content'].lower():
                matches.append((i, msg))
        
        if matches:
            # Highlight matches in the display

            self.highlight_search_results(search_term, matches)
            self.status_bar.showMessage(f"🔍 Found {len(matches)} matches", 3000)
        else:
            self.status_bar.showMessage("❌ No matches found", 2000)

    def highlight_search_results(self, search_term, matches):
        """Highlight search results in the chat display with real HTML highlighting (fix html.escape usage)"""
        import html as htmlmod
        html = ""
        for i, msg in enumerate(self.chat_history):
            content = htmlmod.escape(msg['content'])
            if any(i == idx for idx, _ in matches):
                # Highlight all occurrences of the search term (case-insensitive)
                pattern = re.compile(re.escape(search_term), re.IGNORECASE)
                content = pattern.sub(
                    lambda m: f'<span style="background: #ffe066; color: #222;">{m.group(0)}</span>',
                    content
                )
            html += f'<div style="margin-bottom:8px;"><b>{msg["role"]}:</b> {content}</div>'
        self.chat_display.setHtml(html)
        self.scroll_to_bottom()

    def setup_context_menu(self):
        """Set up context menu for conversation list"""
        self.conv_listbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.conv_listbox.customContextMenuRequested.connect(self.show_conversation_context_menu)

    def show_conversation_context_menu(self, position):
        """Show context menu for conversation list"""
        item = self.conv_listbox.itemAt(position)
        if not item:
            return
        
        context_menu = QMenu(self)
        
        # Rename conversation
        rename_action = QAction("📝 Rename", self)
        rename_action.triggered.connect(lambda: self.rename_conversation(item))
        context_menu.addAction(rename_action)
        
        # Move to folder
        folder_menu = context_menu.addMenu("📁 Move to Folder")
        if folder_menu:  # Check if menu was created successfully
            for folder_name in self.conversation_folders.keys():
                folder_action = QAction(folder_name, self)
                folder_action.triggered.connect(lambda checked, f=folder_name: self.move_conversation_to_folder(
                    self.conversation_map[item.text()], f))
                folder_menu.addAction(folder_action)
            
            # Create new folder
            new_folder_action = QAction("📁 New Folder", self)
            new_folder_action.triggered.connect(self.create_new_folder)
            folder_menu.addAction(new_folder_action)
        
        context_menu.addSeparator()
        
        # Archive conversation
        archive_action = QAction("📦 Archive", self)
        archive_action.triggered.connect(lambda: self.archive_conversation(self.conversation_map[item.text()]))
        context_menu.addAction(archive_action)
        
        # Delete conversation
        delete_action = QAction("🗑️ Delete", self)
        delete_action.triggered.connect(lambda: self.delete_conversation(self.conversation_map[item.text()]))
        context_menu.addAction(delete_action)
        
        context_menu.exec(self.conv_listbox.mapToGlobal(position))

    def refresh_conversation_list(self):
        """Refresh the conversation list display"""
        self.conv_listbox.clear()
        self.conversation_map = {}
        
        # Load all conversations
        conversations_dir = "conversations"
        if os.path.exists(conversations_dir):
            conv_files = [f for f in os.listdir(conversations_dir) if f.endswith('.json')]
            for conv_file in conv_files:
                conv_id = conv_file[:-5]  # Remove .json extension
                if (conv_id not in self.archived_conversations and 
                    not any(conv_id in folder_convs for folder_convs in self.conversation_folders.values())):
                    conv_name = self.get_conversation_display_name(conv_id)
                    conv_item = QListWidgetItem(f"💬 {conv_name}")
                    conv_item.setData(Qt.ItemDataRole.UserRole, conv_id)
                    self.conv_listbox.addItem(conv_item)
                    self.conversation_map[conv_item.text()] = conv_id

    def get_conversation_display_name(self, conv_id):
        """Get display name for a conversation"""
        try:
            filepath = f"conversations/{conv_id}.json"
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                if data:
                    first_msg = data[0]['content'][:50]



                    if len(data[0]['content']) > 50:
                        first_msg += "..."
                    return f"{first_msg} ({len(data)} msgs)"
            return conv_id
        except Exception:
            return conv_id

    def initialize_rag_system(self):
        """Initialize RAG system with vector store and embeddings"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not FAISS_AVAILABLE:
            self.status_bar.showMessage("RAG dependencies not available", 3000)
            return False
        
        try:
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize vector store
            embedding_dim = 384  # MiniLM embedding dimension
            self.vector_store = faiss.IndexFlatL2(embedding_dim)
            
            # Initialize document store
            self.document_store = []
            
            # Create knowledge base directory
            os.makedirs("knowledge_base", exist_ok=True)
            
            self.rag_enabled = True
            self.status_bar.showMessage("✅ RAG system initialized", 2000)
            return True
            
        except Exception as e:
            self.status_bar.showMessage(f"❌ RAG initialization failed: {e}", 3000)
            return False

    def add_document_to_knowledge_base(self, file_path):
        """Add a document to the knowledge base"""
        if not self.rag_enabled:
            if not self.initialize_rag_system():
                return
        
        try:
            # Load document based on file type
            if file_path.endswith('.pdf'):
                content = self.extract_pdf_content(file_path)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif file_path.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif file_path.endswith('.docx'):
                content = self.extract_docx_content(file_path)
            else:
                self.status_bar.showMessage("❌ Unsupported file type", 3000)
                return
            
            # Split content into chunks
            chunks = self.split_document_into_chunks(content)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks)
            
            # Add to vector store
            self.vector_store.add(embeddings)
            
            # Store document metadata
            doc_id = len(self.document_store)
            for i, chunk in enumerate(chunks):
                self.document_store.append({
                    'id': f"{doc_id}_{i}",
                    'content': chunk,
                    'source': os.path.basename(file_path),
                    'chunk_index': i
                })
            
            # Save knowledge base
            self.save_knowledge_base()
            
            self.status_bar.showMessage(f"📚 Added {len(chunks)} chunks from {os.path.basename(file_path)}", 3000)
            
        except Exception as e:
            self.status_bar.showMessage(f"❌ Failed to add document: {e}", 3000)

    def extract_pdf_content(self, file_path):
        """Extract text content from PDF file"""
        if not PDF_AVAILABLE:
            raise Exception("PDF support not available")
        
        content = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
        return content

    def extract_docx_content(self, file_path):
        """Extract text content from DOCX file"""
        if not DOCX_AVAILABLE:
            raise Exception("DOCX support not available")
        
        doc = Document(file_path)
        content = ""
        for paragraph in doc.paragraphs:
            content += paragraph.text + "\n"
        return content

    def split_document_into_chunks(self, content, chunk_size=1000, overlap=200):
        """Split document into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - overlap
            if start >= len(content):
                break
        return chunks

    def search_knowledge_base(self, query, k=5):
        """Search knowledge base for relevant chunks"""
        if not self.rag_enabled or not self.document_store:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Search vector store
            distances, indices = self.vector_store.search(query_embedding, k)
            
            # Get relevant chunks
            relevant_chunks = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.document_store):
                    chunk_data = self.document_store[idx].copy()
                    chunk_data['relevance_score'] = float(distances[0][i])
                    relevant_chunks.append(chunk_data)
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            return []

    def save_knowledge_base(self):
        """Save knowledge base to disk"""
        try:
            # Save vector store
            faiss.write_index(self.vector_store, "knowledge_base/vector_store.index")
            
            # Save document store
            with open("knowledge_base/document_store.pkl", 'wb') as f:
                pickle.dump(self.document_store, f)
                
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")

    def load_knowledge_base(self):
        """Load knowledge base from disk"""
        try:
            if os.path.exists("knowledge_base/vector_store.index"):
                self.vector_store = faiss.read_index("knowledge_base/vector_store.index")
            
            if os.path.exists("knowledge_base/document_store.pkl"):
                with open("knowledge_base/document_store.pkl", 'rb') as f:
                    self.document_store = pickle.load(f)
            
            if self.vector_store and self.document_store:
                self.rag_enabled = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
        
        return False

    def toggle_rag_for_prompt(self):
        """Toggle RAG for the current prompt"""
        self.rag_enabled = not self.rag_enabled
        status = "enabled" if self.rag_enabled else "disabled"
        self.status_bar.showMessage(f"📚 RAG {status}", 2000)

    def create_prompt_with_rag(self, user_prompt):
        """Create prompt with RAG context"""
        if not self.rag_enabled:
            return user_prompt
        
        # Search knowledge base
        relevant_chunks = self.search_knowledge_base(user_prompt)
        
        if not relevant_chunks:
            return user_prompt
        
        # Build context
        context = "Based on the following information:\n\n"
        for chunk in relevant_chunks:
            context += f"From {chunk['source']}:\n{chunk['content']}\n\n"
        
        context += f"Please answer the following question: {user_prompt}"
        
        return context

    def show_rag_sources(self, relevant_chunks):
        """Show RAG sources used in response"""
        if not relevant_chunks:
            return
        
        sources_html = "<div class='rag-sources' style='background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px;'>"
        sources_html += "<h4>📚 Sources used:</h4>"
        
        for chunk in relevant_chunks:
            sources_html += f"<p><strong>{chunk['source']}</strong> (relevance: {chunk['relevance_score']:.2f})</p>"
            sources_html += f"<p style='font-size: 12px; color: #666;'>{chunk['content'][:200]}...</p>"
        
        sources_html += "</div>"
        
        # Add to chat display
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(sources_html)

    def setup_knowledge_base_ui(self):
        """Set up knowledge base management UI"""
        # Add knowledge base button to toolbar
        kb_button = ModernButton("📚 Knowledge Base", self.get_icon_path("general", "book"))
        kb_button.clicked.connect(self.show_knowledge_base_dialog)
        
        # Add to toolbar (you'll need to add this to your toolbar setup)
        return kb_button

    def show_knowledge_base_dialog(self):
        """Show knowledge base management dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📚 Knowledge Base Manager")
        dialog.setFixedSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Document list
        doc_list = QListWidget()
        for doc in self.document_store:
            doc_list.addItem(f"{doc['source']} - Chunk {doc['chunk_index']}")
        layout.addWidget(doc_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("📁 Add Document")
        add_button.clicked.connect(self.add_document_dialog)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("🗑️ Remove Selected")
        remove_button.clicked.connect(lambda: self.remove_document_from_kb(doc_list))
        button_layout.addWidget(remove_button)
        
        clear_button = QPushButton("🗑️ Clear All")
        clear_button.clicked.connect(self.clear_knowledge_base)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        
        # Close button
        close_button = QPushButton("✅ Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()

    def add_document_dialog(self):
        """Show dialog to add document to knowledge base"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Add Document to Knowledge Base", 
            "", "Documents (*.pdf *.txt *.md *.docx)"
        )
        
        if file_path:
            self.add_document_to_knowledge_base(file_path)

    def remove_document_from_kb(self, doc_list):
        """Remove selected document from knowledge base"""
        current_item = doc_list.currentItem()
        if current_item:
            # This would need more sophisticated implementation
            # to properly remove from vector store and document store
            self.status_bar.showMessage("Document removal not yet implemented", 3000)

    def clear_knowledge_base(self):
        """Clear entire knowledge base"""
        reply = QMessageBox.question(
            self, "Clear Knowledge Base",
            "Are you sure you want to clear the entire knowledge base?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.document_store = []
            if FAISS_AVAILABLE:
                embedding_dim = 384
                self.vector_store = faiss.IndexFlatL2(embedding_dim)
            
            # Remove files
            kb_files = ["knowledge_base/vector_store.index", "knowledge_base/document_store.pkl"]
            for file_path in kb_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            self.status_bar.showMessage("🗑️ Knowledge base cleared", 2000)

    def show_about_dialog(self):
        """Show the About The Oracle dialog"""
        about_text = (
            "<h2>The Oracle</h2>"
            "<p>Version: 1.0.0</p>"
            "<p>License: MIT</p>"
            "<p><a href='https://github.com/yourrepo/oracle'>Project Repository</a></p>"
            "<p>Dependencies:</p>"
            "<ul>"
            "<li>PyQt6</li>"
            "<li>sentence-transformers</li>"
            "<li>faiss</li>"
            "<li>keyring</li>"
            "<li>and more...</li>"
            "</ul>"
        )
        QMessageBox.about(self, "About The Oracle", about_text)

    def show_threaded_reply_dialog(self, message_index):
        """Show dialog to reply to a specific message (threaded reply)"""
        original_msg = self.chat_history[message_index]['content']
        reply_text, ok = QInputDialog.getMultiLineText(
            self, "Threaded Reply", f"Reply to:\n{original_msg}", ""
        )
        if ok and reply_text.strip():
            # Store parent index for threading
            self.add_message('user', reply_text.strip(), parent_index=message_index)
            self.generate_response(reply_text.strip())

    def add_message(self, role, content, parent_index=None):
        """Add a message to chat history, supporting threading"""
        msg = {'role': role, 'content': content}
        if parent_index is not None:
            msg['parent'] = parent_index
        self.chat_history.append(msg)
        self.refresh_chat_display()

    def context_menu_for_message(self, message_index):
        """Show context menu for a message (threaded reply, pin, edit, etc.)"""
        menu = QMenu(self)
        reply_action = QAction("Reply (Threaded)", self)
        reply_action.triggered.connect(lambda: self.show_threaded_reply_dialog(message_index))
        menu.addAction(reply_action)
        pin_action = QAction("Pin Message", self)
        pin_action.triggered.connect(lambda: self.pin_message(message_index))
        menu.addAction(pin_action)
        if self.chat_history[message_index].get('role') == 'user':
            edit_action = QAction("Edit This Prompt", self)
            edit_action.triggered.connect(lambda: self.edit_specific_prompt(message_index))
            menu.addAction(edit_action)
        menu.exec(QCursor.pos())

    def edit_specific_prompt(self, message_index):
        """Edit a specific user prompt (for threaded or normal messages)"""
        old_prompt = self.chat_history[message_index]['content']
        new_prompt, ok = QInputDialog.getMultiLineText(
            self, "Edit Prompt", "Edit your prompt:", old_prompt
        )
        if ok and new_prompt.strip():
            self.chat_history[message_index]['content'] = new_prompt.strip()
            self.refresh_chat_display()
            self.generate_response(new_prompt.strip())

    def mousePressEvent(self, event):
        """Override mouse press to show message context menu on right-click"""
        if event.button() == Qt.MouseButton.RightButton:
            cursor = self.chat_display.cursorForPosition(event.pos())
            block = cursor.block()
            message_index = block.blockNumber()
            if 0 <= message_index < len(self.chat_history):
                self.context_menu_for_message(message_index)
        super().mousePressEvent(event)

    def render_threaded_messages(self):
        """Render messages with threading/branching UI (fix html.escape usage, remove duplicate)"""
        import html as htmlmod
        html = ""
        for i, msg in enumerate(self.chat_history):
            indent = 0
            parent = msg.get('parent')
            while parent is not None:
                indent += 1
                parent = self.chat_history[parent].get('parent')
            html += f'<div style="margin-left: {indent*30}px;">{msg["role"]}: {htmlmod.escape(msg["content"])}</div>'
        self.chat_display.setHtml(html)
