"""
Model Settings Dialog for The Oracle AI Chat Application.
Allows users to configure model parameters like temperature, max tokens, top_p, etc.
"""

import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox,
    QDoubleSpinBox, QGroupBox, QPushButton, QGridLayout, QCheckBox,
    QComboBox, QTabWidget, QWidget, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from .theme_styles import get_dialog_theme_styles, get_icon_path


class ModelSettingsDialog(QDialog):
    """Dialog for configuring model parameters"""

    # Signal emitted when settings are applied

    def __init__(self, parent=None, current_model="", current_provider="", current_settings=None, dark_theme=True):
        super().__init__(parent)
        self.current_model = current_model
        self.current_provider = current_provider
        self.current_settings = current_settings or {}
        self.dark_theme = dark_theme
        self.settings_file = "model_settings.json"

        # Set window icon
        icon_path = get_icon_path("settings", "general")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        self.setupUI()
        self.load_saved_settings()
        self.apply_current_settings()

    def setupUI(self):
        """Set up the user interface"""
        self.setWindowTitle(f"Model Settings - {self.current_model}")
        self.setMinimumSize(500, 600)
        self.setMaximumSize(700, 800)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Model info header
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)

        model_label = QLabel(f"🤖 Model: {self.current_model}")
        model_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(model_label)

        provider_label = QLabel(f"🏭 Provider: {self.current_provider}")
        provider_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(provider_label)

        layout.addWidget(header_frame)

        # Create tabs for different parameter categories
        self.tab_widget = QTabWidget()

        # Core Parameters Tab
        self.core_tab = self.create_core_parameters_tab()
        self.tab_widget.addTab(self.core_tab, "🔧 Core")

        # Advanced Parameters Tab
        self.advanced_tab = self.create_advanced_parameters_tab()
        self.tab_widget.addTab(self.advanced_tab, "⚙️ Advanced")

        # Provider-Specific Tab
        self.provider_tab = self.create_provider_specific_tab()
        self.tab_widget.addTab(self.provider_tab, "🏭 Provider")

        layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()

        self.reset_button = QPushButton("🔄 Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.apply_button = QPushButton("✅ Apply Settings")
        self.apply_button.clicked.connect(self.apply_settings)
        self.apply_button.setDefault(True)
        button_layout.addWidget(self.apply_button)

        layout.addLayout(button_layout)

        # Apply theme-aware styling
        self.apply_theme_styles()

    def create_core_parameters_tab(self):
        """Create the core parameters tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create scroll area for parameters
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Temperature
        temp_group = self.create_parameter_group(
            "🌡️ Temperature",
            "Controls randomness in the output. Higher values make output more random.",
            "temperature",
            0.0, 2.0, 0.01, 0.7, "float"
        )
        scroll_layout.addWidget(temp_group)

        # Max Tokens / Context Window
        tokens_group = self.create_parameter_group(
            "📏 Max Tokens",
            "Maximum number of tokens to generate in the response.",
            "max_tokens",
            100, 128000, 1, 4096, "int"
        )
        scroll_layout.addWidget(tokens_group)

        # Top P
        top_p_group = self.create_parameter_group(
            "🎯 Top P (Nucleus Sampling)",
            "Controls diversity via nucleus sampling. Lower values are more focused.",
            "top_p",
            0.01, 1.0, 0.01, 1.0, "float"
        )
        scroll_layout.addWidget(top_p_group)

        # Top K
        top_k_group = self.create_parameter_group(
            "🔝 Top K",
            "Limits the number of highest probability tokens to consider.",
            "top_k",
            1, 100, 1, 50, "int"
        )
        scroll_layout.addWidget(top_k_group)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return tab

    def create_advanced_parameters_tab(self):
        """Create the advanced parameters tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Frequency Penalty
        freq_penalty_group = self.create_parameter_group(
            "📊 Frequency Penalty",
            "Reduces repetition by penalizing tokens based on their frequency.",
            "frequency_penalty",
            -2.0, 2.0, 0.01, 0.0, "float"
        )
        scroll_layout.addWidget(freq_penalty_group)

        # Presence Penalty
        presence_penalty_group = self.create_parameter_group(
            "👁️ Presence Penalty",
            "Encourages the model to talk about new topics.",
            "presence_penalty",
            -2.0, 2.0, 0.01, 0.0, "float"
        )
        scroll_layout.addWidget(presence_penalty_group)

        # Repetition Penalty
        rep_penalty_group = self.create_parameter_group(
            "🔄 Repetition Penalty",
            "Penalizes repetitive text generation.",
            "repetition_penalty",
            0.1, 2.0, 0.01, 1.0, "float"
        )
        scroll_layout.addWidget(rep_penalty_group)

        # Min P
        min_p_group = self.create_parameter_group(
            "⬇️ Min P",
            "Sets a minimum probability threshold for token selection.",
            "min_p",
            0.0, 1.0, 0.001, 0.0, "float"
        )
        scroll_layout.addWidget(min_p_group)

        # Typical P
        typical_p_group = self.create_parameter_group(
            "📈 Typical P",
            "Alternative to top-p, focuses on typical tokens.",
            "typical_p",
            0.0, 1.0, 0.01, 1.0, "float"
        )
        scroll_layout.addWidget(typical_p_group)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return tab

    def create_provider_specific_tab(self):
        """Create provider-specific parameters tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Seed
        seed_group = self.create_parameter_group(
            "🌱 Seed",
            "Random seed for reproducible outputs. -1 for random.",
            "seed",
            -1, 2147483647, 1, -1, "int"
        )
        scroll_layout.addWidget(seed_group)

        # Stop Sequences
        stop_group = QGroupBox("🛑 Stop Sequences")
        stop_layout = QVBoxLayout(stop_group)

        stop_label = QLabel("Sequences where the model should stop generating:")
        stop_layout.addWidget(stop_label)

        # Add common stop sequences as checkboxes
        self.stop_sequences = {}
        common_stops = ["\\n\\n", "</s>", "<|endoftext|>", "Human:", "Assistant:", "User:"]

        for stop_seq in common_stops:
            checkbox = QCheckBox(f'"{stop_seq}"')
            self.stop_sequences[stop_seq] = checkbox
            stop_layout.addWidget(checkbox)

        scroll_layout.addWidget(stop_group)

        # Model-specific settings based on provider
        if "openai" in self.current_provider.lower():
            self.add_openai_settings(scroll_layout)
        elif "anthropic" in self.current_provider.lower():
            self.add_anthropic_settings(scroll_layout)
        elif "google" in self.current_provider.lower():
            self.add_google_settings(scroll_layout)
        elif "ollama" in self.current_provider.lower():
            self.add_ollama_settings(scroll_layout)

        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return tab

    def add_openai_settings(self, layout):
        """Add OpenAI-specific settings"""
        openai_group = QGroupBox("🤖 OpenAI Settings")
        openai_layout = QVBoxLayout(openai_group)

        # Stream
        self.stream_checkbox = QCheckBox("Enable Streaming")
        self.stream_checkbox.setChecked(True)
        self.stream_checkbox.setToolTip("Stream the response as it's generated")
        openai_layout.addWidget(self.stream_checkbox)

        # Logit Bias (simplified)
        self.logit_bias_checkbox = QCheckBox("Enable Custom Logit Bias")
        self.logit_bias_checkbox.setToolTip("Apply custom biases to specific tokens")
        openai_layout.addWidget(self.logit_bias_checkbox)

        layout.addWidget(openai_group)

    def add_anthropic_settings(self, layout):
        """Add Anthropic-specific settings"""
        anthropic_group = QGroupBox("🧠 Anthropic Settings")
        anthropic_layout = QVBoxLayout(anthropic_group)

        # System prompt handling
        self.system_prompt_checkbox = QCheckBox("Use System Messages")
        self.system_prompt_checkbox.setChecked(True)
        anthropic_layout.addWidget(self.system_prompt_checkbox)

        layout.addWidget(anthropic_group)

    def add_google_settings(self, layout):
        """Add Google-specific settings"""
        google_group = QGroupBox("🔍 Google Settings")
        google_layout = QVBoxLayout(google_group)

        # Safety settings
        self.safety_checkbox = QCheckBox("Enable Safety Filters")
        self.safety_checkbox.setChecked(True)
        google_layout.addWidget(self.safety_checkbox)

        layout.addWidget(google_group)

    def add_ollama_settings(self, layout):
        """Add Ollama-specific settings"""
        ollama_group = QGroupBox("🦙 Ollama Settings")
        ollama_layout = QVBoxLayout(ollama_group)

        # Context size
        context_group = self.create_parameter_group(
            "📋 Context Size",
            "Number of tokens to keep in context memory.",
            "num_ctx",
            512, 32768, 1, 2048, "int"
        )
        ollama_layout.addLayout(context_group.layout())

        # Prediction count
        predict_group = self.create_parameter_group(
            "🔮 Num Predict",
            "Maximum number of tokens to predict.",
            "num_predict",
            1, 4096, 1, -1, "int"
        )
        ollama_layout.addLayout(predict_group.layout())

        layout.addWidget(ollama_group)

    def create_parameter_group(self, title, description, param_name, min_val, max_val, step, default, param_type):
        """Create a parameter control group with slider and spinbox"""
        group = QGroupBox(title)
        layout = QGridLayout(group)

        # Description
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(desc_label, 0, 0, 1, 3)

        # Slider
        slider = QSlider(Qt.Orientation.Horizontal)

        # Spinbox (int or float)
        if param_type == "int":
            spinbox = QSpinBox()
            spinbox.setRange(int(min_val), int(max_val))
            spinbox.setValue(int(default))
            spinbox.setSingleStep(int(step))

            # Configure slider for int
            slider.setRange(int(min_val), int(max_val))
            slider.setValue(int(default))
            slider.setSingleStep(int(step))

            # Connect slider and spinbox
            slider.valueChanged.connect(spinbox.setValue)
            spinbox.valueChanged.connect(slider.setValue)

        else:  # float
            spinbox = QDoubleSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setValue(default)
            spinbox.setSingleStep(step)
            spinbox.setDecimals(3)

            # Configure slider for float (scale by 1000 for precision)
            scale = 1000
            slider.setRange(int(min_val * scale), int(max_val * scale))
            slider.setValue(int(default * scale))

            # Connect with scaling
            slider.valueChanged.connect(lambda v: spinbox.setValue(v / scale))
            spinbox.valueChanged.connect(lambda v: slider.setValue(int(v * scale)))

        # Current value label
        value_label = QLabel(f"Current: {default}")

        # Update value label when changed
        def update_label():
            value_label.setText(f"Current: {spinbox.value()}")

        spinbox.valueChanged.connect(update_label)

        # Layout the controls
        layout.addWidget(QLabel("Value:"), 1, 0)
        layout.addWidget(slider, 1, 1)
        layout.addWidget(spinbox, 1, 2)
        layout.addWidget(value_label, 2, 0, 1, 3)

        # Store references for later access
        setattr(self, f"{param_name}_slider", slider)
        setattr(self, f"{param_name}_spinbox", spinbox)

        return group

    def apply_theme_styles(self):
        """Apply theme-aware styling to the dialog"""
        self.setStyleSheet(get_dialog_theme_styles(self.dark_theme))

    def get_current_settings(self):
        """Get all current settings from the UI controls"""
        settings = {}

        # Core parameters
        if hasattr(self, 'temperature_spinbox'):
            settings['temperature'] = self.temperature_spinbox.value()
        if hasattr(self, 'max_tokens_spinbox'):
            settings['max_tokens'] = self.max_tokens_spinbox.value()
        if hasattr(self, 'top_p_spinbox'):
            settings['top_p'] = self.top_p_spinbox.value()
        if hasattr(self, 'top_k_spinbox'):
            settings['top_k'] = self.top_k_spinbox.value()

        # Advanced parameters
        if hasattr(self, 'frequency_penalty_spinbox'):
            settings['frequency_penalty'] = self.frequency_penalty_spinbox.value()
        if hasattr(self, 'presence_penalty_spinbox'):
            settings['presence_penalty'] = self.presence_penalty_spinbox.value()
        if hasattr(self, 'repetition_penalty_spinbox'):
            settings['repetition_penalty'] = self.repetition_penalty_spinbox.value()
        if hasattr(self, 'min_p_spinbox'):
            settings['min_p'] = self.min_p_spinbox.value()
        if hasattr(self, 'typical_p_spinbox'):
            settings['typical_p'] = self.typical_p_spinbox.value()

        # Provider-specific parameters
        if hasattr(self, 'seed_spinbox'):
            settings['seed'] = self.seed_spinbox.value()
        if hasattr(self, 'num_ctx_spinbox'):
            settings['num_ctx'] = self.num_ctx_spinbox.value()
        if hasattr(self, 'num_predict_spinbox'):
            settings['num_predict'] = self.num_predict_spinbox.value()

        # Stop sequences
        stop_sequences = []
        for seq, checkbox in self.stop_sequences.items():
            if checkbox.isChecked():
                stop_sequences.append(seq)
        if stop_sequences:
            settings['stop'] = stop_sequences

        # Provider-specific checkboxes
        if hasattr(self, 'stream_checkbox'):
            settings['stream'] = self.stream_checkbox.isChecked()
        if hasattr(self, 'system_prompt_checkbox'):
            settings['use_system_prompt'] = self.system_prompt_checkbox.isChecked()
        if hasattr(self, 'safety_checkbox'):
            settings['safety_enabled'] = self.safety_checkbox.isChecked()

        return settings

    def apply_current_settings(self):
        """Apply the current settings to the UI controls"""
        for param, value in self.current_settings.items():
            if hasattr(self, f"{param}_spinbox"):
                spinbox = getattr(self, f"{param}_spinbox")
                spinbox.setValue(value)

    def load_saved_settings(self):
        """Load saved settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)

                # Load settings for current model
                model_key = f"{self.current_provider}::{self.current_model}"
                if model_key in saved_settings:
                    self.current_settings.update(saved_settings[model_key])

            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self, settings):
        """Save settings to file"""
        saved_settings = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
            except Exception:
                pass

        # Save settings for current model
        model_key = f"{self.current_provider}::{self.current_model}"
        saved_settings[model_key] = settings

        try:
            with open(self.settings_file, 'w') as f:
                json.dump(saved_settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        defaults = {
            'temperature': 0.7,
            'max_tokens': 4096,
            'top_p': 1.0,
            'top_k': 50,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'repetition_penalty': 1.0,
            'min_p': 0.0,
            'typical_p': 1.0,
            'seed': -1,
            'num_ctx': 2048,
            'num_predict': -1
        }

        for param, value in defaults.items():
            if hasattr(self, f"{param}_spinbox"):
                spinbox = getattr(self, f"{param}_spinbox")
                spinbox.setValue(value)

        # Reset checkboxes
        for checkbox in self.stop_sequences.values():
            checkbox.setChecked(False)

    def apply_settings(self):
        """Apply the current settings and close dialog"""
        settings = self.get_current_settings()
        self.save_settings(settings)
        self.settings_applied.emit(settings)
        self.accept()
