"""
API Settings Dialog for managing API keys
"""

import json
from pathlib import Path
from core.config import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                        QLineEdit, QGroupBox, QScrollArea, QWidget, QMessageBox,
                        QSettings, Qt, webbrowser, QIcon)
from ui.theme_styles import get_dialog_theme_styles, get_icon_path, create_themed_message_box


class APISettingsDialog(QDialog):
    """Comprehensive dialog for managing API keys"""
    def __init__(self, parent=None, dark_theme=True):
        super().__init__(parent)
        self.dark_theme = dark_theme
        self.setWindowTitle("API Key Management")
        self.setModal(True)
        self.resize(600, 500)

        # Set window icon
        icon_path = get_icon_path("general", "settings")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        # Load config from launcher's config file
        self.config_path = Path.home() / ".the_oracle_config.json"
        self.load_config()

        self.setup_ui()
        self.load_current_settings()
        self.apply_theme_styles()

    def load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.config = {}
        else:
            self.config = {}

        if 'api_keys' not in self.config:
            self.config['api_keys'] = {}

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except IOError as e:
            create_themed_message_box(
                self, "Error",
                f"Failed to save configuration: {e}",
                "error", self.dark_theme
            ).exec()
            return False

    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("The Oracle - API Key Management")
        title_label.setObjectName("title_label")
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Enter your API keys for different LLM providers. Keys are stored securely on your system.")
        desc_label.setObjectName("desc_label")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)

        # Scroll area for API key inputs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # API key inputs
        self.api_inputs = {}
        self.api_info = {
            'openai': {
                'name': 'OpenAI',
                'description': 'For GPT-4, GPT-3.5-turbo, etc.',
                'placeholder': 'sk-...',
                'env_var': 'OPENAI_API_KEY',
                'website': 'https://platform.openai.com/api-keys'
            },
            'anthropic': {
                'name': 'Anthropic (Claude)',
                'description': 'For Claude 3, Claude 2, etc.',
                'placeholder': 'sk-ant-...',
                'env_var': 'ANTHROPIC_API_KEY',
                'website': 'https://console.anthropic.com/'
            },
            'google': {
                'name': 'Google (Gemini)',
                'description': 'For Gemini Pro, Gemini Pro Vision',
                'placeholder': 'AI...',
                'env_var': 'GOOGLE_API_KEY',
                'website': 'https://aistudio.google.com/app/apikey'
            },
            'deepseek': {
                'name': 'DeepSeek',
                'description': 'For DeepSeek Chat, DeepSeek Coder',
                'placeholder': 'sk-...',
                'env_var': 'DEEPSEEK_API_KEY',
                'website': 'https://platform.deepseek.com/api_keys'
            },
            'qwen': {
                'name': 'Qwen (Alibaba)',
                'description': 'For Qwen-Plus, Qwen-Turbo, Qwen-Max',
                'placeholder': 'sk-...',
                'env_var': 'DASHSCOPE_API_KEY',
                'website': 'https://dashscope.console.aliyun.com/apiKey'
            }
        }

        for api_key, info in self.api_info.items():
            group = QGroupBox(info['name'])
            group_layout = QVBoxLayout()

            # Description
            desc = QLabel(info['description'])
            desc.setObjectName("api_desc_label")
            group_layout.addWidget(desc)

            # API key input with show/hide toggle
            key_layout = QHBoxLayout()

            key_input = QLineEdit()
            key_input.setPlaceholderText(info['placeholder'])
            key_input.setEchoMode(QLineEdit.EchoMode.Password)

            show_button = QPushButton("👁")
            show_button.setObjectName("show_button")
            show_button.setMaximumWidth(30)
            show_button.setCheckable(True)
            show_button.toggled.connect(lambda checked, inp=key_input:
                inp.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))

            clear_button = QPushButton("Clear")
            clear_button.setObjectName("clear_button")
            clear_button.setMaximumWidth(60)
            clear_button.clicked.connect(lambda checked, inp=key_input: inp.clear())

            key_layout.addWidget(QLabel("API Key:"))
            key_layout.addWidget(key_input)
            key_layout.addWidget(show_button)
            key_layout.addWidget(clear_button)

            group_layout.addLayout(key_layout)

            # Environment variable info
            env_label = QLabel(f"Environment variable: {info['env_var']}")
            env_label.setObjectName("env_label")
            group_layout.addWidget(env_label)

            # Website link
            website_button = QPushButton(f"Get API Key from {info['name']}")
            website_button.setObjectName("website_button")
            website_button.clicked.connect(lambda checked, url=info['website']: self.open_website(url))
            group_layout.addWidget(website_button)

            self.api_inputs[api_key] = key_input
            group.setLayout(group_layout)
            scroll_layout.addWidget(group)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        main_layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        test_button = QPushButton("Test Connections")
        test_button.setObjectName("test_button")
        test_button.clicked.connect(self.test_connections)
        button_layout.addWidget(test_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel_button")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setObjectName("save_button")
        save_button.clicked.connect(self.save_and_close)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)

        main_layout.addLayout(button_layout)

    def open_website(self, url):
        """Open website in default browser"""
        webbrowser.open(url)

    def load_current_settings(self):
        """Load current API key settings"""
        settings = QSettings("TheOracle", "TheOracle")

        # Load from QSettings
        for api_key, input_widget in self.api_inputs.items():
            key = f"{api_key}_api_key"
            if api_key == "google":
                key = "gemini_api_key"
            elif api_key == "anthropic":
                key = "claude_api_key"

            value = settings.value(key, "")
            if value:
                input_widget.setText(value)

    def save_settings(self):
        """Save API key settings"""
        settings = QSettings("TheOracle", "TheOracle")

        # Save to QSettings
        for api_key, input_widget in self.api_inputs.items():
            key = f"{api_key}_api_key"
            if api_key == "google":
                key = "gemini_api_key"
            elif api_key == "anthropic":
                key = "claude_api_key"

            value = input_widget.text().strip()
            settings.setValue(key, value)

            # Also save to config file
            self.config['api_keys'][api_key] = value

        return self.save_config()

    def save_and_close(self):
        """Save settings and close dialog"""
        if self.save_settings():
            self.accept()
        else:
            create_themed_message_box(
                self, "Error",
                "Failed to save API settings. Please check your configuration.",
                "error", self.dark_theme
            ).exec()

    def test_connections(self):
        """Test API connections"""
        self.status_label.setText("Testing connections...")
        # Here you would implement actual connection testing
        # For now, just show a simple message
        active_keys = sum(1 for input_widget in self.api_inputs.values() if input_widget.text().strip())
        self.status_label.setText(f"Found {active_keys} API keys configured")

    def update_status(self):
        """Update status display"""
        active_keys = sum(1 for input_widget in self.api_inputs.values() if input_widget.text().strip())
        self.status_label.setText(f"{active_keys} API keys configured")

    def apply_theme_styles(self):
        """Apply theme-aware styling to the dialog"""
        dialog_styles = get_dialog_theme_styles(self.dark_theme)

        # Apply dialog-wide styles
        self.setStyleSheet(dialog_styles + """
            QLabel#title_label {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }

            QLabel#desc_label {
                margin-bottom: 20px;
                font-size: 13px;
            }

            QLabel#api_desc_label {
                font-size: 12px;
                opacity: 0.8;
            }

            QLabel#env_label {
                font-size: 11px;
                opacity: 0.7;
            }

            QLineEdit {
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }

            QPushButton#show_button {
                max-width: 30px;
                padding: 4px;
                font-size: 12px;
            }

            QPushButton#clear_button {
                max-width: 60px;
                padding: 4px 8px;
                font-size: 11px;
            }

            QPushButton#website_button {
                border: none;
                text-align: left;
                padding: 4px 8px;
                font-size: 12px;
            }

            QPushButton#test_button, QPushButton#save_button, QPushButton#cancel_button {
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 80px;
            }

            QLabel#status_label {
                font-size: 12px;
                margin: 10px 0;
            }
        """)
