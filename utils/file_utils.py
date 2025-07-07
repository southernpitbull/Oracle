"""
File utilities for handling attachments, exports, and file operations.
"""

import os
import json
import shutil
import zipfile
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Directories
ATTACHMENTS_DIR = "attachments"
EXPORTS_DIR = "exports"
MEMORY_DB = "memory.db"

# Ensure directories exist
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(os.path.join(ATTACHMENTS_DIR, "user"), exist_ok=True)
os.makedirs(os.path.join(ATTACHMENTS_DIR, "assistant"), exist_ok=True)


def get_attachments_dir():
    """Get the attachments directory path"""
    return ATTACHMENTS_DIR


def get_exports_dir():
    """Get the exports directory path"""
    return EXPORTS_DIR


def get_user_attachments_dir():
    """Get the user attachments directory path"""
    return os.path.join(ATTACHMENTS_DIR, "user")


def get_assistant_attachments_dir():
    """Get the assistant attachments directory path"""
    return os.path.join(ATTACHMENTS_DIR, "assistant")


def save_attachment(content, filename, is_user=True):
    """Save an attachment file"""
    try:
        if is_user:
            dir_path = get_user_attachments_dir()
        else:
            dir_path = get_assistant_attachments_dir()
        
        filepath = os.path.join(dir_path, filename)
        
        # Handle different content types
        if isinstance(content, str):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        elif isinstance(content, bytes):
            with open(filepath, 'wb') as f:
                f.write(content)
        else:
            # Try to convert to string
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(content))
        
        logger.info(f"Saved attachment: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save attachment {filename}: {e}")
        return None


def load_attachment(filename, is_user=True):
    """Load an attachment file"""
    try:
        if is_user:
            dir_path = get_user_attachments_dir()
        else:
            dir_path = get_assistant_attachments_dir()
        
        filepath = os.path.join(dir_path, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Attachment file not found: {filepath}")
            return None
    except Exception as e:
        logger.error(f"Failed to load attachment {filename}: {e}")
        return None


def export_to_json(data, filename=None):
    """Export data to JSON file"""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.json"
        
        filepath = os.path.join(get_exports_dir(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported to JSON: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to export to JSON: {e}")
        return None


def export_to_txt(text, filename=None):
    """Export text to TXT file"""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.txt"
        
        filepath = os.path.join(get_exports_dir(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Exported to TXT: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to export to TXT: {e}")
        return None


def export_to_html(html_content, filename=None):
    """Export HTML content to HTML file"""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.html"
        
        filepath = os.path.join(get_exports_dir(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Exported to HTML: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to export to HTML: {e}")
        return None


def create_export_archive(files, archive_name=None):
    """Create a ZIP archive of export files"""
    try:
        if archive_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"export_archive_{timestamp}.zip"
        
        archive_path = os.path.join(get_exports_dir(), archive_name)
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                if os.path.exists(file_path):
                    # Add file to archive with just the filename (no path)
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created export archive: {archive_path}")
        return archive_path
    except Exception as e:
        logger.error(f"Failed to create export archive: {e}")
        return None


def clean_old_exports(days_old=30):
    """Clean up old export files"""
    try:
        exports_dir = get_exports_dir()
        current_time = datetime.now()
        
        for filename in os.listdir(exports_dir):
            filepath = os.path.join(exports_dir, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                age_days = (current_time - file_time).days
                
                if age_days > days_old:
                    os.remove(filepath)
                    logger.info(f"Removed old export file: {filepath}")
    except Exception as e:
        logger.error(f"Failed to clean old exports: {e}")


def get_file_size(filepath):
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Failed to get file size for {filepath}: {e}")
        return 0


def get_file_extension(filepath):
    """Get file extension"""
    return os.path.splitext(filepath)[1].lower()


def is_text_file(filepath):
    """Check if file is a text file"""
    text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.ini', '.cfg'}
    return get_file_extension(filepath) in text_extensions


def is_image_file(filepath):
    """Check if file is an image file"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
    return get_file_extension(filepath) in image_extensions


def read_file_content(filepath):
    """Read file content based on file type"""
    try:
        if is_text_file(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif is_image_file(filepath):
            with open(filepath, 'rb') as f:
                return f.read()
        else:
            # Try to read as text first
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # If text reading fails, read as binary
                with open(filepath, 'rb') as f:
                    return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {filepath}: {e}")
        return None
