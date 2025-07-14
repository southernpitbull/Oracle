# -*- coding: utf-8 -*-
# File: ui/last_read_marker_widget.py
# Author: The Oracle Development Team
# Date: 2024-12-19
# Description: GUI components for Last Read Marker system

"""
Last Read Marker GUI Components

This module provides GUI widgets and components for displaying and managing
last read markers in conversations.
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QToolButton, QMenu,
    QProgressBar, QCheckBox, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPalette

from core.last_read_marker import LastReadMarker
from utils.error_handler import (
    ErrorCategory,
    ErrorSeverity,
    error_handler,
    log_function_call,
    safe_execute
)


class UnreadIndicator(QWidget):
    """
    Visual indicator for unread messages in conversations.
    
    Displays a colored dot or badge showing unread message count.
    """
    
    clicked = pyqtSignal(str)  # Emits conversation_id when clicked
    
    def __init__(self, conversation_id: str, unread_count: int = 0, parent=None):
        super().__init__(parent)
        self.conversation_id = conversation_id
        self.unread_count = unread_count
        self.setup_ui()
    
    @log_function_call
    def setup_ui(self):
        """Setup the unread indicator UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Create the indicator label
        self.indicator_label = QLabel()
        self.indicator_label.setFixedSize(12, 12)
        self.indicator_label.setStyleSheet("""
            QLabel {
                background-color: #007acc;
                border-radius: 6px;
                border: 1px solid #005a9e;
            }
        """)
        
        # Create count label
        self.count_label = QLabel()
        self.count_label.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        
        layout.addWidget(self.indicator_label)
        layout.addWidget(self.count_label)
        layout.addStretch()
        
        self.update_display()
        
        # Make clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mousePressEvent = self._on_click
    
    @log_function_call
    def update_display(self):
        """Update the visual display based on unread count."""
        if self.unread_count > 0:
            self.indicator_label.setVisible(True)
            self.count_label.setVisible(True)
            
            if self.unread_count > 99:
                self.count_label.setText("99+")
            else:
                self.count_label.setText(str(self.unread_count))
                
            # Change color based on count
            if self.unread_count > 10:
                color = "#ff4444"  # Red for many unread
            elif self.unread_count > 5:
                color = "#ff8800"  # Orange for moderate
            else:
                color = "#007acc"  # Blue for few
                
            self.indicator_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    border-radius: 6px;
                    border: 1px solid {color};
                }}
            """)
        else:
            self.indicator_label.setVisible(False)
            self.count_label.setVisible(False)
    
    @log_function_call
    def set_unread_count(self, count: int):
        """Set the unread count and update display."""
        self.unread_count = count
        self.update_display()
    
    def _on_click(self, event):
        """Handle click events."""
        self.clicked.emit(self.conversation_id)


class LastReadMarkerWidget(QWidget):
    """
    Main widget for managing last read markers.
    
    Provides a comprehensive interface for viewing and managing
    conversation reading progress.
    """
    
    conversation_selected = pyqtSignal(str)  # Emits conversation_id
    marker_updated = pyqtSignal(str, str)  # Emits conversation_id, message_id
    
    def __init__(self, last_read_marker: LastReadMarker, parent=None):
        super().__init__(parent)
        self.last_read_marker = last_read_marker
        self.conversation_data = {}
        self.unread_indicators = {}
        self.setup_ui()
    
    @log_function_call
    def setup_ui(self):
        """Setup the main widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Last Read Markers")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
            }
        """)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_markers)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self.clear_all_markers)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(clear_all_btn)
        
        layout.addLayout(header_layout)
        
        # Summary section
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #f5f5f5;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
        """)
        layout.addWidget(self.summary_label)
        
        # Conversations list
        self.conversations_scroll = QScrollArea()
        self.conversations_widget = QWidget()
        self.conversations_layout = QVBoxLayout(self.conversations_widget)
        self.conversations_layout.setSpacing(5)
        self.conversations_layout.addStretch()
        
        self.conversations_scroll.setWidget(self.conversations_widget)
        self.conversations_scroll.setWidgetResizable(True)
        self.conversations_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        layout.addWidget(self.conversations_scroll)
        
        # Update summary
        self.update_summary()
    
    @log_function_call
    def set_conversation_data(self, conversation_data: Dict):
        """Set conversation data and update display."""
        self.conversation_data = conversation_data
        self.update_conversations_list()
        self.update_summary()
    
    @log_function_call
    def update_conversations_list(self):
        """Update the conversations list display."""
        # Clear existing widgets
        for i in reversed(range(self.conversations_layout.count() - 1)):
            widget = self.conversations_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.unread_indicators.clear()
        
        # Add conversation items
        for conv_id, conv_data in self.conversation_data.items():
            if 'messages' in conv_data and conv_data['messages']:
                item_widget = self.create_conversation_item(conv_id, conv_data)
                self.conversations_layout.insertWidget(
                    self.conversations_layout.count() - 1, item_widget
                )
    
    @log_function_call
    def create_conversation_item(self, conv_id: str, conv_data: Dict) -> QWidget:
        """Create a widget for a single conversation item."""
        item_widget = QFrame()
        item_widget.setFrameStyle(QFrame.Shape.StyledPanel)
        item_widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #f0f8ff;
                border-color: #007acc;
            }
        """)
        
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Conversation title
        title = conv_data.get('title', f'Conversation {conv_id[:8]}')
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        
        # Unread indicator
        unread_count = self.get_unread_count(conv_id, conv_data)
        indicator = UnreadIndicator(conv_id, unread_count)
        indicator.clicked.connect(self.on_conversation_clicked)
        self.unread_indicators[conv_id] = indicator
        
        # Last read info
        last_read_info = self.get_last_read_info(conv_id)
        info_label = QLabel(last_read_info)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        
        # Actions
        actions_layout = QHBoxLayout()
        
        mark_read_btn = QPushButton("Mark Read")
        mark_read_btn.setFixedSize(80, 25)
        mark_read_btn.clicked.connect(lambda: self.mark_conversation_read(conv_id))
        
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(60, 25)
        clear_btn.clicked.connect(lambda: self.clear_conversation_marker(conv_id))
        
        actions_layout.addWidget(mark_read_btn)
        actions_layout.addWidget(clear_btn)
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(indicator)
        layout.addWidget(info_label)
        layout.addLayout(actions_layout)
        
        return item_widget
    
    @log_function_call
    def get_unread_count(self, conv_id: str, conv_data: Dict) -> int:
        """Get unread count for a conversation."""
        if 'messages' in conv_data and conv_data['messages']:
            message_ids = [msg['id'] for msg in conv_data['messages']]
            return self.last_read_marker.get_unread_count(conv_id, message_ids)
        return 0
    
    @log_function_call
    def get_last_read_info(self, conv_id: str) -> str:
        """Get formatted last read information."""
        marker = self.last_read_marker.get_last_read(conv_id)
        if marker and 'last_read_timestamp' in marker:
            try:
                timestamp = datetime.fromisoformat(marker['last_read_timestamp'])
                return f"Last read: {timestamp.strftime('%Y-%m-%d %H:%M')}"
            except ValueError:
                return "Last read: Unknown"
        return "Not read"
    
    @log_function_call
    def update_summary(self):
        """Update the summary display."""
        summary = self.last_read_marker.get_marker_summary()
        
        summary_text = (
            f"Total conversations: {summary['total_conversations']} | "
            f"Recent activity: {summary['recent_markers']} | "
            f"Oldest: {summary['oldest_marker'][:10] if summary['oldest_marker'] else 'None'} | "
            f"Newest: {summary['newest_marker'][:10] if summary['newest_marker'] else 'None'}"
        )
        
        self.summary_label.setText(summary_text)
    
    @log_function_call
    def refresh_markers(self):
        """Refresh all markers and update display."""
        self.update_conversations_list()
        self.update_summary()
    
    @log_function_call
    def clear_all_markers(self):
        """Clear all last read markers."""
        self.last_read_marker.clear_all_markers()
        self.refresh_markers()
    
    @log_function_call
    def mark_conversation_read(self, conv_id: str):
        """Mark a conversation as read."""
        if conv_id in self.conversation_data:
            self.last_read_marker.mark_conversation_as_read(
                conv_id, self.conversation_data[conv_id]
            )
            self.refresh_markers()
            self.marker_updated.emit(conv_id, "")
    
    @log_function_call
    def clear_conversation_marker(self, conv_id: str):
        """Clear the marker for a specific conversation."""
        self.last_read_marker.clear_conversation_marker(conv_id)
        self.refresh_markers()
    
    @log_function_call
    def on_conversation_clicked(self, conv_id: str):
        """Handle conversation item click."""
        self.conversation_selected.emit(conv_id)
    
    @log_function_call
    def mark_message_as_read(self, conv_id: str, message_id: str):
        """Mark a specific message as read."""
        self.last_read_marker.mark_as_read(conv_id, message_id)
        
        # Update indicator if it exists
        if conv_id in self.unread_indicators:
            if conv_id in self.conversation_data:
                unread_count = self.get_unread_count(conv_id, self.conversation_data[conv_id])
                self.unread_indicators[conv_id].set_unread_count(unread_count)
        
        self.marker_updated.emit(conv_id, message_id)


class LastReadMarkerDialog(QWidget):
    """
    Dialog for managing last read markers.
    
    Provides a modal interface for viewing and managing conversation
    reading progress.
    """
    
    def __init__(self, last_read_marker: LastReadMarker, conversation_data: Dict, parent=None):
        super().__init__(parent)
        self.last_read_marker = last_read_marker
        self.conversation_data = conversation_data
        self.setup_ui()
    
    @log_function_call
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Last Read Markers")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Create the main widget
        self.marker_widget = LastReadMarkerWidget(self.last_read_marker)
        self.marker_widget.set_conversation_data(self.conversation_data)
        
        layout.addWidget(self.marker_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(100, 30)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout) 
