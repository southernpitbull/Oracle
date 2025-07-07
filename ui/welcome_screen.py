"""
Welcome screen widget for new conversations
"""

from core.config import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                        QPushButton, Qt)


class WelcomeScreen(QWidget):
    """Welcome screen widget for new conversations"""
    
    def __init__(self, current_provider=None, current_model=None, parent=None):
        super().__init__(parent)
        self.current_provider = current_provider
        self.current_model = current_model
        self.parent_app = parent
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the welcome screen UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Welcome to The Oracle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #1F6FEB;
                margin: 20px 0;
            }
        """)
        layout.addWidget(title_label)
        
        # Current model info
        model_info = QLabel()
        model_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        model_info.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #8B949E;
                margin: 10px 0;
            }
        """)
        layout.addWidget(model_info)
        
        # Update model info display
        provider_text = self.current_provider or "No provider"
        model_text = self.current_model or "No model"
        model_info.setText(f"Current Model: {provider_text} - {model_text}")
        
        # Quick start buttons
        quick_start_label = QLabel("Quick Start")
        quick_start_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        quick_start_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #F0F6FC;
                margin: 30px 0 15px 0;
            }
        """)
        layout.addWidget(quick_start_label)
        
        # Quick action buttons
        quick_actions = [
            ("💻 Explain Code", "Please explain this code snippet and what it does:"),
            ("✉️ Write an Email", "Help me write a professional email about:"),
            ("📝 Create Documentation", "Create documentation for this code/project:"),
            ("🐛 Debug Issue", "Help me debug this error or issue:"),
            ("🔍 Code Review", "Please review this code and suggest improvements:"),
            ("📊 Data Analysis", "Help me analyze this data and find insights:")
        ]
        
        buttons_layout = QGridLayout()
        for i, (text, prompt) in enumerate(quick_actions):
            btn = QPushButton(text)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    padding: 10px 20px;
                    text-align: left;
                    background-color: #30363D;
                    border: 1px solid #373E47;
                    border-radius: 8px;
                    color: #F0F6FC;
                }
                QPushButton:hover {
                    background-color: #21262D;
                    border: 1px solid #1F6FEB;
                }
            """)
            btn.clicked.connect(lambda checked, p=prompt: self.quick_start_action(p))
            buttons_layout.addWidget(btn, i // 2, i % 2)
        
        layout.addLayout(buttons_layout)
        
        # Example prompts
        examples_label = QLabel("Example Prompts")
        examples_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        examples_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #F0F6FC;
                margin: 30px 0 15px 0;
            }
        """)
        layout.addWidget(examples_label)
        
        example_prompts = [
            "What are the best practices for Python error handling?",
            "How do I optimize database queries for better performance?",
            "Explain the difference between REST and GraphQL APIs",
            "Write a function to parse JSON data from an API",
            "How do I implement authentication in a web application?"
        ]
        
        for prompt in example_prompts:
            example_btn = QPushButton(f"💡 {prompt}")
            example_btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    padding: 8px 15px;
                    text-align: left;
                    background-color: transparent;
                    border: 1px solid #373E47;
                    border-radius: 6px;
                    color: #8B949E;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #21262D;
                    color: #F0F6FC;
                    border: 1px solid #1F6FEB;
                }
            """)
            example_btn.clicked.connect(lambda checked, p=prompt: self.use_example_prompt(p))
            layout.addWidget(example_btn)
        
        layout.addStretch()
    
    def quick_start_action(self, prompt_template):
        """Handle quick start button clicks"""
        if self.parent_app and hasattr(self.parent_app, 'input_entry'):
            self.parent_app.input_entry.setPlainText(prompt_template)
            self.parent_app.input_entry.setFocus()
            # Hide welcome screen and show chat
            if hasattr(self.parent_app, 'toggle_welcome_screen'):
                self.parent_app.toggle_welcome_screen(False)
    
    def use_example_prompt(self, prompt):
        """Use an example prompt"""
        if self.parent_app and hasattr(self.parent_app, 'input_entry'):
            self.parent_app.input_entry.setPlainText(prompt)
            self.parent_app.input_entry.setFocus()
            # Hide welcome screen and show chat
            if hasattr(self.parent_app, 'toggle_welcome_screen'):
                self.parent_app.toggle_welcome_screen(False)
