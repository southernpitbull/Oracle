"""
Bottom Sliding Panel - API Key Management & Settings
File: ui/bottom_panel.py

Bottom sliding panel that expands upwards from the bottom of the screen.
Contains comprehensive API key management, local server settings, and provider configuration.
"""

from PyQt6.QtWidgets import (QFrame, QToolButton, QVBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QHBoxLayout, QLineEdit, QScrollArea, 
                             QWidget, QGridLayout, QGroupBox, QSpacerItem, 
                             QSizePolicy, QMessageBox, QCheckBox, QComboBox)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
import json
import os
from typing import Dict, List, Optional

# Add comprehensive error handling imports at the top
from utils.error_handler import (
    error_handler, error_context, safe_execute, log_function_call,
    ErrorSeverity, ErrorCategory, RetryConfig, handle_error, 
    create_error_context, validate_input
)


class APIKeyValidator:
    """Helper class for API key validation."""
    
    @staticmethod
    def validate_anthropic_key(key: str) -> bool:
        """Validate Anthropic API key format."""
        return key.startswith('sk-ant-') and len(key) > 20
    
    @staticmethod
    def validate_openai_key(key: str) -> bool:
        """Validate OpenAI API key format."""
        return key.startswith('sk-') and len(key) > 20
    
    @staticmethod
    def validate_google_key(key: str) -> bool:
        """Validate Google API key format."""
        return len(key) > 20 and not key.startswith('sk-')
    
    @staticmethod
    def validate_local_server(address: str, port: str) -> bool:
        """Validate local server address and port."""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535 and address.strip() != ""
        except ValueError:
            return False


