# AI Autonomous Agent

An autonomous AI agent powered by Groq (Llama 3.1 70B & Gemma 2 9B) that can execute tasks autonomously including web generation, file operations, and terminal commands.

## Features

- **Autonomous Task Execution**: Uses ReAct (Reasoning + Acting) pattern to think and act
- **Web Generation**: Generate HTML, React, Vue, and Tailwind CSS applications
- **File System Operations**: Safe file reading, writing, and directory management
- **Terminal Access**: Execute whitelisted shell commands safely
- **Sandboxed Environment**: All operations run in a controlled workspace
- **Multi-Model Support**: Uses fast model for decisions, powerful model for complex tasks

## Installation

### 1. Clone Repository
```bash
cd ai-agent-vps
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Copy `.env.example` to `.env` and add your Groq API key:
```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
```

Get your free Groq API key at: https://console.groq.com/

## Usage

### Interactive Mode
```bash
python main.py
```

This starts an interactive session where you can enter tasks:
```
Task: Create a landing page for a coffee shop
Task: List all Python files in the current directory
Task: Run git status
```

### Single Task Mode
```bash
python main.py "Generate a React todo app"
```

### Command Line Options
```bash
python main.py --help

Options:
  --verbose, -v              Enable verbose output
  --max-iterations N         Maximum iterations (default: 10)
  --working-dir PATH         Working directory
```

## Interactive Commands

While in interactive mode, you can use these commands:

- `help` - Show help message
- `tools` - List available tools
- `stats` - Show agent statistics
- `config` - Show current configuration
- `reset` - Reset agent state
- `exit` / `quit` - Exit program

## Available Tools

### 1. File System Tool
Read, write, list, and manage files safely.

**Operations:**
- `read` - Read file contents
- `write` - Write content to file
- `list` - List directory contents
- `mkdir` - Create directory
- `delete` - Delete file/directory
- `exists` - Check if path exists
- `search` - Search files by pattern

**Example Tasks:**
```
Create a new file called notes.txt with content "Hello World"
List all files in the current directory
Read the contents of config.json
```

### 2. Terminal Tool
Execute safe shell commands.

**Whitelisted Commands:**
- Version control: `git`, `gh`, `svn`
- Package managers: `npm`, `pip`, `yarn`, `poetry`
- Languages: `python`, `node`, `ruby`, `java`
- File viewers: `cat`, `ls`, `grep`, `find`
- And more...

**Example Tasks:**
```
Run git status
Install the requests package with pip
Check Python version
List all .py files
```

### 3. Web Generator Tool
Generate complete web applications.

**Supported Frameworks:**
- `html` - Plain HTML/CSS/JavaScript
- `react` - React with JSX
- `vue` - Vue.js components
- `tailwind` - HTML with Tailwind CSS

**Example Tasks:**
```
Generate a landing page for a restaurant
Create a React todo list app
Build a portfolio website with Tailwind CSS
Make a Vue.js counter component
```

## Project Structure

```
ai-agent-vps/
├── agent/                     # Main agent package
│   ├── core/                  # Core orchestration
│   │   └── orchestrator.py    # Agent brain (ReAct pattern)
│   ├── llm/                   # LLM interface
│   │   ├── groq_client.py     # Groq API wrapper
│   │   ├── prompts.py         # System prompts
│   │   └── parsers.py         # Response parsers
│   ├── tools/                 # Agent tools
│   │   ├── base.py            # Tool base class
│   │   ├── registry.py        # Tool registry
│   │   ├── filesystem.py      # File operations
│   │   ├── terminal.py        # Shell commands
│   │   └── web_generator.py   # Web generation
│   ├── safety/                # Safety modules (future)
│   ├── state/                 # State management (future)
│   └── api/                   # API server (future)
├── config/                    # Configuration
│   └── settings.py            # Settings management
├── templates/                 # Templates for generation
├── workspace/                 # Agent working directory
├── logs/                      # Application logs
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

## Configuration

Edit `.env` file or environment variables:

```env
# Groq API
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-70b-versatile
GROQ_FAST_MODEL=gemma2-9b-it

# Agent
AGENT_NAME=AutonomousAgent
MAX_ITERATIONS=10
ENABLE_SELF_IMPROVE=true

# Safety
SANDBOX_MODE=true
WORKING_DIRECTORY=workspace
MAX_FILE_SIZE_MB=10
COMMAND_TIMEOUT_SECONDS=300

# Allowed file extensions
ALLOWED_EXTENSIONS=.py,.txt,.md,.json,.yaml,.yml,.sh,.js,.ts,.html,.css,.jsx,.tsx,.vue

# Blocked paths (never access these)
BLOCKED_PATHS=/etc,/sys,/proc,/root,C:\Windows,C:\System32
```

## Security & Safety

### Sandbox Mode
When `SANDBOX_MODE=true`, all file operations are restricted to the `workspace/` directory.

### Command Whitelist
Only safe, pre-approved commands can be executed. Dangerous commands like `rm -rf`, `shutdown`, `sudo` are blocked.

### File Restrictions
- File size limits prevent memory issues
- Extension whitelist ensures only safe files are created
- Path blacklist protects system directories

### Blocked Operations
- No privilege escalation (`sudo`, `su`)
- No system modifications (`shutdown`, `reboot`)
- No dangerous deletions (`rm -rf /`)
- No direct system file access

## Example Use Cases

### 1. Web Development
```
Generate a landing page for a tech startup with hero section, features, and contact form
```

### 2. Project Setup
```
Create a new project directory called 'my-app', initialize git, and create a README.md
```

### 3. Code Analysis
```
List all Python files and count how many have 'import pandas'
```

### 4. Automation
```
Generate a React dashboard, install dependencies, and run the dev server
```

## Development

### Adding New Tools

1. Create tool class in `agent/tools/`:
```python
from agent.tools.base import BaseTool, ToolResult, ToolStatus

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "What my tool does"

    def execute(self, **kwargs) -> ToolResult:
        # Tool logic here
        return ToolResult(
            status=ToolStatus.SUCCESS,
            output="Result"
        )
```

2. Register in `main.py`:
```python
from agent.tools.my_tool import MyTool

tools = [
    MyTool(),
    # ... other tools
]
```

## Troubleshooting

### API Key Error
```
ValueError: GROQ_API_KEY not set
```
**Solution**: Set your Groq API key in `.env` file.

### Import Errors
```
ModuleNotFoundError: No module named 'groq'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`

### Permission Denied
```
Error: Path '/etc/passwd' is outside workspace
```
**Solution**: This is expected. Sandbox mode prevents access to system files.

### Command Not Allowed
```
Error: Command 'rm' is blacklisted
```
**Solution**: Use file_system tool's delete operation instead.

## Future Enhancements

- [ ] Vector memory with ChromaDB for learning
- [ ] Web API with FastAPI
- [ ] Docker containerization
- [ ] State persistence with Redis
- [ ] Self-improvement capabilities
- [ ] Multi-agent collaboration
- [ ] Web search integration
- [ ] Code execution sandbox

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

## Credits

- Powered by [Groq](https://groq.com/) - Lightning-fast LLM inference
- Models: Llama 3.1 70B, Gemma 2 9B
- Built with Python, Rich, and LangChain

---

**Made with ❤️ for autonomous AI development**
# radira
