# Known Bugs

This document tracks specific cases where an implemented feature does not behave as expected. Each entry describes the affected feature, the exact failure scenario, and its current status.

---

## BUG-001 — Debug output printed to console during AI analysis

**Feature affected:** AI project analysis (project upload pipeline)
**Severity:** Medium
**Status:** Open

**Description:**
When a project is uploaded and analyzed by the AI, multiple debug `print()` statements fire to stdout. These appear in the terminal and in the browser's response stream if SSE is in use.

**Reproduction:**
Upload any project and trigger AI analysis. The console (server-side) will show output such as:

```
[DEBUG] AI Response:
'...'
[DEBUG] Added bullet: ...
[DEBUG] Total bullets found: 3
🔍 DEBUG: Starting overview analysis...
🔍 DEBUG: Starting technical depth analysis...
🔍 DEBUG: Starting skills extraction...
✅ API key loaded: AIzaSy...
```

**Affected files:**
- [src/AI/ai_enhanced_summarizer.py:306](../src/AI/ai_enhanced_summarizer.py#L306)
- [src/AI/ai_project_analyzer.py:540](../src/AI/ai_project_analyzer.py#L540)
- [src/AI/ai_service.py:34](../src/AI/ai_service.py#L34)
- [src/main.py:1035](../src/main.py#L1035)

---

## BUG-002 — Partial API key printed to console on server startup

**Feature affected:** AI service initialization
**Severity:** Medium
**Status:** Open

**Description:**
Every time the backend starts, the first 10 characters of the `GEMINI_API_KEY` are printed to the terminal. This is a diagnostic leftover that should not run in any environment.

**Reproduction:**
Start the backend server (`uvicorn` or `python -m src.mainAPI`). The terminal will show:

```
✅ API key loaded: AIzaSy1234...
```

**Affected file:** [src/AI/ai_service.py:34–38](../src/AI/ai_service.py#L34)

---

## BUG-003 — JWT secret key is hardcoded in source code
