# -*- coding: utf-8 -*-
"""
Local Model Server Management Dialog
File: ui/local_model_server_dialog.py
Author: The Oracle Development Team
Date: 2024-12-19

Comprehensive UI for managing local model servers with support for:
- Multiple backends (CPU, CUDA, Vulkan, ROCm, Metal, OpenCL)
- All model architectures
- Server configuration and monitoring
- Model loading and management
- Performance monitoring and optimization
"""

import os
import sys
import json
import time
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QLineEdit, QTextEdit, QTabWidget, QWidget,
    QGroupBox, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QScrollArea, QFrame, QMessageBox,
    QFileDialog, QSlider, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QApplication
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor

from api.local_model_server import (
    LocalModelServerManager, LlamaCppServer, ServerConfig, ModelConfig,
    BackendType, ModelArchitecture, QuantizationType, InferenceRequest
)
# from ui.theme_styles import get_theme_stylesheet

logger = logging.getLogger(__name__)


class ServerMonitorThread(QThread):
    """Thread for monitoring server status."""
    
    status_updated = pyqtSignal(dict)  # server_status
    model_updated = pyqtSignal(dict)  # model_status
    
    def __init__(self, server_manager: LocalModelServerManager):
        super().__init__()
        self.server_manager = server_manager
        self.running = True
    
    def run(self):
        """Monitor server status continuously."""
        while self.running:
            try:
                status = self.server_manager.get_all_server_status()
                self.status_updated.emit(status)
                
                models = self.server_manager.get_available_models()
                self.model_updated.emit(models)
                
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Error in server monitor: {e}")
                time.sleep(5)
    
    def stop(self):
        """Stop monitoring."""
        self.running = False


