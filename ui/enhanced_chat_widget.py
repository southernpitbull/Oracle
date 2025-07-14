# ui/enhanced_chat_widget.py
"""
Enhanced Chat Widget for The Oracle AI Assistant
Author: AI Assistant
Date: 2024-12-19

This module provides an enhanced chat widget with modern visual elements,
avatars, message bubbles, emojis, and beautiful styling.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QLabel, QFrame, QScrollArea, QSplitter, QToolButton, QMenu,
    QListWidget, QListWidgetItem, QApplication, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QSize
from PyQt6.QtGui import (
    QFont, QColor, QPixmap, QIcon, QPainter, QBrush, QPen,
    QTextCursor, QTextCharFormat, QKeySequence, QShortcut
)

# Import visual enhancements
from ui.visual_enhancements import (
    VisualEnhancements, AvatarWidget, MessageBubble, CodeBlockWidget,
    ModernFonts, IconManager, EmojiManager
)

# Import error handling
from utils.error_handler import error_handler, ErrorSeverity, ErrorCategory


class EnhancedMessageWidget(QWidget):
    """Enhanced message widget with avatar and bubble."""
    
    def __init__(self, message: str, sender: str = "user", timestamp: str = None, 
                 avatar_path: str = None, message_type: str = "text"):
        super().__init__()
        self.message = message
        self.sender = sender
        self.timestamp = timestamp or datetime.now().strftime("%H:%M")
        self.avatar_path = avatar_path
        self.message_type = message_type
        self.setup_message()
    
    @error_handler(ErrorCategory.UI, "Failed to setup enhanced message")
    def setup_message(self):
        """Setup the enhanced message widget."""
        try:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(8, 4, 8, 4)
            layout.setSpacing(8)
            
            # Avatar
            if self.sender == "user":
                avatar = AvatarWidget(self.avatar_path, 32, True)
                layout.addWidget(avatar)
            
            # Message content
            content_widget = self.create_message_content()
            layout.addWidget(content_widget, 1)
            
            # Avatar for assistant
            if self.sender == "assistant":
                avatar = AvatarWidget(self.avatar_path, 32, True)
                layout.addWidget(avatar)
            
            # Apply styling
            self.setStyleSheet("""
                QWidget {
                    background: transparent;
                }
            """)
            
        except Exception as e:
            print(f"Error setting up message: {e}")
    
    def create_message_content(self) -> QWidget:
        """Create the message content widget."""
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        
        if self.message_type == "code":
            # Code block
            code_widget = CodeBlockWidget(self.message, "python")
            content_layout.addWidget(code_widget)
        else:
            # Text message bubble
            bubble = MessageBubble(self.message, self.sender, self.timestamp)
            content_layout.addWidget(bubble)
        
        return content_widget


class EmojiPicker(QWidget):
    """Emoji picker widget for chat input."""
    
    emoji_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.emoji_manager = EmojiManager()
        self.setup_emoji_picker()
    
    @error_handler(ErrorCategory.UI, "Failed to setup emoji picker")
    def setup_emoji_picker(self):
        """Setup the emoji picker widget."""
        try:
            self.setFixedSize(300, 200)
            self.setWindowFlags(Qt.WindowType.Popup)
            
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(4)
            
            # Header
            header = QLabel("😊 Emojis")
            header.setFont(ModernFonts().get_font('primary', 12, 'bold'))
            header.setStyleSheet("color: #ffffff; padding: 4px;")
            layout.addWidget(header)
            
            # Emoji grid
            emoji_grid = QHBoxLayout()
            emoji_grid.setSpacing(4)
            
            # Add common emojis
            common_emojis = ['😊', '😂', '❤️', '👍', '🎉', '🔥', '⚡', '✨', '💡', '🤔']
            
            for emoji in common_emojis:
                emoji_btn = QPushButton(emoji)
                emoji_btn.setFixedSize(32, 32)
                emoji_btn.setStyleSheet("""
                    QPushButton {
                        font-size: 16px;
                        border: 1px solid #555;
                        border-radius: 4px;
                        background: #2b2b2b;
                        color: white;
                    }
                    QPushButton:hover {
                        background: #0078d4;
                        border-color: #0078d4;
                    }
                """)
                emoji_btn.clicked.connect(lambda checked, e=emoji: self.emoji_selected.emit(e))
                emoji_grid.addWidget(emoji_btn)
            
            layout.addLayout(emoji_grid)
            
            # Apply styling
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    border: 1px solid #555;
                    border-radius: 8px;
                }
            """)
            
        except Exception as e:
            print(f"Error setting up emoji picker: {e}")
    
    def show_at_position(self, pos):
        """Show the emoji picker at a specific position."""
        self.move(pos)
        self.show()


