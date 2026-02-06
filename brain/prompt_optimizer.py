"""
Aether Brain — AI-Specific Prompt Optimizer

Each AI model has unique strengths, formatting preferences, and optimization
techniques. This module generates world-class prompts tailored for EACH target AI.

Sources:
  - Community analysis (25+ prompts from prompts.chat)
  - AI provider documentation (Anthropic, OpenAI, Google, xAI)
  - Prompt engineering research (Chain-of-Thought, Tree-of-Thought, etc.)

Security: All generated prompts include built-in safety constraints.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════════════
# 1. AI-SPECIFIC PROFILE DEFINITIONS
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AIProfile:
    """Immutable profile defining how to optimize prompts for a specific AI."""
    id: str
    name: str
    provider: str

    # Formatting preferences
    uses_xml_tags: bool = False
    uses_markdown: bool = True
    uses_json_schema: bool = False
    supports_system_prompt: bool = True

    # Optimal techniques
    best_techniques: tuple[str, ...] = ()

    # Token optimization
    max_recommended_tokens: int = 4096
    prefers_concise: bool = False

    # Prompt structure template
    structure_template: str = ""

    # Security constraints to always inject
    security_constraints: tuple[str, ...] = ()

    # Anti-patterns to avoid for this AI
    anti_patterns: tuple[str, ...] = ()


# ── AI Profile Registry ─────────────────────────────────────────────

AI_PROFILES: dict[str, AIProfile] = {

    # ─── Claude (Anthropic) ──────────────────────────────────────────
    "claude": AIProfile(
        id="claude",
        name="Claude (Anthropic)",
        provider="Anthropic",
        uses_xml_tags=True,
        uses_markdown=True,
        supports_system_prompt=True,
        best_techniques=(
            "xml_structured_prompting",
            "explicit_constraints",
            "chain_of_thought",
            "constitutional_ai_alignment",
            "artifact_generation",
            "prefill_technique",
        ),
        max_recommended_tokens=8192,
        prefers_concise=False,
        structure_template="""\
<system>
<role>{role}</role>
<expertise>{expertise}</expertise>
</system>

<context>
<project_type>{project_type}</project_type>
<tech_stack>{tech_stack}</tech_stack>
<constraints>
{constraints}
</constraints>
</context>

<task>
<objective>{objective}</objective>
<requirements>
{requirements}
</requirements>
<deliverables>
{deliverables}
</deliverables>
</task>

<quality_gates>
{quality_gates}
</quality_gates>

<output_format>
{output_format}
</output_format>

<security_requirements>
- Never output credentials, API keys, or secrets in generated code
- Always sanitize user inputs before processing
- Use parameterized queries for all database operations
- Implement proper authentication and authorization checks
- Follow the principle of least privilege
- Never use eval(), exec(), or dynamic code execution with user input
</security_requirements>""",
        security_constraints=(
            "Never output credentials, API keys, or secrets in generated code",
            "Always sanitize user inputs before processing",
            "Use parameterized queries for all database operations",
            "Implement CSRF protection for all state-changing operations",
            "Follow OWASP Top 10 security guidelines",
        ),
        anti_patterns=(
            "Avoid 'Please' or overly polite language — Claude responds to clear directives",
            "Don't use JSON for structuring — XML tags work better with Claude",
            "Avoid vague 'be helpful' instructions — be specific about behavior",
        ),
    ),

    # ─── GPT (OpenAI) ───────────────────────────────────────────────
    "gpt": AIProfile(
        id="gpt",
        name="GPT (OpenAI)",
        provider="OpenAI",
        uses_xml_tags=False,
        uses_markdown=True,
        uses_json_schema=True,
        supports_system_prompt=True,
        best_techniques=(
            "persona_based_prompting",
            "markdown_structured",
            "few_shot_examples",
            "chain_of_thought",
            "step_by_step_reasoning",
            "json_mode_output",
        ),
        max_recommended_tokens=4096,
        prefers_concise=False,
        structure_template="""\
