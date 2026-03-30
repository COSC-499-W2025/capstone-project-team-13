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

**Feature affected:** User authentication
**Severity:** High
**Status:** Open

**Description:**
The JWT signing secret is a static string committed to the repository. Any user who can read the source code can forge valid authentication tokens.

**Reproduction:**
Open [src/Services/auth_service.py:16](../src/Services/auth_service.py#L16):

```python
SECRET_KEY = "dam-secret-key-2025-change-in-production"
```

No runtime configuration or environment variable overrides this value.

**Impact:** All issued JWTs can be forged by anyone with access to the codebase.

---

## BUG-004 — AI analysis silently produces no output when Gemini response is truncated

**Feature affected:** AI project analysis / resume bullet generation
**Severity:** Medium
**Status:** Open

**Description:**
When the AI model hits its `max_tokens` limit mid-response, the response is flagged as truncated (`finish_reason = MAX_TOKENS`). The library then raises an exception when accessing `response.text` because the response has no valid `Part`. The service catches this and falls back to a generic message, with no indication to the user that analysis is incomplete.

**Reproduction:**
Upload a very large project (many files, high line count). The AI analysis step will appear to succeed but return either a fallback generic summary or fewer resume bullets than expected.

**Affected file:** [src/AI/ai_service.py:331–352](../src/AI/ai_service.py#L331)

---

## BUG-005 — Git contributor data missing for projects without a `.git` directory

**Feature affected:** Contributor analysis / role attribution
**Severity:** Low
**Status:** Open (by design, but not communicated to the user)

**Description:**
The contributor extraction feature relies on running `git log` against the uploaded project. If the uploaded ZIP does not contain a `.git` directory, contributor data is silently skipped. The project page shows no contributors, with no explanation.

**Reproduction:**
Upload a code project as a ZIP that was exported without git history (e.g., downloaded from GitHub as "Download ZIP"). Navigate to the project's contributor section — it will be empty.

**Affected file:** [src/Helpers/gitContributorExtraction.py:54–73](../src/Helpers/gitContributorExtraction.py#L54)

---

## BUG-006 — Project type detection misclassifies mixed-content projects

**Feature affected:** Project upload — type detection
**Severity:** Medium
**Status:** Partially fixed (PR #516, PR #537)

**Description:**
The file-type sniffer (`sniff_supertype`) counts file extensions to determine whether a project is a coding, text, or media project. Projects that contain documentation alongside code, or media alongside text, can be misclassified as the wrong type. When misclassified, the wrong scanner runs and skills/languages are not extracted correctly.

**Reproduction:**
Upload a project folder that contains both Python/JS source files and image assets. Depending on the ratio, the project may be classified as `media` instead of `code`, and language detection will return empty results.

**Affected files:**
- [src/Helpers/fileDataCheck.py](../src/Helpers/fileDataCheck.py)
- [src/Analysis/multiProjectZip.py](../src/Analysis/multiProjectZip.py)

---

## BUG-007 — SKILL_KEYWORDS defined inline instead of from shared module

**Feature affected:** Keyword analytics / skill extraction
**Severity:** Low
**Status:** Open (pending PR #82)

**Description:**
`keywordAnalytics.py` defines its own copy of `SKILL_KEYWORDS` inline because the shared module that should export this constant was not merged. This means changes to skill keywords in the shared module are not reflected in keyword analytics.

**Reproduction:**
Search the codebase for `SKILL_KEYWORDS` — two separate definitions exist. Adding a new skill to one does not update the other.

**Affected file:** [src/Analysis/keywordAnalytics.py:165](../src/Analysis/keywordAnalytics.py#L165)

---

## BUG-008 — Bare `except` clauses silently swallow unexpected errors

**Feature affected:** Multiple — deletion manager, CLI stats display
**Severity:** Low
**Status:** Open

**Description:**
Several locations use bare `except: pass` which catches all exceptions including `KeyboardInterrupt` and `SystemExit`. When an unexpected error occurs in these blocks, it is silently ignored and the user sees no indication that something went wrong.

**Reproduction:**
Trigger an error inside the guarded code path (e.g., corrupt database record when displaying shared-file warnings, or malformed JSON in cache stats). The error will be swallowed with no output.

**Affected file:** [src/main.py:406](../src/main.py#L406), [src/main.py:1950](../src/main.py#L1950), [src/main.py:1980](../src/main.py#L1980)

---

## BUG-009 — AI features unavailable when `GEMINI_API_KEY` is not set, with no user-facing message in UI

**Feature affected:** AI analysis, resume bullet generation, project summarization
**Severity:** Medium
**Status:** Open

**Description:**
When `GEMINI_API_KEY` is absent from the environment, the AI service initializes but all generation calls return `None` or empty strings. In the web UI, the analysis section simply shows nothing or a spinner that never resolves, without any error message explaining that AI is unavailable.

**Reproduction:**
Remove `GEMINI_API_KEY` from `.env`, restart the server, then upload a project and navigate to the analysis or resume page.

**Affected files:**
- [src/AI/ai_service.py](../src/AI/ai_service.py)
- [src/AI/ai_project_analyzer.py](../src/AI/ai_project_analyzer.py)

---

## BUG-010 — Incremental update failure provides no actionable error to the user

**Feature affected:** Incremental file/ZIP upload
**Severity:** Low
**Status:** Open

**Description:**
When an incremental update fails (e.g., hash mismatch, missing project record), the system prints `INCREMENTAL UPDATE FAILED` or `❌ FAILED TO ADD FILE` to the server console but returns a generic success or ambiguous response to the frontend. The user has no indication that the update did not apply.

**Reproduction:**
Trigger an incremental update while the underlying project record has been deleted from the database. The API returns a 200-level response while the server logs show the failure.

**Affected files:**
- [src/Analysis/incrementalZipHandler.py:318](../src/Analysis/incrementalZipHandler.py#L318)
- [src/Analysis/incrementalFileHandler.py:347](../src/Analysis/incrementalFileHandler.py#L347)

---

*Last updated: 2026-03-29*
