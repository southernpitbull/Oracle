# -*- coding: utf-8 -*-
"""
Tag Editor Dialog for The Oracle AI Chat Application
File: ui/tag_editor_dialog.py
Author: The Oracle Development Team
Date: 2024-12-19

Comprehensive tag editor dialog for managing conversation tags with:
- Add/remove tags for conversations
- Tag suggestions from existing tags
- Tag filtering and organization
- Visual tag management interface
"""

import os
import json
import logging
from typing import Set, List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QListWidget, QListWidgetItem, QGroupBox,
                             QAbstractItemView, QMessageBox, QFrame, QScrollArea,
                             QWidget, QGridLayout, QComboBox, QCheckBox, QInputDialog)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor, QBrush, QPainter

logger = logging.getLogger(__name__)


class TagEditorDialog(QDialog):
    """Dialog for editing conversation tags with comprehensive functionality."""
    
    # Signals
    tags_updated = pyqtSignal(str, set)  # conversation_id, new_tags
    
    def __init__(self, parent=None, conversation_id: str = None, 
                 current_tags: Set[str] = None, all_tags: Set[str] = None):
        super().__init__(parent)
        self.conversation_id = conversation_id
        self.current_tags = set(current_tags or [])
        self.all_tags = set(all_tags or [])
        self.suggested_tags = set()
        self.tag_colors = {}
        
        self.setup_ui()
        self.load_tag_colors()
        
    def setup_ui(self):
        """Set up the tag editor interface."""
        self.setWindowTitle("🏷️ Edit Conversation Tags")
        self.setMinimumSize(500, 600)
        self.setMaximumSize(700, 800)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("Conversation Tag Management")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        if self.conversation_id:
            conv_label = QLabel(f"Conversation ID: {self.conversation_id}")
            conv_label.setFont(QFont("Arial", 10))
            header_layout.addWidget(conv_label)
        
        layout.addWidget(header_frame)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left panel - Current tags
        left_panel = self.create_current_tags_panel()
        content_layout.addWidget(left_panel)
        
        # Right panel - Add tags
        right_panel = self.create_add_tags_panel()
        content_layout.addWidget(right_panel)
        
        layout.addLayout(content_layout)
        
        # Tag statistics
        stats_frame = self.create_statistics_panel()
        layout.addWidget(stats_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Tag management buttons
        manage_btn = QPushButton("⚙️ Manage All Tags")
        manage_btn.clicked.connect(self.show_tag_management)
        button_layout.addWidget(manage_btn)
        
        button_layout.addStretch()
        
        # Standard buttons
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Save Tags")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Apply styling
        self.apply_styles()
        
    def create_current_tags_panel(self):
        """Create the current tags panel."""
        panel = QGroupBox("Current Tags")
        layout = QVBoxLayout(panel)
        
        # Current tags list
        self.current_tags_list = QListWidget()
        self.current_tags_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.current_tags_list.setMaximumHeight(300)
        self.update_current_tags_display()
        layout.addWidget(self.current_tags_list)
        
        # Current tags buttons
        current_buttons_layout = QHBoxLayout()
        
        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_tags)
        current_buttons_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self.clear_all_tags)
        current_buttons_layout.addWidget(clear_btn)
        
        layout.addLayout(current_buttons_layout)
        
        return panel
        
    def create_add_tags_panel(self):
        """Create the add tags panel."""
        panel = QGroupBox("Add Tags")
        layout = QVBoxLayout(panel)
        
        # Tag input section
        input_group = QGroupBox("New Tag")
        input_layout = QVBoxLayout(input_group)
        
        input_row = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Enter new tag...")
        self.tag_input.returnPressed.connect(self.add_tag)
        input_row.addWidget(self.tag_input)
        
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.add_tag)
        input_row.addWidget(add_btn)
        
        input_layout.addLayout(input_row)
        layout.addWidget(input_group)
        
        # Quick add section
        if self.all_tags:
            quick_group = QGroupBox("Quick Add")
            quick_layout = QVBoxLayout(quick_group)
            
            quick_label = QLabel("Click to add existing tags:")
            quick_layout.addWidget(quick_label)
            
            self.quick_tags_list = QListWidget()
            self.quick_tags_list.setMaximumHeight(200)
            self.update_quick_tags_display()
            self.quick_tags_list.itemDoubleClicked.connect(self.add_quick_tag)
            quick_layout.addWidget(self.quick_tags_list)
            
            layout.addWidget(quick_group)
        
        # Suggested tags section
        if self.suggested_tags:
            suggested_group = QGroupBox("Suggested Tags")
            suggested_layout = QVBoxLayout(suggested_group)
            
            suggested_label = QLabel("AI-suggested tags based on conversation content:")
            suggested_layout.addWidget(suggested_label)
            
            self.suggested_tags_list = QListWidget()
            self.suggested_tags_list.setMaximumHeight(150)
            self.update_suggested_tags_display()
            self.suggested_tags_list.itemDoubleClicked.connect(self.add_suggested_tag)
            suggested_layout.addWidget(self.suggested_tags_list)
            
            layout.addWidget(suggested_group)
        
        return panel
        
    def create_statistics_panel(self):
        """Create the statistics panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # Tag count
        count_label = QLabel(f"📊 Total Tags: {len(self.current_tags)}")
        count_label.setStyleSheet("font-weight: bold; color: #6366f1;")
        layout.addWidget(count_label)
        
        # Most used tags
        if self.all_tags:
            most_used = self.get_most_used_tags()
            if most_used:
                used_label = QLabel(f"🔥 Most Used: {', '.join(most_used[:3])}")
                used_label.setStyleSheet("color: #888;")
                layout.addWidget(used_label)
        
        layout.addStretch()
        
        return panel
        
    def update_current_tags_display(self):
        """Update the display of current tags."""
        self.current_tags_list.clear()
        for tag in sorted(self.current_tags):
            item = self.create_tag_item(tag, is_current=True)
            self.current_tags_list.addItem(item)
            
    def update_quick_tags_display(self):
        """Update the display of quick add tags."""
        self.quick_tags_list.clear()
        available_tags = self.all_tags - self.current_tags
        for tag in sorted(available_tags):
            item = self.create_tag_item(tag, is_current=False)
            self.quick_tags_list.addItem(item)
            
    def update_suggested_tags_display(self):
        """Update the display of suggested tags."""
        self.suggested_tags_list.clear()
        for tag in sorted(self.suggested_tags):
            item = self.create_tag_item(tag, is_current=False, is_suggested=True)
            self.suggested_tags_list.addItem(item)
            
    def create_tag_item(self, tag: str, is_current: bool = False, 
                       is_suggested: bool = False) -> QListWidgetItem:
        """Create a tag list item with appropriate styling."""
        if is_suggested:
            text = f"💡 {tag}"
        elif is_current:
            text = f"🏷️ {tag}"
        else:
            text = f"💡 {tag}"
            
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, tag)
        
        # Set background color based on tag type
        if is_current:
            item.setBackground(QBrush(QColor(99, 102, 241, 50)))  # Light blue
        elif is_suggested:
            item.setBackground(QBrush(QColor(34, 197, 94, 50)))   # Light green
        else:
            item.setBackground(QBrush(QColor(156, 163, 175, 30))) # Light gray
            
        return item
        
    def add_tag(self):
        """Add a new tag from input."""
        tag = self.tag_input.text().strip()
        if not tag:
            return
            
        # Validate tag format
        if not self.is_valid_tag(tag):
            QMessageBox.warning(self, "Invalid Tag", 
                              "Tags should be 1-20 characters long and contain only letters, numbers, spaces, and hyphens.")
            return
            
        if tag not in self.current_tags:
            self.current_tags.add(tag)
            self.tag_input.clear()
            self.update_current_tags_display()
            if hasattr(self, 'quick_tags_list'):
                self.update_quick_tags_display()
                
    def add_quick_tag(self, item):
        """Add a tag from the quick add list."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        if tag not in self.current_tags:
            self.current_tags.add(tag)
            self.update_current_tags_display()
            self.update_quick_tags_display()
            
    def add_suggested_tag(self, item):
        """Add a suggested tag."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        if tag not in self.current_tags:
            self.current_tags.add(tag)
            self.update_current_tags_display()
            self.update_suggested_tags_display()
            
    def remove_selected_tags(self):
        """Remove selected tags."""
        selected_items = self.current_tags_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select tags to remove.")
            return
            
        for item in selected_items:
            tag = item.data(Qt.ItemDataRole.UserRole)
            self.current_tags.discard(tag)
            
        self.update_current_tags_display()
        if hasattr(self, 'quick_tags_list'):
            self.update_quick_tags_display()
            
    def clear_all_tags(self):
        """Clear all tags from the conversation."""
        if not self.current_tags:
            return
            
        reply = QMessageBox.question(self, "Clear All Tags", 
                                   "Are you sure you want to remove all tags from this conversation?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_tags.clear()
            self.update_current_tags_display()
            if hasattr(self, 'quick_tags_list'):
                self.update_quick_tags_display()
                
    def is_valid_tag(self, tag: str) -> bool:
        """Validate tag format."""
        if not tag or len(tag) > 20:
            return False
            
        # Allow letters, numbers, spaces, and hyphens
        import re
        return bool(re.match(r'^[a-zA-Z0-9\s\-]+$', tag))
        
    def get_most_used_tags(self) -> List[str]:
        """Get the most frequently used tags."""
        # This would typically load from a database or file
        # For now, return a simple list
        return list(self.all_tags)[:5]
        
    def load_tag_colors(self):
        """Load tag color preferences."""
        try:
            if os.path.exists('conversations/tag_colors.json'):
                with open('conversations/tag_colors.json', 'r') as f:
                    self.tag_colors = json.load(f)
        except Exception as e:
            logger.error(f"Error loading tag colors: {e}")
            self.tag_colors = {}
            
    def save_tag_colors(self):
        """Save tag color preferences."""
        try:
            os.makedirs('conversations', exist_ok=True)
            with open('conversations/tag_colors.json', 'w') as f:
                json.dump(self.tag_colors, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving tag colors: {e}")
            
    def show_tag_management(self):
        """Show the tag management dialog."""
        dialog = TagManagementDialog(self, self.all_tags, self.tag_colors)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update tag colors
            self.tag_colors = dialog.get_tag_colors()
            self.save_tag_colors()
            
            # Refresh displays
            self.update_current_tags_display()
            if hasattr(self, 'quick_tags_list'):
                self.update_quick_tags_display()
                
    def get_tags(self) -> Set[str]:
        """Get the current tags."""
        return self.current_tags.copy()
        
    def apply_styles(self):
        """Apply custom styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
            QListWidget::item:selected {
                background-color: #6366f1;
                color: white;
            }
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5855eb;
            }
            QPushButton:pressed {
                background-color: #4f46e5;
            }
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)


