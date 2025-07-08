"""
Prompt Template Dialog for The Oracle AI Chat Application.

This dialog allows users to create and use prompt templates with variables,
filling in placeholders like {{audience}} and {{text_to_summarize}}.
"""

import re
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QScrollArea,
    QWidget, QFrame, QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class PromptTemplateDialog(QDialog):
    """Dialog for filling in prompt template variables."""
    
    template_filled = pyqtSignal(str)  # Emitted when template is filled and ready to use
    
    def __init__(self, template_content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fill Template Variables")
        self.setModal(True)
        self.resize(600, 500)
        
        self.template_content = template_content
        self.variables = self.extract_variables(template_content)
        self.variable_inputs = {}
        
        # UI setup
        self.setup_ui()
        self.setup_connections()
        
        # Apply styling
        self.setup_styles()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Fill in the template variables:")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Template preview
        preview_group = QFrame()
        preview_group.setFrameStyle(QFrame.Shape.Box)
        preview_layout = QVBoxLayout(preview_group)
        
        preview_label = QLabel("Template Preview:")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        preview_layout.addWidget(preview_label)
        
        self.template_preview = QTextEdit()
        self.template_preview.setPlainText(self.template_content)
        self.template_preview.setReadOnly(True)
        self.template_preview.setMaximumHeight(120)
        self.template_preview.setFont(QFont("Consolas", 9))
        preview_layout.addWidget(self.template_preview)
        
        layout.addWidget(preview_group)
        
        # Variables section
        if self.variables:
            variables_label = QLabel(f"Variables found: {len(self.variables)}")
            variables_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            layout.addWidget(variables_label)
            
            # Scroll area for variables
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QFormLayout(scroll_widget)
            
            for variable in self.variables:
                var_label = QLabel(f"{variable}:")
                var_label.setFont(QFont("Arial", 10))
                
                # Create appropriate input widget based on variable name
                if any(keyword in variable.lower() for keyword in ['text', 'content', 'description', 'prompt']):
                    var_input = QTextEdit()
                    var_input.setMaximumHeight(80)
                    var_input.setPlaceholderText(f"Enter {variable.replace('_', ' ').lower()}...")
                else:
                    var_input = QLineEdit()
                    var_input.setPlaceholderText(f"Enter {variable.replace('_', ' ').lower()}...")
                
                self.variable_inputs[variable] = var_input
                scroll_layout.addRow(var_label, var_input)
                
                # Connect text changes to preview update
                if isinstance(var_input, QTextEdit):
                    var_input.textChanged.connect(self.update_preview)
                else:
                    var_input.textChanged.connect(self.update_preview)
            
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setMaximumHeight(250)
            layout.addWidget(scroll_area)
        else:
            no_vars_label = QLabel("No template variables found in this prompt.")
            no_vars_label.setStyleSheet("color: #888888; font-style: italic;")
            layout.addWidget(no_vars_label)
        
        # Result preview
        result_group = QFrame()
        result_group.setFrameStyle(QFrame.Shape.Box)
        result_layout = QVBoxLayout(result_group)
        
        result_label = QLabel("Result Preview:")
        result_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        result_layout.addWidget(result_label)
        
        self.result_preview = QTextEdit()
        self.result_preview.setReadOnly(True)
        self.result_preview.setMaximumHeight(150)
        self.result_preview.setFont(QFont("Consolas", 9))
        result_layout.addWidget(self.result_preview)
        
        layout.addWidget(result_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        
        # Add additional buttons
        self.clear_btn = QPushButton("Clear All")
        self.fill_sample_btn = QPushButton("Fill Sample Data")
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.fill_sample_btn)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        
        # Store references
        self.button_box = button_box
        
        # Initial preview update
        self.update_preview()
    
    def setup_connections(self):
        """Set up signal connections."""
        self.button_box.accepted.connect(self.accept_template)
        self.button_box.rejected.connect(self.reject)
        
        self.clear_btn.clicked.connect(self.clear_all_inputs)
        self.fill_sample_btn.clicked.connect(self.fill_sample_data)
    
    def setup_styles(self):
        """Apply styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QFrame {
                border: 1px solid #555555;
                border-radius: 5px;
                margin: 5px;
                padding: 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QTextEdit, QLineEdit {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QTextEdit:focus, QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 3px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QScrollArea {
                border: 1px solid #555555;
                border-radius: 3px;
            }
        """)
    
    def extract_variables(self, template: str) -> List[str]:
        """Extract variables from template using {{variable}} syntax."""
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, template)
        # Remove duplicates while preserving order
        variables = []
        for var in matches:
            var = var.strip()
            if var not in variables:
                variables.append(var)
        return variables
    
    def get_variable_value(self, variable: str) -> str:
        """Get the current value for a variable."""
        if variable not in self.variable_inputs:
            return ""
        
        input_widget = self.variable_inputs[variable]
        if isinstance(input_widget, QTextEdit):
            return input_widget.toPlainText()
        else:
            return input_widget.text()
    
    def update_preview(self):
        """Update the result preview with current variable values."""
        result = self.template_content
        
        for variable in self.variables:
            value = self.get_variable_value(variable)
            placeholder = f"{{{{{variable}}}}}"
            
            if value:
                result = result.replace(placeholder, value)
            else:
                # Show placeholder in different style if empty
                result = result.replace(placeholder, f"[{variable}]")
        
        self.result_preview.setPlainText(result)
    
    def clear_all_inputs(self):
        """Clear all variable inputs."""
        for input_widget in self.variable_inputs.values():
            if isinstance(input_widget, QTextEdit):
                input_widget.clear()
            else:
                input_widget.clear()
        self.update_preview()
    
    def fill_sample_data(self):
        """Fill inputs with sample data for testing."""
        sample_data = {
            'audience': 'technical team',
            'topic': 'machine learning',
            'text': 'This is sample text for summarization.',
            'text_to_summarize': 'This is sample text that needs to be summarized for demonstration purposes.',
            'recipient': 'John Smith',
            'subject': 'Project Update',
            'purpose': 'provide status update',
            'key_points': '• Progress on milestone 1\n• Upcoming deadlines\n• Resource requirements',
            'code': 'def hello():\n    print("Hello, World!")',
            'problem_description': 'Function returns incorrect results',
            'language': 'Python',
            'context': 'web development project',
            'requirements': 'responsive design, fast loading',
            'sections': 'overview, implementation, examples'
        }
        
        for variable, input_widget in self.variable_inputs.items():
            # Find best matching sample data
            sample_value = None
            var_lower = variable.lower()
            
            # Direct match
            if var_lower in sample_data:
                sample_value = sample_data[var_lower]
            else:
                # Fuzzy matching
                for key, value in sample_data.items():
                    if key in var_lower or var_lower in key:
                        sample_value = value
                        break
                
                # Fallback to generic sample
                if sample_value is None:
                    sample_value = f"Sample {variable.replace('_', ' ').lower()}"
            
            if isinstance(input_widget, QTextEdit):
                input_widget.setPlainText(sample_value)
            else:
                input_widget.setText(sample_value)
        
        self.update_preview()
    
    def validate_inputs(self) -> Tuple[bool, str]:
        """Validate that all required inputs are filled."""
        empty_variables = []
        
        for variable in self.variables:
            value = self.get_variable_value(variable).strip()
            if not value:
                empty_variables.append(variable)
        
        if empty_variables:
            return False, f"Please fill in the following variables: {', '.join(empty_variables)}"
        
        return True, ""
    
    def accept_template(self):
        """Accept the template with filled variables."""
        # Validate inputs
        is_valid, error_message = self.validate_inputs()
        if not is_valid:
            QMessageBox.warning(self, "Missing Variables", error_message)
            return
        
        # Generate final result
        result = self.template_content
        for variable in self.variables:
            value = self.get_variable_value(variable)
            placeholder = f"{{{{{variable}}}}}"
            result = result.replace(placeholder, value)
        
        # Emit the filled template
        self.template_filled.emit(result)
        self.accept()
    
    def get_filled_template(self) -> str:
        """Get the template with all variables filled in."""
        result = self.template_content
        for variable in self.variables:
            value = self.get_variable_value(variable)
            placeholder = f"{{{{{variable}}}}}"
            result = result.replace(placeholder, value)
        return result


def test_template_dialog():
    """Test function for the template dialog."""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Test template with various variable types
    test_template = """Please help me write a professional email with the following details:

Recipient: {{recipient}}
Subject: {{subject}}
Purpose: {{purpose}}
Key points to include: {{key_points}}

Please make it {{tone}} and appropriate for {{audience}}.

Additional context: {{context}}"""
    
    dialog = PromptTemplateDialog(test_template)
    
    def on_template_filled(filled_template):
        print("Template filled:")
        print("=" * 50)
        print(filled_template)
        print("=" * 50)
    
    dialog.template_filled.connect(on_template_filled)
    dialog.exec()
    
    app.quit()


if __name__ == "__main__":
    test_template_dialog()
