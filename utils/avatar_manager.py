# utils/avatar_manager.py
"""
Avatar Manager for The Oracle Chat Application

This module manages avatar selection and display for users and AI models,
providing a consistent avatar system throughout the application.

Author: The Oracle Team
Date: 2024
"""

import os
import random
from typing import Dict, List, Optional, Tuple
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QSize, Qt


class AvatarManager:
    """Manages avatar selection and display for chat participants."""
    
    def __init__(self, icons_dir: str = "icons/Avatars"):
        self.icons_dir = icons_dir
        self.avatar_cache: Dict[str, QPixmap] = {}
        self.available_avatars: List[str] = []
        self.user_avatar: Optional[str] = None
        self.ai_avatars: Dict[str, str] = {}
        
        self._load_available_avatars()
        self._assign_default_avatars()
    
    def _load_available_avatars(self):
        """Load all available avatar files from the icons directory."""
        if not os.path.exists(self.icons_dir):
            return
        
        for filename in os.listdir(self.icons_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.available_avatars.append(filename)
        
        # Sort for consistent ordering
        self.available_avatars.sort()
    
    def _assign_default_avatars(self):
        """Assign default avatars for common AI models."""
        # Default AI model avatars
        default_ai_avatars = {
            "GPT-4": "016_businesswoman-3d-icon-download-in-png-blend-fbx-gltf-file-formats--business-woman-young-girl-entrepreneur-employee-people-avatar-pack-icons-4741049.png",
            "GPT-3.5-turbo": "015_male-construction-worker-3d-icon-download-in-png-blend-fbx-gltf-file-formats--contractor-architect-avatar-pack-people-icons-4741048.png",
            "GPT-4-turbo": "017_flight-attendant-3d-icon-download-in-png-blend-fbx-gltf-file-formats--female-stewardess-woman-avatar-pack-people-icons-4741050.png",
            "Claude-3-opus": "124_professor-3d-icon-download-in-png-blend-fbx-gltf-file-formats--teacher-education-teaching-professional-avatar-pack-people-icons-10199753.png",
            "Claude-3-sonnet": "071_teacher-3d-icon-download-in-png-blend-fbx-gltf-file-formats--education-study-learning-professional-avatar-pack-people-icons-10199756.png",
            "Claude-3-haiku": "021_girl-student-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--knowledge-avatar-pack-professionals-illustrations-3930438.png",
            "Gemini-Pro": "086_doctor-3d-icon-download-in-png-blend-fbx-gltf-file-formats--medical-healthcare-health-hospital-medicine-professional-avatar-pack-people-icons-10199758.png",
            "Gemini-Pro-Vision": "020_woman-doctor-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--female-surgeon-avatar-pack-professionals-illustrations-3930437.png",
            "Gemini 2.5 Pro": "131_surgeon-3d-icon-download-in-png-blend-fbx-gltf-file-formats--medical-healthcare-hospital-health-professional-avatar-pack-people-icons-10199757.png",
            "Gemma 3": "022_boy-student-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--kid-person-avatar-pack-professionals-illustrations-3930439.png",
            "llama2": "089_gamer-3d-icon-download-in-png-blend-fbx-gltf-file-formats--gaming-game-technology-professional-avatar-pack-people-icons-10199764.png",
            "mistral": "130_gamers-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--gamer-video-game-cute-boy-profession-pack-professionals-illustrations-4403854.png",
            "codellama": "116_astronout-3d-icon-download-in-png-blend-fbx-gltf-file-formats--space-astronaut-spacesuit-landing-professional-avatar-pack-people-icons-10199752.png",
            "Qwen 3": "135_astronaut-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--spaceman-interstellar-cosmonaut-spacesuit-space-man-profession-pack-professionals-illustrations-4403843.png",
            "Local-GPT": "088_construction-worker-3d-icon-download-in-png-blend-fbx-gltf-file-formats--labour-engineer-professional-avatar-pack-people-icons-10199746.png",
            "Custom-Model": "072_magician-3d-icon-download-in-png-blend-fbx-gltf-file-formats--magic-wizard-hat-wand-witch-professional-avatar-pack-people-icons-10199755.png"
        }
        
        # Assign default avatars
        for model, avatar in default_ai_avatars.items():
            if avatar in self.available_avatars:
                self.ai_avatars[model] = avatar
        
        # Set default user avatar
        user_avatars = [
            "003_man-wearing-shall-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--male-person-avatar-pack-people-illustrations-4800728.png",
            "006_girl-with-red-cloth-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--headband-happy-cute-avatar-pack-professionals-illustrations-4118344.png",
            "007_boy-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--man-fashion-human-avatar-pack-people-illustrations-4107671.png",
            "096_black-woman-3d-illustration-download-in-png-blend-fbx-gltf-file-formats--girl-people-avatar-pack-illustrations-4061807.png"
        ]
        
        for avatar in user_avatars:
            if avatar in self.available_avatars:
                self.user_avatar = avatar
                break
    
    def get_avatar_pixmap(self, avatar_name: str, size: QSize = QSize(40, 40)) -> QPixmap:
        """Get a QPixmap for the specified avatar."""
        cache_key = f"{avatar_name}_{size.width()}_{size.height()}"
        
        if cache_key in self.avatar_cache:
            return self.avatar_cache[cache_key]
        
        avatar_path = os.path.join(self.icons_dir, avatar_name)
        if not os.path.exists(avatar_path):
            # Return a default avatar if the specified one doesn't exist
            return self._create_default_avatar(size)
        
        pixmap = QPixmap(avatar_path)
        if pixmap.isNull():
            return self._create_default_avatar(size)
        
        # Scale the pixmap to the requested size
        scaled_pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # Cache the result
        self.avatar_cache[cache_key] = scaled_pixmap
        return scaled_pixmap
    
    def get_avatar_icon(self, avatar_name: str, size: QSize = QSize(40, 40)) -> QIcon:
        """Get a QIcon for the specified avatar."""
        pixmap = self.get_avatar_pixmap(avatar_name, size)
        return QIcon(pixmap)
    
    def _create_default_avatar(self, size: QSize) -> QPixmap:
        """Create a default avatar when the specified one is not found."""
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.gray)
        return pixmap
    
    def get_user_avatar(self, size: QSize = QSize(40, 40)) -> QPixmap:
        """Get the current user avatar."""
        if self.user_avatar:
            return self.get_avatar_pixmap(self.user_avatar, size)
        return self._create_default_avatar(size)
    
    def get_ai_avatar(self, model_name: str, size: QSize = QSize(40, 40)) -> QPixmap:
        """Get the avatar for a specific AI model."""
        avatar_name = self.ai_avatars.get(model_name)
        if avatar_name:
            return self.get_avatar_pixmap(avatar_name, size)
        
        # If no specific avatar is assigned, use a random one
        if self.available_avatars:
            random_avatar = random.choice(self.available_avatars)
            self.ai_avatars[model_name] = random_avatar
            return self.get_avatar_pixmap(random_avatar, size)
        
        return self._create_default_avatar(size)
    
    def set_user_avatar(self, avatar_name: str):
        """Set the user's avatar."""
        if avatar_name in self.available_avatars:
            self.user_avatar = avatar_name
    
    def set_ai_avatar(self, model_name: str, avatar_name: str):
        """Set the avatar for a specific AI model."""
        if avatar_name in self.available_avatars:
            self.ai_avatars[model_name] = avatar_name
    
    def get_available_avatars(self) -> List[str]:
        """Get a list of all available avatar names."""
        return self.available_avatars.copy()
    
    def get_avatar_display_name(self, avatar_name: str) -> str:
        """Get a human-readable name for an avatar."""
        # Remove file extension and clean up the name
        name = os.path.splitext(avatar_name)[0]
        # Remove the numeric prefix and clean up
        if '_' in name:
            parts = name.split('_', 1)
            if len(parts) > 1:
                name = parts[1]
        
        # Replace underscores with spaces and capitalize
        name = name.replace('_', ' ').title()
        return name
    
    def clear_cache(self):
        """Clear the avatar cache."""
        self.avatar_cache.clear()


# Global instance for easy access
avatar_manager = AvatarManager() 