class EnhancedChatInput(QWidget):
    """Enhanced chat input with emoji picker and file attachment."""
    
    message_sent = pyqtSignal(str)
    file_attached = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.emoji_picker = None
        self.setup_input_widget()
    
    @error_handler(ErrorCategory.UI, "Failed to setup enhanced chat input")
    def setup_input_widget(self):
        """Setup the enhanced chat input widget."""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(8)
            
            # Input area
            input_layout = QHBoxLayout()
            input_layout.setSpacing(8)
            
            # Emoji button
            self.emoji_btn = QPushButton("😊")
            self.emoji_btn.setFixedSize(40, 40)
            self.emoji_btn.setStyleSheet("""
                QPushButton {
                    font-size: 18px;
                    border: 2px solid #555;
                    border-radius: 20px;
                    background: #2b2b2b;
                    color: white;
                }
                QPushButton:hover {
                    border-color: #0078d4;
                    background: #0078d4;
                }
            """)
            self.emoji_btn.clicked.connect(self.show_emoji_picker)
            input_layout.addWidget(self.emoji_btn)
            
            # File attachment button
            self.attach_btn = QPushButton("📎")
            self.attach_btn.setFixedSize(40, 40)
            self.attach_btn.setStyleSheet("""
                QPushButton {
                    font-size: 18px;
                    border: 2px solid #555;
                    border-radius: 20px;
                    background: #2b2b2b;
                    color: white;
                }
                QPushButton:hover {
                    border-color: #0078d4;
                    background: #0078d4;
                }
            """)
            self.attach_btn.clicked.connect(self.attach_file)
            input_layout.addWidget(self.attach_btn)
            
            # Text input
            self.text_input = QLineEdit()
            self.text_input.setPlaceholderText("💭 Type your message here...")
            self.text_input.setFont(ModernFonts().get_font('primary', 12))
            self.text_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2b2b2b;
                    border: 2px solid #555;
                    border-radius: 20px;
                    padding: 10px 16px;
                    color: white;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #0078d4;
                    box-shadow: 0 0 10px #0078d4;
                }
            """)
            self.text_input.returnPressed.connect(self.send_message)
            input_layout.addWidget(self.text_input, 1)
            
            # Send button
            self.send_btn = QPushButton("📤")
            self.send_btn.setFixedSize(40, 40)
            self.send_btn.setStyleSheet("""
                QPushButton {
                    font-size: 18px;
                    border: 2px solid #0078d4;
                    border-radius: 20px;
                    background: #0078d4;
                    color: white;
                }
                QPushButton:hover {
                    background: #106ebe;
                    border-color: #106ebe;
                    box-shadow: 0 0 10px #0078d4;
                }
                QPushButton:pressed {
                    background: #005a9e;
                    border-color: #005a9e;
                }
            """)
            self.send_btn.clicked.connect(self.send_message)
            input_layout.addWidget(self.send_btn)
            
            layout.addLayout(input_layout)
            
            # Character counter
            self.char_counter = QLabel("0/1000")
            self.char_counter.setFont(ModernFonts().get_font('secondary', 10))
            self.char_counter.setStyleSheet("color: #888; padding: 4px;")
            self.char_counter.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(self.char_counter)
            
            # Connect text change signal
            self.text_input.textChanged.connect(self.update_char_counter)
            
        except Exception as e:
            print(f"Error setting up chat input: {e}")
    
    def show_emoji_picker(self):
        """Show the emoji picker."""
        if not self.emoji_picker:
            self.emoji_picker = EmojiPicker(self)
            self.emoji_picker.emoji_selected.connect(self.insert_emoji)
        
        # Position the picker above the emoji button
        pos = self.emoji_btn.mapToGlobal(self.emoji_btn.rect().bottomLeft())
        pos.setY(pos.y() - 200)  # Show above the button
        self.emoji_picker.show_at_position(pos)
    
    def insert_emoji(self, emoji: str):
        """Insert an emoji into the text input."""
        current_text = self.text_input.text()
        cursor_pos = self.text_input.cursorPosition()
        
        new_text = current_text[:cursor_pos] + emoji + current_text[cursor_pos:]
        self.text_input.setText(new_text)
        
        # Move cursor after the emoji
        self.text_input.setCursorPosition(cursor_pos + len(emoji))
        self.text_input.setFocus()
    
    def attach_file(self):
        """Open file dialog for attachment."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach File", "", "All Files (*.*)"
        )
        if file_path:
            self.file_attached.emit(file_path)
    
    def send_message(self):
        """Send the current message."""
        message = self.text_input.text().strip()
        if message:
            self.message_sent.emit(message)
            self.text_input.clear()
    
    def update_char_counter(self):
        """Update the character counter."""
        current_length = len(self.text_input.text())
        max_length = 1000
        self.char_counter.setText(f"{current_length}/{max_length}")
        
        # Change color based on length
        if current_length > max_length * 0.9:
            self.char_counter.setStyleSheet("color: #ff6b6b; padding: 4px;")
        elif current_length > max_length * 0.7:
            self.char_counter.setStyleSheet("color: #ffaa00; padding: 4px;")
        else:
            self.char_counter.setStyleSheet("color: #888; padding: 4px;")


