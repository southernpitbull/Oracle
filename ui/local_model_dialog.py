"""
Local Model Management Dialog for The Oracle AI Chat Application.
Provides UI for downloading, configuring, and managing local models.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, 
    QListWidgetItem, QProgressBar, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QGridLayout, QTabWidget, QWidget, QScrollArea, QFrame,
    QMessageBox, QTextEdit, QCheckBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressDialog, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QFont, QIcon, QPixmap

from api.local_model_manager import LocalModelManager, BackendType, InferenceConfig, ModelInfo, ModelArchitecture
from .theme_styles import get_dialog_theme_styles


class LocalModelDialog(QDialog):
    """Dialog for managing local models."""
    
    def __init__(self, parent=None, dark_theme=True):
        super().__init__(parent)
        self.dark_theme = dark_theme
        self.settings = QSettings("TheOracle", "TheOracle")
        
        # Initialize local model manager
        self.model_manager = LocalModelManager()
        
        # Connect signals
        self.model_manager.model_download_progress.connect(self.on_download_progress)
        self.model_manager.model_download_complete.connect(self.on_download_complete)
        self.model_manager.model_download_error.connect(self.on_download_error)
        
        self.setup_ui()
        self.load_models()
        self.apply_theme()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Local Model Manager - The Oracle")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("🤖 Local Model Manager")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Download and manage local AI models using llama.cpp")
        subtitle_label.setFont(QFont("Arial", 10))
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Available models
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Available models group
        available_group = QGroupBox("📥 Available Models")
        available_layout = QVBoxLayout(available_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Architecture filter
        arch_label = QLabel("Architecture:")
        self.arch_filter = QComboBox()
        self.arch_filter.addItem("All Architectures", None)
        filter_layout.addWidget(arch_label)
        filter_layout.addWidget(self.arch_filter)
        
        # Capability filter
        cap_label = QLabel("Capability:")
        self.cap_filter = QComboBox()
        self.cap_filter.addItem("All Capabilities", None)
        filter_layout.addWidget(cap_label)
        filter_layout.addWidget(self.cap_filter)
        
        # Size filter
        size_label = QLabel("Max Size (GB):")
        self.size_filter = QComboBox()
        self.size_filter.addItems(["Any", "2", "4", "8", "16", "32", "70+"])
        filter_layout.addWidget(size_label)
        filter_layout.addWidget(self.size_filter)
        
        available_layout.addLayout(filter_layout)
        
        # Apply filters button
        apply_filters_btn = QPushButton("🔍 Apply Filters")
        apply_filters_btn.clicked.connect(self.apply_filters)
        available_layout.addWidget(apply_filters_btn)
        
        self.available_list = QListWidget()
        self.available_list.setMinimumHeight(300)
        self.available_list.itemSelectionChanged.connect(self.on_model_selected)
        available_layout.addWidget(self.available_list)
        
        # Download button
        download_btn = QPushButton("📥 Download Selected Model")
        download_btn.clicked.connect(self.download_selected_model)
        available_layout.addWidget(download_btn)
        
        left_layout.addWidget(available_group)
        
        # Downloaded models group
        downloaded_group = QGroupBox("💾 Downloaded Models")
        downloaded_layout = QVBoxLayout(downloaded_group)
        
        self.downloaded_list = QListWidget()
        self.downloaded_list.setMinimumHeight(200)
        self.downloaded_list.itemSelectionChanged.connect(self.on_model_selected)
        downloaded_layout.addWidget(self.downloaded_list)
        
        # Model actions
        actions_layout = QHBoxLayout()
        
        load_btn = QPushButton("🚀 Load Model")
        load_btn.clicked.connect(self.load_selected_model)
        actions_layout.addWidget(load_btn)
        
        delete_btn = QPushButton("🗑️ Delete Model")
        delete_btn.clicked.connect(self.delete_selected_model)
        actions_layout.addWidget(delete_btn)
        
        downloaded_layout.addLayout(actions_layout)
        
        left_layout.addWidget(downloaded_group)
        
        content_splitter.addWidget(left_widget)
        
        # Right side - Model details and configuration
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Model details tab widget
        self.details_tabs = QTabWidget()
        
        # Info tab
        info_tab = self.create_info_tab()
        self.details_tabs.addTab(info_tab, "ℹ️ Info")
        
        # Architecture tab
        arch_tab = self.create_architecture_tab()
        self.details_tabs.addTab(arch_tab, "🏗️ Architecture")
        
        # Configuration tab
        config_tab = self.create_config_tab()
        self.details_tabs.addTab(config_tab, "⚙️ Configuration")
        
        # Backend tab
        backend_tab = self.create_backend_tab()
        self.details_tabs.addTab(backend_tab, "🔧 Backend")
        
        right_layout.addWidget(self.details_tabs)
        
        content_splitter.addWidget(right_widget)
        
        # Set splitter proportions
        content_splitter.setSizes([400, 600])
        
        layout.addWidget(content_splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_models)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_info_tab(self) -> QWidget:
        """Create the model information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Model info display
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        layout.addWidget(self.info_text)
        
        # Model details table
        details_group = QGroupBox("📋 Model Details")
        details_layout = QVBoxLayout(details_group)
        
        self.model_details_table = QTableWidget()
        self.model_details_table.setColumnCount(2)
        self.model_details_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.model_details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        details_layout.addWidget(self.model_details_table)
        
        layout.addWidget(details_group)
        
        # Progress bar for downloads
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        layout.addWidget(self.download_progress)
        
        # System info
        system_group = QGroupBox("🖥️ System Information")
        system_layout = QGridLayout(system_group)
        
        # Backend availability
        backend_label = QLabel("Available Backends:")
        self.backend_status = QLabel("Checking...")
        system_layout.addWidget(backend_label, 0, 0)
        system_layout.addWidget(self.backend_status, 0, 1)
        
        # llama.cpp status
        llama_label = QLabel("llama.cpp Status:")
        self.llama_status = QLabel("Checking...")
        system_layout.addWidget(llama_label, 1, 0)
        system_layout.addWidget(self.llama_status, 1, 1)
        
        # Models directory
        models_label = QLabel("Models Directory:")
        self.models_dir_label = QLabel(str(self.model_manager.models_dir))
        system_layout.addWidget(models_label, 2, 0)
        system_layout.addWidget(self.models_dir_label, 2, 1)
        
        layout.addWidget(system_group)
        layout.addStretch()
        
        return tab
    
    def create_architecture_tab(self) -> QWidget:
        """Create the architecture information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Architecture overview
        overview_group = QGroupBox("🏗️ Architecture Overview")
        overview_layout = QVBoxLayout(overview_group)
        
        self.arch_info_text = QTextEdit()
        self.arch_info_text.setReadOnly(True)
        self.arch_info_text.setMaximumHeight(200)
        overview_layout.addWidget(self.arch_info_text)
        
        layout.addWidget(overview_group)
        
        # Architecture comparison table
        comparison_group = QGroupBox("📊 Architecture Comparison")
        comparison_layout = QVBoxLayout(comparison_group)
        
        self.arch_table = QTableWidget()
        self.arch_table.setColumnCount(5)
        self.arch_table.setHorizontalHeaderLabels(["Architecture", "Creator", "Capabilities", "Typical Size", "License"])
        self.arch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        comparison_layout.addWidget(self.arch_table)
        
        layout.addWidget(comparison_group)
        layout.addStretch()
        
        return tab
    
    def create_config_tab(self) -> QWidget:
        """Create the model configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Inference parameters
        params_group = QGroupBox("🎛️ Inference Parameters")
        params_layout = QGridLayout(params_group)
        
        # Temperature
        temp_label = QLabel("Temperature:")
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setValue(0.7)
        self.temperature_spin.setSingleStep(0.1)
        params_layout.addWidget(temp_label, 0, 0)
        params_layout.addWidget(self.temperature_spin, 0, 1)
        
        # Top P
        top_p_label = QLabel("Top P:")
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setValue(1.0)
        self.top_p_spin.setSingleStep(0.1)
        params_layout.addWidget(top_p_label, 1, 0)
        params_layout.addWidget(self.top_p_spin, 1, 1)
        
        # Top K
        top_k_label = QLabel("Top K:")
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 100)
        self.top_k_spin.setValue(40)
        params_layout.addWidget(top_k_label, 2, 0)
        params_layout.addWidget(self.top_k_spin, 2, 1)
        
        # Repeat Penalty
        repeat_label = QLabel("Repeat Penalty:")
        self.repeat_penalty_spin = QDoubleSpinBox()
        self.repeat_penalty_spin.setRange(1.0, 2.0)
        self.repeat_penalty_spin.setValue(1.1)
        self.repeat_penalty_spin.setSingleStep(0.1)
        params_layout.addWidget(repeat_label, 3, 0)
        params_layout.addWidget(self.repeat_penalty_spin, 3, 1)
        
        # Max Tokens
        max_tokens_label = QLabel("Max Tokens:")
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 8192)
        self.max_tokens_spin.setValue(2048)
        params_layout.addWidget(max_tokens_label, 4, 0)
        params_layout.addWidget(self.max_tokens_spin, 4, 1)
        
        # Context Length
        context_label = QLabel("Context Length:")
        self.context_length_spin = QSpinBox()
        self.context_length_spin.setRange(512, 32768)
        self.context_length_spin.setValue(4096)
        params_layout.addWidget(context_label, 5, 0)
        params_layout.addWidget(self.context_length_spin, 5, 1)
        
        layout.addWidget(params_group)
        
        # Threads and GPU
        hardware_group = QGroupBox("💻 Hardware Configuration")
        hardware_layout = QGridLayout(hardware_group)
        
        # Threads
        threads_label = QLabel("CPU Threads:")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(-1, 32)
        self.threads_spin.setValue(-1)
        self.threads_spin.setToolTip("-1 for auto-detect")
        hardware_layout.addWidget(threads_label, 0, 0)
        hardware_layout.addWidget(self.threads_spin, 0, 1)
        
        # GPU Layers
        gpu_layers_label = QLabel("GPU Layers:")
        self.gpu_layers_spin = QSpinBox()
        self.gpu_layers_spin.setRange(0, 100)
        self.gpu_layers_spin.setValue(0)
        hardware_layout.addWidget(gpu_layers_label, 1, 0)
        hardware_layout.addWidget(self.gpu_layers_spin, 1, 1)
        
        layout.addWidget(hardware_group)
        layout.addStretch()
        
        return tab
    
    def create_backend_tab(self) -> QWidget:
        """Create the backend configuration tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Backend selection
        backend_group = QGroupBox("🔧 Backend Configuration")
        backend_layout = QVBoxLayout(backend_group)
        
        # Backend combo box
        backend_label = QLabel("Select Backend:")
        self.backend_combo = QComboBox()
        for backend in BackendType:
            self.backend_combo.addItem(backend.value.title(), backend)
        backend_layout.addWidget(backend_label)
        backend_layout.addWidget(self.backend_combo)
        
        # Backend info
        self.backend_info = QTextEdit()
        self.backend_info.setReadOnly(True)
        self.backend_info.setMaximumHeight(150)
        backend_layout.addWidget(self.backend_info)
        
        layout.addWidget(backend_group)
        
        # Backend status table
        status_group = QGroupBox("📊 Backend Status")
        status_layout = QVBoxLayout(status_group)
        
        self.backend_table = QTableWidget()
        self.backend_table.setColumnCount(3)
        self.backend_table.setHorizontalHeaderLabels(["Backend", "Status", "Details"])
        self.backend_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        status_layout.addWidget(self.backend_table)
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        return tab
    
    def load_models(self):
        """Load available and downloaded models."""
        # Clear lists
        self.available_list.clear()
        self.downloaded_list.clear()
        
        # Load available models
        available_models = self.model_manager.get_available_models()
        for model_name, model_info in available_models.items():
            if not self.model_manager.is_model_downloaded(model_name):
                item = QListWidgetItem(f"{model_info.name} ({model_info.parameters // 1_000_000_000}B)")
                item.setData(Qt.ItemDataRole.UserRole, model_name)
                item.setToolTip(model_info.description)
                self.available_list.addItem(item)
        
        # Load downloaded models
        downloaded_models = self.model_manager.get_downloaded_models()
        for model_name in downloaded_models:
            item = QListWidgetItem(model_name)
            item.setData(Qt.ItemDataRole.UserRole, model_name)
            self.downloaded_list.addItem(item)
        
        # Update filters
        self.update_filters()
        
        # Update system info
        self.update_system_info()
        
        # Update architecture info
        self.update_architecture_info()
    
    def update_filters(self):
        """Update filter dropdowns with available options."""
        # Architecture filter
        self.arch_filter.clear()
        self.arch_filter.addItem("All Architectures", None)
        
        architectures = self.model_manager.get_model_architectures()
        for arch in architectures:
            self.arch_filter.addItem(arch.value.title(), arch)
        
        # Capability filter
        self.cap_filter.clear()
        self.cap_filter.addItem("All Capabilities", None)
        
        capabilities = self.model_manager.get_model_capabilities()
        for cap in capabilities:
            self.cap_filter.addItem(cap.title(), cap)
    
    def apply_filters(self):
        """Apply selected filters to the model list."""
        self.available_list.clear()
        
        # Get filter values
        selected_arch = self.arch_filter.currentData()
        selected_cap = self.cap_filter.currentData()
        selected_size = self.size_filter.currentText()
        
        # Get filtered models
        available_models = self.model_manager.get_available_models()
        filtered_models = {}
        
        for model_name, model_info in available_models.items():
            if not self.model_manager.is_model_downloaded(model_name):
                # Apply architecture filter
                if selected_arch and model_info.architecture != selected_arch:
                    continue
                
                # Apply capability filter
                if selected_cap and (not model_info.capabilities or selected_cap not in model_info.capabilities):
                    continue
                
                # Apply size filter
                if selected_size != "Any":
                    if selected_size == "70+":
                        if model_info.size < 70 * 1024 * 1024 * 1024:
                            continue
                    else:
                        max_size = float(selected_size) * 1024 * 1024 * 1024
                        if model_info.size > max_size:
                            continue
                
                filtered_models[model_name] = model_info
        
        # Update list with filtered models
        for model_name, model_info in filtered_models.items():
            item = QListWidgetItem(f"{model_info.name} ({model_info.parameters // 1_000_000_000}B)")
            item.setData(Qt.ItemDataRole.UserRole, model_name)
            item.setToolTip(model_info.description)
            self.available_list.addItem(item)
    
    def update_architecture_info(self):
        """Update architecture information display."""
        # Update architecture overview
        arch_info = self.model_manager.get_architecture_info(ModelArchitecture.LLAMA)
        overview_text = f"""
        <h3>Architecture Overview</h3>
        <p><strong>Total Architectures:</strong> {len(self.model_manager.get_model_architectures())}</p>
        <p><strong>Total Capabilities:</strong> {len(self.model_manager.get_model_capabilities())}</p>
        <p><strong>Available Models:</strong> {len(self.model_manager.get_available_models())}</p>
        """
        self.arch_info_text.setHtml(overview_text)
        
        # Update architecture comparison table
        architectures = self.model_manager.get_model_architectures()
        self.arch_table.setRowCount(len(architectures))
        
        for i, arch in enumerate(architectures):
            arch_info = self.model_manager.get_architecture_info(arch)
            
            # Architecture name
            name_item = QTableWidgetItem(arch.value.title())
            self.arch_table.setItem(i, 0, name_item)
            
            # Creator (get from first model of this architecture)
            models = self.model_manager.get_models_by_architecture(arch)
            creator = "Unknown"
            if models:
                first_model = list(models.values())[0]
                creator = first_model.creator
            creator_item = QTableWidgetItem(creator)
            self.arch_table.setItem(i, 1, creator_item)
            
            # Capabilities
            capabilities = ", ".join(arch_info["capabilities"])
            cap_item = QTableWidgetItem(capabilities)
            self.arch_table.setItem(i, 2, cap_item)
            
            # Typical size
            size_text = "2-8GB"
            if arch in [ModelArchitecture.MIXTRAL, ModelArchitecture.LLAMA3]:
                size_text = "8-70GB"
            elif arch in [ModelArchitecture.PHI, ModelArchitecture.GEMMA]:
                size_text = "1-4GB"
            size_item = QTableWidgetItem(size_text)
            self.arch_table.setItem(i, 3, size_item)
            
            # License
            license_text = "Various"
            if models:
                first_model = list(models.values())[0]
                license_text = first_model.license
            license_item = QTableWidgetItem(license_text)
            self.arch_table.setItem(i, 4, license_item)
    
    def update_system_info(self):
        """Update system information display."""
        # Backend status
        available_backends = []
        for backend in BackendType:
            if backend in self.model_manager.get_supported_backends():
                available_backends.append(backend.value)
        
        self.backend_status.setText(", ".join(available_backends) if available_backends else "None")
        
        # llama.cpp status
        if self.model_manager.llama_cpp_path:
            self.llama_status.setText("✅ Available")
        else:
            self.llama_status.setText("❌ Not found")
        
        # Update backend table
        self.update_backend_table()
    
    def update_backend_table(self):
        """Update the backend status table."""
        self.backend_table.setRowCount(len(BackendType))
        
        for i, backend in enumerate(BackendType):
            # Backend name
            name_item = QTableWidgetItem(backend.value.title())
            self.backend_table.setItem(i, 0, name_item)
            
            # Status
            if backend in self.model_manager.get_supported_backends():
                status_item = QTableWidgetItem("✅ Available")
            else:
                status_item = QTableWidgetItem("❌ Not available")
            self.backend_table.setItem(i, 1, status_item)
            
            # Details
            details = self.get_backend_details(backend)
            details_item = QTableWidgetItem(details)
            self.backend_table.setItem(i, 2, details_item)
    
    def get_backend_details(self, backend: BackendType) -> str:
        """Get details for a specific backend."""
        if backend == BackendType.CPU:
            return "CPU-based inference"
        elif backend == BackendType.CUDA:
            return "NVIDIA GPU acceleration"
        elif backend == BackendType.VULKAN:
            return "Vulkan GPU acceleration"
        elif backend == BackendType.ROCM:
            return "AMD GPU acceleration"
        return "Unknown"
    
    def download_selected_model(self):
        """Download the selected model."""
        current_item = self.available_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a model to download.")
            return
        
        model_name = current_item.data(Qt.ItemDataRole.UserRole)
        model_info = self.model_manager.get_model_info(model_name)
        
        if not model_info:
            QMessageBox.error(self, "Error", "Model information not found.")
            return
        
        # Show confirmation dialog with detailed information
        size_mb = model_info.size / (1024 * 1024)
        size_gb = size_mb / 1024
        
        capabilities_text = ", ".join(model_info.capabilities) if model_info.capabilities else "None"
        
        confirmation_text = f"""
