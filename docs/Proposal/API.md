# Digital Artifact Mining API

## Overview
The **Digital Artifact Mining API** provides endpoints for uploading and analyzing projects, managing portfolios and resumes, tracking skills, and generating career-related content.  
Built with **FastAPI**, all responses are in **JSON** format.

---

## Base Information
- **Framework:** FastAPI
- **Default Local URL:** `http://localhost:8000`
- **Authentication:** JWT Bearer token — include `Authorization: Bearer <token>` in all protected request headers

---

## Authentication

All endpoints are either:
- **Protected** (`require_auth`) — requires a valid JWT token, returns `401` if missing
- **Guest-tolerant** (`get_current_user_id`) — works without a token, returns guest/public data
- **Public** — no token required

---

## Router Summary

| Tag | Prefix | Auth | Description |
|-----|--------|------|-------------|
| Authentication | `/auth` | Mixed | Signup, login, profile, avatar |
| Projects | `/projects` | Mixed | Upload, retrieve, manage projects |
| Portfolio | `/portfolio` | Protected | Generate and manage portfolios |
| Public Portfolios | `/public` | Public | Browse public portfolios |
| Resume | `/resume` | Protected | Build, customize, and export resumes |
| Skills | `/skills` | Guest-tolerant | Skill lists, detail, and timeline |
| Analytics | `/analytics` | Guest-tolerant | Skill co-occurrence and insights |
| Education | `/education` | Protected | Education entries |
| Work History | `/work-history` | Protected | Work history entries |
| Evidence | `/evidence` | Guest-tolerant | Project metrics, feedback, achievements |
| Interview | `/interview` | Protected | AI-generated STAR interview answers |
| Contributors | `/contributors` | Public | Git contributor extraction |
| Configuration | `/configuration` | Public | Privacy settings and analysis preferences |
| Consent | `/consent` | Public | File access and AI consent management |
| User | `/user` | Protected | GitHub username |

---

## Response Conventions

### Success
- `200 OK` – request succeeded

### Client Errors
- `400 Bad Request` – invalid input
- `401 Unauthorized` – missing or invalid token
- `403 Forbidden` – authenticated but not the resource owner
- `404 Not Found` – resource not found
- `422 Unprocessable Entity` – validation error

### Server Errors
- `500 Internal Server Error` – unexpected error
- `503 Service Unavailable` – module not available

### Standard Error Format
```json
{
  "detail": "Error message"
}
```

---

# Authentication API `/auth`

## POST `/auth/signup`
Create a new user account.

