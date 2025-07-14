# ui/enhanced_theme_styles.py
"""
Enhanced Theme Styles for The Oracle AI Assistant
Author: AI Assistant
Date: 2024-12-19

This module provides enhanced theme styles with modern visual elements,
icons, emojis, glowing effects, and beautiful styling.
"""

from PyQt6.QtGui import QColor, QPalette, QFont
from PyQt6.QtWidgets import QApplication, QStyleFactory

from ui.visual_enhancements import VisualEnhancements, VisualTheme


class EnhancedThemeStyles:
    """Enhanced theme styles with modern visual elements."""
    
    def __init__(self):
        self.visual_enhancements = VisualEnhancements()
        self.setup_themes()
    
    def setup_themes(self):
        """Setup available themes."""
        self.themes = {
            "modern_dark": VisualTheme(
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
            ),
            "modern_light": VisualTheme(
                name="Modern Light",
                primary_color="#0078d4",
                secondary_color="#106ebe",
                accent_color="#ff6b6b",
                background_color="#ffffff",
                text_color="#000000",
                border_color="#e0e0e0",
                glow_color="#0078d4",
                font_family="Segoe UI",
                font_size=12
            ),
            "cyber_punk": VisualTheme(
                name="Cyber Punk",
                primary_color="#00ff88",
                secondary_color="#ff0088",
                accent_color="#ffaa00",
                background_color="#0a0a0a",
                text_color="#00ff88",
                border_color="#00ff88",
                glow_color="#00ff88",
                font_family="Consolas",
                font_size=12
            ),
            "ocean_blue": VisualTheme(
                name="Ocean Blue",
                primary_color="#0066cc",
                secondary_color="#0099ff",
                accent_color="#ff9933",
                background_color="#001122",
                text_color="#ffffff",
                border_color="#0066cc",
                glow_color="#0099ff",
                font_family="Segoe UI",
                font_size=12
            ),
            "sunset_orange": VisualTheme(
                name="Sunset Orange",
                primary_color="#ff6b35",
                secondary_color="#f7931e",
                accent_color="#ffd23f",
                background_color="#2c1810",
                text_color="#ffffff",
                border_color="#ff6b35",
                glow_color="#ff6b35",
                font_family="Segoe UI",
                font_size=12
            )
        }
    
    def apply_theme(self, theme_name: str = "modern_dark"):
        """Apply a theme to the application."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        self.visual_enhancements.apply_theme(theme)
        return theme
    
    def get_main_window_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get enhanced main window stylesheet."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QMainWindow {{
            background-color: {theme.background_color};
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QMenuBar {{
            background-color: {theme.background_color};
            color: {theme.text_color};
            border-bottom: 1px solid {theme.border_color};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 6px 12px;
            border-radius: 4px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {theme.primary_color};
            color: {theme.text_color};
        }}
        
        QMenu {{
            background-color: {theme.background_color};
            color: {theme.text_color};
            border: 1px solid {theme.border_color};
            border-radius: 6px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 6px 20px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {theme.primary_color};
            color: {theme.text_color};
        }}
        
        QStatusBar {{
            background-color: {theme.background_color};
            color: {theme.text_color};
            border-top: 1px solid {theme.border_color};
            padding: 4px;
        }}
        
        QToolBar {{
            background-color: {theme.background_color};
            border: none;
            spacing: 4px;
            padding: 4px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 6px;
            margin: 2px;
        }}
        
        QToolButton:hover {{
            background-color: {theme.primary_color};
            border-color: {theme.primary_color};
            box-shadow: 0 0 8px {theme.glow_color};
        }}
        
        QToolButton:pressed {{
            background-color: {theme.secondary_color};
            border-color: {theme.secondary_color};
        }}
        """
    
    def get_chat_widget_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get enhanced chat widget stylesheet."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QWidget {{
            background-color: {theme.background_color};
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QTextEdit {{
            background-color: #2b2b2b;
            border: 1px solid {theme.border_color};
            border-radius: 8px;
            padding: 12px;
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
            line-height: 1.4;
        }}
        
        QTextEdit:focus {{
            border-color: {theme.primary_color};
            box-shadow: 0 0 10px {theme.glow_color};
        }}
        
        QLineEdit {{
            background-color: #2b2b2b;
            border: 2px solid {theme.border_color};
            border-radius: 12px;
            padding: 12px 16px;
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QLineEdit:focus {{
            border-color: {theme.primary_color};
            box-shadow: 0 0 15px {theme.glow_color};
        }}
        
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {theme.primary_color}, stop:1 {theme.secondary_color});
            border: none;
            border-radius: 12px;
            color: {theme.text_color};
            font-weight: bold;
            padding: 10px 20px;
            font-size: {theme.font_size}px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {theme.secondary_color}, stop:1 {theme.primary_color});
            box-shadow: 0 0 15px {theme.glow_color};
            transform: translateY(-1px);
        }}
        
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {theme.secondary_color}, stop:1 {theme.primary_color});
            transform: translateY(1px);
        }}
        
        QScrollBar:vertical {{
            background-color: #2b2b2b;
            width: 14px;
            border-radius: 7px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {theme.primary_color};
            border-radius: 7px;
            min-height: 30px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {theme.secondary_color};
            box-shadow: 0 0 8px {theme.glow_color};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        """
    
    def get_panel_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get enhanced panel stylesheet."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.background_color}, stop:1 #2b2b2b);
            border: 1px solid {theme.border_color};
            border-radius: 10px;
            margin: 4px;
        }}
        
        QLabel {{
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QLabel[class="header"] {{
            font-size: {theme.font_size + 4}px;
            font-weight: bold;
            color: {theme.primary_color};
            padding: 8px;
        }}
        
        QListWidget {{
            background-color: transparent;
            border: none;
            outline: none;
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QListWidget::item {{
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 8px;
            margin: 2px 4px;
        }}
        
        QListWidget::item:hover {{
            background-color: {theme.primary_color}20;
            border-color: {theme.primary_color};
        }}
        
        QListWidget::item:selected {{
            background-color: {theme.primary_color}40;
            border-color: {theme.primary_color};
            box-shadow: 0 0 8px {theme.glow_color};
        }}
        
        QComboBox {{
            background-color: #2b2b2b;
            border: 2px solid {theme.border_color};
            border-radius: 8px;
            padding: 8px 12px;
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QComboBox:focus {{
            border-color: {theme.primary_color};
            box-shadow: 0 0 10px {theme.glow_color};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {theme.text_color};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: #2b2b2b;
            border: 1px solid {theme.border_color};
            border-radius: 6px;
            color: {theme.text_color};
            selection-background-color: {theme.primary_color};
        }}
        """
    
    def get_dialog_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get enhanced dialog stylesheet."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QDialog {{
            background-color: {theme.background_color};
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QDialog QLabel {{
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QDialog QLineEdit {{
            background-color: #2b2b2b;
            border: 2px solid {theme.border_color};
            border-radius: 8px;
            padding: 10px;
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QDialog QLineEdit:focus {{
            border-color: {theme.primary_color};
            box-shadow: 0 0 10px {theme.glow_color};
        }}
        
        QDialog QTextEdit {{
            background-color: #2b2b2b;
            border: 2px solid {theme.border_color};
            border-radius: 8px;
            padding: 10px;
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QDialog QTextEdit:focus {{
            border-color: {theme.primary_color};
            box-shadow: 0 0 10px {theme.glow_color};
        }}
        
        QDialog QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {theme.primary_color}, stop:1 {theme.secondary_color});
            border: none;
            border-radius: 10px;
            color: {theme.text_color};
            font-weight: bold;
            padding: 8px 16px;
            font-size: {theme.font_size}px;
            min-width: 80px;
        }}
        
        QDialog QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {theme.secondary_color}, stop:1 {theme.primary_color});
            box-shadow: 0 0 12px {theme.glow_color};
        }}
        
        QDialog QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {theme.secondary_color}, stop:1 {theme.primary_color});
        }}
        
        QDialog QPushButton[class="danger"] {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #dc3545, stop:1 #c82333);
        }}
        
        QDialog QPushButton[class="danger"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #c82333, stop:1 #dc3545);
            box-shadow: 0 0 12px #dc3545;
        }}
        """
    
    def get_code_block_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get enhanced code block stylesheet."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QFrame[class="code-block"] {{
            background-color: #1e1e1e;
            border: 2px solid {theme.primary_color};
            border-radius: 8px;
            margin: 8px 0px;
            padding: 0px;
        }}
        
        QFrame[class="code-block"]:hover {{
            border-color: {theme.secondary_color};
            box-shadow: 0 0 15px {theme.glow_color};
        }}
        
        QFrame[class="code-header"] {{
            background-color: #2d2d2d;
            border-bottom: 1px solid {theme.primary_color};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 6px 12px;
        }}
        
        QFrame[class="code-content"] {{
            background-color: #1e1e1e;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
            padding: 12px;
        }}
        
        QTextEdit[class="code-text"] {{
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: none;
            font-family: Consolas, Monaco, monospace;
            font-size: 11px;
            line-height: 1.4;
            selection-background-color: #264f78;
        }}
        """
    
    def get_animation_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get stylesheet with animation effects."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QPushButton {{
            transition: all 0.3s ease;
        }}
        
        QPushButton:hover {{
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }}
        
        QPushButton:pressed {{
            transform: translateY(0px);
            transition: all 0.1s ease;
        }}
        
        QLineEdit, QTextEdit {{
            transition: all 0.3s ease;
        }}
        
        QLineEdit:focus, QTextEdit:focus {{
            transition: all 0.3s ease;
        }}
        """
    
    def get_emoji_stylesheet(self) -> str:
        """Get stylesheet for emoji elements."""
        return """
        QLabel[class="emoji"] {
            font-size: 16px;
            padding: 4px;
            border-radius: 4px;
        }
        
        QLabel[class="emoji"]:hover {
            background-color: rgba(255, 255, 255, 0.1);
            transform: scale(1.1);
        }
        
        QPushButton[class="emoji-button"] {
            font-size: 18px;
            padding: 8px;
            border-radius: 8px;
            background-color: transparent;
            border: 1px solid transparent;
        }
        
        QPushButton[class="emoji-button"]:hover {
            background-color: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }
        """
    
    def get_avatar_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get stylesheet for avatar elements."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QLabel[class="avatar"] {{
            border: 3px solid {theme.primary_color};
            border-radius: 50%;
            background-color: transparent;
            padding: 2px;
        }}
        
        QLabel[class="avatar"]:hover {{
            border-color: {theme.secondary_color};
            box-shadow: 0 0 15px {theme.glow_color};
            transform: scale(1.05);
        }}
        
        QLabel[class="avatar-online"] {{
            border-color: #00ff00;
        }}
        
        QLabel[class="avatar-offline"] {{
            border-color: #ff0000;
        }}
        """
    
    def get_message_bubble_stylesheet(self, theme_name: str = "modern_dark") -> str:
        """Get stylesheet for message bubbles."""
        theme = self.themes.get(theme_name, self.themes["modern_dark"])
        
        return f"""
        QFrame[class="message-bubble-user"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.primary_color}, stop:1 {theme.secondary_color});
            border: none;
            border-radius: 18px;
            margin: 4px 0px;
            padding: 12px 16px;
        }}
        
        QFrame[class="message-bubble-user"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {theme.secondary_color}, stop:1 {theme.primary_color});
            box-shadow: 0 4px 12px rgba(0, 120, 212, 0.3);
        }}
        
        QFrame[class="message-bubble-assistant"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #2b2b2b, stop:1 #3a3a3a);
            border: 1px solid {theme.border_color};
            border-radius: 18px;
            margin: 4px 0px;
            padding: 12px 16px;
        }}
        
        QFrame[class="message-bubble-assistant"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3a3a3a, stop:1 #2b2b2b);
            border-color: {theme.primary_color};
            box-shadow: 0 4px 12px rgba(0, 120, 212, 0.2);
        }}
        
        QLabel[class="message-text"] {{
            color: {theme.text_color};
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
            line-height: 1.4;
        }}
        
        QLabel[class="message-time"] {{
            color: rgba(255, 255, 255, 0.6);
            font-family: {theme.font_family};
            font-size: {theme.font_size - 2}px;
        }}
        """


# Global instance
enhanced_theme_styles = EnhancedThemeStyles() 