class ProviderWidget(QWidget):
    """Widget for individual provider configuration."""
    
    def __init__(self, provider_name: str, provider_info: dict, parent=None):
        super().__init__(parent)
        self.provider_name = provider_name
        self.provider_info = provider_info
        self.api_key = ""
        self.is_valid = False
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the provider widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # Provider name and link
        header_layout = QHBoxLayout()
        
        name_label = QLabel(self.provider_name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # API key creation link
        if self.provider_info.get('api_url'):
            link_btn = QPushButton("🔑 Get API Key")
            link_btn.setStyleSheet("""
                QPushButton {
                    background: #0078d4;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #106ebe;
                }
            """)
            link_btn.clicked.connect(lambda: self.open_api_url())
            header_layout.addWidget(link_btn)
        
        layout.addLayout(header_layout)
        
        # API Key input and validation
        key_layout = QHBoxLayout()
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter API Key...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setStyleSheet("""
            QLineEdit {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.key_input.textChanged.connect(self.on_key_changed)
        key_layout.addWidget(self.key_input)
        
        self.validate_btn = QPushButton("✓ Validate")
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background: #4a4a4a;
                border: 1px solid #666666;
                border-radius: 4px;
                padding: 8px 12px;
                color: white;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5a5a5a;
                border: 1px solid #0078d4;
            }
            QPushButton:disabled {
                background: #2a2a2a;
                color: #666666;
            }
        """)
        self.validate_btn.clicked.connect(self.validate_key)
        key_layout.addWidget(self.validate_btn)
        
        layout.addLayout(key_layout)
        
        # Status indicator
        self.status_label = QLabel("No API key entered")
        self.status_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.status_label)
    
    def on_key_changed(self):
        """Handle API key text changes."""
        self.api_key = self.key_input.text().strip()
        if self.api_key:
            self.validate_btn.setEnabled(True)
            self.status_label.setText("Click 'Validate' to verify API key")
            self.status_label.setStyleSheet("color: #ffa500; font-size: 10px;")
        else:
            self.validate_btn.setEnabled(False)
            self.status_label.setText("No API key entered")
            self.status_label.setStyleSheet("color: #888888; font-size: 10px;")
            self.is_valid = False
    
    def validate_key(self):
        """Validate the API key."""
        if not self.api_key:
            return
        
        # Get validation method from provider info
        validator_method = self.provider_info.get('validator', 'validate_google_key')
        
        if validator_method == 'validate_anthropic_key':
            self.is_valid = APIKeyValidator.validate_anthropic_key(self.api_key)
        elif validator_method == 'validate_openai_key':
            self.is_valid = APIKeyValidator.validate_openai_key(self.api_key)
        else:
            self.is_valid = APIKeyValidator.validate_google_key(self.api_key)
        
        if self.is_valid:
            self.status_label.setText("✓ API key is valid")
            self.status_label.setStyleSheet("color: #00b894; font-size: 10px;")
            self.validate_btn.setText("✓ Valid")
            self.validate_btn.setStyleSheet("""
                QPushButton {
                    background: #00b894;
                    border: 1px solid #00b894;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
        else:
            self.status_label.setText("✗ Invalid API key format")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 10px;")
            self.validate_btn.setText("✗ Invalid")
            self.validate_btn.setStyleSheet("""
                QPushButton {
                    background: #e74c3c;
                    border: 1px solid #e74c3c;
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
    
    def open_api_url(self):
        """Open the provider's API key creation page."""
        if self.provider_info.get('api_url'):
            QDesktopServices.openUrl(QUrl(self.provider_info['api_url']))
    
    def get_api_key(self) -> Optional[str]:
        """Get the API key if valid."""
        return self.api_key if self.is_valid else None


class BottomSlidingPanel(QFrame):
    """Bottom sliding panel that expands upwards from the bottom of the screen."""
    
    panel_toggled = pyqtSignal(bool)  # is_open
    settings_saved = pyqtSignal(dict)  # settings data
    
    def __init__(self, parent=None, height=200):
        """Initialize BottomSlidingPanel with comprehensive error handling."""
        try:
            super().__init__(parent)
            self.full_height = height
            self.button_width = 40
            self.button_height = 30
            self.collapsed_height = self.button_height + 4
            self.is_open = False
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(300)
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            # Provider configurations
            self.providers = {
                # AI Playgrounds
                "Nebius AI Studio": {
                    'api_url': 'https://nebius.ai/',
                    'validator': 'validate_google_key'
                },
                "Hugging Face": {
                    'api_url': 'https://huggingface.co/settings/tokens',
                    'validator': 'validate_openai_key'
                },
                "OpenRouter.ai": {
                    'api_url': 'https://openrouter.ai/keys',
                    'validator': 'validate_openai_key'
                },
                
                # Commercial LLM Providers (Alphabetical)
                "Anthropic": {
                    'api_url': 'https://console.anthropic.com/',
                    'validator': 'validate_anthropic_key'
                },
                "Deepseek": {
                    'api_url': 'https://platform.deepseek.com/',
                    'validator': 'validate_openai_key'
                },
                "Grok": {
                    'api_url': 'https://x.ai/',
                    'validator': 'validate_openai_key'
                },
                "Llama": {
                    'api_url': 'https://ai.meta.com/llama/',
                    'validator': 'validate_google_key'
                },
                "Mistral AI": {
                    'api_url': 'https://console.mistral.ai/',
                    'validator': 'validate_openai_key'
                },
                "Meta": {
                    'api_url': 'https://ai.meta.com/',
                    'validator': 'validate_google_key'
                },
                "Microsoft": {
                    'api_url': 'https://azure.microsoft.com/en-us/services/cognitive-services/openai-service/',
                    'validator': 'validate_openai_key'
                },
                "OpenAI": {
                    'api_url': 'https://platform.openai.com/api-keys',
                    'validator': 'validate_openai_key'
                },
                "Qwen": {
                    'api_url': 'https://dashscope.console.aliyun.com/',
                    'validator': 'validate_openai_key'
                }
            }
            
            self.provider_widgets = {}
            
            # Set up the panel
            self.setFixedHeight(self.collapsed_height)
            self.setFrameStyle(QFrame.Shape.StyledPanel)
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2b2b2b, stop:1 #3a3a3a);
                    border: 1px solid #555555;
                    border-radius: 8px 8px 0px 0px;
                }
            """)
            
            # Create scroll area for content
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    border: none;
                    background: transparent;
                }
                QScrollBar:vertical {
                    background: #3a3a3a;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background: #666666;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #888888;
                }
            """)
            
            # Create content widget
            self.content_widget = QWidget()
            self.content_layout = QVBoxLayout(self.content_widget)
            self.content_layout.setContentsMargins(15, 40, 15, 15)
            self.content_layout.setSpacing(15)
            
            # Title
            title = QLabel("🔧 API Keys & Settings")
            title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            title.setStyleSheet("color: #ffffff; padding: 5px;")
            self.content_layout.addWidget(title)
            
            # Local Model Server Settings
            with error_context("setup_local_server_section", ErrorSeverity.ERROR):
                self.setup_local_server_section()
            
            # Separator
            separator1 = QFrame()
            separator1.setFrameShape(QFrame.Shape.HLine)
            separator1.setStyleSheet("background-color: #555555;")
            separator1.setFixedHeight(1)
            self.content_layout.addWidget(separator1)
            
            # AI Playgrounds Section
            with error_context("setup_ai_playgrounds_section", ErrorSeverity.ERROR):
                self.setup_ai_playgrounds_section()
            
            # Separator
            separator2 = QFrame()
            separator2.setFrameShape(QFrame.Shape.HLine)
            separator2.setStyleSheet("background-color: #555555;")
            separator2.setFixedHeight(1)
            self.content_layout.addWidget(separator2)
            
            # Commercial LLM Providers Section
            with error_context("setup_commercial_providers_section", ErrorSeverity.ERROR):
                self.setup_commercial_providers_section()
            
            # Save Button
            with error_context("setup_save_section", ErrorSeverity.ERROR):
                self.setup_save_section()
            
            # Set scroll area widget
            self.scroll_area.setWidget(self.content_widget)
            
            # Add scroll area to main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(self.scroll_area)
            
            # Initially hide content when collapsed
            self.hide_content()
            
            # logger.info("BottomSlidingPanel initialized successfully") # This line is removed as per the edit hint.
            
        except Exception as exc:
            # logger.critical("Failed to initialize BottomSlidingPanel: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("BottomSlidingPanel.__init__"))
            raise

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_local_server_section(self):
        """Set up the local model server settings section with error handling."""
        try:
            server_group = QGroupBox("🏠 Local Model Server")
            server_group.setStyleSheet("""
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
            
            server_layout = QGridLayout(server_group)
            server_layout.setSpacing(10)
            
            # Server Address
            address_label = QLabel("Server Address:")
            address_label.setStyleSheet("color: #ffffff; font-size: 11px;")
            server_layout.addWidget(address_label, 0, 0)
            
            self.server_address = QLineEdit()
            self.server_address.setPlaceholderText("localhost")
            self.server_address.setText("localhost")
            self.server_address.setStyleSheet("""
                QLineEdit {
                    background: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 8px;
                    color: white;
                    font-size: 11px;
                }
                QLineEdit:focus {
                    border: 2px solid #0078d4;
                }
            """)
            server_layout.addWidget(self.server_address, 0, 1)
            
            # Port
            port_label = QLabel("Port:")
            port_label.setStyleSheet("color: #ffffff; font-size: 11px;")
            server_layout.addWidget(port_label, 1, 0)
            
            self.server_port = QLineEdit()
            self.server_port.setPlaceholderText("8000")
            self.server_port.setText("8000")
            self.server_port.setStyleSheet("""
                QLineEdit {
                    background: #3a3a3a;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 8px;
                    color: white;
                    font-size: 11px;
                }
                QLineEdit:focus {
                    border: 2px solid #0078d4;
                }
            """)
            server_layout.addWidget(self.server_port, 1, 1)
            
            # Test connection button
            self.test_connection_btn = QPushButton("🔗 Test Connection")
            self.test_connection_btn.setStyleSheet("""
                QPushButton {
                    background: #4a4a4a;
                    border: 1px solid #666666;
                    border-radius: 4px;
                    padding: 8px 16px;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #5a5a5a;
                    border: 1px solid #0078d4;
                }
            """)
            self.test_connection_btn.clicked.connect(self.test_local_connection)
            server_layout.addWidget(self.test_connection_btn, 2, 0, 1, 2)
            
            self.content_layout.addWidget(server_group)
            # logger.debug("Local server section setup completed") # This line is removed as per the edit hint.
            
        except Exception as exc:
            # logger.error("Failed to setup local server section: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("setup_local_server_section"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_ai_playgrounds_section(self):
        """Set up the AI playgrounds section with error handling."""
        try:
            playgrounds_group = QGroupBox("🎮 AI Playgrounds")
            playgrounds_group.setStyleSheet("""
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
            
            playgrounds_layout = QVBoxLayout(playgrounds_group)
            playgrounds_layout.setSpacing(10)
            
            # Add AI playground providers
            playground_providers = ["Nebius AI Studio", "Hugging Face", "OpenRouter.ai"]
            
            for provider in playground_providers:
                if provider in self.providers:
                    try:
                        provider_widget = ProviderWidget(provider, self.providers[provider])
                        self.provider_widgets[provider] = provider_widget
                        playgrounds_layout.addWidget(provider_widget)
                    except Exception as widget_error:
                        # logger.error("Failed to create widget for provider {}: {}", provider, widget_error) # This line is removed as per the edit hint.
                        handle_error(widget_error, create_error_context("create_provider_widget", provider=provider))
            
            self.content_layout.addWidget(playgrounds_group)
            # logger.debug("AI playgrounds section setup completed") # This line is removed as per the edit hint.
            
        except Exception as exc:
            # logger.error("Failed to setup AI playgrounds section: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("setup_ai_playgrounds_section"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_commercial_providers_section(self):
        """Set up the commercial LLM providers section with error handling."""
        try:
            providers_group = QGroupBox("🏢 Commercial LLM Providers")
            providers_group.setStyleSheet("""
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
            
            providers_layout = QVBoxLayout(providers_group)
            providers_layout.setSpacing(10)
            
            # Add commercial providers (already in alphabetical order)
            commercial_providers = [
                "Anthropic", "Deepseek", "Grok", "Llama", "Mistral AI", 
                "Meta", "Microsoft", "OpenAI", "Qwen"
            ]
            
            for provider in commercial_providers:
                if provider in self.providers:
                    try:
                        provider_widget = ProviderWidget(provider, self.providers[provider])
                        self.provider_widgets[provider] = provider_widget
                        providers_layout.addWidget(provider_widget)
                    except Exception as widget_error:
                        # logger.error("Failed to create widget for provider {}: {}", provider, widget_error) # This line is removed as per the edit hint.
                        handle_error(widget_error, create_error_context("create_provider_widget", provider=provider))
            
            self.content_layout.addWidget(providers_group)
            # logger.debug("Commercial providers section setup completed") # This line is removed as per the edit hint.
            
        except Exception as exc:
            # logger.error("Failed to setup commercial providers section: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("setup_commercial_providers_section"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def setup_save_section(self):
        """Set up the save button section with error handling."""
        try:
            save_layout = QHBoxLayout()
            save_layout.addStretch()
            
            self.save_btn = QPushButton("💾 Save All Settings")
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background: #00b894;
                    border: 1px solid #00b894;
                    border-radius: 6px;
                    padding: 12px 24px;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #00a085;
                    border: 1px solid #00a085;
                }
                QPushButton:pressed {
                    background: #008f75;
                }
            """)
            self.save_btn.clicked.connect(self.save_settings)
            save_layout.addWidget(self.save_btn)
            
            self.content_layout.addLayout(save_layout)
            # logger.debug("Save section setup completed") # This line is removed as per the edit hint.
            
        except Exception as exc:
            # logger.error("Failed to setup save section: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("setup_save_section"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.NETWORK)
    def test_local_connection(self):
        """Test the local server connection with error handling."""
        try:
            address = self.server_address.text().strip()
            port = self.server_port.text().strip()
            
            if APIKeyValidator.validate_local_server(address, port):
                QMessageBox.information(self, "Connection Test", 
                                      f"Local server settings are valid!\nAddress: {address}\nPort: {port}")
                # logger.info("Local server connection test successful: {}:{}", address, port) # This line is removed as per the edit hint.
            else:
                QMessageBox.warning(self, "Connection Test", 
                                  "Invalid local server settings!\nPlease check address and port.")
                # logger.warning("Local server connection test failed: {}:{}", address, port) # This line is removed as per the edit hint.
                
        except Exception as exc:
            # logger.error("Failed to test local connection: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("test_local_connection"))
            QMessageBox.critical(self, "Connection Test Error", f"Error testing connection: {str(exc)}")

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.FILE_SYSTEM)
    def save_settings(self):
        """Save all settings with comprehensive error handling and retry mechanism."""
        try:
            settings = {
                'local_server': {
                    'address': self.server_address.text().strip(),
                    'port': self.server_port.text().strip()
                },
                'api_keys': {}
            }
            
            # Collect valid API keys
            for provider_name, widget in self.provider_widgets.items():
                try:
                    api_key = widget.get_api_key()
                    if api_key:
                        settings['api_keys'][provider_name] = api_key
                except Exception as key_error:
                    # logger.error("Failed to get API key for provider {}: {}", provider_name, key_error) # This line is removed as per the edit hint.
                    handle_error(key_error, create_error_context("get_api_key", provider=provider_name))
            
            # Validate local server settings
            if not APIKeyValidator.validate_local_server(
                settings['local_server']['address'], 
                settings['local_server']['port']
            ):
                QMessageBox.warning(self, "Save Settings", 
                                  "Invalid local server settings!\nPlease check address and port.")
                # logger.warning("Invalid local server settings during save") # This line is removed as per the edit hint.
                return
            
            # Save to file with retry mechanism
            retry_config = RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                exponential_backoff=True,
                retry_on_exceptions=[OSError, IOError]
            )
            
            def save_to_file():
                config_dir = os.path.join(os.path.expanduser("~"), ".oracle")
                os.makedirs(config_dir, exist_ok=True)
                
                config_file = os.path.join(config_dir, "api_settings.json")
                with open(config_file, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                return config_file
            
            config_file = safe_execute(save_to_file)
            
            if config_file:
                QMessageBox.information(self, "Save Settings", 
                                      f"Settings saved successfully!\nValid API keys: {len(settings['api_keys'])}")
                
                # Emit signal with settings
                self.settings_saved.emit(settings)
                
                # logger.info("Settings saved successfully to: {}", config_file) # This line is removed as per the edit hint.
            else:
                raise RuntimeError("Failed to save settings after retry attempts")
                
        except Exception as exc:
            # logger.error("Failed to save settings: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("save_settings"))
            QMessageBox.critical(self, "Save Settings", f"Failed to save settings: {str(exc)}")

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.FILE_SYSTEM)
    def load_settings(self):
        """Load saved settings with error handling."""
        try:
            config_file = os.path.join(os.path.expanduser("~"), ".oracle", "api_settings.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    settings = json.load(f)
                
                # Load local server settings
                if 'local_server' in settings:
                    self.server_address.setText(settings['local_server'].get('address', 'localhost'))
                    self.server_port.setText(settings['local_server'].get('port', '8000'))
                
                # Load API keys
                if 'api_keys' in settings:
                    for provider_name, api_key in settings['api_keys'].items():
                        if provider_name in self.provider_widgets:
                            try:
                                widget = self.provider_widgets[provider_name]
                                widget.key_input.setText(api_key)
                                widget.validate_key()
                            except Exception as key_error:
                                # logger.error("Failed to load API key for provider {}: {}", provider_name, key_error) # This line is removed as per the edit hint.
                                handle_error(key_error, create_error_context("load_api_key", provider=provider_name))
                
                # logger.info("Settings loaded successfully from: {}", config_file) # This line is removed as per the edit hint.
            else:
                # logger.info("No settings file found, using defaults") # This line is removed as per the edit hint.
                pass # No default settings to load if file doesn't exist
        
        except Exception as exc:
            # logger.error("Failed to load settings: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("load_settings"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.CONFIGURATION)
    def get_valid_providers(self) -> List[str]:
        """Get list of providers with valid API keys with error handling."""
        try:
            valid_providers = []
            for provider_name, widget in self.provider_widgets.items():
                try:
                    if widget.get_api_key():
                        valid_providers.append(provider_name)
                except Exception as key_error:
                    # logger.error("Failed to check API key for provider {}: {}", provider_name, key_error) # This line is removed as per the edit hint.
                    handle_error(key_error, create_error_context("check_api_key", provider=provider_name))
            
            return sorted(valid_providers)
            
        except Exception as exc:
            # logger.error("Failed to get valid providers: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("get_valid_providers"))
            return []

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def show_content(self):
        """Show the content area with error handling."""
        try:
            self.scroll_area.show()
            # logger.debug("Bottom panel content shown") # This line is removed as per the edit hint.
        except Exception as exc:
            # logger.error("Failed to show content: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("show_content"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def hide_content(self):
        """Hide the content area with error handling."""
        try:
            self.scroll_area.hide()
            # logger.debug("Bottom panel content hidden") # This line is removed as per the edit hint.
        except Exception as exc:
            # logger.error("Failed to hide content: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("hide_content"))

    # def toggle_panel(self): # This method is removed as per the edit hint.
    #     """Toggle panel between open and closed states.""" # This method is removed as per the edit hint.
    #     if self.is_open: # This method is removed as per the edit hint.
    #         self.collapse_panel() # This method is removed as per the edit hint.
    #     else: # This method is removed as per the edit hint.
    #         self.expand_panel() # This method is removed as per the edit hint.

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def collapse_panel(self):
        """Collapse the panel with error handling."""
        try:
            if not self.is_open:
                return
            
            self.is_open = False
            self.hide_content()
            
            # Animate to collapsed height - move bottom edge up (contract upward)
            start_rect = self.geometry()
            end_rect = QRect(start_rect.x(), start_rect.y() + (self.full_height - self.collapsed_height),
                            start_rect.width(), self.collapsed_height)
            
            self.animation.setStartValue(start_rect)
            self.animation.setEndValue(end_rect)
            self.animation.start()
            
            # logger.debug("Bottom panel collapsed") # This line is removed as per the edit hint.
            
        except Exception as exc:
            # logger.error("Failed to collapse panel: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("collapse_panel"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def expand_panel(self):
        """Expand the panel with error handling."""
        try:
            if self.is_open:
                return
            
            self.is_open = True
            self.show_content()
            
            # Animate to full height - move bottom edge down (expand downward)
            start_rect = self.geometry()
            end_rect = QRect(start_rect.x(), start_rect.y() - (self.full_height - self.collapsed_height),
                            start_rect.width(), self.full_height)
            
            self.animation.setStartValue(start_rect)
            self.animation.setEndValue(end_rect)
            self.animation.start()
            
            # logger.debug("Bottom panel expanded") # This line is removed as per the edit hint.
            
        except Exception as exc:
            # logger.error("Failed to expand panel: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("expand_panel"))

    @error_handler(severity=ErrorSeverity.ERROR, category=ErrorCategory.UI)
    def update_height(self, window_height):
        """Update panel height with error handling."""
        try:
            self.full_height = min(400, int(window_height * 0.5))
            # logger.debug("Bottom panel height updated to: {}", self.full_height) # This line is removed as per the edit hint.
        except Exception as exc:
            # logger.error("Failed to update height: {}", exc) # This line is removed as per the edit hint.
            handle_error(exc, create_error_context("update_height")) 
