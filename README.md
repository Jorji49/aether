# Aether - AI Prompt Optimizer

Transform rough ideas ("vibes") into perfect, AI-optimized prompts. Powered by **local Ollama models** — your data stays private.

## Features

- **AI-Specific Optimization**: Tailored prompts for Claude, GPT, Gemini, Grok, and Codex
- **100% Local & Private**: Uses Ollama — no data leaves your machine
- **Context-Aware**: Scans your workspace to generate project-specific prompts
- **Security-First**: Built-in prompt injection detection and OWASP compliance
- **Fast**: Generate prompts in <1 second with small models
- **Quality Scoring**: Automatic quality assessment of generated prompts

## Quick Start

### Prerequisites

1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull gemma2:2b` (recommended starter model)

### Installation

1. Install from VS Code Marketplace: Search "Aether" or [click here](https://marketplace.visualstudio.com/items?itemName=kama.aether)
2. Start the Aether Brain backend:
   ```bash
   cd brain
   pip install -r requirements.txt
   python sslm_engine.py
   ```
3. Open Aether sidebar in VS Code (brain icon in activity bar)

### Usage

1. Type your rough idea in the "Vibe" input (e.g., "create a REST API for user auth")
2. Select target AI (Claude, GPT, Gemini, etc.)
3. Click "Generate Prompt"
4. Copy optimized prompt and paste into your AI tool

### Example

**Input (Vibe):** `create a secure REST API for user authentication`

**Output:**

```xml
<role>
Senior Backend Engineer specializing in API design. 10+ years production experience...
</role>

<objective>
Create a secure REST API for user authentication with JWT tokens...
</objective>

<security>
- Use bcrypt/argon2 for password hashing
- Implement rate limiting on auth endpoints
- CSRF protection for state-changing operations
</security>
```

## Configuration

Access via VS Code Settings (`Cmd/Ctrl + ,` → search "Aether"):

| Setting | Default | Description |
|---------|---------|-------------|
| Ollama Model | `gemma2:2b` | Change to `phi4` for higher quality |
| Brain Server URL | `http://127.0.0.1:8420` | Only change if running Brain remotely |
| Max Context Files | `30` | How many project files to scan (20–50 recommended) |
| Temperature | `0.1` | 0.1 for coding (focused), 0.7 for creative tasks |
| Auto Send to Agent | `false` | Automatically send generated prompt to AI agent |

## Quality Scoring

Every generated prompt is scored across 5 dimensions:

- **Role Clarity**: Expert persona definition
- **Task Clarity**: Clear, actionable objectives
- **Structure**: Logical organization
- **Security**: OWASP compliance, input validation
- **Actionability**: Specific, executable instructions

Grade scale: **A+** (90+), **A** (80–89), **B** (70–79), **C** (60–69), **D** (<60)

## Security

- **Local-first**: No cloud APIs, no telemetry
- **Prompt injection detection**: Built-in safety checks
- **Rate limiting**: 30 requests/minute to prevent abuse
- **CORS restricted**: localhost + VS Code webviews only

## License

MIT License — see [LICENSE.md](LICENSE.md)

## Acknowledgments

Built on top of:

- [Ollama](https://ollama.ai) — Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com) — Backend framework
- Prompt patterns from [prompts.chat](https://prompts.chat) community

Made with love by kama