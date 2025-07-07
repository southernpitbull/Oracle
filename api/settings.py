"""
API Settings dialog for managing API keys
"""
from core.config import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                        QGroupBox, QHBoxLayout, QScrollArea, QWidget, QMessageBox,
                        QSettings, json, webbrowser)
from pathlib import Path


class APISettingsDialog(QDialog):
    """Comprehensive dialog for managing API keys"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Key Management")
        self.setModal(True)
        self.resize(600, 500)
        
        # Load config from launcher's config file
        self.config_path = Path.home() / ".the_oracle_config.json"
        self.load_config()
        
        self.setup_ui()
        self.load_current_settings()
    
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
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {e}")
            return False
    
    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("The Oracle - API Key Management")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Enter your API keys for different LLM providers. Keys are stored securely on your system.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 20px;")
        main_layout.addWidget(desc_label)
        
        # Scroll area for API key inputs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
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
            desc.setStyleSheet("color: #666; font-size: 12px;")
            group_layout.addWidget(desc)
            
            # API key input with show/hide toggle
            key_layout = QHBoxLayout()
            
            key_input = QLineEdit()
            key_input.setPlaceholderText(info['placeholder'])
            key_input.setEchoMode(QLineEdit.EchoMode.Password)
            
            show_button = QPushButton("👁")
            show_button.setMaximumWidth(30)
            show_button.setCheckable(True)
            show_button.toggled.connect(lambda checked, inp=key_input: 
                inp.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password))
            
            clear_button = QPushButton("Clear")
            clear_button.setMaximumWidth(60)
            clear_button.clicked.connect(lambda checked, inp=key_input: inp.clear())
            
            key_layout.addWidget(QLabel("API Key:"))
            key_layout.addWidget(key_input)
            key_layout.addWidget(show_button)
            key_layout.addWidget(clear_button)
            
            group_layout.addLayout(key_layout)
            
            # Environment variable info
            env_label = QLabel(f"Environment variable: {info['env_var']}")
            env_label.setStyleSheet("color: #888; font-size: 11px;")
            group_layout.addWidget(env_label)
            
            # Website link
            website_button = QPushButton(f"Get API Key from {info['name']}")
            website_button.setStyleSheet("color: #0066cc; border: none; text-align: left;")
            website_button.clicked.connect(lambda checked, url=info['website']: self.open_website(url))
            group_layout.addWidget(website_button)
            
            self.api_inputs[api_key] = key_input
            group.setLayout(group_layout)
            scroll_layout.addWidget(group)
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px;")
        main_layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet("background-color: #007acc; color: white; padding: 8px 16px; border-radius: 4px;")
        save_button.clicked.connect(self.save_settings)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("background-color: #666; color: white; padding: 8px 16px; border-radius: 4px;")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        main_layout.addLayout(button_layout)
    
    def load_current_settings(self):
        """Load current API key settings"""
        settings = QSettings("TheOracle", "TheOracle")
        
        # Load from QSettings
        for api_key in self.api_inputs.keys():
            stored_key = settings.value(f"{api_key}_api_key", "")
            if stored_key:
                self.api_inputs[api_key].setText(stored_key)
    
    def save_settings(self):
        """Save API key settings"""
        settings = QSettings("TheOracle", "TheOracle")
        saved_keys = []
        
        for api_key, input_widget in self.api_inputs.items():
            key_value = input_widget.text().strip()
            if key_value:
                settings.setValue(f"{api_key}_api_key", key_value)
                self.config['api_keys'][api_key] = key_value
                saved_keys.append(self.api_info[api_key]['name'])
            else:
                settings.remove(f"{api_key}_api_key")
                if api_key in self.config['api_keys']:
                    del self.config['api_keys'][api_key]
        
        # Save to config file
        self.save_config()
        
        if saved_keys:
            self.status_label.setText(f"✓ Saved API keys for: {', '.join(saved_keys)}")
            self.status_label.setStyleSheet("color: #007acc; font-size: 12px; margin: 10px;")
        else:
            self.status_label.setText("ℹ No API keys to save")
            self.status_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px;")
        
        # Close dialog after short delay
        from core.config import QTimer
        QTimer.singleShot(1500, self.accept)
    
    def open_website(self, url):
        """Open website in default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open website: {e}")
