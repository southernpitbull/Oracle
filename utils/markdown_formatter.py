# utils/markdown_formatter.py
"""
Markdown Formatter Utility for The Oracle Chat Application

This module provides markdown to HTML conversion for chat messages,
including syntax highlighting for code blocks and proper formatting
for various markdown elements.

Author: The Oracle Team
Date: 2024
"""

import re
import html
from typing import Dict, List, Optional
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound


class MarkdownFormatter:
    """Converts markdown text to HTML with syntax highlighting."""
    
    def __init__(self):
        self.code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        self.inline_code_pattern = re.compile(r'`([^`]+)`')
        self.bold_pattern = re.compile(r'\*\*(.*?)\*\*')
        self.italic_pattern = re.compile(r'\*(.*?)\*')
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        self.list_pattern = re.compile(r'^[\s]*[-*+]\s+(.+)$', re.MULTILINE)
        self.numbered_list_pattern = re.compile(r'^[\s]*\d+\.\s+(.+)$', re.MULTILINE)
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.blockquote_pattern = re.compile(r'^>\s+(.+)$', re.MULTILINE)
        self.horizontal_rule_pattern = re.compile(r'^---$', re.MULTILINE)
        
    def format_markdown(self, text: str) -> str:
        """Convert markdown text to HTML."""
        if not text:
            return ""
        
        # Escape HTML characters first
        text = html.escape(text)
        
        # Process code blocks first (before other formatting)
        text = self._process_code_blocks(text)
        
        # Process other markdown elements
        text = self._process_headers(text)
        text = self._process_lists(text)
        text = self._process_blockquotes(text)
        text = self._process_horizontal_rules(text)
        text = self._process_links(text)
        text = self._process_bold(text)
        text = self._process_italic(text)
        text = self._process_inline_code(text)
        
        # Convert line breaks to <br> tags
        text = text.replace('\n', '<br>')
        
        return text
    
    def _process_code_blocks(self, text: str) -> str:
        """Process code blocks with syntax highlighting."""
        def replace_code_block(match):
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            
            try:
                lexer = get_lexer_by_name(language)
            except ClassNotFound:
                lexer = TextLexer()
            
            formatter = HtmlFormatter(
                style='monokai',
                noclasses=True,
                nobackground=True,
                cssstyles='color: #f8f8f2; background: #272822; padding: 10px; border-radius: 5px; margin: 10px 0; font-family: "Consolas", "Monaco", monospace;'
            )
            
            highlighted_code = highlight(code, lexer, formatter)
            return f'<div style="background: #272822; border-radius: 5px; margin: 10px 0; overflow-x: auto;">{highlighted_code}</div>'
        
        return self.code_block_pattern.sub(replace_code_block, text)
    
    def _process_inline_code(self, text: str) -> str:
        """Process inline code."""
        def replace_inline_code(match):
            code = match.group(1)
            return f'<code style="background: #2d2d2d; color: #f8f8f2; padding: 2px 4px; border-radius: 3px; font-family: monospace;">{code}</code>'
        
        return self.inline_code_pattern.sub(replace_inline_code, text)
    
    def _process_bold(self, text: str) -> str:
        """Process bold text."""
        def replace_bold(match):
            content = match.group(1)
            return f'<strong style="font-weight: bold;">{content}</strong>'
        
        return self.bold_pattern.sub(replace_bold, text)
    
    def _process_italic(self, text: str) -> str:
        """Process italic text."""
        def replace_italic(match):
            content = match.group(1)
            return f'<em style="font-style: italic;">{content}</em>'
        
        return self.italic_pattern.sub(replace_italic, text)
    
    def _process_links(self, text: str) -> str:
        """Process links."""
        def replace_link(match):
            text_content = match.group(1)
            url = match.group(2)
            return f'<a href="{url}" style="color: #0078d4; text-decoration: none;">{text_content}</a>'
        
        return self.link_pattern.sub(replace_link, text)
    
    def _process_headers(self, text: str) -> str:
        """Process headers."""
        def replace_header(match):
            level = len(match.group(1))
            content = match.group(2)
            tag = f'h{min(level, 6)}'
            return f'<{tag} style="margin: 15px 0 10px 0; color: #ffffff;">{content}</{tag}>'
        
        return self.header_pattern.sub(replace_header, text)
    
    def _process_lists(self, text: str) -> str:
        """Process unordered and ordered lists."""
        lines = text.split('\n')
        in_list = False
        in_ordered_list = False
        result_lines = []
        
        for line in lines:
            # Check for unordered list
            unordered_match = self.list_pattern.match(line)
            if unordered_match:
                if not in_list:
                    result_lines.append('<ul style="margin: 10px 0; padding-left: 20px;">')
                    in_list = True
                content = unordered_match.group(1)
                result_lines.append(f'<li style="margin: 5px 0;">{content}</li>')
                continue
            
            # Check for ordered list
            ordered_match = self.numbered_list_pattern.match(line)
            if ordered_match:
                if not in_ordered_list:
                    result_lines.append('<ol style="margin: 10px 0; padding-left: 20px;">')
                    in_ordered_list = True
                content = ordered_match.group(1)
                result_lines.append(f'<li style="margin: 5px 0;">{content}</li>')
                continue
            
            # Close lists if we're not in one anymore
            if in_list and not unordered_match:
                result_lines.append('</ul>')
                in_list = False
            
            if in_ordered_list and not ordered_match:
                result_lines.append('</ol>')
                in_ordered_list = False
            
            result_lines.append(line)
        
        # Close any remaining lists
        if in_list:
            result_lines.append('</ul>')
        if in_ordered_list:
            result_lines.append('</ol>')
        
        return '\n'.join(result_lines)
    
    def _process_blockquotes(self, text: str) -> str:
        """Process blockquotes."""
        def replace_blockquote(match):
            content = match.group(1)
            return f'<blockquote style="border-left: 4px solid #0078d4; margin: 10px 0; padding-left: 15px; color: #cccccc;">{content}</blockquote>'
        
        return self.blockquote_pattern.sub(replace_blockquote, text)
    
    def _process_horizontal_rules(self, text: str) -> str:
        """Process horizontal rules."""
        def replace_hr(match):
            return '<hr style="border: none; border-top: 1px solid #555555; margin: 20px 0;">'
        
        return self.horizontal_rule_pattern.sub(replace_hr, text)


# Global instance for easy access
markdown_formatter = MarkdownFormatter() 
