"""
Icon utility for The Oracle application.
Provides fallback icons when requested icons are not found.
"""

import os
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtCore import Qt, QSize


class IconManager:
    """Manages icon loading with fallbacks"""

    def __init__(self, base_path=""):
        self.base_path = base_path or os.path.join(os.path.dirname(__file__), "..", "icons")
        self.icon_cache = {}

    def get_icon(self, icon_name: str, size: QSize = QSize(16, 16)) -> QIcon:
        """Get an icon with fallback to generated icon if not found"""
        cache_key = f"{icon_name}_{size.width()}x{size.height()}"

        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        # Try to load the icon from various paths
        possible_paths = [
            os.path.join(self.base_path, icon_name),
            os.path.join(self.base_path, f"{icon_name}.png"),
            os.path.join(self.base_path, "general", icon_name),
            os.path.join(self.base_path, "general", f"{icon_name}.png"),
            os.path.join(self.base_path, "toolbar", icon_name),
            os.path.join(self.base_path, "toolbar", f"{icon_name}.png"),
            os.path.join(self.base_path, "buttons", icon_name),
            os.path.join(self.base_path, "buttons", f"{icon_name}.png"),
            os.path.join(self.base_path, "actions", icon_name),
            os.path.join(self.base_path, "actions", f"{icon_name}.png"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                icon = QIcon(path)
                self.icon_cache[cache_key] = icon
                return icon

        # Generate fallback icon
        icon = self._generate_fallback_icon(icon_name, size)
        self.icon_cache[cache_key] = icon
        return icon

    def _generate_fallback_icon(self, icon_name: str, size: QSize) -> QIcon:
        """Generate a fallback icon when the requested icon is not found"""
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Choose color based on icon name
        color = self._get_icon_color(icon_name)

        # Draw a simple shape based on icon name
        if "folder" in icon_name.lower():
            self._draw_folder_icon(painter, size, color)
        elif "file" in icon_name.lower() or "document" in icon_name.lower():
            self._draw_file_icon(painter, size, color)
        elif "search" in icon_name.lower():
            self._draw_search_icon(painter, size, color)
        elif "settings" in icon_name.lower() or "config" in icon_name.lower():
            self._draw_settings_icon(painter, size, color)
        elif "refresh" in icon_name.lower() or "reload" in icon_name.lower():
            self._draw_refresh_icon(painter, size, color)
        elif "library" in icon_name.lower() or "book" in icon_name.lower():
            self._draw_library_icon(painter, size, color)
        elif "template" in icon_name.lower():
            self._draw_template_icon(painter, size, color)
        elif "download" in icon_name.lower():
            self._draw_download_icon(painter, size, color)
        elif "upload" in icon_name.lower():
            self._draw_upload_icon(painter, size, color)
        elif "save" in icon_name.lower():
            self._draw_save_icon(painter, size, color)
        elif "add" in icon_name.lower() or "new" in icon_name.lower():
            self._draw_add_icon(painter, size, color)
        elif "trash" in icon_name.lower() or "delete" in icon_name.lower():
            self._draw_trash_icon(painter, size, color)
        elif "user" in icon_name.lower() or "person" in icon_name.lower():
            self._draw_user_icon(painter, size, color)
        elif "theme" in icon_name.lower():
            self._draw_theme_icon(painter, size, color)
        elif "share" in icon_name.lower():
            self._draw_share_icon(painter, size, color)
        elif "notification" in icon_name.lower():
            self._draw_notification_icon(painter, size, color)
        else:
            self._draw_default_icon(painter, size, color, icon_name)

        painter.end()
        return QIcon(pixmap)

    def _get_icon_color(self, icon_name: str) -> QColor:
        """Get color for icon based on name"""
        if "error" in icon_name.lower() or "trash" in icon_name.lower():
            return QColor(220, 80, 80)  # Red
        elif "success" in icon_name.lower() or "save" in icon_name.lower():
            return QColor(80, 220, 80)  # Green
        elif "warning" in icon_name.lower():
            return QColor(255, 200, 60)  # Yellow
        elif "info" in icon_name.lower() or "notification" in icon_name.lower():
            return QColor(80, 150, 255)  # Blue
        else:
            return QColor(150, 150, 150)  # Gray

    def _draw_folder_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a folder icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()
        painter.drawRect(2, h//3, w-4, h//2)
        painter.drawRect(2, h//4, w//2, h//6)

    def _draw_file_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a file icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()
        painter.drawRect(3, 2, w-6, h-4)
        painter.drawLine(w-6, 2, w-6, h//4)
        painter.drawLine(w-6, h//4, w-3, h//4)

    def _draw_search_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a search icon"""
        painter.setPen(QPen(color, 2))

        w, h = size.width(), size.height()
        center_x, center_y = w//2 - 2, h//2 - 2
        radius = min(w, h) // 4

        painter.drawEllipse(center_x - radius, center_y - radius, radius*2, radius*2)
        painter.drawLine(center_x + radius, center_y + radius, w - 2, h - 2)

    def _draw_settings_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a settings gear icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()
        center_x, center_y = w//2, h//2

        # Draw gear shape (simplified)
        painter.drawEllipse(center_x - 6, center_y - 6, 12, 12)
        painter.drawEllipse(center_x - 3, center_y - 3, 6, 6)

        # Draw gear teeth
        for angle in range(0, 360, 45):
            x = center_x + 8 * (1 if angle % 90 == 0 else 0.7)
            y = center_y + 8 * (1 if angle % 90 == 0 else 0.7)
            painter.drawLine(center_x, center_y, int(x), int(y))

    def _draw_refresh_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a refresh icon"""
        painter.setPen(QPen(color, 2))

        w, h = size.width(), size.height()
        center_x, center_y = w//2, h//2

        # Draw circular arrow
        painter.drawArc(center_x - 6, center_y - 6, 12, 12, 0, 270 * 16)
        # Draw arrow head
        painter.drawLine(center_x + 6, center_y - 6, center_x + 3, center_y - 3)
        painter.drawLine(center_x + 6, center_y - 6, center_x + 3, center_y - 9)

    def _draw_library_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a library/book icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()

        # Draw book
        painter.drawRect(3, 2, w-6, h-4)
        painter.drawLine(w//2, 2, w//2, h-2)

        # Draw pages
        for i in range(3):
            painter.drawLine(5, 4 + i*2, w-5, 4 + i*2)

    def _draw_template_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a template icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()

        # Draw template layout
        painter.drawRect(2, 2, w-4, h-4)
        painter.drawLine(2, h//3, w-2, h//3)
        painter.drawLine(w//3, h//3, w//3, h-2)

    def _draw_download_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a download icon"""
        painter.setPen(QPen(color, 2))

        w, h = size.width(), size.height()
        center_x = w//2

        # Draw arrow
        painter.drawLine(center_x, 2, center_x, h-6)
        painter.drawLine(center_x, h-6, center_x-3, h-9)
        painter.drawLine(center_x, h-6, center_x+3, h-9)

        # Draw base
        painter.drawLine(3, h-3, w-3, h-3)

    def _draw_upload_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw an upload icon"""
        painter.setPen(QPen(color, 2))

        w, h = size.width(), size.height()
        center_x = w//2

        # Draw arrow
        painter.drawLine(center_x, h-2, center_x, 6)
        painter.drawLine(center_x, 6, center_x-3, 9)
        painter.drawLine(center_x, 6, center_x+3, 9)

        # Draw base
        painter.drawLine(3, h-3, w-3, h-3)

    def _draw_save_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a save icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()

        # Draw floppy disk
        painter.drawRect(2, 2, w-4, h-4)
        painter.drawRect(4, 2, w-8, h//3)
        painter.drawRect(w//2-1, 2, 2, h//4)

    def _draw_add_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw an add/plus icon"""
        painter.setPen(QPen(color, 2))

        w, h = size.width(), size.height()
        center_x, center_y = w//2, h//2

        # Draw plus sign
        painter.drawLine(center_x, 3, center_x, h-3)
        painter.drawLine(3, center_y, w-3, center_y)

    def _draw_trash_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a trash icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()

        # Draw trash can
        painter.drawRect(4, h//3, w-8, h*2//3-2)
        painter.drawRect(3, h//3-2, w-6, 2)
        painter.drawRect(w//2-1, 2, 2, h//3-4)

    def _draw_user_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a user icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()
        center_x, center_y = w//2, h//2

        # Draw head
        painter.drawEllipse(center_x-3, center_y-6, 6, 6)
        # Draw body
        painter.drawEllipse(center_x-5, center_y, 10, 8)

    def _draw_theme_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a theme icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()
        center_x, center_y = w//2, h//2

        # Draw half-filled circle for theme
        painter.drawEllipse(center_x-6, center_y-6, 12, 12)
        painter.drawPie(center_x-6, center_y-6, 12, 12, 0, 180*16)

    def _draw_share_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a share icon"""
        painter.setPen(QPen(color, 2))

        w, h = size.width(), size.height()

        # Draw share arrow
        painter.drawLine(w//3, h//2, w-3, 3)
        painter.drawLine(w-3, 3, w-6, 6)
        painter.drawLine(w-3, 3, w-6, 0)

        # Draw connection lines
        painter.drawLine(w//3, h//2, w//3, h-3)
        painter.drawLine(w//3, h-3, w*2//3, h-3)

    def _draw_notification_icon(self, painter: QPainter, size: QSize, color: QColor):
        """Draw a notification icon"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()

        # Draw bell shape
        painter.drawEllipse(w//2-4, h//2-4, 8, 8)
        painter.drawRect(w//2-2, 2, 4, h//2-2)
        painter.drawLine(w//2-6, h-4, w//2+6, h-4)

    def _draw_default_icon(self, painter: QPainter, size: QSize, color: QColor, icon_name: str):
        """Draw a default icon with the first letter of the icon name"""
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color.darker(), 1))

        w, h = size.width(), size.height()

        # Draw square background
        painter.drawRect(2, 2, w-4, h-4)

        # Draw first letter
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Arial", max(8, min(w, h) // 2))
        painter.setFont(font)

        letter = icon_name[0].upper() if icon_name else "?"
        painter.drawText(2, 2, w-4, h-4, Qt.AlignmentFlag.AlignCenter, letter)


# Global icon manager instance
icon_manager = IconManager()


def get_icon(icon_name: str, size: QSize = QSize(16, 16)) -> QIcon:
    """Get an icon with fallback"""
    return icon_manager.get_icon(icon_name, size)
