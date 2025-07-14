# ui/visual_enhancements.py
"""
Visual Enhancements for The Oracle AI Assistant
Author: AI Assistant
Date: 2024-12-19

This module provides comprehensive visual enhancements including:
- Modern UI elements with icons and emojis
- Glowing effects and animations
- Beautiful fonts and styling
- Avatars and message bubbles
- Graphical borders for code blocks
- Enhanced chat interface
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QFrame, QTextEdit, QLineEdit,
    QVBoxLayout, QHBoxLayout, QApplication, QStyleFactory
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal
from PyQt6.QtGui import (
    QFont, QColor, QPixmap, QIcon, QPainter, QBrush, QPen,
    QLinearGradient, QRadialGradient, QFontDatabase, QPalette
)

# Import error handling
from utils.error_handler import error_handler, ErrorSeverity, ErrorCategory


@dataclass
class VisualTheme:
    """Visual theme configuration."""
    name: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    border_color: str
    glow_color: str
    font_family: str
    font_size: int


class IconManager:
    """Manages icons from the Unused_Icons folder."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.icons_path = self.project_root / 'icons' / 'Unused_Icons'
        self.icons_cache = {}
        self.load_available_icons()
    
    @error_handler(ErrorCategory.UI, "Failed to load available icons")
    def load_available_icons(self):
        """Load all available icons from the Unused_Icons folder."""
        try:
            if not self.icons_path.exists():
                print(f"Warning: Icons path not found: {self.icons_path}")
                return
            
            # Load all PNG files
            for icon_file in self.icons_path.rglob("*.png"):
                icon_name = icon_file.stem
                self.icons_cache[icon_name] = str(icon_file)
            
            print(f"Loaded {len(self.icons_cache)} icons from {self.icons_path}")
            
        except Exception as e:
            print(f"Error loading icons: {e}")
    
    def get_icon(self, icon_name: str, size: int = 32) -> Optional[QIcon]:
        """Get an icon by name with specified size."""
        try:
            if icon_name in self.icons_cache:
                icon_path = self.icons_cache[icon_name]
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    return QIcon(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            # Fallback to default icon
            return self.get_default_icon(size)
            
        except Exception as e:
            print(f"Error loading icon {icon_name}: {e}")
            return self.get_default_icon(size)
    
    def get_default_icon(self, size: int = 32) -> QIcon:
        """Get a default icon when the requested icon is not found."""
        # Create a simple colored square as default icon
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(100, 100, 100))
        return QIcon(pixmap)
    
    def get_available_icons(self) -> List[str]:
        """Get list of available icon names."""
        return list(self.icons_cache.keys())


class EmojiManager:
    """Manages emojis and fun text elements."""
    
    def __init__(self):
        self.emojis = {
            # Chat and communication
            'chat': '💬', 'message': '💭', 'thought': '💭', 'speech': '💬',
            'user': '👤', 'assistant': '🤖', 'robot': '🤖', 'ai': '🧠',
            
            # Actions
            'send': '📤', 'receive': '📥', 'attach': '📎', 'download': '⬇️',
            'upload': '⬆️', 'save': '💾', 'delete': '🗑️', 'edit': '✏️',
            'search': '🔍', 'filter': '🔧', 'settings': '⚙️', 'help': '❓',
            
            # Status
            'success': '✅', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️',
            'loading': '⏳', 'done': '🎉', 'processing': '⚡', 'waiting': '⏰',
            
            # Features
            'tag': '🏷️', 'bookmark': '🔖', 'star': '⭐', 'heart': '❤️',
            'lightning': '⚡', 'fire': '🔥', 'sparkles': '✨', 'rainbow': '🌈',
            'brain': '🧠', 'magic': '🔮', 'crystal': '💎', 'diamond': '💠',
            
            # Navigation
            'home': '🏠', 'back': '⬅️', 'forward': '➡️', 'up': '⬆️', 'down': '⬇️',
            'menu': '☰', 'close': '❌', 'minimize': '➖', 'maximize': '➕',
            
            # Tools
            'code': '💻', 'file': '📄', 'folder': '📁', 'image': '🖼️',
            'video': '🎥', 'audio': '🎵', 'document': '📋', 'link': '🔗',
            
            # Emotions
            'happy': '😊', 'sad': '😢', 'excited': '🤩', 'surprised': '😲',
            'thinking': '🤔', 'confused': '😕', 'wink': '😉', 'cool': '😎'
        }
    
    def get_emoji(self, name: str) -> str:
        """Get an emoji by name."""
        return self.emojis.get(name, '✨')
    
    def get_all_emojis(self) -> Dict[str, str]:
        """Get all available emojis."""
        return self.emojis.copy()