**Request Body**
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@example.com",
  "password": "securepassword123"
}
```

**Response `200 OK`**
```json
{
  "user": {
    "id": 1,
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com"
  },
  "token": "<jwt_token>"
}
```

**Errors:** `400` email already registered, `400` password too short, `500` creation failed

---

## POST `/auth/login`
Login with email and password.

**Request Body**
```json
{
  "email": "jane@example.com",
  "password": "securepassword123"
}
```

**Response `200 OK`**
```json
{
  "user": {
    "id": 1,
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com"
  },
  "token": "<jwt_token>"
}
```

**Errors:** `401` invalid credentials

---

## GET `/auth/me`
Get the current authenticated user's profile. **Protected.**

**Response `200 OK`**
```json
{
  "id": 1,
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@example.com",
  "avatar": null,
  "education_count": 2,
  "work_history_count": 1,
  "project_count": 5,
  "created_at": "2025-01-01T00:00:00"
}
```

**Errors:** `401` not authenticated, `404` user not found

---

## POST `/auth/reset-password`
Reset a user's password by email. No authentication required.

**Request Body**
```json
{
  "email": "jane@example.com",
  "new_password": "newpassword123"
}
```

**Response `200 OK`**
```json
{ "message": "Password updated successfully" }
```

**Errors:** `400` password too short, `404` email not found

---

## PUT `/auth/avatar`
Save or clear the user's profile picture. **Protected.**

**Request Body**
```json
{ "avatar": "<base64_data_url_or_null>" }
```

**Response `200 OK`**
```json
{ "avatar": "<base64_data_url>" }
```

---

## GET `/auth/guest/projects/count`
Get count of guest (unauthenticated) projects. **Public.**

**Response `200 OK`**
```json
{
  "count": 3,
  "message": "Sign up to save your projects permanently"
}
```

---

# Projects API `/projects`

## POST `/projects/upload`
Upload a file or ZIP archive for analysis. **Protected.**  
Files are extracted and scanned automatically. Duplicates are detected by path and content hash.

**Request:** `multipart/form-data`  
**Body:** `file` (required) — any supported file or ZIP

**Response `200 OK`**
```json
{
  "status": "created",
  "project_id": 12,
  "project_name": "my-capstone",
  "project_type": "code",
  "file_count": 42
}
```

Possible `status` values: `"created"`, `"exists"` (duplicate), `"skipped"` (no supported files found)

**Errors:** `422` no file provided, `500` processing error

---

## POST `/projects/guest-analyze`
Analyze a file without an account. Results are not saved. **Public.**

**Request:** `multipart/form-data`  
**Body:** `file` (required)

**Response `200 OK`**
```json
{
  "status": "analyzed",
  "name": "my-project",
  "project_type": "code",
  "file_count": 10,
  "lines_of_code": 1200,
  "languages": ["Python"],
  "skills": ["FastAPI", "SQLAlchemy"],
  "importance_score": 4.5,
  "description": "..."
}
```

---

## GET `/projects`
List all projects for the authenticated user. **Protected.**

**Response `200 OK`**
```json
[
  {
    "id": 1,
    "name": "capstone",
    "project_type": "code",
    "importance_score": 8.2,
    "languages": ["Python", "JavaScript"],
    "file_count": 42,
    "total_size_bytes": 204800
  }
]
```

---

## GET `/projects/{project_id}`
Get a single project by ID. **Protected.**

**Response `200 OK`** — full project object including metrics, languages, frameworks, skills, AI fields.

**Errors:** `404` not found, `403` not your project

---

## PUT `/projects/{project_id}`
Update project fields (e.g. custom description, role, featured, hidden). **Protected.**

**Request Body** — any subset of updatable fields:
```json
{
  "custom_description": "My capstone project",
  "user_role": "Lead Developer",
  "is_featured": true,
  "is_hidden": false
}
```

**Errors:** `403` not your project, `404` not found

---

## DELETE `/projects/{project_id}`
Delete a project. **Protected.**

**Response `200 OK`**
```json
{ "message": "Project deleted successfully" }
```

**Errors:** `403` not your project, `404` not found

---

## POST `/projects/{project_id}/upload`
Add files to an existing project (incremental upload). **Protected.**

**Request:** `multipart/form-data`  
**Body:** `file` (required)

**Response `200 OK`**
```json
{
  "success": true,
  "files_added": 3
}
```

---

## POST `/projects/{project_id}/thumbnail`
Upload a thumbnail image for a project. **Protected.**

**Request:** `multipart/form-data`  
**Body:** `file` (required) — image file (.jpg, .jpeg, .png, .gif, .webp, .bmp, .svg)

**Errors:** `400` invalid image format, `403` not your project

---

## POST `/projects/{project_id}/analyze`
Run or re-run AI analysis on a project (requires AI consent). **Protected.**

**Errors:** `403` not your project, `404` not found

---

## DELETE `/projects/{project_id}/ai-insights`
Delete AI-generated insights for a project without deleting the project itself. **Protected.**

---

## DELETE `/projects/ai-insights/all`
Delete all AI insights across all projects. **Protected.**

---

## GET `/projects/shared-files`
Get a report of files shared across multiple projects. **Protected.**

---

## GET `/projects/cache-stats`
Get statistics about the AI analysis cache. **Protected.**

---

## DELETE `/projects/cache`
Clear all cached AI analysis data. **Protected.**

---

# Portfolio API `/portfolio`

All portfolio endpoints require authentication.

## GET `/portfolio`
Return the stored portfolio for the authenticated user. Generates and stores one if none exists.

**Query Parameters**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| include_hidden | boolean | false | Include hidden projects |

**Response `200 OK`** — full portfolio object with projects, stats, and summary text.

---

## POST `/portfolio/generate`
Regenerate the portfolio from current project data and save it.

**Query Parameters:** `include_hidden` (boolean, default false)

**Response `200 OK`** — fresh portfolio object.

---

## GET `/portfolio/stats`
Return only the portfolio statistics.

**Response `200 OK`**
```json
{
  "total_projects": 5,
  "total_languages": 8,
  "total_skills": 24,
  "project_types": { "code": 3, "text": 1, "media": 1 }
}
```

---

## GET `/portfolio/summary`
Return only the portfolio summary text and highlights.

---

## GET `/portfolio/showcase`
Return the top 3 projects by importance score with evolution milestone data.

**Response `200 OK`**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "Capstone",
      "importance_score": 8.2,
      "languages": ["Python"],
      "skills": ["FastAPI"],
      "evolution": [
        { "label": "Project started", "date": "Sep 2024" },
        { "label": "42 files analysed", "date": null }
      ]
    }
  ],
  "total": 5
}
```

