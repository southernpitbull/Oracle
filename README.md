# 🌟 The Oracle - Enhanced AI Chat Interface

<div align="center">

![The Oracle](icons/oracle_app.png)

**A Modern, Multi-Provider AI Chat Application with Advanced Features**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen.svg)]()

</div>

## ✨ Features

### 🤖 **Multi-Provider AI Support**
- **Ollama** - Local AI models with ollama-python integration
- **OpenAI** - GPT-3.5, GPT-4, GPT-4 Turbo
- **Anthropic** - Claude 3 Sonnet, Haiku, Opus
- **Google Gemini** - Gemini 2.5 Flash, Pro models
- **Google AI Studio** - Direct API access
- **DeepSeek** - DeepSeek models
- **Qwen** - Alibaba's Qwen models
- **Nebius AI Studio** - Nebius platform integration
- **OpenRouter** - Multiple model access
- **Hugging Face** - HF model playground
- **LM Studio** - Local model hosting
- **llama.cpp** - Local model inference
- **vLLM** - High-performance inference
- **Perplexity** - Search-augmented AI

### 💬 **Enhanced Chat Experience**
- **Modern PyQt6 Interface** - Beautiful, responsive UI with dark/light themes
- **Real-time Streaming** - Live response generation with typing indicators
- **Conversation Management** - Save, load, and organize chat sessions
- **Message Threading** - Organized conversation flow
- **Search & Filter** - Find conversations and messages quickly
- **Export Options** - JSON, TXT, HTML, Markdown formats
- **Code Block Handling** - Syntax highlighting and copy functionality
- **File Attachments** - Support for documents and images
- **Keyboard Shortcuts** - Efficient navigation and actions

### 🧠 **Advanced Capabilities**
- **Multi-Model Support** - 15+ AI providers with dynamic model switching
- **Model Parameter Control** - Temperature, tokens, top-p, and more
- **System Prompts** - Customizable AI behavior and context
- **Prompt Templates** - Saved prompt library with categorization
- **Conversation Analytics** - Token usage and performance metrics
- **Plugin Manager** - Extensible architecture (planned)
- **Batch Processing** - Process multiple requests efficiently
- **Model Comparison** - Side-by-side response comparison
- **Auto-save** - Never lose your conversations
- **Settings Management** - Comprehensive configuration options

### 🎨 **User Experience**
- **Modern UI Design** - Clean, intuitive interface with PyQt6
- **Dark/Light Themes** - Customizable appearance
- **Rich Menu System** - 80+ features accessible via comprehensive menus
- **Keyboard Shortcuts** - Efficient navigation and actions
- **Responsive Layout** - Adapts to different screen sizes
- **Status Indicators** - Real-time connection and processing status
- **Error Handling** - Graceful error management and user feedback
- **Markdown Support** - Rich text formatting in messages
- **Syntax Highlighting** - Code block formatting with language detection
- **Virtual Scrolling** - Handle large conversations efficiently

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- PyQt6
- Git (for cloning)
- Ollama (optional, for local models)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/southernpitbull/Oracle.git
   cd Oracle
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run The Oracle**
   ```bash
   python main.py
   ```

### First Time Setup

1. **Configure API Keys** (optional - Ollama works without API keys)
   - Go to Settings → API Configuration
   - Add your API keys for desired providers:
     - OpenAI API key
     - Anthropic API key
     - Google Gemini API key
     - Other provider keys as needed

2. **Set up Ollama** (for local models)
   ```bash
   # Install Ollama from https://ollama.ai
   # Pull your preferred models
   ollama pull llama3.1
   ollama pull codellama
   ollama pull mistral
   ```

3. **Start chatting!**
   - Select a provider and model from the dropdown
   - Type your message and press Enter
   - Enjoy AI conversations!

## 📁 Project Structure

```
Oracle/
├── 📄 main.py                    # Application entry point
├── 📄 requirements.txt           # Python dependencies
├── 📄 LICENSE                    # MIT License
├── 📄 README.md                  # This file
├── 📁 api/                       # Multi-provider API clients
│   ├── __init__.py              # Package initialization
│   ├── clients.py               # Individual provider clients (15+ providers)
│   ├── multi_provider.py        # Unified provider interface
│   ├── settings.py              # API configuration management
│   └── threads.py               # Threading for async operations
├── 📁 core/                      # Core functionality
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Application configuration and imports
│   ├── evaluator.py             # AI response evaluation
│   └── knowledge_graph.py       # Knowledge management (future)
├── 📁 ui/                        # User interface components
│   ├── __init__.py              # Package initialization
│   ├── chat_app.py              # Main chat interface (80+ menu features)
│   ├── main_window.py           # Application window framework
│   ├── message_formatter.py     # Message display formatting
│   ├── welcome_screen.py        # Welcome and onboarding
│   └── [additional UI dialogs]  # Various settings and feature dialogs
├── 📁 utils/                     # Utility functions
│   ├── __init__.py              # Package initialization
│   ├── file_utils.py            # File operations and exports
│   ├── formatting.py            # Text formatting helpers
│   └── dependencies.py          # Dependency management
├── 📁 icons/                     # UI icons and assets
│   ├── oracle_app.png           # Main application icon
│   ├── chat/                    # Chat-related icons
│   ├── buttons/                 # Button icons
│   ├── general/                 # General UI icons
│   └── [other icon categories]  # Organized icon library
├── 📁 conversations/             # Saved conversation history
├── 📁 exports/                   # Exported files and reports
└── 📁 Models/                    # Local model storage (optional)
```

## 🔧 Configuration

### API Providers

