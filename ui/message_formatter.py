"""
Message formatting utilities
"""

from core.config import (html, re, hashlib, PYGMENTS_AVAILABLE, highlight,
                        get_lexer_by_name, TextLexer, HtmlFormatter)


class MessageFormatter:
    """Handles formatting of chat messages with markdown, code highlighting, etc."""

    def __init__(self, dark_theme=True, show_line_numbers=False, enable_code_folding=False):
        self.dark_theme = dark_theme
        self.show_line_numbers = show_line_numbers
        self.enable_code_folding = enable_code_folding

    def format_message(self, text, current_model=None):
        """Format message with enhanced styling and features"""
        # Escape HTML to avoid rendering issues with raw text
        text = html.escape(text)

        # Handle thinking blocks with collapsible thought bubble design
        text = self._format_thinking_blocks(text, current_model)

        # Enhanced code blocks with syntax highlighting and copy functionality
        text = self._format_code_blocks(text)

        # Enhanced markdown formatting
        text = self._format_markdown(text)

        # Enhanced markdown table rendering
        text = self._format_tables(text)

        # Make URLs clickable (after other formatting to avoid conflicts)
        url_pattern = r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?'
        text = re.sub(url_pattern, r'<a href="\g<0>" style="color: #1F6FEB; text-decoration: underline;">\g<0></a>', text)

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

    def _detect_foldable_sections(self, code_text, lang):
        """Detect functions, classes, and other foldable sections in code"""
        lines = code_text.split('\n')
        foldable_sections = []

        if lang.lower() in ['python', 'py']:
            # Python function and class detection
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('class '):
                    # Find the end of this function/class (next def/class or unindented line)
                    indent_level = len(line) - len(line.lstrip())
                    start_line = i
                    end_line = len(lines) - 1

                    for j in range(i + 1, len(lines)):
                        current_line = lines[j]
                        if current_line.strip():  # Skip empty lines
                            current_indent = len(current_line) - len(current_line.lstrip())
                            if current_indent <= indent_level and (current_line.strip().startswith('def ') or
                                                                 current_line.strip().startswith('class ') or
                                                                 current_indent == 0):
                                end_line = j - 1
                                break

                    if end_line > start_line:
                        foldable_sections.append({
                            'start': start_line,
                            'end': end_line,
                            'type': 'function' if stripped.startswith('def ') else 'class',
                            'name': stripped.split('(')[0].replace('def ', '').replace('class ', '').strip()
                        })

        elif lang.lower() in ['javascript', 'js', 'typescript', 'ts']:
            # JavaScript/TypeScript function detection
            for i, line in enumerate(lines):
                stripped = line.strip()
                if ('function ' in stripped or
                    stripped.startswith('const ') and '=>' in stripped or
                    stripped.startswith('let ') and '=>' in stripped or
                    stripped.startswith('var ') and '=>' in stripped):

                    # Simple bracket matching for JS functions
                    brace_count = 0
                    start_line = i
                    end_line = i

                    for j in range(i, len(lines)):
                        line_text = lines[j]
                        brace_count += line_text.count('{') - line_text.count('}')
                        if brace_count == 0 and j > i and '{' in lines[i:j+1][0]:
                            end_line = j
                            break

                    if end_line > start_line:
                        func_name = stripped.split('function ')[-1].split('(')[0].strip() if 'function ' in stripped else stripped.split(' ')[1].split('=')[0].strip()
                        foldable_sections.append({
                            'start': start_line,
                            'end': end_line,
                            'type': 'function',
                            'name': func_name
                        })

        return foldable_sections

    def _apply_code_folding(self, highlighted_code, foldable_sections, code_id):
        """Apply code folding to highlighted code"""
        if not self.enable_code_folding or not foldable_sections:
            return highlighted_code

        # Split the highlighted code into lines
        lines = highlighted_code.split('\n')

        # Process foldable sections in reverse order to maintain line numbers
        for section in reversed(foldable_sections):
            start_idx = section['start']
            end_idx = section['end']
            section_type = section['type']
            section_name = section['name']

            if start_idx < len(lines) and end_idx < len(lines):
                # Create foldable section
                header_line = lines[start_idx]
                content_lines = lines[start_idx + 1:end_idx + 1]

                # Generate unique ID for this foldable section
                section_id = f"{code_id}_fold_{start_idx}"

                folded_section = f'''
                <details class="code-fold" data-section="{section_id}">
                    <summary style="
                        cursor: pointer;
                        background-color: #3d4043;
                        padding: 2px 8px;
                        border-radius: 4px;
                        margin: 2px 0;
                        user-select: none;
                        font-size: 12px;
                        color: #8B949E;
                    ">
                        ▶ {section_type}: {section_name} ({len(content_lines)} lines)
                    </summary>
                    <div style="margin-left: 20px;">
                        {header_line}
                        {chr(10).join(content_lines)}
                    </div>
                </details>'''

                # Replace the section with the foldable version
                lines[start_idx:end_idx + 1] = [folded_section]

        return '\n'.join(lines)

    def _format_code_blocks(self, text):
        """Format code blocks with syntax highlighting"""
        def highlight_code(match):
            lang = (match.group(1) or 'text').strip()
            code = match.group(2).strip()

            # The code is already HTML-escaped, so we need to unescape it for the lexer
            code_to_highlight = html.unescape(code)

            # Generate unique ID for this code block
            code_id = hashlib.md5(code_to_highlight.encode()).hexdigest()[:8]

            # Detect foldable sections if code folding is enabled
            foldable_sections = []
            if self.enable_code_folding:
                foldable_sections = self._detect_foldable_sections(code_to_highlight, lang)

            if PYGMENTS_AVAILABLE:
                try:
                    lexer = get_lexer_by_name(lang, stripall=True)
                except Exception:
                    try:
                        # Try common language aliases
                        lang_map = {
                            'js': 'javascript',
                            'py': 'python',
                            'ts': 'typescript',
                            'sh': 'bash',
                            'shell': 'bash',
                            'yml': 'yaml'
                        }
                        mapped_lang = lang_map.get(lang.lower(), lang)
                        lexer = get_lexer_by_name(mapped_lang, stripall=True)
                    except Exception:
                        lexer = TextLexer()

                # Configure formatter with line numbers if enabled
                if self.show_line_numbers:
                    formatter = HtmlFormatter(
                        style='monokai' if self.dark_theme else 'default',
                        noclasses=True,
                        linenos='inline',
                        linenostart=1,
                        linenospecial=0,
                        linenumsep='  ',
                        lineanchors='line',
                        anchorlinenos=True
                    )
                else:
                    formatter = HtmlFormatter(
                        style='monokai' if self.dark_theme else 'default',
                        noclasses=True
                    )

                highlighted_code = highlight(code_to_highlight, lexer, formatter)

                # Clean up the highlighted code
                if self.show_line_numbers:
                    # Ensure line numbers are properly styled
                    highlighted_code = re.sub(
                        r'<span class="linenos">(\d+)</span>',
                        r'<span style="color: #8B949E; margin-right: 1em; user-select: none; font-weight: normal;">\1</span>',
                        highlighted_code
                    )
            else:
                # Fallback without syntax highlighting - use terminal-like styling
                code_bg = "#0d1117" if self.dark_theme else "#ffffff"
                code_color = "#f8f8f2" if self.dark_theme else "#24292f"
                line_color = "#8B949E"

                if self.show_line_numbers:
                    # Add line numbers manually for fallback
                    lines = code_to_highlight.split('\n')
                    numbered_lines = []
                    for i, line in enumerate(lines, 1):
                        numbered_lines.append(f'<span style="color: {line_color}; margin-right: 1em; user-select: none; font-weight: normal;">{i:>3}</span>{html.escape(line)}')
                    highlighted_code = f'<pre style="background-color: {code_bg}; color: {code_color}; padding: 0; margin: 0; border-radius: 0; overflow-x: auto; line-height: 1.4; font-family: monospace;"><code>{"<br>".join(numbered_lines)}</code></pre>'
                else:
                    highlighted_code = f'<pre style="background-color: {code_bg}; color: {code_color}; padding: 0; margin: 0; border-radius: 0; overflow-x: auto; line-height: 1.4; font-family: monospace;"><code>{html.escape(code_to_highlight)}</code></pre>'

            # Apply code folding if enabled and sections were detected
            if self.enable_code_folding and foldable_sections:
                highlighted_code = self._apply_code_folding(highlighted_code, foldable_sections, code_id)

            # Determine features text for header
            features = []
            if self.show_line_numbers:
                features.append("with line numbers")
            if self.enable_code_folding and foldable_sections:
                features.append(f"foldable ({len(foldable_sections)} sections)")

            features_text = f" ({', '.join(features)})" if features else ""

            # Theme-appropriate colors
            if self.dark_theme:
                header_bg = "#1e1e1e"
                header_color = "#8B949E"
                border_color = "#333"
                button_bg = "#30363D"
                button_border = "#373E47"
                button_color = "#F0F6FC"
                button_hover_bg = "#1F6FEB"
                button_success_bg = "#238636"
            else:
                header_bg = "#f6f8fa"
                header_color = "#656d76"
                border_color = "#d1d9e0"
                button_bg = "#f6f8fa"
                button_border = "#d1d9e0"
                button_color = "#24292f"
                button_hover_bg = "#0969da"
                button_success_bg = "#1a7f37"

            # Create enhanced terminal-like code block with copy button
            code_block_html = f'''
            <div style="
                background-color: {"#0d1117" if self.dark_theme else "#f6f8fa"};
                border: 2px solid {"#30363d" if self.dark_theme else "#d1d9e0"};
                border-radius: 8px;
                margin: 10px 0;
                position: relative;
                overflow: hidden;
                font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace;
                font-size: 13px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, {"0.4" if self.dark_theme else "0.1"});
            ">
                <div style="
                    background: {"linear-gradient(135deg, #161b22 0%, #21262d 100%)" if self.dark_theme else "linear-gradient(135deg, #f6f8fa 0%, #e1e7f0 100%)"};
                    padding: 8px 12px;
                    border-bottom: 1px solid {"#30363d" if self.dark_theme else "#d1d9e0"};
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                    color: {"#8b949e" if self.dark_theme else "#656d76"};
                ">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div style="display: flex; gap: 4px;">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: {"#ff5f57" if self.dark_theme else "#ff5f57"};"></div>
                            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: {"#ffbd2e" if self.dark_theme else "#ffbd2e"};"></div>
                            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: {"#28ca42" if self.dark_theme else "#28ca42"};"></div>
                        </div>
                        <span style="font-weight: 600; text-transform: uppercase; font-family: system-ui; margin-left: 8px;">{lang}{features_text}</span>
                    </div>
                    <button onclick="copyCodeBlock('{code_id}')" style="
                        background-color: {button_bg};
                        border: 1px solid {button_border};
                        border-radius: 4px;
                        color: {button_color};
                        padding: 4px 8px;
                        cursor: pointer;
                        font-size: 11px;
                        font-family: system-ui;
                        transition: all 0.2s ease;
                    " onmouseover="this.style.backgroundColor='{button_hover_bg}'; this.style.borderColor='{button_hover_bg}'; this.style.color='#ffffff';"
                       onmouseout="this.style.backgroundColor='{button_bg}'; this.style.borderColor='{button_border}'; this.style.color='{button_color}';">
                        📋 Copy
                    </button>
                </div>
                <div style="
                    padding: 16px;
                    background-color: {"#0d1117" if self.dark_theme else "#ffffff"};
                    overflow-x: auto;
                    line-height: 1.4;
                    min-height: 40px;
                " id="code_{code_id}">
                    {highlighted_code}
                </div>
            </div>
            <script>
                function copyCodeBlock(codeId) {{
                    const codeElement = document.getElementById('code_' + codeId);
                    let codeText = '';

                    // Try to get the text content, stripping line numbers if present
                    if (codeElement) {{
                        const preElement = codeElement.querySelector('pre');
                        if (preElement) {{
                            // Clone the element to avoid modifying the original
                            const clone = preElement.cloneNode(true);

                            // Remove line number spans
                            const lineNumbers = clone.querySelectorAll('span[style*="user-select: none"]');
                            lineNumbers.forEach(span => span.remove());

                            codeText = clone.textContent || clone.innerText || '';
                        }} else {{
                            codeText = codeElement.textContent || codeElement.innerText || '';
                        }}
                    }}

                    if (navigator.clipboard && codeText.trim()) {{
                        navigator.clipboard.writeText(codeText.trim()).then(() => {{
                            // Visual feedback
                            const button = event.target;
                            const originalText = button.textContent;
                            button.textContent = '✓ Copied!';
                            button.style.backgroundColor = '{button_success_bg}';
                            button.style.borderColor = '{button_success_bg}';
                            button.style.color = '#ffffff';
                            setTimeout(() => {{
                                button.textContent = originalText;
                                button.style.backgroundColor = '{button_bg}';
                                button.style.borderColor = '{button_border}';
                                button.style.color = '{button_color}';
                            }}, 1500);
                        }}).catch(() => {{
                            // Fallback for older browsers
                            const textArea = document.createElement('textarea');
                            textArea.value = codeText.trim();
                            document.body.appendChild(textArea);
                            textArea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textArea);

                            const button = event.target;
                            const originalText = button.textContent;
                            button.textContent = '✓ Copied!';
                            setTimeout(() => {{
                                button.textContent = originalText;
                            }}, 1500);
                        }});
                    }}
                }}
            </script>
            '''
            return code_block_html

        # Improved regex to handle code blocks with optional language and proper fencing
        # This handles: ```lang\ncode\n``` and ```\ncode\n```
        text = re.sub(r'```(\w+)?\s*\n(.*?)\n```', highlight_code, text, flags=re.DOTALL)

        return text

    def _format_tables(self, text):
        """Format markdown tables with enhanced styling"""
        def format_table(match):
            table_text = match.group(1)
            lines = table_text.strip().split('\n')

            if len(lines) < 2:
                return table_text

            # Parse header
            header = [cell.strip() for cell in lines[0].split('|') if cell.strip()]
            if not header:
                return table_text

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

            # Ensure we have alignments for all columns
            while len(alignments) < len(header):
                alignments.append('left')

            # Parse data rows
            data_rows = []
            for line in lines[2:]:
                if line.strip() and '|' in line:
                    row = [cell.strip() for cell in line.split('|') if cell.strip() or cell.strip() == '']
                    # Pad row to match header length
                    while len(row) < len(header):
                        row.append('')
                    data_rows.append(row[:len(header)])  # Trim to header length

            if not data_rows:
                return table_text

            # Theme-appropriate colors
            if self.dark_theme:
                table_bg = "#161B22"
                header_bg = "#21262D"
                border_color = "#373E47"
                text_color = "#F0F6FC"
                header_color = "#F0F6FC"
                row_hover_bg = "#1C2128"
            else:
                table_bg = "#FFFFFF"
                header_bg = "#F6F8FA"
                border_color = "#D1D9E0"
                text_color = "#24292F"
                header_color = "#24292F"
                row_hover_bg = "#F6F8FA"

            # Generate HTML table
            table_html = f'''
            <table style="
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
                background-color: {table_bg};
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid {border_color};
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 14px;
            ">
                <thead style="background-color: {header_bg};">
                    <tr>
            '''

            for i, header_cell in enumerate(header):
                align = alignments[i] if i < len(alignments) else 'left'
                table_html += f'''
                        <th style="
                            padding: 12px 16px;
                            text-align: {align};
                            font-weight: 600;
                            color: {header_color};
                            border-bottom: 2px solid {border_color};
                            background-color: {header_bg};
                        ">{header_cell}</th>
                '''

            table_html += '''
                    </tr>
                </thead>
                <tbody>
            '''

            for row_idx, row in enumerate(data_rows):
                stripe_bg = table_bg if row_idx % 2 == 0 else (row_hover_bg if self.dark_theme else "#FBFCFD")
                table_html += f'<tr style="background-color: {stripe_bg};">'
                for i, cell in enumerate(row):
                    align = alignments[i] if i < len(alignments) else 'left'
                    table_html += f'''
                        <td style="
                            padding: 10px 16px;
                            text-align: {align};
                            color: {text_color};
                            border-bottom: 1px solid {border_color};
                            vertical-align: top;
                        ">{cell}</td>
                    '''
                table_html += '</tr>'

            table_html += '''
                </tbody>
            </table>
            '''

            return table_html

        # Enhanced table detection - more robust pattern for markdown tables
        # Match tables that start with | and have at least 2 rows (header + separator)
        table_pattern = r'((?:^\|[^\n]*\|\s*\n){2,})'
        text = re.sub(table_pattern, format_table, text, flags=re.MULTILINE)

        return text

    def _format_markdown(self, text):
        """Format markdown elements like bold, italic, headers, lists, etc."""
        # Handle headers (### ### text)
        text = re.sub(r'^(#{1,6})\s*(.*?)$',
                     lambda m: f'<h{len(m.group(1))} style="color: {("#1F6FEB" if self.dark_theme else "#2B6CB0")}; margin: 15px 0 10px 0; font-weight: 600;">{m.group(2)}</h{len(m.group(1))}>',
                     text, flags=re.MULTILINE)

        # Handle bold text (**text** or __text__)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="font-weight: 600; color: inherit;">\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong style="font-weight: 600; color: inherit;">\1</strong>', text)

        # Handle italic text (*text* or _text_) - but not inside URLs or already formatted text
        text = re.sub(r'(?<![\w*_])\*([^*]+?)\*(?![\w*_])', r'<em style="font-style: italic; color: inherit;">\1</em>', text)
        text = re.sub(r'(?<![\w*_])_([^_]+?)_(?![\w*_])', r'<em style="font-style: italic; color: inherit;">\1</em>', text)

        # Handle strikethrough (~~text~~)
        text = re.sub(r'~~(.*?)~~', r'<del style="text-decoration: line-through; color: #8B949E;">\1</del>', text)

        # Handle inline code (`code`) - but not if it's part of code blocks
        text = re.sub(r'(?<!`)`([^`\n]+?)`(?!`)',
                     lambda m: f'<code style="background-color: {"#21262D" if self.dark_theme else "#F6F8FA"}; '
                               f'color: {"#FF7B72" if self.dark_theme else "#D73A49"}; '
                               f'padding: 2px 4px; border-radius: 3px; font-family: \'Courier New\', monospace; font-size: 0.9em;">{m.group(1)}</code>',
                     text)

        # Handle blockquotes (> text)
        blockquote_bg = "#161B22" if self.dark_theme else "#F6F8FA"
        blockquote_border = "#373E47" if self.dark_theme else "#D1D9E0"
        blockquote_color = "#8B949E" if self.dark_theme else "#656D76"

        def format_blockquote(match):
            quote_text = match.group(1).strip()
            return f'''<blockquote style="
                margin: 15px 0;
                padding: 10px 15px;
                background-color: {blockquote_bg};
                border-left: 4px solid {blockquote_border};
                border-radius: 0 6px 6px 0;
                color: {blockquote_color};
                font-style: italic;
            ">{quote_text}</blockquote>'''

        text = re.sub(r'^>\s*(.*?)$', format_blockquote, text, flags=re.MULTILINE)

        # Handle unordered lists (- or * item)
        list_color = "#F0F6FC" if self.dark_theme else "#24292F"
        bullet_color = "#1F6FEB" if self.dark_theme else "#0969DA"

        def format_unordered_list(match):
            items = match.group(0).strip().split('\n')
            list_html = f'<ul style="margin: 10px 0; padding-left: 20px; color: {list_color};">'
            for item in items:
                if item.strip().startswith(('-', '*', '+')):
                    item_text = item.strip()[1:].strip()
                    list_html += f'<li style="margin: 5px 0; list-style-type: none; position: relative;"><span style="color: {bullet_color}; position: absolute; left: -15px;">•</span>{item_text}</li>'
            list_html += '</ul>'
            return list_html

        # Match multiple lines starting with - or * or +
        text = re.sub(r'^((?:[-*+]\s+.*\n?)+)', format_unordered_list, text, flags=re.MULTILINE)

        # Handle ordered lists (1. item)
        def format_ordered_list(match):
            items = match.group(0).strip().split('\n')
            list_html = f'<ol style="margin: 10px 0; padding-left: 20px; color: {list_color};">'
            for item in items:
                if re.match(r'^\d+\.\s+', item.strip()):
                    item_text = re.sub(r'^\d+\.\s+', '', item.strip())
                    list_html += f'<li style="margin: 5px 0; color: {bullet_color};">{item_text}</li>'
            list_html += '</ol>'
            return list_html

        # Match multiple lines starting with numbers
        text = re.sub(r'^((?:\d+\.\s+.*\n?)+)', format_ordered_list, text, flags=re.MULTILINE)

        # Handle horizontal rules (--- or ***)
        hr_color = "#373E47" if self.dark_theme else "#D1D9E0"
        text = re.sub(r'^(---+|\*\*\*+)$',
                     f'<hr style="border: none; height: 2px; background-color: {hr_color}; margin: 20px 0;">',
                     text, flags=re.MULTILINE)

        return text
