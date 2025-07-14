"""
Splash screen for The Oracle application with progress indicator and package installation info.
"""

import os
import sys
import subprocess
from typing import List, Tuple, Optional
from PyQt6.QtWidgets import (QWidget,
                           QProgressBar, QSplashScreen, QApplication)
from PyQt6.QtCore import Qt, QTimer, QThread, QPointF, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QPen, QBrush, QColor, QLinearGradient, QFontMetrics


class DependencyInstaller(QThread):
    """Thread to handle dependency installation with real-time progress updates"""
    
    progress_updated = pyqtSignal(int, str, str)  # progress, message, tip
    package_checked = pyqtSignal(str, bool, str)  # package_name, found, status_message
    installation_complete = pyqtSignal(bool, str)  # success, message
    
    def __init__(self):
        super().__init__()
        self.required_packages = []
        self.missing_packages = []
        
    def set_packages(self, required: List[str], missing: List[str]):
        """Set the packages to check and install"""
        self.required_packages = required
        self.missing_packages = missing
        
    def run(self):
        """Run the dependency installation process"""
        try:
            if not self.missing_packages:
                self.progress_updated.emit(100, "All dependencies satisfied", "Ready to launch!")
                self.installation_complete.emit(True, "All dependencies available")
                return
                
            total_packages = len(self.required_packages)
            missing_count = len(self.missing_packages)
            
            # Check for NumPy compatibility issues first
            self.progress_updated.emit(5, "Checking NumPy compatibility...", "Ensuring system compatibility")
            self.check_numpy_compatibility()
            
            # Install missing packages
            for i, package in enumerate(self.missing_packages):
                progress = 10 + int(80 * i / missing_count)
                self.progress_updated.emit(
                    progress,
                    f"Installing {package}...",
                    f"Adding {package} to your system"
                )
                
                success = self.install_package(package)
                if not success:
                    self.installation_complete.emit(False, f"Failed to install {package}")
                    return
                    
            self.progress_updated.emit(95, "Finalizing installation...", "Almost ready!")
            self.installation_complete.emit(True, "All packages installed successfully")
            
        except Exception as e:
            self.installation_complete.emit(False, f"Installation error: {str(e)}")
    
    def check_numpy_compatibility(self):
        """Check and fix NumPy compatibility issues"""
        try:
            import numpy as np
            numpy_version = np.__version__
            
            if numpy_version.startswith('2.'):
                try:
                    import chromadb
                except AttributeError as e:
                    if "np.float_" in str(e):
                        self.progress_updated.emit(8, "Fixing NumPy compatibility...", "Upgrading chromadb for compatibility")
                        self.install_package("chromadb", upgrade=True)
                except ImportError:
                    pass
        except ImportError:
            pass
    
    def install_package(self, package: str, upgrade: bool=False) -> bool:
        """Install a single package"""
        try:
            python_exe = sys.executable
            cmd = [python_exe, "-m", "pip", "install"]
            
            if upgrade:
                cmd.append("--upgrade")
                
            cmd.append(package)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception:
            return False


class DependencyChecker(QThread):
    """Thread to handle dependency checking with real-time progress updates"""
    
    progress_updated = pyqtSignal(int, str, str)  # progress, message, tip
    package_checked = pyqtSignal(str, bool, str)  # package_name, found, status_message
    check_complete = pyqtSignal(list, list)  # required_packages, missing_packages
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        """Run the dependency checking process"""
        try:
            # Import here to avoid circular imports
            from utils.dependencies import get_required_dependencies, safe_import_check
            
            required = get_required_dependencies()
            total_packages = len(required)
            
            self.progress_updated.emit(0, f"Checking {total_packages} dependencies...", "Verifying installation")
            
            missing = []
            for i, pkg in enumerate(required):
                # Calculate cumulative progress (0-100) across all packages
                progress = int(100 * (i + 1) / total_packages)
                self.progress_updated.emit(progress, f"Checking {pkg}...", f"Verifying {pkg} installation")
                
                # Check if package is available
                found = safe_import_check(pkg)
                if found:
                    status_msg = "Found"
                    self.package_checked.emit(pkg, True, status_msg)
                else:
                    status_msg = "Missing"
                    missing.append(pkg)
                    self.package_checked.emit(pkg, False, status_msg)
                
                # Small delay to show progress
                self.msleep(50)
            
            self.progress_updated.emit(100, "Dependency check complete", "Processing results")
            self.check_complete.emit(required, missing)
            
        except Exception as e:
            self.progress_updated.emit(0, f"Check error: {str(e)}", "Please check your system")