# System Instructions

You are {role}. {expertise}

## Context
- **Project Type**: {project_type}
- **Tech Stack**: {tech_stack}
- **Constraints**: {constraints}

## Your Task
{objective}

### Requirements
{requirements}

### Deliverables
{deliverables}

## Quality Standards
{quality_gates}

## Output Format
{output_format}

## Security Requirements
- Never expose sensitive data (API keys, passwords, tokens) in code output
- Always validate and sanitize all user inputs
- Use parameterized queries — never string concatenation for SQL
- Implement proper error handling without exposing stack traces to users
- Apply Content Security Policy headers for web applications
- Use HTTPS for all external communications""",
        security_constraints=(
            "Never expose sensitive data in code output",
            "Always validate and sanitize all user inputs",
            "Use parameterized queries for database operations",
            "Implement proper error handling without exposing internals",
            "Apply Content Security Policy headers",
        ),
        anti_patterns=(
            "Don't use XML tags — GPT responds best to markdown",
            "Avoid extremely long system prompts — GPT can lose focus",
            "Don't ask GPT to 'not do' things — tell it what TO do",
        ),
    ),

    # ─── GPT Codex (OpenAI) ─────────────────────────────────────────
    "gpt-codex": AIProfile(
        id="gpt-codex",
        name="GPT Codex (OpenAI)",
        provider="OpenAI",
        uses_xml_tags=False,
        uses_markdown=True,
        uses_json_schema=True,
        supports_system_prompt=True,
        best_techniques=(
            "code_first_prompting",
            "type_signature_hints",
            "test_driven_prompting",
            "file_path_context",
            "docstring_style_instructions",
            "function_signature_prefill",
        ),
        max_recommended_tokens=4096,
        prefers_concise=True,
        structure_template="""\
# Codex Task

**Role**: {role}
**Expertise**: {expertise}

## Project Context
```
Type: {project_type}
Stack: {tech_stack}
```

## Objective
{objective}

## Technical Requirements
{requirements}

## Expected Files & Signatures
{deliverables}

## Quality Checklist
{quality_gates}

## Security Checklist
- [ ] All user inputs validated and sanitized
- [ ] No hardcoded secrets or credentials
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF tokens for state-changing endpoints
- [ ] Rate limiting on sensitive endpoints
- [ ] Proper authentication/authorization guards

## Output
{output_format}""",
        security_constraints=(
            "All user inputs validated and sanitized",
            "No hardcoded secrets — use environment variables",
            "SQL injection prevention via parameterized queries",
            "XSS prevention via output encoding",
            "Rate limiting on authentication endpoints",
        ),
        anti_patterns=(
            "Don't write prose — Codex wants specifications, not explanations",
            "Always include file paths and function signatures",
            "Include test cases as part of the specification",
        ),
    ),

    # ─── Gemini (Google) ─────────────────────────────────────────────
    "gemini": AIProfile(
        id="gemini",
        name="Gemini (Google)",
        provider="Google",
        uses_xml_tags=False,
        uses_markdown=True,
        uses_json_schema=True,
        supports_system_prompt=True,
        best_techniques=(
            "structured_chain_of_thought",
            "step_by_step_planning",
            "multi_turn_refinement",
            "grounded_generation",
            "explicit_reasoning_steps",
            "safety_settings_aware",
        ),
        max_recommended_tokens=8192,
        prefers_concise=False,
        structure_template="""\
# Task Definition

## Role & Expertise
{role} — {expertise}

## Project Context
| Attribute | Value |
|-----------|-------|
| Project Type | {project_type} |
| Tech Stack | {tech_stack} |
| Constraints | {constraints} |

## Objective
{objective}

## Step-by-Step Plan
Think through this step by step:

### Requirements
{requirements}

### Expected Deliverables
{deliverables}

## Quality Standards
{quality_gates}