---

## GET `/portfolio/about`
Return the user's About Me fields.

**Response `200 OK`**
```json
{
  "about_name": "Jane Doe",
  "about_subtitle": "Full Stack Developer",
  "about_bio": "..."
}
```

---

## POST `/portfolio/about`
Save the user's About Me fields.

**Request Body**
```json
{
  "about_name": "Jane Doe",
  "about_subtitle": "Full Stack Developer",
  "about_bio": "..."
}
```

---

## GET `/portfolio/contact`
Return the user's contact info.

**Response `200 OK`**
```json
{ "contact_info": { "email": "jane@example.com", "github": "janedoe" } }
```

---

## POST `/portfolio/contact`
Save the user's contact info. Accepts any key-value pairs.

---

## GET `/portfolio/visibility`
Return whether the portfolio is public.

**Response `200 OK`**
```json
{ "portfolio_public": false }
```

---

## POST `/portfolio/visibility`
Set portfolio visibility.

**Request Body**
```json
{ "portfolio_public": true }
```

---

## GET `/portfolio/{project_id}`
Return a single formatted project card. Owner only.

**Errors:** `403` not your project, `404` not found

---

## POST `/portfolio/{project_id}/edit`
Edit a project's fields and regenerate the portfolio. Owner only.

**Request Body** — any updatable project fields:
```json
{
  "custom_description": "Updated name",
  "user_role": "Backend Developer",
  "is_featured": true
}
```

**Errors:** `403` not your project, `404` not found

---

# Public Portfolios API `/public`

## GET `/public/portfolios`
List all users who have made their portfolio public. **Public.**

**Response `200 OK`**
```json
{
  "portfolios": [
    {
      "user_id": 1,
      "display_name": "Jane Doe",
      "about_subtitle": "Full Stack Developer",
      "project_count": 5,
      "top_skills": ["Python", "React"],
      "summary": "..."
    }
  ],
  "total": 1
}
```

---

## GET `/public/portfolios/{user_id}`
Get a specific user's public portfolio. Returns `404` if not public. **Public.**

**Response `200 OK`**
```json
{
  "user_id": 1,
  "display_name": "Jane Doe",
  "about_name": "Jane Doe",
  "about_subtitle": "Full Stack Developer",
  "about_bio": "...",
  "projects": [...],
  "stats": {},
  "summary_text": "...",
  "education": [...],
  "work_history": [...],
  "contact_info": {}
}
```

---

# Resume API `/resume`

All resume endpoints require authentication. All bullet and full-resume endpoints require a `resume_id` query parameter.

## Resume Management

### GET `/resume/list`
List all resumes for the authenticated user.

**Response `200 OK`**
```json
[
  { "id": 1, "name": "Software Engineer Resume", "created_at": "..." }
]
```

---

### POST `/resume/create`
Create a new resume.

**Request Body**
```json
{ "name": "New Resume" }
```

---

### PUT `/resume/{resume_id}/rename`
Rename a resume.

**Request Body**
```json
{ "name": "Updated Name" }
```

---

### DELETE `/resume/{resume_id}`
Delete a resume. The last resume cannot be deleted.

**Errors:** `400` cannot delete last resume, `403` not your resume

---

### POST `/resume/{resume_id}/duplicate`
Duplicate a resume with an optional new name.

**Request Body** (optional)
```json
{ "name": "Copy of My Resume" }
```

---

## Per-Project Bullet Endpoints

All require `?resume_id=<id>` query parameter.

### POST `/resume/projects/{project_id}/generate`
Generate and store resume bullets for a project using rule-based generation.

**Request Body** (optional)
```json
{ "num_bullets": 3 }
```

---

### POST `/resume/projects/{project_id}/ai-generate`
Generate bullets using Gemini AI.

