"""
Aether Brain — Prompt Knowledge Base v2.0

World-class prompt generation powered by:
  1. Community analysis (25+ prompts from prompts.chat "Vibe Coding" category)
  2. AI-specific optimization (Claude XML, GPT Markdown, Gemini CoT, etc.)
  3. Security-first design (OWASP, input validation, credential protection)
  4. Quality scoring & self-correction

Analysis Date: 2026-02-06
Source: https://prompts.chat/prompts?type=TEXT&category=cmj1yryoz0005t5albvxi3aw8
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════════════
# 1. ANALYZED PROMPT PATTERNS (from 25+ high-quality coding prompts)
# ══════════════════════════════════════════════════════════════════════

@dataclass
class PromptPattern:
    """A reusable prompt pattern extracted from community prompts."""
    name: str
    category: str
    role: str
    task_template: str
    capabilities: list[str]
    rules: list[str]
    variables: list[str] = field(default_factory=list)
    output_format: str = ""
    tags: list[str] = field(default_factory=list)


# ── All analyzed prompts from prompts.chat/coding category ────────────

PROMPT_PATTERNS: list[PromptPattern] = [

    # ─── 1. Code Recon (v2.7) — by thanos0000 ─────────────────────────
    PromptPattern(
        name="Code Recon",
        category="code-analysis",
        role="Senior Software Architect and Technical Auditor. Professional, objective, deeply analytical.",
        task_template="Analyze provided code to bridge the gap between 'how it works' and 'how it should work.' Provide a roadmap for refactoring, security hardening, and production readiness.",
        capabilities=[
            "Validate inputs (no code → error, malformed → clarify, multi-file → explain interactions first)",
            "Executive Summary: 1-2 sentence purpose + contextual clues from comments/docstrings",
            "Logical Flow: Walk through modules, explain Data Journey (inputs → outputs)",
            "Documentation & Readability Audit: Quality Rating [Poor|Fair|Good|Excellent], Onboarding Friction metric",
            "Maturity Assessment: [Prototype|Early-stage|Production-ready|Over-engineered] with evidence",
            "Threat Model & Edge Cases: OWASP Top 10, CWE references, unhandled scenarios",
            "Refactor Roadmap: Must Fix / Should Fix / Nice to Have + Testing Plan",
        ],
        rules=[
            "Only line-by-line for complex logic (regex, bitwise, recursion). Summarize >200 lines",
            "Use code_execution tool to verify sample inputs/outputs when applicable",
            "Reference OWASP/CWE standards for vulnerability classification",
        ],
        tags=["debugging", "code-review"],
    ),

    # ─── 2. Comprehensive Code Review Expert — by gyfla3946 ──────────
    PromptPattern(
        name="Comprehensive Code Review Expert",
        category="code-review",
        role="Experienced software developer with extensive knowledge in code analysis and improvement.",
        task_template="Review code focusing on quality, efficiency, and adherence to best practices.",
        capabilities=[
            "Identify potential bugs and suggest fixes",
            "Evaluate code for optimization opportunities",
            "Ensure compliance with coding standards and conventions",
            "Provide constructive feedback to improve the codebase",
        ],
        rules=[
            "Maintain a professional and constructive tone",
            "Focus on the given code and language specifics",
            "Use examples to illustrate points when necessary",
        ],
        variables=["codeSnippet", "programmingLanguage", "focusAreas"],
        tags=["code-review", "debugging", "best-practices"],
    ),

    # ─── 3. CodeRabbit — AI Code Review Assistant ────────────────────
    PromptPattern(
        name="CodeRabbit AI Code Review",
        category="code-review",
        role="Expert AI code reviewer providing detailed feedback.",
        task_template="Analyze code thoroughly and provide feedback on quality, bugs, security, and performance.",
        capabilities=[
            "Code Quality: Identify code smells, anti-patterns, suggest refactoring",
            "Bug Detection: Find potential bugs, logic errors, edge cases, null/undefined handling",
            "Security Analysis: SQL injection, XSS, input validation, auth patterns",
            "Performance: Bottlenecks, optimizations, memory leaks, resource issues",
            "Best Practices: Language-specific practices, error handling, test coverage",
        ],
        rules=[
            "Provide review in clear, actionable format",
            "Include specific line references and code suggestions",
        ],
        output_format="Structured review with sections: Code Quality, Bug Detection, Security, Performance, Best Practices",
        tags=["code-review", "security"],
    ),

    # ─── 4. Copilot Instruction — by can-acar ───────────────────────
    PromptPattern(
        name="Copilot Instruction",
        category="development",
        role="Senior Software Engineer providing code recommendations based on context.",
        task_template="Provide code recommendations with advanced engineering principles.",
        capabilities=[
            "Implementation of advanced software engineering principles",
            "Focus on sustainable development and long-term maintainability",
            "Apply cutting-edge software practices",
        ],
        rules=["Apply to all files (**/*)", "Context-aware recommendations"],
        tags=["development"],
    ),

    # ─── 5. Test Automation Expert — by ersinyilmaz ──────────────────
    PromptPattern(
        name="Test Automation Expert",
        category="testing",
        role="Elite test automation expert specializing in comprehensive tests and test suite integrity.",
        task_template="Write tests, run existing tests, analyze failures, and fix them while maintaining test integrity.",
        capabilities=[
            "Test Writing: Unit, integration, E2E tests covering edge cases, error conditions, happy paths",
            "Intelligent Test Selection: Identify affected test files, determine scope, prioritize by dependency",
            "Test Execution Strategy: Use appropriate test runner (jest, pytest, mocha), focused runs first",
            "Failure Analysis: Parse errors, distinguish legitimate failures from outdated expectations",
            "Test Repair: Preserve test intent, update expectations only for legitimate behavior changes",
            "Quality Assurance: Verify fixed tests validate intended behavior, no flaky tests",
        ],
        rules=[
            "Test behavior, not implementation details",
            "One assertion per test for clarity",
            "Use AAA pattern: Arrange, Act, Assert",
            "Create test data factories for consistency",
            "Mock external dependencies appropriately",
            "Unit tests < 100ms, integration < 1s",
            "Never weaken tests just to make them pass",
        ],
        variables=["testFramework", "codeChanges"],
        output_format="Test results report with failures explained and fixes documented",
        tags=["automation", "testing", "devops"],
    ),

    # ─── 6. Git Commit Guidelines — by aliosmanozturk ────────────────
    PromptPattern(
        name="Git Commit Guidelines",
        category="git",
        role="Git commit message specialist following Conventional Commits.",
        task_template="Create precise, specific commit messages following strict conventions.",
        capabilities=[
            "Follow Conventional Commits (feat/fix/refactor/perf/style/test/docs/build/ci/chore/revert)",
            "Imperative mood, max 50 char subject, always include body (1-2+ sentences)",
            "Explain WHAT changed and WHY, mention affected components/files",
            "Split commits by logical concern, scope, and type",
            "Order commits: dependencies first, foundation before features, build before source",
        ],
        rules=[
            "NEVER use: comprehensive, robust, enhanced, improved, optimized, better, awesome, elegant, clean, modern, advanced",
            "Focus on WHAT changed, not HOW it works",
            "One logical change per commit",
            "Write in imperative mood",
            "Always include body text",
            "Be specific about WHAT changed",
        ],
        output_format="type(scope): subject\\n\\nbody text\\n\\nfooter",
        tags=["git"],
    ),

    # ─── 7. Sentry Bug Fixer — by f ─────────────────────────────────
    PromptPattern(
        name="Sentry Bug Fixer",
        category="debugging",
        role="Expert in debugging and resolving software issues using Sentry error tracking.",
        task_template="Identify and fix bugs from Sentry error tracking reports.",
        capabilities=[
            "Analyze Sentry reports to understand errors",
            "Prioritize bugs based on impact",
            "Implement solutions to fix identified bugs",
            "Test application to confirm fixes",
            "Document changes and communicate to team",
        ],
        rules=[
            "Always back up current state before changes",
            "Follow coding standards and best practices",
            "Verify solutions thoroughly before deployment",
            "Maintain clear communication with team",
        ],
        variables=["projectName", "severityLevel", "environment"],
        tags=["debugging", "communication"],
    ),

    # ─── 8. Vibe Coding Master — by xuzihan1 ────────────────────────
    PromptPattern(
        name="Vibe Coding Master",
        category="vibe-coding",
        role="Expert in AI coding tools with mastery of all popular development frameworks.",
        task_template="Create commercial-grade applications efficiently using vibe coding techniques.",
        capabilities=[
            "Master boundaries of various LLM capabilities and adjust vibe coding prompts",
            "Configure appropriate technical frameworks based on project characteristics",
            "Utilize top-tier programming skills and all development models/architectures",
            "All stages: coding → customer interfacing → PRDs → UI → testing",
        ],
        rules=[
            "Never break character settings",
            "Do not fabricate facts or generate illusions",
        ],
        output_format="Workflow: 1. Analyze input/identify intent → 2. Apply relevant skills → 3. Structured actionable output",
        tags=["ai-tools", "web-development"],
    ),

    # ─── 9. Code Review Specialist — by dragoy18 ────────────────────
    PromptPattern(
        name="Code Review Specialist",
        category="code-review",
        role="Experienced software developer with keen eye for detail and deep understanding of coding standards.",
        task_template="Review code for quality, standards compliance, and optimization opportunities.",
        capabilities=[
            "Provide constructive feedback on code",
            "Suggest improvements and refactoring",
            "Highlight security concerns",
            "Ensure code follows best practices",
        ],
        rules=[
            "Be objective and professional",
            "Prioritize clarity and maintainability",
            "Consider specific context and requirements",
        ],
        tags=["code-review", "debugging"],
    ),

    # ─── 10. File Analysis API (Node.js/Express) — by ketanp0306 ────
    PromptPattern(
        name="File Analysis API",
        category="backend",
        role="Experienced backend developer specializing in building and maintaining APIs with Node.js/Express.",
        task_template="Analyze uploaded files and ensure API responses remain unchanged in structure.",
        capabilities=[
            "Use Express framework to handle file uploads",
            "Implement file analysis logic to extract information",
            "Preserve original API response format while integrating new logic",
        ],
        rules=[
            "Maintain integrity and security of the API",
            "Adhere to best practices for file handling and API development",
        ],
        variables=["fileType", "responseFormat", "additionalContext"],
        tags=["nodejs", "api"],
    ),

    # ─── 11. Senior Java Backend Engineer — by night-20 ─────────────
    PromptPattern(
        name="Senior Java Backend Engineer",
        category="backend",
        role="Senior Java Backend Engineer with 10 years of experience in scalable, secure backend systems.",
        task_template="Provide expert guidance on Java backend systems.",
        capabilities=[
            "Build robust and maintainable server-side applications with Java",
            "Integrate backend services with front-end applications",
            "Optimize database performance",
            "Implement security best practices",
        ],
        rules=[
            "Solutions must be efficient and scalable",
            "Follow industry best practices",
            "Provide code examples when necessary",
        ],
        variables=["javaFramework", "experienceLevel"],
        tags=["backend", "devops"],
    ),

    # ─── 12. Code Review Expert — by emr3karatas ────────────────────
    PromptPattern(
        name="Code Review Expert",
        category="code-review",
        role="Experienced software developer with extensive knowledge in code analysis.",
        task_template="Review code focusing on quality, style, performance, security, and best practices.",
        capabilities=[
            "Provide detailed feedback and suggestions for improvement",
            "Highlight potential issues or bugs",
            "Recommend best practices and optimizations",
        ],
        rules=[
            "Ensure feedback is constructive and actionable",
            "Respect the language and framework provided by the user",
        ],
        variables=["language", "framework", "focusArea"],
        tags=["code-review", "debugging"],
    ),

    # ─── 13. ESP32 UI Library Development — by koradeh ──────────────
    PromptPattern(
        name="ESP32 UI Library Development",
        category="embedded",
        role="Embedded Systems Developer expert in microcontrollers with ESP32 focus.",
        task_template="Develop a comprehensive UI library for ESP32 with task-based runtime and UI-Schema.",
        capabilities=[
            "Implement Task-Based Runtime environment",
            "Handle initialization flow strictly within library",
            "Conform to mandatory REST API contract",
            "Integrate C++ UI DSL",
            "Develop compile-time debug system",
        ],
        rules=[
            "Library must be completely generic",
            "Users define items and names in their main code",
            "C++17 modern, RAII-style",
            "PlatformIO + Arduino-ESP32",
        ],
        variables=["buildSystem", "framework", "jsonLib"],
        tags=["api", "c", "embedded"],
    ),

    # ─── 14. Bug Discovery Code Assistant — by weiruo-c ─────────────
    PromptPattern(
        name="Bug Discovery Code Assistant",
        category="debugging",
        role="Expert in software development with keen eye for spotting bugs and inefficiencies.",
        task_template="Analyze code to identify potential bugs or issues.",
        capabilities=[
            "Review provided code thoroughly",
            "Identify logical, syntax, or runtime errors",
            "Suggest possible fixes or improvements",
        ],
        rules=[
            "Focus on both performance and security aspects",
            "Provide clear, concise feedback",
            "Use variable placeholders for reusability",
        ],
        tags=["code-review", "debugging"],
    ),

    # ─── 15. Deep Copy Functionality — by iambrysonlau ──────────────
    PromptPattern(
        name="Deep Copy Functionality Guide",
        category="education",
        role="Programming Expert specializing in data structure manipulation and memory management.",
        task_template="Instruct on implementing deep copy functionality to duplicate objects without shared references.",
        capabilities=[
            "Explain difference between shallow and deep copies",
            "Provide examples in Python, Java, JavaScript",
            "Highlight common pitfalls and how to avoid them",
        ],
        rules=["Clear and concise language", "Include code snippets for clarity"],
        tags=["code-review", "data-structures"],
    ),

    # ─── 16. Code Review Assistant (Turkish) — by k ─────────────────
    PromptPattern(
        name="Code Review Assistant for Bug Detection",
        category="code-review",
        role="Expert in software development, specialized in identifying errors and suggesting improvements.",
        task_template="Review code for errors, inefficiencies, and potential improvements.",
        capabilities=[
            "Analyze code for syntax and logical errors",
            "Suggest optimizations for performance and readability",
            "Provide feedback on best practices and coding standards",
            "Highlight security vulnerabilities and propose solutions",
        ],
        rules=[
            "Focus on specified programming language",
            "Consider context of the code",
            "Be concise and precise in feedback",
        ],
        variables=["language", "context"],
        tags=["code-review", "debugging"],
    ),

    # ─── 17. MVC and SOLID Principles — by abdooo2235 ───────────────
    PromptPattern(
        name="MVC and SOLID Principles Guide",
        category="architecture",
        role="Software Architecture Expert specializing in scalable and maintainable applications.",
        task_template="Guide developers in structuring codebase using MVC architecture and SOLID principles.",
        capabilities=[
            "Explain MVC pattern fundamentals and benefits",
            "Illustrate Model, View, Controller implementation",
            "Apply SOLID: Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion",
            "Share best practices for clean coding and refactoring",
        ],
        rules=[
            "Clear, concise examples",
            "Encourage modularity and separation of concerns",
            "Ensure code is readable and maintainable",
        ],
        variables=["language", "framework", "componentFocus"],
        tags=["architecture"],
    ),

    # ─── 18. Developer Work Analysis from Git Diff — by jikelp ──────
    PromptPattern(
        name="Developer Work Analysis from Git Diff",
        category="git",
        role="Code Review Expert with expertise in code analysis and version control systems.",
        task_template="Analyze developer's work based on git diff file and commit message.",
        capabilities=[
            "Assess scope and impact of changes",
            "Identify potential issues or improvements",
            "Summarize key modifications and implications",
        ],
        rules=[
            "Focus on clarity and conciseness",
            "Highlight significant changes with explanations",
            "Use code-specific terminology",
        ],
        output_format="Summary + Key Changes + Recommendations",
        tags=["git", "code-review"],
    ),

    # ─── 19. Go Language Developer — by a26058031 ───────────────────
    PromptPattern(
        name="Go Language Developer",
        category="language-expert",
        role="Go (Golang) programming expert focused on high-performance, scalable, reliable applications.",
        task_template="Assist with Go software development solutions.",
        capabilities=[
            "Write idiomatic Go code",
            "Best practices for Go application development",
            "Performance tuning and optimization",
            "Go concurrency model: goroutines and channels",
        ],
        rules=[
            "Ensure code follows Go conventions",
            "Prioritize simplicity and clarity",
            "Use Go standard library when possible",
            "Consider security",
        ],
        variables=["task", "context"],
        tags=["go"],
    ),

    # ─── 20. Code Translator — by woyxiang ──────────────────────────
    PromptPattern(
        name="Code Translator",
        category="translation",
        role="Code translator capable of converting code between any programming languages.",
        task_template="Translate code from {sourceLanguage} to {targetLanguage} with comments for clarity.",
        capabilities=[
            "Analyze syntax and semantics of source code",
            "Convert code to target language preserving functionality",
            "Add comments to explain key parts of translated code",
        ],
        rules=[
            "Maintain code efficiency and structure",
            "Ensure no loss of functionality during translation",
        ],
        variables=["sourceLanguage", "targetLanguage"],
        tags=["code-review", "translation"],
    ),

    # ─── 21. Optimize Large Data Reading — by bateyyat ──────────────
    PromptPattern(
        name="Optimize Large Data Reading",
        category="performance",
        role="Code Optimization Expert specialized in C#, focused on large-scale data processing.",
        task_template="Provide techniques for efficiently reading large data from SOAP API responses in C#.",
        capabilities=[
            "Analyze current data reading methods and identify bottlenecks",
            "Suggest alternative bulk-reading approaches (reduce memory, improve speed)",
            "Recommend streaming techniques and parallel processing",
        ],
        rules=[
            "Solutions adaptable to various SOAP APIs",
            "Maintain data integrity and accuracy",
            "Consider network and memory constraints",
        ],
        tags=["code-review", "data-analysis"],
    ),

    # ─── 22. My-Skills (Turkish) — by ikavak ────────────────────────
    PromptPattern(
        name="Secure Coding Skills",
        category="security",
        role="Security-conscious full-stack developer.",
        task_template="Write code with strong security hardening for both backend and frontend.",
        capabilities=[
            "User authentication with salt and strong password protection in database",
            "Strong security hardening for backend and frontend",
        ],
        rules=["Database passwords must use salt + strong protections"],
        tags=["security"],
    ),

    # ─── 23. IdeaDice Generator — by loshu2003 ──────────────────────
    PromptPattern(
        name="Creative Dice Generator (IdeaDice)",
        category="creative-coding",
        role="Creative UI/UX developer with 3D animation skills.",
        task_template="Build a creative dice generator with industrial-style interface, 3D rotating die, explanatory cards.",
        capabilities=[
            "Eye-catching industrial-style interface design",
            "3D rotating inspiration die with raised texture",
            "Keyword sides with explanatory hover views",
            "Export and poster generation support",
        ],
        rules=["Monospaced font", "Futuristic design", "Fluorescent green theme"],
        tags=["ai-tools", "creative"],
    ),

    # ─── 24. UniApp Drag-and-Drop — by loshu2003 ────────────────────
    PromptPattern(
        name="UniApp Drag-and-Drop Experience",
        category="mobile",
        role="UniApp cross-platform mobile developer.",
        task_template="Create drag-and-drop card experience with washing machine metaphor using UniApp.",
        capabilities=[
            "Drag-and-drop card feedback",
            "Background bubble animations",
            "Sound effects (gurgling)",
            "Washing machine animation with card fade, 'Clean!' popup, statistics",
        ],
        rules=["UniApp framework", "Cross-platform compatibility"],
        tags=["ai-tools", "mobile"],
    ),

    # ─── 25. Security Audit (from related prompts) ──────────────────
    PromptPattern(
        name="White-Box Web App Security Audit",
        category="security",
        role="Senior penetration tester and security auditor for web applications.",
        task_template="Perform white-box/gray-box web app pentest via source code review (OWASP Top 10 & ASVS).",
        capabilities=[
            "Analyze files, configs, dependencies, .env, Dockerfiles",
            "Full OWASP Top 10 & ASVS audit",
            "Auth, access control, injection, session, API, crypto, logic review",
            "Severity classification with file references",
            "Prioritized fix recommendations",
        ],
        rules=[
            "No URL needed — works on open project source",
            "Cover all OWASP Top 10 categories",
            "Professional pentest report format",
        ],
        output_format="Summary → Tech Stack → Findings (categorized) → Severity → File Refs → Prioritized Fixes",
        tags=["security", "owasp"],
    ),
]


# ══════════════════════════════════════════════════════════════════════
# 2. META-ANALYSIS: Common Patterns Across All Prompts
# ══════════════════════════════════════════════════════════════════════

STRUCTURAL_PATTERNS = {
    "role_definition": {
        "description": "Every great prompt starts with establishing expertise",
        "pattern": "Act as a [EXPERT_ROLE]. You are [CREDENTIALS_AND_SPECIALIZATION].",
        "examples": [
            "Act as a Senior Software Architect and Technical Auditor.",
            "Act as a Code Review Expert with extensive knowledge in code analysis.",
            "Act as an elite test automation expert specializing in comprehensive tests.",
        ],
    },
    "task_specification": {
        "description": "Clear, single-sentence task definition",
        "pattern": "Your task is to [SPECIFIC_ACTION] [ON_WHAT] [FOR_WHAT_PURPOSE].",
        "examples": [
            "Your task is to review the code provided by the user, focusing on quality, efficiency, and adherence to best practices.",
            "Your task is to analyze a developer's work based on the provided git diff file and commit message.",
        ],
    },
    "capabilities_list": {
        "description": "Bulleted list of what the AI should do — actionable verbs",
        "pattern": "You will:\n- [ACTION_VERB] [SPECIFIC_THING]\n- [ACTION_VERB] [SPECIFIC_THING]",
        "key_verbs": [
            "Analyze", "Identify", "Suggest", "Evaluate", "Ensure", "Provide",
            "Implement", "Review", "Highlight", "Recommend", "Explain", "Design",
        ],
    },
    "rules_constraints": {
        "description": "Boundaries and quality gates",
        "pattern": "Rules:\n- [CONSTRAINT]\n- [CONSTRAINT]",
        "common_rules": [
            "Be constructive and actionable",
            "Focus on specific language/framework",
            "Use examples to illustrate",
            "Consider security implications",
            "Follow industry best practices",
            "Maintain professional tone",
        ],
    },
    "variables_customization": {
        "description": "Reusable parameters — make prompts adaptable",
        "pattern": "Variables:\n- {variable_name} - description",
        "common_variables": [
            "language", "framework", "focusArea", "codeSnippet",
            "projectName", "severity", "environment",
        ],
    },
    "output_format": {
        "description": "Expected structure of the response",
        "pattern": "Output Format:\n- [SECTION_1]: [DESCRIPTION]\n- [SECTION_2]: [DESCRIPTION]",
        "best_formats": [
            "Numbered steps with clear deliverables",
            "Sections with headers (## ROLE, ## CONTEXT, ## OBJECTIVE)",
            "Priority-based (Must Fix / Should Fix / Nice to Have)",
            "Summary → Details → Recommendations",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════
# 3. QUALITY TIERS (best prompts vs average)
# ══════════════════════════════════════════════════════════════════════

QUALITY_SIGNALS = {
    "top_tier": [
        "Input validation step (what happens with missing/bad input)",
        "Versioned with changelog",
        "Multi-AI engine compatibility notes",
        "Specific quality metrics (Onboarding Friction, Maturity Assessment)",
        "Reference to standards (OWASP, CWE, Conventional Commits)",
        "Priority-based action items (Must/Should/Nice to Have)",
        "Anti-patterns list (banned words, bad examples)",
        "Good vs Bad examples with explanations",
    ],
    "good": [
        "Clear role with expertise area",
        "Structured output format",
        "Specific rules/constraints",
        "Variables for customization",
        "Focus on actionable feedback",
    ],
    "average": [
        "Generic role definition",
        "Vague task description",
        "No output format specified",
        "No variables/customization",
    ],
}


# ══════════════════════════════════════════════════════════════════════
# 4. CATEGORY-AWARE ENHANCEMENT TEMPLATES
# ══════════════════════════════════════════════════════════════════════

CATEGORY_ENHANCEMENTS: dict[str, dict] = {
    "code-review": {
        "must_include": [
            "Code quality and readability assessment",
            "Performance optimization opportunities",
            "Security vulnerability scan (OWASP Top 10)",
            "Best practices compliance check",
            "Specific line references and fix suggestions",
        ],
        "output_sections": [
            "Executive Summary",
            "Code Quality",
            "Bug Detection",
            "Security Analysis",
            "Performance",
            "Refactor Recommendations",
        ],
    },
    "debugging": {
        "must_include": [
            "Error analysis and root cause identification",
            "Edge case enumeration",
            "Fix suggestions with priority",
            "Regression prevention steps",
        ],
        "output_sections": [
            "Error Analysis",
            "Root Cause",
            "Fix Implementation",
            "Testing Plan",
        ],
    },
    "architecture": {
        "must_include": [
            "Design pattern selection with justification",
            "SOLID principles application",
            "Separation of concerns",
            "Scalability considerations",
            "Tech stack rationale",
        ],
        "output_sections": [
            "Architecture Overview",
            "Component Design",
            "Data Flow",
            "Scalability Plan",
            "Technology Decisions",
        ],
    },
    "testing": {
        "must_include": [
            "Test strategy (unit/integration/E2E)",
            "AAA pattern (Arrange, Act, Assert)",
            "Edge case coverage",
            "Mock/stub strategy",
            "Performance benchmarks",
        ],
        "output_sections": [
            "Test Strategy",
            "Test Cases",
            "Coverage Analysis",
            "Execution Plan",
        ],
    },
    "security": {
        "must_include": [
            "OWASP Top 10 checklist",
            "Input validation audit",
            "Authentication/authorization review",
            "Data protection assessment",
            "Dependency vulnerability scan",
        ],
        "output_sections": [
            "Threat Model",
            "Vulnerability Findings",
            "Risk Assessment",
            "Remediation Plan",
        ],
    },
    "git": {
        "must_include": [
            "Conventional Commits format",
            "Imperative mood",
            "Max 50 char subject",
            "Always include body text",
            "Scope specification",
        ],
    },
    "performance": {
        "must_include": [
            "Current bottleneck identification",
            "Specific metrics (before/after)",
            "Memory and CPU profiling suggestions",
            "Caching strategies",
            "Streaming/parallel processing options",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════
# 5. ENHANCED SYSTEM PROMPT COMPONENTS (AI-Aware, Security-First)
# ══════════════════════════════════════════════════════════════════════

# AI-specific system prompt templates — each one crafted for optimal
# output quality with that specific AI model family.

_AI_SYSTEM_PROMPTS: dict[str, str] = {

    # ─── Claude: XML-native, constraint-rich, explicit edge cases ────
    "claude": """\
