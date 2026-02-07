# Changelog

All notable changes to the Aether extension will be documented in this file.

## [1.0.2] - 2026-02-07

### Fixed
- Bug: `_fallback()` passed `list[str]` instead of `str` for security rules — caused crashes on fallback prompts
- `num_predict` was hard-capped at 768 tokens even with higher settings — now respects up to 2048
- Context window (`num_ctx`) increased from 2048 → 4096 for better prompt generation with larger vibes
- Security auditor vibe length warning raised from 4000 → 12000 chars

### Changed
- Default `OLLAMA_MAX_TOKENS` increased from 1024 → 2048
- Vibe input limit increased from 8192 → 16384 characters (backend)
- Prompt output area max-height increased from 400px → 600px
- Textarea max-height increased from 140px → 200px for longer inputs
- Max tokens setting range expanded: 512 – 8192 (was 256 – 4096)

### Added
- `.env.example` file for easy brain configuration

## [1.0.1] - 2026-02-07

### Fixed
- Brain folder discovery now checks 5 locations including user home directory
- Added manual folder picker when Brain is not found automatically
- Translated all Turkish UI text to English

## [1.0.0] - 2026-02-07

### Added
- Initial release of Aether — AI Prompt Optimizer
- Vibe-to-prompt generation powered by local Ollama models
- Smart project context scanning (files, structure, tech stack)
- Multi-IDE support: Cursor, Windsurf, Claude Code, GitHub Copilot, VS Code
- Agent selector panel with Claude, GPT, Gemini, and Grok model families
- Quality scoring and grading system (A+ to D)
- Security auditing for prompt injection and data leak detection
- One-click model download and management from sidebar
- Ollama auto-start on Brain launch
- Resilient health check with 3-failure threshold
- Chat history persistence across sessions
- Dark theme UI optimized for IDE sidebars
- Send-to-Agent with automatic IDE detection
- Clipboard fallback for unsupported environments