**Request Body** (optional)
```json
{ "num_bullets": 3 }
```

---

### POST `/resume/projects/{project_id}/ai-enhance`
Enhance existing bullets using Gemini AI. Falls back to generation if none exist.

**Request Body** (optional)
```json
{
  "bullets": ["Existing bullet..."],
  "num_bullets": 3
}
```

---

### POST `/resume/projects/{project_id}/regenerate`
Regenerate all bullets, replacing existing ones.

---

### GET `/resume/projects/{project_id}`
Get stored bullets for a project.

**Response `200 OK`**
```json
{
  "project_id": 1,
  "bullets": ["Built REST API...", "Reduced load time by 40%..."],
  "header": "Custom Project Header"
}
```

---

### POST `/resume/projects/{project_id}/edit`
Edit stored bullets and/or header for a project.

**Request Body**
```json
{
  "bullets": ["Updated bullet..."],
  "header": "My Project"
}
```

---

### GET `/resume/projects/{project_id}/ats`
Get ATS scores for a project's stored bullets.

---

### DELETE `/resume/projects/{project_id}`
Delete stored bullets for a project.

---

## Full Resume Endpoints

### POST `/resume/generate?resume_id=<id>`
Smart generate: fills missing bullets for all projects, then assembles and stores the full resume.

**Request Body** (optional)
```json
{ "num_bullets": 3 }
```

---

### GET `/resume?resume_id=<id>`
Return the stored resume JSON.

---

### POST `/resume/save?resume_id=<id>`
Save the enriched resume to the database. Called after the frontend adds education, work history, skills, section order, and section labels.

**Request Body** — full resume JSON object including `sectionOrder` and `sectionLabels`.

---

### POST `/resume/page-count`
Build the resume PDF in memory and return the page count. Nothing is saved.

**Request Body** — resume JSON payload.

**Response `200 OK`**
```json
{ "pages": 1 }
```

---

### GET `/resume/download/pdf?resume_id=<id>`
Export the stored resume as a downloadable PDF file.

**Response:** `application/pdf` stream with `Content-Disposition: attachment`

**Errors:** `404` no resume found, `500` generation failed

---

### GET `/resume/download/docx?resume_id=<id>`
Export the stored resume as a downloadable DOCX file.

**Response:** `application/vnd.openxmlformats-officedocument.wordprocessingml.document` stream

**Errors:** `404` no resume found, `500` generation failed

---

# Skills API `/skills`

Guest-tolerant — works without authentication, scoped to the authenticated user if a token is provided.

## GET `/skills/`
List all skills with project counts.

**Response `200 OK`**
```json
{
  "skills": [
    {
      "name": "Python",
      "count": 4,
      "projects": [
        { "project_id": 1, "project_name": "Capstone", "project_type": "code" }
      ]
    }
  ]
}
```

---

## GET `/skills/timeline`
Return skills with first and last seen dates derived from project activity.

**Response `200 OK`**
```json
{
  "skills": [
    {
      "name": "Python",
      "first_seen": "2023-09-01",
      "last_seen": "2025-03-01",
      "project_count": 4,
      "projects": [...]
    }
  ]
}
```

---

## GET `/skills/{skill_name}`
Get detail for a specific skill including all projects that use it.

**Response `200 OK`**
```json
{
  "skill": "Python",
  "project_count": 4,
  "projects": [
    { "project_id": 1, "project_name": "Capstone", "project_type": "code", "file_count": 42 }
  ]
}
```

---

# Analytics API `/analytics`

Guest-tolerant.

## GET `/analytics/co-occurrence`
Return skill pairs that appear together across projects.

**Response `200 OK`**
```json
{
  "pairs": [
    {
      "skill_1": "Python",
      "skill_2": "FastAPI",
      "count": 3,
      "projects": [{ "project_name": "Capstone" }]
    }
  ]
}
```

---

## GET `/analytics/skills`
Return full skill analytics including raw data, co-occurrence, and insights.

**Response `200 OK`**
```json
{
  "raw": {
    "skills": [...],
    "co_occurrence": [...]
  },
  "insights": {
    "top_skills": [...],
    "most_common_pair": { "skill_1": "Python", "skill_2": "FastAPI", "count": 3 },
    "skill_diversity": 4.8
  }
}
```

---

# Education API `/education`

All endpoints require authentication.