Download {model_name}?

📊 Model Information:
• Size: {size_gb:.1f} GB ({size_mb:.0f} MB)
• Architecture: {model_info.architecture.value.title()}
• Parameters: {model_info.parameters // 1_000_000_000}B
• Context Length: {model_info.context_length:,}
• Creator: {model_info.creator}
• License: {model_info.license}
• Capabilities: {capabilities_text}

📝 Description: {model_info.description}

This may take a while depending on your internet connection.
        """
        
        reply = QMessageBox.question(
            self, "Download Model", confirmation_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_download(model_name)
    
    def update_model_info_display(self, model_name: str):
        """Update the model information display for a selected model."""
        model_info = self.model_manager.get_model_info(model_name)
        if not model_info:
            return
        
        # Update info text
        size_mb = model_info.size / (1024 * 1024)
        size_gb = size_mb / 1024
        
        info_text = f"""
        <h3>{model_info.name}</h3>
        <p><strong>Description:</strong> {model_info.description}</p>
        <p><strong>Size:</strong> {size_gb:.1f} GB ({size_mb:.0f} MB)</p>
        <p><strong>Architecture:</strong> {model_info.architecture.value.title()}</p>
        <p><strong>Parameters:</strong> {model_info.parameters // 1_000_000_000}B</p>
        <p><strong>Context Length:</strong> {model_info.context_length:,}</p>
        <p><strong>Creator:</strong> {model_info.creator}</p>
        <p><strong>License:</strong> {model_info.license}</p>
        """
        
        if model_info.capabilities:
            capabilities_text = ", ".join(model_info.capabilities)
            info_text += f"<p><strong>Capabilities:</strong> {capabilities_text}</p>"
        
        self.info_text.setHtml(info_text)
        
        # Update details table
        details = [
            ("Name", model_info.name),
            ("Filename", model_info.filename),
            ("Size", f"{size_gb:.1f} GB"),
            ("Architecture", model_info.architecture.value.title()),
            ("Parameters", f"{model_info.parameters // 1_000_000_000}B"),
            ("Context Length", f"{model_info.context_length:,}"),
            ("Quantization", model_info.quantization),
            ("Creator", model_info.creator),
            ("License", model_info.license),
            ("Training Data", model_info.training_data),
            ("Backend", model_info.backend.value.title())
        ]
        
        self.model_details_table.setRowCount(len(details))
        for i, (property_name, value) in enumerate(details):
            self.model_details_table.setItem(i, 0, QTableWidgetItem(property_name))
            self.model_details_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def on_model_selected(self):
        """Handle model selection in either list."""
        # Check which list has the selection
        available_item = self.available_list.currentItem()
        downloaded_item = self.downloaded_list.currentItem()
        
        if available_item:
            model_name = available_item.data(Qt.ItemDataRole.UserRole)
            self.update_model_info_display(model_name)
        elif downloaded_item:
            model_name = downloaded_item.data(Qt.ItemDataRole.UserRole)
            self.update_model_info_display(model_name)
    
    def start_download(self, model_name: str):
        """Start downloading a model."""
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.status_label.setText(f"Downloading {model_name}...")
        
        success = self.model_manager.download_model(model_name)
        if not success:
            self.download_progress.setVisible(False)
            self.status_label.setText("Download failed to start")
    
    def on_download_progress(self, model_name: str, progress: int):
        """Handle download progress updates."""
        self.download_progress.setValue(progress)
        self.status_label.setText(f"Downloading {model_name}: {progress}%")
    
    def on_download_complete(self, model_name: str, model_path: str):
        """Handle download completion."""
        self.download_progress.setVisible(False)
        self.status_label.setText(f"Download complete: {model_name}")
        self.load_models()  # Refresh the lists
        
        QMessageBox.information(
            self, "Download Complete",
            f"Model {model_name} has been downloaded successfully!\n\n"
            f"Path: {model_path}"
        )
    
    def on_download_error(self, model_name: str, error: str):
        """Handle download errors."""
        self.download_progress.setVisible(False)
        self.status_label.setText(f"Download failed: {model_name}")
        
        QMessageBox.critical(
            self, "Download Error",
            f"Failed to download {model_name}:\n\n{error}"
        )
    
    def load_selected_model(self):
        """Load the selected downloaded model."""
        current_item = self.downloaded_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a model to load.")
            return
        
        model_name = current_item.data(Qt.ItemDataRole.UserRole)
        backend = self.backend_combo.currentData()
        
        try:
            success = self.model_manager.load_model(model_name, backend)
            if success:
                self.status_label.setText(f"Model {model_name} loaded successfully")
                QMessageBox.information(
                    self, "Model Loaded",
                    f"Model {model_name} has been loaded with {backend.value} backend."
                )
            else:
                QMessageBox.warning(
                    self, "Load Failed",
                    f"Failed to load model {model_name}."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Error loading model {model_name}:\n\n{str(e)}"
            )
    
    def delete_selected_model(self):
        """Delete the selected downloaded model."""
        current_item = self.downloaded_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a model to delete.")
            return
        
        model_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, "Delete Model",
            f"Are you sure you want to delete {model_name}?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                model_path = self.model_manager.downloaded_models[model_name]
                os.remove(model_path)
                self.status_label.setText(f"Model {model_name} deleted")
                self.load_models()  # Refresh the lists
            except Exception as e:
                QMessageBox.critical(
                    self, "Delete Error",
                    f"Failed to delete model {model_name}:\n\n{str(e)}"
                )
    
    def apply_theme(self):
        """Apply the current theme to the dialog."""
        theme_styles = get_dialog_theme_styles(self.dark_theme)
        self.setStyleSheet(theme_styles)
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        # Cleanup model manager
        self.model_manager.cleanup()
        event.accept() 