class LocalModelServerDialog(QDialog):
    """Main dialog for local model server management."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.server_manager = LocalModelServerManager()
        self.monitor_thread = ServerMonitorThread(self.server_manager)
        
        self.setWindowTitle("Local Model Server Management")
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.setup_connections()
        self.start_monitoring()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Local Model Server Management")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.setup_server_tab()
        self.setup_models_tab()
        self.setup_configuration_tab()
        self.setup_monitoring_tab()
        self.setup_logs_tab()
        
        # Apply theme
        # self.setStyleSheet(get_theme_stylesheet())
    
    def setup_server_tab(self):
        """Set up the server management tab."""
        server_widget = QWidget()
        layout = QVBoxLayout(server_widget)
        
        # Server controls
        controls_group = QGroupBox("Server Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.start_server_btn = QPushButton("🚀 Start Server")
        self.start_server_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; border-radius: 4px; }")
        controls_layout.addWidget(self.start_server_btn)
        
        self.stop_server_btn = QPushButton("🛑 Stop Server")
        self.stop_server_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 8px; border-radius: 4px; }")
        controls_layout.addWidget(self.stop_server_btn)
        
        self.restart_server_btn = QPushButton("🔄 Restart Server")
        self.restart_server_btn.setStyleSheet("QPushButton { background-color: #ff9800; color: white; padding: 8px; border-radius: 4px; }")
        controls_layout.addWidget(self.restart_server_btn)
        
        controls_layout.addStretch()
        
        # Server status
        self.server_status_label = QLabel("Status: Not Running")
        self.server_status_label.setStyleSheet("QLabel { font-weight: bold; padding: 8px; background: #f0f0f0; border-radius: 4px; }")
        controls_layout.addWidget(self.server_status_label)
        
        layout.addWidget(controls_group)
        
        # Server configuration
        config_group = QGroupBox("Server Configuration")
        config_layout = QFormLayout(config_group)
        
        self.host_input = QLineEdit("127.0.0.1")
        config_layout.addRow("Host:", self.host_input)
        
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(8080)
        config_layout.addRow("Port:", self.port_input)
        
        self.max_connections_input = QSpinBox()
        self.max_connections_input.setRange(1, 100)
        self.max_connections_input.setValue(10)
        config_layout.addRow("Max Connections:", self.max_connections_input)
        
        self.enable_websocket_check = QCheckBox("Enable WebSocket")
        self.enable_websocket_check.setChecked(True)
        config_layout.addRow("", self.enable_websocket_check)
        
        self.enable_ssl_check = QCheckBox("Enable SSL")
        config_layout.addRow("", self.enable_ssl_check)
        
        layout.addWidget(config_group)
        
        # Server information
        info_group = QGroupBox("Server Information")
        info_layout = QVBoxLayout(info_group)
        
        self.server_info_text = QTextEdit()
        self.server_info_text.setMaximumHeight(150)
        self.server_info_text.setReadOnly(True)
        info_layout.addWidget(self.server_info_text)
        
        layout.addWidget(info_group)
        
        self.tab_widget.addTab(server_widget, "🖥️ Server Management")
    
    def setup_models_tab(self):
        """Set up the model management tab."""
        models_widget = QWidget()
        layout = QVBoxLayout(models_widget)
        
        # Model controls
        controls_group = QGroupBox("Model Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.load_model_btn = QPushButton("📥 Load Model")
        self.load_model_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; border-radius: 4px; }")
        controls_layout.addWidget(self.load_model_btn)
        
        self.unload_model_btn = QPushButton("📤 Unload Model")
        self.unload_model_btn.setStyleSheet("QPushButton { background-color: #ff9800; color: white; padding: 8px; border-radius: 4px; }")
        controls_layout.addWidget(self.unload_model_btn)
        
        self.refresh_models_btn = QPushButton("🔄 Refresh")
        controls_layout.addWidget(self.refresh_models_btn)
        
        controls_layout.addStretch()
        
        layout.addWidget(controls_group)
        
        # Model configuration
        config_group = QGroupBox("Model Configuration")
        config_layout = QFormLayout(config_group)
        
        self.backend_combo = QComboBox()
        for backend in BackendType:
            self.backend_combo.addItem(backend.value.title(), backend)
        config_layout.addRow("Backend:", self.backend_combo)
        
        self.quantization_combo = QComboBox()
        for quant in QuantizationType:
            self.quantization_combo.addItem(quant.value.upper(), quant)
        self.quantization_combo.setCurrentText("Q4_K_M")
        config_layout.addRow("Quantization:", self.quantization_combo)
        
        self.context_length_input = QSpinBox()
        self.context_length_input.setRange(512, 32768)
        self.context_length_input.setValue(4096)
        self.context_length_input.setSuffix(" tokens")
        config_layout.addRow("Context Length:", self.context_length_input)
        
        self.gpu_layers_input = QSpinBox()
        self.gpu_layers_input.setRange(0, 100)
        self.gpu_layers_input.setValue(0)
        config_layout.addRow("GPU Layers:", self.gpu_layers_input)
        
        self.batch_size_input = QSpinBox()
        self.batch_size_input.setRange(1, 2048)
        self.batch_size_input.setValue(512)
        config_layout.addRow("Batch Size:", self.batch_size_input)
        
        layout.addWidget(config_group)
        
        # Model list
        models_group = QGroupBox("Loaded Models")
        models_layout = QVBoxLayout(models_group)
        
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(5)
        self.models_table.setHorizontalHeaderLabels([
            "Model Name", "Server", "Backend", "Context Length", "Status"
        ])
        self.models_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        models_layout.addWidget(self.models_table)
        
        layout.addWidget(models_group)
        
        self.tab_widget.addTab(models_widget, "🤖 Model Management")
    
    def setup_configuration_tab(self):
        """Set up the configuration tab."""
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        
        # Advanced server settings
        advanced_group = QGroupBox("Advanced Server Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(5, 300)
        self.timeout_input.setValue(30)
        self.timeout_input.setSuffix(" seconds")
        advanced_layout.addRow("Timeout:", self.timeout_input)
        
        self.max_batch_size_input = QSpinBox()
        self.max_batch_size_input.setRange(1, 16)
        self.max_batch_size_input.setValue(4)
        advanced_layout.addRow("Max Batch Size:", self.max_batch_size_input)
        
        self.enable_cors_check = QCheckBox("Enable CORS")
        self.enable_cors_check.setChecked(True)
        advanced_layout.addRow("", self.enable_cors_check)
        
        self.enable_metrics_check = QCheckBox("Enable Metrics")
        self.enable_metrics_check.setChecked(True)
        advanced_layout.addRow("", self.enable_metrics_check)
        
        self.enable_health_check_check = QCheckBox("Enable Health Check")
        self.enable_health_check_check.setChecked(True)
        advanced_layout.addRow("", self.enable_health_check_check)
        
        layout.addWidget(advanced_group)
        
        # Model architecture settings
        arch_group = QGroupBox("Model Architecture Settings")
        arch_layout = QFormLayout(arch_group)
        
        self.rope_freq_base_input = QDoubleSpinBox()
        self.rope_freq_base_input.setRange(1000.0, 100000.0)
        self.rope_freq_base_input.setValue(10000.0)
        self.rope_freq_base_input.setDecimals(1)
        arch_layout.addRow("RoPE Frequency Base:", self.rope_freq_base_input)
        
        self.rope_freq_scale_input = QDoubleSpinBox()
        self.rope_freq_scale_input.setRange(0.1, 10.0)
        self.rope_freq_scale_input.setValue(1.0)
        self.rope_freq_scale_input.setDecimals(2)
        arch_layout.addRow("RoPE Frequency Scale:", self.rope_freq_scale_input)
        
        self.rms_norm_eps_input = QDoubleSpinBox()
        self.rms_norm_eps_input.setRange(1e-6, 1e-3)
        self.rms_norm_eps_input.setValue(1e-5)
        self.rms_norm_eps_input.setDecimals(6)
        arch_layout.addRow("RMS Norm Epsilon:", self.rms_norm_eps_input)
        
        self.flash_attn_check = QCheckBox("Enable Flash Attention")
        self.flash_attn_check.setChecked(True)
        arch_layout.addRow("", self.flash_attn_check)
        
        self.offload_kqv_check = QCheckBox("Offload KQV to GPU")
        self.offload_kqv_check.setChecked(True)
        arch_layout.addRow("", self.offload_kqv_check)
        
        layout.addWidget(arch_group)
        
        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(perf_group)
        
        self.threads_input = QSpinBox()
        self.threads_input.setRange(-1, 64)
        self.threads_input.setValue(-1)
        self.threads_input.setSuffix(" (-1 = auto)")
        perf_layout.addRow("Threads:", self.threads_input)
        
        self.use_mmap_check = QCheckBox("Use Memory Mapping")
        self.use_mmap_check.setChecked(True)
        perf_layout.addRow("", self.use_mmap_check)
        
        self.use_mlock_check = QCheckBox("Use Memory Lock")
        perf_layout.addRow("", self.use_mlock_check)
        
        self.numa_check = QCheckBox("Enable NUMA")
        perf_layout.addRow("", self.numa_check)
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(config_widget, "⚙️ Configuration")
    
    def setup_monitoring_tab(self):
        """Set up the monitoring tab."""
        monitoring_widget = QWidget()
        layout = QVBoxLayout(monitoring_widget)
        
        # Performance metrics
        metrics_group = QGroupBox("Performance Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        self.cpu_usage_label = QLabel("CPU Usage: --")
        self.cpu_usage_label.setStyleSheet("QLabel { background: #e3f2fd; padding: 8px; border-radius: 4px; }")
        metrics_layout.addWidget(self.cpu_usage_label, 0, 0)
        
        self.memory_usage_label = QLabel("Memory Usage: --")
        self.memory_usage_label.setStyleSheet("QLabel { background: #f3e5f5; padding: 8px; border-radius: 4px; }")
        metrics_layout.addWidget(self.memory_usage_label, 0, 1)
        
        self.gpu_usage_label = QLabel("GPU Usage: --")
        self.gpu_usage_label.setStyleSheet("QLabel { background: #e8f5e8; padding: 8px; border-radius: 4px; }")
        metrics_layout.addWidget(self.gpu_usage_label, 1, 0)
        
        self.response_time_label = QLabel("Avg Response Time: --")
        self.response_time_label.setStyleSheet("QLabel { background: #fff3e0; padding: 8px; border-radius: 4px; }")
        metrics_layout.addWidget(self.response_time_label, 1, 1)
        
        layout.addWidget(metrics_group)
        
        # Server status table
        status_group = QGroupBox("Server Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels([
            "Server Name", "Status", "URL", "Loaded Models"
        ])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        status_layout.addWidget(self.status_table)
        
        layout.addWidget(status_group)
        
        # Model performance table
        perf_group = QGroupBox("Model Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        self.perf_table = QTableWidget()
        self.perf_table.setColumnCount(6)
        self.perf_table.setHorizontalHeaderLabels([
            "Model", "Server", "Tokens/sec", "Memory (MB)", "GPU Memory (MB)", "Status"
        ])
        self.perf_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        perf_layout.addWidget(self.perf_table)
        
        layout.addWidget(perf_group)
        
        self.tab_widget.addTab(monitoring_widget, "📊 Monitoring")
    
    def setup_logs_tab(self):
        """Set up the logs tab."""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        # Log controls
        controls_layout = QHBoxLayout()
        
        self.clear_logs_btn = QPushButton("🗑️ Clear Logs")
        controls_layout.addWidget(self.clear_logs_btn)
        
        self.save_logs_btn = QPushButton("💾 Save Logs")
        controls_layout.addWidget(self.save_logs_btn)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        controls_layout.addWidget(QLabel("Log Level:"))
        controls_layout.addWidget(self.log_level_combo)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Log display
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.logs_text)
        
        self.tab_widget.addTab(logs_widget, "📝 Logs")
    
    def setup_connections(self):
        """Set up signal connections."""
        # Server controls
        self.start_server_btn.clicked.connect(self.start_server)
        self.stop_server_btn.clicked.connect(self.stop_server)
        self.restart_server_btn.clicked.connect(self.restart_server)
        
        # Model controls
        self.load_model_btn.clicked.connect(self.load_model)
        self.unload_model_btn.clicked.connect(self.unload_model)
        self.refresh_models_btn.clicked.connect(self.refresh_models)
        
        # Log controls
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.save_logs_btn.clicked.connect(self.save_logs)
        
        # Monitor thread
        self.monitor_thread.status_updated.connect(self.update_server_status)
        self.monitor_thread.model_updated.connect(self.update_model_status)
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        self.monitor_thread.start()
    
    def start_server(self):
        """Start the local model server."""
        try:
            # Create server configuration
            config = ServerConfig(
                host=self.host_input.text(),
                port=self.port_input.value(),
                max_connections=self.max_connections_input.value(),
                timeout=self.timeout_input.value(),
                enable_cors=self.enable_cors_check.isChecked(),
                enable_metrics=self.enable_metrics_check.isChecked(),
                enable_health_check=self.enable_health_check_check.isChecked(),
                enable_websocket=self.enable_websocket_check.isChecked(),
                enable_ssl=self.enable_ssl_check.isChecked(),
                max_batch_size=self.max_batch_size_input.value()
            )
            
            # Create and start server
            if self.server_manager.create_server("main", config):
                self.log_message("INFO", "Server started successfully")
                self.update_server_status_display()
            else:
                self.log_message("ERROR", "Failed to start server")
                
        except Exception as e:
            self.log_message("ERROR", f"Error starting server: {e}")
    
    def stop_server(self):
        """Stop the local model server."""
        try:
            if self.server_manager.stop_server("main"):
                self.log_message("INFO", "Server stopped successfully")
                self.update_server_status_display()
            else:
                self.log_message("ERROR", "Failed to stop server")
                
        except Exception as e:
            self.log_message("ERROR", f"Error stopping server: {e}")
    
    def restart_server(self):
        """Restart the local model server."""
        self.stop_server()
        time.sleep(2)
        self.start_server()
    
    def load_model(self):
        """Load a model into the server."""
        try:
            # Get model file
            model_path, _ = QFileDialog.getOpenFileName(
                self, "Select Model File", "", "GGUF Files (*.gguf);;All Files (*)"
            )
            
            if not model_path:
                return
            
            # Create model configuration
            config = ModelConfig(
                model_path=model_path,
                backend=self.backend_combo.currentData(),
                quantization=self.quantization_combo.currentData(),
                context_length=self.context_length_input.value(),
                gpu_layers=self.gpu_layers_input.value(),
                batch_size=self.batch_size_input.value(),
                rope_freq_base=self.rope_freq_base_input.value(),
                rope_freq_scale=self.rope_freq_scale_input.value(),
                rms_norm_eps=self.rms_norm_eps_input.value(),
                flash_attn=self.flash_attn_check.isChecked(),
                offload_kqv=self.offload_kqv_check.isChecked(),
                threads=self.threads_input.value(),
                use_mmap=self.use_mmap_check.isChecked(),
                use_mlock=self.use_mlock_check.isChecked(),
                numa=self.numa_check.isChecked()
            )
            
            # Load model
            if self.server_manager.load_model("main", model_path, config):
                model_name = Path(model_path).stem
                self.log_message("INFO", f"Model {model_name} loaded successfully")
                self.refresh_models()
            else:
                self.log_message("ERROR", "Failed to load model")
                
        except Exception as e:
            self.log_message("ERROR", f"Error loading model: {e}")
    
    def unload_model(self):
        """Unload a model from the server."""
        try:
            # Get selected model
            current_row = self.models_table.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Warning", "Please select a model to unload")
                return
            
            model_name = self.models_table.item(current_row, 0).text()
            
            # Unload model
            if self.server_manager.unload_model("main", model_name):
                self.log_message("INFO", f"Model {model_name} unloaded successfully")
                self.refresh_models()
            else:
                self.log_message("ERROR", f"Failed to unload model {model_name}")
                
        except Exception as e:
            self.log_message("ERROR", f"Error unloading model: {e}")
    
    def refresh_models(self):
        """Refresh the models table."""
        try:
            models = self.server_manager.get_available_models()
            
            self.models_table.setRowCount(len(models))
            
            for i, (key, info) in enumerate(models.items()):
                self.models_table.setItem(i, 0, QTableWidgetItem(info["model"]))
                self.models_table.setItem(i, 1, QTableWidgetItem(info["server"]))
                self.models_table.setItem(i, 2, QTableWidgetItem("CPU"))  # TODO: Get actual backend
                self.models_table.setItem(i, 3, QTableWidgetItem("4096"))  # TODO: Get actual context length
                self.models_table.setItem(i, 4, QTableWidgetItem("Loaded"))
                
        except Exception as e:
            self.log_message("ERROR", f"Error refreshing models: {e}")
    
    def update_server_status(self, status: Dict[str, Any]):
        """Update server status display."""
        try:
            # Update status table
            self.status_table.setRowCount(len(status))
            
            for i, (server_name, server_status) in enumerate(status.items()):
                self.status_table.setItem(i, 0, QTableWidgetItem(server_name))
                self.status_table.setItem(i, 1, QTableWidgetItem(server_status.get("status", "unknown")))
                self.status_table.setItem(i, 2, QTableWidgetItem(server_status.get("url", "")))
                self.status_table.setItem(i, 3, QTableWidgetItem(str(len(server_status.get("loaded_models", [])))))
            
            # Update status label
            if "main" in status:
                main_status = status["main"]
                if main_status.get("status") == "running":
                    self.server_status_label.setText("Status: Running")
                    self.server_status_label.setStyleSheet("QLabel { font-weight: bold; padding: 8px; background: #4CAF50; color: white; border-radius: 4px; }")
                else:
                    self.server_status_label.setText("Status: Stopped")
                    self.server_status_label.setStyleSheet("QLabel { font-weight: bold; padding: 8px; background: #f44336; color: white; border-radius: 4px; }")
            
            # Update server info
            self.update_server_info(status)
            
        except Exception as e:
            self.log_message("ERROR", f"Error updating server status: {e}")
    
    def update_model_status(self, models: Dict[str, Any]):
        """Update model status display."""
        try:
            # Update performance table
            self.perf_table.setRowCount(len(models))
            
            for i, (key, info) in enumerate(models.items()):
                self.perf_table.setItem(i, 0, QTableWidgetItem(info["model"]))
                self.perf_table.setItem(i, 1, QTableWidgetItem(info["server"]))
                self.perf_table.setItem(i, 2, QTableWidgetItem("--"))  # TODO: Get actual tokens/sec
                self.perf_table.setItem(i, 3, QTableWidgetItem("--"))  # TODO: Get actual memory usage
                self.perf_table.setItem(i, 4, QTableWidgetItem("--"))  # TODO: Get actual GPU memory usage
                self.perf_table.setItem(i, 5, QTableWidgetItem("Active"))
                
        except Exception as e:
            self.log_message("ERROR", f"Error updating model status: {e}")
    
    def update_server_info(self, status: Dict[str, Any]):
        """Update server information display."""
        try:
            if "main" in status:
                main_status = status["main"]
                info_text = f"Server URL: {main_status.get('url', 'N/A')}\n"
                info_text += f"WebSocket URL: {main_status.get('websocket_url', 'N/A')}\n"
                info_text += f"Loaded Models: {', '.join(main_status.get('loaded_models', []))}\n"
                info_text += f"Available Backends: {', '.join(main_status.get('available_backends', []))}\n"
                
                self.server_info_text.setText(info_text)
            else:
                self.server_info_text.setText("Server not running")
                
        except Exception as e:
            self.log_message("ERROR", f"Error updating server info: {e}")
    
    def update_server_status_display(self):
        """Update the server status display."""
        try:
            status = self.server_manager.get_server_status("main")
            if status.get("status") == "running":
                self.server_status_label.setText("Status: Running")
                self.server_status_label.setStyleSheet("QLabel { font-weight: bold; padding: 8px; background: #4CAF50; color: white; border-radius: 4px; }")
            else:
                self.server_status_label.setText("Status: Stopped")
                self.server_status_label.setStyleSheet("QLabel { font-weight: bold; padding: 8px; background: #f44336; color: white; border-radius: 4px; }")
                
        except Exception as e:
            self.log_message("ERROR", f"Error updating status display: {e}")
    
    def clear_logs(self):
        """Clear the logs display."""
        self.logs_text.clear()
    
    def save_logs(self):
        """Save logs to file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Logs", "", "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.logs_text.toPlainText())
                self.log_message("INFO", f"Logs saved to {file_path}")
                
        except Exception as e:
            self.log_message("ERROR", f"Error saving logs: {e}")
    
    def log_message(self, level: str, message: str):
        """Add a log message to the display."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level.upper()}: {message}\n"
        
        self.logs_text.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.logs_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        try:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.server_manager.cleanup()
            event.accept()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            event.accept()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = LocalModelServerDialog()
    dialog.show()
    sys.exit(app.exec()) 
