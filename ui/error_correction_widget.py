#!/usr/bin/env python3
"""
Oracle/ui/error_correction_widget.py

Author: The Oracle Development Team
Date: 2024-01-01

GUI widget for monitoring and controlling the automatic error correction system.
"""

import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QProgressBar, QCheckBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import (
    get_error_correction_status, 
    force_error_scan,
    start_auto_error_correction,
    stop_auto_error_correction
)


class ErrorCorrectionStatusThread(QThread):
    """Thread for updating error correction status"""
    status_updated = pyqtSignal(dict)
    
    def __init__(self, update_interval=5):
        super().__init__()
        self.update_interval = update_interval
        self.running = True
    
    def run(self):
        """Main thread loop"""
        while self.running:
            try:
                status = get_error_correction_status()
                self.status_updated.emit(status)
            except Exception as e:
                print(f"Error updating status: {e}")
            
            self.msleep(self.update_interval * 1000)
    
    def stop(self):
        """Stop the thread"""
        self.running = False
        self.wait()


class ErrorCorrectionWidget(QWidget):
    """Main widget for error correction monitoring and control"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_thread = None
        self.init_ui()
        self.start_status_updates()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🔧 Automatic Error Correction System")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Control Panel
        control_group = QGroupBox("Control Panel")
        control_layout = QHBoxLayout()
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("Start Monitoring")
        self.start_stop_btn.setMinimumHeight(40)
        self.start_stop_btn.clicked.connect(self.toggle_monitoring)
        control_layout.addWidget(self.start_stop_btn)
        
        # Force scan button
        self.force_scan_btn = QPushButton("Force Scan Now")
        self.force_scan_btn.setMinimumHeight(40)
        self.force_scan_btn.clicked.connect(self.force_scan)
        control_layout.addWidget(self.force_scan_btn)
        
        # Interval control
        interval_layout = QVBoxLayout()
        interval_label = QLabel("Scan Interval (seconds):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(10, 3600)
        self.interval_spinbox.setValue(60)
        self.interval_spinbox.setSuffix(" sec")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        control_layout.addLayout(interval_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Status Panel
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        
        # Status indicators
        status_grid = QHBoxLayout()
        
        # Running status
        self.running_label = QLabel("Status: Stopped")
        self.running_label.setStyleSheet("color: red; font-weight: bold;")
        status_grid.addWidget(self.running_label)
        
        # Last scan time
        self.last_scan_label = QLabel("Last Scan: Never")
        status_grid.addWidget(self.last_scan_label)
        
        # Total errors fixed
        self.total_fixed_label = QLabel("Total Fixed: 0")
        status_grid.addWidget(self.total_fixed_label)
        
        status_layout.addLayout(status_grid)
        
        # Progress bar for next scan
        self.progress_label = QLabel("Next scan in: 60 seconds")
        status_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 60)
        self.progress_bar.setValue(60)
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Correction History
        history_group = QGroupBox("Recent Corrections")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "Error Type", "File", "Action"
        ])
        
        # Set table properties
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.history_table.setMaximumHeight(200)
        history_layout.addWidget(self.history_table)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Log Panel
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Clear log button
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        
        # Timer for progress bar updates
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(1000)  # Update every second
        
        # Initialize with current status
        self.update_status()
    
    def start_status_updates(self):
        """Start the status update thread"""
        self.status_thread = ErrorCorrectionStatusThread(update_interval=5)
        self.status_thread.status_updated.connect(self.update_status)
        self.status_thread.start()
    
    def stop_status_updates(self):
        """Stop the status update thread"""
        if self.status_thread:
            self.status_thread.stop()
            self.status_thread = None
    
    def toggle_monitoring(self):
        """Toggle the monitoring on/off"""
        try:
            status = get_error_correction_status()
            
            if status['running']:
                stop_auto_error_correction()
                self.log_message("🛑 Stopped automatic error correction")
                self.start_stop_btn.setText("Start Monitoring")
                self.start_stop_btn.setStyleSheet("background-color: #4CAF50; color: white;")
            else:
                interval = self.interval_spinbox.value()
                start_auto_error_correction(interval=interval)
                self.log_message(f"🚀 Started automatic error correction (interval: {interval}s)")
                self.start_stop_btn.setText("Stop Monitoring")
                self.start_stop_btn.setStyleSheet("background-color: #f44336; color: white;")
                
        except Exception as e:
            self.log_message(f"❌ Error toggling monitoring: {e}")
            QMessageBox.warning(self, "Error", f"Failed to toggle monitoring: {e}")
    
    def force_scan(self):
        """Force an immediate error scan"""
        try:
            force_error_scan()
            self.log_message("🔍 Forced error scan initiated")
        except Exception as e:
            self.log_message(f"❌ Error forcing scan: {e}")
            QMessageBox.warning(self, "Error", f"Failed to force scan: {e}")
    
    def update_status(self, status=None):
        """Update the status display"""
        if status is None:
            try:
                status = get_error_correction_status()
            except Exception as e:
                self.log_message(f"❌ Error getting status: {e}")
                return
        
        # Update running status
        if status['running']:
            self.running_label.setText("Status: Running")
            self.running_label.setStyleSheet("color: green; font-weight: bold;")
            self.start_stop_btn.setText("Stop Monitoring")
            self.start_stop_btn.setStyleSheet("background-color: #f44336; color: white;")
        else:
            self.running_label.setText("Status: Stopped")
            self.running_label.setStyleSheet("color: red; font-weight: bold;")
            self.start_stop_btn.setText("Start Monitoring")
            self.start_stop_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        # Update last scan time
        if status['last_scan_time']:
            last_scan = status['last_scan_time']
            if isinstance(last_scan, str):
                self.last_scan_label.setText(f"Last Scan: {last_scan}")
            else:
                self.last_scan_label.setText(f"Last Scan: {last_scan.strftime('%H:%M:%S')}")
        else:
            self.last_scan_label.setText("Last Scan: Never")
        
        # Update total errors fixed
        self.total_fixed_label.setText(f"Total Fixed: {status['total_errors_fixed']}")
        
        # Update interval
        self.interval_spinbox.setValue(status['interval'])
        
        # Update history table
        self.update_history_table(status.get('correction_history', []))
    
    def update_history_table(self, history):
        """Update the correction history table"""
        self.history_table.setRowCount(len(history))
        
        for row, correction in enumerate(history):
            # Timestamp
            timestamp = correction.get('timestamp', '')
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime('%H:%M:%S')
            else:
                timestamp_str = str(timestamp)
            
            self.history_table.setItem(row, 0, QTableWidgetItem(timestamp_str))
            
            # Error type
            error_type = correction.get('error_type', '')
            self.history_table.setItem(row, 1, QTableWidgetItem(error_type))
            
            # File
            file_path = correction.get('file', '')
            self.history_table.setItem(row, 2, QTableWidgetItem(file_path))
            
            # Action
            action = correction.get('action', '')
            self.history_table.setItem(row, 3, QTableWidgetItem(action))
    
    def update_progress(self):
        """Update the progress bar for next scan"""
        try:
            status = get_error_correction_status()
            
            if status['running'] and status['last_scan_time']:
                # Calculate time since last scan
                last_scan = status['last_scan_time']
                if isinstance(last_scan, str):
                    # Parse string timestamp
                    try:
                        last_scan = datetime.fromisoformat(last_scan.replace('Z', '+00:00'))
                    except:
                        return
                
                time_since_scan = (datetime.now() - last_scan).total_seconds()
                interval = status['interval']
                
                # Calculate remaining time
                remaining = max(0, interval - time_since_scan)
                
                # Update progress bar
                self.progress_bar.setRange(0, interval)
                self.progress_bar.setValue(int(remaining))
                
                # Update label
                if remaining > 0:
                    self.progress_label.setText(f"Next scan in: {int(remaining)} seconds")
                else:
                    self.progress_label.setText("Scanning...")
            else:
                self.progress_bar.setValue(0)
                self.progress_label.setText("Monitoring stopped")
                
        except Exception as e:
            self.progress_label.setText("Error updating progress")
    
    def log_message(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.clear()
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.stop_status_updates()
        super().closeEvent(event)


class ErrorCorrectionDialog(QWidget):
    """Dialog for error correction settings and monitoring"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error Correction System")
        self.setMinimumSize(800, 600)
        
        # Create main widget
        self.error_widget = ErrorCorrectionWidget()
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.error_widget)
        self.setLayout(layout)
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self.error_widget.stop_status_updates()
        super().closeEvent(event)


if __name__ == "__main__":
    # Test the widget
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create and show the dialog
    dialog = ErrorCorrectionDialog()
    dialog.show()
    
    sys.exit(app.exec())