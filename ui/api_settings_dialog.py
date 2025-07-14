"""
API Settings Dialog for The Oracle AI Chat Application.
Allows users to configure API keys for different providers.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QGridLayout, QCheckBox, QTabWidget, QWidget, QScrollArea,
    QFrame, QMessageBox, QTextEdit, QComboBox
)
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFont, QIcon
from .theme_styles import get_dialog_theme_styles, get_icon_path


class APISettingsDialog(QDialog):
    """Dialog for configuring API keys and settings"""

    # Signal emitted when settings are applied

    def __init__(self, parent=None, dark_theme=True):
        super().__init__(parent)
        self.dark_theme = dark_theme
        self.settings = QSettings("TheOracle", "TheOracle")

        # Set window icon
        icon_path = get_icon_path("settings", "general")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self.setupUI()
        self.load_saved_settings()

    def setupUI(self):
        """Set up the user interface"""
        self.setWindowTitle("API Settings - The Oracle")
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 700)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)

        title_label = QLabel("🔑 API Configuration")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Configure API keys for different AI providers")
        subtitle_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(subtitle_label)

        layout.addWidget(header_frame)

        # Create scroll area for settings
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # OpenAI Settings
        openai_group = self.create_provider_group("OpenAI", "openai_api_key", "sk-...")
        scroll_layout.addWidget(openai_group)

        # Anthropic Settings
        anthropic_group = self.create_provider_group("Anthropic", "anthropic_api_key", "sk-ant-...")
        scroll_layout.addWidget(anthropic_group)

        # Google Settings
        google_group = self.create_provider_group("Google", "google_api_key", "AIza...")
        scroll_layout.addWidget(google_group)

        # Nebius Settings
        nebius_group = self.create_provider_group("Nebius", "nebius_api_key", "AQVN...")
        scroll_layout.addWidget(nebius_group)

        # OpenRouter Settings
        openrouter_group = self.create_provider_group("OpenRouter", "openrouter_api_key", "sk-or-...")
        scroll_layout.addWidget(openrouter_group)

        # Ollama Settings
        ollama_group = self.create_ollama_group()
        scroll_layout.addWidget(ollama_group)

        # Test Connection Button
        test_group = QGroupBox("🔗 Test Connections")
        test_layout = QVBoxLayout(test_group)
        
        test_label = QLabel("Test API connections to verify your keys are working:")
        test_layout.addWidget(test_label)
        
        test_button = QPushButton("🧪 Test All Connections")
        test_button.clicked.connect(self.test_connections)
        test_layout.addWidget(test_button)
        
        scroll_layout.addWidget(test_group)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()

        self.clear_button = QPushButton("🗑️ Clear All")
        self.clear_button.clicked.connect(self.clear_all_keys)
        button_layout.addWidget(self.clear_button)

        button_layout.addStretch()

        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("💾 Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        # Apply theme-aware styling
        self.apply_theme_styles()

    def create_provider_group(self, provider_name, key_name, placeholder):
        """Create a provider settings group"""
        group = QGroupBox(f"{provider_name} API Settings")
        layout = QVBoxLayout(group)

        # API Key
        key_layout = QHBoxLayout()
        key_label = QLabel("API Key:")
        key_label.setMinimumWidth(80)
        key_layout.addWidget(key_label)

        self.key_edits[key_name] = QLineEdit()
        self.key_edits[key_name].setPlaceholderText(placeholder)
        self.key_edits[key_name].setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addWidget(self.key_edits[key_name])

        # Show/Hide button
        show_button = QPushButton("👁️")
        show_button.setMaximumWidth(40)
        show_button.clicked.connect(lambda: self.toggle_key_visibility(key_name))
        key_layout.addWidget(show_button)

        layout.addLayout(key_layout)

        # Status indicator
        status_layout = QHBoxLayout()
        status_label = QLabel("Status:")
        status_layout.addWidget(status_label)

        self.status_labels[key_name] = QLabel("❓ Not tested")
        self.status_labels[key_name].setStyleSheet("color: gray;")
        status_layout.addWidget(self.status_labels[key_name])

        status_layout.addStretch()
        layout.addLayout(status_layout)

        return group

    def create_ollama_group(self):
        """Create Ollama settings group"""
        group = QGroupBox("Ollama Local Server")
        layout = QVBoxLayout(group)

        # Server URL
        url_layout = QHBoxLayout()
        url_label = QLabel("Server URL:")
        url_label.setMinimumWidth(80)
        url_layout.addWidget(url_label)

        self.key_edits["ollama_url"] = QLineEdit()
        self.key_edits["ollama_url"].setPlaceholderText("http://localhost:11434")
        self.key_edits["ollama_url"].setText("http://localhost:11434")
        url_layout.addWidget(self.key_edits["ollama_url"])

        layout.addLayout(url_layout)

        # Status indicator
        status_layout = QHBoxLayout()
        status_label = QLabel("Status:")
        status_layout.addWidget(status_label)

        self.status_labels["ollama_url"] = QLabel("❓ Not tested")
        self.status_labels["ollama_url"].setStyleSheet("color: gray;")
        status_layout.addWidget(self.status_labels["ollama_url"])

        status_layout.addStretch()
        layout.addLayout(status_layout)

        return group

    def toggle_key_visibility(self, key_name):
        """Toggle API key visibility"""
        edit = self.key_edits[key_name]
        if edit.echoMode() == QLineEdit.EchoMode.Password:
            edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            edit.setEchoMode(QLineEdit.EchoMode.Password)

    def load_saved_settings(self):
        """Load saved API settings"""
        # Initialize key edits and status labels
        self.key_edits = {}
        self.status_labels = {}

        # Load saved values
        for key_name in ["openai_api_key", "anthropic_api_key", "google_api_key", 
                        "nebius_api_key", "openrouter_api_key", "ollama_url"]:
            saved_value = self.settings.value(key_name, "")
            if key_name in self.key_edits:
                self.key_edits[key_name].setText(saved_value)

    def save_settings(self):
        """Save API settings"""
        try:
            # Save all API keys
            for key_name, edit in self.key_edits.items():
                value = edit.text().strip()
                self.settings.setValue(key_name, value)

            # Emit signal that settings were applied
            self.settings_applied.emit({
                "openai_api_key": self.key_edits.get("openai_api_key", "").text().strip(),
                "anthropic_api_key": self.key_edits.get("anthropic_api_key", "").text().strip(),
                "google_api_key": self.key_edits.get("google_api_key", "").text().strip(),
                "nebius_api_key": self.key_edits.get("nebius_api_key", "").text().strip(),
                "openrouter_api_key": self.key_edits.get("openrouter_api_key", "").text().strip(),
                "ollama_url": self.key_edits.get("ollama_url", "").text().strip()
            })

            QMessageBox.information(self, "Success", "API settings saved successfully!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def clear_all_keys(self):
        """Clear all API keys"""
        reply = QMessageBox.question(
            self, "Clear All Keys", 
            "Are you sure you want to clear all API keys? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for edit in self.key_edits.values():
                edit.clear()
            
            # Clear saved settings
            for key_name in ["openai_api_key", "anthropic_api_key", "google_api_key", 
                           "nebius_api_key", "openrouter_api_key"]:
                self.settings.remove(key_name)

    def test_connections(self):
        """Test API connections"""
        try:
            # Test each provider
            for key_name, edit in self.key_edits.items():
                if key_name == "ollama_url":
                    self.test_ollama_connection(edit.text().strip())
                else:
                    self.test_api_key(key_name, edit.text().strip())

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to test connections: {str(e)}")

    def test_api_key(self, key_name, api_key):
        """Test a specific API key"""
        if not api_key:
            self.status_labels[key_name].setText("❌ No key provided")
            self.status_labels[key_name].setStyleSheet("color: red;")
            return

        # Simple validation - check if key has expected format
        if key_name == "openai_api_key" and not api_key.startswith("sk-"):
            self.status_labels[key_name].setText("❌ Invalid format")
            self.status_labels[key_name].setStyleSheet("color: red;")
        elif key_name == "anthropic_api_key" and not api_key.startswith("sk-ant-"):
            self.status_labels[key_name].setText("❌ Invalid format")
            self.status_labels[key_name].setStyleSheet("color: red;")
        elif key_name == "google_api_key" and not api_key.startswith("AIza"):
            self.status_labels[key_name].setText("❌ Invalid format")
            self.status_labels[key_name].setStyleSheet("color: red;")
        else:
            self.status_labels[key_name].setText("✅ Valid format")
            self.status_labels[key_name].setStyleSheet("color: green;")

    def test_ollama_connection(self, url):
        """Test Ollama server connection"""
        try:
            import requests
            response = requests.get(f"{url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.status_labels["ollama_url"].setText("✅ Connected")
                self.status_labels["ollama_url"].setStyleSheet("color: green;")
            else:
                self.status_labels["ollama_url"].setText("❌ Connection failed")
                self.status_labels["ollama_url"].setStyleSheet("color: red;")
        except Exception:
            pass

    def apply_theme_styles(self):
        """Apply theme-aware styling"""
        theme_styles = get_dialog_theme_styles(self.dark_theme)
        self.setStyleSheet(theme_styles) 