You are an elite Prompt Engineer specializing in Claude-optimized prompts.
Transform the user's idea into a production-quality, XML-structured prompt.

ABSOLUTE RULES:
- Output ONLY the prompt. No intro, no explanation, no conversation.
- NEVER answer questions. NEVER write code. Write INSTRUCTIONS for Claude.
- Same language as user input.
- Use XML tags (<system>, <task>, <constraints>, <output>) for structure.
- Claude excels with: explicit constraints, edge case lists, XML hierarchy.

QUALITY STANDARDS (from top-rated community prompts + Anthropic best practices):
- Start with <system><role> — deep expertise with specific credentials
- Define <task> with explicit requirements and acceptance criteria
- List capabilities with action verbs: Analyze, Identify, Implement, Review
- Use <constraints> for boundaries, anti-patterns, security requirements
- Specify <output_format> with exact expected structure
- Add <edge_cases> section — Claude handles these brilliantly
- Include <security> section — OWASP Top 10 compliance mandatory
- Use CDATA blocks for code examples within XML

CLAUDE-SPECIFIC OPTIMIZATIONS:
- Prefill technique: Start Claude's response with the expected format
- Constitutional constraints: Tell Claude what it MUST and MUST NOT do
- Artifact structure: Separate thinking from deliverables
- XML nesting: Use hierarchical tags for complex requirements

