"""
Aether Brain v3.0 — AI-Specific Prompt Engine

Transforms user vibes into world-class, AI-family-optimized prompts.
Each target AI (Claude, GPT, Gemini, Grok, Codex) gets tailored output.

Pipeline: Security Audit → Context Scan → AI-Specific Generation →
          Sanitization → Quality Scoring → Fingerprinting

Architecture: 100% LOCAL — Ollama only, no external APIs.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
import json
import queue
import uuid
from collections import defaultdict

import ollama as ollama_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from context_scanner import scan_workspace, ProjectContext
from prompt_knowledge_base import (
    get_enhanced_system_prompt,
    get_relevant_patterns,
    build_pattern_context,
    PROMPT_PATTERNS,
    CATEGORY_ENHANCEMENTS,
)
from prompt_optimizer import (
    build_optimized_prompt,
    sanitize_generated_prompt,
    score_prompt_quality,
    get_language_security_rules,
    fingerprint_prompt,
)
from security_auditor import audit_vibe, Verdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
log = logging.getLogger("brain")

app = FastAPI(title="Aether Brain", version="3.0.0")

# ── Security: CORS restricted to localhost + VS Code extension origins ──
# Note: allow_origins expects exact strings or "*". Port-wildcards are not
# supported, so we rely on allow_origin_regex for flexible matching.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^(https?://(127\.0\.0\.1|localhost)(:\d+)?|vscode-webview://.*)$",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
    allow_credentials=False,
)


# ── Security: Rate limiting (per-client, in-memory) ──

_rate_limits: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW = 60.0   # seconds
_RATE_MAX_VIBE = 30   # max vibe requests per window
_RATE_MAX_GENERAL = 120  # max general requests per window
_RATE_CLEANUP_INTERVAL = 300.0  # seconds between full cleanups
_rate_last_cleanup = 0.0


def _check_rate(key: str, limit: int) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    global _rate_last_cleanup
    now = time.monotonic()

    # Periodic full cleanup to prevent memory leak from stale keys
    if now - _rate_last_cleanup > _RATE_CLEANUP_INTERVAL:
        stale = [k for k, v in _rate_limits.items() if not v or now - v[-1] > _RATE_WINDOW]
        for k in stale:
            del _rate_limits[k]
        _rate_last_cleanup = now

    bucket = _rate_limits[key]
    # Prune old entries
    _rate_limits[key] = [t for t in bucket if now - t < _RATE_WINDOW]
    if len(_rate_limits[key]) >= limit:
        return False
    _rate_limits[key].append(now)
    return True


# ── Agent guides (reinforcement lines for llama — injected after system prompt) ──

_GUIDES: dict[str, str] = {
    "claude": "TARGET AI: Claude (Anthropic). USE XML TAGS. Include <constraints>, <edge_cases>, <security>. Be explicit and thorough.",
    "gpt": "TARGET AI: GPT (OpenAI). USE MARKDOWN. Start with 'You are...'. Use ## headers, bullet points, bold **keywords**.",
    "gpt-codex": "TARGET AI: GPT Codex (OpenAI). SPECIFICATION ONLY. Include file paths, type signatures, test cases. No prose.",
    "gemini": "TARGET AI: Gemini (Google). USE TABLES + STEP-BY-STEP. Include reasoning checkpoints. Be thorough.",
    "grok": "TARGET AI: Grok (xAI). BE CONCISE AND DIRECT. Under 500 words. Every word must earn its place.",
    "auto": "TARGET: Any AI coding agent. Use clear markdown structure with ## headers.",
}

_FAMILY_NAMES: dict[str, str] = {
    "claude": "Claude (Anthropic)", "gpt": "GPT (OpenAI)", "gpt-codex": "GPT Codex (OpenAI)",
    "gemini": "Gemini (Google)", "grok": "Grok (xAI)", "auto": "Universal (Any Agent)",
}


class VibeRequest(BaseModel):
    vibe: str = Field(..., min_length=1, max_length=8192)
    workspace_path: str = Field("")
    agent: str = Field("auto")


class PromptResponse(BaseModel):
    prompt: str
    context_summary: str = ""
    model_used: str = ""
    generation_time_ms: int = 0
    agent_used: str = ""
    quality_score: float = 0.0
    quality_grade: str = ""
    security_verdict: str = "PASS"
    prompt_fingerprint: str = ""


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.OLLAMA_MODEL}


@app.get("/agents")
async def list_agents():
    return {"families": [{"id": k, "name": v} for k, v in _FAMILY_NAMES.items()]}


@app.get("/knowledge-base")
async def knowledge_base():
    """Expose analyzed prompt patterns from prompts.chat community."""
    return {
        "total_patterns": len(PROMPT_PATTERNS),
        "categories": list(CATEGORY_ENHANCEMENTS.keys()),
        "patterns": [
            {
                "name": p.name,
                "category": p.category,
                "role": p.role,
                "capabilities_count": len(p.capabilities),
                "tags": p.tags,
            }
            for p in PROMPT_PATTERNS
        ],
    }


@app.get("/knowledge-base/{category}")
async def knowledge_base_category(category: str):
    """Get patterns and enhancement rules for a specific category."""
    patterns = [p for p in PROMPT_PATTERNS if p.category == category or category in p.tags]
    enhancements = CATEGORY_ENHANCEMENTS.get(category, {})
    return {
        "category": category,
        "patterns": [
            {
                "name": p.name,
                "role": p.role,
                "task_template": p.task_template,
                "capabilities": p.capabilities,
                "rules": p.rules,
                "output_format": p.output_format,
            }
            for p in patterns
        ],
        "enhancements": enhancements,
    }


class ScoreRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32768)


class ScoreResponse(BaseModel):
    total_score: float
    grade: str
    dimensions: dict
    fingerprint: str


@app.post("/prompt/score", response_model=ScoreResponse)
async def score_prompt_endpoint(req: ScoreRequest):
    """Score any prompt for quality and return detailed dimensions."""
    q = score_prompt_quality(req.prompt)
    fp = fingerprint_prompt(req.prompt)
    return ScoreResponse(
        total_score=q.total_score,
        grade=q.grade,
        dimensions={
            "role_clarity": q.role_score,
            "task_clarity": q.task_clarity_score,
            "structure": q.structure_score,
            "security": q.security_score,
            "actionability": q.actionability_score,
        },
        fingerprint=fp,
    )


class OptimizeRequest(BaseModel):
    vibe: str = Field(..., min_length=1, max_length=8192)
    family: str = Field("auto")
    tech_stack: str = Field("")
    language: str = Field("")


class OptimizeResponse(BaseModel):
    prompt: str
    family: str
    quality_score: float
    quality_grade: str
    fingerprint: str
    sanitized_issues: list[str]


@app.post("/prompt/optimize", response_model=OptimizeResponse)
async def optimize_prompt_endpoint(req: OptimizeRequest):
    """Generate an optimized prompt for a specific AI family without LLM."""
    if not _check_rate("optimize", _RATE_MAX_GENERAL):
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    # Security check first
    audit = audit_vibe(req.vibe)
    if audit.verdict == Verdict.FAIL:
        return JSONResponse(status_code=400, content={"detail": f"Security issue: {audit.summary()}"})
    lang_rules = get_language_security_rules(req.language) if req.language else []
    extra = "\n".join(f"- {r}" for r in lang_rules) if lang_rules else ""
    prompt = build_optimized_prompt(
        vibe=req.vibe, family=req.family, tech_stack=req.tech_stack,
        language_hint=req.language, extra_rules=extra,
    )
    prompt, issues = sanitize_generated_prompt(prompt)
    quality = score_prompt_quality(prompt)
    fp = fingerprint_prompt(prompt)

    return OptimizeResponse(
        prompt=prompt,
        family=req.family,
        quality_score=quality.total_score,
        quality_grade=quality.grade,
        fingerprint=fp,
        sanitized_issues=issues,
    )


@app.get("/models")
async def list_models():
    try:
        result = await asyncio.to_thread(ollama_client.list)
        models = []
        raw = result.get("models", []) if isinstance(result, dict) else getattr(result, "models", [])
        for m in raw:
            name = m.get("name", "") if isinstance(m, dict) else getattr(m, "model", getattr(m, "name", ""))
            size = m.get("size", 0) if isinstance(m, dict) else getattr(m, "size", 0)
            # Normalize: strip ':latest' suffix for consistent display
            if name.endswith(":latest"):
                name = name[:-7]
            models.append({"name": name, "size_mb": round(size / 1048576)})
        return {"models": models, "current": settings.OLLAMA_MODEL}
    except Exception as e:
        log.error("List models: %s", e)
        return {"models": [], "current": settings.OLLAMA_MODEL, "error": str(e)}


@app.get("/models/available")
async def available_models():
    catalog = [
        # ── Recommended (best value) ──
        {"name": "gemma3:4b", "desc": "⭐ Best Pick — Great quality/speed balance.", "size": "3.3 GB"},
        {"name": "gemma2:2b", "desc": "⚡ Fast — Quick prompt generation, low RAM.", "size": "1.6 GB"},
        {"name": "gemma3:1b", "desc": "⚡ Ultra fast — Minimal RAM. Quick iterations.", "size": "815 MB"},
        # ── Good alternatives (small) ──
        {"name": "qwen2.5:1.5b", "desc": "Efficient multilingual. Turkish/English.", "size": "986 MB"},
        {"name": "llama3.2:3b", "desc": "Good speed/quality balance.", "size": "2.0 GB"},
        {"name": "llama3.2:1b", "desc": "Tiny, instant responses. Simple prompts.", "size": "1.3 GB"},
        {"name": "codegemma:2b", "desc": "Code specialist. Tech-aware prompts.", "size": "1.6 GB"},
        {"name": "deepseek-r1:1.5b", "desc": "Reasoning-focused. Logic-heavy prompts.", "size": "1.1 GB"},
        # ── Advanced (bigger, higher quality, more RAM) ──
        {"name": "gemma2", "desc": "Strong 7B. High quality, moderate speed.", "size": "5.4 GB"},
        {"name": "phi4", "desc": "Best reasoning. Top quality, needs 12GB+ RAM.", "size": "9.1 GB"},
        {"name": "llama3.1:8b", "desc": "Powerful 8B. Excellent quality, needs 8GB+ RAM.", "size": "4.7 GB"},
        {"name": "mistral", "desc": "Versatile 7B. Reliable quality.", "size": "4.1 GB"},
        {"name": "qwen2.5:7b", "desc": "Strong multilingual 7B. Non-English prompts.", "size": "4.7 GB"},
        {"name": "deepseek-r1:7b", "desc": "Advanced reasoning. Complex architectures.", "size": "4.7 GB"},
        {"name": "codellama:7b", "desc": "Code specialist 7B. Deep understanding.", "size": "3.8 GB"},
    ]
    installed_names: set[str] = set()
    try:
        result = await asyncio.to_thread(ollama_client.list)
        raw = result.get("models", []) if isinstance(result, dict) else getattr(result, "models", [])
        for m in raw:
            n = m.get("name", "") if isinstance(m, dict) else getattr(m, "model", getattr(m, "name", ""))
            installed_names.add(n)
            # Also add with :latest suffix stripped for matching
            if n.endswith(":latest"):
                installed_names.add(n.replace(":latest", ""))
    except Exception:
        pass
    for item in catalog:
        # Exact match only — don't match base name (gemma3:1b ≠ gemma3:4b)
        item["installed"] = item["name"] in installed_names
    return {"catalog": catalog}


class PullModelRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=256)


@app.post("/models/pull")
async def pull_model(req: PullModelRequest):
    """Pull model with SSE progress events."""
    model = req.model
    log.info("Pulling model: %s", model)

    q_: queue.Queue = queue.Queue()

    def _pull_sync():
        """Runs in a background thread — ollama.pull is blocking."""
        try:
            gen = ollama_client.pull(model, stream=True)
            for chunk in gen:
                total = 0
                completed = 0
                status_text = ""

                if isinstance(chunk, dict):
                    status_text = chunk.get("status", "")
                    total = chunk.get("total", 0)
                    completed = chunk.get("completed", 0)
                else:
                    status_text = getattr(chunk, "status", "")
                    total = getattr(chunk, "total", 0) or 0
                    completed = getattr(chunk, "completed", 0) or 0

                pct = 0
                if total and total > 0:
                    pct = min(100, int(completed * 100 / total))

                q_.put({"status": status_text, "pct": pct})

            q_.put({"status": "done", "pct": 100})
            log.info("Pull complete: %s", model)
        except Exception as e:
            log.error("Pull failed: %s", e)
            q_.put({"status": "error", "message": str(e)})
        finally:
            q_.put(None)  # sentinel

    async def _stream():
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _pull_sync)

        while True:
            try:
                item = await asyncio.to_thread(q_.get, timeout=300)
            except Exception:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Download timeout'})}\n\n"
                break
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


class SetModelRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=256)


@app.post("/model")
async def set_model(req: SetModelRequest):
    settings.OLLAMA_MODEL = req.model
    log.info("Model changed to: %s", req.model)
    return {"status": "ok", "model": req.model}


@app.post("/vibe", response_model=PromptResponse)
async def vibe(req: VibeRequest) -> PromptResponse:
    request_id = uuid.uuid4().hex[:8]

    # Rate limit check (per-endpoint, not per-client since localhost-only)
    if not _check_rate("vibe", _RATE_MAX_VIBE):
        return PromptResponse(
            prompt="⚠️ Rate limit exceeded. Please wait a moment before trying again.",
            security_verdict="WARN",
            model_used=settings.OLLAMA_MODEL,
        )

    family = req.agent.lower().strip() if req.agent else "auto"
    if family not in _GUIDES:
        family = "auto"

    log.info("[%s] Vibe [%s]: %s", request_id, family, req.vibe[:100])
    t0 = time.monotonic()

    # ── 1. Security audit on raw vibe input ──────────────────────────
    audit = audit_vibe(req.vibe)
    if audit.verdict == Verdict.FAIL:
        log.warning("Security FAIL: %s", audit.summary())
        return PromptResponse(
            prompt=f"⚠️ Security issue detected:\n{audit.summary()}\n\nPlease rephrase your request.",
            security_verdict="FAIL",
            model_used=settings.OLLAMA_MODEL,
            generation_time_ms=0,
            agent_used=family,
        )

    # ── 2. Scan workspace context ────────────────────────────────────
    ctx_hint = ""
    if req.workspace_path:
        # Validate workspace path: must exist and be a directory
        from pathlib import Path
        ws_path = Path(req.workspace_path).resolve()
        if ws_path.is_dir() and not any(
            part.startswith('.') for part in ws_path.parts[1:]
        ):
            ctx = scan_workspace(str(ws_path))
            ctx_hint = _ctx(ctx)
        else:
            log.warning("[%s] Invalid workspace path: %s", request_id, req.workspace_path[:100])

    # ── 3. Generate prompt (AI-specific) ─────────────────────────────
    prompt = await _gen(req.vibe, ctx_hint, family)

    # ── 4. Sanitize generated prompt ─────────────────────────────────
    prompt, sanitize_issues = sanitize_generated_prompt(prompt)
    if sanitize_issues:
        log.warning("Sanitized %d issues in generated prompt", len(sanitize_issues))

    # ── 5. Quality score ─────────────────────────────────────────────
    quality = score_prompt_quality(prompt)

    # If quality is too low and model generated something, use optimized fallback
    if quality.total_score < 40 and len(prompt) > 20:
        log.warning("Quality too low (%.0f), upgrading with optimizer", quality.total_score)
        lang_hint = ctx_hint.split("/")[0].strip() if ctx_hint else ""
        prompt = build_optimized_prompt(
            vibe=req.vibe, family=family,
            tech_stack=ctx_hint,
            language_hint=lang_hint,
        )
        quality = score_prompt_quality(prompt)

    # ── 6. Fingerprint for traceability ──────────────────────────────
    fp = fingerprint_prompt(prompt)

    ms = int((time.monotonic() - t0) * 1000)
    log.info(
        "[%s] Done %d chars / %dms / family=%s / quality=%s (%.0f) / fp=%s",
        request_id, len(prompt), ms, family, quality.grade, quality.total_score, fp,
    )

    return PromptResponse(
        prompt=prompt,
        context_summary=ctx_hint,
        model_used=settings.OLLAMA_MODEL,
        generation_time_ms=ms,
        agent_used=family,
        quality_score=quality.total_score,
        quality_grade=quality.grade,
        security_verdict=audit.verdict.value,
        prompt_fingerprint=fp,
    )


# ── Prompt generation (AI-Specific + Knowledge Base + Security) ───────
# DESIGN: Each AI family gets its own optimized system prompt.
# Knowledge base provides category-aware patterns.
# Security layer sanitizes both input AND output.
# Quality scorer ensures minimum quality threshold.


async def _gen(vibe: str, ctx_hint: str, family: str) -> str:
    """Generate AI-optimized prompt. Each family gets tailored instructions."""
    user_msg = vibe.strip()
    if ctx_hint:
        user_msg += f"\n[Tech: {ctx_hint}]"

    # Find relevant patterns from knowledge base
    patterns = get_relevant_patterns(vibe)
    pattern_ctx = build_pattern_context(patterns)
    if pattern_ctx:
        user_msg += f"\n{pattern_ctx}"

    # Build AI-SPECIFIC system prompt (different for each target AI)
    system = get_enhanced_system_prompt(category_hint=vibe, family=family)
    agent_line = _GUIDES.get(family, _GUIDES["auto"])
    system += "\n" + agent_line

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]

    try:
        resp = await asyncio.to_thread(
            ollama_client.chat,
            model=settings.OLLAMA_MODEL,
            messages=messages,
            stream=False,
            options={
                "num_predict": min(settings.OLLAMA_MAX_TOKENS, 768),
                "temperature": settings.OLLAMA_TEMPERATURE,
                "num_ctx": 2048,
            },
        )

        raw = ""
        if hasattr(resp, "message"):
            raw = resp.message.content.strip()
        elif isinstance(resp, dict) and "message" in resp:
            raw = resp["message"]["content"].strip()

        cleaned = _clean(raw)

        if _is_bad(cleaned):
            log.warning("Bad output detected, using fallback")
            return _fallback(vibe, ctx_hint, family)

        if len(cleaned) < 40:
            log.warning("Output too short (%d chars), using fallback", len(cleaned))
            return _fallback(vibe, ctx_hint, family)

        return cleaned

    except Exception as e:
        log.error("Ollama error: %s", e)
        return _fallback(vibe, ctx_hint, family)


def _clean(text: str) -> str:
    """Strip fences, preambles, trailing artifacts."""
    text = re.sub(r"```[\w]*\n?", "", text).strip()
    text = re.sub(
        r"^(Here is|Here's|Below is|The following|Sure|Okay|Of course|Certainly|I'll)[^\n]*\n+",
        "", text, flags=re.IGNORECASE
    ).strip()
    text = re.sub(r"\n*(END EXAMPLE|END|---)\s*$", "", text).strip()
    return text


def _is_bad(text: str) -> bool:
    """Detect conversational or code output — trigger fallback."""
    low = text.lower()

    # Model acting as assistant instead of prompt engineer
    bad_phrases = [
        "how can i help", "please provide", "what programming language",
        "what would you like", "i'd be happy", "i can help", "let me know",
        "could you please", "tell me more", "what specific", "please share",
        "i need more", "can you provide", "what is the purpose",
        "are there any specific", "i'll help you",
    ]
    if any(p in low for p in bad_phrases):
        return True

    # Code instead of prompt (2+ code markers in first 200 chars)
    code_marks = [
        "import ", "from ", "def ", "class ", "function ", "const ", "let ",
        "return ", "export ", "<!doctype", "<html", "console.log(",
    ]
    head = low[:200]
    if sum(1 for m in code_marks if m in head) >= 2:
        return True

    return False


def _fallback(vibe: str, ctx_hint: str, family: str) -> str:
    """AI-optimized deterministic prompt when model fails or is too slow.

    Uses build_optimized_prompt() from prompt_optimizer to produce
    world-class, AI-family-specific prompts even without the LLM.
    """
    # Extract language from ctx_hint (format: "python / FastAPI")
    lang_hint = ctx_hint.split("/")[0].strip() if ctx_hint else ""
    lang_security = get_language_security_rules(lang_hint) if lang_hint else ""

    return build_optimized_prompt(
        vibe=vibe,
        family=family,
        tech_stack=ctx_hint,
        language_hint=lang_hint,
        extra_rules=lang_security,
    )


# ── Context detection ─────────────────────────────────────────────────

_MARKERS: dict[str, str] = {
    "next.config.js": "Next.js", "next.config.ts": "Next.js",
    "nuxt.config.ts": "Nuxt", "angular.json": "Angular",
    "svelte.config.js": "SvelteKit", "astro.config.mjs": "Astro",
    "vite.config.ts": "Vite", "vite.config.js": "Vite",
    "tailwind.config.js": "Tailwind", "manage.py": "Django",
    "app.py": "Flask/FastAPI", "pubspec.yaml": "Flutter",
    "Cargo.toml": "Rust", "go.mod": "Go", "CMakeLists.txt": "C/C++",
    "Dockerfile": "Docker", "Gemfile": "Ruby", "composer.json": "PHP",
    "pom.xml": "Java", "build.gradle.kts": "Kotlin",
    "tsconfig.json": "TypeScript", "package.json": "Node.js",
}


def _ctx(c: ProjectContext) -> str:
    parts = []
    if c.language_hint:
        parts.append(c.language_hint)
    files = set(c.file_tree or [])
    for marker, name in _MARKERS.items():
        if marker in files and name not in parts:
            parts.append(name)
            break
    return " / ".join(parts[:2]) if parts else ""


if __name__ == "__main__":
    import sys
    import socket
    import uvicorn

    use_reload = "--reload" in sys.argv
    port = settings.PORT

    # Try to kill whatever holds the port, then try binding
    def _port_free(p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((settings.HOST, p))
                return True
            except OSError:
                return False

    if not _port_free(port):
        # Try to gracefully shut down the old server
        try:
            import urllib.request
            urllib.request.urlopen(f"http://{settings.HOST}:{port}/health", timeout=1)
        except Exception:
            pass
        # If still occupied, try alternate port
        if not _port_free(port):
            for alt in range(port + 1, port + 10):
                if _port_free(alt):
                    log.warning("Port %d busy, using %d instead", port, alt)
                    port = alt
                    break

    log.info("Brain v3.0 | %s | :%d | reload=%s", settings.OLLAMA_MODEL, port, use_reload)
    uvicorn.run(
        "sslm_engine:app",
        host=settings.HOST,
        port=port,
        reload=use_reload,
        timeout_keep_alive=30,
    )