## GET `/education`
Return all education entries for the authenticated user.

**Response `200 OK`**
```json
{
  "education": [
    {
      "id": 1,
      "institution": "UBC Okanagan",
      "degree_type": "Bachelor of Science",
      "topic": "Computer Science",
      "start_date": "2021-09-01",
      "end_date": "2025-04-30",
      "location": "Kelowna, BC",
      "gpa": "3.8",
      "details": ["Dean's List 2023"]
    }
  ]
}
```

---

## POST `/education`
Add a new education entry.

**Request Body**
```json
{
  "institution": "UBC Okanagan",
  "degree_type": "Bachelor of Science",
  "topic": "Computer Science",
  "start_date": "2021-09-01",
  "end_date": "2025-04-30",
  "location": "Kelowna, BC",
  "gpa": "3.8",
  "details": ["Dean's List 2023"]
}
```

**Errors:** `422` invalid date format

---

## DELETE `/education/{education_id}`
Delete an education entry. Owner only.

**Errors:** `404` not found or not your entry, `500` deletion failed

---

# Work History API `/work-history`

All endpoints require authentication.

## GET `/work-history`
Return all work history entries for the authenticated user.

**Response `200 OK`**
```json
{
  "work_history": [
    {
      "id": 1,
      "company": "Acme Corp",
      "role": "Software Developer Intern",
      "experience_type": "work",
      "start_date": "2024-05-01",
      "end_date": null,
      "location": "Vancouver, BC",
      "bullets": ["Built internal tooling...", "Reduced deploy time by 30%..."]
    }
  ]
}
```

---

## POST `/work-history`
Add a new work history entry.

**Request Body**
```json
{
  "company": "Acme Corp",
  "role": "Software Developer Intern",
  "experience_type": "work",
  "start_date": "2024-05-01",
  "end_date": null,
  "location": "Vancouver, BC",
  "bullets": ["Built internal tooling..."]
}
```

`experience_type` defaults to `"work"` if not provided.

**Errors:** `422` invalid date format

---

## DELETE `/work-history/{work_id}`
Delete a work history entry. Owner only.

**Errors:** `404` not found or not your entry, `500` deletion failed

---

# Evidence API `/evidence`

Guest-tolerant — ownership enforced if authenticated.

## GET `/evidence/{project_id}`
Return all evidence for a project.

**Response `200 OK`**
```json
{
  "test_coverage": 85,
  "code_quality": "A",
  "manual_metrics": {
    "users": { "value": 1000, "description": "Active users" }
  },
  "feedback": [
    { "text": "Great project!", "source": "Professor", "rating": 5 }
  ],
  "achievements": [
    { "description": "Won 1st place at hackathon", "date": "2024-11-01" }
  ],
  "readme_badges": []
}
```

---

## POST `/evidence/{project_id}/extract`
Auto-extract evidence from project files. Routes to the appropriate extractor by project type.

**Response `200 OK`**
```json
{ "extracted": true, "evidence": {...}, "nothing_found": false }
```

---

## POST `/evidence/{project_id}/metric`
Add a manual metric.

**Request Body**
```json
{
  "metric_name": "Active Users",
  "value": "1000",
  "description": "Monthly active users at launch"
}
```

**Errors:** `400` rating out of range, `500` save failed

---

## POST `/evidence/{project_id}/feedback`
Add feedback or a testimonial.

**Request Body**
```json
{
  "text": "Excellent work on the architecture.",
  "source": "Professor",
  "rating": 5
}
```

**Errors:** `400` rating not 1–5, `500` save failed

---

## POST `/evidence/{project_id}/achievement`
Add an achievement or award.

**Request Body**
```json
{
  "description": "Won 1st place at UBC Hackathon",
  "date": "2024-11-01"
}
```

---

## DELETE `/evidence/{project_id}`
Clear all evidence for a project.

**Response `200 OK`**
```json
{ "cleared": true, "project_id": 1 }
```

---

# Interview API `/interview`

Requires authentication.

## POST `/interview/generate`
Generate 4 STAR-format behavioral interview answers from the user's projects using Gemini AI.

**Request Body**
```json
{
  "target_role": "Software Engineer",
  "project_ids": [1, 2, 3]
}
```

`project_ids` is optional — omitting it uses all projects (capped at 5).