class TagManagementDialog(QDialog):
    """Dialog for managing all tags across conversations."""
    
    def __init__(self, parent=None, all_tags: Set[str] = None, tag_colors: dict = None):
        super().__init__(parent)
        self.all_tags = set(all_tags or [])
        self.tag_colors = dict(tag_colors or {})
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the tag management interface."""
        self.setWindowTitle("⚙️ Tag Management")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Manage All Tags")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Tag list with colors
        self.tag_list = QListWidget()
        self.update_tag_list()
        layout.addWidget(self.tag_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Tag")
        add_btn.clicked.connect(self.add_new_tag)
        button_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("🗑️ Delete Tag")
        delete_btn.clicked.connect(self.delete_tag)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def update_tag_list(self):
        """Update the tag list display."""
        self.tag_list.clear()
        for tag in sorted(self.all_tags):
            item = QListWidgetItem(f"🏷️ {tag}")
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.tag_list.addItem(item)
            
    def add_new_tag(self):
        """Add a new tag to the global tag list."""
        tag, ok = QInputDialog.getText(self, "Add Tag", "Enter new tag name:")
        if ok and tag.strip():
            tag = tag.strip()
            if tag not in self.all_tags:
                self.all_tags.add(tag)
                self.update_tag_list()
                
    def delete_tag(self):
        """Delete a tag from the global tag list."""
        current_item = self.tag_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a tag to delete.")
            return
            
        tag = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Delete Tag", 
                                   f"Are you sure you want to delete the tag '{tag}'?\n\nThis will remove it from all conversations.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.all_tags.discard(tag)
            if tag in self.tag_colors:
                del self.tag_colors[tag]
            self.update_tag_list()
            
    def get_tag_colors(self) -> dict:
        """Get the current tag colors."""
        return self.tag_colors.copy() 
