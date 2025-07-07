"""
Utility modules for The Oracle chat application.
"""

from .dependencies import check_and_install_dependencies, add_python_to_path
from .file_utils import (
    get_attachments_dir, get_exports_dir, get_user_attachments_dir,
    get_assistant_attachments_dir, save_attachment, load_attachment,
    export_to_json, export_to_txt, export_to_html, create_export_archive,
    clean_old_exports, get_file_size, get_file_extension, is_text_file,
    is_image_file, read_file_content
)
from .formatting import (
    format_chat_message, format_system_message, format_code_block,
    format_thinking_block, format_table, format_list, extract_code_blocks,
    clean_text, truncate_text, sanitize_filename, highlight_search_terms,
    format_file_size, format_duration
)

__all__ = [
    # Dependencies
    'check_and_install_dependencies',
    'add_python_to_path',
    
    # File utilities
    'get_attachments_dir',
    'get_exports_dir',
    'get_user_attachments_dir',
    'get_assistant_attachments_dir',
    'save_attachment',
    'load_attachment',
    'export_to_json',
    'export_to_txt',
    'export_to_html',
    'create_export_archive',
    'clean_old_exports',
    'get_file_size',
    'get_file_extension',
    'is_text_file',
    'is_image_file',
    'read_file_content',
    
    # Formatting utilities
    'format_chat_message',
    'format_system_message',
    'format_code_block',
    'format_thinking_block',
    'format_table',
    'format_list',
    'extract_code_blocks',
    'clean_text',
    'truncate_text',
    'sanitize_filename',
    'highlight_search_terms',
    'format_file_size',
    'format_duration'
]