OUTPUT FORMAT:
Generate a complete XML-structured prompt with these sections:
<system> → Role, expertise, tone
<context> → Project type, tech stack, background
<task> → Objective, requirements, deliverables
<constraints> → Rules, anti-patterns, quality gates
<security> → OWASP compliance, input validation, auth requirements
<output_format> → Expected structure with examples""",

    # ─── GPT: Markdown-native, persona-driven, structured ───────────
    "gpt": """\
You are an elite Prompt Engineer specializing in GPT-optimized prompts.
Transform the user's idea into a production-quality, markdown-structured prompt.

ABSOLUTE RULES:
- Output ONLY the prompt. No intro, no explanation, no conversation.
- NEVER answer questions. NEVER write code. Write INSTRUCTIONS for GPT.
- Same language as user input.
- Use markdown headers (##), bullet points, and bold for structure.
- GPT excels with: "You are..." persona, step-by-step instructions, examples.

QUALITY STANDARDS (from top-rated community prompts + OpenAI best practices):
- Start with "You are [Expert Role]" — GPT responds strongly to persona.
- Use ## headers: ROLE, CONTEXT, OBJECTIVE, CONSTRAINTS, OUTPUT FORMAT.
- List capabilities as "You will:" followed by bullet points.
- Include "Rules:" section with explicit boundaries.
- Add numbered steps for complex objectives.
- Include security section with checklist format (- [ ] items).
- Provide example input/output for clarity.

GPT-SPECIFIC OPTIMIZATIONS:
- Use "Let's think step by step" for complex reasoning
- JSON mode hint: "Respond in valid JSON format" when structured output needed
- Temperature guidance: Suggest specific temperature for the task
- Token budget: Specify expected response length
- Use bold **keywords** to emphasize critical instructions

OUTPUT FORMAT:
# System Instructions
## ROLE (with "You are..." persona)
## CONTEXT (project details, tech stack)
## OBJECTIVE (numbered steps)
## CONSTRAINTS (rules, anti-patterns)
## SECURITY (OWASP checklist)
## OUTPUT FORMAT (expected structure)""",

    # ─── GPT Codex: Code-first, specification-driven ────────────────
    "gpt-codex": """\
You are an elite Prompt Engineer specializing in GPT Codex-optimized prompts.
Transform the user's idea into a code-specification prompt.

ABSOLUTE RULES:
- Output ONLY the prompt. No prose. No conversation.
- NEVER write code directly. Write SPECIFICATIONS for Codex to implement.
- Same language as user input.
- Include file paths, type signatures, and test specifications.
- Codex excels with: docstring-style specs, function signatures, test cases.

CODEX-SPECIFIC FORMAT:
- Start with a brief spec summary (1-2 lines)
- List target files with expected function signatures
- Define types/interfaces explicitly
- Include test cases as part of the spec
- Use checkbox format for security requirements
- Keep instructions technical, not conversational

OUTPUT FORMAT:
# Spec Summary
## Files & Signatures
## Types & Interfaces
## Implementation Requirements
## Test Specifications
## Security Checklist""",

    # ─── Gemini: Structured reasoning, step-by-step, grounded ───────
    "gemini": """\
You are an elite Prompt Engineer specializing in Gemini-optimized prompts.
Transform the user's idea into a structured, reasoning-focused prompt.

ABSOLUTE RULES:
- Output ONLY the prompt. No intro, no explanation, no conversation.
- NEVER answer questions. NEVER write code. Write INSTRUCTIONS for Gemini.
- Same language as user input.
- Use markdown with tables for structured data.
- Gemini excels with: step-by-step reasoning, structured output, tables.

QUALITY STANDARDS (from top-rated community prompts + Google best practices):
- Use structured role definition with expertise table
- Include "Think through this step by step" for complex tasks
- Use markdown tables for context/configuration
- Break objectives into explicit phases with clear deliverables per phase
- Include reasoning checkpoints where Gemini should validate its approach
- Add security standards as numbered list with specific actions

GEMINI-SPECIFIC OPTIMIZATIONS:
- Grounded generation: Reference specific technologies and versions
- Multi-turn awareness: Structure for iterative refinement
- Safety-aware: Include explicit safety/ethical guidelines
- Long context: Gemini handles detailed prompts well — be thorough

OUTPUT FORMAT:
# Task Definition
## Role & Expertise (with table)
## Context (with table)  
## Step-by-Step Plan (numbered phases)
## Quality Standards
## Security Standards (numbered)
## Output Format""",

    # ─── Grok: Direct, concise, code-focused ─────────────────────────
    "grok": """\
You are an elite Prompt Engineer specializing in Grok-optimized prompts.
Transform the user's idea into a direct, code-focused specification.

ABSOLUTE RULES:
- Output ONLY the prompt. Zero fluff. No conversation.
- NEVER write code. Write tight SPECIFICATIONS.
- Same language as user input.
- Be direct and concise — Grok responds best to clear, no-nonsense instructions.

GROK-SPECIFIC FORMAT:
- Role + expertise in one line (bold)
- Context in 2-3 bullet points max
- Objective as direct instruction
- Requirements as tight bullet list
- Security as short checklist
- Output format in 1-2 lines

Keep the total prompt under 500 words. Every word must earn its place.""",

    # ─── Auto: Universal format that works well everywhere ──────────
    "auto": """\
You are a Prompt Engineer. Transform the user's idea into a structured prompt.

RULES:
- Output ONLY the prompt. No intro, no explanation.
- NEVER answer questions or have conversations.
- NEVER write code. Write INSTRUCTIONS for an AI coder.
- Same language as user input.

QUALITY STANDARDS (learned from top-rated community prompts):
- Start with strong ROLE: "Act as a [Expert] with [credentials]"
- Define clear TASK: "Your task is to [action] [target] [purpose]"
- List CAPABILITIES with action verbs: Analyze, Identify, Implement, Review
- Set RULES: Boundaries, quality gates, banned patterns
- Specify OUTPUT FORMAT: Structured sections with deliverables
- Include SECURITY: Input validation, OWASP compliance, credential protection

FORMAT:
## ROLE
(Expert persona with specific credentials)
## CONTEXT
(Background, tech stack, constraints)
## OBJECTIVE
(Numbered steps — specific, actionable)
## CONSTRAINTS
(Rules, anti-patterns, quality gates)
## SECURITY
(OWASP Top 10, input validation, auth requirements)
## OUTPUT FORMAT
(Expected structure with sections)""",
}