**Response `200 OK`**
```json
{
  "answers": [
    {
      "question": "Tell me about a time you solved a challenging technical problem.",
      "situation": "...",
      "task": "...",
      "action": "...",
      "result": "...",
      "project_name": "Capstone",
      "project_type": "code"
    }
  ],
  "target_role": "Software Engineer"
}
```

**Errors:** `404` no projects found, `500` AI parse error

---

# Contributors API `/contributors`

Public — no authentication required.

## POST `/contributors/populate/all`
Extract Git contributor data for all projects.

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| since_date | string | Start date (YYYY-MM-DD) |
| until_date | string | End date (YYYY-MM-DD) |

---

## POST `/contributors/populate/project`
Extract Git contributor data for a specific project.

**Query Parameters:** `project_name` or `project_id` (one required), `since_date`, `until_date`

**Errors:** `400` neither project_name nor project_id provided

---

## GET `/contributors/verify-git-stats`
Verify Git stats for a repository path. Results logged server-side.

**Query Parameters:** `project_path` (required), `since_date`, `until_date`

---

# Configuration API `/configuration`

Public — no authentication required.

## GET `/configuration/privacy-settings`
Return current privacy settings.

**Response `200 OK`**
```json
{
  "anonymous_mode": false,
  "store_file_contents": true,
  "store_contributor_names": true,
  "store_file_paths": true,
  "max_file_size_scan": 10485760,
  "excluded_folders": [],
  "excluded_file_types": []
}
```

---

## PATCH `/configuration/privacy-settings`
Update one or more privacy settings.

**Request Body** — any subset:
```json
{
  "anonymous_mode": true,
  "max_file_size_scan": 5242880
}
```

---

## POST `/configuration/privacy-settings/excluded-folders`
Add a folder to the exclusion list.

**Request Body**
```json
{ "folder_path": "/node_modules" }
```

---

## DELETE `/configuration/privacy-settings/excluded-folders`
Remove a folder from the exclusion list.

**Request Body**
```json
{ "folder_path": "/node_modules" }
```

---

## POST `/configuration/privacy-settings/excluded-file-types`
Add a file type to the exclusion list.

**Request Body**
```json
{ "file_type": ".log" }
```

---

## DELETE `/configuration/privacy-settings/excluded-file-types`
Remove a file type from the exclusion list.

---

## GET `/configuration/analysis-preferences`
Return current analysis preferences.

**Response `200 OK`**
```json
{
  "enable_keyword_extraction": true,
  "enable_language_detection": true,
  "enable_framework_detection": true,
  "enable_collaboration_analysis": true,
  "enable_duplicate_detection": true
}
```

---

## PATCH `/configuration/analysis-preferences`
Update one or more analysis preferences.

---

## POST `/configuration/analysis-preferences/enable-all`
Enable all analysis preferences at once.

---

## POST `/configuration/analysis-preferences/disable-all`
Disable all analysis preferences at once.

---

## GET `/configuration/current-configuration`
Return the full system configuration including consent, privacy, analysis, scanning, AI, output, UI, performance, notification, and backup settings.

---

# Consent API `/consent`

Public — no authentication required.

## POST `/consent/basic-consent-grant`
Grant file access consent. Required before uploading projects.

**Response `200 OK`** — full config object.

---

## POST `/consent/basic-consent-revoke`
Revoke file access consent.

---

## POST `/consent/ai-consent-grant`
Grant AI consent. Required before using Gemini-powered features.

---

## POST `/consent/ai-consent-revoke`
Revoke AI consent.

---

## GET `/consent/basic-consent-status`
Return current file access consent status.

**Response `200 OK`**
```json
{
  "basic_consent_granted": true,
  "basic_consent_timestamp": "2025-01-01T00:00:00"
}
```

---

## GET `/consent/ai-consent-status`
Return current AI consent status.

**Response `200 OK`**
```json
{
  "ai_consent_granted": false,
  "ai_consent_timestamp": null
}
```

---

# User API `/user`

Requires authentication.

## POST `/user/github-username`
Save the user's GitHub username.

**Request Body**
```json
{ "github_username": "janedoe" }
```

**Response `200 OK`**
```json
{ "success": true, "github_username": "janedoe" }
```

---

## GET `/user/github-username`
Get the user's GitHub username.

**Response `200 OK`**
```json
{ "github_username": "janedoe" }
```
