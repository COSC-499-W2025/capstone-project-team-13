# Digital Artifact Mining API

## Overview
The **Digital Artifact Mining API** provides endpoints for uploading and analyzing projects, and for generating and managing portfolios and resumes.  
The API is built using **FastAPI** and returns responses in **JSON** format.

---

## Base Information
- **Framework:** FastAPI
- **Default Local URL:** `http://localhost:8000`


- **Code found in Router folder**
---

## Router Summary

| Tag | Prefix | Description |
|-----|--------|-------------|
| Projects | `/projects` | Upload and retrieve project data |
| Portfolio | `/portfolio` | Generate and manage portfolios |
| Resume | `/resumes` | Generate and manage resumes |
| Meta | `/meta` | Miscellaneous endpoints such as privacy consent and skills |
---

## Response Conventions

### Success
- `200 OK` – request succeeded
- `201 Created` – resource created (future use)

### Client Errors
- `400 Bad Request` – invalid request
- `404 Not Found` – resource not found
- `422 Unprocessable Entity` – validation error

### Server Errors
- `500 Internal Server Error` – unexpected error

### Standard Error Format
```json
{
  "detail": "Error message"
}
```

---

# Projects API

## 1. Upload Project
**POST** `/projects/upload`

Uploads a project file for analysis.  
If the uploaded file is a ZIP, it will be extracted and processed as a folder.

### Request
- **Content-Type:** `multipart/form-data`
- **Body**
  - `file` (required): project file
```

### Successful Response
**200 OK**
```json
{
  "message": "Analysis complete",
  "project_type": "code",
  "summary": "...",
  "metrics": {
    "lines_of_code": 1234,
    "files": 42
  }
}
```

### Errors
- `422` – file missing
- `500` – processing or extraction error

### Notes
- Files are stored in `evidence/uploads/`
- ZIP files are automatically extracted before processing
- The response structure depends on the analysis service

---

## 2. List All Projects
**GET** `/projects`

Returns all projects stored in the database.

### Request
No parameters.

### Successful Response
**200 OK**
```json
[
  {
    "id": 1,
    "name": "Project A",
    "project_type": "code"
  },
  {
    "id": 2,
    "name": "Project B",
    "project_type": "text"
  }
]
```

### Errors
- `500` – database error

---

## 3. Get Project by ID
**GET** `/projects/{project_id}`

Returns a single project and its metrics.

### Path Parameters
| Name | Type | Description |
|------|------|-------------|
| project_id | integer | ID of the project |

### Example
```
GET /projects/12
```

### Successful Response
**200 OK**
```json
{
  "id": 12,
  "name": "Capstone",
  "project_type": "code",
  "counts": {
    "lines_of_code": 9500,
    "word_count": 0,
    "total_size_bytes": 0
  }
}
```

### Errors
- `404` – project not found
```json
{
  "detail": "Project not found"
}
```
- `422` – invalid project ID
- `500` – database error

---

# Portfolio API

## 1. Get Portfolio by ID
**GET** `/portfolio/{id}`

Returns a portfolio by ID.

### Path Parameters
| Name | Type | Description |
|------|------|-------------|
| id | integer | Portfolio ID |

### Successful Response
**200 OK**
```json
{
  "portfolio_id": 5
}
```

### Errors
- `422` – invalid ID

---

## 2. Generate Portfolio
**POST** `/portfolio/generate`

Triggers portfolio generation.

### Request
No request body required.

### Successful Response
**200 OK**
```json
{
  "message": "Portfolio generated"
}
```

---

## 3. Edit Portfolio
**POST** `/portfolio/{id}/edit`

Updates a portfolio.

### Path Parameters
| Name | Type | Description |
|------|------|-------------|
| id | integer | Portfolio ID |

### Successful Response
**200 OK**
```json
{
  "message": "Portfolio 3 updated"
}
```

---

# Resume API

## 1. Get Resume by ID
**GET** `/resume/{id}`

Returns a resume by ID.

### Path Parameters
| Name | Type | Description |
|------|------|-------------|
| id | integer | Resume ID |

### Successful Response
**200 OK**
```json
{
  "resume_id": 10
}
```

---

## 2. Generate Resume
**POST** `/resume/generate`

Triggers resume generation.

### Request
No request body required.

### Successful Response
**200 OK**
```json
{
  "message": "Resume generated"
}
```

---

## 3. Edit Resume
**POST** `/resume/{id}/edit`

Updates a resume.

### Path Parameters
| Name | Type | Description |
|------|------|-------------|
| id | integer | Resume ID |

### Successful Response
**200 OK**
```json
{
  "message": "Resume 10 updated"
}
```

---