class EnhancedChatWidget(QWidget):
    """Enhanced chat widget with modern visual elements."""
    
    message_sent = pyqtSignal(str)
    file_attached = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.visual_enhancements = VisualEnhancements()
        self.icon_manager = IconManager()
        self.emoji_manager = EmojiManager()
        self.messages = []
        self.setup_chat_widget()
    
    @error_handler(ErrorCategory.UI, "Failed to setup enhanced chat widget")
    def setup_chat_widget(self):
        """Setup the enhanced chat widget."""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Chat header
            header = self.create_chat_header()
            layout.addWidget(header)
            
            # Messages area
            self.messages_area = self.create_messages_area()
            layout.addWidget(self.messages_area, 1)
            
            # Chat input
            self.chat_input = EnhancedChatInput()
            self.chat_input.message_sent.connect(self.handle_message_sent)
            self.chat_input.file_attached.connect(self.handle_file_attached)
            layout.addWidget(self.chat_input)
            
            # Apply styling
            self.setStyleSheet(self.visual_enhancements.get_chat_stylesheet())
            
        except Exception as e:
            print(f"Error setting up chat widget: {e}")
    
    def create_chat_header(self) -> QWidget:
        """Create the chat header widget."""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2b2b2b, stop:1 #3a3a3a);
                border-bottom: 1px solid #555;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        
        # Chat icon and title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        chat_icon = QLabel("💬")
        chat_icon.setFont(ModernFonts().get_font('primary', 20))
        title_layout.addWidget(chat_icon)
        
        title = QLabel("The Oracle AI Assistant")
        title.setFont(ModernFonts().get_header_font())
        title.setStyleSheet("color: #ffffff;")
        title_layout.addWidget(title)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        # Status indicator
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        
        status_dot = QLabel("●")
        status_dot.setFont(ModernFonts().get_font('primary', 12))
        status_dot.setStyleSheet("color: #00ff00;")
        status_layout.addWidget(status_dot)
        
        status_text = QLabel("Online")
        status_text.setFont(ModernFonts().get_font('secondary', 10))
        status_text.setStyleSheet("color: #888;")
        status_layout.addWidget(status_text)
        
        layout.addLayout(status_layout)
        
        return header
    
    def create_messages_area(self) -> QWidget:
        """Create the messages area widget."""
        messages_widget = QWidget()
        messages_layout = QVBoxLayout(messages_widget)
        messages_layout.setContentsMargins(16, 16, 16, 16)
        messages_layout.setSpacing(8)
        messages_layout.addStretch()
        
        # Scroll area for messages
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        # Messages container
        self.messages_container = QWidget()
        self.messages_container_layout = QVBoxLayout(self.messages_container)
        self.messages_container_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_container_layout.setSpacing(8)
        self.messages_container_layout.addStretch()
        
        scroll_area.setWidget(self.messages_container)
        messages_layout.addWidget(scroll_area)
        
        return messages_widget
    
    def add_message(self, message: str, sender: str = "user", message_type: str = "text", 
                   avatar_path: str = None, timestamp: str = None):
        """Add a message to the chat."""
        try:
            # Create message widget
            message_widget = EnhancedMessageWidget(
                message, sender, timestamp, avatar_path, message_type
            )
            
            # Add to layout (before the stretch)
            self.messages_container_layout.insertWidget(
                self.messages_container_layout.count() - 1, message_widget
            )
            
            # Store message
            self.messages.append({
                'message': message,
                'sender': sender,
                'type': message_type,
                'timestamp': timestamp or datetime.now().strftime("%H:%M"),
                'widget': message_widget
            })
            
            # Scroll to bottom
            QTimer.singleShot(100, self.scroll_to_bottom)
            
        except Exception as e:
            print(f"Error adding message: {e}")
    
    def scroll_to_bottom(self):
        """Scroll the messages area to the bottom."""
        try:
            scroll_area = self.messages_area.findChild(QScrollArea)
            if scroll_area:
                scroll_area.verticalScrollBar().setValue(
                    scroll_area.verticalScrollBar().maximum()
                )
        except Exception as e:
            print(f"Error scrolling to bottom: {e}")
    
    def handle_message_sent(self, message: str):
        """Handle message sent from input."""
        self.message_sent.emit(message)
    
    def handle_file_attached(self, file_path: str):
        """Handle file attachment."""
        self.file_attached.emit(file_path)
    
    def clear_messages(self):
        """Clear all messages."""
        try:
            # Remove all message widgets
            for i in reversed(range(self.messages_container_layout.count() - 1)):
                widget = self.messages_container_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # Clear messages list
            self.messages.clear()
            
        except Exception as e:
            print(f"Error clearing messages: {e}")
    
    def get_message_count(self) -> int:
        """Get the number of messages."""
        return len(self.messages)
    
    def get_last_message(self) -> Optional[Dict]:
        """Get the last message."""
        return self.messages[-1] if self.messages else None


# Test function
def test_enhanced_chat_widget():
    """Test the enhanced chat widget."""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    
    # Create and show the enhanced chat widget
    chat_widget = EnhancedChatWidget()
    chat_widget.resize(800, 600)
    chat_widget.show()
    
    # Add some test messages
    chat_widget.add_message("Hello! How can I help you today? 🤖", "assistant")
    chat_widget.add_message("Hi! I need help with Python programming. 💻", "user")
    chat_widget.add_message("Sure! I'd be happy to help with Python. Here's a simple example:", "assistant")
    
    # Add a code block
    code_example = '''def hello_world():
    print("Hello, World!")
    return "Success!"

# Call the function
result = hello_world()'''
    chat_widget.add_message(code_example, "assistant", "code")
    
    return app.exec()


if __name__ == '__main__':
    test_enhanced_chat_widget() 
