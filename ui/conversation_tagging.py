#!/usr/bin/env python3
"""
Conversation Tagging System
File: ui/conversation_tagging.py

This module provides a comprehensive conversation tagging system that allows users
to organize and categorize their conversations with custom tags, colors, and
hierarchical organization.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QDialog, QDialogButtonBox,
    QFormLayout, QColorDialog, QMessageBox, QFrame, QGridLayout,
    QScrollArea, QFrame, QMessageBox, QMenu, QToolButton,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QTabWidget,
    QTextEdit, QSplitter, QSizePolicy, QSpacerItem, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon, QAction

from utils.error_handler import error_handler, ErrorSeverity, ErrorCategory
from utils.dependencies import log as logger


class TagColor(Enum):
    """Predefined tag colors for easy selection."""
    RED = "#ff6b6b"
    ORANGE = "#ffa726"
    YELLOW = "#ffeb3b"
    GREEN = "#66bb6a"
    BLUE = "#42a5f5"
    PURPLE = "#ab47bc"
    PINK = "#ec407a"
    GRAY = "#9e9e9e"
    BROWN = "#8d6e63"
    TEAL = "#26a69a"


@dataclass
class Tag:
    """Represents a conversation tag with metadata."""
    id: str
    name: str
    color: str
    description: str = ""
    created_at: datetime = None
    updated_at: datetime = None
    usage_count: int = 0
    is_system: bool = False
    parent_id: Optional[str] = None
    children: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.children is None:
            self.children = []
    
    def to_dict(self) -> Dict:
        """Convert tag to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'usage_count': self.usage_count,
            'is_system': self.is_system,
            'parent_id': self.parent_id,
            'children': self.children
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Tag':
        """Create tag from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class TagManager:
    """Manages conversation tags with persistence and hierarchy."""
    
    def __init__(self, storage_path: str = "data/tags.json"):
        self.storage_path = storage_path
        self.tags: Dict[str, Tag] = {}
        self.conversation_tags: Dict[str, Set[str]] = {}  # conversation_id -> set of tag_ids
        self.load_tags()
        self.initialize_system_tags()
    
    def initialize_system_tags(self):
        """Initialize default system tags if none exist."""
        if not any(tag.is_system for tag in self.tags.values()):
            system_tags = [
                ("Important", TagColor.RED.value, "High priority conversations"),
                ("Work", TagColor.BLUE.value, "Work-related conversations"),
                ("Personal", TagColor.GREEN.value, "Personal conversations"),
                ("Research", TagColor.PURPLE.value, "Research and learning"),
                ("Code", TagColor.ORANGE.value, "Programming and development"),
                ("Draft", TagColor.GRAY.value, "Draft or incomplete conversations"),
                ("Archive", TagColor.BROWN.value, "Archived conversations"),
                ("Favorite", TagColor.YELLOW.value, "Favorite conversations"),
            ]
            
            for name, color, description in system_tags:
                self.create_tag(name, color, description, is_system=True)
    
    def create_tag(self, name: str, color: str, description: str = "", is_system: bool = False) -> Tag:
        """Create a new tag."""
        tag_id = str(uuid.uuid4())
        tag = Tag(
            id=tag_id,
            name=name,
            color=color,
            description=description,
            is_system=is_system
        )
        self.tags[tag_id] = tag
        self.save_tags()
        
        if hasattr(logger, 'info'):
            logger.info("Created tag: {} ({})".format(name, tag_id))
        
        return tag
    
    def update_tag(self, tag_id: str, **kwargs) -> bool:
        """Update an existing tag."""
        if tag_id not in self.tags:
            return False
        
        tag = self.tags[tag_id]
        for key, value in kwargs.items():
            if hasattr(tag, key):
                setattr(tag, key, value)
        
        tag.updated_at = datetime.now()
        self.save_tags()
        
        if hasattr(logger, 'info'):
            logger.info("Updated tag: {} ({})".format(tag.name, tag_id))
        
        return True
    
    def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag and remove it from all conversations."""
        if tag_id not in self.tags:
            return False
        
        tag = self.tags[tag_id]
        
        # Remove from all conversations
        for conversation_id in list(self.conversation_tags.keys()):
            self.conversation_tags[conversation_id].discard(tag_id)
            if not self.conversation_tags[conversation_id]:
                del self.conversation_tags[conversation_id]
        
        # Remove from parent's children list
        if tag.parent_id and tag.parent_id in self.tags:
            self.tags[tag.parent_id].children.remove(tag_id)
        
        # Move children to parent or make them root
        for child_id in tag.children:
            if child_id in self.tags:
                child_tag = self.tags[child_id]
                child_tag.parent_id = tag.parent_id
                if tag.parent_id and tag.parent_id in self.tags:
                    self.tags[tag.parent_id].children.append(child_id)
        
        del self.tags[tag_id]
        self.save_tags()
        
        if hasattr(logger, 'info'):
            logger.info("Deleted tag: {} ({})".format(tag.name, tag_id))
        
        return True
    
    def add_tag_to_conversation(self, conversation_id: str, tag_id: str) -> bool:
        """Add a tag to a conversation."""
        if tag_id not in self.tags:
            return False
        
        if conversation_id not in self.conversation_tags:
            self.conversation_tags[conversation_id] = set()
        
        self.conversation_tags[conversation_id].add(tag_id)
        self.tags[tag_id].usage_count += 1
        self.tags[tag_id].updated_at = datetime.now()
        self.save_tags()
        
        return True
    
    def remove_tag_from_conversation(self, conversation_id: str, tag_id: str) -> bool:
        """Remove a tag from a conversation."""
        if conversation_id not in self.conversation_tags:
            return False
        
        if tag_id in self.conversation_tags[conversation_id]:
            self.conversation_tags[conversation_id].remove(tag_id)
            if not self.conversation_tags[conversation_id]:
                del self.conversation_tags[conversation_id]
            
            if tag_id in self.tags:
                self.tags[tag_id].usage_count = max(0, self.tags[tag_id].usage_count - 1)
                self.tags[tag_id].updated_at = datetime.now()
            
            self.save_tags()
            return True
        
        return False
    
    def get_conversation_tags(self, conversation_id: str) -> List[Tag]:
        """Get all tags for a conversation."""
        if conversation_id not in self.conversation_tags:
            return []
        
        return [self.tags[tag_id] for tag_id in self.conversation_tags[conversation_id] 
                if tag_id in self.tags]
    
    def get_conversations_with_tag(self, tag_id: str) -> List[str]:
        """Get all conversations that have a specific tag."""
        return [conv_id for conv_id, tag_set in self.conversation_tags.items() 
                if tag_id in tag_set]
    
    def search_tags(self, query: str) -> List[Tag]:
        """Search tags by name or description."""
        query = query.lower()
        results = []
        
        for tag in self.tags.values():
            if (query in tag.name.lower() or 
                query in tag.description.lower()):
                results.append(tag)
        
        return sorted(results, key=lambda t: t.name.lower())
    
    def get_tag_hierarchy(self) -> Dict[str, List[Tag]]:
        """Get tags organized by hierarchy."""
        hierarchy = {}
        
        for tag in self.tags.values():
            parent_id = tag.parent_id or "root"
            if parent_id not in hierarchy:
                hierarchy[parent_id] = []
            hierarchy[parent_id].append(tag)
        
        # Sort each level by name
        for parent_id in hierarchy:
            hierarchy[parent_id].sort(key=lambda t: t.name.lower())
        
        return hierarchy
    
    def load_tags(self):
        """Load tags from storage."""
        try:
            if os.path.exists(self.storage_path):
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load tags
                for tag_data in data.get('tags', []):
                    tag = Tag.from_dict(tag_data)
                    self.tags[tag.id] = tag
                
                # Load conversation tags
                for conv_id, tag_ids in data.get('conversation_tags', {}).items():
                    self.conversation_tags[conv_id] = set(tag_ids)
                
                if hasattr(logger, 'info'):
                    logger.info("Loaded {} tags and {} conversation tag mappings".format(
                        len(self.tags), len(self.conversation_tags)))
            
        except Exception as e:
            if hasattr(logger, 'error'):
                logger.error("Failed to load tags: {}".format(e))
            else:
                print("Error: Failed to load tags: {}".format(e))
    
    def save_tags(self):
        """Save tags to storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            data = {
                'tags': [tag.to_dict() for tag in self.tags.values()],
                'conversation_tags': {
                    conv_id: list(tag_ids) 
                    for conv_id, tag_ids in self.conversation_tags.items()
                }
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            if hasattr(logger, 'debug'):
                logger.debug("Saved {} tags and {} conversation tag mappings".format(
                    len(self.tags), len(self.conversation_tags)))
            
        except Exception as e:
            if hasattr(logger, 'error'):
                logger.error("Failed to save tags: {}".format(e))
            else:
                print("Error: Failed to save tags: {}".format(e))


class TagColorButton(QPushButton):
    """A button that displays a color and allows color selection."""
    
    color_changed = pyqtSignal(str)  # color_hex
    
    def __init__(self, color: str = "#42a5f5", parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 30)
        self.set_color(color)
        self.clicked.connect(self.choose_color)
    
    def set_color(self, color: str):
        """Set the button color."""
        self.color = color
        self.setStyleSheet("""
            QPushButton {
                background-color: %s;
                border: 2px solid #555555;
                border-radius: 15px;
            }
            QPushButton:hover {
                border: 2px solid #0078d4;
            }
        """ % color)
    
    def choose_color(self):
        """Open color dialog to choose a new color."""
        color_dialog = QColorDialog(QColor(self.color), self)
        color_dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        
        if color_dialog.exec() == QDialog.DialogCode.Accepted:
            new_color = color_dialog.selectedColor()
            color_hex = new_color.name()
            self.set_color(color_hex)
            self.color_changed.emit(color_hex)


class TagEditDialog(QDialog):
    """Dialog for creating or editing tags."""
    
    def __init__(self, tag_manager: TagManager, tag: Optional[Tag] = None, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.tag = tag
        self.is_editing = tag is not None
        
        self.setWindowTitle("Edit Tag" if self.is_editing else "Create Tag")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()
        
        if self.is_editing:
            self.load_tag_data()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter tag name...")
        form_layout.addRow("Name:", self.name_edit)
        
        # Color selection
        color_layout = QHBoxLayout()
        self.color_button = TagColorButton()
        self.color_button.color_changed.connect(self.on_color_changed)
        
        # Color presets
        self.color_combo = QComboBox()
        for color_enum in TagColor:
            self.color_combo.addItem(color_enum.name.title(), color_enum.value)
        self.color_combo.currentTextChanged.connect(self.on_preset_color_changed)
        
        color_layout.addWidget(QLabel("Color:"))
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_combo)
        color_layout.addStretch()
        
        form_layout.addRow("", color_layout)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Enter tag description (optional)...")
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Parent tag selection
        parent_group = QGroupBox("Parent Tag (Optional)")
        parent_layout = QVBoxLayout(parent_group)
        
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("None (Root Tag)", None)
        
        # Add existing tags as parent options
        for tag in self.tag_manager.tags.values():
            if not self.is_editing or tag.id != self.tag.id:
                self.parent_combo.addItem(tag.name, tag.id)
        
        parent_layout.addWidget(self.parent_combo)
        layout.addWidget(parent_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect validation
        self.name_edit.textChanged.connect(self.validate_form)
        self.validate_form()
    
    def load_tag_data(self):
        """Load existing tag data into the form."""
        self.name_edit.setText(self.tag.name)
        self.color_button.set_color(self.tag.color)
        self.description_edit.setPlainText(self.tag.description)
        
        # Set parent
        if self.tag.parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.tag.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break
    
    def on_color_changed(self, color: str):
        """Handle color button change."""
        # Update combo box to match
        for i in range(self.color_combo.count()):
            if self.color_combo.itemData(i) == color:
                self.color_combo.setCurrentIndex(i)
                break
    
    def on_preset_color_changed(self, color_name: str):
        """Handle preset color selection."""
        color_value = self.color_combo.currentData()
        if color_value:
            self.color_button.set_color(color_value)
    
    def validate_form(self):
        """Validate the form and enable/disable OK button."""
        name = self.name_edit.text().strip()
        is_valid = bool(name)
        
        # Check for duplicate names
        if is_valid and not self.is_editing:
            for tag in self.tag_manager.tags.values():
                if tag.name.lower() == name.lower():
                    is_valid = False
                    break
        
        # Enable/disable OK button
        ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setEnabled(is_valid)
    
    def accept(self):
        """Handle form submission."""
        name = self.name_edit.text().strip()
        color = self.color_button.color
        description = self.description_edit.toPlainText().strip()
        parent_id = self.parent_combo.currentData()
        
        if self.is_editing:
            # Update existing tag
            success = self.tag_manager.update_tag(
                self.tag.id,
                name=name,
                color=color,
                description=description,
                parent_id=parent_id
            )
            if not success:
                QMessageBox.warning(self, "Error", "Failed to update tag")
                return
        else:
            # Create new tag
            self.tag = self.tag_manager.create_tag(name, color, description)
            if parent_id:
                self.tag_manager.update_tag(self.tag.id, parent_id=parent_id)
        
        super().accept()


class TagWidget(QWidget):
    """A widget that displays a tag with color and name."""
    
    tag_clicked = pyqtSignal(str)  # tag_id
    tag_removed = pyqtSignal(str)  # tag_id
    
    def __init__(self, tag: Tag, removable: bool = True, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.removable = removable
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the tag widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Color indicator
        color_label = QLabel()
        color_label.setFixedSize(12, 12)
        color_label.setStyleSheet("""
            QLabel {
                background-color: %s;
                border-radius: 6px;
                border: 1px solid #555555;
            }
        """ % self.tag.color)
        layout.addWidget(color_label)
        
        # Tag name
        name_label = QLabel(self.tag.name)
        name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        layout.addWidget(name_label)
        
        # Remove button
        if self.removable:
            remove_btn = QPushButton("×")
            remove_btn.setFixedSize(16, 16)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    color: #ff6b6b;
                }
            """)
            remove_btn.clicked.connect(lambda: self.tag_removed.emit(self.tag.id))
            layout.addWidget(remove_btn)
        
        layout.addStretch()
        
        # Set widget style
        self.setStyleSheet("""
            QWidget {
                background-color: %s;
                border-radius: 8px;
                padding: 2px;
            }
        """ % self.tag.color)
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = self.on_click
    
    def on_click(self, event):
        """Handle widget click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.tag_clicked.emit(self.tag.id)


class TagManagerWidget(QWidget):
    """Main widget for managing tags."""
    
    tag_selected = pyqtSignal(str)  # tag_id
    tag_created = pyqtSignal(Tag)
    tag_updated = pyqtSignal(Tag)
    tag_deleted = pyqtSignal(str)  # tag_id
    
    def __init__(self, tag_manager: TagManager, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.setup_ui()
        self.refresh_tags()
    
    def setup_ui(self):
        """Set up the tag manager UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🏷️ Tag Manager")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Create tag button
        create_btn = QPushButton("➕ Create Tag")
        create_btn.setStyleSheet("""
            QPushButton {
                background: #00b894;
                border: 1px solid #00b894;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #00a085;
                border: 1px solid #00a085;
            }
        """)
        create_btn.clicked.connect(self.create_tag)
        header_layout.addWidget(create_btn)
        
        layout.addLayout(header_layout)
        
        # Search
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Search:")
        search_label.setStyleSheet("color: #ffffff;")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search tags...")
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 10px;
                color: white;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        self.search_edit.textChanged.connect(self.filter_tags)
        search_layout.addWidget(self.search_edit)
        
        layout.addLayout(search_layout)
        
        # Tags list
        self.tags_list = QListWidget()
        self.tags_list.setStyleSheet("""
            QListWidget {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 8px;
                color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background: #0078d4;
            }
            QListWidget::item:hover {
                background: #3a3a3a;
            }
        """)
        self.tags_list.itemClicked.connect(self.on_tag_selected)
        self.tags_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tags_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tags_list)
        
        # Statistics
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #888888; font-size: 11px;")
        stats_layout.addWidget(self.stats_label)
        
        layout.addLayout(stats_layout)
    
    def refresh_tags(self):
        """Refresh the tags list."""
        self.tags_list.clear()
        
        # Get tags sorted by usage count and name
        tags = sorted(
            self.tag_manager.tags.values(),
            key=lambda t: (-t.usage_count, t.name.lower())
        )
        
        for tag in tags:
            item = QListWidgetItem()
            
            # Create tag widget
            tag_widget = TagWidget(tag, removable=False)
            tag_widget.tag_clicked.connect(self.on_tag_selected)
            
            # Set item widget
            item.setSizeHint(tag_widget.sizeHint())
            self.tags_list.addItem(item)
            self.tags_list.setItemWidget(item, tag_widget)
        
        self.update_statistics()
    
    def filter_tags(self):
        """Filter tags based on search query."""
        query = self.search_edit.text().strip().lower()
        
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            tag_widget = self.tags_list.itemWidget(item)
            
            if query:
                # Show only matching tags
                item.setHidden(query not in tag_widget.tag.name.lower())
            else:
                # Show all tags
                item.setHidden(False)
    
    def on_tag_selected(self, tag_id: str):
        """Handle tag selection."""
        self.tag_selected.emit(tag_id)
    
    def create_tag(self):
        """Create a new tag."""
        dialog = TagEditDialog(self.tag_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_tags()
            self.tag_created.emit(dialog.tag)
    
    def edit_tag(self, tag_id: str):
        """Edit an existing tag."""
        if tag_id not in self.tag_manager.tags:
            return
        
        tag = self.tag_manager.tags[tag_id]
        dialog = TagEditDialog(self.tag_manager, tag, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_tags()
            self.tag_updated.emit(tag)
    
    def delete_tag(self, tag_id: str):
        """Delete a tag."""
        if tag_id not in self.tag_manager.tags:
            return
        
        tag = self.tag_manager.tags[tag_id]
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Tag",
            f"Are you sure you want to delete the tag '{tag.name}'?\n\n"
            f"This will remove it from {tag.usage_count} conversation(s).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.tag_manager.delete_tag(tag_id):
                self.refresh_tags()
                self.tag_deleted.emit(tag_id)
    
    def show_context_menu(self, position):
        """Show context menu for tags."""
        item = self.tags_list.itemAt(position)
        if not item:
            return
        
        tag_widget = self.tags_list.itemWidget(item)
        if not tag_widget:
            return
        
        tag = tag_widget.tag
        
        menu = QMenu(self)
        
        # Edit action
        edit_action = QAction("✏️ Edit Tag", self)
        edit_action.triggered.connect(lambda: self.edit_tag(tag.id))
        menu.addAction(edit_action)
        
        # Delete action (only for non-system tags)
        if not tag.is_system:
            delete_action = QAction("🗑️ Delete Tag", self)
            delete_action.triggered.connect(lambda: self.delete_tag(tag.id))
            menu.addAction(delete_action)
        
        # Show usage info
        if tag.usage_count > 0:
            menu.addSeparator()
            usage_action = QAction(f"📊 Used in {tag.usage_count} conversation(s)", self)
            usage_action.setEnabled(False)
            menu.addAction(usage_action)
        
        menu.exec(self.tags_list.mapToGlobal(position))
    
    def update_statistics(self):
        """Update statistics display."""
        total_tags = len(self.tag_manager.tags)
        system_tags = sum(1 for tag in self.tag_manager.tags.values() if tag.is_system)
        user_tags = total_tags - system_tags
        total_usage = sum(tag.usage_count for tag in self.tag_manager.tags.values())
        
        self.stats_label.setText(
            f"Total: {total_tags} tags ({system_tags} system, {user_tags} user) • "
            f"Total usage: {total_usage} conversations"
        )


class ConversationTagWidget(QWidget):
    """Widget for managing tags on a specific conversation."""
    
    tags_changed = pyqtSignal(list)  # list of tag_ids
    
    def __init__(self, tag_manager: TagManager, conversation_id: str, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.conversation_id = conversation_id
        self.setup_ui()
        self.refresh_tags()
    
    def setup_ui(self):
        """Set up the conversation tag widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🏷️ Tags")
        title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add tag button
        add_btn = QPushButton("➕")
        add_btn.setFixedSize(24, 24)
        add_btn.setToolTip("Add tag to conversation")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #00b894;
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #00a085;
            }
        """)
        add_btn.clicked.connect(self.show_tag_menu)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Tags container
        self.tags_container = QWidget()
        self.tags_layout = QVBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(4)
        
        layout.addWidget(self.tags_container)
    
    def refresh_tags(self):
        """Refresh the conversation tags display."""
        # Clear existing tags
        for i in reversed(range(self.tags_layout.count())):
            child = self.tags_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # Add current tags
        conversation_tags = self.tag_manager.get_conversation_tags(self.conversation_id)
        
        if not conversation_tags:
            # Show "no tags" message
            no_tags_label = QLabel("No tags added")
            no_tags_label.setStyleSheet("color: #888888; font-style: italic; font-size: 11px;")
            self.tags_layout.addWidget(no_tags_label)
        else:
            # Add tag widgets
            for tag in conversation_tags:
                tag_widget = TagWidget(tag, removable=True)
                tag_widget.tag_removed.connect(self.remove_tag)
                self.tags_layout.addWidget(tag_widget)
        
        self.tags_layout.addStretch()
    
    def show_tag_menu(self):
        """Show menu to add tags to the conversation."""
        menu = QMenu(self)
        
        # Get current conversation tags
        current_tag_ids = {tag.id for tag in self.tag_manager.get_conversation_tags(self.conversation_id)}
        
        # Add all available tags
        for tag in sorted(self.tag_manager.tags.values(), key=lambda t: t.name.lower()):
            action = QAction(tag.name, self)
            action.setCheckable(True)
            action.setChecked(tag.id in current_tag_ids)
            
            # Set icon color
            icon = QPixmap(16, 16)
            icon.fill(QColor(tag.color))
            action.setIcon(QIcon(icon))
            
            action.triggered.connect(lambda checked, t=tag: self.toggle_tag(t.id, checked))
            menu.addAction(action)
        
        # Add separator and create new tag option
        if self.tag_manager.tags:
            menu.addSeparator()
        
        create_action = QAction("➕ Create New Tag...", self)
        create_action.triggered.connect(self.create_new_tag)
        menu.addAction(create_action)
        
        menu.exec(self.mapToGlobal(self.sender().pos()))
    
    def toggle_tag(self, tag_id: str, add: bool):
        """Toggle a tag on the conversation."""
        if add:
            self.tag_manager.add_tag_to_conversation(self.conversation_id, tag_id)
        else:
            self.tag_manager.remove_tag_from_conversation(self.conversation_id, tag_id)
        
        self.refresh_tags()
        self.emit_tags_changed()
    
    def remove_tag(self, tag_id: str):
        """Remove a tag from the conversation."""
        self.tag_manager.remove_tag_from_conversation(self.conversation_id, tag_id)
        self.refresh_tags()
        self.emit_tags_changed()
    
    def create_new_tag(self):
        """Create a new tag and add it to the conversation."""
        dialog = TagEditDialog(self.tag_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Add the new tag to the conversation
            self.tag_manager.add_tag_to_conversation(self.conversation_id, dialog.tag.id)
            self.refresh_tags()
            self.emit_tags_changed()
    
    def emit_tags_changed(self):
        """Emit tags changed signal."""
        tag_ids = [tag.id for tag in self.tag_manager.get_conversation_tags(self.conversation_id)]
        self.tags_changed.emit(tag_ids) 
