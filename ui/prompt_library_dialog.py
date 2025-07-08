"""
Prompt Library Dialog for The Oracle AI Chat Application.

This dialog allows users to manage a library of favorite or effective prompts,
organized by category, that can be inserted into the chat with one click.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QLineEdit, QComboBox, QPushButton, QLabel, QSplitter,
    QMessageBox, QInputDialog, QGroupBox, QFormLayout, QDialogButtonBox,
    QMenu, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon
from .theme_styles import get_dialog_theme_styles, get_icon_path, create_themed_message_box


class PromptLibraryDialog(QDialog):
    """Dialog for managing prompt library with categories and search functionality."""

    prompt_selected = pyqtSignal(str)  # Emitted when a prompt is selected for insertion

    def __init__(self, parent=None, dark_theme=True):
        super().__init__(parent)
        self.dark_theme = dark_theme
        self.setWindowTitle("Prompt Library")
        self.setModal(False)
        self.resize(800, 600)

        # Set window icon
        icon_path = get_icon_path("chat", "chat")
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        # Data storage
        self.prompts_file = Path("prompts_library.json")
        self.prompts_data = self.load_prompts()

        # UI setup
        self.setup_ui()
        self.setup_connections()
        self.load_prompts_to_tree()

        # Apply styling
        self.apply_theme_styles()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Search and filter section
        search_layout = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search prompts...")
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_edit)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        search_layout.addWidget(QLabel("Category:"))
        search_layout.addWidget(self.category_filter)

        layout.addLayout(search_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - prompt tree
        left_widget = QGroupBox("Prompt Library")
        left_layout = QVBoxLayout(left_widget)

        # Tree widget for prompts
        self.prompt_tree = QTreeWidget()
        self.prompt_tree.setHeaderLabels(["Name", "Category", "Description"])
        header = self.prompt_tree.header()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.prompt_tree.setAlternatingRowColors(True)
        self.prompt_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        left_layout.addWidget(self.prompt_tree)

        # Tree buttons
        tree_buttons = QHBoxLayout()
        self.add_prompt_btn = QPushButton("Add Prompt")
        self.add_category_btn = QPushButton("Add Category")
        self.delete_btn = QPushButton("Delete")
        self.use_prompt_btn = QPushButton("Use Prompt")

        tree_buttons.addWidget(self.add_prompt_btn)
        tree_buttons.addWidget(self.add_category_btn)
        tree_buttons.addWidget(self.delete_btn)
        tree_buttons.addStretch()
        tree_buttons.addWidget(self.use_prompt_btn)

        left_layout.addLayout(tree_buttons)
        splitter.addWidget(left_widget)

        # Right side - prompt editor
        right_widget = QGroupBox("Prompt Details")
        right_layout = QFormLayout(right_widget)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Prompt name")
        right_layout.addRow("Name:", self.name_edit)

        self.category_edit = QComboBox()
        self.category_edit.setEditable(True)
        self.category_edit.setPlaceholderText("Category name")
        right_layout.addRow("Category:", self.category_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Brief description")
        right_layout.addRow("Description:", self.description_edit)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Enter your prompt here...")
        self.content_edit.setFont(QFont("Consolas", 10))
        right_layout.addRow("Content:", self.content_edit)

        # Editor buttons
        editor_buttons = QHBoxLayout()
        self.save_btn = QPushButton("Save Changes")
        self.revert_btn = QPushButton("Revert")
        self.preview_btn = QPushButton("Preview")

        editor_buttons.addWidget(self.save_btn)
        editor_buttons.addWidget(self.revert_btn)
        editor_buttons.addStretch()
        editor_buttons.addWidget(self.preview_btn)

        right_layout.addRow(editor_buttons)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        layout.addWidget(button_box)

        # Store references
        self.button_box = button_box
        self.splitter = splitter

        # Initially disable editor
        self.set_editor_enabled(False)

    def setup_connections(self):
        """Set up signal connections."""
        # Search and filter
        self.search_edit.textChanged.connect(self.filter_prompts)
        self.category_filter.currentTextChanged.connect(self.filter_prompts)

        # Tree interactions
        self.prompt_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.prompt_tree.itemDoubleClicked.connect(self.use_selected_prompt)
        self.prompt_tree.customContextMenuRequested.connect(self.show_context_menu)

        # Buttons
        self.add_prompt_btn.clicked.connect(self.add_new_prompt)
        self.add_category_btn.clicked.connect(self.add_new_category)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.use_prompt_btn.clicked.connect(self.use_selected_prompt)

        self.save_btn.clicked.connect(self.save_current_prompt)
        self.revert_btn.clicked.connect(self.revert_changes)
        self.preview_btn.clicked.connect(self.preview_prompt)

        # Dialog
        self.button_box.rejected.connect(self.close)

    def apply_theme_styles(self):
        """Apply theme-aware styling to the dialog"""
        dialog_styles = get_dialog_theme_styles(self.dark_theme)

        # Apply dialog-wide styles
        self.setStyleSheet(dialog_styles + """
            QTreeWidget {
                border-radius: 5px;
                alternate-background-color: transparent;
                padding: 5px;
            }

            QTreeWidget::item {
                padding: 8px;
                border-radius: 3px;
                margin: 1px;
            }

            QTreeWidget::item:selected {
                font-weight: bold;
            }

            QLineEdit, QComboBox, QTextEdit {
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }

            QPushButton {
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }

            QPushButton:disabled {
                opacity: 0.5;
            }

            QLabel {
                font-size: 12px;
            }

            QSplitter::handle {
                border-radius: 2px;
            }
        """)

    def load_prompts(self) -> Dict:
        """Load prompts from JSON file."""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading prompts: {e}")

        # Return default structure with some sample prompts
        return {
            "categories": {
                "General": {
                    "Explain Code": {
                        "description": "Ask AI to explain code functionality",
                        "content": "Please explain how this code works, including its purpose, key components, and any important details:\n\n{{code}}"
                    },
                    "Summarize Text": {
                        "description": "Summarize long text content with audience consideration",
                        "content": "Please provide a clear and concise summary of the following text for {{audience}}:\n\n{{text_to_summarize}}"
                    },
                    "Custom Analysis": {
                        "description": "Analyze content with specific focus",
                        "content": "Please analyze the following {{content_type}} focusing on {{analysis_focus}}:\n\n{{content}}\n\nPlease provide insights on {{specific_aspects}}."
                    }
                },
                "Development": {
                    "Code Review": {
                        "description": "Request a thorough code review",
                        "content": "Please review this {{language}} code for:\n- Logic errors\n- Performance issues\n- Security vulnerabilities\n- Best practices\n- Code style\n\nContext: {{context}}\n\nCode:\n{{code}}"
                    },
                    "Bug Analysis": {
                        "description": "Analyze and debug code issues",
                        "content": "I'm experiencing a bug in this {{language}} code. Please help me identify the issue and suggest a fix:\n\nProblem: {{problem_description}}\n\nExpected behavior: {{expected_behavior}}\n\nActual behavior: {{actual_behavior}}\n\nCode:\n{{code}}"
                    },
                    "Optimize Code": {
                        "description": "Request code optimization suggestions",
                        "content": "Please analyze this {{language}} code and suggest optimizations for {{optimization_focus}}:\n\nCurrent requirements: {{requirements}}\n\nCode:\n{{code}}"
                    },
                    "Generate Documentation": {
                        "description": "Create documentation for code",
                        "content": "Please generate comprehensive documentation for this {{language}} code:\n\nTarget audience: {{audience}}\nDocumentation type: {{doc_type}}\n\nCode:\n{{code}}\n\nPlease include:\n- Purpose and overview\n- Parameters and return values\n- Usage examples\n- Any important notes"
                    }
                },
                "Writing": {
                    "Professional Email": {
                        "description": "Draft a professional email with template variables",
                        "content": "Please help me write a professional email with the following details:\n\nRecipient: {{recipient}}\nSubject: {{subject}}\nPurpose: {{purpose}}\nTone: {{tone}}\nKey points to include:\n{{key_points}}\n\nAdditional context: {{context}}"
                    },
                    "Technical Documentation": {
                        "description": "Create technical documentation with variables",
                        "content": "Please help me create clear technical documentation for:\n\nTopic: {{topic}}\nAudience: {{audience}}\nDocument type: {{doc_type}}\n\nKey sections needed:\n{{sections}}\n\nTechnical requirements:\n{{requirements}}\n\nPlease ensure the documentation is {{writing_style}} and includes practical examples."
                    },
                    "Content Review": {
                        "description": "Review and improve written content",
                        "content": "Please review and improve the following {{content_type}} for {{target_audience}}:\n\nFocus areas:\n- {{review_focus}}\n- Clarity and readability\n- Grammar and style\n- Structure and flow\n\nContent:\n{{content}}\n\nPlease provide both feedback and a revised version."
                    }
                },
                "Templates": {
                    "Meeting Summary": {
                        "description": "Generate meeting summary template",
                        "content": "Please create a meeting summary for:\n\nMeeting: {{meeting_title}}\nDate: {{date}}\nAttendees: {{attendees}}\n\nKey discussion points:\n{{discussion_points}}\n\nDecisions made:\n{{decisions}}\n\nAction items:\n{{action_items}}\n\nNext meeting: {{next_meeting}}"
                    },
                    "Project Proposal": {
                        "description": "Draft a project proposal",
                        "content": "Please help me draft a project proposal for:\n\nProject: {{project_name}}\nClient/Stakeholder: {{client}}\nTimeline: {{timeline}}\nBudget range: {{budget}}\n\nObjectives:\n{{objectives}}\n\nScope:\n{{scope}}\n\nDeliverables:\n{{deliverables}}\n\nRisks and mitigation:\n{{risks}}\n\nPlease make it {{proposal_tone}} and professional."
                    }
                }
            }
        }

    def save_prompts(self):
        """Save prompts to JSON file."""
        try:
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            create_themed_message_box(
                self, "Save Error",
                f"Failed to save prompts: {e}",
                "error", self.dark_theme
            ).exec()

    def load_prompts_to_tree(self):
        """Load prompts into the tree widget."""
        self.prompt_tree.clear()
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        self.category_edit.clear()

        categories = self.prompts_data.get("categories", {})

        for category_name, prompts in categories.items():
            self.category_filter.addItem(category_name)
            self.category_edit.addItem(category_name)

            category_item = QTreeWidgetItem([category_name, "", ""])
            category_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "category", "name": category_name})
            self.prompt_tree.addTopLevelItem(category_item)

            for prompt_name, prompt_data in prompts.items():
                prompt_item = QTreeWidgetItem([
                    prompt_name,
                    category_name,
                    prompt_data.get("description", "")
                ])
                prompt_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "prompt",
                    "category": category_name,
                    "name": prompt_name,
                    "data": prompt_data
                })
                category_item.addChild(prompt_item)

        self.prompt_tree.expandAll()

    def filter_prompts(self):
        """Filter prompts based on search text and category."""
        search_text = self.search_edit.text().lower()
        selected_category = self.category_filter.currentText()

        def should_show_item(item):
            user_data = item.data(0, Qt.ItemDataRole.UserRole)
            if not user_data:
                return False

            if user_data["type"] == "category":
                category_name = user_data["name"]
                if selected_category != "All Categories" and category_name != selected_category:
                    return False

                # Show category if any child matches
                for i in range(item.childCount()):
                    if should_show_item(item.child(i)):
                        return True
                return False

            elif user_data["type"] == "prompt":
                category_name = user_data["category"]
                prompt_name = user_data["name"]
                description = user_data["data"].get("description", "")

                # Category filter
                if selected_category != "All Categories" and category_name != selected_category:
                    return False

                # Search filter
                if search_text:
                    searchable_text = f"{prompt_name} {description}".lower()
                    if search_text not in searchable_text:
                        return False

                return True

            return False

        # Hide/show items based on filter
        for i in range(self.prompt_tree.topLevelItemCount()):
            category_item = self.prompt_tree.topLevelItem(i)
            if not category_item:
                continue

            category_visible = False

            for j in range(category_item.childCount()):
                prompt_item = category_item.child(j)
                if not prompt_item:
                    continue

                prompt_visible = should_show_item(prompt_item)
                prompt_item.setHidden(not prompt_visible)
                if prompt_visible:
                    category_visible = True

            category_item.setHidden(not category_visible)

    def on_selection_changed(self):
        """Handle tree selection changes."""
        current_item = self.prompt_tree.currentItem()
        if not current_item:
            self.set_editor_enabled(False)
            return

        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data or user_data["type"] != "prompt":
            self.set_editor_enabled(False)
            return

        # Load prompt data into editor
        prompt_data = user_data["data"]
        self.name_edit.setText(user_data["name"])
        self.category_edit.setCurrentText(user_data["category"])
        self.description_edit.setText(prompt_data.get("description", ""))
        self.content_edit.setPlainText(prompt_data.get("content", ""))

        self.set_editor_enabled(True)
        self.use_prompt_btn.setEnabled(True)

    def set_editor_enabled(self, enabled):
        """Enable or disable the editor section."""
        self.name_edit.setEnabled(enabled)
        self.category_edit.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.content_edit.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.revert_btn.setEnabled(enabled)
        self.preview_btn.setEnabled(enabled)

        if not enabled:
            self.name_edit.clear()
            self.category_edit.setCurrentText("")
            self.description_edit.clear()
            self.content_edit.clear()
            self.use_prompt_btn.setEnabled(False)

    def add_new_prompt(self):
        """Add a new prompt to the library."""
        # Get category (create new if needed)
        category, ok = QInputDialog.getItem(
            self, "Select Category", "Choose a category for the new prompt:",
            list(self.prompts_data.get("categories", {}).keys()) + ["Create New..."],
            0, True
        )

        if not ok:
            return

        if category == "Create New...":
            category, ok = QInputDialog.getText(
                self, "New Category", "Enter new category name:"
            )
            if not ok or not category.strip():
                return
            category = category.strip()

        # Get prompt name
        name, ok = QInputDialog.getText(
            self, "New Prompt", "Enter prompt name:"
        )
        if not ok or not name.strip():
            return
        name = name.strip()

        # Ensure category exists
        if "categories" not in self.prompts_data:
            self.prompts_data["categories"] = {}
        if category not in self.prompts_data["categories"]:
            self.prompts_data["categories"][category] = {}

        # Add new prompt
        self.prompts_data["categories"][category][name] = {
            "description": "New prompt",
            "content": "Enter your prompt here..."
        }

        self.save_prompts()
        self.load_prompts_to_tree()

        # Select the new prompt
        self.select_prompt(category, name)

    def add_new_category(self):
        """Add a new category."""
        name, ok = QInputDialog.getText(
            self, "New Category", "Enter category name:"
        )
        if not ok or not name.strip():
            return

        name = name.strip()
        if "categories" not in self.prompts_data:
            self.prompts_data["categories"] = {}

        if name not in self.prompts_data["categories"]:
            self.prompts_data["categories"][name] = {}
            self.save_prompts()
            self.load_prompts_to_tree()
        else:
            create_themed_message_box(
                self, "Category Exists",
                f"Category '{name}' already exists.",
                "info", self.dark_theme
            ).exec()

    def delete_selected(self):
        """Delete the selected prompt or category."""
        current_item = self.prompt_tree.currentItem()
        if not current_item:
            return

        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data:
            return

        if user_data["type"] == "prompt":
            category = user_data["category"]
            name = user_data["name"]

            reply = QMessageBox.question(
                self, "Delete Prompt",
                f"Are you sure you want to delete the prompt '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                del self.prompts_data["categories"][category][name]
                self.save_prompts()
                self.load_prompts_to_tree()

        elif user_data["type"] == "category":
            category = user_data["name"]
            prompts_count = len(self.prompts_data["categories"].get(category, {}))

            reply = QMessageBox.question(
                self, "Delete Category",
                f"Are you sure you want to delete the category '{category}' and all {prompts_count} prompts in it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                del self.prompts_data["categories"][category]
                self.save_prompts()
                self.load_prompts_to_tree()

    def save_current_prompt(self):
        """Save changes to the current prompt."""
        current_item = self.prompt_tree.currentItem()
        if not current_item:
            return

        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data or user_data["type"] != "prompt":
            return

        old_category = user_data["category"]
        old_name = user_data["name"]

        new_name = self.name_edit.text().strip()
        new_category = self.category_edit.currentText().strip()
        new_description = self.description_edit.text().strip()
        new_content = self.content_edit.toPlainText()

        if not new_name or not new_category:
            create_themed_message_box(
                self, "Invalid Data",
                "Name and category are required.",
                "warning", self.dark_theme
            ).exec()
            return

        # Remove old entry
        del self.prompts_data["categories"][old_category][old_name]

        # Ensure new category exists
        if new_category not in self.prompts_data["categories"]:
            self.prompts_data["categories"][new_category] = {}

        # Add updated entry
        self.prompts_data["categories"][new_category][new_name] = {
            "description": new_description,
            "content": new_content
        }

        self.save_prompts()
        self.load_prompts_to_tree()
        self.select_prompt(new_category, new_name)

        create_themed_message_box(
            self, "Saved",
            "Prompt saved successfully.",
            "success", self.dark_theme
        ).exec()

    def revert_changes(self):
        """Revert editor to original values."""
        self.on_selection_changed()

    def preview_prompt(self):
        """Show a preview of the prompt."""
        content = self.content_edit.toPlainText()
        if not content:
            return

        # Simple preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Prompt Preview")
        preview_dialog.resize(500, 400)

        layout = QVBoxLayout(preview_dialog)
        preview_text = QTextEdit()
        preview_text.setPlainText(content)
        preview_text.setReadOnly(True)
        layout.addWidget(QLabel("Prompt Content:"))
        layout.addWidget(preview_text)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(preview_dialog.accept)
        layout.addWidget(buttons)

        preview_dialog.exec()

    def use_selected_prompt(self):
        """Use the selected prompt by emitting it."""
        current_item = self.prompt_tree.currentItem()
        if not current_item:
            return

        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data or user_data["type"] != "prompt":
            return

        content = user_data["data"].get("content", "")
        if not content:
            return

        # Simply emit the prompt directly
        self.prompt_selected.emit(content)
        self.close()

    def select_prompt(self, category: str, name: str):
        """Select a specific prompt in the tree."""
        for i in range(self.prompt_tree.topLevelItemCount()):
            category_item = self.prompt_tree.topLevelItem(i)
            if not category_item:
                continue

            category_data = category_item.data(0, Qt.ItemDataRole.UserRole)

            if category_data and category_data.get("name") == category:
                for j in range(category_item.childCount()):
                    prompt_item = category_item.child(j)
                    if not prompt_item:
                        continue

                    prompt_data = prompt_item.data(0, Qt.ItemDataRole.UserRole)

                    if prompt_data and prompt_data.get("name") == name:
                        self.prompt_tree.setCurrentItem(prompt_item)
                        return

    def show_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.prompt_tree.itemAt(position)
        if not item:
            return

        user_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data:
            return

        menu = QMenu(self)

        if user_data["type"] == "prompt":
            use_action = QAction("Use Prompt", self)
            use_action.triggered.connect(self.use_selected_prompt)
            menu.addAction(use_action)

            menu.addSeparator()

            duplicate_action = QAction("Duplicate", self)
            duplicate_action.triggered.connect(self.duplicate_prompt)
            menu.addAction(duplicate_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_selected)
        menu.addAction(delete_action)

        menu.exec(self.prompt_tree.mapToGlobal(position))

    def duplicate_prompt(self):
        """Duplicate the selected prompt."""
        current_item = self.prompt_tree.currentItem()
        if not current_item:
            return

        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data or user_data["type"] != "prompt":
            return

        category = user_data["category"]
        original_name = user_data["name"]
        prompt_data = user_data["data"].copy()

        # Generate new name
        new_name = f"{original_name} (Copy)"
        counter = 1
        while new_name in self.prompts_data["categories"][category]:
            counter += 1
            new_name = f"{original_name} (Copy {counter})"

        # Add duplicate
        self.prompts_data["categories"][category][new_name] = prompt_data
        self.save_prompts()
        self.load_prompts_to_tree()
        self.select_prompt(category, new_name)
