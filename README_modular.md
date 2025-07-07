# The Oracle - Enhanced AI Chat Application

## Overview
The Oracle is a sophisticated AI chat application that has been dramatically modernized with enhanced visual design, animations, and improved accessibility features. The application now features a modular architecture with a stunning 3D-enhanced UI.

## 🎨 Enhanced UI Features

### Visual Enhancements
- **Modern 3D Icons**: Integrated throughout the interface from curated icon library
- **Animated Buttons**: Hover effects, scaling, and smooth transitions
- **Enhanced Color Schemes**: Beautiful gradients for both dark and light themes
- **Drop Shadows**: Modern depth effects on interactive elements
- **Improved Typography**: Better font choices and sizing
- **Responsive Layout**: Adaptive design that works on different screen sizes

### Accessibility Improvements
- **Keyboard Navigation**: Full keyboard support with shortcuts
- **Screen Reader Support**: Proper ARIA labels and descriptions
- **High Contrast**: Enhanced color contrast for better readability
- **Theme Switching**: Toggle between dark and light modes
- **Tooltips**: Contextual help throughout the interface
- **Scalable Icons**: Vector-based icons that scale properly

### Interactive Elements
- **Animated List Widgets**: Enhanced conversation and message lists
- **Modern Toolbars**: Icon-rich toolbars with proper spacing
- **Enhanced Search**: Advanced search dialog with filters
- **Typing Indicators**: Visual feedback during AI responses
- **Progress Animations**: Loading states and transitions

## 🚀 Quick Start

### Standard Launch
```bash
python standalone_oracle.py
```

### Alternative Launch Methods
```bash
# Using the main launcher
python main.py

# Using the enhanced launcher
python launch_enhanced.py
```

## 🎯 Key Features

### Core Functionality
- Multi-provider AI support (OpenAI, Anthropic, Ollama)
- Real-time streaming responses
- Conversation management and persistence
- Advanced search and filtering
- Export capabilities (JSON, TXT, HTML)
- File attachment support
- Knowledge graph integration

### Enhanced UI Features
- **3D Icon Library**: Organized icon system with categories
- **Animation System**: Smooth transitions and effects
- **Theme System**: Dark/Light mode with instant switching
- **Modern Controls**: Enhanced buttons, dialogs, and menus
- **Visual Feedback**: Loading states, hover effects, and animations
- **Accessibility**: Screen reader support and keyboard navigation

## 📁 Enhanced Project Structure

```
Oracle/
├── main.py                 # Main application entry point
├── standalone_oracle.py    # Standalone enhanced UI version
├── launch_enhanced.py      # Enhanced launcher script
├── run_enhanced.py         # Alternative enhanced launcher
├── ui_demo.py             # UI features demonstration
├── 
├── core/                   # Core application logic
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── evaluator.py       # AI response evaluation
│   └── knowledge_graph.py  # Knowledge graph functionality
├── 
├── api/                    # API integrations
│   ├── __init__.py
│   ├── multi_provider.py  # Multi-provider client
│   ├── settings.py        # API settings dialog
│   └── threads.py         # Threading for API calls
├── 
├── ui/                     # User interface components
│   ├── __init__.py
│   ├── main_window.py     # Main window implementation
│   ├── chat_app.py        # Enhanced chat interface
│   └── enhanced_chat_app.py # Alternative enhanced UI
├── 
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── dependencies.py    # Dependency management
│   ├── file_utils.py      # File operations
│   └── formatting.py      # Text formatting utilities
├── 
├── icons/                  # Enhanced icon library
│   ├── oracle_app.png     # Main application icon
│   ├── toolbar/           # Toolbar icons
│   ├── buttons/           # Button icons
│   ├── chat/              # Chat-related icons
│   ├── general/           # General purpose icons
│   └── unused-icon-library/ # Additional icons
├── 
├── ENHANCED_UI_GUIDE.md    # Complete UI enhancement guide
├── README_modular.md       # This file
└── requirements.txt        # Python dependencies
```

## 🎨 Icon System

The application includes a comprehensive 3D icon library organized by category:

### Categories
- **toolbar/**: Main toolbar icons (save, load, search, etc.)
- **buttons/**: Action button icons (send, attach, delete, etc.)
- **chat/**: Chat-specific icons (message, typing, etc.)
- **general/**: General purpose icons (folder, file, theme, etc.)

### Usage
Icons are dynamically loaded and scaled appropriately for different contexts.

## 🌟 Animation System

### Button Animations
- Hover scaling effects
- Color transitions
- Shadow animations
- Press feedback

### List Animations
- Item hover effects
- Selection animations
- Smooth scrolling
- Dynamic loading states

### Theme Animations
- Smooth color transitions
- Gradual style changes
- Animated theme switching

## 🎯 Accessibility Features

### Keyboard Navigation
- **Ctrl+N**: New conversation
- **Ctrl+S**: Save chat
- **Ctrl+O**: Load chat
- **Ctrl+F**: Search
- **Ctrl+Enter**: Send message
- **Tab**: Navigate between elements
- **Space/Enter**: Activate buttons

### Screen Reader Support
- Proper ARIA labels
- Descriptive button text
- Status announcements
- Structural headings

### Visual Accessibility
- High contrast color schemes
- Scalable fonts and icons
- Clear visual hierarchy
- Sufficient color contrast ratios

## 🔧 Configuration

### Theme Customization
The application supports extensive theme customization through CSS-like styling:

```python
# Dark theme example
DARK_THEME = {
    'background': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0F1419, stop:1 #1A202C)',
    'foreground': '#F7FAFC',
    'accent': '#3182CE',
    'border': '#4A5568'
}
```

### Icon Configuration
Icons can be customized by replacing files in the `icons/` directory structure.

## 🚀 Advanced Features

### Export System
- **JSON**: Complete conversation data
- **TXT**: Plain text format
- **HTML**: Rich formatted output

### Search System
- Real-time search
- Multi-field filtering
- Conversation search
- Message content search

### Knowledge Graph
- Relationship mapping
- Context awareness
- Learning from conversations

## 📖 Documentation

For detailed information about the enhanced UI features, see:
- [ENHANCED_UI_GUIDE.md](ENHANCED_UI_GUIDE.md) - Complete visual enhancement guide
- [FEATURES_IMPLEMENTED.md](FEATURES_IMPLEMENTED.md) - Detailed feature list

## 🤝 Contributing

When contributing to the enhanced UI:
1. Follow the established icon naming conventions
2. Maintain accessibility standards
3. Test theme switching functionality
4. Ensure keyboard navigation works
5. Document new visual features

## 📜 License

This project maintains its original license terms while incorporating modern UI enhancements.

---

**The Oracle - Enhanced UI** brings together powerful AI capabilities with a modern, accessible, and visually stunning interface. The enhanced version maintains all original functionality while dramatically improving the user experience through thoughtful design and animation.
