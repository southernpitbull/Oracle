"""
Text formatting utilities for chat messages and system messages.
"""

import re
import html
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    markdown = None

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    highlight = None
    get_lexer_by_name = None
    TextLexer = None
    HtmlFormatter = None


def format_chat_message(role, content, timestamp=None, enable_markdown=True):
    """Format a chat message with proper styling"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Escape HTML entities
    content = html.escape(content)
    
    # Apply markdown formatting if enabled
    if enable_markdown and MARKDOWN_AVAILABLE:
        try:
            content = markdown.markdown(content, extensions=['codehilite', 'fenced_code'])
        except Exception as e:
            logger.warning(f"Markdown formatting failed: {e}")
    
    # Format based on role
    if role.lower() == "user":
        return f"""
        <div class="user-message">
            <div class="message-header">
                <span class="role">You</span>
                <span class="timestamp">{timestamp}</span>
            </div>
            <div class="message-content">{content}</div>
        </div>
        """
    elif role.lower() == "assistant":
        return f"""
        <div class="assistant-message">
            <div class="message-header">
                <span class="role">Assistant</span>
                <span class="timestamp">{timestamp}</span>
            </div>
            <div class="message-content">{content}</div>
        </div>
        """
    else:
        return f"""
        <div class="system-message">
            <div class="message-header">
                <span class="role">{role}</span>
                <span class="timestamp">{timestamp}</span>
            </div>
            <div class="message-content">{content}</div>
        </div>
        """


def format_system_message(content, message_type="info"):
    """Format a system message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Escape HTML entities
    content = html.escape(content)
    
    # Choose icon based on message type
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅"
    }
    
    icon = icons.get(message_type, "ℹ️")
    
    return f"""
    <div class="system-message {message_type}">
        <div class="message-header">
            <span class="icon">{icon}</span>
            <span class="role">System</span>
            <span class="timestamp">{timestamp}</span>
        </div>
        <div class="message-content">{content}</div>
    </div>
    """


def format_code_block(code, language="", enable_syntax_highlighting=True):
    """Format a code block with syntax highlighting"""
    if not code.strip():
        return ""
    
    if enable_syntax_highlighting and PYGMENTS_AVAILABLE:
        try:
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                lexer = TextLexer()
            
            formatter = HtmlFormatter(
                style='monokai',
                cssclass='highlight',
                noclasses=False
            )
            
            highlighted = highlight(code, lexer, formatter)
            return f'<div class="code-block">{highlighted}</div>'
        except Exception as e:
            logger.warning(f"Syntax highlighting failed: {e}")
    
    # Fallback to simple HTML formatting
    escaped_code = html.escape(code)
    return f'''
    <div class="code-block">
        <pre><code class="language-{language}">{escaped_code}</code></pre>
    </div>
    '''


def format_thinking_block(content):
    """Format a thinking block (for models that show reasoning)"""
    if not content.strip():
        return ""
    
    escaped_content = html.escape(content)
    
    return f'''
    <div class="thinking-block">
        <div class="thinking-header">
            <span class="thinking-icon">🤔</span>
            <span class="thinking-label">Thinking...</span>
        </div>
        <div class="thinking-content">{escaped_content}</div>
    </div>
    '''


def format_table(table_data, headers=None):
    """Format table data as HTML"""
    if not table_data:
        return ""
    
    html_table = '<table class="formatted-table">'
    
    # Add headers if provided
    if headers:
        html_table += '<thead><tr>'
        for header in headers:
            html_table += f'<th>{html.escape(str(header))}</th>'
        html_table += '</tr></thead>'
    
    # Add data rows
    html_table += '<tbody>'
    for row in table_data:
        html_table += '<tr>'
        for cell in row:
            html_table += f'<td>{html.escape(str(cell))}</td>'
        html_table += '</tr>'
    html_table += '</tbody>'
    
    html_table += '</table>'
    return html_table


def format_list(items, ordered=False):
    """Format a list as HTML"""
    if not items:
        return ""
    
    tag = 'ol' if ordered else 'ul'
    html_list = f'<{tag} class="formatted-list">'
    
    for item in items:
        html_list += f'<li>{html.escape(str(item))}</li>'
    
    html_list += f'</{tag}>'
    return html_list


def extract_code_blocks(text):
    """Extract code blocks from text"""
    # Pattern to match code blocks with optional language specifier
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for match in matches:
        language = match[0] if match[0] else 'text'
        code = match[1]
        code_blocks.append({'language': language, 'code': code})
    
    return code_blocks


def clean_text(text):
    """Clean text by removing extra whitespace and normalizing"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def truncate_text(text, max_length=100, suffix="..."):
    """Truncate text to a maximum length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters"""
    # Remove invalid characters for Windows/Linux filenames
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename


def highlight_search_terms(text, search_terms, highlight_class="highlight"):
    """Highlight search terms in text"""
    if not text or not search_terms:
        return text
    
    # Escape HTML first
    text = html.escape(text)
    
    # Highlight each search term
    for term in search_terms:
        if term:
            # Escape special regex characters in search term
            escaped_term = re.escape(term)
            pattern = f'({escaped_term})'
            replacement = f'<span class="{highlight_class}">\\1</span>'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds):
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {remaining_seconds:.1f}s"
    else:
        hours = seconds // 3600
        remaining_seconds = seconds % 3600
        minutes = remaining_seconds // 60
        remaining_seconds = remaining_seconds % 60
        return f"{int(hours)}h {int(minutes)}m {remaining_seconds:.1f}s"