## Security Standards
1. Input Validation: Validate type, length, format, and range of all inputs
2. Authentication: Implement secure session management with proper token handling
3. Data Protection: Encrypt sensitive data at rest and in transit
4. Access Control: Implement role-based access control (RBAC)
5. Error Handling: Use generic error messages for users, detailed logs for developers
6. Dependencies: Use only trusted, up-to-date packages with known CVE patches

## Output Format
{output_format}""",
        security_constraints=(
            "Validate type, length, format, and range of all inputs",
            "Implement secure session management",
            "Encrypt sensitive data at rest and in transit",
            "Implement role-based access control",
            "Use only trusted, up-to-date dependencies",
        ),
        anti_patterns=(
            "Don't use XML — Gemini prefers markdown and tables",
            "Include explicit 'think step by step' for complex tasks",
            "Avoid overly nested structures — keep flat and scannable",
        ),
    ),

    # ─── Grok (xAI) ─────────────────────────────────────────────────
    "grok": AIProfile(
        id="grok",
        name="Grok (xAI)",
        provider="xAI",
        uses_xml_tags=False,
        uses_markdown=True,
        supports_system_prompt=True,
        best_techniques=(
            "direct_instruction",
            "code_focused_prompting",
            "concise_specification",
            "example_driven",
            "real_world_context",
        ),
        max_recommended_tokens=4096,
        prefers_concise=True,
        structure_template="""\
**Role**: {role} | {expertise}

**Context**: {project_type} / {tech_stack}
{constraints}

**Task**: {objective}

**Requirements**:
{requirements}

**Deliver**:
{deliverables}

**Quality**:
{quality_gates}

**Security**:
- Sanitize all inputs. No eval/exec with user data.
- Parameterized queries only. No string concat for SQL.
- No hardcoded secrets. Use env vars.
- Validate auth on every protected endpoint.
- Rate limit sensitive operations.

**Format**:
{output_format}""",
        security_constraints=(
            "Sanitize all inputs — no eval/exec with user data",
            "Parameterized queries only",
            "No hardcoded secrets — use env vars",
            "Validate auth on every protected endpoint",
        ),
        anti_patterns=(
            "Don't be verbose — Grok likes direct, concise instructions",
            "Skip preambles and philosophical context",
            "Get to the point quickly",
        ),
    ),

    # ─── Auto (Universal) ───────────────────────────────────────────
    "auto": AIProfile(
        id="auto",
        name="Universal (Any Agent)",
        provider="Any",
        uses_xml_tags=False,
        uses_markdown=True,
        supports_system_prompt=True,
        best_techniques=(
            "clear_structure",
            "explicit_constraints",
            "numbered_steps",
            "chain_of_thought",
        ),
        max_recommended_tokens=4096,
        prefers_concise=False,
        structure_template="""\
## ROLE
{role}
{expertise}

## CONTEXT
- Project: {project_type}
- Stack: {tech_stack}
- Constraints: {constraints}

## OBJECTIVE
{objective}

## REQUIREMENTS
{requirements}

## DELIVERABLES
{deliverables}

## QUALITY STANDARDS
{quality_gates}

## SECURITY REQUIREMENTS
- Sanitize and validate all user inputs
- Use parameterized queries for database operations
- Never hardcode credentials or secrets
- Implement proper authentication and authorization
- Follow OWASP Top 10 security guidelines
- Handle errors gracefully without exposing internals

