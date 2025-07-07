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
- **Ollama** - Local AI models
- **OpenAI** - GPT-3.5, GPT-4, GPT-4 Turbo
- **Anthropic** - Claude models
- **Google** - Gemini models
- **Groq** - Fast inference models
- **Mistral** - Mistral AI models

### 💬 **Enhanced Chat Experience**
- **Modern PyQt6 Interface** - Beautiful, responsive UI
- **Real-time Streaming** - Live response generation
- **Conversation Management** - Save, load, and organize chats
- **Message Threading** - Reply to specific messages
- **Search & Filter** - Find conversations quickly
- **Export Options** - JSON, TXT, HTML formats

### 🧠 **Advanced Capabilities**
- **RAG (Retrieval-Augmented Generation)** - Knowledge base integration
- **Knowledge Graph** - Semantic understanding
- **Code Execution** - Run code snippets safely
- **File Attachments** - Process documents and images
- **Model Switching** - Change models mid-conversation
- **Custom Prompts** - Saved prompt library

### 🎨 **User Experience**
- **Dark/Light Themes** - Customizable appearance
- **Keyboard Shortcuts** - Efficient navigation
- **Virtual Scrolling** - Handle large conversations
- **Auto-save** - Never lose your progress
- **Markdown Support** - Rich text formatting
- **Syntax Highlighting** - Code block formatting

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- PyQt6
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/the-oracle.git
   cd the-oracle
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run The Oracle**
   ```bash
   python main.py
   ```

### Configuration

1. **Set up API Keys** (optional - Ollama works locally)
   - OpenAI: Add your API key in settings
   - Anthropic: Configure Claude access
   - Other providers: See [API Setup Guide](docs/api-setup.md)

2. **Install Ollama** (for local models)
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama2  # or your preferred model
   ```

## 📁 Project Structure

```
the-oracle/
├── 📄 main.py                 # Application entry point
├── 📄 requirements.txt        # Python dependencies
├── 📁 api/                    # Multi-provider API clients
│   ├── clients.py            # Individual provider clients
│   ├── multi_provider.py     # Unified interface
│   └── settings.py           # Configuration management
├── 📁 core/                   # Core functionality
│   ├── config.py             # Application configuration
│   ├── evaluator.py          # AI response evaluation
│   └── knowledge_graph.py    # Semantic knowledge management
├── 📁 ui/                     # User interface
│   ├── chat_app.py           # Main chat interface
│   ├── main_window.py        # Application window
│   └── message_formatter.py  # Message display formatting
├── 📁 utils/                  # Utility functions
│   ├── file_utils.py         # File operations
│   └── formatting.py         # Text formatting helpers
└── 📁 icons/                  # UI icons and assets
```

## 🔧 Configuration

### API Providers

The Oracle supports multiple AI providers. Configure them in the settings:

```python
# Example configuration
PROVIDERS = {
    "Ollama": {
        "base_url": "http://localhost:11434",
        "models": ["llama2", "codellama", "mistral"]
    },
    "OpenAI": {
        "api_key": "your-api-key",
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
    },
    "Anthropic": {
        "api_key": "your-api-key", 
        "models": ["claude-3-sonnet", "claude-3-opus"]
    }
}
```

### Advanced Features

- **RAG System**: Enable knowledge base integration
- **Code Execution**: Safe code running environment
- **Custom Themes**: Personalize the interface
- **Workflow Automation**: Chain multiple AI interactions

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   python -m pytest tests/
   ```
5. **Submit a pull request**

## 📋 Roadmap

- [ ] **Voice Integration** - Speech-to-text and text-to-speech
- [ ] **Plugin System** - Extensible architecture
- [ ] **Mobile App** - Cross-platform mobile version
- [ ] **Collaborative Features** - Shared conversations
- [ ] **Advanced RAG** - Enhanced knowledge processing
- [ ] **Model Fine-tuning** - Custom model training

See our detailed [Feature Roadmap](feature_roadmap.md) for more information.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** - Local AI model hosting
- **PyQt6** - Modern GUI framework  
- **OpenAI** - Advanced language models
- **Anthropic** - Claude AI models
- **Community** - Open source contributors

## 📞 Support

- 📧 **Email**: oracle@theoracle.app
- 🐛 **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/the-oracle/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/the-oracle/discussions)

---

<div align="center">

**Made with ❤️ by The Oracle Project Team**

⭐ **Star this repository if you find it helpful!** ⭐

</div>
