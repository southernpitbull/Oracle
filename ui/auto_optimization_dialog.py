# ui/auto_optimization_dialog.py
"""
Auto-optimization settings dialog for The Oracle.

Author: The Oracle Development Team
Date: 2024-12-19
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QComboBox, QCheckBox, QPushButton, QTextEdit,
    QSpinBox, QTabWidget, QWidget, QProgressBar, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

from api.auto_optimizer import (
    AutoOptimizer, AutoOptimizationConfig, OptimizationLevel,
    OptimizationPresets, create_auto_optimizer
)
from .theme_styles import get_dialog_theme_styles


class OptimizationWorker(QThread):
    """Worker thread for running optimization."""
    
    progress_updated = pyqtSignal(str)
    optimization_complete = pyqtSignal(bool, str)
    
    def __init__(self, optimizer: AutoOptimizer):
        super().__init__()
        self.optimizer = optimizer
    
    def run(self):
        """Run the optimization."""
        try:
            self.progress_updated.emit("Starting hardware detection...")
            
            success = self.optimizer.run_optimization()
            
            if success:
                summary = self.optimizer.get_optimization_summary()
                self.optimization_complete.emit(True, summary)
            else:
                self.optimization_complete.emit(False, "Optimization failed")
                
        except Exception as e:
            self.optimization_complete.emit(False, f"Error: {str(e)}")


class AutoOptimizationDialog(QDialog):
    """Dialog for auto-optimization settings."""
    
    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.optimizer = create_auto_optimizer(model_manager)
        self.worker = None
        
        self.setWindowTitle("🔧 Auto-Optimization Settings")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_current_settings()
        self.apply_theme()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Settings tab
        settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        # Hardware info tab
        hardware_tab = self.create_hardware_tab()
        self.tab_widget.addTab(hardware_tab, "💻 Hardware")
        
        # Optimization tab
        optimization_tab = self.create_optimization_tab()
        self.tab_widget.addTab(optimization_tab, "🚀 Optimization")
        
        # Recommendations tab
        recommendations_tab = self.create_recommendations_tab()
        self.tab_widget.addTab(recommendations_tab, "📋 Recommendations")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.run_optimization_btn = QPushButton("🚀 Run Optimization")
        self.run_optimization_btn.clicked.connect(self.run_optimization)
        
        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.close_btn = QPushButton("❌ Close")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.run_optimization_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def create_settings_tab(self) -> QWidget:
        """Create the settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # General settings group
        general_group = QGroupBox("🔧 General Settings")
        general_layout = QGridLayout(general_group)
        
        self.enabled_checkbox = QCheckBox("Enable Auto-Optimization")
        self.enabled_checkbox.setChecked(True)
        general_layout.addWidget(self.enabled_checkbox, 0, 0, 1, 2)
        
        general_layout.addWidget(QLabel("Optimization Level:"), 1, 0)
        self.optimization_level_combo = QComboBox()
        self.optimization_level_combo.addItems([
            "Conservative (Stable, Lower Performance)",
            "Balanced (Good Balance)",
            "Aggressive (High Performance)",
            "Maximum (Maximum Performance, May Be Unstable)"
        ])
        self.optimization_level_combo.setCurrentText("Balanced (Good Balance)")
        general_layout.addWidget(self.optimization_level_combo, 1, 1)
        
        self.auto_detect_checkbox = QCheckBox("Auto-detect on Startup")
        self.auto_detect_checkbox.setChecked(True)
        general_layout.addWidget(self.auto_detect_checkbox, 2, 0, 1, 2)
        
        self.auto_apply_checkbox = QCheckBox("Auto-apply Settings")
        self.auto_apply_checkbox.setChecked(True)
        general_layout.addWidget(self.auto_apply_checkbox, 3, 0, 1, 2)
        
        self.save_profile_checkbox = QCheckBox("Save Hardware Profile")
        self.save_profile_checkbox.setChecked(True)
        general_layout.addWidget(self.save_profile_checkbox, 4, 0, 1, 2)
        
        general_layout.addWidget(QLabel("Update Interval (hours):"), 5, 0)
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 168)  # 1 hour to 1 week
        self.update_interval_spin.setValue(24)
        general_layout.addWidget(self.update_interval_spin, 5, 1)
        
        layout.addWidget(general_group)
        
        # Preset configurations group
        preset_group = QGroupBox("🎯 Preset Configurations")
        preset_layout = QVBoxLayout(preset_group)
        
        preset_buttons_layout = QHBoxLayout()
        
        self.stable_btn = QPushButton("🛡️ Stable")
        self.stable_btn.clicked.connect(lambda: self.apply_preset("stable"))
        
        self.balanced_btn = QPushButton("⚖️ Balanced")
        self.balanced_btn.clicked.connect(lambda: self.apply_preset("balanced"))
        
        self.performance_btn = QPushButton("🚀 Performance")
        self.performance_btn.clicked.connect(lambda: self.apply_preset("performance"))
        
        self.maximum_btn = QPushButton("🔥 Maximum")
        self.maximum_btn.clicked.connect(lambda: self.apply_preset("maximum"))
        
        self.manual_btn = QPushButton("🔧 Manual")
        self.manual_btn.clicked.connect(lambda: self.apply_preset("manual"))
        
        preset_buttons_layout.addWidget(self.stable_btn)
        preset_buttons_layout.addWidget(self.balanced_btn)
        preset_buttons_layout.addWidget(self.performance_btn)
        preset_buttons_layout.addWidget(self.maximum_btn)
        preset_buttons_layout.addWidget(self.manual_btn)
        
        preset_layout.addLayout(preset_buttons_layout)
        
        # Preset descriptions
        preset_desc = QTextEdit()
        preset_desc.setMaximumHeight(100)
        preset_desc.setReadOnly(True)
        preset_desc.setHtml("""
        <h4>Preset Descriptions:</h4>
        <p><strong>Stable:</strong> Conservative settings for maximum stability</p>
        <p><strong>Balanced:</strong> Good balance of performance and stability</p>
        <p><strong>Performance:</strong> Optimized for high performance</p>
        <p><strong>Maximum:</strong> Maximum performance, may be less stable</p>
        <p><strong>Manual:</strong> Disable auto-optimization for manual control</p>
        """)
        preset_layout.addWidget(preset_desc)
        
        layout.addWidget(preset_group)
        layout.addStretch()
        
        return tab
    
    def create_hardware_tab(self) -> QWidget:
        """Create the hardware information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Hardware summary
        summary_group = QGroupBox("💻 Hardware Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.hardware_summary_text = QTextEdit()
        self.hardware_summary_text.setReadOnly(True)
        summary_layout.addWidget(self.hardware_summary_text)
        
        layout.addWidget(summary_group)
        
        # Detailed hardware info
        details_group = QGroupBox("📊 Detailed Information")
        details_layout = QVBoxLayout(details_group)
        
        self.hardware_details_table = QTableWidget()
        self.hardware_details_table.setColumnCount(2)
        self.hardware_details_table.setHorizontalHeaderLabels(["Component", "Details"])
        self.hardware_details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        details_layout.addWidget(self.hardware_details_table)
        
        layout.addWidget(details_group)
        
        return tab
    
    def create_optimization_tab(self) -> QWidget:
        """Create the optimization tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Progress section
        progress_group = QGroupBox("🔄 Optimization Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(100)
        self.progress_text.setReadOnly(True)
        progress_layout.addWidget(self.progress_text)
        
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox("📈 Optimization Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        return tab
    
    def create_recommendations_tab(self) -> QWidget:
        """Create the recommendations tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Recommended models
        models_group = QGroupBox("🤖 Recommended Models")
        models_layout = QVBoxLayout(models_group)
        
        self.recommended_models_table = QTableWidget()
        self.recommended_models_table.setColumnCount(3)
        self.recommended_models_table.setHorizontalHeaderLabels(["Model", "Size", "Reason"])
        self.recommended_models_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        models_layout.addWidget(self.recommended_models_table)
        
        layout.addWidget(models_group)
        
        # Optimization notes
        notes_group = QGroupBox("💡 Optimization Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        self.optimization_notes_text = QTextEdit()
        self.optimization_notes_text.setReadOnly(True)
        notes_layout.addWidget(self.optimization_notes_text)
        
        layout.addWidget(notes_group)
        
        return tab
    
    def load_current_settings(self):
        """Load current optimization settings."""
        config = self.optimizer.config
        
        self.enabled_checkbox.setChecked(config.enabled)
        
        # Set optimization level
        level_map = {
            OptimizationLevel.CONSERVATIVE: 0,
            OptimizationLevel.BALANCED: 1,
            OptimizationLevel.AGGRESSIVE: 2,
            OptimizationLevel.MAXIMUM: 3
        }
        self.optimization_level_combo.setCurrentIndex(level_map.get(config.optimization_level, 1))
        
        self.auto_detect_checkbox.setChecked(config.auto_detect_on_startup)
        self.auto_apply_checkbox.setChecked(config.auto_apply_settings)
        self.save_profile_checkbox.setChecked(config.save_profile)
        self.update_interval_spin.setValue(config.update_interval_hours)
        
        # Load hardware info if available
        self.update_hardware_info()
    
    def update_hardware_info(self):
        """Update hardware information display."""
        system_info = self.optimizer.get_system_info()
        performance_profile = self.optimizer.get_performance_profile()
        
        if system_info:
            # Update hardware summary
            summary = f"""
            <h3>System Information</h3>
            <p><strong>OS:</strong> {system_info.os_name} {system_info.os_version}</p>
            <p><strong>Architecture:</strong> {system_info.os_architecture}</p>
            <p><strong>CPU:</strong> {system_info.cpu.name}</p>
            <p><strong>Cores/Threads:</strong> {system_info.cpu.cores}/{system_info.cpu.threads}</p>
            <p><strong>Memory:</strong> {system_info.memory.total_gb:.1f}GB total, {system_info.memory.available_gb:.1f}GB available</p>
            <p><strong>Storage:</strong> {system_info.storage.total_gb:.1f}GB total, {system_info.storage.available_gb:.1f}GB available {'(SSD)' if system_info.storage.is_ssd else '(HDD)'}</p>
            """
            
            if system_info.gpus:
                summary += "<p><strong>GPUs:</strong></p>"
                for i, gpu in enumerate(system_info.gpus):
                    summary += f"<p>• GPU {i+1}: {gpu.name} ({gpu.vendor.value.title()}, {gpu.memory_gb:.1f}GB)</p>"
            else:
                summary += "<p><strong>GPU:</strong> No dedicated GPU detected</p>"
            
            self.hardware_summary_text.setHtml(summary)
            
            # Update detailed table
            self.update_hardware_details_table(system_info)
        
        if performance_profile:
            # Update results
            self.results_text.setHtml(f"""
            <h3>Performance Profile</h3>
            <p><strong>Recommended Backend:</strong> {performance_profile.recommended_backend.upper()}</p>
            <p><strong>Max Model Size:</strong> {performance_profile.max_model_size_gb}GB</p>
            <p><strong>Optimal Threads:</strong> {performance_profile.optimal_threads}</p>
            <p><strong>GPU Layers:</strong> {performance_profile.gpu_layers}</p>
            <p><strong>Context Length:</strong> {performance_profile.context_length:,}</p>
            <p><strong>Batch Size:</strong> {performance_profile.batch_size}</p>
            <p><strong>Memory Buffer:</strong> {performance_profile.memory_buffer_gb}GB</p>
            """)
            
            # Update recommended models
            self.update_recommended_models_table(performance_profile.recommended_models)
            
            # Update optimization notes
            notes_html = "<h3>Optimization Notes</h3>"
            for note in performance_profile.optimization_notes:
                notes_html += f"<p>• {note}</p>"
            self.optimization_notes_text.setHtml(notes_html)
    
    def update_hardware_details_table(self, system_info):
        """Update the hardware details table."""
        details = [
            ("OS Name", system_info.os_name),
            ("OS Version", system_info.os_version),
            ("OS Architecture", system_info.os_architecture),
            ("Python Version", system_info.python_version),
            ("CPU Name", system_info.cpu.name),
            ("CPU Cores", str(system_info.cpu.cores)),
            ("CPU Threads", str(system_info.cpu.threads)),
            ("CPU Frequency", f"{system_info.cpu.frequency_mhz:.1f} MHz"),
            ("CPU Architecture", system_info.cpu.architecture),
            ("CPU 64-bit", "Yes" if system_info.cpu.is_64bit else "No"),
            ("CPU Manufacturer", system_info.cpu.manufacturer),
            ("Memory Total", f"{system_info.memory.total_gb:.1f} GB"),
            ("Memory Available", f"{system_info.memory.available_gb:.1f} GB"),
            ("Memory Used", f"{system_info.memory.used_gb:.1f} GB"),
            ("Swap Total", f"{system_info.memory.swap_gb:.1f} GB"),
            ("Storage Total", f"{system_info.storage.total_gb:.1f} GB"),
            ("Storage Available", f"{system_info.storage.available_gb:.1f} GB"),
            ("Storage Type", "SSD" if system_info.storage.is_ssd else "HDD"),
            ("Virtual Machine", "Yes" if system_info.is_virtual_machine else "No")
        ]
        
        # Add GPU details
        for i, gpu in enumerate(system_info.gpus):
            details.extend([
                (f"GPU {i+1} Name", gpu.name),
                (f"GPU {i+1} Vendor", gpu.vendor.value.title()),
                (f"GPU {i+1} Memory", f"{gpu.memory_gb:.1f} GB"),
                (f"GPU {i+1} Integrated", "Yes" if gpu.is_integrated else "No"),
                (f"GPU {i+1} CUDA", "Yes" if gpu.supports_cuda else "No"),
                (f"GPU {i+1} Vulkan", "Yes" if gpu.supports_vulkan else "No"),
                (f"GPU {i+1} Metal", "Yes" if gpu.supports_metal else "No"),
                (f"GPU {i+1} OpenCL", "Yes" if gpu.supports_opencl else "No")
            ])
        
        self.hardware_details_table.setRowCount(len(details))
        for i, (component, detail) in enumerate(details):
            self.hardware_details_table.setItem(i, 0, QTableWidgetItem(component))
            self.hardware_details_table.setItem(i, 1, QTableWidgetItem(detail))
    
    def update_recommended_models_table(self, recommended_models):
        """Update the recommended models table."""
        self.recommended_models_table.setRowCount(len(recommended_models))
        
        for i, model_name in enumerate(recommended_models):
            # Get model info
            model_info = self.model_manager.get_model_info(model_name)
            
            if model_info:
                size_gb = model_info.size / (1024**3)
                reason = f"Recommended for {self.optimizer.get_performance_profile().max_model_size_gb}GB max size"
            else:
                size_gb = 0
                reason = "Model not found"
            
            self.recommended_models_table.setItem(i, 0, QTableWidgetItem(model_name))
            self.recommended_models_table.setItem(i, 1, QTableWidgetItem(f"{size_gb:.1f} GB"))
            self.recommended_models_table.setItem(i, 2, QTableWidgetItem(reason))
    
    def apply_preset(self, preset_name: str):
        """Apply a preset configuration."""
        config = OptimizationPresets.get_preset_config(preset_name)
        
        self.enabled_checkbox.setChecked(config.enabled)
        
        level_map = {
            OptimizationLevel.CONSERVATIVE: 0,
            OptimizationLevel.BALANCED: 1,
            OptimizationLevel.AGGRESSIVE: 2,
            OptimizationLevel.MAXIMUM: 3
        }
        self.optimization_level_combo.setCurrentIndex(level_map.get(config.optimization_level, 1))
        
        self.auto_detect_checkbox.setChecked(config.auto_detect_on_startup)
        self.auto_apply_checkbox.setChecked(config.auto_apply_settings)
        self.save_profile_checkbox.setChecked(config.save_profile)
        self.update_interval_spin.setValue(config.update_interval_hours)
        
        QMessageBox.information(self, "Preset Applied", f"Applied {preset_name.title()} preset configuration.")
    
    def run_optimization(self):
        """Run the optimization process."""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Optimization Running", "Optimization is already running. Please wait.")
            return
        
        # Update UI
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_text.clear()
        self.progress_text.append("Starting optimization...")
        self.run_optimization_btn.setEnabled(False)
        
        # Create and start worker
        self.worker = OptimizationWorker(self.optimizer)
        self.worker.progress_updated.connect(self.progress_text.append)
        self.worker.optimization_complete.connect(self.optimization_complete)
        self.worker.start()
    
    def optimization_complete(self, success: bool, result: str):
        """Handle optimization completion."""
        # Update UI
        self.progress_bar.setVisible(False)
        self.run_optimization_btn.setEnabled(True)
        
        if success:
            self.progress_text.append("✅ Optimization completed successfully!")
            self.results_text.setHtml(result)
            self.update_hardware_info()
            QMessageBox.information(self, "Optimization Complete", "Hardware optimization completed successfully!")
        else:
            self.progress_text.append(f"❌ Optimization failed: {result}")
            QMessageBox.warning(self, "Optimization Failed", f"Optimization failed: {result}")
    
    def save_settings(self):
        """Save the current settings."""
        try:
            # Create config from UI
            config = AutoOptimizationConfig(
                enabled=self.enabled_checkbox.isChecked(),
                optimization_level=self.get_optimization_level(),
                auto_detect_on_startup=self.auto_detect_checkbox.isChecked(),
                auto_apply_settings=self.auto_apply_checkbox.isChecked(),
                save_profile=self.save_profile_checkbox.isChecked(),
                update_interval_hours=self.update_interval_spin.value()
            )
            
            # Update optimizer
            self.optimizer.update_config(config)
            
            QMessageBox.information(self, "Settings Saved", "Auto-optimization settings saved successfully!")
            
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Failed to save settings: {str(e)}")
    
    def get_optimization_level(self) -> OptimizationLevel:
        """Get the selected optimization level."""
        level_map = {
            0: OptimizationLevel.CONSERVATIVE,
            1: OptimizationLevel.BALANCED,
            2: OptimizationLevel.AGGRESSIVE,
            3: OptimizationLevel.MAXIMUM
        }
        return level_map.get(self.optimization_level_combo.currentIndex(), OptimizationLevel.BALANCED)
    
    def apply_theme(self):
        """Apply theme styling."""
        self.setStyleSheet(get_dialog_theme_styles()) 