## OUTPUT FORMAT
{output_format}""",
        security_constraints=(
            "Sanitize and validate all user inputs",
            "Use parameterized queries for database operations",
            "Never hardcode credentials or secrets",
            "Implement proper authentication and authorization",
            "Follow OWASP Top 10 guidelines",
        ),
        anti_patterns=(),
    ),
}


# ══════════════════════════════════════════════════════════════════════
# 2. PROMPT OPTIMIZATION TECHNIQUES
# ══════════════════════════════════════════════════════════════════════

@dataclass
class PromptTechnique:
    """A specific prompt engineering technique with applicability rules."""
    name: str
    description: str
    when_to_use: str
    injection_template: str
    effectiveness_score: float  # 0.0 - 1.0


TECHNIQUES: dict[str, PromptTechnique] = {
    "chain_of_thought": PromptTechnique(
        name="Chain of Thought",
        description="Break complex problems into sequential reasoning steps",
        when_to_use="Complex logic, architecture decisions, multi-step implementations",
        injection_template="Think through this step by step before implementing:\n1. Analyze the requirements\n2. Design the approach\n3. Consider edge cases\n4. Implement the solution\n5. Verify correctness",
        effectiveness_score=0.9,
    ),
    "few_shot_examples": PromptTechnique(
        name="Few-Shot Examples",
        description="Provide input/output examples to demonstrate expected behavior",
        when_to_use="Pattern-based tasks, formatting requirements, API design",
        injection_template="Example:\nInput: {example_input}\nExpected Output: {example_output}",
        effectiveness_score=0.85,
    ),
    "constraint_anchoring": PromptTechnique(
        name="Constraint Anchoring",
        description="Place critical constraints at both beginning and end of prompt",
        when_to_use="All prompts — especially when constraints are critical",
        injection_template="CRITICAL: {constraint}\n...\nREMINDER: {constraint}",
        effectiveness_score=0.8,
    ),
    "role_depth": PromptTechnique(
        name="Deep Role Definition",
        description="Give the AI a specific background, years of experience, and personality",
        when_to_use="All expert-level tasks",
        injection_template="Act as a {role} with {years}+ years of experience specializing in {specialty}. Your approach is {tone} and you prioritize {priorities}.",
        effectiveness_score=0.85,
    ),
    "negative_constraints": PromptTechnique(
        name="Negative Constraints",
        description="Explicitly state what NOT to do — prevents common AI failure modes",
        when_to_use="Code generation, where AIs tend to add boilerplate or hallucinate",
        injection_template="DO NOT:\n- Generate placeholder or TODO comments\n- Use deprecated APIs or patterns\n- Include unnecessary dependencies\n- Hardcode configuration values\n- Skip error handling",
        effectiveness_score=0.75,
    ),
    "output_scaffolding": PromptTechnique(
        name="Output Scaffolding",
        description="Provide the exact structure of the expected output",
        when_to_use="When output format is critical — APIs, reports, code files",
        injection_template="Your response must follow this exact structure:\n{scaffold}",
        effectiveness_score=0.9,
    ),
    "security_by_default": PromptTechnique(
        name="Security by Default",
        description="Embed security requirements as non-negotiable constraints",
        when_to_use="ALL code generation tasks",
        injection_template="SECURITY (non-negotiable):\n- All inputs MUST be validated before use\n- All outputs MUST be sanitized/escaped\n- All secrets MUST come from environment variables\n- All DB queries MUST use parameterized statements\n- All auth MUST be checked on every request",
        effectiveness_score=0.95,
    ),
}


# ══════════════════════════════════════════════════════════════════════
# 3. SECURITY LAYER FOR GENERATED PROMPTS
# ══════════════════════════════════════════════════════════════════════

# Patterns that should NEVER appear in a generated prompt
_DANGEROUS_PROMPT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("prompt_injection", re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I)),
    ("prompt_injection", re.compile(r"disregard\s+(all\s+)?(prior|above)", re.I)),
    ("role_hijack", re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.I)),
    ("credential_leak", re.compile(r"(sk-[a-zA-Z0-9]{20,})")),
    ("credential_leak", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("credential_leak", re.compile(r"-----BEGIN\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY", re.I)),
    ("destructive_cmd", re.compile(r"rm\s+-rf\s+/", re.I)),
    ("destructive_cmd", re.compile(r"DROP\s+(TABLE|DATABASE|SCHEMA)", re.I)),
    ("data_exfil", re.compile(r"(curl|wget|fetch)\s+https?://[^\s]+\s+.*(-d|--data)", re.I)),
    ("eval_injection", re.compile(r"\beval\s*\(\s*['\"].*user", re.I)),
]

# Auto-injected security constraints per language
_LANG_SECURITY: dict[str, list[str]] = {
    "javascript": [
        "Use Content-Security-Policy headers",
        "Sanitize HTML output with DOMPurify or equivalent",
        "Use 'strict' mode in all modules",
        "Never use innerHTML with user data — use textContent",
        "Validate all URL parameters and query strings",
    ],
    "typescript": [
        "Enable strict TypeScript compiler options",
        "Use Content-Security-Policy headers",
        "Sanitize HTML output — never trust user input in templates",
        "Use Zod or similar for runtime input validation",
        "Type-check all API boundaries",
    ],
    "python": [
        "Never use eval(), exec(), or __import__() with user input",
        "Use parameterized queries with SQLAlchemy or psycopg2",
        "Validate inputs with Pydantic models",
        "Use secrets module for token generation, not random",
        "Set secure cookie flags (HttpOnly, Secure, SameSite)",
    ],
    "java": [
        "Use PreparedStatement for all database queries",
        "Enable CSRF protection in Spring Security",
        "Use BCrypt for password hashing",
        "Validate inputs with Bean Validation (JSR 380)",
        "Never deserialize untrusted data",
    ],
    "go": [
        "Use database/sql with parameterized queries",
        "Validate all inputs at API boundaries",
        "Use crypto/rand for secure random generation",
        "Set proper CORS headers",
        "Never use fmt.Sprintf for SQL queries",
    ],
    "rust": [
        "Use sqlx or diesel with parameterized queries",
        "Validate inputs at deserialization boundaries",
        "Use ring or rustls for cryptographic operations",
        "Never use unsafe blocks for user data handling",
        "Enable all clippy security lints",
    ],
    "dart": [
        "Validate all inputs from user forms",
        "Use secure storage for sensitive data on device",
        "Implement certificate pinning for API calls",
        "Never store tokens in SharedPreferences without encryption",
        "Use Flutter's built-in XSS protections",
    ],
    "php": [
        "Use PDO with prepared statements for all queries",
        "Enable CSRF token validation on all forms",
        "Use password_hash() with PASSWORD_ARGON2ID",
        "Set Content-Security-Policy headers",
        "Never use extract() on user input arrays",
    ],
}


def sanitize_generated_prompt(prompt: str) -> tuple[str, list[str]]:
    """
    Scan a generated prompt for dangerous patterns and sanitize.
    Returns (sanitized_prompt, list_of_issues_found).

    This is the LAST LINE OF DEFENSE before a prompt reaches the user.
    """
    issues: list[str] = []

    for rule_name, pattern in _DANGEROUS_PROMPT_PATTERNS:
        match = pattern.search(prompt)
        if match:
            issues.append(f"[{rule_name}] Removed: '{match.group()[:60]}'")
            prompt = pattern.sub("[REDACTED]", prompt)

    return prompt, issues


def get_language_security_rules(language_hint: str) -> list[str]:
    """Get security rules specific to the detected programming language."""
    if not language_hint:
        return []

    lang_lower = language_hint.lower()
    for lang_key, rules in _LANG_SECURITY.items():
        if lang_key in lang_lower:
            return rules

    # Check common framework → language mappings
    _FRAMEWORK_LANGS = {
        "next.js": "typescript", "react": "javascript", "vue": "javascript",
        "angular": "typescript", "svelte": "javascript", "nuxt": "typescript",
        "django": "python", "flask": "python", "fastapi": "python",
        "spring": "java", "gin": "go", "echo": "go", "fiber": "go",
        "actix": "rust", "axum": "rust", "flutter": "dart",
        "laravel": "php", "symfony": "php",
    }
    for fw, lang in _FRAMEWORK_LANGS.items():
        if fw in lang_lower:
            return _LANG_SECURITY.get(lang, [])

    return []


# ══════════════════════════════════════════════════════════════════════
# 4. PROMPT QUALITY SCORER
# ══════════════════════════════════════════════════════════════════════

@dataclass
class QualityScore:
    """Quantified quality assessment of a generated prompt."""
    total_score: float  # 0-100
    role_score: float
    task_clarity_score: float
    structure_score: float
    security_score: float
    actionability_score: float
    breakdown: dict[str, str] = field(default_factory=dict)

    @property
    def grade(self) -> str:
        if self.total_score >= 90:
            return "A+"
        elif self.total_score >= 80:
            return "A"
        elif self.total_score >= 70:
            return "B"
        elif self.total_score >= 60:
            return "C"
        else:
            return "D"


def score_prompt_quality(prompt: str) -> QualityScore:
    """
    Score a generated prompt on multiple quality dimensions.
    Used internally to decide if fallback is needed and for /quality endpoint.
    """
    low = prompt.lower()

    # 1. Role Definition (0-20)
    role_score = 0.0
    role_indicators = [
        ("act as", 5), ("you are", 5), ("expert", 4), ("specialist", 4),
        ("senior", 3), ("experience", 3), ("years", 2),
    ]
    for indicator, points in role_indicators:
        if indicator in low:
            role_score = min(20.0, role_score + points)

    # 2. Task Clarity (0-20)
    task_score = 0.0
    task_indicators = [
        ("your task", 6), ("objective", 5), ("goal", 4), ("you will", 5),
        ("requirements", 4), ("deliverables", 4),
    ]
    for indicator, points in task_indicators:
        if indicator in low:
            task_score = min(20.0, task_score + points)

    # 3. Structure (0-20)
    structure_score = 0.0
    # Count headers/sections
    headers = len(re.findall(r"^#{1,3}\s", prompt, re.M))
    structure_score += min(10.0, headers * 2.5)
    # Count numbered/bulleted lists
    lists = len(re.findall(r"^\s*[-*\d]+[.)]\s", prompt, re.M))
    structure_score += min(10.0, lists * 1.0)
    structure_score = min(20.0, structure_score)

    # 4. Security (0-20)
    security_score = 0.0
    security_keywords = [
        "security", "sanitize", "validate", "injection", "xss",
        "authentication", "authorization", "owasp", "parameterized",
        "credentials", "secrets", "encrypt", "csrf",
    ]
    found_security = sum(1 for kw in security_keywords if kw in low)
    security_score = min(20.0, found_security * 4.0)

    # 5. Actionability (0-20)
    action_score = 0.0
    action_verbs = [
        "implement", "create", "build", "design", "analyze", "review",
        "test", "optimize", "refactor", "deploy", "configure", "integrate",
    ]
    found_actions = sum(1 for v in action_verbs if v in low)
    action_score += min(10.0, found_actions * 2.0)
    # Numbered steps
    numbered = len(re.findall(r"^\s*\d+\.\s", prompt, re.M))
    action_score += min(10.0, numbered * 2.0)
    action_score = min(20.0, action_score)

    total = role_score + task_score + structure_score + security_score + action_score

    return QualityScore(
        total_score=total,
        role_score=role_score,
        task_clarity_score=task_score,
        structure_score=structure_score,
        security_score=security_score,
        actionability_score=action_score,
        breakdown={
            "role": f"{role_score}/20",
            "task_clarity": f"{task_score}/20",
            "structure": f"{structure_score}/20",
            "security": f"{security_score}/20",
            "actionability": f"{action_score}/20",
        },
    )


# ══════════════════════════════════════════════════════════════════════
# 5. MASTER PROMPT BUILDER (AI-Specific)
# ══════════════════════════════════════════════════════════════════════

def build_optimized_prompt(
    vibe: str,
    family: str,
    *,
    tech_stack: str = "",
    language_hint: str = "",
    project_context: str = "",
    pattern_context: str = "",
    extra_rules: str = "",
) -> str:
    """
    Build a world-class prompt optimized for the target AI family.

    Combines:
    - AI-specific formatting (XML for Claude, Markdown for GPT, etc.)
    - Community patterns from prompts.chat knowledge base
    - Security constraints per language and AI
    - Prompt engineering best practices (CoT, constraints, etc.)

    Returns the complete, ready-to-use prompt string.
    """
    profile = AI_PROFILES.get(family, AI_PROFILES["auto"])

    # Build components
    role = _build_role(vibe, tech_stack)
    expertise = _build_expertise(vibe, tech_stack, language_hint)
    objective = _build_objective(vibe)
    requirements = _build_requirements(vibe, pattern_context)
    constraints_text = _build_constraints(vibe, tech_stack)
    deliverables = _build_deliverables(vibe)
    quality_gates = _build_quality_gates(language_hint)
    output_format = _build_output_format(vibe)
    security_rules = _build_security_section(profile, language_hint)

    # Fill the AI-specific template
    prompt = profile.structure_template.format(
        role=role,
        expertise=expertise,
        project_type=_detect_project_type(vibe),
        tech_stack=tech_stack or "Not specified",
        constraints=constraints_text,
        objective=objective,
        requirements=requirements,
        deliverables=deliverables,
        quality_gates=quality_gates,
        output_format=output_format,
    )

    # Inject language-specific security rules
    if security_rules:
        prompt += f"\n\n## Language-Specific Security\n{security_rules}"

    # Inject extra rules (e.g. from language security resolver)
    if extra_rules:
        prompt += f"\n\n## Additional Security Rules\n{extra_rules}"

    # Inject project context if available
    if project_context:
        if profile.uses_xml_tags:
            prompt += f"\n\n<project_context>\n{project_context}\n</project_context>"
        else:
            prompt += f"\n\n## Project Context\n{project_context}"

    # Final sanitization
    prompt, issues = sanitize_generated_prompt(prompt)
    if issues:
        import logging
        log = logging.getLogger("brain.optimizer")
        for issue in issues:
            log.warning("Sanitized: %s", issue)

    return prompt


# ── Component Builders ───────────────────────────────────────────────

def _build_role(vibe: str, tech_stack: str) -> str:
    """Generate a deep, specific role definition."""
    vibe_l = vibe.lower()

    if any(w in vibe_l for w in ["review", "audit", "analyze"]):
        return "Senior Software Architect and Code Auditor"
    elif any(w in vibe_l for w in ["test", "testing", "coverage"]):
        return "Senior Test Engineer and Quality Specialist"
    elif any(w in vibe_l for w in ["security", "pentest", "vulnerability"]):
        return "Application Security Engineer and Penetration Tester"
    elif any(w in vibe_l for w in ["api", "backend", "server", "endpoint"]):
        return "Senior Backend Engineer specializing in API design"
    elif any(w in vibe_l for w in ["frontend", "ui", "ux", "component", "react", "vue"]):
        return "Senior Frontend Engineer and UI Architect"
    elif any(w in vibe_l for w in ["mobile", "ios", "android", "flutter", "react native"]):
        return "Senior Mobile Application Developer"
    elif any(w in vibe_l for w in ["devops", "deploy", "ci/cd", "docker", "kubernetes"]):
        return "Senior DevOps Engineer and Infrastructure Specialist"
    elif any(w in vibe_l for w in ["data", "ml", "machine learning", "ai"]):
        return "Senior Data Engineer and ML Specialist"
    elif any(w in vibe_l for w in ["architect", "design", "system"]):
        return "Principal Software Architect"
    else:
        return "Senior Full-Stack Software Engineer"


def _build_expertise(vibe: str, tech_stack: str, language_hint: str) -> str:
    """Generate expertise description."""
    parts = ["10+ years of production experience"]
    if tech_stack:
        parts.append(f"deep expertise in {tech_stack}")
    if language_hint:
        parts.append(f"specializing in {language_hint}")
    parts.append("strong focus on security, performance, and maintainability")
    return ". ".join(parts) + "."


def _build_objective(vibe: str) -> str:
    """Transform vibe into a clear objective."""
    return vibe.strip()


def _build_requirements(vibe: str, pattern_context: str) -> str:
    """Build requirements from vibe + matched patterns."""
    reqs = [
        "- Follow clean code principles and industry best practices",
        "- Include comprehensive error handling and input validation",
        "- Write self-documenting code with clear naming conventions",
        "- Implement proper logging for debugging and monitoring",
    ]
    if pattern_context:
        reqs.append(f"- {pattern_context}")
    return "\n".join(reqs)


def _build_constraints(vibe: str, tech_stack: str) -> str:
    """Build constraints section."""
    constraints = [
        "No placeholder or TODO code — everything must be fully functional",
        "No hardcoded credentials or configuration values",
        "No unnecessary dependencies — minimize attack surface",
        "No deprecated APIs or patterns",
    ]
    return "\n".join(f"- {c}" for c in constraints)


def _build_deliverables(vibe: str) -> str:
    """Build deliverables list."""
    deliverables = [
        "Complete, production-ready source code",
        "All necessary configuration files",
        "Clear inline documentation and comments",
    ]
    vibe_l = vibe.lower()
    if any(w in vibe_l for w in ["test", "testing"]):
        deliverables.append("Comprehensive test suite")
    if any(w in vibe_l for w in ["api", "endpoint"]):
        deliverables.append("API documentation with request/response examples")
    if any(w in vibe_l for w in ["deploy", "docker"]):
        deliverables.append("Deployment configuration (Dockerfile / docker-compose)")
    return "\n".join(f"- {d}" for d in deliverables)


def _build_quality_gates(language_hint: str) -> str:
    """Build quality gates."""
    gates = [
        "- Code passes linting with zero warnings",
        "- All edge cases handled with appropriate error responses",
        "- No known security vulnerabilities (OWASP Top 10 compliance)",
        "- Performance-optimized with no unnecessary computations",
        "- Follows single responsibility and separation of concerns",
    ]
    return "\n".join(gates)


def _build_output_format(vibe: str) -> str:
    """Build output format instructions."""
    return (
        "Provide complete file contents with file paths.\n"
        "Each file in its own clearly labeled code block.\n"
        "Start with a brief architectural summary (2-3 sentences).\n"
        "End with usage instructions."
    )


def _build_security_section(profile: AIProfile, language_hint: str) -> str:
    """Build language-specific security section."""
    rules = get_language_security_rules(language_hint)
    if not rules:
        return ""
    return "\n".join(f"- {r}" for r in rules)


def _detect_project_type(vibe: str) -> str:
    """Detect project type from vibe."""
    vibe_l = vibe.lower()
    mappings = [
        (["web app", "website", "frontend"], "Web Application"),
        (["api", "rest", "graphql", "backend"], "API / Backend Service"),
        (["mobile", "ios", "android", "flutter"], "Mobile Application"),
        (["cli", "command line", "terminal"], "CLI Tool"),
        (["library", "package", "module", "npm"], "Library / Package"),
        (["microservice", "service"], "Microservice"),
        (["bot", "discord", "telegram", "slack"], "Chat Bot"),
        (["game", "engine"], "Game / Interactive"),
        (["extension", "plugin", "addon"], "Extension / Plugin"),
        (["data", "etl", "pipeline"], "Data Pipeline"),
    ]
    for keywords, project_type in mappings:
        if any(kw in vibe_l for kw in keywords):
            return project_type
    return "Software Project"


# ══════════════════════════════════════════════════════════════════════
# 6. PROMPT FINGERPRINTING (anti-replay, traceability)
# ══════════════════════════════════════════════════════════════════════

def fingerprint_prompt(prompt: str) -> str:
    """Generate a short hash fingerprint for prompt traceability."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:12]
