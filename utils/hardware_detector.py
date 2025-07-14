# utils/hardware_detector.py
"""
Hardware Detection and Performance Optimization
Author: AI Assistant
Date: 2024-12-19

This module provides comprehensive hardware detection and performance optimization
for AI model inference and training operations.
"""

import os
import sys
import platform
import subprocess
import psutil
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

# Optional imports for enhanced detection
try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import cpuinfo
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False

class GPUVendor(Enum):
    """GPU vendor types."""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    APPLE = "apple"
    UNKNOWN = "unknown"

@dataclass
class CPUInfo:
    """CPU information."""
    name: str
    cores: int
    threads: int
    frequency_mhz: float
    architecture: str
    is_64bit: bool
    cache_size_mb: Optional[float] = None
    manufacturer: str = "Unknown"

@dataclass
class GPUInfo:
    """GPU information."""
    name: str
    vendor: GPUVendor
    memory_gb: float
    compute_capability: Optional[str] = None
    driver_version: Optional[str] = None
    is_integrated: bool = False
    supports_cuda: bool = False
    supports_vulkan: bool = False
    supports_rocm: bool = False
    supports_metal: bool = False
    supports_opencl: bool = False

@dataclass
class MemoryInfo:
    """Memory information."""
    total_gb: float
    available_gb: float
    used_gb: float
    swap_gb: float
    swap_used_gb: float

@dataclass
class StorageInfo:
    """Storage information."""
    total_gb: float
    available_gb: float
    is_ssd: bool
    read_speed_mbps: Optional[float] = None
    write_speed_mbps: Optional[float] = None

@dataclass
class SystemInfo:
    """Complete system information."""
    os_name: str
    os_version: str
    os_architecture: str
    python_version: str
    cpu: CPUInfo
    gpus: List[GPUInfo]
    memory: MemoryInfo
    storage: StorageInfo
    is_virtual_machine: bool = False

@dataclass
class PerformanceProfile:
    """Performance optimization profile."""
    recommended_backend: str
    max_model_size_gb: float
    optimal_threads: int
    gpu_layers: int
    context_length: int
    batch_size: int
    memory_buffer_gb: float
    recommended_models: List[str]
    optimization_notes: List[str]