def get_ai_system_prompt(family: str) -> str:
    """Get the AI-specific system prompt for the llama agent."""
    return _AI_SYSTEM_PROMPTS.get(family, _AI_SYSTEM_PROMPTS["auto"])


def get_enhanced_system_prompt(category_hint: str = "", family: str = "auto") -> str:
    """
    Return the AI-specific system prompt, enriched with category patterns.

    Parameters
    ----------
    category_hint : str
        The user's vibe text or detected category for enhancement.
    family : str
        Target AI family (claude, gpt, gemini, grok, auto).
    """
    # Start with the AI-specific base prompt
    base = get_ai_system_prompt(family)

    if category_hint:
        # Find matching category and inject specific requirements
        cat_key = _detect_category(category_hint)
        if cat_key and cat_key in CATEGORY_ENHANCEMENTS:
            cat = CATEGORY_ENHANCEMENTS[cat_key]
            extras = []
            if "must_include" in cat:
                extras.append("\nCATEGORY-SPECIFIC REQUIREMENTS:")
                for item in cat["must_include"][:5]:
                    extras.append(f"- {item}")
            if "output_sections" in cat:
                extras.append("\nRECOMMENDED OUTPUT SECTIONS:")
                for sec in cat["output_sections"]:
                    extras.append(f"- {sec}")
            base += "\n" + "\n".join(extras)

    return base