class GlowEffect:
    """Creates glowing effects for UI elements."""
    
    def __init__(self, color: str = "#0078d4", intensity: int = 10):
        self.color = color
        self.intensity = intensity
    
    def get_glow_stylesheet(self, element: str = "QWidget") -> str:
        """Get CSS stylesheet for glowing effect."""
        return f"""
        {element} {{
            border: 2px solid {self.color};
            border-radius: 8px;
            background: qradialgradient(
                cx: 0.5, cy: 0.5, radius: 1,
                stop: 0 rgba(0, 120, 212, 0.1),
                stop: 0.5 rgba(0, 120, 212, 0.05),
                stop: 1 rgba(0, 120, 212, 0)
            );
            box-shadow: 0 0 {self.intensity}px {self.color};
        }}
        """
    
    def get_button_glow(self, base_color: str = "#0078d4") -> str:
        """Get glowing button stylesheet."""
        return f"""
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {base_color}, stop:1 {self._darken_color(base_color, 0.8)});
            border: none;
            border-radius: 15px;
            color: white;
            font-weight: bold;
            padding: 8px 16px;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self._lighten_color(base_color, 1.2)}, stop:1 {base_color});
            box-shadow: 0 0 15px {base_color};
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {self._darken_color(base_color, 0.6)}, stop:1 {self._darken_color(base_color, 0.8)});
        }}
        """
    
    def _lighten_color(self, color: str, factor: float) -> str:
        """Lighten a hex color by a factor."""
        # Simple color lightening - in production, use proper color manipulation
        return color
    
    def _darken_color(self, color: str, factor: float) -> str:
        """Darken a hex color by a factor."""
        # Simple color darkening - in production, use proper color manipulation
        return color


class ModernFonts:
    """Manages modern, legible fonts."""
    
    def __init__(self):
        self.fonts = {
            'primary': 'Segoe UI',
            'secondary': 'Calibri',
            'monospace': 'Consolas',
            'fun': 'Comic Sans MS',
            'elegant': 'Georgia',
            'modern': 'Arial'
        }
    
    def get_font(self, font_type: str = 'primary', size: int = 12, weight: str = 'normal') -> QFont:
        """Get a font with specified type, size, and weight."""
        font_name = self.fonts.get(font_type, self.fonts['primary'])
        font = QFont(font_name, size)
        
        if weight == 'bold':
            font.setWeight(QFont.Weight.Bold)
        elif weight == 'light':
            font.setWeight(QFont.Weight.Light)
        
        return font
    
    def get_chat_font(self) -> QFont:
        """Get font for chat messages."""
        return self.get_font('primary', 11)
    
    def get_code_font(self) -> QFont:
        """Get font for code blocks."""
        return self.get_font('monospace', 10)
    
    def get_header_font(self) -> QFont:
        """Get font for headers."""
        return self.get_font('primary', 16, 'bold')
    
    def get_button_font(self) -> QFont:
        """Get font for buttons."""
        return self.get_font('primary', 10, 'bold')


