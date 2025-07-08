"""
System Prompt Dialog for The Oracle
Allows users to set custom system prompts per conversation
"""

import sys
import os
from core.config import *

class SystemPromptDialog(QDialog):
    """Dialog for setting system prompts for conversations"""
    
    def __init__(self, current_prompt="", parent=None):
        super().__init__(parent)
        self.current_prompt = current_prompt
        self.setup_ui()
        self.setModal(True)
    
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Set System Prompt")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "icons", "oracle.png")))
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Title and description
        title_label = QLabel("System Prompt for This Conversation")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D3748; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        description = QLabel(
            "Set a custom system prompt that will be applied to all messages in this conversation. "
            "This allows you to define the AI's personality, role, or behavior for this specific chat."
        )
        description.setStyleSheet("color: #4A5568; margin-bottom: 15px;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Preset prompts section
        presets_group = QGroupBox("Quick Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        # Create preset buttons
        self.preset_buttons = []
        presets = [
            ("Default Assistant", "You are a helpful, harmless, and honest AI assistant."),
            ("Code Expert", "You are an expert software developer. Provide clean, well-documented code with explanations. Focus on best practices and efficient solutions."),
            ("Creative Writer", "You are a creative writing assistant. Help with storytelling, character development, and engaging narrative techniques."),
            ("Teacher/Tutor", "You are a patient and encouraging teacher. Explain concepts clearly, provide examples, and adapt your teaching style to the student's level."),
            ("Business Analyst", "You are a business analyst. Focus on data-driven insights, strategic recommendations, and clear communication of complex business concepts."),
            ("Research Assistant", "You are a research assistant. Provide accurate, well-sourced information and help organize research findings clearly and systematically."),
            ("Clear (No System Prompt)", "")
        ]
        
        for name, prompt in presets:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, p=prompt: self.load_preset(p))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #EDF2F7;
                    border: 1px solid #CBD5E0;
                    border-radius: 6px;
                    padding: 8px 12px;
                    text-align: left;
                    color: #2D3748;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    border-color: #A0AEC0;
                }
                QPushButton:pressed {
                    background-color: #CBD5E0;
                }
            """)
            presets_layout.addWidget(btn)
            self.preset_buttons.append(btn)
        
        layout.addWidget(presets_group)
        
        # Text editor for custom prompt
        prompt_label = QLabel("Custom System Prompt:")
        prompt_label.setStyleSheet("font-weight: bold; color: #2D3748; margin-top: 15px;")
        layout.addWidget(prompt_label)
        
        self.prompt_editor = QTextEdit()
        self.prompt_editor.setPlainText(self.current_prompt)
        self.prompt_editor.setPlaceholderText(
            "Enter your custom system prompt here...\n\n"
            "Examples:\n"
            "• You are a helpful coding assistant specializing in Python.\n"
            "• Act as a creative writing partner who helps brainstorm ideas.\n"
            "• You are an expert in data science and machine learning.\n"
            "• Respond in the style of a Shakespearean character."
        )
        self.prompt_editor.setStyleSheet("""
            QTextEdit {
                background-color: #F7FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #2D3748;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #4299E1;
                background-color: #F0F4F8;
            }
        """)
        layout.addWidget(self.prompt_editor)
        
        # Character count
        self.char_count_label = QLabel("0 characters")
        self.char_count_label.setStyleSheet("color: #718096; font-size: 11px;")
        self.prompt_editor.textChanged.connect(self.update_char_count)
        layout.addWidget(self.char_count_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Preview button
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self.preview_prompt)
        preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A5568;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2D3748;
            }
        """)
        button_layout.addWidget(preview_btn)
        
        button_layout.addStretch()
        
        # Cancel and OK buttons
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0;
                color: #4A5568;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #CBD5E0;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Set Prompt")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4299E1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3182CE;
            }
        """)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # Update character count initially
        self.update_char_count()
    
    def load_preset(self, prompt):
        """Load a preset prompt"""
        self.prompt_editor.setPlainText(prompt)
        self.update_char_count()
    
    def update_char_count(self):
        """Update the character count display"""
        text = self.prompt_editor.toPlainText()
        char_count = len(text)
        self.char_count_label.setText(f"{char_count} characters")
        
        # Color coding for length
        if char_count > 2000:
            self.char_count_label.setStyleSheet("color: #E53E3E; font-size: 11px; font-weight: bold;")
        elif char_count > 1000:
            self.char_count_label.setStyleSheet("color: #DD6B20; font-size: 11px;")
        else:
            self.char_count_label.setStyleSheet("color: #718096; font-size: 11px;")
    
    def preview_prompt(self):
        """Show a preview of how the prompt will appear"""
        prompt = self.prompt_editor.toPlainText().strip()
        
        if not prompt:
            preview_text = "No system prompt set. The AI will use default behavior."
        else:
            preview_text = f"System Prompt Preview:\n\n{prompt}\n\n---\n\nThis prompt will be applied to all messages in the current conversation."
        
        QMessageBox.information(self, "System Prompt Preview", preview_text)
    
    def get_system_prompt(self):
        """Get the entered system prompt"""
        return self.prompt_editor.toPlainText().strip()