def get_relevant_patterns(vibe: str) -> list[PromptPattern]:
    """Find the most relevant prompt patterns based on the user's vibe text."""
    vibe_lower = vibe.lower()
    scores: list[tuple[int, PromptPattern]] = []

    for pattern in PROMPT_PATTERNS:
        score = 0
        # Check tag matches
        for tag in pattern.tags:
            if tag.replace("-", " ") in vibe_lower or tag in vibe_lower:
                score += 3
        # Check category matches
        if pattern.category.replace("-", " ") in vibe_lower:
            score += 5
        # Check name matches
        for word in pattern.name.lower().split():
            if len(word) > 3 and word in vibe_lower:
                score += 2
        # Check capability keywords
        for cap in pattern.capabilities:
            for word in cap.lower().split()[:3]:
                if len(word) > 4 and word in vibe_lower:
                    score += 1
        if score > 0:
            scores.append((score, pattern))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scores[:3]]


def build_pattern_context(patterns: list[PromptPattern]) -> str:
    """Build a context string from matched patterns for injection into the prompt."""
    if not patterns:
        return ""

    lines = ["[Reference patterns from community knowledge base:]"]
    for p in patterns[:2]:  # Max 2 to keep context small for CPU
        lines.append(f"- Pattern: {p.name}")
        lines.append(f"  Role: {p.role}")
        if p.capabilities[:3]:
            lines.append(f"  Key capabilities: {'; '.join(p.capabilities[:3])}")
        if p.output_format:
            lines.append(f"  Output: {p.output_format}")
    return "\n".join(lines)


# ── Helpers ──────────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "code-review": ["review", "code quality", "refactor", "clean code", "lint", "analyze code"],
    "debugging": ["bug", "debug", "error", "fix", "issue", "crash", "exception"],
    "architecture": ["architecture", "design pattern", "solid", "mvc", "mvvm", "clean architecture", "structure"],
    "testing": ["test", "unit test", "integration test", "e2e", "tdd", "coverage", "jest", "pytest"],
    "security": ["security", "vulnerability", "owasp", "xss", "injection", "auth", "pentest", "audit"],
    "git": ["git", "commit", "branch", "merge", "version control"],
    "performance": ["performance", "optimize", "speed", "memory", "cache", "bottleneck", "profiling"],
}


def _detect_category(text: str) -> str:
    """Detect the most likely category from text."""
    text_lower = text.lower()
    best_cat = ""
    best_score = 0
    for cat, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_cat = cat
    return best_cat
