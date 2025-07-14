"""
Theme-aware styling utilities for dialogs and components
"""

import os
from typing import Optional


def get_dialog_theme_styles(dark_theme: bool = True, icon_path: Optional[str] = None) -> str:
    """
    Get theme-aware styles for dialogs

    Args:
        dark_theme: Whether to use dark theme
        icon_path: Base path for icons (optional)

    Returns:
        QSS stylesheet string
    """

    if dark_theme:
        return """
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin: 10px 5px;
                padding-top: 15px;
            }

            QGroupBox::title {
                color: #4a9eff;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }

            QLabel {
                color: #ffffff;
            }

            QListWidget {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                selection-background-color: #4a9eff;
                selection-color: #ffffff;
            }

            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }

            QListWidget::item:hover {
                background-color: #4a4a4a;
            }

            QListWidget::item:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }

            QTextEdit, QPlainTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
            }

            QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #4a9eff;
                background-color: #404040;
            }

            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
            }

            QLineEdit:focus {
                border: 2px solid #4a9eff;
                background-color: #404040;
            }

            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
            }

            QComboBox:focus {
                border: 2px solid #4a9eff;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                image: none;
                border: none;
            }

            QPushButton {
                background-color: #4a9eff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                min-width: 80px;
            }

            QPushButton:hover {
                background-color: #5badff;
            }

            QPushButton:pressed {
                background-color: #3a8edf;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }

            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 4px;
                background-color: #3c3c3c;
            }

            QCheckBox::indicator:checked {
                background-color: #4a9eff;
                border-color: #4a9eff;
            }

            QCheckBox::indicator:hover {
                border-color: #4a9eff;
            }

            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
                border-radius: 5px;
            }

            QTabBar::tab {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                color: #ffffff;
            }

            QTabBar::tab:selected {
                background-color: #4a9eff;
                color: #ffffff;
            }

            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }

            QScrollArea {
                border: none;
                background-color: #2b2b2b;
            }

            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #4a9eff;
            }

            QFrame {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #3c3c3c;
            }

            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 8px;
                background-color: #3c3c3c;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background-color: #4a9eff;
                border: 1px solid #2b2b2b;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }

            QSlider::handle:horizontal:hover {
                background-color: #5badff;
            }

            QSpinBox, QDoubleSpinBox {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }

            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #4a9eff;
            }
        """
    else:
        # Light theme
        return """
            QDialog {
                background-color: #f5f5f5;
                color: #2d3748;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin: 10px 5px;
                padding-top: 15px;
                background-color: #ffffff;
            }

            QGroupBox::title {
                color: #4299e1;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }

            QLabel {
                color: #2d3748;
            }

            QListWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                color: #2d3748;
                selection-background-color: #4299e1;
                selection-color: #ffffff;
            }

            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }

            QListWidget::item:hover {
                background-color: #f7fafc;
            }

            QListWidget::item:selected {
                background-color: #4299e1;
                color: #ffffff;
            }

            QTextEdit, QPlainTextEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                padding: 8px;
                color: #2d3748;
                font-family: 'Consolas', 'Monaco', monospace;
            }

            QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #4299e1;
                background-color: #f7fafc;
            }

            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                padding: 8px;
                color: #2d3748;
            }

            QLineEdit:focus {
                border: 2px solid #4299e1;
                background-color: #f7fafc;
            }

            QComboBox {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                padding: 8px;
                color: #2d3748;
            }

            QComboBox:focus {
                border: 2px solid #4299e1;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QComboBox::down-arrow {
                image: none;
                border: none;
            }

            QPushButton {
                background-color: #4299e1;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                min-width: 80px;
            }

            QPushButton:hover {
                background-color: #3182ce;
            }

            QPushButton:pressed {
                background-color: #2b6cb0;
            }

            QPushButton:disabled {
                background-color: #a0aec0;
                color: #718096;
            }

            QCheckBox {
                color: #2d3748;
                spacing: 8px;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #e2e8f0;
                border-radius: 4px;
                background-color: #ffffff;
            }

            QCheckBox::indicator:checked {
                background-color: #4299e1;
                border-color: #4299e1;
            }

            QCheckBox::indicator:hover {
                border-color: #4299e1;
            }

            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                background-color: #ffffff;
                border-radius: 5px;
            }

            QTabBar::tab {
                background-color: #f7fafc;
                border: 1px solid #e2e8f0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                color: #2d3748;
            }

            QTabBar::tab:selected {
                background-color: #4299e1;
                color: #ffffff;
            }

            QTabBar::tab:hover {
                background-color: #edf2f7;
            }

            QScrollArea {
                border: none;
                background-color: #ffffff;
            }

            QScrollBar:vertical {
                background-color: #f7fafc;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #cbd5e0;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #4299e1;
            }

            QFrame {
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                background-color: #ffffff;
            }

            QSlider::groove:horizontal {
                border: 1px solid #e2e8f0;
                height: 8px;
                background-color: #f7fafc;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background-color: #4299e1;
                border: 1px solid #ffffff;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }

            QSlider::handle:horizontal:hover {
                background-color: #3182ce;
            }

            QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                padding: 5px;
                color: #2d3748;
            }

            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #4299e1;
            }
        """


