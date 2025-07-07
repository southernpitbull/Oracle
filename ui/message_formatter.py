"""
Message formatting utilities
"""

from core.config import (html, re, hashlib, PYGMENTS_AVAILABLE, highlight, 
                        get_lexer_by_name, TextLexer, HtmlFormatter)


class MessageFormatter:
    """Handles formatting of chat messages with markdown, code highlighting, etc."""
    
    def __init__(self, dark_theme=True):
        self.dark_theme = dark_theme
    
    def format_message(self, text, current_model=None):
        """Format message with enhanced styling and features"""
        # Escape HTML to avoid rendering issues with raw text
        text = html.escape(text)
        
        # Make URLs clickable
        url_pattern = r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?'
        text = re.sub(url_pattern, r'<a href="\g<0>" style="color: #1F6FEB; text-decoration: underline;">\g<0></a>', text)
        
        # Handle thinking blocks with collapsible thought bubble design
        text = self._format_thinking_blocks(text, current_model)
        
        # Enhanced code blocks with syntax highlighting and copy functionality
        text = self._format_code_blocks(text)
        
        # Enhanced markdown table rendering
        text = self._format_tables(text)
        
        return text
    
    def _format_thinking_blocks(self, text, model_name=None):
        """Format thinking blocks with collapsible design"""
        def format_thinking_block(match):
            thinking_content = match.group(1)
            model_name_display = model_name or "AI"
            
            # Choose colors based on theme
            if self.dark_theme:
                # Dark theme colors
                bubble_bg = "linear-gradient(135deg, #161B22 0%, #21262D 100%)"
                bubble_border = "#373E47"
                summary_bg = "linear-gradient(135deg, #1F6FEB 0%, #0969DA 100%)"
                summary_color = "#F0F6FC"
                content_bg = "#0D1117"
                content_border = "#373E47"
                text_color = "#F0F6FC"
                accent_color = "#1F6FEB"
            else:
                # Light theme colors
                bubble_bg = "linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%)"
                bubble_border = "#d1d9ff"
                summary_bg = "linear-gradient(135deg, #6c7ce7 0%, #4834d4 100%)"
                summary_color = "white"
                content_bg = "white"
                content_border = "#e0e6ff"
                text_color = "#2d3748"
                accent_color = "#4834d4"
            
            # Create a thought bubble with rounded corners
            thinking_html = f'''
            <div style="margin: 15px 0; font-family: 'Segoe UI', Arial, sans-serif;">
                <details style="
                    background: {bubble_bg};
                    border: 2px solid {bubble_border};
                    border-radius: 20px;
                    padding: 0;
                    margin: 10px 0;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    position: relative;
                    overflow: hidden;
                ">
                    <summary style="
                        background: {summary_bg};
                        color: {summary_color};
                        padding: 12px 20px;
                        border-radius: 18px;
                        cursor: pointer;
                        font-weight: 600;
                        font-size: 14px;
                        outline: none;
                        border: none;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        transition: all 0.3s ease;
                        user-select: none;
                    ">
                        <span style="font-size: 16px;">🤔</span>
                        <span>{model_name_display} is thinking right now - click to view thought process</span>
                        <span style="margin-left: auto; font-size: 12px;">▼</span>
                    </summary>
                    <div style="
                        padding: 20px;
                        background: {content_bg};
                        border-radius: 0 0 18px 18px;
                        border-top: 1px solid {content_border};
                        position: relative;
                    ">
                        <div style="
                            background: {bubble_bg};
                            border: 1px solid {content_border};
                            border-radius: 12px;
                            padding: 15px;
                            font-family: 'Segoe UI', Arial, sans-serif;
                            color: {text_color};
                            line-height: 1.6;
                            font-size: 14px;
                        ">
                            <div style="
                                font-weight: 600;
                                color: {accent_color};
                                margin-bottom: 8px;
                                font-size: 13px;
                                text-transform: uppercase;
                                letter-spacing: 0.5px;
                            ">💭 Thought Process</div>
                            <div style="white-space: pre-wrap;">{thinking_content}</div>
                        </div>
                    </div>
                </details>
            </div>
            '''
            return thinking_html

        # Handle both <thinking> and <think> tags
        text = re.sub(r'&lt;thinking&gt;(.*?)&lt;/thinking&gt;', format_thinking_block, text, flags=re.DOTALL)
        text = re.sub(r'&lt;think&gt;(.*?)&lt;/think&gt;', format_thinking_block, text, flags=re.DOTALL)
        
        return text
    
    def _format_code_blocks(self, text):
        """Format code blocks with syntax highlighting"""
        def highlight_code(match):
            lang = match.group(1) or 'text'
            code = match.group(2)
            
            # The code is already HTML-escaped, so we need to unescape it for the lexer
            code_to_highlight = html.unescape(code)
            
            # Generate unique ID for this code block
            code_id = hashlib.md5(code_to_highlight.encode()).hexdigest()[:8]

            if PYGMENTS_AVAILABLE:
                try:
                    lexer = get_lexer_by_name(lang, stripall=True)
                except Exception:
                    lexer = TextLexer()

                formatter = HtmlFormatter(style='monokai', noclasses=True)
                highlighted_code = highlight(code_to_highlight, lexer, formatter)
            else:
                # Fallback without syntax highlighting
                highlighted_code = f'<pre style="background-color: #272822; color: #f8f8f2; padding: 10px; border-radius: 4px; overflow-x: auto;"><code>{html.escape(code_to_highlight)}</code></pre>'
            
            # Create enhanced code block with copy button
            code_block_html = f'''
            <div style="
                background-color: #272822; 
                border: 1px solid #333; 
                border-radius: 8px; 
                margin: 15px 0; 
                position: relative;
                overflow: hidden;
                font-family: 'Courier New', Courier, monospace;
            ">
                <div style="
                    background-color: #1e1e1e;
                    padding: 8px 12px;
                    border-bottom: 1px solid #333;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                    color: #8B949E;
                ">
                    <span style="font-weight: 600; text-transform: uppercase;">{lang}</span>
                    <button onclick="copyCode('{code_id}')" style="
                        background-color: #30363D;
                        border: 1px solid #373E47;
                        border-radius: 4px;
                        color: #F0F6FC;
                        padding: 4px 8px;
                        cursor: pointer;
                        font-size: 11px;
                        transition: all 0.2s;
                    " onmouseover="this.style.backgroundColor='#1F6FEB'; this.style.borderColor='#1F6FEB';" 
                       onmouseout="this.style.backgroundColor='#30363D'; this.style.borderColor='#373E47';">
                        📋 Copy Code
                    </button>
                </div>
                <div style="padding: 12px; overflow-x: auto;" id="code_{code_id}">
                    {highlighted_code}
                </div>
            </div>
            <script>
                function copyCode(codeId) {{
                    const codeElement = document.getElementById('code_' + codeId);
                    const codeText = codeElement.innerText || codeElement.textContent;
                    navigator.clipboard.writeText(codeText).then(() => {{
                        // Visual feedback
                        const button = event.target;
                        const originalText = button.textContent;
                        button.textContent = '✓ Copied!';
                        button.style.backgroundColor = '#238636';
                        setTimeout(() => {{
                            button.textContent = originalText;
                            button.style.backgroundColor = '#30363D';
                        }}, 1500);
                    }});
                }}
            </script>
            '''
            return code_block_html

        # Regex to find ```lang\ncode``` blocks
        text = re.sub(r'```(\w+)?\n(.*?)\n```', highlight_code, text, flags=re.DOTALL)
        
        return text
    
    def _format_tables(self, text):
        """Format markdown tables"""
        def format_table(match):
            table_text = match.group(0)
            lines = table_text.strip().split('\n')
            
            if len(lines) < 2:
                return table_text
            
            # Parse header
            header = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
            
            # Parse alignment row
            alignment_row = lines[1] if len(lines) > 1 else ""
            alignments = []
            for cell in alignment_row.split('|'):
                cell = cell.strip()
                if cell.startswith(':') and cell.endswith(':'):
                    alignments.append('center')
                elif cell.endswith(':'):
                    alignments.append('right')
                else:
                    alignments.append('left')
            
            # Parse data rows
            data_rows = []
            for line in lines[2:]:
                if line.strip():
                    row = [cell.strip() for cell in line.split('|') if cell.strip()]
                    data_rows.append(row)
            
            # Generate HTML table
            table_html = '''
            <table style="
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
                background-color: #161B22;
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid #373E47;
            ">
                <thead style="background-color: #21262D;">
                    <tr>
            '''
            
            for i, header_cell in enumerate(header):
                align = alignments[i] if i < len(alignments) else 'left'
                table_html += f'''
                        <th style="
                            padding: 12px;
                            text-align: {align};
                            font-weight: 600;
                            color: #F0F6FC;
                            border-bottom: 2px solid #373E47;
                        ">{header_cell}</th>
                '''
            
            table_html += '''
                    </tr>
                </thead>
                <tbody>
            '''
            
            for row in data_rows:
                table_html += '<tr>'
                for i, cell in enumerate(row):
                    align = alignments[i] if i < len(alignments) else 'left'
                    table_html += f'''
                        <td style="
                            padding: 10px 12px;
                            text-align: {align};
                            color: #F0F6FC;
                            border-bottom: 1px solid #373E47;
                        ">{cell}</td>
                    '''
                table_html += '</tr>'
            
            table_html += '''
                </tbody>
            </table>
            '''
            
            return table_html

        # Enhanced table detection - more robust pattern
        table_pattern = r'(?:^|\n)(\|[^\n]+\|(?:\n\|[^\n]+\|)*)'
        text = re.sub(table_pattern, format_table, text, flags=re.MULTILINE)

        return text