class SplashScreen(QSplashScreen):
    loading_complete = pyqtSignal()
    """Custom splash screen with progress indicator and dependency installation info"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(500, 400)  # Increased height for more info

        # Animation state
        self._glow_phase = 0
        self._bg_phase = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)

        # For displaying tips and loading info
        self.tip_text = ""
        self.loading_text = "Initializing..."
        self.package_info = ""  # New field for package installation info
        self.installation_status = ""
        self.log_messages = []  # Store recent log messages
        self.max_log_messages = 5  # Maximum number of log messages to display
        self.total_progress = 0  # Unified progress (0-100)
        self.phase = 'check'  # 'check', 'install', 'load'
        self.check_total = 1
        self.check_done = 0
        self.install_total = 1
        self.install_done = 0

        # Emoji/icon list for tips
        self.tip_emojis = [
            "💡", "✨", "🤖", "📝", "🎨", "🛠️", "🔒", "⚡", "📚", "🧠", "🗂️", "🔍", "🖱️", "⌨️", "📤", "📥", "🗨️", "🧩", "🎯", "🌙", "☀️", "🖼️", "📊", "🔗", "🧑‍💻", "🦾", "🛡️", "🧭", "🗃️", "🧬", "🧰", "🧑‍🏫"
        ]
        
        # Initialize dependency threads
        self.dependency_checker = DependencyChecker()
        self.dependency_checker.progress_updated.connect(self._on_check_progress)
        self.dependency_checker.package_checked.connect(self.on_package_checked)
        self.dependency_checker.check_complete.connect(self.on_check_complete)
        
        self.dependency_installer = DependencyInstaller()
        self.dependency_installer.progress_updated.connect(self._on_install_progress)
        self.dependency_installer.package_checked.connect(self.on_package_checked)
        self.dependency_installer.installation_complete.connect(self.on_installation_complete)
        
        # Initialize progress tracking
        self.progress = 0
        self.status_text = "Initializing..."
        
        # Center the splash screen
        self.center_on_screen()

    def _animate(self):
        self._glow_phase = (self._glow_phase + 2) % 360
        self._bg_phase = (self._bg_phase + 1) % 360
        self.repaint()

    def center_on_screen(self):
        """Center the splash screen on the screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            self.move(x, y)

    def update_progress(self, progress: int, message: str="", tip: str=None) -> None:
        """Update progress bar, loading message, and optionally tip text"""
        import random
        self.progress = progress
        if message:
            self.loading_text = message
        if tip is not None:
            # Prepend a random emoji/icon to the tip for visual appeal
            emoji = random.choice(self.tip_emojis) if self.tip_emojis else "💡"
            self.tip_text = f"{emoji}  {tip}"
        self.repaint()
        QApplication.processEvents()

    def update_package_info(self, package_info: str, status: str=""):
        """Update package installation information"""
        self.package_info = package_info
        self.installation_status = status
        self.repaint()
        QApplication.processEvents()

    def add_log_message(self, message: str):
        """Add a log message to the display"""
        self.log_messages.append(message)
        if len(self.log_messages) > self.max_log_messages:
            self.log_messages.pop(0)
        self.repaint()
        QApplication.processEvents()

    def on_package_checked(self, package_name: str, found: bool, status_message: str):
        """Handle package check result"""
        status_icon = "✅" if found else "❌"
        log_msg = f"{status_icon} {package_name}: {status_message}"
        self.add_log_message(log_msg)

    def _on_check_progress(self, progress: int, message: str, tip: str=None):
        # Allow package checking to contribute to progress bar
        self.phase = 'check'
        # Map the cumulative progress (0-100) to the check phase (0-10%)
        self.check_done = progress
        self._update_total_progress()
        self.loading_text = message
        if tip:
            self.tip_text = tip
        self.update_progress(self.total_progress, message, tip)

    def _on_install_progress(self, progress: int, message: str, tip: str=None):
        # Only show progress during actual installation
        self.phase = 'install'
        self.install_done = progress
        self._update_total_progress()
        self.update_progress(self.total_progress, message, tip)

    def _update_total_progress(self):
        # Map: check 0-20, install 20-100 (removed load phase, scaled to 100%)
        # Allow check phase to contribute to progress based on actual progress
        check_part = (self.check_done / 100) * 20 if self.check_total and self.phase == 'check' else 0
        install_part = (self.install_done / 100) * 80 if self.install_total and self.phase == 'install' else 0
        # Removed load_part - no longer needed
        self.total_progress = int(check_part + install_part)

    def on_check_complete(self, required_packages: list, missing_packages: list):
        if missing_packages:
            self.phase = 'install'
            self.install_total = 100
            self.install_done = 0
            self.check_done = 100  # Mark check as complete
            self._update_total_progress()  # This will set progress to 20%
            self.update_package_info(f"Missing packages: {', '.join(missing_packages)}", "Installing...")
            self.dependency_installer.set_packages(required_packages, missing_packages)
            self.dependency_installer.start()
        else:
            # No missing packages, mark as complete
            self.check_done = 100  # Mark check as complete
            self.install_done = 100  # Mark install as complete (no packages to install)
            self._update_total_progress()  # This will set progress to 100%
            self.update_package_info("All dependencies satisfied", "Ready!")
            self.update_progress(self.total_progress, "All dependencies available", "Ready to launch!")
            # Emit loading complete signal immediately
            QTimer.singleShot(1000, self.loading_complete.emit)

    def on_installation_complete(self, success: bool, message: str):
        if success:
            self.install_done = 100  # Mark installation as complete
            self._update_total_progress()  # This will set progress to 100%
            self.update_progress(self.total_progress, "Installation complete!", "Ready to launch The Oracle!")
            # Emit loading complete signal immediately
            QTimer.singleShot(1000, self.loading_complete.emit)
        else:
            self.update_progress(0, f"Installation failed: {message}", "Please check your internet connection")

    def start_dependency_check(self):
        self.phase = 'check'
        self.check_total = 100
        self.check_done = 0
        self.install_total = 100
        self.install_done = 0
        self.loading_total = 100
        self.loading_done = 0
        self.total_progress = 0
        self.update_progress(0, "Checking dependencies...", "Verifying system requirements")
        self.dependency_checker.start()

    def drawContents(self, painter):
        """Override to draw custom content"""
        if not painter:
            return

        super().drawContents(painter)

        # --- Animated background gradient ---
        import math
        phase = self._bg_phase
        grad = QLinearGradient(0, 0, 500, 400)
        grad.setColorAt(0, QColor(40 + int(20 * math.sin(math.radians(phase))), 60, 120 + int(40 * math.cos(math.radians(phase)))))
        grad.setColorAt(1, QColor(30, 30 + int(20 * math.cos(math.radians(phase / 2))), 60 + int(30 * math.sin(math.radians(phase / 2)))))
        painter.fillRect(self.rect(), grad)

        # --- Glowing animated border ---
        glow_color = QColor(0, 180 + int(60 * math.sin(math.radians(self._glow_phase))), 255, 180)
        pen = QPen(glow_color, 6)
        painter.setPen(pen)
        painter.drawRoundedRect(3, 3, 494, 394, 18, 18)

        # --- Central Oracle icon (large, semi-transparent) ---
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icons", "oracle_app.png")
        if os.path.exists(icon_path):
            icon_pix = QPixmap(icon_path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.setOpacity(0.18)
            painter.drawPixmap(190, 20, icon_pix)
            painter.setOpacity(1.0)

        # --- Title with gradient text ---
        title_font = QFont("Segoe UI Black", 28, QFont.Weight.Black)
        painter.setFont(title_font)
        grad_text = QLinearGradient(0, 0, 500, 0)
        grad_text.setColorAt(0, QColor(0, 200, 255))
        grad_text.setColorAt(1, QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(grad_text))
        painter.drawText(0, 40, 500, 50, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "The Oracle")
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # --- Subtitle ---
        subtitle_font = QFont("Segoe UI", 13, QFont.Weight.Medium)
        painter.setFont(subtitle_font)
        painter.setPen(QPen(QColor(200, 255, 255)))
        painter.drawText(0, 75, 500, 30, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "AI Chat Application")

        # --- Version ---
        version_font = QFont("Segoe UI", 10, QFont.Weight.Normal)
        painter.setFont(version_font)
        painter.setPen(QPen(QColor(180, 220, 255)))
        painter.drawText(0, 100, 500, 20, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, "Version 2.0.0")

        # --- Draw tip text in the center area ---
        if self.tip_text:
            tip_font = QFont("Segoe Script", 15, QFont.Weight.Bold)
            tip_font.setItalic(True)
            painter.setFont(tip_font)
            painter.setPen(QPen(QColor(255, 220, 120)))
            rect = self.rect().adjusted(30, 130, -30, -200)
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.tip_text)

        # --- Draw package installation info ---
        if self.package_info:
            pkg_font = QFont("Segoe UI Semibold", 11, QFont.Weight.DemiBold)
            painter.setFont(pkg_font)
            painter.setPen(QPen(QColor(255, 255, 200)))
            rect = self.rect().adjusted(30, 170, -30, -120)
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.package_info)
            
            # Draw installation status
            if self.installation_status:
                status_font = QFont("Segoe UI", 10, QFont.Weight.Normal)
                painter.setFont(status_font)
                status_color = QColor(100, 255, 100) if "Ready" in self.installation_status else QColor(255, 200, 100)
                painter.setPen(QPen(status_color))
                rect = self.rect().adjusted(30, 190, -30, -100)
                painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.installation_status)

        # --- Draw log messages ---
        if self.log_messages:
            log_font = QFont("Consolas", 9, QFont.Weight.Normal)
            painter.setFont(log_font)
            painter.setPen(QPen(QColor(200, 255, 200)))
            
            log_rect = self.rect().adjusted(30, 220, -30, -80)
            log_text = "\n".join(self.log_messages[-3:])  # Show last 3 messages
            painter.drawText(log_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, log_text)

        # --- Draw loading/progress info just above the progress bar ---
        if self.loading_text:
            load_font = QFont("Segoe UI Semibold", 12, QFont.Weight.DemiBold)
            painter.setFont(load_font)
            painter.setPen(QPen(QColor(200, 255, 255)))
            rect = self.rect().adjusted(30, 300, -30, -50)
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, f"{self.loading_text}  {self.progress}%")

        # --- Draw progress bar ---
        progress_rect = self.rect()
        progress_rect.setTop(progress_rect.bottom() - 60)
        progress_rect.setBottom(progress_rect.bottom() - 40)
        progress_rect.setLeft(progress_rect.left() + 50)
        progress_rect.setRight(progress_rect.right() - 50)

        # Draw progress bar background
        painter.fillRect(progress_rect, QColor(60, 60, 60, 200))

        # Draw progress bar border
        painter.setPen(QPen(QColor(100, 200, 255), 2))
        painter.drawRect(progress_rect)

        # Draw progress bar fill
        if self.progress > 0:
            fill_width = int((progress_rect.width() - 2) * self.progress / 100)
            fill_rect = progress_rect.adjusted(1, 1, -1, -1)
            fill_rect.setWidth(fill_width)

            # Create animated gradient for progress bar
            grad = QLinearGradient(QPointF(fill_rect.topLeft()), QPointF(fill_rect.topRight()))
            grad.setColorAt(0, QColor(0, 180, 255))
            grad.setColorAt(0.5, QColor(0, 255, 200 + int(55 * math.sin(math.radians(self._glow_phase / 2)))))
            grad.setColorAt(1, QColor(0, 120, 255))
            painter.fillRect(fill_rect, QBrush(grad))

    def _wrap_text(self, text: str, metrics: QFontMetrics, max_width: int) -> list[str]:
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if metrics.horizontalAdvance(test_line) > max_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        return lines


def show_splash_screen():
    """Show splash screen and return it"""
    splash = SplashScreen()
    splash.show()

    # Start dependency check first
    splash.start_dependency_check()

    return splash