class AvatarWidget(QLabel):
    """Custom avatar widget with glowing effects."""
    
    def __init__(self, avatar_path: str = None, size: int = 40, is_online: bool = True):
        super().__init__()
        self.size = size
        self.is_online = is_online
        self.avatar_path = avatar_path
        self.setup_avatar()
    
    def setup_avatar(self):
        """Setup the avatar display."""
        self.setFixedSize(self.size, self.size)
        
        if self.avatar_path and os.path.exists(self.avatar_path):
            pixmap = QPixmap(self.avatar_path)
        else:
            # Create default avatar
            pixmap = self.create_default_avatar()
        
        # Scale to size
        scaled_pixmap = pixmap.scaled(
            self.size, self.size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
        self.setStyleSheet(self.get_avatar_stylesheet())
    
    def create_default_avatar(self) -> QPixmap:
        """Create a default avatar pixmap."""
        pixmap = QPixmap(self.size, self.size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circular background
        gradient = QRadialGradient(self.size//2, self.size//2, self.size//2)
        gradient.setColorAt(0, QColor(100, 150, 255))
        gradient.setColorAt(1, QColor(50, 100, 200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawEllipse(2, 2, self.size-4, self.size-4)
        
        # Draw user icon
        painter.setFont(QFont("Arial", self.size//3, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "👤")
        
        painter.end()
        return pixmap
    
    def get_avatar_stylesheet(self) -> str:
        """Get stylesheet for avatar with online indicator."""
        online_color = "#00ff00" if self.is_online else "#ff0000"
        return f"""
        QLabel {{
            border: 3px solid {online_color};
            border-radius: {self.size//2}px;
            background: transparent;
        }}
        QLabel:hover {{
            border-color: #0078d4;
            box-shadow: 0 0 10px {online_color};
        }}
        """


class MessageBubble(QFrame):
    """Custom message bubble with modern styling."""
    
    def __init__(self, message: str, sender: str = "user", timestamp: str = None):
        super().__init__()
        self.message = message
        self.sender = sender
        self.timestamp = timestamp
        self.setup_bubble()
    
    def setup_bubble(self):
        """Setup the message bubble."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Message text
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setFont(ModernFonts().get_chat_font())
        message_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(message_label)
        
        # Timestamp
        if self.timestamp:
            time_label = QLabel(self.timestamp)
            time_label.setFont(ModernFonts().get_font('secondary', 8))
            time_label.setStyleSheet("color: #888888;")
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(time_label)
        
        # Apply styling
        self.setStyleSheet(self.get_bubble_stylesheet())
    
    def get_bubble_stylesheet(self) -> str:
        """Get stylesheet for message bubble."""
        if self.sender == "user":
            return """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d4, stop:1 #106ebe);
                border: none;
                border-radius: 15px;
                margin: 4px 0px;
                padding: 8px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #106ebe, stop:1 #0078d4);
                box-shadow: 0 2px 8px rgba(0, 120, 212, 0.3);
            }
            """
        else:
            return """
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2b2b2b, stop:1 #3a3a3a);
                border: 1px solid #555555;
                border-radius: 15px;
                margin: 4px 0px;
                padding: 8px;
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3a3a3a, stop:1 #2b2b2b);
                border-color: #0078d4;
                box-shadow: 0 2px 8px rgba(0, 120, 212, 0.2);
            }
            """


class CodeBlockWidget(QFrame):
    """Enhanced code block with graphical borders."""
    
    def __init__(self, code: str, language: str = "python"):
        super().__init__()
        self.code = code
        self.language = language
        self.setup_code_block()
    
    def setup_code_block(self):
        """Setup the code block display."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Language header
        header = QLabel(f"📝 {self.language.upper()}")
        header.setFont(ModernFonts().get_font('monospace', 10, 'bold'))
        header.setStyleSheet("""
            QLabel {
                background: #1e1e1e;
                color: #ffffff;
                padding: 4px 8px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid #333333;
            }
        """)
        layout.addWidget(header)
        
        # Code content
        code_text = QTextEdit()
        code_text.setPlainText(self.code)
        code_text.setFont(ModernFonts().get_code_font())
        code_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: none;
                padding: 8px;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                selection-background-color: #264f78;
            }
        """)
        code_text.setReadOnly(True)
        code_text.setMaximumHeight(300)
        layout.addWidget(code_text)
        
        # Apply overall styling
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #0078d4;
                border-radius: 8px;
                background: #1e1e1e;
                margin: 8px 0px;
            }
            QFrame:hover {
                border-color: #106ebe;
                box-shadow: 0 0 10px rgba(0, 120, 212, 0.3);
            }
        """)


class VisualEnhancements:
    """Main class for managing all visual enhancements."""
    
    def __init__(self):
        self.icon_manager = IconManager()
        self.emoji_manager = EmojiManager()
        self.glow_effect = GlowEffect()
        self.fonts = ModernFonts()
        self.current_theme = self.get_default_theme()
    
    def get_default_theme(self) -> VisualTheme:
        """Get the default visual theme."""
        return VisualTheme(
            name="Modern Dark",
            primary_color="#0078d4",
            secondary_color="#106ebe",
            accent_color="#ff6b6b",
            background_color="#1e1e1e",
            text_color="#ffffff",
            border_color="#555555",
            glow_color="#0078d4",
            font_family="Segoe UI",
            font_size=12
        )
    
    def apply_theme(self, theme: VisualTheme):
        """Apply a visual theme to the application."""
        self.current_theme = theme
        
        # Apply to QApplication
        app = QApplication.instance()
        if app:
            app.setStyle(QStyleFactory.create("Fusion"))
            
            # Create custom palette
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(theme.background_color))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.Base, QColor(theme.background_color))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.secondary_color))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme.background_color))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.Text, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.Button, QColor(theme.primary_color))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.text_color))
            palette.setColor(QPalette.ColorRole.Link, QColor(theme.accent_color))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(theme.primary_color))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme.text_color))
            
            app.setPalette(palette)
    
    def get_enhanced_button_stylesheet(self, button_type: str = "primary") -> str:
        """Get enhanced button stylesheet."""
        base_styles = {
            "primary": self.glow_effect.get_button_glow("#0078d4"),
            "secondary": self.glow_effect.get_button_glow("#6c757d"),
            "success": self.glow_effect.get_button_glow("#28a745"),
            "danger": self.glow_effect.get_button_glow("#dc3545"),
            "warning": self.glow_effect.get_button_glow("#ffc107")
        }
        
        return base_styles.get(button_type, base_styles["primary"])
    
    def create_enhanced_button(self, text: str, icon_name: str = None, button_type: str = "primary") -> QPushButton:
        """Create an enhanced button with icon and styling."""
        button = QPushButton(text)
        
        if icon_name:
            icon = self.icon_manager.get_icon(icon_name, 16)
            if icon:
                button.setIcon(icon)
        
        button.setFont(self.fonts.get_button_font())
        button.setStyleSheet(self.get_enhanced_button_stylesheet(button_type))
        
        return button
    
    def get_chat_stylesheet(self) -> str:
        """Get enhanced chat stylesheet."""
        return f"""
        QWidget {{
            background-color: {self.current_theme.background_color};
            color: {self.current_theme.text_color};
            font-family: {self.current_theme.font_family};
            font-size: {self.current_theme.font_size}px;
        }}
        
        QTextEdit {{
            background-color: #2b2b2b;
            border: 1px solid {self.current_theme.border_color};
            border-radius: 8px;
            padding: 8px;
            color: {self.current_theme.text_color};
        }}
        
        QLineEdit {{
            background-color: #2b2b2b;
            border: 1px solid {self.current_theme.border_color};
            border-radius: 8px;
            padding: 8px;
            color: {self.current_theme.text_color};
        }}
        
        QLineEdit:focus {{
            border-color: {self.current_theme.primary_color};
            box-shadow: 0 0 5px {self.current_theme.glow_color};
        }}
        
        QScrollBar:vertical {{
            background-color: #2b2b2b;
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self.current_theme.primary_color};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.current_theme.secondary_color};
        }}
        """


# Global instance
visual_enhancements = VisualEnhancements() 
