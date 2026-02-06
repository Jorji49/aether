# Aether — AI Prompt Optimizer

> Transform rough ideas into perfect AI prompts. Powered by local Ollama models — your data stays private.

![Visual Studio Marketplace](https://img.shields.io/visual-studio-marketplace/v/AhmetKayraKama.aether-prompt-generator)
![License](https://img.shields.io/github/license/Jorji49/aether)

## Features

- **Vibe-to-Prompt**: Type a rough idea like "create a login page" and get a fully structured, production-ready AI prompt
- **100% Local & Private**: Runs entirely on your machine via Ollama — no data leaves your computer
- **Multi-IDE Support**: Works with Cursor, Windsurf, Claude Code, GitHub Copilot, and VS Code
- **Smart Context Scanning**: Automatically analyzes your project structure for context-aware prompts
- **Agent Selector**: Choose your target AI model (Claude, GPT, Gemini, Grok) for optimized prompt formatting
- **Quality Scoring**: Every generated prompt gets a quality grade (A+, A, B, C, D)
- **Security Auditing**: Prompts are checked for injection risks and sensitive data leaks
- **One-Click Model Management**: Download, switch, and manage Ollama models from the sidebar
- **Send to Agent**: Instantly send generated prompts to your IDE's AI assistant

## Quick Start

### Prerequisites

1. **[Ollama](https://ollama.com)** — Install and run locally
2. **Python 3.10+** — For the Brain backend server

### Setup

1. Install the Aether extension from the VS Code Marketplace
2. Open a project folder in your IDE
3. Run the command **"Aether: Start Brain"** from the Command Palette (`Ctrl+Shift+P`)
4. The extension will:
   - Start Ollama (if not running)
   - Install Python dependencies
   - Launch the Brain server on port 8420
5. Select a model in the Welcome screen (recommended: **gemma3:4b**)
6. Start typing your ideas!

## How It Works

```
Your Idea → Aether Brain → Ollama (Local LLM) → Optimized Prompt → Your AI Agent
```

1. **You type** a rough idea in the Aether sidebar
2. **Context Scanner** analyzes your project (files, structure, tech stack)
3. **Prompt Optimizer** crafts a detailed, structured prompt using the local LLM
4. **Quality Auditor** scores the output and checks for security issues
5. **One click** sends the prompt to your AI agent (Cursor, Copilot, etc.)

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `aether.brainServerUrl` | `http://127.0.0.1:8420` | Brain server URL |
| `aether.ollamaModel` | `gemma2:2b` | Ollama model for prompt generation |
| `aether.maxContextFiles` | `30` | Max project files to scan for context |
| `aether.autoSendToAgent` | `false` | Auto-send prompt to AI agent |
| `aether.ollamaTemperature` | `0.1` | Generation temperature (0.0–1.0) |
| `aether.ollamaMaxTokens` | `1024` | Max tokens for generated prompts |

## Recommended Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| gemma3:4b | 3.3 GB | ⚡⚡ | ⭐⭐⭐ | Best balance (recommended) |
| gemma2:2b | 1.6 GB | ⚡⚡⚡ | ⭐⭐ | Fast iterations |
| gemma3:1b | 815 MB | ⚡⚡⚡⚡ | ⭐ | Ultra-fast, low RAM |
| phi4 | 9.1 GB | ⚡ | ⭐⭐⭐⭐ | Highest quality |
| llama3.1:8b | 4.7 GB | ⚡ | ⭐⭐⭐⭐ | Strong general use |

## Privacy

Aether is designed with privacy as a core principle:

- **Zero cloud dependency** — All processing happens locally
- **No telemetry** — We don't collect any usage data
- **No API keys needed** — Works entirely with local Ollama models
- **Your code stays yours** — Context scanning is local-only

## Architecture

```
aether/
├── brain/              # Python backend (FastAPI)
│   ├── sslm_engine.py          # Main server & Ollama integration
│   ├── prompt_optimizer.py     # Prompt generation engine
│   ├── prompt_knowledge_base.py # Best practices & patterns
│   ├── context_scanner.py      # Project analysis
│   ├── security_auditor.py     # Security checks
│   └── config.py               # Configuration
└── extension/          # VS Code extension (TypeScript)
    └── src/
        ├── extension.ts            # Entry point
        ├── providers/SidebarProvider.ts  # UI
        ├── services/BrainClient.ts      # HTTP client
        └── utils/config.ts              # Settings
```

## Commands

| Command | Description |
|---------|-------------|
| `Aether: Send Vibe` | Enter a prompt idea via input box |
| `Aether: Start Brain` | Start the Ollama + Brain server |
| `Aether: Send to Agent` | Send a prompt to your AI assistant |

## Troubleshooting

### Brain server won't start
- Make sure Python 3.10+ is installed: `python --version`
- Make sure Ollama is installed: `ollama --version`
- Check if port 8420 is available

### No models showing up
- Ensure Ollama is running: `ollama serve`
- Try pulling a model manually: `ollama pull gemma2:2b`

### Extension not connecting
- Check the Brain server URL in settings
- The extension auto-discovers ports 8420–8429

## License

MIT © [AhmetKayraKama](https://github.com/Jorji49)