def get_message_box_styles(dark_theme: bool = True, message_type: str = "info") -> str:
    """
    Get styles for message boxes with appropriate icons

    Args:
        dark_theme: Whether to use dark theme
        message_type: Type of message (info, warning, error, success)

    Returns:
        QSS stylesheet string
    """

    # Color schemes for different message types
    type_colors = {
        "info": {
            "dark": {"bg": "#2b2b2b", "border": "#4a9eff", "text": "#ffffff"},
            "light": {"bg": "#f7fafc", "border": "#4299e1", "text": "#2d3748"}
        },
        "warning": {
            "dark": {"bg": "#2b2b2b", "border": "#f6ad55", "text": "#ffffff"},
            "light": {"bg": "#fffaf0", "border": "#ed8936", "text": "#2d3748"}
        },
        "error": {
            "dark": {"bg": "#2b2b2b", "border": "#fc8181", "text": "#ffffff"},
            "light": {"bg": "#fff5f5", "border": "#e53e3e", "text": "#2d3748"}
        },
        "success": {
            "dark": {"bg": "#2b2b2b", "border": "#68d391", "text": "#ffffff"},
            "light": {"bg": "#f0fff4", "border": "#38a169", "text": "#2d3748"}
        }
    }

    theme = "dark" if dark_theme else "light"
    colors = type_colors.get(message_type, type_colors["info"])[theme]

    return f"""
        QMessageBox {{
            background-color: {colors["bg"]};
            color: {colors["text"]};
            border: 2px solid {colors["border"]};
            border-radius: 8px;
        }}

        QMessageBox QLabel {{
            color: {colors["text"]};
            font-size: 14px;
        }}

        QMessageBox QPushButton {{
            background-color: {colors["border"]};
            color: {"#ffffff" if dark_theme else "#ffffff"};
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        }}

        QMessageBox QPushButton:hover {{
            background-color: {colors["border"]}88;
        }}

        QMessageBox QPushButton:pressed {{
            background-color: {colors["border"]}aa;
        }}
    """


def get_icon_path(icon_name: str, category: str = "general") -> str:
    """
    Get the path to an icon file

    Args:
        icon_name: Name of the icon file (without extension)
        category: Category folder (general, chat, toolbar, etc.)

    Returns:
        Path to the icon file
    """

    base_path = os.path.join(os.path.dirname(__file__), "..", "icons")
    icon_path = os.path.join(base_path, category, f"{icon_name}.png")

    if os.path.exists(icon_path):
        return icon_path

    # Fallback to general folder
    fallback_path = os.path.join(base_path, "general", f"{icon_name}.png")
    if os.path.exists(fallback_path):
        return fallback_path

    return ""


def create_themed_message_box(parent, title: str, message: str, message_type: str = "info",
                            dark_theme: bool = True, icon_name: Optional[str] = None):
    """
    Create a themed message box with appropriate styling and icons

    Args:
        parent: Parent widget
        title: Window title
        message: Message text
        message_type: Type of message (info, warning, error, success)
        dark_theme: Whether to use dark theme
        icon_name: Optional custom icon name

    Returns:
        QMessageBox instance
    """
    from PyQt6.QtWidgets import QMessageBox
    from PyQt6.QtGui import QPixmap

    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    # Set icon based on message type
    if icon_name:
        icon_path = get_icon_path(icon_name)
        if icon_path:
            msg_box.setIconPixmap(QPixmap(icon_path).scaled(48, 48))
    else:
        # Use default system icons or our custom ones
        icon_map = {
            "info": QMessageBox.Icon.Information,
            "warning": QMessageBox.Icon.Warning,
            "error": QMessageBox.Icon.Critical,
            "success": QMessageBox.Icon.Information
        }
        msg_box.setIcon(icon_map.get(message_type, QMessageBox.Icon.Information))

    # Apply theme styles
    msg_box.setStyleSheet(get_message_box_styles(dark_theme, message_type))

    return msg_box


class ThemeManager:
    """Theme management class for The Oracle application."""
    
    def __init__(self, dark_theme: bool = True):
        """
        Initialize theme manager.
        
        Args:
            dark_theme: Whether to use dark theme by default
        """
        self.dark_theme = dark_theme
        self.available_themes = ["dark", "light", "auto"]
        self.current_theme = "dark" if dark_theme else "light"
    
    def get_available_themes(self) -> list:
        """Get list of available themes."""
        return self.available_themes.copy()
    
    def get_theme_stylesheet(self, theme: str = None) -> str:
        """
        Get stylesheet for specified theme.
        
        Args:
            theme: Theme name (dark, light, auto)
            
        Returns:
            QSS stylesheet string
        """
        if theme is None:
            theme = self.current_theme
        
        if theme == "dark":
            return get_dialog_theme_styles(dark_theme=True)
        elif theme == "light":
            return get_dialog_theme_styles(dark_theme=False)
        elif theme == "auto":
            # Auto theme - use system preference
            return get_dialog_theme_styles(dark_theme=self.dark_theme)
        else:
            # Default to dark theme
            return get_dialog_theme_styles(dark_theme=True)
    
    def apply_theme(self, widget, theme: str = None):
        """
        Apply theme to a widget.
        
        Args:
            widget: Qt widget to apply theme to
            theme: Theme name (optional)
        """
        if theme:
            self.current_theme = theme
        
        stylesheet = self.get_theme_stylesheet(self.current_theme)
        widget.setStyleSheet(stylesheet)
    
    def set_theme(self, theme: str):
        """
        Set the current theme.
        
        Args:
            theme: Theme name
        """
        if theme in self.available_themes:
            self.current_theme = theme
        else:
            raise ValueError(f"Unknown theme: {theme}")
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.current_theme
    
    def is_dark_theme(self) -> bool:
        """Check if current theme is dark."""
        return self.current_theme == "dark"
    
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
