"""
Splash screen for The Oracle application with progress indicator.
"""

import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QProgressBar, QSplashScreen, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve, QPointF
from PyQt6.QtGui import QPixmap, QFont, QPainter, QPen, QBrush, QColor, QLinearGradient


class SplashScreen(QSplashScreen):
    """Custom splash screen with progress indicator"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(500, 300)

        # Create a custom pixmap for the splash screen
        pixmap = QPixmap(500, 300)
        pixmap.fill(QColor(45, 45, 45))  # Dark background

        # Draw on the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create gradient background
        gradient = QLinearGradient(0, 0, 0, 300)
        gradient.setColorAt(0, QColor(60, 60, 60))
        gradient.setColorAt(1, QColor(30, 30, 30))
        painter.fillRect(0, 0, 500, 300, QBrush(gradient))

        # Draw border
        painter.setPen(QPen(QColor(0, 150, 255), 2))
        painter.drawRect(1, 1, 498, 298)

        # Draw title
        painter.setPen(QPen(QColor(255, 255, 255)))
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(50, 80, "The Oracle")

        # Draw subtitle
        subtitle_font = QFont("Segoe UI", 12)
        painter.setFont(subtitle_font)
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawText(50, 110, "AI Chat Application")

        # Draw version
        version_font = QFont("Segoe UI", 10)
        painter.setFont(version_font)
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.drawText(50, 130, "Version 2.0.0")

        painter.end()

        self.setPixmap(pixmap)

        # Initialize progress tracking
        self.progress = 0
        self.status_text = "Initializing..."

        # Center the splash screen
        self.center_on_screen()

    def center_on_screen(self):
        """Center the splash screen on the screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def update_progress(self, progress, message=""):
        """Update progress bar and status message"""
        self.progress = progress
        if message:
            self.status_text = message

        # Show progress and message
        self.showMessage(
            f"{self.status_text}\n\n{self.progress}%",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor(255, 255, 255)
        )

        # Process events to update the display
        QApplication.processEvents()

    def drawContents(self, painter):
        """Override to draw custom content"""
        if not painter:
            return

        super().drawContents(painter)

        # Draw progress bar
        progress_rect = self.rect()
        progress_rect.setTop(progress_rect.bottom() - 60)
        progress_rect.setBottom(progress_rect.bottom() - 40)
        progress_rect.setLeft(progress_rect.left() + 50)
        progress_rect.setRight(progress_rect.right() - 50)

        # Draw progress bar background
        painter.fillRect(progress_rect, QColor(60, 60, 60))

        # Draw progress bar border
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(progress_rect)

        # Draw progress bar fill
        if self.progress > 0:
            fill_width = int((progress_rect.width() - 2) * self.progress / 100)
            fill_rect = progress_rect.adjusted(1, 1, -1, -1)
            fill_rect.setWidth(fill_width)

            # Create gradient for progress bar
            gradient = QLinearGradient(QPointF(fill_rect.topLeft()), QPointF(fill_rect.topRight()))
            gradient.setColorAt(0, QColor(0, 100, 200))
            gradient.setColorAt(1, QColor(0, 150, 255))
            painter.fillRect(fill_rect, QBrush(gradient))


class LoadingThread(QThread):
    """Thread to simulate loading process"""

    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.steps = [
            (10, "Loading configuration..."),
            (20, "Initializing API clients..."),
            (30, "Loading themes..."),
            (40, "Setting up UI components..."),
            (50, "Loading icons and resources..."),
            (60, "Initializing chat system..."),
            (70, "Loading prompt library..."),
            (80, "Setting up knowledge graph..."),
            (90, "Finalizing setup..."),
            (100, "Ready!")
        ]

    def run(self):
        """Run the loading simulation"""
        for progress, message in self.steps:
            self.progress_updated.emit(progress, message)
            self.msleep(200)  # Simulate loading time

        self.finished.emit()


def show_splash_screen():
    """Show splash screen and return it"""
    splash = SplashScreen()
    splash.show()

    # Start loading thread
    loading_thread = LoadingThread()
    loading_thread.progress_updated.connect(splash.update_progress)
    loading_thread.start()

    return splash, loading_thread
