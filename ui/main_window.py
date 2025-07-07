"""
Main window UI components for The Oracle chat application.
"""

import logging
from datetime import datetime
from collections import Counter
from functools import partial

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QLineEdit, QPushButton, QComboBox, QListWidget, QSplitter,
                             QMenuBar, QMenu, QStatusBar, QLabel, QCheckBox, QFileDialog,
                             QMessageBox, QInputDialog, QFrame, QScrollArea, QTextBrowser,
                             QPlainTextEdit, QTabWidget, QGroupBox, QGridLayout, QSpinBox,
                             QDoubleSpinBox, QSlider, QDialog, QDialogButtonBox, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QSettings
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction, QTextCursor, QTextCharFormat, QColor, QCloseEvent

from ..core.config import *
from ..api.multi_provider import MultiProviderClient
from ..api.settings import APISettingsDialog
from ..utils.dependencies import check_and_install_dependencies
from ..utils.file_utils import *
from ..utils.formatting import format_chat_message, format_system_message

logger = logging.getLogger(__name__)


class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Oracle")
        self.setGeometry(100, 100, 1400, 900)
        
        # State variables
        self.current_conversation_id = None
        self.servers = ["http://localhost:11434"]
        self.file_images = []
        self.evaluator = None  # Will be imported from core
        self.knowledge_graph = None  # Will be imported from core
        self.ai_evaluator = None  # Will be imported from core
        self.chat_history = []
        self.conversation_map = {}
        self.conversation_models = {}  # Track model used for each conversation
        self.conversation_cache = {}  # Cache for lazy loaded conversations
        self.conversation_metadata = {}  # Store metadata for lazy loading
        self.response_thread = None
        self.auto_save_timer = None
        self.last_scroll_position = 0
        self.scroll_to_bottom_button = None
        
        # Virtual scrolling variables
        self.virtual_messages = []  # All messages in current conversation
        self.visible_message_widgets = []  # Currently visible message widgets
        self.message_heights = {}  # Cache of message heights
        self.viewport_start = 0  # First visible message index
        self.viewport_end = 0  # Last visible message index
        self.virtual_scroll_enabled = True  # Enable virtual scrolling for long conversations
        
        # Multi-provider client
        self.multi_client = MultiProviderClient()
        self.current_provider = "Ollama"  # Default provider
        self.current_model = None

        # Actions
        self.save_code_blocks_action = QAction("Save Code Blocks", self)
        self.save_code_blocks_action.setCheckable(True)
        self.save_code_blocks_action.setChecked(True)
        self.enable_code_saving = True
        self.save_code_blocks_action.triggered.connect(self.toggle_code_saving)
        self.enable_markdown = True
        self.dark_theme = True
        
        # Initialize the UI
        self.setup_ui()
        self.setup_menu()
        self.setup_styles()
        self.load_providers_and_models()
        self.load_conversations()
        
        # Setup auto-save
        self.setup_auto_save()
        
        # Load most recent conversation or show welcome screen
        self.load_chat_on_startup()

    def setup_ui(self):
        """Set up the main user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        # Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(120)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        toolbar_layout.addWidget(QLabel("Provider:"))
        toolbar_layout.addWidget(self.provider_combo)
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        toolbar_layout.addWidget(QLabel("Model:"))
        toolbar_layout.addWidget(self.model_combo)
        
        # Refresh models button
        self.refresh_models_button = QPushButton("🔄")
        self.refresh_models_button.setMaximumWidth(30)
        self.refresh_models_button.setToolTip("Refresh models for current provider")
        self.refresh_models_button.clicked.connect(self.refresh_current_provider_models)
        toolbar_layout.addWidget(self.refresh_models_button)
        
        # API Settings button
        self.api_settings_button = QPushButton("API Settings")
        self.api_settings_button.clicked.connect(self.open_api_settings)
        toolbar_layout.addWidget(self.api_settings_button)
        
        # Theme toggle
        self.theme_checkbox = QCheckBox("Dark Theme")
        self.theme_checkbox.setChecked(True)
        self.theme_checkbox.stateChanged.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_checkbox)
        
        # Pull model button (for Ollama)
        self.pull_button = QPushButton("Pull Model")
        self.pull_button.clicked.connect(self.pull_model)
        toolbar_layout.addWidget(self.pull_button)
        
        # New chat button
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.clicked.connect(self.new_conversation)
        toolbar_layout.addWidget(self.new_chat_button)
        
        # Search
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search chat...")
        toolbar_layout.addWidget(self.search_entry)
        
        self.search_button = QPushButton("🔍")
        self.search_button.clicked.connect(self.filter_chat)
        toolbar_layout.addWidget(self.search_button)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # Splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Conversation list
        self.conv_listbox = QListWidget()
        self.conv_listbox.setMaximumWidth(250)
        self.conv_listbox.currentRowChanged.connect(self.load_selected_conv)
        splitter.addWidget(self.conv_listbox)
        
        # Chat area
        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)
        
        # Chat display with scroll-to-bottom functionality
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.setOpenExternalLinks(True)  # Enable clickable links
        chat_layout.addWidget(self.chat_display)
        
        # Create and initially hide the scroll-to-bottom button
        self.scroll_to_bottom_button = QPushButton("↓ Scroll to Bottom")
        self.scroll_to_bottom_button.setMaximumHeight(30)
        self.scroll_to_bottom_button.setStyleSheet("""
            QPushButton {
                background-color: #1F6FEB;
                border: 1px solid #1F6FEB;
                border-radius: 15px;
                color: #F0F6FC;
                font-size: 12px;
                padding: 5px 15px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #0969DA;
                border: 1px solid #0969DA;
            }
        """)
        self.scroll_to_bottom_button.clicked.connect(self.scroll_to_bottom)
        self.scroll_to_bottom_button.hide()
        
        # Add scroll button to chat layout
        scroll_button_layout = QHBoxLayout()
        scroll_button_layout.addStretch()
        scroll_button_layout.addWidget(self.scroll_to_bottom_button)
        scroll_button_layout.addStretch()
        chat_layout.addLayout(scroll_button_layout)
        
        # Connect scroll events
        self.chat_display.verticalScrollBar().valueChanged.connect(self.on_scroll_changed)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_entry = QTextEdit()
        self.input_entry.setMaximumHeight(100)
        self.input_entry.setPlaceholderText("Type your message here... (Ctrl+Enter to send)")
        # Add key event handler for Ctrl+Enter
        self.input_entry.keyPressEvent = self.input_key_press_event
        input_layout.addWidget(self.input_entry)
        
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("send_button")  # For styling
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        chat_layout.addLayout(input_layout)
        splitter.addWidget(self.chat_widget)
        
        # Set splitter proportions
        splitter.setSizes([250, 1150])
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Status: Ready")

    def setup_menu(self):
        """Set up the application menu"""
        menubar = self.menuBar()
        if not menubar:
            return
        
        # File menu
        file_menu = menubar.addMenu("File")
        if not file_menu:
            return
        
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
        
        # Chat Settings menu
        chat_menu = menubar.addMenu("Chat Settings")
        if not chat_menu:
            return
        
        markdown_action = QAction("Markdown Formatting", self)
        markdown_action.setCheckable(True)
        markdown_action.setChecked(True)
        markdown_action.triggered.connect(self.toggle_markdown)
        chat_menu.addAction(markdown_action)
        
        code_saving_action = QAction("Save Code Blocks", self)
        code_saving_action.setCheckable(True)
        code_saving_action.setChecked(True)
        code_saving_action.triggered.connect(self.toggle_code_saving)
        chat_menu.addAction(code_saving_action)
        
        # Export submenu
        export_menu = chat_menu.addMenu("Export Chat")
        if export_menu:
            export_actions = [
                ("To JSON", lambda: self.export_chat("json")),
                ("To PDF", lambda: self.export_chat("pdf")),
                ("To TXT", lambda: self.export_chat("txt")),
                ("To HTML", lambda: self.export_chat("html")),
                ("To DOCX", lambda: self.export_chat("docx")),
                ("To ZIP", lambda: self.export_chat("zip"))
            ]
            
            for text, func in export_actions:
                action = QAction(text, self)
                action.triggered.connect(func)
                export_menu.addAction(action)
        
        chat_menu.addSeparator()
        
        summarize_action = QAction("Summarize Chat", self)
        summarize_action.triggered.connect(self.summarize_chat)
        chat_menu.addAction(summarize_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        if not view_menu:
            return
        
        toggle_theme_action = QAction("Toggle Dark/Light Mode", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(toggle_theme_action)
        
        refresh_models_action = QAction("Refresh Models", self)
        refresh_models_action.triggered.connect(self.load_models)
        view_menu.addAction(refresh_models_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        if not tools_menu:
            return
        
        attach_file_action = QAction("Attach File", self)
        attach_file_action.triggered.connect(self.attach_file)
        tools_menu.addAction(attach_file_action)
        
        # Quick actions submenu
        quick_actions_menu = tools_menu.addMenu("Quick Actions")
        if quick_actions_menu:
            quick_actions = [
                ("Explain This", "Explain this concept in simple terms."),
                ("Write Code", "Write a Python function that does X."),
                ("Generate Report", "Summarize the key points.")
            ]
            
            for text, prompt in quick_actions:
                action = QAction(text, self)
                action.triggered.connect(lambda checked, p=prompt: self.input_entry.append(p))
                quick_actions_menu.addAction(action)
        
        # Analysis menu
        analysis_menu = menubar.addMenu("Analysis")
        if not analysis_menu:
            return
        
        analysis_actions = [
            ("Generate Word Cloud", self.generate_word_cloud),
            ("Keyword Frequency Chart", self.plot_keyword_frequency),
            ("Sentiment Over Time", self.sentiment_over_time)
        ]
        
        for text, func in analysis_actions:
            action = QAction(text, self)
            action.triggered.connect(func)
            analysis_menu.addAction(action)

    def setup_styles(self):
        """Apply the comprehensive Noir-Tech theme"""
        # This will be implemented with the styling logic
        pass

    def load_providers_and_models(self):
        """Load available providers and models"""
        # This will be implemented with provider loading logic
        pass

    def load_conversations(self):
        """Load conversation history"""
        # This will be implemented with conversation loading logic
        pass

    def setup_auto_save(self):
        """Set up automatic saving"""
        # This will be implemented with auto-save logic
        pass

    def load_chat_on_startup(self):
        """Load the most recent chat on startup"""
        # This will be implemented with startup logic
        pass

    # Placeholder methods for functionality to be implemented
    def on_provider_changed(self, provider): pass
    def on_model_changed(self, model): pass
    def refresh_current_provider_models(self): pass
    def open_api_settings(self): pass
    def toggle_theme(self): pass
    def pull_model(self): pass
    def new_conversation(self): pass
    def filter_chat(self): pass
    def load_selected_conv(self, index): pass
    def input_key_press_event(self, event): pass
    def send_message(self): pass
    def save_chat(self): pass
    def load_chat(self): pass
    def toggle_markdown(self): pass
    def toggle_code_saving(self): pass
    def export_chat(self, format_type): pass
    def summarize_chat(self): pass
    def load_models(self): pass
    def attach_file(self): pass
    def generate_word_cloud(self): pass
    def plot_keyword_frequency(self): pass
    def sentiment_over_time(self): pass
    def on_scroll_changed(self, value): pass
    def scroll_to_bottom(self): pass
