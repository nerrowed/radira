# RADIRA - AI Autonomous Agent

> Created by Nerrow

AI autonomous agent dengan kemampuan learning, memory management, dan context tracking.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run agent in interactive mode
python main.py

# Run memory management (interactive)
python manage_memory_interactive.py

# Run memory management (CLI)
python manage_memory.py --help
```

## 📁 Project Structure

```
radira/
├── agent/              # Core agent modules
│   ├── core/          # Orchestrators & core logic
│   ├── llm/           # LLM integration
│   ├── tools/         # Tool implementations
│   ├── state/         # State & memory management
│   ├── learning/      # Learning & reflection
│   └── safety/        # Safety & validation
├── config/            # Configuration
├── workspace/         # Agent workspace (gitignored)
├── docs/             # Documentation
├── tests/            # Test files
├── main.py           # Main entry point
└── manage_memory*.py # Memory management tools
```

## 🎯 Key Features

- **Dual Orchestrator** - Anti-looping dengan intelligent routing
- **Context Chain Tracking** - Melacak urutan tindakan dan keputusan
- **Memory Management** - Manage experiences, lessons, strategies
- **Error Learning** - Belajar dari error dan auto-remediation
- **Interactive Mode** - User-friendly menu-driven interface
- **Safety System** - Validasi dan permission management

## 📚 Documentation

Dokumentasi lengkap tersedia di folder [`docs/`](docs/):

### Getting Started
- [README](docs/README.md) - Overview dan setup
- [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - Ringkasan implementasi

### Core Systems
- [Orchestrator Architecture](docs/ORCHESTRATOR_ARCHITECTURE.md) - Arsitektur orchestrator
- [Learning System](docs/LEARNING_SYSTEM.md) - Sistem pembelajaran
- [Context Tracking](docs/CONTEXT_TRACKING_README.md) - Context chain tracking
- [Memory Management](docs/MEMORY_MANAGEMENT_README.md) - Memory management system
- [Interactive Mode](docs/INTERACTIVE_MODE_README.md) - Interactive mode guide

### Specialized Guides
- [Error Learning System](docs/ERROR_LEARNING_SYSTEM.md) - Error learning & remediation
- [Error Learning Quickstart](docs/ERROR_LEARNING_QUICKSTART.md) - Quick guide
- [Auto Remediation Guide](docs/AUTO_REMEDIATION_GUIDE.md) - Remediation patterns
- [Pentest Guide](docs/PENTEST_GUIDE.md) - Penetration testing tools

### Technical Details
- [Token Optimization](docs/TOKEN_OPTIMIZATION.md) - Token management
- [Memory Fix](docs/MEMORY_FIX.md) - Memory system fixes
- [Remediation Summary](docs/REMEDIATION_SUMMARY.md) - Remediation capabilities

## 🛠️ Tools & Commands

### Main Agent
```bash
# Interactive mode
python main.py

# Single task
python main.py "create a landing page"

# With options
python main.py --max-iterations 20 --verbose
```

### Memory Management

#### Interactive Mode (Recommended)
```bash
python manage_memory_interactive.py
```

#### CLI Mode
```bash
# List memory
python manage_memory.py list context --limit 10
python manage_memory.py list experiences --success-only

# Search
python manage_memory.py search "file operations"

# Add
python manage_memory.py add lesson --lesson "..." --context "..."

# Statistics
python manage_memory.py stats

# Export/Import
python manage_memory.py export backup.json
python manage_memory.py import backup.json

# Clear
python manage_memory.py clear context
```

## 🧪 Testing

```bash
# Test context tracking
python test_context_tracking.py

# Test interactive mode
python test_interactive.py

# Run all tests
python -m pytest tests/
```

## 📊 Features Overview

### Context Chain Tracking
Track urutan user commands → AI actions → results untuk contextual awareness.

### Memory Management
- **Context Memory**: Tracking tindakan AI
- **Experiences**: Task execution history
- **Lessons Learned**: Knowledge extraction
- **Strategies**: Successful approaches

### Learning System
- Reflective learning dari experiences
- Error pattern detection
- Auto-remediation suggestions
- Knowledge accumulation

### Interactive UI
Menu-driven interface dengan:
- Colored output
- Guided input
- Confirmation dialogs
- Help system

## 🔧 Configuration

Edit `config/settings.py` untuk konfigurasi:
- Model selection
- Max iterations
- Token limits
- Working directory
- Orchestrator type

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📝 License

[Add license information]

## 🙏 Credits

Created by Nerrow

---

**Version:** 1.0.0
**Last Updated:** 2025-11-13
