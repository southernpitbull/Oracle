"""
Keyboard Shortcut Editor Dialog for The Oracle AI Chat Application.

This dialog allows users to customize keyboard shortcuts for common actions
like "New Chat," "Send Message," etc.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QMessageBox, QGroupBox, QFormLayout, QDialogButtonBox,
    QLineEdit, QKeySequenceEdit, QHeaderView, QTabWidget, QWidget,
    QTextEdit, QCheckBox, QComboBox, QSpacerItem, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QKeySequence, QFont


class KeyboardShortcutEditor(QDialog):
    """Dialog for editing keyboard shortcuts."""
    
    shortcuts_changed = pyqtSignal(dict)  # Emitted when shortcuts are changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)
        self.resize(700, 500)
        
        # Data storage
        self.shortcuts_file = Path("keyboard_shortcuts.json")
        self.shortcuts_data = self.load_shortcuts()
        self.default_shortcuts = self.get_default_shortcuts()
        self.modified_shortcuts = {}
        
        # UI setup
        self.setup_ui()
        self.setup_connections()
        self.load_shortcuts_to_tree()
        
        # Apply styling
        self.setup_styles()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Customize keyboard shortcuts for The Oracle")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Search section
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search shortcuts...")
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_edit)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        search_layout.addWidget(QLabel("Category:"))
        search_layout.addWidget(self.category_filter)
        
        layout.addLayout(search_layout)
        
        # Main content
        main_group = QGroupBox("Shortcuts")
        main_layout = QVBoxLayout(main_group)
        
        # Shortcuts tree
        self.shortcuts_tree = QTreeWidget()
        self.shortcuts_tree.setHeaderLabels(["Action", "Category", "Current Shortcut", "Default"])
        header = self.shortcuts_tree.header()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.shortcuts_tree.setAlternatingRowColors(True)
        self.shortcuts_tree.setRootIsDecorated(False)
        main_layout.addWidget(self.shortcuts_tree)
        
        # Edit section
        edit_group = QGroupBox("Edit Shortcut")
        edit_layout = QFormLayout(edit_group)
        
        self.action_label = QLabel("No action selected")
        self.action_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        edit_layout.addRow("Action:", self.action_label)
        
        self.current_shortcut_edit = QKeySequenceEdit()
        edit_layout.addRow("Shortcut:", self.current_shortcut_edit)
        
        # Edit buttons
        edit_buttons = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.reset_btn = QPushButton("Reset to Default")
        self.apply_btn = QPushButton("Apply")
        
        edit_buttons.addWidget(self.clear_btn)
        edit_buttons.addWidget(self.reset_btn)
        edit_buttons.addStretch()
        edit_buttons.addWidget(self.apply_btn)
        
        edit_layout.addRow(edit_buttons)
        
        # Initially disable edit section
        self.set_edit_enabled(False)
        
        layout.addWidget(main_group)
        layout.addWidget(edit_group)
        
        # Global buttons
        global_buttons = QHBoxLayout()
        self.reset_all_btn = QPushButton("Reset All to Defaults")
        self.export_btn = QPushButton("Export...")
        self.import_btn = QPushButton("Import...")
        
        global_buttons.addWidget(self.reset_all_btn)
        global_buttons.addWidget(self.export_btn)
        global_buttons.addWidget(self.import_btn)
        global_buttons.addStretch()
        
        layout.addLayout(global_buttons)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        layout.addWidget(button_box)
        
        # Store references
        self.button_box = button_box
        self.edit_group = edit_group
    
    def setup_connections(self):
        """Set up signal connections."""
        # Search and filter
        self.search_edit.textChanged.connect(self.filter_shortcuts)
        self.category_filter.currentTextChanged.connect(self.filter_shortcuts)
        
        # Tree selection
        self.shortcuts_tree.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Edit controls
        self.current_shortcut_edit.keySequenceChanged.connect(self.on_shortcut_changed)
        self.clear_btn.clicked.connect(self.clear_shortcut)
        self.reset_btn.clicked.connect(self.reset_to_default)
        self.apply_btn.clicked.connect(self.apply_current_shortcut)
        
        # Global actions
        self.reset_all_btn.clicked.connect(self.reset_all_to_defaults)
        self.export_btn.clicked.connect(self.export_shortcuts)
        self.import_btn.clicked.connect(self.import_shortcuts)
        
        # Dialog buttons
        self.button_box.accepted.connect(self.accept_changes)
        self.button_box.rejected.connect(self.reject)
        apply_button = self.button_box.button(QDialogButtonBox.StandardButton.Apply)
        if apply_button:
            apply_button.clicked.connect(self.apply_changes)
    
    def setup_styles(self):
        """Apply styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTreeWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                alternate-background-color: #404040;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QLineEdit, QComboBox, QKeySequenceEdit {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
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
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
    
    def get_default_shortcuts(self) -> Dict:
        """Get default keyboard shortcuts."""
        return {
            "file": {
                "new_chat": {
                    "name": "New Chat",
                    "shortcut": "Ctrl+N",
                    "description": "Start a new conversation"
                },
                "save_chat": {
                    "name": "Save Chat",
                    "shortcut": "Ctrl+S",
                    "description": "Save current conversation"
                },
                "load_chat": {
                    "name": "Load Chat",
                    "shortcut": "Ctrl+O",
                    "description": "Load a conversation"
                },
                "export_chat": {
                    "name": "Export Chat",
                    "shortcut": "Ctrl+E",
                    "description": "Export current conversation"
                }
            },
            "chat": {
                "send_message": {
                    "name": "Send Message",
                    "shortcut": "Ctrl+Return",
                    "description": "Send the current message"
                },
                "clear_chat": {
                    "name": "Clear Chat",
                    "shortcut": "Ctrl+K",
                    "description": "Clear the current conversation"
                },
                "prompt_library": {
                    "name": "Prompt Library",
                    "shortcut": "Ctrl+P",
                    "description": "Open prompt library"
                },
                "system_prompt": {
                    "name": "Set System Prompt",
                    "shortcut": "Ctrl+Shift+P",
                    "description": "Set system prompt for conversation"
                }
            },
            "edit": {
                "copy_message": {
                    "name": "Copy Message",
                    "shortcut": "Ctrl+C",
                    "description": "Copy selected message"
                },
                "copy_code": {
                    "name": "Copy Code",
                    "shortcut": "Ctrl+Shift+C",
                    "description": "Copy code from selected block"
                },
                "search": {
                    "name": "Search in Chat",
                    "shortcut": "Ctrl+F",
                    "description": "Search within current conversation"
                }
            },
            "view": {
                "toggle_theme": {
                    "name": "Toggle Theme",
                    "shortcut": "Ctrl+T",
                    "description": "Switch between light and dark theme"
                },
                "line_numbers": {
                    "name": "Toggle Line Numbers",
                    "shortcut": "Ctrl+L",
                    "description": "Show/hide line numbers in code blocks"
                },
                "code_folding": {
                    "name": "Toggle Code Folding",
                    "shortcut": "Ctrl+F",
                    "description": "Enable/disable code folding"
                },
                "compact_mode": {
                    "name": "Toggle Compact Mode",
                    "shortcut": "Ctrl+M",
                    "description": "Switch between compact and spacious UI"
                }
            },
            "tools": {
                "attach_file": {
                    "name": "Attach File",
                    "shortcut": "Ctrl+A",
                    "description": "Attach a file to the conversation"
                },
                "api_settings": {
                    "name": "API Settings",
                    "shortcut": "Ctrl+,",
                    "description": "Open API settings dialog"
                }
            }
        }
    
    def load_shortcuts(self) -> Dict:
        """Load shortcuts from JSON file."""
        if self.shortcuts_file.exists():
            try:
                with open(self.shortcuts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading shortcuts: {e}")
        
        return self.get_default_shortcuts()
    
    def save_shortcuts(self):
        """Save shortcuts to JSON file."""
        try:
            with open(self.shortcuts_file, 'w', encoding='utf-8') as f:
                json.dump(self.shortcuts_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save shortcuts: {e}")
    
    def load_shortcuts_to_tree(self):
        """Load shortcuts into the tree widget."""
        self.shortcuts_tree.clear()
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        
        for category_name, shortcuts in self.shortcuts_data.items():
            self.category_filter.addItem(category_name.title())
            
            for shortcut_id, shortcut_data in shortcuts.items():
                name = shortcut_data.get("name", shortcut_id)
                current_shortcut = shortcut_data.get("shortcut", "")
                default_shortcut = self.default_shortcuts.get(category_name, {}).get(shortcut_id, {}).get("shortcut", "")
                
                item = QTreeWidgetItem([
                    name,
                    category_name.title(),
                    current_shortcut,
                    default_shortcut
                ])
                
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    "category": category_name,
                    "id": shortcut_id,
                    "data": shortcut_data
                })
                
                self.shortcuts_tree.addTopLevelItem(item)
    
    def filter_shortcuts(self):
        """Filter shortcuts based on search text and category."""
        search_text = self.search_edit.text().lower()
        selected_category = self.category_filter.currentText()
        
        for i in range(self.shortcuts_tree.topLevelItemCount()):
            item = self.shortcuts_tree.topLevelItem(i)
            if not item:
                continue
            
            user_data = item.data(0, Qt.ItemDataRole.UserRole)
            if not user_data:
                continue
            
            category = user_data["category"]
            name = user_data["data"].get("name", "")
            description = user_data["data"].get("description", "")
            
            # Category filter
            category_match = (selected_category == "All Categories" or 
                            category.title() == selected_category)
            
            # Search filter
            search_match = True
            if search_text:
                searchable_text = f"{name} {description} {category}".lower()
                search_match = search_text in searchable_text
            
            item.setHidden(not (category_match and search_match))
    
    def on_selection_changed(self):
        """Handle tree selection changes."""
        current_item = self.shortcuts_tree.currentItem()
        if not current_item:
            self.set_edit_enabled(False)
            return
        
        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data:
            self.set_edit_enabled(False)
            return
        
        # Load shortcut data into editor
        shortcut_data = user_data["data"]
        self.action_label.setText(shortcut_data.get("name", "Unknown Action"))
        
        current_shortcut = shortcut_data.get("shortcut", "")
        self.current_shortcut_edit.setKeySequence(QKeySequence(current_shortcut))
        
        self.set_edit_enabled(True)
        
        # Store current selection
        self.current_category = user_data["category"]
        self.current_id = user_data["id"]
    
    def set_edit_enabled(self, enabled):
        """Enable or disable the edit section."""
        self.current_shortcut_edit.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.reset_btn.setEnabled(enabled)
        self.apply_btn.setEnabled(enabled)
        
        if not enabled:
            self.action_label.setText("No action selected")
            self.current_shortcut_edit.clear()
    
    def on_shortcut_changed(self, key_sequence):
        """Handle shortcut changes."""
        # Check for conflicts
        shortcut_text = key_sequence.toString()
        if shortcut_text:
            conflict = self.check_shortcut_conflict(shortcut_text)
            if conflict:
                self.current_shortcut_edit.setStyleSheet("border: 2px solid red;")
                self.apply_btn.setEnabled(False)
                QMessageBox.warning(self, "Shortcut Conflict", 
                                  f"This shortcut is already used by: {conflict}")
            else:
                self.current_shortcut_edit.setStyleSheet("")
                self.apply_btn.setEnabled(True)
    
    def check_shortcut_conflict(self, shortcut_text: str) -> Optional[str]:
        """Check if a shortcut conflicts with existing ones."""
        current_item = self.shortcuts_tree.currentItem()
        if not current_item:
            return None
        
        current_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        current_category = current_data["category"]
        current_id = current_data["id"]
        
        for category_name, shortcuts in self.shortcuts_data.items():
            for shortcut_id, shortcut_data in shortcuts.items():
                # Skip current item
                if category_name == current_category and shortcut_id == current_id:
                    continue
                
                if shortcut_data.get("shortcut", "") == shortcut_text:
                    return shortcut_data.get("name", f"{category_name}.{shortcut_id}")
        
        return None
    
    def clear_shortcut(self):
        """Clear the current shortcut."""
        self.current_shortcut_edit.clear()
    
    def reset_to_default(self):
        """Reset current shortcut to default."""
        current_item = self.shortcuts_tree.currentItem()
        if not current_item:
            return
        
        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data:
            return
        
        category = user_data["category"]
        shortcut_id = user_data["id"]
        
        default_shortcut = self.default_shortcuts.get(category, {}).get(shortcut_id, {}).get("shortcut", "")
        self.current_shortcut_edit.setKeySequence(QKeySequence(default_shortcut))
    
    def apply_current_shortcut(self):
        """Apply the current shortcut changes."""
        current_item = self.shortcuts_tree.currentItem()
        if not current_item:
            return
        
        user_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not user_data:
            return
        
        category = user_data["category"]
        shortcut_id = user_data["id"]
        new_shortcut = self.current_shortcut_edit.keySequence().toString()
        
        # Update data
        self.shortcuts_data[category][shortcut_id]["shortcut"] = new_shortcut
        
        # Update tree display
        current_item.setText(2, new_shortcut)
        
        # Mark as modified
        self.modified_shortcuts[f"{category}.{shortcut_id}"] = new_shortcut
        
        QMessageBox.information(self, "Shortcut Updated", 
                              f"Shortcut updated to: {new_shortcut}")
    
    def reset_all_to_defaults(self):
        """Reset all shortcuts to defaults."""
        reply = QMessageBox.question(self, "Reset All Shortcuts",
                                   "Are you sure you want to reset all shortcuts to defaults?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.shortcuts_data = self.get_default_shortcuts().copy()
            self.modified_shortcuts.clear()
            self.load_shortcuts_to_tree()
            QMessageBox.information(self, "Reset Complete", "All shortcuts have been reset to defaults.")
    
    def export_shortcuts(self):
        """Export shortcuts to a file."""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Shortcuts", 
                "keyboard_shortcuts.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.shortcuts_data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Export Complete", f"Shortcuts exported to: {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export shortcuts: {e}")
    
    def import_shortcuts(self):
        """Import shortcuts from a file."""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Import Shortcuts",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                # Validate structure (basic check)
                if isinstance(imported_data, dict):
                    reply = QMessageBox.question(self, "Import Shortcuts",
                                               "This will replace all current shortcuts. Continue?",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.shortcuts_data = imported_data
                        self.load_shortcuts_to_tree()
                        QMessageBox.information(self, "Import Complete", "Shortcuts imported successfully.")
                else:
                    QMessageBox.warning(self, "Import Error", "Invalid file format.")
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import shortcuts: {e}")
    
    def apply_changes(self):
        """Apply changes without closing dialog."""
        self.save_shortcuts()
        self.shortcuts_changed.emit(self.shortcuts_data)
        QMessageBox.information(self, "Changes Applied", "Keyboard shortcuts have been updated.")
    
    def accept_changes(self):
        """Accept and apply changes, then close dialog."""
        self.save_shortcuts()
        self.shortcuts_changed.emit(self.shortcuts_data)
        self.accept()
    
    def get_shortcuts_dict(self) -> Dict[str, str]:
        """Get a flattened dict of action_id -> shortcut for easy lookup."""
        result = {}
        for category_name, shortcuts in self.shortcuts_data.items():
            for shortcut_id, shortcut_data in shortcuts.items():
                action_id = f"{category_name}.{shortcut_id}"
                result[action_id] = shortcut_data.get("shortcut", "")
        return result