The Oracle supports 15+ AI providers with unified configuration:

```python
# Built-in Provider Support
PROVIDERS = {
    # Local Servers
    "Ollama": {"host": "http://localhost:11434", "auth": None},
    "LM Studio": {"host": "http://localhost:1234", "auth": None},
    "llama.cpp": {"host": "http://localhost:8080", "auth": None},
    "vLLM": {"host": "http://localhost:8000", "auth": None},
    
    # Commercial APIs
    "OpenAI": {"api_key": "your-openai-key"},
    "Anthropic": {"api_key": "your-anthropic-key"},
    "Google Gemini": {"api_key": "your-gemini-key"},
    
    # AI Studios & Platforms
    "Google AI Studio": {"api_key": "your-google-ai-key"},
    "Nebius AI Studio": {"api_key": "your-nebius-key"},
    "OpenRouter": {"api_key": "your-openrouter-key"},
    "Hugging Face": {"api_key": "your-hf-key"},
    "Perplexity": {"api_key": "your-perplexity-key"},
    
    # International Providers
    "DeepSeek": {"api_key": "your-deepseek-key"},
    "Qwen": {"api_key": "your-qwen-key"}
}
```

### Model Management

- **Dynamic Model Loading**: Automatically discover available models
- **Model Parameters**: Control temperature, max tokens, top-p, etc.
- **Provider Switching**: Change providers without losing conversation context
- **Model Comparison**: Compare responses from different models
- **Local Model Support**: Full Ollama integration with model pulling

### Advanced Features

- **Comprehensive Menu System**: 80+ features organized in intuitive menus:
  - File operations (new, save, export, import)
  - Edit functions (copy, paste, find, preferences)
  - Chat management (clear, save conversations, templates)
  - View options (themes, layouts, zoom)
  - Tools (model settings, API configuration, analytics)
  - Help and documentation
- **Model Parameter Control**: Fine-tune AI behavior with advanced settings
- **Conversation Analytics**: Track token usage, response times, and costs
- **Plugin Architecture**: Extensible system for custom features (planned)
- **Batch Processing**: Handle multiple requests efficiently
- **Error Recovery**: Robust error handling and retry mechanisms

## 🤝 Contributing

We welcome contributions! The Oracle is an open-source project that benefits from community involvement.

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Set up development environment**
   ```bash
   pip install -r requirements.txt
   # Run the application in development mode
   python main.py
   ```
4. **Make your changes and test**
5. **Submit a pull request**

### Contributing Areas

- 🐛 **Bug Fixes**: Help improve stability and performance
- ✨ **New Features**: Add new AI providers or UI improvements
- 📖 **Documentation**: Improve guides and documentation
- 🎨 **UI/UX**: Enhance the user interface and experience
- 🧪 **Testing**: Add tests and improve quality assurance

## 📋 Roadmap

### Currently Implemented ✅
- [x] **Multi-Provider Support** - 15+ AI providers integrated
- [x] **Modern PyQt6 UI** - Complete interface with 80+ menu features
- [x] **Conversation Management** - Save, load, export functionality
- [x] **Model Parameter Control** - Advanced model configuration
- [x] **Real-time Streaming** - Live response generation
- [x] **Ollama Integration** - Full local model support

### In Progress 🚧
- [ ] **Enhanced Documentation** - Comprehensive user guides
- [ ] **Testing Suite** - Automated testing framework
- [ ] **Performance Optimization** - Speed and memory improvements

### Planned Features 🎯
- [ ] **Voice Integration** - Speech-to-text and text-to-speech
- [ ] **Plugin System** - Extensible architecture for custom features
- [ ] **RAG Implementation** - Knowledge base integration
- [ ] **Mobile App** - Cross-platform mobile version
- [ ] **Collaborative Features** - Shared conversations and workspaces
- [ ] **Advanced Analytics** - Detailed usage statistics and insights
- [ ] **Model Fine-tuning** - Custom model training capabilities
- [ ] **API Rate Limiting** - Smart request management
- [ ] **Workflow Automation** - Chain multiple AI interactions

See our detailed [Feature Roadmap](feature_roadmap.md) for more information.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama Team** - Exceptional local AI model hosting platform
- **PyQt6** - Powerful and modern GUI framework for Python
- **OpenAI** - Pioneering language models and API design
- **Anthropic** - Advanced AI safety and Claude models
- **Google** - Gemini models and AI research
- **All AI Providers** - Making diverse AI capabilities accessible
- **Open Source Community** - Contributors and supporters
- **Python Ecosystem** - Rich libraries and tools that make this possible

Special thanks to all the developers and researchers working to make AI more accessible and useful for everyone.

## 📞 Support

Need help or have questions? We're here to assist!

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/southernpitbull/Oracle/issues)
- � **Feature Requests**: [GitHub Discussions](https://github.com/southernpitbull/Oracle/discussions)
- 📖 **Documentation**: Check the project wiki and README
- 💬 **Community**: Join our discussions for tips and help

### Common Issues

1. **Installation Problems**: Ensure Python 3.8+ and PyQt6 are properly installed
2. **API Key Issues**: Verify API keys are correctly configured in settings
3. **Ollama Connection**: Make sure Ollama is running on localhost:11434
4. **Performance**: Check system resources if experiencing slowdowns

### Reporting Bugs

When reporting bugs, please include:
- Operating system and Python version
- Error messages or screenshots
- Steps to reproduce the issue
- Oracle version information

---

<div align="center">

**Made with ❤️ by The Oracle Project Team**

⭐ **Star this repository if you find it helpful!** ⭐

</div>