class HardwareDetector:
    """Hardware detection and performance optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_system(self) -> SystemInfo:
        """Detect complete system information."""
        try:
            cpu = self._detect_cpu()
            gpus = self._detect_gpus()
            memory = self._detect_memory()
            storage = self._detect_storage()
            is_vm = self._detect_virtual_machine()
            
            return SystemInfo(
                os_name=platform.system(),
                os_version=platform.version(),
                os_architecture=platform.machine(),
                python_version=sys.version,
                cpu=cpu,
                gpus=gpus,
                memory=memory,
                storage=storage,
                is_virtual_machine=is_vm
            )
        except Exception as e:
            self.logger.error(f"Error detecting system: {e}")
            # Return minimal system info
            return SystemInfo(
                os_name=platform.system(),
                os_version=platform.version(),
                os_architecture=platform.machine(),
                python_version=sys.version,
                cpu=CPUInfo("Unknown", 1, 1, 0.0, "unknown", False),
                gpus=[],
                memory=MemoryInfo(1.0, 0.5, 0.5, 0.0, 0.0),
                storage=StorageInfo(1.0, 0.5, False),
                is_virtual_machine=False
            )
    
    def _detect_cpu(self) -> CPUInfo:
        """Detect CPU information."""
        try:
            if CPUINFO_AVAILABLE:
                info = cpuinfo.get_cpu_info()
                cpu_name = info.get('brand_raw', 'Unknown CPU')
                cores = psutil.cpu_count(logical=False)
                threads = psutil.cpu_count(logical=True)
                frequency_mhz = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0
                architecture = info.get('arch', 'unknown')
                is_64bit = info.get('bits', 32) == 64
                manufacturer = info.get('vendor_id', 'Unknown')
                
                # Try to get cache size
                cache_size = None
                try:
                    cache_info = info.get('l3_cache_size', '')
                    if cache_info:
                        cache_str = str(cache_info)
                        if "KB" in cache_str:
                            cache_size = float(cache_str.replace("KB", "")) / 1024
                        elif "MB" in cache_str:
                            cache_size = float(cache_str.replace("MB", ""))
                except Exception:
                    pass
                
                return CPUInfo(
                    name=cpu_name,
                    cores=cores,
                    threads=threads,
                    frequency_mhz=frequency_mhz,
                    architecture=architecture,
                    is_64bit=is_64bit,
                    cache_size_mb=cache_size,
                    manufacturer=manufacturer
                )
            
            # Fallback to psutil only
            cpu_name = platform.processor() or "Unknown CPU"
            cores = psutil.cpu_count(logical=False) or 1
            threads = psutil.cpu_count(logical=True) or 1
            frequency_mhz = psutil.cpu_freq().current if psutil.cpu_freq() else 0.0
            architecture = platform.machine()
            is_64bit = sys.maxsize > 2**32
            
            return CPUInfo(
                name=cpu_name,
                cores=cores,
                threads=threads,
                frequency_mhz=frequency_mhz,
                architecture=architecture,
                is_64bit=is_64bit
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting CPU: {e}")
            return CPUInfo(
                name="Unknown",
                cores=1,
                threads=1,
                frequency_mhz=0.0,
                architecture="unknown",
                is_64bit=False
            )
    
    def _detect_gpus(self) -> List[GPUInfo]:
        """Detect GPU information."""
        gpus = []
        
        # Try different GPU detection methods
        if PYNVML_AVAILABLE:
            gpus.extend(self._detect_nvidia_gpus_nvml())
        
        if GPUTIL_AVAILABLE:
            gpus.extend(self._detect_gpus_gputil())
        
        if TORCH_AVAILABLE:
            gpus.extend(self._detect_gpus_torch())
        
        # Fallback to system-specific detection
        if not gpus:
            gpus.extend(self._detect_gpus_system())
        
        return gpus
    
    def _detect_nvidia_gpus_nvml(self) -> List[GPUInfo]:
        """Detect NVIDIA GPUs using NVML."""
        gpus = []
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_gb = memory_info.total / (1024**3)
                
                # Get compute capability
                compute_cap = None
                try:
                    compute_cap = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                    compute_cap = f"{compute_cap[0]}.{compute_cap[1]}"
                except Exception:
                    pass
                
                # Get driver version
                driver_version = None
                try:
                    driver_version = pynvml.nvmlSystemGetDriverVersion().decode('utf-8')
                except Exception:
                    pass
                
                gpus.append(GPUInfo(
                    name=name,
                    vendor=GPUVendor.NVIDIA,
                    memory_gb=memory_gb,
                    compute_capability=compute_cap,
                    driver_version=driver_version,
                    supports_cuda=True,
                    supports_vulkan=True,
                    supports_opencl=True
                ))
            
            pynvml.nvmlShutdown()
            
        except Exception as e:
            self.logger.error(f"Error detecting NVIDIA GPUs: {e}")
        
        return gpus
    
    def _detect_gpus_gputil(self) -> List[GPUInfo]:
        """Detect GPUs using GPUtil."""
        gpus = []
        try:
            gpu_list = GPUtil.getGPUs()
            
            for gpu in gpu_list:
                vendor = GPUVendor.UNKNOWN
                if "nvidia" in gpu.name.lower():
                    vendor = GPUVendor.NVIDIA
                elif "amd" in gpu.name.lower():
                    vendor = GPUVendor.AMD
                elif "intel" in gpu.name.lower():
                    vendor = GPUVendor.INTEL
                
                gpus.append(GPUInfo(
                    name=gpu.name,
                    vendor=vendor,
                    memory_gb=gpu.memoryTotal / 1024,
                    is_integrated=vendor in [GPUVendor.INTEL, GPUVendor.AMD],
                    supports_cuda=vendor == GPUVendor.NVIDIA,
                    supports_vulkan=True,
                    supports_opencl=True
                ))
                
        except Exception as e:
            self.logger.error(f"Error detecting GPUs with GPUtil: {e}")
        
        return gpus
    
    def _detect_gpus_torch(self) -> List[GPUInfo]:
        """Detect GPUs using PyTorch."""
        gpus = []
        try:
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    name = torch.cuda.get_device_name(i)
                    memory_gb = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    
                    gpus.append(GPUInfo(
                        name=name,
                        vendor=GPUVendor.NVIDIA,
                        memory_gb=memory_gb,
                        supports_cuda=True,
                        supports_vulkan=True,
                        supports_opencl=True
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error detecting GPUs with PyTorch: {e}")
        
        return gpus
    
    def _detect_gpus_system(self) -> List[GPUInfo]:
        """Fallback GPU detection using system commands."""
        gpus = []
        
        try:
            if platform.system() == "Windows":
                # Windows GPU detection
                try:
                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split('\n')[1:]
                    for line in lines:
                        if line.strip():
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                name = ' '.join(parts[:-1])
                                memory_bytes = int(parts[-1])
                                memory_gb = memory_bytes / (1024**3)
                                
                                vendor = GPUVendor.UNKNOWN
                                if "nvidia" in name.lower():
                                    vendor = GPUVendor.NVIDIA
                                elif "amd" in name.lower():
                                    vendor = GPUVendor.AMD
                                elif "intel" in name.lower():
                                    vendor = GPUVendor.INTEL
                                
                                gpus.append(GPUInfo(
                                    name=name,
                                    vendor=vendor,
                                    memory_gb=memory_gb,
                                    is_integrated=vendor in [GPUVendor.INTEL, GPUVendor.AMD],
                                    supports_cuda=vendor == GPUVendor.NVIDIA,
                                    supports_vulkan=True,
                                    supports_opencl=True
                                ))
                except Exception:
                    pass
                    
            elif platform.system() == "Linux":
                # Linux GPU detection
                try:
                    result = subprocess.run(
                        ["lspci", "-v"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.split('\n')
                    current_gpu = None
                    
                    for line in lines:
                        if "VGA" in line or "3D" in line:
                            if "nvidia" in line.lower():
                                vendor = GPUVendor.NVIDIA
                                supports_cuda = True
                            elif "amd" in line.lower():
                                vendor = GPUVendor.AMD
                                supports_cuda = False
                            elif "intel" in line.lower():
                                vendor = GPUVendor.INTEL
                                supports_cuda = False
                            else:
                                vendor = GPUVendor.UNKNOWN
                                supports_cuda = False
                            
                            # Extract name
                            name = line.split(':')[-1].strip()
                            if name:
                                gpus.append(GPUInfo(
                                    name=name,
                                    vendor=vendor,
                                    memory_gb=0.0,  # Unknown on Linux
                                    is_integrated=vendor in [GPUVendor.INTEL, GPUVendor.AMD],
                                    supports_cuda=supports_cuda,
                                    supports_vulkan=True,
                                    supports_opencl=True
                                ))
                except Exception:
                    pass
                    
            elif platform.system() == "Darwin":
                # macOS GPU detection
                try:
                    result = subprocess.run(
                        ["system_profiler", "SPDisplaysDataType"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.split('\n')
                    
                    for line in lines:
                        if "Chipset Model:" in line:
                            name = line.split(':')[-1].strip()
                            vendor = GPUVendor.UNKNOWN
                            if "nvidia" in name.lower():
                                vendor = GPUVendor.NVIDIA
                            elif "amd" in name.lower():
                                vendor = GPUVendor.AMD
                            elif "intel" in name.lower():
                                vendor = GPUVendor.INTEL
                            
                            gpus.append(GPUInfo(
                                name=name,
                                vendor=vendor,
                                memory_gb=0.0,  # Unknown on macOS
                                is_integrated=vendor in [GPUVendor.INTEL, GPUVendor.AMD],
                                supports_cuda=vendor == GPUVendor.NVIDIA,
                                supports_vulkan=True,
                                supports_opencl=True
                            ))
                except Exception:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error in system GPU detection: {e}")
        
        return gpus
    
    def _detect_memory(self) -> MemoryInfo:
        """Detect memory information."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return MemoryInfo(
                total_gb=memory.total / (1024**3),
                available_gb=memory.available / (1024**3),
                used_gb=memory.used / (1024**3),
                swap_gb=swap.total / (1024**3),
                swap_used_gb=swap.used / (1024**3)
            )
        except Exception as e:
            self.logger.error(f"Error detecting memory: {e}")
            return MemoryInfo(1.0, 0.5, 0.5, 0.0, 0.0)
    
    def _detect_storage(self) -> StorageInfo:
        """Detect storage information."""
        try:
            # Get the disk where the current directory is located
            current_path = Path.cwd()
            disk_usage = psutil.disk_usage(current_path)
            
            # Try to determine if it's an SSD
            is_ssd = False
            try:
                if platform.system() == "Windows":
                    # Windows SSD detection
                    result = subprocess.run(
                        ["wmic", "diskdrive", "get", "MediaType"],
                        capture_output=True, text=True, timeout=10
                    )
                    if "SSD" in result.stdout:
                        is_ssd = True
                elif platform.system() == "Linux":
                    # Linux SSD detection
                    result = subprocess.run(
                        ["cat", "/sys/block/sda/queue/rotational"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.stdout.strip() == "0":
                        is_ssd = True
            except Exception:
                pass
            
            return StorageInfo(
                total_gb=disk_usage.total / (1024**3),
                available_gb=disk_usage.free / (1024**3),
                is_ssd=is_ssd
            )
        except Exception as e:
            self.logger.error(f"Error detecting storage: {e}")
            return StorageInfo(1.0, 0.5, False)
    
    def _detect_virtual_machine(self) -> bool:
        """Detect if running in a virtual machine."""
        try:
            # Check for common VM indicators
            vm_indicators = [
                "vmware",
                "virtualbox",
                "qemu",
                "xen",
                "hyper-v",
                "parallels"
            ]
            
            # Check system manufacturer
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(
                        ["wmic", "computersystem", "get", "manufacturer"],
                        capture_output=True, text=True, timeout=10
                    )
                    manufacturer = result.stdout.lower()
                    for indicator in vm_indicators:
                        if indicator in manufacturer:
                            return True
                except Exception:
                    pass
            
            # Check for VM-specific files
            vm_files = [
                "/sys/class/dmi/id/product_name",
                "/proc/scsi/scsi",
                "/proc/cpuinfo"
            ]
            
            for vm_file in vm_files:
                try:
                    with open(vm_file, 'r') as f:
                        content = f.read().lower()
                        for indicator in vm_indicators:
                            if indicator in content:
                                return True
                except Exception:
                    pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting VM: {e}")
            return False
    
    def generate_performance_profile(self) -> PerformanceProfile:
        """Generate performance optimization profile."""
        try:
            system = self.detect_system()
            
            backend = self._determine_best_backend(system)
            max_model_size = self._calculate_max_model_size(system)
            optimal_threads = self._calculate_optimal_threads(system)
            gpu_layers = self._calculate_gpu_layers(system)
            context_length = self._determine_context_length(system)
            batch_size = self._determine_batch_size(system)
            memory_buffer = self._calculate_memory_buffer(system)
            recommended_models = self._get_recommended_models(system)
            optimization_notes = self._generate_optimization_notes(system)
            
            return PerformanceProfile(
                recommended_backend=backend,
                max_model_size_gb=max_model_size,
                optimal_threads=optimal_threads,
                gpu_layers=gpu_layers,
                context_length=context_length,
                batch_size=batch_size,
                memory_buffer_gb=memory_buffer,
                recommended_models=recommended_models,
                optimization_notes=optimization_notes
            )
            
        except Exception as e:
            self.logger.error(f"Error generating performance profile: {e}")
            # Return default profile
            return PerformanceProfile(
                recommended_backend="llama.cpp",
                max_model_size_gb=2.0,
                optimal_threads=4,
                gpu_layers=0,
                context_length=2048,
                batch_size=1,
                memory_buffer_gb=0.5,
                recommended_models=["llama-2-7b-chat.gguf"],
                optimization_notes=["Using default profile due to detection errors"]
            )
    
    def _determine_best_backend(self, system: SystemInfo) -> str:
        """Determine the best backend for the system."""
        # Check for CUDA support
        cuda_gpus = [gpu for gpu in system.gpus if gpu.supports_cuda]
        if cuda_gpus:
            return "llama.cpp-cuda"
        
        # Check for Metal support (macOS)
        if platform.system() == "Darwin":
            return "llama.cpp-metal"
        
        # Check for Vulkan support
        vulkan_gpus = [gpu for gpu in system.gpus if gpu.supports_vulkan]
        if vulkan_gpus:
            return "llama.cpp-vulkan"
        
        # Fallback to CPU
        return "llama.cpp"
    
    def _calculate_max_model_size(self, system: SystemInfo) -> float:
        """Calculate maximum model size based on available memory."""
        # Reserve 2GB for system and other processes
        available_memory = system.memory.available_gb - 2.0
        
        # If we have GPU memory, use it
        if system.gpus:
            gpu_memory = max(gpu.memory_gb for gpu in system.gpus)
            available_memory = max(available_memory, gpu_memory * 0.8)
        
        # Cap at reasonable maximum
        return min(available_memory, 32.0)
    
    def _calculate_optimal_threads(self, system: SystemInfo) -> int:
        """Calculate optimal number of threads."""
        # Use 75% of available CPU threads
        optimal = max(1, int(system.cpu.threads * 0.75))
        
        # Don't exceed available memory
        memory_per_thread = 0.5  # GB per thread
        max_by_memory = int(system.memory.available_gb / memory_per_thread)
        
        return min(optimal, max_by_memory)
    
    def _calculate_gpu_layers(self, system: SystemInfo) -> int:
        """Calculate optimal number of GPU layers."""
        if not system.gpus:
            return 0
        
        # Use the most powerful GPU
        best_gpu = max(system.gpus, key=lambda g: g.memory_gb)
        
        if best_gpu.supports_cuda:
            # For CUDA, use more layers
            return min(32, int(best_gpu.memory_gb * 2))
        else:
            # For other backends, be more conservative
            return min(16, int(best_gpu.memory_gb))
    
    def _determine_context_length(self, system: SystemInfo) -> int:
        """Determine optimal context length."""
        # Base context length on available memory
        memory_gb = system.memory.available_gb
        
        if memory_gb >= 16:
            return 8192
        elif memory_gb >= 8:
            return 4096
        elif memory_gb >= 4:
            return 2048
        else:
            return 1024
    
    def _determine_batch_size(self, system: SystemInfo) -> int:
        """Determine optimal batch size."""
        # Conservative batch size
        if system.memory.available_gb >= 16:
            return 4
        elif system.memory.available_gb >= 8:
            return 2
        else:
            return 1
    
    def _calculate_memory_buffer(self, system: SystemInfo) -> float:
        """Calculate memory buffer for operations."""
        # Reserve 20% of available memory as buffer
        return system.memory.available_gb * 0.2
    
    def _get_recommended_models(self, system: SystemInfo) -> List[str]:
        """Get recommended models for the system."""
        max_size = self._calculate_max_model_size(system)
        
        if max_size >= 16:
            return [
                "llama-2-70b-chat.gguf",
                "codellama-34b-instruct.gguf",
                "mistral-7b-instruct-v0.2.gguf"
            ]
        elif max_size >= 8:
            return [
                "llama-2-13b-chat.gguf",
                "codellama-13b-instruct.gguf",
                "mistral-7b-instruct-v0.2.gguf"
            ]
        elif max_size >= 4:
            return [
                "llama-2-7b-chat.gguf",
                "codellama-7b-instruct.gguf",
                "mistral-7b-instruct-v0.2.gguf"
            ]
        else:
            return [
                "llama-2-7b-chat.gguf",
                "tinyllama-1.1b-chat.gguf"
            ]
    
    def _generate_optimization_notes(self, system: SystemInfo) -> List[str]:
        """Generate optimization notes for the system."""
        notes = []
        
        if system.is_virtual_machine:
            notes.append("Running in virtual machine - performance may be limited")
        
        if system.memory.available_gb < 4:
            notes.append("Low memory system - consider closing other applications")
        
        if not system.gpus:
            notes.append("No GPU detected - using CPU-only mode")
        elif not any(gpu.supports_cuda for gpu in system.gpus):
            notes.append("No CUDA-capable GPU - using CPU or alternative acceleration")
        
        if system.cpu.cores < 4:
            notes.append("Low CPU core count - consider upgrading for better performance")
        
        if system.storage.is_ssd:
            notes.append("SSD detected - good for model loading performance")
        else:
            notes.append("HDD detected - model loading may be slower")
        
        return notes
    
    def save_profile(self, filepath: str = None):
        """Save performance profile to file."""
        if filepath is None:
            filepath = "performance_profile.json"
        
        try:
            profile = self.generate_performance_profile()
            
            import json
            from dataclasses import asdict
            
            # Convert to dict
            profile_dict = asdict(profile)
            
            # Add system info
            system = self.detect_system()
            profile_dict['system_info'] = {
                'os_name': system.os_name,
                'os_version': system.os_version,
                'cpu_name': system.cpu.name,
                'cpu_cores': system.cpu.cores,
                'memory_gb': system.memory.total_gb,
                'gpu_count': len(system.gpus),
                'gpu_names': [gpu.name for gpu in system.gpus]
            }
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(profile_dict, f, indent=2)
            
            self.logger.info(f"Performance profile saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving performance profile: {e}")
    
    def get_optimization_summary(self) -> str:
        """Get a human-readable optimization summary."""
        try:
            profile = self.generate_performance_profile()
            system = self.detect_system()
            
            summary = f"""
Performance Optimization Summary
================================

System Information:
- OS: {system.os_name} {system.os_version}
- CPU: {system.cpu.name} ({system.cpu.cores} cores, {system.cpu.threads} threads)
- Memory: {system.memory.total_gb:.1f} GB total, {system.memory.available_gb:.1f} GB available
- GPU: {len(system.gpus)} detected
"""

            if system.gpus:
                for i, gpu in enumerate(system.gpus):
                    summary += f"  - {gpu.name} ({gpu.memory_gb:.1f} GB)\n"
            
            summary += f"""
Optimization Profile:
- Recommended Backend: {profile.recommended_backend}
- Max Model Size: {profile.max_model_size_gb:.1f} GB
- Optimal Threads: {profile.optimal_threads}
- GPU Layers: {profile.gpu_layers}
- Context Length: {profile.context_length}
- Batch Size: {profile.batch_size}
- Memory Buffer: {profile.memory_buffer_gb:.1f} GB

Recommended Models:
"""
            
            for model in profile.recommended_models:
                summary += f"- {model}\n"
            
            if profile.optimization_notes:
                summary += "\nOptimization Notes:\n"
                for note in profile.optimization_notes:
                    summary += f"- {note}\n"
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating optimization summary: {e}")
            return "Error generating optimization summary"


def main():
    """Main function for testing."""
    detector = HardwareDetector()
    
    print("Hardware Detection and Performance Optimization")
    print("=" * 50)
    
    # Detect system
    system = detector.detect_system()
    print(f"OS: {system.os_name} {system.os_version}")
    print(f"CPU: {system.cpu.name}")
    print(f"Memory: {system.memory.total_gb:.1f} GB")
    print(f"GPUs: {len(system.gpus)}")
    
    # Generate profile
    profile = detector.generate_performance_profile()
    print(f"\nRecommended Backend: {profile.recommended_backend}")
    print(f"Max Model Size: {profile.max_model_size_gb:.1f} GB")
    print(f"Optimal Threads: {profile.optimal_threads}")
    
    # Save profile
    detector.save_profile()
    print("\nPerformance profile saved to performance_profile.json")


if __name__ == "__main__":
    main() 
